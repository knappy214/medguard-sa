"""
Pharmacy Locator Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PharmacyLocatorConfig(AppConfig):
    """Django app configuration for Pharmacy Locator plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_pharmacy_locator"
    verbose_name = _("Pharmacy Locator")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
        from . import signals  # noqa: F401
