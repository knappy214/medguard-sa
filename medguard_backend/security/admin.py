"""
Django admin configuration for MedGuard SA security models.

This module registers all security models with the Django admin interface
for healthcare-compliant management and monitoring.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
# Wagtail imports will be added later when needed

from .models import (
    SecurityEvent, HealthcareRole, UserHealthcareRole
)

# Import from other modules
from .session_management import MedicalSession
from .password_policies import PasswordPolicy, PasswordHistory, TwoFactorAuth

# Import new Wagtail 7.0.2 security models - temporarily commented out
# from .document_privacy import SecureDocument, DocumentAccessLog, PatientConsent
# from .form_security import FormSubmissionLog, RateLimitViolation
# from .admin_access_controls import HealthcareRole, AdminAccessLog
# from .patient_encryption import EncryptionKey, PatientDataLog
# from .compliance_reporting import ComplianceReport


class SecurityEventAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityEvent model.
    """
    list_display = [
        'event_type', 'user', 'ip_address', 'timestamp', 
        'severity_level', 'is_resolved'
    ]
    list_filter = [
        'event_type', 'severity', 'is_resolved', 'timestamp',
        'user__is_staff'
    ]
    search_fields = ['user__username', 'ip_address', 'target_object', 'details']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Event Information'), {
            'fields': ('event_type', 'user', 'ip_address', 'timestamp')
        }),
        (_('Details'), {
            'fields': ('target_object', 'target_id', 'details', 'severity')
        }),
        (_('Resolution'), {
            'fields': ('is_resolved', 'resolution_notes', 'resolved_by', 'resolved_at')
        }),
    )
    
    def severity_level(self, obj):
        """Display severity with color coding."""
        colors = {
            'low': 'green',
            'medium': 'orange', 
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_level.short_description = _('Severity Level')


class UserHealthcareRoleAdmin(admin.ModelAdmin):
    """
    Admin interface for UserHealthcareRole model.
    """
    list_display = [
        'user', 'role', 'assigned_at', 'is_active'
    ]
    list_filter = ['role', 'is_active', 'assigned_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['assigned_at']


class HealthcareRoleAdmin(admin.ModelAdmin):
    """
    Admin interface for HealthcareRole model.
    """
    list_display = [
        'name', 'role_type', 'access_level', 
        'can_view_patient_data', 'can_edit_patient_data'
    ]
    list_filter = ['role_type', 'access_level']
    search_fields = ['name', 'description']
    
    fieldsets = (
        (_('Role Information'), {
            'fields': ('name', 'role_type', 'description')
        }),
        (_('Access Control'), {
            'fields': ('access_level',)
        }),
        (_('Permissions'), {
            'fields': ('can_view_patient_data', 'can_edit_patient_data', 'can_prescribe_medications')
        }),
    )


class EncryptionKeyAdmin(admin.ModelAdmin):
    """
    Admin interface for EncryptionKey model.
    """
    list_display = [
        'key_id', 'key_type', 'created_at', 'expires_at', 
        'is_active', 'created_by', 'is_valid_status'
    ]
    list_filter = ['key_type', 'is_active', 'created_at']
    search_fields = ['key_id', 'created_by__username']
    readonly_fields = ['key_id', 'created_at']
    
    fieldsets = (
        (_('Key Information'), {
            'fields': ('key_id', 'key_type', 'created_by', 'created_at')
        }),
        (_('Validity'), {
            'fields': ('is_active', 'expires_at')
        }),
        (_('Metadata'), {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def is_valid_status(self, obj):
        """Display key validity status."""
        if obj.is_valid():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Invalid</span>'
            )
    is_valid_status.short_description = _('Status')


class PatientDataLogAdmin(admin.ModelAdmin):
    """
    Admin interface for PatientDataLog model.
    """
    list_display = [
        'operation', 'patient_id', 'field_name', 'user', 
        'timestamp', 'success', 'encryption_level'
    ]
    list_filter = [
        'operation', 'data_type', 'success', 'encryption_level', 'timestamp'
    ]
    search_fields = ['user__username', 'patient_id', 'field_name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        (_('Operation Details'), {
            'fields': ('operation', 'data_type', 'patient_id', 'field_name')
        }),
        (_('User & Security'), {
            'fields': ('user', 'key_id', 'encryption_level', 'ip_address')
        }),
        (_('Result'), {
            'fields': ('success', 'error_message', 'timestamp')
        }),
        (_('Additional Details'), {
            'fields': ('details',),
            'classes': ('collapse',)
        }),
    )


class FormSubmissionLogAdmin(admin.ModelAdmin):
    """
    Admin interface for FormSubmissionLog model.
    """
    list_display = [
        'form_type', 'user', 'submission_time', 'status', 
        'processing_time', 'ip_address'
    ]
    list_filter = ['form_type', 'status', 'submission_time']
    search_fields = ['user__username', 'form_type', 'ip_address']
    readonly_fields = ['submission_time', 'form_data_hash']
    date_hierarchy = 'submission_time'


class RateLimitViolationAdmin(admin.ModelAdmin):
    """
    Admin interface for RateLimitViolation model.
    """
    list_display = [
        'user', 'form_type', 'limit_type', 'ip_address', 'timestamp'
    ]
    list_filter = ['form_type', 'limit_type', 'timestamp']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


class DocumentAccessLogAdmin(admin.ModelAdmin):
    """
    Admin interface for DocumentAccessLog model.
    """
    list_display = [
        'document', 'user', 'access_type', 'timestamp', 'ip_address'
    ]
    list_filter = ['access_type', 'timestamp']
    search_fields = ['document__title', 'user__username', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


class PatientConsentAdmin(admin.ModelAdmin):
    """
    Admin interface for PatientConsent model.
    """
    list_display = [
        'patient_id', 'document_type', 'user', 'is_granted', 
        'is_active', 'expires_at', 'consent_method'
    ]
    list_filter = [
        'document_type', 'is_granted', 'is_active', 
        'consent_method', 'granted_at'
    ]
    search_fields = ['patient_id', 'user__username']
    readonly_fields = ['granted_at']
    
    def is_valid_consent(self, obj):
        """Display consent validity status."""
        if obj.is_valid():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ Invalid</span>'
            )
    is_valid_consent.short_description = _('Status')


class ComplianceReportAdmin(admin.ModelAdmin):
    """
    Admin interface for ComplianceReport model.
    """
    list_display = [
        'report_type', 'generated_by', 'generated_at', 
        'start_date', 'end_date', 'is_archived'
    ]
    list_filter = ['report_type', 'is_archived', 'generated_at']
    search_fields = ['generated_by__username', 'notes']
    readonly_fields = ['generated_at', 'report_data']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        (_('Report Information'), {
            'fields': ('report_type', 'generated_by', 'generated_at')
        }),
        (_('Period'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Status'), {
            'fields': ('is_archived', 'file_path')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Report Data'), {
            'fields': ('report_data',),
            'classes': ('collapse',)
        }),
    )


class AdminAccessLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AdminAccessLog model.
    """
    list_display = [
        'user', 'action', 'target_object', 'timestamp', 
        'ip_address', 'duration'
    ]
    list_filter = ['action', 'timestamp']
    search_fields = ['user__username', 'target_object', 'ip_address']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'


# Register existing models with Django admin
admin.site.register(SecurityEvent, SecurityEventAdmin)
admin.site.register(HealthcareRole, HealthcareRoleAdmin)
admin.site.register(UserHealthcareRole, UserHealthcareRoleAdmin)

# New models will be registered after migrations are created
# admin.site.register(HealthcareRole, HealthcareRoleAdmin)
# admin.site.register(EncryptionKey, EncryptionKeyAdmin)
# admin.site.register(PatientDataLog, PatientDataLogAdmin)
# admin.site.register(FormSubmissionLog, FormSubmissionLogAdmin)
# admin.site.register(RateLimitViolation, RateLimitViolationAdmin)
# admin.site.register(DocumentAccessLog, DocumentAccessLogAdmin)
# admin.site.register(PatientConsent, PatientConsentAdmin)
# admin.site.register(ComplianceReport, ComplianceReportAdmin)
# admin.site.register(AdminAccessLog, AdminAccessLogAdmin)

# Register remaining models with basic admin
admin.site.register(MedicalSession)
admin.site.register(PasswordPolicy)
admin.site.register(PasswordHistory)
admin.site.register(TwoFactorAuth)


# Wagtail integration will be added later when models are properly imported


# Customize admin site
admin.site.site_header = _('MedGuard SA Security Administration')
admin.site.site_title = _('MedGuard SA Security Admin')
admin.site.index_title = _('Security Management Dashboard')