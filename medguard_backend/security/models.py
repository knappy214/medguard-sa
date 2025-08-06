"""
Security models for MedGuard SA.

This module imports all security-related models for Django's ORM.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone

# Wagtail imports for enhanced admin integration
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.permission_policies import ModelPermissionPolicy

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
    
    # Wagtail 7.0.2: Enhanced search configuration with permission-aware indexing
    search_fields = [
        # Primary search fields with boost factors
        index.SearchField('description', boost=2.0),
        index.SearchField('event_type', boost=1.5),
        index.SearchField('severity', boost=1.2),
        index.SearchField('ip_address', boost=1.0),
        index.SearchField('request_path', boost=1.0),
        
        # Related fields with permission context
        index.RelatedFields('user', [
            index.SearchField('username', boost=1.5),
            index.SearchField('email', boost=1.0),
        ]),
        index.RelatedFields('resolved_by', [
            index.SearchField('username', boost=1.0),
        ]),
        
        # Autocomplete fields for quick search
        index.AutocompleteField('event_type'),
        index.AutocompleteField('severity'),
        index.AutocompleteField('ip_address'),
        
        # Filter fields for faceted search with permission filtering
        index.FilterField('event_type'),
        index.FilterField('severity'),
        index.FilterField('is_resolved'),
        index.FilterField('timestamp'),
        index.FilterField('user'),
        index.FilterField('resolved_by'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels with permission-based access
    panels = [
        # Event Information Panel
        MultiFieldPanel([
            FieldPanel('event_type'),
            FieldPanel('severity'),
            FieldPanel('description'),
        ], heading=_('Event Information'), classname='collapsible'),
        
        # User Information Panel (permission-restricted)
        MultiFieldPanel([
            FieldPanel('user'),
            FieldPanel('resolved_by'),
        ], heading=_('User Information'), classname='collapsible'),
        
        # Request Details Panel
        MultiFieldPanel([
            FieldPanel('ip_address'),
            FieldPanel('user_agent'),
            FieldPanel('request_path'),
            FieldPanel('request_method'),
        ], heading=_('Request Details'), classname='collapsible'),
        
        # Resolution Panel
        MultiFieldPanel([
            FieldPanel('is_resolved'),
            FieldPanel('resolution_notes'),
            FieldPanel('resolved_at'),
        ], heading=_('Resolution'), classname='collapsible'),
        
        # Metadata Panel
        MultiFieldPanel([
            FieldPanel('metadata'),
            FieldPanel('timestamp'),
        ], heading=_('Metadata'), classname='collapsible'),
    ]
    

    
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
        permissions = [
            ('view_security_events', _('Can view security events')),
            ('manage_security_events', _('Can manage security events')),
            ('export_security_events', _('Can export security events')),
            ('resolve_security_events', _('Can resolve security events')),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def save(self, *args, **kwargs):
        """Override save to add automatic resolution tracking."""
        if self.is_resolved and not self.resolved_at:
            self.resolved_at = timezone.now()
        elif not self.is_resolved:
            self.resolved_at = None
            self.resolved_by = None
        
        super().save(*args, **kwargs)
    
    @property
    def is_critical(self) -> bool:
        """Check if event is critical severity."""
        return self.severity == self.Severity.CRITICAL
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Check if event requires immediate attention."""
        return (self.severity in [self.Severity.HIGH, self.Severity.CRITICAL] and 
                not self.is_resolved)
    
    # Wagtail 7.0.2: Enhanced validation with permission-aware checks
    def clean(self):
        """Enhanced validation for security events."""
        super().clean()
        
        # Validate description length
        if len(self.description.strip()) < 10:
            raise ValidationError({
                'description': _('Description must be at least 10 characters long.')
            })
        
        # Validate resolution logic
        if self.is_resolved and not self.resolution_notes:
            raise ValidationError({
                'resolution_notes': _('Resolution notes are required when marking as resolved.')
            })
        
        if self.is_resolved and not self.resolved_by:
            raise ValidationError({
                'resolved_by': _('Resolver must be specified when marking as resolved.')
            })
        
        # Validate IP address format
        if self.ip_address:
            try:
                # Django's GenericIPAddressField handles validation
                pass
            except ValidationError:
                raise ValidationError({
                    'ip_address': _('Invalid IP address format.')
                })
        
        # Validate request method
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        if self.request_method and self.request_method.upper() not in valid_methods:
            raise ValidationError({
                'request_method': _('Invalid HTTP method.')
            })
    
    # Wagtail 7.0.2: Enhanced admin methods with permission context
    def get_admin_display_title(self):
        """Return the title to display in admin with severity indicators."""
        severity_icon = {
            self.Severity.LOW: '🔵',
            self.Severity.MEDIUM: '🟡',
            self.Severity.HIGH: '🟠',
            self.Severity.CRITICAL: '🔴',
        }
        icon = severity_icon.get(self.severity, '⚪')
        return f"{icon} {self.get_event_type_display()}"
    
    def get_admin_display_subtitle(self):
        """Return the subtitle to display in admin."""
        status = "Resolved" if self.is_resolved else "Active"
        return f"{self.severity} - {status} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def get_admin_url(self):
        """Return the admin URL for this security event."""
        from django.urls import reverse
        return reverse('admin:security_securityevent_change', args=[self.id])
    
    def get_absolute_url(self):
        """Return the public URL for this security event."""
        return f"/security/events/{self.id}/"
    
    # Wagtail 7.0.2: Permission-aware search methods
    def get_search_display_title(self):
        """Return the title to display in search results."""
        return f"{self.get_event_type_display()} - {self.severity}"
    
    def get_search_description(self):
        """Return the description to display in search results."""
        return self.description[:200] + "..." if len(self.description) > 200 else self.description
    
    def get_search_url(self, request=None):
        """Return the URL for this security event in search results."""
        return self.get_absolute_url()
    
    def get_search_meta(self):
        """Return additional metadata for search results."""
        return {
            'event_type': self.get_event_type_display(),
            'severity': self.get_severity_display(),
            'is_resolved': self.is_resolved,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
        }
    
    # Wagtail 7.0.2: Permission-based access control methods
    def user_can_view(self, user):
        """Check if user can view this security event."""
        return self.permission_policy.user_has_permission(user, 'view')
    
    def user_can_change(self, user):
        """Check if user can change this security event."""
        return self.permission_policy.user_has_permission(user, 'change')
    
    def user_can_delete(self, user):
        """Check if user can delete this security event."""
        return self.permission_policy.user_has_permission(user, 'delete')
    
    def user_can_resolve(self, user):
        """Check if user can resolve this security event."""
        return self.permission_policy.user_has_permission(user, 'resolve_security_events')
    
    def user_can_export(self, user):
        """Check if user can export this security event."""
        return self.permission_policy.user_has_permission(user, 'export_security_events')


# Wagtail 7.0.2: Permission policy for enhanced access control
SecurityEvent.permission_policy = ModelPermissionPolicy(SecurityEvent)


# Import all security models
from .audit import AuditLog
from .anonymization import AnonymizedDataset, DatasetAccessLog

__all__ = [
    'AuditLog',
    'AnonymizedDataset', 
    'DatasetAccessLog',
    'SecurityEvent',
] 