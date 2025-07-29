"""
Periodic task management for the notification system.

This module contains functions to create, update, and manage periodic tasks
for medication reminders, stock alerts, and other notifications.
"""

import json
from datetime import datetime, timedelta
from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule, CrontabSchedule
from notifications.tasks import (
    send_daily_medication_reminders,
    check_low_stock_alerts,
    check_expiring_medications,
    cleanup_old_notifications
)


def create_medication_reminder_tasks():
    """
    Create periodic tasks for medication reminders.
    
    This function sets up tasks that run at different times of day
    to send medication reminders to patients.
    """
    # Morning medication reminders (8:00 AM)
    morning_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='8',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=timezone.get_current_timezone()
    )
    
    PeriodicTask.objects.get_or_create(
        name='Morning Medication Reminders',
        task='notifications.send_daily_medication_reminders',
        crontab=morning_schedule,
        enabled=True,
        defaults={
            'kwargs': json.dumps({'reminder_type': 'morning'}),
            'description': 'Send morning medication reminders to all patients'
        }
    )
    
    # Afternoon medication reminders (2:00 PM)
    afternoon_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='14',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=timezone.get_current_timezone()
    )
    
    PeriodicTask.objects.get_or_create(
        name='Afternoon Medication Reminders',
        task='notifications.send_daily_medication_reminders',
        crontab=afternoon_schedule,
        enabled=True,
        defaults={
            'kwargs': json.dumps({'reminder_type': 'afternoon'}),
            'description': 'Send afternoon medication reminders to all patients'
        }
    )
    
    # Evening medication reminders (8:00 PM)
    evening_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='20',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=timezone.get_current_timezone()
    )
    
    PeriodicTask.objects.get_or_create(
        name='Evening Medication Reminders',
        task='notifications.send_daily_medication_reminders',
        crontab=evening_schedule,
        enabled=True,
        defaults={
            'kwargs': json.dumps({'reminder_type': 'evening'}),
            'description': 'Send evening medication reminders to all patients'
        }
    )


def create_stock_alert_tasks():
    """
    Create periodic tasks for stock alerts.
    
    This function sets up tasks to check for low stock and expiring medications.
    """
    # Check low stock alerts (every 6 hours)
    low_stock_schedule, _ = IntervalSchedule.objects.get_or_create(
        every=6,
        period=IntervalSchedule.HOURS
    )
    
    PeriodicTask.objects.get_or_create(
        name='Check Low Stock Alerts',
        task='notifications.check_low_stock_alerts',
        interval=low_stock_schedule,
        enabled=True,
        defaults={
            'description': 'Check for medications with low stock and create alerts'
        }
    )
    
    # Check expiring medications (daily at 9:00 AM)
    expiring_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='9',
        day_of_week='*',
        day_of_month='*',
        month_of_year='*',
        timezone=timezone.get_current_timezone()
    )
    
    PeriodicTask.objects.get_or_create(
        name='Check Expiring Medications',
        task='notifications.check_expiring_medications',
        crontab=expiring_schedule,
        enabled=True,
        defaults={
            'description': 'Check for medications expiring within 5 days'
        }
    )


def create_cleanup_tasks():
    """
    Create periodic tasks for cleanup operations.
    
    This function sets up tasks to clean up old notifications and logs.
    """
    # Cleanup old notifications (weekly on Sunday at 2:00 AM)
    cleanup_schedule, _ = CrontabSchedule.objects.get_or_create(
        minute='0',
        hour='2',
        day_of_week='0',  # Sunday
        day_of_month='*',
        month_of_year='*',
        timezone=timezone.get_current_timezone()
    )
    
    PeriodicTask.objects.get_or_create(
        name='Cleanup Old Notifications',
        task='notifications.cleanup_old_notifications',
        crontab=cleanup_schedule,
        enabled=True,
        defaults={
            'kwargs': json.dumps({'days_old': 90}),
            'description': 'Clean up notifications older than 90 days'
        }
    )


def create_all_periodic_tasks():
    """
    Create all periodic tasks for the notification system.
    
    This function should be called during system setup or migration.
    """
    create_medication_reminder_tasks()
    create_stock_alert_tasks()
    create_cleanup_tasks()
    
    print("All periodic tasks created successfully!")


