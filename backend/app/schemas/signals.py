from pydantic import BaseModel


class SignalDetailOut(BaseModel):
    name: str
    score: float
    weight: float
    description: str


class RiskContext(BaseModel):
    stop_loss: float | None
    target_price: float | None
    risk_reward: float | None
    position_size: float
    position_pct: float


class ScanResult(BaseModel):
    symbol: str
    current_price: float
    direction: str
    conviction: str
    composite_score: float
    confidence: int
    signals: list[SignalDetailOut]
    risk: RiskContext
