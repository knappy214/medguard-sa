"""
Environment-specific configuration for MedGuard SA.

This file contains environment-specific settings for different deployment
environments (development, staging, production).
"""

import os
from .base import *

# Environment detection
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development').lower()

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
API_VERSION = os.getenv('API_VERSION', 'v1')
API_PREFIX = f'/api/{API_VERSION}'

# Security Configuration
SECURITY_SETTINGS = {
    'JWT_ACCESS_TOKEN_LIFETIME': int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 3600)),  # 1 hour
    'JWT_REFRESH_TOKEN_LIFETIME': int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 604800)),  # 7 days
    'JWT_ROTATE_REFRESH_TOKENS': os.getenv('JWT_ROTATE_REFRESH_TOKENS', 'True').lower() == 'true',
    'JWT_BLACKLIST_AFTER_ROTATION': os.getenv('JWT_BLACKLIST_AFTER_ROTATION', 'True').lower() == 'true',
    'JWT_UPDATE_LAST_LOGIN': os.getenv('JWT_UPDATE_LAST_LOGIN', 'True').lower() == 'true',
    
    # Device fingerprinting
    'DEVICE_FINGERPRINTING_ENABLED': os.getenv('DEVICE_FINGERPRINTING_ENABLED', 'True').lower() == 'true',
    'DEVICE_FINGERPRINT_CACHE_TIMEOUT': int(os.getenv('DEVICE_FINGERPRINT_CACHE_TIMEOUT', 3600)),
    
    # Rate limiting
    'RATE_LIMIT_ENABLED': os.getenv('RATE_LIMIT_ENABLED', 'True').lower() == 'true',
    'RATE_LIMIT_PER_MINUTE': int(os.getenv('RATE_LIMIT_PER_MINUTE', 100)),
    'RATE_LIMIT_PER_HOUR': int(os.getenv('RATE_LIMIT_PER_HOUR', 1000)),
    'RATE_LIMIT_PER_DAY': int(os.getenv('RATE_LIMIT_PER_DAY', 10000)),
    
    # Audit logging
    'AUDIT_LOGGING_ENABLED': os.getenv('AUDIT_LOGGING_ENABLED', 'True').lower() == 'true',
    'AUDIT_LOG_RETENTION_DAYS': int(os.getenv('AUDIT_LOG_RETENTION_DAYS', 2555)),  # 7 years
    'AUDIT_LOG_ENCRYPTION': os.getenv('AUDIT_LOG_ENCRYPTION', 'True').lower() == 'true',
    
    # Session security
    'SESSION_TIMEOUT_MINUTES': int(os.getenv('SESSION_TIMEOUT_MINUTES', 60)),
    'INACTIVE_SESSION_TIMEOUT_MINUTES': int(os.getenv('INACTIVE_SESSION_TIMEOUT_MINUTES', 15)),
    'CONCURRENT_SESSION_LIMIT': int(os.getenv('CONCURRENT_SESSION_LIMIT', 3)),
    
    # Password security
    'PASSWORD_EXPIRY_DAYS': int(os.getenv('PASSWORD_EXPIRY_DAYS', 90)),
    'MAX_LOGIN_ATTEMPTS': int(os.getenv('MAX_LOGIN_ATTEMPTS', 5)),
    'LOGIN_LOCKOUT_DURATION_MINUTES': int(os.getenv('LOGIN_LOCKOUT_DURATION_MINUTES', 30)),
}

# Update JWT settings with environment-specific values
SIMPLE_JWT.update({
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=SECURITY_SETTINGS['JWT_ACCESS_TOKEN_LIFETIME']),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=SECURITY_SETTINGS['JWT_REFRESH_TOKEN_LIFETIME']),
    'ROTATE_REFRESH_TOKENS': SECURITY_SETTINGS['JWT_ROTATE_REFRESH_TOKENS'],
    'BLACKLIST_AFTER_ROTATION': SECURITY_SETTINGS['JWT_BLACKLIST_AFTER_ROTATION'],
    'UPDATE_LAST_LOGIN': SECURITY_SETTINGS['JWT_UPDATE_LAST_LOGIN'],
})

# Update rate limiting settings
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'].update({
    'anon': f"{SECURITY_SETTINGS['RATE_LIMIT_PER_MINUTE']}/minute",
    'user': f"{SECURITY_SETTINGS['RATE_LIMIT_PER_HOUR']}/hour",
})

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
]

# Add environment-specific CORS origins
if ENVIRONMENT == 'production':
    CORS_ALLOWED_ORIGINS.extend([
        os.getenv('FRONTEND_URL', 'https://medguard-sa.com'),
        os.getenv('MOBILE_APP_URL', 'https://app.medguard-sa.com'),
    ])
elif ENVIRONMENT == 'staging':
    CORS_ALLOWED_ORIGINS.extend([
        os.getenv('STAGING_FRONTEND_URL', 'https://staging.medguard-sa.com'),
        os.getenv('STAGING_MOBILE_APP_URL', 'https://staging-app.medguard-sa.com'),
    ])

# CSRF Configuration
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS.copy()

# Database Configuration
if ENVIRONMENT == 'production':
    DATABASES['default'].update({
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'NAME': os.getenv('DB_NAME', 'medguard_sa_prod'),
        'USER': os.getenv('DB_USER', 'medguard_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'sslmode': 'require',  # Require SSL in production
        }
    })
elif ENVIRONMENT == 'staging':
    DATABASES['default'].update({
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'NAME': os.getenv('DB_NAME', 'medguard_sa_staging'),
        'USER': os.getenv('DB_USER', 'medguard_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'sslmode': 'prefer',  # Prefer SSL in staging
        }
    })

