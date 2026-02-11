from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_async_db
from app.schemas.dashboard import DashboardStatsResponse
from app.api.auth import get_current_active_user
from app.services.dashboard import dashboard_stats

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    main_db: AsyncSession = Depends(get_async_db),
    current_user=Depends(get_current_active_user),
):
    """
    Get dashboard statistics:
    - Total number of Animals
    - Count of Tracking Animals grouped by status
    """
    stats = await dashboard_stats(main_db, current_user)
    return stats
