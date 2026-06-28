# RBAC Guide

KeepAI uses **database-driven Role-Based Access Control (RBAC)**. Roles, permissions, and their assignments are stored in PostgreSQL — no hardcoded permission maps in application code.

---

## Data Model

```
permissions
├── id          (int, PK)
├── name        (str, unique) — e.g. "users:read", "prompts:create"
└── description (str, nullable)

roles
├── id          (int, PK)
├── name        (str, unique) — e.g. "admin", "user"
└── permissions (many-to-many via role_permissions)

role_permissions  (association table)
├── role_id       → roles.id
└── permission_id → permissions.id

users
├── id
├── email
├── hashed_password
├── is_active
└── role_id       → roles.id  (one role per user)
```

One user has one role. One role has many permissions.

---

## Built-in Seed Data

Seeded by migration `000000000003_db_rbac.py`:

### Permissions

| Name | Description |
|------|-------------|
| `users:read` | View all registered users |
| `prompts:read_all` | View all prompts across all users |
| `prompts:create` | Create prompts (send to LLM) |

### Roles

| Role | Permissions |
|------|-------------|
| `admin` | `users:read`, `prompts:read_all`, `prompts:create` |
| `user` | `prompts:create` |

---

## How Permission Checking Works

The `PermissionChecker` class in `src/modules/auth/service.py` is a FastAPI dependency:

```python
class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, user: User = Depends(get_current_user_with_permissions)) -> User:
        user_permissions = [p.name for p in user.role.permissions]
        if self.required_permission not in user_permissions:
            raise HTTPException(403, f"Missing permission: {self.required_permission}")
        return user
```

Use it on any route:

```python
@router.get("/admin/users")
async def list_users(
    user: User = Depends(PermissionChecker("users:read")),
    db: AsyncSession = Depends(get_db),
):
    ...
```

---

## Permission Cache

`get_current_user_with_permissions()` caches the loaded `user → role → permissions` graph in memory for 5 minutes per user (max 5000 entries). This avoids a DB join on every request to a permission-gated endpoint.

**When to invalidate:**

```python
from src.modules.auth.service import invalidate_permission_cache

# Call this whenever a user's role changes
invalidate_permission_cache(user_id)
```

The cache is per-process — in multi-worker deployments (Gunicorn), each worker has its own cache. Role changes take effect within 5 minutes across all workers without any explicit invalidation.

---

## Adding a New Permission

### Step 1: Create a migration

```bash
alembic revision --autogenerate -m "add_reports_read_permission"
```

Edit the generated migration file in `alembic/versions/`:

```python
def upgrade() -> None:
    op.execute("""
        INSERT INTO permissions (name, description)
        VALUES ('reports:read', 'View analytics reports')
        ON CONFLICT (name) DO NOTHING;
    """)
    # Optionally assign to a role
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'admin' AND p.name = 'reports:read'
        ON CONFLICT DO NOTHING;
    """)

def downgrade() -> None:
    op.execute("DELETE FROM permissions WHERE name = 'reports:read'")
```

### Step 2: Apply the migration

```bash
alembic upgrade head
# or in Docker:
docker compose exec backend alembic upgrade head
```

### Step 3: Use the permission in a route

```python
@router.get("/reports")
async def get_reports(
    user: User = Depends(PermissionChecker("reports:read")),
    db: AsyncSession = Depends(get_db),
):
    ...
```

---

## Adding a New Role

```python
# In a migration
def upgrade() -> None:
    op.execute("""
        INSERT INTO roles (name) VALUES ('analyst')
        ON CONFLICT (name) DO NOTHING;
    """)
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id)
        SELECT r.id, p.id
        FROM roles r, permissions p
        WHERE r.name = 'analyst'
          AND p.name IN ('prompts:create', 'reports:read')
        ON CONFLICT DO NOTHING;
    """)
```

---

## Assigning a Role During Registration

The registration endpoint accepts an optional `role` field:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@example.com", "password": "pass", "role": "analyst"}'
```

If `role` is omitted, the user gets the `"user"` role.

> In production, restrict which roles can be self-assigned at registration. See [Deployment Guide](deployment.md#production-hardening).

---

## Changing a User's Role (Direct DB)

There is currently no API endpoint to change a user's role after registration. Update directly via SQL:

```sql
UPDATE users
SET role_id = (SELECT id FROM roles WHERE name = 'admin')
WHERE email = 'alice@example.com';
```

After updating, invalidate the permission cache if you are calling from application code:

```python
invalidate_permission_cache(user.id)
```

---

## Custom Permission Patterns

Beyond the built-in three permissions, you can introduce any namespace:

| Pattern | Example |
|---------|---------|
| `resource:action` | `invoices:read`, `invoices:delete` |
| `module:action` | `billing:manage` |
| `scope:resource:action` | `org:users:invite` |

Choose a naming convention and stick to it — the permission name is just a string compared at runtime.

---

## Security Considerations

- The `admin` role currently has all permissions. Create narrower roles for least-privilege access.
- Public admin registration is enabled by default — **disable it in production** (see [Deployment Guide](deployment.md)).
- Permission cache TTL is 5 minutes. Immediate revocation requires a process restart or `invalidate_permission_cache()` call.

---

## Related

- [Architecture — Auth Section](../architecture.md#auth-module-detail)
- [API Reference — Admin Endpoints](../api/reference.md#admin)
- [Deployment Guide — Hardening](deployment.md#production-hardening)
