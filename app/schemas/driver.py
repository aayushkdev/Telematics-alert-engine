from datetime import datetime

from app.schemas.base import BaseSchema


class DriverCreate(BaseSchema):
    organization_id: int
    name: str
    phone: str


class DriverResponse(BaseSchema):
    id: int
    organization_id: int
    name: str
    phone: str
    created_at: datetime


class DriverUpdate(BaseSchema):
    name: str | None = None
    phone: str | None = None
