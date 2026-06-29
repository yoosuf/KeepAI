# Developer Walkthrough

This walkthrough guides you through the KeepAI codebase and shows how the key components work together.

---

## Project Structure

```
KeepAI/
+-- backend/
|   +-- src/
|   |   +-- main.py              # FastAPI app entrypoint, lifespan, routers
|   |   +-- core/
|   |   |   +-- config.py        # Pydantic settings from env vars
|   |   |   +-- database.py      # Async SQLAlchemy session management
|   |   |   +-- middleware.py    # Request ID middleware
|   |   |   +-- rate_limit.py    # Slowapi rate limiter
|   |   |   +-- logging_config.py # Structured JSON logging
|   |   |   +-- interfaces/
|   |   |       +-- llm_interface.py  # Abstract LLM port
|   |   +-- infrastructure/
|   |   |   +-- llm/
|   |   |       +-- ollama_client.py  # Ollama adapter
|   |   +-- modules/
|   |       +-- auth/            # Authentication (models, schemas, service, utils, router)
|   |       +-- prompts/         # Prompt CRUD and agents
|   |       +-- conversations/   # Conversation threads (REST + WS)
|   |       +-- api_keys/        # API key management
|   |       +-- analytics/       # Usage analytics
|   |       +-- documents/       # Document RAG
|   |       +-- admin/           # Admin endpoints
|   |       +-- models/          # Model management
|   |       +-- ws/              # WebSocket handler
|   |       +-- rag/             # RAG (stub)
|   +-- tests/                   # Backend tests
|   +-- alembic/                 # Database migrations
+-- frontend/
|   +-- src/
|       +-- main.tsx             # React entry
|       +-- App.tsx              # Routes and Layout
|       +-- context/AuthContext.tsx  # Auth state management
|       +-- api/                 # API client functions
|       +-- pages/               # All page components
|       +-- components/          # Shared components
|       +-- types/               # TypeScript interfaces
+-- docker/                      # Docker configs
+-- docs/                        # Documentation
```

---

## Start the Application

### Docker (Recommended)

```bash
docker compose -f docker/docker-compose.yml up --build
```

This starts four containers:
- `backend` — FastAPI on port 8000
- `frontend` — Nginx serving React on port 3000
- `db` — PostgreSQL on port 5432
- `ollama` — Ollama on port 11434

### Local Development

Terminal 1 (Backend):
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Postgres/Ollama settings
alembic upgrade head
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 (Frontend):
```bash
cd frontend
npm install
npm run dev
```

---

## First API Calls

### Register and Login

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin@example.com" \
  -F "password=adminpass" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Test admin endpoint
curl http://localhost:8000/api/v1/admin/users -H "Authorization: Bearer $TOKEN"
```

### Send a Prompt

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Explain quantum computing in 3 sentences."}'
```

---

## Key Architecture Concepts

### Request Flow

1. Request hits FastAPI router
2. Dependencies are resolved (auth, DB session, rate limiter)
3. Router calls service method
4. Service calls LLMInterface methods
5. OllamaClient (or other adapter) makes HTTP request to LLM
6. Response flows back: adapter -> service -> router -> client

### Module Pattern

Every feature module follows the same structure:

```python
# models.py — SQLAlchemy ORM
class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(BigInteger, primary_key=True)
    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text)

# schemas.py — Pydantic validation
class PromptCreate(BaseModel):
    prompt_text: str
    model_name: str = ""

# service.py — Business logic
class PromptService:
    def __init__(self, db: AsyncSession, llm_client: LLMInterface):
        self.db = db
        self.llm_client = llm_client

    async def create_prompt(self, user_id: int, prompt_text: str, ...) -> Prompt:
        response = await self.llm_client.generate(prompt_text, model_name)
        prompt = Prompt(user_id=user_id, prompt_text=prompt_text, ...)
        self.db.add(prompt)
        await self.db.commit()
        return prompt

# router.py — HTTP endpoints
@router.post("/prompts", response_model=PromptResponse)
async def create_prompt(
    body: PromptCreate,
    service: PromptService = Depends(get_prompt_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_prompt(user_id=current_user.id, ...)
```

### WebSocket Chat Flow

1. Client connects to `ws://host/ws/chat?token=<jwt>`
2. `ConnectionManager` authenticates the user and tracks the connection
3. Client sends `{"type": "chat", "message": "Hello", "conversation_id": 1}`
4. Handler calls `ConversationService.chat_in_conversation()`
5. Service loads conversation history, appends new message
6. Calls LLM with full message history
7. Saves response to DB
8. Sends response back over WebSocket

---

## Verification Checklist

After setup, verify everything works:

- [ ] `curl http://localhost:8000/health/live` returns `{"status": "ok"}`
- [ ] `curl http://localhost:8000/health/ready` returns `{"status": "ready", "db": "ok", "llm": "ok"}`
- [ ] User registration works
- [ ] Login returns a JWT token
- [ ] Authenticated prompt requests work
- [ ] Admin endpoints work with admin token
- [ ] `http://localhost:5173` (dev) or `http://localhost:3000` (Docker) shows the frontend login page
- [ ] Chat page connects via WebSocket and sends messages
- [ ] Conversations page shows conversation threads

---

## Related

- [Architecture](../architecture.md)
- [API Reference](../api/reference.md)
- [Contributing](contributing.md)
- [Getting Started](../getting-started.md)
