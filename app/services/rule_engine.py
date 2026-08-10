import operator
from typing import Any

from app.models import Rule, Telemetry
from app.models.enums import RuleOperator

FIELDS = frozenset({"speed_mph", "fuel_level_percent", "odometer_miles"})

OPERATORS = {
    RuleOperator.GT: operator.gt,
    RuleOperator.GTE: operator.ge,
    RuleOperator.LT: operator.lt,
    RuleOperator.LTE: operator.le,
    RuleOperator.EQ: operator.eq,
}


def matches(rule: Rule, telemetry: Telemetry) -> bool:
    """Check whether a telemetry record matches a rule's threshold condition."""
    if not rule.enabled:
        return False

    if rule.field not in FIELDS:
        return False

    value: Any = getattr(telemetry, rule.field, None)
    if value is None:
        return False

    op_func = OPERATORS.get(rule.operator)
    if op_func is None:
        return False

    try:
        return op_func(value, rule.threshold)
    except (TypeError, ValueError):
        return False
