from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Notification, UserNotification, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for the Notification model."""
    
    list_display = (
        'title', 'notification_type', 'priority', 'status', 
        'is_active', 'show_on_dashboard', 'created_at'
    )
    
    list_filter = (
        'notification_type', 'priority', 'status', 'is_active', 
        'show_on_dashboard', 'require_acknowledgment', 'created_at'
    )
    
    search_fields = ('title', 'content')
    
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'content', 'notification_type', 'priority', 'status')
        }),
        (_('Targeting'), {
            'fields': ('target_user_types', 'scheduled_at', 'expires_at')
        }),
        (_('Display Settings'), {
            'fields': ('is_active', 'show_on_dashboard', 'require_acknowledgment')
        }),
        (_('Metadata'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['activate_notifications', 'deactivate_notifications', 'mark_as_urgent']
    
    def activate_notifications(self, request, queryset):
        """Activate selected notifications."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Successfully activated {updated} notification(s).'
        )
    activate_notifications.short_description = _('Activate selected notifications')
    
    def deactivate_notifications(self, request, queryset):
        """Deactivate selected notifications."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {updated} notification(s).'
        )
    deactivate_notifications.short_description = _('Deactivate selected notifications')
    
    def mark_as_urgent(self, request, queryset):
        """Mark selected notifications as urgent."""
        updated = queryset.update(priority='HIGH')
        self.message_user(
            request,
            f'Successfully marked {updated} notification(s) as urgent.'
        )
    mark_as_urgent.short_description = _('Mark selected notifications as urgent')


@admin.register(UserNotification)
class UserNotificationAdmin(admin.ModelAdmin):
    """Admin interface for the UserNotification model."""
    
    list_display = (
        'user', 'notification', 'status', 'sent_at', 'read_at', 
        'acknowledged_at', 'dismissed_at'
    )
    
    list_filter = (
        'status', 'sent_at', 'read_at', 'user__user_type'
    )
    
    search_fields = (
        'user__username', 'user__first_name', 'user__last_name', 
        'notification__title'
    )
    
    ordering = ('-sent_at',)
    
    fieldsets = (
        (_('User & Notification'), {
            'fields': ('user', 'notification')
        }),
        (_('Status'), {
            'fields': ('status', 'sent_at', 'read_at', 'acknowledged_at', 'dismissed_at')
        }),
    )
    
    readonly_fields = ('sent_at', 'read_at', 'acknowledged_at', 'dismissed_at')
    
    actions = ['mark_as_read', 'mark_as_sent', 'resend_notifications']
    

    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        from django.utils import timezone
        updated = queryset.update(read_at=timezone.now())
        self.message_user(
            request,
            f'Successfully marked {updated} notification(s) as read.'
        )
    mark_as_read.short_description = _('Mark selected notifications as read')
    
    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent."""
        from django.utils import timezone
        updated = queryset.update(sent_at=timezone.now())
        self.message_user(
            request,
            f'Successfully marked {updated} notification(s) as sent.'
        )
    mark_as_sent.short_description = _('Mark selected notifications as sent')
    
    def resend_notifications(self, request, queryset):
        """Resend selected notifications."""
        from django.utils import timezone
        updated = queryset.update(sent_at=None, read_at=None)
        self.message_user(
            request,
            f'Successfully queued {updated} notification(s) for resending.'
        )
    resend_notifications.short_description = _('Resend selected notifications')


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Admin interface for the NotificationTemplate model."""
    
    list_display = (
        'name', 'template_type', 'is_active', 'created_at'
    )
    
    list_filter = (
        'template_type', 'is_active', 'created_at'
    )
    
    search_fields = ('name', 'content')
    
    ordering = ('name',)
    
    fieldsets = (
        (_('Template Information'), {
            'fields': ('name', 'template_type', 'content', 'is_active')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['activate_templates', 'deactivate_templates']
    
    def activate_templates(self, request, queryset):
        """Activate selected templates."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'Successfully activated {updated} template(s).'
        )
    activate_templates.short_description = _('Activate selected templates')
    
    def deactivate_templates(self, request, queryset):
        """Deactivate selected templates."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Successfully deactivated {updated} template(s).'
        )
    deactivate_templates.short_description = _('Deactivate selected templates')
