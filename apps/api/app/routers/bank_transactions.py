from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import BankTransaction
from app.schemas import BankTransactionOut

router = APIRouter(prefix="/bank-transactions", tags=["bank-transactions"])


@router.get("", response_model=list[BankTransactionOut])
async def list_bank_transactions(
    instrument_id: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(200, le=1000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    q = select(BankTransaction).order_by(BankTransaction.posted_date.desc())
    if instrument_id:
        q = q.where(BankTransaction.instrument_id == instrument_id)
    if date_from:
        q = q.where(BankTransaction.posted_date >= date_from)
    if date_to:
        q = q.where(BankTransaction.posted_date <= date_to)
    q = q.limit(limit).offset(offset)
    rows = await db.scalars(q)
    return rows.all()
