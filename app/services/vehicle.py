from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Driver, Organization, Vehicle
from app.schemas.vehicle import VehicleAssignDriver, VehicleCreate, VehicleUpdate


async def create(db: AsyncSession, data: VehicleCreate) -> Vehicle | None:
    result = await db.execute(
        select(Organization).where(Organization.id == data.organization_id)
    )
    if not result.scalar_one_or_none():
        return None

    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def get_by_id(
    db: AsyncSession, vehicle_id: int, organization_id: int
) -> Vehicle | None:
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.id == vehicle_id, Vehicle.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()


async def list_by_org(db: AsyncSession, organization_id: int) -> list[Vehicle]:
    result = await db.execute(
        select(Vehicle).where(Vehicle.organization_id == organization_id).limit(100)
    )
    return list(result.scalars().all())


async def update(
    db: AsyncSession, vehicle_id: int, organization_id: int, data: VehicleUpdate
) -> Vehicle | None:
    vehicle = await get_by_id(db, vehicle_id, organization_id)
    if not vehicle:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(vehicle, key, value)

    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def assign_driver(
    db: AsyncSession, vehicle_id: int, organization_id: int, data: VehicleAssignDriver
) -> Vehicle | None:
    vehicle = await get_by_id(db, vehicle_id, organization_id)
    if not vehicle:
        return None

    # If assigning a driver, verify same organization
    if data.driver_id is not None:
        result = await db.execute(
            select(Driver).where(
                Driver.id == data.driver_id, Driver.organization_id == organization_id
            )
        )
        if not result.scalar_one_or_none():
            return None

    vehicle.current_driver_id = data.driver_id
    await db.commit()
    await db.refresh(vehicle)
    return vehicle
