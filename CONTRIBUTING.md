# Contributing to KeepAI

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to this project. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

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

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/fastapi-ollama-backend.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Set up your local environment (see below)
5. Make your changes
6. Run tests and linting
7. Commit and push
8. Open a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 15 (if running without Docker)
- Ollama (running locally or in Docker)

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies with dev tools
pip install -r requirements.txt
pip install ruff pytest pytest-asyncio pytest-cov httpx

# Copy and configure environment
cp .env.example .env
# Edit .env with your local settings

# Run migrations
alembic upgrade head

# Start the server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development

```bash
docker compose up --build
```

## Project Structure

The project follows **Clean Architecture** (ports and adapters / hexagonal):

```
src/
├── main.py                    # FastAPI app entrypoint
├── core/                      # Core domain & interfaces
│   ├── config.py              # Pydantic settings
│   ├── database.py            # DB session management
│   ├── logging_config.py      # Structured logging
│   └── interfaces/            # Abstract interfaces (ports)
│       └── llm_interface.py   # LLM port
├── infrastructure/            # Adapters (external integrations)
│   └── llm/
│       └── ollama_client.py   # Ollama adapter
├── modules/                   # Feature modules
│   ├── admin/                 # Admin endpoints
│   ├── auth/                  # Auth (models, schemas, service, utils)
│   └── prompts/               # Prompts (models, schemas, service, agents)
└── scripts/
    └── seed_db.py             # Database seeding
```

## Coding Standards

### Python

We use **Ruff** for linting and formatting. Configuration is in `pyproject.toml`.

```bash
# Run linting
ruff check .

# Run formatting
ruff format .
```

### Style Guide

- **Line length**: 120 characters
- **Quotes**: Double quotes (`"`)
- **Imports**: isort-style (stdlib, third-party, local) with blank lines between groups
- **Type hints**: Required for all function signatures
- **Async**: Use async/await for I/O operations (DB, HTTP calls)
- **Naming**: `snake_case` for variables/functions, `PascalCase` for classes, `UPPER_CASE` for constants
- **Docstrings**: Use docstrings for public modules, classes, and functions

### Architecture Principles

- **Interface segregation**: Depend on abstractions, not concretions
- **Dependency injection**: Pass dependencies through constructors or function parameters
- **Separation of concerns**: Each module has `router.py`, `service.py`, `schemas.py`, `models.py`
- **Testability**: Write tests for all services with mocked dependencies

## Testing

We use `pytest` with `pytest-asyncio` for async support.

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/api/test_auth.py

# Run tests matching a pattern
pytest -k "invoice"
```

### Test Guidelines

- Write tests for **services** with mocked LLM and database
- Write tests for **API endpoints** with mocked dependencies
- Use pytest fixtures from `tests/conftest.py` for common setup
- Tests should be fast — mock external services
- Name test files with `test_` prefix

## Pull Request Process

1. Ensure all tests pass: `pytest`
2. Ensure linting passes: `ruff check .`
3. Update documentation if you change APIs
4. Add tests for new features
5. Update the `CHANGELOG.md` with your changes
6. PRs require at least one review before merging
7. Squash commits before merging

### PR Title Format

```
<type>: <short description>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`

Example: `feat: add streaming response support`

## Reporting Bugs

Bugs are tracked as [GitHub Issues](https://github.com/yoosuf/KeepAI/issues).

Before submitting:
1. Check if the bug has already been reported
2. Check if it exists in the latest version
3. Include detailed steps to reproduce
4. Include logs, screenshots, and environment details

## Suggesting Features

Feature suggestions are welcome! Please:
1. Check existing issues for similar requests
2. Describe the problem you're solving
3. Explain the proposed solution
4. Include any alternative approaches considered

## Additional Resources

- [README.md](README.md) — Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) — System design
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) — Full API reference
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) — Production deployment

---

**Thank you for contributing!** Every issue, feature request, and pull request makes this project better for everyone.
