"""Soul & Memory 服务层"""
import json
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.redis import redis_client
from app.models.soul import MemoryEntry, SoulConfig
from app.schemas.soul import (
    MemoryEntryCreate,
    MemoryEntryUpdate,
    SoulConfigCreate,
    SoulConfigUpdate,
    SoulContextMetadata,
    SoulContextResponse,
)
from app.utils.token_utils import compress_markdown, count_tokens, select_memories

settings = get_settings()

SOUL_CONTEXT_CACHE_KEY = "soul:context"


# ── Soul CRUD ──

async def create_soul(
    db: AsyncSession, data: SoulConfigCreate, user_id: uuid.UUID
) -> SoulConfig:
    """创建新版本 Soul，自动压缩，设为 active"""
    token_count = count_tokens(data.content)
    soul_budget = int(settings.SOUL_TOKEN_BUDGET * settings.SOUL_RATIO)
    compressed = compress_markdown(data.content, soul_budget)
    compressed_token_count = count_tokens(compressed)

    # 将所有现有版本设为非 active
    await db.execute(
        update(SoulConfig).where(SoulConfig.is_active == True).values(is_active=False)
    )

    soul = SoulConfig(
        title=data.title,
        content=data.content,
        content_compressed=compressed,
        token_count=token_count,
        compressed_token_count=compressed_token_count,
        is_active=True,
        created_by=user_id,
    )
    db.add(soul)
    await db.flush()
    await _invalidate_context_cache()
    return soul


async def update_soul(
    db: AsyncSession, soul_id: uuid.UUID, data: SoulConfigUpdate
) -> SoulConfig:
    """更新 Soul 内容，重新压缩"""
    result = await db.execute(select(SoulConfig).where(SoulConfig.id == soul_id))
    soul = result.scalar_one_or_none()
    if not soul:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soul 版本不存在")

    if data.title is not None:
        soul.title = data.title
    if data.content is not None:
        soul.content = data.content
        soul.token_count = count_tokens(data.content)
        soul_budget = int(settings.SOUL_TOKEN_BUDGET * settings.SOUL_RATIO)
        soul.content_compressed = compress_markdown(data.content, soul_budget)
        soul.compressed_token_count = count_tokens(soul.content_compressed)

    await db.flush()
    if soul.is_active:
        await _invalidate_context_cache()
    return soul


async def get_active_soul(db: AsyncSession) -> SoulConfig | None:
    """获取当前生效版本"""
    result = await db.execute(
        select(SoulConfig).where(SoulConfig.is_active == True)
    )
    return result.scalar_one_or_none()


async def list_soul_versions(db: AsyncSession) -> list[SoulConfig]:
    """历史版本列表"""
    result = await db.execute(
        select(SoulConfig).order_by(SoulConfig.created_at.desc())
    )
    return list(result.scalars().all())


async def activate_soul(db: AsyncSession, soul_id: uuid.UUID) -> SoulConfig:
    """切换生效版本"""
    result = await db.execute(select(SoulConfig).where(SoulConfig.id == soul_id))
    soul = result.scalar_one_or_none()
    if not soul:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soul 版本不存在")

    await db.execute(
        update(SoulConfig).where(SoulConfig.is_active == True).values(is_active=False)
    )
    soul.is_active = True
    await db.flush()
    await _invalidate_context_cache()
    return soul


async def get_soul_by_id(db: AsyncSession, soul_id: uuid.UUID) -> SoulConfig:
    """按 ID 获取 Soul"""
    result = await db.execute(select(SoulConfig).where(SoulConfig.id == soul_id))
    soul = result.scalar_one_or_none()
    if not soul:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soul 版本不存在")
    return soul


# ── Memory CRUD ──

async def add_memory(
    db: AsyncSession, data: MemoryEntryCreate, user_id: uuid.UUID
) -> MemoryEntry:
    """添加记忆条目"""
    entry = MemoryEntry(
        category=data.category,
        content=data.content,
        source=data.source,
        importance=data.importance,
        created_by=user_id,
    )
    db.add(entry)
    await db.flush()
    await _invalidate_context_cache()
    return entry


async def list_memories(
    db: AsyncSession,
    category: str | None = None,
    archived: bool | None = None,
) -> list[MemoryEntry]:
    """查询记忆条目"""
    query = select(MemoryEntry).order_by(
        MemoryEntry.importance.desc(), MemoryEntry.created_at.desc()
    )
    if category is not None:
        query = query.where(MemoryEntry.category == category)
    if archived is not None:
        query = query.where(MemoryEntry.is_archived == archived)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_memory(
    db: AsyncSession, memory_id: uuid.UUID, data: MemoryEntryUpdate
) -> MemoryEntry:
    """更新记忆条目"""
    result = await db.execute(select(MemoryEntry).where(MemoryEntry.id == memory_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记忆条目不存在")

    if data.category is not None:
        entry.category = data.category
    if data.content is not None:
        entry.content = data.content
    if data.importance is not None:
        entry.importance = data.importance

    await db.flush()
    await _invalidate_context_cache()
    return entry


async def archive_memory(db: AsyncSession, memory_id: uuid.UUID) -> MemoryEntry:
    """归档记忆条目"""
    result = await db.execute(select(MemoryEntry).where(MemoryEntry.id == memory_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="记忆条目不存在")

    entry.is_archived = True
    await db.flush()
    await _invalidate_context_cache()
    return entry


# ── Context 拼装 ──

async def build_context(db: AsyncSession) -> SoulContextResponse:
    """加载 Soul + Memory，拼装上下文。结果缓存到 Redis。"""
    # 尝试从缓存读取
    cached = await redis_client.get(SOUL_CONTEXT_CACHE_KEY)
    if cached:
        return SoulContextResponse(**json.loads(cached))

    soul_budget = int(settings.SOUL_TOKEN_BUDGET * settings.SOUL_RATIO)
    memory_budget = settings.SOUL_TOKEN_BUDGET - soul_budget

    # Soul
    soul = await get_active_soul(db)
    if soul:
        soul_content = soul.content_compressed
        soul_tokens = soul.compressed_token_count
        soul_version = soul.title
    else:
        soul_content = ""
        soul_tokens = 0
        soul_version = None

    # Memory: 未归档条目，按重要度和时间排序
    memory_entries = await list_memories(db, archived=False)
    memory_content, memory_loaded = select_memories(memory_entries, memory_budget)
    memory_tokens = count_tokens(memory_content)

    response = SoulContextResponse(
        soul_content=soul_content,
        memory_content=memory_content,
        total_tokens=soul_tokens + memory_tokens,
        metadata=SoulContextMetadata(
            soul_version=soul_version,
            memory_count=len(memory_entries),
            memory_loaded=memory_loaded,
        ),
    )

    # 缓存到 Redis
    await redis_client.set(
        SOUL_CONTEXT_CACHE_KEY,
        response.model_dump_json(),
        ex=settings.SOUL_CACHE_TTL,
    )
    return response


async def _invalidate_context_cache() -> None:
    """清除 Soul 上下文缓存"""
    await redis_client.delete(SOUL_CONTEXT_CACHE_KEY)
