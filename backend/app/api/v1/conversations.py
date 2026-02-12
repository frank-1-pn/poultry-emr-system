"""AI 对话式病历录入 REST API"""

import math
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.conversation import (
    AIReplyResponse,
    ConfirmRecordRequest,
    ConversationCompleteResponse,
    ConversationCreate,
    ConversationListItem,
    ConversationMessageResponse,
    ConversationResponse,
    ConversationTagUpdate,
    SendMessageRequest,
    SimilarCaseItem,
)
from app.services import conversation_service

router = APIRouter(prefix="/conversations", tags=["AI对话"])


@router.post("", response_model=ConversationResponse)
async def create_conversation(
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 AI 对话会话"""
    conversation, _ = await conversation_service.create_conversation(
        db, current_user,
        record_id=data.record_id,
        farm_id=data.farm_id,
        tags=data.tags,
    )
    return conversation


@router.get("", response_model=PaginatedResponse[ConversationListItem])
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    farm_id: uuid.UUID | None = Query(None),
    tag: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话列表"""
    conversations, total = await conversation_service.list_conversations(
        db, current_user, page=page, page_size=page_size,
        status_filter=status, farm_id=farm_id, tag=tag,
    )
    return PaginatedResponse(
        items=[ConversationListItem.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取对话详情"""
    conversation = await conversation_service.get_conversation(
        db, conversation_id, current_user.id
    )
    return conversation


@router.post("/{conversation_id}/messages", response_model=AIReplyResponse)
async def send_message(
    conversation_id: uuid.UUID,
    data: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发送消息（HTTP 方式）"""
    result = await conversation_service.send_message(
        db, conversation_id, current_user,
        content=data.content, audio_url=data.audio_url,
    )
    similar_cases = [
        SimilarCaseItem(**c) for c in result.get("similar_cases", [])
    ]
    return AIReplyResponse(
        message=ConversationMessageResponse.model_validate(result["message"]),
        collected_info=result["collected_info"],
        confidence_scores=result["confidence_scores"],
        needs_confirmation=result["needs_confirmation"],
        completeness=result["completeness"],
        similar_cases=similar_cases,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=PaginatedResponse[ConversationMessageResponse],
)
async def get_messages(
    conversation_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取消息历史"""
    messages, total = await conversation_service.get_messages(
        db, conversation_id, current_user.id, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=[ConversationMessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total else 0,
    )


@router.post(
    "/{conversation_id}/complete", response_model=ConversationCompleteResponse
)
async def complete_conversation(
    conversation_id: uuid.UUID,
    data: ConfirmRecordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """确认完成对话，保存病历"""
    result = await conversation_service.complete_conversation(
        db, conversation_id, current_user,
        confirmed=data.confirmed, corrections=data.corrections,
    )
    return ConversationCompleteResponse(
        conversation=ConversationResponse.model_validate(result["conversation"]),
        record_id=result["record_id"],
        record_no=result["record_no"],
    )


@router.post("/{conversation_id}/pause", response_model=ConversationResponse)
async def pause_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """暂停对话"""
    conversation = await conversation_service.pause_conversation(
        db, conversation_id, current_user.id
    )
    return conversation


@router.post("/{conversation_id}/resume", response_model=ConversationResponse)
async def resume_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """恢复对话"""
    conversation = await conversation_service.resume_conversation(
        db, conversation_id, current_user.id
    )
    return conversation


@router.patch("/{conversation_id}/tags", response_model=ConversationResponse)
async def update_tags(
    conversation_id: uuid.UUID,
    data: ConversationTagUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新对话标签"""
    conversation = await conversation_service.update_tags(
        db, conversation_id, current_user.id, data.tags
    )
    return conversation
