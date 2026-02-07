import asyncio

import pandas as pd
import yfinance as yf


async def get_current_price(symbol: str) -> float | None:
    """Fetch the latest price for a symbol."""
    def _fetch():
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        return info.get("lastPrice")
    return await asyncio.to_thread(_fetch)


async def get_current_prices(symbols: list[str]) -> dict[str, float | None]:
    """Fetch latest prices for multiple symbols concurrently."""
    tasks = {s: get_current_price(s) for s in set(symbols)}
    results = {}
    for symbol, task in tasks.items():
        results[symbol] = await task
    return results


async def get_history(
    symbol: str, period: str = "1y", interval: str = "1d"
) -> pd.DataFrame:
    """Fetch historical OHLCV data as a pandas DataFrame."""
    def _fetch():
        ticker = yf.Ticker(symbol)
        return ticker.history(period=period, interval=interval)
    return await asyncio.to_thread(_fetch)


# ──────────────────────────────────────────────
# Options Chain
# ──────────────────────────────────────────────


async def get_option_expirations(symbol: str) -> list[str]:
    """Fetch available option expiration dates for a symbol."""
    def _fetch():
        ticker = yf.Ticker(symbol)
        return list(ticker.options)
    return await asyncio.to_thread(_fetch)


async def get_option_chain(symbol: str, expiration: str) -> dict[str, pd.DataFrame]:
    """Fetch the full option chain for a given expiration.

    Returns dict with keys 'calls' and 'puts', each a DataFrame with columns:
    contractSymbol, lastTradeDate, strike, lastPrice, bid, ask, change,
    percentChange, volume, openInterest, impliedVolatility, inTheMoney.
    """
    def _fetch():
        ticker = yf.Ticker(symbol)
        chain = ticker.option_chain(expiration)
        return {"calls": chain.calls, "puts": chain.puts}
    return await asyncio.to_thread(_fetch)


async def get_all_chains(symbol: str) -> dict[str, dict[str, pd.DataFrame]]:
    """Fetch option chains for all available expirations.

    Returns {expiration_str: {"calls": df, "puts": df}, ...}
    """
    expirations = await get_option_expirations(symbol)
    result = {}
    for exp in expirations:
        result[exp] = await get_option_chain(symbol, exp)
    return result
