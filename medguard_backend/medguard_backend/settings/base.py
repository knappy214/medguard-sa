"""
Base settings for MedGuard SA backend.

This file contains all the common settings shared across all environments.
"""

import os
from pathlib import Path
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

WAGTAIL_APPS = [
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',  # Re-enabled
    'wagtail',
    'wagtail.contrib.settings',  # For site-wide settings
    'modelcluster',
    'taggit',
]

THIRD_PARTY_APPS = [
    'django_filters',
    'rest_framework',
    'rest_framework_simplejwt',  # JWT authentication
    'corsheaders',
    'post_office',
    'push_notifications',
]

LOCAL_APPS = [
    'users',
    'medications',
    'medguard_notifications',  # Re-enabled with modern implementation
    'security',  # HIPAA-compliant security package
    'home',  # Wagtail home app
    'search',  # Wagtail search app
    'wagtail_hooks',  # Wagtail admin customizations
]

INSTALLED_APPS = DJANGO_APPS + WAGTAIL_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'security.audit.AuditMiddleware',  # HIPAA audit logging
]

ROOT_URLCONF = 'medguard_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'medguard_backend.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'medguard_sa'),
        'USER': os.getenv('DB_USER', 'medguard_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'medguard123'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'sslmode': 'disable',  # Disable SSL for development
        },
    }
}

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'users.authentication.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,  # Increased for HIPAA compliance
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Enhanced password hashing for HIPAA compliance
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported languages for Django frontend
LANGUAGES = [
    ('en', _('English')),
    ('af', _('Afrikaans')),
]

# Wagtail content languages (can be same as LANGUAGES or subset)
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Enable Wagtail internationalization
WAGTAIL_I18N_ENABLED = True

# Locale paths for translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Site ID for django.contrib.sites
SITE_ID = 1

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Wagtail settings
WAGTAIL_SITE_NAME = "MedGuard SA"

# Search
# https://docs.wagtail.org/en/stable/topics/search/backends.html
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'OPTIONS': {
            'SEARCH_BACKEND': 'wagtail.search.backends.database',
        }
    }
}

# Base URL to use when referring to full URLs within the Wagtail admin backend
WAGTAILADMIN_BASE_URL = os.getenv('WAGTAILADMIN_BASE_URL', 'http://localhost:8000')

# Allowed file extensions for documents
WAGTAILDOCS_EXTENSIONS = [
    'csv', 'docx', 'key', 'odt', 'pdf', 'pptx', 'rtf', 'txt', 'xlsx', 'zip'
]

# Wagtail API v2 configuration
WAGTAILAPI_BASE_URL = os.getenv('WAGTAILAPI_BASE_URL', 'http://localhost:8000')
WAGTAILAPI_SEARCH_ENABLED = True
WAGTAILAPI_LIMIT_MAX = 20

# Wagtail admin settings
WAGTAILADMIN_EXTERNAL_LINK_CONVERSION = 'exact'

# Django sets a maximum of 1000 fields per form by default, but particularly complex page models
# can exceed this limit within Wagtail's page editor.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# Reverse the default case-sensitive handling of tags
TAGGIT_CASE_INSENSITIVE = True

# Default storage settings
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}

# REST Framework settings with HIPAA-compliant security
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'security.jwt_auth.HIPAACompliantJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'security.permissions.HIPAACompliantPermission',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# JWT Settings for HIPAA compliance
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),  # Short lifetime for security
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://localhost:5173",  # Vite development server
    "http://127.0.0.1:5173",  # Vite development server
]

CORS_ALLOW_CREDENTIALS = True

# Allow custom HIPAA security headers
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
    'X-Security-Level',      # Custom HIPAA security header (exact case)
    'X-Client-Version',      # Custom HIPAA security header (exact case)
    'X-Request-Timestamp',   # Custom HIPAA security header (exact case)
]

# Enhanced security settings for HIPAA compliance
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# SSL/HTTPS settings (for production)
SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False').lower() == 'true'

# HSTS settings
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.getenv('SECURE_HSTS_PRELOAD', 'False').lower() == 'true'

