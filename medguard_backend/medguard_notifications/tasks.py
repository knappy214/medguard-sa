"""
Celery tasks for MedGuard SA notification system.

This module provides background tasks for processing notifications
asynchronously using Celery.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction

# Celery imports
from celery import shared_task
from celery.utils.log import get_task_logger

# Post-office imports
from post_office import mail as po_mail
from post_office.models import Email, EmailTemplate

# Local imports
from .services import notification_service
from .models import Notification, UserNotification, UserNotificationPreferences

User = get_user_model()
logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification_task(
    self,
    user_id: int,
    subject: str,
    message: str,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
    scheduled_at: Optional[datetime] = None,
    priority: str = 'medium'
):
    """
    Send an email notification asynchronously.
    
    Args:
        user_id: ID of the user to send email to
        subject: Email subject
        message: Email message
        template_name: Optional template name
        template_context: Optional template context
        scheduled_at: When to send the email
        priority: Email priority
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Check user preferences
        prefs = UserNotificationPreferences.objects.get_or_create(user=user)[0]
        if not prefs.email_notifications_enabled:
            logger.info(f"Email notifications disabled for user {user_id}")
            return
        
        # Check quiet hours
        if prefs.is_in_quiet_hours and priority != 'critical':
            logger.info(f"Email suppressed due to quiet hours for user {user_id}")
            return
        
        context = template_context or {}
        context.update({
            'user': user,
            'subject': subject,
            'message': message,
            'site_name': settings.WAGTAIL_SITE_NAME,
        })
        
        if template_name:
            # Use template from post-office
            template = EmailTemplate.objects.get(name=template_name)
            po_mail.send(
                user.email,
                settings.DEFAULT_FROM_EMAIL,
                template=template,
                context=context,
                scheduled_time=scheduled_at,
                priority=priority,
            )
        else:
            # Send simple email
            po_mail.send(
                user.email,
                settings.DEFAULT_FROM_EMAIL,
                subject=subject,
                message=message,
                html_message=message,
                scheduled_time=scheduled_at,
                priority=priority,
            )
        
        logger.info(f"Email notification sent to user {user_id}")
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
    except EmailTemplate.DoesNotExist:
        logger.error(f"Email template '{template_name}' not found")
        # Retry without template
        self.retry(countdown=300)  # Retry in 5 minutes
    except Exception as exc:
        logger.error(f"Error sending email to user {user_id}: {str(exc)}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_bulk_email_notifications_task(
    self,
    user_ids: List[int],
    subject: str,
    message: str,
    template_name: Optional[str] = None,
    template_context: Optional[Dict[str, Any]] = None,
    scheduled_at: Optional[datetime] = None,
    priority: str = 'medium'
):
    """
    Send bulk email notifications asynchronously.
    
    Args:
        user_ids: List of user IDs to send emails to
        subject: Email subject
        message: Email message
        template_name: Optional template name
        template_context: Optional template context
        scheduled_at: When to send the emails
        priority: Email priority
    """
    try:
        users = User.objects.filter(id__in=user_ids)
        
        # Filter users by preferences
        users_with_prefs = []
        for user in users:
            prefs = UserNotificationPreferences.objects.get_or_create(user=user)[0]
            if (prefs.email_notifications_enabled and 
                (not prefs.is_in_quiet_hours or priority == 'critical')):
                users_with_prefs.append(user)
        
        if not users_with_prefs:
            logger.info("No users eligible for bulk email notification")
            return
        
        context = template_context or {}
        context.update({
            'subject': subject,
            'message': message,
            'site_name': settings.WAGTAIL_SITE_NAME,
        })
        
        if template_name:
            # Use template from post-office
            template = EmailTemplate.objects.get(name=template_name)
            for user in users_with_prefs:
                user_context = context.copy()
                user_context['user'] = user
                po_mail.send(
                    user.email,
                    settings.DEFAULT_FROM_EMAIL,
                    template=template,
                    context=user_context,
                    scheduled_time=scheduled_at,
                    priority=priority,
                )
        else:
            # Send simple emails
            for user in users_with_prefs:
                po_mail.send(
                    user.email,
                    settings.DEFAULT_FROM_EMAIL,
                    subject=subject,
                    message=message,
                    html_message=message,
                    scheduled_time=scheduled_at,
                    priority=priority,
                )
        
        logger.info(f"Bulk email notifications sent to {len(users_with_prefs)} users")
        
    except EmailTemplate.DoesNotExist:
        logger.error(f"Email template '{template_name}' not found")
        self.retry(countdown=300)  # Retry in 5 minutes
    except Exception as exc:
        logger.error(f"Error sending bulk emails: {str(exc)}")
        self.retry(exc=exc)


