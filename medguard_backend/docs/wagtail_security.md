# Wagtail Security Guide for MedGuard SA Healthcare Platform

## Overview

This comprehensive security guide covers the implementation of healthcare-grade security measures in Wagtail 7.0.2 for the MedGuard SA platform. The security implementation ensures compliance with POPIA (Protection of Personal Information Act), HIPAA principles, and South African healthcare regulations.

## Security Architecture

### 1. Multi-Layer Security Model

```python
# security/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
import uuid

class SecurityAuditLog(models.Model):
    """Comprehensive audit logging for security events"""
    
    EVENT_TYPES = [
        ('login_success', _('Successful Login')),
        ('login_failure', _('Failed Login')),
        ('logout', _('Logout')),
        ('password_change', _('Password Change')),
        ('permission_change', _('Permission Change')),
        ('data_access', _('Data Access')),
        ('data_modification', _('Data Modification')),
        ('system_access', _('System Access')),
        ('security_violation', _('Security Violation')),
        ('export_data', _('Data Export')),
        ('print_data', _('Data Print')),
    ]
    
    SEVERITY_LEVELS = [
        ('info', _('Information')),
        ('warning', _('Warning')),
        ('critical', _('Critical')),
        ('emergency', _('Emergency')),
    ]
    
    event_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='info')
    
    # User and Session Information
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, blank=True)
    
    # Request Information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    
    # Event Details
    event_description = models.TextField()
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Patient Data Access (for HIPAA compliance)
    patient_accessed = models.ForeignKey(
        'users.Patient',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=_("Patient whose data was accessed")
    )
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Security Audit Log")
        verbose_name_plural = _("Security Audit Logs")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['patient_accessed', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_event_type_display()} - {self.user} - {self.timestamp}"

class SecurityRole(models.Model):
    """Healthcare-specific security roles"""
    
    ROLE_TYPES = [
        ('physician', _('Physician')),
        ('nurse', _('Nurse')),
        ('pharmacist', _('Pharmacist')),
        ('admin_staff', _('Administrative Staff')),
        ('patient', _('Patient')),
        ('system_admin', _('System Administrator')),
        ('security_officer', _('Security Officer')),
        ('audit_reviewer', _('Audit Reviewer')),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES)
    description = models.TextField()
    
    # Access Level
    access_level = models.PositiveIntegerField(
        default=1,
        help_text=_("Access level (1-10, higher = more access)")
    )
    
    # Permissions
    can_view_all_patients = models.BooleanField(default=False)
    can_modify_patient_data = models.BooleanField(default=False)
    can_prescribe_medications = models.BooleanField(default=False)
    can_access_audit_logs = models.BooleanField(default=False)
    can_export_data = models.BooleanField(default=False)
    can_manage_users = models.BooleanField(default=False)
    
    # Time-based access
    access_hours_start = models.TimeField(null=True, blank=True)
    access_hours_end = models.TimeField(null=True, blank=True)
    
    # Emergency access
    emergency_access_allowed = models.BooleanField(
        default=False,
        help_text=_("Allow emergency access outside normal hours")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Security Role")
        verbose_name_plural = _("Security Roles")
        ordering = ['name']
    
    def __str__(self):
        return self.name

class UserSecurityProfile(models.Model):
    """Extended security profile for users"""
    
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='security_profile'
    )
    
    security_role = models.ForeignKey(
        SecurityRole,
        on_delete=models.CASCADE,
        related_name='users'
    )
    
    # Authentication
    mfa_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Multi-Factor Authentication Enabled")
    )
    mfa_secret = models.CharField(max_length=32, blank=True)
    
    # Password Security
    password_expires_at = models.DateTimeField(null=True, blank=True)
    password_history = models.JSONField(
        default=list,
        help_text=_("Hashed previous passwords to prevent reuse")
    )
    
    # Account Security
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    last_password_change = models.DateTimeField(null=True, blank=True)
    last_successful_login = models.DateTimeField(null=True, blank=True)
    
    # Professional Credentials
    license_number = models.CharField(
        max_length=50,
        blank=True,
        help_text=_("Professional license number")
    )
    license_expiry = models.DateField(null=True, blank=True)
    
    # Access Control
    allowed_ip_addresses = models.JSONField(
        default=list,
        blank=True,
        help_text=_("List of allowed IP addresses (empty = all allowed)")
    )
    
    # Emergency Access
    emergency_access_code = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("Emergency access code for break-glass scenarios")
    )
    emergency_access_used = models.DateTimeField(null=True, blank=True)
    
    # Compliance
    privacy_training_completed = models.DateField(null=True, blank=True)
    security_training_completed = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("User Security Profile")
        verbose_name_plural = _("User Security Profiles")
    
    def __str__(self):
        return f"{self.user.username} - {self.security_role.name}"
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        from django.utils import timezone
        return (
            self.account_locked_until and
            self.account_locked_until > timezone.now()
        )
    
    def can_access_at_time(self, access_time=None):
        """Check if user can access system at given time"""
        from django.utils import timezone
        
        if not access_time:
            access_time = timezone.now().time()
        
        role = self.security_role
        if not role.access_hours_start or not role.access_hours_end:
            return True  # No time restrictions
        
        return role.access_hours_start <= access_time <= role.access_hours_end
```

