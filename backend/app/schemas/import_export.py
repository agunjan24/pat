from pydantic import BaseModel


class ImportRowOut(BaseModel):
    symbol: str
    asset_type: str
    quantity: float
    price: float


class ImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
    positions_created: list[ImportRowOut]
