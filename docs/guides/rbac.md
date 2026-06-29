# Role-Based Access Control (RBAC)

KeepAI uses a database-driven RBAC system that allows dynamic permission management without code changes.

---

## Database Tables

The RBAC system uses four database tables:

```
users
+-- id (PK)
+-- email
+-- hashed_password
+-- is_active
+-- role_id (FK -> roles.id)
+-- created_at
+-- updated_at

roles
+-- id (PK)
+-- name (unique: "admin", "user")
+-- description
+-- created_at

permissions
+-- id (PK)
+-- name (unique: "users:read", "prompts:read_all", "models:manage", etc.)
+-- description
+-- created_at

role_permissions (join table)
+-- role_id (FK -> roles.id)
+-- permission_id (FK -> permissions.id)
+-- (composite PK on role_id, permission_id)
```

---

## Default Roles

### Admin

Has all permissions granted. Can:
- List all users (`users:read`)
- View all prompts (`prompts:read_all`)
- Manage models (`models:manage`)

### User

Has basic permissions. Can:
- Create and view own prompts
- Use chat and conversations
- Manage own API keys
- Upload and search own documents
- View own usage analytics

---

## How It Works

### Permission Checker

Endpoints are protected using the `PermissionChecker` dependency:

```python
from src.modules.auth.utils import PermissionChecker

router = APIRouter()

@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(PermissionChecker("users:read")),
    db: AsyncSession = Depends(get_db),
):
    # Only reached if user has "users:read" permission
    ...
```

### Flow

1. Request arrives at protected endpoint
2. `PermissionChecker("users:read")` dependency activates
3. It extracts the JWT, loads the user from DB
4. Loads the user's role and eagerly loads permissions
5. Checks if the required permission is in the user's permission set
6. If found: request proceeds. If not: returns `403 Forbidden`

### Example: Permission Checker Implementation

```python
class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    async def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        # Eagerly load role and permissions
        await current_user.awaitable_attrs.role
        for perm in current_user.role.permissions:
            if perm.name == self.required_permission:
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
```

---

## Adding New Permissions

### 1. Add the permission to the database

```python
# In a migration or seed script
from src.modules.auth.models import Permission

new_perm = Permission(name="documents:delete_all", description="Delete any document")
db.add(new_perm)
await db.commit()
```

### 2. Assign to a role

```python
admin_role = await db.execute(select(Role).where(Role.name == "admin"))
admin_role = admin_role.scalar_one()
admin_role.permissions.append(new_perm)
await db.commit()
```

### 3. Protect an endpoint

```python
@router.delete("/admin/documents/{document_id}")
async def admin_delete_document(
    current_user: User = Depends(PermissionChecker("documents:delete_all")),
):
    ...
```

---

## Migration-Seeded Defaults

The initial migration (`000000000004`) seeds default roles and permissions:

```python
# Permissions
permissions = [
    Permission(name="users:read", description="View all users"),
    Permission(name="prompts:read_all", description="View all prompts"),
    Permission(name="models:manage", description="Pull and delete models"),
]

# Roles
admin_role = Role(name="admin", description="Administrator with full access")
user_role = Role(name="user", description="Standard user")

# Assign all permissions to admin
admin_role.permissions = permissions
```

---

## Related

- [Architecture](../architecture.md)
- [API Reference](../api/reference.md)
- [Contributing](../development/contributing.md)
