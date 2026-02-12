import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, CreatedAtMixin, UUIDMixin


class ClinicalExamination(UUIDMixin, CreatedAtMixin, Base):
    __tablename__ = "clinical_examinations"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=False
    )
    body_temperature: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_condition_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mental_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    symptoms: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    physical_findings: Mapped[str | None] = mapped_column(Text, nullable=True)

    record = relationship("MedicalRecord", back_populates="examinations")


class Diagnosis(UUIDMixin, CreatedAtMixin, Base):
    __tablename__ = "diagnoses"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=False
    )
    diagnosis_type: Mapped[str] = mapped_column(String(20), nullable=False)
    disease_name: Mapped[str] = mapped_column(String(200), nullable=False)
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    basis: Mapped[str | None] = mapped_column(Text, nullable=True)

    record = relationship("MedicalRecord", back_populates="diagnoses")


class Treatment(UUIDMixin, CreatedAtMixin, Base):
    __tablename__ = "treatments"

    record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("medical_records.id"), nullable=False
    )
    treatment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    medication_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    route: Mapped[str | None] = mapped_column(String(50), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    management_advice: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sort_order: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)

    record = relationship("MedicalRecord", back_populates="treatments")
    media_files = relationship("MediaFile", back_populates="treatment", lazy="selectin")
