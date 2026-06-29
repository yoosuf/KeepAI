import json
import logging
from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.database import get_db
from src.infrastructure.llm.ollama_client import OllamaClient
from src.modules.auth.models import User
from src.modules.auth.utils import decode_token
from src.modules.conversations.service import ConversationService

router = APIRouter()
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active: Dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        if user_id not in self.active:
            self.active[user_id] = []
        self.active[user_id].append(ws)

    def disconnect(self, user_id: int, ws: WebSocket):
        if user_id in self.active:
            self.active[user_id] = [w for w in self.active[user_id] if w != ws]
            if not self.active[user_id]:
                del self.active[user_id]

    async def send_to_user(self, user_id: int, message: str):
        if user_id in self.active:
            for ws in self.active[user_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, db: AsyncSession = Depends(get_db)):  # noqa: C901
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if not email:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        query = select(User).where(User.email == email)
        result = await db.execute(query)
        user = result.scalars().first()
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    llm_client = OllamaClient(base_url=settings.OLLAMA_BASE_URL)
    conv_service = ConversationService(db, llm_client)

    await manager.connect(user.id, websocket)
    logger.info(f"WebSocket connected: user={user.id} email={email}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "message")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg_type == "chat":
                conversation_id = msg.get("conversation_id")
                message_text = msg.get("message", "")
                if not message_text:
                    await websocket.send_json({"type": "error", "message": "Message is required"})
                    continue

                try:
                    result = await conv_service.chat_in_conversation(
                        user_id=user.id,
                        message=message_text,
                        conversation_id=conversation_id,
                        model_name=msg.get("model_name"),
                        system_prompt=msg.get("system_prompt"),
                        temperature=msg.get("temperature"),
                        top_p=msg.get("top_p"),
                        max_tokens=msg.get("max_tokens"),
                    )

                    await websocket.send_json(
                        {
                            "type": "chat_response",
                            "conversation_id": result["conversation_id"],
                            "message_id": result["message_id"],
                            "response_text": result["response_text"],
                            "processing_time_ms": result["processing_time_ms"],
                            "model_name": result["model_name"],
                        }
                    )
                except Exception as e:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": f"Chat failed: {e}",
                        }
                    )

            elif msg_type == "list_conversations":
                conversations, total = await conv_service.get_conversations(user_id=user.id)
                await websocket.send_json(
                    {
                        "type": "conversations",
                        "items": [
                            {
                                "id": c.id,
                                "title": c.title,
                                "model_name": c.model_name,
                                "message_count": len(c.messages) if hasattr(c, "messages") else 0,
                                "created_at": str(c.created_at),
                                "updated_at": str(c.updated_at),
                            }
                            for c in conversations
                        ],
                        "total": total,
                    }
                )

            elif msg_type == "get_conversation":
                conv = await conv_service.get_conversation(msg["conversation_id"], user.id)
                if conv:
                    await websocket.send_json(
                        {
                            "type": "conversation",
                            "id": conv.id,
                            "user_id": conv.user_id,
                            "title": conv.title,
                            "model_name": conv.model_name,
                            "system_prompt": conv.system_prompt,
                            "created_at": str(conv.created_at),
                            "updated_at": str(conv.updated_at),
                            "messages": [
                                {"id": m.id, "role": m.role, "content": m.content, "created_at": str(m.created_at)}
                                for m in conv.messages
                            ],
                        }
                    )
                else:
                    await websocket.send_json({"type": "error", "message": "Conversation not found"})

            elif msg_type == "delete_conversation":
                deleted = await conv_service.delete_conversation(msg["conversation_id"], user.id)
                await websocket.send_json(
                    {
                        "type": "conversation_deleted",
                        "conversation_id": msg["conversation_id"],
                        "success": deleted,
                    }
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user={user.id}")
    except Exception as e:
        logger.error(f"WebSocket error user={user.id}: {e}")
    finally:
        manager.disconnect(user.id, websocket)
        await llm_client.close()
