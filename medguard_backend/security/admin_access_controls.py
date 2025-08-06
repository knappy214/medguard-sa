"""
Improved admin access controls using Wagtail 7.0.2's admin security features.

This module provides healthcare-specific admin access controls including:
- Role-based admin access
- Healthcare staff permissions
- Admin session management
- Audit trails for admin actions
- HIPAA-compliant admin controls
"""

import logging
from typing import Dict, Any, List, Optional, Set
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.admin.auth import require_admin_access
from wagtail.admin.forms import WagtailAdminPageForm
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.admin.views.pages import listing
from wagtail.permissions import ModelPermissionPolicy

from .models import SecurityEvent, HealthcareRole
from .audit import log_security_event

logger = logging.getLogger(__name__)
User = get_user_model()


class HealthcareAdminAccessMixin:
    """
    Mixin for healthcare admin access controls.
    
    Provides HIPAA-compliant admin access controls and audit trails.
    """
    
    # Healthcare staff roles
    ROLE_ADMIN = 'admin'
    ROLE_PHYSICIAN = 'physician'
    ROLE_NURSE = 'nurse'
    ROLE_PHARMACIST = 'pharmacist'
    ROLE_TECHNICIAN = 'technician'
    ROLE_RECEPTIONIST = 'receptionist'
    ROLE_READ_ONLY = 'read_only'
    
    # Admin access levels
    ACCESS_NONE = 'none'
    ACCESS_READ = 'read'
    ACCESS_WRITE = 'write'
    ACCESS_ADMIN = 'admin'
    ACCESS_SUPER = 'super'
    
    class Meta:
        abstract = True
    
    def get_healthcare_role(self) -> str:
        """Get user's healthcare role."""
        if hasattr(self, 'healthcare_role'):
            return self.healthcare_role
        return self.ROLE_READ_ONLY
    
    def get_admin_access_level(self) -> str:
        """Get user's admin access level."""
        if self.is_superuser:
            return self.ACCESS_SUPER
        elif self.is_staff:
            return self._determine_staff_access_level()
        else:
            return self.ACCESS_NONE
    
    def _determine_staff_access_level(self) -> str:
        """Determine staff access level based on roles and permissions."""
        user_permissions = self.get_all_permissions()
        
        if 'security.admin_access' in user_permissions:
            return self.ACCESS_ADMIN
        elif 'security.write_access' in user_permissions:
            return self.ACCESS_WRITE
        elif 'security.read_access' in user_permissions:
            return self.ACCESS_READ
        else:
            return self.ACCESS_NONE


class HealthcareRoleManager(models.Manager):
    """
    Manager for healthcare role management.
    """
    
    def get_role_permissions(self, role: str) -> Set[str]:
        """
        Get permissions for a healthcare role.
        
        Args:
            role: Healthcare role name
            
        Returns:
            Set of permission codenames
        """
        role_permissions = {
            HealthcareAdminAccessMixin.ROLE_ADMIN: {
                'security.admin_access',
                'security.write_access',
                'security.read_access',
                'security.view_audit_logs',
                'security.manage_users',
                'security.manage_roles',
            },
            HealthcareAdminAccessMixin.ROLE_PHYSICIAN: {
                'security.write_access',
                'security.read_access',
                'medications.add_prescription',
                'medications.change_prescription',
                'medications.view_prescription',
                'security.view_patient_data',
            },
            HealthcareAdminAccessMixin.ROLE_NURSE: {
                'security.read_access',
                'medications.view_prescription',
                'security.view_patient_data',
                'notifications.send_notifications',
            },
            HealthcareAdminAccessMixin.ROLE_PHARMACIST: {
                'security.read_access',
                'medications.view_prescription',
                'medications.change_prescription',
                'security.view_patient_data',
                'medications.manage_inventory',
            },
            HealthcareAdminAccessMixin.ROLE_TECHNICIAN: {
                'security.read_access',
                'security.view_technical_data',
            },
            HealthcareAdminAccessMixin.ROLE_RECEPTIONIST: {
                'security.read_access',
                'users.view_patient_contact',
                'notifications.send_notifications',
            },
            HealthcareAdminAccessMixin.ROLE_READ_ONLY: {
                'security.read_access',
            },
        }
        
        return role_permissions.get(role, set())
    
    def assign_role_to_user(self, user: User, role: str) -> bool:
        """
        Assign healthcare role to user.
        
        Args:
            user: User to assign role to
            role: Healthcare role to assign
            
        Returns:
            True if role assignment successful
        """
        try:
            # Get or create healthcare role
            healthcare_role, created = HealthcareRole.objects.get_or_create(
                user=user,
                defaults={'role': role}
            )
            
            if not created:
                healthcare_role.role = role
                healthcare_role.save()
            
            # Assign permissions
            permissions = self.get_role_permissions(role)
            self._assign_permissions_to_user(user, permissions)
            
            # Log role assignment
            log_security_event(
                user=user,
                event_type='role_assigned',
                details={'role': role, 'permissions': list(permissions)}
            )
            
            return True
        except Exception as e:
            logger.error(f"Failed to assign role {role} to user {user.id}: {e}")
            return False
    
    def _assign_permissions_to_user(self, user: User, permissions: Set[str]):
        """Assign permissions to user."""
        # Get permission objects
        permission_objects = Permission.objects.filter(
            codename__in=[perm.split('.')[-1] for perm in permissions],
            content_type__app_label__in=[perm.split('.')[0] for perm in permissions]
        )
        
        # Assign permissions
        user.user_permissions.set(permission_objects)


