import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas.elliott_wave import (
    ElliottWaveResult,
    FibLevel,
    IndividualSignal,
    WaveAnalysis,
    WavePivot,
)
from app.schemas.signals import RiskContext
from app.signals.elliott_wave import detect_waves, score_elliott_wave
from app.signals.risk import compute_risk_context
from app.signals.scoring import score_macd, score_rsi
from app.tracker.market_data import get_history

logger = logging.getLogger(__name__)

router = APIRouter()


def _direction_from_score(score: float) -> str:
    if score >= 0.2:
        return "buy"
    elif score <= -0.2:
        return "sell"
    return "hold"


def _conviction_from_score(score: float) -> str:
    a = abs(score)
    if a >= 0.6:
        return "high"
    elif a >= 0.3:
        return "medium"
    return "low"


def _describe_wave_score(score: float, pattern: str, current_wave: str) -> str:
    if pattern == "unclear":
        return "No clear wave structure detected"
    direction = "bullish" if "up" in pattern else "bearish"
    kind = "impulse" if "impulse" in pattern else "corrective"
    return f"{kind.title()} {direction} pattern — currently in wave {current_wave}"


def _describe_rsi(score: float) -> str:
    if score > 0.1:
        return "RSI oversold — potential bounce"
    elif score < -0.1:
        return "RSI overbought — potential pullback"
    return "RSI neutral"


def _describe_macd(score: float) -> str:
    if score > 0.1:
        return "MACD histogram positive — bullish momentum"
    elif score < -0.1:
        return "MACD histogram negative — bearish momentum"
    return "MACD neutral"


@router.get("/analyze", response_model=ElliottWaveResult)
async def analyze_elliott_wave(
    symbol: str = Query(..., description="Ticker symbol to analyze"),
    portfolio_value: float = Query(100_000, description="Portfolio value for position sizing"),
):
    """Elliott Wave analysis with independent RSI and MACD signals."""
    df = await get_history(symbol.upper(), period="2y", interval="1d")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # Wave detection
    wave = detect_waves(high, low, close)

    # Convert dates for wave pivots
    wave_pivots: list[WavePivot] = []
    for wp in wave["wave_pivots"]:
        idx = wp["index"]
        if 0 <= idx < len(df):
            date_val = df.index[idx]
            date_str = str(date_val.date()) if hasattr(date_val, "date") else str(date_val)
        else:
            date_str = ""
        wave_pivots.append(WavePivot(
            index=wp["index"],
            date=date_str,
            price=round(wp["price"], 2),
            type=wp["type"],
            wave_label=wp["wave_label"],
        ))

    fib_levels = [
        FibLevel(level=fl["level"], ratio=fl["ratio"], label=fl["label"])
        for fl in wave["fib_levels"]
    ]

    wave_analysis = WaveAnalysis(
        pattern=wave["pattern"],
        current_wave=wave["current_wave"],
        confidence=round(wave["confidence"], 3),
        wave_pivots=wave_pivots,
        fib_levels=fib_levels,
    )

    # 3 independent signals
    ew_score = score_elliott_wave(high, low, close)
    rsi_score = score_rsi(close)
    macd_score = score_macd(close)

    signals = [
        IndividualSignal(
            name="elliott_wave",
            score=round(ew_score, 4),
            description=_describe_wave_score(ew_score, wave["pattern"], wave["current_wave"]),
        ),
        IndividualSignal(
            name="rsi",
            score=round(rsi_score, 4),
            description=_describe_rsi(rsi_score),
        ),
        IndividualSignal(
            name="macd",
            score=round(macd_score, 4),
            description=_describe_macd(macd_score),
        ),
    ]

    # Direction from simple average of 3 scores
    avg_score = (ew_score + rsi_score + macd_score) / 3.0
    direction = _direction_from_score(avg_score)
    conviction = _conviction_from_score(avg_score)

    # Risk context
    risk = compute_risk_context(
        df,
        direction=direction,
        composite_score=avg_score,
        portfolio_value=portfolio_value,
    )

    return ElliottWaveResult(
        symbol=symbol.upper(),
        current_price=round(float(close.iloc[-1]), 2),
        wave_analysis=wave_analysis,
        signals=signals,
        direction=direction,
        conviction=conviction,
        risk=RiskContext(**risk),
    )
