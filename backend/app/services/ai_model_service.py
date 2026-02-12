"""AI 模型管理服务"""

import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import ChatMessage
from app.adapters.factory import LLMAdapterFactory
from app.models.ai_model import AIModel, AIUsageLog
from app.schemas.ai_model import (
    AIModelCreate,
    AIModelResponse,
    AIModelTestResponse,
    AIModelUpdate,
    UsageStatsResponse,
)
from app.utils.encryption import decrypt_api_key, encrypt_api_key


def _model_to_response(model: AIModel) -> AIModelResponse:
    return AIModelResponse(
        id=model.id,
        provider=model.provider,
        model_name=model.model_name,
        display_name=model.display_name,
        api_endpoint=model.api_endpoint,
        api_key_set=bool(model.api_key_encrypted),
        is_active=model.is_active,
        is_default=model.is_default,
        config=model.config,
        usage_limit=model.usage_limit,
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


async def create_model(
    db: AsyncSession, data: AIModelCreate, user_id: uuid.UUID
) -> AIModelResponse:
    """创建 AI 模型配置"""
    # 如果设为默认，先取消其他默认
    if data.is_default:
        await _clear_default(db)

    model = AIModel(
        provider=data.provider.value,
        model_name=data.model_name,
        display_name=data.display_name,
        api_key_encrypted=encrypt_api_key(data.api_key),
        api_endpoint=data.api_endpoint,
        config=data.config.model_dump() if data.config else None,
        usage_limit=data.usage_limit.model_dump() if data.usage_limit else None,
        is_default=data.is_default,
        created_by=user_id,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return _model_to_response(model)


async def update_model(
    db: AsyncSession, model_id: uuid.UUID, data: AIModelUpdate
) -> AIModelResponse:
    """更新 AI 模型配置"""
    model = await _get_model_or_404(db, model_id)

    if data.display_name is not None:
        model.display_name = data.display_name
    if data.api_key is not None:
        model.api_key_encrypted = encrypt_api_key(data.api_key)
    if data.api_endpoint is not None:
        model.api_endpoint = data.api_endpoint
    if data.config is not None:
        model.config = data.config.model_dump()
    if data.usage_limit is not None:
        model.usage_limit = data.usage_limit.model_dump()
    if data.is_active is not None:
        model.is_active = data.is_active

    await db.flush()
    await db.refresh(model)
    return _model_to_response(model)


async def delete_model(db: AsyncSession, model_id: uuid.UUID) -> AIModelResponse:
    """软删除（停用）AI 模型"""
    model = await _get_model_or_404(db, model_id)
    model.is_active = False
    model.is_default = False
    await db.flush()
    await db.refresh(model)
    return _model_to_response(model)


async def list_models(db: AsyncSession) -> list[AIModelResponse]:
    """列出所有 AI 模型"""
    result = await db.execute(
        select(AIModel).order_by(AIModel.is_default.desc(), AIModel.created_at.desc())
    )
    models = result.scalars().all()
    return [_model_to_response(m) for m in models]


async def get_model(db: AsyncSession, model_id: uuid.UUID) -> AIModelResponse:
    """获取单个 AI 模型"""
    model = await _get_model_or_404(db, model_id)
    return _model_to_response(model)


async def set_default(db: AsyncSession, model_id: uuid.UUID) -> AIModelResponse:
    """设置默认模型"""
    model = await _get_model_or_404(db, model_id)
    if not model.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法将已停用的模型设为默认",
        )
    await _clear_default(db)
    model.is_default = True
    await db.flush()
    await db.refresh(model)
    return _model_to_response(model)


async def test_model(
    db: AsyncSession, model_id: uuid.UUID, test_message: str
) -> AIModelTestResponse:
    """测试模型连通性"""
    model = await _get_model_or_404(db, model_id)
    if not model.api_key_encrypted:
        return AIModelTestResponse(success=False, error="未设置 API Key")

    try:
        api_key = decrypt_api_key(model.api_key_encrypted)
        adapter = LLMAdapterFactory.create_adapter(
            provider=model.provider,
            api_key=api_key,
            model_name=model.model_name,
            api_endpoint=model.api_endpoint,
            config=model.config,
        )
        messages = [ChatMessage(role="user", content=test_message)]
        result = await adapter.chat_completion(messages)

        return AIModelTestResponse(
            success=True,
            response=result.content,
            latency_ms=result.latency_ms,
            tokens=result.total_tokens,
            cost=result.cost,
        )
    except Exception as e:
        return AIModelTestResponse(success=False, error=str(e))


async def log_usage(
    db: AsyncSession,
    model_id: uuid.UUID,
    user_id: uuid.UUID,
    request_tokens: int = 0,
    response_tokens: int = 0,
    total_tokens: int = 0,
    cost: float = 0.0,
    latency_ms: int = 0,
    status_val: str = "success",
    error_message: str | None = None,
    conversation_id: uuid.UUID | None = None,
) -> AIUsageLog:
    """记录使用日志"""
    log = AIUsageLog(
        model_id=model_id,
        user_id=user_id,
        conversation_id=conversation_id,
        request_tokens=request_tokens,
        response_tokens=response_tokens,
        total_tokens=total_tokens,
        cost=cost,
        latency_ms=latency_ms,
        status=status_val,
        error_message=error_message,
    )
    db.add(log)
    await db.flush()
    return log


async def get_usage_stats(
    db: AsyncSession,
    start_date: date | None = None,
    end_date: date | None = None,
    model_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
) -> list[UsageStatsResponse]:
    """获取使用统计"""
    query = (
        select(
            AIUsageLog.model_id,
            AIModel.model_name,
            func.count().label("total_requests"),
            func.sum(AIUsageLog.total_tokens).label("total_tokens"),
            func.sum(AIUsageLog.cost).label("total_cost"),
            func.sum(case((AIUsageLog.status == "success", 1), else_=0)).label("success_count"),
            func.sum(case((AIUsageLog.status != "success", 1), else_=0)).label("error_count"),
            func.avg(AIUsageLog.latency_ms).label("avg_latency_ms"),
        )
        .join(AIModel, AIUsageLog.model_id == AIModel.id)
        .group_by(AIUsageLog.model_id, AIModel.model_name)
    )

    if start_date:
        query = query.where(AIUsageLog.created_at >= datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc))
    if end_date:
        query = query.where(AIUsageLog.created_at < datetime(end_date.year, end_date.month, end_date.day + 1, tzinfo=timezone.utc) if end_date.day < 28 else AIUsageLog.created_at <= datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc))
    if model_id:
        query = query.where(AIUsageLog.model_id == model_id)
    if user_id:
        query = query.where(AIUsageLog.user_id == user_id)

    result = await db.execute(query)
    rows = result.all()

    return [
        UsageStatsResponse(
            model_id=row.model_id,
            model_name=row.model_name,
            total_requests=row.total_requests or 0,
            total_tokens=int(row.total_tokens or 0),
            total_cost=float(row.total_cost or 0),
            success_count=int(row.success_count or 0),
            error_count=int(row.error_count or 0),
            avg_latency_ms=float(row.avg_latency_ms or 0),
        )
        for row in rows
    ]


