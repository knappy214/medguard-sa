"""
Audit trail system for tracking all medication changes.

This module provides comprehensive audit logging for HIPAA compliance,
tracking all access, modifications, and deletions of medical data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    """
    Comprehensive audit log for tracking all data access and modifications.
    
    This model stores detailed audit trails for HIPAA compliance and
    South African POPIA regulations.
    """
    
    # Action types
    class ActionType(models.TextChoices):
        CREATE = 'create', _('Create')
        READ = 'read', _('Read')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        EXPORT = 'export', _('Export')
        IMPORT = 'import', _('Import')
        LOGIN = 'login', _('Login')
        LOGIN_SUCCESS = 'login_success', _('Login Success')
        LOGIN_FAILURE = 'login_failure', _('Login Failure')
        LOGOUT = 'logout', _('Logout')
        ACCESS_DENIED = 'access_denied', _('Access Denied')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        PERMISSION_CHANGE = 'permission_change', _('Permission Change')
        DATA_ANONYMIZATION = 'data_anonymization', _('Data Anonymization')
        BREACH_ATTEMPT = 'breach_attempt', _('Breach Attempt')
        SECURITY_EVENT = 'security_event', _('Security Event')
    
    # Severity levels
    class Severity(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # User performing the action
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text=_('User who performed the action')
    )
    
    # Action details
    action = models.CharField(
        max_length=50,
        choices=ActionType.choices,
        help_text=_('Type of action performed')
    )
    
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        default=Severity.LOW,
        help_text=_('Severity level of the action')
    )
    
    # Object being acted upon
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=_('Content type of the object')
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of the object')
    )
    
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Object details
    object_repr = models.CharField(
        max_length=200,
        help_text=_('String representation of the object')
    )
    
    # Change details
    changes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('JSON representation of changes made')
    )
    
    previous_values = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Previous values before changes')
    )
    
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('New values after changes')
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
    
    session_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text=_('Session ID')
    )
    
    # Additional context
    description = models.TextField(
        blank=True,
        help_text=_('Human-readable description of the action')
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional metadata about the action')
    )
    
    # Timestamps
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the action occurred')
    )
    
    # Retention and compliance
    retention_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Date until which this log should be retained')
    )
    
    is_anonymized = models.BooleanField(
        default=False,
        help_text=_('Whether this log entry has been anonymized')
    )
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.object_repr} ({self.timestamp})"
    
    def save(self, *args, **kwargs):
        """Override save to set retention date and validate data."""
        if not self.retention_date:
            # Set retention date to 7 years for HIPAA compliance
            self.retention_date = timezone.now() + timezone.timedelta(days=2555)
        
        super().save(*args, **kwargs)
    
    @property
    def is_sensitive_action(self) -> bool:
        """Check if this action involves sensitive data."""
        sensitive_actions = [
            self.ActionType.READ,
            self.ActionType.UPDATE,
            self.ActionType.DELETE,
            self.ActionType.EXPORT,
        ]
        return self.action in sensitive_actions
    
    @property
    def requires_review(self) -> bool:
        """Check if this action requires manual review."""
        return self.severity in [self.Severity.HIGH, self.Severity.CRITICAL]


class AuditLogger:
    """
    Audit logger for creating audit trail entries.
    
    This class provides methods for logging various types of actions
    with appropriate context and metadata.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_action(
        self,
        user: Optional[User],
        action: str,
        obj: Optional[models.Model] = None,
        changes: Optional[Dict] = None,
        previous_values: Optional[Dict] = None,
        new_values: Optional[Dict] = None,
        description: str = "",
        severity: str = AuditLog.Severity.LOW,
        request=None,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """
        Log an action to the audit trail.
        
        Args:
            user: User performing the action
            action: Type of action (from AuditLog.ActionType)
            obj: Object being acted upon
            changes: Dictionary of changes made
            previous_values: Previous values before changes
            new_values: New values after changes
            description: Human-readable description
            severity: Severity level
            request: Django request object for context
            metadata: Additional metadata
            
        Returns:
            Created AuditLog instance
        """
        try:
            # Extract request information
            ip_address = None
            user_agent = ""
            request_path = ""
            request_method = ""
            session_id = ""
            
            if request:
                ip_address = self._get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                request_path = request.path
                request_method = request.method
                session_id = getattr(request, 'session', None)
                session_id = session_id.session_key if session_id else ""
            
            # Create audit log entry
            audit_log = AuditLog.objects.create(
                user=user,
                action=action,
                severity=severity,
                content_type=ContentType.objects.get_for_model(obj) if obj else None,
                object_id=obj.pk if obj else None,
                object_repr=str(obj) if obj else "",
                changes=changes or {},
                previous_values=previous_values or {},
                new_values=new_values or {},
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request_path,
                request_method=request_method,
                session_id=session_id,
                description=description,
                metadata=metadata or {},
            )
            
            # Log to application logger as well
            self.logger.info(
                f"Audit: {user} performed {action} on {obj} - {description}",
                extra={
                    'audit_log_id': audit_log.id,
                    'user_id': user.id if user else None,
                    'action': action,
                    'object_id': obj.pk if obj else None,
                    'severity': severity,
                }
            )
            
            return audit_log
            
        except Exception as e:
            self.logger.error(f"Failed to create audit log: {str(e)}")
            raise
    
    def log_medication_access(
        self,
        user: User,
        medication: models.Model,
        action: str,
        request=None,
        description: str = ""
    ) -> AuditLog:
        """
        Log medication-specific access.
        
        Args:
            user: User accessing the medication
            medication: Medication being accessed
            action: Type of action
            request: Django request object
            description: Description of the access
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            user=user,
            action=action,
            obj=medication,
            description=description,
            severity=AuditLog.Severity.MEDIUM,
            request=request,
            metadata={'medication_type': 'medication_access'}
        )
    
    def log_patient_data_access(
        self,
        user: User,
        patient: models.Model,
        action: str,
        request=None,
        description: str = ""
    ) -> AuditLog:
        """
        Log patient data access (high severity).
        
        Args:
            user: User accessing patient data
            patient: Patient whose data is being accessed
            action: Type of action
            request: Django request object
            description: Description of the access
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            user=user,
            action=action,
            obj=patient,
            description=description,
            severity=AuditLog.Severity.HIGH,
            request=request,
            metadata={'data_type': 'patient_data'}
        )
    
    def log_security_event(
        self,
        user: Optional[User],
        action: str,
        description: str,
        severity: str = AuditLog.Severity.HIGH,
        request=None,
        metadata: Optional[Dict] = None
    ) -> AuditLog:
        """
        Log security-related events.
        
        Args:
            user: User involved in the security event
            action: Type of security action
            description: Description of the security event
            severity: Severity level
            request: Django request object
            metadata: Additional metadata
            
        Returns:
            Created AuditLog instance
        """
        return self.log_action(
            user=user,
            action=action,
            description=description,
            severity=severity,
            request=request,
            metadata=metadata or {'event_type': 'security'}
        )
    
    def _get_client_ip(self, request) -> Optional[str]:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# Global audit logger instance
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_audit_event(
    user: Optional[User],
    action: str,
    obj: Optional[models.Model] = None,
    description: str = "",
    severity: str = AuditLog.Severity.LOW,
    request=None,
    **kwargs
) -> AuditLog:
    """
    Convenience function for logging audit events.
    
    Args:
        user: User performing the action
        action: Type of action
        obj: Object being acted upon
        description: Description of the action
        severity: Severity level
        request: Django request object
        **kwargs: Additional arguments for AuditLogger.log_action
        
    Returns:
        Created AuditLog instance
    """
    audit_logger = get_audit_logger()
    return audit_logger.log_action(
        user=user,
        action=action,
        obj=obj,
        description=description,
        severity=severity,
        request=request,
        **kwargs
    )


