"""养殖场相关 Pydantic schemas"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    name: str = Field(..., max_length=200)
    owner_name: str | None = None
    contact_phone: str | None = None
    address: str | None = None


class FarmResponse(BaseModel):
    id: uuid.UUID
    farm_code: str
    name: str
    owner_name: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FarmListItem(BaseModel):
    id: uuid.UUID
    farm_code: str
    name: str
    owner_name: str | None = None
    contact_phone: str | None = None

    model_config = {"from_attributes": True}
