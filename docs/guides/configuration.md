# Configuration Reference

KeepAI is configured through environment variables (loaded via pydantic-settings from a `.env` file or environment).

---

## Database

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `POSTGRES_USER` | string | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | string | `postgres` | PostgreSQL password |
| `POSTGRES_SERVER` | string | `db` | PostgreSQL host (use `localhost` for local dev) |
| `POSTGRES_PORT` | int | `5432` | PostgreSQL port |
| `POSTGRES_DB` | string | `app` | PostgreSQL database name |
| `DB_POOL_SIZE` | int | `10` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | int | `20` | Max overflow connections |
| `DB_POOL_TIMEOUT` | int | `30` | Pool timeout in seconds |
| `DB_POOL_RECYCLE` | int | `3600` | Recycle connections after N seconds |

---

## Auth

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SECRET_KEY` | string | `changethis` | JWT signing key. Generate with `openssl rand -hex 32` |
| `ALGORITHM` | string | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `30` | JWT token expiry in minutes |

---

## LLM

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `OLLAMA_BASE_URL` | string | `http://ollama:11434` | Ollama API endpoint |
| `OLLAMA_MODEL` | string | `llama3` | Default model for generation |
| `LLM_TIMEOUT_SECONDS` | float | `60.0` | Timeout for LLM calls |
| `MODEL_ROUTING` | dict | `{}` | Map task_type labels to models, e.g., `{"code": "codellama", "analysis": "llama3"}` |

---

## CORS

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CORS_ORIGINS` | list | `["*"]` | Allowed CORS origins. Restrict in production: `["https://myapp.com"]` |

---

## Rate Limiting

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RATE_LIMIT_LLM` | string | `20/minute` | LLM endpoint rate limit (slowapi format) |

---

## Development Mode

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEV_MODE` | bool | `false` | Enable hot reload via uvicorn --reload |

---

## Reference: backend/.env.example

```ini
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=app

# Database pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Auth
SECRET_KEY=changethis
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
LLM_TIMEOUT_SECONDS=60.0

# CORS
CORS_ORIGINS=["*"]

# Rate limiting
RATE_LIMIT_LLM=20/minute
```

---

## Frontend Configuration

The frontend (Vite) uses environment variables with the `VITE_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | (proxied by Vite) | Backend API URL for production builds |

In development, Vite proxies `/api` to `http://localhost:8000` via `vite.config.ts`.

---

## Docker Configuration

### Via docker-compose.yml

Environment variables are set inline in `docker/docker-compose.yml`. To override, create a `docker-compose.override.yml`:

```yaml
services:
  backend:
    environment:
      - SECRET_KEY=<your-production-key>
      - CORS_ORIGINS=["https://myapp.com"]
```

### Via .env file

Set `env_file: backend/.env` in your compose file to load from a file:

```yaml
services:
  backend:
    env_file: backend/.env
```

---

## Production Configuration Checklist

- [ ] Generate a strong `SECRET_KEY`: `openssl rand -hex 32`
- [ ] Change `POSTGRES_PASSWORD` to a strong unique password
- [ ] Change `POSTGRES_USER` from `postgres` to a custom user
- [ ] Set `CORS_ORIGINS` to your frontend domain(s)
- [ ] Set `RATE_LIMIT_LLM` to an appropriate value for your usage
- [ ] Disable `DEV_MODE` (set to `false` or remove)
- [ ] Increase `LLM_TIMEOUT_SECONDS` if using slower models
- [ ] Tune `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` for expected concurrency
