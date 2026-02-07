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
    atr,
    bollinger_pct_b,
    ema,
    macd,
    obv,
    rsi,
    sma,
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
