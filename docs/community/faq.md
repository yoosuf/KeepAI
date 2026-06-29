# Frequently Asked Questions

---

## General

### What is KeepAI?

KeepAI is a self-hosted LLM inference platform with a FastAPI backend, React frontend, WebSocket chat, document RAG, API key management, and usage analytics. It runs entirely on your infrastructure using Ollama for local LLM inference.

### How is it different from ChatGPT?

KeepAI runs locally on your hardware. No data leaves your server. You control which models are used, how data is stored, and who has access. It's designed for privacy-conscious users and organizations.

### What models are supported?

Any model available in Ollama's library: Llama 3, Mistral, CodeLlama, Phi, Mixtral, and 100+ more. You can also add custom models via Ollama.

---

## Setup

### How do I install KeepAI?

See the [Getting Started Guide](../getting-started.md). The fastest path is Docker:

```bash
git clone https://github.com/yoosuf/KeepAI.git
cd KeepAI
docker compose -f docker/docker-compose.yml up --build -d
```

### Docker vs local development — which should I use?

- **Docker** (recommended): one command starts everything — backend, database, Ollama, and frontend
- **Local**: more control, easier debugging, but requires PostgreSQL and Ollama installed separately

### How do I change the default model?

Set `OLLAMA_MODEL` in `backend/.env`:

```ini
OLLAMA_MODEL=mistral
```

Or pass `"model_name": "mistral"` in individual API requests.

### How do I change the port?

Edit the ports section in `docker/docker-compose.yml`:

```yaml
backend:
  ports:
    - "8080:8000"  # host:container
```

---

## Usage

### How do I register as an admin?

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'
```

### How do I get an API token?

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin@example.com" \
  -F "password=adminpass" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

### How do I use WebSocket chat?

Connect to `ws://<host>/ws/chat?token=<jwt>` and send JSON messages:

```json
{ "type": "chat", "message": "Hello!", "model_name": "llama3" }
```

### How do I stream responses?

Use the SSE endpoints:

```bash
curl -N -X POST http://localhost:8000/api/v1/prompts/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Write a poem."}'
```

### How do I use the frontend?

In Docker, open `http://localhost:3000`. In local development, open `http://localhost:5173`.

---

## Troubleshooting

### The API returns 500 errors

Check the application logs:

```bash
docker compose -f docker/docker-compose.yml logs backend
```

Common causes: Ollama not running, model not pulled, database connection issues.

### "Model not found" errors

Ensure the model is pulled:

```bash
docker compose -f docker/docker-compose.yml exec ollama ollama list
```

If empty, pull a model:

```bash
docker compose -f docker/docker-compose.yml exec ollama ollama pull llama3
```

### Responses are very slow

- Ensure your server has enough RAM (8 GB+ recommended)
- Try a smaller model: `ollama pull phi` or `ollama pull tinyllama`
- Enable GPU passthrough if you have an NVIDIA GPU
- Check Docker resource limits in Docker Desktop

### Rate limit exceeded

The default rate limit is 20 requests per minute. Increase it:

```ini
RATE_LIMIT_LLM=100/minute
```

Or wait a minute for the rate limit window to reset.

### Token expired

JWT tokens expire after 30 minutes by default. Log in again to get a new token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -F "username=..." -F "password=..." | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

---

## Development

### How do I add a new endpoint?

1. Create or update the module's `router.py`
2. Add service logic in `service.py`
3. Define schemas in `schemas.py`
4. Add ORM models in `models.py`
5. Register the router in `src/main.py`

### How do I add a new LLM provider?

1. Create a new adapter in `src/infrastructure/llm/`
2. Implement the `LLMInterface` abstract methods
3. Register the adapter in `src/main.py`
4. See [Extending LLM Support](../guides/extending-llm.md) for details.

### How do I run tests?

```bash
cd backend
python -m pytest
python -m pytest --cov=src

cd frontend
npm run build  # smoke test
```

### How do I create a database migration?

```bash
docker compose -f docker/docker-compose.yml exec backend alembic revision --autogenerate -m "description"
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
```

---

## Related

- [Getting Started Guide](../getting-started.md)
- [API Reference](../api/reference.md)
- [Troubleshooting Guide](troubleshooting.md)
