#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

if [ "${DEV_MODE}" = "true" ]; then
  echo "Starting development server (single worker, hot reload)..."
  exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Starting production server (gunicorn + uvicorn workers)..."
  exec gunicorn -c gunicorn.conf.py src.main:app
fi
