from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import services
from app.db.session import get_db
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter()


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: RuleCreate, db: AsyncSession = Depends(get_db)
) -> RuleResponse:
    rule = await services.rule.create(db, data)
    if rule is None:
        raise HTTPException(status_code=404, detail="Organization or vehicle not found")
    return rule


@router.get("", response_model=list[RuleResponse])
async def list_rules(
    organization_id: int, db: AsyncSession = Depends(get_db)
) -> list[RuleResponse]:
    return await services.rule.list_by_organization(db, organization_id)


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int, organization_id: int, db: AsyncSession = Depends(get_db)
) -> RuleResponse:
    rule = await services.rule.get_by_id(db, rule_id, organization_id)
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    organization_id: int,
    data: RuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> RuleResponse:
    try:
        rule = await services.rule.update(db, rule_id, organization_id, data)
    except services.rule.InvalidRuleConfigurationError as error:
        raise HTTPException(status_code=422, detail=str(error))
    if rule is None:
        raise HTTPException(status_code=404, detail="Rule or vehicle not found")
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int, organization_id: int, db: AsyncSession = Depends(get_db)
) -> Response:
    deleted = await services.rule.delete(db, rule_id, organization_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
