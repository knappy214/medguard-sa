"""
Enhanced user session management for medical data security.

This module implements Wagtail 7.0.2's enhanced session management features
specifically designed for healthcare applications with HIPAA compliance.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.contrib.sessions.backends.db import SessionStore
from django.core.cache import cache
from django.db import models, transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.permission_policies import ModelPermissionPolicy

# Import SecurityEvent to avoid circular imports
from django.apps import apps

logger = logging.getLogger(__name__)
User = get_user_model()


class MedicalSession(models.Model):
    """
    Enhanced session model for medical data access tracking.
    
    This model extends Django's session management with healthcare-specific
    features including HIPAA compliance tracking, session validation,
    and medical data access logging.
    """
    
    # Session states for medical data access
    class SessionState(models.TextChoices):
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        EXPIRED = 'expired', _('Expired')
        TERMINATED = 'terminated', _('Terminated')
        UNDER_REVIEW = 'under_review', _('Under Review')
    
    # Medical data access levels
    class AccessLevel(models.TextChoices):
        NONE = 'none', _('No Medical Data Access')
        READ_ONLY = 'read_only', _('Read-Only Medical Data')
        LIMITED_WRITE = 'limited_write', _('Limited Write Access')
        FULL_ACCESS = 'full_access', _('Full Medical Data Access')
        EMERGENCY = 'emergency', _('Emergency Access')
    
    # Core session fields
    session_key = models.CharField(
        max_length=40,
        unique=True,
        db_index=True,
        help_text=_('Django session key')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medical_sessions',
        help_text=_('User associated with this session')
    )
    
    # Session state and access control
    state = models.CharField(
        max_length=20,
        choices=SessionState.choices,
        default=SessionState.ACTIVE,
        help_text=_('Current state of the medical session')
    )
    
    access_level = models.CharField(
        max_length=20,
        choices=AccessLevel.choices,
        default=AccessLevel.NONE,
        help_text=_('Medical data access level for this session')
    )
    
    # HIPAA compliance tracking
    hipaa_consent_given = models.BooleanField(
        default=False,
        help_text=_('Whether HIPAA consent has been given for this session')
    )
    
    consent_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When HIPAA consent was given')
    )
    
    consent_ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address when consent was given')
    )
    
    # Session security features
    device_fingerprint = models.TextField(
        blank=True,
        help_text=_('Device fingerprint for session validation')
    )
    
    location_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Geographic location data for session validation')
    )
    
    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text=_('Security risk score for this session (0-100)')
    )
    
    # Medical data access tracking
    patient_records_accessed = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of patient records accessed in this session')
    )
    
    medical_actions_performed = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of medical actions performed in this session')
    )
    
    # Session lifecycle
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the session was created')
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        help_text=_('Last activity timestamp')
    )
    
    expires_at = models.DateTimeField(
        help_text=_('When the session expires')
    )
    
    terminated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the session was terminated')
    )
    
    terminated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='terminated_sessions',
        help_text=_('User who terminated this session')
    )
    
    termination_reason = models.TextField(
        blank=True,
        help_text=_('Reason for session termination')
    )
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        FieldPanel('session_key'),
        FieldPanel('user'),
        FieldPanel('state'),
        FieldPanel('access_level'),
        MultiFieldPanel([
            FieldPanel('hipaa_consent_given'),
            FieldPanel('consent_timestamp'),
            FieldPanel('consent_ip_address'),
        ], heading=_('HIPAA Compliance')),
        MultiFieldPanel([
            FieldPanel('device_fingerprint'),
            FieldPanel('location_data'),
            FieldPanel('risk_score'),
        ], heading=_('Security Features')),
        MultiFieldPanel([
            FieldPanel('patient_records_accessed'),
            FieldPanel('medical_actions_performed'),
        ], heading=_('Medical Data Access')),
        MultiFieldPanel([
            FieldPanel('created_at'),
            FieldPanel('last_activity'),
            FieldPanel('expires_at'),
            FieldPanel('terminated_at'),
            FieldPanel('terminated_by'),
            FieldPanel('termination_reason'),
        ], heading=_('Session Lifecycle')),
    ]
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('session_key', boost=2.0),
        index.SearchField('state', boost=1.5),
        index.SearchField('access_level', boost=1.5),
        index.SearchField('device_fingerprint', boost=1.0),
        index.SearchField('termination_reason', boost=1.0),
        
        # Related fields
        index.RelatedFields('user', [
            index.SearchField('username', boost=1.5),
            index.SearchField('email', boost=1.0),
        ]),
        index.RelatedFields('terminated_by', [
            index.SearchField('username', boost=1.0),
        ]),
        
        # Filter fields
        index.FilterField('state'),
        index.FilterField('access_level'),
        index.FilterField('hipaa_consent_given'),
        index.FilterField('user'),
        index.FilterField('created_at'),
        index.FilterField('expires_at'),
    ]
    
    class Meta:
        verbose_name = _('Medical Session')
        verbose_name_plural = _('Medical Sessions')
        db_table = 'medical_sessions'
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user', 'state']),
            models.Index(fields=['state', 'expires_at']),
            models.Index(fields=['access_level', 'state']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['risk_score']),
        ]
        ordering = ['-last_activity']
        permissions = [
            ('view_medical_session', _('Can view medical session')),
            ('change_medical_session', _('Can change medical session')),
            ('delete_medical_session', _('Can delete medical session')),
            ('terminate_medical_session', _('Can terminate medical session')),
            ('audit_medical_session', _('Can audit medical session')),
        ]
    
    def __str__(self):
        return f"Medical Session {self.session_key} - {self.user.username} ({self.state})"
    
    def clean(self):
        """Validate session data."""
        super().clean()
        
        # Validate expiration time
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_('Session expiration time must be in the future'))
        
        # Validate risk score
        if self.risk_score < 0 or self.risk_score > 100:
            raise ValidationError(_('Risk score must be between 0 and 100'))
        
        # Validate HIPAA consent
        if self.hipaa_consent_given and not self.consent_timestamp:
            self.consent_timestamp = timezone.now()
    
    def save(self, *args, **kwargs):
        """Save with additional validation and logging."""
        self.clean()
        
        # Set default expiration if not provided
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=settings.MEDICAL_SESSION_TIMEOUT)
        
        # Log session state changes
        if self.pk:
            old_instance = MedicalSession.objects.get(pk=self.pk)
            if old_instance.state != self.state:
                SecurityEvent = apps.get_model('security', 'SecurityEvent')
                SecurityEvent.objects.create(
                    user=self.user,
                    event_type=SecurityEvent.EventType.USER_MODIFICATION,
                    severity=SecurityEvent.Severity.MEDIUM,
                    description=f"Medical session state changed from {old_instance.state} to {self.state}",
                    metadata={
                        'session_key': self.session_key,
                        'old_state': old_instance.state,
                        'new_state': self.state,
                    }
                )
        
        super().save(*args, **kwargs)
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active."""
        return (
            self.state == self.SessionState.ACTIVE and
            self.expires_at > timezone.now() and
            not self.is_suspended
        )
    
    @property
    def is_suspended(self) -> bool:
        """Check if session is suspended."""
        return self.state == self.SessionState.SUSPENDED
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return self.expires_at <= timezone.now()
    
    @property
    def time_until_expiry(self) -> timedelta:
        """Get time remaining until session expires."""
        return self.expires_at - timezone.now()
    
    @property
    def requires_hipaa_consent(self) -> bool:
        """Check if session requires HIPAA consent."""
        return (
            self.access_level in [self.AccessLevel.READ_ONLY, self.AccessLevel.LIMITED_WRITE, 
                                 self.AccessLevel.FULL_ACCESS] and
            not self.hipaa_consent_given
        )
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = timezone.now()
        self.save(update_fields=['last_activity'])
    
    def suspend_session(self, reason: str = "", suspended_by: Optional[User] = None):
        """Suspend the session for security reasons."""
        self.state = self.SessionState.SUSPENDED
        self.termination_reason = f"Session suspended: {reason}"
        if suspended_by:
            self.terminated_by = suspended_by
        self.save()
        
        # Log security event
        SecurityEvent = apps.get_model('security', 'SecurityEvent')
        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.SECURITY_ALERT,
            severity=SecurityEvent.Severity.HIGH,
            description=f"Medical session suspended: {reason}",
            metadata={
                'session_key': self.session_key,
                'reason': reason,
                'suspended_by': suspended_by.username if suspended_by else None,
            }
        )
    
    def terminate_session(self, reason: str = "", terminated_by: Optional[User] = None):
        """Terminate the session."""
        self.state = self.SessionState.TERMINATED
        self.terminated_at = timezone.now()
        self.termination_reason = reason
        if terminated_by:
            self.terminated_by = terminated_by
        self.save()
        
        # Log security event
        SecurityEvent = apps.get_model('security', 'SecurityEvent')
        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.USER_MODIFICATION,
            severity=SecurityEvent.Severity.MEDIUM,
            description=f"Medical session terminated: {reason}",
            metadata={
                'session_key': self.session_key,
                'reason': reason,
                'terminated_by': terminated_by.username if terminated_by else None,
            }
        )
    
    def give_hipaa_consent(self, ip_address: str = ""):
        """Record HIPAA consent for this session."""
        self.hipaa_consent_given = True
        self.consent_timestamp = timezone.now()
        self.consent_ip_address = ip_address
        self.save()
        
        # Log consent event
        SecurityEvent = apps.get_model('security', 'SecurityEvent')
        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.DATA_ACCESS,
            severity=SecurityEvent.Severity.LOW,
            description="HIPAA consent given for medical session",
            ip_address=ip_address,
            metadata={
                'session_key': self.session_key,
                'consent_timestamp': self.consent_timestamp.isoformat(),
            }
        )
    
    def record_patient_access(self, patient_id: str, action: str, details: Dict[str, Any] = None):
        """Record access to patient data."""
        access_record = {
            'patient_id': patient_id,
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'details': details or {},
        }
        
        self.patient_records_accessed.append(access_record)
        self.save(update_fields=['patient_records_accessed'])
        
        # Log patient data access
        SecurityEvent = apps.get_model('security', 'SecurityEvent')
        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.DATA_ACCESS,
            severity=SecurityEvent.Severity.MEDIUM,
            description=f"Patient data accessed: {action}",
            metadata={
                'session_key': self.session_key,
                'patient_id': patient_id,
                'action': action,
                'details': details,
            }
        )
    
    def record_medical_action(self, action: str, details: Dict[str, Any] = None):
        """Record medical actions performed in this session."""
        action_record = {
            'action': action,
            'timestamp': timezone.now().isoformat(),
            'details': details or {},
        }
        
        self.medical_actions_performed.append(action_record)
        self.save(update_fields=['medical_actions_performed'])
        
        # Log medical action
        SecurityEvent = apps.get_model('security', 'SecurityEvent')
        SecurityEvent.objects.create(
            user=self.user,
            event_type=SecurityEvent.EventType.DATA_MODIFICATION,
            severity=SecurityEvent.Severity.HIGH,
            description=f"Medical action performed: {action}",
            metadata={
                'session_key': self.session_key,
                'action': action,
                'details': details,
            }
        )
    
    def update_risk_score(self, new_score: float, reason: str = ""):
        """Update session risk score."""
        old_score = self.risk_score
        self.risk_score = new_score
        self.save(update_fields=['risk_score'])
        
        # Log significant risk score changes
        if abs(new_score - old_score) >= 10:
            SecurityEvent = apps.get_model('security', 'SecurityEvent')
            SecurityEvent.objects.create(
                user=self.user,
                event_type=SecurityEvent.EventType.SECURITY_ALERT,
                severity=SecurityEvent.Severity.MEDIUM if new_score > 50 else SecurityEvent.Severity.LOW,
                description=f"Session risk score changed from {old_score} to {new_score}: {reason}",
                metadata={
                    'session_key': self.session_key,
                    'old_score': old_score,
                    'new_score': new_score,
                    'reason': reason,
                }
            )


