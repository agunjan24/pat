"""
Individual signal evaluators.

Each evaluator takes a DataFrame (OHLCV) and returns a normalized score
in the range [-1, +1]:
  -1 = strong sell
   0 = neutral
  +1 = strong buy
"""

import pandas as pd

from app.signals.technical import (
    accumulation_distribution,
    adx,
    atr,
    bollinger_pct_b,
    chaikin_money_flow,
    ema,
    macd,
    obv,
    rsi,
    sma,
    stochastic,
)


def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ──────────────────────────────────────────────
# Momentum Signals
# ──────────────────────────────────────────────


def score_ma_crossover(close: pd.Series, fast: int = 20, slow: int = 50) -> float:
    """SMA crossover: bullish when fast > slow, scaled by gap magnitude."""
    fast_ma = sma(close, fast)
    slow_ma = sma(close, slow)
    if fast_ma.isna().iloc[-1] or slow_ma.isna().iloc[-1]:
        return 0.0
    gap_pct = (fast_ma.iloc[-1] - slow_ma.iloc[-1]) / slow_ma.iloc[-1]
    # Scale: 2% gap → score ±1
    return _clamp(gap_pct / 0.02)


def score_rsi(close: pd.Series, period: int = 14) -> float:
    """RSI: oversold (<30) → buy, overbought (>70) → sell."""
    r = rsi(close, period)
    if r.isna().iloc[-1]:
        return 0.0
    value = r.iloc[-1]
    if value <= 30:
        return _clamp((30 - value) / 20)  # 30→0, 10→1
    elif value >= 70:
        return _clamp(-(value - 70) / 20)  # 70→0, 90→-1
    return 0.0


def score_macd(close: pd.Series) -> float:
    """MACD histogram direction and magnitude."""
    macd_line, signal_line, histogram = macd(close)
    if histogram.isna().iloc[-1]:
        return 0.0
    # Normalize histogram by recent ATR-like price range
    recent_range = close.iloc[-26:].std()
    if recent_range == 0:
        return 0.0
    normalized = histogram.iloc[-1] / recent_range
    return _clamp(normalized)


# ──────────────────────────────────────────────
# Mean Reversion Signals
# ──────────────────────────────────────────────


def score_bollinger(close: pd.Series, window: int = 20) -> float:
    """Bollinger %B: near lower band → buy, near upper → sell."""
    pct_b = bollinger_pct_b(close, window)
    if pct_b.isna().iloc[-1]:
        return 0.0
    value = pct_b.iloc[-1]
    # 0.0 → +1 (buy at lower band), 1.0 → -1 (sell at upper band), 0.5 → 0
    return _clamp(-(value - 0.5) * 2)


def score_mean_reversion(close: pd.Series, window: int = 20) -> float:
    """Z-score of price vs. SMA: deviation from mean → reversion signal."""
    ma = sma(close, window)
    std = close.rolling(window=window).std()
    if ma.isna().iloc[-1] or std.iloc[-1] == 0:
        return 0.0
    z = (close.iloc[-1] - ma.iloc[-1]) / std.iloc[-1]
    # z > 2 → sell, z < -2 → buy
    return _clamp(-z / 2)


# ──────────────────────────────────────────────
# Trend Strength
# ──────────────────────────────────────────────


def score_trend(close: pd.Series) -> float:
    """Multi-timeframe EMA alignment: bullish when 20 > 50 > 200."""
    ema20 = ema(close, 20)
    ema50 = ema(close, 50)
    ema200 = ema(close, 200)
    if ema200.isna().iloc[-1]:
        return 0.0

    e20, e50, e200 = ema20.iloc[-1], ema50.iloc[-1], ema200.iloc[-1]
    score = 0.0
    if e20 > e50:
        score += 0.33
    else:
        score -= 0.33
    if e50 > e200:
        score += 0.33
    else:
        score -= 0.33
    if close.iloc[-1] > e200:
        score += 0.34
    else:
        score -= 0.34
    return _clamp(score)


# ──────────────────────────────────────────────
# Volume
# ──────────────────────────────────────────────


def score_volume_trend(close: pd.Series, volume: pd.Series, window: int = 20) -> float:
    """OBV trend confirms price trend."""
    obv_series = obv(close, volume)
    if len(obv_series) < window:
        return 0.0
    obv_ma = sma(obv_series, window)
    if obv_ma.isna().iloc[-1] or obv_ma.iloc[-1] == 0:
        return 0.0
    obv_deviation = (obv_series.iloc[-1] - obv_ma.iloc[-1]) / abs(obv_ma.iloc[-1])
    price_direction = 1.0 if close.iloc[-1] > sma(close, window).iloc[-1] else -1.0
    # Confirms trend if OBV aligns with price direction
    if (obv_deviation > 0 and price_direction > 0) or (obv_deviation < 0 and price_direction < 0):
        return _clamp(price_direction * min(abs(obv_deviation), 1.0))
    return 0.0


