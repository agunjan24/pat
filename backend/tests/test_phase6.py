"""Tests for Phase 6 features: CSV import, optimizer, alerts, paper trading."""

import numpy as np
import pandas as pd
import pytest
from httpx import AsyncClient

from app.tracker.csv_import import parse_csv
from app.analyzer.optimizer import (
    _annualized_stats,
    compute_efficient_frontier,
    compute_risk_parity,
)


# ── CSV Import Tests ──────────────────────────────────────────────────────────


class TestCSVImport:
    def test_basic_csv_parse(self):
        csv = "symbol,quantity,price\nAAPL,10,150.50\nMSFT,20,300\n"
        result = parse_csv(csv)
        assert len(result.rows) == 2
        assert result.rows[0].symbol == "AAPL"
        assert result.rows[0].quantity == 10
        assert result.rows[0].price == 150.50
        assert result.rows[1].symbol == "MSFT"
        assert result.skipped == 0
        assert len(result.errors) == 0

    def test_csv_with_aliases(self):
        csv = "ticker,qty,cost\nGOOGL,5,2800\n"
        result = parse_csv(csv)
        assert len(result.rows) == 1
        assert result.rows[0].symbol == "GOOGL"
        assert result.rows[0].quantity == 5
        assert result.rows[0].price == 2800

    def test_csv_with_optional_columns(self):
        csv = "symbol,quantity,price,asset_type,option_type,strike,expiration\nSPY,1,400,option,call,420,2025-06-20\n"
        result = parse_csv(csv)
        assert len(result.rows) == 1
        row = result.rows[0]
        assert row.asset_type == "option"
        assert row.option_type == "call"
        assert row.strike == 420.0
        assert row.expiration is not None

    def test_csv_missing_required_columns(self):
        csv = "symbol,foo\nAAPL,bar\n"
        result = parse_csv(csv)
        assert len(result.rows) == 0
        assert len(result.errors) == 1
        assert "Missing required" in result.errors[0]

    def test_csv_empty_symbol_skipped(self):
        csv = "symbol,quantity,price\n,10,100\nAAPL,5,150\n"
        result = parse_csv(csv)
        assert len(result.rows) == 1
        assert result.skipped == 1

    def test_csv_negative_quantity_skipped(self):
        csv = "symbol,quantity,price\nAAPL,-5,150\n"
        result = parse_csv(csv)
        assert len(result.rows) == 0
        assert result.skipped == 1

    def test_csv_zero_price_skipped(self):
        csv = "symbol,quantity,price\nAAPL,5,0\n"
        result = parse_csv(csv)
        assert len(result.rows) == 0
        assert result.skipped == 1

    def test_csv_no_header(self):
        result = parse_csv("")
        assert len(result.rows) == 0
        assert len(result.errors) == 1

    def test_csv_date_parsing(self):
        csv = "symbol,quantity,price,date\nAAPL,10,150,2024-01-15\nMSFT,5,300,01/20/2024\n"
        result = parse_csv(csv)
        assert len(result.rows) == 2
        assert result.rows[0].date is not None
        assert result.rows[0].date.year == 2024
        assert result.rows[0].date.month == 1
        assert result.rows[1].date is not None

    def test_csv_uppercase_symbol(self):
        csv = "symbol,quantity,price\naapl,10,150\n"
        result = parse_csv(csv)
        assert result.rows[0].symbol == "AAPL"

    def test_csv_default_asset_type(self):
        csv = "symbol,quantity,price\nAAPL,10,150\n"
        result = parse_csv(csv)
        assert result.rows[0].asset_type == "stock"


# ── Optimizer Tests ───────────────────────────────────────────────────────────


