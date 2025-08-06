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

# Medical session management settings
MEDICAL_SESSION_TIMEOUT = int(os.getenv('MEDICAL_SESSION_TIMEOUT', '8'))  # Hours
MEDICAL_SESSION_MAX_ACTIVE = int(os.getenv('MEDICAL_SESSION_MAX_ACTIVE', '3'))  # Max active sessions per user

# Healthcare Security Settings - Wagtail 7.0.2
HEALTHCARE_ENCRYPTION_KEY = os.getenv('HEALTHCARE_ENCRYPTION_KEY', '')
HEALTHCARE_ENCRYPTION_SALT = os.getenv('HEALTHCARE_ENCRYPTION_SALT', b'medguard_salt_2024')

# Patient Data Encryption Settings
PATIENT_DATA_ENCRYPTION = {
    'ALGORITHM': 'AES-256-GCM',
    'KEY_ROTATION_DAYS': int(os.getenv('KEY_ROTATION_DAYS', '90')),
    'BACKUP_KEYS_COUNT': int(os.getenv('BACKUP_KEYS_COUNT', '3')),
    'ENCRYPTION_REQUIRED_FIELDS': [
        'ssn', 'social_security_number', 'credit_card', 'card_number',
        'medical_record_number', 'diagnosis', 'treatment_plan',
        'medication_list', 'allergies', 'family_history', 'genetic_info'
    ]
}

# Form Security Settings
FORM_SECURITY = {
    'RATE_LIMITS': {
        'default': int(os.getenv('FORM_RATE_LIMIT_DEFAULT', '10')),  # per minute
        'prescription': int(os.getenv('FORM_RATE_LIMIT_PRESCRIPTION', '5')),
        'critical': int(os.getenv('FORM_RATE_LIMIT_CRITICAL', '2')),
    },
    'VALIDATION': {
        'max_field_length': int(os.getenv('MAX_FIELD_LENGTH', '10000')),
        'suspicious_patterns_enabled': True,
        'injection_detection_enabled': True,
    }
}

# Admin Access Control Settings
ADMIN_ACCESS_CONTROL = {
    'SESSION_TIMEOUT_MINUTES': int(os.getenv('ADMIN_SESSION_TIMEOUT', '30')),
    'MAX_FAILED_ATTEMPTS': int(os.getenv('ADMIN_MAX_FAILED_ATTEMPTS', '5')),
    'LOCKOUT_DURATION_MINUTES': int(os.getenv('ADMIN_LOCKOUT_DURATION', '15')),
    'REQUIRE_2FA_FOR_ADMIN': os.getenv('REQUIRE_2FA_FOR_ADMIN', 'True').lower() == 'true',
}

# Document Privacy Settings
DOCUMENT_PRIVACY = {
    'DEFAULT_PRIVACY_LEVEL': os.getenv('DEFAULT_PRIVACY_LEVEL', 'internal'),
    'ENCRYPTION_FOR_CONFIDENTIAL': True,
    'AUDIT_ALL_ACCESS': True,
    'PATIENT_CONSENT_REQUIRED': ['confidential', 'restricted'],
}

