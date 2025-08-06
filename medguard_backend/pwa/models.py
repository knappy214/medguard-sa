"""
PWA Models for MedGuard SA
Handles push notifications, medication reminders, and PWA-specific data
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import json

User = get_user_model()


class PushSubscription(models.Model):
    """
    Model to store push notification subscriptions
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
        verbose_name=_('User')
    )
    endpoint = models.URLField(
        max_length=500,
        verbose_name=_('Push Endpoint')
    )
    p256dh = models.CharField(
        max_length=255,
        verbose_name=_('P256DH Key')
    )
    auth = models.CharField(
        max_length=255,
        verbose_name=_('Auth Key')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )

    class Meta:
        verbose_name = _('Push Subscription')
        verbose_name_plural = _('Push Subscriptions')
        unique_together = ['user', 'endpoint']

    def __str__(self):
        return f"Push subscription for {self.user.username}"

    def to_dict(self):
        """Convert subscription to dictionary for web push"""
        return {
            'endpoint': self.endpoint,
            'keys': {
                'p256dh': self.p256dh,
                'auth': self.auth
            }
        }


class MedicationReminder(models.Model):
    """
    Model for medication reminders with push notification support
    """
    REMINDER_TYPES = [
        ('medication', _('Medication Reminder')),
        ('refill', _('Refill Reminder')),
        ('appointment', _('Appointment Reminder')),
        ('test', _('Test Reminder')),
    ]

    REMINDER_STATUS = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('acknowledged', _('Acknowledged')),
        ('snoozed', _('Snoozed')),
        ('cancelled', _('Cancelled')),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medication_reminders',
        verbose_name=_('User')
    )
    medication_name = models.CharField(
        max_length=255,
        verbose_name=_('Medication Name')
    )
    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPES,
        default='medication',
        verbose_name=_('Reminder Type')
    )
    scheduled_time = models.DateTimeField(
        verbose_name=_('Scheduled Time')
    )
    message = models.TextField(
        verbose_name=_('Reminder Message')
    )
    status = models.CharField(
        max_length=20,
        choices=REMINDER_STATUS,
        default='pending',
        verbose_name=_('Status')
    )
    push_sent = models.BooleanField(
        default=False,
        verbose_name=_('Push Notification Sent')
    )
    push_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Push Sent At')
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Acknowledged At')
    )
    snooze_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Snooze Until')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Medication Reminder')
        verbose_name_plural = _('Medication Reminders')
        ordering = ['scheduled_time']
        indexes = [
            models.Index(fields=['user', 'status', 'scheduled_time']),
            models.Index(fields=['status', 'scheduled_time']),
        ]

    def __str__(self):
        return f"{self.medication_name} - {self.scheduled_time}"

    @property
    def is_overdue(self):
        """Check if reminder is overdue"""
        return self.scheduled_time < timezone.now() and self.status == 'pending'

    @property
    def is_snoozed(self):
        """Check if reminder is snoozed"""
        return self.status == 'snoozed' and self.snooze_until and self.snooze_until > timezone.now()

    def mark_as_sent(self):
        """Mark reminder as sent"""
        self.status = 'sent'
        self.push_sent = True
        self.push_sent_at = timezone.now()
        self.save()

    def mark_as_acknowledged(self):
        """Mark reminder as acknowledged"""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.save()

    def snooze(self, minutes=15):
        """Snooze reminder for specified minutes"""
        from django.utils import timezone
        self.status = 'snoozed'
        self.snooze_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()

    def get_push_payload(self):
        """Get payload for push notification"""
        return {
            'title': f'MedGuard SA - {self.get_reminder_type_display()}',
            'body': self.message,
            'icon': '/static/pwa/icons/icon-192x192.png',
            'badge': '/static/pwa/icons/badge-72x72.png',
            'data': {
                'reminder_id': self.id,
                'medication_name': self.medication_name,
                'reminder_type': self.reminder_type,
                'scheduled_time': self.scheduled_time.isoformat(),
            },
            'actions': [
                {
                    'action': 'take',
                    'title': _('Take Medication'),
                    'icon': '/static/pwa/icons/take-medication.png'
                },
                {
                    'action': 'snooze',
                    'title': _('Snooze 15min'),
                    'icon': '/static/pwa/icons/snooze.png'
                }
            ],
            'vibrate': [100, 50, 100],
            'requireInteraction': True,
            'tag': f'medication-reminder-{self.id}',
        }


