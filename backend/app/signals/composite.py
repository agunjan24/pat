"""
Composite signal engine.

Combines individual signal scores into a single recommendation
with direction, conviction, and confidence.
"""

from dataclasses import dataclass

import pandas as pd

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
    score_volume_trend,
)

# Weights for each signal category
WEIGHTS = {
    # Existing (rebalanced)
    "ma_crossover": 0.10,
    "rsi": 0.10,
    "macd": 0.10,
    "bollinger": 0.07,
    "mean_reversion": 0.07,
    "trend": 0.12,
    "volume": 0.08,
    # New
    "adx": 0.10,
    "stochastic": 0.08,
    "ad_line": 0.06,
    "cmf": 0.07,
    "put_call_ratio": 0.05,
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


def compute_composite(
    symbol: str, df: pd.DataFrame, put_call_ratio: float | None = None
) -> CompositeSignal:
    """Compute composite signal from OHLCV DataFrame.

    Args:
        symbol: Ticker symbol for labeling.
        df: DataFrame with columns: Open, High, Low, Close, Volume.
        put_call_ratio: Optional put/call volume ratio from options chain.
            When None, that signal scores 0.0 and its weight is redistributed.

    Returns:
        CompositeSignal with direction, conviction, and individual breakdowns.
    """
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Score put/call ratio (may be None → 0.0)
    pc_score = score_put_call_ratio(put_call_ratio)

    signal_results: list[SignalDetail] = []

    evaluators = [
        ("ma_crossover", score_ma_crossover, [close], "SMA 20/50 crossover"),
        ("rsi", score_rsi, [close], "RSI (14) overbought/oversold"),
        ("macd", score_macd, [close], "MACD histogram momentum"),
        ("bollinger", score_bollinger, [close], "Bollinger Band %B position"),
        ("mean_reversion", score_mean_reversion, [close], "Z-score mean reversion"),
        ("trend", score_trend, [close], "EMA 20/50/200 alignment"),
        ("volume", score_volume_trend, [close, volume], "OBV trend confirmation"),
        ("adx", score_adx, [high, low, close], "ADX trend strength"),
        ("stochastic", score_stochastic, [high, low, close], "Stochastic %K/%D oscillator"),
        ("ad_line", score_ad_line, [high, low, close, volume], "A/D line vs price trend"),
        ("cmf", score_cmf, [high, low, close, volume], "Chaikin Money Flow pressure"),
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

    # Put/call ratio is pre-computed (not from OHLCV)
    signal_results.append(SignalDetail(
        name="put_call_ratio",
        score=round(pc_score, 4),
        weight=WEIGHTS["put_call_ratio"],
        description="Put/call ratio contrarian sentiment",
    ))

    # When put_call_ratio data is unavailable, redistribute its weight
    if put_call_ratio is None:
        pc_weight = WEIGHTS["put_call_ratio"]
        other_weight_sum = sum(
            s.weight for s in signal_results if s.name != "put_call_ratio"
        )
        if other_weight_sum > 0:
            scale = 1.0 / other_weight_sum
            for s in signal_results:
                if s.name != "put_call_ratio":
                    s.weight = round(s.weight * scale, 4)
                else:
                    s.weight = 0.0

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
