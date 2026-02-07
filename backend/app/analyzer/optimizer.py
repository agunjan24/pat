"""
Portfolio optimization: efficient frontier and risk parity.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FrontierPoint:
    expected_return: float
    volatility: float
    sharpe_ratio: float
    weights: dict[str, float]


@dataclass
class OptimizationResult:
    symbols: list[str]
    min_variance: FrontierPoint
    max_sharpe: FrontierPoint
    risk_parity: FrontierPoint
    frontier: list[FrontierPoint]


def _annualized_stats(
    weights: np.ndarray, mean_returns: np.ndarray, cov_matrix: np.ndarray
) -> tuple[float, float]:
    """Compute annualized return and volatility for given weights."""
    port_return = float(np.sum(mean_returns * weights) * 252)
    port_vol = float(np.sqrt(np.dot(weights.T, np.dot(cov_matrix * 252, weights))))
    return port_return, port_vol


def _random_portfolios(
    n_portfolios: int,
    n_assets: int,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
) -> list[tuple[float, float, float, np.ndarray]]:
    """Generate random portfolio allocations."""
    results = []
    for _ in range(n_portfolios):
        w = np.random.random(n_assets)
        w /= w.sum()
        ret, vol = _annualized_stats(w, mean_returns, cov_matrix)
        sharpe = (ret - risk_free_rate) / vol if vol > 0 else 0
        results.append((ret, vol, sharpe, w))
    return results


def compute_risk_parity(cov_matrix: np.ndarray) -> np.ndarray:
    """Compute risk parity weights (equal risk contribution).

    Uses inverse-volatility as an approximation.
    """
    vols = np.sqrt(np.diag(cov_matrix))
    inv_vols = 1.0 / vols
    weights = inv_vols / inv_vols.sum()
    return weights


def compute_efficient_frontier(
    returns_df: pd.DataFrame,
    risk_free_rate: float = 0.045,
    n_portfolios: int = 5000,
    n_frontier_points: int = 30,
) -> OptimizationResult:
    """Compute efficient frontier, max Sharpe, min variance, and risk parity.

    Args:
        returns_df: DataFrame of daily returns with columns = symbols.
        risk_free_rate: Annual risk-free rate.
        n_portfolios: Number of random portfolios to simulate.
        n_frontier_points: Number of points on the efficient frontier curve.
    """
    symbols = list(returns_df.columns)
    n_assets = len(symbols)
    mean_returns = returns_df.mean().values
    cov_matrix = returns_df.cov().values

    def _make_point(weights: np.ndarray) -> FrontierPoint:
        ret, vol = _annualized_stats(weights, mean_returns, cov_matrix)
        sharpe = (ret - risk_free_rate) / vol if vol > 0 else 0
        w_dict = {s: round(float(w), 4) for s, w in zip(symbols, weights)}
        return FrontierPoint(
            expected_return=round(ret, 4),
            volatility=round(vol, 4),
            sharpe_ratio=round(sharpe, 4),
            weights=w_dict,
        )

    # Generate random portfolios
    portfolios = _random_portfolios(
        n_portfolios, n_assets, mean_returns, cov_matrix, risk_free_rate
    )

    # Find max Sharpe and min variance
    max_sharpe_idx = max(range(len(portfolios)), key=lambda i: portfolios[i][2])
    min_vol_idx = min(range(len(portfolios)), key=lambda i: portfolios[i][1])

    max_sharpe = _make_point(portfolios[max_sharpe_idx][3])
    min_variance = _make_point(portfolios[min_vol_idx][3])

    # Risk parity
    rp_weights = compute_risk_parity(cov_matrix)
    risk_parity = _make_point(rp_weights)

    # Build frontier curve from random portfolios
    # Sort by volatility and take the upper envelope
    sorted_ports = sorted(portfolios, key=lambda p: p[1])
    step = max(1, len(sorted_ports) // n_frontier_points)
    frontier = []
    best_return = -np.inf
    for i in range(0, len(sorted_ports), step):
        ret, vol, sharpe, w = sorted_ports[i]
        if ret >= best_return:  # upper envelope
            best_return = ret
            frontier.append(_make_point(w))

    return OptimizationResult(
        symbols=symbols,
        min_variance=min_variance,
        max_sharpe=max_sharpe,
        risk_parity=risk_parity,
        frontier=frontier,
    )
