"""
Elliott Wave detection engine.

Uses ATR-filtered zigzag pivots to identify swing highs/lows, then matches
impulse (5-wave) and corrective (A-B-C) patterns with Fibonacci ratio
validation.  Returns a structured wave count and a standalone signal score.
"""

import pandas as pd
import numpy as np

from app.signals.technical import atr


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# Fibonacci target ratios for validation
_FIB_RATIOS = {
    "wave2_retrace": (0.382, 0.618),     # Wave 2 retraces 38.2–61.8% of Wave 1
    "wave3_extension": (1.272, 2.618),    # Wave 3 is 1.272–2.618× Wave 1
    "wave4_retrace": (0.236, 0.500),      # Wave 4 retraces 23.6–50% of Wave 3
    "wave5_extension": (0.618, 1.618),    # Wave 5 is 0.618–1.618× Wave 1
}


# ──────────────────────────────────────────────
# Zigzag Pivot Detection
# ──────────────────────────────────────────────

def zigzag_pivots(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    atr_threshold: float = 1.5,
) -> list[dict]:
    """Detect swing highs and lows using ATR-filtered zigzag.

    Returns list of {"index": int, "price": float, "type": "high"|"low"}.
    """
    n = len(close)
    if n < 20:
        return []

    atr_series = atr(high, low, close, period=14)

    # Use the median ATR as the threshold size
    valid_atr = atr_series.dropna()
    if len(valid_atr) == 0:
        return []
    min_swing = float(valid_atr.median()) * atr_threshold

    pivots: list[dict] = []
    # Start by finding the initial direction
    direction = 0  # 1 = looking for high, -1 = looking for low
    last_high_idx = 0
    last_high_val = float(high.iloc[0])
    last_low_idx = 0
    last_low_val = float(low.iloc[0])

    for i in range(1, n):
        h = float(high.iloc[i])
        l = float(low.iloc[i])

        if direction == 0:
            # Determine initial direction
            if h - last_low_val >= min_swing:
                # Initial swing up — mark the low as first pivot
                pivots.append({"index": last_low_idx, "price": last_low_val, "type": "low"})
                direction = 1  # now tracking upward, looking for high
                last_high_idx = i
                last_high_val = h
            elif last_high_val - l >= min_swing:
                pivots.append({"index": last_high_idx, "price": last_high_val, "type": "high"})
                direction = -1
                last_low_idx = i
                last_low_val = l
            else:
                if h > last_high_val:
                    last_high_idx = i
                    last_high_val = h
                if l < last_low_val:
                    last_low_idx = i
                    last_low_val = l

        elif direction == 1:
            # Tracking upward swing, looking for the high
            if h > last_high_val:
                last_high_idx = i
                last_high_val = h
            elif last_high_val - l >= min_swing:
                # Reversal detected — mark the high
                pivots.append({"index": last_high_idx, "price": last_high_val, "type": "high"})
                direction = -1
                last_low_idx = i
                last_low_val = l

        elif direction == -1:
            # Tracking downward swing, looking for the low
            if l < last_low_val:
                last_low_idx = i
                last_low_val = l
            elif h - last_low_val >= min_swing:
                # Reversal detected — mark the low
                pivots.append({"index": last_low_idx, "price": last_low_val, "type": "low"})
                direction = 1
                last_high_idx = i
                last_high_val = h

    # Append the final pending pivot
    if direction == 1:
        pivots.append({"index": last_high_idx, "price": last_high_val, "type": "high"})
    elif direction == -1:
        pivots.append({"index": last_low_idx, "price": last_low_val, "type": "low"})

    return pivots


# ──────────────────────────────────────────────
# Fibonacci Validation
# ──────────────────────────────────────────────

def _ratio_score(actual: float, low_bound: float, high_bound: float) -> float:
    """Score how well *actual* falls within [low_bound, high_bound].

    Returns 1.0 if perfectly in range, decaying toward 0.0 as it deviates.
    """
    if low_bound <= actual <= high_bound:
        return 1.0
    # Distance from nearest bound, normalised by range width
    range_width = high_bound - low_bound
    if range_width == 0:
        return 0.0
    if actual < low_bound:
        miss = (low_bound - actual) / range_width
    else:
        miss = (actual - high_bound) / range_width
    return max(0.0, 1.0 - miss)


