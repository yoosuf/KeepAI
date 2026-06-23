# Changelog

All notable changes to KeepAI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-15

### Added

- **FastAPI application** with clean architecture (hexagonal/ports-and-adapters)
- **Local LLM inference** via Ollama integration (`LLMInterface` + `OllamaClient`)
- **JWT authentication** — register, login, token-based auth
- **Database-driven RBAC** — dynamic roles and permissions in PostgreSQL
- **Structured JSON extraction** — invoice extraction with `InvoiceAgent`
- **Prompt management** — CRUD for prompts with user scoping
- **Admin endpoints** — list users, list all prompts (permission-gated)
- **PostgreSQL persistence** with async SQLAlchemy 2.0
- **Alembic migrations** — 4 migrations covering prompts, users, roles, permissions
- **Docker & Docker Compose** — one-command startup
- **Structured JSON logging** — JSON-formatted stdout logs
- **Health check endpoint** — `/health`
- **Comprehensive test suite** — pytest + async tests + coverage
- **Ruff linting** — pycodestyle, pyflakes, isort, flake8-bugbear
- **GitHub Actions CI** — lint + test on every push/PR to main
- **Seed script** — pre-populate database with test users

### Security

- bcrypt password hashing
- JWT token expiry (30 min default)
- Non-root user in Docker container
- Environment-based configuration via pydantic-settings
