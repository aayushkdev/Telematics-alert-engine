from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.db.session import get_db
from app.schemas.vehicle import (
    VehicleAssignDriver,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)

router = APIRouter()


@router.post("", response_model=VehicleResponse)
async def create_vehicle(data: VehicleCreate, db: AsyncSession = Depends(get_db)):
    vehicle = await services.vehicle.create(db, data)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Organization not found")
    return vehicle


@router.get("", response_model=list[VehicleResponse])
async def list_vehicles(organization_id: int, db: AsyncSession = Depends(get_db)):
    vehicles = await services.vehicle.list_by_org(db, organization_id)
    return vehicles


@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int, organization_id: int, db: AsyncSession = Depends(get_db)
):
    vehicle = await services.vehicle.get_by_id(db, vehicle_id, organization_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    organization_id: int,
    data: VehicleUpdate,
    db: AsyncSession = Depends(get_db),
):
    vehicle = await services.vehicle.update(db, vehicle_id, organization_id, data)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@router.post("/{vehicle_id}/assign-driver", response_model=VehicleResponse)
async def assign_driver(
    vehicle_id: int,
    organization_id: int,
    data: VehicleAssignDriver,
    db: AsyncSession = Depends(get_db),
):
    vehicle = await services.vehicle.assign_driver(
        db, vehicle_id, organization_id, data
    )
    if not vehicle:
        raise HTTPException(
            status_code=404,
            detail="Vehicle or driver not found or different organization",
        )
    return vehicle
