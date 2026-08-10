from datetime import datetime

from app.models.enums import UserRole
from app.schemas.base import BaseSchema


class UserCreate(BaseSchema):
    organization_id: int
    name: str
    email: str
    role: UserRole


class UserResponse(BaseSchema):
    id: int
    organization_id: int
    name: str
    email: str
    role: UserRole
    created_at: datetime


class UserUpdate(BaseSchema):
    name: str | None = None
    email: str | None = None
    role: UserRole | None = None
