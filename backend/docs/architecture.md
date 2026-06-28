# Architecture

KeepAI follows **Hexagonal Architecture** (also called Clean Architecture or Ports and Adapters). The goal: business logic never depends on external systems — instead, external systems plug into defined interfaces.

---

## Layered Structure

```
┌──────────────────────────────────────────────────────────┐
│                     Presentation Layer                    │
│  FastAPI Routers  src/modules/*/router.py                 │
│  - Auth routes (register, login)                          │
│  - Prompt routes (create, list, get, stream)              │
│  - Admin routes (list users, all prompts)                 │
│  - Invoice extraction route                               │
├──────────────────────────────────────────────────────────┤
│                    Application Layer                       │
│  Services  src/modules/*/service.py                       │
│  - AuthService (user creation, credential validation)      │
│  - PromptService (prompt creation, LLM interaction)       │
│  Business logic, orchestration                            │
├──────────────────────────────────────────────────────────┤
│                      Domain Layer                          │
│  Interfaces  src/core/interfaces/                         │
│  - LLMInterface (abstract port for LLM interactions)      │
│  Zero framework dependencies                              │
├──────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                     │
│  Adapters  src/infrastructure/                            │
│  - OllamaClient (concrete LLM adapter)                    │
│  - Database (SQLAlchemy models, session management)       │
│  - Auth utilities (JWT, Argon2id)                         │
└──────────────────────────────────────────────────────────┘
```

### Dependency Rule

Dependencies point **inward only**:

```
Presentation → Application → Domain ← Infrastructure
```

The **Domain layer** (`src/core/interfaces/`) has zero dependencies on FastAPI, SQLAlchemy, or Ollama. It defines interfaces (ports) that the infrastructure layer implements (adapters).

---

## Request Flow

```
Client Request
      │
      ▼
   Router (presentation)
      │  Validates request via Pydantic schemas
      │  Extracts user from JWT (get_current_user dependency)
      ▼
   Service (application)
      │  Orchestrates business logic
      │  Calls LLMInterface port
      ▼
   LLMInterface (domain port)
      │  Abstract contract — no implementation here
      ▼
   OllamaClient (infrastructure adapter)
      │  HTTP POST to Ollama /api/generate
      ▼
   LLM Response
      │  Saved to PostgreSQL via async SQLAlchemy
      ▼
   JSON Response to Client
```

### Example: Prompt Creation (`POST /api/v1/prompts`)

1. Router receives request, validates via `PromptCreate` Pydantic schema
2. `get_current_user` dependency decodes JWT, loads user from DB
3. `PromptService.create_prompt()` is called with user + prompt text
4. Service calls `llm_client.generate(prompt_text, model_name)` via `LLMInterface`
5. `OllamaClient.generate()` sends HTTP request to `http://ollama:11434/api/generate`
6. Response and metadata are saved to the `prompts` table via SQLAlchemy
7. Service returns the saved `Prompt` ORM object
8. Router serializes to `PromptResponse` Pydantic schema and returns JSON

---

## Source Tree

```
src/
├── main.py                         # FastAPI app, middleware, router registration
├── core/
│   ├── config.py                   # Pydantic BaseSettings (loaded from .env)
│   ├── database.py                 # AsyncEngine, AsyncSessionLocal, get_db()
│   ├── interfaces/
│   │   └── llm_interface.py        # LLMInterface ABC (generate + stream_generate)
│   ├── logging_config.py           # Structured JSON logging setup
│   ├── middleware.py               # RequestIDMiddleware (X-Request-ID header)
│   └── rate_limit.py               # slowapi Limiter, key_func from JWT email
├── infrastructure/
│   └── llm/
│       └── ollama_client.py        # OllamaClient implements LLMInterface
├── modules/
│   ├── auth/
│   │   ├── models.py               # User, Role, Permission, role_permissions
│   │   ├── schemas.py              # UserCreate, Token, TokenData
│   │   ├── service.py              # register_new_user, authenticate_user, PermissionChecker
│   │   ├── utils.py                # get_password_hash, verify_password, create_access_token
│   │   └── router.py               # POST /register, POST /login
│   ├── prompts/
│   │   ├── models.py               # Prompt ORM model
│   │   ├── schemas.py              # PromptCreate, PromptResponse
│   │   ├── service.py              # PromptService: create_prompt, list_prompts, extract_invoice
│   │   ├── router.py               # Prompt CRUD + streaming + invoice extraction
│   │   └── agents/
│   │       └── invoice_agent.py    # InvoiceAgent: prompt template + JSON parser
│   └── admin/
│       └── router.py               # Admin-only endpoints (PermissionChecker guards)
└── scripts/
    └── seed_db.py                  # Seed test users into the database
```

---

## Module Layout Convention

Each feature module (`src/modules/{feature}/`) follows a consistent four-file pattern:

| File | Responsibility |
|------|---------------|
| `models.py` | SQLAlchemy ORM models — source of truth for DB schema |
| `schemas.py` | Pydantic request/response schemas — separate from ORM |
| `service.py` | Business logic injected with `db` and `llm_client` |
| `router.py` | FastAPI routes, wires dependencies, calls service |

---

## Auth Module Detail

### Models (`src/modules/auth/models.py`)

