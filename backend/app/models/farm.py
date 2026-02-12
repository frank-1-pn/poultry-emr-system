from sqlalchemy import Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin, UUIDMixin


class Farm(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "farms"

    farm_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    owner_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    province: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(50), nullable=True)
    district: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    location_lat: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    scale: Mapped[str | None] = mapped_column(String(20), nullable=True)
    poultry_types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    records = relationship("MedicalRecord", back_populates="farm")
