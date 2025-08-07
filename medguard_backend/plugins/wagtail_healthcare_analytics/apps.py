"""
Healthcare Analytics Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HealthcareAnalyticsConfig(AppConfig):
    """Django app configuration for Healthcare Analytics plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_healthcare_analytics"
    verbose_name = _("Healthcare Analytics")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
