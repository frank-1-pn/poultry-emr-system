import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, UUIDMixin


class RecordTag(UUIDMixin, CreatedAtMixin, Base):
    __tablename__ = "record_tags"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=False
    )
    tag: Mapped[str] = mapped_column(String(50), nullable=False)

    record = relationship("MedicalRecord", back_populates="tags")
