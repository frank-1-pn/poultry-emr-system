import uuid
from datetime import datetime

from pydantic import BaseModel


class STSTokenResponse(BaseModel):
    access_key_id: str
    access_key_secret: str
    security_token: str
    expiration: str
    bucket: str
    endpoint: str


class MediaFileCreate(BaseModel):
    record_id: uuid.UUID
    file_type: str
    media_type: str
    oss_key: str
    url: str
    thumbnail_url: str | None = None
    file_size: int | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    description: str | None = None
    captured_at: datetime | None = None


class MediaFileResponse(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID
    file_type: str
    media_type: str
    oss_key: str
    url: str
    thumbnail_url: str | None = None
    file_size: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
