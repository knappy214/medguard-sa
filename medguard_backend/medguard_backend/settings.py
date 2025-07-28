"""
Django settings for medguard_backend project.

This file imports the appropriate settings based on the environment.
For development, use: export DJANGO_SETTINGS_MODULE=medguard_backend.settings.development
For production, use: export DJANGO_SETTINGS_MODULE=medguard_backend.settings.production
"""

import os

# Set the default settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')

# Import the appropriate settings
from .settings.development import *
