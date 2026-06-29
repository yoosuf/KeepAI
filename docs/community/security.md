# Security Policy

---

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x | Active |

---

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please **do not** open a public issue.

Instead, report it privately via email:

**mayoosuf@gmail.com**

You should receive a response within **48 hours**. If not, please follow up.

### What to include

- Type of vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Any suggested fix (if known)

### What to expect

1. Acknowledgement of receipt within 48 hours
2. Initial assessment within 5 business days
3. Regular updates on progress
4. Credit in release notes (if desired)

---

## Security Best Practices

### Environment Variables

- **Never** commit `.env` files to version control
- Use strong `SECRET_KEY`: `openssl rand -hex 32`
- Rotate secrets regularly

### Docker

- The backend runs as a **non-root user** (`appuser`) inside containers
- Database port `5432` should not be exposed to the internet
- Use Docker networks to isolate services
- Regularly pull updated base images: `docker compose -f docker/docker-compose.yml pull`

### Authentication

- JWT tokens expire after 30 minutes by default
- Argon2id is used for password hashing (memory-hard, resistant to GPU attacks)
- Passwords are never logged or returned in responses
- Use HTTPS in production (reverse proxy with Caddy/Nginx)

### Database

- Network access to PostgreSQL should be restricted to the backend service only
- Use strong, unique passwords for database users
- Regular backups (configure via `pg_dump` or your cloud provider)

### RBAC

- The `admin` role should only be assigned to trusted users
- Review permissions regularly
- Disable public admin registration in production

### API Keys

- Keys are prefixed with `ka_` for easy identification
- Keys are hashed with SHA-512 before storage (plaintext is only shown once at creation)
- Rotate keys periodically
- Revoke compromised keys immediately

---

## Disclosure Policy

We follow **responsible disclosure**:

- Reporters disclose privately
- We fix and release within 90 days
- We publicly acknowledge the reporter after the fix is released

---

## Related

- [API Reference](../api/reference.md)
- [Deployment Guide](../guides/deployment.md)
