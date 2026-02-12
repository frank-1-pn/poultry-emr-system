"""AI 模型管理 API（Master only）"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_master
from app.core.database import get_db
from app.models.user import User
from app.schemas.ai_model import (
    AIModelCreate,
    AIModelListResponse,
    AIModelResponse,
    AIModelTestRequest,
    AIModelTestResponse,
    AIModelUpdate,
    UsageStatsResponse,
)
from app.schemas.common import MessageResponse
from app.services import ai_model_service

router = APIRouter(prefix="/ai-models", tags=["AI模型管理"])


@router.post("", response_model=AIModelResponse)
async def create_model(
    data: AIModelCreate,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """创建 AI 模型配置"""
    return await ai_model_service.create_model(db, data, master.id)


@router.get("", response_model=AIModelListResponse)
async def list_models(
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """列出所有 AI 模型"""
    models = await ai_model_service.list_models(db)
    return AIModelListResponse(items=models, total=len(models))


@router.get("/usage-stats", response_model=list[UsageStatsResponse])
async def usage_stats(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    model_id: uuid.UUID | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """获取 AI 使用统计"""
    return await ai_model_service.get_usage_stats(db, start_date, end_date, model_id, user_id)


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model(
    model_id: uuid.UUID,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """获取单个 AI 模型详情"""
    return await ai_model_service.get_model(db, model_id)


@router.put("/{model_id}", response_model=AIModelResponse)
async def update_model(
    model_id: uuid.UUID,
    data: AIModelUpdate,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """更新 AI 模型配置"""
    return await ai_model_service.update_model(db, model_id, data)


@router.delete("/{model_id}", response_model=AIModelResponse)
async def delete_model(
    model_id: uuid.UUID,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """停用 AI 模型"""
    return await ai_model_service.delete_model(db, model_id)


@router.post("/{model_id}/set-default", response_model=AIModelResponse)
async def set_default_model(
    model_id: uuid.UUID,
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """设置默认 AI 模型"""
    return await ai_model_service.set_default(db, model_id)


@router.post("/{model_id}/test", response_model=AIModelTestResponse)
async def test_model(
    model_id: uuid.UUID,
    data: AIModelTestRequest = AIModelTestRequest(),
    master: User = Depends(require_master),
    db: AsyncSession = Depends(get_db),
):
    """测试 AI 模型连通性"""
    return await ai_model_service.test_model(db, model_id, data.test_message)
