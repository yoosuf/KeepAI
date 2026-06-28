# API Reference

KeepAI exposes a REST API at `/api/v1`. When the server is running, interactive docs are available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Base URL

```
http://localhost:8000/api/v1
```

---

## Authentication

Most endpoints require a JWT token. Obtain one via login, then pass it in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after 30 minutes by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

---

## Endpoints

### Health

#### Liveness Check

```http
GET /health/live
```

Always returns 200 if the process is up.

**Response** `200 OK`
```json
{ "status": "ok" }
```

#### Readiness Check

```http
GET /health/ready
```

Pings the database (`SELECT 1`) and Ollama (`/api/tags`). Returns 503 if either is unavailable.

**Response** `200 OK`
```json
{ "status": "ok", "db": "ok", "ollama": "ok" }
```

**Response** `503 Service Unavailable`
```json
{ "status": "degraded", "db": "ok", "ollama": "error" }
```

---

### Auth

#### Register

```http
POST /api/v1/auth/register
Content-Type: application/json
```

Creates a new user account.

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | yes | Valid email address |
| `password` | string | yes | Plaintext password (Argon2id hashed on server) |
| `role` | string | no | `"admin"` or `"user"` — defaults to `"user"` |

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "securepass123",
    "role": "user"
  }'
```

**Response** `201 Created`
```json
{
  "id": 1,
  "email": "alice@example.com",
  "is_active": true,
  "role_id": 2
}
```

**Response** `400 Bad Request` — email already exists or role name not found.

---

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded
```

Authenticates a user and returns a JWT access token. Uses OAuth2 password flow (form data, not JSON).

