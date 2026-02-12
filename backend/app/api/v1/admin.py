import logging
import math
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_master
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse

logger = logging.getLogger(__name__)
from app.schemas.permission import (
    PermissionBatchGrant,
    PermissionGrant,
    PermissionResponse,
    PermissionRevoke,
)
from app.schemas.user import UserResponse, UserUpdateStatus
from app.services.audit_service import log_action
from app.services.permission_service import (
    batch_grant,
    get_user_permissions,
    grant_permission,
    revoke_permission,
)

router = APIRouter(prefix="/admin", tags=["管理"])


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """获取用户列表（仅Master）"""
    count_result = await db.execute(select(func.count()).select_from(User))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = list(result.scalars().all())

    return PaginatedResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.patch("/users/{user_id}/status", response_model=UserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    data: UserUpdateStatus,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """激活/禁用用户"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.is_active = data.is_active
    await db.flush()

    await log_action(
        db,
        master.id,
        "update_user_status",
        "user",
        user_id,
        {"is_active": data.is_active, "reason": data.reason},
    )

    return user


@router.post("/permissions", response_model=PermissionResponse)
async def grant_perm(
    data: PermissionGrant,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """授予病历访问权限"""
    perm = await grant_permission(
        db,
        data.record_id,
        data.user_id,
        data.permission_level,
        master.id,
        data.expires_at,
        data.notes,
    )
    await log_action(
        db, master.id, "grant_permission", "record_permission", perm.id,
        {"record_id": str(data.record_id), "user_id": str(data.user_id), "level": data.permission_level},
    )
    return perm


@router.post("/permissions/batch", response_model=list[PermissionResponse])
async def batch_grant_perm(
    data: PermissionBatchGrant,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """批量授予病历访问权限"""
    perms = await batch_grant(
        db,
        data.record_ids,
        data.user_ids,
        data.permission_level,
        master.id,
        data.expires_at,
        data.notes,
    )
    return perms


@router.delete("/permissions/{permission_id}", response_model=PermissionResponse)
async def revoke_perm(
    permission_id: uuid.UUID,
    data: PermissionRevoke,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """撤销病历访问权限"""
    perm = await revoke_permission(db, permission_id, master.id, data.reason)
    await log_action(
        db, master.id, "revoke_permission", "record_permission", permission_id,
        {"reason": data.reason},
    )
    return perm


@router.get("/users/{user_id}/permissions", response_model=list[PermissionResponse])
async def user_permissions(
    user_id: uuid.UUID,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """获取用户的权限列表"""
    return await get_user_permissions(db, user_id)


# ---- Embedding 管理 ----


class EmbeddingBatchRequest(BaseModel):
    batch_size: int = Field(20, ge=1, le=100, description="每批处理数")
    limit: int = Field(100, ge=1, le=1000, description="最大处理数")


class EmbeddingBatchResponse(BaseModel):
    processed: int
    success: int
    failed: int


class EmbeddingStatsResponse(BaseModel):
    total: int
    completed: int
    pending: int
    failed: int
    skipped: int


@router.post("/embeddings/generate", response_model=EmbeddingBatchResponse)
async def generate_embeddings(
    data: EmbeddingBatchRequest = EmbeddingBatchRequest(),
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """批量生成病历 embedding（仅Master）"""
    from app.services.embedding_service import batch_generate_embeddings

    result = await batch_generate_embeddings(
        db, batch_size=data.batch_size, limit=data.limit,
    )
    logger.info(
        "Embedding 批量生成完成: processed=%d, success=%d, failed=%d",
        result["processed"], result["success"], result["failed"],
    )
    return result


@router.post("/embeddings/generate/{record_id}", response_model=MessageResponse)
async def generate_single_embedding(
    record_id: uuid.UUID,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """为单条病历生成 embedding"""
    from app.services.embedding_service import generate_record_embedding

    success = await generate_record_embedding(db, record_id)
    if success:
        return MessageResponse(message="Embedding 生成成功")
    return MessageResponse(message="Embedding 生成失败或无可用文本")


@router.get("/embeddings/stats", response_model=EmbeddingStatsResponse)
async def embedding_stats(
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """获取 embedding 生成统计"""
    from app.models.medical_record import MedicalRecord

    total_result = await db.execute(
        select(func.count()).select_from(
            select(MedicalRecord).where(MedicalRecord.status != "deleted").subquery()
        )
    )
    total = total_result.scalar() or 0

    stats = {}
    for status_val in ("completed", "pending", "failed", "skipped"):
        result = await db.execute(
            select(func.count()).select_from(
                select(MedicalRecord).where(
                    MedicalRecord.embedding_status == status_val,
                    MedicalRecord.status != "deleted",
                ).subquery()
            )
        )
        stats[status_val] = result.scalar() or 0

    return EmbeddingStatsResponse(total=total, **stats)


@router.get("/audit-logs")
async def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """查询审计日志"""
    query = select(AuditLog)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0

    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    logs = list(result.scalars().all())

    return {
        "items": logs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }
