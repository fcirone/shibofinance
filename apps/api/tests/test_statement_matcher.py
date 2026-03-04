"""Integration tests for the statement payment matcher."""
import uuid
from datetime import date, datetime, timezone

import pytest

from app.models import (
    BankTransaction,
    Categorization,
    Category,
    CategoryKind,
    CreditCard,
    CreditCardStatement,
    Instrument,
    InstrumentSource,
    InstrumentType,
    StatementPaymentLink,
    StatementStatus,
    TargetType,
)
from app.services.statement_matcher import match_statement_payments


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _instrument(itype: InstrumentType, name: str = "test") -> Instrument:
    return Instrument(
        name=name,
        type=itype,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )


def _credit_card(instrument: Instrument) -> CreditCard:
    return CreditCard(instrument_id=instrument.id, statement_currency="BRL")


def _statement(
    credit_card: CreditCard,
    due_date: date,
    total_minor: int,
    status: StatementStatus = StatementStatus.open,
) -> CreditCardStatement:
    import uuid as _uuid
    from app.models import ImportBatch, ImportStatus
    # minimal import_batch_id placeholder — we insert a real one in each test
    return CreditCardStatement(
        credit_card_id=credit_card.id,
        statement_start=date(due_date.year, due_date.month - 1 or 12, 1),
        statement_end=due_date,
        closing_date=due_date,
        due_date=due_date,
        total_minor=total_minor,
        currency="BRL",
        status=status,
        import_batch_id=_uuid.uuid4(),  # will be overridden in tests
        raw_payload={},
    )


def _import_batch(instrument: Instrument) -> "ImportBatch":
    from app.models import ImportBatch, ImportStatus
    return ImportBatch(
        instrument_id=instrument.id,
        filename="test.pdf",
        sha256="a" * 64,
        status=ImportStatus.processed,
        inserted_count=1,
    )


def _bank_tx(
    instrument: Instrument,
    batch,
    description: str,
    amount_minor: int,
    posted_date: date,
) -> BankTransaction:
    from core.fingerprint import compute_fingerprint
    from core.normalizers import normalize_description
    desc_norm = normalize_description(description)
    fp = compute_fingerprint(str(instrument.id), posted_date, "BRL", amount_minor, desc_norm)
    return BankTransaction(
        instrument_id=instrument.id,
        posted_at=datetime(posted_date.year, posted_date.month, posted_date.day, 12, 0, tzinfo=timezone.utc),
        posted_date=posted_date,
        description_raw=description,
        description_norm=desc_norm,
        amount_minor=amount_minor,
        currency="BRL",
        fingerprint_hash=fp,
        import_batch_id=batch.id,
        raw_payload={},
    )


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_exact_match_creates_link(db_session):
    """An exact-amount payment within the date window creates a link."""
    bank_inst = _instrument(InstrumentType.bank_account, "bank")
    card_inst = _instrument(InstrumentType.credit_card, "card")
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()

    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()

    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=100000,  # R$ 1000.00
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "PAGAMENTO DE FATURA CARTAO", -100000, date(2025, 12, 9))
    db_session.add(tx)
    await db_session.flush()

    created = await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    assert created == 1

    link = await db_session.scalar(
        __import__("sqlalchemy", fromlist=["select"]).select(StatementPaymentLink).where(
            StatementPaymentLink.bank_transaction_id == tx.id,
            StatementPaymentLink.card_statement_id == stmt.id,
        )
    )
    assert link is not None
    assert link.amount_minor == 100000


@pytest.mark.asyncio
async def test_exact_match_marks_statement_paid(db_session):
    bank_inst = _instrument(InstrumentType.bank_account)
    card_inst = _instrument(InstrumentType.credit_card)
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()
    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()
    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=50000,
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "PAGTO CARTAO SANTANDER", -50000, date(2025, 12, 10))
    db_session.add(tx)
    await db_session.flush()

    await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    assert stmt.status == StatementStatus.paid