**Request Body** (form data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | yes | User's email address |
| `password` | string | yes | User's password |

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=alice@example.com" \
  -F "password=securepass123"

# Capture token in shell
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=alice@example.com" \
  -F "password=securepass123" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

**Response** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Response** `401 Unauthorized` — incorrect email or password.

---

### Prompts

#### Create Prompt

```http
POST /api/v1/prompts
Authorization: Bearer <token>
Content-Type: application/json
```

Sends a prompt to the LLM, persists the response, and returns the result.

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt_text` | string | yes | The prompt to send to the LLM |
| `model_name` | string | no | Model name (e.g., `"llama3"`). Defaults to `OLLAMA_MODEL` env var |

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "prompt_text": "Explain machine learning in 3 bullet points.",
    "model_name": "llama3"
  }'
```

**Response** `201 Created`
```json
{
  "id": 42,
  "prompt_text": "Explain machine learning in 3 bullet points.",
  "response_text": "- Machine learning is a subset of AI...",
  "model_name": "llama3",
  "processing_time_ms": 4523,
  "meta_data": {
    "raw_response": {
      "model": "llama3",
      "total_duration": 4523000000,
      "eval_count": 120
    }
  },
  "created_at": "2026-01-15T10:30:00Z"
}
```

**Required permission**: `prompts:create`

---

#### Stream Prompt

```http
POST /api/v1/prompts/stream
Authorization: Bearer <token>
Content-Type: application/json
```

Sends a prompt and streams the response token-by-token as Server-Sent Events. Not persisted to DB.

**Request Body** — same as [Create Prompt](#create-prompt).

**Response** `200 OK` — `Content-Type: text/event-stream`

```
data: The

data:  quick

data:  brown

data:  fox

data: [DONE]
```

**Example** (using curl)

```bash
curl -N -X POST http://localhost:8000/api/v1/prompts/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prompt_text": "Write a haiku about code."}'
```

---

#### List Prompts

```http
GET /api/v1/prompts?skip=0&limit=50
Authorization: Bearer <token>
```

Lists prompts belonging to the authenticated user, newest first.

**Query Parameters**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `skip` | int | 0 | Records to skip (for pagination) |
| `limit` | int | 50 | Maximum records to return |

**Example**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/prompts?skip=0&limit=10"
```

**Response** `200 OK`
```json
[
  {
    "id": 42,
    "prompt_text": "Explain machine learning...",
    "response_text": "...",
    "model_name": "llama3",
    "processing_time_ms": 4523,
    "meta_data": {},
    "created_at": "2026-01-15T10:30:00Z"
  }
]
```

---

#### Get Prompt by ID

```http
GET /api/v1/prompts/{prompt_id}
Authorization: Bearer <token>
```

Retrieves a specific prompt. Scoped to the authenticated user — users cannot see each other's prompts.

**Example**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/prompts/42
```

**Response** `200 OK` — same schema as list item above.

**Response** `404 Not Found` — prompt doesn't exist or belongs to another user.

---

#### Extract Invoice (Structured JSON)

```http
POST /api/v1/extract-invoice?text_content=<url_encoded_text>
Authorization: Bearer <token>
```

Extracts structured invoice data from unstructured text using the `InvoiceAgent` prompt template and the LLM's JSON mode.

**Query Parameters**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `text_content` | string | yes | Raw invoice text to parse |

**Example**

```bash
curl -X POST "http://localhost:8000/api/v1/extract-invoice?text_content=Invoice%20%23999%20from%20TechCorp.%20Date:%202026-01-15.%202%20Laptops%20at%20%241000%20each.%20Total:%20%242000." \
  -H "Authorization: Bearer $TOKEN"
```

**Response** `200 OK`
```json
{
  "invoice_number": "999",
  "vendor_name": "TechCorp",
  "date": "2026-01-15",
  "items": [
    {
      "description": "Laptop",
      "quantity": 2,
      "unit_price": 1000.0,
      "total": 2000.0
    }
  ],
  "total_amount": 2000.0,
  "currency": "USD"
}
```

> Extraction quality depends on the LLM model and clarity of the source text. Larger models produce better results.

---

### Admin

Admin endpoints require the authenticated user to have the corresponding permission. Attempting access without the permission returns 403.

#### List All Users

```http
GET /api/v1/admin/users
Authorization: Bearer <admin_token>
```

**Required permission**: `users:read` (admin role)

**Example**

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/users
```

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "is_active": true,
    "role": {
      "id": 1,
      "name": "admin"
    }
  }
]
```

---

#### List All Prompts

```http
GET /api/v1/admin/all-prompts
Authorization: Bearer <admin_token>
```

Lists all prompts across all users.

**Required permission**: `prompts:read_all` (admin role)

**Example**

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/all-prompts
```

**Response** `200 OK`
```json
[
  {
    "id": 42,
    "user_id": 1,
    "prompt_text": "...",
    "response_text": "...",
    "model_name": "llama3",
    "created_at": "2026-01-15T10:30:00Z"
  }
]
```

---

## Error Responses

All errors follow FastAPI's standard format.

### 401 Unauthorized
```json
{ "detail": "Could not validate credentials" }
```
Token is missing, expired, or invalid.

### 403 Forbidden
```json
{ "detail": "Operation not permitted. Missing permission: users:read" }
```
User is authenticated but lacks the required permission.

### 404 Not Found
```json
{ "detail": "Prompt not found" }
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
Request body failed Pydantic validation.

### 429 Too Many Requests
```json
{ "detail": "Rate limit exceeded: 20 per 1 minute" }
```
Rate limit hit. Default: 20 LLM requests per minute per user.

### 500 Internal Server Error
```json
{ "detail": "Internal server error" }
```
Unexpected error — check server logs for details.

---

## Rate Limiting

LLM endpoints (`/prompts`, `/prompts/stream`, `/extract-invoice`) are rate-limited per user (by JWT email) or by IP for unauthenticated requests. Default: `20/minute`, configurable via `RATE_LIMIT_LLM` env var.

---

## Response Headers

Every response includes:

| Header | Description |
|--------|-------------|
| `X-Request-ID` | Unique request identifier (from `X-Request-ID` input header or auto-generated UUID) |
| `X-Response-Time-Ms` | Server-side processing time in milliseconds |

---

## Pagination

List endpoints accept `skip` and `limit` query parameters:

```
GET /api/v1/prompts?skip=0&limit=20   # Page 1
GET /api/v1/prompts?skip=20&limit=20  # Page 2
GET /api/v1/prompts?skip=40&limit=20  # Page 3
```
