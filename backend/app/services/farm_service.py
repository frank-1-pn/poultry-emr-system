"""养殖场 CRUD 服务"""

import random
import string
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm import Farm
from app.schemas.farm import FarmCreate


def _generate_farm_code() -> str:
    """生成养殖场编码: F-YYYYMMDD-XXXX"""
    today = date.today().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=4))
    return f"F-{today}-{suffix}"


async def list_farms(
    db: AsyncSession,
    search: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Farm], int]:
    """获取养殖场列表，支持搜索"""
    query = select(Farm)

    if search:
        like_pattern = f"%{search}%"
        query = query.where(
            Farm.name.ilike(like_pattern)
            | Farm.farm_code.ilike(like_pattern)
            | Farm.owner_name.ilike(like_pattern)
        )

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = (
        query.order_by(Farm.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    farms = list(result.scalars().all())
    return farms, total


async def create_farm(db: AsyncSession, data: FarmCreate) -> Farm:
    """创建养殖场"""
    farm = Farm(
        farm_code=_generate_farm_code(),
        name=data.name,
        owner_name=data.owner_name,
        contact_phone=data.contact_phone,
        address=data.address,
    )
    db.add(farm)
    await db.flush()
    await db.refresh(farm)
    return farm


async def get_farm(db: AsyncSession, farm_id) -> Farm | None:
    """获取养殖场详情"""
    result = await db.execute(select(Farm).where(Farm.id == farm_id))
    return result.scalar_one_or_none()
