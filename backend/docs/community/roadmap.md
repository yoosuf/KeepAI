# Roadmap

KeepAI is under active development. This document outlines planned features and improvements.

## Legend

- ✅ Done
- 📋 Planned
- 💡 Under Consideration

---

## Phase 1: Foundation ✅

- [x] FastAPI application with hexagonal architecture
- [x] Ollama local LLM integration
- [x] JWT authentication (register/login)
- [x] Database-driven RBAC
- [x] PostgreSQL persistence with Alembic migrations
- [x] Structured JSON extraction (InvoiceAgent)
- [x] Streaming responses (SSE)
- [x] Connection pooling
- [x] Rate limiting
- [x] Permission caching
- [x] Request tracing
- [x] Docker & Docker Compose
- [x] Comprehensive test suite and CI
- [x] Gunicorn production server config
- [x] Structured docs in `/docs`

---

## Phase 2: Enhanced UX

### Conversational Context

- [ ] 📋 **Conversation history** — Persistent chat threads that pass prior turns to the LLM as context
- [ ] 📋 **WebSocket chat** — Real-time bidirectional interface for conversational use
- [ ] 📋 **Session management** — Named sessions, archive/restore

### Frontend

- [ ] 📋 **Web UI** — React application with:
  - Chat interface with streaming output
  - Prompt history browser
  - Admin dashboard
- [ ] 📋 **API playground** — Built-in UI for testing endpoints (similar to Swagger but focused on LLM UX)

### LLM Features

- [ ] 📋 **Multi-model routing** — Route prompts to different models based on task type or user preference
- [ ] 📋 **Model management API** — List, pull, and delete models from Ollama via REST
- [ ] 📋 **Custom system prompts** — Per-user or per-request system instructions
- [ ] 📋 **Parameter control** — Expose `temperature`, `top_p`, `max_tokens` via API

---

## Phase 3: Advanced Capabilities

### RAG (Retrieval-Augmented Generation)

- [ ] 📋 **Document ingestion** — Upload PDFs, markdown, text files
- [ ] 📋 **Vector embeddings** — Generate and store embeddings (`pgvector` or Chroma)
- [ ] 📋 **Semantic search** — Query documents in natural language
- [ ] 📋 **Context-aware chat** — Chat with your documents

### Code Development Agents

- [ ] 📋 **Code generation** — Generate functions, classes, and tests from specs
- [ ] 📋 **Project scaffolding** — Generate full project structures
- [ ] 📋 **Sandbox execution** — Run generated code in isolated containers

### Enterprise Features

- [ ] 📋 **API key management** — Generate, rotate, and revoke API keys
- [ ] 📋 **Usage analytics** — Dashboard with token usage, request counts, latency
- [ ] 📋 **Audit logging** — All actions logged for compliance

---

## Phase 4: Production Hardening

- [ ] 📋 **Redis caching** — Cache frequent LLM responses and rate-limit state
- [ ] 📋 **Background task queue** — Async LLM jobs via Celery or similar
- [ ] 📋 **Multi-tenant support** — Isolated data per organization
- [ ] 📋 **SSO / OAuth2** — Social login (Google, GitHub, Microsoft)
- [ ] 📋 **Prometheus metrics** — Expose `/metrics` endpoint
- [ ] 📋 **Grafana dashboards** — Pre-built monitoring dashboards

---

## Phase 5: Ecosystem

- [ ] 💡 **Python SDK** — Client library for Python
- [ ] 💡 **TypeScript SDK** — Client library for Node.js / TypeScript
- [ ] 💡 **OpenAI-compatible API** — Drop-in replacement for `openai` client
- [ ] 💡 **HuggingFace integration** — Pull models directly from HuggingFace Hub
- [ ] 💡 **Fine-tuning API** — Fine-tune models on custom data

---

## How to Influence the Roadmap

1. **Upvote** 👍 existing issues on [GitHub](https://github.com/yoosuf/KeepAI/issues)
2. **Submit** feature requests via [GitHub Issues](https://github.com/yoosuf/KeepAI/issues/new/choose)
3. **Contribute** — PRs are always welcome! See [Contributing](../development/contributing.md).

---

*Last updated: 2026-06*
