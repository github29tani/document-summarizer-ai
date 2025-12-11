from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "document_summarizer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_routes={
        'app.tasks.process_document_task': {'queue': 'document_processing'},
        'app.tasks.generate_summary_task': {'queue': 'ai_processing'},
        'app.tasks.generate_embeddings_task': {'queue': 'ai_processing'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)
