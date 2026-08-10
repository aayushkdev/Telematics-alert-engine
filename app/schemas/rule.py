from datetime import datetime

from pydantic import field_validator, model_validator

from app.models.enums import RuleOperator, RuleType
from app.schemas.base import BaseSchema

ALLOWED_FIELDS = frozenset(
    {"speed_mph", "fuel_level_percent", "odometer_miles", "location"}
)


def validate_window_configuration(
    rule_type: RuleType,
    window_seconds: int | None,
    min_matching_events: int | None,
) -> None:
    if rule_type is RuleType.SIMPLE:
        if window_seconds is not None or min_matching_events is not None:
            raise ValueError("simple rules cannot include window settings")
        return

    if window_seconds is None or min_matching_events is None:
        raise ValueError("windowed rules require window_seconds and min_matching_events")
    if window_seconds <= 0 or min_matching_events <= 0:
        raise ValueError("window settings must be greater than zero")


def validate_location_configuration(
    rule_type: RuleType,
    field: str,
    operator: RuleOperator | str,
    threshold: float,
    center_latitude: float | None,
    center_longitude: float | None,
) -> None:
    operator_value = getattr(operator, "value", operator)
    if field == "location":
        if rule_type is not RuleType.SIMPLE:
            raise ValueError("location rules must use the simple rule type")
        if operator_value != RuleOperator.OUTSIDE_RADIUS.value:
            raise ValueError("location rules require the outside_radius operator")
        if threshold <= 0:
            raise ValueError("location rule radius must be greater than zero")
        if center_latitude is None or center_longitude is None:
            raise ValueError("location rules require center_latitude and center_longitude")
    elif center_latitude is not None or center_longitude is not None:
        raise ValueError("only location rules can include a center point")


class RuleCreate(BaseSchema):
    organization_id: int
    vehicle_id: int | None = None
    name: str
    enabled: bool = True
    rule_type: RuleType
    field: str
    operator: RuleOperator
    threshold: float
    center_latitude: float | None = None
    center_longitude: float | None = None
    window_seconds: int | None = None
    min_matching_events: int | None = None
    suppress_for_seconds: int = 0
    escalate_after_seconds: int = 0

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str) -> str:
        if value not in ALLOWED_FIELDS:
            raise ValueError(
                f"field must be one of: {', '.join(sorted(ALLOWED_FIELDS))}"
            )
        return value

    @field_validator("suppress_for_seconds", "escalate_after_seconds")
    @classmethod
    def validate_non_negative_duration(cls, value: int) -> int:
        if value < 0:
            raise ValueError("duration must be zero or positive")
        return value

    @field_validator("center_latitude")
    @classmethod
    def validate_center_latitude(cls, value: float | None) -> float | None:
        if value is not None and not -90 <= value <= 90:
            raise ValueError("center_latitude must be between -90 and 90")
        return value

    @field_validator("center_longitude")
    @classmethod
    def validate_center_longitude(cls, value: float | None) -> float | None:
        if value is not None and not -180 <= value <= 180:
            raise ValueError("center_longitude must be between -180 and 180")
        return value

    @model_validator(mode="after")
    def validate_rule_configuration(self) -> "RuleCreate":
        validate_window_configuration(
            self.rule_type, self.window_seconds, self.min_matching_events
        )
        validate_location_configuration(
            self.rule_type,
            self.field,
            self.operator,
            self.threshold,
            self.center_latitude,
            self.center_longitude,
        )
        return self


class RuleResponse(BaseSchema):
    id: int
    organization_id: int
    vehicle_id: int | None
    name: str
    enabled: bool
    rule_type: RuleType
    field: str
    operator: RuleOperator
    threshold: float
    center_latitude: float | None
    center_longitude: float | None
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
    operator: RuleOperator | None = None
    threshold: float | None = None
    center_latitude: float | None = None
    center_longitude: float | None = None
    window_seconds: int | None = None
    min_matching_events: int | None = None
    suppress_for_seconds: int | None = None
    escalate_after_seconds: int | None = None

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_FIELDS:
            raise ValueError(
                f"field must be one of: {', '.join(sorted(ALLOWED_FIELDS))}"
            )
        return value

    @field_validator("suppress_for_seconds", "escalate_after_seconds")
    @classmethod
    def validate_non_negative_duration(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("duration must be zero or positive")
        return value

    @field_validator("center_latitude")
    @classmethod
    def validate_center_latitude(cls, value: float | None) -> float | None:
        if value is not None and not -90 <= value <= 90:
            raise ValueError("center_latitude must be between -90 and 90")
        return value

    @field_validator("center_longitude")
    @classmethod
    def validate_center_longitude(cls, value: float | None) -> float | None:
        if value is not None and not -180 <= value <= 180:
            raise ValueError("center_longitude must be between -180 and 180")
        return value

    @model_validator(mode="after")
    def validate_window_settings(self) -> "RuleUpdate":
        if self.window_seconds is not None and self.window_seconds <= 0:
            raise ValueError("window_seconds must be greater than zero")
        if self.min_matching_events is not None and self.min_matching_events <= 0:
            raise ValueError("min_matching_events must be greater than zero")
        return self
