from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.alert import Alert, AlertType
from app.schemas.alert import AlertCheckResult, AlertCreate, AlertOut
from app.tracker.market_data import get_current_price

router = APIRouter()


@router.get("", response_model=list[AlertOut])
async def list_alerts(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Alert).order_by(Alert.created_at.desc())
    if active_only:
        stmt = stmt.where(Alert.is_active == True)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=AlertOut, status_code=201)
async def create_alert(body: AlertCreate, db: AsyncSession = Depends(get_db)):
    alert = Alert(
        symbol=body.symbol.upper(),
        alert_type=body.alert_type,
        threshold=body.threshold,
        message=body.message,
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.delete(alert)
    await db.commit()


@router.post("/check", response_model=list[AlertCheckResult])
async def check_alerts(db: AsyncSession = Depends(get_db)):
    """Check all active alerts against current market data."""
    result = await db.execute(
        select(Alert).where(Alert.is_active == True, Alert.is_triggered == False)
    )
    alerts = result.scalars().all()

    results: list[AlertCheckResult] = []
    price_cache: dict[str, float | None] = {}

    for alert in alerts:
        if alert.symbol not in price_cache:
            price_cache[alert.symbol] = await get_current_price(alert.symbol)

        current = price_cache[alert.symbol]
        triggered = False

        if current is not None and alert.threshold is not None:
            if alert.alert_type == AlertType.PRICE_ABOVE and current >= alert.threshold:
                triggered = True
            elif alert.alert_type == AlertType.PRICE_BELOW and current <= alert.threshold:
                triggered = True

        if triggered:
            alert.is_triggered = True
            alert.triggered_at = datetime.utcnow()

        results.append(AlertCheckResult(
            alert_id=alert.id,
            symbol=alert.symbol,
            alert_type=alert.alert_type.value,
            triggered=triggered,
            current_value=current,
            message=alert.message,
        ))

    await db.commit()
    return results
