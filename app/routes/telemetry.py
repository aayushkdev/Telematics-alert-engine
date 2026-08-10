from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.db.session import get_db
from app.schemas.telemetry import TelemetryCreate, TelemetryResponse

router = APIRouter()


@router.post("", response_model=TelemetryResponse, status_code=201)
async def create_telemetry(data: TelemetryCreate, db: AsyncSession = Depends(get_db)):
    try:
        telemetry = await services.telemetry.create(db, data)
        return TelemetryResponse(
            id=telemetry.id,
            event_id=telemetry.event_id,
            organization_id=telemetry.organization_id,
            vehicle_id=data.vehicle_id,
            timestamp=telemetry.timestamp,
            speed_mph=telemetry.speed_mph,
            fuel_level_percent=telemetry.fuel_level_percent,
            engine_state=telemetry.engine_state,
            odometer_miles=telemetry.odometer_miles,
            latitude=telemetry.latitude,
            longitude=telemetry.longitude,
            received_at=telemetry.received_at,
        )
    except services.telemetry.DuplicateEventError:
        raise HTTPException(status_code=409, detail="Duplicate event_id")
    except services.telemetry.VehicleNotFoundError:
        raise HTTPException(status_code=404, detail="Vehicle not found")
