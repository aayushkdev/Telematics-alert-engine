from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.post("", response_model=UserResponse)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await services.user.create(db, data)
    if not user:
        raise HTTPException(status_code=404, detail="Organization not found")
    return user


@router.get("", response_model=list[UserResponse])
async def list_users(organization_id: int, db: AsyncSession = Depends(get_db)):
    users = await services.user.list_by_org(db, organization_id)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int, organization_id: int, db: AsyncSession = Depends(get_db)
):
    user = await services.user.get_by_id(db, user_id, organization_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    organization_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
):
    user = await services.user.update(db, user_id, organization_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
