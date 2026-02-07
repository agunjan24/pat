# Architecture

## High-Level Design

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         Dashboards / Charts / Controls           │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                  API Layer                        │
└───┬──────────┬──────────┬──────────┬────────────┘
    │          │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼────┐ ┌───▼────┐
│Tracker│ │Visual-│ │Analyzer│ │Signals │
│       │ │izer   │ │        │ │        │
└───┬───┘ └───────┘ └───┬────┘ └───┬────┘
    │                    │          │
┌───▼────────────────────▼──────────▼─────────────┐
│               Data Layer                         │
│     Market Data / Portfolio Store / Cache         │
└─────────────────────────────────────────────────┘
```

## Module Responsibilities

### Tracker
- Portfolio ingestion (manual entry, CSV/broker import)
- Position management (open, close, adjust)
- Real-time and historical P&L calculation
- Transaction history and audit trail

### Visualizer
- Portfolio allocation (treemaps, pie/donut charts)
- Performance over time (line charts, benchmarks)
- Risk dashboards (VaR, drawdown, Sharpe heatmaps)
- Options-specific views (payoff diagrams, Greeks surfaces)

### Analyzer
- Return metrics: CAGR, Sharpe, Sortino, Calmar ratios
- Risk metrics: VaR, CVaR, max drawdown, beta
- Correlation and covariance analysis
- Performance attribution (sector, factor, asset class)
- Options Greeks calculation and aggregation

### Signals
- Technical indicators (momentum, mean-reversion, volatility breakout)
- Fundamental scoring (value, quality, growth factors)
- Options-specific signals (IV rank/percentile, skew, term structure)
- Risk-adjusted position sizing (Kelly criterion, risk parity)
- Composite scoring with confidence levels

## Data Flow

1. **Ingest** — Market data and portfolio positions enter through the Tracker
2. **Store** — Normalized data persisted in the Data Layer
3. **Compute** — Analyzer and Signals modules process stored data
4. **Present** — Visualizer renders computed results to the frontend

## Key Design Principles

- **Modularity** — Each module is independently testable and deployable
- **Separation of concerns** — Data, logic, and presentation layers are distinct
- **Extensibility** — New signal algorithms and visualizations plug in without core changes
- **Risk-first** — Every signal and recommendation includes risk context
