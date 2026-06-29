# Roadmap

KeepAI is under active development. This document outlines planned features and improvements.

## Legend

- ✅ Done
- 📋 Planned
- 💡 Under Consideration

---

## Phase 1: Foundation ✅

- [x] FastAPI application with clean architecture (hexagonal/ports-and-adapters)
- [x] Ollama local LLM integration (LLMInterface + OllamaClient)
- [x] JWT authentication (register/login with Argon2id hashing)
- [x] Database-driven RBAC (dynamic roles and permissions)
- [x] PostgreSQL persistence with async SQLAlchemy 2.0
- [x] Structured JSON extraction (InvoiceAgent)
- [x] Docker & Docker Compose (backend + frontend in docker/ directory)
- [x] Alembic migrations (6 migrations covering all tables)
- [x] Testing and CI pipeline (pytest, GitHub Actions)
- [x] Comprehensive documentation

---

## Phase 2: Enhanced UX ✅

### Streaming & Real-time

- [x] Server-Sent Events (SSE) — stream LLM responses token-by-token
- [x] WebSocket chat — real-time conversational interface
- [x] Conversation threads — persistent chat with full message history

### Frontend

- [x] React 18 + TypeScript + Vite application
- [x] Chat interface (multi-turn, system prompt, temperature/top-p controls)
- [x] Conversation threads browser with pagination
- [x] Prompt history browser with detail view and pagination
- [x] Admin dashboard (users + prompts tables)
- [x] Models management (list, pull, delete)
- [x] API Playground (prompt + invoice extraction tabs)
- [x] API key management UI (create, copy, revoke)
- [x] Documents/RAG management UI (upload, list, search, query LLM)
- [x] Usage analytics dashboard (stat cards, bar charts, per-user table)

### LLM Features

- [x] Multi-model routing (route prompts by task_type)
- [x] Model management API (list, pull, delete from Ollama)
- [x] Custom system prompts per request
- [x] Temperature, top_p, max_tokens parameter control

---

## Phase 3: Advanced Capabilities

### RAG (Retrieval-Augmented Generation)

- [x] Document ingestion — upload text files, chunking, keyword search
- [x] Vector embeddings endpoint (ready for pgvector upgrade)
- [ ] 📋 Semantic search — upgrade from keyword to vector search
- [ ] 📋 Context-aware chat — chat with document context injected into LLM

### Code Development

- [ ] 📋 Code generation agents — generate functions, classes, tests from specs
- [ ] 📋 Project scaffolding — generate full project structures
- [ ] 📋 File editing — apply changes to existing files
- [ ] 📋 Sandbox execution — run generated code in isolated containers

### Enterprise Features

- [x] API key management — generate, revoke, SHA-512 hashed keys
- [x] Rate limiting — per-user/per-key limits (slowapi)
- [x] Usage analytics — dashboard with request counts, processing time, model usage
- [x] Audit logging — all actions logged for compliance (schema exists, not yet wired)

---

## Phase 4: Production Hardening

- [ ] 📋 Redis caching — frequent LLM response cache, rate limit storage
- [ ] 📋 Async task queue — background processing for large documents, model pulls
- [ ] 📋 Multi-tenant support — organization-scoped isolation
- [ ] 📋 SSO / OAuth — social login (Google, GitHub, Microsoft)
- [ ] 📋 Prometheus metrics — request counters, latency histograms
- [ ] 📋 Grafana dashboards — visual monitoring dashboards

---

## Phase 5: Ecosystem

- [ ] 💡 Python SDK — client library for programmatic access
- [ ] 💡 TypeScript SDK — client library for Node.js/TypeScript
- [ ] 💡 OpenAI-compatible API — drop-in replacement for OpenAI clients
- [ ] 💡 Plugin system — extend functionality with plugins
- [ ] 💡 HuggingFace integration — pull models directly from HuggingFace
- [ ] 💡 Fine-tuning API — fine-tune models on custom datasets

---

## Current Release

- **v1.2.0** — Full-stack monorepo with React frontend, conversation threads, WebSocket, API keys, RAG pipeline, usage analytics, and audit logging schema

---

*Last updated: 2026*
