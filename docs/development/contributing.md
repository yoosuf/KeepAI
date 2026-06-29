# Contributing to KeepAI

First off, thanks for taking the time to contribute!

The following is a set of guidelines for contributing to this project. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

---

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](../community/code-of-conduct.md). By participating, you are expected to uphold this code.

---

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/KeepAI.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Set up your local environment (see below)
5. Make your changes
6. Run tests and linting
7. Commit and push
8. Open a pull request

---

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose v2+ (recommended)
- PostgreSQL 15 (if running without Docker)
- Ollama (running locally or in Docker)
- Node.js 20+ (for frontend development)

### Local Development (Backend)

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your local settings

# Run migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Local Development (Frontend)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server (proxies /api to localhost:8000)
npm run dev
```

### Docker Development

```bash
docker compose -f docker/docker-compose.yml up --build
```

---

## Project Structure

The project is a monorepo with two main directories:

```
KeepAI/
+-- backend/                  # Python FastAPI backend
|   +-- src/
|   |   +-- main.py           # FastAPI app entrypoint
|   |   +-- core/             # Core domain and interfaces
|   |   |   +-- config.py     # Pydantic settings
|   |   |   +-- database.py   # DB session management
|   |   |   +-- middleware.py # Request ID middleware
|   |   |   +-- rate_limit.py # Slowapi rate limiter
|   |   |   +-- interfaces/   # Abstract interfaces (ports)
|   |   |       +-- llm_interface.py
|   |   +-- infrastructure/   # Adapters
|   |   |   +-- llm/
|   |   |       +-- ollama_client.py
|   |   +-- modules/          # Feature modules
|   |       +-- admin/        # Admin endpoints
|   |       +-- analytics/    # Usage analytics
|   |       +-- api_keys/     # API key management
|   |       +-- auth/         # Authentication
|   |       +-- conversations/ # Conversation threads
|   |       +-- documents/    # Document RAG
|   |       +-- models/       # Model management
|   |       +-- prompts/      # Prompt CRUD
|   |       +-- rag/          # RAG (stub)
|   |       +-- ws/           # WebSocket chat
|   +-- tests/                # Backend tests
|   +-- alembic/              # Database migrations
+-- frontend/                 # React TypeScript frontend
|   +-- src/
|       +-- main.tsx          # React entry
|       +-- App.tsx           # Routes and layout
|       +-- context/          # Auth context
|       +-- api/              # API client functions
|       +-- pages/            # Page components
|       +-- components/       # Shared components
|       +-- types/            # TypeScript interfaces
+-- docker/                   # Docker configs
|   +-- docker-compose.yml
|   +-- backend/Dockerfile
|   +-- frontend/Dockerfile
|   +-- frontend/nginx.conf
+-- docs/                     # Documentation
```

### Module Pattern

Each feature module follows Clean Architecture:

```
src/modules/{feature}/
+-- __init__.py
+-- models.py        # SQLAlchemy ORM models
+-- schemas.py       # Pydantic request/response schemas
+-- service.py       # Business logic
+-- router.py        # FastAPI route definitions
+-- utils.py         # Helper functions (optional)
+-- agents/
    +-- {agent}.py   # Domain-specific LLM agents
```

---

## Coding Standards

### Python

We use **Ruff** for linting and formatting. Configuration is in `backend/pyproject.toml`.

```bash
cd backend
ruff check src/ tests/
ruff format src/ tests/
```

### Style Guide

- **Line length**: 120 characters
- **Quotes**: Double quotes (`"`)
- **Imports**: isort-style (stdlib, third-party, local) with blank lines between groups
- **Type hints**: Required for all function signatures
- **Async**: Use async/await for I/O operations (DB, HTTP calls)
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants
- **Docstrings**: Use docstrings for public modules, classes, and functions

### TypeScript

- **Strict mode** enabled in `tsconfig.json`
- **Naming**: `camelCase` for variables/functions, `PascalCase` for components/types/interfaces
- **Imports**: Use named exports, group by external/internal

### Architecture Principles

- **Interface segregation**: Depend on abstractions, not concretions
- **Dependency injection**: Pass dependencies through constructors or function parameters
- **Separation of concerns**: Each module has router, service, schemas, models
- **Testability**: Write tests for all services with mocked dependencies

---

## Testing

### Backend

```bash
cd backend

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src

# Run specific test file
python -m pytest tests/api/test_auth.py

# Run tests matching a pattern
python -m pytest -k "invoice"
```

### Frontend

```bash
cd frontend

# TypeScript type check
npx tsc --noEmit

# Build (smoke test)
npm run build
```

### Test Guidelines

- Write tests for **services** with mocked LLM and database
- Write tests for **API endpoints** with mocked dependencies
- Use pytest fixtures from `tests/conftest.py` for common setup
- Tests should be fast — mock external services
- Name test files with `test_` prefix

---

## Pull Request Process

1. Ensure all tests pass: `python -m pytest` (backend) + `npm run build` (frontend)
2. Ensure linting passes: `ruff check .` (Python)
3. Update documentation if you change APIs
4. Add tests for new features
5. Update the [Changelog](../community/changelog.md) with your changes
6. PRs require at least one review before merging
7. Squash commits before merging

### PR Title Format

```
<type>: <short description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`

Example: `feat: add streaming response support`

---

## Reporting Bugs

Bugs are tracked as [GitHub Issues](https://github.com/yoosuf/KeepAI/issues).

Before submitting:
1. Check if the bug has already been reported
2. Check if it exists in the latest version
3. Include detailed steps to reproduce
4. Include logs, screenshots, and environment details

---

## Suggesting Features

Feature suggestions are welcome! Please:
1. Check existing issues for similar requests
2. Describe the problem you're solving
3. Explain the proposed solution
4. Include any alternative approaches considered

---

## Additional Resources

- [Getting Started](../getting-started.md) — Project overview
- [Architecture](../architecture.md) — System design
- [API Reference](../api/reference.md) — Full API reference
- [Deployment Guide](../guides/deployment.md) — Production deployment
- [Next Steps](../next-steps.md) — Planned improvements

---

**Thank you for contributing!** Every issue, feature request, and pull request makes this project better for everyone.
