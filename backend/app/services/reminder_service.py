"""提醒服务 — AI 根据治疗方案生成每日跟进提醒"""

import json
import logging
import uuid
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.clinical import Treatment
from app.models.medical_record import MedicalRecord
from app.models.reminder import Reminder

logger = logging.getLogger(__name__)


async def generate_reminders(
    db: AsyncSession,
    record_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[Reminder]:
    """根据病历的治疗方案自动生成提醒"""
    # 获取病历的治疗记录
    result = await db.execute(
        select(Treatment).where(Treatment.record_id == record_id)
    )
    treatments = list(result.scalars().all())

    # 获取病历基本信息用于提醒内容
    record_result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.id == record_id)
    )
    record = record_result.scalar_one_or_none()
    if not record:
        return []

    created_reminders: list[Reminder] = []
    today = date.today()

    for treatment in treatments:
        start = treatment.start_date or today
        duration = treatment.duration_days or 1

        for day_offset in range(duration):
            reminder_date = start + timedelta(days=day_offset)
            # 不生成过去日期的提醒
            if reminder_date < today:
                continue

            # 检查是否已存在同一天同一病历的提醒
            existing = await db.execute(
                select(Reminder).where(
                    Reminder.record_id == record_id,
                    Reminder.user_id == user_id,
                    Reminder.reminder_date == reminder_date,
                )
            )
            if existing.scalar_one_or_none():
                continue

            content = {
                "title": f"治疗跟进 - 第{day_offset + 1}天",
                "record_no": record.record_no,
                "poultry_type": record.poultry_type,
                "treatment_type": treatment.treatment_type,
                "medication_name": treatment.medication_name,
                "dosage": treatment.dosage,
                "route": treatment.route,
                "frequency": treatment.frequency,
                "message": _build_reminder_message(treatment, day_offset + 1, duration),
            }

            reminder = Reminder(
                record_id=record_id,
                user_id=user_id,
                reminder_date=reminder_date,
                content=content,
                status="pending",
                ai_generated=True,
            )
            db.add(reminder)
            created_reminders.append(reminder)

    await db.flush()
    for r in created_reminders:
        await db.refresh(r)

    return created_reminders


async def list_reminders(
    db: AsyncSession,
    user_id: uuid.UUID,
    reminder_date: date | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Reminder], int]:
    """查询用户的提醒列表"""
    query = select(Reminder).where(Reminder.user_id == user_id)

    if reminder_date:
        query = query.where(Reminder.reminder_date == reminder_date)
    if status_filter:
        query = query.where(Reminder.status == status_filter)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(Reminder.reminder_date.asc(), Reminder.created_at.asc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reminders = list(result.scalars().all())

    return reminders, total


async def confirm_reminder(
    db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID
) -> Reminder:
    """确认提醒"""
    return await _update_status(db, reminder_id, user_id, "confirmed")


async def dismiss_reminder(
    db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID
) -> Reminder:
    """忽略提醒"""
    return await _update_status(db, reminder_id, user_id, "dismissed")


async def _update_status(
    db: AsyncSession, reminder_id: uuid.UUID, user_id: uuid.UUID, new_status: str
) -> Reminder:
    result = await db.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        )
    )
    reminder = result.scalar_one_or_none()
    if not reminder:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="提醒不存在",
        )
    reminder.status = new_status
    await db.flush()
    await db.refresh(reminder)
    return reminder


def _build_reminder_message(treatment: Treatment, day: int, total_days: int) -> str:
    """构建提醒消息文本"""
    parts = [f"治疗第{day}天（共{total_days}天）"]
    if treatment.medication_name:
        parts.append(f"药物: {treatment.medication_name}")
    if treatment.dosage:
        parts.append(f"剂量: {treatment.dosage}")
    if treatment.route:
        parts.append(f"给药途径: {treatment.route}")
    if treatment.frequency:
        parts.append(f"频率: {treatment.frequency}")
    if day == total_days:
        parts.append("⚠️ 今天是疗程最后一天，请注意观察治疗效果")
    return "；".join(parts)
