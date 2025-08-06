"""
Mobile app configuration for MedGuard SA
"""
from django.apps import AppConfig


class MobileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mobile'
    verbose_name = 'Mobile Optimization' 