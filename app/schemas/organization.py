from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import BaseSchema


class OrganizationCreate(BaseSchema):
    name: str


class OrganizationResponse(BaseSchema):
    id: int
    name: str
    created_at: datetime


class OrganizationUpdate(BaseSchema):
    name: str | None = None