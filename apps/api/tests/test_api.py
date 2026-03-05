"""API endpoint tests using httpx AsyncClient."""
import uuid
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.main import app
from app.models import (
    BankTransaction,
    CreditCard,
    CreditCardStatement,
    CreditCardTransaction,
    ImportBatch,
    ImportStatus,
    Instrument,
    InstrumentSource,
    InstrumentType,
    StatementStatus,
)
from core.fingerprint import compute_fingerprint
from core.normalizers import normalize_description


# ---------------------------------------------------------------------------
# Client fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session):
    """AsyncClient wired to the FastAPI app with a test DB session."""
    from app.db import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_bank_tx(instrument, batch, desc, amount, d):
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(str(instrument.id), d, "BRL", amount, desc_norm)
    return BankTransaction(
        instrument_id=instrument.id,
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


def _make_card_tx(credit_card, batch, desc, amount, d):
    desc_norm = normalize_description(desc)
    fp = compute_fingerprint(str(credit_card.id), d, "BRL", amount, desc_norm)
    return CreditCardTransaction(
        credit_card_id=credit_card.id,
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


async def _seed(db_session):
    """Seed minimal test data and return (bank_inst, card_inst, batch)."""
    bank_inst = Instrument(
        name="Test Bank",
        type=InstrumentType.bank_account,
        source=InstrumentSource.santander_br,
        currency="BRL",
        source_instrument_id=str(uuid.uuid4()),
    )
    card_inst = Instrument(
        name="Test Card",
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


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_instrument(client, db_session):
    r = await client.post("/instruments", json={
        "name": "Santander Conta",
        "type": "bank_account",
        "source": "santander_br",
        "currency": "BRL",
        "source_instrument_id": "12345",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Santander Conta"
    assert data["type"] == "bank_account"


@pytest.mark.asyncio
async def test_list_instruments(client, db_session):
    bank_inst, _, _, _ = await _seed(db_session)
    r = await client.get("/instruments")
    assert r.status_code == 200
    ids = [i["id"] for i in r.json()]
    assert str(bank_inst.id) in ids


@pytest.mark.asyncio
async def test_get_instrument_not_found(client):
    r = await client.get(f"/instruments/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Bank transactions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_bank_transactions(client, db_session):
    bank_inst, _, _, batch = await _seed(db_session)
    tx = _make_bank_tx(bank_inst, batch, "PIX ENVIADO Teste", -5000, date(2025, 12, 1))
    db_session.add(tx)
    await db_session.flush()

    r = await client.get("/bank-transactions", params={"instrument_id": str(bank_inst.id)})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["amount_minor"] == -5000


@pytest.mark.asyncio
async def test_bank_transactions_date_filter(client, db_session):
    bank_inst, _, _, batch = await _seed(db_session)
    db_session.add(_make_bank_tx(bank_inst, batch, "PIX A", -1000, date(2025, 11, 1)))
    db_session.add(_make_bank_tx(bank_inst, batch, "PIX B", -2000, date(2025, 12, 1)))
    await db_session.flush()

    r = await client.get("/bank-transactions", params={
        "instrument_id": str(bank_inst.id),
        "date_from": "2025-12-01",
    })
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["amount_minor"] == -2000


# ---------------------------------------------------------------------------
# Card transactions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_card_transactions(client, db_session):
    bank_inst, card_inst, cc, batch = await _seed(db_session)
    tx = _make_card_tx(cc, batch, "AMAZON", 9900, date(2025, 12, 5))
    db_session.add(tx)
    await db_session.flush()

    r = await client.get("/card-transactions", params={"instrument_id": str(card_inst.id)})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["amount_minor"] == 9900


# ---------------------------------------------------------------------------
# Card statements
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_card_statements(client, db_session):
    bank_inst, card_inst, cc, batch = await _seed(db_session)
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

    r = await client.get("/card-statements", params={"instrument_id": str(card_inst.id)})
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["total_minor"] == 50000


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_categories_empty(client, db_session):
    r = await client.get("/categories")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_categorize_transaction(client, db_session):
    from app.models import Category, CategoryKind
    bank_inst, _, _, batch = await _seed(db_session)
    cat = Category(name="alimentacao", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx = _make_bank_tx(bank_inst, batch, "IFOOD", -3000, date(2025, 12, 10))
    db_session.add(tx)
    await db_session.flush()

    r = await client.post("/categorize", json={
        "target_type": "bank_transaction",
        "target_id": str(tx.id),
        "category_id": str(cat.id),
        "confidence": 0.9,
    })
    assert r.status_code == 201
    assert r.json()["category_id"] == str(cat.id)


# ---------------------------------------------------------------------------
# Spending summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_spending_summary(client, db_session):
    from app.models import Category, CategoryKind
    bank_inst, card_inst, cc, batch = await _seed(db_session)

    cat = Category(name="restaurante", kind=CategoryKind.expense)
    db_session.add(cat)
    await db_session.flush()

    tx = _make_card_tx(cc, batch, "RESTAURANTE ABC", 8000, date(2025, 12, 5))
    db_session.add(tx)
    await db_session.flush()

    from app.models import Categorization, TargetType
    db_session.add(Categorization(
        target_type=TargetType.card_transaction,
        target_id=tx.id,
        category_id=cat.id,
    ))
    await db_session.flush()

    r = await client.get("/spending-summary", params={
        "date_from": "2025-12-01",
        "date_to": "2025-12-31",
        "instrument_id": str(card_inst.id),
    })
    assert r.status_code == 200
    data = r.json()
    assert data["total_minor"] == 8000
    assert len(data["by_category"]) == 1
    assert data["by_category"][0]["category_name"] == "restaurante"


@pytest.mark.asyncio
async def test_spending_summary_missing_params(client):
    r = await client.get("/spending-summary")
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Import batches
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_import_batches(client, db_session):
    bank_inst, _, _, batch = await _seed(db_session)
    r = await client.get("/imports")
    assert r.status_code == 200
    ids = [b["id"] for b in r.json()]
    assert str(batch.id) in ids


@pytest.mark.asyncio
async def test_list_import_batches_filter_by_instrument(client, db_session):
    bank_inst, card_inst, _, batch = await _seed(db_session)
    # Create a second batch for card_inst
    batch2 = ImportBatch(
        instrument_id=card_inst.id,
        filename="card.csv",
        sha256="b" * 64,
        status=ImportStatus.processed,
    )
    db_session.add(batch2)
    await db_session.flush()

    r = await client.get("/imports", params={"instrument_id": str(bank_inst.id)})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["id"] == str(batch.id)


@pytest.mark.asyncio
async def test_get_import_batch(client, db_session):
    bank_inst, _, _, batch = await _seed(db_session)
    r = await client.get(f"/imports/{batch.id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == str(batch.id)
    assert data["filename"] == "test.pdf"
    assert data["status"] == "processed"


@pytest.mark.asyncio
async def test_get_import_batch_not_found(client):
    r = await client.get(f"/imports/{uuid.uuid4()}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_import_batches_pagination(client, db_session):
    """limit/offset params are respected."""
    bank_inst, _, _, _ = await _seed(db_session)
    for i in range(3):
        db_session.add(ImportBatch(
            instrument_id=bank_inst.id,
            filename=f"file{i}.csv",
            sha256=str(i) * 64,
            status=ImportStatus.processed,
        ))
    await db_session.flush()

    r = await client.get("/imports", params={"instrument_id": str(bank_inst.id), "limit": 2, "offset": 0})
    assert r.status_code == 200
    assert len(r.json()) == 2

    r2 = await client.get("/imports", params={"instrument_id": str(bank_inst.id), "limit": 2, "offset": 2})
    assert r2.status_code == 200
    assert len(r2.json()) == 2  # 1 original + 3 added = 4 total; offset 2 → 2 remaining
