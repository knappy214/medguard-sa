"""
Custom admin site configuration for MedGuard SA.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from users.models import User


# Custom admin site
admin.site.site_header = "MedGuard SA Administration"
admin.site.site_title = "MedGuard SA Admin Portal"
admin.site.index_title = "Welcome to MedGuard SA Administration"


# User Admin
class CustomUserAdmin(UserAdmin):
    """Custom user admin with additional fields."""
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'date_joined', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        (_('MedGuard SA Info'), {
            'fields': ('user_type', 'date_of_birth', 'gender', 'phone_number', 
                      'medical_record_number', 'emergency_contact_name', 
                      'emergency_contact_phone', 'emergency_contact_relationship',
                      'primary_healthcare_provider', 'healthcare_provider_phone',
                      'preferred_language', 'timezone', 'email_notifications',
                      'sms_notifications', 'push_notifications')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('MedGuard SA Info'), {
            'fields': ('user_type', 'email_notifications', 'sms_notifications', 'push_notifications')
        }),
    )


# Register models
admin.site.register(User, CustomUserAdmin) 