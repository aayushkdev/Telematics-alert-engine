from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Driver, Organization
from app.schemas.driver import DriverCreate, DriverUpdate


async def create(db: AsyncSession, data: DriverCreate) -> Driver | None:
    result = await db.execute(
        select(Organization).where(Organization.id == data.organization_id)
    )
    if not result.scalar_one_or_none():
        return None

    driver = Driver(**data.model_dump())
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return driver


async def get_by_id(
    db: AsyncSession, driver_id: int, organization_id: int
) -> Driver | None:
    result = await db.execute(
        select(Driver).where(
            Driver.id == driver_id, Driver.organization_id == organization_id
        )
    )
    return result.scalar_one_or_none()


async def list_by_org(db: AsyncSession, organization_id: int) -> list[Driver]:
    result = await db.execute(
        select(Driver).where(Driver.organization_id == organization_id).limit(100)
    )
    return list(result.scalars().all())


async def update(
    db: AsyncSession, driver_id: int, organization_id: int, data: DriverUpdate
) -> Driver | None:
    driver = await get_by_id(db, driver_id, organization_id)
    if not driver:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(driver, key, value)

    await db.commit()
    await db.refresh(driver)
    return driver
