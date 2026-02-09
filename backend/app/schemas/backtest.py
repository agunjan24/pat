from pydantic import BaseModel


class DailySignal(BaseModel):
    date: str
    composite_score: float
    direction: str
    conviction: str
    confidence: int
    forward_1d: float | None
    forward_5d: float | None
    forward_21d: float | None
    signal_return_1d: float | None
    signal_return_5d: float | None
    signal_return_21d: float | None


class HorizonMetrics(BaseModel):
    hit_rate: float
    avg_signal_return: float
    profit_factor: float | None
    total_signals: int
    wins: int
    losses: int


class ConvictionBreakdown(BaseModel):
    conviction: str
    count: int
    hit_rate_1d: float
    hit_rate_5d: float
    hit_rate_21d: float
    avg_return_1d: float
    avg_return_5d: float
    avg_return_21d: float


class BacktestResult(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    total_trading_days: int
    horizon_1d: HorizonMetrics
    horizon_5d: HorizonMetrics
    horizon_21d: HorizonMetrics
    conviction_breakdown: list[ConvictionBreakdown]
    daily_signals: list[DailySignal]
    equity_curve: list[dict]
    max_drawdown_1d: float
    max_drawdown_5d: float
    max_drawdown_21d: float
