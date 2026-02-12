"""AI 对话会话和消息表"""

import uuid

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, TimestampMixin, UUIDMixin


class Conversation(UUIDMixin, TimestampMixin, Base):
    """AI 对话会话表"""

    __tablename__ = "conversations"

    record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farms.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
    )  # active | completed | paused | cancelled
    state: Mapped[str] = mapped_column(
        String(30), nullable=False, default="initializing"
    )  # initializing | collecting_basic | collecting_symptoms | collecting_diagnosis | collecting_treatment | confirming | completed
    session_number: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)
    collected_info: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    record = relationship("MedicalRecord", foreign_keys=[record_id])
    farm = relationship("Farm", foreign_keys=[farm_id])
    messages = relationship(
        "ConversationMessage", back_populates="conversation",
        cascade="all, delete-orphan", order_by="ConversationMessage.created_at",
    )

    __table_args__ = (
        Index("idx_conversations_user", "user_id"),
        Index("idx_conversations_record", "record_id"),
        Index("idx_conversations_farm", "farm_id"),
        Index("idx_conversations_status", "status"),
        Index("idx_conversations_created", "created_at"),
    )


class ConversationMessage(UUIDMixin, CreatedAtMixin, Base):
    """对话消息表"""

    __tablename__ = "conversation_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user | assistant | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index("idx_conv_messages_conversation", "conversation_id"),
        Index("idx_conv_messages_created", "created_at"),
    )
