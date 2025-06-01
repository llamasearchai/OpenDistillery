"""
OpenDistillery Celery Application
Handles background tasks and distributed processing.
"""

import os
from celery import Celery
from kombu import Queue, Exchange
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

# Create Celery app
celery_app = Celery('opendistillery')

# Configuration
celery_app.conf.update(
    # Broker settings
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/1'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
    
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Task routing
    task_routes={
        'opendistillery.tasks.ai_processing.*': {'queue': 'ai_processing'},
        'opendistillery.tasks.data_processing.*': {'queue': 'data_processing'},
        'opendistillery.tasks.notifications.*': {'queue': 'notifications'},
    },
    
    # Queue configuration
    task_default_queue='default',
    task_queues=(
        Queue('default', Exchange('default'), routing_key='default'),
        Queue('ai_processing', Exchange('ai_processing'), routing_key='ai_processing'),
        Queue('data_processing', Exchange('data_processing'), routing_key='data_processing'),
        Queue('notifications', Exchange('notifications'), routing_key='notifications'),
        Queue('priority', Exchange('priority'), routing_key='priority'),
    ),
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Task discovery
celery_app.autodiscover_tasks([
    'src.workers.tasks.ai_tasks',
    'src.workers.tasks.data_tasks',
    'src.workers.tasks.notification_tasks',
])

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing"""
    logger.info(f'Request: {self.request!r}')
    return f'Debug task executed: {self.request.id}'

if __name__ == '__main__':
    celery_app.start() 