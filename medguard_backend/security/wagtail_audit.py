"""
Wagtail 7.0.2 Enhanced Audit Logging for Healthcare

This module implements Wagtail 7.0.2's improved audit logging system
with healthcare-specific tracking for content changes and access.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError
from wagtail.models import Page, Site, Revision
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.permission_policies import ModelPermissionPolicy

User = get_user_model()
logger = logging.getLogger(__name__)


class WagtailAuditLog(models.Model):
    """
    Wagtail 7.0.2 enhanced audit logging for content changes and access.
    
    This model tracks all content-related activities in the Wagtail CMS
    with healthcare-specific context and HIPAA compliance features.
    """
    
    # Audit event types for Wagtail content
    class EventType(models.TextChoices):
        # Content creation and modification
        PAGE_CREATED = 'page_created', _('Page Created')
        PAGE_MODIFIED = 'page_modified', _('Page Modified')
        PAGE_DELETED = 'page_deleted', _('Page Deleted')
        PAGE_PUBLISHED = 'page_published', _('Page Published')
        PAGE_UNPUBLISHED = 'page_unpublished', _('Page Unpublished')
        
        # Content access
        PAGE_VIEWED = 'page_viewed', _('Page Viewed')
        PAGE_ACCESSED = 'page_accessed', _('Page Accessed')
        CONTENT_EXPORTED = 'content_exported', _('Content Exported')
        CONTENT_IMPORTED = 'content_imported', _('Content Imported')
        
        # Media and documents
        IMAGE_UPLOADED = 'image_uploaded', _('Image Uploaded')
        IMAGE_MODIFIED = 'image_modified', _('Image Modified')
        IMAGE_DELETED = 'image_deleted', _('Image Deleted')
        DOCUMENT_UPLOADED = 'document_uploaded', _('Document Uploaded')
        DOCUMENT_MODIFIED = 'document_modified', _('Document Modified')
        DOCUMENT_DELETED = 'document_deleted', _('Document Deleted')
        
        # User management
        USER_LOGIN = 'user_login', _('User Login')
        USER_LOGOUT = 'user_logout', _('User Logout')
        USER_PERMISSION_CHANGED = 'user_permission_changed', _('User Permission Changed')
        USER_ROLE_ASSIGNED = 'user_role_assigned', _('User Role Assigned')
        USER_ROLE_REVOKED = 'user_role_revoked', _('User Role Revoked')
        
        # Healthcare-specific events
        PATIENT_DATA_ACCESSED = 'patient_data_accessed', _('Patient Data Accessed')
        MEDICATION_DATA_MODIFIED = 'medication_data_modified', _('Medication Data Modified')
        PRESCRIPTION_CREATED = 'prescription_created', _('Prescription Created')
        PRESCRIPTION_MODIFIED = 'prescription_modified', _('Prescription Modified')
        PRESCRIPTION_APPROVED = 'prescription_approved', _('Prescription Approved')
        PRESCRIPTION_REJECTED = 'prescription_rejected', _('Prescription Rejected')
        
        # System events
        SYSTEM_BACKUP = 'system_backup', _('System Backup')
        SYSTEM_RESTORE = 'system_restore', _('System Restore')
        SECURITY_ALERT = 'security_alert', _('Security Alert')
        COMPLIANCE_CHECK = 'compliance_check', _('Compliance Check')
    
    # Severity levels for audit events
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # User who performed the action
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wagtail_audit_events',
        help_text=_('User who performed the audited action')
    )
    
    # Event details
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        help_text=_('Type of audit event')
    )
    
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.MEDIUM,
        help_text=_('Severity level of the audit event')
    )
    
    description = models.TextField(
        help_text=_('Description of the audit event')
    )
    
    # Content tracking
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_('Content type of the affected object')
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of the affected object')
    )
    
    object_repr = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('String representation of the affected object')
    )
    
    # Wagtail-specific fields
    page = models.ForeignKey(
        Page,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
        help_text=_('Page associated with the audit event')
    )
    
    revision = models.ForeignKey(
        Revision,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_events',
        help_text=_('Revision associated with the audit event')
    )
    
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_('Site associated with the audit event')
    )
    
    # Request context
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
    
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Session ID for the request')
    )
    
    # Healthcare-specific context
    patient_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Patient ID if the event involves patient data')
    )
    
    medication_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Medication ID if the event involves medication data')
    )
    
    prescription_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Prescription ID if the event involves prescription data')
    )
    
    # Change tracking
    old_values = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Previous values before the change')
    )
    
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('New values after the change')
    )
    
    changed_fields = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of fields that were changed')
    )
    
    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional metadata about the audit event')
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the audit event occurred')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        # Primary search fields with boost factors
        index.SearchField('description', boost=2.0),
        index.SearchField('event_type', boost=1.5),
        index.SearchField('severity', boost=1.2),
        index.SearchField('object_repr', boost=1.0),
        index.SearchField('request_path', boost=1.0),
        
        # Healthcare-specific search fields
        index.SearchField('patient_id', boost=1.5),
        index.SearchField('medication_id', boost=1.5),
        index.SearchField('prescription_id', boost=1.5),
        
        # Related fields with permission context
        index.RelatedFields('user', [
            index.SearchField('username', boost=1.5),
            index.SearchField('email', boost=1.0),
        ]),
        index.RelatedFields('page', [
            index.SearchField('title', boost=1.5),
            index.SearchField('slug', boost=1.0),
        ]),
        
        # Autocomplete fields for quick search
        index.AutocompleteField('event_type'),
        index.AutocompleteField('severity'),
        index.AutocompleteField('patient_id'),
        index.AutocompleteField('medication_id'),
        
        # Filter fields for faceted search
        index.FilterField('event_type'),
        index.FilterField('severity'),
        index.FilterField('timestamp'),
        index.FilterField('user'),
        index.FilterField('page'),
        index.FilterField('content_type'),
        index.FilterField('patient_id'),
        index.FilterField('medication_id'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        FieldPanel('event_type'),
        FieldPanel('severity'),
        FieldPanel('description'),
        FieldPanel('user'),
        MultiFieldPanel([
            FieldPanel('content_type'),
            FieldPanel('object_id'),
            FieldPanel('object_repr'),
        ], heading=_('Content Information')),
        MultiFieldPanel([
            FieldPanel('page'),
            FieldPanel('revision'),
            FieldPanel('site'),
        ], heading=_('Wagtail Context')),
        MultiFieldPanel([
            FieldPanel('patient_id'),
            FieldPanel('medication_id'),
            FieldPanel('prescription_id'),
        ], heading=_('Healthcare Context')),
        MultiFieldPanel([
            FieldPanel('ip_address'),
            FieldPanel('user_agent'),
            FieldPanel('request_path'),
            FieldPanel('request_method'),
            FieldPanel('session_id'),
        ], heading=_('Request Context')),
        MultiFieldPanel([
            FieldPanel('old_values'),
            FieldPanel('new_values'),
            FieldPanel('changed_fields'),
        ], heading=_('Change Tracking')),
        FieldPanel('metadata'),
        FieldPanel('timestamp'),
    ]
    
    class Meta:
        verbose_name = _('Wagtail Audit Log')
        verbose_name_plural = _('Wagtail Audit Logs')
        db_table = 'wagtail_audit_logs'
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['page', 'timestamp']),
            models.Index(fields=['patient_id', 'timestamp']),
            models.Index(fields=['medication_id', 'timestamp']),
            models.Index(fields=['prescription_id', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
        permissions = [
            ('view_audit_logs', _('Can view audit logs')),
            ('export_audit_logs', _('Can export audit logs')),
            ('delete_audit_logs', _('Can delete audit logs')),
            ('anonymize_audit_logs', _('Can anonymize audit logs')),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def save(self, *args, **kwargs):
        """Override save to add validation and automatic field population."""
        self.clean()
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate the audit log entry."""
        super().clean()
        
        # Validate IP address
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
        
        # Validate healthcare IDs
        if self.patient_id and len(self.patient_id) > 100:
            raise ValidationError({
                'patient_id': _('Patient ID must be 100 characters or less.')
            })
        
        if self.medication_id and len(self.medication_id) > 100:
            raise ValidationError({
                'medication_id': _('Medication ID must be 100 characters or less.')
            })
        
        if self.prescription_id and len(self.prescription_id) > 100:
            raise ValidationError({
                'prescription_id': _('Prescription ID must be 100 characters or less.')
            })
    
    @property
    def is_critical(self) -> bool:
        """Check if this is a critical audit event."""
        return self.severity == self.Severity.CRITICAL
    
    @property
    def involves_patient_data(self) -> bool:
        """Check if this event involves patient data."""
        return bool(self.patient_id or 'patient' in self.event_type.lower())
    
    @property
    def involves_medication_data(self) -> bool:
        """Check if this event involves medication data."""
        return bool(self.medication_id or 'medication' in self.event_type.lower())
    
    @property
    def involves_prescription_data(self) -> bool:
        """Check if this event involves prescription data."""
        return bool(self.prescription_id or 'prescription' in self.event_type.lower())
    
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
        context = []
        if self.patient_id:
            context.append(f"Patient: {self.patient_id}")
        if self.medication_id:
            context.append(f"Medication: {self.medication_id}")
        if self.prescription_id:
            context.append(f"Prescription: {self.prescription_id}")
        
        context_str = " - ".join(context) if context else ""
        return f"{self.severity} - {context_str} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    def get_absolute_url(self):
        """Return the URL for this audit log entry."""
        return f"/admin/security/wagtailauditlog/{self.id}/"
    
    def get_search_display_title(self):
        """Return the title to display in search results."""
        return f"{self.get_event_type_display()} - {self.severity}"
    
    def get_search_description(self):
        """Return the description to display in search results."""
        return self.description[:200] + "..." if len(self.description) > 200 else self.description
    
    def get_search_url(self, request=None):
        """Return the URL for this audit log in search results."""
        return self.get_absolute_url()
    
    def get_search_meta(self):
        """Return additional metadata for search results."""
        return {
            'event_type': self.get_event_type_display(),
            'severity': self.get_severity_display(),
            'timestamp': self.timestamp.isoformat(),
            'patient_id': self.patient_id,
            'medication_id': self.medication_id,
            'prescription_id': self.prescription_id,
        }


