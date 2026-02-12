"""用户记忆 API 路由"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.memory import MemoryUpdateRequest, UserMemoryResponse
from app.services import memory_service

router = APIRouter(prefix="/memory", tags=["记忆"])


@router.get("", response_model=UserMemoryResponse)
async def get_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取用户记忆"""
    memory = await memory_service.get_or_create_memory(db, current_user.id)
    return UserMemoryResponse.model_validate(memory)


@router.put("", response_model=UserMemoryResponse)
async def update_memory(
    req: MemoryUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新用户记忆"""
    memory = await memory_service.update_memory(db, current_user.id, req.content)
    return UserMemoryResponse.model_validate(memory)
