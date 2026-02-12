from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_master
from app.core.database import get_db
from app.models.user import User
from app.services.statistics_service import (
    get_disease_stats,
    get_overview_stats,
    get_poultry_type_stats,
    get_severity_stats,
    get_trend_stats,
)

router = APIRouter(prefix="/statistics", tags=["数据统计"])


@router.get("/overview")
async def overview(
    current_user: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """全局概览统计（仅 Master）"""
    return await get_overview_stats(db)


@router.get("/diseases")
async def diseases(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """疾病分布统计"""
    return await get_disease_stats(db, days)


@router.get("/poultry-types")
async def poultry_types(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """禽类类型分布"""
    return await get_poultry_type_stats(db)


@router.get("/severity")
async def severity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """严重程度分布"""
    return await get_severity_stats(db)


@router.get("/trend")
async def trend(
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """病历创建趋势"""
    return await get_trend_stats(db, days)
