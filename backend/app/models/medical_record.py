import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean, Column, Date, ForeignKey, Index, Integer, Numeric, String, Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None

from app.core.database import Base, TimestampMixin, UUIDMixin


class MedicalRecord(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "medical_records"

    record_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(10), default="1.0")
    veterinarian_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    farm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farms.id"), nullable=True
    )
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    poultry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    breed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    affected_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_flock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    onset_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    primary_diagnosis: Mapped[str | None] = mapped_column(String(200), nullable=True)
    icd_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_reportable: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    record_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    record_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_status: Mapped[str] = mapped_column(String(20), default="pending")
    # pgvector embedding (1536 维)
    if Vector is not None:
        embedding_vector = mapped_column(Vector(1536), nullable=True)
    else:
        embedding_vector = Column("embedding_vector", nullable=True)
    data_quality_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    current_version: Mapped[str] = mapped_column(String(10), default="1.0")

    # Relationships
    owner = relationship("User", back_populates="owned_records", foreign_keys=[owner_id])
    veterinarian = relationship("User", foreign_keys=[veterinarian_id])
    farm = relationship("Farm", back_populates="records")
    examinations = relationship("ClinicalExamination", back_populates="record", cascade="all, delete-orphan")
    diagnoses = relationship("Diagnosis", back_populates="record", cascade="all, delete-orphan")
    treatments = relationship("Treatment", back_populates="record", cascade="all, delete-orphan")
    media_files = relationship("MediaFile", back_populates="record", cascade="all, delete-orphan")
    lab_tests = relationship("LabTest", back_populates="record", cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="record", cascade="all, delete-orphan")
    tags = relationship("RecordTag", back_populates="record", cascade="all, delete-orphan")
    versions = relationship("RecordVersion", back_populates="record", cascade="all, delete-orphan")
    permissions = relationship("RecordPermission", back_populates="record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_records_owner", "owner_id"),
        Index("idx_records_vet", "veterinarian_id"),
        Index("idx_records_farm", "farm_id"),
        Index("idx_records_visit_date", "visit_date"),
        Index("idx_records_diagnosis", "primary_diagnosis"),
        Index("idx_records_status", "status"),
        Index("idx_records_created", "created_at"),
    )
