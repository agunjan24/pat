import pandas as pd

from app.analyzer.metrics import cagr, daily_returns, max_drawdown, sharpe_ratio


def test_daily_returns():
    prices = pd.Series([100, 110, 105, 115])
    returns = daily_returns(prices)
    assert len(returns) == 3
    assert abs(returns.iloc[0] - 0.1) < 1e-9


def test_sharpe_ratio():
    returns = pd.Series([0.01, 0.02, -0.005, 0.015, 0.01])
    result = sharpe_ratio(returns)
    assert isinstance(result, float)


def test_max_drawdown():
    prices = pd.Series([100, 120, 90, 110])
    dd = max_drawdown(prices)
    assert dd < 0
    assert abs(dd - (-0.25)) < 1e-9


def test_cagr():
    # 100 → 110 over 1 period, 1 period/year → 10% CAGR
    prices = pd.Series([100, 110])
    result = cagr(prices, periods_per_year=1)
    assert abs(result - 0.1) < 0.01