def update_task_schedules():
    """
    Update existing task schedules if needed.
    
    This function can be used to modify existing periodic tasks.
    """
    # Example: Update medication reminder times if needed
    morning_task = PeriodicTask.objects.filter(name='Morning Medication Reminders').first()
    if morning_task:
        # Update to 7:30 AM instead of 8:00 AM
        new_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute='30',
            hour='7',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*',
            timezone=timezone.get_current_timezone()
        )
        morning_task.crontab = new_schedule
        morning_task.save()


def disable_task(task_name: str):
    """
    Disable a specific periodic task.
    
    Args:
        task_name: Name of the task to disable
    """
    try:
        task = PeriodicTask.objects.get(name=task_name)
        task.enabled = False
        task.save()
        print(f"Task '{task_name}' disabled successfully!")
    except PeriodicTask.DoesNotExist:
        print(f"Task '{task_name}' not found!")


def enable_task(task_name: str):
    """
    Enable a specific periodic task.
    
    Args:
        task_name: Name of the task to enable
    """
    try:
        task = PeriodicTask.objects.get(name=task_name)
        task.enabled = True
        task.save()
        print(f"Task '{task_name}' enabled successfully!")
    except PeriodicTask.DoesNotExist:
        print(f"Task '{task_name}' not found!")


def list_all_tasks():
    """
    List all periodic tasks and their status.
    
    Returns:
        List of task information dictionaries
    """
    tasks = []
    for task in PeriodicTask.objects.all():
        task_info = {
            'name': task.name,
            'task': task.task,
            'enabled': task.enabled,
            'description': task.description,
            'last_run': task.last_run_at,
            'total_run_count': task.total_run_count,
        }
        
        if task.crontab:
            task_info['schedule_type'] = 'crontab'
            task_info['schedule'] = f"{task.crontab.minute} {task.crontab.hour} {task.crontab.day_of_week} {task.crontab.day_of_month} {task.crontab.month_of_year}"
        elif task.interval:
            task_info['schedule_type'] = 'interval'
            task_info['schedule'] = f"Every {task.interval.every} {task.interval.period}"
        else:
            task_info['schedule_type'] = 'unknown'
            task_info['schedule'] = 'Unknown'
        
        tasks.append(task_info)
    
    return tasks


def reset_task_counters():
    """
    Reset the run counters for all periodic tasks.
    
    This is useful for testing or when you want to start fresh.
    """
    PeriodicTask.objects.all().update(
        last_run_at=None,
        total_run_count=0
    )
    print("All task counters reset successfully!")


def delete_task(task_name: str):
    """
    Delete a specific periodic task.
    
    Args:
        task_name: Name of the task to delete
    """
    try:
        task = PeriodicTask.objects.get(name=task_name)
        task.delete()
        print(f"Task '{task_name}' deleted successfully!")
    except PeriodicTask.DoesNotExist:
        print(f"Task '{task_name}' not found!")


def create_custom_medication_reminder(user_id: int, schedule_id: int, reminder_time: datetime):
    """
    Create a custom one-time medication reminder for a specific user.
    
    Args:
        user_id: ID of the user to send reminder to
        schedule_id: ID of the medication schedule
        reminder_time: When to send the reminder
    """
    # Create a one-time task using Celery's apply_async
    from notifications.tasks import send_medication_reminder
    
    # Schedule the task to run at the specified time
    eta = timezone.localtime(reminder_time)
    send_medication_reminder.apply_async(
        args=[schedule_id],
        eta=eta,
        kwargs={'user_id': user_id}
    )
    
    print(f"Custom medication reminder scheduled for {eta}")


def create_bulk_medication_reminders(schedule_ids: list, reminder_time: datetime):
    """
    Create bulk medication reminders for multiple schedules.
    
    Args:
        schedule_ids: List of medication schedule IDs
        reminder_time: When to send the reminders
    """
    from notifications.tasks import send_medication_reminder
    
    eta = timezone.localtime(reminder_time)
    
    for schedule_id in schedule_ids:
        send_medication_reminder.apply_async(
            args=[schedule_id],
            eta=eta
        )
    
    print(f"Bulk medication reminders scheduled for {len(schedule_ids)} schedules at {eta}") 