from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "arjuna_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.tasks']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Jakarta',
    enable_utc=True,
    task_routes={
        'app.tasks.tasks.send_notification': {'queue': 'notifications'},
        'app.tasks.tasks.generate_report': {'queue': 'reports'},
    }
)
