from wagtail import hooks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel, HelpPanel
from wagtail.search import index
from .models import User, UserAvatar, UserProfile

@hooks.register('construct_user_editor_panels')
def user_panels(panels, **kwargs):
    panels[:] = [
        MultiFieldPanel([
            FieldPanel('username'),
            FieldPanel('email'),
            FieldPanel('first_name'),
            FieldPanel('last_name'),
            FieldPanel('user_type'),
        ], heading='Basic Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('phone'),
            FieldPanel('address'),
            FieldPanel('city'),
            FieldPanel('province'),
            FieldPanel('postal_code'),
        ], heading='Contact Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('date_of_birth'),
            FieldPanel('gender'),
            FieldPanel('blood_type'),
        ], heading='Personal Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('allergies'),
            FieldPanel('medical_conditions'),
            FieldPanel('current_medications'),
        ], heading='Medical Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('emergency_contact_name'),
            FieldPanel('emergency_contact_phone'),
            FieldPanel('emergency_contact_relationship'),
        ], heading='Emergency Contact', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('preferred_language'),
            FieldPanel('timezone'),
            FieldPanel('email_notifications'),
            FieldPanel('sms_notifications'),
            FieldPanel('mfa_enabled'),
        ], heading='Account Settings', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('is_active'),
            FieldPanel('is_staff'),
            FieldPanel('is_superuser'),
            FieldPanel('groups'),
            FieldPanel('user_permissions'),
        ], heading='Security & Permissions', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('date_joined'),
            FieldPanel('last_login'),
        ], heading='Timestamps', classname='collapsible'),
    ]

@hooks.register('construct_avatar_editor_panels')
def avatar_panels(panels, **kwargs):
    panels[:] = [
        MultiFieldPanel([
            FieldPanel('user'),
            FieldPanel('image'),
        ], heading='Avatar Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('created_at'),
            FieldPanel('updated_at'),
        ], heading='Timestamps', classname='collapsible'),
    ]

@hooks.register('construct_profile_editor_panels')
def profile_panels(panels, **kwargs):
    panels[:] = [
        MultiFieldPanel([
            FieldPanel('user'),
        ], heading='User Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('professional_title'),
            FieldPanel('license_number'),
            FieldPanel('specialization'),
        ], heading='Professional Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('facility_name'),
            FieldPanel('facility_address'),
            FieldPanel('facility_phone'),
        ], heading='Facility Information', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('notification_preferences'),
            FieldPanel('privacy_settings'),
        ], heading='Preferences', classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('created_at'),
            FieldPanel('updated_at'),
        ], heading='Timestamps', classname='collapsible'),
    ]
