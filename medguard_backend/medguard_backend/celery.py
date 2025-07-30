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

# Configure Celery settings with optimized performance
app.conf.update(
    # Task routing for optimized performance with priority-based queues
    task_routes={
        # High priority notification tasks
        'medguard_notifications.tasks.send_email_notification_task': {'queue': 'email_high', 'priority': 9},
        'medguard_notifications.tasks.send_bulk_email_notifications_task': {'queue': 'email_bulk', 'priority': 7},
        'medguard_notifications.tasks.send_daily_digest_notifications': {'queue': 'email_digest', 'priority': 5},
        'medguard_notifications.tasks.send_weekly_digest_notifications': {'queue': 'email_digest', 'priority': 5},
        'medguard_notifications.tasks.send_medication_reminders': {'queue': 'reminders_high', 'priority': 9},
        'medguard_notifications.tasks.send_stock_alerts': {'queue': 'alerts_high', 'priority': 8},
        
        # Medium priority maintenance tasks
        'medguard_notifications.tasks.cleanup_old_notifications': {'queue': 'maintenance', 'priority': 3},
        'medguard_notifications.tasks.process_scheduled_notifications': {'queue': 'scheduled', 'priority': 6},
        'medguard_notifications.tasks.update_notification_statistics': {'queue': 'maintenance', 'priority': 4},
        
        # High priority medication tasks
        'medications.tasks.update_stock_analytics': {'queue': 'analytics', 'priority': 7},
        'medications.tasks.predict_stock_depletion': {'queue': 'analytics', 'priority': 8},
        'medications.tasks.analyze_usage_patterns': {'queue': 'analytics', 'priority': 6},
        'medications.tasks.generate_stock_visualizations': {'queue': 'visualization', 'priority': 5},
        'medications.tasks.refresh_stock_visualizations': {'queue': 'visualization', 'priority': 4},
        'medications.tasks.check_prescription_renewals': {'queue': 'renewals', 'priority': 8},
        'medications.tasks.integrate_with_pharmacy': {'queue': 'pharmacy', 'priority': 7},
        'medications.tasks.sync_pharmacy_integrations': {'queue': 'pharmacy', 'priority': 6},
        'medications.tasks.monitor_stock_levels': {'queue': 'monitoring', 'priority': 9},
        'medications.tasks.generate_stock_report': {'queue': 'reports', 'priority': 5},
        'medications.tasks.cleanup_old_transactions': {'queue': 'maintenance', 'priority': 2},
        
        # Image optimization tasks with different priorities
        'medications.tasks.optimize_medication_images': {'queue': 'image_processing', 'priority': 6},
        'medications.tasks.cleanup_old_medication_images': {'queue': 'maintenance', 'priority': 1},
        'medications.tasks.process_urgent_images': {'queue': 'image_processing', 'priority': 9},
        'medications.tasks.process_high_priority_images': {'queue': 'image_processing', 'priority': 8},
        'medications.tasks.process_standard_images': {'queue': 'image_processing', 'priority': 5},
        'medications.tasks.process_low_priority_images': {'queue': 'image_processing', 'priority': 3},
    },
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone=settings.TIME_ZONE,
    enable_utc=True,
    
    # Worker settings for optimal performance with multi-tier optimization
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    worker_concurrency=8,  # Increased for better throughput
    worker_pool='prefork',
    worker_autoscale=(4, 16),  # Min 4, max 16 workers for scalability
    worker_max_memory_per_child=300000,  # 300MB for image processing
    worker_direct=True,  # Direct task routing for better performance
    
    # Task execution settings
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': "mymaster",
        'visibility_timeout': 3600,
    },
    
    # Beat schedule for periodic tasks with optimized timing
    beat_schedule={
        # High priority tasks - frequent execution
        'send-medication-reminders': {
            'task': 'medguard_notifications.tasks.send_medication_reminders',
            'schedule': 300.0,  # Every 5 minutes
            'options': {'queue': 'reminders_high'},
        },
        'send-stock-alerts': {
            'task': 'medguard_notifications.tasks.send_stock_alerts',
            'schedule': 1800.0,  # Every 30 minutes
            'options': {'queue': 'alerts_high'},
        },
        'monitor-stock-levels': {
            'task': 'medications.tasks.monitor_stock_levels',
            'schedule': 900.0,  # Every 15 minutes
            'options': {'queue': 'monitoring'},
        },
        
        # Medium priority tasks - regular execution
        'process-scheduled-notifications': {
            'task': 'medguard_notifications.tasks.process_scheduled_notifications',
            'schedule': 300.0,  # Every 5 minutes
            'options': {'queue': 'scheduled'},
        },
        'update-stock-analytics': {
            'task': 'medications.tasks.update_stock_analytics',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'analytics'},
        },
        'check-prescription-renewals': {
            'task': 'medications.tasks.check_prescription_renewals',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'renewals'},
        },
        'sync-pharmacy-integrations': {
            'task': 'medications.tasks.sync_pharmacy_integrations',
            'schedule': 7200.0,  # Every 2 hours
            'options': {'queue': 'pharmacy'},
        },
        'generate-stock-visualizations': {
            'task': 'medications.tasks.generate_stock_visualizations',
            'schedule': 7200.0,  # Every 2 hours
            'options': {'queue': 'visualization'},
        },
        'optimize-medication-images': {
            'task': 'medications.tasks.optimize_medication_images',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'image_processing'},
        },
        
        # Low priority tasks - daily/weekly execution
        'send-daily-digest': {
            'task': 'medguard_notifications.tasks.send_daily_digest_notifications',
            'schedule': 86400.0,  # Daily at 8:00 AM
            'options': {'queue': 'email_digest'},
        },
        'send-weekly-digest': {
            'task': 'medguard_notifications.tasks.send_weekly_digest_notifications',
            'schedule': 604800.0,  # Weekly on Monday at 9:00 AM
            'options': {'queue': 'email_digest'},
        },
        'predict-stock-depletion': {
            'task': 'medications.tasks.predict_stock_depletion',
            'schedule': 86400.0,  # Daily at 2:00 AM
            'options': {'queue': 'analytics'},
        },
        'cleanup-old-notifications': {
            'task': 'medguard_notifications.tasks.cleanup_old_notifications',
            'schedule': 86400.0,  # Daily at 2:00 AM
            'options': {'queue': 'maintenance'},
        },
        'cleanup-old-transactions': {
            'task': 'medications.tasks.cleanup_old_transactions',
            'schedule': 604800.0,  # Weekly
            'options': {'queue': 'maintenance'},
        },
        'cleanup-old-medication-images': {
            'task': 'medications.tasks.cleanup_old_medication_images',
            'schedule': 604800.0,  # Weekly
            'options': {'queue': 'maintenance'},
        },
        'update-notification-statistics': {
            'task': 'medguard_notifications.tasks.update_notification_statistics',
            'schedule': 3600.0,  # Every hour
            'options': {'queue': 'maintenance'},
        },
    },
    
    # Queue settings with priorities
    task_default_queue='default',
    task_default_exchange='default',
    task_default_routing_key='default',
    
    # Queue definitions with priorities
    task_queues={
        'email_high': {'exchange': 'email_high', 'routing_key': 'email_high'},
        'email_bulk': {'exchange': 'email_bulk', 'routing_key': 'email_bulk'},
        'email_digest': {'exchange': 'email_digest', 'routing_key': 'email_digest'},
        'reminders_high': {'exchange': 'reminders_high', 'routing_key': 'reminders_high'},
        'alerts_high': {'exchange': 'alerts_high', 'routing_key': 'alerts_high'},
        'scheduled': {'exchange': 'scheduled', 'routing_key': 'scheduled'},
        'analytics': {'exchange': 'analytics', 'routing_key': 'analytics'},
        'visualization': {'exchange': 'visualization', 'routing_key': 'visualization'},
        'renewals': {'exchange': 'renewals', 'routing_key': 'renewals'},
        'pharmacy': {'exchange': 'pharmacy', 'routing_key': 'pharmacy'},
        'monitoring': {'exchange': 'monitoring', 'routing_key': 'monitoring'},
        'reports': {'exchange': 'reports', 'routing_key': 'reports'},
        'image_processing': {'exchange': 'image_processing', 'routing_key': 'image_processing'},
        'maintenance': {'exchange': 'maintenance', 'routing_key': 'maintenance'},
    },
    
    # Error handling and retry settings
    task_reject_on_worker_lost=True,
    task_acks_late=True,
    
    # Redis broker settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    
    # Monitoring and logging
    worker_send_task_events=True,
    task_send_sent_event=True,
    event_queue_expires=60,
    event_queue_ttl=5,
    
    # Performance optimizations
    task_compression='gzip',
    result_compression='gzip',
    
    # Security settings
    security_key=os.getenv('CELERY_SECURITY_KEY', ''),
    security_certificate=os.getenv('CELERY_SECURITY_CERTIFICATE', ''),
    security_cert_store=os.getenv('CELERY_SECURITY_CERT_STORE', ''),
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')


# Import tasks to ensure they are registered
from medguard_notifications import tasks  # noqa 