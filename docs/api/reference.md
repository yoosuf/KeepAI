# API Documentation

KeepAI exposes a REST API at `/api/v1` and a WebSocket endpoint at `/ws/chat`. Live interactive documentation is available at `/docs` (Swagger) and `/redoc` (ReDoc).

---

## Base URL

```
http://localhost:8000/api/v1
```

WebSocket URL (derived from host):
```
ws://<host>/ws/chat?token=<jwt>
```

---

## Authentication

Most endpoints require JWT authentication. Obtain a token via login, then include it in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

---

## Health

### Liveness

```http
GET /health/live
```

Always returns 200 if the process is running. No dependencies.

**Response** `200 OK`
```json
{ "status": "ok" }
```

### Readiness

```http
GET /health/ready
```

Verifies database and Ollama connectivity before accepting traffic.

**Response** `200 OK`
```json
{ "status": "ready", "db": "ok", "llm": "ok" }
```

**Response** `503 Service Unavailable`
```json
{ "detail": { "status": "unavailable", "db": "could not connect to database" } }
```

---

## Auth

### Register

```http
POST /api/v1/auth/register
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | yes | Valid email address |
| `password` | string | yes | Password (min 8 chars recommended) |
| `role` | string | no | `"admin"` or `"user"` (defaults to `"user"`) |

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword"}'
```

**Response** `201 Created`
```json
{ "id": 1, "email": "user@example.com", "is_active": true, "role": "user" }
```

### Login

```http
POST /api/v1/auth/login
```

Uses OAuth2 form data.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | yes | User's email |
| `password` | string | yes | User's password |

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=user@example.com" \
  -F "password=securepassword"
```

**Response** `200 OK`
```json
{ "access_token": "eyJhbGciOiJIUzI1NiIs...", "token_type": "bearer" }
```

Token expires in 30 minutes by default.

---

## Prompts

### Generate

```http
POST /api/v1/prompts
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt_text` | string | yes | The prompt to send to the LLM |
| `model_name` | string | no | Model name. Defaults to `OLLAMA_MODEL` |
| `system_prompt` | string | no | System instructions |
| `task_type` | string | no | Task type for model routing |
| `temperature` | float | no | Sampling temperature (0.0-2.0) |
| `top_p` | float | no | Nucleus sampling (0.0-1.0) |
| `max_tokens` | int | no | Maximum tokens to generate |

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Explain ML in 3 points.", "model_name": "llama3"}'
```

**Response** `201 Created`
```json
{
  "id": 42,
  "prompt_text": "Explain ML in 3 points.",
  "response_text": "- Machine learning is a subset of AI...",
  "model_name": "llama3",
  "processing_time_ms": 4523,
  "meta_data": {},
  "created_at": "2026-01-15T10:30:00Z",
  "user_id": 1
}
```

### Stream

```http
POST /api/v1/prompts/stream
```

Same body as Generate. Returns SSE stream. Not persisted.

```
data: Machine
data:  learning
data: [DONE]
```

### List

```http
GET /api/v1/prompts?skip=0&limit=20
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Records to skip |
| `limit` | int | 20 | Max records per page |

**Response** `200 OK`
```json
{ "items": [...], "total": 1, "skip": 0, "limit": 20 }
```

### Get by ID

```http
GET /api/v1/prompts/{prompt_id}
```

Scoped to the authenticated user.

### Extract Invoice

```http
POST /api/v1/extract-invoice
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text_content` | string | yes | Raw invoice text |
| `model_name` | string | no | Model name |

Returns structured JSON with invoice_number, vendor_name, date, items, total_amount, currency.

---

## Chat (Multi-turn)

### Generate

```http
POST /api/v1/chat
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `messages` | array | yes | `[{role, content}]` roles: user/assistant/system |
| `model_name` | string | no | Model name |
| `system_prompt` | string | no | Prepended as system message |
| `temperature` | float | no | 0.0-2.0 |
| `top_p` | float | no | 0.0-1.0 |
| `max_tokens` | int | no | Max tokens |

### Stream

```http
POST /api/v1/chat/stream
```

Same body as Chat. Returns SSE stream.

---

## Conversations

### Create

```http
POST /api/v1/conversations
```

```json
{ "title": "My conversation", "model_name": "llama3" }
```

### List

```http
GET /api/v1/conversations?skip=0&limit=20
```

Returns conversations with message_count.

### Get

```http
GET /api/v1/conversations/{conversation_id}
```

Returns conversation with all messages.

### Update Title

```http
PUT /api/v1/conversations/{conversation_id}/title?title=New+Title
```

### Delete

```http
DELETE /api/v1/conversations/{conversation_id}
```

### Chat in Conversation

```http
POST /api/v1/conversations/{conversation_id}/chat
```

