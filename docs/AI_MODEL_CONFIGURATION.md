# AI模型配置系统设计

## 概述
系统支持多种AI大模型接入，由Master管理员统一配置和管理。

**核心特性**：
- ✅ 支持多种AI模型（通义千问、MiniMax、OpenAI、Claude等）
- ✅ Master后台可配置和切换模型
- ✅ **模型热切换**：切换模型不影响对话历史和记忆
- ✅ 对话历史与模型解耦，支持跨模型延续对话

## 支持的AI模型

### 优先支持（国产模型）

#### 1. 通义千问 (阿里云) - 推荐 ⭐
**优势**：
- 中文理解能力强，特别适合医疗领域
- 与阿里云生态集成良好（OSS、语音识别等）
- 性价比高
- 国内访问稳定，低延迟

**模型选择**：
- `qwen-max`: 最强能力，适合复杂病历分析
- `qwen-plus`: 平衡性能和成本
- `qwen-turbo`: 快速响应，适合简单对话

**API文档**: https://help.aliyun.com/zh/dashscope/

#### 2. MiniMax - 推荐 ⭐
**优势**：
- 国产大模型，中文能力优秀
- 支持长上下文
- 价格合理
- API稳定

**模型选择**：
- `abab6-chat`: 综合能力强
- `abab5.5-chat`: 性价比版本

**API文档**: https://api.minimax.chat/

### 国际模型（完整支持）

#### 3. OpenAI GPT ⭐
**优势**：
- 综合能力最强，多模态支持
- 全球最成熟的API生态
- Function Calling支持完善
- 文档和社区资源丰富

**模型选择**：
- `gpt-4o`: 最新旗舰，多模态，速度快
- `gpt-4-turbo`: 128K上下文，性能强大
- `gpt-4`: 经典版本，稳定可靠
- `gpt-3.5-turbo`: 成本优化，适合简单任务

**API配置**：
```python
OPENAI_CONFIG = {
    "api_key": "sk-xxxxxxxxxx",
    "base_url": "https://api.openai.com/v1",  # 可替换为代理
    "model": "gpt-4o",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 30
}
```

**API文档**: https://platform.openai.com/docs/

#### 4. Anthropic Claude ⭐
**优势**：
- 逻辑推理能力强
- 长上下文支持（200K tokens）
- 安全性和可控性好
- 中文理解能力优秀

**模型选择**：
- `claude-3-opus`: 最强能力，复杂任务首选
- `claude-3-sonnet`: 平衡选择，日常使用
- `claude-3-haiku`: 快速响应，简单任务

**API配置**：
```python
CLAUDE_CONFIG = {
    "api_key": "sk-ant-xxxxxxxxxx",
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.7,
    "max_tokens": 4096,
    "timeout": 30
}
```

**API文档**: https://docs.anthropic.com/

#### 5. Kimi (月之暗面 Moonshot) ⭐
**优势**：
- 超长上下文支持（200K tokens）
- 中文理解能力优秀
- 国产模型，访问稳定
- API兼容OpenAI格式

**模型选择**：
- `moonshot-v1-8k`: 8K上下文，速度快
- `moonshot-v1-32k`: 32K上下文，平衡
- `moonshot-v1-128k`: 128K上下文，长文档

**API配置**：
```python
KIMI_CONFIG = {
    "api_key": "sk-xxxxxxxxxx",
    "base_url": "https://api.moonshot.cn/v1",
    "model": "moonshot-v1-32k",
    "temperature": 0.7,
    "max_tokens": 4096
}
```

**API文档**: https://platform.moonshot.cn/docs/

#### 6. 腾讯元宝/混元 ⭐
**优势**：
- 腾讯生态集成（微信小程序友好）
- 中文能力强
- 支持图像理解
- 企业级服务稳定

**模型选择**：
- `hunyuan-lite`: 轻量版，速度快
- `hunyuan-standard`: 标准版，平衡
- `hunyuan-pro`: 专业版，能力最强

**API配置**：
```python
HUNYUAN_CONFIG = {
    "secret_id": "AKIDxxxxxxxxxx",
    "secret_key": "xxxxxxxxxx",
    "region": "ap-guangzhou",
    "model": "hunyuan-standard",
    "temperature": 0.7,
    "max_tokens": 4096
}
```

**API文档**: https://cloud.tencent.com/document/product/1729

#### 7. Google Gemini
**优势**：
- 多模态能力强（图像、视频理解）
- 推理能力优秀
- 支持长上下文

**模型选择**：
- `gemini-1.5-pro`: 最强能力，100万tokens上下文
- `gemini-1.5-flash`: 快速响应
- `gemini-1.0-pro`: 经典版本

**API配置**：
```python
GEMINI_CONFIG = {
    "api_key": "AIzaxxxxxxxxxx",
    "model": "gemini-1.5-pro",
    "temperature": 0.7,
    "max_tokens": 4096
}
```

**API文档**: https://ai.google.dev/docs

#### 8. DeepSeek
**优势**：
- 国产开源模型，成本极低
- 支持自部署
- API兼容OpenAI格式

**模型选择**：
- `deepseek-chat`: 对话模型
- `deepseek-coder`: 代码专用

**API配置**：
```python
DEEPSEEK_CONFIG = {
    "api_key": "sk-xxxxxxxxxx",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "temperature": 0.7,
    "max_tokens": 4096
}
```

## 模型能力对比

