"""Match bank transactions that represent credit card bill payments to statements.

Algorithm:
  For each open CreditCardStatement with a due_date:
    1. Find bank transactions on the same instrument (any bank account linked to
       the same user — we search all bank accounts for now) whose description
       matches a payment pattern AND whose date is within DATE_WINDOW days of
       due_date.
    2. Among those candidates, prefer exact-amount matches; fall back to
       partial-payment matches (amount <= total_minor).
    3. Create a StatementPaymentLink and auto-categorize the bank transaction
       as "transfer".
"""
import re
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BankTransaction,
    Categorization,
    Category,
    CategoryKind,
    CreditCard,
    CreditCardStatement,
    Instrument,
    InstrumentType,
    StatementPaymentLink,
    StatementStatus,
    TargetType,
)

# ---- tunables ----------------------------------------------------------------

DATE_WINDOW = 7          # days before/after due_date to look for payments
PARTIAL_THRESHOLD = 0.5  # candidate must be >= 50% of statement total

# ---- payment description patterns -------------------------------------------

_PAYMENT_RE = re.compile(
    r"(PAGAMENTO\s+(DE\s+)?FATURA|PAGTO\s+CART[AÃ]O|CARD\s+PAYMENT"
    r"|PAGTO\s+FATURA|PAG\s+FATURA|PAGAMENTO\s+CART[AÃ]O)",
    re.IGNORECASE,
)


def _is_payment(description: str) -> bool:
    return bool(_PAYMENT_RE.search(description))


# ---- helpers -----------------------------------------------------------------


async def _get_or_create_transfer_category(session: AsyncSession) -> Category:
    cat = await session.scalar(select(Category).where(Category.name == "transfer"))
    if cat:
        return cat
    cat = Category(name="transfer", kind=CategoryKind.transfer)
    session.add(cat)
    await session.flush()
    return cat


async def _categorize_bank_tx(
    session: AsyncSession,
    bank_tx: BankTransaction,
    category: Category,
) -> None:
    """Insert a Categorization for a bank tx if not already categorized."""
    existing = await session.scalar(
        select(Categorization).where(
            Categorization.target_type == TargetType.bank_transaction,
            Categorization.target_id == bank_tx.id,
        )
    )
    if existing:
        return
    session.add(
        Categorization(
            target_type=TargetType.bank_transaction,
            target_id=bank_tx.id,
            category_id=category.id,
            confidence=1.0,
        )
    )


async def _link_exists(
    session: AsyncSession,
    bank_tx_id: uuid.UUID,
    statement_id: uuid.UUID,
) -> bool:
    row = await session.scalar(
        select(StatementPaymentLink).where(
            StatementPaymentLink.bank_transaction_id == bank_tx_id,
            StatementPaymentLink.card_statement_id == statement_id,
        )
    )
    return row is not None


# ---- public API --------------------------------------------------------------


async def match_statement_payments(
    session: AsyncSession,
    instrument_ids: list[uuid.UUID] | None = None,
) -> int:
    """Scan statements and create payment links where bank payments are found.

    Args:
        instrument_ids: optional list of instrument IDs to restrict the search.
                        If None, all instruments are considered.

    Returns:
        Number of new StatementPaymentLinks created.
    """
    created = 0
    transfer_cat = await _get_or_create_transfer_category(session)

    # Load open statements (those not yet fully paid)
    stmt_q = select(CreditCardStatement).where(
        CreditCardStatement.status.in_([StatementStatus.open, StatementStatus.partial]),
        CreditCardStatement.due_date.is_not(None),
        CreditCardStatement.total_minor > 0,
    )
    statements = (await session.scalars(stmt_q)).all()

    for statement in statements:
        # Resolve the instrument_id for this credit card
        cc = await session.get(CreditCard, statement.credit_card_id)
        if cc is None:
            continue

        # Find all bank account instruments to search
        bank_inst_q = select(Instrument).where(
            Instrument.type == InstrumentType.bank_account,
        )
        if instrument_ids:
            bank_inst_q = bank_inst_q.where(Instrument.id.in_(instrument_ids))
        bank_instruments = (await session.scalars(bank_inst_q)).all()
        if not bank_instruments:
            continue

        bank_instrument_ids = [i.id for i in bank_instruments]

        # Date window around due_date
        due = statement.due_date
        date_lo = due - timedelta(days=DATE_WINDOW)
        date_hi = due + timedelta(days=DATE_WINDOW)

        # Fetch candidate bank transactions
        tx_q = select(BankTransaction).where(
            BankTransaction.instrument_id.in_(bank_instrument_ids),
            BankTransaction.posted_date >= date_lo,
            BankTransaction.posted_date <= date_hi,
            BankTransaction.amount_minor < 0,  # debits only
        )
        candidates = (await session.scalars(tx_q)).all()

        for tx in candidates:
            if not _is_payment(tx.description_raw):
                continue

            debit_abs = abs(tx.amount_minor)

            # Must cover at least PARTIAL_THRESHOLD of total
            if debit_abs < statement.total_minor * PARTIAL_THRESHOLD:
                continue

            if await _link_exists(session, tx.id, statement.id):
                continue

            session.add(
                StatementPaymentLink(
                    bank_transaction_id=tx.id,
                    card_statement_id=statement.id,
                    amount_minor=debit_abs,
                )
            )
            await _categorize_bank_tx(session, tx, transfer_cat)

            # Update statement status
            if debit_abs >= statement.total_minor:
                statement.status = StatementStatus.paid
            else:
                statement.status = StatementStatus.partial

            created += 1

    return created
