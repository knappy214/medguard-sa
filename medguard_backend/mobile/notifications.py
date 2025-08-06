"""
Mobile push notifications integration with Wagtail content
Wagtail 7.0.2 notification features
"""

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.models import Page
from wagtail.images.models import Image
import json
import logging
import requests
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class MobilePushNotificationManager:
    """
    Mobile push notification manager for Wagtail content
    """
    
    def __init__(self):
        self.notification_types = {
            'medication_reminder': 'Medication Reminder',
            'prescription_update': 'Prescription Update',
            'stock_alert': 'Stock Alert',
            'health_tip': 'Health Tip',
            'emergency_alert': 'Emergency Alert',
            'content_update': 'Content Update',
        }
    
    def send_notification(self, notification_type, title, message, data=None, target_users=None):
        """
        Send push notification to mobile devices
        """
        try:
            notification = {
                'id': str(uuid.uuid4()),
                'type': notification_type,
                'title': title,
                'message': message,
                'data': data or {},
                'timestamp': datetime.now().isoformat(),
                'target_users': target_users,
            }
            
            # Store notification for tracking
            self._store_notification(notification)
            
            # Send to mobile devices
            success = self._send_to_mobile_devices(notification)
            
            return {
                'success': success,
                'notification_id': notification['id'],
                'message': 'Notification sent successfully' if success else 'Failed to send notification'
            }
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _store_notification(self, notification):
        """
        Store notification in cache/database for tracking
        """
        cache_key = f"mobile_notification_{notification['id']}"
        cache.set(cache_key, notification, 86400)  # Store for 24 hours
    
    def _send_to_mobile_devices(self, notification):
        """
        Send notification to mobile devices via FCM/APNS
        """
        try:
            # This would integrate with Firebase Cloud Messaging (FCM) or Apple Push Notification Service (APNS)
            # For now, we'll simulate the sending
            
            # FCM example (would need firebase-admin package)
            # fcm_response = self._send_fcm_notification(notification)
            
            # APNS example (would need apns2 package)
            # apns_response = self._send_apns_notification(notification)
            
            # Simulate successful sending
            logger.info(f"Notification sent: {notification['title']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending to mobile devices: {e}")
            return False
    
    def _send_fcm_notification(self, notification):
        """
        Send notification via Firebase Cloud Messaging
        """
        # This would require firebase-admin package
        # Example implementation:
        """
        import firebase_admin
        from firebase_admin import messaging
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=notification['title'],
                body=notification['message']
            ),
            data=notification['data'],
            topic='medguard_notifications'
        )
        
        response = messaging.send(message)
        return response
        """
        pass
    
    def _send_apns_notification(self, notification):
        """
        Send notification via Apple Push Notification Service
        """
        # This would require apns2 package
        # Example implementation:
        """
        from apns2.client import APNsClient
        from apns2.payload import Payload
        
        client = APNsClient('path/to/cert.pem', use_sandbox=True)
        payload = Payload(alert=notification['message'], badge=1)
        
        client.send_notification('device_token', payload, 'com.medguard.app')
        """
        pass


