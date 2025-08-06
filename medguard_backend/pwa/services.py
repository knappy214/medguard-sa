"""
PWA Services for MedGuard SA
Handles push notifications, background sync, and PWA-specific functionality
"""

import json
import logging
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from django.utils.translation import gettext as _
from pywebpush import WebPushException, webpush
from .models import PushSubscription, MedicationReminder, PWASettings

logger = logging.getLogger(__name__)


class PushNotificationService:
    """
    Service for handling push notifications
    """
    
    def __init__(self):
        self.vapid_private_key = getattr(settings, 'VAPID_PRIVATE_KEY', None)
        self.vapid_public_key = getattr(settings, 'VAPID_PUBLIC_KEY', None)
        self.vapid_claims = {
            "sub": f"mailto:{getattr(settings, 'VAPID_EMAIL', 'admin@medguard.co.za')}",
            "aud": "https://fcm.googleapis.com"
        }

    def send_push_notification(
        self,
        subscription: PushSubscription,
        payload: Dict[str, Any],
        ttl: int = 86400
    ) -> bool:
        """
        Send push notification to a specific subscription
        
        Args:
            subscription: PushSubscription instance
            payload: Notification payload
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            subscription_dict = subscription.to_dict()
            
            response = webpush(
                subscription_info=subscription_dict,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key,
                vapid_claims=self.vapid_claims,
                ttl=ttl
            )
            
            logger.info(f"Push notification sent successfully: {response.status_code}")
            return True
            
        except WebPushException as e:
            logger.error(f"Push notification failed: {e}")
            if e.response and e.response.status_code == 410:
                # Subscription is no longer valid
                subscription.is_active = False
                subscription.save()
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {e}")
            return False

    def send_medication_reminder(self, reminder: MedicationReminder) -> bool:
        """
        Send medication reminder push notification
        
        Args:
            reminder: MedicationReminder instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Check user settings
        try:
            pwa_settings = reminder.user.pwa_settings
            if not pwa_settings.notifications_enabled:
                logger.info(f"Notifications disabled for user {reminder.user.username}")
                return False
                
            if pwa_settings.is_quiet_hours:
                logger.info(f"Quiet hours active for user {reminder.user.username}")
                return False
                
        except PWASettings.DoesNotExist:
            # Use default settings
            pass

        # Get user's active subscriptions
        subscriptions = PushSubscription.objects.filter(
            user=reminder.user,
            is_active=True
        )

        if not subscriptions.exists():
            logger.warning(f"No active push subscriptions for user {reminder.user.username}")
            return False

        # Prepare payload
        payload = reminder.get_push_payload()
        
        # Customize payload based on user settings
        try:
            pwa_settings = reminder.user.pwa_settings
            if not pwa_settings.reminder_vibration:
                payload.pop('vibrate', None)
        except PWASettings.DoesNotExist:
            pass

        # Send to all user subscriptions
        success_count = 0
        for subscription in subscriptions:
            if self.send_push_notification(subscription, payload):
                success_count += 1

        if success_count > 0:
            reminder.mark_as_sent()
            logger.info(f"Medication reminder sent to {success_count} devices for user {reminder.user.username}")
            return True
        else:
            logger.error(f"Failed to send medication reminder to any device for user {reminder.user.username}")
            return False

    def send_bulk_medication_reminders(self, reminders: List[MedicationReminder]) -> Dict[str, int]:
        """
        Send multiple medication reminders
        
        Args:
            reminders: List of MedicationReminder instances
            
        Returns:
            Dict with success and failure counts
        """
        results = {'success': 0, 'failure': 0}
        
        for reminder in reminders:
            if self.send_medication_reminder(reminder):
                results['success'] += 1
            else:
                results['failure'] += 1
                
        return results

    def send_emergency_notification(
        self,
        user,
        message: str,
        title: str = "MedGuard SA - Emergency"
    ) -> bool:
        """
        Send emergency notification (bypasses quiet hours)
        
        Args:
            user: User instance
            message: Emergency message
            title: Notification title
            
        Returns:
            bool: True if successful, False otherwise
        """
        subscriptions = PushSubscription.objects.filter(
            user=user,
            is_active=True
        )

        if not subscriptions.exists():
            return False

        payload = {
            'title': title,
            'body': message,
            'icon': '/static/pwa/icons/icon-192x192.png',
            'badge': '/static/pwa/icons/badge-72x72.png',
            'data': {
                'type': 'emergency',
                'timestamp': timezone.now().isoformat(),
            },
            'vibrate': [200, 100, 200, 100, 200],
            'requireInteraction': True,
            'priority': 'high',
            'tag': 'emergency-notification',
        }

        success_count = 0
        for subscription in subscriptions:
            if self.send_push_notification(subscription, payload, ttl=3600):
                success_count += 1

        return success_count > 0


