"""
Wagtail 7.0.2 Optimized Development Settings for MedGuard SA

This configuration enables all latest Wagtail 7.0.2 features for development
while maintaining optimal performance and debugging capabilities.
"""

from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Enhanced allowed hosts for development
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '[::1]',  # IPv6 localhost
    'testserver',  # For Django test client
    '*.ngrok.io',  # For ngrok tunneling
    '*.localhost.run',  # For localhost tunneling
]

# =============================================================================
# WAGTAIL 7.0.2 ENHANCED FEATURES FOR DEVELOPMENT
# =============================================================================

# Wagtail 7.0.2 Enhanced Admin Interface
WAGTAIL_ENABLE_UPDATE_CHECK = True
WAGTAIL_ADMIN_TEMPLATE_CACHE = False  # Disable template caching in development
WAGTAIL_ENABLE_WHITELISTING = True
WAGTAIL_WORKFLOW_ENABLED = True
WAGTAIL_WORKFLOW_REQUIRE_PRIVACY_CHECK = False  # Relaxed for development

# Wagtail 7.0.2 Enhanced Search Configuration
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'OPTIONS': {
            'SEARCH_BACKEND': 'wagtail.search.backends.database',
            'ATOMIC_REBUILD': False,  # Faster rebuilds in development
            'AUTO_UPDATE': True,
        }
    }
}

# Wagtail 7.0.2 Enhanced Image Optimization for Development
WAGTAILIMAGES_RENDITION_STORAGE = 'django.core.files.storage.FileSystemStorage'
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB for development testing
WAGTAILIMAGES_WEBP_QUALITY = 85
WAGTAILIMAGES_AVIF_QUALITY = 80
WAGTAILIMAGES_JPEG_QUALITY = 85

# Wagtail 7.0.2 Enhanced Document Management
WAGTAILDOCS_EXTENSIONS = [
    'csv', 'docx', 'key', 'odt', 'pdf', 'pptx', 'rtf', 'txt', 'xlsx', 'zip',
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp', 'avif',  # Image formats
    'mp4', 'mov', 'avi', 'wmv', 'flv', 'webm',  # Video formats for medical content
]

# Wagtail 7.0.2 Enhanced Forms
WAGTAILFORMS_HELP_TEXT_ALLOW_HTML = True
WAGTAILFORMS_ADVANCED_SPAM_PROTECTION = True

# Wagtail 7.0.2 Enhanced Embeds
WAGTAILEMBEDS_RESPONSIVE_HTML = True
WAGTAILEMBEDS_RENDITION_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Wagtail 7.0.2 Enhanced Redirects
WAGTAIL_REDIRECTS_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# =============================================================================
# ENHANCED DATABASE CONFIGURATION FOR DEVELOPMENT
# =============================================================================

DATABASES['default'].update({
    'OPTIONS': {
        'client_encoding': 'UTF8',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        'options': {
            'isolation_level': 'read committed',
        },
    },
    'CONN_MAX_AGE': 0,  # Disable persistent connections in development
    'ATOMIC_REQUESTS': True,  # Enable atomic requests for data integrity
})

# =============================================================================
# ENHANCED CACHING CONFIGURATION FOR DEVELOPMENT
# =============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'medguard-dev-cache',
        'TIMEOUT': 300,  # 5 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 2000,
            'CULL_FREQUENCY': 3,
        }
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'medguard-sessions-cache',
        'TIMEOUT': 3600,  # 1 hour
        'OPTIONS': {
            'MAX_ENTRIES': 500,
        }
    },
    'wagtail': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'medguard-wagtail-cache',
        'TIMEOUT': 1800,  # 30 minutes
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    },
}

# =============================================================================
# ENHANCED LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'wagtail': {
            'format': 'WAGTAIL {levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'wagtail_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'wagtail_dev.log',
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 3,
            'formatter': 'wagtail',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'wagtail': {
            'handlers': ['console', 'wagtail_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'medguard_backend': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'medications': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'security': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# ENHANCED CORS SETTINGS FOR DEVELOPMENT
# =============================================================================

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'X-Security-Level',
    'X-Client-Version',
    'X-Request-Timestamp',
    'X-Wagtail-Preview',  # For Wagtail 7.0.2 preview mode
    'X-Wagtail-Workflow',  # For Wagtail 7.0.2 workflows
]

CORS_EXPOSE_HEADERS = [
    'X-Security-Level',
    'X-Client-Version',
    'X-Request-Timestamp',
    'X-Wagtail-Version',
    'X-Total-Count',
    'X-Page-Count',
]

# =============================================================================
# DEVELOPMENT-SPECIFIC EMAIL CONFIGURATION
# =============================================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_FILE_PATH = BASE_DIR / 'logs' / 'emails'

# =============================================================================
# ENHANCED DEBUG TOOLBAR CONFIGURATION
# =============================================================================

if DEBUG:
    INSTALLED_APPS += [
        'debug_toolbar',
        'django_extensions',  # For enhanced development tools
        'wagtail.contrib.styleguide',  # Wagtail 7.0.2 styleguide
    ]
    
    MIDDLEWARE = [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ] + MIDDLEWARE
    
    INTERNAL_IPS = ['127.0.0.1', 'localhost', '::1', '0.0.0.0']
    
    # Enhanced Debug Toolbar Configuration
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        'SHOW_COLLAPSED': False,  # Show expanded in development
        'SHOW_TEMPLATE_CONTEXT': True,
        'IS_RUNNING_TESTS': False,
        'ROOT_TAG_EXTRA_ATTRS': 'style="z-index: 99999"',  # Ensure toolbar is visible
    }
    
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

