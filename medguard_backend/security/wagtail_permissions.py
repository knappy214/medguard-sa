"""
Wagtail 7.0.2 Enhanced Permission System for Healthcare

This module implements Wagtail 7.0.2's enhanced permission system with
healthcare-specific roles, permissions, and access controls.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Union
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from wagtail.permission_policies import ModelPermissionPolicy
from wagtail.permission_policies.base import PermissionPolicy
from wagtail.models import Page, Site
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index

User = get_user_model()
logger = logging.getLogger(__name__)


class HealthcareRole(models.Model):
    """
    Healthcare-specific roles for Wagtail 7.0.2 enhanced permission system.
    
    This model defines healthcare roles with specific permissions and access levels
    that comply with HIPAA and medical data protection requirements.
    """
    
    # Core healthcare roles
    class RoleType(models.TextChoices):
        # Clinical roles
        DOCTOR = 'doctor', _('Doctor')
        NURSE = 'nurse', _('Nurse')
        PHARMACIST = 'pharmacist', _('Pharmacist')
        PHARMACY_TECH = 'pharmacy_tech', _('Pharmacy Technician')
        
        # Administrative roles
        ADMINISTRATOR = 'administrator', _('Administrator')
        RECEPTIONIST = 'receptionist', _('Receptionist')
        BILLING_SPECIALIST = 'billing_specialist', _('Billing Specialist')
        
        # Technical roles
        IT_ADMIN = 'it_admin', _('IT Administrator')
        SYSTEM_ADMIN = 'system_admin', _('System Administrator')
        
        # Research roles
        RESEARCHER = 'researcher', _('Researcher')
        DATA_ANALYST = 'data_analyst', _('Data Analyst')
        
        # Patient roles
        PATIENT = 'patient', _('Patient')
        CAREGIVER = 'caregiver', _('Caregiver')
    
    # Access levels for HIPAA compliance
    class AccessLevel(models.TextChoices):
        NONE = 'none', _('No Access')
        OWN_DATA = 'own_data', _('Own Data Only')
        ASSIGNED_PATIENTS = 'assigned_patients', _('Assigned Patients')
        DEPARTMENT = 'department', _('Department Level')
        ORGANIZATION = 'organization', _('Organization Level')
        SYSTEM = 'system', _('System Level')
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_('Name of the healthcare role')
    )
    
    role_type = models.CharField(
        max_length=50,
        choices=RoleType.choices,
        help_text=_('Type of healthcare role')
    )
    
    description = models.TextField(
        blank=True,
        help_text=_('Description of the role and its responsibilities')
    )
    
    # HIPAA compliance settings
    access_level = models.CharField(
        max_length=30,
        choices=AccessLevel.choices,
        default=AccessLevel.NONE,
        help_text=_('Maximum data access level for this role')
    )
    
    can_view_patient_data = models.BooleanField(
        default=False,
        help_text=_('Can view patient medical data')
    )
    
    can_edit_patient_data = models.BooleanField(
        default=False,
        help_text=_('Can edit patient medical data')
    )
    
    can_prescribe_medications = models.BooleanField(
        default=False,
        help_text=_('Can prescribe medications')
    )
    
    can_dispense_medications = models.BooleanField(
        default=False,
        help_text=_('Can dispense medications')
    )
    
    can_approve_prescriptions = models.BooleanField(
        default=False,
        help_text=_('Can approve prescriptions')
    )
    
    can_access_audit_logs = models.BooleanField(
        default=False,
        help_text=_('Can access audit logs')
    )
    
    can_export_data = models.BooleanField(
        default=False,
        help_text=_('Can export patient data')
    )
    
    can_manage_users = models.BooleanField(
        default=False,
        help_text=_('Can manage user accounts')
    )
    
    can_manage_roles = models.BooleanField(
        default=False,
        help_text=_('Can manage healthcare roles')
    )
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        FieldPanel('name'),
        FieldPanel('role_type'),
        FieldPanel('description'),
        FieldPanel('access_level'),
        MultiFieldPanel([
            FieldPanel('can_view_patient_data'),
            FieldPanel('can_edit_patient_data'),
            FieldPanel('can_prescribe_medications'),
            FieldPanel('can_dispense_medications'),
            FieldPanel('can_approve_prescriptions'),
        ], heading=_('Clinical Permissions')),
        MultiFieldPanel([
            FieldPanel('can_access_audit_logs'),
            FieldPanel('can_export_data'),
            FieldPanel('can_manage_users'),
            FieldPanel('can_manage_roles'),
        ], heading=_('Administrative Permissions')),
    ]
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('name', boost=2.0),
        index.SearchField('description', boost=1.5),
        index.SearchField('role_type', boost=1.2),
        index.AutocompleteField('name'),
        index.FilterField('role_type'),
        index.FilterField('access_level'),
    ]
    
    class Meta:
        verbose_name = _('Healthcare Role')
        verbose_name_plural = _('Healthcare Roles')
        db_table = 'healthcare_roles'
        ordering = ['name']
        permissions = [
            ('assign_healthcare_role', _('Can assign healthcare roles')),
            ('view_healthcare_role_permissions', _('Can view healthcare role permissions')),
            ('audit_healthcare_roles', _('Can audit healthcare role assignments')),
        ]
    
    def __str__(self):
        return self.name
    
    def get_permissions(self) -> Set[str]:
        """Get all permissions for this role."""
        permissions = set()
        
        if self.can_view_patient_data:
            permissions.update([
                'view_patient_data',
                'view_medication_data',
                'view_prescription_data',
            ])
        
        if self.can_edit_patient_data:
            permissions.update([
                'edit_patient_data',
                'edit_medication_data',
                'edit_prescription_data',
            ])
        
        if self.can_prescribe_medications:
            permissions.update([
                'create_prescription',
                'edit_prescription',
                'view_prescription_history',
            ])
        
        if self.can_dispense_medications:
            permissions.update([
                'dispense_medication',
                'update_inventory',
                'view_inventory',
            ])
        
        if self.can_approve_prescriptions:
            permissions.update([
                'approve_prescription',
                'reject_prescription',
                'view_pending_prescriptions',
            ])
        
        if self.can_access_audit_logs:
            permissions.update([
                'view_audit_logs',
                'export_audit_data',
            ])
        
        if self.can_export_data:
            permissions.update([
                'export_patient_data',
                'export_medication_data',
                'export_prescription_data',
            ])
        
        if self.can_manage_users:
            permissions.update([
                'create_user',
                'edit_user',
                'delete_user',
                'assign_user_roles',
            ])
        
        if self.can_manage_roles:
            permissions.update([
                'create_healthcare_role',
                'edit_healthcare_role',
                'delete_healthcare_role',
                'assign_healthcare_role',
            ])
        
        return permissions


class UserHealthcareRole(models.Model):
    """
    Association between users and healthcare roles.
    
    This model manages the assignment of healthcare roles to users with
    additional context for HIPAA compliance.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='healthcare_roles',
        help_text=_('User assigned to this role')
    )
    
    role = models.ForeignKey(
        HealthcareRole,
        on_delete=models.CASCADE,
        related_name='user_assignments',
        help_text=_('Healthcare role assigned to the user')
    )
    
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_assignments_made',
        help_text=_('User who assigned this role')
    )
    
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the role was assigned')
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the role assignment expires')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether the role assignment is active')
    )
    
    # HIPAA compliance fields
    requires_annual_review = models.BooleanField(
        default=True,
        help_text=_('Whether this role requires annual review')
    )
    
    last_reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the role was last reviewed')
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_reviews_conducted',
        help_text=_('User who conducted the last review')
    )
    
    notes = models.TextField(
        blank=True,
        help_text=_('Additional notes about the role assignment')
    )
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        FieldPanel('user'),
        FieldPanel('role'),
        FieldPanel('assigned_by'),
        FieldPanel('assigned_at'),
        FieldPanel('expires_at'),
        FieldPanel('is_active'),
        MultiFieldPanel([
            FieldPanel('requires_annual_review'),
            FieldPanel('last_reviewed_at'),
            FieldPanel('reviewed_by'),
        ], heading=_('Review Settings')),
        FieldPanel('notes'),
    ]
    
    class Meta:
        verbose_name = _('User Healthcare Role')
        verbose_name_plural = _('User Healthcare Roles')
        db_table = 'user_healthcare_roles'
        unique_together = ['user', 'role']
        ordering = ['-assigned_at']
        permissions = [
            ('review_role_assignments', _('Can review role assignments')),
            ('expire_role_assignments', _('Can expire role assignments')),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    
    def is_expired(self) -> bool:
        """Check if the role assignment has expired."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def needs_review(self) -> bool:
        """Check if the role assignment needs annual review."""
        if not self.requires_annual_review:
            return False
        
        if not self.last_reviewed_at:
            return True
        
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.last_reviewed_at + timedelta(days=365)


class HealthcarePermissionPolicy(PermissionPolicy):
    """
    Wagtail 7.0.2 enhanced permission policy for healthcare data.
    
    This policy implements healthcare-specific permission checks with
    HIPAA compliance and role-based access control.
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
        
        # Filter by healthcare access level
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
        # Get user's healthcare roles
        user_roles = HealthcareRole.objects.filter(
            user_assignments__user=user,
            user_assignments__is_active=True
        )
        
        # Check access level for each role
        for role in user_roles:
            if self._check_role_instance_access(role, instance, action):
                return True
        
        return False
    
    def _check_role_instance_access(self, role: HealthcareRole, instance: Any, action: str) -> bool:
        """
        Check if role has access to specific instance.
        
        Args:
            role: Healthcare role to check
            instance: Instance to check access to
            action: Action to check
            
        Returns:
            True if role has access
        """
        # Check access level
        if role.access_level == HealthcareRole.AccessLevel.NONE:
            return False
        
        # Check if instance belongs to user (for own_data access)
        if role.access_level == HealthcareRole.AccessLevel.OWN_DATA:
            if hasattr(instance, 'user') and instance.user == role.user_assignments.first().user:
                return True
            return False
        
        # For higher access levels, check specific permissions
        if role.access_level in [
            HealthcareRole.AccessLevel.ASSIGNED_PATIENTS,
            HealthcareRole.AccessLevel.DEPARTMENT,
            HealthcareRole.AccessLevel.ORGANIZATION,
            HealthcareRole.AccessLevel.SYSTEM
        ]:
            return True
        
        return False


# Utility functions for healthcare permissions
def get_user_healthcare_roles(user: User) -> List[HealthcareRole]:
    """
    Get all active healthcare roles for a user.
    
    Args:
        user: User to get roles for
        
    Returns:
        List of active healthcare roles
    """
    return list(HealthcareRole.objects.filter(
        user_assignments__user=user,
        user_assignments__is_active=True
    ))


def assign_healthcare_role(user: User, role: HealthcareRole, assigned_by: User = None) -> UserHealthcareRole:
    """
    Assign a healthcare role to a user.
    
    Args:
        user: User to assign role to
        role: Healthcare role to assign
        assigned_by: User making the assignment
        
    Returns:
        Created UserHealthcareRole instance
    """
    with transaction.atomic():
        # Check if assignment already exists
        existing_assignment, created = UserHealthcareRole.objects.get_or_create(
            user=user,
            role=role,
            defaults={
                'assigned_by': assigned_by,
                'is_active': True,
            }
        )
        
        if not created:
            # Reactivate existing assignment
            existing_assignment.is_active = True
            existing_assignment.assigned_by = assigned_by
            existing_assignment.save()
        
        return existing_assignment


def revoke_healthcare_role(user: User, role: HealthcareRole, revoked_by: User = None) -> bool:
    """
    Revoke a healthcare role from a user.
    
    Args:
        user: User to revoke role from
        role: Healthcare role to revoke
        revoked_by: User making the revocation
        
    Returns:
        True if role was revoked
    """
    try:
        assignment = UserHealthcareRole.objects.get(user=user, role=role, is_active=True)
        assignment.is_active = False
        assignment.notes = f"Revoked by {revoked_by.username if revoked_by else 'system'}"
        assignment.save()
        return True
    except UserHealthcareRole.DoesNotExist:
        return False


def user_has_healthcare_permission(user: User, permission: str) -> bool:
    """
    Check if user has specific healthcare permission.
    
    Args:
        user: User to check permission for
        permission: Permission to check
        
    Returns:
        True if user has permission
    """
    if user.is_superuser:
        return True
    
    user_roles = get_user_healthcare_roles(user)
    
    for role in user_roles:
        if permission in role.get_permissions():
            return True
    
    return False 