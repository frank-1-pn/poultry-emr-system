"""提醒 API 路由"""

import math
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.reminder import ReminderGenerateRequest, ReminderResponse
from app.services import reminder_service

router = APIRouter(prefix="/reminders", tags=["提醒"])


@router.get("", response_model=PaginatedResponse[ReminderResponse])
async def list_reminders(
    reminder_date: date | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取提醒列表"""
    reminders, total = await reminder_service.list_reminders(
        db, current_user.id, reminder_date, status, page, page_size
    )
    return PaginatedResponse(
        items=[ReminderResponse.model_validate(r) for r in reminders],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/generate", response_model=list[ReminderResponse])
async def generate_reminders(
    req: ReminderGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """根据病历治疗方案生成提醒"""
    reminders = await reminder_service.generate_reminders(
        db, req.record_id, current_user.id
    )
    return [ReminderResponse.model_validate(r) for r in reminders]


@router.post("/{reminder_id}/confirm", response_model=ReminderResponse)
async def confirm(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """确认提醒"""
    reminder = await reminder_service.confirm_reminder(db, reminder_id, current_user.id)
    return ReminderResponse.model_validate(reminder)


@router.post("/{reminder_id}/dismiss", response_model=ReminderResponse)
async def dismiss(
    reminder_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """忽略提醒"""
    reminder = await reminder_service.dismiss_reminder(db, reminder_id, current_user.id)
    return ReminderResponse.model_validate(reminder)
