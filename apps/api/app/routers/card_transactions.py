from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Categorization, CreditCard, CreditCardTransaction
from app.schemas import CardTransactionOut

router = APIRouter(prefix="/card-transactions", tags=["card-transactions"])


def _enrich(tx: CreditCardTransaction) -> CardTransactionOut:
    out = CardTransactionOut.model_validate(tx)
    if tx.categorization:
        out.category_id = tx.categorization.category_id
        if tx.categorization.category:
            out.category_name = tx.categorization.category.name
    return out


@router.get("", response_model=list[CardTransactionOut])
async def list_card_transactions(
    instrument_id: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    category_id: str | None = Query(None),
    limit: int = Query(200, le=1000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(CreditCardTransaction)
        .options(
            selectinload(CreditCardTransaction.categorization).selectinload(Categorization.category)
        )
        .order_by(CreditCardTransaction.posted_date.desc())
    )
    if instrument_id:
        q = q.join(CreditCard, CreditCardTransaction.credit_card_id == CreditCard.id).where(
            CreditCard.instrument_id == instrument_id
        )
    if date_from:
        q = q.where(CreditCardTransaction.posted_date >= date_from)
    if date_to:
        q = q.where(CreditCardTransaction.posted_date <= date_to)
    if search:
        q = q.where(CreditCardTransaction.description_raw.ilike(f"%{search}%"))
    if category_id:
        q = q.join(
            Categorization,
            (Categorization.target_id == CreditCardTransaction.id)
            & (Categorization.target_type == "card_transaction"),
        ).where(Categorization.category_id == category_id)
    q = q.limit(limit).offset(offset)
    rows = (await db.scalars(q)).all()
    return [_enrich(tx) for tx in rows]
