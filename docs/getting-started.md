# Getting Started

This guide gets KeepAI running on your machine in minutes, then walks you through the first API calls.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | For local development without Docker |
| Docker & Docker Compose | v2+ | Recommended — starts everything |
| PostgreSQL | 15+ | Only needed without Docker |
| Ollama | Latest | Only needed without Docker |

---

## Option A: Docker (Recommended)

One command starts the backend, database, Ollama, and frontend:

```bash
git clone https://github.com/yoosuf/KeepAI.git
cd KeepAI

# Start all services
docker compose -f docker/docker-compose.yml up --build -d

# Pull a model (only needed once per model)
docker compose -f docker/docker-compose.yml exec ollama ollama pull llama3
```

Your API is now running at `http://localhost:8000` and frontend at `http://localhost:3000`.

**Check it's up:**
```bash
curl http://localhost:8000/health/live
# {"status": "ok"}
```

---

## Option B: Local Development

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your PostgreSQL credentials:
```ini
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_DB=app
```

For Ollama running locally, update:
```ini
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the server

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Start the frontend (separate terminal)

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:5173` and proxies API calls to `http://localhost:8000`.

---

## First API Calls

### Step 1: Register a user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'
```

### Step 2: Log in and get a token

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=you@example.com" \
  -F "password=yourpassword" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo $TOKEN
```

### Step 3: Send a prompt

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Explain quantum computing in 3 sentences."}'
```

### Step 4: Stream a response

```bash
curl -N -X POST http://localhost:8000/api/v1/prompts/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Write a haiku about Python."}'
```

Tokens appear one-by-one as Server-Sent Events.

---

## Register an Admin User

Admin users have access to user management and all-prompts endpoints:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'
```

In production, restrict public admin registration. See [Deployment Guide](guides/deployment.md#production-hardening).

---

## Using the Frontend

### Local Development
Open `http://localhost:5173` and log in with your credentials.

### Docker
Open `http://localhost:3000` and log in.

### Available Pages

| Route | Page | Description |
|-------|------|-------------|
| `/chat` | Chat | WebSocket-based conversation interface |
| `/chat/:id` | Chat | Continue an existing conversation |
| `/history` | History | Browse and search prompt history |
| `/conversations` | Conversations | Browse, export, delete conversation threads |
| `/api-keys` | API Keys | Create and manage API keys |
| `/documents` | Documents | Upload, search, and query documents (RAG) |
| `/analytics` | Analytics | Usage statistics dashboard |
| `/admin/users` | Admin Users | Manage users (admin only) |
| `/admin/prompts` | Admin Prompts | View all prompts (admin only) |
| `/playground` | Playground | Test prompts and invoice extraction |
| `/models` | Models | Browse and manage Ollama models |

---

## Interactive API Docs

With the server running, open:
- **Swagger UI**: `http://localhost:8000/docs` — click "Try it out" on any endpoint
- **ReDoc**: `http://localhost:8000/redoc` — cleaner read-only view

---

## Pull Different Models

Ollama supports 100+ models:

```bash
# Docker
docker compose -f docker/docker-compose.yml exec ollama ollama pull llama3.1
docker compose -f docker/docker-compose.yml exec ollama ollama pull mistral
docker compose -f docker/docker-compose.yml exec ollama ollama pull codellama

# Local Ollama
ollama pull llama3.1
```

Then use the model name in your request:
```json
{ "prompt_text": "...", "model_name": "mistral" }
```

---

## Verify Everything Works

```bash
# Liveness
curl http://localhost:8000/health/live

# Readiness (checks DB + Ollama)
curl http://localhost:8000/health/ready

# List available Ollama models
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/models
```

---

## Next Steps

- [Architecture Overview](architecture.md) — understand the codebase
- [API Reference](api/reference.md) — full endpoint documentation
- [Deployment Guide](guides/deployment.md) — production setup
- [Configuration Reference](guides/configuration.md) — all environment variables
- [Contributing Guide](development/contributing.md) — how to contribute
