"""AI 模型配置相关 Schema"""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AIProvider(str, Enum):
    qwen = "qwen"
    minimax = "minimax"
    kimi = "kimi"
    hunyuan = "hunyuan"
    openai = "openai"
    claude = "claude"
    gemini = "gemini"
    deepseek = "deepseek"


class ModelConfig(BaseModel):
    """模型参数配置"""

    temperature: float = Field(0.7, ge=0, le=2)
    max_tokens: int = Field(2048, ge=1, le=128000)
    top_p: float = Field(1.0, ge=0, le=1)
    timeout: int = Field(60, ge=5, le=300)


class UsageLimit(BaseModel):
    """使用限制配置"""

    daily_requests: int | None = None
    daily_tokens: int | None = None
    daily_cost: float | None = None


# --- Create / Update ---


class AIModelCreate(BaseModel):
    provider: AIProvider
    model_name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=1, description="API Key 明文，后端加密存储")
    api_endpoint: str | None = None
    config: ModelConfig | None = None
    usage_limit: UsageLimit | None = None
    is_default: bool = False


class AIModelUpdate(BaseModel):
    display_name: str | None = None
    api_key: str | None = Field(None, description="不传则不更新")
    api_endpoint: str | None = None
    config: ModelConfig | None = None
    usage_limit: UsageLimit | None = None
    is_active: bool | None = None


# --- Response ---


class AIModelResponse(BaseModel):
    id: uuid.UUID
    provider: str
    model_name: str
    display_name: str
    api_endpoint: str | None = None
    api_key_set: bool = Field(description="是否已设置 API Key")
    is_active: bool
    is_default: bool
    config: dict | None = None
    usage_limit: dict | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIModelListResponse(BaseModel):
    items: list[AIModelResponse]
    total: int


# --- Test ---


class AIModelTestRequest(BaseModel):
    test_message: str = Field("你好，请简单介绍一下你自己。", max_length=500)


class AIModelTestResponse(BaseModel):
    success: bool
    response: str | None = None
    latency_ms: int = 0
    tokens: int = 0
    cost: float = 0.0
    error: str | None = None


# --- Usage Stats ---


class UsageStatsResponse(BaseModel):
    model_id: uuid.UUID | None = None
    model_name: str | None = None
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    success_count: int = 0
    error_count: int = 0
    avg_latency_ms: float = 0.0
