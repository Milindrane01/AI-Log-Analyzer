"""Celery application. Run: celery -A app.workers.celery_app worker --loglevel=INFO"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery("loganalyzer", broker=settings.redis_url)
celery_app.conf.update(
    task_acks_late=True,  # ack AFTER completion: worker crash → task redelivered
    worker_prefetch_multiplier=1,  # long tasks: don't hoard work in one worker
    task_default_queue="analysis",
    broker_connection_retry_on_startup=True,
)
