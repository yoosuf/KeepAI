from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analytics.models import UsageRecord


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_usage(
        self,
        user_id: int,
        action: str,
        model_name: Optional[str] = None,
        processing_time_ms: Optional[int] = None,
        meta_data: Optional[Dict[str, Any]] = None,
    ) -> UsageRecord:
        record = UsageRecord(
            user_id=user_id,
            action=action,
            model_name=model_name,
            processing_time_ms=processing_time_ms,
            meta_data=str(meta_data) if meta_data else None,
        )
        self.db.add(record)
        await self.db.commit()
        return record

    async def get_usage_stats(self, user_id: int, days: Optional[int] = None) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        filters = [UsageRecord.user_id == user_id]
        if days:
            from_start = now - timedelta(days=days)
            filters.append(UsageRecord.created_at >= from_start)

        total = await self.db.execute(select(func.count()).where(*filters).select_from(UsageRecord))
        total_count = total.scalar_one()

        total_time = await self.db.execute(
            select(func.coalesce(func.sum(UsageRecord.processing_time_ms), 0)).where(*filters).select_from(UsageRecord)
        )
        total_ms = total_time.scalar_one()

        by_model_query = select(UsageRecord.model_name, func.count()).where(*filters).group_by(UsageRecord.model_name)
        by_model = {r[0] or "unknown": r[1] for r in (await self.db.execute(by_model_query)).all()}

        by_action_query = select(UsageRecord.action, func.count()).where(*filters).group_by(UsageRecord.action)
        by_action = {r[0]: r[1] for r in (await self.db.execute(by_action_query)).all()}

        today_count = await self.db.execute(
            select(func.count())
            .where(UsageRecord.user_id == user_id, UsageRecord.created_at >= today_start)
            .select_from(UsageRecord)
        )
        today = today_count.scalar_one()

        return {
            "total_requests": total_count,
            "total_processing_time_ms": total_ms,
            "avg_processing_time_ms": round(total_ms / total_count, 2) if total_count else 0.0,
            "requests_by_model": by_model,
            "requests_by_action": by_action,
            "requests_today": today,
        }

    async def get_all_users_stats(self) -> list:
        subq = (
            select(
                UsageRecord.user_id,
                func.count().label("total_requests"),
                func.coalesce(func.sum(UsageRecord.processing_time_ms), 0).label("total_time"),
            )
            .group_by(UsageRecord.user_id)
            .subquery()
        )

        from src.modules.auth.models import User

        users = await self.db.execute(
            select(User.id, User.email, subq.c.total_requests, subq.c.total_time)
            .outerjoin(subq, User.id == subq.c.user_id)
            .order_by(subq.c.total_requests.desc().nullslast())
        )
        result = []
        for row in users.all():
            result.append(
                {
                    "user_id": row[0],
                    "email": row[1],
                    "total_requests": row[2] or 0,
                    "total_processing_time_ms": row[3] or 0,
                }
            )
        return result
