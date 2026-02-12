"""AI 对话 WebSocket 端点"""

import json
import uuid
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import decode_token
from app.models.user import User
from app.schemas.conversation import (
    ConversationCompleteResponse,
    ConversationMessageResponse,
    ConversationResponse,
    WSIncomingMessage,
    WSOutgoingMessage,
)
from app.services import conversation_service

logger = logging.getLogger(__name__)

router = APIRouter()


async def _authenticate_ws(token: str, db: AsyncSession) -> User | None:
    """通过 JWT token 认证 WebSocket 连接"""
    payload = decode_token(token)
    user_id = payload.get("sub")
    token_type = payload.get("type")
    if not user_id or token_type != "access":
        return None
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None
    return user


@router.websocket("/api/v1/conversations/{conversation_id}/ws")
async def conversation_ws(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    token: str = "",
):
    """WebSocket 端点 - AI 对话流式交互

    连接方式: ws://host/api/v1/conversations/{id}/ws?token=xxx

    入站消息格式:
    - {"type": "user_message", "content": "...", "audio_url": "..."}
    - {"type": "ping"}
    - {"type": "confirm", "confirmed": true, "corrections": {...}}

    出站消息格式:
    - {"type": "stream_token", "content": "..."}
    - {"type": "stream_end", "content": "...", "collected_info": {...}, ...}
    - {"type": "assistant_message", "content": "...", "collected_info": {...}, ...}
    - {"type": "pong"}
    - {"type": "error", "error": "..."}
    """
    if not token:
        await websocket.close(code=4001, reason="缺少认证 token")
        return

    async with AsyncSessionLocal() as db:
        user = await _authenticate_ws(token, db)
        if not user:
            await websocket.accept()
            await websocket.send_json({"type": "error", "error": "认证失败"})
            await websocket.close(code=4001, reason="认证失败")
            return

        # 验证对话归属
        try:
            conversation = await conversation_service.get_conversation(
                db, conversation_id, user.id
            )
        except Exception:
            await websocket.accept()
            await websocket.send_json({"type": "error", "error": "对话不存在或无权访问"})
            await websocket.close(code=4004, reason="对话不存在")
            return

        await websocket.accept()
        logger.info("WebSocket 连接建立: conversation=%s user=%s", conversation_id, user.id)

    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
                msg = WSIncomingMessage(**data)
            except (json.JSONDecodeError, Exception) as e:
                await websocket.send_json(
                    WSOutgoingMessage(type="error", error=f"消息格式错误: {e}").model_dump()
                )
                continue

            if msg.type == "ping":
                await websocket.send_json(WSOutgoingMessage(type="pong").model_dump())
                continue

            if msg.type == "user_message":
                if not msg.content:
                    await websocket.send_json(
                        WSOutgoingMessage(type="error", error="消息内容不能为空").model_dump()
                    )
                    continue

                # 使用独立 session 处理每条消息
                async with AsyncSessionLocal() as db:
                    try:
                        async for chunk in conversation_service.send_message_stream(
                            db, conversation_id, user,
                            content=msg.content, audio_url=msg.audio_url,
                        ):
                            await websocket.send_json(
                                WSOutgoingMessage(**chunk).model_dump(exclude_none=True)
                            )
                        await db.commit()
                    except Exception as e:
                        await db.rollback()
                        logger.error("WebSocket 消息处理失败: %s", e)
                        await websocket.send_json(
                            WSOutgoingMessage(type="error", error=str(e)).model_dump()
                        )

            elif msg.type == "confirm":
                async with AsyncSessionLocal() as db:
                    try:
                        result = await conversation_service.complete_conversation(
                            db, conversation_id, user,
                            confirmed=msg.confirmed or False,
                            corrections=msg.corrections,
                        )
                        await db.commit()
                        await websocket.send_json({
                            "type": "completed",
                            "record_id": str(result["record_id"]),
                            "record_no": result["record_no"],
                        })
                    except Exception as e:
                        await db.rollback()
                        logger.error("WebSocket 确认保存失败: %s", e)
                        await websocket.send_json(
                            WSOutgoingMessage(type="error", error=str(e)).model_dump()
                        )
            else:
                await websocket.send_json(
                    WSOutgoingMessage(type="error", error=f"未知消息类型: {msg.type}").model_dump()
                )

    except WebSocketDisconnect:
        logger.info("WebSocket 断开: conversation=%s", conversation_id)
    except Exception as e:
        logger.error("WebSocket 异常: %s", e)
        try:
            await websocket.close(code=1011, reason="服务器内部错误")
        except Exception:
            pass
