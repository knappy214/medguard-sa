"""
Modern notification services for MedGuard SA.

This module provides a unified interface for sending notifications across
multiple channels using Django 5 and Wagtail 7 compatible libraries.
"""

import logging
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.urls import reverse

# Modern notification libraries
from post_office import mail as po_mail
from post_office.models import Email, EmailTemplate
from push_notifications.models import APNSDevice, GCMDevice
# Note: send_user_notification may not be available in all versions
# We'll implement our own web push functionality

# Local imports
from .models import (
    Notification, UserNotification, NotificationTemplate,
    UserNotificationPreferences
)

User = get_user_model()
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Unified notification service for MedGuard SA.
    
    Provides methods to send notifications across multiple channels:
    - In-app notifications (django-nyt)
    - Email notifications (django-post-office)
    - Push notifications (django-push-notifications)
    - SMS notifications (via external service)
    """
    
    def __init__(self):
        self.rate_limit_cache = cache
        self.template_cache = {}
    
    def send_notification(
        self,
        user: User,
        title: str,
        message: str,
        notification_type: str = 'general',
        channels: List[str] = None,
        priority: str = 'medium',
        data: Dict[str, Any] = None,
        scheduled_at: Optional[datetime] = None,
        template_name: Optional[str] = None,
        template_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send a notification to a user across specified channels.
        
        Args:
            user: Target user
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            channels: List of channels to use ('in_app', 'email', 'push', 'sms')
            priority: Notification priority
            data: Additional data for the notification
            scheduled_at: When to send the notification
            template_name: Template to use for rendering
            template_context: Context data for template rendering
            
        Returns:
            Dict with success status for each channel
        """
        if channels is None:
            channels = ['in_app', 'email']
        
        if data is None:
            data = {}
        
        # Check user preferences and rate limits
        user_prefs = self._get_user_preferences(user)
        if not user_prefs:
            logger.warning(f"No notification preferences found for user {user.id}")
            return {}
        
        # Filter channels based on user preferences
        channels = self._filter_channels_by_preferences(channels, user_prefs)
        
        results = {}
        
        try:
            with transaction.atomic():
                # Create base notification record
                notification = self._create_notification_record(
                    user, title, message, notification_type, priority, data
                )
                
                # Send to each channel
                for channel in channels:
                    if self._check_rate_limit(user, channel):
                        success = self._send_to_channel(
                            channel, user, notification, title, message,
                            template_name, template_context, scheduled_at
                        )
                        results[channel] = success
                    else:
                        logger.warning(f"Rate limit exceeded for user {user.id} on channel {channel}")
                        results[channel] = False
                
                # Update notification record with results
                self._update_notification_results(notification, results)
                
        except Exception as e:
            logger.error(f"Error sending notification to user {user.id}: {str(e)}")
            results = {channel: False for channel in channels}
        
        return results
    
    def send_bulk_notifications(
        self,
        users: List[User],
        title: str,
        message: str,
        notification_type: str = 'general',
        channels: List[str] = None,
        priority: str = 'medium',
        data: Dict[str, Any] = None,
        scheduled_at: Optional[datetime] = None,
        template_name: Optional[str] = None,
        template_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send notifications to multiple users efficiently.
        
        Args:
            users: List of target users
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            channels: List of channels to use
            priority: Notification priority
            data: Additional data for the notification
            scheduled_at: When to send the notification
            template_name: Template to use for rendering
            template_context: Context data for template rendering
            
        Returns:
            Dict with results for each user and channel
        """
        if channels is None:
            channels = ['in_app', 'email']
        
        results = {}
        
        # Group users by preferences for efficient sending
        user_groups = self._group_users_by_preferences(users, channels)
        
        for group_key, group_users in user_groups.items():
            group_channels = group_key.split(',')
            
            # Send bulk notifications for this group
            group_results = self._send_bulk_to_group(
                group_users, title, message, notification_type,
                group_channels, priority, data, scheduled_at,
                template_name, template_context
            )
            
            results.update(group_results)
        
        return results
    
    def send_medication_reminder(
        self,
        user: User,
        medication_name: str,
        dosage: str,
        time: str,
        channels: List[str] = None,
    ) -> Dict[str, bool]:
        """
        Send a medication reminder notification.
        
        Args:
            user: Target user
            medication_name: Name of the medication
            dosage: Dosage information
            time: Time to take the medication
            channels: Channels to use
            
        Returns:
            Dict with success status for each channel
        """
        if channels is None:
            channels = ['in_app', 'push']
        
        title = _("Medication Reminder")
        message = _("Time to take {medication} - {dosage} at {time}").format(
            medication=medication_name,
            dosage=dosage,
            time=time
        )
        
        data = {
            'medication_name': medication_name,
            'dosage': dosage,
            'time': time,
            'type': 'medication_reminder'
        }
        
        return self.send_notification(
            user=user,
            title=title,
            message=message,
            notification_type='medication',
            channels=channels,
            priority='high',
            data=data,
            template_name='medication_reminder'
        )
    
    def send_stock_alert(
        self,
        user: User,
        medication_name: str,
        current_stock: int,
        threshold: int,
        channels: List[str] = None,
    ) -> Dict[str, bool]:
        """
        Send a stock alert notification.
        
        Args:
            user: Target user
            medication_name: Name of the medication
            current_stock: Current stock level
            threshold: Stock threshold
            channels: Channels to use
            
        Returns:
            Dict with success status for each channel
        """
        if channels is None:
            channels = ['in_app', 'email']
        
        title = _("Stock Alert")
        message = _("Low stock alert: {medication} - {current} remaining (threshold: {threshold})").format(
            medication=medication_name,
            current=current_stock,
            threshold=threshold
        )
        
        data = {
            'medication_name': medication_name,
            'current_stock': current_stock,
            'threshold': threshold,
            'type': 'stock_alert'
        }
        
        return self.send_notification(
            user=user,
            title=title,
            message=message,
            notification_type='stock',
            channels=channels,
            priority='medium',
            data=data,
            template_name='stock_alert'
        )
    
    def send_system_maintenance(
        self,
        users: List[User],
        maintenance_type: str,
        start_time: datetime,
        end_time: datetime,
        description: str,
        channels: List[str] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send system maintenance notification.
        
        Args:
            users: List of target users
            maintenance_type: Type of maintenance
            start_time: Maintenance start time
            end_time: Maintenance end time
            description: Maintenance description
            channels: Channels to use
            
        Returns:
            Dict with results for each user and channel
        """
        if channels is None:
            channels = ['in_app', 'email']
        
        title = _("System Maintenance")
        message = _("Scheduled maintenance: {type} from {start} to {end}").format(
            type=maintenance_type,
            start=start_time.strftime("%Y-%m-%d %H:%M"),
            end=end_time.strftime("%Y-%m-%d %H:%M")
        )
        
        data = {
            'maintenance_type': maintenance_type,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'description': description,
            'type': 'system_maintenance'
        }
        
        return self.send_bulk_notifications(
            users=users,
            title=title,
            message=message,
            notification_type='maintenance',
            channels=channels,
            priority='medium',
            data=data,
            template_name='system_maintenance'
        )
    
    def _get_user_preferences(self, user: User) -> Optional[UserNotificationPreferences]:
        """Get user notification preferences, creating if they don't exist."""
        prefs, created = UserNotificationPreferences.objects.get_or_create(user=user)
        return prefs
    
    def _filter_channels_by_preferences(
        self, 
        channels: List[str], 
        prefs: UserNotificationPreferences
    ) -> List[str]:
        """Filter channels based on user preferences."""
        filtered = []
        
        for channel in channels:
            if channel == 'in_app' and prefs.in_app_notifications_enabled:
                filtered.append(channel)
            elif channel == 'email' and prefs.email_notifications_enabled:
                filtered.append(channel)
            elif channel == 'push' and prefs.push_notifications_enabled:
                filtered.append(channel)
            elif channel == 'sms' and prefs.sms_notifications_enabled:
                filtered.append(channel)
        
        return filtered
    
    def _check_rate_limit(self, user: User, channel: str) -> bool:
        """Check if user has exceeded rate limits for the channel."""
        limits = settings.NOTIFICATION_RATE_LIMITS.get(channel, {})
        
        # Check hourly limit
        hourly_key = f"notif_rate_limit:{user.id}:{channel}:hour:{timezone.now().strftime('%Y%m%d%H')}"
        hourly_count = self.rate_limit_cache.get(hourly_key, 0)
        if hourly_count >= limits.get('per_user_per_hour', 100):
            return False
        
        # Check daily limit
        daily_key = f"notif_rate_limit:{user.id}:{channel}:day:{timezone.now().strftime('%Y%m%d')}"
        daily_count = self.rate_limit_cache.get(daily_key, 0)
        if daily_count >= limits.get('per_user_per_day', 1000):
            return False
        
        return True
    
    def _create_notification_record(
        self,
        user: User,
        title: str,
        message: str,
        notification_type: str,
        priority: str,
        data: Dict[str, Any]
    ) -> Notification:
        """Create a notification record in the database."""
        return Notification.objects.create(
            title=title,
            content=message,
            notification_type=notification_type,
            priority=priority,
            status='active',
            target_users=[user],
            created_by=user,
            **data
        )
    
    def _send_to_channel(
        self,
        channel: str,
        user: User,
        notification: Notification,
        title: str,
        message: str,
        template_name: Optional[str],
        template_context: Optional[Dict[str, Any]],
        scheduled_at: Optional[datetime]
    ) -> bool:
        """Send notification to a specific channel."""
        try:
            if channel == 'in_app':
                return self._send_in_app_notification(user, title, message, notification)
            elif channel == 'email':
                return self._send_email_notification(
                    user, title, message, template_name, template_context, scheduled_at
                )
            elif channel == 'push':
                return self._send_push_notification(user, title, message, notification)
            elif channel == 'sms':
                return self._send_sms_notification(user, message, scheduled_at)
            else:
                logger.warning(f"Unknown notification channel: {channel}")
                return False
        except Exception as e:
            logger.error(f"Error sending {channel} notification to user {user.id}: {str(e)}")
            return False
    
    def _send_in_app_notification(
        self, 
        user: User, 
        title: str, 
        message: str, 
        notification: Notification
    ) -> bool:
        """Send in-app notification using our own implementation."""
        try:
            # Create a user notification record
            UserNotification.objects.create(
                user=user,
                notification=notification,
                title=title,
                message=message,
                is_read=False,
                created_at=timezone.now()
            )
            
            logger.info(f"In-app notification created for user {user.id}: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send in-app notification to user {user.id}: {e}")
            return False
    
    def _send_email_notification(
        self,
        user: User,
        title: str,
        message: str,
        template_name: Optional[str],
        template_context: Optional[Dict[str, Any]],
        scheduled_at: Optional[datetime]
    ) -> bool:
        """Send email notification using django-post-office."""
        try:
            context = template_context or {}
            context.update({
                'user': user,
                'title': title,
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
                    priority='high' if scheduled_at else 'now',
                )
            else:
                # Send simple email
                po_mail.send(
                    user.email,
                    settings.DEFAULT_FROM_EMAIL,
                    subject=title,
                    message=message,
                    html_message=message,
                    scheduled_time=scheduled_at,
                    priority='high' if scheduled_at else 'now',
                )
            
            return True
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
    
    def _send_push_notification(
        self, 
        user: User, 
        title: str, 
        message: str, 
        notification: Notification
    ) -> bool:
        """Send push notification using django-push-notifications."""
        try:
            # Get user's device tokens
            gcm_devices = GCMDevice.objects.filter(user=user, active=True)
            apns_devices = APNSDevice.objects.filter(user=user, active=True)
            
            success = True
            
            # Send to Android devices
            if gcm_devices.exists():
                gcm_devices.send_message(
                    title,
                    extra={
                        'message': message,
                        'notification_id': notification.pk,
                        'type': notification.notification_type,
                    }
                )
            
            # Send to iOS devices
            if apns_devices.exists():
                apns_devices.send_message(
                    title,
                    extra={
                        'message': message,
                        'notification_id': notification.pk,
                        'type': notification.notification_type,
                    }
                )
            
            # Send web push notifications
            try:
                # TODO: Implement web push notification using pywebpush
                # For now, log the notification
                logger.info(f"Web push notification for user {user.id}: {title} - {message}")
                # Placeholder for web push implementation
                # from pywebpush import webpush
                # webpush(subscription_info, data=json.dumps(payload))
            except Exception as e:
                logger.warning(f"Web push notification failed: {str(e)}")
                success = False
            
            return success
        except Exception as e:
            logger.error(f"Error sending push notification: {str(e)}")
            return False
    
    def _send_sms_notification(
        self, 
        user: User, 
        message: str, 
        scheduled_at: Optional[datetime]
    ) -> bool:
        """Send SMS notification (placeholder for external service integration)."""
        try:
            # Get user's phone number from preferences
            prefs = self._get_user_preferences(user)
            if not prefs.sms_phone_number:
                logger.warning(f"No SMS phone number for user {user.id}")
                return False
            
            # TODO: Integrate with SMS service (Twilio, AWS SNS, etc.)
            # For now, just log the SMS
            logger.info(f"SMS to {prefs.sms_phone_number}: {message}")
            
            return True
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
            return False
    
    def _group_users_by_preferences(
        self, 
        users: List[User], 
        channels: List[str]
    ) -> Dict[str, List[User]]:
        """Group users by their notification preferences for efficient sending."""
        groups = {}
        
        for user in users:
            prefs = self._get_user_preferences(user)
            filtered_channels = self._filter_channels_by_preferences(channels, prefs)
            
            if filtered_channels:
                group_key = ','.join(sorted(filtered_channels))
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(user)
        
        return groups
    
    def _send_bulk_to_group(
        self,
        users: List[User],
        title: str,
        message: str,
        notification_type: str,
        channels: List[str],
        priority: str,
        data: Dict[str, Any],
        scheduled_at: Optional[datetime],
        template_name: Optional[str],
        template_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, bool]]:
        """Send bulk notifications to a group of users with same preferences."""
        results = {}
        
        for user in users:
            results[user.id] = self.send_notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                channels=channels,
                priority=priority,
                data=data,
                scheduled_at=scheduled_at,
                template_name=template_name,
                template_context=template_context,
            )
        
        return results
    
    def _update_notification_results(
        self, 
        notification: Notification, 
        results: Dict[str, bool]
    ) -> None:
        """Update notification record with sending results."""
        # Create user notification records
        for user in notification.target_users.all():
            UserNotification.objects.create(
                user=user,
                notification=notification,
                status='unread' if any(results.values()) else 'failed'
            ) 