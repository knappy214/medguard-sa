"""
Django app configuration for security module.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SecurityConfig(AppConfig):
    """
    Configuration for the security app.
    
    This app provides HIPAA-compliant security features for MedGuard SA.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'
    verbose_name = _('Security')
    
    def ready(self):
        """Initialize security components when app is ready."""
        # Import signals and other initialization code
        try:
            import security.signals  # noqa
        except ImportError:
            pass 