# Content Security Policy
SECURE_CSP = {
    'default-src': ["'self'"],
    'script-src': ["'self'", "'unsafe-inline'"],
    'style-src': ["'self'", "'unsafe-inline'"],
    'img-src': ["'self'", "data:", "https:"],
    'font-src': ["'self'"],
    'connect-src': ["'self'"],
    'frame-src': ["'none'"],
    'object-src': ["'none'"],
}

# Session security settings
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE = 3600  # 1 hour for HIPAA compliance

# CSRF settings
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:5173',  # Vite development server
    'http://127.0.0.1:5173',  # Vite development server
]

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
X_CONTENT_TYPE_OPTIONS = 'nosniff'
X_XSS_PROTECTION = '1; mode=block'

# Logging configuration with security focus
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
        'security': {
            'format': 'SECURITY {levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'formatter': 'security',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'security': {
            'handlers': ['console', 'file', 'security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'wagtail': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'medguard_backend': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Email configuration
EMAIL_BACKEND = 'post_office.EmailBackend'  # Use post-office for queued emails
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@medguard-sa.com')

# Wagtail admin notification settings
WAGTAILADMIN_NOTIFICATION_FROM_EMAIL = DEFAULT_FROM_EMAIL

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Background task configuration
# Using Django's built-in async capabilities for now
# Will implement a modern task queue solution later

# Multi-tier Redis cache configuration for optimal performance
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 100,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_keepalive_options': {
                    'TCP_KEEPIDLE': 1,
                    'TCP_KEEPINTVL': 3,
                    'TCP_KEEPCNT': 5,
                }
            },
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            'MASTER_CACHE': os.getenv('REDIS_MASTER_URL', 'redis://localhost:6379/1'),
            'SLAVE_CACHE': os.getenv('REDIS_SLAVE_URL', 'redis://localhost:6379/2'),
            'REDIS_CLIENT_KWARGS': {
                'health_check_interval': 30,
                'socket_keepalive': True,
                'socket_keepalive_options': {
                    'TCP_KEEPIDLE': 1,
                    'TCP_KEEPINTVL': 3,
                    'TCP_KEEPCNT': 5,
                }
            }
        },
        'KEY_PREFIX': 'medguard_sa',
        'TIMEOUT': 300,  # 5 minutes default
        'VERSION': 1,
    },
    'sessions': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        },
        'KEY_PREFIX': 'session',
        'TIMEOUT': 3600,  # 1 hour for sessions
    },
    'medications': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 20},
        },
        'KEY_PREFIX': 'medications',
        'TIMEOUT': 1800,  # 30 minutes for medication data
    },
    'analytics': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 10},
        },
        'KEY_PREFIX': 'analytics',
        'TIMEOUT': 3600,  # 1 hour for analytics
    },
    'image_processing': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_IMAGE_URL', 'redis://localhost:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 20},
            'COMPRESSOR': 'django_redis.compressors.lz4.Lz4Compressor',
        },
        'KEY_PREFIX': 'image_processing',
        'TIMEOUT': 1800,  # 30 minutes for image processing
    },
    'celery_results': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_CELERY_URL', 'redis://localhost:6379/4'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        },
        'KEY_PREFIX': 'celery_results',
        'TIMEOUT': 7200,  # 2 hours for Celery results
    },
    'rate_limiting': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_RATE_URL', 'redis://localhost:6379/5'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 30},
        },
        'KEY_PREFIX': 'rate_limit',
        'TIMEOUT': 60,  # 1 minute for rate limiting
    },
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Admin site customization
ADMIN_SITE_HEADER = "MedGuard SA Administration"
ADMIN_SITE_TITLE = "MedGuard SA Admin Portal"
ADMIN_INDEX_TITLE = "Welcome to MedGuard SA Administration"

# =============================================================================
# HIPAA COMPLIANCE SECURITY SETTINGS
# =============================================================================

# Encryption settings
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', SECRET_KEY)
ANONYMIZATION_SALT = os.getenv('ANONYMIZATION_SALT', 'medguard_sa_anonymization_salt')

# Audit trail settings
AUDIT_LOG_RETENTION_DAYS = 2555  # 7 years for HIPAA compliance
AUDIT_LOG_ENCRYPTION = True
AUDIT_LOG_COMPRESSION = True

# Data retention settings
DATA_RETENTION_DAYS = 2555  # 7 years for HIPAA compliance
AUTOMATIC_DATA_PURGE = True
PURGE_SCHEDULE_HOURS = 24

