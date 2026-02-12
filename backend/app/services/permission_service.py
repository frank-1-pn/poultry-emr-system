import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import (
    get_cached_permission,
    get_redis,
    invalidate_permission_cache,
    invalidate_user_permissions,
    set_cached_permission,
)
from app.models.medical_record import MedicalRecord
from app.models.record_permission import RecordPermission

LEVEL_HIERARCHY = {"read": 1, "write": 2}


async def check_permission(
    db: AsyncSession,
    user_id: str,
    record_id: str,
    required_level: str,
) -> bool:
    # Check if user is the owner
    result = await db.execute(
        select(MedicalRecord.owner_id).where(
            MedicalRecord.id == uuid.UUID(record_id)
        )
    )
    row = result.first()
    if not row:
        return False
    if str(row[0]) == user_id:
        return True

    # Check Redis cache
    r = await get_redis()
    cached = await get_cached_permission(r, user_id, record_id)
    if cached:
        return LEVEL_HIERARCHY.get(cached, 0) >= LEVEL_HIERARCHY.get(required_level, 0)

    # Check DB
    result = await db.execute(
        select(RecordPermission).where(
            and_(
                RecordPermission.record_id == uuid.UUID(record_id),
                RecordPermission.user_id == uuid.UUID(user_id),
                RecordPermission.revoked == False,
            )
        )
    )
    perm = result.scalar_one_or_none()

    if not perm:
        return False

    # Check expiration
    if perm.expires_at and perm.expires_at < datetime.now(timezone.utc):
        return False

    # Cache the result
    await set_cached_permission(r, user_id, record_id, perm.permission_level)

    return LEVEL_HIERARCHY.get(perm.permission_level, 0) >= LEVEL_HIERARCHY.get(
        required_level, 0
    )


async def grant_permission(
    db: AsyncSession,
    record_id: uuid.UUID,
    user_id: uuid.UUID,
    level: str,
    granted_by: uuid.UUID,
    expires_at: datetime | None = None,
    notes: str | None = None,
) -> RecordPermission:
    # Check if permission already exists
    result = await db.execute(
        select(RecordPermission).where(
            and_(
                RecordPermission.record_id == record_id,
                RecordPermission.user_id == user_id,
            )
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.permission_level = level
        existing.granted_by = granted_by
        existing.granted_at = datetime.now(timezone.utc)
        existing.expires_at = expires_at
        existing.revoked = False
        existing.revoked_at = None
        existing.revoked_by = None
        existing.notes = notes
        perm = existing
    else:
        perm = RecordPermission(
            record_id=record_id,
            user_id=user_id,
            permission_level=level,
            granted_by=granted_by,
            granted_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            notes=notes,
        )
        db.add(perm)

    await db.flush()

    # Invalidate cache
    r = await get_redis()
    await invalidate_permission_cache(r, str(user_id), str(record_id))

    return perm


async def revoke_permission(
    db: AsyncSession,
    permission_id: uuid.UUID,
    revoked_by: uuid.UUID,
    reason: str | None = None,
) -> RecordPermission:
    result = await db.execute(
        select(RecordPermission).where(RecordPermission.id == permission_id)
    )
    perm = result.scalar_one_or_none()
    if not perm:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="授权记录不存在")

    perm.revoked = True
    perm.revoked_at = datetime.now(timezone.utc)
    perm.revoked_by = revoked_by
    perm.notes = reason or perm.notes
    await db.flush()

    r = await get_redis()
    await invalidate_permission_cache(r, str(perm.user_id), str(perm.record_id))

    return perm


async def batch_grant(
    db: AsyncSession,
    record_ids: list[uuid.UUID],
    user_ids: list[uuid.UUID],
    level: str,
    granted_by: uuid.UUID,
    expires_at: datetime | None = None,
    notes: str | None = None,
) -> list[RecordPermission]:
    results = []
    for record_id in record_ids:
        for user_id in user_ids:
            perm = await grant_permission(
                db, record_id, user_id, level, granted_by, expires_at, notes
            )
            results.append(perm)
    return results


async def get_user_permissions(
    db: AsyncSession, user_id: uuid.UUID
) -> list[RecordPermission]:
    result = await db.execute(
        select(RecordPermission).where(
            and_(
                RecordPermission.user_id == user_id,
                RecordPermission.revoked == False,
            )
        )
    )
    return list(result.scalars().all())


async def get_record_permissions(
    db: AsyncSession, record_id: uuid.UUID
) -> list[RecordPermission]:
    result = await db.execute(
        select(RecordPermission).where(RecordPermission.record_id == record_id)
    )
    return list(result.scalars().all())
