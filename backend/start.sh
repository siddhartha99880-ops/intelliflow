#!/bin/sh
# Start Celery worker in the background
celery -A app.workers.celery_app:celery worker --loglevel=INFO --concurrency=1 &

# Start uvicorn FastAPI server in the foreground
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
