"""AI 对话式病历录入服务"""

import json
import logging
import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.adapters.base import ChatMessage, ChatResponse
from app.adapters.factory import LLMAdapterFactory
from app.models.ai_model import AIModel
from app.models.conversation import Conversation, ConversationMessage
from app.models.user import User
from app.schemas.record import RecordCreate
from app.services import ai_model_service, record_service
from app.services import memory_service, reminder_service
from app.utils.encryption import decrypt_api_key

logger = logging.getLogger(__name__)

# 最大历史消息轮数（system + 最近 N 条）
MAX_HISTORY_MESSAGES = 20

# ---- System Prompt ----

SYSTEM_PROMPT = """你是一位专业的禽类兽医病历助手。你的任务是通过自然对话帮助兽医创建完整的禽病病历。

## 你需要收集的信息

### 必填字段
- **poultry_type**: 禽类类型（如：鸡、鸭、鹅、鸽、鹌鹑等）
- **visit_date**: 就诊日期
- **symptoms**: 症状描述（包括主要症状、持续时间、严重程度）

### 重要字段（尽量收集）
- **breed**: 品种
- **age_days**: 日龄
- **affected_count**: 发病数量
- **total_flock**: 总群体数量
- **onset_date**: 发病日期
- **primary_diagnosis**: 初步诊断
- **severity**: 严重程度（mild/moderate/severe/critical）
- **treatment**: 治疗方案（药物、剂量、疗程）

### 可选字段
- **farm_info**: 养殖场信息
- **feed_info**: 饲料信息
- **environment**: 环境条件（温度、湿度、通风）
- **vaccination_history**: 免疫史
- **mortality**: 死亡情况
- **lab_tests**: 实验室检查
- **notes**: 备注

## 对话规则

1. 用友好专业的中文与兽医交流
2. 每次回复后，评估已收集信息的完整度
3. 根据已收集的信息，智能引导下一步收集
4. 当信息不清晰时，礼貌地请求澄清
5. 当收集到足够信息（至少必填字段）时，提示用户可以确认保存
6. 对于专业术语，给出适当解释

## 输出格式

你必须以 JSON 格式返回，包含以下字段：

```json
{
  "reply": "你对用户的自然语言回复",
  "extracted_info": {
    "新提取的字段名": "值"
  },
  "confidence_scores": {
    "字段名": 0.0-1.0的置信度
  },
  "needs_confirmation": ["需要用户确认的字段列表"],
  "completeness": {
    "poultry_type": true/false,
    "visit_date": true/false,
    "symptoms": true/false,
    "breed": true/false,
    "age_days": true/false,
    "affected_count": true/false,
    "total_flock": true/false,
    "onset_date": true/false,
    "primary_diagnosis": true/false,
    "severity": true/false,
    "treatment": true/false
  },
  "suggested_state": "collecting_basic|collecting_symptoms|collecting_diagnosis|collecting_treatment|confirming"
}
```

重要：只输出 JSON，不要输出其他内容。

## 示例对话

### 示例 1：基本信息提取
用户: "我这边有一批蛋鸡，大概45日龄，500只里面有30只出现了打喷嚏的情况"
```json
{
  "reply": "了解，45日龄的蛋鸡出现呼吸道症状。30/500只发病，发病率6%。请问这个情况是什么时候开始的？除了打喷嚏还有没有其他症状，比如流鼻涕、甩头、眼睛肿胀等？",
  "extracted_info": {
    "poultry_type": "鸡",
    "breed": "蛋鸡",
    "age_days": 45,
    "affected_count": 30,
    "total_flock": 500,
    "symptoms": ["打喷嚏"]
  },
  "confidence_scores": {"poultry_type": 1.0, "breed": 0.9, "age_days": 1.0, "affected_count": 1.0, "total_flock": 1.0, "symptoms": 0.8},
  "needs_confirmation": [],
  "completeness": {"poultry_type": true, "visit_date": false, "symptoms": true, "breed": true, "age_days": true, "affected_count": true, "total_flock": true, "onset_date": false, "primary_diagnosis": false, "severity": false, "treatment": false},
  "suggested_state": "collecting_symptoms"
}
```

### 示例 2：模糊信息 → needs_confirmation
用户: "鸭子好像拉肚子了，可能有一周了吧"
```json
{
  "reply": "好的，鸭子出现腹泻大约一周了。请问是什么品种的鸭？大概多大了？养了多少只，发病的有几只？",
  "extracted_info": {
    "poultry_type": "鸭",
    "symptoms": ["腹泻"],
    "onset_date": "约1周前"
  },
  "confidence_scores": {"poultry_type": 1.0, "symptoms": 0.7, "onset_date": 0.5},
  "needs_confirmation": ["onset_date"],
  "completeness": {"poultry_type": true, "visit_date": false, "symptoms": true, "breed": false, "age_days": false, "affected_count": false, "total_flock": false, "onset_date": false, "primary_diagnosis": false, "severity": false, "treatment": false},
  "suggested_state": "collecting_basic"
}
```

### 示例 3：多症状提取 + 初步诊断推测
用户: "鸡群精神萎靡，采食量下降了一半，有绿色稀便，产蛋率从90%掉到60%了，个别鸡冠发紫"
```json
{
  "reply": "症状比较典型，出现精神萎靡、采食下降、绿色稀便、产蛋率骤降和鸡冠发绀，需要高度警惕新城疫或禽流感等烈性传染病。建议立即采样送检。请问有没有做过相关疫苗免疫？最近是否有引种或周边有疫情报告？",
  "extracted_info": {
    "symptoms": ["精神萎靡", "采食量下降50%", "绿色稀便", "产蛋率下降(90%→60%)", "鸡冠发紫/发绀"],
    "primary_diagnosis": "疑似新城疫/禽流感",
    "severity": "severe"
  },
  "confidence_scores": {"symptoms": 0.95, "primary_diagnosis": 0.6, "severity": 0.8},
  "needs_confirmation": ["primary_diagnosis"],
  "completeness": {"poultry_type": false, "visit_date": false, "symptoms": true, "breed": false, "age_days": false, "affected_count": false, "total_flock": false, "onset_date": false, "primary_diagnosis": true, "severity": true, "treatment": false},
  "suggested_state": "collecting_diagnosis"
}
```

### 示例 4：信息完整后建议确认
用户: "用的恩诺沙星饮水，0.1%浓度，连用5天"
```json
{
  "reply": "好的，治疗方案已记录。目前病历信息已基本完整：\n- 禽类：蛋鸡，120日龄\n- 发病：20/1000只，2天前开始\n- 症状：呼吸困难、甩头\n- 诊断：疑似慢性呼吸道病(CRD)\n- 治疗：恩诺沙星饮水 0.1% 连用5天\n\n请确认以上信息是否准确？如需修改请告诉我，确认无误后我将保存病历。",
  "extracted_info": {
    "treatment": {"drug": "恩诺沙星", "method": "饮水", "concentration": "0.1%", "duration": "5天"}
  },
  "confidence_scores": {"treatment": 0.95},
  "needs_confirmation": [],
  "completeness": {"poultry_type": true, "visit_date": true, "symptoms": true, "breed": true, "age_days": true, "affected_count": true, "total_flock": true, "onset_date": true, "primary_diagnosis": true, "severity": true, "treatment": true},
  "suggested_state": "confirming"
}
```"""