| 模型 | 中文能力 | 推理能力 | 上下文 | 成本 | 延迟 | 推荐场景 |
|------|---------|---------|--------|------|------|---------|
| 通义千问-Max | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 32K | 低 | 低 | 日常使用 |
| MiniMax | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 200K | 低 | 低 | 长对话 |
| **Kimi** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | **200K** | 低 | 低 | 超长上下文 |
| **腾讯混元** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 32K | 低 | 低 | 微信生态 |
| GPT-4o | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 128K | 高 | 中 | 复杂分析 |
| Claude-3-Sonnet | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 200K | 中 | 中 | 逻辑推理 |
| **Gemini-1.5-Pro** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **1M** | 中 | 中 | 多模态 |
| DeepSeek | ⭐⭐⭐⭐ | ⭐⭐⭐ | 32K | 极低 | 低 | 成本敏感 |

### 国产模型推荐排序（综合考虑中文能力、稳定性、成本）
1. **通义千问** - 阿里云生态，最稳定
2. **Kimi** - 超长上下文，适合复杂病历
3. **腾讯混元** - 微信小程序原生支持
4. **MiniMax** - 性价比高
5. **DeepSeek** - 成本最低

## 模型热切换与对话保留 🔥

### 核心设计原则

**对话历史与模型完全解耦**：
- 对话历史存储在 `conversations` 和 `conversation_messages` 表
- 模型配置存储在 `ai_models` 表
- 切换模型只改变"使用哪个模型回复"，不影响已有对话

```
┌─────────────────────────────────────────────────────────┐
│                    对话历史（持久化）                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 消息1: 用户 - "阳光养殖场的鸡咳嗽..."            │   │
│  │ 消息2: AI(通义) - "好的，我记录了..."           │   │
│  │ 消息3: 用户 - "大概200只"                       │   │
│  │ 消息4: AI(通义) - "请问是什么品种？"            │   │
│  │ ─────────── 此时Master切换到GPT-4 ───────────  │   │
│  │ 消息5: 用户 - "白羽肉鸡"                        │   │
│  │ 消息6: AI(GPT-4) - "明白了，35日龄的白羽..."    │   │
│  │ ─────────── 此时Master切换到Claude ───────────  │   │
│  │ 消息7: 用户 - "还有呼吸困难"                    │   │
│  │ 消息8: AI(Claude) - "综合症状来看..."           │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ✅ 所有消息都保留                                      │
│  ✅ 新模型能看到完整上下文                               │
│  ✅ 提取的信息持续累积                                   │
└─────────────────────────────────────────────────────────┘
```

### 架构设计

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   前端小程序  │────▶│   后端API    │────▶│  AI适配器层   │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
       对话历史                          ┌────────┼────────┐
    ┌──────────┐                        ▼        ▼        ▼
    │ messages │◀───────────────   ┌────────┐┌────────┐┌────────┐
    │  表      │                   │ 通义   ││ GPT-4  ││ Claude │
    └──────────┘                   │ 千问   ││        ││        │
                                   └────────┘└────────┘└────────┘
    提取的信息                              │
    ┌──────────┐                           │
    │ context  │◀──────────────────────────┘
    │  JSONB   │   每次回复都更新累积信息
    └──────────┘
```

### 关键实现

#### 1. 对话消息存储（模型无关）
```sql
-- conversation_messages 表
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR(20) NOT NULL,        -- user / assistant
    content TEXT NOT NULL,
    audio_url TEXT,                   -- 语音文件URL
    model_used VARCHAR(100),          -- 记录使用的模型（仅供参考）
    extracted_info JSONB,             -- AI提取的信息
    confidence_scores JSONB,          -- 置信度
    timestamp TIMESTAMP NOT NULL
);
```

#### 2. 对话上下文累积（跨模型共享）
```sql
-- conversations 表的 context 字段
{
  "collected_info": {
    "farm_name": "阳光养殖场",
    "onset_date": "2026-01-15",
    "poultry_type": "鸡",
    "breed": "白羽肉鸡",
    "affected_count": 200,
    "symptoms": ["咳嗽", "呼吸困难"]
  },
  "pending_questions": ["日龄", "总群数量"],
  "confidence": {
    "farm_name": 0.98,
    "onset_date": 0.95,
    "symptoms": 0.99
  }
}
```

#### 3. 模型切换不影响对话
```python
class ConversationService:
    async def send_message(
        self,
        conversation_id: UUID,
        user_message: str,
        audio_url: str = None
    ) -> dict:
        """发送消息并获取AI回复"""

        # 1. 获取对话历史（所有历史消息）
        conversation = await self.get_conversation(conversation_id)
        message_history = await self.get_messages(conversation_id)

        # 2. 获取当前默认模型（可能已被Master切换）
        current_model = await self.get_default_model()

        # 3. 构建上下文（包含所有历史，不管之前用的什么模型）
        messages = self._build_context(message_history, conversation.context)

        # 4. 添加用户新消息
        messages.append({"role": "user", "content": user_message})

        # 5. 调用当前模型
        adapter = LLMAdapterFactory.create_adapter(current_model)
        response = await adapter.chat_completion(messages)

        # 6. 保存用户消息
        await self.save_message(
            conversation_id=conversation_id,
            role="user",
            content=user_message,
            audio_url=audio_url,
            model_used=None  # 用户消息不记录模型
        )

        # 7. 保存AI回复（记录使用的模型）
        await self.save_message(
            conversation_id=conversation_id,
            role="assistant",
            content=response["content"],
            model_used=f"{current_model.provider}/{current_model.model_name}",
            extracted_info=response.get("extracted_info"),
            confidence_scores=response.get("confidence_scores")
        )

        # 8. 更新累积的上下文信息
        await self.update_context(conversation_id, response.get("extracted_info"))

        return response

    def _build_context(
        self,
        message_history: list,
        accumulated_context: dict
    ) -> list:
        """构建发送给AI的上下文"""

        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(accumulated_context)
            }
        ]

        # 添加所有历史消息（不管之前用的什么模型）
        for msg in message_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        return messages

    def _build_system_prompt(self, context: dict) -> str:
        """构建系统提示词，包含已收集的信息"""

        base_prompt = """你是一个专业的兽医助手，负责帮助兽医创建禽病电子病历。
请继续之前的对话，帮助兽医完善病历信息。"""

        if context and context.get("collected_info"):
            info = context["collected_info"]
            base_prompt += f"""

当前已收集的信息：
- 养殖场: {info.get('farm_name', '待收集')}
- 发病日期: {info.get('onset_date', '待收集')}
- 禽类: {info.get('poultry_type', '待收集')} {info.get('breed', '')}
- 患病数量: {info.get('affected_count', '待收集')}
- 症状: {', '.join(info.get('symptoms', [])) or '待收集'}

还需要收集: {', '.join(context.get('pending_questions', []))}
"""

        return base_prompt