class MedicationReminderNotifications:
    """
    Medication reminder notification system
    """
    
    def __init__(self):
        self.notification_manager = MobilePushNotificationManager()
    
    def schedule_medication_reminder(self, user_id, medication_name, dosage_time, dosage_amount):
        """
        Schedule a medication reminder notification
        """
        try:
            # Calculate reminder time (15 minutes before dosage time)
            reminder_time = dosage_time - timedelta(minutes=15)
            
            # Create reminder data
            reminder_data = {
                'user_id': user_id,
                'medication_name': medication_name,
                'dosage_time': dosage_time.isoformat(),
                'dosage_amount': dosage_amount,
                'reminder_time': reminder_time.isoformat(),
            }
            
            # Store reminder in cache
            cache_key = f"medication_reminder_{user_id}_{medication_name}_{dosage_time.strftime('%Y%m%d_%H%M')}"
            cache.set(cache_key, reminder_data, 86400)  # Store for 24 hours
            
            return {
                'success': True,
                'reminder_id': cache_key,
                'reminder_time': reminder_time.isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error scheduling medication reminder: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_medication_reminder(self, user_id, medication_name, dosage_amount):
        """
        Send medication reminder notification
        """
        title = "Medication Reminder"
        message = f"Time to take {dosage_amount} of {medication_name}"
        
        data = {
            'type': 'medication_reminder',
            'medication_name': medication_name,
            'dosage_amount': dosage_amount,
            'action': 'mark_taken',
        }
        
        return self.notification_manager.send_notification(
            'medication_reminder',
            title,
            message,
            data,
            [user_id]
        )


class ContentUpdateNotifications:
    """
    Content update notification system
    """
    
    def __init__(self):
        self.notification_manager = MobilePushNotificationManager()
    
    def notify_content_update(self, page, update_type='content_update'):
        """
        Send notification about content updates
        """
        try:
            title = "Content Updated"
            message = f"New information available: {page.title}"
            
            data = {
                'type': 'content_update',
                'page_id': page.id,
                'page_url': page.url,
                'page_title': page.title,
                'update_type': update_type,
            }
            
            return self.notification_manager.send_notification(
                'content_update',
                title,
                message,
                data
            )
            
        except Exception as e:
            logger.error(f"Error sending content update notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def notify_medication_update(self, medication):
        """
        Send notification about medication updates
        """
        try:
            title = "Medication Information Updated"
            message = f"Updated information for {medication.name}"
            
            data = {
                'type': 'medication_update',
                'medication_id': medication.id,
                'medication_name': medication.name,
                'medication_url': f"/medications/{medication.slug}/",
            }
            
            return self.notification_manager.send_notification(
                'content_update',
                title,
                message,
                data
            )
            
        except Exception as e:
            logger.error(f"Error sending medication update notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class EmergencyNotifications:
    """
    Emergency notification system
    """
    
    def __init__(self):
        self.notification_manager = MobilePushNotificationManager()
    
    def send_emergency_alert(self, alert_type, message, urgency='high'):
        """
        Send emergency alert notification
        """
        try:
            title = f"Emergency Alert: {alert_type.title()}"
            
            data = {
                'type': 'emergency_alert',
                'alert_type': alert_type,
                'urgency': urgency,
                'timestamp': datetime.now().isoformat(),
            }
            
            return self.notification_manager.send_notification(
                'emergency_alert',
                title,
                message,
                data
            )
            
        except Exception as e:
            logger.error(f"Error sending emergency alert: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_stock_alert(self, medication_name, current_stock, threshold=10):
        """
        Send stock alert notification
        """
        try:
            title = "Low Stock Alert"
            message = f"Low stock alert for {medication_name}. Current stock: {current_stock}"
            
            data = {
                'type': 'stock_alert',
                'medication_name': medication_name,
                'current_stock': current_stock,
                'threshold': threshold,
                'action': 'reorder',
            }
            
            return self.notification_manager.send_notification(
                'stock_alert',
                title,
                message,
                data
            )
            
        except Exception as e:
            logger.error(f"Error sending stock alert: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class NotificationPreferences:
    """
    User notification preferences management
    """
    
    def __init__(self):
        self.default_preferences = {
            'medication_reminders': True,
            'content_updates': True,
            'stock_alerts': True,
            'emergency_alerts': True,
            'health_tips': False,
            'quiet_hours_start': '22:00',
            'quiet_hours_end': '08:00',
            'timezone': 'Africa/Johannesburg',
        }
    
    def get_user_preferences(self, user_id):
        """
        Get user notification preferences
        """
        cache_key = f"notification_preferences_{user_id}"
        preferences = cache.get(cache_key)
        
        if not preferences:
            preferences = self.default_preferences.copy()
            cache.set(cache_key, preferences, 86400)
        
        return preferences
    
    def update_user_preferences(self, user_id, preferences):
        """
        Update user notification preferences
        """
        try:
            cache_key = f"notification_preferences_{user_id}"
            current_preferences = self.get_user_preferences(user_id)
            
            # Update with new preferences
            current_preferences.update(preferences)
            
            # Store updated preferences
            cache.set(cache_key, current_preferences, 86400)
            
            return {
                'success': True,
                'preferences': current_preferences
            }
            
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def should_send_notification(self, user_id, notification_type):
        """
        Check if notification should be sent based on user preferences
        """
        try:
            preferences = self.get_user_preferences(user_id)
            
            # Check if notification type is enabled
            if not preferences.get(notification_type, True):
                return False
            
            # Check quiet hours
            if self._is_quiet_hours(preferences):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking notification preferences: {e}")
            return True  # Default to sending if error
    
    def _is_quiet_hours(self, preferences):
        """
        Check if current time is within quiet hours
        """
        try:
            from datetime import datetime
            import pytz
            
            timezone = pytz.timezone(preferences.get('timezone', 'Africa/Johannesburg'))
            current_time = datetime.now(timezone).time()
            
            start_time = datetime.strptime(preferences.get('quiet_hours_start', '22:00'), '%H:%M').time()
            end_time = datetime.strptime(preferences.get('quiet_hours_end', '08:00'), '%H:%M').time()
            
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                # Quiet hours span midnight
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False


class NotificationTemplates:
    """
    Notification template management
    """
    
    @staticmethod
    def get_medication_reminder_template(medication_name, dosage_amount, dosage_time):
        """
        Get medication reminder notification template
        """
        return {
            'title': 'Medication Reminder',
            'message': f'Time to take {dosage_amount} of {medication_name}',
            'data': {
                'medication_name': medication_name,
                'dosage_amount': dosage_amount,
                'dosage_time': dosage_time.isoformat(),
                'action': 'mark_taken',
            }
        }
    
    @staticmethod
    def get_content_update_template(page_title, update_type):
        """
        Get content update notification template
        """
        return {
            'title': 'Content Updated',
            'message': f'New information available: {page_title}',
            'data': {
                'update_type': update_type,
                'action': 'view_content',
            }
        }
    
    @staticmethod
    def get_emergency_alert_template(alert_type, message):
        """
        Get emergency alert notification template
        """
        return {
            'title': f'Emergency Alert: {alert_type.title()}',
            'message': message,
            'data': {
                'alert_type': alert_type,
                'urgency': 'high',
                'action': 'view_alert',
            }
        } 