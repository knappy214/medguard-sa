"""
HIPAA-Compliant Permissions System

This module implements comprehensive permission management for the MedGuard SA system,
ensuring HIPAA compliance through role-based access control (RBAC) and principle of least privilege.
"""

import logging
from typing import Any, Dict, List, Optional, Set
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

User = get_user_model()
logger = logging.getLogger(__name__)


class UserPermissionManager:
    """
    HIPAA-compliant user permission manager.
    
    This class manages user permissions based on roles and HIPAA requirements,
    ensuring proper access control for medical data.
    """
    
    # HIPAA-defined permission categories
    class PermissionCategory(models.TextChoices):
        PATIENT_DATA = 'patient_data', _('Patient Data')
        MEDICATION_DATA = 'medication_data', _('Medication Data')
        AUDIT_DATA = 'audit_data', _('Audit Data')
        SYSTEM_ADMIN = 'system_admin', _('System Administration')
        RESEARCH_DATA = 'research_data', _('Research Data')
        REPORTING_DATA = 'reporting_data', _('Reporting Data')
    
    # Permission actions
    class PermissionAction(models.TextChoices):
        VIEW = 'view', _('View')
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        EXPORT = 'export', _('Export')
        IMPORT = 'import', _('Import')
        APPROVE = 'approve', _('Approve')
        AUDIT = 'audit', _('Audit')
    
    def __init__(self, user: User):
        self.user = user
        self._permissions_cache = None
        self._roles_cache = None
    
    def has_permission(self, permission: str, resource: Any = None) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            permission: Permission to check (format: 'action_category')
            resource: Resource being accessed (optional)
            
        Returns:
            True if user has permission
        """
        # Superusers have all permissions
        if self.user.is_superuser:
            return True
        
        # Check cached permissions
        if self._permissions_cache is None:
            self._load_permissions()
        
        # Check basic permission
        if permission not in self._permissions_cache:
            return False
        
        # Check resource-specific permissions
        if resource and hasattr(resource, 'user'):
            if permission.startswith('view_own_') or permission.startswith('update_own_'):
                return resource.user == self.user
        
        return True
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if user has role
        """
        if self._roles_cache is None:
            self._load_roles()
        
        return role in self._roles_cache
    
    def get_permissions(self) -> Set[str]:
        """
        Get all permissions for user.
        
        Returns:
            Set of permission strings
        """
        if self._permissions_cache is None:
            self._load_permissions()
        
        return self._permissions_cache
    
    def get_roles(self) -> Set[str]:
        """
        Get all roles for user.
        
        Returns:
            Set of role strings
        """
        if self._roles_cache is None:
            self._load_roles()
        
        return self._roles_cache
    
    def _load_permissions(self):
        """Load user permissions from database and role definitions."""
        permissions = set()
        
        # Get Django permissions
        django_permissions = self.user.user_permissions.all()
        for perm in django_permissions:
            permissions.add(f"{perm.content_type.app_label}.{perm.codename}")
        
        # Get group permissions
        group_permissions = Permission.objects.filter(group__user=self.user)
        for perm in group_permissions:
            permissions.add(f"{perm.content_type.app_label}.{perm.codename}")
        
        # Get role-based permissions
        role_permissions = self._get_role_permissions()
        permissions.update(role_permissions)
        
        self._permissions_cache = permissions
    
    def _load_roles(self):
        """Load user roles."""
        roles = set()
        
        # Get user type as primary role
        user_type = getattr(self.user, 'user_type', 'patient')
        roles.add(user_type)
        
        # Get additional roles from user profile
        if hasattr(self.user, 'profile'):
            additional_roles = getattr(self.user.profile, 'additional_roles', [])
            roles.update(additional_roles)
        
        self._roles_cache = roles
    
    def _get_role_permissions(self) -> Set[str]:
        """Get permissions based on user roles."""
        permissions = set()
        
        for role in self.get_roles():
            role_permissions = self._get_permissions_for_role(role)
            permissions.update(role_permissions)
        
        return permissions
    
    def _get_permissions_for_role(self, role: str) -> Set[str]:
        """Get permissions for specific role."""
        role_permissions = {
            'patient': {
                'view_own_patient_data',
                'update_own_patient_data',
                'view_own_medication_data',
                'update_own_medication_data',
                'view_own_schedule',
                'update_own_schedule',
            },
            'caregiver': {
                'view_patient_data',
                'update_patient_medication_data',
                'view_patient_schedule',
                'update_patient_schedule',
                'manage_patient_reminders',
            },
            'healthcare_provider': {
                'view_patient_data',
                'update_patient_data',
                'view_medication_data',
                'update_medication_data',
                'prescribe_medications',
                'view_medication_history',
                'export_patient_data',
                'view_audit_data',
            },
            'pharmacist': {
                'view_medication_inventory',
                'update_medication_stock',
                'view_patient_medications',
                'dispense_medications',
                'view_medication_interactions',
            },
            'administrator': {
                'view_all_data',
                'update_all_data',
                'manage_users',
                'manage_system_settings',
                'view_audit_logs',
                'export_system_data',
                'manage_backups',
                'view_compliance_reports',
            },
            'researcher': {
                'view_anonymized_data',
                'export_research_data',
                'view_aggregate_statistics',
            },
            'auditor': {
                'view_audit_logs',
                'view_compliance_reports',
                'view_system_logs',
                'export_audit_data',
            },
        }
        
        return role_permissions.get(role, set())


