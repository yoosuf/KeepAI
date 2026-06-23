<div align="center">
  <h1>KeepAI</h1>
  <p><strong>Your private AI backend. Run LLMs locally. Own your data.</strong></p>

  <p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg?style=flat&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.104-009688?style=flat&logo=fastapi&logoColor=white" alt="FastAPI"></a>
    <a href="https://ollama.ai/"><img src="https://img.shields.io/badge/Ollama-Local%20LLM-5B5B5B?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSIxMCIgZmlsbD0id2hpdGUiLz48L3N2Zz4=" alt="Ollama"></a>
    <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat&logo=postgresql&logoColor=white" alt="PostgreSQL"></a>
    <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white" alt="Docker"></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg?style=flat" alt="License"></a>
    <a href="https://github.com/yoosuf/fastapi-ollama-backend/actions"><img src="https://img.shields.io/github/actions/workflow/status/yoosuf/fastapi-ollama-backend/ci.yml?style=flat&logo=githubactions&logoColor=white" alt="CI"></a>
    <a href="https://github.com/yoosuf/fastapi-ollama-backend/stargazers"><img src="https://img.shields.io/github/stars/yoosuf/fastapi-ollama-backend?style=flat&logo=github&logoColor=white" alt="Stars"></a>
    <a href="https://github.com/yoosuf/fastapi-ollama-backend/issues"><img src="https://img.shields.io/github/issues/yoosuf/fastapi-ollama-backend?style=flat&logo=github&logoColor=white" alt="Issues"></a>
  </p>

  <h3>
    <a href="#-features">Features</a>
    <span> · </span>
    <a href="#-quick-start">Quick Start</a>
    <span> · </span>
    <a href="#-use-cases">Use Cases</a>
    <span> · </span>
    <a href="#-api-overview">API</a>
    <span> · </span>
    <a href="#-architecture">Architecture</a>
    <span> · </span>
    <a href="#-roadmap">Roadmap</a>
  </h3>

  <br>

  <p align="center">
    <img src="https://img.shields.io/badge/Status-Active-success?style=for-the-badge" alt="Status">
    <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=for-the-badge" alt="PRs Welcome">
    <img src="https://img.shields.io/badge/AI-Powered-ff69b4?style=for-the-badge" alt="AI Powered">
  </p>
</div>

---

## Why KeepAI?

Every AI SaaS sends your data to someone else's server. Not this one.

**KeepAI** is a privacy-first, production-ready backend that runs large language models (Llama 3, Mistral, CodeLlama, etc.) **on your own infrastructure** — no cloud dependency, no data leaks, no API usage fees.

> "The best AI is the one that respects your privacy."

### 🏆 What Makes It Different

| Feature | KeepAI | OpenAI API | Other Backends |
|---|---|---|---|
| **Data Privacy** | 🔒 100% local | ❌ Data leaves your infra | ❌ Usually cloud |
| **Cost** | 💰 Free (your hardware) | 💸 Per-token billing | 💸 SaaS fees |
| **Models** | 🔄 Any Ollama model | 🔒 GPT only | 🔒 Limited choices |
| **Auth & RBAC** | ✅ Built-in JWT + RBAC | ❌ Not included | ❌ Rarely included |
| **Structured Output** | ✅ JSON mode | ✅ Supported | ❌ Usually missing |
| **Database** | ✅ PostgreSQL | ❌ No persistence | ⚠️ Varies |
| **Clean Architecture** | ✅ Hexagonal | ❌ N/A | ⚠️ Rarely |

---

## ✨ Features

- **🤖 Local LLM Inference** — Run Llama 3, Mistral, CodeLlama, DeepSeek, and 100+ models locally via Ollama
- **🔐 JWT Authentication** — Register, login, token-based auth out of the box
- **🛡️ Role-Based Access Control** — Database-driven permissions (Admin/User roles, granular permissions)
- **📋 Structured JSON Extraction** — Extract invoices, contracts, forms as validated JSON
- **🗄️ PostgreSQL Persistence** — Async SQLAlchemy + Alembic migrations
- **🐳 Docker Ready** — One command to start everything
- **🏗️ Clean Architecture** — Hexagonal/ports-and-adapters pattern, fully testable
- **📊 Observability** — Structured JSON logging, request tracking
- **✅ Tested** — pytest + async tests + CI pipeline

---

## 🚀 Quick Start

### One-liner (Docker)

```bash
git clone https://github.com/yoosuf/fastapi-ollama-backend.git
cd fastapi-ollama-backend
docker compose up --build -d
docker compose exec ollama ollama pull llama3
```

