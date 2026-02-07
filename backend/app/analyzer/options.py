"""
Options analytics: IV rank/percentile, skew, term structure.
"""

from dataclasses import dataclass
from datetime import datetime, date

import numpy as np
import pandas as pd

from app.analyzer.greeks import compute_greeks


@dataclass
class IVMetrics:
    current_iv: float  # current ATM implied vol
    iv_rank: float  # 0–100, where current IV sits in 1y range
    iv_percentile: float  # 0–100, % of days IV was lower
    iv_high: float
    iv_low: float


@dataclass
class SkewPoint:
    strike: float
    call_iv: float | None
    put_iv: float | None
    delta: float | None


@dataclass
class SkewMetrics:
    skew_ratio: float  # OTM put IV / OTM call IV (>1 = put premium)
    skew_points: list[SkewPoint]


@dataclass
class TermStructurePoint:
    expiration: str
    days_to_expiry: int
    atm_iv: float


def compute_iv_metrics(
    chain_iv_history: pd.Series,
    current_iv: float,
) -> IVMetrics:
    """Compute IV rank and percentile from historical IV series.

    Args:
        chain_iv_history: Series of daily ATM IV values (e.g. 252 trading days).
        current_iv: Current ATM implied volatility.
    """
    if chain_iv_history.empty:
        return IVMetrics(
            current_iv=current_iv, iv_rank=50, iv_percentile=50,
            iv_high=current_iv, iv_low=current_iv,
        )

    iv_high = float(chain_iv_history.max())
    iv_low = float(chain_iv_history.min())
    iv_range = iv_high - iv_low

    if iv_range == 0:
        iv_rank = 50.0
    else:
        iv_rank = (current_iv - iv_low) / iv_range * 100

    iv_percentile = float((chain_iv_history < current_iv).sum() / len(chain_iv_history) * 100)

    return IVMetrics(
        current_iv=round(current_iv, 4),
        iv_rank=round(max(0, min(100, iv_rank)), 1),
        iv_percentile=round(max(0, min(100, iv_percentile)), 1),
        iv_high=round(iv_high, 4),
        iv_low=round(iv_low, 4),
    )


def compute_skew(
    calls_df: pd.DataFrame,
    puts_df: pd.DataFrame,
    spot_price: float,
) -> SkewMetrics:
    """Compute put/call IV skew from an options chain.

    Looks at strikes within ±20% of spot price.
    """
    lower = spot_price * 0.80
    upper = spot_price * 1.20

    calls = calls_df[(calls_df["strike"] >= lower) & (calls_df["strike"] <= upper)].copy()
    puts = puts_df[(puts_df["strike"] >= lower) & (puts_df["strike"] <= upper)].copy()

    # Merge on strike
    merged = pd.merge(
        calls[["strike", "impliedVolatility"]].rename(columns={"impliedVolatility": "call_iv"}),
        puts[["strike", "impliedVolatility"]].rename(columns={"impliedVolatility": "put_iv"}),
        on="strike",
        how="outer",
    ).sort_values("strike")

    points = []
    for _, row in merged.iterrows():
        points.append(SkewPoint(
            strike=row["strike"],
            call_iv=round(row["call_iv"], 4) if pd.notna(row.get("call_iv")) else None,
            put_iv=round(row["put_iv"], 4) if pd.notna(row.get("put_iv")) else None,
            delta=None,
        ))

    # Skew ratio: avg OTM put IV / avg OTM call IV
    otm_puts = puts[puts["strike"] < spot_price]["impliedVolatility"]
    otm_calls = calls[calls["strike"] > spot_price]["impliedVolatility"]

    if otm_calls.mean() > 0 and not otm_puts.empty and not otm_calls.empty:
        skew_ratio = float(otm_puts.mean() / otm_calls.mean())
    else:
        skew_ratio = 1.0

    return SkewMetrics(
        skew_ratio=round(skew_ratio, 4),
        skew_points=points,
    )


def compute_term_structure(
    chains: dict[str, dict[str, pd.DataFrame]],
    spot_price: float,
    today: date | None = None,
) -> list[TermStructurePoint]:
    """Compute ATM implied volatility across expiration dates.

    Args:
        chains: {expiration_str: {"calls": df, "puts": df}, ...}
        spot_price: Current underlying price.
        today: Reference date (defaults to today).
    """
    if today is None:
        today = date.today()

    points = []
    for exp_str, chain_data in sorted(chains.items()):
        try:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        except ValueError:
            continue

        dte = (exp_date - today).days
        if dte <= 0:
            continue

        calls = chain_data["calls"]
        if calls.empty:
            continue

        # Find ATM strike (closest to spot)
        atm_idx = (calls["strike"] - spot_price).abs().idxmin()
        atm_iv = calls.loc[atm_idx, "impliedVolatility"]

        if pd.notna(atm_iv) and atm_iv > 0:
            points.append(TermStructurePoint(
                expiration=exp_str,
                days_to_expiry=dte,
                atm_iv=round(float(atm_iv), 4),
            ))

    return points


def find_atm_iv(chain_data: dict[str, pd.DataFrame], spot_price: float) -> float | None:
    """Find the ATM implied volatility from a single expiration chain."""
    calls = chain_data.get("calls")
    if calls is None or calls.empty:
        return None
    atm_idx = (calls["strike"] - spot_price).abs().idxmin()
    iv = calls.loc[atm_idx, "impliedVolatility"]
    return float(iv) if pd.notna(iv) and iv > 0 else None
