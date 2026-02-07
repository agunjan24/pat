import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AssetType(str, enum.Enum):
    STOCK = "stock"
    OPTION = "option"
    LEAP = "leap"


class TransactionType(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    name: Mapped[str | None] = mapped_column(String(200))
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType))

    # Options/LEAPS fields
    strike: Mapped[float | None] = mapped_column(Float)
    expiration: Mapped[datetime | None] = mapped_column(DateTime)
    option_type: Mapped[str | None] = mapped_column(String(4))  # call/put

    positions: Mapped[list["Position"]] = relationship(back_populates="asset")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))
    quantity: Mapped[float] = mapped_column(Float)
    avg_cost: Mapped[float] = mapped_column(Float)
    opened_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    asset: Mapped["Asset"] = relationship(back_populates="positions")
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="position", cascade="all, delete-orphan"
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    position_id: Mapped[int] = mapped_column(ForeignKey("positions.id"))
    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType))
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    position: Mapped["Position"] = relationship(back_populates="transactions")
