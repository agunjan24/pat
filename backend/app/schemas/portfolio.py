from datetime import datetime

from pydantic import BaseModel

from app.models.portfolio import AssetType, TransactionType


# --- Assets ---


class AssetCreate(BaseModel):
    symbol: str
    name: str | None = None
    asset_type: AssetType
    strike: float | None = None
    expiration: datetime | None = None
    option_type: str | None = None


class AssetOut(AssetCreate):
    id: int
    model_config = {"from_attributes": True}


# --- Transactions ---


class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    quantity: float
    price: float
    timestamp: datetime | None = None


class TransactionOut(BaseModel):
    id: int
    position_id: int
    transaction_type: TransactionType
    quantity: float
    price: float
    timestamp: datetime
    model_config = {"from_attributes": True}


# --- Positions ---


class PositionCreate(BaseModel):
    asset_id: int
    quantity: float
    price: float


class PositionOut(BaseModel):
    id: int
    asset: AssetOut
    quantity: float
    avg_cost: float
    opened_at: datetime
    model_config = {"from_attributes": True}


class PositionDetail(PositionOut):
    transactions: list[TransactionOut] = []
    market_value: float | None = None
    unrealized_pnl: float | None = None
