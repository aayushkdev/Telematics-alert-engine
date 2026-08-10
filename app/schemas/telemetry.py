from datetime import datetime

from pydantic import field_validator, model_validator

from app.models.enums import EngineState
from app.schemas.base import BaseSchema


class TelemetryCreate(BaseSchema):
    event_id: str
    organization_id: int
    vehicle_id: str  # VIN as string in public API
    timestamp: datetime
    speed_mph: float | None = None
    fuel_level_percent: float | None = None
    engine_state: EngineState | None = None
    odometer_miles: float | None = None
    latitude: float | None = None
    longitude: float | None = None

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        if isinstance(v, str):
            parsed = datetime.fromisoformat(v)
            if parsed.tzinfo is None:
                raise ValueError(
                    "timestamp must be timezone-aware (e.g., ending in Z or with offset)"
                )
        return v

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v):
        if v is not None and (v < -90 or v > 90):
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v):
        if v is not None and (v < -180 or v > 180):
            raise ValueError("longitude must be between -180 and 180")
        return v

    @model_validator(mode="after")
    def validate_coordinates_pair(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError(
                "latitude and longitude must both be provided or both be null"
            )
        return self


class TelemetryResponse(BaseSchema):
    id: int
    event_id: str
    organization_id: int
    vehicle_id: str
    timestamp: datetime
    speed_mph: float | None
    fuel_level_percent: float | None
    engine_state: EngineState | None
    odometer_miles: float | None
    latitude: float | None
    longitude: float | None
    received_at: datetime


class TelemetryAccepted(BaseSchema):
    event_id: str
    organization_id: int
    status: str = "accepted"
