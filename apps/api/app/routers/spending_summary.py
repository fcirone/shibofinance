from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
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

    # --- Bank transactions (income = positive, excluding transfers) ---
    income_bank_q = (
        select(BankTransaction)
        .where(
            BankTransaction.posted_date >= date_from,
            BankTransaction.posted_date <= date_to,
            BankTransaction.amount_minor > 0,
            BankTransaction.id.not_in(transfer_tx_ids),
        )
    )
    if instrument_id:
        income_bank_q = income_bank_q.where(BankTransaction.instrument_id == instrument_id)

    card_txs = (await db.scalars(card_q)).all()
    bank_txs = (await db.scalars(bank_q)).all()
    income_bank_txs = (await db.scalars(income_bank_q)).all()

    # Group by (direction_prefix, category_name, currency) to avoid mixing currencies.
    # Key format: "{prefix}__{category_name}__{currency}"
    category_map: dict[str, SpendingByCategory] = {}
    uncategorized_by_currency: dict[str, int] = {}
    uncategorized_income_by_currency: dict[str, int] = {}

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

    def _upsert(prefix: str, cat: Category, kind: CategoryKind, amt: int, currency: str) -> None:
        key = f"{prefix}__{cat.name}__{currency}"
        if key not in category_map:
            category_map[key] = SpendingByCategory(
                category_name=cat.name,
                category_kind=kind,
                total_minor=0,
                currency=currency,
                transaction_count=0,
            )
        category_map[key].total_minor += amt
        category_map[key].transaction_count += 1

    for tx in card_txs:
        cat = await _get_category(TargetType.card_transaction, tx.id)
        if cat:
            _upsert("expense", cat, cat.kind, tx.amount_minor, tx.currency)
        else:
            cur = tx.currency
            uncategorized_by_currency[cur] = uncategorized_by_currency.get(cur, 0) + tx.amount_minor

    for tx in bank_txs:
        cat = await _get_category(TargetType.bank_transaction, tx.id)
        amt = abs(tx.amount_minor)
        if cat:
            _upsert("expense", cat, cat.kind, amt, tx.currency)
        else:
            cur = tx.currency
            uncategorized_by_currency[cur] = uncategorized_by_currency.get(cur, 0) + amt

    for tx in income_bank_txs:
        cat = await _get_category(TargetType.bank_transaction, tx.id)
        amt = tx.amount_minor  # positive
        if cat:
            # Direction forced to income regardless of category.kind
            _upsert("income", cat, CategoryKind.income, amt, tx.currency)
        else:
            cur = tx.currency
            uncategorized_income_by_currency[cur] = uncategorized_income_by_currency.get(cur, 0) + amt

    by_category = sorted(category_map.values(), key=lambda x: x.total_minor, reverse=True)
    total = sum(s.total_minor for s in by_category if s.category_kind != CategoryKind.income) + sum(uncategorized_by_currency.values())

    return SpendingSummaryOut(
        date_from=date_from,
        date_to=date_to,
        by_category=by_category,
        uncategorized_by_currency=uncategorized_by_currency,
        uncategorized_income_by_currency=uncategorized_income_by_currency,
        total_minor=total,
    )
