import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Soul Config ──

class SoulConfigCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)


class SoulConfigUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    content: str | None = Field(None, min_length=1)


class SoulConfigResponse(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    content_compressed: str
    token_count: int
    compressed_token_count: int
    is_active: bool
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SoulPreviewResponse(BaseModel):
    title: str
    original_tokens: int
    compressed_tokens: int
    content_original: str
    content_compressed: str


# ── Memory Entry ──

class MemoryEntryCreate(BaseModel):
    category: str = Field(..., pattern=r"^(style|skill|habit|improvement|feedback)$")
    content: str = Field(..., min_length=1)
    importance: int = Field(3, ge=1, le=5)
    source: str = Field("manual", pattern=r"^(manual|auto)$")


class MemoryEntryUpdate(BaseModel):
    category: str | None = Field(None, pattern=r"^(style|skill|habit|improvement|feedback)$")
    content: str | None = Field(None, min_length=1)
    importance: int | None = Field(None, ge=1, le=5)


class MemoryEntryResponse(BaseModel):
    id: uuid.UUID
    category: str
    content: str
    source: str
    importance: int
    is_archived: bool
    created_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Context (核心接口) ──

class SoulContextMetadata(BaseModel):
    soul_version: str | None = None
    memory_count: int
    memory_loaded: int


class SoulContextResponse(BaseModel):
    soul_content: str
    memory_content: str
    total_tokens: int
    metadata: SoulContextMetadata
