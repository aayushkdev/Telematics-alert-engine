from datetime import datetime

from app.schemas.base import BaseSchema


class VehicleCreate(BaseSchema):
    organization_id: int
    vin: str
    display_name: str


class VehicleResponse(BaseSchema):
    id: int
    organization_id: int
    current_driver_id: int | None
    vin: str
    display_name: str
    created_at: datetime


class VehicleUpdate(BaseSchema):
    display_name: str | None = None


class VehicleAssignDriver(BaseSchema):
    driver_id: int | None = None
