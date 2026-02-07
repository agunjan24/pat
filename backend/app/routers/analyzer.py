from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analyzer.metrics import cagr, daily_returns, max_drawdown, sharpe_ratio
from app.database import get_db
from app.models.portfolio import Position
from app.schemas.analyzer import (
    AllocationItem,
    PerformanceResponse,
    PortfolioSummary,
    PositionSummary,
    PricePoint,
    RiskMetrics,
)
from app.tracker.market_data import get_current_price, get_history

router = APIRouter()

VALID_PERIODS = {"1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"}


@router.get("/summary", response_model=PortfolioSummary)
async def portfolio_summary(db: AsyncSession = Depends(get_db)):
    """Portfolio summary with live prices, P&L, and allocation."""
    result = await db.execute(
        select(Position)
        .where(Position.quantity != 0)
        .options(selectinload(Position.asset))
    )
    positions = result.scalars().all()

    if not positions:
        return PortfolioSummary(
            total_market_value=0,
            total_cost_basis=0,
            total_unrealized_pnl=0,
            total_unrealized_pnl_pct=0,
            position_count=0,
            positions=[],
            allocation=[],
        )

    # Fetch current prices for all unique symbols
    symbols = list({p.asset.symbol for p in positions})
    prices: dict[str, float | None] = {}
    for sym in symbols:
        prices[sym] = await get_current_price(sym)

    pos_summaries: list[PositionSummary] = []
    total_market_value = 0.0
    total_cost_basis = 0.0

    for p in positions:
        current = prices.get(p.asset.symbol) or p.avg_cost
        market_value = p.quantity * current
        cost_basis = p.quantity * p.avg_cost
        pnl = market_value - cost_basis
        pnl_pct = (pnl / cost_basis * 100) if cost_basis != 0 else 0.0

        total_market_value += market_value
        total_cost_basis += cost_basis

        pos_summaries.append(
            PositionSummary(
                position_id=p.id,
                symbol=p.asset.symbol,
                asset_type=p.asset.asset_type.value,
                quantity=p.quantity,
                avg_cost=p.avg_cost,
                current_price=current,
                market_value=round(market_value, 2),
                cost_basis=round(cost_basis, 2),
                unrealized_pnl=round(pnl, 2),
                unrealized_pnl_pct=round(pnl_pct, 2),
            )
        )

    total_pnl = total_market_value - total_cost_basis
    total_pnl_pct = (total_pnl / total_cost_basis * 100) if total_cost_basis != 0 else 0.0

    allocation = [
        AllocationItem(
            symbol=ps.symbol,
            asset_type=ps.asset_type,
            market_value=ps.market_value,
            weight=round(ps.market_value / total_market_value, 4) if total_market_value else 0,
        )
        for ps in pos_summaries
    ]

    return PortfolioSummary(
        total_market_value=round(total_market_value, 2),
        total_cost_basis=round(total_cost_basis, 2),
        total_unrealized_pnl=round(total_pnl, 2),
        total_unrealized_pnl_pct=round(total_pnl_pct, 2),
        position_count=len(pos_summaries),
        positions=pos_summaries,
        allocation=allocation,
    )


@router.get("/performance", response_model=PerformanceResponse)
async def symbol_performance(
    symbol: str = Query(..., description="Ticker symbol"),
    period: str = Query("1y", description="Time period"),
):
    """Historical price data and risk metrics for a symbol."""
    if period not in VALID_PERIODS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid period. Choose from: {', '.join(sorted(VALID_PERIODS))}",
        )

    df = await get_history(symbol, period=period)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

    prices_list = [
        PricePoint(
            date=idx.strftime("%Y-%m-%d"),
            open=round(row["Open"], 2),
            high=round(row["High"], 2),
            low=round(row["Low"], 2),
            close=round(row["Close"], 2),
            volume=int(row["Volume"]),
        )
        for idx, row in df.iterrows()
    ]

    close = df["Close"]
    returns = daily_returns(close)
    volatility = float(returns.std() * (252 ** 0.5)) if len(returns) > 1 else 0.0

    metrics = RiskMetrics(
        symbol=symbol,
        period=period,
        sharpe_ratio=round(sharpe_ratio(returns), 3),
        max_drawdown=round(max_drawdown(close), 4),
        cagr=round(cagr(close), 4),
        volatility=round(volatility, 4),
    )

    return PerformanceResponse(
        symbol=symbol,
        period=period,
        prices=prices_list,
        metrics=metrics,
    )
