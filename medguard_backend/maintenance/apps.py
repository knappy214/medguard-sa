# -*- coding: utf-8 -*-
"""
MedGuard SA - Maintenance App Configuration
===========================================

Django app configuration for the Wagtail 7.0.2 healthcare maintenance module.

Author: MedGuard SA Development Team
License: Proprietary
"""

from django.apps import AppConfig


class MaintenanceConfig(AppConfig):
    """
    Configuration for the MedGuard SA healthcare maintenance application.
    
    This app provides comprehensive maintenance tools specifically designed for
    Wagtail 7.0.2 healthcare applications, ensuring optimal performance, security,
    and compliance with healthcare regulations.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'maintenance'
    verbose_name = 'Healthcare Maintenance'
    
    def ready(self):
        """
        Perform initialization when the app is ready.
        
        This method is called once Django has loaded all apps and is ready to serve requests.
        """
        # Import any signal handlers or other initialization code here
        pass
