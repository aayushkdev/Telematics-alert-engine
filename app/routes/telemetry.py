from fastapi import APIRouter, HTTPException

from app.messaging.rabbitmq import MessagingUnavailable, publish_telemetry
from app.schemas.telemetry import TelemetryAccepted, TelemetryCreate

router = APIRouter()


@router.post("", response_model=TelemetryAccepted, status_code=202)
async def create_telemetry(data: TelemetryCreate):
    try:
        await publish_telemetry(data.model_dump(mode="json"))
    except MessagingUnavailable:
        raise HTTPException(status_code=503, detail="Telemetry queue unavailable")
    return TelemetryAccepted(event_id=data.event_id, organization_id=data.organization_id)
