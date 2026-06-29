<div align="center">
  <img src=".github/banner.svg" alt="KeepAI Banner" width="100%">

  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg?style=flat&logo=python&logoColor=white" alt="Python 3.11+"></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI"></a>
    <a href="https://ollama.ai/"><img src="https://img.shields.io/badge/Ollama-Local%20LLM-5B5B5B?style=flat" alt="Ollama"></a>
    <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
    <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat" alt="MIT License"></a>
    <a href="https://github.com/yoosuf/KeepAI/actions"><img src="https://img.shields.io/github/actions/workflow/status/yoosuf/KeepAI/ci.yml?style=flat&logo=githubactions&logoColor=white&label=CI" alt="CI"></a>
    <a href="https://github.com/yoosuf/KeepAI/stargazers"><img src="https://img.shields.io/github/stars/yoosuf/KeepAI?style=flat&logo=github" alt="Stars"></a>
  </p>

  <p>
    <a href="#-quick-start">Quick Start</a> ·
    <a href="#-features">Features</a> ·
    <a href="#-api">API</a> ·
    <a href="#-architecture">Architecture</a> ·
    <a href="docs/index.md">Docs</a> ·
    <a href="docs/community/roadmap.md">Roadmap</a>
  </p>
</div>

---

**KeepAI** is a privacy-first, production-ready FastAPI backend for running large language models on your own infrastructure. JWT auth, database-driven RBAC, streaming, structured JSON extraction — all included. No data sent to third parties.

---

## Why KeepAI?

Every AI SaaS sends your data to someone else's server. KeepAI runs entirely on your infrastructure — LLM inference, storage, auth.

| | KeepAI | OpenAI API |
|---|---|---|
| **Data privacy** | Stays on your server | Sent to OpenAI |
| **Cost** | Free (hardware only) | Per-token billing |
| **Model choice** | 100+ via Ollama | GPT family only |
| **Auth & RBAC** | Built-in | Not included |
| **Streaming** | SSE built-in | Supported |
| **Persistence** | PostgreSQL | No storage |
| **LLM provider** | Swappable | Locked in |

---

## Features

- **Local LLM inference** — Llama 3, Mistral, CodeLlama, DeepSeek, Phi, and 100+ models via Ollama
- **JWT authentication** — register, login, token-based auth with Argon2id password hashing
- **Database-driven RBAC** — roles and permissions in PostgreSQL, enforced per-route
- **Streaming responses** — Server-Sent Events (SSE) via `POST /api/v1/prompts/stream`
- **Structured JSON extraction** — invoke `InvoiceAgent` to extract typed data from freeform text
- **Swappable LLM backend** — implement `LLMInterface` to use OpenAI, Anthropic, or any provider
- **Connection pooling** — SQLAlchemy async engine with configurable pool sizes
- **Rate limiting** — per-user (JWT) or per-IP via `slowapi`
- **Permission caching** — 5-minute in-memory cache for role lookups
- **Request tracing** — `X-Request-ID` and `X-Response-Time-Ms` on every response
- **Health checks** — `/health/live` (liveness) and `/health/ready` (DB + Ollama readiness)
- **Docker ready** — one command to start the full stack
- **Production server** — Gunicorn + UvicornWorker, auto-sized worker count
- **Tested** — `pytest` + `asyncio` + `AsyncMock`, no real DB or LLM required

---

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/yoosuf/KeepAI.git
cd KeepAI
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec ollama ollama pull llama3
```

API: `http://localhost:8000` · Swagger: `http://localhost:8000/docs`

### Local development

```bash
git clone https://github.com/yoosuf/KeepAI.git
cd KeepAI
python -m venv .venv && source .venv/bin/activate
cd backend
pip install -r requirements.txt
cp .env.example .env          # edit POSTGRES_* and OLLAMA_BASE_URL
alembic upgrade head
uvicorn src.main:app --reload --port 8000
```

### First API call

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpass"}'

# Login — capture the token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=you@example.com" -F "password=yourpass" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Send a prompt
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Explain quantum computing in 3 sentences."}'

# Stream a response
curl -N -X POST http://localhost:8000/api/v1/prompts/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Write a haiku about code."}'
```

---

## API

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/health/live` | — | Liveness check |
| `GET` | `/health/ready` | — | Readiness (DB + Ollama) |
| `POST` | `/api/v1/auth/register` | — | Register a new user |
| `POST` | `/api/v1/auth/login` | — | Login, get JWT token |
| `POST` | `/api/v1/prompts` | JWT | Send a prompt, save response |
| `GET` | `/api/v1/prompts` | JWT | List your prompts |
| `GET` | `/api/v1/prompts/{id}` | JWT | Get a specific prompt |
| `POST` | `/api/v1/prompts/stream` | JWT | Stream response as SSE |
| `POST` | `/api/v1/extract-invoice` | JWT | Extract structured JSON from text |
| `GET` | `/api/v1/admin/users` | Admin | List all users |
| `GET` | `/api/v1/admin/all-prompts` | Admin | List all prompts across users |

Full reference with examples: [docs/api/reference.md](docs/api/reference.md)

---

## Architecture

