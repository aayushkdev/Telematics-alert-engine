import operator
from math import asin, cos, radians, sin, sqrt
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

    if rule.field == "location":
        return _is_outside_radius(rule, telemetry)

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


def _is_outside_radius(rule: Rule, telemetry: Telemetry) -> bool:
    operator_value = getattr(rule.operator, "value", rule.operator)
    if (
        operator_value != RuleOperator.OUTSIDE_RADIUS.value
        or telemetry.latitude is None
        or telemetry.longitude is None
        or rule.center_latitude is None
        or rule.center_longitude is None
    ):
        return False

    earth_radius_miles = 3958.8
    latitude_delta = radians(telemetry.latitude - rule.center_latitude)
    longitude_delta = radians(telemetry.longitude - rule.center_longitude)
    distance_formula = (
        sin(latitude_delta / 2) ** 2
        + cos(radians(rule.center_latitude))
        * cos(radians(telemetry.latitude))
        * sin(longitude_delta / 2) ** 2
    )
    distance_miles = 2 * earth_radius_miles * asin(sqrt(distance_formula))
    return distance_miles > rule.threshold
