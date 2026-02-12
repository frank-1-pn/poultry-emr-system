"""养殖场 CRUD API"""

import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.farm import FarmCreate, FarmListItem, FarmResponse
from app.services import farm_service

router = APIRouter(prefix="/farms", tags=["养殖场"])


@router.get("", response_model=PaginatedResponse[FarmListItem])
async def list_farms(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取养殖场列表"""
    farms, total = await farm_service.list_farms(
        db, search=search, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[FarmListItem.model_validate(f) for f in farms],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    data: FarmCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建养殖场"""
    farm = await farm_service.create_farm(db, data)
    return farm


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取养殖场详情"""
    farm = await farm_service.get_farm(db, farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="养殖场不存在",
        )
    return farm