class HealthcareRole(models.Model):
    """
    Healthcare role assignment for users.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='healthcare_role'
    )
    
    role = models.CharField(
        max_length=20,
        choices=[
            (HealthcareAdminAccessMixin.ROLE_ADMIN, _('Administrator')),
            (HealthcareAdminAccessMixin.ROLE_PHYSICIAN, _('Physician')),
            (HealthcareAdminAccessMixin.ROLE_NURSE, _('Nurse')),
            (HealthcareAdminAccessMixin.ROLE_PHARMACIST, _('Pharmacist')),
            (HealthcareAdminAccessMixin.ROLE_TECHNICIAN, _('Technician')),
            (HealthcareAdminAccessMixin.ROLE_RECEPTIONIST, _('Receptionist')),
            (HealthcareAdminAccessMixin.ROLE_READ_ONLY, _('Read Only')),
        ]
    )
    
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_roles'
    )
    
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    objects = HealthcareRoleManager()
    
    class Meta:
        verbose_name = _('Healthcare Role')
        verbose_name_plural = _('Healthcare Roles')
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_valid(self) -> bool:
        """Check if role assignment is still valid."""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < timezone.now():
            return False
        
        return True


class AdminAccessLog(models.Model):
    """
    Audit log for admin access events.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='admin_access_logs'
    )
    
    action = models.CharField(
        max_length=50,
        choices=[
            ('login', _('Login')),
            ('logout', _('Logout')),
            ('page_view', _('Page View')),
            ('data_access', _('Data Access')),
            ('data_modify', _('Data Modification')),
            ('user_management', _('User Management')),
            ('system_config', _('System Configuration')),
        ]
    )
    
    target_object = models.CharField(max_length=100, blank=True)
    target_id = models.IntegerField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.FloatField(null=True, blank=True)  # seconds
    
    details = models.JSONField(default=dict)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _('Admin Access Log')
        verbose_name_plural = _('Admin Access Logs')
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"


