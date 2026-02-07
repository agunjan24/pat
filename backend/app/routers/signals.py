from fastapi import APIRouter

router = APIRouter()


@router.get("/scan")
async def scan_signals():
    """Scan portfolio for buy/sell signals. Placeholder."""
    return {"message": "signals — not yet implemented"}
