# Walkthrough

A top-to-bottom tour of KeepAI's key systems with working curl examples.

---

## 1. Start the Stack

```bash
docker compose up --build -d
docker compose exec ollama ollama pull llama3
```

Verify everything is healthy:

```bash
curl http://localhost:8000/health/ready
# {"status": "ok", "db": "ok", "ollama": "ok"}
```

---

## 2. Authentication

### Register an Admin

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'
```

Response:
```json
{"id": 1, "email": "admin@example.com", "is_active": true, "role_id": 1}
```

### Register a Regular User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "userpass"}'
```

### Log In and Capture the Token

```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=admin@example.com" \
  -F "password=adminpass" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

USER_TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=user@example.com" \
  -F "password=userpass" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

Tokens are HS256-signed JWTs containing the user's email as `sub`. They expire in 30 minutes.

---

## 3. LLM Prompts

### Send a Prompt

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"prompt_text": "What is the Pythagorean theorem?"}'
```

Response:
```json
{
  "id": 1,
  "prompt_text": "What is the Pythagorean theorem?",
  "response_text": "The Pythagorean theorem states that...",
  "model_name": "llama3",
  "processing_time_ms": 3200,
  "meta_data": {"raw_response": {...}},
  "created_at": "2026-01-15T10:30:00Z"
}
```

The response and all metadata are persisted to the `prompts` table in PostgreSQL.

### Switch Models per Request

```bash
curl -X POST http://localhost:8000/api/v1/prompts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"prompt_text": "Write a Python quicksort.", "model_name": "codellama"}'
```

### Stream a Response

```bash
curl -N -X POST http://localhost:8000/api/v1/prompts/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"prompt_text": "Tell me a short story about a robot."}'
```

Tokens arrive as Server-Sent Events:
```
data: Once

data:  upon

data:  a

data:  time

...

data: [DONE]
```

### List Your Prompts

```bash
curl -H "Authorization: Bearer $USER_TOKEN" \
  "http://localhost:8000/api/v1/prompts?limit=5"
```

### Get a Specific Prompt

```bash
curl -H "Authorization: Bearer $USER_TOKEN" \
  http://localhost:8000/api/v1/prompts/1
```

---

## 4. Structured JSON Extraction (Invoice Agent)

The `InvoiceAgent` builds a JSON-extraction prompt and parses the LLM's response back into structured data.

```bash
curl -X POST "http://localhost:8000/api/v1/extract-invoice?text_content=Invoice%20%23999%20from%20TechCorp.%20Date:%202026-01-15.%202%20Laptops%20at%20%241000%20each.%20Total:%20%242000." \
  -H "Authorization: Bearer $USER_TOKEN"
```

Response:
```json
{
  "invoice_number": "999",
  "vendor_name": "TechCorp",
  "date": "2026-01-15",
  "items": [
    {"description": "Laptop", "quantity": 2, "unit_price": 1000.0, "total": 2000.0}
  ],
  "total_amount": 2000.0,
  "currency": "USD"
}
```

**Under the hood:**

1. `InvoiceAgent.get_extraction_prompt(text)` adds the JSON schema instruction to the raw text
2. `PromptService` calls `llm_client.generate(prompt, model, format="json")` — Ollama's JSON mode
3. `InvoiceAgent.parse_response(response_text)` deserializes the JSON string
4. The structured dict is returned directly (not persisted to DB as a Prompt)

---

## 5. RBAC: Admin-Only Endpoints

### List All Users (requires `users:read`)

```bash
# Admin can do this
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/users

# Regular user cannot — returns 403
curl -H "Authorization: Bearer $USER_TOKEN" \
  http://localhost:8000/api/v1/admin/users
# {"detail": "Operation not permitted. Missing permission: users:read"}
```

### List All Prompts (requires `prompts:read_all`)

```bash
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
  http://localhost:8000/api/v1/admin/all-prompts
```

---

## 6. How the Code Executes

Tracing `POST /api/v1/prompts` from request to DB:

```
1. Request hits src/modules/prompts/router.py → create_prompt()
2. get_current_user (Depends) → decodes JWT → queries users table → returns User
3. get_prompt_service (Depends) → creates PromptService(db, OllamaClient())
4. PromptService.create_prompt(prompt_text, model_name, user) →
     a. calls self.llm_client.generate(prompt_text, model_name)
     b. OllamaClient.generate() → POST http://ollama:11434/api/generate
     c. Returns {"response_text": ..., "processing_time_ms": ..., "meta_data": ...}
5. PromptService creates Prompt ORM object, db.add(), db.commit(), db.refresh()
6. Router serializes Prompt → PromptResponse Pydantic schema → JSON response
```

---

## 7. Database Schema

```sql
-- RBAC
SELECT name FROM roles;           -- admin, user
SELECT name FROM permissions;     -- users:read, prompts:read_all, prompts:create
SELECT r.name, p.name FROM role_permissions rp
  JOIN roles r ON rp.role_id = r.id
  JOIN permissions p ON rp.permission_id = p.id;

-- Users
SELECT id, email, is_active, role_id FROM users;

-- Prompts
SELECT id, user_id, model_name, processing_time_ms, created_at FROM prompts;
```

---

## 8. Observability

Every response includes tracing headers:

```bash
curl -v http://localhost:8000/health/live 2>&1 | grep -E "X-Request|X-Response"
# < X-Request-ID: 7f3c8a1b-2d4e-4f5a-9b0c-1e2f3a4b5c6d
# < X-Response-Time-Ms: 2
```

Pass `X-Request-ID` from your client to correlate requests in logs:
```bash
curl -H "X-Request-ID: my-trace-123" http://localhost:8000/api/v1/prompts \
  -H "Authorization: Bearer $TOKEN" ...
```

---

## Related

- [API Reference](../api/reference.md) — complete endpoint documentation
- [Architecture](../architecture.md) — system design
- [RBAC Guide](../guides/rbac.md) — roles and permissions