class MedicationReminderService:
    """
    Service for managing medication reminders
    """
    
    def __init__(self):
        self.push_service = PushNotificationService()

    def create_medication_reminder(
        self,
        user,
        medication_name: str,
        scheduled_time: timezone.datetime,
        message: str = None,
        reminder_type: str = 'medication'
    ) -> MedicationReminder:
        """
        Create a new medication reminder
        
        Args:
            user: User instance
            medication_name: Name of the medication
            scheduled_time: When to send the reminder
            message: Custom message (optional)
            reminder_type: Type of reminder
            
        Returns:
            MedicationReminder instance
        """
        if not message:
            message = self._generate_default_message(medication_name, reminder_type)

        reminder = MedicationReminder.objects.create(
            user=user,
            medication_name=medication_name,
            reminder_type=reminder_type,
            scheduled_time=scheduled_time,
            message=message
        )

        logger.info(f"Created medication reminder: {reminder}")
        return reminder

    def _generate_default_message(self, medication_name: str, reminder_type: str) -> str:
        """Generate default reminder message"""
        if reminder_type == 'medication':
            return _("Time to take your medication: {medication_name}").format(
                medication_name=medication_name
            )
        elif reminder_type == 'refill':
            return _("Time to refill your prescription: {medication_name}").format(
                medication_name=medication_name
            )
        elif reminder_type == 'appointment':
            return _("You have an upcoming appointment")
        elif reminder_type == 'test':
            return _("Time for your medical test")
        else:
            return _("You have a reminder")

    def get_due_reminders(self, user=None) -> List[MedicationReminder]:
        """
        Get reminders that are due to be sent
        
        Args:
            user: Optional user filter
            
        Returns:
            List of due MedicationReminder instances
        """
        now = timezone.now()
        queryset = MedicationReminder.objects.filter(
            status='pending',
            scheduled_time__lte=now
        )

        if user:
            queryset = queryset.filter(user=user)

        return list(queryset)

    def get_overdue_reminders(self, user=None) -> List[MedicationReminder]:
        """
        Get overdue reminders
        
        Args:
            user: Optional user filter
            
        Returns:
            List of overdue MedicationReminder instances
        """
        now = timezone.now()
        queryset = MedicationReminder.objects.filter(
            status='pending',
            scheduled_time__lt=now - timezone.timedelta(minutes=15)
        )

        if user:
            queryset = queryset.filter(user=user)

        return list(queryset)

    def process_due_reminders(self) -> Dict[str, int]:
        """
        Process all due reminders and send push notifications
        
        Returns:
            Dict with success and failure counts
        """
        due_reminders = self.get_due_reminders()
        
        if not due_reminders:
            logger.info("No due reminders to process")
            return {'success': 0, 'failure': 0}

        logger.info(f"Processing {len(due_reminders)} due reminders")
        
        # Group reminders by user to avoid spam
        user_reminders = {}
        for reminder in due_reminders:
            if reminder.user_id not in user_reminders:
                user_reminders[reminder.user_id] = []
            user_reminders[reminder.user_id].append(reminder)

        results = {'success': 0, 'failure': 0}
        
        for user_id, reminders in user_reminders.items():
            # Send only the most recent reminder per user to avoid spam
            latest_reminder = max(reminders, key=lambda r: r.scheduled_time)
            
            if self.push_service.send_medication_reminder(latest_reminder):
                results['success'] += 1
                # Mark other reminders as sent to avoid duplicates
                for reminder in reminders:
                    if reminder != latest_reminder:
                        reminder.mark_as_sent()
            else:
                results['failure'] += 1

        logger.info(f"Processed reminders: {results}")
        return results

    def snooze_reminder(self, reminder_id: int, minutes: int = 15) -> bool:
        """
        Snooze a reminder
        
        Args:
            reminder_id: ID of the reminder
            minutes: Minutes to snooze
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reminder = MedicationReminder.objects.get(id=reminder_id)
            reminder.snooze(minutes)
            logger.info(f"Snoozed reminder {reminder_id} for {minutes} minutes")
            return True
        except MedicationReminder.DoesNotExist:
            logger.error(f"Reminder {reminder_id} not found")
            return False

    def acknowledge_reminder(self, reminder_id: int) -> bool:
        """
        Acknowledge a reminder
        
        Args:
            reminder_id: ID of the reminder
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reminder = MedicationReminder.objects.get(id=reminder_id)
            reminder.mark_as_acknowledged()
            logger.info(f"Acknowledged reminder {reminder_id}")
            return True
        except MedicationReminder.DoesNotExist:
            logger.error(f"Reminder {reminder_id} not found")
            return False


