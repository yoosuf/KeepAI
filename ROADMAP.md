# Roadmap

KeepAI is under active development. This document outlines planned features and improvements.

## Legend

- ✅ Done
- 🔄 In Progress
- 📋 Planned
- 💡 Under Consideration

---

## Phase 1: Foundation (Current) ✅

- [x] FastAPI application with clean architecture
- [x] Ollama local LLM integration
- [x] JWT authentication (register/login)
- [x] Database-driven RBAC
- [x] PostgreSQL persistence with Alembic migrations
- [x] Structured JSON extraction
- [x] Docker & Docker Compose
- [x] Testing and CI pipeline
- [x] Comprehensive documentation

---

## Phase 2: Enhanced UX (Next)

### Streaming & Real-time

- [ ] 📋 **Server-Sent Events (SSE)** — Stream LLM responses token-by-token
- [ ] 📋 **WebSocket chat** — Real-time conversational interface
- [ ] 📋 **Conversation history** — Persistent chat threads with context

### Frontend

- [ ] 📋 **Web UI** — React application with:
  - Chat interface
  - Prompt history browser
  - Admin dashboard
  - API key management UI
- [ ] 📋 **API playground** — Built-in UI for testing endpoints

### LLM Features

- [ ] 📋 **Multi-model routing** — Route prompts to different models based on task
- [ ] 📋 **Model management API** — List, pull, delete models from Ollama
- [ ] 📋 **Custom system prompts** — Per-user or per-request system instructions
- [ ] 📋 **Temperature & parameter control** — Expose LLM parameters via API

---

## Phase 3: Advanced Capabilities

### RAG (Retrieval-Augmented Generation)

- [ ] 📋 **Document ingestion** — Upload PDFs, text files, markdown
- [ ] 📋 **Vector embeddings** — Generate and store embeddings (pgvector or Chroma)
- [ ] 📋 **Semantic search** — Query your documents in natural language
- [ ] 📋 **Context-aware chat** — Chat with your documents

### Code Development

- [ ] 📋 **Code generation agents** — Generate functions, classes, tests from specs
- [ ] 📋 **Project scaffolding** — Generate full project structures
- [ ] 📋 **File editing** — Apply changes to existing files
- [ ] 📋 **Sandbox execution** — Run generated code in isolated containers

### Enterprise Features

- [ ] 📋 **API key management** — Generate, rotate, and revoke API keys
- [ ] 📋 **Rate limiting** — Per-user/per-key request limits
- [ ] 📋 **Usage analytics** — Dashboard with token usage, request counts, costs
- [ ] 📋 **Audit logging** — All actions logged for compliance

---

## Phase 4: Production Hardening

- [ ] 📋 **Redis caching** — Cache frequent LLM responses
- [ ] 📋 **Async task queue** — Background processing via Celery/Kafka
- [ ] 📋 **Multi-tenant support** — Isolated data per organization
- [ ] 📋 **SSO / OAuth** — Social login (Google, GitHub, Microsoft)
- [ ] 📋 **Prometheus metrics** — Monitor performance and usage
- [ ] 📋 **Grafana dashboards** — Visual monitoring

---

## Phase 5: Ecosystem

- [ ] 💡 **Python SDK** — Client library for Python
- [ ] 💡 **TypeScript SDK** — Client library for Node.js/TypeScript
- [ ] 💡 **OpenAI-compatible API** — Drop-in replacement for OpenAI clients
- [ ] 💡 **Plugin system** — Extend functionality with plugins
- [ ] 💡 **HuggingFace integration** — Pull models directly from HuggingFace
- [ ] 💡 **Fine-tuning API** — Fine-tune models on custom data

---

## How to Influence the Roadmap

This roadmap is community-driven. To prioritize features:

1. **Upvote** 👍 existing issues on GitHub
2. **Submit** feature requests via [GitHub Issues](https://github.com/yoosuf/fastapi-ollama-backend/issues/new/choose)
3. **Contribute** — PRs are always welcome!

---

## Current Release

- **v1.0.0** — Foundation release with auth, RBAC, LLM integration, and structured extraction

---

*Last updated: 2026*
