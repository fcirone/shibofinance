"""Budget planning endpoints."""
import calendar
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import (
    BankTransaction,
    BudgetPeriod,
    BudgetPeriodStatus,
    Categorization,
    CategoryBudget,
    CategoryKind,
    CreditCard,
    CreditCardTransaction,
    TargetType,
)
from app.schemas import (
    BudgetDetailOut,
    BudgetPeriodCreate,
    BudgetPeriodOut,
    CategoryBudgetCreate,
    CategoryBudgetItemOut,
    CategoryBudgetUpdate,
)

router = APIRouter(prefix="/budgets", tags=["budgets"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _period_dates(year: int, month: int) -> tuple[date, date]:
    first = date(year, month, 1)
    last = date(year, month, calendar.monthrange(year, month)[1])
    return first, last


async def _actual_for_category(db: AsyncSession, category_id, date_from: date, date_to: date) -> int:
    """Sum actual spending (in minor units) for a category in a period."""
    # Card transactions: positive amounts categorized to this category
    card_cat_ids = (
        select(Categorization.target_id)
        .where(
            Categorization.target_type == TargetType.card_transaction,
            Categorization.category_id == category_id,
        )
    )
    card_q = select(CreditCardTransaction).where(
        CreditCardTransaction.posted_date >= date_from,
        CreditCardTransaction.posted_date <= date_to,
        CreditCardTransaction.amount_minor > 0,
        CreditCardTransaction.id.in_(card_cat_ids),
    )
    card_txs = (await db.scalars(card_q)).all()
    card_total = sum(tx.amount_minor for tx in card_txs)

    # Bank transactions: negative amounts (expenses) categorized to this category
    bank_cat_ids = (
        select(Categorization.target_id)
        .where(
            Categorization.target_type == TargetType.bank_transaction,
            Categorization.category_id == category_id,
        )
    )
    bank_q = select(BankTransaction).where(
        BankTransaction.posted_date >= date_from,
        BankTransaction.posted_date <= date_to,
        BankTransaction.amount_minor < 0,
        BankTransaction.id.in_(bank_cat_ids),
    )
    bank_txs = (await db.scalars(bank_q)).all()
    bank_total = sum(abs(tx.amount_minor) for tx in bank_txs)

    return card_total + bank_total


async def _build_detail(db: AsyncSession, period: BudgetPeriod) -> BudgetDetailOut:
    date_from, date_to = _period_dates(period.year, period.month)

    items: list[CategoryBudgetItemOut] = []
    for cb in period.category_budgets:
        # Skip non-expense categories in budget calculations
        cat = cb.category
        if cat.kind == CategoryKind.transfer or cat.kind == CategoryKind.income:
            actual = 0
        else:
            actual = await _actual_for_category(db, cb.category_id, date_from, date_to)

        remaining = cb.planned_amount_minor - actual
        pct = (actual / cb.planned_amount_minor * 100) if cb.planned_amount_minor > 0 else 0.0

        items.append(
            CategoryBudgetItemOut(
                id=cb.id,
                budget_period_id=cb.budget_period_id,
                category_id=cb.category_id,
                category_name=cat.name,
                category_kind=cat.kind,
                planned_amount_minor=cb.planned_amount_minor,
                actual_amount_minor=actual,
                remaining_amount_minor=remaining,
                pct_consumed=round(pct, 1),
            )
        )

    # Only expense items count toward totals
    expense_items = [i for i in items if i.category_kind == CategoryKind.expense]
    planned_total = sum(i.planned_amount_minor for i in expense_items)
    actual_total = sum(i.actual_amount_minor for i in expense_items)
    remaining_total = planned_total - actual_total
    pct_total = (actual_total / planned_total * 100) if planned_total > 0 else 0.0

    return BudgetDetailOut(
        id=period.id,
        year=period.year,
        month=period.month,
        status=period.status,
        created_at=period.created_at,
        planned_total_minor=planned_total,
        actual_total_minor=actual_total,
        remaining_total_minor=remaining_total,
        pct_consumed=round(pct_total, 1),
        items=items,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/periods", response_model=list[BudgetPeriodOut])
async def list_periods(db: AsyncSession = Depends(get_db)):
    rows = await db.scalars(
        select(BudgetPeriod).order_by(BudgetPeriod.year.desc(), BudgetPeriod.month.desc())
    )
    return rows.all()


@router.post("/periods", response_model=BudgetPeriodOut, status_code=status.HTTP_201_CREATED)
async def create_period(body: BudgetPeriodCreate, db: AsyncSession = Depends(get_db)):
    if body.month < 1 or body.month > 12:
        raise HTTPException(status_code=422, detail="month must be between 1 and 12")
    existing = await db.scalar(
        select(BudgetPeriod).where(BudgetPeriod.year == body.year, BudgetPeriod.month == body.month)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Budget period already exists for this month")
    period = BudgetPeriod(year=body.year, month=body.month)
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return period


@router.get("/{period_id}", response_model=BudgetDetailOut)
async def get_period(period_id: str, db: AsyncSession = Depends(get_db)):
    period = await db.scalar(
        select(BudgetPeriod)
        .where(BudgetPeriod.id == period_id)
        .options(
            selectinload(BudgetPeriod.category_budgets).selectinload(CategoryBudget.category)
        )
    )
    if not period:
        raise HTTPException(status_code=404, detail="Budget period not found")
    return await _build_detail(db, period)


@router.post("/{period_id}/categories", response_model=CategoryBudgetItemOut, status_code=status.HTTP_201_CREATED)
async def upsert_category_budget(
    period_id: str,
    body: CategoryBudgetCreate,
    db: AsyncSession = Depends(get_db),
):
    period = await db.get(BudgetPeriod, period_id)
    if not period:
        raise HTTPException(status_code=404, detail="Budget period not found")

    existing = await db.scalar(
        select(CategoryBudget).where(
            CategoryBudget.budget_period_id == period_id,
            CategoryBudget.category_id == body.category_id,
        )
    )
    if existing:
        existing.planned_amount_minor = body.planned_amount_minor
        await db.commit()
        await db.refresh(existing)
        cb = existing
    else:
        cb = CategoryBudget(
            budget_period_id=period.id,
            category_id=body.category_id,
            planned_amount_minor=body.planned_amount_minor,
        )
        db.add(cb)
        await db.commit()
        await db.refresh(cb)

    # Reload with category eager
    cb = await db.scalar(
        select(CategoryBudget)
        .where(CategoryBudget.id == cb.id)
        .options(selectinload(CategoryBudget.category))
    )
    date_from, date_to = _period_dates(period.year, period.month)
    cat = cb.category
    if cat.kind in (CategoryKind.transfer, CategoryKind.income):
        actual = 0
    else:
        actual = await _actual_for_category(db, cb.category_id, date_from, date_to)
    remaining = cb.planned_amount_minor - actual
    pct = (actual / cb.planned_amount_minor * 100) if cb.planned_amount_minor > 0 else 0.0

    return CategoryBudgetItemOut(
        id=cb.id,
        budget_period_id=cb.budget_period_id,
        category_id=cb.category_id,
        category_name=cat.name,
        category_kind=cat.kind,
        planned_amount_minor=cb.planned_amount_minor,
        actual_amount_minor=actual,
        remaining_amount_minor=remaining,
        pct_consumed=round(pct, 1),
    )


@router.patch("/category-items/{item_id}", response_model=CategoryBudgetItemOut)
async def update_category_budget(
    item_id: str,
    body: CategoryBudgetUpdate,
    db: AsyncSession = Depends(get_db),
):
    cb = await db.scalar(
        select(CategoryBudget)
        .where(CategoryBudget.id == item_id)
        .options(selectinload(CategoryBudget.category))
    )
    if not cb:
        raise HTTPException(status_code=404, detail="Budget item not found")

    if body.planned_amount_minor is not None:
        cb.planned_amount_minor = body.planned_amount_minor

    await db.commit()
    await db.refresh(cb)

    # Reload category
    cb = await db.scalar(
        select(CategoryBudget)
        .where(CategoryBudget.id == cb.id)
        .options(selectinload(CategoryBudget.category))
    )
    period = await db.get(BudgetPeriod, cb.budget_period_id)
    date_from, date_to = _period_dates(period.year, period.month)
    cat = cb.category
    if cat.kind in (CategoryKind.transfer, CategoryKind.income):
        actual = 0
    else:
        actual = await _actual_for_category(db, cb.category_id, date_from, date_to)
    remaining = cb.planned_amount_minor - actual
    pct = (actual / cb.planned_amount_minor * 100) if cb.planned_amount_minor > 0 else 0.0

    return CategoryBudgetItemOut(
        id=cb.id,
        budget_period_id=cb.budget_period_id,
        category_id=cb.category_id,
        category_name=cat.name,
        category_kind=cat.kind,
        planned_amount_minor=cb.planned_amount_minor,
        actual_amount_minor=actual,
        remaining_amount_minor=remaining,
        pct_consumed=round(pct, 1),
    )


@router.post("/{period_id}/copy-from/{source_period_id}", response_model=BudgetDetailOut)
async def copy_budget(
    period_id: str,
    source_period_id: str,
    db: AsyncSession = Depends(get_db),
):
    target = await db.scalar(
        select(BudgetPeriod)
        .where(BudgetPeriod.id == period_id)
        .options(selectinload(BudgetPeriod.category_budgets))
    )
    if not target:
        raise HTTPException(status_code=404, detail="Target budget period not found")

    source = await db.scalar(
        select(BudgetPeriod)
        .where(BudgetPeriod.id == source_period_id)
        .options(selectinload(BudgetPeriod.category_budgets))
    )
    if not source:
        raise HTTPException(status_code=404, detail="Source budget period not found")

    # Existing category_ids in target
    existing_cat_ids = {cb.category_id for cb in target.category_budgets}

    for src_cb in source.category_budgets:
        if src_cb.category_id in existing_cat_ids:
            # Update existing
            existing = next(cb for cb in target.category_budgets if cb.category_id == src_cb.category_id)
            existing.planned_amount_minor = src_cb.planned_amount_minor
        else:
            db.add(CategoryBudget(
                budget_period_id=target.id,
                category_id=src_cb.category_id,
                planned_amount_minor=src_cb.planned_amount_minor,
            ))

    await db.commit()

    # Reload full detail — populate_existing=True forces a fresh load even if the
    # object is already in the identity map with a (now stale) empty relationship.
    target = await db.scalar(
        select(BudgetPeriod)
        .where(BudgetPeriod.id == period_id)
        .options(selectinload(BudgetPeriod.category_budgets).selectinload(CategoryBudget.category))
        .execution_options(populate_existing=True)
    )
    return await _build_detail(db, target)
