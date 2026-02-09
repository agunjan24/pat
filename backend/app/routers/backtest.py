import logging
from datetime import date

from fastapi import APIRouter, HTTPException, Query

from app.schemas.backtest import BacktestResult
from app.signals.backtest import run_backtest

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_RANGE_DAYS = 730  # ~2 years


@router.get("/run", response_model=BacktestResult)
async def backtest(
    symbol: str = Query(..., description="Ticker symbol"),
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(..., description="End date (YYYY-MM-DD)"),
):
    """Run a rolling-window signal backtest over a date range."""
    if end > date.today():
        raise HTTPException(status_code=400, detail="End date cannot be in the future")
    if start >= end:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    if (end - start).days > MAX_RANGE_DAYS:
        raise HTTPException(status_code=400, detail="Date range cannot exceed 2 years")

    try:
        result = await run_backtest(symbol, start, end)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        logger.exception("Backtest failed for %s", symbol)
        raise HTTPException(status_code=500, detail="Backtest computation failed")

    return result