```
permissions          roles              role_permissions (assoc.)
├── id               ├── id             ├── role_id → roles.id
├── name             ├── name           └── permission_id → permissions.id
└── description      └── permissions[]

users
├── id
├── email
├── hashed_password
├── is_active
├── role_id → roles.id
└── prompts[]
```

### Auth Flow

1. **Register** — `POST /api/v1/auth/register`
   - Validates email uniqueness
   - Resolves role name to `Role` FK from DB
   - Hashes password with Argon2id
   - Inserts `User` row

2. **Login** — `POST /api/v1/auth/login` (OAuth2 form data)
   - Fetches user by email
   - Verifies Argon2id hash
   - Issues HS256 JWT with `sub=email`, expiry = `ACCESS_TOKEN_EXPIRE_MINUTES`

3. **Request Auth** — `get_current_user` dependency
   - Decodes JWT from `Authorization: Bearer <token>`
   - Fetches `User` from DB by email claim

4. **Permission Check** — `PermissionChecker("permission:name")`
   - Loads `user → role → permissions` (with 5-minute in-memory cache)
   - Returns 403 if required permission is absent

### Built-in RBAC Seed Data

| Role | Permissions |
|------|-------------|
| `admin` | `users:read`, `prompts:read_all`, `prompts:create` |
| `user` | `prompts:create` |

---

## LLM Abstraction

### Interface (`src/core/interfaces/llm_interface.py`)

```python
class LLMInterface(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
        # Returns: {"response_text": str, "processing_time_ms": int, "meta_data": dict}

    @abstractmethod
    async def stream_generate(self, prompt: str, model: str, **kwargs) -> AsyncGenerator[str, None]:
        # Yields: raw text tokens
```

### OllamaClient (`src/infrastructure/llm/ollama_client.py`)

- `generate()` — `POST /api/generate` with `stream=False`, returns full response
- `stream_generate()` — `POST /api/generate` with `stream=True`, yields tokens via httpx async streaming

To add a new provider, see [Extending LLM Providers](guides/extending-llm.md).

---

## Scalability Features

### Connection Pooling
SQLAlchemy async engine pool is tunable via env vars:
- `DB_POOL_SIZE` (default: 10) — persistent connections
- `DB_MAX_OVERFLOW` (default: 20) — burst connections
- `DB_POOL_TIMEOUT` (default: 30s) — wait time before error
- `DB_POOL_RECYCLE` (default: 3600s) — recycle idle connections

Defaults handle ~30 concurrent requests. Tune for your load.

### Rate Limiting
`slowapi` limiter in `src/core/rate_limit.py`. Key function extracts user email from JWT (falls back to IP for anonymous). Apply to a route with `@limiter.limit(settings.RATE_LIMIT_LLM)`. For multi-instance deployments, configure Redis storage: `Limiter(storage_uri="redis://redis:6379")`.

### Permission Caching
`get_current_user_with_permissions()` caches `user → role → permissions` in a module-level dict with 5-minute TTL and a cap of 5000 entries. Call `invalidate_permission_cache(user_id)` whenever a user's role changes.

### Streaming
`stream_generate()` yields raw tokens. Exposed as `POST /api/v1/prompts/stream` returning `text/event-stream`. Tokens arrive as `data: <token>\n\n` SSE frames; stream ends with `data: [DONE]\n\n`. Streaming responses are not persisted to DB.

### Request Tracing
`RequestIDMiddleware` reads `X-Request-ID` from the incoming request (or generates a UUID), attaches it to `request.state.request_id`, and echoes it back with `X-Response-Time-Ms` on every response.

### Production Server
`gunicorn.conf.py` configures `(2 × CPU) + 1` workers using `UvicornWorker`, 120s timeout, graceful 30s shutdown, and worker recycling after 1000 requests.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Hexagonal architecture | Swappable LLM backends, testability, clear separation |
| Async throughout | Non-blocking I/O for LLM calls and DB operations |
| DB-driven RBAC | Dynamic permissions without code deploys |
| Pydantic for everything | Validation, settings, serialization, auto docs |
| Argon2id password hashing | Modern, memory-hard, recommended over bcrypt |
| Docker-first | Reproducible dev and deployment environment |
| JSON logging | Machine-parseable logs for observability |

---

## Data Flow Diagram

```
                    ┌──────────┐
                    │  Client  │
                    └────┬─────┘
                         │ HTTP
                    ┌────▼─────┐
                    │  Router  │  (FastAPI, Pydantic, JWT)
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
         │  Auth  │ │Prompts │ │ Admin  │
         │Service │ │Service │ │Router  │
         └────┬───┘ └───┬────┘ └───┬────┘
              │         │          │
              │    ┌────▼─────┐    │
              │    │ LLMInter-│    │
              │    │  face    │    │
              │    └────┬─────┘    │
              │         │          │
         ┌────▼─────────▼──────────▼────┐
         │         PostgreSQL            │
         │  (users, prompts, roles,      │
         │   permissions)                │
         └───────────┬──────────────────┘
                     │
         ┌───────────▼──────────────────┐
         │       Ollama (local LLM)      │
         └───────────────────────────────┘
```

---

## Related Docs

- [API Reference](api/reference.md)
- [Configuration](guides/configuration.md)
- [Extending LLM Providers](guides/extending-llm.md)
- [RBAC Guide](guides/rbac.md)
- [Testing Guide](development/testing.md)
