from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "intelliflow",
    broker_url=str(settings.get_celery_broker()),
    backend=str(settings.get_celery_backend()),
)

# Basic configuration for MVP
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

