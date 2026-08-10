from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"


class EngineState(str, enum.Enum):
    ON = "on"
    OFF = "off"


class AlertStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class RuleType(str, enum.Enum):
    SIMPLE = "simple"
    WINDOWED = "windowed"


class RuleOperator(str, enum.Enum):
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    EQ = "=="