# Compliance Reporting Settings
COMPLIANCE_REPORTING = {
    'AUTO_GENERATE_REPORTS': True,
    'REPORT_RETENTION_DAYS': int(os.getenv('REPORT_RETENTION_DAYS', '2555')),  # 7 years
    'HIPAA_COMPLIANCE_THRESHOLD': float(os.getenv('HIPAA_COMPLIANCE_THRESHOLD', '0.9')),
    'ALERT_ON_NON_COMPLIANCE': True,
}

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
    'forms',  # Wagtail 7.0.2 form pages
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
    # New Wagtail 7.0.2 Security Middleware
    'security.form_security.FormSecurityMiddleware',  # Enhanced form security
    # 'security.admin_access_controls.SecureAdminAccessMiddleware',  # Admin access controls - temporarily disabled
    'security.patient_encryption.PatientDataEncryptionMiddleware',  # Patient data encryption
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
        'NAME': 'security.password_validators.HealthcarePasswordValidator',
    },
    {
        'NAME': 'security.password_validators.HIPAACompliantPasswordValidator',
    },
    {
        'NAME': 'security.password_validators.MedicalDataPasswordValidator',
    },
    {
        'NAME': 'security.password_validators.TwoFactorPasswordValidator',
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
LANGUAGE_CODE = 'en-ZA'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Supported languages for Django frontend (Wagtail 7.0.2 enhanced)
LANGUAGES = [
    ('en-ZA', _('English (South Africa)')),
    ('af-ZA', _('Afrikaans (South Africa)')),
]

# Wagtail 7.0.2 enhanced content languages configuration
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Enable Wagtail 7.0.2 enhanced internationalization
WAGTAIL_I18N_ENABLED = True

# Wagtail 7.0.2 enhanced translation settings
WAGTAIL_I18N_CONFIG = {
    'default_language': 'en-ZA',
    'fallback_language': 'en-ZA',
    'translation_workflow_enabled': True,
    'content_synchronization': True,
    'professional_translation_tools': True,
    'translation_memory': True,
    'quality_assurance': True,
    'page_translation': {
        'enabled': True,
        'synchronization': True,
        'auto_translate': False,
        'translation_memory_enabled': True,
        'content_validation': True,
        'workflow_approval': True,
    },
    'content_sync': {
        'enabled': True,
        'auto_sync_structure': True,
        'sync_metadata': True,
        'sync_images': True,
        'sync_documents': True,
        'sync_forms': True,
        'conflict_resolution': 'source_wins',
    },
    'translation_workflow': {
        'enabled': True,
        'stages': ['draft', 'review', 'approved', 'published'],
        'approvers': ['translators', 'editors', 'managers'],
        'auto_approval': False,
        'quality_checks': True,
    },
}

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

# =============================================================================
# WAGTAIL 7.0.2 ENHANCED CONFIGURATION
# =============================================================================

# Universal Listings feature for medication catalogs
WAGTAIL_UNIVERSAL_LISTINGS_ENABLED = True
WAGTAIL_UNIVERSAL_LISTINGS_CONFIG = {
    'medications': {
        'model': 'medications.Medication',
        'title_field': 'name',
        'description_field': 'description',
        'image_field': 'image',
        'search_fields': ['name', 'description', 'active_ingredient', 'manufacturer'],
        'filter_fields': ['category', 'manufacturer', 'is_prescription_required'],
        'sort_fields': ['name', 'created_at', 'updated_at'],
        'list_template': 'medications/universal_listing.html',
        'detail_template': 'medications/universal_detail.html',
        'per_page': 20,
        'cache_timeout': 300,  # 5 minutes
    },
    'prescriptions': {
        'model': 'medications.Prescription',
        'title_field': 'medication__name',
        'description_field': 'dosage_instructions',
        'search_fields': ['medication__name', 'dosage_instructions', 'prescriber_name'],
        'filter_fields': ['status', 'prescriber_name', 'created_at'],
        'sort_fields': ['created_at', 'medication__name', 'status'],
        'list_template': 'medications/prescription_listing.html',
        'detail_template': 'medications/prescription_detail.html',
        'per_page': 15,
        'cache_timeout': 180,  # 3 minutes
    }
}

# Enhanced Stimulus-powered admin interface
WAGTAILADMIN_STIMULUS_ENABLED = True
WAGTAILADMIN_STIMULUS_CONFIG = {
    'controllers': {
        'medication-form': {
            'auto_save': True,
            'auto_save_interval': 30000,  # 30 seconds
            'validation_delay': 500,  # 500ms
        },
        'prescription-workflow': {
            'step_transitions': True,
            'progress_tracking': True,
        },
        'search-interface': {
            'instant_search': True,
            'search_delay': 300,  # 300ms
            'highlight_results': True,
        }
    },
    'enhanced_ui': {
        'dark_mode_toggle': True,
        'responsive_sidebar': True,
        'keyboard_shortcuts': True,
        'drag_and_drop': True,
        'auto_complete': True,
    }
}

# Improved StreamField with better block performance
WAGTAIL_STREAMFIELD_ENHANCED = True
WAGTAIL_STREAMFIELD_CONFIG = {
    'lazy_loading': True,
    'block_cache_timeout': 600,  # 10 minutes
    'max_blocks_per_stream': 50,
    'auto_save_drafts': True,
    'collapsible_blocks': True,
    'block_templates': {
        'medication_info': 'medications/blocks/medication_info.html',
        'dosage_schedule': 'medications/blocks/dosage_schedule.html',
        'side_effects': 'medications/blocks/side_effects.html',
        'interactions': 'medications/blocks/interactions.html',
    },
    'performance_optimizations': {
        'preload_related': True,
        'select_related': True,
        'batch_size': 20,
        'memory_limit': '256MB',
    }
}

# Responsive image optimizations with modern formats
WAGTAILIMAGES_EXTENSIONS = ['gif', 'jpg', 'jpeg', 'png', 'webp', 'avif']
WAGTAILIMAGES_FORMAT_CONVERSIONS = {
    'png': ['webp', 'avif'],
    'jpg': ['webp', 'avif'],
    'jpeg': ['webp', 'avif'],
}

WAGTAILIMAGES_RESPONSIVE_CONFIG = {
    'breakpoints': {
        'xs': 480,
        'sm': 768,
        'md': 1024,
        'lg': 1280,
        'xl': 1920,
    },
    'quality': {
        'webp': 85,
        'avif': 80,
        'jpeg': 90,
        'png': 95,
    },
    'sizes': {
        'thumbnail': {'width': 150, 'height': 150},
        'small': {'width': 300, 'height': 200},
        'medium': {'width': 600, 'height': 400},
        'large': {'width': 1200, 'height': 800},
        'hero': {'width': 1920, 'height': 1080},
    },
    'art_direction': True,
    'lazy_loading': True,
    'preload_critical': True,
    'format_selection': {
        'webp_support': True,
        'avif_support': True,
        'fallback_format': 'jpeg',
    }
}

# Enhanced PostgreSQL search with better ranking
WAGTAILSEARCH_BACKENDS = {
    'default': {
        'BACKEND': 'wagtail.search.backends.database',
        'OPTIONS': {
            'SEARCH_BACKEND': 'wagtail.search.backends.database',
            'AUTO_UPDATE': True,
            'INDEX_UPDATE_FREQUENCY': 300,  # 5 minutes
        }
    },
    'postgresql': {
        'BACKEND': 'wagtail.search.backends.database',
        'OPTIONS': {
            'SEARCH_BACKEND': 'wagtail.search.backends.database',
            'AUTO_UPDATE': True,
            'INDEX_UPDATE_FREQUENCY': 300,
            'POSTGRESQL_CONFIG': {
                'search_config': 'english',
                'rank_weights': {
                    'A': 1.0,  # Title matches
                    'B': 0.4,  # First paragraph matches
                    'C': 0.2,  # Remaining content matches
                    'D': 0.1,  # Tag matches
                },
                'full_text_search': True,
                'trigram_similarity': True,
                'fuzzy_matching': True,
                'fuzzy_threshold': 0.3,
                'highlighting': True,
                'suggestions': True,
                'autocomplete': True,
                'boost_fields': {
                    'medication__name': 2.0,
                    'medication__active_ingredient': 1.5,
                    'medication__manufacturer': 1.2,
                    'dosage_instructions': 1.0,
                    'prescriber_name': 0.8,
                }
            }
        }
    }
}

# Enhanced search configuration for medications
WAGTAILSEARCH_INDEX_MODELS = {
    'medications.Medication': {
        'fields': [
            'name',
            'active_ingredient',
            'description',
            'manufacturer',
            'category__name',
            'tags__name',
        ],
        'boost_fields': {
            'name': 2.0,
            'active_ingredient': 1.5,
            'manufacturer': 1.2,
        },
        'autocomplete_fields': ['name', 'active_ingredient'],
        'suggest_fields': ['name', 'manufacturer'],
    },
    'medications.Prescription': {
        'fields': [
            'medication__name',
            'dosage_instructions',
            'prescriber_name',
            'patient_notes',
        ],
        'boost_fields': {
            'medication__name': 2.0,
            'dosage_instructions': 1.5,
            'prescriber_name': 1.2,
        },
        'autocomplete_fields': ['medication__name', 'prescriber_name'],
    }
}

# Wagtail admin performance optimizations
WAGTAILADMIN_PERFORMANCE = {
    'lazy_loading': True,
    'infinite_scroll': True,
    'virtual_scrolling': True,
    'debounced_search': True,
    'search_delay': 300,  # 300ms
    'cache_admin_views': True,
    'cache_timeout': 300,  # 5 minutes
    'preload_related': True,
    'select_related': True,
    'batch_size': 50,
}

# Enhanced admin interface features
WAGTAILADMIN_ENHANCED_FEATURES = {
    'bulk_actions': True,
    'advanced_filters': True,
    'custom_dashboards': True,
    'workflow_visualization': True,
    'audit_trail': True,
    'version_control': True,
    'collaborative_editing': True,
    'real_time_updates': True,
}

# Wagtail API v2 enhanced configuration
WAGTAILAPI_BASE_URL = os.getenv('WAGTAILAPI_BASE_URL', 'http://localhost:8000')
WAGTAILAPI_SEARCH_ENABLED = True
WAGTAILAPI_LIMIT_MAX = 50  # Increased from 20
WAGTAILAPI_LIMIT_DEFAULT = 20
WAGTAILAPI_FIELDS_EXCLUDE = ['password', 'secret_key', 'api_key']
WAGTAILAPI_USE_FIELDS_EXCLUDE = True

# Enhanced API configuration
WAGTAILAPI_ENHANCED = {
    'caching': True,
    'cache_timeout': 300,  # 5 minutes
    'rate_limiting': True,
    'rate_limit_per_minute': 100,
    'compression': True,
    'pagination': {
        'type': 'cursor',
        'page_size': 20,
        'max_page_size': 100,
    },
    'filtering': {
        'enabled': True,
        'operators': ['exact', 'iexact', 'contains', 'icontains', 'in', 'gt', 'gte', 'lt', 'lte'],
    },
    'ordering': {
        'enabled': True,
        'default': '-created_at',
    },
    'search': {
        'enabled': True,
        'backend': 'postgresql',
        'highlighting': True,
        'suggestions': True,
    }
}

# Wagtail admin notification settings (will be set after DEFAULT_FROM_EMAIL is defined)

# Enhanced admin settings
WAGTAILADMIN_EXTERNAL_LINK_CONVERSION = 'exact'
WAGTAILADMIN_ADDITIONAL_USER_PERMISSIONS = [
    'medications.add_medication',
    'medications.change_medication',
    'medications.delete_medication',
    'medications.view_medication',
    'medications.add_prescription',
    'medications.change_prescription',
    'medications.delete_prescription',
    'medications.view_prescription',
]

# Wagtail workflow and moderation
WAGTAIL_WORKFLOW_ENABLED = True
WAGTAIL_MODERATION_ENABLED = True
WAGTAIL_WORKFLOW_REQUIRE_REAPPROVAL_ON_EDIT = True

# Enhanced document handling
WAGTAILDOCS_EXTENSIONS = [
    'csv', 'docx', 'key', 'odt', 'pdf', 'pptx', 'rtf', 'txt', 'xlsx', 'zip'
]
WAGTAILDOCS_DOCUMENT_MODEL = 'wagtaildocs.Document'
WAGTAILDOCS_SERVE_METHOD = 'direct'  # or 'redirect'
WAGTAILDOCS_INLINE_VIEW_METHOD = 'direct'

# Enhanced image handling
WAGTAILIMAGES_IMAGE_MODEL = 'wagtailimages.Image'
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
WAGTAILIMAGES_MAX_IMAGE_PIXELS = 128 * 1024 * 1024  # 128MP
WAGTAILIMAGES_FEATURE_DETECTION_ENABLED = True
WAGTAILIMAGES_JPEG_QUALITY = 85
WAGTAILIMAGES_WEBP_QUALITY = 85
WAGTAILIMAGES_AVIF_QUALITY = 80

# Enhanced snippet handling
WAGTAIL_SNIPPETS_ENABLED = True
WAGTAIL_SNIPPETS_ORDER_BY = 'title'
WAGTAIL_SNIPPETS_PER_PAGE = 20

# Enhanced user management
WAGTAIL_USERS_PASSWORD_REQUIRED = True
WAGTAIL_USERS_PASSWORD_VALIDATION = 'django.contrib.auth.password_validation.validate_password'
WAGTAIL_USERS_AVATAR_UPLOAD_DIR = 'avatars/'
WAGTAIL_USERS_AVATAR_STORAGE = 'default'

# Enhanced forms handling
WAGTAIL_FORMS_ENABLED = True
WAGTAIL_FORMS_CSV_EXPORT_ENABLED = True
WAGTAIL_FORMS_CSV_EXPORT_ENCODING = 'utf-8'
WAGTAIL_FORMS_CSV_EXPORT_FILENAME_PATTERN = 'form-{page.slug}-{timestamp}'

# Enhanced redirects handling
WAGTAIL_REDIRECTS_ENABLED = True
WAGTAIL_REDIRECTS_IMPORT_FROM_CSV = True
WAGTAIL_REDIRECTS_CSV_IMPORT_ENCODING = 'utf-8'

# Enhanced sites handling
WAGTAIL_SITES_ENABLED = True
WAGTAIL_SITES_DEFAULT_SITE_ID = 1

# Enhanced embeds handling
WAGTAIL_EMBEDS_ENABLED = True
WAGTAIL_EMBEDS_FINDERS = [
    {
        'class': 'wagtail.embeds.finders.oembed',
    }
]
WAGTAIL_EMBEDS_CACHE_TIMEOUT = 3600  # 1 hour

# Enhanced settings handling
WAGTAIL_SETTINGS_ENABLED = True
WAGTAIL_SETTINGS_MODEL = 'wagtail.contrib.settings.models.BaseSetting'

# Enhanced modeladmin handling
WAGTAIL_MODELADMIN_ENABLED = True
WAGTAIL_MODELADMIN_ORDER_BY = 'title'
WAGTAIL_MODELADMIN_PER_PAGE = 20

# Enhanced search handling
WAGTAIL_SEARCH_ENABLED = True
WAGTAIL_SEARCH_RESULTS_TEMPLATE = 'search/search_results.html'
WAGTAIL_SEARCH_RESULTS_PER_PAGE = 20

# Enhanced admin interface customization
WAGTAILADMIN_BASE_URL = os.getenv('WAGTAILADMIN_BASE_URL', 'http://localhost:8000')

# Enhanced admin branding
WAGTAILADMIN_BRANDING = {
    'logo': '/static/images/medguard-logo.svg',
    'logo_alt': 'MedGuard SA',
    'favicon': '/static/images/favicon.ico',
    'wordmark': 'MedGuard SA',  # Fix for template variable error
    'classname': 'medguard-branding',  # Fix for template variable error
    'brand_colors': {
        'primary': '#2563EB',
        'secondary': '#10B981',
        'accent': '#F59E0B',
        'warning': '#EF4444',
    }
}

# Enhanced admin navigation
WAGTAILADMIN_NAVIGATION = {
    'collapsible': True,
    'search_enabled': True,
    'recent_pages': True,
    'favorites': True,
    'help_text': True,
}

# Enhanced admin dashboard
WAGTAILADMIN_DASHBOARD = {
    'widgets': [
        'wagtail.admin.widgets.pages.WelcomePanel',
        'wagtail.admin.widgets.pages.RecentPagesPanel',
        'wagtail.admin.widgets.pages.SiteSummaryPanel',
        'medications.widgets.MedicationSummaryPanel',
        'medications.widgets.PrescriptionSummaryPanel',
        'security.widgets.SecuritySummaryPanel',
    ],
    'custom_widgets': {
        'medication_summary': 'medications.widgets.MedicationSummaryWidget',
        'prescription_summary': 'medications.widgets.PrescriptionSummaryWidget',
        'security_summary': 'security.widgets.SecuritySummaryWidget',
    }
}

# Enhanced admin permissions
WAGTAILADMIN_PERMISSIONS = {
    'medication_management': [
        'medications.add_medication',
        'medications.change_medication',
        'medications.delete_medication',
        'medications.view_medication',
    ],
    'prescription_management': [
        'medications.add_prescription',
        'medications.change_prescription',
        'medications.delete_prescription',
        'medications.view_prescription',
    ],
    'security_management': [
        'security.view_securityevent',
        'security.view_auditlog',
        'security.view_anonymizeddata',
    ],
    'user_management': [
        'users.add_user',
        'users.change_user',
        'users.delete_user',
        'users.view_user',
    ],
}

# Enhanced admin notifications
WAGTAILADMIN_NOTIFICATIONS = {
    'enabled': True,
    'types': [
        'medication_reminder',
        'stock_alert',
        'system_maintenance',
        'security_alert',
    ],
    'channels': [
        'email',
        'sms',
        'push',
        'in_app',
    ],
    'templates': {
        'medication_reminder': 'notifications/email/medication_reminder.html',
        'stock_alert': 'notifications/email/stock_alert.html',
        'system_maintenance': 'notifications/email/system_maintenance.html',
        'security_alert': 'notifications/email/security_alert.html',
    }
}

# Enhanced admin analytics
WAGTAILADMIN_ANALYTICS = {
    'enabled': True,
    'providers': [
        'google_analytics',
        'matomo',
        'plausible',
    ],
    'tracking_id': os.getenv('ANALYTICS_TRACKING_ID', ''),
    'privacy_compliant': True,
    'anonymize_ip': True,
    'respect_dnt': True,
}

# Enhanced admin accessibility with Wagtail 7.0.2 improvements
WAGTAILADMIN_ACCESSIBILITY = {
    'enabled': True,
    'high_contrast_mode': True,
    'font_size_adjustment': True,
    'keyboard_navigation': True,
    'screen_reader_support': True,
    'focus_indicators': True,
    'color_blind_friendly': True,
    'aria_labels': True,
    'semantic_html': True,
    'skip_links': True,
    'landmark_roles': True,
    'live_regions': True,
    'error_announcements': True,
    'success_announcements': True,
    'loading_announcements': True,
    'form_validation': {
        'announce_errors': True,
        'announce_success': True,
        'error_summary': True,
        'field_descriptions': True,
        'required_field_indicators': True,
    },
    'navigation': {
        'breadcrumb_announcement': True,
        'menu_state_announcement': True,
        'tab_announcement': True,
        'modal_announcement': True,
    },
    'content': {
        'heading_structure': True,
        'list_announcement': True,
        'table_announcement': True,
        'image_alt_text': True,
        'link_purpose': True,
    },
    'interactions': {
        'button_state_announcement': True,
        'checkbox_announcement': True,
        'radio_announcement': True,
        'select_announcement': True,
        'progress_announcement': True,
    },
    'customization': {
        'user_preferences': True,
        'theme_switching': True,
        'font_scaling': True,
        'line_spacing': True,
        'word_spacing': True,
        'letter_spacing': True,
    },
    'compliance': {
        'wcag_2_1_aa': True,
        'section_508': True,
        'aria_1_2': True,
        'aria_1_3': True,
    },
    'testing': {
        'automated_testing': True,
        'manual_testing': True,
        'screen_reader_testing': True,
        'keyboard_testing': True,
        'color_contrast_testing': True,
    }
}

# Enhanced admin performance monitoring
WAGTAILADMIN_PERFORMANCE_MONITORING = {
    'enabled': True,
    'metrics': [
        'page_load_time',
        'api_response_time',
        'database_query_time',
        'memory_usage',
        'cpu_usage',
    ],
    'alerts': {
        'slow_page_load': 3000,  # 3 seconds
        'slow_api_response': 1000,  # 1 second
        'high_memory_usage': 80,  # 80%
        'high_cpu_usage': 90,  # 90%
    },
    'logging': {
        'performance_logs': True,
        'error_logs': True,
        'access_logs': True,
    }
}

# Search configuration is now handled in the enhanced Wagtail 7.0.2 configuration above

# Base URL to use when referring to full URLs within the Wagtail admin backend
WAGTAILADMIN_BASE_URL = os.getenv('WAGTAILADMIN_BASE_URL', 'http://localhost:8000')

# Document extensions are now handled in the enhanced Wagtail 7.0.2 configuration above

# Wagtail API v2 configuration is now handled in the enhanced Wagtail 7.0.2 configuration above

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