### 2. Authentication and Authorization

```python
# security/authentication.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import pyotp
import logging

logger = logging.getLogger('medguard.security')
User = get_user_model()

class HealthcareAuthenticationBackend(BaseBackend):
    """Custom authentication backend for healthcare security"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Authenticate user with enhanced security checks"""
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Log failed authentication attempt
            SecurityAuditLog.objects.create(
                event_type='login_failure',
                severity='warning',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                event_description=f"Failed login attempt for unknown user: {username}"
            )
            return None
        
        # Check if account is locked
        if user.security_profile.is_account_locked():
            SecurityAuditLog.objects.create(
                event_type='login_failure',
                severity='warning',
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                event_description="Login attempt on locked account"
            )
            raise PermissionDenied(_("Account is temporarily locked"))
        
        # Check IP address restrictions
        if not self.check_ip_access(user, request):
            SecurityAuditLog.objects.create(
                event_type='security_violation',
                severity='critical',
                user=user,
                ip_address=self.get_client_ip(request),
                event_description="Login attempt from unauthorized IP address"
            )
            raise PermissionDenied(_("Access denied from this IP address"))
        
        # Check time-based access
        if not user.security_profile.can_access_at_time():
            SecurityAuditLog.objects.create(
                event_type='security_violation',
                severity='warning',
                user=user,
                ip_address=self.get_client_ip(request),
                event_description="Login attempt outside allowed hours"
            )
            raise PermissionDenied(_("Access denied outside allowed hours"))
        
        # Verify password
        if user.check_password(password):
            # Reset failed login attempts
            user.security_profile.failed_login_attempts = 0
            user.security_profile.last_successful_login = timezone.now()
            user.security_profile.save()
            
            # Log successful authentication
            SecurityAuditLog.objects.create(
                event_type='login_success',
                severity='info',
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                event_description="Successful login"
            )
            
            return user
        else:
            # Increment failed login attempts
            profile = user.security_profile
            profile.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts
            if profile.failed_login_attempts >= 5:
                profile.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)
            
            profile.save()
            
            # Log failed authentication
            SecurityAuditLog.objects.create(
                event_type='login_failure',
                severity='warning',
                user=user,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                event_description=f"Failed login attempt ({profile.failed_login_attempts}/5)"
            )
            
            return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_ip_access(self, user, request):
        """Check if user can access from this IP"""
        allowed_ips = user.security_profile.allowed_ip_addresses
        if not allowed_ips:  # Empty list means all IPs allowed
            return True
        
        client_ip = self.get_client_ip(request)
        return client_ip in allowed_ips

class MFAAuthenticationMixin:
    """Multi-Factor Authentication mixin"""
    
    def verify_mfa_token(self, user, token):
        """Verify MFA token"""
        if not user.security_profile.mfa_enabled:
            return True
        
        totp = pyotp.TOTP(user.security_profile.mfa_secret)
        return totp.verify(token, valid_window=1)
    
    def generate_mfa_secret(self):
        """Generate new MFA secret"""
        return pyotp.random_base32()
    
    def get_mfa_qr_code_url(self, user):
        """Get QR code URL for MFA setup"""
        totp = pyotp.TOTP(user.security_profile.mfa_secret)
        return totp.provisioning_uri(
            name=user.email,
            issuer_name="MedGuard SA"
        )
```

