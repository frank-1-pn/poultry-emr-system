"""数据统计服务"""

import uuid
from datetime import date, timedelta

from datetime import datetime, timezone

from sqlalchemy import and_, case, cast, Date, func, select, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.models.conversation import Conversation


async def get_overview_stats(db: AsyncSession) -> dict:
    """获取全局概览统计"""
    # 总病历数
    total_records = await db.execute(
        select(func.count()).select_from(
            select(MedicalRecord).where(MedicalRecord.status != "deleted").subquery()
        )
    )
    # 总用户数
    total_users = await db.execute(
        select(func.count()).select_from(User)
    )
    # 活跃用户（有病历的）
    active_vets = await db.execute(
        select(func.count(func.distinct(MedicalRecord.owner_id))).where(
            MedicalRecord.status != "deleted"
        )
    )
    # 总对话数
    total_conversations = await db.execute(
        select(func.count()).select_from(Conversation)
    )

    return {
        "total_records": total_records.scalar() or 0,
        "total_users": total_users.scalar() or 0,
        "active_veterinarians": active_vets.scalar() or 0,
        "total_conversations": total_conversations.scalar() or 0,
    }


async def get_disease_stats(
    db: AsyncSession,
    days: int = 30,
) -> list[dict]:
    """获取疾病分布统计（按 primary_diagnosis 分组）"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            MedicalRecord.primary_diagnosis,
            func.count().label("count"),
        )
        .where(
            and_(
                MedicalRecord.status != "deleted",
                MedicalRecord.primary_diagnosis.isnot(None),
                MedicalRecord.created_at >= since,
            )
        )
        .group_by(MedicalRecord.primary_diagnosis)
        .order_by(func.count().desc())
        .limit(20)
    )
    return [
        {"diagnosis": row[0], "count": row[1]}
        for row in result.all()
    ]


async def get_poultry_type_stats(db: AsyncSession) -> list[dict]:
    """获取禽类类型分布统计"""
    result = await db.execute(
        select(
            MedicalRecord.poultry_type,
            func.count().label("count"),
        )
        .where(MedicalRecord.status != "deleted")
        .group_by(MedicalRecord.poultry_type)
        .order_by(func.count().desc())
    )
    return [
        {"poultry_type": row[0], "count": row[1]}
        for row in result.all()
    ]


async def get_severity_stats(db: AsyncSession) -> list[dict]:
    """获取严重程度分布统计"""
    result = await db.execute(
        select(
            MedicalRecord.severity,
            func.count().label("count"),
        )
        .where(
            and_(
                MedicalRecord.status != "deleted",
                MedicalRecord.severity.isnot(None),
            )
        )
        .group_by(MedicalRecord.severity)
        .order_by(func.count().desc())
    )
    return [
        {"severity": row[0], "count": row[1]}
        for row in result.all()
    ]


async def get_trend_stats(
    db: AsyncSession,
    days: int = 30,
) -> list[dict]:
    """获取病历创建趋势（按日统计）"""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    # 使用 substr 提取日期部分以兼容 SQLite 和 PostgreSQL
    date_expr = func.substr(cast(MedicalRecord.created_at, String), 1, 10)
    result = await db.execute(
        select(
            date_expr.label("date"),
            func.count().label("count"),
        )
        .where(
            and_(
                MedicalRecord.status != "deleted",
                MedicalRecord.created_at >= since,
            )
        )
        .group_by(date_expr)
        .order_by(date_expr)
    )
    return [
        {"date": str(row[0]), "count": row[1]}
        for row in result.all()
    ]
