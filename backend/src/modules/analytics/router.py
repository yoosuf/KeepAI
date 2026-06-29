from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.modules.analytics.service import AnalyticsService
from src.modules.auth.models import User
from src.modules.auth.service import PermissionChecker

router = APIRouter()


def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)


@router.get("/analytics/stats")
async def my_usage(
    days: Optional[int] = Query(None, description="Number of days to look back"),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(PermissionChecker("prompts:create")),
):
    return await service.get_usage_stats(user_id=current_user.id, days=days)


@router.get("/analytics/admin/user-stats")
async def all_users_stats(
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(PermissionChecker("users:read")),
):
    return await service.get_all_users_stats()
