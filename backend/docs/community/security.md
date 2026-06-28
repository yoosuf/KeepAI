# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x | Active |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report privately by email: **mayoosuf@gmail.com**

### What to include

- Type of vulnerability (e.g., injection, broken auth, misconfiguration)
- Steps to reproduce
- Affected versions
- Potential impact
- Suggested fix (if known)

### What to expect

1. Acknowledgment within 48 hours
2. Initial assessment within 5 business days
3. Regular progress updates
4. Credit in release notes (if desired)

We follow **responsible disclosure**: fix and release within 90 days, then publicly acknowledge the reporter.

---

## Security Architecture

### Authentication

- Passwords hashed with **Argon2id** (memory-hard, recommended by OWASP)
- JWT tokens signed with HS256, expire after 30 minutes (configurable)
- Tokens never returned in error responses or logs
- OAuth2 password flow used for login (standard form data)

### Authorization

- Database-driven RBAC — roles and permissions in PostgreSQL
- `PermissionChecker` dependency enforces access on every protected route
- Users cannot access each other's prompts (scoped queries by `user_id`)
- Admin role is the only role with cross-user data access

### Data Isolation

- All LLM inference is **local** — no data sent to external services (with default Ollama setup)
- Prompts and responses stored in your PostgreSQL instance only
- No telemetry or analytics calls in the application

---

## Deployment Best Practices

### Secret Key

Never use the default `SECRET_KEY=changethis` in production. Generate a secure one:

```bash
openssl rand -hex 32
```

### Database

- Restrict PostgreSQL access to the backend service only (Docker network isolation handles this by default)
- Use strong, unique database credentials
- Do not expose port 5432 externally
- Run regular backups

### Docker

- Backend container runs as non-root user `appuser`
- Database port is not mapped to the host in the default compose file
- Keep base images updated: `docker compose pull && docker compose up --build -d`

### Network

- Run behind HTTPS — use Caddy (auto TLS) or Nginx + Let's Encrypt
- Restrict CORS to your actual frontend origin in production
- Use a firewall: allow only ports 80, 443, and SSH

### CORS

```ini
# .env — restrict in production
CORS_ORIGINS=["https://yourapp.com"]
```

### Admin Registration

By default, anyone can register as admin. Disable this in production:

```python
# src/modules/auth/router.py
if settings.ADMIN_REGISTRATION_DISABLED and user_in.role == "admin":
    raise HTTPException(403, "Admin registration is disabled")
```

### Rate Limiting

LLM endpoints are rate-limited by default (20/minute per user). For multi-instance deployments, configure Redis as the rate-limit backend so limits are shared across workers.

---

## Known Limitations

- **No password reset** — there is no built-in password recovery flow. Users must contact an admin to reset their account.
- **No token revocation** — JWTs are stateless; there is no blacklist. Tokens remain valid until expiry. For immediate revocation, reduce `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **Permission cache** — role/permission changes take up to 5 minutes to propagate (per-process cache TTL).
- **Admin registration** — publicly accessible by default; must be disabled manually for production.

---

## Related

- [Deployment Guide — Production Hardening](../guides/deployment.md#production-hardening)
- [RBAC Guide](../guides/rbac.md)
- [API Reference](../api/reference.md)
