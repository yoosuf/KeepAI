# Architecture

KeepAI follows **Clean Architecture** principles (also known as Hexagonal Architecture or Ports and Adapters).

---

## Layered Architecture

```
+------------------------------------------------------------------+
|                     Presentation Layer                             |
|  FastAPI Routers (src/modules/*/router.py)                         |
|  - Auth routes (register, login)                                   |
|  - Prompt routes (create, list, stream)                            |
|  - Conversation routes (CRUD)                                      |
|  - WebSocket chat handler                                          |
|  - Admin, Models, API Keys, Analytics, Documents routes            |
+------------------------------------------------------------------+
|                      Application Layer                              |
|  Services (src/modules/*/service.py)                                |
|  - AuthService (user creation, credential validation)               |
|  - PromptService (prompt creation, LLM interaction)                |
|  - ConversationService (thread management, chat)                   |
|  - DocumentService (upload, chunk, search)                         |
|  - AnalyticsService (usage stats, recording)                       |
|  - Business logic, orchestration                                   |
+------------------------------------------------------------------+
|                        Domain Layer                                  |
|  Interfaces (src/core/interfaces/)                                  |
|  - LLMInterface (abstract port for LLM interactions)               |
|  - Domain models, schemas                                          |
+------------------------------------------------------------------+
|                     Infrastructure Layer                             |
|  Adapters (src/infrastructure/)                                     |
|  - OllamaClient (concrete LLM adapter)                             |
|  - Database (SQLAlchemy models, session management)                |
|  - Auth utilities (JWT, password hashing)                          |
+------------------------------------------------------------------+
```

### Dependency Rule

Dependencies point **inward**. The outer layers depend on inner layers, never the reverse:

- **Presentation** → **Application** → **Domain** ← **Infrastructure**

The **Domain** layer has zero dependencies on frameworks or external systems. It defines interfaces (ports) that the infrastructure layer implements (adapters).

---

## Request Flow

```
Client Request
      |
      v
   Router (presentation)
      |  Validates request (Pydantic schemas)
      |  Extracts user from JWT (dependency)
      v
   Service (application)
      |  Orchestrates business logic
      |  Calls port interface
      v
   LLMInterface (domain port)
      |  Abstract contract
      v
   OllamaClient (infrastructure adapter)
      |  Calls Ollama HTTP API
      v
   LLM Response
      |
      v
   Back to Router -> JSON Response
```

### Example: Prompt Creation

1. `POST /api/v1/prompts` -> `Router.create_prompt()`
2. JWT dependency extracts and validates user
3. `PromptService.create_prompt()` is called
4. Service calls `llm_interface.generate(prompt_text, model_name)`
5. `OllamaClient.generate()` sends HTTP request to Ollama API
6. Response is saved to PostgreSQL via SQLAlchemy
7. Service returns the saved prompt object
8. Router serializes and returns JSON

---

## Module Structure

Each feature module follows a consistent pattern:

```
src/modules/{feature}/
+-- __init__.py
+-- models.py        # SQLAlchemy ORM models
+-- schemas.py       # Pydantic request/response schemas
+-- service.py       # Business logic
+-- router.py        # FastAPI route definitions
+-- utils.py         # Helper functions (optional)
+-- agents/
    +-- __init__.py
    +-- {agent}.py   # Domain-specific LLM agents (e.g., InvoiceAgent)
```

### Auth Module

| Component | File | Responsibility |
|-----------|------|----------------|
| Models | `models.py` | `User`, `Role`, `Permission`, `role_permissions` tables |
| Schemas | `schemas.py` | Registration/login request/response schemas |
| Service | `service.py` | User creation, credential verification |
| Utils | `utils.py` | Password hashing (Argon2id), JWT creation/verification, token decoding |
| Router | `router.py` | `/register`, `/login` endpoints |

### Prompts Module

| Component | File | Responsibility |
|-----------|------|----------------|
| Models | `models.py` | `Prompt` table |
| Schemas | `schemas.py` | Prompt request/response schemas |
| Service | `service.py` | Prompt creation, listing, invoice extraction |
| Router | `router.py` | Prompt CRUD, invoice extraction, streaming endpoints |
| Agents | `agents/invoice_agent.py` | Invoice-specific prompt templates and response parsing |

### Conversations Module

| Component | File | Responsibility |
|-----------|------|----------------|
| Models | `models.py` | `Conversation`, `ConversationMessage` tables |
| Schemas | `schemas.py` | Conversation request/response schemas |
| Service | `service.py` | Thread management, chat with history |
| Router | `router.py` | REST conversation CRUD, title update |