```json
{ "message": "Hello", "model_name": "llama3" }
```

---

## WebSocket

### Connect

```
ws://<host>/ws/chat?token=<jwt>
```

### Message Types

**Send: list_conversations**
```json
{ "type": "list_conversations" }
```
Response: `{ "type": "conversations", "items": [...] }`

**Send: get_conversation**
```json
{ "type": "get_conversation", "conversation_id": 1 }
```
Response: `{ "type": "conversation", "id": 1, "title": "...", "messages": [...], "user_id": 1, "created_at": "...", "updated_at": "..." }`

**Send: chat**
```json
{
  "type": "chat",
  "conversation_id": 1,
  "message": "Hello!",
  "model_name": "llama3",
  "system_prompt": "Be helpful",
  "temperature": 0.7,
  "top_p": 0.9
}
```
Response: `{ "type": "chat_response", "response_text": "...", "conversation_id": 1 }`

**Send: delete_conversation**
```json
{ "type": "delete_conversation", "conversation_id": 1 }
```
Response: `{ "type": "conversation_deleted", "conversation_id": 1 }`

**Send: ping**
```json
{ "type": "ping" }
```
Response: `{ "type": "pong" }`

---

## API Keys

### List

```http
GET /api/v1/api-keys
```

### Create

```http
POST /api/v1/api-keys
```

```json
{ "name": "My Key" }
```

**Response** `201 Created`
```json
{ "id": 1, "name": "My Key", "key": "ka_...", "is_active": true, "created_at": "..." }
```
The `key` value is only shown once at creation.

### Revoke

```http
DELETE /api/v1/api-keys/{key_id}
```

---

## Analytics

### User Stats

```http
GET /api/v1/analytics/stats?days=7
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `days` | int | null (all time) | Number of days to look back |

**Response** `200 OK`
```json
{
  "total_requests": 150,
  "total_processing_time_ms": 450000,
  "avg_processing_time_ms": 3000.0,
  "requests_by_model": { "llama3": 120, "mistral": 30 },
  "requests_by_action": { "prompt": 100, "chat": 50 },
  "requests_today": 12
}
```

### Admin: All User Stats

```http
GET /api/v1/analytics/admin/user-stats
```

Returns per-user stats for all users. Requires admin.

---

## Documents

### List

```http
GET /api/v1/documents
```

### Upload

```http
POST /api/v1/documents/upload
```

Multipart form with `file` field.

### Get

```http
GET /api/v1/documents/{document_id}
```

Returns document with content_text and chunk_count.

### Delete

```http
DELETE /api/v1/documents/{document_id}
```

### Search (GET)

```http
GET /api/v1/documents/search?q=keyword&top_k=5
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | required | Search query |
| `top_k` | int | 5 | Max results (max 50) |

### Search (POST)

```http
POST /api/v1/documents/search
```

```json
{ "query": "keyword", "top_k": 5 }
```

### Query with LLM

```http
POST /api/v1/documents/query
```

```json
{ "query": "What is this document about?", "top_k": 5 }
```

**Response** `200 OK`
```json
{ "results": [...], "response": "Found 5 relevant documents" }
```

### Generate Embeddings

```http
POST /api/v1/documents/{document_id}/embed
```

**Response** `200 OK`
```json
{ "status": "embedded" }
```

---

## Models

### List

```http
GET /api/v1/models
```

Returns models available in Ollama with name, size, digest, details.

### Pull

```http
POST /api/v1/models/pull
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Model name, e.g., `"llama3"` |
| `insecure` | boolean | no | Allow insecure connections |

Requires `models:manage` permission (admin).

### Delete

```http
DELETE /api/v1/models/{model_name}
```

Requires `models:manage` permission (admin).

---

## Admin

### List Users

```http
GET /api/v1/admin/users?skip=0&limit=100
```

Requires `users:read` permission (admin).

### List All Prompts

```http
GET /api/v1/admin/all-prompts?skip=0&limit=100
```

Requires `prompts:read_all` permission (admin).

---

## Error Responses

### 401 Unauthorized
```json
{ "detail": "Not authenticated" }
```

### 403 Forbidden
```json
{ "detail": "Insufficient permissions" }
```

### 404 Not Found
```json
{ "detail": "Resource not found" }
```

### 422 Validation Error
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

### 429 Rate Limit Exceeded
```json
{ "detail": "Rate limit exceeded. Please slow down." }
```

### 500 Internal Server Error
```json
{ "detail": "Internal server error" }
```

---

## Rate Limiting

Rate limiting is implemented via `slowapi` (configurable via `RATE_LIMIT_LLM` env var, default: `20/minute`). Limits are applied per user (JWT email) or fall back to client IP. See [Configuration](../guides/configuration.md) for details.

---

## Changelog

See [Changelog](../community/changelog.md) for version history.
