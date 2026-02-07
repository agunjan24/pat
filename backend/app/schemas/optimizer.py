from pydantic import BaseModel


class FrontierPointOut(BaseModel):
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


class OptimizationOut(BaseModel):
    symbols: list[str]
    min_variance: FrontierPointOut
    max_sharpe: FrontierPointOut
    risk_parity: FrontierPointOut
    frontier: list[FrontierPointOut]
