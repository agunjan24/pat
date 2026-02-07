import numpy as np
import pandas as pd


def daily_returns(prices: pd.Series) -> pd.Series:
    """Calculate daily returns from a price series."""
    return prices.pct_change().dropna()


def sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods: int = 252) -> float:
    """Annualized Sharpe ratio."""
    excess = returns - risk_free_rate / periods
    if excess.std() == 0:
        return 0.0
    return float(np.sqrt(periods) * excess.mean() / excess.std())


def max_drawdown(prices: pd.Series) -> float:
    """Maximum drawdown from peak."""
    cumulative = prices / prices.iloc[0]
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return float(drawdown.min())


def cagr(prices: pd.Series, periods_per_year: int = 252) -> float:
    """Compound annual growth rate."""
    total_return = prices.iloc[-1] / prices.iloc[0]
    n_periods = len(prices) - 1  # N prices = N-1 periods
    if n_periods <= 0:
        return 0.0
    return float(total_return ** (periods_per_year / n_periods) - 1)
