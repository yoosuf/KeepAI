# Frequently Asked Questions

## General

### What is this project?
A production-ready backend that runs large language models (like Llama 3) locally on your infrastructure. It provides a REST API with authentication, role-based access control, and structured data extraction — all without sending data to third-party services.

### Why would I use this instead of OpenAI?
- **Privacy** — Data never leaves your infrastructure
- **Cost** — No per-token fees (you pay for hardware only)
- **Control** — Choose any model, customize prompts, fine-tune
- **Compliance** — HIPAA, GDPR, and other regulations are easier to satisfy when data stays on-premise

### Do I need a GPU?
No, but GPU acceleration significantly improves performance. Ollama runs on CPU, though response times will be slower (especially with larger models like Llama 3 70B).

---

## Technical

### What models can I use?
Any model supported by Ollama, including:
- Llama 3 / 3.1 (8B, 70B)
- Mistral (7B)
- CodeLlama (7B, 34B)
- DeepSeek Coder
- Phi (2.7B, 14B)
- Gemma (2B, 7B)
- And 100+ more from the [Ollama library](https://ollama.ai/library)

### Can I switch models per request?
Yes. Each prompt request accepts an optional `model_name` parameter. Set it to any model loaded in Ollama.

### What databases are supported?
PostgreSQL 15 (via asyncpg). The project uses SQLAlchemy 2.0 async, so adding support for other databases is straightforward.

### Is there a frontend?
Not yet. The project is currently a pure REST API with Swagger/ReDoc documentation. A web UI is on the [roadmap](ROADMAP.md).

### Can I use this with a frontend framework?
Yes. Any framework that can make HTTP requests (React, Vue, Svelte, Next.js, etc.) can consume this API.

### How does authentication work?
JWT-based. Users register with email/password, login to receive a token, and include the token in subsequent requests. Tokens expire after 30 minutes (configurable).

### How does the RBAC system work?
Roles and permissions are stored in PostgreSQL. Admins can create/assign roles with granular permissions (e.g., `users:read`, `prompts:read_all`). Permission checking happens on every protected endpoint via FastAPI dependency injection.

---

## Usage

### How do I extract structured data?
Use the `/api/v1/extract-invoice` endpoint with raw text. The LLM returns JSON matching a predefined schema. This pattern can be extended for contracts, forms, resumes, or any structured extraction.

### Can I get streaming responses?
Not yet. Streaming (SSE/WebSocket) is on the [roadmap](ROADMAP.md).

### How do I see all my past prompts?
`GET /api/v1/prompts` returns paginated results for the authenticated user.

### How do I create an admin user?
Include `"role": "admin"` in the registration request body. By default, any user can register as admin — **disable this in production** by removing or gating the public admin registration endpoint.

### How do I reset the database?
```bash
# Delete volumes and restart
docker compose down -v
docker compose up -d
```

---

## Deployment

### Can I deploy this to production?
Yes. See the [Deployment Guide](DEPLOYMENT_GUIDE.md) for production configurations, including HTTPS, reverse proxy, and security hardening.

### What are the minimum server requirements?
- 4GB RAM (8GB+ recommended)
- 20GB disk space
- CPU with AVX2 support
- Docker

### Can I use this on a Raspberry Pi?
With smaller models. Try `phi` (2.7B) or `tinyllama` (1.1B). Larger models will not fit in the Pi's memory.

### Does it support GPU acceleration?
Yes, with NVIDIA GPUs. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) and enable GPU passthrough in Docker.

### Can I use a cloud GPU instead of local?
Yes. Run Ollama on a cloud GPU instance (AWS, GCP, Azure, RunPod, etc.) and point `OLLAMA_BASE_URL` to the remote instance.

---

## Contributing

### How can I contribute?
See [CONTRIBUTING.md](CONTRIBUTING.md). We welcome bug reports, feature requests, documentation improvements, and pull requests.

### How do I report a security vulnerability?
See [SECURITY.md](SECURITY.md). Email the maintainer directly — do not open a public issue.

### Are there coding standards?
Yes. We use Ruff for linting and formatting. Configuration is in `pyproject.toml`. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Troubleshooting

### The API returns 500 errors
Check the application logs: `docker compose logs backend`. Common causes: Ollama not running, model not pulled, database connection issues.

### "Model not found" errors
Ensure the model is pulled: `docker compose exec ollama ollama list`. If empty, pull a model: `docker compose exec ollama ollama pull llama3`.

### Passwords aren't working
Passwords are bcrypt-hashed. There's no password recovery built in — use the `/api/v1/auth/register` endpoint to create a new account.

---

*Still have questions? Open a [GitHub Issue](https://github.com/yoosuf/fastapi-ollama-backend/issues).*
