"""
PWA App Configuration
"""
from django.apps import AppConfig


class PWAConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pwa'
    verbose_name = 'Progressive Web App'
    
    def ready(self):
        """Initialize PWA components when app is ready"""
        try:
            import pwa.signals  # noqa
        except ImportError:
            pass 