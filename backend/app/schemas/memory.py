"""用户记忆相关 Pydantic schemas"""

import uuid
from datetime import datetime

from pydantic import BaseModel


class UserMemoryResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    content: dict
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemoryUpdateRequest(BaseModel):
    content: dict
