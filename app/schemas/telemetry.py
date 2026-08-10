from datetime import datetime

from app.models.enums import EngineState
from app.schemas.base import BaseSchema


class TelemetryCreate(BaseSchema):
    event_id: str
    organization_id: int
    vehicle_id: int
    timestamp: datetime
    speed_mph: float | None = None
    fuel_level_percent: float | None = None
    engine_state: EngineState | None = None
    odometer_miles: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    received_at: datetime


class TelemetryResponse(BaseSchema):
    id: int
    event_id: str
    organization_id: int
    vehicle_id: int
    timestamp: datetime
    speed_mph: float | None
    fuel_level_percent: float | None
    engine_state: EngineState | None
    odometer_miles: float | None
    latitude: float | None
    longitude: float | None
    received_at: datetime