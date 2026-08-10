from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization, Rule, Vehicle
from app.schemas.rule import (
    RuleCreate,
    RuleUpdate,
    validate_location_configuration,
    validate_window_configuration,
)


class InvalidRuleConfigurationError(Exception):
    pass


async def create(db: AsyncSession, data: RuleCreate) -> Rule | None:
    organization = await _get_organization(db, data.organization_id)
    if organization is None:
        return None

    if data.vehicle_id is not None and not await _vehicle_belongs_to_organization(
        db, data.vehicle_id, data.organization_id
    ):
        return None

    rule = Rule(
        **data.model_dump(),
        created_at=datetime.now(UTC),
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def get_by_id(
    db: AsyncSession, rule_id: int, organization_id: int
) -> Rule | None:
    result = await db.execute(
        select(Rule).where(
            Rule.id == rule_id,
            Rule.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none()


async def list_by_organization(db: AsyncSession, organization_id: int) -> list[Rule]:
    result = await db.execute(
        select(Rule)
        .where(Rule.organization_id == organization_id)
        .order_by(Rule.id)
        .limit(100)
    )
    return list(result.scalars().all())


async def update(
    db: AsyncSession,
    rule_id: int,
    organization_id: int,
    data: RuleUpdate,
) -> Rule | None:
    rule = await get_by_id(db, rule_id, organization_id)
    if rule is None:
        return None

    updates = data.model_dump(exclude_unset=True)
    if "vehicle_id" in updates and updates["vehicle_id"] is not None:
        if not await _vehicle_belongs_to_organization(
            db, updates["vehicle_id"], organization_id
        ):
            return None

    try:
        validate_window_configuration(
            updates.get("rule_type", rule.rule_type),
            updates.get("window_seconds", rule.window_seconds),
            updates.get("min_matching_events", rule.min_matching_events),
        )
        validate_location_configuration(
            updates.get("rule_type", rule.rule_type),
            updates.get("field", rule.field),
            updates.get("operator", rule.operator),
            updates.get("threshold", rule.threshold),
            updates.get("center_latitude", rule.center_latitude),
            updates.get("center_longitude", rule.center_longitude),
        )
    except ValueError as error:
        raise InvalidRuleConfigurationError(str(error))

    for field, value in updates.items():
        setattr(rule, field, value)

    await db.commit()
    await db.refresh(rule)
    return rule


async def delete(db: AsyncSession, rule_id: int, organization_id: int) -> bool:
    rule = await get_by_id(db, rule_id, organization_id)
    if rule is None:
        return False

    await db.delete(rule)
    await db.commit()
    return True


async def _get_organization(
    db: AsyncSession, organization_id: int
) -> Organization | None:
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    return result.scalar_one_or_none()


async def _vehicle_belongs_to_organization(
    db: AsyncSession, vehicle_id: int, organization_id: int
) -> bool:
    result = await db.execute(
        select(Vehicle.id).where(
            Vehicle.id == vehicle_id,
            Vehicle.organization_id == organization_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def get_active_for_telemetry(
    db: AsyncSession, organization_id: int, vehicle_id: int
) -> list[Rule]:
    """Get enabled rules applicable to a telemetry record."""

    result = await db.execute(
        select(Rule).where(
            Rule.organization_id == organization_id,
            Rule.enabled == True,  # noqa: E712
            (Rule.vehicle_id.is_(None) | (Rule.vehicle_id == vehicle_id)),
        )
    )
    return list(result.scalars().all())
