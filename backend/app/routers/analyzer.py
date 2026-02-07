from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
async def portfolio_summary():
    """Portfolio-level risk and return summary. Placeholder."""
    return {"message": "analyzer — not yet implemented"}
