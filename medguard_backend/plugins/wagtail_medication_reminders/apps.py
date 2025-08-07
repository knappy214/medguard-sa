"""
Medication Reminders Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MedicationRemindersConfig(AppConfig):
    """Django app configuration for Medication Reminders plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_medication_reminders"
    verbose_name = _("Medication Reminders")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
