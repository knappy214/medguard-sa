"""
Drug Interactions Django App Configuration
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DrugInteractionsConfig(AppConfig):
    """Django app configuration for Drug Interactions plugin."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "medguard_backend.plugins.wagtail_drug_interactions"
    verbose_name = _("Drug Interactions")
    
    def ready(self):
        """Initialize the plugin when Django starts."""
        from . import wagtail_hooks  # noqa: F401
        from . import signals  # noqa: F401
