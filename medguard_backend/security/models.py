"""
Security models for MedGuard SA.

This module imports all security-related models for Django's ORM.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class SecurityEvent(models.Model):
    """
    Model for tracking security events and incidents.
    
    This model stores security events for monitoring, alerting,
    and compliance reporting purposes.
    """
    
    # Event types
    class EventType(models.TextChoices):
        LOGIN_FAILED = 'login_failed', _('Login Failed')
        ACCESS_DENIED = 'access_denied', _('Access Denied')
        BREACH_ATTEMPT = 'breach_attempt', _('Breach Attempt')
        DATA_ACCESS = 'data_access', _('Data Access')
        DATA_MODIFICATION = 'data_modification', _('Data Modification')
        DATA_EXPORT = 'data_export', _('Data Export')
        USER_CREATION = 'user_creation', _('User Creation')
        USER_MODIFICATION = 'user_modification', _('User Modification')
        PERMISSION_CHANGE = 'permission_change', _('Permission Change')
        SYSTEM_ERROR = 'system_error', _('System Error')
        SECURITY_ALERT = 'security_alert', _('Security Alert')
    
    # Severity levels
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # User associated with the event
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='security_events',
        help_text=_('User associated with the security event')
    )
    
    # Event details
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        help_text=_('Type of security event')
    )
    
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        help_text=_('Severity level of the event')
    )
    
    description = models.TextField(
        help_text=_('Description of the security event')
    )
    
    # Request details
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address of the request')
    )
    
    user_agent = models.TextField(
        blank=True,
        help_text=_('User agent string')
    )
    
    request_path = models.CharField(
        max_length=500,
        blank=True,
        help_text=_('Request path/URL')
    )
    
    request_method = models.CharField(
        max_length=10,
        blank=True,
        help_text=_('HTTP method used')
    )
    
    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional metadata about the event')
    )
    
    # Resolution tracking
    is_resolved = models.BooleanField(
        default=False,
        help_text=_('Whether the security event has been resolved')
    )
    
    resolution_notes = models.TextField(
        blank=True,
        help_text=_('Notes about how the event was resolved')
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_security_events',
        help_text=_('User who resolved the security event')
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the security event was resolved')
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the security event occurred')
    )
    
    class Meta:
        verbose_name = _('Security Event')
        verbose_name_plural = _('Security Events')
        db_table = 'security_events'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['is_resolved', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.description[:50]}"
    
    def save(self, *args, **kwargs):
        """Override save to handle resolution tracking."""
        if self.is_resolved and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical security event."""
        return self.severity == self.Severity.CRITICAL
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Check if this event requires immediate attention."""
        return (
            self.severity in [self.Severity.HIGH, self.Severity.CRITICAL] or
            self.event_type in [
                self.EventType.BREACH_ATTEMPT,
                self.EventType.SECURITY_ALERT,
                self.EventType.SYSTEM_ERROR
            ]
        )


# Import all security models
from .audit import AuditLog
from .anonymization import AnonymizedDataset, DatasetAccessLog

__all__ = [
    'AuditLog',
    'AnonymizedDataset', 
    'DatasetAccessLog',
    'SecurityEvent',
] 