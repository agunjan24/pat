import yfinance as yf


async def get_current_price(symbol: str) -> float | None:
    """Fetch the latest price for a symbol."""
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info
    return info.get("lastPrice")


async def get_history(symbol: str, period: str = "1y", interval: str = "1d"):
    """Fetch historical OHLCV data as a pandas DataFrame."""
    ticker = yf.Ticker(symbol)
    return ticker.history(period=period, interval=interval)
