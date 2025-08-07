# Wagtail 7.0.2 Setup Guide for MedGuard SA

## Overview

This guide covers the complete setup and configuration of Wagtail 7.0.2 for the MedGuard SA healthcare platform, ensuring compliance with healthcare regulations and optimal performance.

## Prerequisites

- Python 3.9+
- Django 4.2+
- PostgreSQL 12+ (required for healthcare data compliance)
- Redis (for caching and Celery)
- Node.js 18+ (for frontend assets)

## Installation

### 1. Core Dependencies

```bash
# Install Wagtail 7.0.2 and dependencies
pip install wagtail==7.0.2
pip install wagtail-localize>=1.7.0  # For i18n support (en-ZA, af-ZA)
pip install wagtail-modeladmin>=1.0.0  # For admin interface
pip install wagtail-cache>=2.2.0  # For performance optimization
```

### 2. Healthcare-Specific Extensions

```bash
# Security and compliance
pip install django-axes>=6.1.0  # Brute force protection
pip install django-csp>=3.7  # Content Security Policy
pip install django-ratelimit>=4.0.0  # Rate limiting
pip install cryptography>=41.0.0  # Encryption support

# Database and performance
pip install psycopg2-binary>=2.9.0  # PostgreSQL adapter
pip install redis>=4.6.0  # Caching and sessions
pip install celery>=5.3.0  # Background tasks
```

## Django Settings Configuration

### Base Settings (`medguard_backend/settings/base.py`)

```python
import os
from django.utils.translation import gettext_lazy as _

# Wagtail Core Apps
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Wagtail core
    'wagtail.contrib.forms',
    'wagtail.contrib.redirects',
    'wagtail.embeds',
    'wagtail.sites',
    'wagtail.users',
    'wagtail.snippets',
    'wagtail.documents',
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    
    # Wagtail extensions
    'wagtail.contrib.modeladmin',
    'wagtail.contrib.routable_page',
    'wagtail.contrib.table_block',
    'wagtail.contrib.typed_table_block',
    'wagtail.contrib.settings',
    'wagtail_localize',
    'wagtail_localize.locales',
    
    # Third-party
    'modelcluster',
    'taggit',
    'rest_framework',
    'corsheaders',
    'axes',
    'csp',
    
    # MedGuard apps
    'home',
    'medications',
    'users',
    'security',
    'privacy',
    'mobile',
    'medguard_notifications',
    
    # MedGuard Wagtail plugins
    'plugins.wagtail_medication_tracker',
    'plugins.wagtail_prescription_ocr',
    'plugins.wagtail_drug_interactions',
    'plugins.wagtail_pharmacy_locator',
    'plugins.wagtail_medical_forms',
    'plugins.wagtail_hipaa_compliance',
    'plugins.wagtail_healthcare_analytics',
    'plugins.wagtail_emergency_access',
    'plugins.wagtail_medication_reminders',
]

# Middleware configuration
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # i18n support
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',  # Brute force protection
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'wagtail.contrib.redirects.middleware.RedirectMiddleware',
    'csp.middleware.CSPMiddleware',  # Content Security Policy
    'medguard_backend.middleware.mobile.MobileUserAgentMiddleware',
]

# Database configuration (PostgreSQL required for healthcare compliance)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'medguard_db'),
        'USER': os.environ.get('DB_USER', 'medguard_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require' if os.environ.get('DB_SSL', 'false').lower() == 'true' else 'disable',
        },
    }
}

# Cache configuration (Redis)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hour for healthcare security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# Wagtail configuration
WAGTAIL_SITE_NAME = 'MedGuard SA'
WAGTAILIMAGES_IMAGE_MODEL = 'wagtailimages.Image'
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20MB
WAGTAILDOCS_DOCUMENT_MODEL = 'wagtaildocs.Document'

# Base URL configuration
WAGTAILADMIN_BASE_URL = os.environ.get('WAGTAIL_BASE_URL', 'http://localhost:8000')

# Search configuration
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'SEARCH_CONFIG': 'english',  # Can be extended for Afrikaans
    }
}

# Internationalization (i18n)
LANGUAGE_CODE = 'en-ZA'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en-ZA', _('English (South Africa)')),
    ('af-ZA', _('Afrikaans (South Africa)')),
]

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Wagtail Localize configuration
WAGTAIL_I18N_ENABLED = True
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Static files configuration
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Media files configuration
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# Security settings for healthcare compliance
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Django Axes configuration (brute force protection)
AXES_FAILURE_LIMIT = 3
AXES_COOLOFF_TIME = 1  # 1 hour
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_CALLABLE = 'axes.helpers.lockout'

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@medguard.co.za')

# Celery configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'medguard.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'wagtail': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'medguard': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

## URL Configuration

### Main URLs (`medguard_backend/urls.py`)

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.utils.translation import gettext_lazy as _

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('admin/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    
    # API endpoints
    path('api/v1/', include('api.wagtail_api')),
    path('api/mobile/', include('mobile.urls')),
    
    # Healthcare-specific endpoints
    path('medications/', include('medications.urls')),
    path('security/', include('security.urls')),
    path('privacy/', include('privacy.urls')),
    
    # Wagtail pages (catch-all - should be last)
    path('', include(wagtail_urls)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Error handlers
handler404 = 'wagtail.core.views.serve'
handler500 = 'home.views.server_error'
```

