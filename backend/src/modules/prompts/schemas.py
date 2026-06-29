from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PromptBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    prompt_text: str = Field(..., description="The prompt to send to the LLM")
    model_name: Optional[str] = Field(None, description="The model to use; defaults to OLLAMA_MODEL env var")


class PromptCreate(PromptBase):
    system_prompt: Optional[str] = Field(None, description="System instructions prepended to the conversation")
    task_type: Optional[str] = Field(None, description="Task type for model routing (e.g. 'code', 'analysis')")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling probability")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")


class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message content")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        allowed = {"user", "assistant", "system"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {allowed}")
        return v


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., min_length=1, description="Conversation history")
    model_name: Optional[str] = Field(None, description="The model to use; defaults to OLLAMA_MODEL env var")
    system_prompt: Optional[str] = Field(None, description="System instructions prepended to the conversation")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nucleus sampling probability")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")


class ChatResponse(BaseModel):
    response_text: str
    processing_time_ms: int
    model_name: str


class InvoiceExtractRequest(BaseModel):
    text_content: str = Field(..., min_length=1, description="Raw text to extract invoice data from")
    model_name: Optional[str] = Field(None, description="The model to use; defaults to OLLAMA_MODEL env var")


class PromptResponse(PromptBase):
    id: int
    response_text: Optional[str] = None
    processing_time_ms: Optional[int] = None
    meta_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class PaginatedPromptResponse(BaseModel):
    items: List[PromptResponse]
    total: int
    skip: int
    limit: int