class WagtailAuditLogger:
    """
    Wagtail 7.0.2 enhanced audit logger for content changes and access.
    
    This class provides methods to log various types of audit events
    with healthcare-specific context and HIPAA compliance features.
    """
    
    def __init__(self, request=None):
        self.request = request
        self.user = getattr(request, 'user', None) if request else None
    
    def log_event(self, event_type: str, description: str, **kwargs) -> WagtailAuditLog:
        """
        Log an audit event with the given parameters.
        
        Args:
            event_type: Type of audit event
            description: Description of the event
            **kwargs: Additional parameters for the audit log
            
        Returns:
            Created WagtailAuditLog instance
        """
        # Extract request information
        request_data = self._extract_request_data()
        
        # Create audit log entry
        audit_log = WagtailAuditLog(
            user=self.user,
            event_type=event_type,
            description=description,
            **request_data,
            **kwargs
        )
        
        audit_log.save()
        
        # Log to Django logger for debugging
        logger.info(f"Audit log created: {event_type} - {description}")
        
        return audit_log
    
    def log_page_event(self, event_type: str, page: Page, description: str, **kwargs) -> WagtailAuditLog:
        """
        Log a page-related audit event.
        
        Args:
            event_type: Type of audit event
            page: Page associated with the event
            description: Description of the event
            **kwargs: Additional parameters
            
        Returns:
            Created WagtailAuditLog instance
        """
        return self.log_event(
            event_type=event_type,
            description=description,
            page=page,
            content_type=ContentType.objects.get_for_model(page),
            object_id=page.id,
            object_repr=str(page),
            site=page.get_site(),
            **kwargs
        )
    
    def log_content_change(self, obj: Any, old_values: Dict = None, 
                          new_values: Dict = None, changed_fields: List = None,
                          description: str = None, **kwargs) -> WagtailAuditLog:
        """
        Log a content change event.
        
        Args:
            obj: Object that was changed
            old_values: Previous values
            new_values: New values
            changed_fields: List of changed fields
            description: Description of the change
            **kwargs: Additional parameters
            
        Returns:
            Created WagtailAuditLog instance
        """
        if description is None:
            description = f"Content changed: {obj}"
        
        return self.log_event(
            event_type=WagtailAuditLog.EventType.PAGE_MODIFIED,
            description=description,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.id,
            object_repr=str(obj),
            old_values=old_values or {},
            new_values=new_values or {},
            changed_fields=changed_fields or [],
            **kwargs
        )
    
    def log_patient_data_access(self, patient_id: str, description: str, **kwargs) -> WagtailAuditLog:
        """
        Log patient data access event.
        
        Args:
            patient_id: ID of the patient whose data was accessed
            description: Description of the access
            **kwargs: Additional parameters
            
        Returns:
            Created WagtailAuditLog instance
        """
        return self.log_event(
            event_type=WagtailAuditLog.EventType.PATIENT_DATA_ACCESSED,
            description=description,
            patient_id=patient_id,
            severity=WagtailAuditLog.Severity.HIGH,
            **kwargs
        )
    
    def log_medication_data_change(self, medication_id: str, description: str, 
                                  old_values: Dict = None, new_values: Dict = None,
                                  **kwargs) -> WagtailAuditLog:
        """
        Log medication data change event.
        
        Args:
            medication_id: ID of the medication
            description: Description of the change
            old_values: Previous values
            new_values: New values
            **kwargs: Additional parameters
            
        Returns:
            Created WagtailAuditLog instance
        """
        return self.log_event(
            event_type=WagtailAuditLog.EventType.MEDICATION_DATA_MODIFIED,
            description=description,
            medication_id=medication_id,
            severity=WagtailAuditLog.Severity.HIGH,
            old_values=old_values or {},
            new_values=new_values or {},
            **kwargs
        )
    
    def log_prescription_event(self, event_type: str, prescription_id: str, 
                              description: str, **kwargs) -> WagtailAuditLog:
        """
        Log prescription-related event.
        
        Args:
            event_type: Type of prescription event
            prescription_id: ID of the prescription
            description: Description of the event
            **kwargs: Additional parameters
            
        Returns:
            Created WagtailAuditLog instance
        """
        return self.log_event(
            event_type=event_type,
            description=description,
            prescription_id=prescription_id,
            severity=WagtailAuditLog.Severity.HIGH,
            **kwargs
        )
    
    def _extract_request_data(self) -> Dict:
        """Extract request data for audit logging."""
        if not self.request:
            return {}
        
        return {
            'ip_address': self._get_client_ip(),
            'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
            'request_path': self.request.path,
            'request_method': self.request.method,
            'session_id': self.request.session.session_key if self.request.session else '',
        }
    
    def _get_client_ip(self) -> str:
        """Get the client IP address from the request."""
        if not self.request:
            return ''
        
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        
        return ip or ''


