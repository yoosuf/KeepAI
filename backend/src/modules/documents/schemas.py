from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    id: int
    filename: str
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentOut):
    content_text: Optional[str] = None
    chunk_count: int = 0
