import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, UUIDMixin


class LabTest(UUIDMixin, CreatedAtMixin, Base):
    __tablename__ = "lab_tests"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=False
    )
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)
    test_result: Mapped[str | None] = mapped_column(String(100), nullable=True)
    result_value: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    test_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lab_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    report_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    record = relationship("MedicalRecord", back_populates="lab_tests")
