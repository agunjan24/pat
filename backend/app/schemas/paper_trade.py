from datetime import datetime

from pydantic import BaseModel


class PaperTradeCreate(BaseModel):
    symbol: str
    direction: str  # buy / sell
    quantity: float
    entry_price: float
    stop_loss: float | None = None
    target_price: float | None = None
    signal_score: float | None = None


class PaperTradeOut(BaseModel):
    id: int
    symbol: str
    direction: str
    quantity: float
    entry_price: float
    exit_price: float | None
    stop_loss: float | None
    target_price: float | None
    status: str
    signal_score: float | None
    pnl: float | None
    pnl_pct: float | None
    opened_at: datetime
    closed_at: datetime | None
    model_config = {"from_attributes": True}


class PaperTradeClose(BaseModel):
    exit_price: float


class PaperAccountOut(BaseModel):
    id: int
    name: str
    initial_cash: float
    current_cash: float
    created_at: datetime
    model_config = {"from_attributes": True}


class PaperSummary(BaseModel):
    account: PaperAccountOut
    open_trades: list[PaperTradeOut]
    closed_trades: list[PaperTradeOut]
    total_pnl: float
    win_rate: float
    total_trades: int
