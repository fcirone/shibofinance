"""Tests for investment accounts, assets, positions, and portfolio summary."""
from datetime import date

import pytest


# ---------------------------------------------------------------------------
# Investment Accounts
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_investment_accounts_empty(client):
    resp = await client.get("/investment-accounts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_investment_account(client):
    resp = await client.post(
        "/investment-accounts",
        json={"name": "XP Investimentos", "institution_name": "XP", "currency": "BRL"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "XP Investimentos"
    assert data["institution_name"] == "XP"
    assert data["currency"] == "BRL"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_investment_account_minimal(client):
    resp = await client.post("/investment-accounts", json={"name": "My Portfolio"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["institution_name"] is None
    assert data["currency"] == "BRL"


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_assets_empty(client):
    resp = await client.get("/assets")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_asset_stock(client):
    resp = await client.post(
        "/assets",
        json={"symbol": "PETR4", "name": "Petrobras PN", "asset_class": "stock", "currency": "BRL"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["symbol"] == "PETR4"
    assert data["name"] == "Petrobras PN"
    assert data["asset_class"] == "stock"


@pytest.mark.asyncio
async def test_create_asset_crypto(client):
    resp = await client.post(
        "/assets",
        json={"symbol": "BTC", "name": "Bitcoin", "asset_class": "crypto", "currency": "USD"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["asset_class"] == "crypto"
    assert data["currency"] == "USD"


@pytest.mark.asyncio
async def test_create_asset_no_symbol(client):
    resp = await client.post(
        "/assets",
        json={"name": "Real Estate Fund", "asset_class": "real_estate", "currency": "BRL"},
    )
    assert resp.status_code == 201
    assert resp.json()["symbol"] is None


# ---------------------------------------------------------------------------
# Asset Positions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_positions_empty(client):
    resp = await client.get("/asset-positions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_create_and_list_position(client):
    # create account and asset
    acc = (await client.post("/investment-accounts", json={"name": "Pos Test Account"})).json()
    asset = (await client.post("/assets", json={"name": "VALE3", "asset_class": "stock", "symbol": "VALE3", "currency": "BRL"})).json()

    resp = await client.post(
        "/asset-positions",
        json={
            "investment_account_id": acc["id"],
            "asset_id": asset["id"],
            "quantity": 100.0,
            "average_cost_minor": 7500,
            "current_value_minor": 8200,
            "as_of_date": "2026-03-13",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["quantity"] == 100.0
    assert data["asset_name"] == "VALE3"
    assert data["asset_class"] == "stock"
    assert data["current_value_minor"] == 8200

    # list all positions — there may be pre-existing ones, so check >= 1
    list_resp = await client.get("/asset-positions")
    assert len(list_resp.json()) >= 1

    # filter by account — should see exactly our position
    filtered = await client.get(f"/asset-positions?investment_account_id={acc['id']}")
    assert len(filtered.json()) == 1


@pytest.mark.asyncio
async def test_create_position_account_not_found(client):
    asset = (await client.post("/assets", json={"name": "XPTO", "asset_class": "etf", "currency": "BRL"})).json()
    resp = await client.post(
        "/asset-positions",
        json={
            "investment_account_id": "00000000-0000-0000-0000-000000000000",
            "asset_id": asset["id"],
            "quantity": 10,
            "as_of_date": "2026-03-13",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_position(client):
    acc = (await client.post("/investment-accounts", json={"name": "Update Test Account"})).json()
    asset = (await client.post("/assets", json={"name": "BOVA11", "asset_class": "etf", "currency": "BRL"})).json()
    pos = (await client.post(
        "/asset-positions",
        json={
            "investment_account_id": acc["id"],
            "asset_id": asset["id"],
            "quantity": 50.0,
            "current_value_minor": 5000,
            "as_of_date": "2026-03-01",
        },
    )).json()

    resp = await client.patch(
        f"/asset-positions/{pos['id']}",
        json={"current_value_minor": 5500, "quantity": 55.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_value_minor"] == 5500
    assert data["quantity"] == 55.0


@pytest.mark.asyncio
async def test_update_position_not_found(client):
    resp = await client.patch(
        "/asset-positions/00000000-0000-0000-0000-000000000000",
        json={"current_value_minor": 999},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Portfolio Summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_portfolio_summary_empty(client):
    resp = await client.get("/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value_minor" in data
    assert isinstance(data["accounts"], list)
    assert isinstance(data["allocation"], list)


@pytest.mark.asyncio
async def test_portfolio_summary_with_positions(client):
    acc = (await client.post("/investment-accounts", json={"name": "Summary Account"})).json()
    stock = (await client.post("/assets", json={"name": "STOCK A", "asset_class": "stock", "currency": "BRL"})).json()
    bond = (await client.post("/assets", json={"name": "BOND A", "asset_class": "bond", "currency": "BRL"})).json()

    await client.post("/asset-positions", json={
        "investment_account_id": acc["id"], "asset_id": stock["id"],
        "quantity": 1, "current_value_minor": 10000, "as_of_date": "2026-03-13",
    })
    await client.post("/asset-positions", json={
        "investment_account_id": acc["id"], "asset_id": bond["id"],
        "quantity": 1, "current_value_minor": 5000, "as_of_date": "2026-03-13",
    })

    resp = await client.get("/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_value_minor"] >= 15000
    # our account should be in the list
    our_account = next((a for a in data["accounts"] if a["account_id"] == acc["id"]), None)
    assert our_account is not None
    assert our_account["total_value_minor"] == 15000
    # allocation should include both stock and bond classes
    classes = [a["asset_class"] for a in data["allocation"]]
    assert "stock" in classes
    assert "bond" in classes
    # percentages should sum to 100
    total_pct = sum(a["pct"] for a in data["allocation"])
    assert abs(total_pct - 100.0) < 0.1


# ---------------------------------------------------------------------------
# Portfolio Snapshot & History
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_portfolio_history_empty(client):
    resp = await client.get("/portfolio/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_record_snapshot_endpoint(client):
    # create account + asset + position (position create auto-snapshots)
    acc = (await client.post("/investment-accounts", json={"name": "Snap Account"})).json()
    asset = (await client.post("/assets", json={"name": "SNAP ASSET", "asset_class": "cash", "currency": "BRL"})).json()
    await client.post("/asset-positions", json={
        "investment_account_id": acc["id"],
        "asset_id": asset["id"],
        "quantity": 1,
        "current_value_minor": 20000,
        "as_of_date": "2026-03-13",
    })

    # manual snapshot endpoint (today — includes any pre-existing positions too)
    resp = await client.post("/portfolio/snapshot")
    assert resp.status_code == 201
    data = resp.json()
    assert data["total_value_minor"] >= 20000
    assert data["currency"] == "BRL"
    assert "snapshot_date" in data
    assert data["item_count"] >= 1


@pytest.mark.asyncio
async def test_portfolio_history_after_snapshot(client):
    acc = (await client.post("/investment-accounts", json={"name": "History Account"})).json()
    asset = (await client.post("/assets", json={"name": "HIST ASSET", "asset_class": "bond", "currency": "BRL"})).json()
    await client.post("/asset-positions", json={
        "investment_account_id": acc["id"],
        "asset_id": asset["id"],
        "quantity": 1,
        "current_value_minor": 30000,
        "as_of_date": "2026-03-13",
    })

    # history should have at least one point
    resp = await client.get("/portfolio/history")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) >= 1
    assert points[-1]["total_value_minor"] >= 30000


@pytest.mark.asyncio
async def test_asset_history(client):
    acc = (await client.post("/investment-accounts", json={"name": "Asset History Account"})).json()
    asset = (await client.post("/assets", json={"name": "AH ASSET", "asset_class": "etf", "currency": "BRL", "symbol": "AHFUND"})).json()
    await client.post("/asset-positions", json={
        "investment_account_id": acc["id"],
        "asset_id": asset["id"],
        "quantity": 10,
        "current_value_minor": 12000,
        "as_of_date": "2026-03-13",
    })

    resp = await client.get(f"/portfolio/history/assets?asset_id={asset['id']}")
    assert resp.status_code == 200
    points = resp.json()
    assert len(points) >= 1
    pt = points[-1]
    assert pt["asset_id"] == asset["id"]
    assert pt["asset_name"] == "AH ASSET"
    assert pt["asset_symbol"] == "AHFUND"
    assert pt["current_value_minor"] == 12000
    assert pt["quantity"] == 10.0
