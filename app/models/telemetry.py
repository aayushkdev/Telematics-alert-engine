from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, Float, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EngineState


class Telemetry(Base):
    __tablename__ = "telemetry"
    __table_args__ = (Index("ix_telemetry_vehicle_timestamp", "vehicle_id", "timestamp"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    speed_mph: Mapped[float | None] = mapped_column(Float, nullable=True)
    fuel_level_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    engine_state: Mapped[EngineState | None] = mapped_column(nullable=True)
    odometer_miles: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="telemetry")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="telemetry")