```

### 模型切换场景

#### 场景1：Master在后台切换默认模型
```python
# Master操作：将默认模型从通义千问切换到GPT-4
@app.patch("/api/v1/admin/ai-models/{model_id}/set-default")
async def set_default_model(model_id: UUID, current_user: User):
    if current_user.role != "master":
        raise HTTPException(403, "只有Master可以切换模型")

    # 取消当前默认
    await db.execute(
        "UPDATE ai_models SET is_default = FALSE WHERE is_default = TRUE"
    )

    # 设置新默认
    await db.execute(
        "UPDATE ai_models SET is_default = TRUE WHERE id = :id",
        {"id": model_id}
    )

    # 记录切换日志
    await log_model_switch(model_id, current_user.id)

    return {"message": "默认模型已切换", "model_id": model_id}
```

#### 场景2：用户继续对话（无感切换）
```
用户视角：
1. 继续和AI对话
2. AI回复风格可能略有变化（不同模型特点）
3. 但之前说过的信息AI都记得
4. 病历信息继续累积

技术实现：
1. 用户发消息
2. 后端获取当前默认模型（已被Master切换）
3. 加载完整对话历史
4. 用新模型生成回复
5. 保存回复（标记使用的模型）
```

### 前端显示

#### 对话界面标记（可选）
```vue
<template>
  <view class="message" :class="msg.role">
    <view class="content">{{ msg.content }}</view>

    <!-- 可选：显示AI回复使用的模型 -->
    <view v-if="msg.role === 'assistant' && showModelTag" class="model-tag">
      {{ formatModelName(msg.model_used) }}
    </view>
  </view>
</template>

<script>
export default {
  methods: {
    formatModelName(model) {
      const names = {
        'qwen/qwen-plus': '通义千问',
        'openai/gpt-4o': 'GPT-4',
        'claude/claude-3-sonnet': 'Claude'
      }
      return names[model] || model
    }
  }
}
</script>

<style>
.model-tag {
  font-size: 10px;
  color: #999;
  margin-top: 4px;
}
</style>
```

#### 已收集信息面板
```vue
<template>
  <view class="collected-info-panel">
    <text class="title">已收集信息</text>

    <view class="info-item" v-for="(value, key) in collectedInfo">
      <text class="label">{{ labelMap[key] }}</text>
      <text class="value">{{ value || '待收集' }}</text>
      <view class="confidence" :style="{ width: confidence[key] * 100 + '%' }"/>
    </view>

    <view class="pending" v-if="pendingQuestions.length">
      <text>还需确认: {{ pendingQuestions.join('、') }}</text>
    </view>
  </view>
</template>
```

### 数据一致性保证

#### 1. 上下文原子更新
```python
async def update_context(conversation_id: UUID, new_info: dict):
    """原子更新对话上下文"""
    async with db.transaction():
        # 获取当前上下文
        conversation = await db.fetch_one(
            "SELECT context FROM conversations WHERE id = :id FOR UPDATE",
            {"id": conversation_id}
        )

        # 合并新信息
        context = conversation.context or {}
        collected = context.get("collected_info", {})

        for key, value in new_info.items():
            if value and (key not in collected or new_info.get(f"{key}_confidence", 0) >
                         context.get("confidence", {}).get(key, 0)):
                collected[key] = value

        context["collected_info"] = collected

        # 保存
        await db.execute(
            "UPDATE conversations SET context = :context WHERE id = :id",
            {"context": json.dumps(context), "id": conversation_id}
        )
```

#### 2. 消息顺序保证
```python
# 使用时间戳确保消息顺序
await self.save_message(
    conversation_id=conversation_id,
    role="assistant",
    content=response["content"],
    timestamp=datetime.utcnow()  # 精确时间戳
)
```

## 数据库设计

### ai_models 表（AI模型配置表）
```sql
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL,  -- qwen, minimax, openai, claude, deepseek
    model_name VARCHAR(100) NOT NULL,  -- qwen-max, abab6-chat, gpt-4o
    display_name VARCHAR(100) NOT NULL,  -- 显示名称
    api_endpoint TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,  -- 加密存储
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,  -- 默认模型
    config JSONB,  -- 模型特定配置
    usage_limit JSONB,  -- 使用限制
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_models_provider ON ai_models(provider);
CREATE INDEX idx_models_active ON ai_models(is_active);
CREATE INDEX idx_models_default ON ai_models(is_default) WHERE is_default = TRUE;
```

### ai_model_config 字段示例
```json
{
  "temperature": 0.7,
  "max_tokens": 2000,
  "top_p": 0.9,
  "frequency_penalty": 0,
  "presence_penalty": 0,
  "timeout_seconds": 30,
  "retry_attempts": 3,
  "supports_function_calling": true,
  "supports_streaming": true
}
```

### ai_usage_logs 表（AI使用日志）
```sql
CREATE TABLE ai_usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES ai_models(id),
    user_id UUID REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    request_tokens INTEGER,
    response_tokens INTEGER,
    total_tokens INTEGER,
    cost DECIMAL(10,4),  -- 成本（元）
    latency_ms INTEGER,  -- 响应延迟
    status VARCHAR(20),  -- success, error, timeout
    error_message TEXT,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_usage_model ON ai_usage_logs(model_id);
