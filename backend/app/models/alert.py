import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AlertType(str, enum.Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    IV_RANK_ABOVE = "iv_rank_above"
    IV_RANK_BELOW = "iv_rank_below"
    SIGNAL_BUY = "signal_buy"
    SIGNAL_SELL = "signal_sell"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType))
    threshold: Mapped[float | None] = mapped_column(Float)
    message: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
