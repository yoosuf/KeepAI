# Changelog

All notable changes to KeepAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

_Changes in development, not yet released._

---

## [1.0.0] - 2026-01-15

### Added

- FastAPI application with clean hexagonal architecture (ports and adapters)
- Local LLM inference via Ollama integration (`LLMInterface` + `OllamaClient`)
- JWT authentication — register, login, token-based auth
- Database-driven RBAC — dynamic roles and permissions in PostgreSQL
- Structured JSON extraction — invoice extraction with `InvoiceAgent`
- Prompt management — CRUD for prompts with per-user scoping
- Streaming responses — `POST /api/v1/prompts/stream` returning SSE
- Admin endpoints — list users, list all prompts (permission-gated)
- PostgreSQL persistence with async SQLAlchemy 2.0
- Alembic migrations — 4 migrations covering prompts, users, roles, permissions
- Docker & Docker Compose — one-command startup
- Structured JSON logging — machine-parseable stdout logs
- Health check endpoints — `/health/live` and `/health/ready`
- Connection pooling — configurable via `DB_POOL_*` env vars
- Rate limiting — `slowapi` per-user/per-IP limiter on LLM endpoints
- Permission caching — 5-minute TTL cache for `user → role → permissions`
- Request tracing — `X-Request-ID` and `X-Response-Time-Ms` headers on all responses
- Comprehensive test suite — pytest + async tests + coverage
- Ruff linting — pycodestyle, pyflakes, isort, flake8-bugbear
- GitHub Actions CI — lint + test on every push/PR to main
- Seed script — `src/scripts/seed_db.py`
- Production server config — `gunicorn.conf.py` with `(2 × CPU) + 1` workers

### Security

- Argon2id password hashing (replacing bcrypt)
- JWT token expiry (30 min default, configurable)
- Non-root user (`appuser`) in Docker container
- Environment-based configuration via pydantic-settings
