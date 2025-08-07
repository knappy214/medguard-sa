"""
Prescription OCR Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PrescriptionOCRConfig(AppConfig):
    """Django app configuration for Prescription OCR plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_prescription_ocr"
    verbose_name = _("Prescription OCR")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
