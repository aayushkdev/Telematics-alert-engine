from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import AlertStatus, RuleOperator
from app.services import alert as alert_service


def make_rule():
    rule = MagicMock()
    rule.id = 7
    rule.name = "Low fuel"
    rule.field = "fuel_level_percent"
    rule.operator = RuleOperator.LTE
    rule.threshold = 15.0
    return rule


def make_telemetry():
    telemetry = MagicMock()
    telemetry.organization_id = 3
    telemetry.vehicle_id = 12
    telemetry.timestamp = datetime(2026, 8, 11, 10, 0, tzinfo=UTC)
    telemetry.fuel_level_percent = 10.0
    return telemetry


@pytest.mark.asyncio
async def test_record_match_creates_open_alert():
    db = MagicMock()
    result = MagicMock()
    result.scalars.return_value.first.return_value = None
    db.execute = AsyncMock(return_value=result)

    created = await alert_service.record_match(
        db, make_rule(), make_telemetry(), driver_id=4
    )

    assert created.status == AlertStatus.OPEN
    assert created.organization_id == 3
    assert created.rule_id == 7
    assert created.vehicle_id == 12
    assert created.driver_id == 4
    assert created.occurrence_count == 1
    assert created.latest_value == 10.0
    assert created.last_seen_at == datetime(2026, 8, 11, 10, 0, tzinfo=UTC)
    db.add.assert_called_once_with(created)


@pytest.mark.asyncio
async def test_record_match_updates_existing_unresolved_alert():
    existing = MagicMock()
    existing.occurrence_count = 2
    result = MagicMock()
    result.scalars.return_value.first.return_value = existing
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    recorded = await alert_service.record_match(
        db, make_rule(), make_telemetry(), driver_id=4
    )

    assert recorded is existing
    assert existing.occurrence_count == 3
    assert existing.latest_value == 10.0
    assert existing.last_seen_at == datetime(2026, 8, 11, 10, 0, tzinfo=UTC)
    db.add.assert_not_called()


@pytest.mark.asyncio
async def test_acknowledge_sets_status_and_timestamp():
    existing = MagicMock()
    existing.status = AlertStatus.OPEN
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    acknowledged = await alert_service.acknowledge(db, alert_id=8, organization_id=3)

    assert acknowledged is existing
    assert existing.status == AlertStatus.ACKNOWLEDGED
    assert existing.acknowledged_at.tzinfo == UTC
    db.commit.assert_awaited_once()
    db.refresh.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_resolve_is_idempotent_for_resolved_alert():
    existing = MagicMock()
    existing.status = AlertStatus.RESOLVED
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)
    db.commit = AsyncMock()

    resolved = await alert_service.resolve(db, alert_id=8, organization_id=3)

    assert resolved is existing
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_acknowledge_rejects_resolved_alert():
    existing = MagicMock()
    existing.status = AlertStatus.RESOLVED
    result = MagicMock()
    result.scalar_one_or_none.return_value = existing
    db = MagicMock()
    db.execute = AsyncMock(return_value=result)

    with pytest.raises(alert_service.AlertResolvedError):
        await alert_service.acknowledge(db, alert_id=8, organization_id=3)


@pytest.mark.asyncio
async def test_escalate_overdue_changes_only_open_due_alerts():
    now = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    alert = MagicMock()
    alert.id = 8
    alert.opened_at = now - timedelta(seconds=61)
    rule = MagicMock()
    rule.escalate_after_seconds = 60

    candidates = MagicMock()
    candidates.all.return_value = [(alert, rule)]
    update_result = MagicMock()
    update_result.rowcount = 1
    db = MagicMock()
    db.execute = AsyncMock(side_effect=[candidates, update_result])
    db.commit = AsyncMock()

    escalated = await alert_service.escalate_overdue(db, now=now)

    assert escalated == 1
    assert db.execute.await_count == 2
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_escalate_overdue_skips_not_yet_due_alert():
    now = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
    alert = MagicMock()
    alert.opened_at = now - timedelta(seconds=59)
    rule = MagicMock()
    rule.escalate_after_seconds = 60

    candidates = MagicMock()
    candidates.all.return_value = [(alert, rule)]
    db = MagicMock()
    db.execute = AsyncMock(return_value=candidates)
    db.commit = AsyncMock()

    escalated = await alert_service.escalate_overdue(db, now=now)

    assert escalated == 0
    assert db.execute.await_count == 1
    db.commit.assert_not_awaited()
