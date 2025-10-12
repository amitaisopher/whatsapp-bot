from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify the service is running."""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
