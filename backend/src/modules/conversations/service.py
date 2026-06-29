from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.config import settings
from src.core.interfaces.llm_interface import LLMInterface
from src.modules.conversations.models import Conversation, ConversationMessage


class ConversationService:
    def __init__(self, db: AsyncSession, llm_client: LLMInterface):
        self.db = db
        self.llm_client = llm_client

    async def create_conversation(
        self,
        user_id: int,
        title: Optional[str] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            title=title or "New conversation",
            model_name=model_name or settings.OLLAMA_MODEL,
            system_prompt=system_prompt,
        )
        self.db.add(conv)
        await self.db.commit()
        await self.db.refresh(conv)
        return conv

    async def get_conversations(self, user_id: int, skip: int = 0, limit: int = 50) -> Tuple[List[Conversation], int]:
        query = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        count_query = select(func.count()).where(Conversation.user_id == user_id).select_from(Conversation)
        items = await self.db.execute(query)
        total = await self.db.execute(count_query)
        return items.scalars().all(), total.scalar_one()

    async def get_conversation(self, conversation_id: int, user_id: int) -> Optional[Conversation]:
        query = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def update_title(self, conversation_id: int, user_id: int, title: str) -> Optional[Conversation]:
        query = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        result = await self.db.execute(query)
        conv = result.scalars().first()
        if conv:
            conv.title = title
            await self.db.commit()
            await self.db.refresh(conv)
        return conv

    async def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        query = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        result = await self.db.execute(query)
        conv = result.scalars().first()
        if not conv:
            return False
        await self.db.delete(conv)
        await self.db.commit()
        return True

    async def add_message(
        self, conversation_id: int, role: str, content: str, meta_data: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta_data=meta_data,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def chat_in_conversation(
        self,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None,
        model_name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        resolved_model = model_name or settings.OLLAMA_MODEL

        if conversation_id:
            conv = await self.get_conversation(conversation_id, user_id)
            if not conv:
                raise ValueError("Conversation not found")
        else:
            conv = await self.create_conversation(
                user_id=user_id,
                model_name=resolved_model,
                system_prompt=system_prompt,
            )

        await self.add_message(conv.id, "user", message)
        messages: list[dict] = []
        if conv.system_prompt:
            messages.append({"role": "system", "content": conv.system_prompt})

        msg_query = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conv.id)
            .order_by(ConversationMessage.created_at)
        )
        msg_result = await self.db.execute(msg_query)
        for m in msg_result.scalars().all():
            messages.append({"role": m.role, "content": m.content})

        llm_kwargs = {}
        if system_prompt:
            llm_kwargs["system"] = system_prompt
        if temperature is not None:
            llm_kwargs["temperature"] = temperature
        if top_p is not None:
            llm_kwargs["top_p"] = top_p
        if max_tokens is not None:
            llm_kwargs["num_predict"] = max_tokens

        llm_result = await self.llm_client.chat(messages=messages, model=resolved_model, **llm_kwargs)

        assistant_msg = await self.add_message(
            conv.id,
            "assistant",
            llm_result["response_text"],
            meta_data={"processing_time_ms": llm_result["processing_time_ms"]},
        )

        return {
            "conversation_id": conv.id,
            "message_id": assistant_msg.id,
            "response_text": llm_result["response_text"],
            "processing_time_ms": llm_result["processing_time_ms"],
            "model_name": resolved_model,
        }
