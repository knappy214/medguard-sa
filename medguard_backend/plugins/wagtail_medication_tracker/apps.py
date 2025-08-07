"""
Medication Tracker Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MedicationTrackerConfig(AppConfig):
    """Django app configuration for Medication Tracker plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_medication_tracker"
    verbose_name = _("Medication Tracker")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
        from . import signals  # noqa: F401
