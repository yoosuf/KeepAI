from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.core.rate_limit import limiter
from src.modules.auth.models import User
from src.modules.auth.service import get_current_user
from src.modules.conversations.schemas import (
    ConversationChatRequest,
    ConversationChatResponse,
    ConversationCreate,
    ConversationOut,
    ConversationSummary,
)
from src.modules.conversations.service import ConversationService

router = APIRouter()


def get_conversation_service(request: Request, db: AsyncSession = Depends(get_db)) -> ConversationService:
    return ConversationService(db, request.app.state.llm_client)


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    conversations, total = await service.get_conversations(user_id=current_user.id, skip=skip, limit=limit)
    return [
        ConversationSummary(
            id=c.id,
            title=c.title,
            model_name=c.model_name,
            message_count=len(c.messages) if hasattr(c, "messages") else 0,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in conversations
    ]


@router.post("/conversations", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_conversation(
    request: Request,
    body: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_conversation(
        user_id=current_user.id,
        title=body.title,
        model_name=body.model_name,
        system_prompt=body.system_prompt,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    conv = await service.get_conversation(conversation_id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.put("/conversations/{conversation_id}/title", response_model=ConversationOut)
async def update_conversation_title(
    conversation_id: int,
    title: str,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    conv = await service.update_title(conversation_id, user_id=current_user.id, title=title)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    deleted = await service.delete_conversation(conversation_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/conversations/chat", response_model=ConversationChatResponse)
@limiter.limit(settings.RATE_LIMIT_LLM)
async def conversation_chat(
    request: Request,
    body: ConversationChatRequest,
    service: ConversationService = Depends(get_conversation_service),
    current_user: User = Depends(get_current_user),
):
    try:
        result = await service.chat_in_conversation(
            user_id=current_user.id,
            message=body.message,
            conversation_id=body.conversation_id,
            model_name=body.model_name,
            system_prompt=body.system_prompt,
            temperature=body.temperature,
            top_p=body.top_p,
            max_tokens=body.max_tokens,
        )
        return ConversationChatResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {e}",
        ) from e
