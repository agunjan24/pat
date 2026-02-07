from fastapi import APIRouter, HTTPException, Query

from app.analyzer.options import (
    compute_iv_metrics,
    compute_skew,
    compute_term_structure,
    find_atm_iv,
)
from app.analyzer.leaps import analyze_leaps_chain, find_leaps_expirations
from app.schemas.options import (
    IVMetricsOut,
    LeapsAnalysisOut,
    LeapsCandidateOut,
    OptionsAnalysisOut,
    SkewOut,
    SkewPointOut,
    TermStructurePointOut,
    ThetaEfficiencyOut,
)
from app.tracker.market_data import (
    get_all_chains,
    get_current_price,
    get_option_chain,
    get_option_expirations,
    get_history,
)

router = APIRouter()


@router.get("/overview", response_model=OptionsAnalysisOut)
async def options_overview(
    symbol: str = Query(..., description="Ticker symbol"),
):
    """Options analysis: IV rank/percentile, skew, and term structure."""
    spot = await get_current_price(symbol)
    if spot is None:
        raise HTTPException(status_code=404, detail=f"Cannot fetch price for {symbol}")

    expirations = await get_option_expirations(symbol)
    if not expirations:
        raise HTTPException(status_code=404, detail=f"No options available for {symbol}")

    # Get nearest expiration chain for skew and current IV
    nearest_chain = await get_option_chain(symbol, expirations[0])
    current_iv = find_atm_iv(nearest_chain, spot)
    if current_iv is None:
        current_iv = 0.3  # fallback

    # Approximate IV history from historical volatility
    hist = await get_history(symbol, period="1y", interval="1d")
    if not hist.empty:
        returns = hist["Close"].pct_change().dropna()
        rolling_vol = returns.rolling(window=20).std() * (252 ** 0.5)
        iv_history = rolling_vol.dropna()
    else:
        import pandas as pd
        iv_history = pd.Series([current_iv])

    iv_metrics = compute_iv_metrics(iv_history, current_iv)

    # Skew from nearest expiration
    skew = compute_skew(nearest_chain["calls"], nearest_chain["puts"], spot)

    # Term structure — fetch a subset of expirations (first, middle, last few)
    sample_exps = _sample_expirations(expirations, max_count=8)
    chains_for_ts = {}
    for exp in sample_exps:
        chains_for_ts[exp] = await get_option_chain(symbol, exp)
    term_structure = compute_term_structure(chains_for_ts, spot)

    return OptionsAnalysisOut(
        symbol=symbol.upper(),
        spot_price=round(spot, 2),
        expirations=expirations,
        iv_metrics=IVMetricsOut(
            current_iv=iv_metrics.current_iv,
            iv_rank=iv_metrics.iv_rank,
            iv_percentile=iv_metrics.iv_percentile,
            iv_high=iv_metrics.iv_high,
            iv_low=iv_metrics.iv_low,
        ),
        skew=SkewOut(
            skew_ratio=skew.skew_ratio,
            points=[
                SkewPointOut(strike=p.strike, call_iv=p.call_iv, put_iv=p.put_iv)
                for p in skew.skew_points
            ],
        ),
        term_structure=[
            TermStructurePointOut(
                expiration=p.expiration,
                days_to_expiry=p.days_to_expiry,
                atm_iv=p.atm_iv,
            )
            for p in term_structure
        ],
    )


@router.get("/leaps", response_model=LeapsAnalysisOut)
async def leaps_analysis(
    symbol: str = Query(..., description="Ticker symbol"),
):
    """LEAPS analysis: theta efficiency, roll timing, stock replacement candidates."""
    spot = await get_current_price(symbol)
    if spot is None:
        raise HTTPException(status_code=404, detail=f"Cannot fetch price for {symbol}")

    expirations = await get_option_expirations(symbol)
    leaps_exps = find_leaps_expirations(expirations)

    if not leaps_exps:
        raise HTTPException(
            status_code=404,
            detail=f"No LEAPS expirations (>1 year) available for {symbol}",
        )

    all_candidates = []
    for exp in leaps_exps:
        chain = await get_option_chain(symbol, exp)
        candidates = analyze_leaps_chain(
            chain["calls"], chain["puts"], exp, spot,
        )
        all_candidates.extend(candidates)

    return LeapsAnalysisOut(
        symbol=symbol.upper(),
        spot_price=round(spot, 2),
        leaps_expirations=leaps_exps,
        candidates=[
            LeapsCandidateOut(
                strike=c.strike,
                expiration=c.expiration,
                option_type=c.option_type,
                days_to_expiry=c.days_to_expiry,
                market_price=c.market_price,
                delta=c.delta,
                theta=c.theta,
                vega=c.vega,
                iv=c.iv,
                intrinsic=c.intrinsic,
                extrinsic=c.extrinsic,
                extrinsic_pct=c.extrinsic_pct,
                theta_efficiency=ThetaEfficiencyOut(
                    delta_per_dollar=c.theta_efficiency.delta_per_dollar,
                    theta_per_delta=c.theta_efficiency.theta_per_delta,
                ),
                stock_replacement_cost=c.stock_replacement_cost,
                roll_recommendation=c.roll_recommendation,
            )
            for c in all_candidates
        ],
    )


def _sample_expirations(expirations: list[str], max_count: int = 8) -> list[str]:
    """Sample expirations evenly for term structure."""
    if len(expirations) <= max_count:
        return expirations
    step = len(expirations) / max_count
    indices = [int(i * step) for i in range(max_count)]
    return [expirations[i] for i in indices]