```
Client
  │
  ▼
Router          FastAPI · Pydantic validation · JWT extraction
  │
  ▼
Service         Business logic · LLMInterface call
  │
  ├──────────────────────────┐
  ▼                          ▼
LLMInterface (port)       PostgreSQL
  │                     async SQLAlchemy
  ▼
OllamaClient (adapter)
  │
  ▼
Ollama HTTP API
```

**Hexagonal (ports & adapters)** — routers depend on services, services depend on interfaces, infrastructure implements interfaces. The domain layer has zero framework dependencies.

```
src/
├── core/
│   ├── config.py              # Pydantic BaseSettings
│   ├── database.py            # Async engine, session factory
│   ├── interfaces/
│   │   └── llm_interface.py   # LLMInterface ABC (the port)
│   ├── middleware.py          # Request ID + response time headers
│   └── rate_limit.py          # slowapi limiter
├── infrastructure/
│   └── llm/
│       └── ollama_client.py   # OllamaClient (the adapter)
└── modules/
    ├── auth/                  # models · schemas · service · utils · router
    ├── prompts/               # models · schemas · service · agents · router
    └── admin/                 # router (permission-gated)
```

To swap the LLM backend: implement `LLMInterface` and inject it in `get_prompt_service()`. One file change. See [docs/guides/extending-llm.md](docs/guides/extending-llm.md) for complete OpenAI, Anthropic, and vLLM examples.

Full architecture doc: [docs/architecture.md](docs/architecture.md)

---

## Use Cases

**Document intelligence** — extract invoices, contracts, and forms as structured JSON without sending data to a cloud service.

**Healthcare & legal** — process patient records, clinical notes, or legal documents on-premises. HIPAA/GDPR-friendly by design.

**Enterprise assistant** — deploy behind your firewall with role-based access for different teams. Admins see everything; users see their own prompts.

**Research** — run AI workloads on sensitive datasets that cannot leave your environment.

**LLM API gateway** — use as a drop-in backend for your own frontend, with auth, rate limiting, and persistence already wired up.

---

## Documentation

| | |
|---|---|
| [Getting Started](docs/guides/getting-started.md) | Local setup, Docker, first API calls |
| [Configuration](docs/guides/configuration.md) | All environment variables |
| [Deployment](docs/guides/deployment.md) | Production, HTTPS, hardening, backups |
| [Architecture](docs/architecture.md) | Layers, request flow, design decisions |
| [API Reference](docs/api/reference.md) | All endpoints with curl examples |
| [Extending LLM Providers](docs/guides/extending-llm.md) | Add OpenAI, Anthropic, vLLM |
| [RBAC Guide](docs/guides/rbac.md) | Roles, permissions, migrations |
| [Testing Guide](docs/development/testing.md) | AsyncMock patterns, fixtures |
| [Contributing](docs/development/contributing.md) | Dev setup, standards, PR process |
| [FAQ](docs/community/faq.md) | Common questions |
| [Troubleshooting](docs/community/troubleshooting.md) | Common issues and fixes |
| [Roadmap](docs/community/roadmap.md) | Planned features |
| [Changelog](docs/community/changelog.md) | Version history |

---

## Stack

| Layer | Technology |
|-------|-----------|
| API framework | FastAPI + Uvicorn |
| LLM runtime | Ollama |
| Database | PostgreSQL 15 + asyncpg |
| ORM & migrations | SQLAlchemy 2.0 async + Alembic |
| Auth | python-jose (JWT) + argon2-cffi |
| HTTP client | httpx (async) |
| Rate limiting | slowapi |
| Settings | pydantic-settings |
| Production server | Gunicorn + UvicornWorker |
| Testing | pytest + pytest-asyncio + httpx |
| Linting | Ruff |
| Container | Docker + Docker Compose |

---

## Roadmap

Completed in v1.0:
- JWT auth, Argon2id hashing, database-driven RBAC
- PostgreSQL persistence, Alembic migrations
- Streaming SSE responses
- Structured JSON extraction (InvoiceAgent)
- Connection pooling, rate limiting, permission caching, request tracing
- Docker Compose, Gunicorn production config, CI

Completed in v1.2:
- Conversation history, WebSocket chat, React frontend (9 pages)
- Multi-model routing, API key management, document RAG
- Usage analytics and audit logging schema
- Docker files consolidated in docker/ directory

Up next:
- [ ] Semantic search (pgvector), context-aware document chat
- [ ] Redis caching, async task queue
- [ ] SSO/OAuth, multi-tenant support
- [ ] Prometheus metrics, Grafana dashboards

[Full roadmap →](docs/community/roadmap.md)

---

## Contributing

See [Contributing Guide](docs/development/contributing.md) and [Code of Conduct](docs/community/code-of-conduct.md).

```bash
# Run tests (from backend/)
cd backend && python -m pytest

# Lint (from backend/)
cd backend && ruff check src/ tests/
```

PRs welcome — bug fixes, features, and documentation improvements.

---

## Security

Found a vulnerability? Email **mayoosuf@gmail.com** — do not open a public issue. See [Security Policy](docs/community/security.md).

---

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  <b>Yoosuf Mohamed</b> · <a href="mailto:mayoosuf@gmail.com">mayoosuf@gmail.com</a> · <a href="https://github.com/yoosuf/KeepAI">github.com/yoosuf/KeepAI</a>
</p>
