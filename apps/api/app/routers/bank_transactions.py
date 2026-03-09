from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import exists

from app.db import get_db
from app.models import BankTransaction, Categorization, CategoryRule
from app.schemas import BankTransactionOut
from app.services.rule_engine import rule_label

router = APIRouter(prefix="/bank-transactions", tags=["bank-transactions"])


def _enrich(tx: BankTransaction) -> BankTransactionOut:
    out = BankTransactionOut.model_validate(tx)
    if tx.categorization:
        out.category_id = tx.categorization.category_id
        out.category_source = tx.categorization.source
        if tx.categorization.category:
            out.category_name = tx.categorization.category.name
        if tx.categorization.rule:
            out.category_rule_name = rule_label(tx.categorization.rule)
    return out


@router.get("", response_model=list[BankTransactionOut])
async def list_bank_transactions(
    instrument_id: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    category_id: str | None = Query(None),
    uncategorized: bool = Query(False),
    limit: int = Query(200, le=1000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(BankTransaction)
        .options(
            selectinload(BankTransaction.categorization).options(
                selectinload(Categorization.category),
                selectinload(Categorization.rule),
            )
        )
        .order_by(BankTransaction.posted_date.desc())
    )
    if instrument_id:
        q = q.where(BankTransaction.instrument_id == instrument_id)
    if date_from:
        q = q.where(BankTransaction.posted_date >= date_from)
    if date_to:
        q = q.where(BankTransaction.posted_date <= date_to)
    if search:
        q = q.where(BankTransaction.description_raw.ilike(f"%{search}%"))
    if category_id:
        q = q.join(
            Categorization,
            (Categorization.target_id == BankTransaction.id)
            & (Categorization.target_type == "bank_transaction"),
        ).where(Categorization.category_id == category_id)
    if uncategorized:
        q = q.where(
            ~exists().where(
                (Categorization.target_id == BankTransaction.id)
                & (Categorization.target_type == "bank_transaction")
            )
        )
    q = q.limit(limit).offset(offset)
    rows = (await db.scalars(q)).all()
    return [_enrich(tx) for tx in rows]