# Cache Configuration
if ENVIRONMENT == 'production':
    CACHES['default'].update({
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'SOCKET_KEEPALIVE': True,
            'SOCKET_KEEPALIVE_OPTIONS': {
                'TCP_KEEPIDLE': 1,
                'TCP_KEEPINTVL': 3,
                'TCP_KEEPCNT': 5,
            }
        }
    })

# Email Configuration
if ENVIRONMENT == 'production':
    EMAIL_BACKEND = 'post_office.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@medguard-sa.com')
elif ENVIRONMENT == 'staging':
    EMAIL_BACKEND = 'post_office.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@staging.medguard-sa.com')
else:
    # Development - use console backend
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Logging Configuration
if ENVIRONMENT == 'production':
    LOGGING['handlers']['file'].update({
        'level': 'WARNING',
        'filename': '/var/log/medguard-sa/django.log',
    })
    LOGGING['handlers']['security_file'].update({
        'level': 'WARNING',
        'filename': '/var/log/medguard-sa/security.log',
    })
elif ENVIRONMENT == 'staging':
    LOGGING['handlers']['file'].update({
        'level': 'INFO',
        'filename': '/var/log/medguard-sa-staging/django.log',
    })
    LOGGING['handlers']['security_file'].update({
        'level': 'INFO',
        'filename': '/var/log/medguard-sa-staging/security.log',
    })

# Security Headers
if ENVIRONMENT in ['production', 'staging']:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Debug Settings
DEBUG = ENVIRONMENT == 'development'
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG

# Allowed Hosts
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]

if ENVIRONMENT == 'production':
    ALLOWED_HOSTS.extend([
        'medguard-sa.com',
        'www.medguard-sa.com',
        'api.medguard-sa.com',
    ])
elif ENVIRONMENT == 'staging':
    ALLOWED_HOSTS.extend([
        'staging.medguard-sa.com',
        'api-staging.medguard-sa.com',
    ])

# Add environment-specific allowed hosts
env_allowed_hosts = os.getenv('ALLOWED_HOSTS', '').split(',')
if env_allowed_hosts and env_allowed_hosts[0]:
    ALLOWED_HOSTS.extend([host.strip() for host in env_allowed_hosts])

# Static Files Configuration
if ENVIRONMENT == 'production':
    STATIC_ROOT = '/var/www/medguard-sa/staticfiles/'
    MEDIA_ROOT = '/var/www/medguard-sa/media/'
elif ENVIRONMENT == 'staging':
    STATIC_ROOT = '/var/www/medguard-sa-staging/staticfiles/'
    MEDIA_ROOT = '/var/www/medguard-sa-staging/media/'

# Wagtail Configuration
if ENVIRONMENT == 'production':
    WAGTAILADMIN_BASE_URL = 'https://medguard-sa.com'
    WAGTAILAPI_BASE_URL = 'https://api.medguard-sa.com'
elif ENVIRONMENT == 'staging':
    WAGTAILADMIN_BASE_URL = 'https://staging.medguard-sa.com'
    WAGTAILAPI_BASE_URL = 'https://api-staging.medguard-sa.com'
else:
    WAGTAILADMIN_BASE_URL = 'http://localhost:8000'
    WAGTAILAPI_BASE_URL = 'http://localhost:8000'

# API Endpoints Configuration
API_ENDPOINTS = {
    'auth': {
        'login': f'{API_PREFIX}/auth/login/',
        'refresh': f'{API_PREFIX}/auth/refresh/',
        'logout': f'{API_PREFIX}/auth/logout/',
        'verify': f'{API_PREFIX}/auth/verify/',
    },
    'security': {
        'log': f'{API_PREFIX}/security/log/',
        'dashboard': f'{API_PREFIX}/security/dashboard/',
        'audit_logs': f'{API_PREFIX}/security/audit-logs/',
        'security_events': f'{API_PREFIX}/security/security-events/',
    },
    'users': {
        'profile': f'{API_PREFIX}/users/me/',
        'users': f'{API_PREFIX}/users/users/',
    },
    'medications': {
        'list': f'{API_PREFIX}/medications/',
        'detail': f'{API_PREFIX}/medications/{{id}}/',
    },
}

# Notification Configuration
if ENVIRONMENT == 'production':
    PUSH_NOTIFICATIONS_SETTINGS.update({
        'FCM_DJANGO_SETTINGS': {
            'FCM_SERVER_KEY': os.getenv('FCM_SERVER_KEY', ''),
            'DEFAULT_FIREBASE_APP': 'default',
        },
        'APNS_AUTH_KEY_PATH': os.getenv('APNS_AUTH_KEY_PATH', ''),
        'APNS_AUTH_KEY_ID': os.getenv('APNS_AUTH_KEY_ID', ''),
        'APNS_TEAM_ID': os.getenv('APNS_TEAM_ID', ''),
        'APNS_TOPIC': os.getenv('APNS_TOPIC', 'com.medguard.sa'),
    })

# Celery Configuration
if ENVIRONMENT == 'production':
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_ALWAYS_EAGER = False
elif ENVIRONMENT == 'staging':
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
    CELERY_TASK_ALWAYS_EAGER = False
else:
    # Development - use eager execution
    CELERY_TASK_ALWAYS_EAGER = True

# Environment-specific settings
if ENVIRONMENT == 'production':
    # Production-specific settings
    pass
elif ENVIRONMENT == 'staging':
    # Staging-specific settings
    pass
else:
    # Development-specific settings
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    
    # Development email backend
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' 