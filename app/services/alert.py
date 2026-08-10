from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Alert, AlertStatus, Rule, Telemetry


class AlertNotFoundError(Exception):
    pass


class AlertResolvedError(Exception):
    pass


async def record_match(
    db: AsyncSession,
    rule: Rule,
    telemetry: Telemetry,
    driver_id: int | None,
) -> Alert:
    """Create an alert for a new condition or update its active alert."""
    alert = await _get_unresolved(db, rule.id, telemetry.vehicle_id)
    latest_value = getattr(telemetry, rule.field, None)

    if alert is not None:
        alert.occurrence_count += 1
        alert.last_seen_at = telemetry.timestamp
        alert.latest_value = latest_value
        return alert

    alert = Alert(
        organization_id=telemetry.organization_id,
        rule_id=rule.id,
        vehicle_id=telemetry.vehicle_id,
        driver_id=driver_id,
        status=AlertStatus.OPEN,
        opened_at=datetime.now(UTC),
        last_seen_at=telemetry.timestamp,
        occurrence_count=1,
        latest_value=latest_value,
        message=_message(rule, latest_value),
    )
    db.add(alert)
    return alert


async def list_by_organization(
    db: AsyncSession,
    organization_id: int,
    status: AlertStatus | None = None,
) -> list[Alert]:
    statement = select(Alert).where(Alert.organization_id == organization_id)
    if status is not None:
        statement = statement.where(Alert.status == status)

    result = await db.execute(statement.order_by(Alert.last_seen_at.desc()).limit(100))
    return list(result.scalars().all())


async def acknowledge(
    db: AsyncSession, alert_id: int, organization_id: int
) -> Alert:
    alert = await _get_by_id(db, alert_id, organization_id)
    if alert is None:
        raise AlertNotFoundError()
    if alert.status == AlertStatus.RESOLVED:
        raise AlertResolvedError()

    if alert.status != AlertStatus.ACKNOWLEDGED:
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(alert)
    return alert


async def resolve(db: AsyncSession, alert_id: int, organization_id: int) -> Alert:
    alert = await _get_by_id(db, alert_id, organization_id)
    if alert is None:
        raise AlertNotFoundError()

    if alert.status != AlertStatus.RESOLVED:
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(alert)
    return alert


async def escalate_overdue(
    db: AsyncSession, now: datetime | None = None
) -> int:
    """Escalate due open alerts. Conditional updates make duplicate workers safe."""
    now = now or datetime.now(UTC)
    result = await db.execute(
        select(Alert, Rule).join(Rule, Alert.rule_id == Rule.id).where(
            Alert.status == AlertStatus.OPEN,
            Rule.escalate_after_seconds > 0,
        )
    )

    escalated = 0
    for alert, rule in result.all():
        due_at = alert.opened_at + timedelta(seconds=rule.escalate_after_seconds)
        if due_at > now:
            continue

        update_result = await db.execute(
            update(Alert)
            .where(Alert.id == alert.id, Alert.status == AlertStatus.OPEN)
            .values(status=AlertStatus.ESCALATED, escalated_at=now)
        )
        escalated += update_result.rowcount

    if escalated:
        await db.commit()
    return escalated


async def _get_unresolved(
    db: AsyncSession, rule_id: int, vehicle_id: int
) -> Alert | None:
    result = await db.execute(
        select(Alert)
        .where(
            Alert.rule_id == rule_id,
            Alert.vehicle_id == vehicle_id,
            Alert.status != AlertStatus.RESOLVED,
        )
        .order_by(Alert.id.desc())
    )
    return result.scalars().first()


async def _get_by_id(
    db: AsyncSession, alert_id: int, organization_id: int
) -> Alert | None:
    result = await db.execute(
        select(Alert).where(
            Alert.id == alert_id,
            Alert.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()


def _message(rule: Rule, latest_value: float | None) -> str:
    operator = getattr(rule.operator, "value", rule.operator)
    return (
        f"{rule.name}: {rule.field} {operator} {rule.threshold} "
        f"(latest value: {latest_value})"
    )