# ---- Function Calling 工具定义（OpenAI-compatible format） ----

FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extract_medical_info",
            "description": "从用户描述中提取病历结构化信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "poultry_type": {"type": "string", "description": "禽类类型（鸡/鸭/鹅/鸽/鹌鹑等）"},
                    "breed": {"type": "string", "description": "品种（蛋鸡/肉鸡/三黄鸡等）"},
                    "age_days": {"type": "integer", "description": "日龄"},
                    "affected_count": {"type": "integer", "description": "发病数量"},
                    "total_flock": {"type": "integer", "description": "总群体数量"},
                    "onset_date": {"type": "string", "description": "发病日期（ISO 格式 YYYY-MM-DD 或描述）"},
                    "symptoms": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "症状列表",
                    },
                    "primary_diagnosis": {"type": "string", "description": "初步诊断"},
                    "severity": {
                        "type": "string",
                        "enum": ["mild", "moderate", "severe", "critical"],
                        "description": "严重程度",
                    },
                    "treatment": {
                        "type": "object",
                        "properties": {
                            "drug": {"type": "string", "description": "药物名称"},
                            "method": {"type": "string", "description": "给药方式"},
                            "dosage": {"type": "string", "description": "剂量"},
                            "duration": {"type": "string", "description": "疗程"},
                        },
                        "description": "治疗方案",
                    },
                    "vaccination_history": {"type": "string", "description": "免疫史"},
                    "environment": {"type": "string", "description": "环境条件"},
                    "mortality": {"type": "string", "description": "死亡情况"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "request_confirmation",
            "description": "当信息收集完整度足够时，请求用户确认保存病历",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "病历摘要，用于展示给用户确认"},
                    "missing_fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "尚未收集的重要字段",
                    },
                },
                "required": ["summary"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_diagnosis",
            "description": "根据已收集的症状推测可能的诊断",
            "parameters": {
                "type": "object",
                "properties": {
                    "possible_diagnoses": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "疾病名称"},
                                "confidence": {"type": "number", "description": "置信度 0-1"},
                                "reasoning": {"type": "string", "description": "推测依据"},
                            },
                            "required": ["name", "confidence"],
                        },
                        "description": "可能的诊断列表，按置信度排序",
                    },
                    "recommended_tests": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "建议的检测项目",
                    },
                },
                "required": ["possible_diagnoses"],
            },
        },
    },
]