# ──────────────────────────────────────────────
# ADX / Trend Strength
# ──────────────────────────────────────────────


def score_adx(high: pd.Series, low: pd.Series, close: pd.Series) -> float:
    """ADX trend strength: trending + bullish → buy, trending + bearish → sell.

    ADX > 25 AND +DI > -DI = bullish (+0.5 to +1).
    ADX > 25 AND -DI > +DI = bearish (-0.5 to -1).
    ADX < 20 = no clear trend → neutral (0).
    """
    adx_series, plus_di, minus_di = adx(high, low, close)
    if adx_series.isna().iloc[-1]:
        return 0.0
    adx_val = adx_series.iloc[-1]
    plus_val = plus_di.iloc[-1]
    minus_val = minus_di.iloc[-1]

    if adx_val < 20:
        return 0.0  # no trend

    # Scale trend strength: ADX 25→0.5, ADX 50→1.0
    strength = _clamp((adx_val - 20) / 30, 0.0, 1.0) * 0.5 + 0.5

    if plus_val > minus_val:
        return _clamp(strength)
    else:
        return _clamp(-strength)


# ──────────────────────────────────────────────
# Stochastic Oscillator
# ──────────────────────────────────────────────


def score_stochastic(high: pd.Series, low: pd.Series, close: pd.Series) -> float:
    """Stochastic: oversold (<20) → buy, overbought (>80) → sell.

    Bonus when %K crosses %D (momentum shift).
    """
    pct_k, pct_d = stochastic(high, low, close)
    if pct_k.isna().iloc[-1] or pct_d.isna().iloc[-1]:
        return 0.0

    k_val = pct_k.iloc[-1]
    d_val = pct_d.iloc[-1]

    score = 0.0
    if k_val <= 20:
        score = _clamp((20 - k_val) / 20)  # 20→0, 0→1
    elif k_val >= 80:
        score = _clamp(-(k_val - 80) / 20)  # 80→0, 100→-1

    # Cross bonus: %K crossing above %D = bullish, below = bearish
    if len(pct_k) >= 2 and len(pct_d) >= 2:
        prev_k = pct_k.iloc[-2]
        prev_d = pct_d.iloc[-2]
        if not (pd.isna(prev_k) or pd.isna(prev_d)):
            if prev_k <= prev_d and k_val > d_val:
                score = _clamp(score + 0.3)
            elif prev_k >= prev_d and k_val < d_val:
                score = _clamp(score - 0.3)

    return score


# ──────────────────────────────────────────────
# A/D Line
# ──────────────────────────────────────────────


def score_ad_line(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, window: int = 20
) -> float:
    """A/D line trend vs price trend — divergence = reversal, confirmation = continuation."""
    ad = accumulation_distribution(high, low, close, volume)
    if len(ad) < window:
        return 0.0

    ad_ma = sma(ad, window)
    price_ma = sma(close, window)
    if ad_ma.isna().iloc[-1] or price_ma.isna().iloc[-1]:
        return 0.0

    # Direction of A/D vs price
    ad_rising = ad.iloc[-1] > ad_ma.iloc[-1]
    price_rising = close.iloc[-1] > price_ma.iloc[-1]

    if ad_rising and price_rising:
        return 0.5  # confirmation: bullish
    elif not ad_rising and not price_rising:
        return -0.5  # confirmation: bearish
    elif ad_rising and not price_rising:
        return 0.7  # bullish divergence: accumulation despite price drop
    else:  # not ad_rising and price_rising
        return -0.7  # bearish divergence: distribution despite price rise


# ──────────────────────────────────────────────
# Chaikin Money Flow
# ──────────────────────────────────────────────


def score_cmf(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series
) -> float:
    """CMF > 0 = buying pressure (bullish), < 0 = selling pressure. Scaled by magnitude."""
    cmf = chaikin_money_flow(high, low, close, volume)
    if cmf.isna().iloc[-1]:
        return 0.0
    # CMF is already bounded roughly [-1, +1]; scale directly
    return _clamp(cmf.iloc[-1] * 2)


# ──────────────────────────────────────────────
# Put/Call Ratio
# ──────────────────────────────────────────────


def score_put_call_ratio(ratio: float | None) -> float:
    """Contrarian sentiment: high put/call = fear (buy), low = complacency (sell).

    ratio > 1.2 → excessive fear → contrarian buy signal
    ratio < 0.5 → complacency → contrarian sell signal
    Returns 0.0 if ratio is None or NaN.
    """
    if ratio is None or pd.isna(ratio):
        return 0.0
    if ratio > 1.2:
        return _clamp((ratio - 1.2) / 0.8)  # 1.2→0, 2.0→1
    elif ratio < 0.5:
        return _clamp(-(0.5 - ratio) / 0.5)  # 0.5→0, 0.0→-1
    return 0.0
