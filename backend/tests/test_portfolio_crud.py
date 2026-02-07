import pytest
from httpx import AsyncClient


@pytest.fixture
async def stock_asset(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/portfolio/assets",
        json={"symbol": "AAPL", "name": "Apple Inc.", "asset_type": "stock"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture
async def option_asset(client: AsyncClient) -> dict:
    resp = await client.post(
        "/api/portfolio/assets",
        json={
            "symbol": "AAPL",
            "asset_type": "option",
            "strike": 200.0,
            "expiration": "2026-06-19T00:00:00",
            "option_type": "call",
        },
    )
    assert resp.status_code == 201
    return resp.json()


# ──────────────────────────────────────────────
# Asset CRUD
# ──────────────────────────────────────────────


async def test_create_and_list_assets(client: AsyncClient, stock_asset: dict):
    resp = await client.get("/api/portfolio/assets")
    assert resp.status_code == 200
    assets = resp.json()
    assert len(assets) == 1
    assert assets[0]["symbol"] == "AAPL"


async def test_get_asset(client: AsyncClient, stock_asset: dict):
    resp = await client.get(f"/api/portfolio/assets/{stock_asset['id']}")
    assert resp.status_code == 200
    assert resp.json()["symbol"] == "AAPL"


async def test_get_asset_not_found(client: AsyncClient):
    resp = await client.get("/api/portfolio/assets/999")
    assert resp.status_code == 404


async def test_delete_asset(client: AsyncClient, stock_asset: dict):
    resp = await client.delete(f"/api/portfolio/assets/{stock_asset['id']}")
    assert resp.status_code == 204

    resp = await client.get("/api/portfolio/assets")
    assert len(resp.json()) == 0


async def test_delete_asset_with_open_position(client: AsyncClient, stock_asset: dict):
    await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 10, "price": 150.0},
    )
    resp = await client.delete(f"/api/portfolio/assets/{stock_asset['id']}")
    assert resp.status_code == 409


# ──────────────────────────────────────────────
# Position lifecycle
# ──────────────────────────────────────────────


async def test_open_position(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 10, "price": 150.0},
    )
    assert resp.status_code == 201
    pos = resp.json()
    assert pos["quantity"] == 10
    assert pos["avg_cost"] == 150.0
    assert pos["asset"]["symbol"] == "AAPL"
    assert len(pos["transactions"]) == 1
    assert pos["transactions"][0]["transaction_type"] == "buy"


async def test_open_position_invalid_asset(client: AsyncClient):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": 999, "quantity": 10, "price": 150.0},
    )
    assert resp.status_code == 404


async def test_list_positions_excludes_closed(client: AsyncClient, stock_asset: dict):
    # Open and fully sell
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 10, "price": 150.0},
    )
    pos_id = resp.json()["id"]
    await client.post(
        f"/api/portfolio/positions/{pos_id}/transactions",
        json={"transaction_type": "sell", "quantity": 10, "price": 160.0},
    )

    resp = await client.get("/api/portfolio/positions")
    assert len(resp.json()) == 0

    resp = await client.get("/api/portfolio/positions", params={"include_closed": True})
    assert len(resp.json()) == 1


async def test_get_position_detail(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 10, "price": 150.0},
    )
    pos_id = resp.json()["id"]

    resp = await client.get(f"/api/portfolio/positions/{pos_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["quantity"] == 10
    assert len(detail["transactions"]) == 1


async def test_delete_closed_position(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 5, "price": 100.0},
    )
    pos_id = resp.json()["id"]

    # Sell all to close
    await client.post(
        f"/api/portfolio/positions/{pos_id}/transactions",
        json={"transaction_type": "sell", "quantity": 5, "price": 110.0},
    )

    resp = await client.delete(f"/api/portfolio/positions/{pos_id}")
    assert resp.status_code == 204


async def test_delete_open_position_blocked(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 5, "price": 100.0},
    )
    pos_id = resp.json()["id"]

    resp = await client.delete(f"/api/portfolio/positions/{pos_id}")
    assert resp.status_code == 409


# ──────────────────────────────────────────────
# Transaction logic
# ──────────────────────────────────────────────


async def test_buy_updates_avg_cost(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 10, "price": 100.0},
    )
    pos_id = resp.json()["id"]

    # Buy 10 more at $200 → avg_cost = (10*100 + 10*200) / 20 = 150
    await client.post(
        f"/api/portfolio/positions/{pos_id}/transactions",
        json={"transaction_type": "buy", "quantity": 10, "price": 200.0},
    )

    resp = await client.get(f"/api/portfolio/positions/{pos_id}")
    pos = resp.json()
    assert pos["quantity"] == 20
    assert abs(pos["avg_cost"] - 150.0) < 0.01


async def test_sell_reduces_quantity(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 20, "price": 100.0},
    )
    pos_id = resp.json()["id"]

    await client.post(
        f"/api/portfolio/positions/{pos_id}/transactions",
        json={"transaction_type": "sell", "quantity": 5, "price": 120.0},
    )

    resp = await client.get(f"/api/portfolio/positions/{pos_id}")
    pos = resp.json()
    assert pos["quantity"] == 15
    assert pos["avg_cost"] == 100.0  # avg_cost unchanged on sell


async def test_sell_exceeding_quantity_rejected(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 5, "price": 100.0},
    )
    pos_id = resp.json()["id"]

    resp = await client.post(
        f"/api/portfolio/positions/{pos_id}/transactions",
        json={"transaction_type": "sell", "quantity": 10, "price": 120.0},
    )
    assert resp.status_code == 400


async def test_list_transactions(client: AsyncClient, stock_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": stock_asset["id"], "quantity": 10, "price": 100.0},
    )
    pos_id = resp.json()["id"]

    await client.post(
        f"/api/portfolio/positions/{pos_id}/transactions",
        json={"transaction_type": "buy", "quantity": 5, "price": 110.0},
    )
    await client.post(
        f"/api/portfolio/positions/{pos_id}/transactions",
        json={"transaction_type": "sell", "quantity": 3, "price": 120.0},
    )

    resp = await client.get(f"/api/portfolio/positions/{pos_id}/transactions")
    assert resp.status_code == 200
    txns = resp.json()
    assert len(txns) == 3  # initial buy + buy + sell


async def test_option_position(client: AsyncClient, option_asset: dict):
    resp = await client.post(
        "/api/portfolio/positions",
        json={"asset_id": option_asset["id"], "quantity": 2, "price": 5.50},
    )
    assert resp.status_code == 201
    pos = resp.json()
    assert pos["asset"]["asset_type"] == "option"
    assert pos["asset"]["strike"] == 200.0
    assert pos["asset"]["option_type"] == "call"