INITIAL_MESSAGE = (
    "您好！我是禽病病历录入助手。我将帮助您通过对话方式创建一份完整的禽病病历。\n\n"
    "请先告诉我基本情况：\n"
    "1. 是什么禽类？（鸡、鸭、鹅等）\n"
    "2. 主要出了什么问题？\n\n"
    "您可以用自然语言描述，我会帮您整理成标准病历格式。"
)


# ---- 核心服务函数 ----


async def create_conversation(
    db: AsyncSession,
    user: User,
    record_id: uuid.UUID | None = None,
    farm_id: uuid.UUID | None = None,
    tags: list[str] | None = None,
) -> tuple[Conversation, ConversationMessage]:
    """创建对话会话，返回对话及初始引导消息"""
    # 如果有 record_id 但没有 farm_id，从 record 继承
    if record_id and not farm_id:
        from app.models.medical_record import MedicalRecord
        rec_result = await db.execute(
            select(MedicalRecord).where(MedicalRecord.id == record_id)
        )
        rec = rec_result.scalar_one_or_none()
        if rec and rec.farm_id:
            farm_id = rec.farm_id

    # 计算 session_number: 该用户对同一病历的第几次对话
    session_number = 1
    if record_id:
        count_result = await db.execute(
            select(func.count()).where(
                Conversation.user_id == user.id,
                Conversation.record_id == record_id,
            )
        )
        session_number = (count_result.scalar() or 0) + 1

    conversation = Conversation(
        user_id=user.id,
        record_id=record_id,
        farm_id=farm_id,
        session_number=session_number,
        status="active",
        state="initializing",
        collected_info={},
        confidence_scores={},
        tags=tags or [],
    )
    db.add(conversation)
    await db.flush()

    # 加载用户记忆上下文
    memory_context = await memory_service.build_memory_context(db, user.id)
    greeting_text = INITIAL_MESSAGE
    if memory_context:
        greeting_text = (
            f"（已加载您的历史记忆，Session #{session_number}）\n\n"
            + INITIAL_MESSAGE
        )

    # 发送初始引导消息
    greeting = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=greeting_text,
    )
    db.add(greeting)
    await db.flush()

    conversation.state = "collecting_basic"
    await db.flush()
    await db.refresh(conversation)
    await db.refresh(greeting)

    return conversation, greeting


