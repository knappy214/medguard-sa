from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model."""
    
    list_display = (
        'username', 'email', 'get_full_name', 'user_type', 
        'medical_record_number', 'is_active', 'date_joined'
    )
    
    list_filter = (
        'user_type', 'gender', 'is_active', 'is_staff', 'is_superuser',
        'preferred_language', 'email_notifications', 'sms_notifications',
        'push_notifications', 'date_joined'
    )
    
    search_fields = (
        'username', 'email', 'first_name', 'last_name', 
        'medical_record_number', 'phone_number'
    )
    
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal Information'), {
            'fields': (
                'first_name', 'last_name', 'email', 'user_type',
                'date_of_birth', 'gender'
            )
        }),
        (_('Contact Information'), {
            'fields': (
                'phone_number', 'emergency_contact_name', 
                'emergency_contact_phone', 'emergency_contact_relationship'
            )
        }),
        (_('Medical Information'), {
            'fields': (
                'medical_record_number', 'primary_healthcare_provider',
                'healthcare_provider_phone'
            )
        }),
        (_('Preferences'), {
            'fields': (
                'preferred_language', 'timezone', 'email_notifications',
                'sms_notifications', 'push_notifications'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2', 'user_type',
                'first_name', 'last_name', 'phone_number'
            ),
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')
    
    def get_full_name(self, obj):
        """Get the full name of the user."""
        return obj.get_full_name()
    get_full_name.short_description = _('Full Name')
    get_full_name.admin_order_field = 'first_name'
