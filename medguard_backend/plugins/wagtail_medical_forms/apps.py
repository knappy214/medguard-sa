"""
Medical Forms Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MedicalFormsConfig(AppConfig):
    """Django app configuration for Medical Forms plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_medical_forms"
    verbose_name = _("Medical Forms")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
