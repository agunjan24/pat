from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.portfolio import Asset, AssetType, Position, Transaction, TransactionType
from app.schemas.import_export import ImportResponse, ImportRowOut
from app.tracker.csv_import import parse_csv

router = APIRouter()


@router.post("/import", response_model=ImportResponse, status_code=201)
async def import_csv(file: UploadFile, db: AsyncSession = Depends(get_db)):
    """Import positions from a CSV file.

    Expected columns: symbol, quantity, price
    Optional: asset_type, date, option_type, strike, expiration
    """
    content = (await file.read()).decode("utf-8-sig")
    result = parse_csv(content)

    created: list[ImportRowOut] = []

    for row in result.rows:
        # Find or create asset
        stmt = select(Asset).where(
            Asset.symbol == row.symbol,
            Asset.asset_type == AssetType(row.asset_type),
        )
        if row.strike is not None:
            stmt = stmt.where(Asset.strike == row.strike)
        if row.expiration is not None:
            stmt = stmt.where(Asset.expiration == row.expiration)

        existing = (await db.execute(stmt)).scalars().first()

        if existing:
            asset = existing
        else:
            asset = Asset(
                symbol=row.symbol,
                asset_type=AssetType(row.asset_type),
                strike=row.strike,
                expiration=row.expiration,
                option_type=row.option_type,
            )
            db.add(asset)
            await db.flush()

        # Create position + initial transaction
        position = Position(
            asset_id=asset.id,
            quantity=row.quantity,
            avg_cost=row.price,
        )
        db.add(position)
        await db.flush()

        txn = Transaction(
            position_id=position.id,
            transaction_type=TransactionType.BUY,
            quantity=row.quantity,
            price=row.price,
        )
        if row.date:
            txn.timestamp = row.date
        db.add(txn)

        created.append(ImportRowOut(
            symbol=row.symbol,
            asset_type=row.asset_type,
            quantity=row.quantity,
            price=row.price,
        ))

    await db.commit()

    return ImportResponse(
        imported=len(created),
        skipped=result.skipped,
        errors=result.errors,
        positions_created=created,
    )
