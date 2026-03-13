"""Tests for payables and recurring patterns endpoints."""
import uuid
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio

from app.models import (
    BankTransaction,
    Category,
    CategoryKind,
    Categorization,
    CategorizationSource,
    CreditCard,
    CreditCardTransaction,
    ImportBatch,
    ImportStatus,
    Instrument,
    InstrumentSource,
    InstrumentType,
    TargetType,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def expense_category(db_session):
    cat = Category(name="Payables Test Expense", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()
    return cat


@pytest_asyncio.fixture
async def bank_instrument(db_session):
    inst = Instrument(
        name="Payables Test Bank",
        type=InstrumentType.bank_account,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    db_session.add(inst)
    await db_session.flush()
    return inst


@pytest_asyncio.fixture
async def import_batch(db_session, bank_instrument):
    b = ImportBatch(
        instrument_id=bank_instrument.id,
        filename="payables_test.csv",
        sha256="e" * 64,
        status=ImportStatus.processed,
    )
    db_session.add(b)
    await db_session.flush()
    return b


def _bank_tx(instrument_id, import_batch_id, posted_date, description_norm, amount_minor):
    """Helper to create a BankTransaction with minimal fields."""
    return BankTransaction(
        instrument_id=instrument_id,
        posted_at=datetime(posted_date.year, posted_date.month, posted_date.day, tzinfo=timezone.utc),
        posted_date=posted_date,
        description_raw=description_norm,
        description_norm=description_norm,
        amount_minor=amount_minor,
        currency="BRL",
        fingerprint_hash=uuid.uuid4().hex,
        import_batch_id=import_batch_id,
        raw_payload={},
    )


# ---------------------------------------------------------------------------
# Tests: recurring patterns
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_recurring_patterns_empty(client):
    resp = await client.get("/recurring-patterns")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_recurring_pattern_manual(client):
    resp = await client.post(
        "/recurring-patterns",
        json={
            "name": "Netflix",
            "normalized_description": "netflix subscription",
            "cadence": "monthly",
            "expected_amount_minor": 3990,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Netflix"
    assert data["status"] == "approved"
    assert data["detection_source"] == "manual"
    assert data["expected_amount_minor"] == 3990


@pytest.mark.asyncio
async def test_create_recurring_pattern_duplicate(client):
    payload = {"name": "X", "normalized_description": "duplicate description", "cadence": "monthly"}
    await client.post("/recurring-patterns", json=payload)
    resp = await client.post("/recurring-patterns", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_approve_and_ignore_pattern(client):
    resp = await client.post(
        "/recurring-patterns",
        json={"name": "Spotify", "normalized_description": "spotify", "cadence": "monthly"},
    )
    pattern_id = resp.json()["id"]

    resp = await client.post(f"/recurring-patterns/{pattern_id}/ignore")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ignored"

    resp = await client.post(f"/recurring-patterns/{pattern_id}/approve")
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


@pytest.mark.asyncio
async def test_detect_recurring_patterns(client, db_session, bank_instrument, import_batch):
    """Detection creates a suggestion when the same description appears 3+ times across 2+ months."""
    desc = "energia eletrica mensal"
    for i, dt in enumerate([
        date(2026, 1, 10),
        date(2026, 2, 10),
        date(2026, 3, 10),
    ]):
        tx = _bank_tx(bank_instrument.id, import_batch.id, dt, desc, -(5000 + i * 10))
        db_session.add(tx)
    await db_session.flush()

    resp = await client.post("/recurring-patterns/detect")
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] >= 1

    # Pattern should appear in list
    resp = await client.get("/recurring-patterns?status=suggested")
    assert resp.status_code == 200
    names = [p["normalized_description"] for p in resp.json()]
    assert desc in names


@pytest.mark.asyncio
async def test_detect_skips_insufficient_occurrences(client, db_session, bank_instrument, import_batch):
    """Descriptions with fewer than 3 occurrences or 2 months should not be suggested."""
    desc = "compra isolada"
    tx = _bank_tx(bank_instrument.id, import_batch.id, date(2026, 1, 5), desc, -1000)
    db_session.add(tx)
    await db_session.flush()

    resp = await client.post("/recurring-patterns/detect")
    assert resp.status_code == 200

    resp = await client.get("/recurring-patterns")
    descs = [p["normalized_description"] for p in resp.json()]
    assert desc not in descs


# ---------------------------------------------------------------------------
# Tests: payables
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_payable(client):
    resp = await client.post(
        "/payables",
        json={"name": "Internet Bill", "default_amount_minor": 9990, "notes": "monthly"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Internet Bill"
    assert data["source_type"] == "manual"
    assert data["default_amount_minor"] == 9990


@pytest.mark.asyncio
async def test_list_payables(client):
    await client.post("/payables", json={"name": "Rent", "default_amount_minor": 200000})
    resp = await client.get("/payables")
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert "Rent" in names


# ---------------------------------------------------------------------------
# Tests: payable occurrences
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_and_list_occurrences(client):
    # Create two payables
    await client.post("/payables", json={"name": "Water Bill", "default_amount_minor": 5000})
    await client.post("/payables", json={"name": "Gas Bill", "default_amount_minor": 3000})

    resp = await client.post("/payable-occurrences/generate", json={"month": 3, "year": 2026})
    assert resp.status_code == 200
    data = resp.json()
    assert data["created"] >= 2

    resp = await client.get("/payable-occurrences?month=3&year=2026")
    assert resp.status_code == 200
    names = [o["payable_name"] for o in resp.json()]
    assert "Water Bill" in names
    assert "Gas Bill" in names


@pytest.mark.asyncio
async def test_generate_occurrences_idempotent(client):
    await client.post("/payables", json={"name": "Phone Bill", "default_amount_minor": 7000})
    await client.post("/payable-occurrences/generate", json={"month": 4, "year": 2026})
    resp = await client.post("/payable-occurrences/generate", json={"month": 4, "year": 2026})
    assert resp.status_code == 200
    assert resp.json()["created"] == 0


@pytest.mark.asyncio
async def test_update_occurrence_status(client):
    await client.post("/payables", json={"name": "Streaming", "default_amount_minor": 4000})
    await client.post("/payable-occurrences/generate", json={"month": 5, "year": 2026})

    resp = await client.get("/payable-occurrences?month=5&year=2026")
    occurrence_id = resp.json()[0]["id"]

    resp = await client.patch(
        f"/payable-occurrences/{occurrence_id}",
        json={"status": "paid", "actual_amount_minor": 4000},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "paid"
    assert data["actual_amount_minor"] == 4000


@pytest.mark.asyncio
async def test_update_occurrence_not_found(client):
    resp = await client.patch(
        f"/payable-occurrences/{uuid.uuid4()}",
        json={"status": "paid"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_generate_invalid_month(client):
    resp = await client.post("/payable-occurrences/generate", json={"month": 13, "year": 2026})
    assert resp.status_code == 422
