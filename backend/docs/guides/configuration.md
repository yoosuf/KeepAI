# Configuration Reference

All settings are loaded from a `.env` file via Pydantic `BaseSettings` in `src/core/config.py`. Copy `.env.example` to `.env` and adjust values before starting the server.

```bash
cp .env.example .env
```

`DATABASE_URL` is a computed property — never set it directly.

---

## Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_USER` | yes | — | PostgreSQL username |
| `POSTGRES_PASSWORD` | yes | — | PostgreSQL password |
| `POSTGRES_SERVER` | yes | — | Host: `db` in Docker, `localhost` for local dev |
| `POSTGRES_PORT` | no | `5432` | PostgreSQL port |
| `POSTGRES_DB` | yes | — | Database name |

### Connection Pool

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_POOL_SIZE` | `10` | Persistent connections in the pool |
| `DB_MAX_OVERFLOW` | `20` | Additional burst connections above pool size |
| `DB_POOL_TIMEOUT` | `30` | Seconds to wait for a free connection before error |
| `DB_POOL_RECYCLE` | `3600` | Seconds before recycling idle connections |

**Tuning guidance**: `DB_POOL_SIZE + DB_MAX_OVERFLOW` is the maximum concurrent DB connections. Defaults (~30 total) handle light-to-moderate loads. For high concurrency, increase `DB_POOL_SIZE` and ensure your PostgreSQL `max_connections` is high enough.

---

## Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `changethis` | HS256 signing key for JWT tokens. **Must be overridden in production.** |
| `ALGORITHM` | `HS256` | JWT signing algorithm. Do not change unless you implement a new auth flow. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT expiry in minutes |

**Generate a secure secret key:**
```bash
openssl rand -hex 32
```

---

## LLM (Ollama)

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API base URL. Use `http://localhost:11434` for local dev. |
| `OLLAMA_MODEL` | `llama3` | Default model when no `model_name` is specified in a request |
| `LLM_TIMEOUT_SECONDS` | `60.0` | Seconds before an LLM `generate()` call times out. Increase for slow hardware or large models. |

---

## CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `CORS_ORIGINS` | `["*"]` | JSON array of allowed origins. Use `["*"]` for dev, restrict in production. |

**Production example:**
```ini
CORS_ORIGINS=["https://app.yourdomain.com", "https://admin.yourdomain.com"]
```

---

## Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `RATE_LIMIT_LLM` | `20/minute` | slowapi format: `N/period`. Applied to all LLM endpoints. |

**Format examples:**
```
20/minute
100/hour
500/day
```

Rate limiting keys on the user's email (from JWT) for authenticated requests, and on IP for anonymous requests.

For multi-instance deployments, configure Redis storage in `src/core/rate_limit.py`:
```python
Limiter(key_func=get_key, storage_uri="redis://redis:6379")
```

---

## Example `.env` Files

### Local Development

```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=app

DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

SECRET_KEY=dev-secret-not-for-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
LLM_TIMEOUT_SECONDS=120.0

CORS_ORIGINS=["*"]
RATE_LIMIT_LLM=100/minute
```

### Docker (defaults from `.env.example`)

```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=app

DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

SECRET_KEY=changethis
ACCESS_TOKEN_EXPIRE_MINUTES=30

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
LLM_TIMEOUT_SECONDS=60.0

CORS_ORIGINS=["*"]
RATE_LIMIT_LLM=20/minute
```

### Production

```ini
POSTGRES_USER=app_user
POSTGRES_PASSWORD=<strong-generated-password>
POSTGRES_SERVER=your-db-host
POSTGRES_PORT=5432
POSTGRES_DB=app_production

DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800

SECRET_KEY=<output-of-openssl-rand-hex-32>
ACCESS_TOKEN_EXPIRE_MINUTES=30

OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
LLM_TIMEOUT_SECONDS=60.0

CORS_ORIGINS=["https://app.yourdomain.com"]
RATE_LIMIT_LLM=20/minute
```

---

## How Settings Are Loaded

`src/core/config.py` defines:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)
    ...
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:..."
```

- Variables are `case_sensitive=True` — match the variable name exactly
- `.env` file is loaded automatically; environment variables take precedence over `.env` values
- The `settings` singleton is imported across the codebase as `from src.core.config import settings`

---

## Related

- [Getting Started](getting-started.md)
- [Deployment Guide](deployment.md)
- [Architecture](../architecture.md)
