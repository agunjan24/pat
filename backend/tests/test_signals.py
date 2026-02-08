import numpy as np
import pandas as pd
import pytest

from app.signals.technical import (
    accumulation_distribution,
    adx,
    atr,
    bollinger_bands,
    chaikin_money_flow,
    macd,
    obv,
    put_call_volume_ratio,
    rsi,
    sma,
    stochastic,
)
from app.signals.scoring import (
    score_ad_line,
    score_adx,
    score_bollinger,
    score_cmf,
    score_ma_crossover,
    score_macd,
    score_mean_reversion,
    score_put_call_ratio,
    score_rsi,
    score_stochastic,
    score_trend,
)
from app.signals.composite import WEIGHTS, compute_composite
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
# New Indicator Tests
# ──────────────────────────────────────────────


def _make_ohlcv_series(n=100):
    """Create synthetic OHLCV series for indicator tests."""
    close = pd.Series(np.linspace(100, 130, n) + np.random.randn(n) * 0.5)
    high = close + np.random.uniform(0.5, 2, n)
    low = close - np.random.uniform(0.5, 2, n)
    volume = pd.Series(np.random.randint(100_000, 1_000_000, n).astype(float))
    return high, low, close, volume


def test_adx_range():
    high, low, close, _ = _make_ohlcv_series(100)
    adx_series, plus_di, minus_di = adx(high, low, close, period=14)
    valid = adx_series.dropna()
    assert len(valid) > 0
    assert (valid >= 0).all()
    assert (valid <= 100).all()


def test_adx_shape():
    high, low, close, _ = _make_ohlcv_series(100)
    adx_series, plus_di, minus_di = adx(high, low, close)
    assert len(adx_series) == 100
    assert len(plus_di) == 100
    assert len(minus_di) == 100


def test_stochastic_range():
    high, low, close, _ = _make_ohlcv_series(100)
    pct_k, pct_d = stochastic(high, low, close)
    valid_k = pct_k.dropna()
    valid_d = pct_d.dropna()
    assert len(valid_k) > 0
    assert (valid_k >= 0).all()
    assert (valid_k <= 100).all()
    assert len(valid_d) > 0
    assert (valid_d >= 0).all()
    assert (valid_d <= 100).all()


def test_stochastic_shape():
    high, low, close, _ = _make_ohlcv_series(50)
    pct_k, pct_d = stochastic(high, low, close, k_period=14, d_period=3)
    assert len(pct_k) == 50
    assert len(pct_d) == 50


def test_accumulation_distribution_cumulative():
    high, low, close, volume = _make_ohlcv_series(50)
    ad = accumulation_distribution(high, low, close, volume)
    assert len(ad) == 50
    # Should be cumulative (not all zero)
    assert ad.iloc[-1] != 0


def test_cmf_bounded():
    high, low, close, volume = _make_ohlcv_series(100)
    cmf = chaikin_money_flow(high, low, close, volume, period=20)
    valid = cmf.dropna()
    assert len(valid) > 0
    assert (valid >= -1).all()
    assert (valid <= 1).all()


def test_put_call_volume_ratio_normal():
    calls = pd.DataFrame({"volume": [100, 200, 300]})
    puts = pd.DataFrame({"volume": [200, 300, 400]})
    ratio = put_call_volume_ratio(calls, puts)
    assert ratio == pytest.approx(900 / 600)


def test_put_call_volume_ratio_zero_calls():
    calls = pd.DataFrame({"volume": [0, 0]})
    puts = pd.DataFrame({"volume": [100, 200]})
    ratio = put_call_volume_ratio(calls, puts)
    assert np.isnan(ratio)


def test_put_call_volume_ratio_missing_column():
    calls = pd.DataFrame({"openInterest": [100]})
    puts = pd.DataFrame({"openInterest": [200]})
    ratio = put_call_volume_ratio(calls, puts)
    assert np.isnan(ratio)  # call_vol = 0 → nan


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
# New Scorer Tests
# ──────────────────────────────────────────────


def test_score_adx_range():
    high, low, close, _ = _make_ohlcv_series(100)
    score = score_adx(high, low, close)
    assert -1 <= score <= 1


def test_score_adx_trending_up():
    n = 100
    close = pd.Series(np.linspace(100, 150, n) + np.random.randn(n) * 0.3)
    high = close + np.random.uniform(0.5, 1.5, n)
    low = close - np.random.uniform(0.5, 1.5, n)
    score = score_adx(high, low, close)
    assert -1 <= score <= 1
    # Strong uptrend should generally produce non-negative score
    assert score >= -0.5


def test_score_stochastic_range():
    high, low, close, _ = _make_ohlcv_series(100)
    score = score_stochastic(high, low, close)
    assert -1 <= score <= 1


def test_score_stochastic_oversold():
    # Create a steep down series → stochastic should be oversold → buy signal
    n = 50
    close = pd.Series(np.linspace(150, 80, n))
    high = close + 1
    low = close - 1
    score = score_stochastic(high, low, close)
    assert score >= 0  # oversold → buy


def test_score_ad_line_range():
    high, low, close, volume = _make_ohlcv_series(100)
    score = score_ad_line(high, low, close, volume)
    assert -1 <= score <= 1


def test_score_cmf_range():
    high, low, close, volume = _make_ohlcv_series(100)
    score = score_cmf(high, low, close, volume)
    assert -1 <= score <= 1


def test_score_put_call_ratio_high_fear():
    # High ratio = excessive fear → contrarian buy
    score = score_put_call_ratio(1.5)
    assert score > 0


def test_score_put_call_ratio_complacency():
    # Low ratio = complacency → contrarian sell
    score = score_put_call_ratio(0.2)
    assert score < 0


def test_score_put_call_ratio_neutral():
    # Normal range → neutral
    score = score_put_call_ratio(0.8)
    assert score == 0.0


def test_score_put_call_ratio_none():
    score = score_put_call_ratio(None)
    assert score == 0.0


def test_score_put_call_ratio_nan():
    score = score_put_call_ratio(float("nan"))
    assert score == 0.0


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
    assert len(result.signals) == 12


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


def test_composite_weight_sum():
    total = sum(WEIGHTS.values())
    assert abs(total - 1.0) < 1e-10


def test_composite_new_signals_present():
    df = _make_ohlcv_df()
    result = compute_composite("TEST", df)
    names = {s.name for s in result.signals}
    assert "adx" in names
    assert "stochastic" in names
    assert "ad_line" in names
    assert "cmf" in names
    assert "put_call_ratio" in names


def test_composite_with_put_call_ratio():
    df = _make_ohlcv_df()
    result = compute_composite("TEST", df, put_call_ratio=1.5)
    pc = next(s for s in result.signals if s.name == "put_call_ratio")
    assert pc.score > 0  # high ratio → buy
    assert pc.weight > 0  # weight should not be zeroed


def test_composite_without_put_call_ratio():
    df = _make_ohlcv_df()
    result = compute_composite("TEST", df, put_call_ratio=None)
    pc = next(s for s in result.signals if s.name == "put_call_ratio")
    assert pc.score == 0.0
    assert pc.weight == 0.0
    # Other weights should sum to ~1.0
    other_weights = sum(s.weight for s in result.signals if s.name != "put_call_ratio")
    assert abs(other_weights - 1.0) < 0.01


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
