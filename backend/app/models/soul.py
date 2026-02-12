import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDMixin


class SoulConfig(UUIDMixin, TimestampMixin, Base):
    """Soul 配置表 — 管理员维护的 AI 人设 Markdown"""
    __tablename__ = "soul_configs"

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_compressed: Mapped[str] = mapped_column(Text, nullable=False, default="")
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    compressed_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )


class MemoryCategory(str, enum.Enum):
    style = "style"
    skill = "skill"
    habit = "habit"
    improvement = "improvement"
    feedback = "feedback"


class MemorySource(str, enum.Enum):
    manual = "manual"
    auto = "auto"


class MemoryEntry(UUIDMixin, CreatedAtMixin, Base):
    """记忆条目表 — 随时间积累的 AI 记忆"""
    __tablename__ = "memory_entries"

    category: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    importance: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