CREATE INDEX idx_usage_user ON ai_usage_logs(user_id);
CREATE INDEX idx_usage_date ON ai_usage_logs(created_at);
```

## 统一适配器设计

### LLM适配器接口
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, AsyncIterator

class BaseLLMAdapter(ABC):
    """AI模型适配器基类"""

    def __init__(self, api_key: str, api_endpoint: str, config: Dict):
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.config = config

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """聊天补全"""
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式聊天补全"""
        pass

    @abstractmethod
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        pass
```

### 通义千问适配器
```python
import dashscope
from dashscope import Generation

class QwenAdapter(BaseLLMAdapter):
    """通义千问适配器"""

    PRICING = {
        'qwen-max': {'input': 0.04, 'output': 0.12},  # 元/千tokens
        'qwen-plus': {'input': 0.008, 'output': 0.024},
        'qwen-turbo': {'input': 0.002, 'output': 0.006}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        super().__init__(api_key, '', config)
        self.model_name = model_name
        dashscope.api_key = api_key

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用通义千问API"""
        try:
            response = Generation.call(
                model=self.model_name,
                messages=messages,
                tools=self._convert_functions(functions) if functions else None,
                result_format='message',
                temperature=self.config.get('temperature', 0.7),
                top_p=self.config.get('top_p', 0.9),
                max_tokens=self.config.get('max_tokens', 2000)
            )

            if response.status_code == 200:
                return {
                    'content': response.output.choices[0].message.content,
                    'function_call': self._parse_function_call(response),
                    'usage': {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens,
                        'total_tokens': response.usage.total_tokens
                    }
                }
            else:
                raise Exception(f"API调用失败: {response.message}")

        except Exception as e:
            raise Exception(f"通义千问调用错误: {str(e)}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        responses = Generation.call(
            model=self.model_name,
            messages=messages,
            result_format='message',
            stream=True,
            incremental_output=True,
            temperature=self.config.get('temperature', 0.7)
        )

        for response in responses:
            if response.status_code == 200:
                yield response.output.choices[0].message.content

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['qwen-plus'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost

    def _convert_functions(self, functions: List[Dict]) -> List[Dict]:
        """转换函数定义为通义格式"""
        return [
            {
                'type': 'function',
                'function': func
            }
            for func in functions
        ]

    def _parse_function_call(self, response) -> Optional[Dict]:
        """解析函数调用"""
        choice = response.output.choices[0]
        if hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
            tool_call = choice.message.tool_calls[0]
            return {
                'name': tool_call.function.name,
                'arguments': tool_call.function.arguments
            }
        return None
```

### MiniMax适配器
```python
import httpx

class MiniMaxAdapter(BaseLLMAdapter):
    """MiniMax适配器"""

    PRICING = {
        'abab6-chat': {'input': 0.015, 'output': 0.015},  # 元/千tokens
        'abab5.5-chat': {'input': 0.005, 'output': 0.005}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        super().__init__(api_key, 'https://api.minimax.chat/v1/text/chatcompletion_v2', config)
        self.model_name = model_name
        self.group_id = config.get('group_id')

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用MiniMax API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model_name,
            'messages': messages,
            'temperature': self.config.get('temperature', 0.7),
            'top_p': self.config.get('top_p', 0.9),
            'max_tokens': self.config.get('max_tokens', 2000)
        }

        if functions:
            payload['functions'] = functions

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_endpoint}?GroupId={self.group_id}",
                headers=headers,
                json=payload,
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    'content': data['choices'][0]['message']['content'],
                    'function_call': data['choices'][0]['message'].get('function_call'),
                    'usage': {
                        'input_tokens': data['usage']['prompt_tokens'],
                        'output_tokens': data['usage']['completion_tokens'],
                        'total_tokens': data['usage']['total_tokens']
                    }
                }
            else:
                raise Exception(f"API调用失败: {response.text}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        # MiniMax流式实现
        # ...

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['abab6-chat'])
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * pricing['input']
```

### OpenAI适配器 ⭐
```python
from openai import AsyncOpenAI

class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI GPT适配器"""

    PRICING = {
        'gpt-4o': {'input': 0.005, 'output': 0.015},  # $/千tokens
        'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        super().__init__(api_key, config.get('base_url', 'https://api.openai.com/v1'), config)
        self.model_name = model_name
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.api_endpoint,
            timeout=config.get('timeout_seconds', 30)
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用OpenAI API"""
        try:
            kwargs = {
                'model': self.model_name,
                'messages': messages,
                'temperature': self.config.get('temperature', 0.7),
                'max_tokens': self.config.get('max_tokens', 2000),
                'top_p': self.config.get('top_p', 0.9)
            }

            # 添加Function Calling
            if functions:
                kwargs['tools'] = [
                    {'type': 'function', 'function': func}
                    for func in functions
                ]
                kwargs['tool_choice'] = 'auto'

            response = await self.client.chat.completions.create(**kwargs)

            result = {
                'content': response.choices[0].message.content,
                'usage': {
                    'input_tokens': response.usage.prompt_tokens,
                    'output_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

            # 解析Function Call
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                result['function_call'] = {
                    'name': tool_call.function.name,
                    'arguments': tool_call.function.arguments
                }

            return result

        except Exception as e:
            raise Exception(f"OpenAI调用错误: {str(e)}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.config.get('temperature', 0.7),
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本（美元转人民币，按7.2汇率）"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['gpt-4o'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return (input_cost + output_cost) * 7.2  # 转换为人民币
```

