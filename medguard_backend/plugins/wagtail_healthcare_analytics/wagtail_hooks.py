"""
Wagtail Hooks for Healthcare Analytics Plugin
"""
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import AnalyticsReport, Dashboard
from .views import AnalyticsDashboardView


class AnalyticsReportAdmin(ModelAdmin):
    """ModelAdmin for AnalyticsReport."""
    
    model = AnalyticsReport
    menu_label = _("Analytics Reports")
    menu_icon = "doc-full-inverse"
    menu_order = 1000
    list_display = ["name", "report_type", "generated_by", "generated_at"]
    list_filter = ["report_type", "generated_at"]
    ordering = ["-generated_at"]


class DashboardAdmin(ModelAdmin):
    """ModelAdmin for Dashboard."""
    
    model = Dashboard
    menu_label = _("Dashboards")
    menu_icon = "view"
    menu_order = 1001
    list_display = ["name", "created_by", "is_public", "created_at"]
    list_filter = ["is_public", "created_at"]


modeladmin_register(AnalyticsReportAdmin)
modeladmin_register(DashboardAdmin)


@hooks.register("register_admin_urls")
def register_analytics_urls():
    """Register analytics URLs."""
    return [
        path(
            "healthcare-analytics/",
            AnalyticsDashboardView.as_view(),
            name="healthcare_analytics_dashboard"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_analytics_menu():
    """Add Healthcare Analytics menu item."""
    return MenuItem(
        _("Healthcare Analytics"),
        reverse("healthcare_analytics_dashboard"),
        classname="icon icon-doc-full-inverse",
        order=1700
    )
