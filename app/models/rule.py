from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RuleType


class Rule(Base):
    __tablename__ = "rules"
    __table_args__ = (Index("ix_rules_org_enabled", "organization_id", "enabled"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id"), nullable=False
    )
    vehicle_id: Mapped[int | None] = mapped_column(
        ForeignKey("vehicles.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    center_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    center_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    window_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_matching_events: Mapped[int | None] = mapped_column(Integer, nullable=True)
    suppress_for_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    escalate_after_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    organization: Mapped["Organization"] = relationship(back_populates="rules")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="rule")