### Claude适配器 ⭐
```python
from anthropic import AsyncAnthropic

class ClaudeAdapter(BaseLLMAdapter):
    """Anthropic Claude适配器"""

    PRICING = {
        'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},  # $/千tokens
        'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
        'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        super().__init__(api_key, 'https://api.anthropic.com', config)
        self.model_name = model_name
        self.client = AsyncAnthropic(
            api_key=api_key,
            timeout=config.get('timeout_seconds', 30)
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用Claude API"""
        try:
            # 分离system消息（Claude要求system单独传）
            system_message = ""
            chat_messages = []

            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    chat_messages.append(msg)

            kwargs = {
                'model': self.model_name,
                'messages': chat_messages,
                'max_tokens': self.config.get('max_tokens', 2000),
                'temperature': self.config.get('temperature', 0.7)
            }

            if system_message:
                kwargs['system'] = system_message

            # 添加Tool Use（Claude的Function Calling）
            if functions:
                kwargs['tools'] = [
                    {
                        'name': func['name'],
                        'description': func.get('description', ''),
                        'input_schema': func.get('parameters', {})
                    }
                    for func in functions
                ]

            response = await self.client.messages.create(**kwargs)

            # 解析响应
            content = ""
            function_call = None

            for block in response.content:
                if block.type == 'text':
                    content = block.text
                elif block.type == 'tool_use':
                    function_call = {
                        'name': block.name,
                        'arguments': json.dumps(block.input)
                    }

            return {
                'content': content,
                'function_call': function_call,
                'usage': {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens
                }
            }

        except Exception as e:
            raise Exception(f"Claude调用错误: {str(e)}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        # 分离system消息
        system_message = ""
        chat_messages = []

        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                chat_messages.append(msg)

        kwargs = {
            'model': self.model_name,
            'messages': chat_messages,
            'max_tokens': self.config.get('max_tokens', 2000),
            'stream': True
        }

        if system_message:
            kwargs['system'] = system_message

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本（美元转人民币，按7.2汇率）"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['claude-3-sonnet-20240229'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return (input_cost + output_cost) * 7.2  # 转换为人民币
```

### Kimi适配器 (月之暗面) ⭐
```python
class KimiAdapter(BaseLLMAdapter):
    """Kimi/Moonshot适配器（兼容OpenAI格式）"""

    PRICING = {
        'moonshot-v1-8k': {'input': 0.012, 'output': 0.012},    # 元/千tokens
        'moonshot-v1-32k': {'input': 0.024, 'output': 0.024},
        'moonshot-v1-128k': {'input': 0.06, 'output': 0.06}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        super().__init__(api_key, 'https://api.moonshot.cn/v1', config)
        self.model_name = model_name
        # Kimi兼容OpenAI SDK
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.api_endpoint,
            timeout=config.get('timeout_seconds', 60)  # Kimi长上下文可能需要更长时间
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用Kimi API"""
        try:
            kwargs = {
                'model': self.model_name,
                'messages': messages,
                'temperature': self.config.get('temperature', 0.7),
                'max_tokens': self.config.get('max_tokens', 4096)
            }

            # Kimi支持Function Calling
            if functions:
                kwargs['tools'] = [
                    {'type': 'function', 'function': func}
                    for func in functions
                ]

            response = await self.client.chat.completions.create(**kwargs)

            result = {
                'content': response.choices[0].message.content,
                'usage': {
                    'input_tokens': response.usage.prompt_tokens,
                    'output_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                result['function_call'] = {
                    'name': tool_call.function.name,
                    'arguments': tool_call.function.arguments
                }

            return result

        except Exception as e:
            raise Exception(f"Kimi调用错误: {str(e)}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.config.get('temperature', 0.7),
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['moonshot-v1-32k'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost
```

### 腾讯混元适配器 ⭐
```python
import hashlib
import hmac
import json
from datetime import datetime

class HunyuanAdapter(BaseLLMAdapter):
    """腾讯混元适配器"""

    PRICING = {
        'hunyuan-lite': {'input': 0.008, 'output': 0.008},    # 元/千tokens
        'hunyuan-standard': {'input': 0.045, 'output': 0.045},
        'hunyuan-pro': {'input': 0.1, 'output': 0.1}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        # 腾讯云使用SecretId和SecretKey
        self.secret_id = config.get('secret_id')
        self.secret_key = api_key  # 这里api_key存储secret_key
        self.region = config.get('region', 'ap-guangzhou')
        self.model_name = model_name
        self.endpoint = 'hunyuan.tencentcloudapi.com'
        self.config = config

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用腾讯混元API"""
        try:
            # 构建请求
            action = 'ChatCompletions'
            payload = {
                'Model': self.model_name,
                'Messages': [
                    {'Role': msg['role'], 'Content': msg['content']}
                    for msg in messages
                ],
                'Temperature': self.config.get('temperature', 0.7),
                'TopP': self.config.get('top_p', 0.9)
            }

            # 签名和请求
            headers = self._build_headers(action, payload)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.endpoint}",
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )

                data = response.json()

                if 'Response' in data and 'Choices' in data['Response']:
                    choice = data['Response']['Choices'][0]
                    usage = data['Response'].get('Usage', {})

                    return {
                        'content': choice['Message']['Content'],
                        'usage': {
                            'input_tokens': usage.get('PromptTokens', 0),
                            'output_tokens': usage.get('CompletionTokens', 0),
                            'total_tokens': usage.get('TotalTokens', 0)
                        }
                    }
                else:
                    raise Exception(f"API返回错误: {data}")

        except Exception as e:
            raise Exception(f"腾讯混元调用错误: {str(e)}")

    def _build_headers(self, action: str, payload: dict) -> dict:
        """构建腾讯云API签名头"""
        timestamp = int(datetime.now().timestamp())
        date = datetime.utcnow().strftime('%Y-%m-%d')

        # 简化的签名逻辑，实际使用需要完整的TC3-HMAC-SHA256签名
        # 建议使用腾讯云SDK: tencentcloud-sdk-python
        return {
            'Content-Type': 'application/json',
            'X-TC-Action': action,
            'X-TC-Version': '2023-09-01',
            'X-TC-Timestamp': str(timestamp),
            'X-TC-Region': self.region,
            'Authorization': self._sign_request(action, payload, timestamp, date)
        }

    def _sign_request(self, action: str, payload: dict, timestamp: int, date: str) -> str:
        """TC3-HMAC-SHA256签名（简化版，生产环境建议用SDK）"""
        # 实际实现请参考腾讯云文档
        # https://cloud.tencent.com/document/api/1729/105701
        pass

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        # 腾讯混元支持SSE流式
        # 实现类似，设置Stream=True
        pass

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['hunyuan-standard'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost
```