def validate_fibonacci_ratios(pivots: list[dict]) -> dict:
    """Check retracement / extension ratios on a set of pivots.

    Expects at least 6 pivots (start + waves 1–5 end) for impulse analysis.
    Returns {"confidence": 0–1, "details": {wave_name: {actual, score}}}.
    """
    if len(pivots) < 6:
        return {"confidence": 0.0, "details": {}}

    # Extract wave amplitudes
    p = [pv["price"] for pv in pivots]

    wave1 = abs(p[1] - p[0])
    wave2_retrace = abs(p[2] - p[1])
    wave3 = abs(p[3] - p[2])
    wave4_retrace = abs(p[4] - p[3])
    wave5 = abs(p[5] - p[4])

    details: dict = {}
    scores: list[float] = []

    # Wave 2 retracement of Wave 1
    if wave1 != 0:
        r = wave2_retrace / wave1
        s = _ratio_score(r, *_FIB_RATIOS["wave2_retrace"])
        details["wave2_retrace"] = {"actual": round(r, 3), "score": round(s, 3)}
        scores.append(s)

    # Wave 3 extension of Wave 1
    if wave1 != 0:
        r = wave3 / wave1
        s = _ratio_score(r, *_FIB_RATIOS["wave3_extension"])
        details["wave3_extension"] = {"actual": round(r, 3), "score": round(s, 3)}
        scores.append(s)

    # Wave 4 retracement of Wave 3
    if wave3 != 0:
        r = wave4_retrace / wave3
        s = _ratio_score(r, *_FIB_RATIOS["wave4_retrace"])
        details["wave4_retrace"] = {"actual": round(r, 3), "score": round(s, 3)}
        scores.append(s)

    # Wave 5 extension of Wave 1
    if wave1 != 0:
        r = wave5 / wave1
        s = _ratio_score(r, *_FIB_RATIOS["wave5_extension"])
        details["wave5_extension"] = {"actual": round(r, 3), "score": round(s, 3)}
        scores.append(s)

    confidence = float(np.mean(scores)) if scores else 0.0
    return {"confidence": round(confidence, 3), "details": details}


# ──────────────────────────────────────────────
# Wave Pattern Matching
# ──────────────────────────────────────────────

_IMPULSE_LABELS = ["1", "2", "3", "4", "5"]
_CORRECTIVE_LABELS = ["A", "B", "C"]


def _is_impulse_up(pivots: list[dict]) -> bool:
    """Check if 6 pivots form an upward impulse (low-high-low-high-low-high)."""
    if len(pivots) < 6:
        return False
    types = [p["type"] for p in pivots[:6]]
    expected = ["low", "high", "low", "high", "low", "high"]
    if types != expected:
        return False
    # Wave 3 must not be shortest
    w1 = pivots[1]["price"] - pivots[0]["price"]
    w3 = pivots[3]["price"] - pivots[2]["price"]
    w5 = pivots[5]["price"] - pivots[4]["price"]
    if w3 < w1 and w3 < w5:
        return False
    # Wave 4 must not overlap wave 1 territory
    if pivots[4]["price"] < pivots[1]["price"]:
        return False
    return True


def _is_impulse_down(pivots: list[dict]) -> bool:
    """Check if 6 pivots form a downward impulse (high-low-high-low-high-low)."""
    if len(pivots) < 6:
        return False
    types = [p["type"] for p in pivots[:6]]
    expected = ["high", "low", "high", "low", "high", "low"]
    if types != expected:
        return False
    w1 = pivots[0]["price"] - pivots[1]["price"]
    w3 = pivots[2]["price"] - pivots[3]["price"]
    w5 = pivots[4]["price"] - pivots[5]["price"]
    if w3 < w1 and w3 < w5:
        return False
    if pivots[4]["price"] > pivots[1]["price"]:
        return False
    return True


