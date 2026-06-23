# API Documentation

KeepAPI exposes a REST API at `/api/v1`. Live interactive documentation is available at `/docs` (Swagger) and `/redoc` (ReDoc) when the server is running.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require JWT authentication. Obtain a token via login, then include it in the `Authorization` header:

```
Authorization: Bearer <your_access_token>
```

---

## Endpoints

### Health Check

```http
GET /health
```

**Response** `200 OK`

```json
{
  "status": "ok"
}
```

---

### Auth: Register

```http
POST /api/v1/auth/register
```

Creates a new user account.

**Request Body**

| Field    | Type   | Required | Description |
|----------|--------|----------|-------------|
| `email`  | string | ✅       | Valid email address |
| `password` | string | ✅    | Password (min 8 characters recommended) |
| `role`   | string | ❌      | Role name: `"admin"` or `"user"` (defaults to `"user"`) |

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "role": "user"
  }'
```

**Response** `201 Created`

```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "role_id": 2
}
```

---

### Auth: Login

```http
POST /api/v1/auth/login
```

Authenticates a user and returns a JWT token.

**Request Body** (OAuth2 form data)

| Field      | Type   | Required | Description |
|------------|--------|----------|-------------|
| `username` | string | ✅       | User's email |
| `password` | string | ✅       | User's password |

**Example**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=user@example.com" \
  -F "password=securepassword"
```

**Response** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

The token expires in 30 minutes by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

---

### Prompts: Generate

```http
POST /api/v1/prompts
```

Sends a prompt to the LLM and returns the generated response. Requires authentication.

**Request Body**

| Field         | Type   | Required | Description |
|---------------|--------|----------|-------------|
| `prompt_text` | string | ✅       | The prompt to send to the LLM |
| `model_name`  | string | ❌       | Model name (e.g., `"llama3"`). Defaults to `OLLAMA_MODEL` env var |

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
    "total_duration_ms": 4523,
    "eval_count": 120
  },
  "created_at": "2026-01-15T10:30:00Z"
}
```

---

### Prompts: List

```http
GET /api/v1/prompts?skip=0&limit=50
```

Lists prompts for the authenticated user. Requires authentication.

**Query Parameters**

| Param  | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `skip` | int  | ❌       | 0       | Number of records to skip |
| `limit`| int  | ❌       | 50      | Maximum records per page |

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
    "prompt_text": "Explain...",
    "response_text": "...",
    "model_name": "llama3",
    "processing_time_ms": 4523,
    "meta_data": {},
    "created_at": "2026-01-15T10:30:00Z"
  }
]
```

---

### Prompts: Get by ID

```http
GET /api/v1/prompts/{prompt_id}
```

Retrieves a specific prompt by ID (scoped to the authenticated user). Requires authentication.

**Example**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/prompts/42
```

**Response** `200 OK`

```json
{
  "id": 42,
  "prompt_text": "Explain...",
  "response_text": "...",
  "model_name": "llama3",
  "processing_time_ms": 4523,
  "meta_data": {},
  "created_at": "2026-01-15T10:30:00Z"
}
```

**Response** `404 Not Found` — if the prompt doesn't exist or doesn't belong to the user.

---

### Extract Invoice (Structured JSON)

```http
POST /api/v1/extract-invoice?text_content=<url_encoded_text>
```

Extracts structured invoice data from unstructured text using the LLM. Requires authentication.

**Query Parameters**

| Param         | Type   | Required | Description |
|---------------|--------|----------|-------------|
| `text_content`| string | ✅       | Raw invoice text to parse |

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

> Note: Extracted data quality depends on the LLM model and the clarity of the source text.

---

### Admin: List Users

```http
GET /api/v1/admin/users
```

Lists all registered users. Requires `users:read` permission (admin role). Requires authentication.

**Example**

```bash
curl -H "Authorization: Bearer $TOKEN" \
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

### Admin: List All Prompts

```http
GET /api/v1/admin/all-prompts
```

Lists all prompts across all users. Requires `prompts:read_all` permission (admin role). Requires authentication.

**Example**

```bash
curl -H "Authorization: Bearer $TOKEN" \
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

### 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden

```json
{
  "detail": "Insufficient permissions"
}
```

### 404 Not Found

```json
{
  "detail": "Prompt not found"
}
```

### 422 Validation Error

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

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Currently, there is no built-in rate limiting. This is on the [roadmap](ROADMAP.md). For production, add a reverse proxy (e.g., Nginx, Caddy) with rate limiting.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
