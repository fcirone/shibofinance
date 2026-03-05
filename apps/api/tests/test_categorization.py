"""Tests for Phase 23 — Categorization Cycle 1."""
import uuid
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models import (
    BankTransaction,
    Categorization,
    CategorizationSource,
    Category,
    CategoryKind,
    CreditCard,
    CreditCardTransaction,
    ImportBatch,
    ImportStatus,
    Instrument,
    InstrumentSource,
    InstrumentType,
    TargetType,
)
from core.fingerprint import compute_fingerprint
from core.normalizers import normalize_description


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session):
    from app.db import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def _seed_base(db_session):
    bank_inst = Instrument(
        name="Bank",
        type=InstrumentType.bank_account,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    card_inst = Instrument(
        name="Card",
        type=InstrumentType.credit_card,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    db_session.add_all([bank_inst, card_inst])
    await db_session.flush()

    cc = CreditCard(instrument_id=card_inst.id, statement_currency="BRL")
    db_session.add(cc)
    await db_session.flush()

    batch = ImportBatch(
        instrument_id=bank_inst.id,
        filename="test.pdf",
        sha256="a" * 64,
        status=ImportStatus.processed,
    )
    db_session.add(batch)
    await db_session.flush()
    return bank_inst, card_inst, cc, batch


def _bank_tx(inst, batch, desc, amount, d):
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(str(inst.id), d, "BRL", amount, desc_norm)
    return BankTransaction(
        instrument_id=inst.id,
        posted_at=datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc),
        posted_date=d,
        description_raw=desc,
        description_norm=desc_norm,
        amount_minor=amount,
        currency="BRL",
        fingerprint_hash=fp,
        import_batch_id=batch.id,
        raw_payload={},
    )


def _card_tx(cc, batch, desc, amount, d):
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(str(cc.id), d, "BRL", amount, desc_norm)
    return CreditCardTransaction(
        credit_card_id=cc.id,
        posted_at=datetime(d.year, d.month, d.day, 12, tzinfo=timezone.utc),
        posted_date=d,
        description_raw=desc,
        description_norm=desc_norm,
        amount_minor=amount,
        currency="BRL",
        fingerprint_hash=fp,
        import_batch_id=batch.id,
        raw_payload={},
    )


# ---------------------------------------------------------------------------
# Category CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_category(client):
    r = await client.post("/categories", json={"name": "Groceries", "kind": "expense"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Groceries"
    assert data["kind"] == "expense"
    assert data["parent_id"] is None


@pytest.mark.asyncio
async def test_create_category_duplicate_name(client):
    await client.post("/categories", json={"name": "DupCat", "kind": "expense"})
    r = await client.post("/categories", json={"name": "DupCat", "kind": "income"})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_category(client, db_session):
    cat = Category(name="OldName", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    r = await client.patch(f"/categories/{cat.id}", json={"name": "NewName"})
    assert r.status_code == 200
    assert r.json()["name"] == "NewName"


@pytest.mark.asyncio
async def test_delete_category(client, db_session):
    cat = Category(name="Unused", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    r = await client.delete(f"/categories/{cat.id}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_delete_category_in_use(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    cat = Category(name="InUse", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "TEST", -1000, date(2025, 12, 1))
    db_session.add(tx)
    await db_session.flush()

    db_session.add(Categorization(
        target_type=TargetType.bank_transaction,
        target_id=tx.id,
        category_id=cat.id,
        source=CategorizationSource.manual,
    ))
    await db_session.flush()

    r = await client.delete(f"/categories/{cat.id}")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# POST /categorize
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_categorize_creates(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    cat = Category(name="Food", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "IFOOD", -2000, date(2025, 12, 5))
    db_session.add(tx)
    await db_session.flush()

    r = await client.post("/categorize", json={
        "target_type": "bank_transaction",
        "target_id": str(tx.id),
        "category_id": str(cat.id),
    })
    assert r.status_code == 201
    data = r.json()
    assert data["category_id"] == str(cat.id)
    assert data["source"] == "manual"


@pytest.mark.asyncio
async def test_categorize_upserts(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    cat1 = Category(name="Cat1", kind=CategoryKind.expense)
    cat2 = Category(name="Cat2", kind=CategoryKind.expense)
    db_session.add_all([cat1, cat2])
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "UBER", -3000, date(2025, 12, 6))
    db_session.add(tx)
    await db_session.flush()

    await client.post("/categorize", json={
        "target_type": "bank_transaction",
        "target_id": str(tx.id),
        "category_id": str(cat1.id),
    })
    r = await client.post("/categorize", json={
        "target_type": "bank_transaction",
        "target_id": str(tx.id),
        "category_id": str(cat2.id),
    })
    assert r.status_code == 201
    assert r.json()["category_id"] == str(cat2.id)


@pytest.mark.asyncio
async def test_categorize_unknown_category(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    tx = _bank_tx(bank_inst, batch, "UNKNOWN", -500, date(2025, 12, 7))
    db_session.add(tx)
    await db_session.flush()

    r = await client.post("/categorize", json={
        "target_type": "bank_transaction",
        "target_id": str(tx.id),
        "category_id": str(uuid.uuid4()),
    })
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /categorizations/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_categorization(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    cat = Category(name="DelCat", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "DELETE ME", -100, date(2025, 12, 8))
    db_session.add(tx)
    await db_session.flush()

    categ = Categorization(
        target_type=TargetType.bank_transaction,
        target_id=tx.id,
        category_id=cat.id,
        source=CategorizationSource.manual,
    )
    db_session.add(categ)
    await db_session.flush()

    r = await client.delete(f"/categorizations/{categ.id}")
    assert r.status_code == 204


# ---------------------------------------------------------------------------
# Bulk categorize
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bulk_categorize(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    cat = Category(name="Bulk", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx1 = _bank_tx(bank_inst, batch, "TX1", -100, date(2025, 12, 1))
    tx2 = _bank_tx(bank_inst, batch, "TX2", -200, date(2025, 12, 2))
    db_session.add_all([tx1, tx2])
    await db_session.flush()

    r = await client.post("/categorize/bulk", json={"items": [
        {"target_type": "bank_transaction", "target_id": str(tx1.id), "category_id": str(cat.id)},
        {"target_type": "bank_transaction", "target_id": str(tx2.id), "category_id": str(cat.id)},
    ]})
    assert r.status_code == 200
    data = r.json()
    assert data["created"] == 2
    assert data["updated"] == 0


# ---------------------------------------------------------------------------
# Category in transaction list response
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bank_tx_includes_category(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    cat = Category(name="TxCat", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx = _bank_tx(bank_inst, batch, "MERCADO", -4000, date(2025, 12, 9))
    db_session.add(tx)
    await db_session.flush()

    db_session.add(Categorization(
        target_type=TargetType.bank_transaction,
        target_id=tx.id,
        category_id=cat.id,
        source=CategorizationSource.manual,
    ))
    await db_session.flush()

    r = await client.get("/bank-transactions", params={"instrument_id": str(bank_inst.id)})
    assert r.status_code == 200
    row = r.json()[0]
    assert row["category_id"] == str(cat.id)
    assert row["category_name"] == "TxCat"


@pytest.mark.asyncio
async def test_bank_tx_search_filter(client, db_session):
    bank_inst, _, _, batch = await _seed_base(db_session)
    db_session.add(_bank_tx(bank_inst, batch, "MERCADO LIVRE", -1000, date(2025, 12, 1)))
    db_session.add(_bank_tx(bank_inst, batch, "PIX ENVIADO", -2000, date(2025, 12, 2)))
    await db_session.flush()

    r = await client.get("/bank-transactions", params={
        "instrument_id": str(bank_inst.id),
        "search": "MERCADO",
    })
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert "MERCADO" in r.json()[0]["description_raw"]


@pytest.mark.asyncio
async def test_card_tx_includes_category(client, db_session):
    bank_inst, card_inst, cc, batch = await _seed_base(db_session)
    cat = Category(name="CardCat", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx = _card_tx(cc, batch, "AMAZON", 5000, date(2025, 12, 10))
    db_session.add(tx)
    await db_session.flush()

    db_session.add(Categorization(
        target_type=TargetType.card_transaction,
        target_id=tx.id,
        category_id=cat.id,
        source=CategorizationSource.manual,
    ))
    await db_session.flush()

    r = await client.get("/card-transactions", params={"instrument_id": str(card_inst.id)})
    assert r.status_code == 200
    row = r.json()[0]
    assert row["category_id"] == str(cat.id)
    assert row["category_name"] == "CardCat"
