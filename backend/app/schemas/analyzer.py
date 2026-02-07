from pydantic import BaseModel


class AllocationItem(BaseModel):
    symbol: str
    asset_type: str
    market_value: float
    weight: float  # 0–1


class PositionSummary(BaseModel):
    position_id: int
    symbol: str
    asset_type: str
    quantity: float
    avg_cost: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    unrealized_pnl_pct: float


class PortfolioSummary(BaseModel):
    total_market_value: float
    total_cost_basis: float
    total_unrealized_pnl: float
    total_unrealized_pnl_pct: float
    position_count: int
    positions: list[PositionSummary]
    allocation: list[AllocationItem]


class PricePoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class RiskMetrics(BaseModel):
    symbol: str
    period: str
    sharpe_ratio: float
    max_drawdown: float
    cagr: float
    volatility: float


class PerformanceResponse(BaseModel):
    symbol: str
    period: str
    prices: list[PricePoint]
    metrics: RiskMetrics