# =============================================================================
# ENHANCED REST FRAMEWORK CONFIGURATION FOR DEVELOPMENT
# =============================================================================

REST_FRAMEWORK.update({
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.AdminRenderer',  # Enhanced admin interface
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '1000/hour',  # Relaxed for development
        'user': '10000/hour',  # Relaxed for development
    },
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
})

# =============================================================================
# ENHANCED WAGTAIL API CONFIGURATION
# =============================================================================

WAGTAIL_APPEND_SLASH = True
WAGTAILAPI_LIMIT_MAX = 100  # Higher limit for development testing
WAGTAILAPI_USE_FRONTENDCACHE = False  # Disable in development

# =============================================================================
# ENHANCED SECURITY SETTINGS FOR DEVELOPMENT
# =============================================================================

# Relaxed security for development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Relaxed for development

# Enhanced CSRF settings for development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:5173',  # Vite development server
    'http://127.0.0.1:5173',
]

CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript access in development

# =============================================================================
# ENHANCED FILE UPLOAD SETTINGS FOR DEVELOPMENT
# =============================================================================

FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB for development
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB for development
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# =============================================================================
# ENHANCED CELERY CONFIGURATION FOR DEVELOPMENT
# =============================================================================

CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True  # Propagate exceptions
CELERY_BROKER_URL = 'memory://'  # In-memory broker for development
CELERY_RESULT_BACKEND = 'cache+memory://'

# =============================================================================
# ENHANCED SESSION CONFIGURATION
# =============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 86400  # 24 hours for development
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # Keep sessions for development

# =============================================================================
# ENHANCED STATIC/MEDIA FILES CONFIGURATION
# =============================================================================

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Enhanced media settings for development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# WAGTAIL 7.0.2 DEVELOPMENT-SPECIFIC FEATURES
# =============================================================================

# Enable Wagtail 7.0.2 preview modes
WAGTAIL_ENABLE_PREVIEW_COLLECTION = True
WAGTAIL_PREVIEW_MODE_ENABLED = True

# Enable Wagtail 7.0.2 enhanced admin
WAGTAIL_ADMIN_RECENT_EDITS_LIMIT = 20
WAGTAIL_ADMIN_GLOBAL_ACTIONS = True

# Enable Wagtail 7.0.2 workflow features
WAGTAIL_WORKFLOW_ENABLED = True
WAGTAIL_WORKFLOW_CANCEL_ON_REJECTION = False

# Enable Wagtail 7.0.2 enhanced moderation
WAGTAIL_MODERATION_ENABLED = True
WAGTAIL_ENABLE_PRIVATE_PAGES = True

# =============================================================================
# HEALTHCARE-SPECIFIC DEVELOPMENT SETTINGS
# =============================================================================

# HIPAA compliance relaxed for development
HIPAA_COMPLIANCE_MODE = 'development'
AUDIT_LOG_ENABLED = True
DATA_ENCRYPTION_ENABLED = False  # Disabled for easier development debugging

# Healthcare-specific cache timeouts
PRESCRIPTION_CACHE_TIMEOUT = 300  # 5 minutes
MEDICATION_CACHE_TIMEOUT = 600   # 10 minutes
USER_CACHE_TIMEOUT = 1800        # 30 minutes

# =============================================================================
# ENHANCED INTERNATIONALIZATION
# =============================================================================

USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [
    BASE_DIR / 'locale',
    BASE_DIR / 'medications' / 'locale',
    BASE_DIR / 'medguard_notifications' / 'locale',
]

# Enhanced language settings
LANGUAGES = [
    ('en', 'English'),
    ('af', 'Afrikaans'),
]

WAGTAIL_CONTENT_LANGUAGES = LANGUAGES
WAGTAIL_I18N_ENABLED = True

# =============================================================================
# ENHANCED DEVELOPMENT UTILITIES
# =============================================================================

# Django Extensions Configuration
SHELL_PLUS_PRINT_SQL = True
SHELL_PLUS_PRINT_SQL_TRUNCATE = None
RUNSERVER_PLUS_PRINT_SQL_TRUNCATE = None

# Enhanced development middleware
MIDDLEWARE.insert(-1, 'django.middleware.common.BrokenLinkEmailsMiddleware')

# Create logs directory if it doesn't exist
import pathlib
(BASE_DIR / 'logs').mkdir(exist_ok=True)
(BASE_DIR / 'logs' / 'emails').mkdir(exist_ok=True)

print("🏥 MedGuard SA Development Server with Wagtail 7.0.2 Optimizations Loaded!")
print("📊 Debug Toolbar: Enabled")
print("🔍 Enhanced Logging: Enabled") 
print("🚀 Wagtail 7.0.2 Features: Enabled")
print("💊 Healthcare Features: Development Mode")