class ResourcePermissionManager:
    """
    Resource-specific permission manager.
    
    This class manages permissions for specific resources and data types,
    implementing HIPAA-compliant access controls.
    """
    
    def __init__(self):
        self.sensitive_data_types = {
            'patient_records',
            'medication_records',
            'medical_history',
            'diagnostic_results',
            'treatment_plans',
            'billing_information',
        }
    
    def can_access_resource(self, user: User, resource: Any, action: str) -> bool:
        """
        Check if user can perform action on resource.
        
        Args:
            user: User requesting access
            resource: Resource being accessed
            action: Action to perform
            
        Returns:
            True if access is allowed
        """
        permission_manager = UserPermissionManager(user)
        
        # Check basic permission
        permission = f"{action}_{self._get_resource_type(resource)}"
        if not permission_manager.has_permission(permission, resource):
            return False
        
        # Check resource-specific rules
        if self._is_sensitive_resource(resource):
            return self._check_sensitive_resource_access(user, resource, action)
        
        return True
    
    def _get_resource_type(self, resource: Any) -> str:
        """Get resource type for permission checking."""
        if hasattr(resource, '_meta'):
            return resource._meta.model_name
        elif isinstance(resource, str):
            return resource
        else:
            return type(resource).__name__.lower()
    
    def _is_sensitive_resource(self, resource: Any) -> bool:
        """Check if resource contains sensitive data."""
        resource_type = self._get_resource_type(resource)
        return resource_type in self.sensitive_data_types
    
    def _check_sensitive_resource_access(self, user: User, resource: Any, action: str) -> bool:
        """Check access to sensitive resources."""
        # Implement additional checks for sensitive data
        # This could include:
        # - Time-based access restrictions
        # - Location-based restrictions
        # - Purpose-based access controls
        # - Consent verification
        
        # For now, we'll use basic role-based checks
        permission_manager = UserPermissionManager(user)
        
        if action == 'view':
            return permission_manager.has_role('healthcare_provider') or \
                   permission_manager.has_role('administrator') or \
                   permission_manager.has_role('auditor')
        
        if action == 'update':
            return permission_manager.has_role('healthcare_provider') or \
                   permission_manager.has_role('administrator')
        
        if action == 'delete':
            return permission_manager.has_role('administrator')
        
        return False


