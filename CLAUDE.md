# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

KeepAI is a privacy-first FastAPI backend for running local LLMs (via Ollama) with JWT authentication, database-driven RBAC, and structured JSON extraction. It is designed as a reusable foundation — swap Ollama for any LLM provider by implementing `LLMInterface`.

## Commands

### Local Development (without Docker)

```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
# or: python src/main.py
```

### Docker (full stack)

```bash
docker compose up --build -d
docker compose exec ollama ollama pull llama3   # pull a model once
```

### Database

```bash
# Navigate to backend first
cd backend

# Apply all migrations
alembic upgrade head

# Create a new migration (after changing SQLAlchemy models)
alembic revision --autogenerate -m "description"

# Rollback one step
alembic downgrade -1
```

### Testing

```bash
# Navigate to backend first
cd backend

# Run all tests with coverage
pytest

# Run a single test file
pytest tests/api/test_auth.py -v

# Run a single test by name
pytest tests/api/test_auth.py::test_register_user_success -v

# Run without coverage
pytest --no-cov
```

### Linting

```bash
# Navigate to backend first
cd backend

# Lint and format check
ruff check src/ tests/
ruff format --check src/ tests/

# Auto-fix and format
ruff check --fix src/ tests/
ruff format src/ tests/
```

## Architecture

### Layered (Hexagonal) Structure

```
Presentation  →  src/modules/*/router.py       (FastAPI routes, Pydantic validation)
Application   →  src/modules/*/service.py      (business logic, orchestration)
Domain        →  src/core/interfaces/          (abstract ports, e.g. LLMInterface)
Infrastructure → src/infrastructure/           (concrete adapters, e.g. OllamaClient)
```

The **dependency rule**: routers depend on services; services depend on interfaces; infrastructure implements interfaces. The domain layer (`src/core/interfaces/`) has zero framework dependencies.

### Request Lifecycle

`POST /api/v1/prompts` →
1. Router validates request via Pydantic, extracts `current_user` from JWT dependency
2. `PromptService.create_prompt()` calls `llm_client.generate()` (via `LLMInterface`)
3. `OllamaClient` posts to Ollama HTTP API (`/api/generate`)
4. Response + metadata persisted to PostgreSQL via async SQLAlchemy
5. Router serializes `Prompt` ORM object to `PromptResponse` Pydantic schema

### Module Layout

Each feature lives in `src/modules/{feature}/` with consistent files:
- `models.py` — SQLAlchemy ORM models (source of truth for DB schema)
- `schemas.py` — Pydantic request/response schemas (separate from ORM models)
- `service.py` — business logic, injected with `db` and `llm_client`
- `router.py` — FastAPI routes; wires dependencies and calls service
- `agents/` — domain-specific LLM agents (prompt templates + response parsers)

### Authentication & RBAC

- **Register**: hashes password with Argon2id → stores in `users` table with a role FK
- **Login**: verifies hash → issues HS256 JWT (30 min expiry by default)
- **Request auth**: `get_current_user` dependency decodes JWT, fetches user from DB
- **Permission check**: `PermissionChecker("permission:name")` is a FastAPI dependency class — it eagerly loads `user → role → permissions` and returns 403 if the permission is missing
- **RBAC data**: `roles`, `permissions`, `role_permissions` tables; seeded in migration `000000000003_db_rbac.py`
- Built-in permissions: `users:read`, `prompts:read_all`, `prompts:create`
- Built-in roles: `admin` (all permissions), `user` (`prompts:create` only)

### LLM Abstraction

`LLMInterface` (ABC) in `src/core/interfaces/llm_interface.py` defines a single method:

```python
async def generate(self, prompt: str, model: str, **kwargs) -> Dict[str, Any]:
    # Must return: {"response_text": str, "processing_time_ms": int, "meta_data": dict}
```

