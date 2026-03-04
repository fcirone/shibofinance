from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import CreditCard, CreditCardStatement
from app.schemas import CardStatementOut

router = APIRouter(prefix="/card-statements", tags=["card-statements"])


@router.get("", response_model=list[CardStatementOut])
async def list_statements(
    instrument_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(CreditCardStatement).order_by(CreditCardStatement.statement_end.desc())
    if instrument_id:
        q = q.join(CreditCard, CreditCardStatement.credit_card_id == CreditCard.id).where(
            CreditCard.instrument_id == instrument_id
        )
    rows = await db.scalars(q)
    return rows.all()