### WebSocket Module

| Component | File | Responsibility |
|-----------|------|----------------|
| Router | `router.py` | WebSocket endpoint, ConnectionManager, JWT auth for WS |
| Types | - | Message types: chat, list_conversations, get_conversation, delete_conversation, ping |

### API Keys Module

| Component | File | Responsibility |
|-----------|------|----------------|
| Models | `models.py` | `ApiKey` table with SHA-512 hashed keys |
| Schemas | `schemas.py` | Key request/response schemas |
| Service | `service.py` | Key generation, hashing, validation |
| Router | `router.py` | Key CRUD endpoints |

### Analytics Module

| Component | File | Responsibility |
|-----------|------|----------------|
| Models | `models.py` | `UsageRecord`, `AuditLog` tables |
| Service | `service.py` | Usage recording, stats aggregation, per-user stats |
| Router | `router.py` | Stats and admin user-stats endpoints |

### Documents Module

| Component | File | Responsibility |
|-----------|------|----------------|
| Models | `models.py` | `Document`, `DocumentChunk` tables |
| Schemas | `schemas.py` | Document response schemas |
| Service | `service.py` | Upload, chunking, keyword search, embedding generation |
| Router | `router.py` | Document CRUD, search, query, embed endpoints |

---

## Core Components

### Configuration (`src/core/config.py`)

Pydantic settings loaded from environment variables / `.env` file:

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "KeepAI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    SECRET_KEY: str = "changethis"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
    CORS_ORIGINS: list[str] = ["*"]
    RATE_LIMIT_LLM: str = "20/minute"
    DEV_MODE: bool = False
```

### Database (`src/core/database.py`)

- `AsyncSessionLocal` — SQLAlchemy async session factory
- `get_db()` — FastAPI dependency that yields a DB session
- `Base` — SQLAlchemy declarative base
- `engine` — async engine with connection pooling

### LLM Interface (`src/core/interfaces/llm_interface.py`)

```python
class LLMInterface(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str = "", **kwargs) -> dict: ...
    @abstractmethod
    async def chat(self, messages: list, model: str = "", **kwargs) -> dict: ...
    @abstractmethod
    async def stream_generate(self, prompt: str, model: str = "", **kwargs): ...
    @abstractmethod
    async def stream_chat(self, messages: list, model: str = "", **kwargs): ...
```

### Ollama Client (`src/infrastructure/llm/ollama_client.py`)

Concrete adapter implementing `LLMInterface`. Calls Ollama's `/api/generate` and `/api/chat` via `httpx.AsyncClient`. Supports both blocking and streaming modes.

### Middleware (`src/core/middleware.py`)

- `RequestIDMiddleware` — attaches correlation ID (X-Request-ID) and records response time (X-Response-Time-Ms) for every request

### Rate Limiting (`src/core/rate_limit.py`)

- Slowapi `Limiter` with key function that extracts user email from JWT, falling back to client IP
- Configurable via `RATE_LIMIT_LLM` env var

---

## Authentication & Authorization

### Flow

1. **Register** -> Email + password -> Argon2id hash -> stored in `users` table
2. **Login** -> Email + password -> verify hash -> issue JWT (30 min expiry, includes `user_id` and `sub` claims)
3. **Request** -> JWT in `Authorization: Bearer <token>` header -> decode -> extract user -> inject as dependency

### RBAC

- `PermissionChecker` is a FastAPI dependency class parameterized with a required permission name
- It loads the user's role and permissions from DB
- If the required permission is not found, returns 403
- Permissions and roles stored in DB tables (`permissions`, `roles`, `role_permissions`)

---

## WebSocket Architecture

```
Client -> ws://host/ws/chat?token=<jwt>
               |
               v
         ConnectionManager
         (manages per-user connections)
               |
        +------+------+
        |             |
   REST API      ConversationService
   (CRUD)        (chat with history)
        |             |
        +------+------+
               |
         OllamaClient
