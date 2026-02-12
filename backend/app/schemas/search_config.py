import uuid
from datetime import datetime

from pydantic import BaseModel


class SearchConfigResponse(BaseModel):
    id: uuid.UUID
    config_key: str
    config_value: dict
    description: str | None = None
    updated_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SearchConfigUpdate(BaseModel):
    config_value: dict
    description: str | None = None