class BackgroundSyncService:
    """
    Service for handling background sync operations
    """
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes

    def sync_offline_data(self, user) -> Dict[str, Any]:
        """
        Sync offline data for a user
        
        Args:
            user: User instance
            
        Returns:
            Dict with sync results
        """
        from .models import OfflineData
        
        results = {
            'synced': 0,
            'failed': 0,
            'errors': []
        }

        # Get unsynced data
        offline_data = OfflineData.objects.filter(
            user=user,
            is_synced=False
        )

        for data in offline_data:
            try:
                if self._process_offline_data(data):
                    data.is_synced = True
                    data.save()
                    results['synced'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
                logger.error(f"Error syncing offline data {data.id}: {e}")

        return results

    def _process_offline_data(self, offline_data) -> bool:
        """
        Process individual offline data item
        
        Args:
            offline_data: OfflineData instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        data_type = offline_data.data_type
        data_value = offline_data.get_data()

        if data_type == 'medication_schedule':
            return self._sync_medication_schedule(offline_data.user, data_value)
        elif data_type == 'prescription_upload':
            return self._sync_prescription_upload(offline_data.user, data_value)
        elif data_type == 'emergency_contact':
            return self._sync_emergency_contact(offline_data.user, data_value)
        else:
            logger.warning(f"Unknown offline data type: {data_type}")
            return False

    def _sync_medication_schedule(self, user, data) -> bool:
        """Sync medication schedule changes"""
        try:
            # Implementation would sync with medication models
            logger.info(f"Syncing medication schedule for user {user.username}")
            return True
        except Exception as e:
            logger.error(f"Error syncing medication schedule: {e}")
            return False

    def _sync_prescription_upload(self, user, data) -> bool:
        """Sync prescription uploads"""
        try:
            # Implementation would handle prescription upload
            logger.info(f"Syncing prescription upload for user {user.username}")
            return True
        except Exception as e:
            logger.error(f"Error syncing prescription upload: {e}")
            return False

    def _sync_emergency_contact(self, user, data) -> bool:
        """Sync emergency contact changes"""
        try:
            from .models import EmergencyContact
            
            # Update or create emergency contact
            contact, created = EmergencyContact.objects.update_or_create(
                user=user,
                name=data.get('name'),
                defaults={
                    'relationship': data.get('relationship', ''),
                    'phone': data.get('phone', ''),
                    'email': data.get('email', ''),
                    'is_primary': data.get('is_primary', False)
                }
            )
            
            logger.info(f"{'Created' if created else 'Updated'} emergency contact for user {user.username}")
            return True
        except Exception as e:
            logger.error(f"Error syncing emergency contact: {e}")
            return False

    def get_sync_status(self, user) -> Dict[str, Any]:
        """
        Get sync status for a user
        
        Args:
            user: User instance
            
        Returns:
            Dict with sync status information
        """
        from .models import OfflineData
        
        unsynced_count = OfflineData.objects.filter(
            user=user,
            is_synced=False
        ).count()

        last_sync = OfflineData.objects.filter(
            user=user,
            is_synced=True
        ).order_by('-last_synced').first()

        return {
            'unsynced_count': unsynced_count,
            'last_sync': last_sync.last_synced if last_sync else None,
            'needs_sync': unsynced_count > 0
        }


# Service instances
push_service = PushNotificationService()
reminder_service = MedicationReminderService()
sync_service = BackgroundSyncService() 