That's it. Your AI backend runs at **`http://localhost:8000`** with Swagger docs at **`http://localhost:8000/docs`**.

### Or without Docker

```bash
git clone https://github.com/yoosuf/fastapi-ollama-backend.git
cd fastapi-ollama-backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Set up PostgreSQL and Ollama, then:
./entrypoint.sh
```

### First API Call

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "demo1234"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=demo@example.com" \
  -F "password=demo1234" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Generate AI response
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Explain quantum computing in 3 sentences."}'
```

---

## 💡 Use Cases

### 📄 Document Intelligence
Extract structured data from invoices, contracts, forms, and legal documents.

```bash
curl -X POST "http://localhost:8000/api/v1/extract-invoice?text_content=Invoice%20%23999%20from%20TechCorp.%20Date:%202026-01-15.%202%20Laptops%20at%20%241000%20each.%20Total:%20%242000." \
  -H "Authorization: Bearer $TOKEN"
```

### 🏥 Privacy-First Healthcare
Process patient records, clinical notes, and medical documents on-premises — HIPAA-friendly by design.

### ⚖️ Legal Document Analysis
Extract clauses, parties, and obligations from contracts without sending sensitive data to third parties.

### 📊 Natural Language to SQL
Ask questions in English and get SQL queries — the structured JSON pattern makes this trivial.

### 🔬 Research & Academia
Run AI assistants with full data privacy for sensitive research data.

### 🏢 Enterprise Internal Assistant
Deploy behind your firewall with role-based access for different teams.

---

## 📖 API Overview

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | — | Health check |
| `POST` | `/api/v1/auth/register` | — | Register new user |
| `POST` | `/api/v1/auth/login` | — | Login, get JWT token |
| `POST` | `/api/v1/prompts` | JWT | Send prompt to LLM |
| `GET` | `/api/v1/prompts` | JWT | List your prompts |
| `GET` | `/api/v1/prompts/{id}` | JWT | Get prompt details |
| `POST` | `/api/v1/extract-invoice` | JWT | Extract JSON from text |
| `GET` | `/api/v1/admin/users` | Admin | List all users |
| `GET` | `/api/v1/admin/all-prompts` | Admin | List all prompts |

📘 **Full API docs**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md) or live at `/docs` (Swagger).

---

## 🏗 Architecture

```
┌─────────────────────┐
│     KeepAI App      │
│  Router → Service    │
│     → Interface      │
│        ↓             │
│  ┌──────────────┐   │
│  │  PostgreSQL   │   │
│  │  (asyncpg)    │   │
│  └──────────────┘   │
│        ↓             │
│  ┌──────────────┐   │
│  │  Ollama API   │   │
│  │  (local LLM)  │   │
│  └──────────────┘   │
└─────────────────────┘
```

**Clean Architecture / Hexagonal** — `Router (presentation)` → `Service (application)` → `LLMInterface (port)` → `OllamaClient (adapter)`.

Each layer is independently testable and swappable. Swap Ollama for OpenAI, Anthropic, or any API — change one file.

[Full architecture doc →](ARCHITECTURE.md)

---

## 🗺️ Roadmap

- [x] JWT Auth + RBAC
- [x] PostgreSQL persistence
- [x] Structured JSON extraction
- [x] Docker Compose
- [ ] Streaming responses (SSE)
- [ ] Chat history & conversations
- [ ] Web UI (React + Monaco Editor)
- [ ] Multi-model routing
- [ ] RAG (Retrieval-Augmented Generation)
- [ ] Code generation agents
- [ ] API key management
- [ ] Rate limiting
- [ ] Usage analytics dashboard

[Full roadmap →](ROADMAP.md)

---

## 🤝 Contributing

We love contributions! Check out our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

**Ways to contribute:**
- 🐛 Report bugs via [GitHub Issues](https://github.com/yoosuf/fastapi-ollama-backend/issues)
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests

---

## 🛡️ Security

Found a vulnerability? Please read our [Security Policy](SECURITY.md) for reporting instructions.

**Key security features:**
- JWT tokens with configurable expiry
- bcrypt password hashing
- Database-driven RBAC
- No cloud dependencies — your data stays yours
- Non-root user in Docker

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.

---

## 📬 Contact

**Yoosuf Mohamed** — [mayoosuf@gmail.com](mailto:mayoosuf@gmail.com)

Project Link: [https://github.com/yoosuf/fastapi-ollama-backend](https://github.com/yoosuf/fastapi-ollama-backend)

---

<p align="center">
  <strong>⭐ Star this project if you find it useful! ⭐</strong>
  <br>
  <sub>Built with ❤️ for the open-source community</sub>
</p>
