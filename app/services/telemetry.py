from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Telemetry, Vehicle
from app.schemas.telemetry import TelemetryCreate


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
        await db.commit()
        await db.refresh(telemetry)
    except IntegrityError:
        await db.rollback()
        raise DuplicateEventError()

    return telemetry