**推荐：使用腾讯云官方SDK**
```python
# pip install tencentcloud-sdk-python
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models

class HunyuanSDKAdapter(BaseLLMAdapter):
    """腾讯混元适配器（使用官方SDK）"""

    def __init__(self, api_key: str, model_name: str, config: Dict):
        from tencentcloud.common import credential
        from tencentcloud.common.profile.client_profile import ClientProfile

        cred = credential.Credential(
            config.get('secret_id'),
            api_key  # secret_key
        )
        client_profile = ClientProfile()
        self.client = hunyuan_client.HunyuanClient(cred, config.get('region', 'ap-guangzhou'), client_profile)
        self.model_name = model_name
        self.config = config

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用混元API"""
        req = models.ChatCompletionsRequest()
        req.Model = self.model_name
        req.Messages = [
            models.Message(Role=msg['role'], Content=msg['content'])
            for msg in messages
        ]

        resp = self.client.ChatCompletions(req)

        return {
            'content': resp.Choices[0].Message.Content,
            'usage': {
                'input_tokens': resp.Usage.PromptTokens,
                'output_tokens': resp.Usage.CompletionTokens,
                'total_tokens': resp.Usage.TotalTokens
            }
        }
```

### Gemini适配器 (Google)
```python
import google.generativeai as genai

class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini适配器"""

    PRICING = {
        'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},    # $/千tokens
        'gemini-1.5-flash': {'input': 0.000075, 'output': 0.0003},
        'gemini-1.0-pro': {'input': 0.0005, 'output': 0.0015}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        super().__init__(api_key, '', config)
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用Gemini API"""
        try:
            # 转换消息格式
            gemini_messages = self._convert_messages(messages)

            # 配置生成参数
            generation_config = genai.GenerationConfig(
                temperature=self.config.get('temperature', 0.7),
                max_output_tokens=self.config.get('max_tokens', 4096),
                top_p=self.config.get('top_p', 0.9)
            )

            # 创建对话
            chat = self.model.start_chat(history=gemini_messages[:-1])

            # 发送最后一条消息
            response = await chat.send_message_async(
                gemini_messages[-1]['parts'][0],
                generation_config=generation_config
            )

            # 估算token（Gemini不直接返回token数，需要计算）
            input_text = ' '.join([m.get('content', '') for m in messages])
            output_text = response.text

            return {
                'content': response.text,
                'usage': {
                    'input_tokens': self._estimate_tokens(input_text),
                    'output_tokens': self._estimate_tokens(output_text),
                    'total_tokens': self._estimate_tokens(input_text + output_text)
                }
            }

        except Exception as e:
            raise Exception(f"Gemini调用错误: {str(e)}")

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[Dict]:
        """转换为Gemini格式"""
        gemini_messages = []

        for msg in messages:
            if msg['role'] == 'system':
                # Gemini没有system角色，作为用户第一条消息
                gemini_messages.insert(0, {
                    'role': 'user',
                    'parts': [f"[System Instructions]: {msg['content']}"]
                })
            elif msg['role'] == 'user':
                gemini_messages.append({
                    'role': 'user',
                    'parts': [msg['content']]
                })
            elif msg['role'] == 'assistant':
                gemini_messages.append({
                    'role': 'model',
                    'parts': [msg['content']]
                })

        return gemini_messages

    def _estimate_tokens(self, text: str) -> int:
        """估算token数（简单按字符数/4估算）"""
        return len(text) // 4

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        gemini_messages = self._convert_messages(messages)
        chat = self.model.start_chat(history=gemini_messages[:-1])

        response = await chat.send_message_async(
            gemini_messages[-1]['parts'][0],
            stream=True
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本（美元转人民币）"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['gemini-1.5-pro'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return (input_cost + output_cost) * 7.2
```

### DeepSeek适配器
```python
class DeepSeekAdapter(BaseLLMAdapter):
    """DeepSeek适配器（兼容OpenAI格式）"""

    PRICING = {
        'deepseek-chat': {'input': 0.001, 'output': 0.002},  # 元/千tokens
        'deepseek-coder': {'input': 0.001, 'output': 0.002}
    }

    def __init__(self, api_key: str, model_name: str, config: Dict):
        super().__init__(api_key, config.get('base_url', 'https://api.deepseek.com/v1'), config)
        self.model_name = model_name
        # DeepSeek兼容OpenAI SDK
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.api_endpoint,
            timeout=config.get('timeout_seconds', 30)
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        functions: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> Dict:
        """调用DeepSeek API（与OpenAI格式相同）"""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 2000)
            )

            return {
                'content': response.choices[0].message.content,
                'usage': {
                    'input_tokens': response.usage.prompt_tokens,
                    'output_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }

        except Exception as e:
            raise Exception(f"DeepSeek调用错误: {str(e)}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncIterator[str]:
        """流式响应"""
        stream = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        pricing = self.PRICING.get(self.model_name, self.PRICING['deepseek-chat'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost
```

