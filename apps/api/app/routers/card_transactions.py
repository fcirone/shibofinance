from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Categorization, CreditCard, CreditCardTransaction
from app.schemas import CardTransactionOut
from app.services.rule_engine import rule_label

router = APIRouter(prefix="/card-transactions", tags=["card-transactions"])


def _enrich(tx: CreditCardTransaction) -> CardTransactionOut:
    out = CardTransactionOut.model_validate(tx)
    if tx.categorization:
        out.category_id = tx.categorization.category_id
        out.category_source = tx.categorization.source
        if tx.categorization.category:
            out.category_name = tx.categorization.category.name
        if tx.categorization.rule:
            out.category_rule_name = rule_label(tx.categorization.rule)
    return out


@router.get("", response_model=list[CardTransactionOut])
async def list_card_transactions(
    instrument_id: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    category_id: str | None = Query(None),
    uncategorized: bool = Query(False),
    limit: int = Query(200, le=1000),
    offset: int = Query(0),
    response: Response = None,
    db: AsyncSession = Depends(get_db),
):
    def _apply_filters(q):
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
        if uncategorized:
            q = q.where(
                ~exists().where(
                    (Categorization.target_id == CreditCardTransaction.id)
                    & (Categorization.target_type == "card_transaction")
                )
            )
        return q

    count_q = _apply_filters(select(func.count()).select_from(CreditCardTransaction))
    total = await db.scalar(count_q)
    if response is not None:
        response.headers["X-Total-Count"] = str(total)

    q = _apply_filters(
        select(CreditCardTransaction)
        .options(
            selectinload(CreditCardTransaction.categorization).options(
                selectinload(Categorization.category),
                selectinload(Categorization.rule),
            )
        )
        .order_by(CreditCardTransaction.posted_date.desc())
    ).limit(limit).offset(offset)
    rows = (await db.scalars(q)).all()
    return [_enrich(tx) for tx in rows]
