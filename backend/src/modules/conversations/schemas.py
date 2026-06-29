from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class ConversationMessageOut(BaseModel):
    id: int
    role: str
    content: str
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationOut(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    model_name: str
    system_prompt: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessageOut] = []

    model_config = ConfigDict(from_attributes=True)


class ConversationSummary(BaseModel):
    id: int
    title: Optional[str] = None
    model_name: str
    message_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None


class ConversationMessageCreate(BaseModel):
    role: str
    content: str
    meta_data: Optional[Dict[str, Any]] = None


class ConversationChatRequest(BaseModel):
    conversation_id: Optional[int] = None
    message: str
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None


class ConversationChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    response_text: str
    processing_time_ms: int
    model_name: str
