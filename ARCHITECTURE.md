# Architecture

KeepAI follows **Clean Architecture** principles (also known as Hexagonal Architecture or Ports and Adapters).

---

## Layered Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Presentation Layer                    │
│  FastAPI Routers (src/modules/*/router.py)                │
│  - Auth routes (register, login)                          │
│  - Prompt routes (create, list, get)                      │
│  - Admin routes (list users, all prompts)                 │
│  - Invoice extraction route                               │
├──────────────────────────────────────────────────────────┤
│                    Application Layer                       │
│  Services (src/modules/*/service.py)                      │
│  - AuthService (user creation, credential validation)      │
│  - PromptService (prompt creation, LLM interaction)       │
│  - Business logic, orchestration                          │
├──────────────────────────────────────────────────────────┤
│                      Domain Layer                          │
│  Interfaces (src/core/interfaces/)                        │
│  - LLMInterface (abstract port for LLM interactions)      │
│  - Domain models, schemas                                 │
├──────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                     │
│  Adapters (src/infrastructure/)                           │
│  - OllamaClient (concrete LLM adapter)                    │
│  - Database (SQLAlchemy models, session management)       │
│  - Auth utilities (JWT, password hashing)                 │
└──────────────────────────────────────────────────────────┘
```

### Dependency Rule

Dependencies point **inward**. The outer layers depend on inner layers, never the reverse:

- **Presentation** → **Application** → **Domain** ← **Infrastructure**

The **Domain** layer has zero dependencies on frameworks or external systems. It defines interfaces (ports) that the infrastructure layer implements (adapters).

---

## Request Flow

```
Client Request
      │
      ▼
   Router (presentation)
      │  Validates request (Pydantic schemas)
      │  Extracts user from JWT (dependency)
      ▼
   Service (application)
      │  Orchestrates business logic
      │  Calls port interface
      ▼
   LLMInterface (domain port)
      │  Abstract contract
      ▼
   OllamaClient (infrastructure adapter)
      │  Calls Ollama HTTP API
      ▼
   LLM Response
      │
      ▼
   Back to Router → JSON Response
```

### Example: Prompt Creation

1. `POST /prompts` → `Router.create_prompt()`
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
├── __init__.py
├── models.py        # SQLAlchemy ORM models
├── schemas.py       # Pydantic request/response schemas
├── service.py       # Business logic
├── router.py        # FastAPI route definitions
├── utils.py         # Helper functions (optional)
└── agents/
    ├── __init__.py
    └── {agent}.py   # Domain-specific LLM agents (e.g., InvoiceAgent)
```

### Auth Module

| Component | File | Responsibility |
|---|---|---|
| Models | `models.py` | `User`, `Role`, `Permission`, `role_permissions` tables |
| Schemas | `schemas.py` | Registration/login request/response schemas |
| Service | `service.py` | User creation, credential verification |
| Utils | `utils.py` | Password hashing (bcrypt), JWT creation/verification |
| Router | `router.py` | `/register`, `/login` endpoints |

### Prompts Module

| Component | File | Responsibility |
|---|---|---|
| Models | `models.py` | `Prompt` table |
| Schemas | `schemas.py` | Prompt request/response schemas |
| Service | `service.py` | Prompt creation, listing, invoice extraction |
| Router | `router.py` | Prompt CRUD, invoice extraction endpoints |
| Agents | `agents/invoice_agent.py` | Invoice-specific prompt templates and response parsing |

### Admin Module

| Component | File | Responsibility |
|---|---|---|
| Router | `router.py` | Admin-only endpoints with `PermissionChecker` dependency |

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
    SECRET_KEY: str = "changethis"  # Override in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3"
```

### Database (`src/core/database.py`)

- `AsyncSessionLocal` — SQLAlchemy async session factory
- `get_db()` — FastAPI dependency that yields a DB session
- `Base` — SQLAlchemy declarative base

### LLM Interface (`src/core/interfaces/llm_interface.py`)

```python
class LLMInterface(ABC):
    @abstractmethod
    async def generate(self, prompt: str, model: str = "", **kwargs) -> dict:
        ...
```

### Ollama Client (`src/infrastructure/llm/ollama_client.py`)

Concrete adapter implementing `LLMInterface`. Calls Ollama's `/api/generate` via `httpx.AsyncClient`.

---

## Authentication & Authorization

### Flow

1. **Register** → Email + password → bcrypt hash → stored in `users` table
2. **Login** → Email + password → verify hash → issue JWT (30 min expiry)
3. **Request** → JWT in `Authorization` header → decode → extract user → inject as dependency

### RBAC

- `PermissionChecker` is a FastAPI dependency class parameterized with a required permission name
- It eagerly loads the user's role and permissions
- If the required permission is not found, returns 403
- Permissions and roles are stored in DB tables (`permissions`, `roles`, `role_permissions`)

---

## Data Flow Diagram

```
                    ┌──────────┐
                    │  Client   │
                    └────┬─────┘
                         │ HTTP
                    ┌────▼─────┐
                    │  Router   │
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
         │  Auth  │ │ Prompts│ │ Admin  │
         │Service │ │Service │ │Router  │
         └────┬───┘ └───┬────┘ └───┬────┘
              │         │          │
              │    ┌────▼─────┐    │
              │    │LLMInter- │    │
              │    │ face     │    │
              │    └────┬─────┘    │
              │         │          │
         ┌────▼─────────▼──────────▼──┐
         │       PostgreSQL            │
         │   (users, prompts, roles,   │
         │    permissions)             │
         └───────────┬────────────────┘
                     │
         ┌───────────▼────────────────┐
         │     Ollama (local LLM)      │
         └────────────────────────────┘
```

---

## Testing Strategy

```
tests/
├── conftest.py           # Shared fixtures (app client, mock env)
├── test_main.py          # Health check test
├── api/
│   └── test_auth.py      # Auth endpoint tests
└── services/
    └── test_prompt_service.py  # Prompt service tests (mocked LLM + DB)
```

- **Services** are tested with mocked LLM and database dependencies
- **API endpoints** are tested via `httpx.AsyncClient` against the FastAPI app
- **External systems** (Ollama, PostgreSQL) are always mocked in unit tests
- Tests use `pytest-asyncio` for async support

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Hexagonal architecture** | Swappable LLM backends, testability, separation of concerns |
| **Async throughout** | Non-blocking I/O for LLM calls and database operations |
| **DB-driven RBAC** | Dynamic permissions without code changes |
| **Pydantic for everything** | Validation, settings, serialization, docs generation |
| **Docker first** | Reproducible development and deployment environment |
| **JSON logging** | Machine-parseable logs for observability and monitoring |

---

## Related Documents

- [README.md](README.md) — Project overview and quick start
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) — Complete API reference
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) — Production deployment
- [CONTRIBUTING.md](CONTRIBUTING.md) — Development guidelines
