"""
Rolling-window signal backtesting engine.

Replays compute_composite() over a historical date range,
measures forward returns at 1d/5d/21d horizons, and computes
accuracy metrics with no lookahead bias.
"""

import asyncio
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

from app.schemas.backtest import (
    BacktestResult,
    ConvictionBreakdown,
    DailySignal,
    HorizonMetrics,
)
from app.signals.composite import compute_composite


WARMUP_DAYS = 252
FORWARD_DAYS = 21
HORIZONS = {"1d": 1, "5d": 5, "21d": 21}


async def _fetch_history(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Fetch OHLCV data covering warmup + forward look periods."""
    fetch_start = start - timedelta(days=int(WARMUP_DAYS * 1.5))
    fetch_end = end + timedelta(days=int(FORWARD_DAYS * 1.5))

    def _fetch():
        ticker = yf.Ticker(symbol)
        return ticker.history(start=fetch_start.isoformat(), end=fetch_end.isoformat())

    return await asyncio.to_thread(_fetch)


def _compute_forward_return(
    df: pd.DataFrame, current_idx: int, horizon: int
) -> float | None:
    """Compute percentage return from current_idx to current_idx + horizon."""
    target_idx = current_idx + horizon
    if target_idx >= len(df):
        return None
    current_close = df["Close"].iloc[current_idx]
    future_close = df["Close"].iloc[target_idx]
    if current_close == 0:
        return None
    return round(float((future_close - current_close) / current_close * 100), 4)


def _compute_horizon_metrics(
    scores: list[float], forward_returns: list[float | None]
) -> HorizonMetrics:
    """Compute hit rate, avg signal return, profit factor for one horizon."""
    pairs = [
        (s, r) for s, r in zip(scores, forward_returns) if r is not None
    ]
    if not pairs:
        return HorizonMetrics(
            hit_rate=0.0, avg_signal_return=0.0, profit_factor=None,
            total_signals=0, wins=0, losses=0,
        )

    signal_returns = [s * r for s, r in pairs]
    wins = sum(1 for sr in signal_returns if sr > 0)
    losses = sum(1 for sr in signal_returns if sr < 0)
    total = len(pairs)

    # Hit rate: % where signal direction matched price direction
    hits = sum(
        1 for s, r in pairs
        if (s > 0 and r > 0) or (s < 0 and r < 0)
    )
    hit_rate = round(hits / total * 100, 2) if total else 0.0

    avg_sr = round(sum(signal_returns) / total, 4) if total else 0.0

    pos_sum = sum(sr for sr in signal_returns if sr > 0)
    neg_sum = abs(sum(sr for sr in signal_returns if sr < 0))
    profit_factor = round(pos_sum / neg_sum, 4) if neg_sum > 0 else None

    return HorizonMetrics(
        hit_rate=hit_rate,
        avg_signal_return=avg_sr,
        profit_factor=profit_factor,
        total_signals=total,
        wins=wins,
        losses=losses,
    )


def _compute_max_drawdown(cumulative: list[float]) -> float:
    """Max peak-to-trough drawdown on a cumulative return series."""
    if not cumulative:
        return 0.0
    peak = cumulative[0]
    max_dd = 0.0
    for val in cumulative:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd
    return round(max_dd, 4)


def _compute_conviction_breakdown(
    daily_signals: list[DailySignal],
) -> list[ConvictionBreakdown]:
    """Group daily signals by conviction and compute per-group metrics."""
    groups: dict[str, list[DailySignal]] = {}
    for ds in daily_signals:
        groups.setdefault(ds.conviction, []).append(ds)

    result = []
    for conv in ["low", "medium", "high"]:
        signals = groups.get(conv, [])
        if not signals:
            result.append(ConvictionBreakdown(
                conviction=conv, count=0,
                hit_rate_1d=0, hit_rate_5d=0, hit_rate_21d=0,
                avg_return_1d=0, avg_return_5d=0, avg_return_21d=0,
            ))
            continue

        count = len(signals)
        breakdown = {}
        for horizon in ["1d", "5d", "21d"]:
            fr_attr = f"forward_{horizon}"
            sr_attr = f"signal_return_{horizon}"
            valid = [
                (getattr(s, sr_attr), getattr(s, fr_attr), s.composite_score)
                for s in signals
                if getattr(s, fr_attr) is not None
            ]
            if valid:
                hits = sum(
                    1 for sr, fr, sc in valid
                    if (sc > 0 and fr > 0) or (sc < 0 and fr < 0)
                )
                breakdown[f"hit_rate_{horizon}"] = round(hits / len(valid) * 100, 2)
                breakdown[f"avg_return_{horizon}"] = round(
                    sum(sr for sr, _, _ in valid) / len(valid), 4
                )
            else:
                breakdown[f"hit_rate_{horizon}"] = 0.0
                breakdown[f"avg_return_{horizon}"] = 0.0

        result.append(ConvictionBreakdown(
            conviction=conv,
            count=count,
            **breakdown,
        ))

    return result


async def run_backtest(symbol: str, start: date, end: date) -> BacktestResult:
    """Run rolling-window signal backtest over [start, end].

    For each trading day:
    1. Slice OHLCV up to that day only (no lookahead)
    2. Run compute_composite() on the slice
    3. Measure actual forward returns at +1d, +5d, +21d
    4. Score signal correctness as score × forward_return
    """
    symbol = symbol.upper()
    df = await _fetch_history(symbol, start, end)

    if df.empty:
        raise ValueError(f"No data found for {symbol}")

    # Find trading days within [start, end]
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    # Handle timezone-aware index
    if df.index.tz is not None:
        start_ts = start_ts.tz_localize(df.index.tz)
        end_ts = end_ts.tz_localize(df.index.tz)

    trading_days = df.index[(df.index >= start_ts) & (df.index <= end_ts)]

    daily_signals: list[DailySignal] = []
    all_scores: list[float] = []
    all_forwards: dict[str, list[float | None]] = {"1d": [], "5d": [], "21d": []}

    for day in trading_days:
        # Slice: only data up to and including this day (no lookahead)
        df_slice = df.loc[:day]
        if len(df_slice) < 50:
            continue

        signal = compute_composite(symbol, df_slice)

        # Position of current day in full df for forward return calc
        day_pos = df.index.get_loc(day)

        forwards = {}
        signal_returns = {}
        for label, offset in HORIZONS.items():
            fr = _compute_forward_return(df, day_pos, offset)
            forwards[label] = fr
            signal_returns[label] = (
                round(signal.composite_score * fr, 4) if fr is not None else None
            )

        ds = DailySignal(
            date=day.strftime("%Y-%m-%d"),
            composite_score=signal.composite_score,
            direction=signal.direction,
            conviction=signal.conviction,
            confidence=signal.confidence,
            forward_1d=forwards["1d"],
            forward_5d=forwards["5d"],
            forward_21d=forwards["21d"],
            signal_return_1d=signal_returns["1d"],
            signal_return_5d=signal_returns["5d"],
            signal_return_21d=signal_returns["21d"],
        )
        daily_signals.append(ds)
        all_scores.append(signal.composite_score)
        for label in HORIZONS:
            all_forwards[label].append(forwards[label])

    # Aggregate metrics per horizon
    horizon_1d = _compute_horizon_metrics(all_scores, all_forwards["1d"])
    horizon_5d = _compute_horizon_metrics(all_scores, all_forwards["5d"])
    horizon_21d = _compute_horizon_metrics(all_scores, all_forwards["21d"])

    # Equity curves: cumulative signal returns per horizon
    equity_curve: list[dict] = []
    cum = {"1d": 0.0, "5d": 0.0, "21d": 0.0}
    for ds in daily_signals:
        for h in ["1d", "5d", "21d"]:
            sr = getattr(ds, f"signal_return_{h}")
            if sr is not None:
                cum[h] += sr
        equity_curve.append({
            "date": ds.date,
            "cum_1d": round(cum["1d"], 4),
            "cum_5d": round(cum["5d"], 4),
            "cum_21d": round(cum["21d"], 4),
        })

    # Max drawdowns
    max_dd_1d = _compute_max_drawdown([e["cum_1d"] for e in equity_curve])
    max_dd_5d = _compute_max_drawdown([e["cum_5d"] for e in equity_curve])
    max_dd_21d = _compute_max_drawdown([e["cum_21d"] for e in equity_curve])

    # Conviction breakdown
    conviction_breakdown = _compute_conviction_breakdown(daily_signals)

    return BacktestResult(
        symbol=symbol,
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        total_trading_days=len(daily_signals),
        horizon_1d=horizon_1d,
        horizon_5d=horizon_5d,
        horizon_21d=horizon_21d,
        conviction_breakdown=conviction_breakdown,
        daily_signals=daily_signals,
        equity_curve=equity_curve,
        max_drawdown_1d=max_dd_1d,
        max_drawdown_5d=max_dd_5d,
        max_drawdown_21d=max_dd_21d,
    )
