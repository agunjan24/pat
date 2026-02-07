from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import alerts, analyzer, import_export, options, paper_trading, portfolio, signals


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PAT", version="0.1.0", description="Portfolio Analytic Tool", lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(analyzer.router, prefix="/api/analyze", tags=["analyzer"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(options.router, prefix="/api/options", tags=["options"])
app.include_router(import_export.router, prefix="/api/portfolio", tags=["import"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(paper_trading.router, prefix="/api/paper", tags=["paper-trading"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
