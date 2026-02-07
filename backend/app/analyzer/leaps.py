"""
LEAPS-specific analysis.

LEAPS = Long-Term Equity Anticipation Securities (options with > 1 year to expiry).
"""

from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd

from app.analyzer.greeks import bs_price, compute_greeks


LEAPS_MIN_DTE = 365  # minimum days to expiry to qualify as LEAPS


@dataclass
class ThetaEfficiency:
    """How efficiently a LEAPS contract delivers delta exposure per dollar of theta."""
    strike: float
    expiration: str
    option_type: str
    days_to_expiry: int
    price: float
    delta: float
    theta: float  # per day
    delta_per_dollar: float  # delta / price — leverage efficiency
    theta_per_delta: float  # daily theta / delta — cost of time per unit of exposure


@dataclass
class LeapsCandidate:
    """A LEAPS contract with full analysis."""
    strike: float
    expiration: str
    option_type: str
    days_to_expiry: int
    market_price: float
    theo_price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    iv: float
    intrinsic: float
    extrinsic: float
    extrinsic_pct: float  # extrinsic / market_price
    theta_efficiency: ThetaEfficiency
    stock_replacement_cost: float  # cost of 1 LEAPS vs 100 shares (as %)
    roll_recommendation: str  # "hold", "monitor", "roll_now"


@dataclass
class LeapsAnalysis:
    symbol: str
    spot_price: float
    risk_free_rate: float
    candidates: list[LeapsCandidate]


def _roll_recommendation(dte: int, extrinsic_pct: float) -> str:
    """Determine if a LEAPS should be rolled.

    Rules:
    - DTE < 90 and any extrinsic → roll now (time decay accelerates)
    - DTE < 180 and extrinsic < 15% → monitor closely
    - Otherwise hold
    """
    if dte < 90:
        return "roll_now"
    if dte < 180 and extrinsic_pct < 0.15:
        return "monitor"
    return "hold"


def analyze_leaps_chain(
    calls_df: pd.DataFrame,
    puts_df: pd.DataFrame,
    expiration: str,
    spot_price: float,
    risk_free_rate: float = 0.045,
    today: date | None = None,
) -> list[LeapsCandidate]:
    """Analyze LEAPS candidates for a single expiration.

    Filters to deep ITM and ATM calls (delta > 0.5) and deep ITM puts (delta < -0.5).
    """
    if today is None:
        today = date.today()

    try:
        exp_date = datetime.strptime(expiration, "%Y-%m-%d").date()
    except ValueError:
        return []

    dte = (exp_date - today).days
    if dte < LEAPS_MIN_DTE:
        return []

    t = dte / 365.0
    candidates = []

    for df, opt_type in [(calls_df, "call"), (puts_df, "put")]:
        if df.empty:
            continue

        for _, row in df.iterrows():
            strike = row["strike"]
            market_price = row.get("lastPrice", 0) or 0
            iv = row.get("impliedVolatility", 0) or 0

            if market_price <= 0 or iv <= 0:
                continue

            greeks = compute_greeks(spot_price, strike, t, risk_free_rate, iv, opt_type)

            # Filter: only deep ITM to ATM for stock replacement
            if opt_type == "call" and greeks.delta < 0.50:
                continue
            if opt_type == "put" and greeks.delta > -0.50:
                continue

            # Intrinsic / extrinsic breakdown
            if opt_type == "call":
                intrinsic = max(spot_price - strike, 0)
            else:
                intrinsic = max(strike - spot_price, 0)

            extrinsic = max(market_price - intrinsic, 0)
            extrinsic_pct = extrinsic / market_price if market_price > 0 else 0

            # Theta efficiency
            abs_delta = abs(greeks.delta)
            delta_per_dollar = abs_delta / market_price if market_price > 0 else 0
            theta_per_delta = abs(greeks.theta) / abs_delta if abs_delta > 0 else 0

            theta_eff = ThetaEfficiency(
                strike=strike,
                expiration=expiration,
                option_type=opt_type,
                days_to_expiry=dte,
                price=market_price,
                delta=greeks.delta,
                theta=greeks.theta,
                delta_per_dollar=round(delta_per_dollar, 6),
                theta_per_delta=round(theta_per_delta, 4),
            )

            # Stock replacement cost: (LEAPS_price * 100) / (spot * 100) as %
            stock_replacement_cost = market_price / spot_price if spot_price > 0 else 0

            candidates.append(LeapsCandidate(
                strike=strike,
                expiration=expiration,
                option_type=opt_type,
                days_to_expiry=dte,
                market_price=round(market_price, 2),
                theo_price=greeks.price,
                delta=greeks.delta,
                gamma=greeks.gamma,
                theta=greeks.theta,
                vega=greeks.vega,
                iv=round(iv, 4),
                intrinsic=round(intrinsic, 2),
                extrinsic=round(extrinsic, 2),
                extrinsic_pct=round(extrinsic_pct, 4),
                theta_efficiency=theta_eff,
                stock_replacement_cost=round(stock_replacement_cost, 4),
                roll_recommendation=_roll_recommendation(dte, extrinsic_pct),
            ))

    # Sort by theta efficiency (best first = lowest theta per delta)
    candidates.sort(key=lambda c: c.theta_efficiency.theta_per_delta)
    return candidates


def find_leaps_expirations(expirations: list[str], today: date | None = None) -> list[str]:
    """Filter expirations to only those qualifying as LEAPS (> 1 year out)."""
    if today is None:
        today = date.today()
    result = []
    for exp in expirations:
        try:
            exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
        except ValueError:
            continue
        if (exp_date - today).days >= LEAPS_MIN_DTE:
            result.append(exp)
    return result