class PWASettings(models.Model):
    """
    User-specific PWA settings and preferences
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='pwa_settings',
        verbose_name=_('User')
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Notifications Enabled')
    )
    reminder_sound = models.BooleanField(
        default=True,
        verbose_name=_('Reminder Sound')
    )
    reminder_vibration = models.BooleanField(
        default=True,
        verbose_name=_('Reminder Vibration')
    )
    auto_snooze_minutes = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(120)],
        verbose_name=_('Auto Snooze Minutes')
    )
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Quiet Hours Start')
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Quiet Hours End')
    )
    theme_preference = models.CharField(
        max_length=20,
        choices=[
            ('light', _('Light')),
            ('dark', _('Dark')),
            ('auto', _('Auto')),
        ],
        default='auto',
        verbose_name=_('Theme Preference')
    )
    language_preference = models.CharField(
        max_length=10,
        choices=[
            ('en-ZA', 'English (South Africa)'),
            ('af-ZA', 'Afrikaans (Suid-Afrika)'),
        ],
        default='en-ZA',
        verbose_name=_('Language Preference')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('PWA Settings')
        verbose_name_plural = _('PWA Settings')

    def __str__(self):
        return f"PWA Settings for {self.user.username}"

    @property
    def is_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.now().time()
        if self.quiet_hours_start <= self.quiet_hours_end:
            return self.quiet_hours_start <= now <= self.quiet_hours_end
        else:
            # Handles overnight quiet hours
            return now >= self.quiet_hours_start or now <= self.quiet_hours_end


class OfflineData(models.Model):
    """
    Model to store offline data for PWA
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='offline_data',
        verbose_name=_('User')
    )
    data_type = models.CharField(
        max_length=50,
        verbose_name=_('Data Type')
    )
    data_key = models.CharField(
        max_length=255,
        verbose_name=_('Data Key')
    )
    data_value = models.JSONField(
        verbose_name=_('Data Value')
    )
    last_synced = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Synced')
    )
    is_synced = models.BooleanField(
        default=False,
        verbose_name=_('Is Synced')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )

    class Meta:
        verbose_name = _('Offline Data')
        verbose_name_plural = _('Offline Data')
        unique_together = ['user', 'data_type', 'data_key']
        indexes = [
            models.Index(fields=['user', 'data_type', 'is_synced']),
        ]

    def __str__(self):
        return f"{self.data_type}:{self.data_key} for {self.user.username}"

    def get_data(self):
        """Get data value as Python object"""
        return self.data_value

    def set_data(self, data):
        """Set data value from Python object"""
        self.data_value = data
        self.is_synced = False
        self.save()


class PWAInstallation(models.Model):
    """
    Track PWA installations
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pwa_installations',
        verbose_name=_('User')
    )
    platform = models.CharField(
        max_length=50,
        verbose_name=_('Platform')
    )
    browser = models.CharField(
        max_length=50,
        verbose_name=_('Browser')
    )
    version = models.CharField(
        max_length=20,
        verbose_name=_('Version')
    )
    installed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Installed At')
    )
    last_used = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Used')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active')
    )

    class Meta:
        verbose_name = _('PWA Installation')
        verbose_name_plural = _('PWA Installations')
        ordering = ['-installed_at']

    def __str__(self):
        return f"{self.platform} {self.browser} {self.version} - {self.user.username}"


class EmergencyContact(models.Model):
    """
    Emergency contact information for offline access
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='emergency_contacts',
        verbose_name=_('User')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Contact Name')
    )
    relationship = models.CharField(
        max_length=100,
        verbose_name=_('Relationship')
    )
    phone = models.CharField(
        max_length=20,
        verbose_name=_('Phone Number')
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email')
    )
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_('Is Primary Contact')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        verbose_name = _('Emergency Contact')
        verbose_name_plural = _('Emergency Contacts')
        ordering = ['-is_primary', 'name']

    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.user.username}"

    def save(self, *args, **kwargs):
        # Ensure only one primary contact per user
        if self.is_primary:
            EmergencyContact.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs) 