### 适配器工厂
```python
class LLMAdapterFactory:
    """LLM适配器工厂"""

    ADAPTERS = {
        'qwen': QwenAdapter,
        'minimax': MiniMaxAdapter,
        'kimi': KimiAdapter,
        'hunyuan': HunyuanAdapter,
        'openai': OpenAIAdapter,
        'claude': ClaudeAdapter,
        'gemini': GeminiAdapter,
        'deepseek': DeepSeekAdapter
    }

    @staticmethod
    def create_adapter(
        provider: str,
        api_key: str,
        model_name: str,
        config: Dict
    ) -> BaseLLMAdapter:
        """创建适配器"""
        adapter_class = LLMAdapterFactory.ADAPTERS.get(provider)
        if not adapter_class:
            raise ValueError(f"不支持的AI提供商: {provider}")

        return adapter_class(api_key, model_name, config)

    @staticmethod
    async def get_default_adapter() -> BaseLLMAdapter:
        """获取默认适配器"""
        model = await db.query(AIModel).filter(
            AIModel.is_active == True,
            AIModel.is_default == True
        ).first()

        if not model:
            raise Exception("未配置默认AI模型")

        # 解密API密钥
        api_key = decrypt_api_key(model.api_key_encrypted)

        return LLMAdapterFactory.create_adapter(
            model.provider,
            api_key,
            model.model_name,
            model.config
        )
```

## AI模型管理API

### 配置模型（仅Master）
```
POST /api/v1/admin/ai-models
Authorization: Bearer {master_token}
```

**Request**
```json
{
  "provider": "qwen",
  "model_name": "qwen-max",
  "display_name": "通义千问-最强版",
  "api_key": "sk-xxxxxxxxxxxxx",
  "api_endpoint": "",
  "is_default": true,
  "config": {
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.9,
    "timeout_seconds": 30
  }
}
```

### 获取模型列表
```
GET /api/v1/admin/ai-models
```

**Response**
```json
{
  "models": [
    {
      "id": "uuid",
      "provider": "qwen",
      "model_name": "qwen-max",
      "display_name": "通义千问-最强版",
      "is_active": true,
      "is_default": true,
      "config": {...},
      "created_at": "2026-01-27T00:00:00Z"
    },
    {
      "id": "uuid",
      "provider": "minimax",
      "model_name": "abab6-chat",
      "display_name": "MiniMax-标准版",
      "is_active": true,
      "is_default": false,
      "config": {...},
      "created_at": "2026-01-27T00:00:00Z"
    }
  ]
}
```

### 设置默认模型
```
PATCH /api/v1/admin/ai-models/{model_id}/set-default
```

### 测试模型
```
POST /api/v1/admin/ai-models/{model_id}/test
```

**Request**
```json
{
  "test_message": "你好，请介绍一下你自己"
}
```

**Response**
```json
{
  "success": true,
  "response": "你好！我是...",
  "latency_ms": 1200,
  "tokens": {
    "input": 10,
    "output": 50,
    "total": 60
  },
  "cost": 0.003
}
```

### 查看使用统计
```
GET /api/v1/admin/ai-models/usage-stats
```

**Query Parameters**:
- start_date, end_date
- model_id
- user_id

**Response**
```json
{
  "total_requests": 1523,
  "total_tokens": 523400,
  "total_cost": 45.67,
  "by_model": [
    {
      "model_name": "qwen-max",
      "requests": 1200,
      "tokens": 450000,
      "cost": 38.5,
      "avg_latency_ms": 1500
    },
    {
      "model_name": "abab6-chat",
      "requests": 323,
      "tokens": 73400,
      "cost": 7.17,
      "avg_latency_ms": 800
    }
  ],
  "by_user": [
    {
      "user_name": "张医生",
      "requests": 567,
      "tokens": 198000,
      "cost": 16.8
    }
  ]
}
```

## 前端配置界面

