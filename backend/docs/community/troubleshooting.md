# Troubleshooting

Common issues and solutions for KeepAI.

---

## Docker Issues

### Container won't start

```bash
docker compose logs backend
```

| Error message | Solution |
|---------------|---------|
| `port is already allocated` | Stop whatever is using port 8000, 5432, or 11434 |
| `Cannot connect to the Docker daemon` | Start Docker Desktop or run `dockerd` |
| `permission denied` | Add your user to the `docker` group or use `sudo` |

### Database connection error

```bash
# Check if the DB container is running
docker compose ps

# Check DB logs
docker compose logs db

# Restart the backend (it may have started before the DB was ready)
docker compose restart backend
```

### Ollama not responding

```bash
# Is the container running?
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Pull the model (the container needs a few seconds after first start)
docker compose exec ollama ollama pull llama3

# Test Ollama directly
curl http://localhost:11434/api/tags
```

---

## Application Issues

### 401 Not Authenticated

```bash
# Check that you have a token
echo $TOKEN

# Re-login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=your@email.com" \
  -F "password=yourpass" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Tokens expire after 30 minutes. Re-login when the token expires.

### 403 Insufficient Permissions

You are authenticated but lack the required permission for this endpoint. Options:

1. Register as `admin` (has all permissions):
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "pass", "role": "admin"}'
   ```
2. Update the user's role directly in the database
3. Assign the missing permission to the `user` role via a migration (see [RBAC Guide](../guides/rbac.md))

### 500 Internal Server Error on Prompt Endpoints

```bash
docker compose logs backend | tail -50
```

Common causes:
- Ollama not running or model not pulled
- LLM timeout — model is slow on CPU; increase `LLM_TIMEOUT_SECONDS` in `.env`
- Database not connected

### LLM Returns Empty or Nonsense

```bash
# See what models are available
docker compose exec ollama ollama list

# Try a more capable model
docker compose exec ollama ollama pull llama3.1
# Then use "model_name": "llama3.1" in your request
```

For structured extraction: ensure the source text is clear and complete. Smaller models produce lower-quality JSON extraction.

### Migration Errors on Startup

```bash
# Check current state
docker compose exec backend alembic current

# View history
docker compose exec backend alembic history

# Force upgrade
docker compose exec backend alembic upgrade head
```

If stuck on a specific revision, you can manually update the `alembic_version` table in PostgreSQL.

---

## Environment Issues

### Missing .env File

```bash
cp .env.example .env
# Edit .env with your values
```

### Wrong Database Credentials

Ensure `.env` matches what your PostgreSQL instance expects:

```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=db       # Use "localhost" for local dev outside Docker
POSTGRES_PORT=5432
POSTGRES_DB=app
```

### Port Conflicts

```bash
# Find what's using port 8000
lsof -i :8000
# or
ss -tulnp | grep 8000

# Kill the process or change the port mapping in docker-compose.yml
```

### Ollama URL Wrong for Local Dev

When running the backend natively (not in Docker) but Ollama is in Docker:

```ini
# .env
OLLAMA_BASE_URL=http://localhost:11434
```

When both are in Docker, use the service name:
```ini
OLLAMA_BASE_URL=http://ollama:11434
```

---

## Performance Issues

### LLM Responses Are Very Slow

| Cause | Solution |
|-------|---------|
| CPU-only inference | Add a GPU, enable NVIDIA Container Toolkit passthrough |
| Large model on weak CPU | Use smaller model: `phi3`, `tinyllama`, `mistral` (7B) |
| Insufficient RAM | Close other apps; swap may be engaged |
| Container memory limits | Increase Docker Desktop memory limit in settings |

### High Memory Usage

```bash
# Check container memory usage
docker stats

# Limit ollama memory in docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G
```

---

## Network Issues

### Can't Access the API

```bash
# Is the container running and healthy?
docker compose ps

# Is the API responding?
curl http://localhost:8000/health/live

# Check port binding
docker compose port backend 8000
```

---

## Testing Issues

### Tests Fail to Run

```bash
pip install pytest pytest-asyncio pytest-cov httpx
pytest -v
```

### Test DB Connection Errors

Tests use `AsyncMock` — they never connect to a real database. If you're getting DB errors in tests, check that `conftest.py` sets `POSTGRES_*` env vars before importing `src.main`.

---

## Still Stuck?

1. Search [GitHub Issues](https://github.com/yoosuf/KeepAI/issues) — your issue may be already known
2. Open a new issue — include:
   - Steps to reproduce
   - Full error logs (`docker compose logs backend`)
   - Your environment: OS, Docker version, Python version

---

## Related

- [FAQ](faq.md)
- [Deployment Guide](../guides/deployment.md)
- [Security Policy](security.md)
