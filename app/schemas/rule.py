from datetime import datetime

from app.models.enums import RuleType
from app.schemas.base import BaseSchema


class RuleCreate(BaseSchema):
    organization_id: int
    vehicle_id: int | None = None
    name: str
    enabled: bool = True
    rule_type: RuleType
    field: str
    operator: str
    threshold: float
    window_seconds: int | None = None
    min_matching_events: int | None = None
    suppress_for_seconds: int = 0
    escalate_after_seconds: int = 0


class RuleResponse(BaseSchema):
    id: int
    organization_id: int
    vehicle_id: int | None
    name: str
    enabled: bool
    rule_type: RuleType
    field: str
    operator: str
    threshold: float
    window_seconds: int | None
    min_matching_events: int | None
    suppress_for_seconds: int
    escalate_after_seconds: int
    created_at: datetime


class RuleUpdate(BaseSchema):
    name: str | None = None
    enabled: bool | None = None
    vehicle_id: int | None = None
    rule_type: RuleType | None = None
    field: str | None = None
    operator: str | None = None
    threshold: float | None = None
    window_seconds: int | None = None
    min_matching_events: int | None = None
    suppress_for_seconds: int | None = None
    escalate_after_seconds: int | None = None
