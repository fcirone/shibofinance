"""Import idempotency tests.

Verifies that re-importing the same data produces zero new rows and that
duplicate_count reflects the number of skipped rows.
"""
import uuid
from datetime import date, datetime, timezone

import pytest

from app.models import (
    BankTransaction,
    CreditCard,
    ImportBatch,
    ImportStatus,
    Instrument,
    InstrumentSource,
    InstrumentType,
)
from app.services.dedupe_service import upsert_bank_transactions, upsert_card_transactions
from core.fingerprint import compute_fingerprint
from core.normalizers import normalize_description
from importers.base import BankTransactionRow, CardTransactionRow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bank_row(instrument_id: str, desc: str, amount: int, d: date) -> BankTransactionRow:
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(instrument_id, d, "BRL", amount, desc_norm)
    return BankTransactionRow(
        posted_at=datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc),
        posted_date=d,
        description_raw=desc,
        description_norm=desc_norm,
        amount_minor=amount,
        currency="BRL",
        source_tx_id=None,
        fingerprint_hash=fp,
        raw_payload={},
    )


def _card_row(credit_card_id: str, desc: str, amount: int, d: date) -> CardTransactionRow:
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(credit_card_id, d, "BRL", amount, desc_norm)
    return CardTransactionRow(
        posted_at=datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc),
        posted_date=d,
        description_raw=desc,
        description_norm=desc_norm,
        merchant_raw=None,
        amount_minor=amount,
        currency="BRL",
        installments_total=None,
        installment_number=None,
        source_tx_id=None,
        fingerprint_hash=fp,
        raw_payload={},
    )


async def _make_instrument_and_batch(db_session, inst_type=InstrumentType.bank_account):
    inst = Instrument(
        name="Test",
        type=inst_type,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    db_session.add(inst)
    await db_session.flush()

    batch = ImportBatch(
        instrument_id=inst.id,
        filename="test.pdf",
        sha256="b" * 64,
        status=ImportStatus.processed,
    )
    db_session.add(batch)
    await db_session.flush()
    return inst, batch


# ---------------------------------------------------------------------------
# Bank transaction idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bank_tx_first_import_inserts(db_session):
    inst, batch = await _make_instrument_and_batch(db_session)
    rows = [
        _bank_row(str(inst.id), "PIX ENVIADO", -5000, date(2025, 12, 1)),
        _bank_row(str(inst.id), "SALARIO", 300000, date(2025, 12, 5)),
    ]

    inserted, duplicates, _ = await upsert_bank_transactions(db_session, rows, inst.id, batch)

    assert inserted == 2
    assert duplicates == 0


@pytest.mark.asyncio
async def test_bank_tx_reimport_produces_no_new_rows(db_session):
    inst, batch = await _make_instrument_and_batch(db_session)
    rows = [
        _bank_row(str(inst.id), "PIX ENVIADO", -5000, date(2025, 12, 1)),
        _bank_row(str(inst.id), "SALARIO", 300000, date(2025, 12, 5)),
    ]

    # First import
    await upsert_bank_transactions(db_session, rows, inst.id, batch)
    await db_session.flush()

    # Second import — same rows
    inserted, duplicates, _ = await upsert_bank_transactions(db_session, rows, inst.id, batch)

    assert inserted == 0
    assert duplicates == 2


@pytest.mark.asyncio
async def test_bank_tx_partial_reimport(db_session):
    inst, batch = await _make_instrument_and_batch(db_session)
    row_a = _bank_row(str(inst.id), "PIX ENVIADO", -5000, date(2025, 12, 1))
    row_b = _bank_row(str(inst.id), "SALARIO", 300000, date(2025, 12, 5))

    # First import: only row_a
    await upsert_bank_transactions(db_session, [row_a], inst.id, batch)
    await db_session.flush()

    # Second import: both rows — row_a is duplicate, row_b is new
    inserted, duplicates, _ = await upsert_bank_transactions(
        db_session, [row_a, row_b], inst.id, batch
    )

    assert inserted == 1
    assert duplicates == 1


# ---------------------------------------------------------------------------
# Card transaction idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_card_tx_reimport_produces_no_new_rows(db_session):
    inst, batch = await _make_instrument_and_batch(
        db_session, inst_type=InstrumentType.credit_card
    )
    cc = CreditCard(instrument_id=inst.id, statement_currency="BRL")
    db_session.add(cc)
    await db_session.flush()

    rows = [
        _card_row(str(cc.id), "AMAZON", 9900, date(2025, 12, 3)),
        _card_row(str(cc.id), "UBER", 2500, date(2025, 12, 7)),
    ]

    # First import
    await upsert_card_transactions(db_session, rows, cc.id, batch)
    await db_session.flush()

    # Second import — same rows
    inserted, duplicates, _ = await upsert_card_transactions(db_session, rows, cc.id, batch)

    assert inserted == 0
    assert duplicates == 2


# ---------------------------------------------------------------------------
# Fingerprint consistency (same input → same hash)
# ---------------------------------------------------------------------------


def test_fingerprint_same_input_same_hash():
    inst_id = "inst-001"
    d = date(2025, 12, 1)
    h1 = compute_fingerprint(inst_id, d, "BRL", -5000, "pix enviado")
    h2 = compute_fingerprint(inst_id, d, "BRL", -5000, "pix enviado")
    assert h1 == h2


def test_fingerprint_different_amounts_differ():
    inst_id = "inst-001"
    d = date(2025, 12, 1)
    h1 = compute_fingerprint(inst_id, d, "BRL", -5000, "pix enviado")
    h2 = compute_fingerprint(inst_id, d, "BRL", -5001, "pix enviado")
    assert h1 != h2