# Access control settings
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_DURATION_MINUTES = 30
PASSWORD_EXPIRY_DAYS = 90
FORCE_PASSWORD_CHANGE_ON_FIRST_LOGIN = True

# Session security
SESSION_TIMEOUT_MINUTES = 60
INACTIVE_SESSION_TIMEOUT_MINUTES = 15
CONCURRENT_SESSION_LIMIT = 3

# API rate limiting
API_RATE_LIMIT_PER_MINUTE = 100
API_RATE_LIMIT_PER_HOUR = 1000
API_RATE_LIMIT_PER_DAY = 10000

# Data export settings
MAX_EXPORT_RECORDS = 10000
EXPORT_RETENTION_DAYS = 7
EXPORT_ENCRYPTION_REQUIRED = True

# =============================================================================
# NOTIFICATION SYSTEM CONFIGURATION
# =============================================================================

# django-nyt configuration for in-app notifications
NYT_USE_CHANNELS = True  # Enable real-time notifications via WebSockets
NYT_NOTIFICATION_MAX_DAYS = 90  # Auto-purge notifications older than 90 days
NYT_USE_JSONFIELD = True  # Use JSONField for notification data

# django-post-office configuration for email queuing
POST_OFFICE = {
    'BACKENDS': {
        'default': 'django.core.mail.backends.smtp.EmailBackend',
        'console': 'django.core.mail.backends.console.EmailBackend',
    },
    'DEFAULT_PRIORITY': 'medium',
    'LOG_LEVEL': 2,  # Log everything
    'BATCH_SIZE': 100,  # Process emails in batches of 100
    'THREADS_PER_PROCESS': 5,  # Number of threads per worker process
    'DEFAULT_LOG_LEVEL': 2,
    'CONTEXT_FIELD_CLASS': 'django.db.models.TextField',
    'TEMPLATE_ENGINE': 'django',
    'TEMPLATE_CACHE_TTL': 600,  # Cache templates for 10 minutes
}

# django-push-notifications configuration
PUSH_NOTIFICATIONS_SETTINGS = {
    'FCM_DJANGO_SETTINGS': {
        'FCM_SERVER_KEY': os.getenv('FCM_SERVER_KEY', ''),
        'DEFAULT_FIREBASE_APP': 'default',
    },
    'APNS_AUTH_KEY_PATH': os.getenv('APNS_AUTH_KEY_PATH', ''),
    'APNS_AUTH_KEY_ID': os.getenv('APNS_AUTH_KEY_ID', ''),
    'APNS_TEAM_ID': os.getenv('APNS_TEAM_ID', ''),
    'APNS_TOPIC': os.getenv('APNS_TOPIC', 'com.medguard.sa'),
    'WP_PRIVATE_KEY': os.getenv('WP_PRIVATE_KEY', ''),
    'WP_CLAIMS': {
        'sub': 'mailto:{}'.format(DEFAULT_FROM_EMAIL),
    },
}

# Notification templates and settings
NOTIFICATION_TEMPLATES = {
    'medication_reminder': {
        'email': 'notifications/email/medication_reminder.html',
        'sms': 'notifications/sms/medication_reminder.txt',
        'push': 'notifications/push/medication_reminder.json',
    },
    'stock_alert': {
        'email': 'notifications/email/stock_alert.html',
        'sms': 'notifications/sms/stock_alert.txt',
        'push': 'notifications/push/stock_alert.json',
    },
    'system_maintenance': {
        'email': 'notifications/email/system_maintenance.html',
        'sms': 'notifications/sms/system_maintenance.txt',
        'push': 'notifications/push/system_maintenance.json',
    },
    'security_alert': {
        'email': 'notifications/email/security_alert.html',
        'sms': 'notifications/sms/security_alert.txt',
        'push': 'notifications/push/security_alert.json',
    },
}

# Notification rate limiting
NOTIFICATION_RATE_LIMITS = {
    'email': {
        'per_user_per_hour': 10,
        'per_user_per_day': 50,
        'global_per_hour': 1000,
    },
    'sms': {
        'per_user_per_hour': 5,
        'per_user_per_day': 20,
        'global_per_hour': 500,
    },
    'push': {
        'per_user_per_hour': 20,
        'per_user_per_day': 100,
        'global_per_hour': 2000,
    },
} 