### 3. Data Encryption and Protection

```python
# security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.db import models
import base64
import os

class EncryptedField(models.TextField):
    """Custom field for encrypted data storage"""
    
    def __init__(self, *args, **kwargs):
        self.encryption_key = kwargs.pop('encryption_key', None)
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Encrypt value before saving to database"""
        if value is None:
            return value
        
        if isinstance(value, str):
            value = value.encode('utf-8')
        
        cipher = self.get_cipher()
        encrypted_value = cipher.encrypt(value)
        return base64.b64encode(encrypted_value).decode('utf-8')
    
    def from_db_value(self, value, expression, connection):
        """Decrypt value when loading from database"""
        if value is None:
            return value
        
        try:
            cipher = self.get_cipher()
            encrypted_data = base64.b64decode(value.encode('utf-8'))
            decrypted_value = cipher.decrypt(encrypted_data)
            return decrypted_value.decode('utf-8')
        except Exception:
            # Return original value if decryption fails
            return value
    
    def get_cipher(self):
        """Get encryption cipher"""
        key = self.encryption_key or settings.FIELD_ENCRYPTION_KEY
        return Fernet(key)

class DataEncryptionService:
    """Service for data encryption operations"""
    
    @staticmethod
    def generate_encryption_key():
        """Generate new encryption key"""
        return Fernet.generate_key()
    
    @staticmethod
    def encrypt_sensitive_data(data, key=None):
        """Encrypt sensitive healthcare data"""
        if not key:
            key = settings.FIELD_ENCRYPTION_KEY
        
        cipher = Fernet(key)
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        return cipher.encrypt(data)
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data, key=None):
        """Decrypt sensitive healthcare data"""
        if not key:
            key = settings.FIELD_ENCRYPTION_KEY
        
        cipher = Fernet(key)
        return cipher.decrypt(encrypted_data)
    
    @staticmethod
    def hash_sensitive_identifier(identifier):
        """Create one-way hash of sensitive identifier"""
        salt = settings.SECRET_KEY.encode('utf-8')
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(identifier.encode('utf-8')))
        return key.decode('utf-8')

# Example usage in models
class PatientRecord(models.Model):
    """Example model with encrypted fields"""
    
    # Regular fields
    patient_id = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Encrypted fields
    id_number = EncryptedField(help_text=_("Encrypted ID number"))
    medical_history = EncryptedField(help_text=_("Encrypted medical history"))
    
    class Meta:
        verbose_name = _("Patient Record")
        verbose_name_plural = _("Patient Records")
```

### 4. Session Security

```python
# security/sessions.py
from django.contrib.sessions.backends.db import SessionStore as DBStore
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
import json

class SecureSessionStore(DBStore):
    """Enhanced session store with security features"""
    
    def create_model_instance(self, data):
        """Create session with additional security data"""
        session_data = self.encode(data)
        
        # Add security metadata
        security_data = {
            'created_at': timezone.now().isoformat(),
            'ip_address': getattr(self, '_ip_address', None),
            'user_agent': getattr(self, '_user_agent', None),
            'last_activity': timezone.now().isoformat(),
        }
        
        # Combine session data with security metadata
        combined_data = {
            'session_data': session_data,
            'security_data': security_data
        }
        
        return Session(
            session_key=self._get_new_session_key(),
            session_data=self.encode(combined_data),
            expire_date=self.get_expiry_date()
        )
    
    def load(self):
        """Load session with security validation"""
        try:
            s = Session.objects.get(
                session_key=self.session_key,
                expire_date__gt=timezone.now()
            )
            
            # Decode combined data
            combined_data = self.decode(s.session_data)
            
            if isinstance(combined_data, dict) and 'session_data' in combined_data:
                # Extract session data
                session_data = self.decode(combined_data['session_data'])
                security_data = combined_data.get('security_data', {})
                
                # Validate session security
                if not self.validate_session_security(security_data):
                    self.delete()
                    return {}
                
                # Update last activity
                security_data['last_activity'] = timezone.now().isoformat()
                combined_data['security_data'] = security_data
                
                # Save updated data
                s.session_data = self.encode(combined_data)
                s.save()
                
                return session_data
            else:
                # Legacy session format
                return combined_data
                
        except (Session.DoesNotExist, ValueError):
            return {}
    
    def validate_session_security(self, security_data):
        """Validate session security constraints"""
        
        # Check session age
        created_at = security_data.get('created_at')
        if created_at:
            created_time = timezone.datetime.fromisoformat(created_at)
            max_age = timezone.timedelta(hours=8)  # 8-hour session limit
            
            if timezone.now() - created_time > max_age:
                return False
        
        # Check IP consistency (if configured)
        if settings.ENFORCE_IP_CONSISTENCY:
            stored_ip = security_data.get('ip_address')
            current_ip = getattr(self, '_ip_address', None)
            
            if stored_ip and current_ip and stored_ip != current_ip:
                return False
        
        return True
    
    def set_security_context(self, ip_address, user_agent):
        """Set security context for session"""
        self._ip_address = ip_address
        self._user_agent = user_agent

# Middleware for session security
class SessionSecurityMiddleware:
    """Middleware to enhance session security"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set security context
        if hasattr(request.session, 'set_security_context'):
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            request.session.set_security_context(ip_address, user_agent)
        
        # Check session timeout
        if request.user.is_authenticated:
            self.check_session_timeout(request)
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def check_session_timeout(self, request):
        """Check for session timeout"""
        last_activity = request.session.get('last_activity')
        if last_activity:
            last_time = timezone.datetime.fromisoformat(last_activity)
            timeout = timezone.timedelta(minutes=30)  # 30-minute timeout
            
            if timezone.now() - last_time > timeout:
                request.session.flush()
                # Redirect to login or show timeout message
```