class ConsentManager:
    """
    HIPAA consent management system.
    
    This class manages patient consent for data access and sharing,
    ensuring compliance with HIPAA privacy requirements.
    """
    
    def __init__(self):
        self.consent_types = {
            'treatment': 'Consent for treatment-related data access',
            'payment': 'Consent for billing and payment data access',
            'healthcare_operations': 'Consent for healthcare operations',
            'research': 'Consent for research data use',
            'marketing': 'Consent for marketing communications',
        }
    
    def has_valid_consent(self, patient: User, consent_type: str, provider: User = None) -> bool:
        """
        Check if patient has valid consent for data access.
        
        Args:
            patient: Patient user
            consent_type: Type of consent required
            provider: Healthcare provider requesting access
            
        Returns:
            True if valid consent exists
        """
        # This would check consent records in the database
        # For now, we'll implement a basic check
        
        if consent_type == 'treatment':
            # Treatment consent is implied for healthcare providers
            if provider and self._is_healthcare_provider(provider):
                return True
        
        if consent_type == 'research':
            # Research consent must be explicit
            return self._check_explicit_consent(patient, 'research')
        
        return True
    
    def _is_healthcare_provider(self, user: User) -> bool:
        """Check if user is a healthcare provider."""
        permission_manager = UserPermissionManager(user)
        return permission_manager.has_role('healthcare_provider')
    
    def _check_explicit_consent(self, patient: User, consent_type: str) -> bool:
        """Check for explicit consent."""
        # This would query the consent database
        # For now, return False to require explicit consent
        return False
    
    def record_consent(self, patient: User, consent_type: str, granted: bool, 
                      provider: User = None, expires_at: str = None):
        """
        Record patient consent.
        
        Args:
            patient: Patient user
            consent_type: Type of consent
            granted: Whether consent was granted
            provider: Healthcare provider (optional)
            expires_at: Consent expiration date (optional)
        """
        # This would create a consent record in the database
        logger.info(f"Consent recorded: {patient.username} - {consent_type} - {granted}")


class EmergencyAccessManager:
    """
    Emergency access management for HIPAA compliance.
    
    This class manages emergency access to patient data when
    normal access controls cannot be followed.
    """
    
    def __init__(self):
        self.emergency_roles = {
            'emergency_physician',
            'emergency_nurse',
            'paramedic',
            'emergency_responder',
        }
    
    def request_emergency_access(self, user: User, patient: User, reason: str) -> bool:
        """
        Request emergency access to patient data.
        
        Args:
            user: User requesting emergency access
            patient: Patient whose data is needed
            reason: Reason for emergency access
            
        Returns:
            True if emergency access granted
        """
        # Check if user has emergency role
        permission_manager = UserPermissionManager(user)
        has_emergency_role = any(
            permission_manager.has_role(role) 
            for role in self.emergency_roles
        )
        
        if not has_emergency_role:
            return False
        
        # Log emergency access request
        self._log_emergency_access(user, patient, reason)
        
        # Grant temporary access
        self._grant_emergency_access(user, patient)
        
        return True
    
    def _log_emergency_access(self, user: User, patient: User, reason: str):
        """Log emergency access request."""
        from security.audit import log_audit_event, AuditLog
        
        log_audit_event(
            user=user,
            action=AuditLog.ActionType.READ,
            obj=patient,
            description=f"Emergency access requested: {reason}",
            severity=AuditLog.Severity.HIGH,
            metadata={
                'access_type': 'emergency',
                'reason': reason,
                'patient_id': patient.id,
            }
        )
    
    def _grant_emergency_access(self, user: User, patient: User):
        """Grant temporary emergency access."""
        # This would implement temporary permission granting
        # For now, we'll just log the action
        logger.info(f"Emergency access granted to {user.username} for patient {patient.username}")


# Global permission managers
_permission_managers = {}


def get_user_permissions(user: User) -> UserPermissionManager:
    """
    Get permission manager for user.
    
    Args:
        user: User to get permissions for
        
    Returns:
        UserPermissionManager instance
    """
    global _permission_managers
    
    if user.id not in _permission_managers:
        _permission_managers[user.id] = UserPermissionManager(user)
    
    return _permission_managers[user.id]