class TestOptimizer:
    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        dates = pd.date_range("2023-01-01", periods=252)
        data = {
            "AAPL": np.random.normal(0.0005, 0.015, 252),
            "MSFT": np.random.normal(0.0004, 0.013, 252),
            "GOOGL": np.random.normal(0.0006, 0.016, 252),
        }
        return pd.DataFrame(data, index=dates)

    def test_annualized_stats(self):
        weights = np.array([0.5, 0.5])
        mean_returns = np.array([0.001, 0.002])
        cov_matrix = np.array([[0.0004, 0.0001], [0.0001, 0.0009]])
        ret, vol = _annualized_stats(weights, mean_returns, cov_matrix)
        assert ret == pytest.approx(0.378, abs=0.01)
        assert vol > 0

    def test_risk_parity_weights_sum_to_one(self):
        cov = np.array([[0.04, 0.01], [0.01, 0.09]])
        weights = compute_risk_parity(cov)
        assert weights.sum() == pytest.approx(1.0)

    def test_risk_parity_higher_vol_lower_weight(self):
        # Asset 2 has higher vol, so should get lower weight
        cov = np.array([[0.04, 0.0], [0.0, 0.16]])
        weights = compute_risk_parity(cov)
        assert weights[0] > weights[1]

    def test_efficient_frontier_structure(self, sample_returns):
        result = compute_efficient_frontier(
            sample_returns, n_portfolios=500, n_frontier_points=10
        )
        assert result.symbols == ["AAPL", "MSFT", "GOOGL"]
        assert result.max_sharpe is not None
        assert result.min_variance is not None
        assert result.risk_parity is not None
        assert len(result.frontier) > 0

    def test_frontier_weights_sum_to_one(self, sample_returns):
        result = compute_efficient_frontier(
            sample_returns, n_portfolios=500, n_frontier_points=10
        )
        for point in [result.max_sharpe, result.min_variance, result.risk_parity]:
            total = sum(point.weights.values())
            assert total == pytest.approx(1.0, abs=0.01)

    def test_frontier_points_have_positive_vol(self, sample_returns):
        result = compute_efficient_frontier(
            sample_returns, n_portfolios=500, n_frontier_points=10
        )
        for p in result.frontier:
            assert p.volatility > 0

    def test_min_variance_lower_vol_than_max_sharpe(self, sample_returns):
        result = compute_efficient_frontier(
            sample_returns, n_portfolios=2000, n_frontier_points=10
        )
        assert result.min_variance.volatility <= result.max_sharpe.volatility + 0.05


# ── Alert API Tests ───────────────────────────────────────────────────────────


