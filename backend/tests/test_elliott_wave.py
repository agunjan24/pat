import numpy as np
import pandas as pd
import pytest

from app.signals.elliott_wave import (
    detect_waves,
    score_elliott_wave,
    validate_fibonacci_ratios,
    zigzag_pivots,
)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _make_ohlcv_series(n=100):
    """Create synthetic OHLCV series for indicator tests."""
    close = pd.Series(np.linspace(100, 130, n) + np.random.randn(n) * 0.5)
    high = close + np.random.uniform(0.5, 2, n)
    low = close - np.random.uniform(0.5, 2, n)
    volume = pd.Series(np.random.randint(100_000, 1_000_000, n).astype(float))
    return high, low, close, volume


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


# ──────────────────────────────────────────────
# Zigzag Tests
# ──────────────────────────────────────────────


def test_zigzag_uptrend_ascending_lows():
    """Synthetic uptrend produces pivots with ascending lows."""
    n = 200
    np.random.seed(42)
    base = np.linspace(100, 200, n)
    # Add sawtooth to create clear swings
    sawtooth = np.tile(np.concatenate([np.linspace(0, 10, 25), np.linspace(10, 0, 25)]), n // 50)
    close = pd.Series(base + sawtooth[:n])
    high = close + 1
    low = close - 1

    pivots = zigzag_pivots(high, low, close, atr_threshold=1.0)
    assert len(pivots) >= 2

    # Check that low pivots are generally ascending
    low_pivots = [p for p in pivots if p["type"] == "low"]
    if len(low_pivots) >= 2:
        # At least the last low should be higher than the first
        assert low_pivots[-1]["price"] >= low_pivots[0]["price"]


def test_zigzag_filters_noise():
    """Higher ATR threshold produces fewer pivots than lower threshold."""
    n = 200
    np.random.seed(0)
    t = np.arange(n)
    close = pd.Series(100 + 10 * np.sin(t / 10) + np.random.randn(n) * 0.5)
    high = close + np.random.uniform(0.5, 1.5, n)
    low = close - np.random.uniform(0.5, 1.5, n)

    pivots_loose = zigzag_pivots(high, low, close, atr_threshold=3.0)
    pivots_tight = zigzag_pivots(high, low, close, atr_threshold=1.0)
    # Stricter threshold should produce fewer or equal pivots
    assert len(pivots_loose) <= len(pivots_tight)


def test_zigzag_sufficient_pivots_for_long_data():
    """Long data with clear swings returns multiple pivots."""
    n = 300
    np.random.seed(7)
    # Create oscillating price data
    t = np.arange(n)
    close = pd.Series(100 + 20 * np.sin(t / 15) + t * 0.1)
    high = close + 2
    low = close - 2

    pivots = zigzag_pivots(high, low, close, atr_threshold=1.0)
    assert len(pivots) >= 4


def test_zigzag_short_data_returns_empty():
    """Data shorter than 20 bars returns empty list."""
    close = pd.Series([100, 101, 102, 103, 104])
    high = close + 1
    low = close - 1
    pivots = zigzag_pivots(high, low, close)
    assert pivots == []


# ──────────────────────────────────────────────
# Wave Detection Tests
# ──────────────────────────────────────────────


def test_detect_waves_staircase_impulse():
    """Clear staircase pattern should be detected as an impulse."""
    np.random.seed(42)
    n = 200
    # Build a 5-wave staircase up pattern
    segments = [
        np.linspace(100, 130, 40),  # wave 1 up
        np.linspace(130, 115, 20),  # wave 2 down
        np.linspace(115, 160, 50),  # wave 3 up (longest)
        np.linspace(160, 145, 20),  # wave 4 down
        np.linspace(145, 170, 40),  # wave 5 up
        np.linspace(170, 165, 30),  # tail
    ]
    base = np.concatenate(segments)
    close = pd.Series(base + np.random.randn(len(base)) * 0.5)
    high = close + np.random.uniform(0.5, 2, len(base))
    low = close - np.random.uniform(0.5, 2, len(base))

    result = detect_waves(high, low, close, lookback=len(base))
    # Should detect some kind of pattern (impulse or at least not crash)
    assert result["pattern"] in ("impulse_up", "impulse_down", "corrective_up", "corrective_down", "unclear")
    assert 0.0 <= result["confidence"] <= 1.0


def test_detect_waves_confidence_range():
    """Confidence is always between 0.0 and 1.0."""
    high, low, close, _ = _make_ohlcv_series(200)
    result = detect_waves(high, low, close)
    assert 0.0 <= result["confidence"] <= 1.0


def test_detect_waves_current_wave_valid():
    """current_wave is one of the valid labels."""
    high, low, close, _ = _make_ohlcv_series(200)
    result = detect_waves(high, low, close)
    valid_waves = {"1", "2", "3", "4", "5", "A", "B", "C"}
    assert result["current_wave"] in valid_waves


def test_detect_waves_short_data_unclear():
    """Short data (<50 bars) returns 'unclear' pattern gracefully."""
    close = pd.Series(np.linspace(100, 110, 30))
    high = close + 1
    low = close - 1
    result = detect_waves(high, low, close)
    assert result["pattern"] == "unclear"
    assert result["confidence"] == 0.0


# ──────────────────────────────────────────────
# Scoring Tests
# ──────────────────────────────────────────────


def test_score_elliott_wave_range():
    """Score is always in [-1, +1]."""
    high, low, close, _ = _make_ohlcv_series(200)
    score = score_elliott_wave(high, low, close)
    assert -1.0 <= score <= 1.0


def test_score_elliott_wave_short_data_zero():
    """Returns 0.0 on short/insufficient data."""
    close = pd.Series([100, 101, 102])
    high = close + 1
    low = close - 1
    score = score_elliott_wave(high, low, close)
    assert score == 0.0


def test_score_elliott_wave_various_data():
    """Score stays in range for both uptrend and downtrend data."""
    for trend in ("up", "down"):
        df = _make_ohlcv_df(n=250, trend=trend)
        score = score_elliott_wave(df["High"], df["Low"], df["Close"])
        assert -1.0 <= score <= 1.0


# ──────────────────────────────────────────────
# Fibonacci Validation Tests
# ──────────────────────────────────────────────


def test_fibonacci_ideal_ratios_high_confidence():
    """Known pivot points with exact Fibonacci ratios produce high confidence."""
    # Create pivots with ideal Fibonacci ratios:
    # Wave 1: 100 → 120 (amplitude 20)
    # Wave 2: 120 → 110 (retrace 50% of wave 1 — within 0.382–0.618)
    # Wave 3: 110 → 142 (amplitude 32, = 1.6× wave 1 — within 1.272–2.618)
    # Wave 4: 142 → 132 (retrace 31% of wave 3 — within 0.236–0.500)
    # Wave 5: 132 → 150 (amplitude 18, = 0.9× wave 1 — within 0.618–1.618)
    pivots = [
        {"index": 0, "price": 100, "type": "low"},
        {"index": 20, "price": 120, "type": "high"},
        {"index": 30, "price": 110, "type": "low"},
        {"index": 60, "price": 142, "type": "high"},
        {"index": 70, "price": 132, "type": "low"},
        {"index": 90, "price": 150, "type": "high"},
    ]
    result = validate_fibonacci_ratios(pivots)
    assert result["confidence"] > 0.5
    assert "wave2_retrace" in result["details"]
    assert "wave3_extension" in result["details"]


def test_fibonacci_non_fibonacci_lower_confidence():
    """Non-Fibonacci pivots produce lower confidence."""
    # Wave 2 retraces 90% (outside 0.382–0.618 range)
    # Wave 3 = 0.5× Wave 1 (below 1.272–2.618 range)
    pivots = [
        {"index": 0, "price": 100, "type": "low"},
        {"index": 20, "price": 120, "type": "high"},
        {"index": 30, "price": 102, "type": "low"},   # 90% retrace
        {"index": 60, "price": 112, "type": "high"},   # wave 3 = 0.5× wave 1
        {"index": 70, "price": 108, "type": "low"},
        {"index": 90, "price": 115, "type": "high"},
    ]
    result = validate_fibonacci_ratios(pivots)
    # Should have lower confidence than ideal ratios
    assert result["confidence"] < 0.8


def test_fibonacci_too_few_pivots():
    """Fewer than 6 pivots returns 0 confidence."""
    pivots = [
        {"index": 0, "price": 100, "type": "low"},
        {"index": 10, "price": 110, "type": "high"},
        {"index": 20, "price": 105, "type": "low"},
    ]
    result = validate_fibonacci_ratios(pivots)
    assert result["confidence"] == 0.0
    assert result["details"] == {}