@shared_task
def send_daily_digest_notifications():
    """
    Send daily digest notifications to users.
    
    This task aggregates all notifications from the past day and sends
    them as a single digest email to users who have digest enabled.
    """
    try:
        # Get users with digest enabled
        users = User.objects.filter(
            notification_preferences__email_time_preference='morning'
        )
        
        yesterday = timezone.now() - timedelta(days=1)
        
        for user in users:
            try:
                # Get user's unread notifications from yesterday
                notifications = UserNotification.objects.filter(
                    user=user,
                    status='unread',
                    sent_at__gte=yesterday
                ).select_related('notification')
                
                if notifications.exists():
                    # Create digest content
                    digest_content = []
                    for user_notif in notifications:
                        digest_content.append({
                            'title': user_notif.notification.title,
                            'type': user_notif.notification.notification_type,
                            'priority': user_notif.notification.priority,
                            'sent_at': user_notif.sent_at,
                        })
                    
                    # Send digest email
                    context = {
                        'user': user,
                        'notifications': digest_content,
                        'count': len(digest_content),
                        'date': yesterday.strftime('%Y-%m-%d'),
                    }
                    
                    po_mail.send(
                        user.email,
                        settings.DEFAULT_FROM_EMAIL,
                        template='daily_digest',
                        context=context,
                        priority='low',
                    )
                    
                    # Mark notifications as read
                    notifications.update(status='read', read_at=timezone.now())
                    
                    logger.info(f"Daily digest sent to user {user.id} with {len(digest_content)} notifications")
                
            except Exception as e:
                logger.error(f"Error sending digest to user {user.id}: {str(e)}")
                continue
        
        logger.info("Daily digest notifications completed")
        
    except Exception as e:
        logger.error(f"Error in daily digest task: {str(e)}")


@shared_task
def send_weekly_digest_notifications():
    """
    Send weekly digest notifications to users.
    
    This task aggregates all notifications from the past week and sends
    them as a single digest email to users who have weekly digest enabled.
    """
    try:
        # Get users with weekly digest enabled
        users = User.objects.filter(
            notification_preferences__email_time_preference='custom'
        )
        
        week_ago = timezone.now() - timedelta(weeks=1)
        
        for user in users:
            try:
                # Get user's unread notifications from the past week
                notifications = UserNotification.objects.filter(
                    user=user,
                    status='unread',
                    sent_at__gte=week_ago
                ).select_related('notification')
                
                if notifications.exists():
                    # Create digest content
                    digest_content = []
                    for user_notif in notifications:
                        digest_content.append({
                            'title': user_notif.notification.title,
                            'type': user_notif.notification.notification_type,
                            'priority': user_notif.notification.priority,
                            'sent_at': user_notif.sent_at,
                        })
                    
                    # Send digest email
                    context = {
                        'user': user,
                        'notifications': digest_content,
                        'count': len(digest_content),
                        'week_start': week_ago.strftime('%Y-%m-%d'),
                        'week_end': timezone.now().strftime('%Y-%m-%d'),
                    }
                    
                    po_mail.send(
                        user.email,
                        settings.DEFAULT_FROM_EMAIL,
                        template='weekly_digest',
                        context=context,
                        priority='low',
                    )
                    
                    # Mark notifications as read
                    notifications.update(status='read', read_at=timezone.now())
                    
                    logger.info(f"Weekly digest sent to user {user.id} with {len(digest_content)} notifications")
                
            except Exception as e:
                logger.error(f"Error sending weekly digest to user {user.id}: {str(e)}")
                continue
        
        logger.info("Weekly digest notifications completed")
        
    except Exception as e:
        logger.error(f"Error in weekly digest task: {str(e)}")


