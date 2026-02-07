import math
from datetime import date

import pandas as pd
import pytest

from app.analyzer.greeks import (
    bs_price,
    compute_greeks,
    delta,
    gamma,
    implied_volatility,
    rho,
    theta,
    vega,
)
from app.analyzer.options import (
    compute_iv_metrics,
    compute_skew,
    compute_term_structure,
)
from app.analyzer.leaps import (
    analyze_leaps_chain,
    find_leaps_expirations,
    _roll_recommendation,
)


# ──────────────────────────────────────────────
# Black-Scholes & Greeks
# ──────────────────────────────────────────────


def test_bs_call_price():
    # Known: S=100, K=100, T=1, r=5%, sigma=20% → ~10.45
    price = bs_price(100, 100, 1.0, 0.05, 0.20, "call")
    assert 10.0 < price < 11.0


def test_bs_put_price():
    price = bs_price(100, 100, 1.0, 0.05, 0.20, "put")
    assert 5.0 < price < 7.0


def test_put_call_parity():
    s, k, t, r, sigma = 100, 100, 1.0, 0.05, 0.30
    call = bs_price(s, k, t, r, sigma, "call")
    put = bs_price(s, k, t, r, sigma, "put")
    # Put-call parity: C - P = S - K*e^(-rT)
    expected = s - k * math.exp(-r * t)
    assert abs((call - put) - expected) < 0.01


def test_call_delta_range():
    d = delta(100, 100, 1.0, 0.05, 0.30, "call")
    assert 0 < d < 1


def test_put_delta_range():
    d = delta(100, 100, 1.0, 0.05, 0.30, "put")
    assert -1 < d < 0


def test_gamma_positive():
    g = gamma(100, 100, 1.0, 0.05, 0.30)
    assert g > 0


def test_call_theta_negative():
    # Options lose value over time (theta < 0 for long positions)
    t_val = theta(100, 100, 1.0, 0.05, 0.30, "call")
    assert t_val < 0


def test_vega_positive():
    v = vega(100, 100, 1.0, 0.05, 0.30)
    assert v > 0


def test_compute_greeks_structure():
    result = compute_greeks(100, 100, 1.0, 0.05, 0.30, "call")
    assert result.price > 0
    assert 0 < result.delta < 1
    assert result.gamma > 0
    assert result.theta < 0
    assert result.vega > 0


def test_deep_itm_call_delta_near_one():
    d = delta(200, 100, 1.0, 0.05, 0.30, "call")
    assert d > 0.95


def test_deep_otm_call_delta_near_zero():
    d = delta(50, 100, 1.0, 0.05, 0.30, "call")
    assert d < 0.05


def test_expired_call_itm():
    price = bs_price(110, 100, 0, 0.05, 0.30, "call")
    assert abs(price - 10) < 0.01


def test_expired_put_otm():
    price = bs_price(110, 100, 0, 0.05, 0.30, "put")
    assert price == 0


def test_implied_volatility_roundtrip():
    s, k, t, r, sigma = 100, 105, 0.5, 0.04, 0.25
    market = bs_price(s, k, t, r, sigma, "call")
    iv = implied_volatility(market, s, k, t, r, "call")
    assert iv is not None
    assert abs(iv - sigma) < 0.005


# ──────────────────────────────────────────────
# IV Metrics
# ──────────────────────────────────────────────


def test_iv_rank_midpoint():
    history = pd.Series([0.15, 0.20, 0.25, 0.30, 0.35])
    metrics = compute_iv_metrics(history, 0.25)
    assert metrics.iv_rank == 50.0
    assert metrics.iv_low == 0.15
    assert metrics.iv_high == 0.35


def test_iv_rank_at_high():
    history = pd.Series([0.15, 0.20, 0.25, 0.30])
    metrics = compute_iv_metrics(history, 0.30)
    assert metrics.iv_rank == 100.0


