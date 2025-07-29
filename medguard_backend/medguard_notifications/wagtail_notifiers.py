"""
Wagtail Notifier subclasses for MedGuard SA.

This module provides Wagtail Notifier implementations that integrate
with the modern notification system for various workflow events.
"""

import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.urls import reverse

# Wagtail imports
from wagtail.admin.mail import EmailNotificationMixin, Notifier
from wagtail.signals import page_published, task_submitted, task_approved, task_rejected

# Local imports
from .services import notification_service

User = get_user_model()
logger = logging.getLogger(__name__)


class MedicationPagePublishedNotifier(Notifier):
    """
    Notifier for when medication pages are published.
    
    Sends notifications to relevant staff members when medication
    information is updated and published.
    """
    
    notification = "medication_published"
    
    def get_recipient_users(self, instance, **kwargs):
        """Get users who should receive this notification."""
        # Get staff users who manage medications
        return User.objects.filter(
            is_staff=True,
            notification_preferences__medication_notifications_enabled=True
        )
    
    def send(self, recipient, context):
        """Send the notification."""
        try:
            page = context['page']
            
            # Send notification to staff
            notification_service.send_notification(
                user=recipient,
                title=_("Medication Information Updated"),
                message=_("Medication '{medication}' has been updated and published.").format(
                    medication=page.title
                ),
                notification_type='medication',
                channels=['in_app', 'email'],
                priority='medium',
                data={
                    'page_id': page.id,
                    'page_url': page.get_url(),
                    'updated_by': context.get('revision', {}).get('user', 'Unknown'),
                    'type': 'medication_published'
                },
                template_name='medication_published'
            )
            
        except Exception as e:
            logger.error(f"Error sending medication published notification: {str(e)}")


class WorkflowTaskSubmittedNotifier(Notifier):
    """
    Notifier for when content enters a workflow task.
    
    Notifies reviewers when content is submitted for review.
    """
    
    notification = "task_submitted"
    
    def get_recipient_users(self, instance, **kwargs):
        """Get users who should receive this notification."""
        task_state = kwargs.get('task_state')
        if not task_state:
            return []
        
        # Get users assigned to this task
        return task_state.task.get_users_for_task()
    
    def send(self, recipient, context):
        """Send the notification."""
        try:
            task_state = context['task_state']
            page = task_state.page_revision.as_page_object()
            
            notification_service.send_notification(
                user=recipient,
                title=_("Content Review Required"),
                message=_("Content '{title}' has been submitted for review.").format(
                    title=page.title
                ),
                notification_type='workflow',
                channels=['in_app', 'email'],
                priority='medium',
                data={
                    'page_id': page.id,
                    'task_name': task_state.task.name,
                    'submitted_by': task_state.page_revision.user.get_full_name() or task_state.page_revision.user.username,
                    'type': 'task_submitted'
                },
                template_name='workflow_task_submitted'
            )
            
        except Exception as e:
            logger.error(f"Error sending task submitted notification: {str(e)}")


class WorkflowTaskApprovedNotifier(Notifier):
    """
    Notifier for when a workflow task is approved.
    
    Notifies content creators when their content is approved.
    """
    
    notification = "task_approved"
    
    def get_recipient_users(self, instance, **kwargs):
        """Get users who should receive this notification."""
        task_state = kwargs.get('task_state')
        if not task_state:
            return []
        
        # Get the content creator
        creator = task_state.page_revision.user
        if creator:
            return [creator]
        return []
    
    def send(self, recipient, context):
        """Send the notification."""
        try:
            task_state = context['task_state']
            page = task_state.page_revision.as_page_object()
            
            notification_service.send_notification(
                user=recipient,
                title=_("Content Approved"),
                message=_("Your content '{title}' has been approved.").format(
                    title=page.title
                ),
                notification_type='workflow',
                channels=['in_app', 'email'],
                priority='low',
                data={
                    'page_id': page.id,
                    'task_name': task_state.task.name,
                    'approved_by': task_state.get_user().get_full_name() or task_state.get_user().username,
                    'type': 'task_approved'
                },
                template_name='workflow_task_approved'
            )
            
        except Exception as e:
            logger.error(f"Error sending task approved notification: {str(e)}")


class WorkflowTaskRejectedNotifier(Notifier):
    """
    Notifier for when a workflow task is rejected.
    
    Notifies content creators when their content is rejected with comments.
    """
    
    notification = "task_rejected"
    
    def get_recipient_users(self, instance, **kwargs):
        """Get users who should receive this notification."""
        task_state = kwargs.get('task_state')
        if not task_state:
            return []
        
        # Get the content creator
        creator = task_state.page_revision.user
        if creator:
            return [creator]
        return []
    
    def send(self, recipient, context):
        """Send the notification."""
        try:
            task_state = context['task_state']
            page = task_state.page_revision.as_page_object()
            
            # Get rejection comments
            comments = task_state.get_comment() or _("No comments provided")
            
            notification_service.send_notification(
                user=recipient,
                title=_("Content Requires Revision"),
                message=_("Your content '{title}' requires revision. Comments: {comments}").format(
                    title=page.title,
                    comments=comments
                ),
                notification_type='workflow',
                channels=['in_app', 'email'],
                priority='high',
                data={
                    'page_id': page.id,
                    'task_name': task_state.task.name,
                    'rejected_by': task_state.get_user().get_full_name() or task_state.get_user().username,
                    'comments': comments,
                    'type': 'task_rejected'
                },
                template_name='workflow_task_rejected'
            )
            
        except Exception as e:
            logger.error(f"Error sending task rejected notification: {str(e)}")


