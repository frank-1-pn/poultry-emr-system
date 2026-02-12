import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_record_permission
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.permission import PermissionResponse
from app.schemas.record import (
    RecordCreate, RecordListItem, RecordResponse, RecordUpdate,
    RecordVersionResponse, VersionDetailResponse, VersionCompareResponse,
    TreatmentTimelineItem,
)
from app.services.permission_service import get_record_permissions
from app.services.timeline_service import get_record_timeline, get_treatment_timeline
from app.services.record_service import (
    compare_versions,
    create_record,
    delete_record,
    get_record,
    get_record_versions,
    get_version_detail,
    list_records,
    rollback_to_version,
    update_record,
)

router = APIRouter(prefix="/records", tags=["病历"])


@router.post("", response_model=RecordResponse)
async def create(
    data: RecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建病历"""
    record = await create_record(db, current_user, data)
    return record


@router.get("", response_model=PaginatedResponse[RecordListItem])
async def list_all(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    poultry_type: str | None = None,
    farm_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取病历列表（带权限过滤）"""
    records, total = await list_records(
        db, current_user, page, page_size, status, poultry_type, farm_id
    )
    return PaginatedResponse(
        items=[RecordListItem.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{record_id}", response_model=RecordResponse)
async def get_detail(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """获取病历详情（需要读取权限）"""
    record = await get_record(db, record_id)
    return record


@router.put("/{record_id}", response_model=RecordResponse)
async def update(
    record_id: uuid.UUID,
    data: RecordUpdate,
    current_user: User = Depends(require_record_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    """更新病历（需要写入权限）"""
    record = await update_record(db, record_id, data, current_user)
    return record


@router.delete("/{record_id}", response_model=RecordResponse)
async def delete(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    """软删除病历（需要写入权限）"""
    record = await delete_record(db, record_id, current_user)
    return record


@router.get("/{record_id}/versions", response_model=list[RecordVersionResponse])
async def versions(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """获取病历版本历史"""
    return await get_record_versions(db, record_id)


@router.get("/{record_id}/versions/compare", response_model=VersionCompareResponse)
async def version_compare(
    record_id: uuid.UUID,
    v1: str = Query(..., description="版本号1"),
    v2: str = Query(..., description="版本号2"),
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """对比两个版本的差异"""
    return await compare_versions(db, record_id, v1, v2)


@router.get("/{record_id}/versions/{version}", response_model=VersionDetailResponse)
async def version_detail(
    record_id: uuid.UUID,
    version: str,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """获取单个版本详情"""
    return await get_version_detail(db, record_id, version)


@router.post("/{record_id}/versions/{version}/rollback", response_model=RecordResponse)
async def version_rollback(
    record_id: uuid.UUID,
    version: str,
    current_user: User = Depends(require_record_permission("write")),
    db: AsyncSession = Depends(get_db),
):
    """回滚到指定版本"""
    return await rollback_to_version(db, record_id, version, current_user)


@router.get("/{record_id}/timeline")
async def timeline(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """获取病历时间轴事件"""
    return await get_record_timeline(db, record_id)


@router.get(
    "/{record_id}/treatment-timeline",
    response_model=list[TreatmentTimelineItem],
)
async def treatment_timeline(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """获取治疗时间线（按日期排序，包含关联媒体文件）"""
    treatments = await get_treatment_timeline(db, record_id)
    return [TreatmentTimelineItem.model_validate(t) for t in treatments]


@router.get("/{record_id}/permissions", response_model=list[PermissionResponse])
async def permissions(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """查看病历权限列表"""
    return await get_record_permissions(db, record_id)
