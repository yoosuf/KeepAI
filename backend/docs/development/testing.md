# Testing Guide

KeepAI tests never hit a real database or Ollama. All external dependencies are mocked via FastAPI's dependency override system and `AsyncMock`.

---

## Running Tests

```bash
# All tests with coverage report
pytest

# Specific file
pytest tests/api/test_auth.py -v

# Specific test
pytest tests/api/test_auth.py::test_register_user_success -v

# Without coverage (faster feedback loop)
pytest --no-cov

# Tests matching a keyword
pytest -k "invoice" -v

# Stop on first failure
pytest -x
```

---

## Test Structure

```
tests/
├── conftest.py                    # Fixtures: async client, mock env, mock DB
├── test_main.py                   # Smoke test: GET /health/live
├── api/
│   └── test_auth.py               # Auth endpoint integration tests
└── services/
    └── test_prompt_service.py     # PromptService unit tests (mocked)
```

---

## The conftest.py Pattern

The most important thing `conftest.py` does is set dummy `POSTGRES_*` environment variables **before** importing `src.main`. Without this, Pydantic `BaseSettings` raises a `ValidationError` because the required DB vars are missing.

```python
# tests/conftest.py
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient

# Set env vars BEFORE importing the app
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_SERVER", "localhost")
os.environ.setdefault("POSTGRES_DB", "test")

from src.main import app           # noqa: E402 — import after env setup
from src.core.database import get_db

@pytest_asyncio.fixture
async def client(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
def mock_db():
    from unittest.mock import AsyncMock, MagicMock
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session
```

---

## API (Integration) Tests

API tests send HTTP requests to the FastAPI app via `httpx.AsyncClient`. FastAPI's `dependency_overrides` replaces the real `get_db` with a mock session.

```python
# tests/api/test_auth.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.modules.auth.models import Role, User


@pytest.mark.asyncio
async def test_register_user_success(client, mock_db):
    # Arrange: simulate "no existing user" and "role found"
    mock_role = MagicMock(spec=Role)
    mock_role.id = 2

    no_user_result = MagicMock()
    no_user_result.scalars.return_value.first.return_value = None

    role_result = MagicMock()
    role_result.scalars.return_value.first.return_value = mock_role

    mock_db.execute = AsyncMock(side_effect=[no_user_result, role_result])
    mock_db.refresh = AsyncMock()

    # Act
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "testpass123"},
    )

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email(client, mock_db):
    existing_user = MagicMock(spec=User)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = existing_user
    mock_db.execute = AsyncMock(return_value=mock_result)

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "existing@example.com", "password": "pass"},
    )

    assert response.status_code == 400
```

---

## Service Unit Tests

Service tests bypass the router entirely and inject mocks directly into the service constructor. This isolates business logic from HTTP concerns.

```python
# tests/services/test_prompt_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.modules.prompts.service import PromptService
from src.modules.prompts.models import Prompt
from src.modules.auth.models import User


@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value={
        "response_text": "Machine learning is...",
        "processing_time_ms": 1234,
        "meta_data": {"model": "llama3"},
    })
    return llm


@pytest.fixture
def mock_user():
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    return user


@pytest.mark.asyncio
async def test_create_prompt(mock_db, mock_llm, mock_user):
    service = PromptService(db=mock_db, llm_client=mock_llm)

    saved_prompt = MagicMock(spec=Prompt)
    saved_prompt.id = 42
    saved_prompt.response_text = "Machine learning is..."

    mock_db.refresh = AsyncMock(side_effect=lambda p: setattr(p, "id", 42))

    result = await service.create_prompt(
        prompt_text="What is ML?",
        model_name="llama3",
        user=mock_user,
    )

    # LLM was called
    mock_llm.generate.assert_called_once()
    call_args = mock_llm.generate.call_args
    assert "What is ML?" in call_args.args[0] or call_args.kwargs.get("prompt") == "What is ML?"

    # DB was persisted
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
```

---

## Mocking the LLM Client

The `llm_client` is injected into `PromptService`, so you can mock it directly:

```python
from unittest.mock import AsyncMock

mock_llm = AsyncMock()
mock_llm.generate = AsyncMock(return_value={
    "response_text": "Hello!",
    "processing_time_ms": 100,
    "meta_data": {},
})

# For streaming
async def fake_stream(*args, **kwargs):
    for token in ["Hello", " ", "world"]:
        yield token

mock_llm.stream_generate = fake_stream
```

---

## Mocking the Database Session

Use `AsyncMock` for async methods and `MagicMock` for synchronous ones:

```python
from unittest.mock import AsyncMock, MagicMock

mock_db = AsyncMock()
mock_db.execute = AsyncMock()
mock_db.add = MagicMock()      # synchronous
mock_db.commit = AsyncMock()
mock_db.refresh = AsyncMock()

# Simulate a query result
result = MagicMock()
result.scalars.return_value.first.return_value = some_object  # return an entity
result.scalars.return_value.all.return_value = [obj1, obj2]   # return a list

mock_db.execute = AsyncMock(return_value=result)
```

For sequential calls returning different results:

```python
mock_db.execute = AsyncMock(side_effect=[result1, result2, result3])
```

---

## Testing Authentication-Protected Endpoints

To test protected endpoints, override `get_current_user`:

```python
from src.modules.auth.service import get_current_user
from src.modules.auth.models import User

@pytest_asyncio.fixture
async def authenticated_client(mock_db):
    fake_user = MagicMock(spec=User)
    fake_user.id = 1
    fake_user.email = "test@example.com"

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: fake_user

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

---

## Testing PermissionChecker

Override `get_current_user_with_permissions` to inject a user with specific permissions:

```python
from src.modules.auth.service import get_current_user_with_permissions

def make_user_with_permissions(*perm_names):
    perm_mocks = [MagicMock(name=n) for n in perm_names]
    role = MagicMock()
    role.permissions = perm_mocks
    user = MagicMock(spec=User)
    user.role = role
    return user

app.dependency_overrides[get_current_user_with_permissions] = lambda: make_user_with_permissions("users:read")
```

---

## Pytest Configuration

From `pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"          # All async tests run automatically
testpaths = ["tests"]
addopts = "--cov=src --cov-report=term-missing"
```

All tests marked `async def` are automatically run with `pytest-asyncio`. No `@pytest.mark.asyncio` needed per-test (it's set globally with `asyncio_mode = "auto"`).

---

## CI

GitHub Actions runs on every push and PR to `main`:

```yaml
# .github/workflows/ci.yml
- run: ruff check src/ tests/
- run: ruff format --check src/ tests/
- run: pytest
```

Tests must pass and linting must be clean before merging.

---

## Related

- [Contributing Guide](contributing.md)
- [Architecture — Testing Strategy](../architecture.md)
