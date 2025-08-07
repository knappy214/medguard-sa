"""
Wagtail Hooks for Emergency Access Plugin
"""
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import EmergencyAccess, EmergencyContact
from .views import EmergencyDashboardView


class EmergencyAccessAdmin(ModelAdmin):
    """ModelAdmin for EmergencyAccess."""
    
    model = EmergencyAccess
    menu_label = _("Emergency Accesses")
    menu_icon = "warning"
    menu_order = 800
    list_display = ["accessing_user", "patient", "emergency_type", "accessed_at", "is_justified"]
    list_filter = ["emergency_type", "requires_review", "is_justified"]
    ordering = ["-accessed_at"]


modeladmin_register(EmergencyAccessAdmin)


@hooks.register("register_admin_urls")
def register_emergency_access_urls():
    """Register emergency access URLs."""
    return [
        path(
            "emergency-access/",
            EmergencyDashboardView.as_view(),
            name="emergency_access_dashboard"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_emergency_access_menu():
    """Add Emergency Access menu item."""
    return MenuItem(
        _("Emergency Access"),
        reverse("emergency_access_dashboard"),
        classname="icon icon-warning",
        order=1600
    )
