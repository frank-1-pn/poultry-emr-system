import uuid
from datetime import datetime

from pydantic import BaseModel


class PermissionGrant(BaseModel):
    record_id: uuid.UUID
    user_id: uuid.UUID
    permission_level: str = "read"
    expires_at: datetime | None = None
    notes: str | None = None


class PermissionBatchGrant(BaseModel):
    record_ids: list[uuid.UUID]
    user_ids: list[uuid.UUID]
    permission_level: str = "read"
    expires_at: datetime | None = None
    notes: str | None = None


class PermissionResponse(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID
    user_id: uuid.UUID
    permission_level: str
    granted_by: uuid.UUID
    granted_at: datetime
    expires_at: datetime | None = None
    revoked: bool
    revoked_at: datetime | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class PermissionRevoke(BaseModel):
    reason: str | None = None
