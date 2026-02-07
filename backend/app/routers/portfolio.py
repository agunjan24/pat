from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.portfolio import Asset, Position, Transaction, TransactionType
from app.schemas.portfolio import (
    AssetCreate,
    AssetOut,
    PositionCreate,
    PositionDetail,
    PositionOut,
    TransactionCreate,
    TransactionOut,
)

router = APIRouter()


# ──────────────────────────────────────────────
# Assets
# ──────────────────────────────────────────────


@router.get("/assets", response_model=list[AssetOut])
async def list_assets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Asset).order_by(Asset.symbol))
    return result.scalars().all()


@router.get("/assets/{asset_id}", response_model=AssetOut)
async def get_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.post("/assets", response_model=AssetOut, status_code=201)
async def create_asset(asset: AssetCreate, db: AsyncSession = Depends(get_db)):
    db_asset = Asset(**asset.model_dump())
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset


@router.delete("/assets/{asset_id}", status_code=204)
async def delete_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    asset = await db.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    # Prevent deleting assets that have open positions
    result = await db.execute(
        select(Position).where(Position.asset_id == asset_id, Position.quantity != 0)
    )
    if result.scalars().first():
        raise HTTPException(status_code=409, detail="Asset has open positions")
    await db.delete(asset)
    await db.commit()


# ──────────────────────────────────────────────
# Positions
# ──────────────────────────────────────────────


@router.get("/positions", response_model=list[PositionOut])
async def list_positions(
    include_closed: bool = False,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Position).options(selectinload(Position.asset))
    if not include_closed:
        stmt = stmt.where(Position.quantity != 0)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/positions/{position_id}", response_model=PositionDetail)
async def get_position(position_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Position)
        .where(Position.id == position_id)
        .options(selectinload(Position.asset), selectinload(Position.transactions))
    )
    position = result.scalars().first()
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return position


@router.post("/positions", response_model=PositionDetail, status_code=201)
async def open_position(body: PositionCreate, db: AsyncSession = Depends(get_db)):
    """Open a new position with an initial buy transaction."""
    asset = await db.get(Asset, body.asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    position = Position(
        asset_id=body.asset_id,
        quantity=body.quantity,
        avg_cost=body.price,
    )
    db.add(position)
    await db.flush()

    txn = Transaction(
        position_id=position.id,
        transaction_type=TransactionType.BUY,
        quantity=body.quantity,
        price=body.price,
    )
    db.add(txn)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Position)
        .where(Position.id == position.id)
        .options(selectinload(Position.asset), selectinload(Position.transactions))
    )
    return result.scalars().first()


@router.delete("/positions/{position_id}", status_code=204)
async def delete_position(position_id: int, db: AsyncSession = Depends(get_db)):
    position = await db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    if position.quantity != 0:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete an open position. Close it first by selling all shares.",
        )
    await db.delete(position)
    await db.commit()


# ──────────────────────────────────────────────
# Transactions
# ──────────────────────────────────────────────


@router.get("/positions/{position_id}/transactions", response_model=list[TransactionOut])
async def list_transactions(position_id: int, db: AsyncSession = Depends(get_db)):
    position = await db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    result = await db.execute(
        select(Transaction)
        .where(Transaction.position_id == position_id)
        .order_by(Transaction.timestamp)
    )
    return result.scalars().all()


@router.post(
    "/positions/{position_id}/transactions",
    response_model=TransactionOut,
    status_code=201,
)
async def add_transaction(
    position_id: int,
    txn: TransactionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a transaction and update position quantity/avg_cost."""
    position = await db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    if txn.transaction_type == TransactionType.BUY:
        # Recalculate weighted average cost
        total_cost = position.quantity * position.avg_cost + txn.quantity * txn.price
        position.quantity += txn.quantity
        position.avg_cost = total_cost / position.quantity if position.quantity != 0 else 0.0

    elif txn.transaction_type == TransactionType.SELL:
        if txn.quantity > position.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot sell {txn.quantity} — only {position.quantity} held",
            )
        position.quantity -= txn.quantity
        # avg_cost stays the same on sells

    db_txn = Transaction(position_id=position_id, **txn.model_dump(exclude_none=True))
    db.add(db_txn)
    await db.commit()
    await db.refresh(db_txn)
    return db_txn
