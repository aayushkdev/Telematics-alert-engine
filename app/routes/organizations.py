from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app import services
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate

router = APIRouter()


@router.post("", response_model=OrganizationResponse)
async def create_organization(data: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    org = await services.organization.create(db, data)
    return org


@router.get("/{organization_id}", response_model=OrganizationResponse)
async def get_organization(organization_id: int, db: AsyncSession = Depends(get_db)):
    org = await services.organization.get_by_id(db, organization_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@router.patch("/{organization_id}", response_model=OrganizationResponse)
async def update_organization(
    organization_id: int,
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
):
    org = await services.organization.update(db, organization_id, data)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org