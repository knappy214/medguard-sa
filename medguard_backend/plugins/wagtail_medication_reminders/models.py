"""
Medication Reminders Models
Models for managing medication reminders and notifications.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from wagtail.snippets.models import register_snippet

User = get_user_model()


@register_snippet
class ReminderTemplate(models.Model):
    """Template for medication reminder notifications."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Template Name")
    )
    
    message_template = models.TextField(
        verbose_name=_("Message Template"),
        help_text=_("Use {medication_name}, {dosage}, {time} placeholders")
    )
    
    reminder_type = models.CharField(
        max_length=50,
        choices=[
            ('before', _('Before Dose')),
            ('at_time', _('At Dose Time')),
            ('overdue', _('Overdue')),
            ('missed', _('Missed Dose')),
        ],
        verbose_name=_("Reminder Type")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    class Meta:
        verbose_name = _("Reminder Template")
        verbose_name_plural = _("Reminder Templates")
    
    def __str__(self):
        return f"{self.name} ({self.get_reminder_type_display()})"


@register_snippet
class NotificationLog(models.Model):
    """Log of sent medication reminders."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    
    medication_name = models.CharField(
        max_length=255,
        verbose_name=_("Medication Name")
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=[
            ('sms', _('SMS')),
            ('email', _('Email')),
            ('push', _('Push Notification')),
            ('call', _('Phone Call')),
        ],
        verbose_name=_("Notification Type")
    )
    
    message_sent = models.TextField(
        verbose_name=_("Message Sent")
    )
    
    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Sent At")
    )
    
    delivery_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('delivered', _('Delivered')),
            ('failed', _('Failed')),
            ('read', _('Read')),
        ],
        default='pending',
        verbose_name=_("Delivery Status")
    )
    
    class Meta:
        verbose_name = _("Notification Log")
        verbose_name_plural = _("Notification Logs")
        ordering = ["-sent_at"]
    
    def __str__(self):
        return f"{self.notification_type} to {self.user.get_full_name()} - {self.medication_name}"
