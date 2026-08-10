from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Organization
from app.schemas.user import UserCreate, UserUpdate


async def create(db: AsyncSession, data: UserCreate) -> User | None:
    # Check organization exists
    result = await db.execute(select(Organization).where(Organization.id == data.organization_id))
    if not result.scalar_one_or_none():
        return None

    user = User(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_by_id(db: AsyncSession, user_id: int, organization_id: int) -> User | None:
    result = await db.execute(
        select(User).where(User.id == user_id, User.organization_id == organization_id)
    )
    return result.scalar_one_or_none()


async def list_by_org(db: AsyncSession, organization_id: int) -> list[User]:
    result = await db.execute(
        select(User).where(User.organization_id == organization_id).limit(100)
    )
    return list(result.scalars().all())


async def update(db: AsyncSession, user_id: int, organization_id: int, data: UserUpdate) -> User | None:
    user = await get_by_id(db, user_id, organization_id)
    if not user:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user