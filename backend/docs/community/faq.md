# Frequently Asked Questions

---

## General

### What is KeepAI?

A production-ready FastAPI backend that runs large language models (Llama 3, Mistral, CodeLlama, etc.) **locally on your infrastructure**. It provides a REST API with JWT authentication, database-driven role-based access control, structured JSON extraction, and streaming — all without sending data to third-party cloud services.

### Why would I use this instead of OpenAI?

| Concern | KeepAI | OpenAI API |
|---------|--------|-----------|
| Privacy | Data never leaves your infra | Data sent to OpenAI |
| Cost | Free (hardware only) | Per-token billing |
| Model choice | Any Ollama model | GPT family only |
| Compliance | HIPAA/GDPR-friendly | Requires DPA negotiation |
| Offline use | Yes | No |

### Do I need a GPU?

No. Ollama runs on CPU. Smaller models (Phi, TinyLlama, Mistral 7B) run well on a modern CPU. Larger models (Llama 3 70B) need either a GPU or significant RAM and patience.

---

## Technical

### What models can I use?

Any model supported by Ollama:
- Llama 3 / 3.1 (8B, 70B)
- Mistral (7B)
- CodeLlama (7B, 34B)
- DeepSeek Coder
- Phi-3 (2.7B, 14B)
- Gemma (2B, 7B)
- Qwen, Command R, and 100+ more from [ollama.com/library](https://ollama.com/library)

### Can I switch models per request?

Yes. Include `"model_name": "mistral"` in the prompt request body. Any model that's been pulled in Ollama can be used.

### What databases are supported?

PostgreSQL 15 via `asyncpg`. The project uses SQLAlchemy 2.0 async, so adding support for other async-compatible databases (MySQL, SQLite for dev) requires creating a new engine in `src/core/database.py`.

### Is there a frontend?

Not yet. KeepAI is currently a pure REST API with auto-generated Swagger (`/docs`) and ReDoc (`/redoc`) docs. A web UI is on the [roadmap](roadmap.md).

### How does streaming work?

`POST /api/v1/prompts/stream` returns `text/event-stream` (Server-Sent Events). Tokens arrive as `data: <token>\n\n` frames and the stream ends with `data: [DONE]\n\n`. Streaming responses are not persisted to the database.

### Can I add a different LLM provider (OpenAI, Anthropic)?

Yes. Implement `LLMInterface` and inject it in `src/modules/prompts/router.py::get_prompt_service`. See [Extending LLM Providers](../guides/extending-llm.md) for full examples.

### How does authentication work?

JWT-based. Users register with email/password (Argon2id-hashed), log in to receive a 30-minute token, and include the token in the `Authorization: Bearer` header on subsequent requests.

### How does the RBAC system work?

Roles and permissions are stored in PostgreSQL. `PermissionChecker("perm:name")` is a FastAPI dependency that loads `user → role → permissions` on each request (5-minute cache) and returns 403 if the required permission is absent. See [RBAC Guide](../guides/rbac.md).

---

## Usage

### How do I extract structured data?

Use `POST /api/v1/extract-invoice` with raw invoice text. The `InvoiceAgent` constructs a JSON-extraction prompt, calls the LLM in JSON mode, and parses the result. The same pattern can be extended for contracts, resumes, forms, or any structured extraction.

### How do I see all my past prompts?

`GET /api/v1/prompts` returns paginated results for the authenticated user. Use `?skip=0&limit=20` for pagination.

### How do I create an admin user?

Include `"role": "admin"` in the registration request body:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'
```

**In production, restrict or remove public admin registration.**

### How do I reset the database?

```bash
# Docker — destroys all data and restarts fresh
docker compose down -v
docker compose up -d
docker compose exec backend alembic upgrade head
```

### What is the default rate limit?

20 LLM requests per minute per user (by JWT email). Configure via `RATE_LIMIT_LLM` in `.env`. Examples: `"100/hour"`, `"500/day"`.

---

## Deployment

### Can I deploy this to production?

Yes. See the [Deployment Guide](../guides/deployment.md) for Docker, manual, HTTPS reverse proxy, and production hardening steps.

### What are the minimum server requirements?

- 4 GB RAM (8 GB+ recommended)
- 20 GB disk space
- CPU with AVX2 support
- Docker

### Can I use a cloud GPU?

Yes. Run Ollama on a cloud GPU instance (AWS, GCP, Azure, RunPod, etc.) and set `OLLAMA_BASE_URL` in `.env` to the remote instance URL.

### Does it support GPU acceleration?

Yes, with NVIDIA GPUs. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) and enable GPU passthrough in the Docker Compose `ollama` service.

---

## Contributing

### How can I contribute?

See [Contributing](../development/contributing.md). We welcome bug reports, feature requests, documentation improvements, and pull requests.

### How do I report a security vulnerability?

Email directly — do not open a public issue. See [Security Policy](security.md).

### Are there coding standards?

Yes. Ruff for linting and formatting, configured in `pyproject.toml`. See [Contributing](../development/contributing.md).

---

## Troubleshooting

For common issues, see [Troubleshooting](troubleshooting.md).

- API returns 500 → check `docker compose logs backend`
- "Model not found" → run `docker compose exec ollama ollama list`, pull the model
- Slow responses → consider a smaller model or GPU

---

*Still have questions? Open a [GitHub Issue](https://github.com/yoosuf/KeepAI/issues).*
