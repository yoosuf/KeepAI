# Deployment Guide

This guide covers deploying KeepAI to production environments.

---

## Prerequisites

- **Server** with at least:
  - 4 GB RAM (8 GB+ recommended for LLM inference)
  - 20 GB free disk space (Docker images + LLM model files)
  - CPU with AVX2 support (most modern x86_64 CPUs)
  - Optional: NVIDIA GPU with 8 GB+ VRAM for GPU-accelerated inference
- **Docker & Docker Compose** v2+ (recommended path)
- **Domain name** (optional, for HTTPS)
- **Nginx or Caddy** (optional, for reverse proxy)

---

## Environment Configuration

Create a `.env` file from the example:

```bash
cp backend/.env.example backend/.env
```

Minimum production changes:

```ini
# Use a strong, randomly generated secret
SECRET_KEY=$(openssl rand -hex 32)

# Change default database credentials
POSTGRES_USER=app_user
POSTGRES_PASSWORD=<strong-unique-password>
POSTGRES_DB=app_production

# Restrict CORS to your actual frontend
CORS_ORIGINS=["https://yourapp.com"]
```

### Generate a secure secret key

```bash
openssl rand -hex 32
# Example: a7c3b1f9e8d2a4b6c0e1f3d5a7b9c0e2f4d6a8b0c2e4f6a8b0c2e4f6a8b0c2
```

---

## Docker Deployment

### Single Server

```bash
git clone https://github.com/yoosuf/KeepAI.git
cd KeepAI

cp backend/.env.example backend/.env
# Edit backend/.env with production values

docker compose -f docker/docker-compose.yml up --build -d

# Pull the LLM model once
docker compose -f docker/docker-compose.yml exec ollama ollama pull llama3

# Verify
curl http://localhost:8000/health/ready
```

### With GPU Acceleration (NVIDIA)

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
2. Modify the `ollama` service in `docker/docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama:latest
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

### Production Compose File

Create `docker/docker-compose.prod.yml`:

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: docker/backend/Dockerfile
    ports:
      - "127.0.0.1:8000:8000"
    env_file: backend/.env
    restart: unless-stopped
    depends_on:
      - db
      - ollama

  db:
    image: postgres:15-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data

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
docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

---

## Manual Deployment (Without Docker)

### 1. PostgreSQL

```bash
sudo apt-get install postgresql-15

sudo -u postgres psql <<EOF
CREATE USER app_user WITH PASSWORD 'strong_password';
CREATE DATABASE app_production OWNER app_user;
EOF
```

### 2. Application

```bash
git clone https://github.com/yoosuf/KeepAI.git
cd KeepAI
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

cp backend/.env.example backend/.env
# Edit backend/.env

alembic -c backend/alembic.ini upgrade head
```

### 3. Gunicorn + Uvicorn

```bash
cd backend
gunicorn src.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --access-logfile -
```

Or use the included `gunicorn.conf.py`:

```bash
cd backend
gunicorn src.main:app -c gunicorn.conf.py
```

### 4. Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3
ollama serve
```

### 5. Systemd Service

```ini
# /etc/systemd/system/keepai.service
[Unit]
Description=KeepAI API
After=network.target

[Service]
WorkingDirectory=/opt/keepai/backend
ExecStart=/opt/keepai/.venv/bin/gunicorn src.main:app -c gunicorn.conf.py
Restart=always
User=appuser
EnvironmentFile=/opt/keepai/backend/.env

[Install]
WantedBy=multi-user.target
```

---

## Production Hardening

### 1. Disable Public Admin Registration

In `src/modules/auth/router.py`, gate admin registration:

```python
if settings.ADMIN_REGISTRATION_DISABLED and user_in.role == "admin":
    raise HTTPException(403, "Admin registration is disabled")
```

Add to `src/core/config.py`:
```python
ADMIN_REGISTRATION_DISABLED: bool = True
```

### 2. CORS Restriction

```ini
CORS_ORIGINS=["https://yourapp.com"]
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

### 4. Firewall

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 5. Docker Resource Limits

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

## Monitoring & Logging

### Health Checks

```bash
# Liveness
curl http://localhost:8000/health/live

# Readiness (pings DB + Ollama)
curl http://localhost:8000/health/ready
```

### Application Logs

Logs are structured JSON to stdout:

```json
{"timestamp": "2026-01-15T10:30:00Z", "level": "INFO", "message": "Prompt created", "user_id": 1}
```

### Docker Logs

```bash
docker compose -f docker/docker-compose.yml logs -f backend
docker compose -f docker/docker-compose.yml logs backend | grep "ERROR"
```

### Prometheus + Grafana (Optional)

Add to `docker/docker-compose.yml`:

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
# Manual backup
docker compose -f docker/docker-compose.yml exec db pg_dump -U postgres app > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20260115.sql | docker compose -f docker/docker-compose.yml exec -T db psql -U postgres app
```

### Automated Daily Backup (cron)

```bash
# crontab -e
0 2 * * * cd /path/to/keepai && docker compose -f docker/docker-compose.yml exec -T db pg_dump -U postgres app > backups/db_$(date +\%Y\%m\%d).sql && find backups/ -type f -mtime +30 -delete
```

---

## Upgrading

```bash
git pull origin main
docker compose -f docker/docker-compose.yml up --build -d
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
```

---

## Related

- [Configuration Reference](configuration.md)
- [Troubleshooting](../community/troubleshooting.md)
- [Security Policy](../community/security.md)
