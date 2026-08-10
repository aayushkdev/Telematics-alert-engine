import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rule, Telemetry, Vehicle
from app.models.enums import RuleType
from app.schemas.telemetry import TelemetryCreate
from app.services import alert, rule, rule_engine, suppression, windowing

logger = logging.getLogger(__name__)

__all__ = ["create", "DuplicateEventError", "VehicleNotFoundError"]


class DuplicateEventError(Exception):
    pass


class VehicleNotFoundError(Exception):
    pass


async def create(db: AsyncSession, data: TelemetryCreate) -> Telemetry:
    # Look up vehicle by organization_id and vin
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.organization_id == data.organization_id,
            Vehicle.vin == data.vehicle_id,
        )
    )
    vehicle = result.scalar_one_or_none()

    if not vehicle:
        raise VehicleNotFoundError()

    telemetry = Telemetry(
        event_id=data.event_id,
        organization_id=data.organization_id,
        vehicle_id=vehicle.id,
        timestamp=data.timestamp,
        speed_mph=data.speed_mph,
        fuel_level_percent=data.fuel_level_percent,
        engine_state=data.engine_state,
        odometer_miles=data.odometer_miles,
        latitude=data.latitude,
        longitude=data.longitude,
        received_at=datetime.now(UTC),
    )

    db.add(telemetry)

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise DuplicateEventError()

    matched_rules = await evaluate_rules_for_telemetry(db, telemetry)
    processed_rules = []
    for matched_rule in matched_rules:
        if await suppression.is_suppressed(
            matched_rule.id,
            telemetry.vehicle_id,
            matched_rule.suppress_for_seconds,
        ):
            continue
        await alert.record_match(db, matched_rule, telemetry, vehicle.current_driver_id)
        processed_rules.append(matched_rule)

    try:
        await db.commit()
        await db.refresh(telemetry)
    except IntegrityError:
        await db.rollback()
        raise

    for processed_rule in processed_rules:
        await suppression.start_cooldown(
            processed_rule.id,
            telemetry.vehicle_id,
            processed_rule.suppress_for_seconds,
        )

    if processed_rules:
        logger.info(
            "Telemetry %s matched rules: %s",
            telemetry.event_id,
            [processed_rule.id for processed_rule in processed_rules],
        )

    return telemetry


async def evaluate_rules_for_telemetry(
    db: AsyncSession, telemetry: Telemetry
) -> list[Rule]:
    """Evaluate all active rules against a telemetry record."""
    rules = await rule.get_active_for_telemetry(
        db, telemetry.organization_id, telemetry.vehicle_id
    )

    matched = []
    for configured_rule in rules:
        if not rule_engine.matches(configured_rule, telemetry):
            continue

        if configured_rule.rule_type is RuleType.SIMPLE:
            matched.append(configured_rule)
        elif await windowing.threshold_reached(configured_rule, telemetry):
            matched.append(configured_rule)

    return matched