@shared_task
def cleanup_old_notifications():
    """
    Clean up old notifications and email logs.
    
    This task removes notifications and email logs that are older than
    the configured retention period.
    """
    try:
        # Get retention period from settings
        retention_days = getattr(settings, 'NYT_NOTIFICATION_MAX_DAYS', 90)
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        
        # Clean up old user notifications
        deleted_user_notifications = UserNotification.objects.filter(
            sent_at__lt=cutoff_date
        ).delete()
        
        # Clean up old notifications (if no user notifications reference them)
        old_notifications = Notification.objects.filter(
            created_at__lt=cutoff_date
        )
        
        # Only delete notifications that have no user notifications
        for notification in old_notifications:
            if not notification.user_notifications.exists():
                notification.delete()
        
        # Clean up old email logs (using post-office cleanup command)
        from django.core.management import call_command
        call_command('cleanup_queues', verbosity=0)
        
        logger.info(f"Cleanup completed: deleted {deleted_user_notifications[0]} old user notifications")
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {str(e)}")


@shared_task
def process_scheduled_notifications():
    """
    Process scheduled notifications.
    
    This task checks for notifications that are scheduled to be sent
    and processes them.
    """
    try:
        now = timezone.now()
        
        # Get scheduled notifications that are due
        scheduled_notifications = Notification.objects.filter(
            scheduled_at__lte=now,
            status='draft',
            is_active=True
        )
        
        for notification in scheduled_notifications:
            try:
                # Update status to active
                notification.status = 'active'
                notification.save()
                
                # Send to target users
                for user in notification.target_users.all():
                    notification_service.send_notification(
                        user=user,
                        title=notification.title,
                        message=notification.content,
                        notification_type=notification.notification_type,
                        channels=['in_app', 'email'],
                        priority=notification.priority,
                        data={
                            'notification_id': notification.id,
                            'type': 'scheduled_notification'
                        }
                    )
                
                logger.info(f"Processed scheduled notification {notification.id}")
                
            except Exception as e:
                logger.error(f"Error processing scheduled notification {notification.id}: {str(e)}")
                continue
        
        logger.info(f"Processed {scheduled_notifications.count()} scheduled notifications")
        
    except Exception as e:
        logger.error(f"Error in scheduled notifications task: {str(e)}")


@shared_task
def send_medication_reminders():
    """
    Send medication reminders to users.
    
    This task checks for users who need medication reminders and sends
    them notifications.
    """
    try:
        # Get users with medication reminders enabled
        users = User.objects.filter(
            notification_preferences__medication_reminders_enabled=True
        )
        
        # TODO: Integrate with medication scheduling system
        # For now, this is a placeholder that would check medication schedules
        # and send reminders for medications due within the next hour
        
        logger.info("Medication reminders task completed")
        
    except Exception as e:
        logger.error(f"Error in medication reminders task: {str(e)}")


@shared_task
def send_stock_alerts():
    """
    Send stock alerts to staff members.
    
    This task checks medication stock levels and sends alerts when
    stock is low.
    """
    try:
        # TODO: Integrate with inventory management system
        # For now, this is a placeholder that would check stock levels
        # and send alerts to relevant staff members
        
        logger.info("Stock alerts task completed")
        
    except Exception as e:
        logger.error(f"Error in stock alerts task: {str(e)}")


@shared_task
def update_notification_statistics():
    """
    Update notification statistics and metrics.
    
    This task calculates and stores various notification statistics
    for monitoring and reporting purposes.
    """
    try:
        # Calculate daily statistics
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Count notifications by type
        notification_stats = {}
        for notification_type, _ in Notification.NotificationType.choices:
            count = Notification.objects.filter(
                notification_type=notification_type,
                created_at__date=yesterday
            ).count()
            notification_stats[notification_type] = count
        
        # Count user notifications by status
        user_notification_stats = {}
        for status, _ in UserNotification.Status.choices:
            count = UserNotification.objects.filter(
                status=status,
                sent_at__date=yesterday
            ).count()
            user_notification_stats[status] = count
        
        # Store statistics in cache for quick access
        stats = {
            'date': yesterday.isoformat(),
            'notifications': notification_stats,
            'user_notifications': user_notification_stats,
        }
        
        cache.set('notification_stats_daily', stats, timeout=86400)  # 24 hours
        
        logger.info(f"Updated notification statistics for {yesterday}")
        
    except Exception as e:
        logger.error(f"Error updating notification statistics: {str(e)}") 