class StockAlertNotifier(Notifier):
    """
    Notifier for stock alerts.
    
    Sends notifications when medication stock levels are low.
    """
    
    notification = "stock_alert"
    
    def get_recipient_users(self, instance, **kwargs):
        """Get users who should receive stock alerts."""
        return User.objects.filter(
            is_staff=True,
            notification_preferences__stock_alerts_enabled=True
        )
    
    def send(self, recipient, context):
        """Send the stock alert notification."""
        try:
            medication_name = context.get('medication_name', 'Unknown Medication')
            current_stock = context.get('current_stock', 0)
            threshold = context.get('threshold', 0)
            
            notification_service.send_stock_alert(
                user=recipient,
                medication_name=medication_name,
                current_stock=current_stock,
                threshold=threshold,
                channels=['in_app', 'email']
            )
            
        except Exception as e:
            logger.error(f"Error sending stock alert notification: {str(e)}")


class SystemMaintenanceNotifier(Notifier):
    """
    Notifier for system maintenance events.
    
    Sends notifications about scheduled maintenance and system updates.
    """
    
    notification = "system_maintenance"
    
    def get_recipient_users(self, instance, **kwargs):
        """Get users who should receive system maintenance notifications."""
        return User.objects.filter(
            notification_preferences__system_notifications_enabled=True
        )
    
    def send(self, recipient, context):
        """Send the system maintenance notification."""
        try:
            maintenance_type = context.get('maintenance_type', 'System Maintenance')
            start_time = context.get('start_time')
            end_time = context.get('end_time')
            description = context.get('description', '')
            
            if start_time and end_time:
                notification_service.send_notification(
                    user=recipient,
                    title=_("System Maintenance Scheduled"),
                    message=_("Scheduled maintenance: {type} from {start} to {end}").format(
                        type=maintenance_type,
                        start=start_time.strftime("%Y-%m-%d %H:%M"),
                        end=end_time.strftime("%Y-%m-%d %H:%M")
                    ),
                    notification_type='maintenance',
                    channels=['in_app', 'email'],
                    priority='medium',
                    data={
                        'maintenance_type': maintenance_type,
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat(),
                        'description': description,
                        'type': 'system_maintenance'
                    },
                    template_name='system_maintenance'
                )
            
        except Exception as e:
            logger.error(f"Error sending system maintenance notification: {str(e)}")


class SecurityAlertNotifier(Notifier):
    """
    Notifier for security alerts.
    
    Sends high-priority notifications for security-related events.
    """
    
    notification = "security_alert"
    
    def get_recipient_users(self, instance, **kwargs):
        """Get users who should receive security alerts."""
        return User.objects.filter(
            is_staff=True,
            notification_preferences__security_alerts_enabled=True
        )
    
    def send(self, recipient, context):
        """Send the security alert notification."""
        try:
            alert_type = context.get('alert_type', 'Security Alert')
            description = context.get('description', '')
            severity = context.get('severity', 'medium')
            
            notification_service.send_notification(
                user=recipient,
                title=_("Security Alert: {type}").format(type=alert_type),
                message=description,
                notification_type='security',
                channels=['in_app', 'email', 'push'],
                priority='critical' if severity == 'high' else 'high',
                data={
                    'alert_type': alert_type,
                    'severity': severity,
                    'type': 'security_alert'
                },
                template_name='security_alert'
            )
            
        except Exception as e:
            logger.error(f"Error sending security alert notification: {str(e)}")


# Register the notifiers with Wagtail signals
def register_notifiers():
    """Register all notifiers with Wagtail signals."""
    try:
        # Page published notifications
        page_published.connect(
            MedicationPagePublishedNotifier(),
            dispatch_uid="medication_page_published_notifier"
        )
        
        # Workflow notifications
        task_submitted.connect(
            WorkflowTaskSubmittedNotifier(),
            dispatch_uid="workflow_task_submitted_notifier"
        )
        
        task_approved.connect(
            WorkflowTaskApprovedNotifier(),
            dispatch_uid="workflow_task_approved_notifier"
        )
        
        task_rejected.connect(
            WorkflowTaskRejectedNotifier(),
            dispatch_uid="workflow_task_rejected_notifier"
        )
        
        logger.info("Wagtail notifiers registered successfully")
        
    except Exception as e:
        logger.error(f"Error registering Wagtail notifiers: {str(e)}")


# Auto-register notifiers when the module is imported
register_notifiers() 