"""
Celery app instance.

Why background jobs at all: Gmail sync + running 4 LLM calls per email
cannot happen inside an HTTP request/response cycle without the user
staring at a spinner for 10+ seconds. Sync is triggered by an API call but
executed async by a worker; the frontend polls or (later) uses websockets
for progress.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "inboxiq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.sync_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
