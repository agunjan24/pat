import numpy as np
import pandas as pd
import pytest

from app.signals.technical import atr, bollinger_bands, macd, obv, rsi, sma
from app.signals.scoring import (
    score_bollinger,
    score_ma_crossover,
    score_macd,
    score_mean_reversion,
    score_rsi,
    score_trend,
)
from app.signals.composite import compute_composite
from app.signals.risk import (
    atr_stop_loss,
    kelly_fraction,
    position_size_from_risk,
    risk_reward_ratio,
)


# ──────────────────────────────────────────────
# Technical Indicators
# ──────────────────────────────────────────────


def test_macd_shape():
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    macd_line, signal_line, histogram = macd(prices)
    assert len(macd_line) == 100
    assert len(signal_line) == 100
    assert len(histogram) == 100


def test_atr_positive():
    n = 50
    high = pd.Series(np.random.uniform(101, 105, n))
    low = pd.Series(np.random.uniform(95, 99, n))
    close = pd.Series(np.random.uniform(98, 103, n))
    result = atr(high, low, close, period=14)
    # ATR should be positive once calculated
    valid = result.dropna()
    assert len(valid) > 0
    assert (valid > 0).all()


def test_rsi_bounds():
    prices = pd.Series(np.random.randn(100).cumsum() + 100)
    r = rsi(prices, period=14)
    valid = r.dropna()
    assert (valid >= 0).all()
    assert (valid <= 100).all()


def test_obv_cumulative():
    close = pd.Series([100, 102, 101, 103, 104])
    volume = pd.Series([1000, 1200, 800, 1500, 1100])
    result = obv(close, volume)
    assert len(result) == 5


# ──────────────────────────────────────────────
# Signal Scoring
# ──────────────────────────────────────────────


def _make_trending_up(n=250):
    """Create an upward trending price series."""
    return pd.Series(np.linspace(100, 150, n) + np.random.randn(n) * 0.5)


def _make_trending_down(n=250):
    """Create a downward trending price series."""
    return pd.Series(np.linspace(150, 100, n) + np.random.randn(n) * 0.5)


def test_score_ma_crossover_range():
    prices = _make_trending_up()
    score = score_ma_crossover(prices)
    assert -1 <= score <= 1


def test_score_rsi_oversold():
    # Steep drop should produce oversold RSI → positive (buy) score
    prices = pd.Series(np.linspace(150, 80, 100))
    score = score_rsi(prices)
    assert score >= 0  # oversold → buy signal


def test_score_rsi_overbought():
    # Steep rise should produce overbought RSI → negative (sell) score
    prices = pd.Series(np.linspace(80, 150, 100))
    score = score_rsi(prices)
    assert score <= 0  # overbought → sell signal


def test_score_macd_range():
    prices = _make_trending_up()
    score = score_macd(prices)
    assert -1 <= score <= 1


def test_score_bollinger_range():
    prices = _make_trending_up()
    score = score_bollinger(prices)
    assert -1 <= score <= 1


def test_score_mean_reversion_range():
    prices = _make_trending_up()
    score = score_mean_reversion(prices)
    assert -1 <= score <= 1


def test_score_trend_bullish():
    prices = _make_trending_up()
    score = score_trend(prices)
    assert score > 0  # uptrend → positive


def test_score_trend_bearish():
    prices = _make_trending_down()
    score = score_trend(prices)
    assert score < 0  # downtrend → negative


# ──────────────────────────────────────────────
# Composite
# ──────────────────────────────────────────────


def _make_ohlcv_df(n=250, trend="up"):
    base = np.linspace(100, 150, n) if trend == "up" else np.linspace(150, 100, n)
    noise = np.random.randn(n) * 0.5
    close = base + noise
    return pd.DataFrame({
        "Open": close - np.random.uniform(0, 1, n),
        "High": close + np.random.uniform(0, 2, n),
        "Low": close - np.random.uniform(0, 2, n),
        "Close": close,
        "Volume": np.random.randint(100_000, 1_000_000, n),
    })


def test_composite_returns_valid_structure():
    df = _make_ohlcv_df()
    result = compute_composite("TEST", df)
    assert result.symbol == "TEST"
    assert result.direction in ("buy", "sell", "hold")
    assert result.conviction in ("low", "medium", "high")
    assert -1 <= result.composite_score <= 1
    assert 0 <= result.confidence <= 100
    assert len(result.signals) == 7


def test_composite_uptrend_leans_bullish():
    df = _make_ohlcv_df(trend="up")
    result = compute_composite("BULL", df)
    # Strong uptrend should not produce a sell signal
    assert result.direction != "sell"


def test_composite_downtrend_leans_bearish():
    df = _make_ohlcv_df(trend="down")
    result = compute_composite("BEAR", df)
    # Strong downtrend should not produce a buy signal
    assert result.direction != "buy"


# ──────────────────────────────────────────────
# Risk
# ──────────────────────────────────────────────


def test_atr_stop_loss_buy():
    high = pd.Series([105, 106, 104, 107, 108])
    low = pd.Series([100, 101, 99, 102, 103])
    close = pd.Series([103, 104, 101, 105, 106])
    stop = atr_stop_loss(high, low, close, "buy", multiplier=2.0, period=3)
    if stop is not None:
        assert stop < close.iloc[-1]


def test_atr_stop_loss_sell():
    high = pd.Series([105, 106, 104, 107, 108])
    low = pd.Series([100, 101, 99, 102, 103])
    close = pd.Series([103, 104, 101, 105, 106])
    stop = atr_stop_loss(high, low, close, "sell", multiplier=2.0, period=3)
    if stop is not None:
        assert stop > close.iloc[-1]


def test_kelly_fraction_positive_edge():
    # 60% win rate, avg win = $2, avg loss = $1 → positive Kelly
    k = kelly_fraction(0.6, 2.0, 1.0)
    assert k > 0
    assert k <= 0.25  # capped


def test_kelly_fraction_no_edge():
    # 40% win rate, avg win = $1, avg loss = $1 → negative Kelly → clamped to 0
    k = kelly_fraction(0.4, 1.0, 1.0)
    assert k == 0.0


def test_position_size_from_risk():
    shares = position_size_from_risk(
        portfolio_value=100_000,
        entry_price=100,
        stop_price=95,
        risk_pct=0.02,
    )
    # Risk $2000, $5/share risk → 400 shares
    assert abs(shares - 400.0) < 0.01


def test_risk_reward_ratio():
    rr = risk_reward_ratio(entry=100, stop=95, target=115)
    assert rr == 3.0  # $5 risk, $15 reward


def test_risk_reward_zero_risk():
    rr = risk_reward_ratio(entry=100, stop=100, target=110)
    assert rr is None