`OllamaClient` in `src/infrastructure/llm/ollama_client.py` is the only concrete implementation. To add a new LLM provider (OpenAI, Anthropic, etc.), implement `LLMInterface` and inject it in `src/modules/prompts/router.py::get_prompt_service`.

### Configuration

All settings live in `src/core/config.py` as a Pydantic `BaseSettings` class, loaded from `.env`. Required env vars: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_DB`. Optional defaults exist for everything else. `DATABASE_URL` is a computed property — never set it directly.

### Key Env Vars

| Variable | Default | Notes |
|---|---|---|
| `POSTGRES_SERVER` | (required) | `db` in Docker, `localhost` for local |
| `SECRET_KEY` | `changethis` | Override for production (`openssl rand -hex 32`) |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | `http://localhost:11434` for local |
| `OLLAMA_MODEL` | `llama3` | Any model pulled in Ollama |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT expiry |

## Testing Patterns

Tests never hit a real database or Ollama. Dependencies are overridden via FastAPI's `app.dependency_overrides`:

```python
app.dependency_overrides[get_db] = lambda: mock_db_session
```

`conftest.py` sets dummy `POSTGRES_*` env vars **before** importing `src.main` to prevent Pydantic settings from raising validation errors. Service-layer tests inject mock `AsyncMock` for both `db` and `llm_client` directly into `PromptService(db=mock_db, llm_client=mock_llm)`.

## Scalability Features

### Connection Pooling
SQLAlchemy engine is configured via `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_TIMEOUT`, `DB_POOL_RECYCLE` in `.env`. Defaults handle ~30 concurrent requests; tune for your load.

### Rate Limiting
`slowapi` rate limiter lives in `src/core/rate_limit.py`. Key function extracts user email from JWT (falls back to IP). Apply to a route with `@limiter.limit(settings.RATE_LIMIT_LLM)` and add `request: Request` as first parameter. For multi-instance deployments, swap the `Limiter` storage to Redis: `Limiter(key_func=..., storage_uri="redis://redis:6379")`.

### Permission Caching
`get_current_user_with_permissions()` in `src/modules/auth/service.py` caches loaded role+permissions in a module-level dict with a 5-minute TTL (max 5000 entries). Call `invalidate_permission_cache(user_id)` whenever a user's role changes.

### Streaming
`LLMInterface.stream_generate()` yields raw text tokens. `OllamaClient` implements it via httpx streaming against Ollama's `stream=True` mode. Exposed as `POST /api/v1/prompts/stream` returning `text/event-stream`. Tokens arrive as `data: <token>\n\n` SSE frames; stream ends with `data: [DONE]\n\n`. Not persisted to DB.

### Health Checks
- `GET /health/live` — liveness (always 200 if process is up)
- `GET /health/ready` — readiness (pings DB with `SELECT 1` + Ollama `/api/tags`; returns 503 if either is down)

### Production Server
`gunicorn.conf.py` configures `(2 × CPU) + 1` workers using `UvicornWorker`, 120s timeout, graceful 30s shutdown, and worker recycling after 1000 requests. Set `DEV_MODE=true` in `.env` to use uvicorn `--reload` instead.

### Request Tracing
`RequestIDMiddleware` (`src/core/middleware.py`) reads `X-Request-ID` header (or generates a UUID), attaches it to `request.state.request_id`, and echoes it back with `X-Response-Time-Ms` on every response.

## Extending the LLM Backend

To add a new LLM provider (OpenAI, Anthropic, etc.):
1. Create `src/infrastructure/llm/{provider}_client.py` implementing `LLMInterface`
2. The `generate()` method must return `{"response_text": str, "processing_time_ms": int, "meta_data": dict}`
3. Swap it into `get_prompt_service()` in `src/modules/prompts/router.py`

To add a new domain agent (like `InvoiceAgent`):
1. Add `src/modules/prompts/agents/{name}_agent.py` with a static prompt builder and response parser
2. Add a method to `PromptService` and a route in `src/modules/prompts/router.py`