def test_iv_percentile():
    history = pd.Series([0.10, 0.15, 0.20, 0.25, 0.30])
    metrics = compute_iv_metrics(history, 0.22)
    # 3 out of 5 values are below 0.22
    assert metrics.iv_percentile == 60.0


# ──────────────────────────────────────────────
# Skew
# ──────────────────────────────────────────────


def test_skew_computation():
    calls = pd.DataFrame({
        "strike": [90, 95, 100, 105, 110],
        "impliedVolatility": [0.35, 0.30, 0.25, 0.22, 0.20],
    })
    puts = pd.DataFrame({
        "strike": [90, 95, 100, 105, 110],
        "impliedVolatility": [0.40, 0.35, 0.25, 0.22, 0.19],
    })
    skew = compute_skew(calls, puts, spot_price=100)
    assert skew.skew_ratio > 1.0  # puts have higher IV → put skew
    assert len(skew.skew_points) > 0


# ──────────────────────────────────────────────
# Term Structure
# ──────────────────────────────────────────────


def test_term_structure():
    chains = {
        "2027-03-01": {
            "calls": pd.DataFrame({"strike": [100, 105], "impliedVolatility": [0.25, 0.27]}),
            "puts": pd.DataFrame({"strike": [100, 105], "impliedVolatility": [0.26, 0.28]}),
        },
        "2027-06-01": {
            "calls": pd.DataFrame({"strike": [100, 105], "impliedVolatility": [0.28, 0.30]}),
            "puts": pd.DataFrame({"strike": [100, 105], "impliedVolatility": [0.29, 0.31]}),
        },
    }
    ts = compute_term_structure(chains, spot_price=100, today=date(2026, 2, 6))
    assert len(ts) == 2
    assert ts[0].days_to_expiry < ts[1].days_to_expiry
    assert ts[0].atm_iv > 0


# ──────────────────────────────────────────────
# LEAPS
# ──────────────────────────────────────────────


def test_find_leaps_expirations():
    exps = ["2026-03-01", "2026-06-01", "2027-03-01", "2027-12-01"]
    result = find_leaps_expirations(exps, today=date(2026, 2, 6))
    assert "2027-03-01" in result
    assert "2027-12-01" in result
    assert "2026-03-01" not in result


def test_roll_recommendation():
    assert _roll_recommendation(400, 0.20) == "hold"
    assert _roll_recommendation(150, 0.10) == "monitor"
    assert _roll_recommendation(80, 0.10) == "roll_now"


def test_analyze_leaps_chain_filters_short_dated():
    calls = pd.DataFrame({
        "strike": [90, 100, 110],
        "lastPrice": [15, 8, 3],
        "impliedVolatility": [0.30, 0.28, 0.32],
    })
    puts = pd.DataFrame({
        "strike": [90, 100, 110],
        "lastPrice": [2, 7, 14],
        "impliedVolatility": [0.30, 0.28, 0.32],
    })
    # Short-dated expiry → should return empty
    result = analyze_leaps_chain(
        calls, puts, "2026-06-01", spot_price=100, today=date(2026, 2, 6)
    )
    assert len(result) == 0


def test_analyze_leaps_chain_returns_candidates():
    calls = pd.DataFrame({
        "strike": [70, 80, 90, 100, 110],
        "lastPrice": [35, 26, 18, 12, 7],
        "impliedVolatility": [0.25, 0.26, 0.28, 0.30, 0.33],
    })
    puts = pd.DataFrame({
        "strike": [70, 80, 90, 100, 110],
        "lastPrice": [1, 2, 5, 10, 18],
        "impliedVolatility": [0.25, 0.26, 0.28, 0.30, 0.33],
    })
    result = analyze_leaps_chain(
        calls, puts, "2027-06-01", spot_price=100, today=date(2026, 2, 6)
    )
    assert len(result) > 0
    # All candidates should have high absolute delta
    for c in result:
        assert abs(c.delta) >= 0.50
    # Should be sorted by theta efficiency
    thetas = [c.theta_efficiency.theta_per_delta for c in result]
    assert thetas == sorted(thetas)