# Wagtail 7.0.2: Permission policy for enhanced access control
WagtailAuditLog.permission_policy = ModelPermissionPolicy(WagtailAuditLog)


# Utility functions for audit logging
def get_audit_logger(request=None) -> WagtailAuditLogger:
    """
    Get an audit logger instance.
    
    Args:
        request: Django request object
        
    Returns:
        WagtailAuditLogger instance
    """
    return WagtailAuditLogger(request)


def log_wagtail_event(event_type: str, description: str, request=None, **kwargs) -> WagtailAuditLog:
    """
    Log a Wagtail audit event.
    
    Args:
        event_type: Type of audit event
        description: Description of the event
        request: Django request object
        **kwargs: Additional parameters
        
    Returns:
        Created WagtailAuditLog instance
    """
    logger = get_audit_logger(request)
    return logger.log_event(event_type, description, **kwargs)


def log_page_change(page: Page, description: str, request=None, **kwargs) -> WagtailAuditLog:
    """
    Log a page change event.
    
    Args:
        page: Page that was changed
        description: Description of the change
        request: Django request object
        **kwargs: Additional parameters
        
    Returns:
        Created WagtailAuditLog instance
    """
    logger = get_audit_logger(request)
    return logger.log_page_event(
        WagtailAuditLog.EventType.PAGE_MODIFIED,
        page,
        description,
        **kwargs
    )


def log_patient_access(patient_id: str, description: str, request=None, **kwargs) -> WagtailAuditLog:
    """
    Log patient data access event.
    
    Args:
        patient_id: ID of the patient
        description: Description of the access
        request: Django request object
        **kwargs: Additional parameters
        
    Returns:
        Created WagtailAuditLog instance
    """
    logger = get_audit_logger(request)
    return logger.log_patient_data_access(patient_id, description, **kwargs)


def log_medication_change(medication_id: str, description: str, request=None, **kwargs) -> WagtailAuditLog:
    """
    Log medication data change event.
    
    Args:
        medication_id: ID of the medication
        description: Description of the change
        request: Django request object
        **kwargs: Additional parameters
        
    Returns:
        Created WagtailAuditLog instance
    """
    logger = get_audit_logger(request)
    return logger.log_medication_data_change(medication_id, description, **kwargs) 