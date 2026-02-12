import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.media import MediaFile
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.upload import MediaFileCreate, MediaFileResponse, STSTokenResponse
from app.services.oss_service import delete_oss_file, generate_sts_token

router = APIRouter(prefix="/upload", tags=["文件上传"])


@router.get("/sts-token", response_model=STSTokenResponse)
async def get_sts_token(
    current_user: User = Depends(get_current_user),
):
    """获取OSS临时上传凭证"""
    token_data = await generate_sts_token()
    return STSTokenResponse(**token_data)


@router.post("/callback", response_model=MediaFileResponse)
async def upload_callback(
    data: MediaFileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """注册已上传的文件到media_files表"""
    media = MediaFile(
        record_id=data.record_id,
        file_type=data.file_type,
        media_type=data.media_type,
        oss_key=data.oss_key,
        url=data.url,
        thumbnail_url=data.thumbnail_url,
        file_size=data.file_size,
        width=data.width,
        height=data.height,
        duration=data.duration,
        description=data.description,
        captured_at=data.captured_at,
    )
    db.add(media)
    await db.flush()
    return media


@router.delete("/{file_id}", response_model=MessageResponse)
async def delete_file(
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除已上传的文件（从 OSS 和数据库中删除）"""
    result = await db.execute(
        select(MediaFile).where(MediaFile.id == file_id)
    )
    media = result.scalar_one_or_none()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在"
        )

    # 从 OSS 删除
    await delete_oss_file(media.oss_key)

    # 从数据库删除
    await db.delete(media)
    await db.flush()

    return MessageResponse(message="文件已删除")
