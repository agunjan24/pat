import numpy as np
import pandas as pd


# ──────────────────────────────────────────────
# Moving Averages
# ──────────────────────────────────────────────


def sma(prices: pd.Series, window: int) -> pd.Series:
    """Simple moving average."""
    return prices.rolling(window=window).mean()


def ema(prices: pd.Series, span: int) -> pd.Series:
    """Exponential moving average."""
    return prices.ewm(span=span, adjust=False).mean()


# ──────────────────────────────────────────────
# Momentum
# ──────────────────────────────────────────────


def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (0–100)."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """MACD: (macd_line, signal_line, histogram)."""
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def rate_of_change(prices: pd.Series, period: int = 10) -> pd.Series:
    """Price rate of change (%)."""
    return prices.pct_change(periods=period) * 100


# ──────────────────────────────────────────────
# Volatility
# ──────────────────────────────────────────────


def bollinger_bands(
    prices: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Bollinger Bands: (upper, middle, lower)."""
    middle = sma(prices, window)
    std = prices.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(window=period).mean()


def bollinger_pct_b(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
    """%B: where price sits within Bollinger Bands (0 = lower, 1 = upper)."""
    upper, middle, lower = bollinger_bands(prices, window, num_std)
    return (prices - lower) / (upper - lower)


# ──────────────────────────────────────────────
# Volume
# ──────────────────────────────────────────────


def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume-Weighted Average Price (cumulative intraday approximation)."""
    typical_price = (high + low + close) / 3
    cum_tp_vol = (typical_price * volume).cumsum()
    cum_vol = volume.cumsum()
    return cum_tp_vol / cum_vol


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume."""
    direction = np.sign(close.diff())
    return (volume * direction).fillna(0).cumsum()


# ──────────────────────────────────────────────
# Trend Strength
# ──────────────────────────────────────────────


def adx(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Average Directional Index: (ADX, +DI, -DI).

    ADX measures trend strength on a 0-100 scale.
    >25 = trending, <20 = ranging.
    +DI / -DI indicate trend direction.
    """
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    prev_close = close.shift(1)

    # Directional movement
    plus_dm = high - prev_high
    minus_dm = prev_low - low
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    # True range
    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    # Smoothed averages (Wilder's smoothing)
    atr_smooth = tr.rolling(window=period).sum()
    plus_dm_smooth = plus_dm.rolling(window=period).sum()
    minus_dm_smooth = minus_dm.rolling(window=period).sum()

    # +DI and -DI
    plus_di = 100 * plus_dm_smooth / atr_smooth
    minus_di = 100 * minus_dm_smooth / atr_smooth

    # DX and ADX
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    adx_series = dx.rolling(window=period).mean()

    return adx_series, plus_di, minus_di


# ──────────────────────────────────────────────
# Stochastic Oscillator
# ──────────────────────────────────────────────


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """Stochastic Oscillator: (%K, %D).

    %K = (close - lowest low) / (highest high - lowest low) * 100
    %D = SMA of %K
    Returns 0-100 scale. <20 = oversold, >80 = overbought.
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    denom = highest_high - lowest_low
    pct_k = 100 * (close - lowest_low) / denom.replace(0, np.nan)
    pct_d = pct_k.rolling(window=d_period).mean()
    return pct_k, pct_d


# ──────────────────────────────────────────────
# Accumulation / Distribution
# ──────────────────────────────────────────────


def accumulation_distribution(
    high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series
) -> pd.Series:
    """Accumulation/Distribution Line.

    Money Flow Multiplier = ((close - low) - (high - close)) / (high - low)
    Money Flow Volume = MFM * volume
    A/D Line = cumulative sum of MFV.
    """
    denom = high - low
    mfm = ((close - low) - (high - close)) / denom.replace(0, np.nan)
    mfv = mfm * volume
    return mfv.fillna(0).cumsum()


def chaikin_money_flow(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    period: int = 20,
) -> pd.Series:
    """Chaikin Money Flow: bounded [-1, +1].

    Sum of Money Flow Volume over period / sum of volume over period.
    """
    denom = high - low
    mfm = ((close - low) - (high - close)) / denom.replace(0, np.nan)
    mfv = mfm * volume
    cmf = mfv.rolling(window=period).sum() / volume.rolling(window=period).sum()
    return cmf


# ──────────────────────────────────────────────
# Options Sentiment
# ──────────────────────────────────────────────


def put_call_volume_ratio(calls_df: pd.DataFrame, puts_df: pd.DataFrame) -> float:
    """Put/Call volume ratio from option chain DataFrames.

    Returns total put volume / total call volume.
    A single float value (computed from a snapshot, not a series).
    """
    call_vol = calls_df["volume"].sum() if "volume" in calls_df.columns else 0
    put_vol = puts_df["volume"].sum() if "volume" in puts_df.columns else 0
    if call_vol == 0:
        return float("nan")
    return float(put_vol / call_vol)
