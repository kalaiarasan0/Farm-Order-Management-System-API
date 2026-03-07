"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.api_route("/", methods=["GET", "HEAD"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}