async def send_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user: User,
    content: str,
    audio_url: str | None = None,
) -> dict:
    """接收用户消息，调用 LLM，返回 AI 回复及更新后的收集信息"""
    conversation = await _get_conversation_or_404(db, conversation_id, user.id)

    if conversation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已结束或暂停，无法发送消息",
        )

    # 保存用户消息
    user_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="user",
        content=content,
        audio_url=audio_url,
    )
    db.add(user_msg)
    await db.flush()

    # 获取 LLM 适配器和模型信息
    adapter, ai_model = await _get_adapter_and_model(db)

    # 检查使用限额
    allowed = await ai_model_service.check_usage_limit(db, ai_model.id, user.id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日 AI 使用额度已耗尽",
        )

    # 构建消息历史
    messages = await _build_messages(db, conversation, user)

    # 调用 LLM
    try:
        response = await adapter.chat_completion(messages)
    except Exception as e:
        logger.error("LLM 调用失败: %s", e)
        # 记录失败日志
        await ai_model_service.log_usage(
            db, model_id=ai_model.id, user_id=user.id,
            status_val="error", error_message=str(e),
            conversation_id=conversation.id,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI 服务调用失败，请稍后重试",
        )

    # 记录使用日志
    await ai_model_service.log_usage(
        db, model_id=ai_model.id, user_id=user.id,
        request_tokens=response.input_tokens,
        response_tokens=response.output_tokens,
        total_tokens=response.total_tokens,
        cost=response.cost,
        latency_ms=response.latency_ms,
        conversation_id=conversation.id,
    )

    # 解析 LLM 返回的 JSON
    parsed = _parse_llm_response(response.content)

    # 更新已收集信息
    if parsed.get("extracted_info"):
        collected = dict(conversation.collected_info)
        collected.update(parsed["extracted_info"])
        conversation.collected_info = collected

    if parsed.get("confidence_scores"):
        scores = dict(conversation.confidence_scores)
        scores.update(parsed["confidence_scores"])
        conversation.confidence_scores = scores

    # 更新对话状态
    suggested_state = parsed.get("suggested_state")
    if suggested_state and suggested_state in (
        "collecting_basic", "collecting_symptoms", "collecting_diagnosis",
        "collecting_treatment", "confirming",
    ):
        conversation.state = suggested_state

    # 保存 AI 回复消息
    reply_text = parsed.get("reply", response.content)
    assistant_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        extracted_info=parsed.get("extracted_info"),
        confidence_scores=parsed.get("confidence_scores"),
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)
    await db.refresh(conversation)

    # 检索相似病例（异步，失败不影响主流程）
    similar_cases = await _search_similar_cases(
        db, conversation.collected_info, user,
        exclude_record_id=conversation.record_id,
    )

    # 异步更新摘要（失败不影响主流程）
    try:
        from app.services import summary_service
        await summary_service.update_summary_if_needed(db, conversation.id)
    except Exception as e:
        logger.warning("摘要更新失败: %s", e)

    return {
        "message": assistant_msg,
        "collected_info": conversation.collected_info,
        "confidence_scores": conversation.confidence_scores,
        "needs_confirmation": parsed.get("needs_confirmation", []),
        "completeness": parsed.get("completeness", {}),
        "similar_cases": similar_cases,
    }