class TestAlerts:
    @pytest.mark.anyio
    async def test_create_alert(self, client: AsyncClient):
        resp = await client.post(
            "/api/alerts",
            json={"symbol": "AAPL", "alert_type": "price_above", "threshold": 200},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert data["alert_type"] == "price_above"
        assert data["threshold"] == 200
        assert data["is_active"] is True
        assert data["is_triggered"] is False

    @pytest.mark.anyio
    async def test_list_alerts(self, client: AsyncClient):
        await client.post(
            "/api/alerts",
            json={"symbol": "AAPL", "alert_type": "price_above", "threshold": 200},
        )
        await client.post(
            "/api/alerts",
            json={"symbol": "MSFT", "alert_type": "price_below", "threshold": 300},
        )
        resp = await client.get("/api/alerts", params={"active_only": False})
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.anyio
    async def test_delete_alert(self, client: AsyncClient):
        create = await client.post(
            "/api/alerts",
            json={"symbol": "AAPL", "alert_type": "price_above", "threshold": 200},
        )
        alert_id = create.json()["id"]
        resp = await client.delete(f"/api/alerts/{alert_id}")
        assert resp.status_code == 204

        listing = await client.get("/api/alerts", params={"active_only": False})
        assert len(listing.json()) == 0

    @pytest.mark.anyio
    async def test_delete_nonexistent_alert(self, client: AsyncClient):
        resp = await client.delete("/api/alerts/9999")
        assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_create_alert_with_message(self, client: AsyncClient):
        resp = await client.post(
            "/api/alerts",
            json={
                "symbol": "TSLA",
                "alert_type": "signal_buy",
                "message": "Strong buy signal detected",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["message"] == "Strong buy signal detected"


# ── Paper Trading API Tests ───────────────────────────────────────────────────


class TestPaperTrading:
    @pytest.mark.anyio
    async def test_summary_creates_default_account(self, client: AsyncClient):
        resp = await client.get("/api/paper/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["account"]["initial_cash"] == 100_000
        assert data["account"]["current_cash"] == 100_000
        assert data["total_pnl"] == 0
        assert data["win_rate"] == 0

    @pytest.mark.anyio
    async def test_open_trade(self, client: AsyncClient):
        resp = await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "buy", "quantity": 10, "entry_price": 150},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["symbol"] == "AAPL"
        assert data["direction"] == "buy"
        assert data["status"] == "open"
        assert data["quantity"] == 10
        assert data["entry_price"] == 150

    @pytest.mark.anyio
    async def test_open_trade_deducts_cash(self, client: AsyncClient):
        await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "buy", "quantity": 10, "entry_price": 150},
        )
        summary = await client.get("/api/paper/summary")
        assert summary.json()["account"]["current_cash"] == pytest.approx(100_000 - 1500)

    @pytest.mark.anyio
    async def test_close_trade_pnl(self, client: AsyncClient):
        # Open a buy trade
        open_resp = await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "buy", "quantity": 10, "entry_price": 150},
        )
        trade_id = open_resp.json()["id"]

        # Close it at higher price
        close_resp = await client.post(
            f"/api/paper/trades/{trade_id}/close",
            json={"exit_price": 160},
        )
        assert close_resp.status_code == 200
        data = close_resp.json()
        assert data["status"] == "closed"
        assert data["pnl"] == pytest.approx(100)  # (160-150)*10
        assert data["pnl_pct"] == pytest.approx(6.67, abs=0.01)

    @pytest.mark.anyio
    async def test_close_trade_returns_cash(self, client: AsyncClient):
        open_resp = await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "buy", "quantity": 10, "entry_price": 150},
        )
        trade_id = open_resp.json()["id"]
        await client.post(
            f"/api/paper/trades/{trade_id}/close",
            json={"exit_price": 160},
        )
        summary = await client.get("/api/paper/summary")
        # Started 100k, bought 1500, sold 1600
        assert summary.json()["account"]["current_cash"] == pytest.approx(100_000 + 100)

    @pytest.mark.anyio
    async def test_close_already_closed_trade(self, client: AsyncClient):
        open_resp = await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "buy", "quantity": 10, "entry_price": 150},
        )
        trade_id = open_resp.json()["id"]
        await client.post(f"/api/paper/trades/{trade_id}/close", json={"exit_price": 160})
        resp = await client.post(f"/api/paper/trades/{trade_id}/close", json={"exit_price": 170})
        assert resp.status_code == 409

    @pytest.mark.anyio
    async def test_insufficient_cash(self, client: AsyncClient):
        resp = await client.post(
            "/api/paper/trades",
            json={
                "symbol": "BRK.A",
                "direction": "buy",
                "quantity": 1000,
                "entry_price": 500_000,
            },
        )
        assert resp.status_code == 400
        assert "Insufficient" in resp.json()["detail"]

    @pytest.mark.anyio
    async def test_invalid_direction(self, client: AsyncClient):
        resp = await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "hold", "quantity": 10, "entry_price": 150},
        )
        assert resp.status_code == 400

    @pytest.mark.anyio
    async def test_win_rate(self, client: AsyncClient):
        # Open and close two trades: one winner, one loser
        r1 = await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "buy", "quantity": 1, "entry_price": 100},
        )
        r2 = await client.post(
            "/api/paper/trades",
            json={"symbol": "MSFT", "direction": "buy", "quantity": 1, "entry_price": 200},
        )
        await client.post(f"/api/paper/trades/{r1.json()['id']}/close", json={"exit_price": 120})
        await client.post(f"/api/paper/trades/{r2.json()['id']}/close", json={"exit_price": 180})

        summary = await client.get("/api/paper/summary")
        data = summary.json()
        assert data["total_trades"] == 2
        assert data["win_rate"] == 50.0

    @pytest.mark.anyio
    async def test_list_trades_filter(self, client: AsyncClient):
        r1 = await client.post(
            "/api/paper/trades",
            json={"symbol": "AAPL", "direction": "buy", "quantity": 1, "entry_price": 100},
        )
        await client.post(
            "/api/paper/trades",
            json={"symbol": "MSFT", "direction": "buy", "quantity": 1, "entry_price": 200},
        )
        await client.post(f"/api/paper/trades/{r1.json()['id']}/close", json={"exit_price": 120})

        open_resp = await client.get("/api/paper/trades", params={"status": "open"})
        assert len(open_resp.json()) == 1
        assert open_resp.json()[0]["symbol"] == "MSFT"

        closed_resp = await client.get("/api/paper/trades", params={"status": "closed"})
        assert len(closed_resp.json()) == 1
        assert closed_resp.json()[0]["symbol"] == "AAPL"
