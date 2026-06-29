from pydantic import BaseModel


class UsageStats(BaseModel):
    total_requests: int
    total_processing_time_ms: int
    avg_processing_time_ms: float
    requests_by_model: dict[str, int]
    requests_by_action: dict[str, int]
    requests_today: int


class UserUsageStats(BaseModel):
    user_id: int
    email: str
    total_requests: int
    total_processing_time_ms: int
