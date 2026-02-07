from datetime import datetime

from pydantic import BaseModel

from app.models.alert import AlertType


class AlertCreate(BaseModel):
    symbol: str
    alert_type: AlertType
    threshold: float | None = None
    message: str | None = None


class AlertOut(BaseModel):
    id: int
    symbol: str
    alert_type: AlertType
    threshold: float | None
    message: str | None
    is_active: bool
    is_triggered: bool
    triggered_at: datetime | None
    created_at: datetime
    model_config = {"from_attributes": True}


class AlertCheckResult(BaseModel):
    alert_id: int
    symbol: str
    alert_type: str
    triggered: bool
    current_value: float | None
    message: str | None
