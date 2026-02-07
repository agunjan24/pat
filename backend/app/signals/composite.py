"""
Composite signal engine.

Combines individual signal scores into a single recommendation
with direction, conviction, and confidence.
"""

from dataclasses import dataclass

import pandas as pd

from app.signals.scoring import (
    score_bollinger,
    score_ma_crossover,
    score_macd,
    score_mean_reversion,
    score_rsi,
    score_trend,
    score_volume_trend,
)

# Weights for each signal category
WEIGHTS = {
    "ma_crossover": 0.15,
    "rsi": 0.15,
    "macd": 0.15,
    "bollinger": 0.10,
    "mean_reversion": 0.10,
    "trend": 0.20,
    "volume": 0.15,
}


@dataclass
class SignalDetail:
    name: str
    score: float  # -1 to +1
    weight: float
    description: str


@dataclass
class CompositeSignal:
    symbol: str
    direction: str  # "buy", "sell", "hold"
    conviction: str  # "low", "medium", "high"
    composite_score: float  # -1 to +1
    confidence: int  # 0–100
    signals: list[SignalDetail]


def _direction(score: float) -> str:
    if score >= 0.2:
        return "buy"
    elif score <= -0.2:
        return "sell"
    return "hold"


def _conviction(score: float) -> str:
    mag = abs(score)
    if mag >= 0.6:
        return "high"
    elif mag >= 0.3:
        return "medium"
    return "low"


def _confidence(signals: list[SignalDetail]) -> int:
    """Confidence based on signal agreement. More signals pointing the same
    direction = higher confidence."""
    if not signals:
        return 0
    directions = [1 if s.score > 0.1 else (-1 if s.score < -0.1 else 0) for s in signals]
    non_neutral = [d for d in directions if d != 0]
    if not non_neutral:
        return 20  # all neutral → low confidence
    agreement = abs(sum(non_neutral)) / len(non_neutral)
    data_quality = len(non_neutral) / len(signals)
    return int(min(100, (agreement * 70 + data_quality * 30)))


def compute_composite(symbol: str, df: pd.DataFrame) -> CompositeSignal:
    """Compute composite signal from OHLCV DataFrame.

    Args:
        symbol: Ticker symbol for labeling.
        df: DataFrame with columns: Open, High, Low, Close, Volume.

    Returns:
        CompositeSignal with direction, conviction, and individual breakdowns.
    """
    close = df["Close"]
    volume = df["Volume"]

    signal_results: list[SignalDetail] = []

    evaluators = [
        ("ma_crossover", score_ma_crossover, [close], "SMA 20/50 crossover"),
        ("rsi", score_rsi, [close], "RSI (14) overbought/oversold"),
        ("macd", score_macd, [close], "MACD histogram momentum"),
        ("bollinger", score_bollinger, [close], "Bollinger Band %B position"),
        ("mean_reversion", score_mean_reversion, [close], "Z-score mean reversion"),
        ("trend", score_trend, [close], "EMA 20/50/200 alignment"),
        ("volume", score_volume_trend, [close, volume], "OBV trend confirmation"),
    ]

    for name, fn, args, desc in evaluators:
        try:
            score = fn(*args)
        except Exception:
            score = 0.0
        signal_results.append(SignalDetail(
            name=name,
            score=round(score, 4),
            weight=WEIGHTS[name],
            description=desc,
        ))

    # Weighted composite
    composite = sum(s.score * s.weight for s in signal_results)
    composite = max(-1.0, min(1.0, composite))

    return CompositeSignal(
        symbol=symbol,
        direction=_direction(composite),
        conviction=_conviction(composite),
        composite_score=round(composite, 4),
        confidence=_confidence(signal_results),
        signals=signal_results,
    )
