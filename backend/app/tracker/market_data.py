import asyncio
from functools import lru_cache

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
