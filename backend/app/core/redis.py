import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)

PERMISSION_CACHE_TTL = 300  # 5 minutes


async def get_redis() -> aioredis.Redis:
    return redis_client


def _permission_key(user_id: str, record_id: str) -> str:
    return f"perm:{user_id}:{record_id}"


async def get_cached_permission(
    r: aioredis.Redis, user_id: str, record_id: str
) -> str | None:
    val = await r.get(_permission_key(user_id, record_id))
    return val


async def set_cached_permission(
    r: aioredis.Redis, user_id: str, record_id: str, level: str
) -> None:
    await r.set(_permission_key(user_id, record_id), level, ex=PERMISSION_CACHE_TTL)


async def invalidate_permission_cache(
    r: aioredis.Redis, user_id: str, record_id: str
) -> None:
    await r.delete(_permission_key(user_id, record_id))


async def invalidate_user_permissions(
    r: aioredis.Redis, user_id: str
) -> None:
    pattern = f"perm:{user_id}:*"
    async for key in r.scan_iter(match=pattern):
        await r.delete(key)
