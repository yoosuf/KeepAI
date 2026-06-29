from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ApiKeyOut(BaseModel):
    id: int
    name: str
    key_preview: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreateResponse(BaseModel):
    id: int
    name: str
    key_preview: str
    full_key: str
    created_at: datetime


class ApiKeyCreate(BaseModel):
    name: str
    expires_at: Optional[datetime] = None
