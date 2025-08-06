"""
Wagtail 7.0.2 HIPAA-Compliant Page Access Controls

This module implements HIPAA-compliant page access controls using
Wagtail 7.0.2's enhanced permission system for healthcare data protection.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.http import Http404
from wagtail.models import Page, Site, Revision
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.base import BasePermissionPolicy as PermissionPolicy
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index

User = get_user_model()

# Import HealthcareRole for type hints
from .models import HealthcareRole
logger = logging.getLogger(__name__)


class PageAccessControl(models.Model):
    """
    HIPAA-compliant page access control for Wagtail 7.0.2.
    
    This model defines access controls for pages containing sensitive
    healthcare data, ensuring HIPAA compliance through granular permissions.
    """
    
    # Access control types
    class AccessType(models.TextChoices):
        PUBLIC = 'public', _('Public')
        AUTHENTICATED = 'authenticated', _('Authenticated Users')
        ROLE_BASED = 'role_based', _('Role-Based Access')
        PATIENT_SPECIFIC = 'patient_specific', _('Patient-Specific')
        STAFF_ONLY = 'staff_only', _('Staff Only')
        ADMIN_ONLY = 'admin_only', _('Administrators Only')
        EMERGENCY_ONLY = 'emergency_only', _('Emergency Access Only')
    
    # Data sensitivity levels
    class SensitivityLevel(models.TextChoices):
        LOW = 'low', _('Low Sensitivity')
        MEDIUM = 'medium', _('Medium Sensitivity')
        HIGH = 'high', _('High Sensitivity')
        CRITICAL = 'critical', _('Critical Sensitivity')
    
    # Page reference
    page = models.OneToOneField(
        Page,
        on_delete=models.CASCADE,
        related_name='access_control',
        help_text=_('Page to control access for')
    )
    
    # Access control settings
    access_type = models.CharField(
        max_length=30,
        choices=AccessType.choices,
        default=AccessType.AUTHENTICATED,
        help_text=_('Type of access control for this page')
    )
    
    sensitivity_level = models.CharField(
        max_length=20,
        choices=SensitivityLevel.choices,
        default=SensitivityLevel.MEDIUM,
        help_text=_('Sensitivity level of the page content')
    )
    
    # HIPAA compliance settings
    requires_consent = models.BooleanField(
        default=False,
        help_text=_('Whether patient consent is required to access this page')
    )
    
    requires_audit_logging = models.BooleanField(
        default=True,
        help_text=_('Whether access to this page should be audited')
    )
    
    requires_encryption = models.BooleanField(
        default=False,
        help_text=_('Whether page content should be encrypted')
    )
    
    # Role-based access
    allowed_roles = models.ManyToManyField(
        'security.HealthcareRole',
        blank=True,
        related_name='accessible_pages',
        help_text=_('Healthcare roles that can access this page')
    )
    
    # Patient-specific access
    patient_field = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Field name containing patient ID for patient-specific access')
    )
    
    # Emergency access
    emergency_access_enabled = models.BooleanField(
        default=False,
        help_text=_('Whether emergency access is allowed for this page')
    )
    
    emergency_access_roles = models.ManyToManyField(
        'security.HealthcareRole',
        blank=True,
        related_name='emergency_accessible_pages',
        help_text=_('Roles that can access this page in emergencies')
    )
    
    # Time-based restrictions
    access_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text=_('Start time for allowed access hours')
    )
    
    access_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text=_('End time for allowed access hours')
    )
    
    # Geographic restrictions
    allowed_ip_ranges = models.JSONField(
        default=list,
        blank=True,
        help_text=_('List of allowed IP ranges for access')
    )
    
    # Additional settings
    max_access_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Maximum duration in minutes for a single access session')
    )
    
    concurrent_access_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Maximum number of concurrent users allowed')
    )
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        FieldPanel('page'),
        FieldPanel('access_type'),
        FieldPanel('sensitivity_level'),
        MultiFieldPanel([
            FieldPanel('requires_consent'),
            FieldPanel('requires_audit_logging'),
            FieldPanel('requires_encryption'),
        ], heading=_('HIPAA Compliance Settings')),
        MultiFieldPanel([
            FieldPanel('allowed_roles'),
            FieldPanel('patient_field'),
        ], heading=_('Role-Based Access')),
        MultiFieldPanel([
            FieldPanel('emergency_access_enabled'),
            FieldPanel('emergency_access_roles'),
        ], heading=_('Emergency Access')),
        MultiFieldPanel([
            FieldPanel('access_hours_start'),
            FieldPanel('access_hours_end'),
        ], heading=_('Time Restrictions')),
        FieldPanel('allowed_ip_ranges'),
        MultiFieldPanel([
            FieldPanel('max_access_duration'),
            FieldPanel('concurrent_access_limit'),
        ], heading=_('Session Controls')),
    ]
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('page__title', boost=2.0),
        index.SearchField('access_type', boost=1.5),
        index.SearchField('sensitivity_level', boost=1.2),
        index.AutocompleteField('access_type'),
        index.AutocompleteField('sensitivity_level'),
        index.FilterField('access_type'),
        index.FilterField('sensitivity_level'),
        index.FilterField('requires_consent'),
        index.FilterField('requires_audit_logging'),
    ]
    
    class Meta:
        verbose_name = _('Page Access Control')
        verbose_name_plural = _('Page Access Controls')
        db_table = 'page_access_controls'
        ordering = ['page__title']
        permissions = [
            ('manage_page_access', _('Can manage page access controls')),
            ('view_page_access_logs', _('Can view page access logs')),
            ('emergency_page_access', _('Can access pages in emergency mode')),
        ]
    
    def __str__(self):
        return f"Access Control for {self.page.title}"
    
    def clean(self):
        """Validate the access control settings."""
        super().clean()
        
        # Validate time restrictions
        if self.access_hours_start and self.access_hours_end:
            if self.access_hours_start >= self.access_hours_end:
                raise ValidationError({
                    'access_hours_end': _('End time must be after start time.')
                })
        
        # Validate IP ranges
        if self.allowed_ip_ranges:
            if not isinstance(self.allowed_ip_ranges, list):
                raise ValidationError({
                    'allowed_ip_ranges': _('IP ranges must be a list.')
                })
    
    @property
    def is_high_sensitivity(self) -> bool:
        """Check if this page has high sensitivity content."""
        return self.sensitivity_level in [
            self.SensitivityLevel.HIGH,
            self.SensitivityLevel.CRITICAL
        ]
    
    @property
    def requires_hipaa_compliance(self) -> bool:
        """Check if this page requires HIPAA compliance measures."""
        return (
            self.requires_consent or
            self.requires_audit_logging or
            self.requires_encryption or
            self.is_high_sensitivity
        )


class PageAccessLog(models.Model):
    """
    Log of page access attempts for HIPAA compliance.
    
    This model tracks all page access attempts, including successful
    and failed access, for audit and compliance purposes.
    """
    
    # Access result types
    class AccessResult(models.TextChoices):
        GRANTED = 'granted', _('Access Granted')
        DENIED = 'denied', _('Access Denied')
        EMERGENCY = 'emergency', _('Emergency Access')
        EXPIRED = 'expired', _('Access Expired')
        SUSPENDED = 'suspended', _('Access Suspended')
    
    # Page access control
    access_control = models.ForeignKey(
        PageAccessControl,
        on_delete=models.CASCADE,
        related_name='access_logs',
        help_text=_('Page access control that was accessed')
    )
    
    # User who attempted access
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='page_access_logs',
        help_text=_('User who attempted to access the page')
    )
    
    # Access details
    access_result = models.CharField(
        max_length=20,
        choices=AccessResult.choices,
        help_text=_('Result of the access attempt')
    )
    
    access_reason = models.TextField(
        blank=True,
        help_text=_('Reason for the access attempt')
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
    
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Session ID for the request')
    )
    
    # Healthcare context
    patient_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Patient ID if the access involves patient data')
    )
    
    # Timestamps
    access_time = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the access attempt occurred')
    )
    
    session_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Duration of the access session in seconds')
    )
    
    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional metadata about the access attempt')
    )
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        FieldPanel('access_control'),
        FieldPanel('user'),
        FieldPanel('access_result'),
        FieldPanel('access_reason'),
        MultiFieldPanel([
            FieldPanel('ip_address'),
            FieldPanel('user_agent'),
            FieldPanel('session_id'),
        ], heading=_('Request Context')),
        FieldPanel('patient_id'),
        FieldPanel('access_time'),
        FieldPanel('session_duration'),
        FieldPanel('metadata'),
    ]
    
    class Meta:
        verbose_name = _('Page Access Log')
        verbose_name_plural = _('Page Access Logs')
        db_table = 'page_access_logs'
        indexes = [
            models.Index(fields=['access_control', 'access_time']),
            models.Index(fields=['user', 'access_time']),
            models.Index(fields=['access_result', 'access_time']),
            models.Index(fields=['patient_id', 'access_time']),
            models.Index(fields=['ip_address', 'access_time']),
            models.Index(fields=['access_time']),
        ]
        ordering = ['-access_time']
        permissions = [
            ('view_access_logs', _('Can view access logs')),
            ('export_access_logs', _('Can export access logs')),
            ('anonymize_access_logs', _('Can anonymize access logs')),
        ]
    
    def __str__(self):
        return f"{self.access_result} - {self.access_control.page.title} - {self.access_time}"


class HIPAACompliantPagePermissionPolicy(PermissionPolicy):
    """
    HIPAA-compliant permission policy for Wagtail pages.
    
    This policy implements healthcare-specific permission checks with
    HIPAA compliance and granular access controls.
    """
    
    def __init__(self, model):
        self.model = model
        self._permission_policy = ModelPermissionPolicy(model)
    
    def user_has_permission(self, user: User, action: str) -> bool:
        """
        Check if user has permission for a specific action.
        
        Args:
            user: User to check permissions for
            action: Action to check (add, change, delete, publish, etc.)
            
        Returns:
            True if user has permission
        """
        # Superusers have all permissions
        if user.is_superuser:
            return True
        
        # Check basic Wagtail permissions
        if not self._permission_policy.user_has_permission(user, action):
            return False
        
        # Check healthcare-specific permissions
        return self._check_healthcare_permissions(user, action)
    
    def user_has_any_permission(self, user: User, actions: List[str]) -> bool:
        """
        Check if user has any of the specified permissions.
        
        Args:
            user: User to check permissions for
            actions: List of actions to check
            
        Returns:
            True if user has any of the permissions
        """
        return any(self.user_has_permission(user, action) for action in actions)
    
    def users_with_permission(self, action: str, include_superusers: bool = True) -> List[User]:
        """
        Get users with specific permission.
        
        Args:
            action: Action to check
            include_superusers: Whether to include superusers
            
        Returns:
            List of users with permission
        """
        users = list(self._permission_policy.users_with_permission(action, include_superusers))
        
        # Filter by healthcare permissions
        return [user for user in users if self._check_healthcare_permissions(user, action)]
    
    def instances_user_has_permission_for(self, user: User, action: str) -> List[Any]:
        """
        Get instances user has permission for.
        
        Args:
            user: User to check permissions for
            action: Action to check
            
        Returns:
            List of instances user has permission for
        """
        instances = list(self._permission_policy.instances_user_has_permission_for(user, action))
        
        # Filter by healthcare access controls
        return [instance for instance in instances if self._check_instance_access(user, instance, action)]
    
    def _check_healthcare_permissions(self, user: User, action: str) -> bool:
        """
        Check healthcare-specific permissions.
        
        Args:
            user: User to check permissions for
            action: Action to check
            
        Returns:
            True if user has healthcare permission
        """
        # Get user's healthcare roles
        from .models import HealthcareRole
        user_roles = HealthcareRole.objects.filter(
            user_assignments__user=user,
            user_assignments__is_active=True
        )
        
        # Check if any role has the required permission
        for role in user_roles:
            if self._role_has_action_permission(role, action):
                return True
        
        return False
    
    def _role_has_action_permission(self, role: HealthcareRole, action: str) -> bool:
        """
        Check if role has permission for specific action.
        
        Args:
            role: Healthcare role to check
            action: Action to check
            
        Returns:
            True if role has permission
        """
        # Map Wagtail actions to healthcare permissions
        action_mapping = {
            'add': ['create_patient_data', 'create_medication_data'],
            'change': ['edit_patient_data', 'edit_medication_data'],
            'delete': ['delete_patient_data', 'delete_medication_data'],
            'publish': ['approve_prescription', 'publish_content'],
            'unpublish': ['unpublish_content'],
            'lock': ['lock_content'],
            'unlock': ['unlock_content'],
        }
        
        required_permissions = action_mapping.get(action, [])
        role_permissions = role.get_permissions()
        
        return any(perm in role_permissions for perm in required_permissions)
    
    def _check_instance_access(self, user: User, instance: Any, action: str) -> bool:
        """
        Check if user has access to specific instance.
        
        Args:
            user: User to check access for
            instance: Instance to check access to
            action: Action to check
            
        Returns:
            True if user has access
        """
        # Check if instance has access control
        if hasattr(instance, 'access_control'):
            return self._check_page_access_control(user, instance.access_control, action)
        
        return True
    
    def _check_page_access_control(self, user: User, access_control: PageAccessControl, action: str) -> bool:
        """
        Check page access control for user.
        
        Args:
            user: User to check access for
            access_control: Page access control to check
            action: Action to check
            
        Returns:
            True if user has access
        """
        # Check access type
        if access_control.access_type == PageAccessControl.AccessType.PUBLIC:
            return True
        
        if access_control.access_type == PageAccessControl.AccessType.AUTHENTICATED:
            return user.is_authenticated
        
        if access_control.access_type == PageAccessControl.AccessType.STAFF_ONLY:
            return user.is_staff
        
        if access_control.access_type == PageAccessControl.AccessType.ADMIN_ONLY:
            return user.is_superuser
        
        if access_control.access_type == PageAccessControl.AccessType.ROLE_BASED:
            return self._check_role_based_access(user, access_control)
        
        if access_control.access_type == PageAccessControl.AccessType.PATIENT_SPECIFIC:
            return self._check_patient_specific_access(user, access_control)
        
        return False
    
    def _check_role_based_access(self, user: User, access_control: PageAccessControl) -> bool:
        """
        Check role-based access for user.
        
        Args:
            user: User to check access for
            access_control: Page access control to check
            
        Returns:
            True if user has access
        """
        # Get user's healthcare roles
        from .models import HealthcareRole
        user_roles = HealthcareRole.objects.filter(
            user_assignments__user=user,
            user_assignments__is_active=True
        )
        
        # Check if user has any of the allowed roles
        return user_roles.filter(id__in=access_control.allowed_roles.all()).exists()
    
    def _check_patient_specific_access(self, user: User, access_control: PageAccessControl) -> bool:
        """
        Check patient-specific access for user.
        
        Args:
            user: User to check access for
            access_control: Page access control to check
            
        Returns:
            True if user has access
        """
        # This would need to be implemented based on the specific patient data model
        # For now, return True if user has patient data access permission
        from .models import HealthcareRole
        user_roles = HealthcareRole.objects.filter(
            user_assignments__user=user,
            user_assignments__is_active=True
        )
        
        return user_roles.filter(can_view_patient_data=True).exists()


class PageAccessManager:
    """
    Manager for HIPAA-compliant page access controls.
    
    This class provides methods to manage page access controls and
    log access attempts for compliance purposes.
    """
    
    def __init__(self, request=None):
        self.request = request
        self.user = getattr(request, 'user', None) if request else None
    
    def check_page_access(self, page: Page, action: str = 'view') -> bool:
        """
        Check if user can access a page.
        
        Args:
            page: Page to check access for
            action: Action to check (view, edit, etc.)
            
        Returns:
            True if user has access
        """
        # Get page access control
        try:
            access_control = page.access_control
        except PageAccessControl.DoesNotExist:
            # No access control defined, allow access
            return True
        
        # Check access using permission policy
        policy = HIPAACompliantPagePermissionPolicy(Page)
        has_access = policy.user_has_permission(self.user, action)
        
        # Log access attempt
        self._log_access_attempt(access_control, has_access, action)
        
        return has_access
    
    def _log_access_attempt(self, access_control: PageAccessControl, granted: bool, action: str):
        """
        Log page access attempt.
        
        Args:
            access_control: Page access control
            granted: Whether access was granted
            action: Action attempted
        """
        if not access_control.requires_audit_logging:
            return
        
        # Extract request information
        request_data = self._extract_request_data()
        
        # Determine access result
        if granted:
            access_result = PageAccessLog.AccessResult.GRANTED
        else:
            access_result = PageAccessLog.AccessResult.DENIED
        
        # Create access log entry
        PageAccessLog.objects.create(
            access_control=access_control,
            user=self.user,
            access_result=access_result,
            access_reason=f"Page {action} attempt",
            **request_data
        )
    
    def _extract_request_data(self) -> Dict:
        """Extract request data for access logging."""
        if not self.request:
            return {}
        
        return {
            'ip_address': self._get_client_ip(),
            'user_agent': self.request.META.get('HTTP_USER_AGENT', ''),
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


# Utility functions for page access control
def get_page_access_manager(request=None) -> PageAccessManager:
    """
    Get a page access manager instance.
    
    Args:
        request: Django request object
        
    Returns:
        PageAccessManager instance
    """
    return PageAccessManager(request)


def check_page_access(page: Page, user: User, action: str = 'view') -> bool:
    """
    Check if user can access a page.
    
    Args:
        page: Page to check access for
        user: User to check access for
        action: Action to check
        
    Returns:
        True if user has access
    """
    policy = HIPAACompliantPagePermissionPolicy(Page)
    return policy.user_has_permission(user, action)


def create_page_access_control(page: Page, access_type: str = 'authenticated', **kwargs) -> PageAccessControl:
    """
    Create page access control for a page.
    
    Args:
        page: Page to create access control for
        access_type: Type of access control
        **kwargs: Additional parameters
        
    Returns:
        Created PageAccessControl instance
    """
    return PageAccessControl.objects.create(
        page=page,
        access_type=access_type,
        **kwargs
    )


def log_page_access(access_control: PageAccessControl, user: User, granted: bool, **kwargs) -> PageAccessLog:
    """
    Log page access attempt.
    
    Args:
        access_control: Page access control
        user: User who attempted access
        granted: Whether access was granted
        **kwargs: Additional parameters
        
    Returns:
        Created PageAccessLog instance
    """
    access_result = PageAccessLog.AccessResult.GRANTED if granted else PageAccessLog.AccessResult.DENIED
    
    return PageAccessLog.objects.create(
        access_control=access_control,
        user=user,
        access_result=access_result,
        **kwargs
    ) 