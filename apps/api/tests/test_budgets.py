"""Tests for budget planning endpoints."""
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
from core.fingerprint import compute_fingerprint
from core.normalizers import normalize_description


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def food_category(db_session):
    cat = Category(name="Food & Dining Test", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()
    return cat


@pytest_asyncio.fixture
async def transfer_category(db_session):
    cat = Category(name="Transfer Test", kind=CategoryKind.transfer)
    db_session.add(cat)
    await db_session.flush()
    return cat


@pytest_asyncio.fixture
async def bank_instrument(db_session):
    inst = Instrument(
        name="Budget Test Bank",
        type=InstrumentType.bank_account,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    db_session.add(inst)
    await db_session.flush()
    return inst


@pytest_asyncio.fixture
async def card_instrument(db_session):
    inst = Instrument(
        name="Budget Test Card",
        type=InstrumentType.credit_card,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    db_session.add(inst)
    await db_session.flush()
    cc = CreditCard(instrument_id=inst.id, statement_currency="BRL")
    db_session.add(cc)
    await db_session.flush()
    return inst, cc


@pytest_asyncio.fixture
async def import_batch(db_session, bank_instrument):
    b = ImportBatch(
        instrument_id=bank_instrument.id,
        filename="budget_test.csv",
        sha256="c" * 64,
        status=ImportStatus.processed,
    )
    db_session.add(b)
    await db_session.flush()
    return b


# ---------------------------------------------------------------------------
# Tests: period CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_period(client):
    resp = await client.post("/budgets/periods", json={"year": 2026, "month": 3})
    assert resp.status_code == 201
    data = resp.json()
    assert data["year"] == 2026
    assert data["month"] == 3
    assert data["status"] == "open"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_period_duplicate(client):
    await client.post("/budgets/periods", json={"year": 2026, "month": 4})
    resp = await client.post("/budgets/periods", json={"year": 2026, "month": 4})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_period_invalid_month(client):
    resp = await client.post("/budgets/periods", json={"year": 2026, "month": 13})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_periods(client):
    await client.post("/budgets/periods", json={"year": 2025, "month": 1})
    await client.post("/budgets/periods", json={"year": 2026, "month": 2})
    resp = await client.get("/budgets/periods")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2
    # Newest first
    assert data[0]["year"] >= data[-1]["year"]


@pytest.mark.asyncio
async def test_get_period_not_found(client):
    resp = await client.get(f"/budgets/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: category budget lines
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_add_category_budget(client, food_category):
    r = await client.post("/budgets/periods", json={"year": 2026, "month": 5})
    period_id = r.json()["id"]

    resp = await client.post(
        f"/budgets/{period_id}/categories",
        json={"category_id": str(food_category.id), "planned_amount_minor": 50000},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["planned_amount_minor"] == 50000
    assert data["actual_amount_minor"] == 0
    assert data["remaining_amount_minor"] == 50000
    assert data["pct_consumed"] == 0.0
    assert data["category_name"] == food_category.name


@pytest.mark.asyncio
async def test_upsert_category_budget(client, food_category):
    r = await client.post("/budgets/periods", json={"year": 2026, "month": 6})
    period_id = r.json()["id"]

    await client.post(
        f"/budgets/{period_id}/categories",
        json={"category_id": str(food_category.id), "planned_amount_minor": 50000},
    )
    # Upsert same category
    resp = await client.post(
        f"/budgets/{period_id}/categories",
        json={"category_id": str(food_category.id), "planned_amount_minor": 80000},
    )
    assert resp.status_code == 201
    assert resp.json()["planned_amount_minor"] == 80000


@pytest.mark.asyncio
async def test_update_category_budget_item(client, food_category):
    r = await client.post("/budgets/periods", json={"year": 2026, "month": 7})
    period_id = r.json()["id"]

    add_resp = await client.post(
        f"/budgets/{period_id}/categories",
        json={"category_id": str(food_category.id), "planned_amount_minor": 30000},
    )
    item_id = add_resp.json()["id"]

    patch_resp = await client.patch(
        f"/budgets/category-items/{item_id}",
        json={"planned_amount_minor": 45000},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["planned_amount_minor"] == 45000


@pytest.mark.asyncio
async def test_update_item_not_found(client):
    resp = await client.patch(
        f"/budgets/category-items/{uuid.uuid4()}",
        json={"planned_amount_minor": 10000},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests: actual spending calculation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_actual_spending_from_card_transactions(
    client, db_session, food_category, card_instrument, import_batch
):
    _, cc = card_instrument

    # Card tx categorized to food — should count as actual
    d = date(2026, 3, 10)
    desc = "Restaurante test"
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(str(cc.id), d, "BRL", 12000, desc_norm)
    tx = CreditCardTransaction(
        credit_card_id=cc.id,
        posted_at=datetime(2026, 3, 10, 12, tzinfo=timezone.utc),
        posted_date=d,
        description_raw=desc,
        description_norm=desc_norm,
        amount_minor=12000,
        currency="BRL",
        fingerprint_hash=fp,
        import_batch_id=import_batch.id,
        raw_payload={},
    )
    db_session.add(tx)
    await db_session.flush()

    cat_entry = Categorization(
        target_type=TargetType.card_transaction,
        target_id=tx.id,
        category_id=food_category.id,
        source=CategorizationSource.manual,
    )
    db_session.add(cat_entry)
    await db_session.flush()

    # Create period for March 2026
    r = await client.post("/budgets/periods", json={"year": 2026, "month": 3})
    period_id = r.json()["id"]
    await client.post(
        f"/budgets/{period_id}/categories",
        json={"category_id": str(food_category.id), "planned_amount_minor": 50000},
    )

    detail = await client.get(f"/budgets/{period_id}")
    assert detail.status_code == 200
    data = detail.json()
    food_item = next(i for i in data["items"] if i["category_id"] == str(food_category.id))
    assert food_item["actual_amount_minor"] == 12000
    assert food_item["remaining_amount_minor"] == 38000


@pytest.mark.asyncio
async def test_actual_spending_from_bank_transactions(
    client, db_session, food_category, bank_instrument, import_batch
):
    d = date(2026, 3, 15)
    desc = "Supermercado test"
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(str(bank_instrument.id), d, "BRL", -8000, desc_norm)
    tx = BankTransaction(
        instrument_id=bank_instrument.id,
        posted_at=datetime(2026, 3, 15, 12, tzinfo=timezone.utc),
        posted_date=d,
        description_raw=desc,
        description_norm=desc_norm,
        amount_minor=-8000,
        currency="BRL",
        fingerprint_hash=fp,
        import_batch_id=import_batch.id,
        raw_payload={},
    )
    db_session.add(tx)
    await db_session.flush()

    cat_entry = Categorization(
        target_type=TargetType.bank_transaction,
        target_id=tx.id,
        category_id=food_category.id,
        source=CategorizationSource.manual,
    )
    db_session.add(cat_entry)
    await db_session.flush()

    r = await client.post("/budgets/periods", json={"year": 2026, "month": 3})
    period_id = r.json()["id"]
    await client.post(
        f"/budgets/{period_id}/categories",
        json={"category_id": str(food_category.id), "planned_amount_minor": 20000},
    )

    detail = await client.get(f"/budgets/{period_id}")
    data = detail.json()
    food_item = next(i for i in data["items"] if i["category_id"] == str(food_category.id))
    # abs(-8000) = 8000
    assert food_item["actual_amount_minor"] == 8000


@pytest.mark.asyncio
async def test_transfer_category_excluded_from_totals(client, transfer_category):
    r = await client.post("/budgets/periods", json={"year": 2026, "month": 8})
    period_id = r.json()["id"]
    await client.post(
        f"/budgets/{period_id}/categories",
        json={"category_id": str(transfer_category.id), "planned_amount_minor": 100000},
    )

    detail = await client.get(f"/budgets/{period_id}")
    data = detail.json()
    # Transfer categories don't count toward planned/actual totals
    assert data["planned_total_minor"] == 0
    assert data["actual_total_minor"] == 0


# ---------------------------------------------------------------------------
# Tests: copy-from period
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_copy_from_period(client, food_category):
    r1 = await client.post("/budgets/periods", json={"year": 2026, "month": 9})
    source_id = r1.json()["id"]
    await client.post(
        f"/budgets/{source_id}/categories",
        json={"category_id": str(food_category.id), "planned_amount_minor": 60000},
    )

    r2 = await client.post("/budgets/periods", json={"year": 2026, "month": 10})
    target_id = r2.json()["id"]

    copy_resp = await client.post(f"/budgets/{target_id}/copy-from/{source_id}")
    assert copy_resp.status_code == 200
    data = copy_resp.json()
    food_item = next(i for i in data["items"] if i["category_id"] == str(food_category.id))
    assert food_item["planned_amount_minor"] == 60000


@pytest.mark.asyncio
async def test_copy_from_nonexistent_source(client):
    r = await client.post("/budgets/periods", json={"year": 2026, "month": 11})
    target_id = r.json()["id"]
    resp = await client.post(f"/budgets/{target_id}/copy-from/{uuid.uuid4()}")
    assert resp.status_code == 404
