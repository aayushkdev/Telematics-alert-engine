from datetime import datetime

from app.models.enums import AlertStatus
from app.schemas.base import BaseSchema


class AlertResponse(BaseSchema):
    id: int
    organization_id: int
    rule_id: int
    vehicle_id: int
    driver_id: int | None
    status: AlertStatus
    opened_at: datetime
    acknowledged_at: datetime | None
    escalated_at: datetime | None
    resolved_at: datetime | None
    last_seen_at: datetime
    occurrence_count: int
    latest_value: float | None
    message: str


class AlertAcknowledgeResponse(BaseSchema):
    id: int
    status: AlertStatus
    acknowledged_at: datetime


class AlertResolveResponse(BaseSchema):
    id: int
    status: AlertStatus
    resolved_at: datetime
