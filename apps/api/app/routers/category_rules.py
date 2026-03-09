"""Category rules CRUD + rule engine endpoints."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import CategoryRule, MatchField, MatchOperator
from app.schemas import (
    ApplyRulesResult,
    CategoryRuleCreate,
    CategoryRuleOut,
    CategoryRuleUpdate,
    DryRunResult,
)
from app.services.rule_engine import VALID_COMBOS, apply_rules

router = APIRouter(prefix="/category-rules", tags=["category-rules"])


def _to_out(rule: CategoryRule) -> CategoryRuleOut:
    return CategoryRuleOut(
        id=rule.id,
        category_id=rule.category_id,
        category_name=rule.category.name,
        match_field=rule.match_field,
        match_operator=rule.match_operator,
        match_value=rule.match_value,
        target_type=rule.target_type,
        priority=rule.priority,
        enabled=rule.enabled,
        created_at=rule.created_at,
    )


def _validate_combo(field: MatchField, operator: MatchOperator) -> None:
    if operator not in VALID_COMBOS.get(field, set()):
        raise HTTPException(
            status_code=422,
            detail=f"Operator '{operator.value}' is not valid for field '{field.value}'",
        )


# Fixed sub-paths MUST come before /{id} routes
@router.post("/dry-run", response_model=DryRunResult)
async def dry_run_rules(db: AsyncSession = Depends(get_db)):
    result = await apply_rules(db, dry_run=True)
    return DryRunResult(
        would_categorize=result["applied"],
        by_category=result["by_category"],
    )


@router.post("/apply", response_model=ApplyRulesResult)
async def apply_rules_endpoint(db: AsyncSession = Depends(get_db)):
    result = await apply_rules(db)
    await db.commit()
    return ApplyRulesResult(
        applied=result["applied"],
        by_category=result["by_category"],
    )


@router.get("", response_model=list[CategoryRuleOut])
async def list_rules(db: AsyncSession = Depends(get_db)):
    rules = (await db.scalars(
        select(CategoryRule)
        .options(selectinload(CategoryRule.category))
        .order_by(CategoryRule.priority)
    )).all()
    return [_to_out(r) for r in rules]


@router.post("", response_model=CategoryRuleOut, status_code=201)
async def create_rule(body: CategoryRuleCreate, db: AsyncSession = Depends(get_db)):
    _validate_combo(body.match_field, body.match_operator)
    rule = CategoryRule(
        id=uuid.uuid4(),
        category_id=body.category_id,
        match_field=body.match_field,
        match_operator=body.match_operator,
        match_value=body.match_value,
        target_type=body.target_type,
        priority=body.priority,
        enabled=body.enabled,
    )
    db.add(rule)
    await db.flush()
    await db.refresh(rule, ["category"])
    await db.commit()
    return _to_out(rule)


@router.patch("/{rule_id}", response_model=CategoryRuleOut)
async def update_rule(
    rule_id: uuid.UUID,
    body: CategoryRuleUpdate,
    db: AsyncSession = Depends(get_db),
):
    rule = await db.scalar(
        select(CategoryRule)
        .options(selectinload(CategoryRule.category))
        .where(CategoryRule.id == rule_id)
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if body.match_field is not None:
        rule.match_field = body.match_field
    if body.match_operator is not None:
        rule.match_operator = body.match_operator
    if body.match_field is not None or body.match_operator is not None:
        _validate_combo(rule.match_field, rule.match_operator)
    if body.category_id is not None:
        rule.category_id = body.category_id
    if body.match_value is not None:
        rule.match_value = body.match_value
    if body.target_type is not None:
        rule.target_type = body.target_type
    if body.priority is not None:
        rule.priority = body.priority
    if body.enabled is not None:
        rule.enabled = body.enabled

    rule.updated_at = datetime.now(tz=timezone.utc)
    await db.flush()
    await db.refresh(rule, ["category"])
    await db.commit()
    return _to_out(rule)


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    rule = await db.scalar(select(CategoryRule).where(CategoryRule.id == rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
