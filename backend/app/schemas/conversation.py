"""AI 对话相关 Pydantic schemas"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ---- 嵌套 Brief Schemas ----

class FarmBrief(BaseModel):
    id: uuid.UUID
    name: str
    farm_code: str
    owner_name: str | None = None

    model_config = {"from_attributes": True}


class RecordBrief(BaseModel):
    id: uuid.UUID
    record_no: str
    poultry_type: str
    primary_diagnosis: str | None = None
    severity: str | None = None
    status: str

    model_config = {"from_attributes": True}


# ---- 请求 Schemas ----

class ConversationCreate(BaseModel):
    record_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    tags: list[str] = []


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    audio_url: str | None = None


class ConfirmRecordRequest(BaseModel):
    confirmed: bool
    corrections: dict | None = None


class ConversationTagUpdate(BaseModel):
    tags: list[str]


# ---- 响应 Schemas ----

class ConversationResponse(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    user_id: uuid.UUID
    session_number: int | None = None
    status: str
    state: str
    tags: list[str] = []
    summary: str | None = None
    collected_info: dict
    confidence_scores: dict
    farm: FarmBrief | None = None
    record: RecordBrief | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    audio_url: str | None = None
    extracted_info: dict | None = None
    confidence_scores: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SimilarCaseItem(BaseModel):
    id: str
    record_no: str
    poultry_type: str
    primary_diagnosis: str | None = None
    severity: str | None = None
    similarity: float


class AIReplyResponse(BaseModel):
    message: ConversationMessageResponse
    collected_info: dict
    confidence_scores: dict
    needs_confirmation: list[str] = []
    completeness: dict = {}
    similar_cases: list[SimilarCaseItem] = []


class ConversationCompleteResponse(BaseModel):
    conversation: ConversationResponse
    record_id: uuid.UUID
    record_no: str


class ConversationListItem(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID | None = None
    farm_id: uuid.UUID | None = None
    session_number: int | None = None
    status: str
    state: str
    tags: list[str] = []
    summary: str | None = None
    farm: FarmBrief | None = None
    record: RecordBrief | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---- WebSocket 消息 Schemas ----

class WSIncomingMessage(BaseModel):
    type: str  # user_message | ping | confirm
    content: str | None = None
    audio_url: str | None = None
    confirmed: bool | None = None
    corrections: dict | None = None


class WSOutgoingMessage(BaseModel):
    type: str  # assistant_message | pong | error | info_update | stream_token | stream_end
    content: str | None = None
    collected_info: dict | None = None
    confidence_scores: dict | None = None
    needs_confirmation: list[str] | None = None
    completeness: dict | None = None
    similar_cases: list[dict] | None = None
    error: str | None = None
