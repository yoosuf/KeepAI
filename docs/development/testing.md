# Testing Guide

---

## Backend Testing

The backend uses `pytest` with `pytest-asyncio` for async test support. Tests mock external dependencies (Ollama, PostgreSQL) so they run fast without any infrastructure.

### Running Tests

```bash
cd backend

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage report
python -m pytest --cov=src

# Run with HTML coverage report
python -m pytest --cov=src --cov-report=html

# Run a specific test file
python -m pytest tests/api/test_auth.py

# Run tests matching a pattern
python -m pytest -k "invoice"

# Run with print output visible
python -m pytest -s
```

### Test Structure

```
backend/tests/
+-- conftest.py                  # Shared fixtures
+-- test_main.py                 # Health check tests
+-- api/
|   +-- test_auth.py            # Auth endpoint tests
+-- services/
    +-- test_prompt_service.py  # Prompt service tests
```

### Patterns

#### Service Tests (`tests/services/test_prompt_service.py`)

Services are tested with mocked dependencies:

```python
@pytest.mark.asyncio
async def test_create_prompt():
    # Mock LLM client
    llm = MagicMock(spec=LLMInterface)
    llm.generate.return_value = {"response": "mock response", "total_duration": 1000}

    # Mock DB session
    db = AsyncMock(spec=AsyncSession)

    # Run service
    service = PromptService(db, llm)
    result = await service.create_prompt(
        user_id=1, prompt_text="Test", model_name="llama3"
    )

    # Assert
    assert result.response_text == "mock response"
    llm.generate.assert_called_once()
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
```

#### API Tests (`tests/api/test_auth.py`)

API endpoints are tested via the FastAPI test client:

```python
@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "testpass"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"

@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "adminpass"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Fixtures (`tests/conftest.py`)

Shared fixtures provide:

- `client` — `httpx.AsyncClient` connected to the FastAPI app
- Mock database session with `AsyncMock`
- Pre-registered test user
- Auth token for authenticated requests

### Mock Environment Variables

Tests set mock env vars to avoid connecting to real services:

```python
os.environ["POSTGRES_SERVER"] = "test"
os.environ["POSTGRES_USER"] = "test"
os.environ["POSTGRES_PASSWORD"] = "test"
os.environ["POSTGRES_DB"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["OLLAMA_BASE_URL"] = "http://test:11434"
```

---

## Frontend Testing

The frontend currently uses `npm run build` as a smoke test. This compiles TypeScript and bundles the application, catching type errors and import issues.

```bash
cd frontend

# TypeScript type checking
npx tsc --noEmit

# Production build
npm run build
```

### Adding Frontend Tests

To add proper frontend tests, consider:

1. **Vitest** (compatible with Vite) for unit tests
2. **React Testing Library** for component tests
3. **Playwright** or **Cypress** for E2E tests

---

## CI Pipeline

GitHub Actions (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

```yaml
jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r backend/requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov httpx
      - run: ruff check backend/src backend/tests
      - run: ruff format --check backend/src backend/tests
      - run: cd backend && python -m pytest --cov=src
```

**Note**: Frontend CI is not yet configured. See [Next Steps](../next-steps.md) for planned additions.

---

## Test Coverage Goals

| Module | Current | Target |
|--------|---------|--------|
| Auth (API + service) | Tests exist | 90%+ |
| Prompts (service) | Tests exist | 90%+ |
| Conversations | No tests | 80%+ |
| API Keys | No tests | 80%+ |
| Analytics | No tests | 80%+ |
| Documents/RAG | No tests | 80%+ |
| WebSocket | No tests | 70%+ |
| Frontend | Build check | Smoke test |

---

## Related

- [Contributing Guide](contributing.md)
- [Architecture](../architecture.md)
