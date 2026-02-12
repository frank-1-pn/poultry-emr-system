"""对话摘要服务 — 自动生成 / 更新对话摘要"""

import json
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import ChatMessage
from app.adapters.factory import LLMAdapterFactory
from app.models.ai_model import AIModel
from app.models.conversation import Conversation, ConversationMessage
from app.utils.encryption import decrypt_api_key

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """请为以下禽类兽医对话生成一段简洁的中文摘要（50-100字）。
摘要应包含：禽类类型、主要症状、当前诊断进展、治疗方案（如有）。
不要使用 JSON 格式，直接输出纯文本摘要。

对话内容：
{messages}

已收集信息：
{collected_info}

请直接输出摘要文本："""


async def generate_summary(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> str | None:
    """为对话生成摘要"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return None

    # 获取最近消息
    msg_result = await db.execute(
        select(ConversationMessage)
        .where(
            ConversationMessage.conversation_id == conversation_id,
            ConversationMessage.role.in_(["user", "assistant"]),
        )
        .order_by(ConversationMessage.created_at.desc())
        .limit(10)
    )
    messages = list(reversed(msg_result.scalars().all()))

    if not messages:
        return None

    # 构建消息文本
    msg_text = "\n".join(
        f"{'用户' if m.role == 'user' else 'AI'}: {m.content[:200]}"
        for m in messages
    )
    collected_text = json.dumps(
        conversation.collected_info, ensure_ascii=False, indent=2
    ) if conversation.collected_info else "{}"

    prompt = SUMMARY_PROMPT.format(
        messages=msg_text,
        collected_info=collected_text,
    )

    try:
        # 获取 LLM 适配器
        model_result = await db.execute(
            select(AIModel).where(AIModel.is_default == True, AIModel.is_active == True)
        )
        ai_model = model_result.scalar_one_or_none()
        if not ai_model:
            return _fallback_summary(conversation)

        api_key = decrypt_api_key(ai_model.api_key_encrypted)
        adapter = LLMAdapterFactory.create_adapter(
            provider=ai_model.provider,
            api_key=api_key,
            model_name=ai_model.model_name,
            api_endpoint=ai_model.api_endpoint,
            config=ai_model.config,
        )

        response = await adapter.chat_completion([
            ChatMessage(role="user", content=prompt)
        ])
        summary = response.content.strip()

        # 更新到数据库
        conversation.summary = summary
        await db.flush()

        return summary
    except Exception as e:
        logger.warning("生成摘要失败，使用降级摘要: %s", e)
        return _fallback_summary(conversation)


def _fallback_summary(conversation: Conversation) -> str:
    """降级摘要：从 collected_info 提取关键信息"""
    info = conversation.collected_info or {}
    parts = []

    if info.get("poultry_type"):
        parts.append(info["poultry_type"])
    if info.get("breed"):
        parts.append(info["breed"])

    symptoms = info.get("symptoms")
    if symptoms:
        if isinstance(symptoms, list):
            parts.append(f"症状: {', '.join(str(s) for s in symptoms[:3])}")
        else:
            parts.append(f"症状: {str(symptoms)[:50]}")

    if info.get("primary_diagnosis"):
        parts.append(f"诊断: {info['primary_diagnosis']}")

    if not parts:
        return f"对话中，阶段: {conversation.state}"

    summary = "；".join(parts)
    conversation.summary = summary
    return summary


async def update_summary_if_needed(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    force: bool = False,
) -> str | None:
    """在 send_message 后调用，决定是否需要更新摘要"""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        return None

    # 消息数检查：每隔 4 条消息或强制时更新
    msg_count_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
    )
    msg_count = len(list(msg_count_result.scalars().all()))

    if not force and conversation.summary and msg_count % 4 != 0:
        return conversation.summary

    return await generate_summary(db, conversation_id)