@pytest.mark.asyncio
async def test_partial_payment_marks_statement_partial(db_session):
    bank_inst = _instrument(InstrumentType.bank_account)
    card_inst = _instrument(InstrumentType.credit_card)
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()
    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()
    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=100000,
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    # Pays 60% — above PARTIAL_THRESHOLD (50%) but below total
    tx = _bank_tx(bank_inst, batch, "PAGAMENTO FATURA", -60000, date(2025, 12, 8))
    db_session.add(tx)
    await db_session.flush()

    await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    assert stmt.status == StatementStatus.partial


@pytest.mark.asyncio
async def test_too_small_payment_ignored(db_session):
    """A payment below PARTIAL_THRESHOLD is not matched."""
    bank_inst = _instrument(InstrumentType.bank_account)
    card_inst = _instrument(InstrumentType.credit_card)
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()
    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()
    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=100000,
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "PAGAMENTO FATURA", -10000, date(2025, 12, 10))  # 10%
    db_session.add(tx)
    await db_session.flush()

    created = await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    assert created == 0


@pytest.mark.asyncio
async def test_out_of_date_window_ignored(db_session):
    """A payment outside DATE_WINDOW days is not matched."""
    bank_inst = _instrument(InstrumentType.bank_account)
    card_inst = _instrument(InstrumentType.credit_card)
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()
    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()
    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=100000,
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    # 30 days after due_date — way outside window
    tx = _bank_tx(bank_inst, batch, "PAGAMENTO FATURA", -100000, date(2026, 1, 10))
    db_session.add(tx)
    await db_session.flush()

    created = await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    assert created == 0


@pytest.mark.asyncio
async def test_non_payment_description_ignored(db_session):
    """A debit with a non-payment description is not matched."""
    bank_inst = _instrument(InstrumentType.bank_account)
    card_inst = _instrument(InstrumentType.credit_card)
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()
    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()
    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=100000,
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "PIX ENVIADO Eduardo Cirone", -100000, date(2025, 12, 10))
    db_session.add(tx)
    await db_session.flush()

    created = await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    assert created == 0


@pytest.mark.asyncio
async def test_idempotent_no_duplicate_links(db_session):
    """Running the matcher twice does not create duplicate links."""
    bank_inst = _instrument(InstrumentType.bank_account)
    card_inst = _instrument(InstrumentType.credit_card)
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()
    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()
    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=100000,
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "PAGAMENTO DE FATURA", -100000, date(2025, 12, 10))
    db_session.add(tx)
    await db_session.flush()

    c1 = await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    c2 = await match_statement_payments(db_session, instrument_ids=[bank_inst.id])
    assert c1 == 1
    assert c2 == 0


@pytest.mark.asyncio
async def test_auto_categorize_as_transfer(db_session):
    """Matched bank transaction is categorized as 'transfer'."""
    bank_inst = _instrument(InstrumentType.bank_account)
    card_inst = _instrument(InstrumentType.credit_card)
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()
    cc = _credit_card(card_inst)
    db_session.add(cc)
    await db_session.flush()
    batch = _import_batch(bank_inst)
    db_session.add(batch)
    await db_session.flush()

    stmt = CreditCardStatement(
        credit_card_id=cc.id,
        statement_start=date(2025, 11, 1),
        statement_end=date(2025, 11, 30),
        closing_date=date(2025, 11, 30),
        due_date=date(2025, 12, 10),
        total_minor=75000,
        currency="BRL",
        status=StatementStatus.open,
        import_batch_id=batch.id,
        raw_payload={},
    )
    db_session.add(stmt)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "PAGAMENTO FATURA", -75000, date(2025, 12, 10))
    db_session.add(tx)
    await db_session.flush()

    await match_statement_payments(db_session, instrument_ids=[bank_inst.id])

    from sqlalchemy import select
    categ = await db_session.scalar(
        select(Categorization).where(
            Categorization.target_type == TargetType.bank_transaction,
            Categorization.target_id == tx.id,
        )
    )
    assert categ is not None
    cat = await db_session.get(Category, categ.category_id)
    assert cat.name == "transfer"
    assert cat.kind == CategoryKind.transfer