def _is_corrective_up(pivots: list[dict]) -> bool:
    """Check if 4 pivots form an upward A-B-C (low-high-low-high)."""
    if len(pivots) < 4:
        return False
    types = [p["type"] for p in pivots[:4]]
    return types == ["low", "high", "low", "high"]


def _is_corrective_down(pivots: list[dict]) -> bool:
    """Check if 4 pivots form a downward A-B-C (high-low-high-low)."""
    if len(pivots) < 4:
        return False
    types = [p["type"] for p in pivots[:4]]
    return types == ["high", "low", "high", "low"]


def _compute_fib_levels(pivots: list[dict], pattern: str) -> list[dict]:
    """Project Fibonacci support/resistance levels from wave structure."""
    levels: list[dict] = []
    if not pivots or len(pivots) < 2:
        return levels

    prices = [p["price"] for p in pivots]
    if "up" in pattern:
        swing_low = min(prices)
        swing_high = max(prices)
    else:
        swing_high = max(prices)
        swing_low = min(prices)

    swing_range = swing_high - swing_low
    if swing_range == 0:
        return levels

    for ratio, label in [
        (0.236, "0.236"),
        (0.382, "0.382"),
        (0.500, "0.500"),
        (0.618, "0.618"),
        (0.786, "0.786"),
        (1.000, "1.000"),
        (1.618, "1.618"),
    ]:
        if "up" in pattern:
            level = swing_high - ratio * swing_range
            desc = f"Retracement {label}"
            if ratio > 1.0:
                level = swing_high + (ratio - 1.0) * swing_range
                desc = f"Extension {label}"
        else:
            level = swing_low + ratio * swing_range
            desc = f"Retracement {label}"
            if ratio > 1.0:
                level = swing_low - (ratio - 1.0) * swing_range
                desc = f"Extension {label}"
        levels.append({"level": round(level, 2), "ratio": label, "label": desc})

    return levels


def _determine_current_wave(pivots: list[dict], total_bars: int, pattern: str) -> str:
    """Determine which wave we are currently in based on the last pivot's position."""
    if not pivots:
        return "1"

    last_pivot_idx = pivots[-1]["index"]
    # If the last pivot is near the end of the data, we're still in the same wave
    # Otherwise the pattern is likely complete

    if "impulse" in pattern:
        n_pivots = min(len(pivots), 6)
        # Map pivot count to current wave
        # 6 pivots = complete 5-wave, so current_wave = "5" (completed)
        wave_map = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "5"}
        return wave_map.get(n_pivots, "1")
    elif "corrective" in pattern:
        n_pivots = min(len(pivots), 4)
        wave_map = {1: "A", 2: "B", 3: "C", 4: "C"}
        return wave_map.get(n_pivots, "A")
    return "1"


