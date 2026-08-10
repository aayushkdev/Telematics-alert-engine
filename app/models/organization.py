from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    drivers: Mapped[list["Driver"]] = relationship(back_populates="organization")
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="organization")
    telemetry: Mapped[list["Telemetry"]] = relationship(back_populates="organization")
    rules: Mapped[list["Rule"]] = relationship(back_populates="organization")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="organization")
