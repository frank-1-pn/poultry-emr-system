import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_record_permission
from app.core.database import get_db
from app.models.user import User
from app.services.export_service import (
    export_record_pdf,
    export_record_word,
    export_records_excel,
)

router = APIRouter(prefix="/export", tags=["导出"])


@router.get("/records/{record_id}/pdf")
async def export_pdf(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """导出单个病历为 PDF"""
    content = await export_record_pdf(db, record_id)
    return StreamingResponse(
        iter([content]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=record_{record_id}.pdf"},
    )


@router.get("/records/{record_id}/word")
async def export_word(
    record_id: uuid.UUID,
    current_user: User = Depends(require_record_permission("read")),
    db: AsyncSession = Depends(get_db),
):
    """导出单个病历为 Word 文档"""
    content = await export_record_word(db, record_id)
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=record_{record_id}.docx"},
    )


@router.get("/records/excel")
async def export_excel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量导出病历为 Excel（导出当前用户有权查看的所有病历）"""
    content = await export_records_excel(db, current_user)
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=records_export.xlsx"},
    )