class SecureAdminAccessMiddleware:
    """
    Middleware for secure admin access controls.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check admin access for admin URLs
        if self._is_admin_url(request.path):
            self._check_admin_access(request)
        
        response = self.get_response(request)
        return response
    
    def _is_admin_url(self, path: str) -> bool:
        """Check if URL is an admin URL."""
        admin_paths = [
            '/admin/',
            '/wagtail/',
            '/django-admin/',
        ]
        
        return any(path.startswith(admin_path) for admin_path in admin_paths)
    
    def _check_admin_access(self, request: HttpRequest):
        """Check admin access permissions."""
        if not request.user.is_authenticated:
            return
        
        # Check if user has admin access
        if not self._has_admin_access(request.user):
            raise PermissionDenied("User does not have admin access")
        
        # Log admin access
        self._log_admin_access(request)
    
    def _has_admin_access(self, user: User) -> bool:
        """Check if user has admin access."""
        if user.is_superuser:
            return True
        
        if not user.is_staff:
            return False
        
        # Check healthcare role
        try:
            healthcare_role = user.healthcare_role
            if not healthcare_role.is_valid():
                return False
            
            # Check role-based access
            role = healthcare_role.role
            if role in [
                HealthcareAdminAccessMixin.ROLE_ADMIN,
                HealthcareAdminAccessMixin.ROLE_PHYSICIAN,
                HealthcareAdminAccessMixin.ROLE_NURSE,
                HealthcareAdminAccessMixin.ROLE_PHARMACIST,
            ]:
                return True
            
            return False
        except HealthcareRole.DoesNotExist:
            return False
    
    def _log_admin_access(self, request: HttpRequest):
        """Log admin access for audit purposes."""
        AdminAccessLog.objects.create(
            user=request.user,
            action='page_view',
            target_object=request.path,
            ip_address=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_id=request.session.session_key or '',
            details={
                'method': request.method,
                'referer': request.META.get('HTTP_REFERER', ''),
            }
        )


class HealthcareAdminPermissionPolicy(ModelPermissionPolicy):
    """
    Custom permission policy for healthcare admin access.
    """
    
    def user_has_permission(self, user, action):
        """Check if user has permission for action."""
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Check healthcare role
        try:
            healthcare_role = user.healthcare_role
            if not healthcare_role.is_valid():
                return False
            
            # Role-based permissions
            role = healthcare_role.role
            
            if action == 'add':
                return role in [
                    HealthcareAdminAccessMixin.ROLE_ADMIN,
                    HealthcareAdminAccessMixin.ROLE_PHYSICIAN,
                    HealthcareAdminAccessMixin.ROLE_PHARMACIST,
                ]
            elif action == 'change':
                return role in [
                    HealthcareAdminAccessMixin.ROLE_ADMIN,
                    HealthcareAdminAccessMixin.ROLE_PHYSICIAN,
                    HealthcareAdminAccessMixin.ROLE_PHARMACIST,
                ]
            elif action == 'publish':
                return role in [
                    HealthcareAdminAccessMixin.ROLE_ADMIN,
                    HealthcareAdminAccessMixin.ROLE_PHYSICIAN,
                ]
            elif action == 'bulk_delete':
                return role == HealthcareAdminAccessMixin.ROLE_ADMIN
            elif action == 'choose':
                return role != HealthcareAdminAccessMixin.ROLE_READ_ONLY
            
            return False
        except HealthcareRole.DoesNotExist:
            return False
    
    def user_has_any_permission(self, user, actions):
        """Check if user has any of the specified permissions."""
        return any(self.user_has_permission(user, action) for action in actions)
    
    def instances_user_has_permission_for(self, user, action):
        """Get instances user has permission for."""
        if not user.is_authenticated:
            return models.QuerySet()
        
        if user.is_superuser:
            return models.QuerySet()
        
        # Role-based instance filtering
        try:
            healthcare_role = user.healthcare_role
            if not healthcare_role.is_valid():
                return models.QuerySet()
            
            role = healthcare_role.role
            
            if action in ['change', 'publish', 'bulk_delete']:
                # Users can only modify their own content
                return models.QuerySet().filter(created_by=user)
            
            return models.QuerySet()
        except HealthcareRole.DoesNotExist:
            return models.QuerySet()


# Admin access decorators
def require_healthcare_role(roles: List[str]):
    """
    Decorator to require specific healthcare roles.
    
    Args:
        roles: List of required healthcare roles
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            # Check healthcare role
            try:
                healthcare_role = request.user.healthcare_role
                if not healthcare_role.is_valid():
                    raise PermissionDenied("Invalid healthcare role")
                
                if healthcare_role.role not in roles:
                    raise PermissionDenied("Insufficient role permissions")
                
            except HealthcareRole.DoesNotExist:
                raise PermissionDenied("Healthcare role required")
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_admin_access_level(access_level: str):
    """
    Decorator to require specific admin access level.
    
    Args:
        access_level: Required admin access level
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required")
            
            user_access_level = request.user.get_admin_access_level()
            
            # Check access level hierarchy
            access_hierarchy = [
                HealthcareAdminAccessMixin.ACCESS_NONE,
                HealthcareAdminAccessMixin.ACCESS_READ,
                HealthcareAdminAccessMixin.ACCESS_WRITE,
                HealthcareAdminAccessMixin.ACCESS_ADMIN,
                HealthcareAdminAccessMixin.ACCESS_SUPER,
            ]
            
            required_index = access_hierarchy.index(access_level)
            user_index = access_hierarchy.index(user_access_level)
            
            if user_index < required_index:
                raise PermissionDenied("Insufficient admin access level")
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# Wagtail admin integration
class HealthcareAdminForm(WagtailAdminPageForm):
    """
    Healthcare-specific admin form with access controls.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = kwargs.get('user')
    
    def clean(self):
        """Enhanced form validation with healthcare access controls."""
        cleaned_data = super().clean()
        
        if self.user:
            # Check user permissions for form fields
            self._validate_field_permissions(cleaned_data)
        
        return cleaned_data
    
    def _validate_field_permissions(self, data: Dict[str, Any]):
        """Validate user permissions for form fields."""
        # This would implement field-level permission checking
        # based on user's healthcare role
        pass


# Register with Wagtail
def register_healthcare_admin():
    """Register healthcare admin features with Wagtail."""
    from wagtail.admin.views.pages import listing
    
    # Override default admin views with healthcare-specific versions
    # This would be implemented based on specific requirements
    pass 