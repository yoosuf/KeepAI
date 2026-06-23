# Walkthrough: KeepAPI

I have successfully built the complete backend application with Authentication, Accounting, and a fully database-driven Role-Based Access Control (RBAC) system.

## 1. Project Structure

The project follows a clean architecture:

- `src/routes`: API endpoints (Presentation)
- `src/services`: Business logic and LLM integration (Domain/Application)
- `src/models.py` & `src/database.py`: Persistence (Infrastructure)
- `alembic/`: Database migrations

## 2. Key Components

### API Layer

- **POST /api/v1/auth/register**: Register new user. Assigns role "user" or "admin" by verifying dynamic DB tables.
- **POST /api/v1/auth/login**: Login to get JWT Token.
- **POST /api/v1/prompts**: (Protected) Accepts a prompt, saves to DB with user_id.
- **POST /api/v1/extract-invoice**: (Protected) Specialized accounting endpoint returning JSON.
- **GET /api/v1/admin/users**: Protected by `users:read` permission.
- **GET /api/v1/admin/all-prompts**: Protected by `prompts:read_all` permission.

### LLM Integration

- **Generic Generation**: Standard LLM text generation.
- **Structured JSON**: Uses Ollama's `format="json"` mode.

### Database & Security

- **PostgreSQL** with `asyncpg` driver.
- **Alembic** migrations (Init, Add Users, Add DB RBAC).
- **RBAC**: `PermissionChecker` dependency dynamically queries `Role`, `Permission`, and `role_permissions` tables.

## 3. How to Run

### Using Docker (Recommended)

1. **Start Services**:

   ```bash
   docker-compose up --build
   ```

2. **Pull Model and Test Auth**:

   Register an Admin (The migration seeds 'admin' role with all permissions):

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'
   ```

   Login to get Admin Token:

   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -F "username=admin@example.com" \
     -F "password=adminpass"
   ```

   Test Admin Endpoint (Requires `users:read` dynamic permission):

   ```bash
   TOKEN="<admin_token>"
   curl http://localhost:8000/api/v1/admin/users -H "Authorization: Bearer $TOKEN"
   ```

## 4. Verification Check

- **Security**: JWT Auth + Dynamic Permission Checks.
- **Flexible RBAC**: Roles and Permissions are now in the DB, not hardcoded.
- **Structured Output**: Invoice extraction returns validated JSON.
