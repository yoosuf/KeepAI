# Next Steps

This document outlines gaps, missing features, and improvement opportunities for KeepAI, organized by priority.

## Priority Scale

- **P0** — Must fix before production (security, data integrity, broken features)
- **P1** — Should fix soon (important UX gaps, missing test coverage, incomplete features)
- **P2** — Nice to have (enhancements, polish)
- **P3** — Future (ecosystem, advanced features)

---

## P0 — Critical

### 1. Audit logging is defined but never called

The `AuditLog` model and `record_usage()` method exist in `src/modules/analytics/` but are never invoked by any router or service. The `audit_logs` table is created in the schema but never written to. `UsageRecord` is also never populated.

**Files affected:** `analytics/service.py`, `prompts/service.py`, `conversations/service.py`, `documents/service.py`, `api_keys/service.py`, `ws/router.py`

**Fix**: Inject `AnalyticsService` into every mutation service. Call `record_usage()` for:
- Prompt creation (prompts/service.py)
- Conversation chat messages (conversations/service.py, ws/router.py)
- Document upload/deletion (documents/service.py)
- API key creation/revocation (api_keys/service.py)
Call `AuditLog` creation for security-relevant actions: login, register, admin operations.

### 2. Missing security headers

`main.py` adds CORS middleware but no security headers middleware. Missing:
- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Referrer-Policy`

**Fix**: Add a `SecureHeadersMiddleware` in `src/core/middleware.py`.

### 3. CORS wide open

`CORS_ORIGINS = ["*"]` in `config.py` allows any origin in production.

**Fix**: Restrict to specific origins in production (e.g., the frontend domain). Document how to configure.

### 4. Hardcoded `SECRET_KEY=changethis` in docker-compose

The Docker deployment uses a known default secret key.

**Fix**: Document `openssl rand -hex 32` generation. Add a startup check that warns if the key is the default.

### 5. No rate limiting on auth endpoints

`POST /auth/login` and `POST /auth/register` have no rate limiting, enabling brute force attacks.

**Fix**: Add `@limiter.limit("5/minute")` on login, `@limiter.limit("2/minute")` on register.

### 6. Embeddings generation is broken

`DocumentService.generate_embeddings()` uses the LLM with a text prompt ("Generate an embedding for...") instead of a real embedding model. This produces text, not vectors.

**Fix**: Pull `nomic-embed-text` via Ollama and call `/api/embeddings`. Or integrate pgvector with a real embedding provider.

### 7. No tests for 4 critical modules

| Module | Endpoints | Test Status |
|--------|-----------|-------------|
| Conversations | 6 REST + WebSocket | No tests |
| API Keys | 3 (list, create, revoke) | No tests |
| Analytics | 2 (stats, user-stats) | No tests |
| Documents/RAG | 8 (CRUD, search, upload, embed) | No tests |

**Fix**: Write test suites following patterns in `tests/api/test_auth.py` (FastAPI `TestClient` + mocked DB) and `tests/services/test_prompt_service.py` (service-level with mocked dependencies).

### 8. `DEPLOYMENT_GUIDE.md` references non-existent files

`backend/DEPLOYMENT_GUIDE.md` references `docker-compose.prod.yml` multiple times (lines 119, 166, 411) — a file that **does not exist** anywhere in the repo. Also uses `cd fastapi-ollama-backend` (wrong directory name) and has 12+ stale docker-compose path references.

**Fix**: Rewrite deployment guide to use `docker compose -f docker/docker-compose.yml`. Either create a `docker/docker-compose.prod.yml` or remove all references.

✅ **DONE**: Consolidated into `docs/guides/deployment.md` with correct docker paths. Old file removed.

---

## P1 — High

### 9. SSE streaming not consumed by frontend

Backend has `POST /prompts/stream` and `POST /chat/stream` endpoints, but no frontend page offers streaming. The WebSocket chat doesn't stream tokens either — it waits for the full response.

**Fix**: Add streaming toggle to Chat page (switch between WS batch mode and SSE streaming). Add streaming demo to Playground. Implement token-by-token streaming over WebSocket via `LLMInterface.stream_chat()`.

### 10. No password reset flow

No "forgot password" mechanism exists. Users cannot recover accounts.

**Fix**: Add email-based password reset flow:
- `POST /auth/forgot-password` — generates reset token, emails user
- `POST /auth/reset-password` — validates token, updates password
- Frontend password reset page

### 11. No SSO/OAuth

Only email/password authentication. No Google, GitHub, or Microsoft login.

**Fix**: Add OAuth integration (e.g., `authlib`) with provider configuration. Frontend social login buttons.

### 12. Semantic search not implemented

Documents RAG uses `_simple_score()` — a keyword overlap scoring function. No vector embeddings, no semantic similarity.

**Fix**: Upgrade to pgvector:
1. Add pgvector extension migration
2. Replace `generate_embeddings()` with real embedding model
3. Replace `_simple_score()` with `<=>` cosine distance query
4. Add HNSW index for performance

### 13. Context-aware document chat missing

Users can search documents but cannot chat with document context injected into the LLM prompt.

**Fix**: Add `POST /documents/chat` endpoint that:
1. Searches relevant chunks
2. Injects context into system prompt
3. Returns LLM response grounded in documents

### 14. Admin pages lack pagination

`AdminUsers.tsx` and `AdminPrompts.tsx` fetch all records at once with no pagination controls (hard-coded limit of 100). Admin pages may become slow with many records.

**Fix**: Add Previous/Next pagination with skip/limit controls, matching the pattern in `Conversations.tsx` and `History.tsx`.

### 15. "Loading..." text everywhere (8 instances)

Every page uses `<p>Loading...</p>` instead of skeleton loaders.

**Files**: `AdminPrompts.tsx:17`, `AdminUsers.tsx:17`, `Analytics.tsx:77`, `ApiKeys.tsx:125`, `Conversations.tsx:89`, `Documents.tsx:192`, `History.tsx:32`, `ProtectedRoute.tsx:8`

**Fix**: Create `<Skeleton>`, `<SkeletonTable>`, `<SkeletonCard>` components. Replace all text loaders.

### 16. No React error boundaries

A crash in any page component takes down the entire app.

**Fix**: Create `<ErrorBoundary>` component wrapping each route or the entire `<Layout>`. Add friendly fallback UI with "Retry" button.

### 17. No toast/notification system

Frontend uses `alert()` and `confirm()` for all user feedback:
- `Chat.tsx` — `alert(data.message)` for WebSocket errors
- `Conversations.tsx` — `confirm()` for deletion
- `Documents.tsx` — `confirm()` for deletion
- `ApiKeys.tsx` — `confirm()` for revocation
- `Models.tsx` — `confirm()` for model deletion

**Fix**: Create `<ToastProvider>` context + `<Toast>` component with success/error/info/warning variants. Replace all `alert()`/`confirm()` calls.

### 18. No markdown rendering in chat

LLM responses contain markdown (headers, lists, code blocks, bold) but are displayed as raw text.

**Fix**: Install `react-markdown` + `remark-gfm`. Render message content through markdown. Add `prose` styling.

### 19. No Redis in docker-compose

`docker/docker-compose.yml` has no Redis service. Multi-instance rate limiting and caching require Redis.

**Fix**: Add `redis` service to `docker-compose.yml`. Configure slowapi to use Redis storage backend. Optionally add response caching.

### 20. No CI/CD for frontend

GitHub Actions CI only runs backend tests and linting. Frontend changes can break the build unnoticed.

**Fix**: Add frontend `npm run lint && npm run build` step to `.github/workflows/ci.yml`.

### 21. No request body size limiting

Uploads and large prompts are unbounded, risking OOM from huge payloads.

**Fix**: Add middleware limiting request body size (e.g., 10 MB for uploads, 1 MB for prompts).

### 22. Token tracking fields unused

`UsageRecord.prompt_tokens` and `response_tokens` are never populated from Ollama responses.

**Fix**: Parse Ollama response metadata for token counts. Update `record_usage()` calls to pass token data.

### 23. Empty `src/modules/rag/` package

`rag/__init__.py` exists but is empty. No models, schemas, service, or router.

**Fix**: Either implement the RAG module (agents, orchestration) or remove the stub.

### 24. No production-grade docker-compose.{prod,override}.yml

`docker/docker-compose.prod.yml` does not exist. For production deployments, users need a compose file with resource limits, port restrictions, and non-root users. The current `docker-compose.yml` is dev-oriented (wide-open CORS, default secrets, exposed ports).

**Fix**: Create `docker/docker-compose.prod.yml` with production hardening: resource limits, `env_file:` support, non-root users, restricted port ranges, healthcheck tuning.

### 25. `backend/docs/community/roadmap.md` severely outdated

8+ features marked 📋 (Planned) that are actually ✅ done:
- Conversation history, WebSocket chat, React UI, multi-model routing
- Model management API, custom system prompts, temperature controls
- API key management, usage analytics, audit logging

**Fix**: Update roadmap to reflect current v1.2.0 state. Move done items to "Completed" section.

✅ **DONE**: Roadmap rewritten at `docs/community/roadmap.md` with all v1.2.0 items checked. Old file removed.

---

## P2 — Medium

### 26. Search/filter on tables

Admin users, admin prompts, and conversations pages have no search input.

### 27. Dark mode

CSS uses only light theme colors. No `@media (prefers-color-scheme: dark)`, no toggle.

**Fix**: Add dark theme CSS variables, `ThemeContext`/`ThemeProvider`, toggle in sidebar footer, persist in localStorage.

### 28. Responsive/mobile layout

Zero `@media` queries in `index.css`. Sidebar is fixed 240px with no collapse. Tables don't scroll horizontally on small screens.

**Fix**: Add media query breakpoints (768px, 480px), collapsible sidebar with hamburger menu, responsive table containers.

### 29. Conversation title editing

`PUT /conversations/{id}/title` endpoint exists but no frontend UI for renaming. Conversations.tsx and Chat.tsx sidebar both show "Untitled" with no edit capability.

### 30. Document detail view

`GET /documents/{id}` endpoint returns content and chunk count, but no frontend page consumes it.

### 31. Embeddings generation button

`POST /documents/{id}/embed` endpoint exists but no UI action for it.

### 32. Code generation agents

Only `InvoiceAgent` exists. No agents for code generation, project scaffolding, file editing, or sandbox execution.

### 33. Prometheus metrics

No `/metrics` endpoint exposing request counters, latency histograms, or error rates.

### 34. Async task queue

Long-running operations (model pulls, large document processing) block the request thread.

### 35. Bulk operations

No batch delete for conversations or API keys. No batch endpoints.

### 36. Copy-to-clipboard on messages

No easy way to copy LLM responses from the chat interface.

### 37. Keyboard shortcuts

No shortcut system. No hint overlay.

### 38. Analytics visualization

Dashboard uses CSS bar charts. No chart library (Chart.js, Recharts) for proper visualizations.

### 39. Data retention policy

`UsageRecord` and `AuditLog` tables grow unboundedly with no cleanup mechanism.

### 40. Profile/settings page

No user-facing settings page. No way to change password or preferences. No route or sidebar link.

### 41. WebSocket reconnection

`Chat.tsx`'s `connectWs()` only connects on mount with no reconnection logic. `ws.onclose` sets `wsRef.current = null` but never retries. No exponential backoff, no heartbeat/ping.

### 42. Model pull progress

`Models.tsx` shows "Pulling..." status text but doesn't display real-time progress from Ollama's streaming pull response.

### 43. Auto-scroll lock for chat

Scrolling up to read history loses position when new messages arrive.

### 44. CHANGELOG only documents v1.0.0

`CHANGELOG.md` (and `backend/docs/community/changelog.md`) only document v1.0.0. Missing:
- v1.1.0: WebSocket chat, conversation threads, model management, multi-model routing
- v1.2.0: API keys, document RAG, usage analytics, audit logging, React frontend (8 pages), monorepo restructure

✅ **DONE**: Changelog rewritten at `docs/community/changelog.md` covering v1.0.0, v1.1.0, and v1.2.0. Old files removed.

### 45. Root `.env.example` would help discoverability

Only `backend/.env.example` exists. New developers scanning the repo root won't immediately find required env vars.

---

## P3 — Low

### 46. OpenAI-compatible API

Proxy `/v1/chat/completions` to Ollama for drop-in client compatibility.

### 47. Python SDK

Client library for programmatic access to KeepAI API.

### 48. TypeScript SDK

Client library for Node.js/TypeScript applications.

### 49. Plugin system

Plugin loader and extension API for third-party modules.

### 50. HuggingFace integration

Pull models directly from HuggingFace instead of Ollama.

### 51. Fine-tuning API

Fine-tune models on user-provided datasets.

### 52. Multi-tenant support

Organization-scoped isolation of users, conversations, documents, and keys.

### 53. Sandbox execution

Isolated code execution environment for generated code.

### 54. `Update backend/docs/` stale content

Besides the docker path issues (item 24) and roadmap (item 25), several other `backend/docs/` files have stale content referencing old project structure and files.

✅ **DONE**: All documentation consolidated into `docs/` directory with comprehensive rewrites — 19 files total (index, getting-started, architecture, api reference, 4 guides, 3 dev docs, 6 community docs, claude.md, next-steps.md). All `backend/docs/`, `backend/*.md`, and root `*.md` files removed.

---

## Recent Fixes (v1.2.0)

The following gaps were identified and fixed in recent sessions:

- **User.role type mismatch**: Frontend typed `role` as `Role` object, backend returned plain string. Fixed types and display.
- **user.id was email string**: JWT lacked `user_id` claim. Added to backend, decoded in frontend AuthContext.
- **Missing CSS (~63 classes)**: Chat sidebar, data tables, stat cards, bar charts, badges, buttons, forms, and search results were unstyled. Added 350 lines of CSS.
- **PromptResponse missing `updated_at`**: Schema field added.
- **WebSocket responses incomplete**: `message_count`, `user_id`, `created_at`, `updated_at` added to WS responses.
- **ChatRequest type too narrow**: Added `temperature`, `top_p`, `max_tokens`.
- **Hardcoded WS URL**: Changed to derive from `window.location`.
- **Playground invoice tab**: Wired up `extractInvoice` function with form UI.
- **Admin pagination**: API functions accept `skip`/`limit`.
- **Document search**: Sends `top_k` parameter.
- **Unused types removed**: `Role`, `Permission`, `AuthState`, `LoginForm`, `RegisterForm` cleaned.
- **ModelInfo/ConversationMessage types**: Added missing fields from backend schemas.
- **Docker files consolidated**: All Docker configs moved from root/backend/frontend into `docker/` directory. `.dockerignore` consolidated at repo root.
- **Stale docker paths fixed** across 14 documentation files — all `docker compose` commands updated to `docker compose -f docker/docker-compose.yml` in README, CONTRIBUTING, CLAUDE, TROUBLESHOOTING, WALKTHROUGH, FAQ, DEPLOYMENT_GUIDE, and all `backend/docs/` guides.
- **All documentation consolidated** into `docs/` directory — 19 files covering setup, architecture, API, guides, development, community, and roadmap. All old `backend/docs/`, `backend/*.md`, and root `*.md` files removed.
