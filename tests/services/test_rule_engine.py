from unittest.mock import MagicMock

import pytest

from app.models.enums import RuleOperator, RuleType
from app.services import rule_engine


def make_telemetry(**kwargs):
    t = MagicMock()
    t.speed_mph = kwargs.get("speed_mph")
    t.fuel_level_percent = kwargs.get("fuel_level_percent")
    t.odometer_miles = kwargs.get("odometer_miles")
    return t


def make_rule(
    field="speed_mph",
    operator=RuleOperator.GT,
    threshold=70.0,
    enabled=True,
    rule_type=RuleType.SIMPLE,
):
    r = MagicMock()
    r.field = field
    r.operator = operator
    r.threshold = threshold
    r.enabled = enabled
    r.rule_type = rule_type
    return r


def test_speed_75_greater_than_70_matches():
    rule = make_rule(field="speed_mph", operator=RuleOperator.GT, threshold=70.0)
    telemetry = make_telemetry(speed_mph=75)
    assert rule_engine.matches(rule, telemetry) is True


def test_speed_65_greater_than_70_no_match():
    rule = make_rule(field="speed_mph", operator=RuleOperator.GT, threshold=70.0)
    telemetry = make_telemetry(speed_mph=65)
    assert rule_engine.matches(rule, telemetry) is False


def test_fuel_10_less_than_or_equal_15_matches():
    rule = make_rule(
        field="fuel_level_percent", operator=RuleOperator.LTE, threshold=15.0
    )
    telemetry = make_telemetry(fuel_level_percent=10)
    assert rule_engine.matches(rule, telemetry) is True


def test_fuel_20_less_than_or_equal_15_no_match():
    rule = make_rule(
        field="fuel_level_percent", operator=RuleOperator.LTE, threshold=15.0
    )
    telemetry = make_telemetry(fuel_level_percent=20)
    assert rule_engine.matches(rule, telemetry) is False


def test_missing_speed_returns_false():
    rule = make_rule(field="speed_mph", operator=RuleOperator.GT, threshold=70.0)
    telemetry = make_telemetry()
    assert rule_engine.matches(rule, telemetry) is False


def test_disabled_rule_returns_false():
    rule = make_rule(
        field="speed_mph", operator=RuleOperator.GT, threshold=70.0, enabled=False
    )
    telemetry = make_telemetry(speed_mph=80)
    assert rule_engine.matches(rule, telemetry) is False


def test_windowed_rule_threshold_condition_matches():
    rule = make_rule(
        field="speed_mph",
        operator=RuleOperator.GT,
        threshold=70.0,
        rule_type=RuleType.WINDOWED,
    )
    telemetry = make_telemetry(speed_mph=80)
    assert rule_engine.matches(rule, telemetry) is True


def test_unsupported_field_returns_false():
    rule = make_rule(
        field="unsupported_field", operator=RuleOperator.GT, threshold=70.0
    )
    telemetry = make_telemetry(speed_mph=80)
    assert rule_engine.matches(rule, telemetry) is False


def test_unsupported_operator_returns_false():
    unsupported = MagicMock()
    unsupported.value = "!="
    rule = make_rule(field="speed_mph", operator=unsupported, threshold=70.0)
    telemetry = make_telemetry(speed_mph=80)
    assert rule_engine.matches(rule, telemetry) is False


def test_equal_operator_matches():
    rule = make_rule(field="speed_mph", operator=RuleOperator.EQ, threshold=70.0)
    telemetry = make_telemetry(speed_mph=70.0)
    assert rule_engine.matches(rule, telemetry) is True


def test_greater_than_or_equal_operator():
    rule = make_rule(field="speed_mph", operator=RuleOperator.GTE, threshold=70.0)
    assert rule_engine.matches(rule, make_telemetry(speed_mph=70.0)) is True
    assert rule_engine.matches(rule, make_telemetry(speed_mph=71.0)) is True
    assert rule_engine.matches(rule, make_telemetry(speed_mph=69.0)) is False


def test_less_than_operator():
    rule = make_rule(field="speed_mph", operator=RuleOperator.LT, threshold=70.0)
    assert rule_engine.matches(rule, make_telemetry(speed_mph=65.0)) is True
    assert rule_engine.matches(rule, make_telemetry(speed_mph=70.0)) is False


def test_odometer_field():
    rule = make_rule(
        field="odometer_miles", operator=RuleOperator.GT, threshold=10000.0
    )
    assert rule_engine.matches(rule, make_telemetry(odometer_miles=15000)) is True
    assert rule_engine.matches(rule, make_telemetry(odometer_miles=5000)) is False