```

- `ConnectionManager` tracks active WebSocket connections per user_id
- Supports message types: `chat`, `list_conversations`, `get_conversation`, `delete_conversation`, `ping`
- Chat calls `ConversationService.chat_in_conversation()` which maintains full message history

---

## Frontend Architecture

```
frontend/
+-- src/
    +-- main.tsx          # React entry point, BrowserRouter setup
    +-- App.tsx           # Route definitions, Layout wrapper
    +-- context/
    |   +-- AuthContext.tsx  # JWT decoding, auth state, login/logout
    +-- api/
    |   +-- client.ts       # Fetch wrapper with auth header, 401 redirect
    |   +-- prompts.ts      # Prompt API functions
    |   +-- conversations.ts # Conversation REST API functions
    |   +-- apiKeys.ts      # API key API functions
    |   +-- documents.ts    # Document API functions
    |   +-- analytics.ts    # Analytics API functions
    |   +-- admin.ts        # Admin API functions
    |   +-- models.ts       # Model API functions
    +-- pages/
    |   +-- Chat.tsx         # WebSocket chat interface
    |   +-- Conversations.tsx # Conversation browser
    |   +-- History.tsx      # Prompt history browser
    |   +-- Playground.tsx   # API test playground
    |   +-- Models.tsx       # Model management
    |   +-- ApiKeys.tsx      # API key management
    |   +-- Documents.tsx    # Document RAG interface
    |   +-- Analytics.tsx    # Usage analytics dashboard
    |   +-- AdminUsers.tsx   # Admin user management
    |   +-- AdminPrompts.tsx # Admin prompt viewer
    |   +-- Login.tsx        # Login form
    |   +-- Register.tsx     # Registration form
    +-- components/
    |   +-- Layout.tsx       # Sidebar + main content layout
    |   +-- ProtectedRoute.tsx # Auth guard wrapper
    +-- types/
    |   +-- index.ts         # TypeScript interfaces
    +-- index.css            # Global styles (~1283 lines)
```

### Data Flow

- Vite dev server proxies `/api` to `localhost:8000`
- Auth token stored in `localStorage`, auto-attached to all fetch requests
- 401 responses auto-redirect to `/login`
- WebSocket URL derived from `window.location` (supports any host/port)

---

## Data Flow Diagram

```
                    +----------+
                    |  Client   |
                    +----+-----+
                         | HTTP / WS
                    +----v-----+
                    |  Router   |
                    +----+-----+
                         |
              +----------+----------+----------+
              |          |          |          |
         +----v---+ +---v----+ +---v----+ +---v----+
         | Auth   | |Prompt  | |Convers | |Document|
         |Service | |Service | |Service | |Service |
         +----+---+ +---+----+ +---+----+ +---+----+
              |         |          |          |
              |    +----v-----+    |          |
              |    |LLMInter- |    |          |
              |    | face     |    |          |
              |    +----+-----+    |          |
              |         |          |          |
         +----v---------v----------v----------v----+
         |            PostgreSQL                     |
         |  (users, prompts, conversations,          |
         |   messages, api_keys, documents,          |
         |   chunks, usage_records, audit_logs,         |
         |   roles, permissions)                     |
         +------------------+------------------------+
                            |
         +------------------v------------------------+
         |        Ollama (local LLM)                   |
         +-------------------------------------------+
```

---

## Testing Strategy

```
tests/
+-- conftest.py           # Shared fixtures (app client, mock env)
+-- test_main.py          # Health check test
+-- api/
|   +-- test_auth.py      # Auth endpoint tests
+-- services/
    +-- test_prompt_service.py  # Prompt service tests (mocked LLM + DB)
```

- **Services** are tested with mocked LLM and database dependencies
- **API endpoints** are tested via `httpx.AsyncClient` against the FastAPI app
- **External systems** (Ollama, PostgreSQL) are always mocked in unit tests
- Tests use `pytest-asyncio` for async support
- Coverage tracked via `pytest-cov`

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Hexagonal architecture | Swappable LLM backends, testability, separation of concerns |
| Async throughout | Non-blocking I/O for LLM calls and database operations |
| DB-driven RBAC | Dynamic permissions without code changes |
| Pydantic for everything | Validation, settings, serialization, docs generation |
| Docker first | Reproducible development and deployment environment |
| JSON logging | Machine-parseable logs for observability |
| WebSocket for chat | Full duplex, low latency vs polling/SSE |
| SHA-512 for API keys | Fast lookups (vs bcrypt/argon2) with `ka_` prefix |
| Plain fetch (no axios) | Minimize frontend dependencies |
| CSS bar charts | No chart library dependency for initial analytics |

---

## Related Documents

- [Getting Started](getting-started.md) — Project overview and quick start
- [API Reference](api/reference.md) — Complete API reference
- [Deployment Guide](guides/deployment.md) — Production deployment
- [Contributing](development/contributing.md) — Development guidelines
