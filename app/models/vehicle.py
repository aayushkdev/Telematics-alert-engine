from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("vin"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    current_driver_id: Mapped[int | None] = mapped_column(
        ForeignKey("drivers.id"), nullable=True
    )
    vin: Mapped[str] = mapped_column(String(17), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    organization: Mapped["Organization"] = relationship(back_populates="vehicles")
    current_driver: Mapped["Driver"] = relationship(back_populates="vehicles")
    telemetry: Mapped[list["Telemetry"]] = relationship(back_populates="vehicle")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="vehicle")