def detect_waves(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    lookback: int = 200,
) -> dict:
    """Detect Elliott Wave patterns from OHLCV data.

    Returns dict with keys:
        pattern: str — "impulse_up", "impulse_down", "corrective_up",
                       "corrective_down", "unclear"
        current_wave: str — "1"–"5" or "A"–"C"
        wave_pivots: list[dict] — pivot points with wave labels
        confidence: float — 0.0–1.0 based on Fibonacci adherence
        fib_levels: list[dict] — projected support/resistance levels
    """
    # Use the last `lookback` bars
    n = len(close)
    if n < 50:
        return {
            "pattern": "unclear",
            "current_wave": "1",
            "wave_pivots": [],
            "confidence": 0.0,
            "fib_levels": [],
        }

    start = max(0, n - lookback)
    h = high.iloc[start:].reset_index(drop=True)
    l = low.iloc[start:].reset_index(drop=True)
    c = close.iloc[start:].reset_index(drop=True)

    pivots = zigzag_pivots(h, l, c)
    if len(pivots) < 4:
        return {
            "pattern": "unclear",
            "current_wave": "1",
            "wave_pivots": [],
            "confidence": 0.0,
            "fib_levels": [],
        }

    # Try to match the most recent pivots against templates
    # Try impulse first (needs 6 pivots), then corrective (needs 4)
    best_pattern = "unclear"
    best_confidence = 0.0
    best_pivots: list[dict] = []

    # Try impulse patterns from various starting offsets
    for offset in range(max(0, len(pivots) - 8), max(0, len(pivots) - 5)):
        segment = pivots[offset:offset + 6]
        if len(segment) < 6:
            continue

        if _is_impulse_up(segment):
            fib = validate_fibonacci_ratios(segment)
            if fib["confidence"] > best_confidence:
                best_confidence = fib["confidence"]
                best_pattern = "impulse_up"
                best_pivots = segment
        elif _is_impulse_down(segment):
            fib = validate_fibonacci_ratios(segment)
            if fib["confidence"] > best_confidence:
                best_confidence = fib["confidence"]
                best_pattern = "impulse_down"
                best_pivots = segment

    # Try corrective patterns
    for offset in range(max(0, len(pivots) - 6), max(0, len(pivots) - 3)):
        segment = pivots[offset:offset + 4]
        if len(segment) < 4:
            continue

        if _is_corrective_up(segment):
            conf = 0.4  # corrective patterns get lower base confidence
            if conf > best_confidence:
                best_confidence = conf
                best_pattern = "corrective_up"
                best_pivots = segment
        elif _is_corrective_down(segment):
            conf = 0.4
            if conf > best_confidence:
                best_confidence = conf
                best_pattern = "corrective_down"
                best_pivots = segment

    # Label the pivots with wave names
    labeled_pivots: list[dict] = []
    if "impulse" in best_pattern:
        labels = _IMPULSE_LABELS
        for i, pv in enumerate(best_pivots[:6]):
            # Waves 1,3,5 end at odd indices; waves 2,4 at even indices (after start)
            label = labels[i] if i < len(labels) else str(i)
            labeled_pivots.append({
                "index": pv["index"] + start,
                "price": pv["price"],
                "type": pv["type"],
                "wave_label": label,
            })
    elif "corrective" in best_pattern:
        labels = ["start"] + list(_CORRECTIVE_LABELS)
        for i, pv in enumerate(best_pivots[:4]):
            label = labels[i] if i < len(labels) else str(i)
            labeled_pivots.append({
                "index": pv["index"] + start,
                "price": pv["price"],
                "type": pv["type"],
                "wave_label": label,
            })

    current_wave = _determine_current_wave(best_pivots, n, best_pattern)
    fib_levels = _compute_fib_levels(best_pivots, best_pattern)

    return {
        "pattern": best_pattern,
        "current_wave": current_wave,
        "wave_pivots": labeled_pivots,
        "confidence": min(best_confidence, 1.0),
        "fib_levels": fib_levels,
    }


# ──────────────────────────────────────────────
# Wave-Based Signal Scoring
# ──────────────────────────────────────────────

def score_elliott_wave(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
) -> float:
    """Score based on Elliott Wave structure.  Returns [-1, +1].

    - Impulse up in waves 1/3: bullish  (+0.5 to +1.0, scaled by confidence)
    - Impulse up in wave 5:   weakening (+0.2)
    - Corrective A-B-C after impulse up: bearish (-0.5 to -1.0)
    - Unclear / low confidence: neutral (0.0)
    """
    if len(close) < 50:
        return 0.0

    wave = detect_waves(high, low, close)
    pattern = wave["pattern"]
    confidence = wave["confidence"]
    current = wave["current_wave"]

    if pattern == "unclear" or confidence < 0.15:
        return 0.0

    if pattern == "impulse_up":
        if current in ("1", "3"):
            return _clamp(0.5 + 0.5 * confidence)
        elif current == "5":
            return _clamp(0.2 * confidence)
        elif current in ("2", "4"):
            return _clamp(0.3 * confidence)
        return 0.0

    elif pattern == "impulse_down":
        if current in ("1", "3"):
            return _clamp(-(0.5 + 0.5 * confidence))
        elif current == "5":
            return _clamp(-0.2 * confidence)
        elif current in ("2", "4"):
            return _clamp(-0.3 * confidence)
        return 0.0

    elif pattern == "corrective_up":
        return _clamp(0.3 * confidence)

    elif pattern == "corrective_down":
        return _clamp(-0.3 * confidence)

    return 0.0
