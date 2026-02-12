"""提醒表"""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, UUIDMixin


class Reminder(UUIDMixin, CreatedAtMixin, Base):
    """AI 生成的跟进提醒"""

    __tablename__ = "reminders"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    reminder_date: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending | confirmed | dismissed
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    record = relationship("MedicalRecord", foreign_keys=[record_id])
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_reminders_user_date", "user_id", "reminder_date"),
        Index("idx_reminders_record", "record_id"),
        Index("idx_reminders_status", "status"),
    )
