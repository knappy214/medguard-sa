"""
Emergency Access Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EmergencyAccessConfig(AppConfig):
    """Django app configuration for Emergency Access plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_emergency_access"
    verbose_name = _("Emergency Access")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
