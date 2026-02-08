import logging

from fastapi import APIRouter, HTTPException, Query

from app.schemas.signals import RiskContext, ScanResult, SignalDetailOut
from app.signals.composite import compute_composite
from app.signals.risk import compute_risk_context
from app.signals.technical import put_call_volume_ratio
from app.tracker.market_data import get_history, get_option_chain, get_option_expirations

logger = logging.getLogger(__name__)

router = APIRouter()


async def _fetch_put_call_ratio(symbol: str) -> float | None:
    """Try to fetch nearest-expiry put/call volume ratio. Returns None on failure."""
    try:
        expirations = await get_option_expirations(symbol)
        if not expirations:
            return None
        nearest = expirations[0]
        chain = await get_option_chain(symbol, nearest)
        return put_call_volume_ratio(chain["calls"], chain["puts"])
    except Exception:
        logger.debug("Could not fetch options data for %s", symbol, exc_info=True)
        return None


@router.get("/scan", response_model=ScanResult)
async def scan_signals(
    symbol: str = Query(..., description="Ticker symbol to scan"),
    portfolio_value: float = Query(100_000, description="Portfolio value for position sizing"),
):
    """Scan a symbol for buy/sell signals with risk-adjusted context."""
    df = await get_history(symbol, period="1y", interval="1d")
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    # Optionally fetch put/call ratio (never blocks scan on failure)
    pc_ratio = await _fetch_put_call_ratio(symbol.upper())

    composite = compute_composite(symbol.upper(), df, put_call_ratio=pc_ratio)

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
