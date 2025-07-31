"""
Development settings for MedGuard SA backend.

This file contains settings specific to the development environment.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '[::1]',  # IPv6 localhost
    'testserver',  # For Django test client
]

# Development-specific database settings
DATABASES['default']['OPTIONS']['client_encoding'] = 'UTF8'

# Development-specific email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Development-specific logging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['wagtail']['level'] = 'DEBUG'
LOGGING['loggers']['medguard_backend']['level'] = 'DEBUG'

# Development-specific CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Development-specific cache settings
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Development-specific session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Development-specific static files settings
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Development-specific media settings
MEDIA_URL = '/media/'

# Development-specific debug toolbar
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1', 'localhost', '::1']
    
    # Add CSRF exemption middleware for API endpoints
    MIDDLEWARE.insert(0, 'medguard_backend.middleware.csrf_exempt.CSRFExemptMiddleware')
    
    # Debug toolbar configuration
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        'SHOW_COLLAPSED': True,
        'SHOW_TEMPLATE_CONTEXT': True,
    }
    
    # Debug toolbar panels
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]

# Development-specific Celery settings
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Development-specific security settings
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Temporarily disable CSRF for development API testing
MIDDLEWARE = [mw for mw in MIDDLEWARE if 'csrf' not in mw.lower()]

# CSRF exemption for API endpoints in development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8080',
    'http://127.0.0.1:8080'
]

# Disable CSRF for API endpoints in development
CSRF_EXEMPT_URLS = [
    r'^/api/.*$',
]

# Development-specific Wagtail settings
WAGTAILADMIN_BASE_URL = 'http://localhost:8000'
WAGTAILAPI_BASE_URL = 'http://localhost:8000'

# Development-specific search settings
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'OPTIONS': {
            'SEARCH_BACKEND': 'wagtail.search.backends.database',
        }
    }
}

# Development-specific REST Framework settings
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Development-specific file upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440  # 2.5 MB

# Development-specific performance settings
CONN_MAX_AGE = 0  # Disable persistent connections in development 