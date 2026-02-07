from pydantic import BaseModel


# ──────────────────────────────────────────────
# Greeks
# ──────────────────────────────────────────────


class GreeksOut(BaseModel):
    price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float


# ──────────────────────────────────────────────
# IV / Skew / Term Structure
# ──────────────────────────────────────────────


class IVMetricsOut(BaseModel):
    current_iv: float
    iv_rank: float
    iv_percentile: float
    iv_high: float
    iv_low: float


class SkewPointOut(BaseModel):
    strike: float
    call_iv: float | None
    put_iv: float | None


class SkewOut(BaseModel):
    skew_ratio: float
    points: list[SkewPointOut]


class TermStructurePointOut(BaseModel):
    expiration: str
    days_to_expiry: int
    atm_iv: float


class OptionsAnalysisOut(BaseModel):
    symbol: str
    spot_price: float
    expirations: list[str]
    iv_metrics: IVMetricsOut
    skew: SkewOut
    term_structure: list[TermStructurePointOut]


# ──────────────────────────────────────────────
# LEAPS
# ──────────────────────────────────────────────


class ThetaEfficiencyOut(BaseModel):
    delta_per_dollar: float
    theta_per_delta: float


class LeapsCandidateOut(BaseModel):
    strike: float
    expiration: str
    option_type: str
    days_to_expiry: int
    market_price: float
    delta: float
    theta: float
    vega: float
    iv: float
    intrinsic: float
    extrinsic: float
    extrinsic_pct: float
    theta_efficiency: ThetaEfficiencyOut
    stock_replacement_cost: float
    roll_recommendation: str


class LeapsAnalysisOut(BaseModel):
    symbol: str
    spot_price: float
    leaps_expirations: list[str]
    candidates: list[LeapsCandidateOut]
