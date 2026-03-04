from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import (
    BankTransaction,
    Categorization,
    Category,
    CategoryKind,
    CreditCard,
    CreditCardTransaction,
    TargetType,
)
from app.schemas import SpendingByCategory, SpendingSummaryOut

router = APIRouter(prefix="/spending-summary", tags=["spending-summary"])


@router.get("", response_model=SpendingSummaryOut)
async def spending_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    instrument_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    # --- Card transactions (expenses = positive amount_minor) ---
    card_q = (
        select(CreditCardTransaction)
        .where(
            CreditCardTransaction.posted_date >= date_from,
            CreditCardTransaction.posted_date <= date_to,
            CreditCardTransaction.amount_minor > 0,
        )
    )
    if instrument_id:
        card_q = card_q.join(
            CreditCard, CreditCardTransaction.credit_card_id == CreditCard.id
        ).where(CreditCard.instrument_id == instrument_id)

    # --- Bank transactions (expenses = negative, excluding transfers) ---
    transfer_cat_ids = select(Category.id).where(Category.kind == CategoryKind.transfer)
    transfer_tx_ids = select(Categorization.target_id).where(
        Categorization.target_type == TargetType.bank_transaction,
        Categorization.category_id.in_(transfer_cat_ids),
    )
    bank_q = (
        select(BankTransaction)
        .where(
            BankTransaction.posted_date >= date_from,
            BankTransaction.posted_date <= date_to,
            BankTransaction.amount_minor < 0,
            BankTransaction.id.not_in(transfer_tx_ids),
        )
    )
    if instrument_id:
        bank_q = bank_q.where(BankTransaction.instrument_id == instrument_id)

    card_txs = (await db.scalars(card_q)).all()
    bank_txs = (await db.scalars(bank_q)).all()

    # Group by category
    category_map: dict[str, SpendingByCategory] = {}
    uncategorized = 0

    async def _get_category(target_type: TargetType, target_id) -> Category | None:
        categ = await db.scalar(
            select(Categorization).where(
                Categorization.target_type == target_type,
                Categorization.target_id == target_id,
            )
        )
        if categ is None:
            return None
        return await db.get(Category, categ.category_id)

    for tx in card_txs:
        cat = await _get_category(TargetType.card_transaction, tx.id)
        amt = tx.amount_minor
        if cat:
            key = cat.name
            if key not in category_map:
                category_map[key] = SpendingByCategory(
                    category_name=cat.name,
                    category_kind=cat.kind,
                    total_minor=0,
                    currency=tx.currency,
                    transaction_count=0,
                )
            category_map[key].total_minor += amt
            category_map[key].transaction_count += 1
        else:
            uncategorized += amt

    for tx in bank_txs:
        cat = await _get_category(TargetType.bank_transaction, tx.id)
        amt = abs(tx.amount_minor)
        if cat:
            key = cat.name
            if key not in category_map:
                category_map[key] = SpendingByCategory(
                    category_name=cat.name,
                    category_kind=cat.kind,
                    total_minor=0,
                    currency=tx.currency,
                    transaction_count=0,
                )
            category_map[key].total_minor += amt
            category_map[key].transaction_count += 1
        else:
            uncategorized += amt

    by_category = sorted(category_map.values(), key=lambda x: x.total_minor, reverse=True)
    total = sum(s.total_minor for s in by_category) + uncategorized

    return SpendingSummaryOut(
        date_from=date_from,
        date_to=date_to,
        by_category=by_category,
        uncategorized_minor=uncategorized,
        total_minor=total,
    )