class MedicalSessionManager:
    """
    Manager for medical session operations with enhanced security features.
    """
    
    @staticmethod
    def create_session(user: User, request: HttpRequest, access_level: str = MedicalSession.AccessLevel.NONE) -> MedicalSession:
        """Create a new medical session with enhanced security."""
        session_store = SessionStore()
        session_store.create()
        
        # Create medical session
        medical_session = MedicalSession.objects.create(
            session_key=session_store.session_key,
            user=user,
            access_level=access_level,
            device_fingerprint=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timedelta(hours=settings.MEDICAL_SESSION_TIMEOUT),
        )
        
        # Set session data
        session_store['medical_session_id'] = medical_session.id
        session_store['user_id'] = user.id
        session_store['access_level'] = access_level
        session_store['created_at'] = medical_session.created_at.isoformat()
        session_store.save()
        
        # Log session creation
        SecurityEvent = apps.get_model('security', 'SecurityEvent')
        SecurityEvent.objects.create(
            user=user,
            event_type=SecurityEvent.EventType.USER_CREATION,
            severity=SecurityEvent.Severity.LOW,
            description=f"Medical session created with access level: {access_level}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
            metadata={
                'session_key': session_store.session_key,
                'access_level': access_level,
            }
        )
        
        return medical_session
    
    @staticmethod
    def get_session(session_key: str) -> Optional[MedicalSession]:
        """Get medical session by session key."""
        try:
            return MedicalSession.objects.get(session_key=session_key)
        except MedicalSession.DoesNotExist:
            return None
    
    @staticmethod
    def validate_session(session_key: str, request: HttpRequest) -> bool:
        """Validate session security and integrity."""
        medical_session = MedicalSessionManager.get_session(session_key)
        if not medical_session:
            return False
        
        # Check if session is active
        if not medical_session.is_active:
            return False
        
        # Validate device fingerprint
        current_fingerprint = request.META.get('HTTP_USER_AGENT', '')
        if medical_session.device_fingerprint and medical_session.device_fingerprint != current_fingerprint:
            medical_session.suspend_session("Device fingerprint mismatch")
            return False
        
        # Update activity
        medical_session.update_activity()
        
        return True
    
    @staticmethod
    def cleanup_expired_sessions():
        """Clean up expired medical sessions."""
        expired_sessions = MedicalSession.objects.filter(
            expires_at__lte=timezone.now(),
            state__in=[MedicalSession.SessionState.ACTIVE, MedicalSession.SessionState.SUSPENDED]
        )
        
        for session in expired_sessions:
            session.state = MedicalSession.SessionState.EXPIRED
            session.save()
            
            # Log cleanup
            SecurityEvent = apps.get_model('security', 'SecurityEvent')
            SecurityEvent.objects.create(
                user=session.user,
                event_type=SecurityEvent.EventType.SYSTEM_ERROR,
                severity=SecurityEvent.Severity.LOW,
                description="Medical session expired and cleaned up",
                metadata={
                    'session_key': session.session_key,
                    'expired_at': session.expires_at.isoformat(),
                }
            )
        
        return expired_sessions.count()
    
    @staticmethod
    def get_user_sessions(user: User) -> List[MedicalSession]:
        """Get all active sessions for a user."""
        return MedicalSession.objects.filter(
            user=user,
            state__in=[MedicalSession.SessionState.ACTIVE, MedicalSession.SessionState.SUSPENDED]
        ).order_by('-last_activity')
    
    @staticmethod
    def terminate_user_sessions(user: User, reason: str = "", terminated_by: Optional[User] = None):
        """Terminate all active sessions for a user."""
        active_sessions = MedicalSessionManager.get_user_sessions(user)
        
        for session in active_sessions:
            session.terminate_session(reason, terminated_by)
        
        return len(active_sessions) 