### Master管理后台 - AI模型配置
```vue
<template>
  <view class="ai-model-config">
    <view class="header">
      <text class="title">AI模型配置</text>
      <button @click="showAddModel">添加模型</button>
    </view>

    <view class="model-list">
      <view v-for="model in models" :key="model.id" class="model-card">
        <view class="model-info">
          <text class="name">{{ model.display_name }}</text>
          <text class="provider">{{ model.provider }} - {{ model.model_name }}</text>
          <view class="badges">
            <view v-if="model.is_default" class="badge default">默认</view>
            <view v-if="model.is_active" class="badge active">启用</view>
            <view v-else class="badge inactive">停用</view>
          </view>
        </view>

        <view class="model-stats">
          <text>使用次数: {{ model.usage_count }}</text>
          <text>总成本: ¥{{ model.total_cost }}</text>
        </view>

        <view class="actions">
          <button @click="testModel(model)">测试</button>
          <button @click="setDefault(model)" :disabled="model.is_default">
            设为默认
          </button>
          <button @click="toggleActive(model)">
            {{ model.is_active ? '停用' : '启用' }}
          </button>
          <button @click="editModel(model)">编辑</button>
        </view>
      </view>
    </view>

    <!-- 添加/编辑模型弹窗 -->
    <uni-popup ref="modelPopup" type="center">
      <view class="model-form">
        <text class="form-title">配置AI模型</text>

        <picker @change="selectProvider" :range="providers" range-key="name">
          <view class="field">
            <text>AI提供商</text>
            <text>{{ selectedProvider.name }}</text>
          </view>
        </picker>

        <picker @change="selectModel" :range="availableModels" range-key="name">
          <view class="field">
            <text>模型</text>
            <text>{{ selectedModel.name }}</text>
          </view>
        </picker>

        <input v-model="formData.display_name" placeholder="显示名称" />
        <input v-model="formData.api_key" type="password" placeholder="API Key" />

        <view class="config-section">
          <text>高级配置</text>
          <slider v-model="formData.temperature" min="0" max="1" step="0.1" />
          <text>Temperature: {{ formData.temperature }}</text>

          <input v-model.number="formData.max_tokens" type="number" placeholder="最大Tokens" />
        </view>

        <checkbox v-model="formData.is_default">设为默认模型</checkbox>

        <view class="form-actions">
          <button @click="saveModel">保存</button>
          <button @click="closePopup">取消</button>
        </view>
      </view>
    </uni-popup>

    <!-- 使用统计 -->
    <view class="usage-stats">
      <text class="section-title">使用统计</text>
      <view class="chart">
        <!-- 使用echarts展示统计图表 -->
      </view>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      models: [],
      providers: [
        { value: 'qwen', name: '通义千问（阿里云）', icon: '🇨🇳' },
        { value: 'minimax', name: 'MiniMax', icon: '🇨🇳' },
        { value: 'openai', name: 'OpenAI', icon: '🇺🇸' },
        { value: 'claude', name: 'Claude', icon: '🇺🇸' },
        { value: 'deepseek', name: 'DeepSeek', icon: '🇨🇳' }
      ],
      modelOptions: {
        'qwen': [
          { value: 'qwen-max', name: 'Qwen Max (最强)', desc: '复杂任务' },
          { value: 'qwen-plus', name: 'Qwen Plus (平衡)', desc: '日常使用' },
          { value: 'qwen-turbo', name: 'Qwen Turbo (快速)', desc: '简单任务' }
        ],
        'minimax': [
          { value: 'abab6-chat', name: 'Abab 6 (标准)', desc: '综合能力强' },
          { value: 'abab5.5-chat', name: 'Abab 5.5 (经济)', desc: '性价比高' }
        ]
      }
    }
  },
  methods: {
    async testModel(model) {
      uni.showLoading({ title: '测试中...' })
      try {
        const res = await this.$api.testAIModel(model.id, {
          test_message: '你好，请介绍一下你自己'
        })
        uni.showModal({
          title: '测试成功',
          content: `响应: ${res.response}\n延迟: ${res.latency_ms}ms\n成本: ¥${res.cost}`,
          showCancel: false
        })
      } catch (e) {
        uni.showToast({ title: '测试失败', icon: 'none' })
      } finally {
        uni.hideLoading()
      }
    }
  }
}
</script>
```

## 环境变量配置示例

### .env
```bash
# 默认AI模型配置（可通过管理后台覆盖）

# 通义千问
QWEN_API_KEY=sk-xxxxxxxxxx
QWEN_MODEL=qwen-plus

# MiniMax
MINIMAX_API_KEY=xxxxx
MINIMAX_GROUP_ID=xxxxx
MINIMAX_MODEL=abab6-chat

# OpenAI (备用)
OPENAI_API_KEY=sk-xxxxxxxxxx
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1

# Claude (备用)
CLAUDE_API_KEY=sk-xxxxxxxxxx
CLAUDE_MODEL=claude-3-sonnet-20240229
```

## 成本控制

### 使用限制
```python
# 在ai_models表的usage_limit字段
{
  "daily_requests": 1000,      # 每日请求数限制
  "daily_tokens": 1000000,     # 每日token限制
  "daily_cost": 100.0,         # 每日成本限制（元）
  "per_user_daily_requests": 50  # 单用户每日限制
}
```

### 限制检查
```python
async def check_usage_limit(model_id: UUID, user_id: UUID) -> bool:
    """检查是否超过使用限制"""
    model = await get_model(model_id)
    limits = model.usage_limit

    # 检查模型每日限制
    today_usage = await get_today_usage(model_id)
    if limits.get('daily_requests') and today_usage['requests'] >= limits['daily_requests']:
        raise Exception("模型每日请求数已达上限")

    # 检查用户每日限制
    user_today_usage = await get_user_today_usage(user_id, model_id)
    if limits.get('per_user_daily_requests') and \
       user_today_usage['requests'] >= limits['per_user_daily_requests']:
        raise Exception("您今日的AI使用次数已达上限")

    return True
```

## 初始化脚本

### 默认模型配置
```python
async def init_default_models():
    """初始化默认AI模型配置"""

    # 通义千问（默认）
    qwen_model = AIModel(
        provider='qwen',
        model_name='qwen-plus',
        display_name='通义千问-标准版',
        api_endpoint='',
        api_key_encrypted=encrypt_api_key(os.getenv('QWEN_API_KEY')),
        is_active=True,
        is_default=True,
        config={
            'temperature': 0.7,
            'max_tokens': 2000,
            'top_p': 0.9,
            'timeout_seconds': 30
        }
    )

    # MiniMax
    minimax_model = AIModel(
        provider='minimax',
        model_name='abab6-chat',
        display_name='MiniMax-标准版',
        api_endpoint='https://api.minimax.chat/v1/text/chatcompletion_v2',
        api_key_encrypted=encrypt_api_key(os.getenv('MINIMAX_API_KEY')),
        is_active=True,
        is_default=False,
        config={
            'temperature': 0.7,
            'max_tokens': 2000,
            'group_id': os.getenv('MINIMAX_GROUP_ID')
        }
    )

    db.add_all([qwen_model, minimax_model])
    await db.commit()
```

## 监控和告警

### 监控指标
- API调用成功率
- 平均响应延迟
- Token消耗速率
- 成本趋势
- 错误类型分布

### 告警规则
```python
ALERT_RULES = {
    'high_error_rate': {
        'threshold': 0.1,  # 10%错误率
        'action': 'switch_to_backup_model'
    },
    'high_latency': {
        'threshold': 5000,  # 5秒
        'action': 'notify_admin'
    },
    'daily_cost_exceeded': {
        'threshold': 100,  # 100元/天
        'action': 'pause_non_critical_usage'
    }
}
```
