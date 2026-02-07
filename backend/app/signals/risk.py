"""
Risk adjustment layer.

Provides stop-loss levels, position sizing, and risk/reward context
for any signal output.
"""

import pandas as pd

from app.signals.technical import atr


def atr_stop_loss(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    direction: str,
    multiplier: float = 2.0,
    period: int = 14,
) -> float | None:
    """ATR-based stop-loss level.

    For buy: stop = current_price - multiplier * ATR
    For sell: stop = current_price + multiplier * ATR
    """
    atr_val = atr(high, low, close, period)
    if atr_val.isna().iloc[-1]:
        return None
    current = close.iloc[-1]
    atr_now = atr_val.iloc[-1]
    if direction == "buy":
        return round(current - multiplier * atr_now, 2)
    elif direction == "sell":
        return round(current + multiplier * atr_now, 2)
    return None


def kelly_fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
    """Kelly criterion for optimal bet size.

    Returns fraction of portfolio to allocate (0–1).
    Uses half-Kelly for conservatism.
    """
    if avg_loss == 0:
        return 0.0
    b = avg_win / avg_loss  # win/loss ratio
    q = 1 - win_rate
    kelly = (win_rate * b - q) / b
    # Half-Kelly for safety
    half_kelly = kelly / 2
    return max(0.0, min(0.25, half_kelly))  # cap at 25%


def position_size_from_risk(
    portfolio_value: float,
    entry_price: float,
    stop_price: float,
    risk_pct: float = 0.02,
) -> float:
    """Position size based on fixed risk per trade.

    Args:
        portfolio_value: Total portfolio value.
        entry_price: Planned entry price.
        stop_price: Stop-loss price.
        risk_pct: Max fraction of portfolio to risk (default 2%).

    Returns:
        Number of shares/contracts to buy.
    """
    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share == 0:
        return 0.0
    risk_amount = portfolio_value * risk_pct
    return risk_amount / risk_per_share


def risk_reward_ratio(
    entry: float, stop: float, target: float
) -> float | None:
    """Risk/reward ratio. Returns None if risk is zero."""
    risk = abs(entry - stop)
    reward = abs(target - entry)
    if risk == 0:
        return None
    return round(reward / risk, 2)


def compute_risk_context(
    df: pd.DataFrame,
    direction: str,
    composite_score: float,
    portfolio_value: float = 100_000.0,
) -> dict:
    """Compute full risk context for a signal.

    Returns dict with stop_loss, target, risk_reward, position_size, risk_pct.
    """
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    current_price = close.iloc[-1]

    stop = atr_stop_loss(high, low, close, direction)
    if stop is None:
        return {
            "stop_loss": None,
            "target_price": None,
            "risk_reward": None,
            "position_size": 0,
            "position_pct": 0.0,
        }

    # Target = 2x the risk distance (minimum 2:1 R/R)
    risk_distance = abs(current_price - stop)
    if direction == "buy":
        target = round(current_price + 2 * risk_distance, 2)
    elif direction == "sell":
        target = round(current_price - 2 * risk_distance, 2)
    else:
        target = current_price

    rr = risk_reward_ratio(current_price, stop, target)

    # Position size: scale risk% by conviction (0.5%–2%)
    conviction_scale = min(abs(composite_score), 1.0)
    risk_pct = 0.005 + conviction_scale * 0.015  # 0.5% to 2%
    shares = position_size_from_risk(portfolio_value, current_price, stop, risk_pct)

    position_value = shares * current_price
    position_pct = (position_value / portfolio_value * 100) if portfolio_value else 0.0

    return {
        "stop_loss": stop,
        "target_price": target,
        "risk_reward": rr,
        "position_size": round(shares, 2),
        "position_pct": round(position_pct, 2),
    }
