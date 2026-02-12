from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_master
from app.core.database import get_db
from app.models.user import User
from app.schemas.search_config import SearchConfigResponse, SearchConfigUpdate
from app.services.search_config_service import get_config, list_configs, update_config

router = APIRouter(prefix="/search-config", tags=["搜索配置"])


@router.get("", response_model=list[SearchConfigResponse])
async def list_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有搜索配置（所有用户可读）"""
    return await list_configs(db)


@router.get("/{config_key}", response_model=SearchConfigResponse)
async def get_detail(
    config_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个搜索配置"""
    return await get_config(db, config_key)


@router.put("/{config_key}", response_model=SearchConfigResponse)
async def update(
    config_key: str,
    data: SearchConfigUpdate,
    current_user: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """更新搜索配置（仅 Master 可写）"""
    return await update_config(db, config_key, data, current_user.id)