def get_resource_permissions() -> ResourcePermissionManager:
    """
    Get resource permission manager.
    
    Returns:
        ResourcePermissionManager instance
    """
    return ResourcePermissionManager()


def get_consent_manager() -> ConsentManager:
    """
    Get consent manager.
    
    Returns:
        ConsentManager instance
    """
    return ConsentManager()


def get_emergency_access_manager() -> EmergencyAccessManager:
    """
    Get emergency access manager.
    
    Returns:
        EmergencyAccessManager instance
    """
    return EmergencyAccessManager()


# Convenience functions
def check_permission(user: User, permission: str, resource: Any = None) -> bool:
    """
    Check if user has permission.
    
    Args:
        user: User to check
        permission: Permission to check
        resource: Resource being accessed
        
    Returns:
        True if user has permission
    """
    permission_manager = get_user_permissions(user)
    return permission_manager.has_permission(permission, resource)


def check_resource_access(user: User, resource: Any, action: str) -> bool:
    """
    Check if user can access resource.
    
    Args:
        user: User requesting access
        resource: Resource being accessed
        action: Action to perform
        
    Returns:
        True if access is allowed
    """
    resource_manager = get_resource_permissions()
    return resource_manager.can_access_resource(user, resource, action)


def check_consent(patient: User, consent_type: str, provider: User = None) -> bool:
    """
    Check if patient has valid consent.
    
    Args:
        patient: Patient user
        consent_type: Type of consent required
        provider: Healthcare provider requesting access
        
    Returns:
        True if valid consent exists
    """
    consent_manager = get_consent_manager()
    return consent_manager.has_valid_consent(patient, consent_type, provider)


def request_emergency_access(user: User, patient: User, reason: str) -> bool:
    """
    Request emergency access to patient data.
    
    Args:
        user: User requesting emergency access
        patient: Patient whose data is needed
        reason: Reason for emergency access
        
    Returns:
        True if emergency access granted
    """
    emergency_manager = get_emergency_access_manager()
    return emergency_manager.request_emergency_access(user, patient, reason)


# DRF Permission Classes
from rest_framework.permissions import BasePermission


class HIPAACompliantPermission(BasePermission):
    """
    DRF permission class for HIPAA-compliant access control.
    
    This permission class enforces role-based access control
    for API endpoints handling medical data.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to access the view."""
        if not request.user.is_authenticated:
            return False
        
        # Get permission manager
        permission_manager = get_user_permissions(request.user)
        
        # Check based on view action
        action = getattr(view, 'action', None)
        
        if action == 'list':
            return self._check_list_permission(permission_manager, view)
        elif action == 'create':
            return self._check_create_permission(permission_manager, view)
        elif action in ['retrieve', 'update', 'partial_update']:
            return self._check_object_permission(permission_manager, view)
        elif action == 'destroy':
            return self._check_delete_permission(permission_manager, view)
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user has permission to access specific object."""
        if not request.user.is_authenticated:
            return False
        
        permission_manager = get_user_permissions(request.user)
        
        # Check object-specific permissions
        if hasattr(obj, 'user') and obj.user:
            return permission_manager.has_permission('view_own_patient_data', obj)
        
        return True
    
    def _check_list_permission(self, permission_manager, view):
        """Check permission for list actions."""
        # Determine data type from view
        if 'medication' in view.__class__.__name__.lower():
            return permission_manager.has_permission('view_medication_data')
        elif 'patient' in view.__class__.__name__.lower():
            return permission_manager.has_permission('view_patient_data')
        
        return True
    
    def _check_create_permission(self, permission_manager, view):
        """Check permission for create actions."""
        if 'medication' in view.__class__.__name__.lower():
            return permission_manager.has_permission('create_medication_data')
        
        return True
    
    def _check_object_permission(self, permission_manager, view):
        """Check permission for object-specific actions."""
        return True  # Will be handled by has_object_permission
    
    def _check_delete_permission(self, permission_manager, view):
        """Check permission for delete actions."""
        if 'medication' in view.__class__.__name__.lower():
            return permission_manager.has_permission('delete_medication_data')
        
        return False 