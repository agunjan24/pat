from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.paper_trade import PaperAccount, PaperTrade, PaperTradeStatus
from app.schemas.paper_trade import (
    PaperAccountOut,
    PaperSummary,
    PaperTradeClose,
    PaperTradeCreate,
    PaperTradeOut,
)

router = APIRouter()


async def _get_or_create_account(db: AsyncSession) -> PaperAccount:
    result = await db.execute(select(PaperAccount).limit(1))
    account = result.scalars().first()
    if not account:
        account = PaperAccount(name="Default", initial_cash=100_000, current_cash=100_000)
        db.add(account)
        await db.commit()
        await db.refresh(account)
    return account


@router.get("/summary", response_model=PaperSummary)
async def paper_summary(db: AsyncSession = Depends(get_db)):
    """Paper trading account summary with open/closed trades and stats."""
    account = await _get_or_create_account(db)

    open_result = await db.execute(
        select(PaperTrade).where(PaperTrade.status == PaperTradeStatus.OPEN)
    )
    open_trades = open_result.scalars().all()

    closed_result = await db.execute(
        select(PaperTrade)
        .where(PaperTrade.status == PaperTradeStatus.CLOSED)
        .order_by(PaperTrade.closed_at.desc())
    )
    closed_trades = closed_result.scalars().all()

    total_pnl = sum(t.pnl or 0 for t in closed_trades)
    winners = sum(1 for t in closed_trades if (t.pnl or 0) > 0)
    total_closed = len(closed_trades)
    win_rate = (winners / total_closed * 100) if total_closed > 0 else 0

    return PaperSummary(
        account=PaperAccountOut.model_validate(account),
        open_trades=[PaperTradeOut.model_validate(t) for t in open_trades],
        closed_trades=[PaperTradeOut.model_validate(t) for t in closed_trades],
        total_pnl=round(total_pnl, 2),
        win_rate=round(win_rate, 1),
        total_trades=total_closed,
    )


@router.post("/trades", response_model=PaperTradeOut, status_code=201)
async def open_paper_trade(body: PaperTradeCreate, db: AsyncSession = Depends(get_db)):
    """Open a new paper trade."""
    if body.direction not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="Direction must be 'buy' or 'sell'")

    account = await _get_or_create_account(db)
    cost = body.quantity * body.entry_price
    if body.direction == "buy" and cost > account.current_cash:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient cash. Need ${cost:.2f}, have ${account.current_cash:.2f}",
        )

    if body.direction == "buy":
        account.current_cash -= cost

    trade = PaperTrade(
        symbol=body.symbol.upper(),
        direction=body.direction,
        quantity=body.quantity,
        entry_price=body.entry_price,
        stop_loss=body.stop_loss,
        target_price=body.target_price,
        signal_score=body.signal_score,
    )
    db.add(trade)
    await db.commit()
    await db.refresh(trade)
    return trade


@router.post("/trades/{trade_id}/close", response_model=PaperTradeOut)
async def close_paper_trade(
    trade_id: int,
    body: PaperTradeClose,
    db: AsyncSession = Depends(get_db),
):
    """Close a paper trade and realize P&L."""
    trade = await db.get(PaperTrade, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.status == PaperTradeStatus.CLOSED:
        raise HTTPException(status_code=409, detail="Trade already closed")

    trade.exit_price = body.exit_price
    trade.status = PaperTradeStatus.CLOSED
    trade.closed_at = datetime.utcnow()

    if trade.direction == "buy":
        trade.pnl = round((body.exit_price - trade.entry_price) * trade.quantity, 2)
    else:
        trade.pnl = round((trade.entry_price - body.exit_price) * trade.quantity, 2)

    trade.pnl_pct = round(
        trade.pnl / (trade.entry_price * trade.quantity) * 100, 2
    ) if trade.entry_price * trade.quantity != 0 else 0

    # Return proceeds to account
    account = await _get_or_create_account(db)
    if trade.direction == "buy":
        account.current_cash += body.exit_price * trade.quantity
    else:
        account.current_cash += trade.pnl  # short: return profit/loss

    await db.commit()
    await db.refresh(trade)
    return trade


@router.post("/reset", response_model=PaperAccountOut)
async def reset_paper_account(db: AsyncSession = Depends(get_db)):
    """Reset the paper trading account: delete all trades, restore cash to $100k."""
    from sqlalchemy import delete as sql_delete

    await db.execute(sql_delete(PaperTrade))

    # Reset or create account
    result = await db.execute(select(PaperAccount).limit(1))
    account = result.scalars().first()
    if account:
        account.initial_cash = 100_000
        account.current_cash = 100_000
    else:
        account = PaperAccount(name="Default", initial_cash=100_000, current_cash=100_000)
        db.add(account)

    await db.commit()
    await db.refresh(account)
    return account


@router.get("/trades", response_model=list[PaperTradeOut])
async def list_paper_trades(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(PaperTrade).order_by(PaperTrade.opened_at.desc())
    if status == "open":
        stmt = stmt.where(PaperTrade.status == PaperTradeStatus.OPEN)
    elif status == "closed":
        stmt = stmt.where(PaperTrade.status == PaperTradeStatus.CLOSED)
    result = await db.execute(stmt)
    return result.scalars().all()
