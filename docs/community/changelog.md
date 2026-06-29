# Changelog

All notable changes to KeepAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-06

### Added

- **React frontend** (9 pages) — Chat, Conversations, History, Playground, Models, API Keys, Documents, Analytics, Admin
- **WebSocket chat** — real-time conversation interface with token-authenticated WebSocket
- **Conversation threads** — persistent messages with conversation CRUD via WebSocket
- **API key management** — create, revoke, SHA-512 hashed keys with `ka_` prefix
- **Document RAG** — upload, chunk, keyword search, query LLM with document context
- **Usage analytics** — dashboard with request counts, processing time, model/action breakdown
- **Audit logging schema** — `audit_logs` table (not yet wired to endpoints)
- **Monorepo restructure** — `backend/` and `frontend/` with root `docker/` directory
- **Root `.dockerignore`** — single dockerignore for monorepo Docker builds
- **350 lines of CSS** — chat sidebar, data tables, stat cards, bar charts, badges, forms, search results

### Fixed

- User.role type mismatch (object → string) in frontend
- JWT missing `user_id` claim — added to backend, decoded in AuthContext
- Hardcoded WebSocket URL — now derived from `window.location`
- Missing `message_count`, `user_id`, `created_at`, `updated_at` in WebSocket responses
- Missing `temperature`, `top_p`, `max_tokens` in ChatRequest type
- Missing `updated_at` field in PromptResponse schema
- Admin pagination API functions now accept skip/limit
- Document search sends top_k parameter
- Playground invoice extraction tab wired up

### Changed

- All Docker configs moved to `docker/` directory
- Frontend proxies `/api` to `localhost:8000` in dev
- Nginx proxies `/api` to `backend:8000` in Docker prod

## [1.1.0] - 2026-03

### Added

- Server-Sent Events (SSE) streaming for prompts and chat
- Multi-model routing via `MODEL_ROUTING` env var
- Model management API (list, pull, delete)
- Custom system prompts per request
- Temperature, top_p, max_tokens parameter control
- Rate limiting with slowapi (RATE_LIMIT_LLM env var)
- Prompt history browser with pagination

## [1.0.0] - 2026-01-15

### Added

- FastAPI application with clean architecture (hexagonal/ports-and-adapters)
- Local LLM inference via Ollama integration (LLMInterface + OllamaClient)
- JWT authentication — register, login, token-based auth
- Database-driven RBAC — dynamic roles and permissions in PostgreSQL
- Structured JSON extraction — invoice extraction with InvoiceAgent
- Prompt management — CRUD for prompts with user scoping
- Admin endpoints — list users, list all prompts (permission-gated)
- PostgreSQL persistence with async SQLAlchemy 2.0
- Alembic migrations — 4 migrations covering prompts, users, roles, permissions
- Docker & Docker Compose — one-command startup
- Structured JSON logging — JSON-formatted stdout logs
- Health check endpoints — `/health/live` and `/health/ready`
- Comprehensive test suite — pytest + async tests + coverage
- Ruff linting — pycodestyle, pyflakes, isort, flake8-bugbear
- GitHub Actions CI — lint + test on every push/PR to main
- Seed script — pre-populate database with test users

### Security

- Argon2id password hashing
- JWT token expiry (30 min default)
- Non-root user in Docker container
- Environment-based configuration via pydantic-settings