## Environment Configuration

### Development Environment (`.env`)

```env
# Database
DB_NAME=medguard_dev
DB_USER=medguard_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
DB_SSL=false

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Celery
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# Email
EMAIL_HOST=localhost
EMAIL_PORT=1025
EMAIL_USE_TLS=false
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=dev@medguard.co.za

# Wagtail
WAGTAIL_BASE_URL=http://localhost:8000

# Security
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=true
ALLOWED_HOSTS=localhost,127.0.0.1

# Healthcare compliance
HIPAA_COMPLIANCE_MODE=true
AUDIT_LOGGING=true
```

## Database Setup

### 1. Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE medguard_dev;
CREATE USER medguard_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE medguard_dev TO medguard_user;

# Grant additional permissions for healthcare compliance
ALTER USER medguard_user CREATEDB;
\q
```

### 2. Run Migrations

```bash
# Navigate to backend directory
cd medguard_backend

# Run Django migrations
python manage.py makemigrations
python manage.py migrate

# Create Wagtail superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Compile translation files
python manage.py compilemessages
```

## Initial Content Setup

### 1. Create Root Page

```bash
# Create initial Wagtail content
python manage.py shell

# In Django shell:
from wagtail.models import Page, Site
from home.models import HomePage

# Get root page
root = Page.objects.get(pk=1)

# Create homepage
homepage = HomePage(
    title="MedGuard SA - Healthcare Management",
    slug="home",
    intro="Welcome to MedGuard SA - Your comprehensive healthcare management platform"
)
root.add_child(instance=homepage)

# Set as default site
site = Site.objects.get(is_default_site=True)
site.root_page = homepage
site.save()
```

### 2. Configure Wagtail Settings

```python
# In Wagtail admin (/admin/), configure:
# 1. Site Settings -> General -> Site name: "MedGuard SA"
# 2. Settings -> Locales -> Add en-ZA and af-ZA
# 3. Settings -> Collections -> Create "Healthcare Documents"
# 4. Settings -> Groups -> Configure healthcare roles
```

## Performance Optimization

### 1. Caching Configuration

```python
# Add to settings
WAGTAIL_CACHE = True
WAGTAIL_CACHE_BACKEND = 'default'

# Cache middleware (add to MIDDLEWARE)
'wagtail.contrib.frontend_cache.middleware.FrontendCacheMiddleware',

# Cache configuration
WAGTAILFRONTENDCACHE = {
    'default': {
        'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
        'LOCATION': 'http://localhost:8000',
    },
}
```

### 2. Image Optimization

```python
# Image settings
WAGTAILIMAGES_JPEG_QUALITY = 85
WAGTAILIMAGES_WEBP_QUALITY = 85
WAGTAILIMAGES_AVIF_QUALITY = 85

# Image formats
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    'bmp': 'jpeg',
    'webp': 'webp',
}
```

## Testing Configuration

```bash
# Run tests
python manage.py test

# Run with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Next Steps

1. **Content Management**: Refer to `healthcare_content_guide.md`
2. **Security Setup**: See `wagtail_security.md`
3. **API Configuration**: Check `wagtail_api.md`
4. **Deployment**: Follow `wagtail_deployment.md`

## Troubleshooting

For common issues and solutions, refer to `wagtail_troubleshooting.md`.

## Healthcare Compliance

For HIPAA and healthcare regulatory compliance, see `wagtail_compliance.md`.
