# Troubleshooting Guide

Common issues and their solutions when running KeepAPI.

---

## Docker Issues

### Container won't start

**Symptom:** `docker compose up` fails immediately.

**Check logs:**
```bash
docker compose logs backend
```

**Common causes:**

| Error | Solution |
|-------|----------|
| `port is already allocated` | Stop other services using ports 8000, 5432, or 11434 |
| `Cannot connect to the Docker daemon` | Ensure Docker is running: `docker info` |
| `permission denied` | Ensure you have Docker permissions or use `sudo` |

### Database connection error

**Symptom:** Backend logs show `could not connect to server`.

```bash
# Check if database is running
docker compose ps

# Check database logs
docker compose logs db

# Wait for DB to be ready (first start takes a moment)
docker compose restart backend
```

### Ollama not responding

**Symptom:** Prompts return 500 errors.

```bash
# Check if Ollama is running
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Pull the model (container may need a moment to start)
docker compose exec ollama ollama pull llama3

# Verify Ollama API
curl http://localhost:11434/api/tags
```

---

## Application Issues

### "Not authenticated" error

**Symptom:** API returns `401 Not authenticated`.

```bash
# Check your token
echo $TOKEN

# Login again
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin@example.com" \
  -F "password=adminpass" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Verify token works
curl http://localhost:8000/api/v1/prompts -H "Authorization: Bearer $TOKEN"
```

### "Insufficient permissions" error

**Symptom:** API returns `403 Forbidden`.

```bash
# Register as admin instead of user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'
```

### LLM returns empty or nonsense responses

**Symptom:** Response text is empty, gibberish, or irrelevant.

```bash
# Check which model is loaded
docker compose exec ollama ollama list

# Try a different, more capable model
docker compose exec ollama ollama pull llama3.1
# Then use "model_name": "llama3.1" in your request

# For structured extraction, ensure your input text is clear and complete
```

### Migration errors

**Symptom:** Backend fails to start with migration errors.

```bash
# Check current migration state
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history

# Manually upgrade
docker compose exec backend alembic upgrade head

# If a migration is stuck:
# 1. Check the alembic_version table in the database
# 2. Manually set the version: UPDATE alembic_version SET version_num = '<correct_revision>'
```

---

## Environment Issues

### Missing .env file

**Symptom:** Backend fails to start with configuration errors.

```bash
cp .env.example .env
# Edit .env with your settings
```

### Wrong database credentials

**Symptom:** `FATAL: password authentication failed for user "postgres"`.

Ensure your `.env` file matches the credentials in `docker-compose.yml`:

```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=app
```

### Port conflicts

**Symptom:** `Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use`.

```bash
# Find what's using the port
lsof -i :8000

# Kill the process or change the port in docker-compose.yml
```

---

## Performance Issues

### LLM responses are very slow

**Possible causes:**

| Cause | Solution |
|-------|----------|
| CPU-only inference | Use a GPU-capable machine, enable GPU passthrough to Docker |
| Small model on slow CPU | Try a smaller model: `ollama pull phi` or `ollama pull tinyllama` |
| Insufficient RAM | Close other applications, or use a smaller model |
| Container resource limits | Increase Docker resource limits in Docker Desktop settings |

### High memory usage

```bash
# Check container resource usage
docker stats

# Limit container memory in docker-compose.yml
services:
  ollama:
    deploy:
      resources:
        limits:
          memory: 8G
```

---

## Network Issues

### Cannot access the API

```bash
# Is the container running?
docker compose ps

# Is it listening on the right port?
curl http://localhost:8000/health

# Check if the port is bound correctly
docker compose port backend 8000
```

### Cannot connect to Ollama from backend

If running without Docker (backend natively, Ollama in Docker):

```bash
# Update OLLAMA_BASE_URL in .env
OLLAMA_BASE_URL=http://host.docker.internal:11434
# On Linux: OLLAMA_BASE_URL=http://localhost:11434
```

---

## Testing Issues

### Tests fail to run

```bash
# Ensure test dependencies are installed
pip install pytest pytest-asyncio pytest-cov httpx

# Run with verbose output
pytest -v

# Run a specific test
pytest tests/api/test_auth.py -v
```

### Test database issues

Tests use mocks/dummy environment variables. If tests fail with DB errors:

```bash
# Check conftest.py has valid mock env vars
# Ensure you're not accidentally connecting to a real database
```

---

## Still Stuck?

1. **Search existing issues** — [GitHub Issues](https://github.com/yoosuf/fastapi-ollama-backend/issues)
2. **Open a new issue** — Include:
   - Steps to reproduce
   - Full error logs
   - Your environment details (OS, Docker version, Python version)
   - What you've tried so far

---

## Related

- [FAQ](FAQ.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Security Policy](SECURITY.md)
