# Contributing to KeepAI

Thanks for taking the time to contribute! This document covers setup, coding standards, testing, and the pull request process.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](../community/code-of-conduct.md). By participating, you agree to uphold it.

---

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork: `git clone https://github.com/your-username/KeepAI.git`
3. Create a feature branch: `git checkout -b feat/my-feature`
4. Set up your local environment (see below)
5. Make your changes, add tests, run linting
6. Open a pull request

---

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 15 (if running without Docker)
- Ollama (if testing LLM endpoints locally)

### Local Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set POSTGRES_* and OLLAMA_BASE_URL for your local setup

# Run database migrations
alembic upgrade head

# Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Setup

```bash
docker compose up --build
```

Changes to Python files are not hot-reloaded in Docker by default. For rapid iteration, use the local setup above.

---

## Project Structure

```
src/
├── main.py                    # FastAPI app entry point, middleware registration
├── core/
│   ├── config.py              # Pydantic settings loaded from .env
│   ├── database.py            # Async engine, session factory, get_db()
│   ├── interfaces/
│   │   └── llm_interface.py   # LLMInterface ABC (the port)
│   ├── logging_config.py      # Structured JSON logging
│   ├── middleware.py          # RequestIDMiddleware
│   └── rate_limit.py          # slowapi Limiter
├── infrastructure/
│   └── llm/
│       └── ollama_client.py   # OllamaClient (the adapter)
├── modules/
│   ├── auth/                  # Auth: models, schemas, service, utils, router
│   ├── prompts/               # Prompts: models, schemas, service, agents, router
│   └── admin/                 # Admin: router only
└── scripts/
    └── seed_db.py             # Dev DB seeding

tests/
├── conftest.py                # Shared fixtures, mock env setup
├── test_main.py               # Health endpoint smoke test
├── api/
│   └── test_auth.py           # Auth endpoint integration tests
└── services/
    └── test_prompt_service.py # PromptService unit tests (mocked DB + LLM)
```

---

## Coding Standards

### Linting & Formatting

We use **Ruff** for both linting and formatting. Config is in `pyproject.toml`.

```bash
# Check for issues
ruff check src/ tests/

# Auto-fix
ruff check --fix src/ tests/

# Format
ruff format src/ tests/

# Check format without changing files
ruff format --check src/ tests/
```

CI will fail if either check fails.

### Style Guide

- **Line length**: 120 characters
- **Quotes**: Double (`"`)
- **Imports**: stdlib → third-party → local, blank lines between groups
- **Type hints**: Required on all public function signatures
- **Async**: Use `async/await` for all I/O (DB queries, HTTP calls)
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants
- **Comments**: Only when the *why* is non-obvious — no restating what the code does

### Architecture Principles

- **No cross-module imports at the model level** — modules communicate via service interfaces, not by importing each other's models
- **Dependency injection** — pass `db` and `llm_client` through constructors or FastAPI `Depends`
- **Thin routers** — routers validate, extract dependencies, call service, return response
- **No business logic in routers** — orchestration belongs in services

---

## Testing

We use `pytest` with `pytest-asyncio`. All external dependencies (DB, LLM) are mocked.

```bash
# Run all tests with coverage report
pytest

# Run a specific file
pytest tests/api/test_auth.py -v

# Run a specific test
pytest tests/api/test_auth.py::test_register_user_success -v

# Run without coverage (faster)
pytest --no-cov

# Run only tests matching a keyword
pytest -k "invoice"
```

See the full [Testing Guide](testing.md) for patterns, fixtures, and async patterns.

### Test Requirements

- Every new service method needs a unit test in `tests/services/`
- Every new endpoint needs an integration test in `tests/api/`
- Tests must pass without a real database or Ollama running
- Coverage must not decrease

---

## Pull Request Process

1. Ensure all tests pass: `pytest`
2. Ensure linting passes: `ruff check src/ tests/`
3. Update `docs/` if you change APIs, architecture, or add features
4. Update `docs/community/changelog.md` under `[Unreleased]`
5. PRs require at least one review approval before merging

### Commit Message Format

```
<type>: <short imperative description>
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`

Examples:
```
feat: add streaming response support
fix: handle missing model name in prompt creation
docs: add RBAC guide to /docs
test: add invoice extraction unit tests
```

### PR Title

Same format as commit messages. Keep it under 70 characters.

---

## Reporting Bugs

File a [GitHub Issue](https://github.com/yoosuf/KeepAI/issues). Include:

- Steps to reproduce
- Expected vs actual behavior
- Full error logs (from `docker compose logs backend`)
- Environment: OS, Docker version, Python version

---

## Suggesting Features

Open a [GitHub Issue](https://github.com/yoosuf/KeepAI/issues) with label `enhancement`. Describe:

- The problem you're solving
- The proposed solution
- Alternative approaches considered

---

## Additional Resources

- [Architecture](../architecture.md)
- [API Reference](../api/reference.md)
- [Deployment Guide](../guides/deployment.md)
- [Testing Guide](testing.md)
