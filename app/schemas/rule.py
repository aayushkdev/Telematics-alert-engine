from datetime import datetime

from pydantic import field_validator, model_validator

from app.models.enums import RuleType
from app.schemas.base import BaseSchema

ALLOWED_FIELDS = frozenset({"speed_mph", "fuel_level_percent", "odometer_miles"})
ALLOWED_OPERATORS = frozenset({">", ">=", "<", "<=", "=="})


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

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str) -> str:
        if value not in ALLOWED_FIELDS:
            raise ValueError(f"field must be one of: {', '.join(sorted(ALLOWED_FIELDS))}")
        return value

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, value: str) -> str:
        if value not in ALLOWED_OPERATORS:
            raise ValueError(
                f"operator must be one of: {', '.join(sorted(ALLOWED_OPERATORS))}"
            )
        return value

    @field_validator("suppress_for_seconds", "escalate_after_seconds")
    @classmethod
    def validate_non_negative_duration(cls, value: int) -> int:
        if value < 0:
            raise ValueError("duration must be zero or positive")
        return value

    @model_validator(mode="after")
    def validate_simple_rule(self) -> "RuleCreate":
        if self.rule_type is not RuleType.SIMPLE:
            raise ValueError("only simple rules are supported in this build")
        if self.window_seconds is not None or self.min_matching_events is not None:
            raise ValueError("simple rules cannot include window settings")
        return self


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

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_FIELDS:
            raise ValueError(f"field must be one of: {', '.join(sorted(ALLOWED_FIELDS))}")
        return value

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, value: str | None) -> str | None:
        if value is not None and value not in ALLOWED_OPERATORS:
            raise ValueError(
                f"operator must be one of: {', '.join(sorted(ALLOWED_OPERATORS))}"
            )
        return value

    @field_validator("suppress_for_seconds", "escalate_after_seconds")
    @classmethod
    def validate_non_negative_duration(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("duration must be zero or positive")
        return value

    @model_validator(mode="after")
    def validate_simple_rule(self) -> "RuleUpdate":
        if self.rule_type is RuleType.WINDOWED:
            raise ValueError("only simple rules are supported in this build")
        if self.window_seconds is not None or self.min_matching_events is not None:
            raise ValueError("simple rules cannot include window settings")
        return self
