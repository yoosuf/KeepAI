# KeepAI Context for Claude/OpenCode

## Project Overview

- **Monorepo** at `/Users/yoosuf/Desktop/KeepAI`
- `backend/` — Python 3.11+ FastAPI, SQLAlchemy async, PostgreSQL, Ollama
- `frontend/` — React 18 + Vite + TypeScript + react-router-dom
- `docker/` — All Docker configs (docker-compose.yml, Dockerfiles, nginx.conf)
- `docs/` — All documentation
- Root `.dockerignore` for monorepo Docker builds

## Docker Commands

Always use `-f docker/docker-compose.yml` — there is no docker-compose.yml at repo root.

```bash
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec ollama ollama pull llama3
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
docker compose -f docker/docker-compose.yml logs -f backend
docker compose -f docker/docker-compose.yml down
```

## Database

```bash
# Run migrations
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head

# Create new migration
docker compose -f docker/docker-compose.yml exec backend alembic revision --autogenerate -m "description"

# Check current migration
docker compose -f docker/docker-compose.yml exec backend alembic current
```

## Testing

```bash
# Backend (from backend/)
python -m pytest
python -m pytest tests/api/test_auth.py -v
python -m pytest --cov=src

# Frontend (from frontend/)
npm run build
```

## Key Architecture Patterns

- Clean Architecture: Routers → Services → Interfaces ← Adapters
- Each module: models.py, schemas.py, service.py, router.py
- Async throughout (asyncpg, httpx.AsyncClient)
- JWT auth with Argon2id password hashing
- RBAC via PermissionChecker dependency

## Frontend Patterns

- Vite dev server proxies `/api` to `localhost:8000`
- Auth stored in localStorage, decoded in AuthContext
- Plain fetch API (no Axios)
- React Context for auth (no Redux)

## Documentation

All documentation is in `docs/`. Update relevant files when adding features.

## Common Pitfalls

- `expire_on_commit=False` on DB sessions can cause stale reads
- WebSocket auth uses JWT from query params, not headers
- Ruff line length is 120 chars
- Docker build context is repo root, so Dockerfile COPY paths use `backend/` or `frontend/` prefix
- Never forget `-f docker/docker-compose.yml` in docker compose commands
