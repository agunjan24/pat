from pydantic import BaseModel

from app.schemas.signals import RiskContext


class WavePivot(BaseModel):
    index: int
    date: str
    price: float
    type: str
    wave_label: str


class FibLevel(BaseModel):
    level: float
    ratio: str
    label: str


class WaveAnalysis(BaseModel):
    pattern: str
    current_wave: str
    confidence: float
    wave_pivots: list[WavePivot]
    fib_levels: list[FibLevel]


class IndividualSignal(BaseModel):
    name: str
    score: float
    description: str


class ElliottWaveResult(BaseModel):
    symbol: str
    current_price: float
    wave_analysis: WaveAnalysis
    signals: list[IndividualSignal]
    direction: str
    conviction: str
    risk: RiskContext
