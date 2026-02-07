# Signal Generation

## Philosophy

All signals are **risk-adjusted**. A raw buy/sell trigger is never surfaced without accompanying risk context — position size guidance, stop-loss levels, expected risk/reward ratio, and confidence scoring.

## Signal Categories

### 1. Technical Signals
- **Momentum** — Trend-following indicators (moving average crossovers, RSI, MACD)
- **Mean Reversion** — Oversold/overbought detection (Bollinger Bands, z-score)
- **Volatility Breakout** — Expansion/contraction regimes (ATR, squeeze indicators)
- **Volume Profile** — Accumulation/distribution, VWAP deviations

### 2. Fundamental Signals
- **Value** — P/E, P/B, EV/EBITDA relative to historical and sector norms
- **Quality** — ROE, debt ratios, earnings stability
- **Growth** — Revenue/earnings growth rates, estimate revisions

### 3. Options-Specific Signals
- **IV Rank / IV Percentile** — Current implied volatility vs. historical range
- **Skew Analysis** — Put/call skew for sentiment and tail risk
- **Term Structure** — Contango/backwardation across expiration dates
- **Greeks Optimization** — Optimal strike/expiry selection for target exposure

### 4. LEAPS-Specific Signals
- **Theta Efficiency** — Cost of time vs. delta exposure
- **Deep ITM vs. ATM** — Risk/reward tradeoffs for stock replacement strategies
- **Roll Timing** — When to roll forward based on remaining extrinsic value

## Risk Adjustment Framework

Every signal passes through a risk adjustment layer before output:

| Component | Description |
|-----------|-------------|
| Position Sizing | Kelly criterion or fractional Kelly based on edge estimate |
| Stop-Loss | Volatility-based stop (ATR multiple) or structural level |
| Risk/Reward | Minimum acceptable ratio (default: 2:1) |
| Correlation Check | Reject signals that increase portfolio concentration |
| Confidence Score | 0–100 composite based on signal agreement and data quality |

## Composite Scoring

Individual signals are combined into a composite score:

1. Each signal produces a normalized score (-1 to +1)
2. Signals are weighted by category and historical reliability
3. Risk adjustment modifies the raw composite
4. Final output: **direction** (buy/sell/hold), **conviction** (low/medium/high), **sizing** (% of portfolio)

## Backtesting

All signal strategies will be backtested with:
- Walk-forward analysis (no lookahead bias)
- Transaction cost modeling
- Slippage estimation
- Multiple market regime testing (bull, bear, sideways, high-vol)
