"""提醒相关 Pydantic schemas"""

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class ReminderResponse(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID
    user_id: uuid.UUID
    reminder_date: date
    content: dict
    status: str
    ai_generated: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReminderGenerateRequest(BaseModel):
    record_id: uuid.UUID


class ReminderListQuery(BaseModel):
    date: date | None = None
    status: str | None = None
    page: int = 1
    page_size: int = 20
