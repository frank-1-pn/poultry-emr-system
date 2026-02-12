import logging
import math
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.record import RecordListItem
from app.services.search_service import search_records

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["搜索"])


# ---- Schemas ----

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="语义搜索文本")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数")
    threshold: float = Field(0.3, ge=0.0, le=1.0, description="相似度阈值")


class SimilarRecordItem(BaseModel):
    id: str
    record_no: str
    poultry_type: str
    breed: str | None = None
    primary_diagnosis: str | None = None
    severity: str | None = None
    visit_date: str | None = None
    similarity: float


class SemanticSearchResponse(BaseModel):
    items: list[SimilarRecordItem]
    total: int


# ---- Endpoints ----

@router.get("", response_model=PaginatedResponse[RecordListItem])
async def search(
    keyword: str = Query(..., min_length=1, max_length=100, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    poultry_type: str | None = None,
    severity: str | None = None,
    farm_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """全文搜索病历（带权限过滤）"""
    records, total = await search_records(
        db, current_user, keyword, page, page_size,
        poultry_type, severity, farm_id,
    )
    return PaginatedResponse(
        items=[RecordListItem.model_validate(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.post("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    body: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """语义搜索病历 — 基于 embedding 向量相似度"""
    from app.services.embedding_service import search_similar_records

    try:
        results = await search_similar_records(
            db,
            query_text=body.query,
            user_id=current_user.id,
            is_master=(current_user.role == "master"),
            top_k=body.top_k,
            threshold=body.threshold,
        )
    except Exception as e:
        logger.error("语义搜索失败: %s", e)
        return SemanticSearchResponse(items=[], total=0)

    items = [
        SimilarRecordItem(
            id=r["id"],
            record_no=r["record_no"],
            poultry_type=r["poultry_type"],
            breed=r.get("breed"),
            primary_diagnosis=r.get("primary_diagnosis"),
            severity=r.get("severity"),
            visit_date=r.get("visit_date"),
            similarity=r["similarity"],
        )
        for r in results
    ]
    return SemanticSearchResponse(items=items, total=len(items))
