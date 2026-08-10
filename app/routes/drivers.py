from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app import services
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate

router = APIRouter()


@router.post("", response_model=DriverResponse)
async def create_driver(data: DriverCreate, db: AsyncSession = Depends(get_db)):
    driver = await services.driver.create(db, data)
    if not driver:
        raise HTTPException(status_code=404, detail="Organization not found")
    return driver


@router.get("", response_model=list[DriverResponse])
async def list_drivers(organization_id: int, db: AsyncSession = Depends(get_db)):
    drivers = await services.driver.list_by_org(db, organization_id)
    return drivers


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: int, organization_id: int, db: AsyncSession = Depends(get_db)):
    driver = await services.driver.get_by_id(db, driver_id, organization_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver


@router.patch("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: int,
    organization_id: int,
    data: DriverUpdate,
    db: AsyncSession = Depends(get_db),
):
    driver = await services.driver.update(db, driver_id, organization_id, data)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver