"""
HIPAA Compliance Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HIPAAComplianceConfig(AppConfig):
    """Django app configuration for HIPAA Compliance plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_hipaa_compliance"
    verbose_name = _("HIPAA Compliance")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
        from . import signals  # noqa: F401