async def complete_conversation(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user: User,
    confirmed: bool,
    corrections: dict | None = None,
) -> dict:
    """确认完成对话，将收集的信息转换为病历并保存"""
    conversation = await _get_conversation_or_404(db, conversation_id, user.id)

    if conversation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已结束",
        )

    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请确认保存病历",
        )

    # 合并修正信息
    collected = dict(conversation.collected_info)
    if corrections:
        collected.update(corrections)

    # 构建 record_json
    record_json = _build_record_json(collected)

    # 提取必要字段
    poultry_type = collected.get("poultry_type", "未知")
    visit_date_str = collected.get("visit_date")
    try:
        visit_date = date.fromisoformat(visit_date_str) if visit_date_str else date.today()
    except (ValueError, TypeError):
        visit_date = date.today()

    if conversation.record_id:
        # 更新已有病历
        from app.schemas.record import RecordUpdate
        update_data = RecordUpdate(
            record_json=record_json,
            poultry_type=poultry_type,
            visit_date=visit_date,
            breed=collected.get("breed"),
            age_days=collected.get("age_days"),
            affected_count=collected.get("affected_count"),
            total_flock=collected.get("total_flock"),
            primary_diagnosis=collected.get("primary_diagnosis"),
            severity=collected.get("severity"),
        )
        record = await record_service.update_record(
            db, conversation.record_id, update_data, user
        )
    else:
        # 创建新病历
        create_data = RecordCreate(
            visit_date=visit_date,
            poultry_type=poultry_type,
            breed=collected.get("breed"),
            age_days=collected.get("age_days"),
            affected_count=collected.get("affected_count"),
            total_flock=collected.get("total_flock"),
            onset_date=_parse_date(collected.get("onset_date")),
            record_json=record_json,
        )
        record = await record_service.create_record(db, user, create_data)
        conversation.record_id = record.id

    # 将 farm_id 传播到 record（若 record 没有 farm_id）
    if conversation.farm_id and record.farm_id is None:
        record.farm_id = conversation.farm_id
        await db.flush()

    # 标记对话完成
    conversation.status = "completed"
    conversation.state = "completed"
    conversation.collected_info = collected

    # 添加完成系统消息
    sys_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="system",
        content=f"病历已保存，编号: {record.record_no}",
    )
    db.add(sys_msg)
    await db.flush()
    await db.refresh(conversation)

    # 触发提醒生成
    try:
        await reminder_service.generate_reminders(db, record.id, user.id)
    except Exception as e:
        logger.warning("提醒生成失败: %s", e)

    # 触发记忆更新
    try:
        msg_result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation.id)
            .order_by(ConversationMessage.created_at.asc())
        )
        msg_dicts = [
            {"role": m.role, "content": m.content}
            for m in msg_result.scalars().all()
        ]
        await memory_service.extract_memory_updates(db, user.id, msg_dicts)
    except Exception as e:
        logger.warning("记忆更新失败: %s", e)

    return {
        "conversation": conversation,
        "record_id": record.id,
        "record_no": record.record_no,
    }


