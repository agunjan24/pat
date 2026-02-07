"""
Black-Scholes option pricing and Greeks.

All functions assume:
- s: underlying price
- k: strike price
- t: time to expiration in years
- r: risk-free rate (annualized, e.g. 0.05 = 5%)
- sigma: implied volatility (annualized, e.g. 0.30 = 30%)
- option_type: "call" or "put"
"""

import math
from dataclasses import dataclass

from scipy.stats import norm


@dataclass
class GreeksResult:
    price: float
    delta: float
    gamma: float
    theta: float  # per day
    vega: float  # per 1% IV move
    rho: float  # per 1% rate move


def _d1(s: float, k: float, t: float, r: float, sigma: float) -> float:
    if t <= 0 or sigma <= 0:
        return 0.0
    return (math.log(s / k) + (r + sigma**2 / 2) * t) / (sigma * math.sqrt(t))


def _d2(s: float, k: float, t: float, r: float, sigma: float) -> float:
    return _d1(s, k, t, r, sigma) - sigma * math.sqrt(t)


def bs_price(
    s: float, k: float, t: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Black-Scholes option price."""
    if t <= 0:
        if option_type == "call":
            return max(s - k, 0.0)
        return max(k - s, 0.0)

    d1 = _d1(s, k, t, r, sigma)
    d2 = _d2(s, k, t, r, sigma)

    if option_type == "call":
        return s * norm.cdf(d1) - k * math.exp(-r * t) * norm.cdf(d2)
    else:
        return k * math.exp(-r * t) * norm.cdf(-d2) - s * norm.cdf(-d1)


def delta(
    s: float, k: float, t: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Option delta."""
    if t <= 0:
        if option_type == "call":
            return 1.0 if s > k else 0.0
        return -1.0 if s < k else 0.0

    d1 = _d1(s, k, t, r, sigma)
    if option_type == "call":
        return norm.cdf(d1)
    return norm.cdf(d1) - 1.0


def gamma(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """Option gamma (same for calls and puts)."""
    if t <= 0 or sigma <= 0:
        return 0.0
    d1 = _d1(s, k, t, r, sigma)
    return norm.pdf(d1) / (s * sigma * math.sqrt(t))


def theta(
    s: float, k: float, t: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Option theta (per calendar day)."""
    if t <= 0 or sigma <= 0:
        return 0.0

    d1 = _d1(s, k, t, r, sigma)
    d2 = _d2(s, k, t, r, sigma)

    common = -(s * norm.pdf(d1) * sigma) / (2 * math.sqrt(t))

    if option_type == "call":
        annual = common - r * k * math.exp(-r * t) * norm.cdf(d2)
    else:
        annual = common + r * k * math.exp(-r * t) * norm.cdf(-d2)

    return annual / 365.0


def vega(s: float, k: float, t: float, r: float, sigma: float) -> float:
    """Option vega (per 1% IV move). Same for calls and puts."""
    if t <= 0 or sigma <= 0:
        return 0.0
    d1 = _d1(s, k, t, r, sigma)
    return s * norm.pdf(d1) * math.sqrt(t) / 100.0


def rho(
    s: float, k: float, t: float, r: float, sigma: float, option_type: str = "call"
) -> float:
    """Option rho (per 1% rate move)."""
    if t <= 0:
        return 0.0
    d2 = _d2(s, k, t, r, sigma)
    if option_type == "call":
        return k * t * math.exp(-r * t) * norm.cdf(d2) / 100.0
    else:
        return -k * t * math.exp(-r * t) * norm.cdf(-d2) / 100.0


def compute_greeks(
    s: float, k: float, t: float, r: float, sigma: float, option_type: str = "call"
) -> GreeksResult:
    """Compute all Greeks for an option."""
    return GreeksResult(
        price=round(bs_price(s, k, t, r, sigma, option_type), 4),
        delta=round(delta(s, k, t, r, sigma, option_type), 4),
        gamma=round(gamma(s, k, t, r, sigma), 4),
        theta=round(theta(s, k, t, r, sigma, option_type), 4),
        vega=round(vega(s, k, t, r, sigma), 4),
        rho=round(rho(s, k, t, r, sigma, option_type), 4),
    )


def implied_volatility(
    market_price: float,
    s: float,
    k: float,
    t: float,
    r: float,
    option_type: str = "call",
    tol: float = 1e-6,
    max_iter: int = 100,
) -> float | None:
    """Solve for implied volatility using Newton-Raphson.

    Returns None if convergence fails.
    """
    if t <= 0:
        return None

    sigma = 0.3  # initial guess
    for _ in range(max_iter):
        price = bs_price(s, k, t, r, sigma, option_type)
        v = vega(s, k, t, r, sigma) * 100  # un-scale vega
        if v < 1e-12:
            break
        diff = price - market_price
        if abs(diff) < tol:
            return sigma
        sigma -= diff / v
        if sigma <= 0.001:
            sigma = 0.001
    return sigma if abs(bs_price(s, k, t, r, sigma, option_type) - market_price) < 0.01 else None
