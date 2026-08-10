import pytest
from pydantic import ValidationError

from app.models.enums import RuleOperator, RuleType
from app.schemas.rule import RuleCreate, RuleUpdate


def valid_rule_data() -> dict:
    return {
        "organization_id": 1,
        "name": "Speeding",
        "rule_type": RuleType.SIMPLE,
        "field": "speed_mph",
        "operator": RuleOperator.GT,
        "threshold": 70,
    }


def rule_data(**changes) -> dict:
    data = valid_rule_data()
    data.update(changes)
    return data


def test_simple_rule_is_valid():
    rule = RuleCreate(**valid_rule_data())
    assert rule.rule_type is RuleType.SIMPLE


@pytest.mark.parametrize("field", ["engine_state", "location", "unknown"])
def test_disallowed_field_is_rejected(field):
    with pytest.raises(ValidationError, match="field must be one of"):
        RuleCreate(**rule_data(field=field))


@pytest.mark.parametrize("operator", ["!=", "contains", "and"])
def test_disallowed_operator_is_rejected(operator):
    with pytest.raises(ValidationError, match="Input should be"):
        RuleCreate(**rule_data(operator=operator))


def test_windowed_rule_is_valid():
    rule = RuleCreate(
        **rule_data(
            rule_type=RuleType.WINDOWED,
            window_seconds=300,
            min_matching_events=3,
        )
    )
    assert rule.rule_type is RuleType.WINDOWED


@pytest.mark.parametrize("field", ["window_seconds", "min_matching_events"])
def test_windowed_rule_requires_both_window_settings(field):
    with pytest.raises(ValidationError, match="windowed rules require"):
        RuleCreate(
            **rule_data(
                rule_type=RuleType.WINDOWED,
                **{field: 60},
            )
        )


@pytest.mark.parametrize("field", ["window_seconds", "min_matching_events"])
def test_simple_rule_rejects_window_settings(field):
    with pytest.raises(ValidationError, match="simple rules cannot include window settings"):
        RuleCreate(**rule_data(**{field: 60}))


@pytest.mark.parametrize("field", ["suppress_for_seconds", "escalate_after_seconds"])
def test_negative_duration_is_rejected(field):
    with pytest.raises(ValidationError, match="duration must be zero or positive"):
        RuleCreate(**rule_data(**{field: -1}))


def test_windowed_rule_update_accepts_window_settings():
    update = RuleUpdate(
        rule_type=RuleType.WINDOWED,
        window_seconds=300,
        min_matching_events=3,
    )
    assert update.rule_type is RuleType.WINDOWED