async def get_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    """获取对话详情（含 farm、record 关联）"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.record), selectinload(Conversation.farm))
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )
    if conversation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此对话",
        )
    return conversation


async def update_tags(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID, tags: list[str]
) -> Conversation:
    """更新对话标签"""
    conversation = await _get_conversation_or_404(db, conversation_id, user_id)
    conversation.tags = tags
    await db.flush()
    await db.refresh(conversation)
    return conversation


async def list_conversations(
    db: AsyncSession,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    farm_id: uuid.UUID | None = None,
    tag: str | None = None,
) -> tuple[list[Conversation], int]:
    """获取用户的对话列表"""
    query = select(Conversation).where(Conversation.user_id == user.id)

    if status_filter:
        query = query.where(Conversation.status == status_filter)
    if farm_id:
        query = query.where(Conversation.farm_id == farm_id)
    if tag:
        query = query.where(Conversation.tags.contains([tag]))

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = (
        query.options(selectinload(Conversation.record), selectinload(Conversation.farm))
        .order_by(Conversation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    conversations = list(result.scalars().all())

    return conversations, total


async def get_messages(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[ConversationMessage], int]:
    """获取对话消息历史"""
    # 验证归属
    await _get_conversation_or_404(db, conversation_id, user_id)

    query = select(ConversationMessage).where(
        ConversationMessage.conversation_id == conversation_id
    )

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(ConversationMessage.created_at.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    messages = list(result.scalars().all())

    return messages, total


async def pause_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    """暂停对话（并生成摘要用于后续续聊）"""
    conversation = await _get_conversation_or_404(db, conversation_id, user_id)
    if conversation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能暂停进行中的对话",
        )
    conversation.status = "paused"

    # 暂停时强制生成 / 更新摘要
    try:
        from app.services import summary_service
        await summary_service.update_summary_if_needed(db, conversation.id, force=True)
    except Exception as e:
        logger.warning("暂停时摘要生成失败: %s", e)

    await db.flush()
    await db.refresh(conversation)
    return conversation


async def resume_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    """恢复对话（摘要已注入到 _build_messages 的 system prompt 中）"""
    conversation = await _get_conversation_or_404(db, conversation_id, user_id)
    if conversation.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只能恢复已暂停的对话",
        )
    conversation.status = "active"

    # 添加续聊系统消息
    if conversation.summary:
        resume_msg = ConversationMessage(
            conversation_id=conversation.id,
            role="system",
            content=f"对话已恢复。上次摘要：{conversation.summary}",
        )
        db.add(resume_msg)

    await db.flush()
    await db.refresh(conversation)
    return conversation


# ---- WebSocket 流式调用 ----


async def send_message_stream(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    user: User,
    content: str,
    audio_url: str | None = None,
):
    """流式发送消息，yield 逐 token 片段，最后 yield 完整解析结果"""
    conversation = await _get_conversation_or_404(db, conversation_id, user.id)

    if conversation.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="对话已结束或暂停",
        )

    # 保存用户消息
    user_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="user",
        content=content,
        audio_url=audio_url,
    )
    db.add(user_msg)
    await db.flush()

    adapter, ai_model = await _get_adapter_and_model(db)

    allowed = await ai_model_service.check_usage_limit(db, ai_model.id, user.id)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日 AI 使用额度已耗尽",
        )

    messages = await _build_messages(db, conversation, user)

    # 流式调用
    full_content = ""
    try:
        async for token in adapter.chat_completion_stream(messages):
            full_content += token
            yield {"type": "stream_token", "content": token}
    except Exception as e:
        logger.error("LLM 流式调用失败: %s", e)
        await ai_model_service.log_usage(
            db, model_id=ai_model.id, user_id=user.id,
            status_val="error", error_message=str(e),
            conversation_id=conversation.id,
        )
        yield {"type": "error", "error": "AI 服务调用失败，请稍后重试"}
        return

    # 记录使用（流式模式无法精确统计 token，仅记录调用）
    await ai_model_service.log_usage(
        db, model_id=ai_model.id, user_id=user.id,
        conversation_id=conversation.id,
    )

    # 解析完整响应
    parsed = _parse_llm_response(full_content)

    if parsed.get("extracted_info"):
        collected = dict(conversation.collected_info)
        collected.update(parsed["extracted_info"])
        conversation.collected_info = collected

    if parsed.get("confidence_scores"):
        scores = dict(conversation.confidence_scores)
        scores.update(parsed["confidence_scores"])
        conversation.confidence_scores = scores

    suggested_state = parsed.get("suggested_state")
    if suggested_state and suggested_state in (
        "collecting_basic", "collecting_symptoms", "collecting_diagnosis",
        "collecting_treatment", "confirming",
    ):
        conversation.state = suggested_state

    reply_text = parsed.get("reply", full_content)
    assistant_msg = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=reply_text,
        extracted_info=parsed.get("extracted_info"),
        confidence_scores=parsed.get("confidence_scores"),
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(conversation)

    # 检索相似病例
    similar_cases = await _search_similar_cases(
        db, conversation.collected_info, user,
        exclude_record_id=conversation.record_id,
    )

    # 异步更新摘要
    try:
        from app.services import summary_service
        await summary_service.update_summary_if_needed(db, conversation.id)
    except Exception as e:
        logger.warning("流式摘要更新失败: %s", e)

    yield {
        "type": "stream_end",
        "content": reply_text,
        "collected_info": conversation.collected_info,
        "confidence_scores": conversation.confidence_scores,
        "needs_confirmation": parsed.get("needs_confirmation", []),
        "completeness": parsed.get("completeness", {}),
        "similar_cases": similar_cases,
    }


# ---- 内部辅助函数 ----


async def _get_conversation_or_404(
    db: AsyncSession, conversation_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    """获取对话，验证归属"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="对话不存在",
        )
    if conversation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此对话",
        )
    return conversation


