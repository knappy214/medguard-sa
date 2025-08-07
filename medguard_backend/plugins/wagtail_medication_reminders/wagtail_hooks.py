"""
Wagtail Hooks for Medication Reminders Plugin
"""
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import ReminderTemplate, NotificationLog


class ReminderTemplateAdmin(ModelAdmin):
    """ModelAdmin for ReminderTemplate."""
    
    model = ReminderTemplate
    menu_label = _("Reminder Templates")
    menu_icon = "mail"
    menu_order = 900
    list_display = ["name", "reminder_type", "is_active"]
    list_filter = ["reminder_type", "is_active"]


class NotificationLogAdmin(ModelAdmin):
    """ModelAdmin for NotificationLog."""
    
    model = NotificationLog
    menu_label = _("Notification Logs")
    menu_icon = "doc-full"
    menu_order = 901
    list_display = ["user", "medication_name", "notification_type", "delivery_status", "sent_at"]
    list_filter = ["notification_type", "delivery_status", "sent_at"]


modeladmin_register(ReminderTemplateAdmin)
modeladmin_register(NotificationLogAdmin)
