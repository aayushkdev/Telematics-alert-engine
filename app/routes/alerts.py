from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.db.session import get_db
from app.models.enums import AlertStatus
from app.schemas.alert import (
    AlertAcknowledgeResponse,
    AlertResolveResponse,
    AlertResponse,
)

router = APIRouter()


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    organization_id: int,
    status: AlertStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    return await services.alert.list_by_organization(db, organization_id, status)


@router.post("/{alert_id}/acknowledge", response_model=AlertAcknowledgeResponse)
async def acknowledge_alert(
    alert_id: int,
    organization_id: int,
    db: AsyncSession = Depends(get_db),
) -> AlertAcknowledgeResponse:
    try:
        alert = await services.alert.acknowledge(db, alert_id, organization_id)
    except services.alert.AlertNotFoundError:
        raise HTTPException(status_code=404, detail="Alert not found")
    except services.alert.AlertResolvedError:
        raise HTTPException(status_code=409, detail="Resolved alert cannot be acknowledged")
    return AlertAcknowledgeResponse.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertResolveResponse)
async def resolve_alert(
    alert_id: int,
    organization_id: int,
    db: AsyncSession = Depends(get_db),
) -> AlertResolveResponse:
    try:
        alert = await services.alert.resolve(db, alert_id, organization_id)
    except services.alert.AlertNotFoundError:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResolveResponse.model_validate(alert)