async def check_usage_limit(
    db: AsyncSession, model_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """检查是否超出使用限额，返回 True 表示允许"""
    model = await _get_model_or_404(db, model_id)
    limits = model.usage_limit
    if not limits:
        return True

    # 查询今日使用量
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    query = select(
        func.count().label("count"),
        func.sum(AIUsageLog.total_tokens).label("tokens"),
        func.sum(AIUsageLog.cost).label("cost"),
    ).where(
        and_(
            AIUsageLog.model_id == model_id,
            AIUsageLog.user_id == user_id,
            AIUsageLog.created_at >= today_start,
        )
    )
    result = await db.execute(query)
    row = result.one()

    daily_requests = limits.get("daily_requests")
    if daily_requests and (row.count or 0) >= daily_requests:
        return False

    daily_tokens = limits.get("daily_tokens")
    if daily_tokens and (row.tokens or 0) >= daily_tokens:
        return False

    daily_cost = limits.get("daily_cost")
    if daily_cost and (row.cost or 0) >= daily_cost:
        return False

    return True


# --- Helpers ---


async def _get_model_or_404(db: AsyncSession, model_id: uuid.UUID) -> AIModel:
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI 模型不存在",
        )
    return model


async def _clear_default(db: AsyncSession) -> None:
    result = await db.execute(select(AIModel).where(AIModel.is_default == True))
    for m in result.scalars().all():
        m.is_default = False
    await db.flush()
