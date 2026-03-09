"""Tests for the category rules engine and API endpoints."""
import uuid
from datetime import date, datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models import (
    BankTransaction,
    Categorization,
    CategorizationSource,
    Category,
    CategoryKind,
    CategoryRule,
    MatchField,
    MatchOperator,
    RuleTargetType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _make_category(db, name="Test", kind=CategoryKind.expense):
    cat = await db.scalar(select(Category).where(Category.name == name))
    if not cat:
        cat = Category(id=uuid.uuid4(), name=name, kind=kind)
        db.add(cat)
        await db.flush()
    return cat


async def _make_rule(db, cat_id, field=MatchField.description_norm, op=MatchOperator.contains, value="netflix", target=RuleTargetType.bank_transaction, priority=100, enabled=True):
    rule = CategoryRule(
        id=uuid.uuid4(),
        category_id=cat_id,
        match_field=field,
        match_operator=op,
        match_value=value,
        target_type=target,
        priority=priority,
        enabled=enabled,
    )
    db.add(rule)
    await db.flush()
    return rule


async def _make_bank_tx(db, inst_id, batch_id, description="NETFLIX", amount=-1500):
    tx = BankTransaction(
        id=uuid.uuid4(),
        instrument_id=inst_id,
        posted_at=datetime(2025, 1, 1, 12, tzinfo=timezone.utc),
        posted_date=date(2025, 1, 1),
        description_raw=description,
        description_norm=description.lower(),
        amount_minor=amount,
        currency="BRL",
        fingerprint_hash=str(uuid.uuid4()),
        import_batch_id=batch_id,
        raw_payload={},
    )
    db.add(tx)
    await db.flush()
    return tx


# ---------------------------------------------------------------------------
# Rule CRUD
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_list_rules_empty(client: AsyncClient):
    resp = await client.get("/category-rules")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_create_rule(client: AsyncClient, db_session):
    cat = await _make_category(db_session, "Entertainment")
    await db_session.commit()

    resp = await client.post("/category-rules", json={
        "category_id": str(cat.id),
        "match_field": "description_norm",
        "match_operator": "contains",
        "match_value": "netflix",
        "target_type": "bank_transaction",
        "priority": 10,
        "enabled": True,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["match_value"] == "netflix"
    assert data["category_name"] == "Entertainment"
    assert data["priority"] == 10


@pytest.mark.anyio
async def test_create_rule_invalid_combo(client: AsyncClient, db_session):
    cat = await _make_category(db_session, "Foo")
    await db_session.commit()

    # gte on description_norm is invalid
    resp = await client.post("/category-rules", json={
        "category_id": str(cat.id),
        "match_field": "description_norm",
        "match_operator": "gte",
        "match_value": "100",
        "target_type": "bank_transaction",
    })
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_update_rule(client: AsyncClient, db_session):
    cat = await _make_category(db_session, "Shopping")
    rule = await _make_rule(db_session, cat.id)
    await db_session.commit()

    resp = await client.patch(f"/category-rules/{rule.id}", json={"priority": 5, "enabled": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority"] == 5
    assert data["enabled"] is False


@pytest.mark.anyio
async def test_delete_rule(client: AsyncClient, db_session):
    cat = await _make_category(db_session, "Health")
    rule = await _make_rule(db_session, cat.id)
    await db_session.commit()

    resp = await client.delete(f"/category-rules/{rule.id}")
    assert resp.status_code == 204

    resp2 = await client.get("/category-rules")
    ids = [r["id"] for r in resp2.json()]
    assert str(rule.id) not in ids


@pytest.mark.anyio
async def test_delete_rule_not_found(client: AsyncClient):
    resp = await client.delete(f"/category-rules/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_apply_rules_categorizes_matching_transaction(client: AsyncClient, db_session, instrument, batch):
    cat = await _make_category(db_session, "Streaming")
    await _make_rule(db_session, cat.id, value="netflix")
    tx = await _make_bank_tx(db_session, instrument.id, batch.id, description="NETFLIX SUBSCRIPTION")
    await db_session.commit()

    resp = await client.post("/category-rules/apply")
    assert resp.status_code == 200
    data = resp.json()
    assert data["applied"] >= 1

    # Verify the categorization was persisted
    cat_row = await db_session.scalar(
        select(Categorization).where(Categorization.target_id == tx.id)
    )
    assert cat_row is not None
    assert cat_row.category_id == cat.id
    assert cat_row.source == CategorizationSource.rule


@pytest.mark.anyio
async def test_apply_rules_skips_non_matching(client: AsyncClient, db_session, instrument, batch):
    cat = await _make_category(db_session, "Transport")
    await _make_rule(db_session, cat.id, value="uber")
    tx = await _make_bank_tx(db_session, instrument.id, batch.id, description="AMAZON PRIME")
    await db_session.commit()

    resp = await client.post("/category-rules/apply")
    assert resp.status_code == 200

    cat_row = await db_session.scalar(
        select(Categorization).where(Categorization.target_id == tx.id)
    )
    assert cat_row is None


@pytest.mark.anyio
async def test_apply_rules_does_not_overwrite_manual(client: AsyncClient, db_session, instrument, batch):
    cat_manual = await _make_category(db_session, "Manual Cat")
    cat_rule = await _make_category(db_session, "Rule Cat")
    await _make_rule(db_session, cat_rule.id, value="netflix")
    tx = await _make_bank_tx(db_session, instrument.id, batch.id, description="NETFLIX")

    # Manually categorize first
    manual_cat = Categorization(
        id=uuid.uuid4(),
        target_type="bank_transaction",
        target_id=tx.id,
        category_id=cat_manual.id,
        source=CategorizationSource.manual,
    )
    db_session.add(manual_cat)
    await db_session.commit()

    resp = await client.post("/category-rules/apply")
    assert resp.status_code == 200

    # Should still be manual cat
    cat_row = await db_session.scalar(
        select(Categorization).where(Categorization.target_id == tx.id)
    )
    await db_session.refresh(cat_row)
    assert cat_row.category_id == cat_manual.id
    assert cat_row.source == CategorizationSource.manual


@pytest.mark.anyio
async def test_dry_run_returns_counts_without_persisting(client: AsyncClient, db_session, instrument, batch):
    cat = await _make_category(db_session, "Food Dry")
    await _make_rule(db_session, cat.id, value="ifood")
    tx = await _make_bank_tx(db_session, instrument.id, batch.id, description="IFOOD DELIVERY")
    await db_session.commit()

    resp = await client.post("/category-rules/dry-run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["would_categorize"] >= 1

    # Nothing should be persisted
    cat_row = await db_session.scalar(
        select(Categorization).where(Categorization.target_id == tx.id)
    )
    assert cat_row is None


@pytest.mark.anyio
async def test_priority_first_match_wins(client: AsyncClient, db_session, instrument, batch):
    cat_high = await _make_category(db_session, "High Priority")
    cat_low = await _make_category(db_session, "Low Priority")
    # Both rules match "pix", but high priority (10) wins over low (100)
    await _make_rule(db_session, cat_high.id, value="pix", priority=10)
    await _make_rule(db_session, cat_low.id, value="pix", priority=100)
    tx = await _make_bank_tx(db_session, instrument.id, batch.id, description="PIX ENVIADO")
    await db_session.commit()

    resp = await client.post("/category-rules/apply")
    assert resp.status_code == 200

    cat_row = await db_session.scalar(
        select(Categorization).where(Categorization.target_id == tx.id)
    )
    assert cat_row.category_id == cat_high.id


@pytest.mark.anyio
async def test_disabled_rule_is_skipped(client: AsyncClient, db_session, instrument, batch):
    cat = await _make_category(db_session, "Disabled Cat")
    await _make_rule(db_session, cat.id, value="spotify", enabled=False)
    tx = await _make_bank_tx(db_session, instrument.id, batch.id, description="SPOTIFY")
    await db_session.commit()

    resp = await client.post("/category-rules/apply")
    assert resp.status_code == 200
    assert resp.json()["applied"] == 0

    cat_row = await db_session.scalar(
        select(Categorization).where(Categorization.target_id == tx.id)
    )
    assert cat_row is None


@pytest.mark.anyio
async def test_transaction_response_includes_rule_name(client: AsyncClient, db_session, instrument, batch):
    cat = await _make_category(db_session, "Rule Source Cat")
    await _make_rule(db_session, cat.id, value="amazon")
    await _make_bank_tx(db_session, instrument.id, batch.id, description="AMAZON MARKETPLACE")
    await db_session.commit()

    await client.post("/category-rules/apply")

    resp = await client.get(f"/bank-transactions?instrument_id={instrument.id}")
    assert resp.status_code == 200
    txs = resp.json()
    categorized = [t for t in txs if t["category_id"] is not None]
    assert categorized
    tx = categorized[0]
    assert tx["category_source"] == "rule"
    assert tx["category_rule_name"] is not None
    assert "amazon" in tx["category_rule_name"]