class AuditMiddleware:
    """
    Django middleware for automatic audit logging.
    
    This middleware automatically logs certain types of requests
    for audit trail purposes.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.audit_logger = get_audit_logger()
    
    def __call__(self, request):
        # Log the request
        self._log_request(request)
        
        response = self.get_response(request)
        
        # Log the response if needed
        self._log_response(request, response)
        
        return response
    
    def _log_request(self, request):
        """Log incoming request details."""
        if request.user.is_authenticated:
            # Log access to sensitive endpoints
            sensitive_paths = [
                '/api/medications/',
                '/api/patients/',
                '/admin/medications/',
                '/admin/users/',
            ]
            
            for path in sensitive_paths:
                if path in request.path:
                    self.audit_logger.log_action(
                        user=request.user,
                        action=AuditLog.ActionType.READ,
                        description=f"Access to sensitive endpoint: {request.path}",
                        severity=AuditLog.Severity.MEDIUM,
                        request=request,
                        metadata={'endpoint_type': 'sensitive'}
                    )
                    break
    
    def _log_response(self, request, response):
        """Log response details if needed."""
        if request.user.is_authenticated and response.status_code >= 400:
            self.audit_logger.log_action(
                user=request.user,
                action=AuditLog.ActionType.ACCESS_DENIED,
                description=f"HTTP {response.status_code} error for {request.path}",
                severity=AuditLog.Severity.MEDIUM,
                request=request,
                metadata={'status_code': response.status_code}
            ) 