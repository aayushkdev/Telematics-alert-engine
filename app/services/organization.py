from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Organization
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


async def create(db: AsyncSession, data: OrganizationCreate) -> Organization:
    org = Organization(name=data.name)
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org


async def get_by_id(db: AsyncSession, organization_id: int) -> Organization | None:
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    return result.scalar_one_or_none()


async def update(
    db: AsyncSession, organization_id: int, data: OrganizationUpdate
) -> Organization | None:
    org = await get_by_id(db, organization_id)
    if not org:
        return None
    if data.name is not None:
        org.name = data.name
    await db.commit()
    await db.refresh(org)
    return org
