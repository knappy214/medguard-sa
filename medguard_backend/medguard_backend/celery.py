"""
Celery configuration for MedGuard SA.

This module configures Celery for handling background tasks,
particularly for the notification system.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')

# Create the Celery app
app = Celery('medguard_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery settings
app.conf.update(
    # Task routing
    task_routes={
        'medguard_notifications.tasks.*': {'queue': 'notifications'},
        'medguard_notifications.tasks.send_email_notification_task': {'queue': 'email'},
        'medguard_notifications.tasks.send_bulk_email_notifications_task': {'queue': 'email'},
        'medguard_notifications.tasks.send_daily_digest_notifications': {'queue': 'digest'},
        'medguard_notifications.tasks.send_weekly_digest_notifications': {'queue': 'digest'},
        'medguard_notifications.tasks.cleanup_old_notifications': {'queue': 'maintenance'},
        'medguard_notifications.tasks.process_scheduled_notifications': {'queue': 'scheduled'},
        'medguard_notifications.tasks.send_medication_reminders': {'queue': 'reminders'},
        'medguard_notifications.tasks.send_stock_alerts': {'queue': 'alerts'},
        'medguard_notifications.tasks.update_notification_statistics': {'queue': 'maintenance'},
    },
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task execution settings
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': "mymaster",
        'visibility_timeout': 3600,
    },
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'send-daily-digest': {
            'task': 'medguard_notifications.tasks.send_daily_digest_notifications',
            'schedule': 86400.0,  # Daily at 8:00 AM
            'options': {'queue': 'digest'},
        },
        'send-weekly-digest': {
            'task': 'medguard_notifications.tasks.send_weekly_digest_notifications',
            'schedule': 604800.0,  # Weekly on Monday at 9:00 AM
            'options': {'queue': 'digest'},
        },
        'process-scheduled-notifications': {
            'task': 'medguard_notifications.tasks.process_scheduled_notifications',
            'schedule': 300.0,  # Every 5 minutes
            'options': {'queue': 'scheduled'},
        },
        'send-medication-reminders': {
            'task': 'medguard_notifications.tasks.send_medication_reminders',
            'schedule': 600.0,  # Every 10 minutes
            'options': {'queue': 'reminders'},
        },
        'send-stock-alerts': {
            'task': 'medguard_notifications.tasks.send_stock_alerts',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'alerts'},
        },
        'cleanup-old-notifications': {
            'task': 'medguard_notifications.tasks.cleanup_old_notifications',
            'schedule': 86400.0,  # Daily at 2:00 AM
            'options': {'queue': 'maintenance'},
        },
        'update-notification-statistics': {
            'task': 'medguard_notifications.tasks.update_notification_statistics',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'maintenance'},
        },
    },
    
    # Queue settings
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Error handling
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')


# Import tasks to ensure they are registered
from medguard_notifications import tasks  # noqa 