"""用户记忆服务 — 跨对话 session 的持久记忆"""

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_memory import UserMemory

logger = logging.getLogger(__name__)


async def get_or_create_memory(
    db: AsyncSession, user_id: uuid.UUID
) -> UserMemory:
    """获取用户记忆，不存在则创建空记忆"""
    result = await db.execute(
        select(UserMemory).where(UserMemory.user_id == user_id)
    )
    memory = result.scalar_one_or_none()
    if not memory:
        memory = UserMemory(
            user_id=user_id,
            content={
                "preferences": {},
                "farm_context": {},
                "common_issues": [],
                "notes": [],
            },
        )
        db.add(memory)
        await db.flush()
        await db.refresh(memory)
    return memory


async def update_memory(
    db: AsyncSession, user_id: uuid.UUID, content: dict
) -> UserMemory:
    """直接更新记忆内容"""
    memory = await get_or_create_memory(db, user_id)
    memory.content = content
    memory.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(memory)
    return memory


async def build_memory_context(
    db: AsyncSession, user_id: uuid.UUID
) -> str:
    """构建用于注入到 system prompt 的记忆上下文"""
    memory = await get_or_create_memory(db, user_id)
    content = memory.content

    if not content or content == {"preferences": {}, "farm_context": {}, "common_issues": [], "notes": []}:
        return ""

    parts = ["## 用户历史记忆（跨对话持久化）"]

    preferences = content.get("preferences", {})
    if preferences:
        parts.append("### 用户偏好")
        for k, v in preferences.items():
            parts.append(f"- {k}: {v}")

    farm_context = content.get("farm_context", {})
    if farm_context:
        parts.append("### 养殖场信息")
        for k, v in farm_context.items():
            parts.append(f"- {k}: {v}")

    common_issues = content.get("common_issues", [])
    if common_issues:
        parts.append("### 常见问题历史")
        for issue in common_issues[-5:]:  # 最近5条
            parts.append(f"- {issue}")

    notes = content.get("notes", [])
    if notes:
        parts.append("### 备注")
        for note in notes[-5:]:
            parts.append(f"- {note}")

    return "\n".join(parts)


async def extract_memory_updates(
    db: AsyncSession,
    user_id: uuid.UUID,
    messages: list[dict],
) -> UserMemory:
    """从对话消息中提取关键信息更新记忆

    这里使用简单的关键词匹配提取，不调用 LLM 以避免额外开销。
    后续可升级为 LLM 提取。
    """
    memory = await get_or_create_memory(db, user_id)
    content = dict(memory.content)
    notes = list(content.get("notes", []))
    farm_context = dict(content.get("farm_context", {}))

    for msg in messages:
        if msg.get("role") != "user":
            continue
        text = msg.get("content", "")

        # 提取养殖场规模信息
        if "只" in text and any(kw in text for kw in ["养了", "存栏", "规模"]):
            farm_context["recent_mention"] = text[:100]

        # 提取常用品种信息
        for breed_kw in ["蛋鸡", "肉鸡", "白羽", "三黄", "麻鸡", "鸭", "鹅"]:
            if breed_kw in text:
                farm_context["common_breed"] = breed_kw
                break

    content["farm_context"] = farm_context
    content["notes"] = notes[-10:]  # 保留最近10条

    memory.content = content
    memory.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(memory)
    return memory
