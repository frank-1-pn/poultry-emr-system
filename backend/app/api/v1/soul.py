"""Soul & Memory API 路由"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_master
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.soul import (
    MemoryEntryCreate,
    MemoryEntryResponse,
    MemoryEntryUpdate,
    SoulConfigCreate,
    SoulConfigResponse,
    SoulConfigUpdate,
    SoulContextResponse,
    SoulPreviewResponse,
)
from app.services import soul_service

router = APIRouter(prefix="/soul", tags=["Soul 灵魂"])


# ── Soul 管理（Master only） ──

@router.post("", response_model=SoulConfigResponse)
async def create_soul(
    data: SoulConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """创建新版 Soul"""
    soul = await soul_service.create_soul(db, data, current_user.id)
    return soul


@router.get("/active", response_model=SoulConfigResponse | None)
async def get_active_soul(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """获取当前生效的 Soul"""
    return await soul_service.get_active_soul(db)


@router.get("/versions", response_model=list[SoulConfigResponse])
async def list_soul_versions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """获取 Soul 历史版本列表"""
    return await soul_service.list_soul_versions(db)


@router.get("/context", response_model=SoulContextResponse)
async def get_soul_context(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取拼装好的 AI 上下文（Soul + Memory）"""
    return await soul_service.build_context(db)


@router.put("/{soul_id}", response_model=SoulConfigResponse)
async def update_soul(
    soul_id: uuid.UUID,
    data: SoulConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """更新 Soul 内容"""
    return await soul_service.update_soul(db, soul_id, data)


@router.post("/{soul_id}/activate", response_model=SoulConfigResponse)
async def activate_soul(
    soul_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """切换生效版本"""
    return await soul_service.activate_soul(db, soul_id)


@router.get("/{soul_id}/preview", response_model=SoulPreviewResponse)
async def preview_soul(
    soul_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """预览压缩效果（原文 vs 压缩版 token 对比）"""
    soul = await soul_service.get_soul_by_id(db, soul_id)
    return SoulPreviewResponse(
        title=soul.title,
        original_tokens=soul.token_count,
        compressed_tokens=soul.compressed_token_count,
        content_original=soul.content,
        content_compressed=soul.content_compressed,
    )


# ── Memory 管理（Master only） ──

@router.post("/memory", response_model=MemoryEntryResponse)
async def add_memory(
    data: MemoryEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """添加记忆条目"""
    return await soul_service.add_memory(db, data, current_user.id)


@router.get("/memory", response_model=list[MemoryEntryResponse])
async def list_memories(
    category: str | None = Query(None),
    archived: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """列出记忆条目（支持 category 和 archived 过滤）"""
    return await soul_service.list_memories(db, category=category, archived=archived)


@router.patch("/memory/{memory_id}", response_model=MemoryEntryResponse)
async def update_memory(
    memory_id: uuid.UUID,
    data: MemoryEntryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """更新记忆条目"""
    return await soul_service.update_memory(db, memory_id, data)


@router.delete("/memory/{memory_id}", response_model=MessageResponse)
async def archive_memory(
    memory_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_master),
):
    """归档记忆条目（软删除）"""
    await soul_service.archive_memory(db, memory_id)
    return MessageResponse(message="记忆条目已归档")
