from fastapi import APIRouter, HTTPException, Query

from app.schemas.signals import RiskContext, ScanResult, SignalDetailOut
from app.signals.composite import compute_composite
from app.signals.risk import compute_risk_context
from app.tracker.market_data import get_history

router = APIRouter()


@router.get("/scan", response_model=ScanResult)
async def scan_signals(
    symbol: str = Query(..., description="Ticker symbol to scan"),
    portfolio_value: float = Query(100_000, description="Portfolio value for position sizing"),
):
    """Scan a symbol for buy/sell signals with risk-adjusted context."""
    df = await get_history(symbol, period="1y", interval="1d")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    composite = compute_composite(symbol.upper(), df)

    risk = compute_risk_context(
        df,
        direction=composite.direction,
        composite_score=composite.composite_score,
        portfolio_value=portfolio_value,
    )

    return ScanResult(
        symbol=composite.symbol,
        current_price=round(float(df["Close"].iloc[-1]), 2),
        direction=composite.direction,
        conviction=composite.conviction,
        composite_score=composite.composite_score,
        confidence=composite.confidence,
        signals=[
            SignalDetailOut(
                name=s.name,
                score=s.score,
                weight=s.weight,
                description=s.description,
            )
            for s in composite.signals
        ],
        risk=RiskContext(**risk),
    )
