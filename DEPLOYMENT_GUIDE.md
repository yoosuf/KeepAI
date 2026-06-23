# Deployment Guide

This guide covers deploying KeepAI to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [Production Hardening](#production-hardening)
- [Reverse Proxy Setup](#reverse-proxy-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Upgrading](#upgrading)

---

## Prerequisites

- **Server** with at least:
  - 4GB RAM (8GB+ recommended for LLM inference)
  - 20GB free disk space (for Docker images + LLM models)
  - CPU with AVX2 support (most modern x86_64 CPUs)
  - Optional: NVIDIA GPU with 8GB+ VRAM for GPU-accelerated inference
- **Docker & Docker Compose** (recommended)
- **Domain name** (optional, for HTTPS)
- **Nginx or Caddy** (optional, for reverse proxy)

---

## Environment Configuration

### Required Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Configure for production:

```ini
# Database
POSTGRES_USER=app_user
POSTGRES_PASSWORD=<generate-a-strong-password>
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_DB=app_production

# Auth — GENERATE A STRONG SECRET KEY
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3
```

### Generate a secure secret key

```bash
openssl rand -hex 32
# Example output: a7c3b1f9e8d2a4b6c0e1f3d5a7b9c0e2f4d6a8b0c2e4f6a8b0c2e4f6a8b0c2
```

---

## Docker Deployment

### Single Server

```bash
# Clone the repository
git clone https://github.com/yoosuf/fastapi-ollama-backend.git
cd fastapi-ollama-backend

# Configure environment
cp .env.example .env
# Edit .env with production values (see above)

# Deploy
docker compose up --build -d

# Pull the LLM model
docker compose exec ollama ollama pull llama3

# Verify
curl http://localhost:8000/health
```

### With GPU Acceleration

To use NVIDIA GPUs with Ollama inside Docker:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
2. Update `docker-compose.yml` for the `ollama` service:

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

### Docker Compose Production Profile

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "127.0.0.1:8000:8000"  # Only expose to localhost
    environment:
      - POSTGRES_SERVER=db
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - OLLAMA_BASE_URL=http://ollama:11434
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - ollama
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # No port exposure to external

  ollama:
    image: ollama/ollama:latest
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama

volumes:
  postgres_data:
  ollama_data:
```

Run with:

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## Manual Deployment (Without Docker)

### 1. PostgreSQL

```bash
# Install PostgreSQL 15
sudo apt-get install postgresql-15

# Create database and user
sudo -u postgres psql
CREATE USER app_user WITH PASSWORD 'strong_password';
CREATE DATABASE app_production OWNER app_user;
\q
```

### 2. Application Setup

```bash
# Clone and install
git clone https://github.com/yoosuf/fastapi-ollama-backend.git
cd fastapi-ollama-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with production values

# Run migrations
alembic upgrade head

# Run with Gunicorn + Uvicorn
gunicorn src.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile -
```

### 3. Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3

# Run as a service
ollama serve
```

---

## Production Hardening

### 1. Disable Public Admin Registration

In the auth router, remove or gate the admin registration endpoint behind an environment variable:

```python
# In src/modules/auth/router.py
if settings.ADMIN_REGISTRATION_DISABLED and role_name == "admin":
    raise HTTPException(status_code=403, detail="Admin registration is disabled")
```

Add to `config.py`:

```python
ADMIN_REGISTRATION_DISABLED: bool = True
```

### 2. CORS Configuration

Restrict CORS in `src/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Not ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 3. HTTPS via Reverse Proxy

**Caddy** (simplest — auto TLS):

```caddyfile
api.yourdomain.com {
    reverse_proxy localhost:8000
}
```

**Nginx**:

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Firewall

```bash
# Allow only SSH, HTTP, and HTTPS
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 5. Resource Limits

Docker Compose resource limits:

```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G

ollama:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
```

---

## Reverse Proxy Setup

### Caddy (Recommended — Auto HTTPS)

Install Caddy, create `Caddyfile`:

```caddyfile
api.yourdomain.com {
    reverse_proxy localhost:8000
    log {
        output file /var/log/caddy/api.log
    }
}
```

```bash
caddy run
```

### Nginx

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_send_timeout 120s;
    }
}
```

---

## Monitoring & Logging

### Health Check Endpoint

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### Application Logs

Logs are output as JSON to stdout for easy ingestion by log aggregators:

```json
{"timestamp": "2026-01-15T10:30:00Z", "level": "INFO", "module": "src.modules.prompts.service", "message": "Prompt created", "user_id": 1, "prompt_id": 42}
```

### Docker Logs

```bash
# Follow all services
docker compose logs -f

# Specific service
docker compose logs -f backend

# Search logs
docker compose logs backend | grep "ERROR"
```

### Prometheus + Grafana (Optional)

Add this to `docker-compose.prod.yml`:

```yaml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
```

---

## Backup & Recovery

### Database Backup

```bash
# Automated daily backup
docker compose exec db pg_dump -U postgres app > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260115.sql | docker compose exec -T db psql -U postgres app
```

### Automated Backups with Cron

```bash
# Add to crontab (runs daily at 2 AM)
0 2 * * * cd /path/to/project && docker compose exec -T db pg_dump -U postgres app > backups/db_$(date +\%Y\%m\%d).sql && find backups/ -type f -mtime +30 -delete
```

---

## Upgrading

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose up --build -d

# Run any new migrations
docker compose exec backend alembic upgrade head
```

---

## Troubleshooting

For common issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or [FAQ.md](FAQ.md).

---

## Related

- [Architecture Overview](ARCHITECTURE.md)
- [Security Policy](SECURITY.md)
- [API Documentation](API_DOCUMENTATION.md)
