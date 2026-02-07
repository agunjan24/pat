# PAT — Portfolio Analytic Tool

## Project Summary
PAT is a portfolio analytics platform for visualizing, analyzing, and tracking investments (stocks, options, LEAPS) with algorithmic signal generation for risk-adjusted buy/sell decisions.

## Tech Stack
- **Backend**: Python 3.11+ / FastAPI / SQLAlchemy (async) / SQLite
- **Frontend**: React + TypeScript / Vite / Recharts / React Router
- **Data**: yfinance for market data, pandas/numpy for computation

## Project Structure
```
pat/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint
│   │   ├── config.py          # Settings (env-based)
│   │   ├── database.py        # SQLAlchemy async engine
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response schemas
│   │   ├── routers/           # API route handlers
│   │   ├── tracker/           # Market data ingestion
│   │   ├── analyzer/          # Risk/return metrics
│   │   └── signals/           # Technical signal algorithms
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios HTTP client
│   │   ├── types/             # TypeScript interfaces
│   │   ├── pages/             # Route-level components
│   │   └── App.tsx            # Root with routing
│   └── package.json
└── docs/
    ├── architecture.md
    ├── signals.md
    └── roadmap.md
```

## Key Commands
- **Backend**: `cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload`
- **Frontend**: `cd frontend && npm install && npm run dev`
- **Tests**: `cd backend && pytest`

## API Routes
- `GET /api/health` — Health check
- **Assets**: `GET /api/portfolio/assets` | `GET .../assets/{id}` | `POST .../assets` | `DELETE .../assets/{id}`
- **Positions**: `GET /api/portfolio/positions?include_closed=bool` | `GET .../positions/{id}` (detail + txns) | `POST .../positions` (open) | `DELETE .../positions/{id}` (closed only)
- **Transactions**: `GET /api/portfolio/positions/{id}/transactions` | `POST .../positions/{id}/transactions` (updates qty/avg_cost)
- `GET /api/analyze/summary` — Portfolio analytics (placeholder)
- `GET /api/signals/scan` — Signal scanner (placeholder)

## Key Business Logic
- **Open position**: Creates position + initial buy transaction atomically
- **Buy transaction**: Recalculates weighted avg_cost = (old_qty * old_avg + new_qty * price) / total_qty
- **Sell transaction**: Reduces quantity, avg_cost unchanged. Rejects if sell_qty > held_qty
- **Closed positions**: quantity == 0, hidden from default list, deletable
- **Asset deletion**: Blocked if asset has open positions (409)

## Key Documentation
- `docs/architecture.md` — System architecture and module design
- `docs/signals.md` — Signal generation philosophy and framework
- `docs/roadmap.md` — Phased development plan

## Design Principles
- Risk-first: every output includes risk context
- Modular: independent, testable components
- No lookahead bias in backtesting
- All signals are risk-adjusted (position sizing, stops, confidence)
