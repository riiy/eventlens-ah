"""Celery application factory for EventLens AH."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "eventlens",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_BROKER_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
)