### 5. Access Control and Permissions

```python
# security/permissions.py
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.utils import timezone
import functools

class HealthcarePermissionMixin:
    """Mixin for healthcare-specific permissions"""
    
    def has_patient_access(self, user, patient):
        """Check if user has access to specific patient"""
        
        # System administrators have access to all
        if user.security_profile.security_role.role_type == 'system_admin':
            return True
        
        # Patients can only access their own data
        if user.security_profile.security_role.role_type == 'patient':
            return hasattr(user, 'patient') and user.patient == patient
        
        # Healthcare providers need assigned relationship
        if user.security_profile.security_role.role_type in ['physician', 'nurse']:
            return patient.assigned_providers.filter(user=user).exists()
        
        # Pharmacists can access patients with active prescriptions
        if user.security_profile.security_role.role_type == 'pharmacist':
            return patient.prescriptions.filter(
                status='approved',
                expiry_date__gt=timezone.now()
            ).exists()
        
        return False
    
    def has_emergency_access(self, user):
        """Check emergency access privileges"""
        return (
            user.security_profile.security_role.emergency_access_allowed and
            user.security_profile.emergency_access_code
        )

def require_role(role_types):
    """Decorator to require specific role types"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied(_("Authentication required"))
            
            user_role = request.user.security_profile.security_role.role_type
            if user_role not in role_types:
                # Log unauthorized access attempt
                SecurityAuditLog.objects.create(
                    event_type='security_violation',
                    severity='warning',
                    user=request.user,
                    ip_address=get_client_ip(request),
                    event_description=f"Unauthorized access attempt to {view_func.__name__}"
                )
                raise PermissionDenied(_("Insufficient privileges"))
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def audit_data_access(patient_field='patient_id'):
    """Decorator to audit patient data access"""
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Get patient from request
            patient_id = kwargs.get(patient_field) or request.GET.get(patient_field)
            
            if patient_id:
                try:
                    from users.models import Patient
                    patient = Patient.objects.get(id=patient_id)
                    
                    # Log data access
                    SecurityAuditLog.objects.create(
                        event_type='data_access',
                        severity='info',
                        user=request.user,
                        patient_accessed=patient,
                        ip_address=get_client_ip(request),
                        request_method=request.method,
                        request_path=request.path,
                        event_description=f"Accessed patient data via {view_func.__name__}"
                    )
                except Patient.DoesNotExist:
                    pass
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

class PatientDataAccessMixin:
    """Mixin for views that access patient data"""
    
    def dispatch(self, request, *args, **kwargs):
        """Check patient data access permissions"""
        
        # Get patient from URL or request
        patient_id = kwargs.get('patient_id') or request.GET.get('patient_id')
        
        if patient_id:
            try:
                from users.models import Patient
                patient = Patient.objects.get(id=patient_id)
                
                # Check access permissions
                permission_mixin = HealthcarePermissionMixin()
                if not permission_mixin.has_patient_access(request.user, patient):
                    # Log unauthorized access attempt
                    SecurityAuditLog.objects.create(
                        event_type='security_violation',
                        severity='critical',
                        user=request.user,
                        patient_accessed=patient,
                        ip_address=get_client_ip(request),
                        event_description="Unauthorized patient data access attempt"
                    )
                    raise PermissionDenied(_("Access denied to patient data"))
                
                # Store patient in request for later use
                request.patient = patient
                
            except Patient.DoesNotExist:
                raise Http404(_("Patient not found"))
        
        return super().dispatch(request, *args, **kwargs)

def get_client_ip(request):
    """Utility function to get client IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

### 6. Security Middleware

```python
# security/middleware.py
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.conf import settings
import re

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to all responses"""
    
    def process_response(self, request, response):
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        # HSTS for HTTPS
        if request.is_secure():
            response['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware for security"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limits = {
            'login': {'requests': 5, 'window': 300},  # 5 requests per 5 minutes
            'api': {'requests': 100, 'window': 3600},  # 100 requests per hour
            'default': {'requests': 1000, 'window': 3600},  # 1000 requests per hour
        }
    
    def process_request(self, request):
        # Determine rate limit type
        if '/login' in request.path:
            limit_type = 'login'
        elif '/api/' in request.path:
            limit_type = 'api'
        else:
            limit_type = 'default'
        
        # Check rate limit
        if self.is_rate_limited(request, limit_type):
            # Log rate limit violation
            SecurityAuditLog.objects.create(
                event_type='security_violation',
                severity='warning',
                user=request.user if request.user.is_authenticated else None,
                ip_address=get_client_ip(request),
                event_description=f"Rate limit exceeded for {limit_type}"
            )
            return HttpResponseForbidden("Rate limit exceeded")
        
        return None
    
    def is_rate_limited(self, request, limit_type):
        """Check if request should be rate limited"""
        # Implementation would use cache (Redis) to track requests
        # This is a simplified version
        return False  # Placeholder

class IPWhitelistMiddleware(MiddlewareMixin):
    """IP whitelist middleware for admin access"""
    
    def process_request(self, request):
        # Only apply to admin paths
        if not request.path.startswith('/admin/'):
            return None
        
        client_ip = get_client_ip(request)
        allowed_ips = getattr(settings, 'ADMIN_ALLOWED_IPS', [])
        
        if allowed_ips and client_ip not in allowed_ips:
            # Log unauthorized admin access attempt
            SecurityAuditLog.objects.create(
                event_type='security_violation',
                severity='critical',
                ip_address=client_ip,
                event_description=f"Unauthorized admin access attempt from {client_ip}"
            )
            return HttpResponseForbidden("Access denied")
        
        return None

class DataLeakPreventionMiddleware(MiddlewareMixin):
    """Prevent data leakage through error messages"""
    
    def process_exception(self, request, exception):
        # In production, log detailed error but return generic message
        if not settings.DEBUG:
            # Log the actual exception
            SecurityAuditLog.objects.create(
                event_type='system_access',
                severity='warning',
                user=request.user if request.user.is_authenticated else None,
                ip_address=get_client_ip(request),
                event_description=f"System exception: {str(exception)[:200]}",
                additional_data={'exception_type': type(exception).__name__}
            )
        
        return None  # Let Django handle the response
```

### 7. Wagtail Admin Security

```python
# security/wagtail_hooks.py
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import user_passes_test

def is_security_officer(user):
    """Check if user is a security officer"""
    return (
        user.is_authenticated and
        hasattr(user, 'security_profile') and
        user.security_profile.security_role.role_type == 'security_officer'
    )

@hooks.register('register_admin_menu_item')
def register_security_menu_item():
    return MenuItem(
        _('Security Dashboard'),
        reverse('security_dashboard'),
        classnames='icon icon-lock',
        order=1000
    )

@hooks.register('before_serve_page')
def log_page_access(page, request, serve_args, serve_kwargs):
    """Log page access for audit trail"""
    if request.user.is_authenticated:
        SecurityAuditLog.objects.create(
            event_type='data_access',
            severity='info',
            user=request.user,
            ip_address=get_client_ip(request),
            request_path=request.path,
            event_description=f"Accessed page: {page.title}",
            additional_data={
                'page_id': page.id,
                'page_type': page.__class__.__name__
            }
        )

@hooks.register('after_edit_page')
def log_page_edit(request, page):
    """Log page edits"""
    SecurityAuditLog.objects.create(
        event_type='data_modification',
        severity='info',
        user=request.user,
        ip_address=get_client_ip(request),
        event_description=f"Modified page: {page.title}",
        additional_data={
            'page_id': page.id,
            'page_type': page.__class__.__name__
        }
    )

@hooks.register('construct_main_menu')
def hide_menu_items_for_role(request, menu_items):
    """Hide menu items based on user role"""
    if not request.user.is_authenticated:
        return
    
    user_role = request.user.security_profile.security_role.role_type
    
    # Define role-based menu visibility
    role_permissions = {
        'patient': ['pages'],  # Patients can only see pages
        'physician': ['pages', 'documents', 'medications'],
        'nurse': ['pages', 'documents'],
        'pharmacist': ['pages', 'medications', 'prescriptions'],
        'admin_staff': ['pages', 'documents', 'users'],
    }
    
    allowed_items = role_permissions.get(user_role, [])
    
    # Filter menu items
    if user_role != 'system_admin':  # System admin sees everything
        menu_items[:] = [
            item for item in menu_items
            if any(allowed in item.name.lower() for allowed in allowed_items)
        ]
```

### 8. Security Settings Configuration

```python
# settings/security.py
import os
from datetime import timedelta

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'security.authentication.HealthcareAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Session configuration
SESSION_ENGINE = 'security.sessions'
SESSION_COOKIE_AGE = 28800  # 8 hours
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Security middleware
MIDDLEWARE = [
    'security.middleware.SecurityHeadersMiddleware',
    'security.middleware.RateLimitMiddleware',
    'security.middleware.IPWhitelistMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'security.middleware.SessionSecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'security.middleware.DataLeakPreventionMiddleware',
]

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'security.validators.HealthcarePasswordValidator',
    },
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True
X_FRAME_OPTIONS = 'DENY'

# CSRF protection
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")

# Django Axes (brute force protection)
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # hours
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = 'axes.helpers.lockout'
AXES_USE_USER_AGENT = True
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True

# Encryption keys
FIELD_ENCRYPTION_KEY = os.environ.get('FIELD_ENCRYPTION_KEY')
if not FIELD_ENCRYPTION_KEY:
    raise ValueError("FIELD_ENCRYPTION_KEY environment variable must be set")

# IP whitelist for admin
ADMIN_ALLOWED_IPS = os.environ.get('ADMIN_ALLOWED_IPS', '').split(',')

# Session security
ENFORCE_IP_CONSISTENCY = os.environ.get('ENFORCE_IP_CONSISTENCY', 'true').lower() == 'true'

# Logging configuration for security
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'security': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'security.log'),
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
            'formatter': 'security',
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'audit.log'),
            'maxBytes': 1024*1024*50,  # 50MB
            'backupCount': 50,
            'formatter': 'security',
        },
    },
    'loggers': {
        'medguard.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'medguard.audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## Security Testing

### 1. Security Test Cases

```python
# security/tests/test_security.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from security.models import SecurityRole, UserSecurityProfile, SecurityAuditLog
from django.utils import timezone

class SecurityTestCase(TestCase):
    """Test security functionality"""
    
    def setUp(self):
        # Create security role
        self.physician_role = SecurityRole.objects.create(
            name="Test Physician",
            role_type="physician",
            access_level=5,
            can_view_all_patients=False,
            can_modify_patient_data=True
        )
        
        # Create test user
        self.user = User.objects.create_user(
            username='testphysician',
            password='TestPass123!',
            email='test@medguard.co.za'
        )
        
        # Create security profile
        self.security_profile = UserSecurityProfile.objects.create(
            user=self.user,
            security_role=self.physician_role,
            mfa_enabled=False
        )
    
    def test_failed_login_attempts(self):
        """Test account lockout after failed attempts"""
        client = Client()
        
        # Make 5 failed login attempts
        for i in range(5):
            response = client.post(reverse('login'), {
                'username': 'testphysician',
                'password': 'wrongpassword'
            })
        
        # Check if account is locked
        self.security_profile.refresh_from_db()
        self.assertTrue(self.security_profile.is_account_locked())
        
        # Check audit logs
        failed_attempts = SecurityAuditLog.objects.filter(
            event_type='login_failure',
            user=self.user
        ).count()
        self.assertEqual(failed_attempts, 5)
    
    def test_successful_login_audit(self):
        """Test audit logging for successful login"""
        client = Client()
        
        response = client.post(reverse('login'), {
            'username': 'testphysician',
            'password': 'TestPass123!'
        })
        
        # Check audit log
        success_log = SecurityAuditLog.objects.filter(
            event_type='login_success',
            user=self.user
        ).first()
        
        self.assertIsNotNone(success_log)
        self.assertEqual(success_log.severity, 'info')
    
    def test_ip_restriction(self):
        """Test IP address restrictions"""
        # Set allowed IPs
        self.security_profile.allowed_ip_addresses = ['192.168.1.100']
        self.security_profile.save()
        
        client = Client()
        
        # This would need to be tested with actual IP spoofing
        # In real tests, you'd use a test client that allows setting REMOTE_ADDR
        pass
    
    def test_role_based_access(self):
        """Test role-based access control"""
        client = Client()
        client.login(username='testphysician', password='TestPass123!')
        
        # Test access to different endpoints based on role
        # This would depend on your specific URL patterns and views
        pass
```

## Security Monitoring and Alerts

### 1. Security Monitoring Service

```python
# security/monitoring.py
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger('medguard.security')

class SecurityMonitoringService:
    """Service for monitoring security events"""
    
    @staticmethod
    def check_suspicious_activity():
        """Check for suspicious activity patterns"""
        now = timezone.now()
        hour_ago = now - timedelta(hours=1)
        
        # Check for multiple failed logins
        failed_logins = SecurityAuditLog.objects.filter(
            event_type='login_failure',
            timestamp__gte=hour_ago
        ).count()
        
        if failed_logins > 50:  # Threshold for alert
            SecurityMonitoringService.send_security_alert(
                'Multiple Failed Login Attempts',
                f'Detected {failed_logins} failed login attempts in the last hour'
            )
        
        # Check for unauthorized access attempts
        violations = SecurityAuditLog.objects.filter(
            event_type='security_violation',
            severity='critical',
            timestamp__gte=hour_ago
        ).count()
        
        if violations > 0:
            SecurityMonitoringService.send_security_alert(
                'Critical Security Violations',
                f'Detected {violations} critical security violations in the last hour'
            )
    
    @staticmethod
    def send_security_alert(subject, message):
        """Send security alert email"""
        security_team = getattr(settings, 'SECURITY_TEAM_EMAILS', [])
        
        if security_team:
            send_mail(
                subject=f'[MedGuard Security Alert] {subject}',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=security_team,
                fail_silently=False
            )
        
        # Log the alert
        logger.critical(f"Security Alert: {subject} - {message}")
    
    @staticmethod
    def generate_security_report():
        """Generate daily security report"""
        yesterday = timezone.now() - timedelta(days=1)
        
        report_data = {
            'total_logins': SecurityAuditLog.objects.filter(
                event_type='login_success',
                timestamp__gte=yesterday
            ).count(),
            'failed_logins': SecurityAuditLog.objects.filter(
                event_type='login_failure',
                timestamp__gte=yesterday
            ).count(),
            'security_violations': SecurityAuditLog.objects.filter(
                event_type='security_violation',
                timestamp__gte=yesterday
            ).count(),
            'data_access_events': SecurityAuditLog.objects.filter(
                event_type='data_access',
                timestamp__gte=yesterday
            ).count(),
        }
        
        return report_data
```

## Next Steps

1. **API Security**: Review `wagtail_api.md`
2. **Compliance Implementation**: See `wagtail_compliance.md`
3. **Deployment Security**: Check `wagtail_deployment.md`
4. **Monitoring Setup**: Follow `wagtail_troubleshooting.md`

## Resources

- [OWASP Healthcare Security](https://owasp.org/www-project-healthcare-security/)
- [POPIA Compliance Guide](https://popia.co.za/)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [Wagtail Security Documentation](https://docs.wagtail.io/en/stable/advanced_topics/security.html)
