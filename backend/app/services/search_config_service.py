import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_config import SearchConfig
from app.schemas.search_config import SearchConfigUpdate

# 默认配置
DEFAULT_CONFIGS = [
    {
        "config_key": "search_weights",
        "config_value": {
            "primary_diagnosis": 3.0,
            "symptoms": 2.0,
            "poultry_type": 1.5,
            "breed": 1.0,
            "treatment": 1.0,
            "notes": 0.5,
        },
        "description": "全文搜索字段权重配置",
    },
    {
        "config_key": "search_options",
        "config_value": {
            "max_results": 50,
            "min_score": 0.1,
            "enable_fuzzy": True,
            "fuzzy_distance": 2,
            "highlight_enabled": True,
        },
        "description": "搜索行为选项",
    },
    {
        "config_key": "embedding_config",
        "config_value": {
            "model": "text-embedding-ada-002",
            "dimension": 1536,
            "batch_size": 100,
            "auto_embed": True,
        },
        "description": "向量嵌入配置",
    },
]


async def get_config(db: AsyncSession, config_key: str) -> SearchConfig:
    result = await db.execute(
        select(SearchConfig).where(SearchConfig.config_key == config_key)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"配置项 '{config_key}' 不存在",
        )
    return config


async def update_config(
    db: AsyncSession,
    config_key: str,
    data: SearchConfigUpdate,
    user_id: uuid.UUID,
) -> SearchConfig:
    config = await get_config(db, config_key)
    config.config_value = data.config_value
    if data.description is not None:
        config.description = data.description
    config.updated_by = user_id
    await db.flush()
    await db.refresh(config)
    return config


async def list_configs(db: AsyncSession) -> list[SearchConfig]:
    result = await db.execute(
        select(SearchConfig).order_by(SearchConfig.config_key)
    )
    return list(result.scalars().all())


async def init_defaults(db: AsyncSession) -> list[SearchConfig]:
    """初始化默认配置（仅在配置表为空时执行）"""
    result = await db.execute(select(SearchConfig).limit(1))
    if result.scalar_one_or_none() is not None:
        return []

    created = []
    for cfg in DEFAULT_CONFIGS:
        config = SearchConfig(**cfg)
        db.add(config)
        created.append(config)

    await db.flush()
    return created