async def _get_adapter_and_model(db: AsyncSession):
    """获取默认 LLM 适配器及其模型 ORM 对象"""
    result = await db.execute(
        select(AIModel).where(AIModel.is_default == True, AIModel.is_active == True)
    )
    ai_model = result.scalar_one_or_none()
    if not ai_model:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="未配置默认 AI 模型",
        )

    api_key = decrypt_api_key(ai_model.api_key_encrypted)
    adapter = LLMAdapterFactory.create_adapter(
        provider=ai_model.provider,
        api_key=api_key,
        model_name=ai_model.model_name,
        api_endpoint=ai_model.api_endpoint,
        config=ai_model.config,
    )
    return adapter, ai_model


async def _build_messages(
    db: AsyncSession, conversation: Conversation, user: User | None = None
) -> list[ChatMessage]:
    """构建发送给 LLM 的消息列表：system prompt + 记忆 + 相似病例 + 收集状态 + 最近 N 条历史"""
    # 注入用户记忆到 system prompt
    memory_context = await memory_service.build_memory_context(db, conversation.user_id)
    system_content = SYSTEM_PROMPT
    if memory_context:
        system_content += f"\n\n{memory_context}"

    messages = [ChatMessage(role="system", content=system_content)]

    # 注入相似病例参考（如果有收集到信息）
    if conversation.collected_info:
        is_master = user.role == "master" if user else False
        similar_context = await _build_similar_cases_context(
            db, conversation.collected_info, conversation.user_id,
            is_master=is_master,
            exclude_record_id=conversation.record_id,
        )
        if similar_context:
            messages.append(ChatMessage(role="system", content=similar_context))

    # 注入摘要（续聊上下文，帮助 LLM 快速理解之前的对话）
    if conversation.summary:
        messages.append(ChatMessage(
            role="system",
            content=f"对话摘要：{conversation.summary}",
        ))

    # 注入当前收集状态到 system 消息
    if conversation.collected_info:
        state_summary = (
            f"\n\n当前已收集的信息：\n```json\n"
            f"{json.dumps(conversation.collected_info, ensure_ascii=False, indent=2)}\n"
            f"```\n当前对话阶段: {conversation.state}"
        )
        messages.append(ChatMessage(role="system", content=state_summary))

    # 获取最近的消息历史
    result = await db.execute(
        select(ConversationMessage)
        .where(
            ConversationMessage.conversation_id == conversation.id,
            ConversationMessage.role.in_(["user", "assistant"]),
        )
        .order_by(ConversationMessage.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
    )
    history = list(reversed(result.scalars().all()))

    for msg in history:
        messages.append(ChatMessage(role=msg.role, content=msg.content))

    return messages


async def _search_similar_cases(
    db: AsyncSession,
    collected_info: dict,
    user: User,
    exclude_record_id: uuid.UUID | None = None,
) -> list[dict]:
    """检索相似病例，异常时返回空列表"""
    if not collected_info:
        return []
    try:
        from app.services.embedding_service import search_similar_by_collected_info
        results = await search_similar_by_collected_info(
            db, collected_info,
            user_id=user.id,
            is_master=(user.role == "master"),
            top_k=3,
            exclude_record_id=exclude_record_id,
        )
        # 返回前端友好的精简格式
        return [
            {
                "id": r["id"],
                "record_no": r["record_no"],
                "poultry_type": r["poultry_type"],
                "primary_diagnosis": r.get("primary_diagnosis"),
                "severity": r.get("severity"),
                "similarity": r["similarity"],
            }
            for r in results
        ]
    except Exception as e:
        logger.warning("相似病例检索失败: %s", e)
        return []


async def _build_similar_cases_context(
    db: AsyncSession,
    collected_info: dict,
    user_id: uuid.UUID,
    is_master: bool = False,
    exclude_record_id: uuid.UUID | None = None,
) -> str:
    """构建注入给 LLM 的相似病例参考上下文"""
    try:
        from app.services.embedding_service import search_similar_by_collected_info

        cases = await search_similar_by_collected_info(
            db, collected_info,
            user_id=user_id,
            is_master=is_master,
            top_k=3,
            exclude_record_id=exclude_record_id,
        )
        if not cases:
            return ""

        lines = ["## 相似历史病例参考（仅供辅助诊断参考）\n"]
        for i, c in enumerate(cases, 1):
            lines.append(f"### 病例 {i}（相似度 {c['similarity']:.0%}）")
            lines.append(f"- 编号: {c['record_no']}")
            lines.append(f"- 禽类: {c['poultry_type']}")
            if c.get("primary_diagnosis"):
                lines.append(f"- 诊断: {c['primary_diagnosis']}")
            if c.get("severity"):
                lines.append(f"- 严重程度: {c['severity']}")
            # 提取症状和治疗
            rj = c.get("record_json", {})
            if rj.get("symptoms"):
                symptoms = rj["symptoms"]
                if isinstance(symptoms, list):
                    lines.append(f"- 症状: {', '.join(str(s) for s in symptoms)}")
                else:
                    lines.append(f"- 症状: {symptoms}")
            if rj.get("treatment"):
                t = rj["treatment"]
                if isinstance(t, dict):
                    t_str = " ".join(str(v) for v in t.values() if v)
                    lines.append(f"- 治疗: {t_str}")
                else:
                    lines.append(f"- 治疗: {t}")
            lines.append("")

        return "\n".join(lines)
    except Exception as e:
        logger.warning("构建相似病例上下文失败: %s", e)
        return ""


def _parse_llm_response(content: str) -> dict:
    """解析 LLM 返回的 JSON，容错处理"""
    # 尝试直接解析
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # 尝试提取 JSON 块（```json ... ```）
    import re
    json_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试找 { ... } 块
    brace_match = re.search(r"\{.*\}", content, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # 无法解析，返回原始内容作为回复
    logger.warning("无法解析 LLM JSON 响应，使用原始内容")
    return {"reply": content}


def _build_record_json(collected: dict) -> dict:
    """将收集的信息组织为标准 record_json 格式"""
    record_json = {}

    # 基本信息
    basic_info = {}
    for key in ("poultry_type", "breed", "age_days", "affected_count",
                "total_flock", "farm_info", "feed_info"):
        if key in collected:
            basic_info[key] = collected[key]
    if basic_info:
        record_json["basic_info"] = basic_info

    # 拷贝顶级字段
    for key in ("poultry_type", "breed", "age_days", "affected_count",
                "total_flock", "onset_date", "visit_date"):
        if key in collected:
            record_json[key] = collected[key]

    # 症状
    if "symptoms" in collected:
        record_json["symptoms"] = collected["symptoms"]

    # 诊断
    if "primary_diagnosis" in collected:
        record_json["primary_diagnosis"] = collected["primary_diagnosis"]
    if "severity" in collected:
        record_json["severity"] = collected["severity"]
    if "icd_code" in collected:
        record_json["icd_code"] = collected["icd_code"]

    # 治疗
    if "treatment" in collected:
        record_json["treatment"] = collected["treatment"]

    # 其他
    for key in ("environment", "vaccination_history", "mortality",
                "lab_tests", "notes"):
        if key in collected:
            record_json[key] = collected[key]

    return record_json


def _parse_date(value) -> date | None:
    """安全解析日期"""
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None
