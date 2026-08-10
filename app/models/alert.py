from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AlertStatus


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_rule_vehicle_status", "rule_id", "vehicle_id", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    rule_id: Mapped[int] = mapped_column(ForeignKey("rules.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), nullable=False)
    driver_id: Mapped[int | None] = mapped_column(ForeignKey("drivers.id"), nullable=True)
    status: Mapped[AlertStatus] = mapped_column(nullable=False, default=AlertStatus.OPEN)
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    latest_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="alerts")
    rule: Mapped["Rule"] = relationship(back_populates="alerts")
    vehicle: Mapped["Vehicle"] = relationship(back_populates="alerts")