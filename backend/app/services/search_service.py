"""全文搜索服务 — 基于 PostgreSQL"""

import uuid

from sqlalchemy import and_, cast, func, or_, select, String, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.record_permission import RecordPermission
from app.models.user import User


async def search_records(
    db: AsyncSession,
    user: User,
    keyword: str,
    page: int = 1,
    page_size: int = 20,
    poultry_type: str | None = None,
    severity: str | None = None,
    farm_id: uuid.UUID | None = None,
) -> tuple[list[MedicalRecord], int]:
    """
    全文搜索病历。
    搜索范围：record_no、primary_diagnosis、poultry_type、breed、record_markdown、record_json。
    使用 ILIKE 模式匹配（兼容 SQLite 测试），生产环境可升级为 PostgreSQL ts_vector。
    """
    like_pattern = f"%{keyword}%"

    query = select(MedicalRecord).where(
        MedicalRecord.status != "deleted",
    )

    # 权限过滤
    if user.role != "master":
        authorized_subq = (
            select(RecordPermission.record_id)
            .where(
                and_(
                    RecordPermission.user_id == user.id,
                    RecordPermission.revoked == False,
                )
            )
            .scalar_subquery()
        )
        query = query.where(
            or_(
                MedicalRecord.owner_id == user.id,
                MedicalRecord.id.in_(authorized_subq),
            )
        )

    # 关键词搜索（多字段 OR）
    query = query.where(
        or_(
            MedicalRecord.record_no.ilike(like_pattern),
            MedicalRecord.primary_diagnosis.ilike(like_pattern),
            MedicalRecord.poultry_type.ilike(like_pattern),
            MedicalRecord.breed.ilike(like_pattern),
            MedicalRecord.record_markdown.ilike(like_pattern),
            cast(MedicalRecord.record_json, String).ilike(like_pattern),
        )
    )

    # 额外筛选
    if poultry_type:
        query = query.where(MedicalRecord.poultry_type == poultry_type)
    if severity:
        query = query.where(MedicalRecord.severity == severity)
    if farm_id:
        query = query.where(MedicalRecord.farm_id == farm_id)

    # 统计总数
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    # 分页
    query = query.order_by(MedicalRecord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    records = list(result.scalars().all())

    return records, total
