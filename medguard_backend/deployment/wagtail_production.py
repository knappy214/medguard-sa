"""
MedGuard SA - Wagtail 7.0.2 Production Configuration
Healthcare-focused production settings for optimal performance and security.
"""
import os
from django.conf import settings
from django.core.management.utils import get_random_secret_key


# ============================================================================
# 1. WAGTAIL 7.0.2 ENHANCED STATIC FILE HANDLING FOR CDN DEPLOYMENT
# ============================================================================

class WagtailCDNStaticFiles:
    """
    Enhanced static file handling for CDN deployment with Wagtail 7.0.2 features.
    Optimized for healthcare applications requiring high availability and performance.
    """
    
    @staticmethod
    def get_cdn_settings():
        """
        Configure CDN settings for static files with healthcare-specific optimizations.
        
        Returns:
            dict: CDN configuration settings
        """
        return {
            # Static files configuration for CDN
            'STATIC_URL': os.environ.get('CDN_STATIC_URL', '/static/'),
            'STATIC_ROOT': os.path.join(settings.BASE_DIR, 'staticfiles'),
            'STATICFILES_STORAGE': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
            
            # Wagtail 7.0.2 enhanced static file finders
            'STATICFILES_FINDERS': [
                'django.contrib.staticfiles.finders.FileSystemFinder',
                'django.contrib.staticfiles.finders.AppDirectoriesFinder',
                'compressor.finders.CompressorFinder',  # For CSS/JS compression
            ],
            
            # Healthcare-specific static file directories
            'STATICFILES_DIRS': [
                os.path.join(settings.BASE_DIR, 'static'),
                os.path.join(settings.BASE_DIR, 'medguard_cms', 'static'),
                os.path.join(settings.BASE_DIR, 'medications', 'static'),
                os.path.join(settings.BASE_DIR, 'security', 'static'),
            ],
            
            # Wagtail 7.0.2 enhanced compression settings
            'COMPRESS_ENABLED': True,
            'COMPRESS_OFFLINE': True,
            'COMPRESS_CSS_FILTERS': [
                'compressor.filters.css_default.CssAbsoluteFilter',
                'compressor.filters.cssmin.rCSSMinFilter',
            ],
            'COMPRESS_JS_FILTERS': [
                'compressor.filters.jsmin.rJSMinFilter',
            ],
            
            # CDN-specific headers for healthcare compliance
            'COMPRESS_CSS_HASHING_METHOD': 'content',
            'COMPRESS_OFFLINE_CONTEXT': {
                'STATIC_URL': os.environ.get('CDN_STATIC_URL', '/static/'),
            },
        }
    
    @staticmethod
    def configure_whitenoise_cdn():
        """
        Configure WhiteNoise for CDN deployment with healthcare-specific settings.
        
        Returns:
            dict: WhiteNoise configuration for CDN
        """
        return {
            # WhiteNoise configuration for CDN
            'WHITENOISE_USE_FINDERS': True,
            'WHITENOISE_AUTOREFRESH': False,  # Disabled in production
            'WHITENOISE_SKIP_COMPRESS_EXTENSIONS': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br'],
            
            # Healthcare-specific cache headers
            'WHITENOISE_MAX_AGE': 31536000,  # 1 year for static assets
            'WHITENOISE_MANIFEST_STRICT': True,
            
            # Security headers for healthcare compliance
            'SECURE_CONTENT_TYPE_NOSNIFF': True,
            'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
        }
    
    @staticmethod
    def get_wagtail_static_settings():
        """
        Wagtail 7.0.2 specific static file settings for production.
        
        Returns:
            dict: Wagtail-specific static file configuration
        """
        return {
            # Wagtail admin static files
            'WAGTAILADMIN_STATIC_FILE_VERSION_STRINGS': True,
            'WAGTAIL_ENABLE_UPDATE_CHECK': False,  # Disabled in production
            
            # Wagtail document serving with CDN support
            'WAGTAILDOCS_SERVE_METHOD': 'redirect',
            'WAGTAILIMAGES_SERVE_METHOD': 'redirect',
            
            # Enhanced static file versioning for cache busting
            'WAGTAIL_APPEND_SLASH': False,  # Let CDN handle trailing slashes
            
            # Wagtail 7.0.2 enhanced frontend cache invalidation
            'WAGTAILFRONTENDCACHE': {
                'cloudflare': {
                    'BACKEND': 'wagtail.contrib.frontend_cache.backends.CloudflareBackend',
                    'EMAIL': os.environ.get('CLOUDFLARE_EMAIL'),
                    'API_KEY': os.environ.get('CLOUDFLARE_API_KEY'),
                    'ZONE_ID': os.environ.get('CLOUDFLARE_ZONE_ID'),
                },
                'varnish': {
                    'BACKEND': 'wagtail.contrib.frontend_cache.backends.HTTPBackend',
                    'LOCATION': os.environ.get('VARNISH_URL', 'http://localhost:6081/'),
                },
            },
        }
    
    @classmethod
    def apply_cdn_configuration(cls):
        """
        Apply all CDN static file configurations.
        
        Returns:
            dict: Complete CDN configuration dictionary
        """
        config = {}
        config.update(cls.get_cdn_settings())
        config.update(cls.configure_whitenoise_cdn())
        config.update(cls.get_wagtail_static_settings())
        
        return config


# Apply CDN static file configuration
CDN_STATIC_CONFIG = WagtailCDNStaticFiles.apply_cdn_configuration()


# ============================================================================
# 2. WAGTAIL 7.0.2 IMPROVED DATABASE MIGRATION HANDLING FOR PRODUCTION
# ============================================================================

class WagtailProductionMigrations:
    """
    Enhanced database migration handling for production with Wagtail 7.0.2 features.
    Healthcare-focused migration management with zero-downtime deployment support.
    """
    
    @staticmethod
    def get_migration_settings():
        """
        Configure migration settings for production healthcare environments.
        
        Returns:
            dict: Migration configuration settings
        """
        return {
            # Database migration settings
            'MIGRATION_MODULES': {
                # Custom migration paths for healthcare apps
                'medications': 'medications.migrations',
                'security': 'security.migrations',
                'medguard_notifications': 'medguard_notifications.migrations',
                'users': 'users.migrations',
                'privacy': 'privacy.migrations',
            },
            
            # Wagtail 7.0.2 enhanced migration recorder
            'MIGRATION_RECORDER_CLASS': 'django.db.migrations.recorder.MigrationRecorder',
            
            # Healthcare-specific migration validation
            'MIGRATION_CHECK_FRAMEWORK': True,
            'SILKY_PYTHON_PROFILER': False,  # Disabled in production
            
            # Zero-downtime migration settings
            'ATOMIC_REQUESTS': True,
            'CONN_MAX_AGE': 600,  # 10 minutes connection pooling
        }
    
    @staticmethod
    def configure_migration_executor():
        """
        Configure migration executor for healthcare production environments.
        
        Returns:
            dict: Migration executor configuration
        """
        return {
            # Migration execution settings
            'MIGRATION_EXECUTOR_TIMEOUT': 3600,  # 1 hour timeout for large migrations
            'MIGRATION_BATCH_SIZE': 1000,  # Process migrations in batches
            
            # Healthcare data integrity checks
            'MIGRATION_INTEGRITY_CHECKS': True,
            'MIGRATION_BACKUP_BEFORE_MIGRATE': True,
            
            # Wagtail 7.0.2 enhanced migration planning
            'MIGRATION_PLAN_OPTIMIZATION': True,
            'MIGRATION_DEPENDENCY_RESOLUTION': 'strict',
        }
    
    @staticmethod
    def get_wagtail_migration_settings():
        """
        Wagtail 7.0.2 specific migration settings for production.
        
        Returns:
            dict: Wagtail-specific migration configuration
        """
        return {
            # Wagtail search index migrations
            'WAGTAILSEARCH_BACKENDS': {
                'default': {
                    'BACKEND': 'wagtail.search.backends.elasticsearch7',
                    'URLS': [os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')],
                    'INDEX': os.environ.get('ELASTICSEARCH_INDEX', 'medguard'),
                    'TIMEOUT': 20,
                    'OPTIONS': {
                        'max_retries': 3,
                        'retry_on_timeout': True,
                    },
                    'INDEX_SETTINGS': {
                        'settings': {
                            'index': {
                                'number_of_shards': 2,
                                'number_of_replicas': 1,
                                'refresh_interval': '30s',
                            }
                        }
                    }
                }
            },
            
            # Wagtail 7.0.2 enhanced content migration
            'WAGTAIL_CONTENT_LANGUAGES': [
                ('en-ZA', 'English (South Africa)'),
                ('af-ZA', 'Afrikaans (South Africa)'),
            ],
            
            # Healthcare-specific content type migrations
            'WAGTAIL_CONTENT_TYPE_MIGRATION_BATCH_SIZE': 500,
            'WAGTAIL_PAGE_MIGRATION_BATCH_SIZE': 100,
        }
    
    @staticmethod
    def configure_migration_monitoring():
        """
        Configure migration monitoring and logging for healthcare compliance.
        
        Returns:
            dict: Migration monitoring configuration
        """
        return {
            # Migration logging for healthcare audit trails
            'LOGGING': {
                'version': 1,
                'disable_existing_loggers': False,
                'formatters': {
                    'migration_formatter': {
                        'format': '{asctime} - {name} - {levelname} - {message}',
                        'style': '{',
                    },
                },
                'handlers': {
                    'migration_file': {
                        'level': 'INFO',
                        'class': 'logging.handlers.RotatingFileHandler',
                        'filename': os.path.join(settings.BASE_DIR, 'logs', 'migrations.log'),
                        'maxBytes': 50 * 1024 * 1024,  # 50MB
                        'backupCount': 10,
                        'formatter': 'migration_formatter',
                    },
                    'migration_console': {
                        'level': 'INFO',
                        'class': 'logging.StreamHandler',
                        'formatter': 'migration_formatter',
                    },
                },
                'loggers': {
                    'django.db.migrations': {
                        'handlers': ['migration_file', 'migration_console'],
                        'level': 'INFO',
                        'propagate': False,
                    },
                    'wagtail.core.migrations': {
                        'handlers': ['migration_file', 'migration_console'],
                        'level': 'INFO',
                        'propagate': False,
                    },
                },
            },
            
            # Migration performance monitoring
            'MIGRATION_PERFORMANCE_TRACKING': True,
            'MIGRATION_SLOW_QUERY_THRESHOLD': 5.0,  # 5 seconds
        }
    
    @staticmethod
    def get_backup_migration_settings():
        """
        Configure automatic backup settings before migrations.
        
        Returns:
            dict: Backup configuration for migrations
        """
        return {
            # Pre-migration backup settings
            'AUTO_BACKUP_BEFORE_MIGRATION': True,
            'BACKUP_STORAGE_PATH': os.environ.get('MIGRATION_BACKUP_PATH', '/backups/migrations/'),
            'BACKUP_RETENTION_DAYS': 30,
            
            # Healthcare data backup encryption
            'BACKUP_ENCRYPTION_KEY': os.environ.get('BACKUP_ENCRYPTION_KEY'),
            'BACKUP_COMPRESSION': True,
            
            # Backup verification
            'VERIFY_BACKUP_INTEGRITY': True,
            'BACKUP_CHECKSUM_ALGORITHM': 'sha256',
        }
    
    @classmethod
    def apply_migration_configuration(cls):
        """
        Apply all migration configurations for production.
        
        Returns:
            dict: Complete migration configuration dictionary
        """
        config = {}
        config.update(cls.get_migration_settings())
        config.update(cls.configure_migration_executor())
        config.update(cls.get_wagtail_migration_settings())
        config.update(cls.configure_migration_monitoring())
        config.update(cls.get_backup_migration_settings())
        
        return config


# Apply production migration configuration
PRODUCTION_MIGRATION_CONFIG = WagtailProductionMigrations.apply_migration_configuration()


# ============================================================================
# 3. WAGTAIL 7.0.2 ENHANCED CACHING STRATEGIES FOR HIGH-TRAFFIC HEALTHCARE SITES
# ============================================================================

class WagtailHealthcareCaching:
    """
    Enhanced caching strategies for high-traffic healthcare sites with Wagtail 7.0.2.
    HIPAA-compliant caching with performance optimization and data privacy protection.
    """
    
    @staticmethod
    def get_redis_cache_settings():
        """
        Configure Redis caching for healthcare applications with privacy protection.
        
        Returns:
            dict: Redis cache configuration
        """
        return {
            'CACHES': {
                'default': {
                    'BACKEND': 'django_redis.cache.RedisCache',
                    'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
                    'OPTIONS': {
                        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                        'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                        'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                        'CONNECTION_POOL_KWARGS': {
                            'max_connections': 100,
                            'retry_on_timeout': True,
                            'health_check_interval': 30,
                        },
                        # Healthcare-specific encryption for cached data
                        'IGNORE_EXCEPTIONS': True,
                        'LOG_IGNORED_EXCEPTIONS': True,
                    },
                    'KEY_PREFIX': 'medguard',
                    'VERSION': 1,
                    'TIMEOUT': 300,  # 5 minutes default timeout
                },
                
                # Separate cache for session data (HIPAA compliance)
                'sessions': {
                    'BACKEND': 'django_redis.cache.RedisCache',
                    'LOCATION': os.environ.get('REDIS_SESSIONS_URL', 'redis://localhost:6379/2'),
                    'OPTIONS': {
                        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                        'SERIALIZER': 'django_redis.serializers.pickle.PickleSerializer',
                        'CONNECTION_POOL_KWARGS': {
                            'max_connections': 50,
                            'retry_on_timeout': True,
                        },
                    },
                    'KEY_PREFIX': 'medguard_session',
                    'TIMEOUT': 3600,  # 1 hour for sessions
                },
                
                # Cache for static content and templates
                'templates': {
                    'BACKEND': 'django_redis.cache.RedisCache',
                    'LOCATION': os.environ.get('REDIS_TEMPLATES_URL', 'redis://localhost:6379/3'),
                    'OPTIONS': {
                        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                        'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                        'CONNECTION_POOL_KWARGS': {
                            'max_connections': 30,
                        },
                    },
                    'KEY_PREFIX': 'medguard_templates',
                    'TIMEOUT': 3600,  # 1 hour for templates
                },
            }
        }
    
    @staticmethod
    def configure_wagtail_cache_settings():
        """
        Configure Wagtail 7.0.2 specific caching for healthcare sites.
        
        Returns:
            dict: Wagtail caching configuration
        """
        return {
            # Wagtail page caching with healthcare considerations
            'WAGTAIL_CACHE': True,
            'WAGTAIL_CACHE_BACKEND': 'default',
            'WAGTAIL_CACHE_TIMEOUT': 1800,  # 30 minutes for pages
            
            # Wagtail 7.0.2 enhanced cache invalidation
            'WAGTAILCACHE_INVALIDATE_ON': [
                'save',
                'delete',
                'move',
                'publish',
                'unpublish',
            ],
            
            # Healthcare-specific cache headers
            'WAGTAIL_CACHE_CONTROL_MAX_AGE': 300,  # 5 minutes
            'WAGTAIL_VARY_ON_HEADERS': [
                'Accept-Language',
                'Accept-Encoding',
                'User-Agent',
            ],
            
            # Cache warming for critical healthcare pages
            'WAGTAIL_CACHE_WARMING_ENABLED': True,
            'WAGTAIL_CACHE_WARMING_PAGES': [
                'medications.MedicationListPage',
                'security.SecurityPage',
                'home.HomePage',
            ],
        }
    
    @staticmethod
    def get_session_cache_settings():
        """
        Configure session caching for HIPAA compliance.
        
        Returns:
            dict: Session cache configuration
        """
        return {
            # Session configuration for healthcare compliance
            'SESSION_ENGINE': 'django.contrib.sessions.backends.cache',
            'SESSION_CACHE_ALIAS': 'sessions',
            'SESSION_COOKIE_AGE': 3600,  # 1 hour
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Strict',
            'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
            
            # Healthcare-specific session security
            'SESSION_COOKIE_NAME': 'medguard_sessionid',
            'CSRF_COOKIE_SECURE': True,
            'CSRF_COOKIE_HTTPONLY': True,
            'CSRF_COOKIE_SAMESITE': 'Strict',
        }
    
    @staticmethod
    def configure_template_caching():
        """
        Configure template caching for high-traffic healthcare sites.
        
        Returns:
            dict: Template caching configuration
        """
        return {
            # Template caching settings
            'TEMPLATE_CACHE_BACKEND': 'templates',
            'TEMPLATE_CACHE_TIMEOUT': 3600,  # 1 hour
            
            # Cached template loader for production
            'TEMPLATES': [
                {
                    'BACKEND': 'django.template.backends.django.DjangoTemplates',
                    'DIRS': [
                        os.path.join(settings.BASE_DIR, 'templates'),
                    ],
                    'OPTIONS': {
                        'context_processors': [
                            'django.template.context_processors.debug',
                            'django.template.context_processors.request',
                            'django.contrib.auth.context_processors.auth',
                            'django.contrib.messages.context_processors.messages',
                            'wagtail.contrib.settings.context_processors.settings',
                        ],
                        'loaders': [
                            ('django.template.loaders.cached.Loader', [
                                'django.template.loaders.filesystem.Loader',
                                'django.template.loaders.app_directories.Loader',
                            ]),
                        ],
                    },
                },
            ],
        }
    
    @staticmethod
    def get_database_cache_settings():
        """
        Configure database query caching for healthcare applications.
        
        Returns:
            dict: Database cache configuration
        """
        return {
            # Database caching settings
            'DATABASE_CACHE_TIMEOUT': 300,  # 5 minutes
            'DATABASE_CACHE_KEY_PREFIX': 'medguard_db',
            
            # Query caching for medication data
            'MEDICATION_CACHE_TIMEOUT': 900,  # 15 minutes
            'PRESCRIPTION_CACHE_TIMEOUT': 300,  # 5 minutes (more frequent updates)
            
            # User-specific caching (HIPAA compliant)
            'USER_CACHE_TIMEOUT': 600,  # 10 minutes
            'SECURITY_LOG_CACHE_TIMEOUT': 60,  # 1 minute (security-sensitive)
        }
    
    @staticmethod
    def configure_cache_middleware():
        """
        Configure cache middleware for healthcare sites.
        
        Returns:
            list: Middleware configuration for caching
        """
        return [
            'django.middleware.cache.UpdateCacheMiddleware',
            'django.middleware.security.SecurityMiddleware',
            'whitenoise.middleware.WhiteNoiseMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'corsheaders.middleware.CorsMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            'wagtail.contrib.redirects.middleware.RedirectMiddleware',
            'django.middleware.cache.FetchFromCacheMiddleware',
            
            # Healthcare-specific middleware
            'security.middleware.SecurityAuditMiddleware',
            'privacy.middleware.HIPAAComplianceMiddleware',
        ]
    
    @staticmethod
    def get_cache_monitoring_settings():
        """
        Configure cache monitoring for healthcare compliance.
        
        Returns:
            dict: Cache monitoring configuration
        """
        return {
            # Cache performance monitoring
            'CACHE_MONITORING_ENABLED': True,
            'CACHE_HIT_RATE_THRESHOLD': 0.8,  # 80% hit rate minimum
            'CACHE_MISS_ALERT_THRESHOLD': 100,  # Alert after 100 consecutive misses
            
            # Healthcare audit logging for cache access
            'CACHE_AUDIT_LOGGING': True,
            'CACHE_AUDIT_LOG_LEVEL': 'INFO',
            'CACHE_SENSITIVE_DATA_TRACKING': True,
            
            # Cache invalidation logging
            'CACHE_INVALIDATION_LOGGING': True,
            'CACHE_INVALIDATION_REASONS': [
                'manual_clear',
                'data_update',
                'security_event',
                'compliance_requirement',
            ],
        }
    
    @classmethod
    def apply_caching_configuration(cls):
        """
        Apply all caching configurations for healthcare production.
        
        Returns:
            dict: Complete caching configuration dictionary
        """
        config = {}
        config.update(cls.get_redis_cache_settings())
        config.update(cls.configure_wagtail_cache_settings())
        config.update(cls.get_session_cache_settings())
        config.update(cls.configure_template_caching())
        config.update(cls.get_database_cache_settings())
        config.update(cls.get_cache_monitoring_settings())
        
        # Add middleware as a separate key
        config['MIDDLEWARE'] = cls.configure_cache_middleware()
        
        return config


# Apply healthcare caching configuration
HEALTHCARE_CACHE_CONFIG = WagtailHealthcareCaching.apply_caching_configuration()


# ============================================================================
# 4. WAGTAIL 7.0.2 OPTIMIZED SEARCH INDEX MANAGEMENT FOR PRODUCTION
# ============================================================================

class WagtailSearchIndexManagement:
    """
    Optimized search index management for production healthcare environments.
    Enhanced Elasticsearch integration with Wagtail 7.0.2 for medical content search.
    """
    
    @staticmethod
    def get_elasticsearch_settings():
        """
        Configure Elasticsearch for healthcare content search with HIPAA compliance.
        
        Returns:
            dict: Elasticsearch configuration
        """
        return {
            'WAGTAILSEARCH_BACKENDS': {
                'default': {
                    'BACKEND': 'wagtail.search.backends.elasticsearch7',
                    'URLS': [
                        os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')
                    ],
                    'INDEX': os.environ.get('ELASTICSEARCH_INDEX', 'medguard_production'),
                    'TIMEOUT': 20,
                    'OPTIONS': {
                        'max_retries': 3,
                        'retry_on_timeout': True,
                        'retry_on_status': [502, 503, 504],
                        'sniff_on_start': True,
                        'sniff_on_connection_fail': True,
                        'sniffer_timeout': 60,
                        'sniff_timeout': 10,
                    },
                    'INDEX_SETTINGS': {
                        'settings': {
                            'index': {
                                'number_of_shards': 3,
                                'number_of_replicas': 2,
                                'refresh_interval': '30s',
                                'max_result_window': 50000,
                                'analysis': {
                                    'analyzer': {
                                        'medical_analyzer': {
                                            'type': 'custom',
                                            'tokenizer': 'standard',
                                            'filter': [
                                                'lowercase',
                                                'asciifolding',
                                                'medical_synonym',
                                                'medical_stemmer'
                                            ]
                                        },
                                        'medication_analyzer': {
                                            'type': 'custom',
                                            'tokenizer': 'keyword',
                                            'filter': [
                                                'lowercase',
                                                'asciifolding'
                                            ]
                                        }
                                    },
                                    'filter': {
                                        'medical_synonym': {
                                            'type': 'synonym',
                                            'synonyms_path': 'medical_synonyms.txt'
                                        },
                                        'medical_stemmer': {
                                            'type': 'stemmer',
                                            'language': 'english'
                                        }
                                    }
                                }
                            }
                        },
                        'mappings': {
                            'properties': {
                                'title': {
                                    'type': 'text',
                                    'analyzer': 'medical_analyzer',
                                    'search_analyzer': 'medical_analyzer'
                                },
                                'body': {
                                    'type': 'text',
                                    'analyzer': 'medical_analyzer',
                                    'search_analyzer': 'medical_analyzer'
                                },
                                'medication_name': {
                                    'type': 'text',
                                    'analyzer': 'medication_analyzer',
                                    'search_analyzer': 'medication_analyzer'
                                },
                                'dosage': {
                                    'type': 'keyword'
                                },
                                'medical_condition': {
                                    'type': 'text',
                                    'analyzer': 'medical_analyzer'
                                }
                            }
                        }
                    }
                }
            }
        }
    
    @staticmethod
    def configure_search_indexing():
        """
        Configure search indexing for healthcare content with privacy protection.
        
        Returns:
            dict: Search indexing configuration
        """
        return {
            # Search index management
            'WAGTAIL_SEARCH_INDEX_NAME': 'medguard_production',
            'WAGTAIL_SEARCH_AUTO_UPDATE': True,
            'WAGTAIL_SEARCH_ATOMIC_REBUILD': True,
            
            # Healthcare-specific indexing settings
            'SEARCH_INDEX_BATCH_SIZE': 100,
            'SEARCH_INDEX_TIMEOUT': 300,  # 5 minutes
            'SEARCH_INDEX_RETRY_ATTEMPTS': 3,
            
            # Privacy-compliant indexing
            'SEARCH_EXCLUDE_SENSITIVE_FIELDS': [
                'patient_id',
                'social_security',
                'phone_number',
                'email_address',
                'medical_record_number'
            ],
            
            # Content type specific indexing
            'SEARCH_INDEX_MODELS': {
                'medications.Medication': {
                    'fields': ['name', 'description', 'dosage_form', 'strength'],
                    'boost': 2.0,
                    'analyzer': 'medication_analyzer'
                },
                'medications.Prescription': {
                    'fields': ['medication__name', 'dosage', 'frequency'],
                    'boost': 1.5,
                    'privacy_filter': True
                },
                'security.SecurityPage': {
                    'fields': ['title', 'body'],
                    'boost': 1.0
                },
                'home.HomePage': {
                    'fields': ['title', 'body', 'intro'],
                    'boost': 1.2
                }
            }
        }
    
    @staticmethod
    def get_search_performance_settings():
        """
        Configure search performance optimization for high-traffic healthcare sites.
        
        Returns:
            dict: Search performance configuration
        """
        return {
            # Search performance settings
            'SEARCH_RESULTS_PER_PAGE': 20,
            'SEARCH_MAX_RESULTS': 1000,
            'SEARCH_CACHE_TIMEOUT': 300,  # 5 minutes
            
            # Search query optimization
            'SEARCH_QUERY_BOOST_FACTORS': {
                'title': 3.0,
                'medication_name': 2.5,
                'body': 1.0,
                'tags': 1.5
            },
            
            # Faceted search configuration
            'SEARCH_FACETS': {
                'content_type': {
                    'field': '_type',
                    'display_name': 'Content Type'
                },
                'medication_category': {
                    'field': 'category',
                    'display_name': 'Medication Category'
                },
                'language': {
                    'field': 'locale',
                    'display_name': 'Language'
                }
            },
            
            # Search highlighting
            'SEARCH_HIGHLIGHT_ENABLED': True,
            'SEARCH_HIGHLIGHT_FRAGMENT_SIZE': 150,
            'SEARCH_HIGHLIGHT_MAX_FRAGMENTS': 3,
        }
    
    @staticmethod
    def configure_search_monitoring():
        """
        Configure search monitoring and analytics for healthcare compliance.
        
        Returns:
            dict: Search monitoring configuration
        """
        return {
            # Search analytics
            'SEARCH_ANALYTICS_ENABLED': True,
            'SEARCH_ANALYTICS_RETENTION_DAYS': 90,
            'SEARCH_QUERY_LOGGING': True,
            
            # Performance monitoring
            'SEARCH_PERFORMANCE_MONITORING': True,
            'SEARCH_SLOW_QUERY_THRESHOLD': 2.0,  # 2 seconds
            'SEARCH_ERROR_RATE_THRESHOLD': 0.05,  # 5% error rate
            
            # Healthcare-specific search audit
            'SEARCH_AUDIT_SENSITIVE_QUERIES': True,
            'SEARCH_AUDIT_USER_TRACKING': True,
            'SEARCH_AUDIT_RETENTION_DAYS': 365,  # 1 year for compliance
            
            # Index health monitoring
            'INDEX_HEALTH_CHECK_INTERVAL': 300,  # 5 minutes
            'INDEX_SIZE_ALERT_THRESHOLD': '10GB',
            'INDEX_DOCUMENT_COUNT_ALERT': 1000000,
        }
    
    @staticmethod
    def get_search_security_settings():
        """
        Configure search security for HIPAA compliance.
        
        Returns:
            dict: Search security configuration
        """
        return {
            # Search access control
            'SEARCH_PERMISSION_REQUIRED': True,
            'SEARCH_USER_AUTHENTICATION': True,
            'SEARCH_ROLE_BASED_FILTERING': True,
            
            # Content filtering by user permissions
            'SEARCH_CONTENT_FILTERS': {
                'medications': 'medications.view_medication',
                'prescriptions': 'medications.view_prescription',
                'security_logs': 'security.view_securityevent',
            },
            
            # Search query sanitization
            'SEARCH_QUERY_SANITIZATION': True,
            'SEARCH_BLOCKED_TERMS': [
                'script',
                'javascript',
                'eval',
                'exec'
            ],
            
            # Rate limiting for search
            'SEARCH_RATE_LIMIT_ENABLED': True,
            'SEARCH_RATE_LIMIT_PER_MINUTE': 60,
            'SEARCH_RATE_LIMIT_PER_HOUR': 1000,
        }
    
    @staticmethod
    def configure_index_maintenance():
        """
        Configure automated index maintenance for production.
        
        Returns:
            dict: Index maintenance configuration
        """
        return {
            # Automated index maintenance
            'AUTO_INDEX_MAINTENANCE': True,
            'INDEX_OPTIMIZATION_SCHEDULE': '0 2 * * *',  # Daily at 2 AM
            'INDEX_CLEANUP_SCHEDULE': '0 3 * * 0',  # Weekly on Sunday at 3 AM
            
            # Index backup and recovery
            'INDEX_BACKUP_ENABLED': True,
            'INDEX_BACKUP_SCHEDULE': '0 1 * * *',  # Daily at 1 AM
            'INDEX_BACKUP_RETENTION_DAYS': 30,
            
            # Index rebuilding
            'AUTO_INDEX_REBUILD': True,
            'INDEX_REBUILD_THRESHOLD': 0.1,  # 10% document changes
            'INDEX_REBUILD_SCHEDULE': '0 4 * * 0',  # Weekly on Sunday at 4 AM
            
            # Dead letter queue for failed indexing
            'INDEX_DEAD_LETTER_QUEUE': True,
            'INDEX_RETRY_FAILED_DOCUMENTS': True,
            'INDEX_MAX_RETRY_ATTEMPTS': 3,
        }
    
    @classmethod
    def apply_search_configuration(cls):
        """
        Apply all search index configurations for production.
        
        Returns:
            dict: Complete search configuration dictionary
        """
        config = {}
        config.update(cls.get_elasticsearch_settings())
        config.update(cls.configure_search_indexing())
        config.update(cls.get_search_performance_settings())
        config.update(cls.configure_search_monitoring())
        config.update(cls.get_search_security_settings())
        config.update(cls.configure_index_maintenance())
        
        return config


# Apply search index configuration
SEARCH_INDEX_CONFIG = WagtailSearchIndexManagement.apply_search_configuration()


# ============================================================================
# 5. WAGTAIL 7.0.2 IMPROVED IMAGE OPTIMIZATION PIPELINE FOR PRODUCTION
# ============================================================================

class WagtailImageOptimization:
    """
    Improved image optimization pipeline for production healthcare environments.
    Enhanced image processing with Wagtail 7.0.2 for medical imagery and compliance.
    """
    
    @staticmethod
    def get_image_storage_settings():
        """
        Configure image storage for healthcare applications with HIPAA compliance.
        
        Returns:
            dict: Image storage configuration
        """
        return {
            # Image storage configuration
            'DEFAULT_FILE_STORAGE': 'storages.backends.s3boto3.S3Boto3Storage',
            'STATICFILES_STORAGE': 'storages.backends.s3boto3.StaticS3Boto3Storage',
            
            # AWS S3 configuration for healthcare compliance
            'AWS_ACCESS_KEY_ID': os.environ.get('AWS_ACCESS_KEY_ID'),
            'AWS_SECRET_ACCESS_KEY': os.environ.get('AWS_SECRET_ACCESS_KEY'),
            'AWS_STORAGE_BUCKET_NAME': os.environ.get('AWS_STORAGE_BUCKET_NAME', 'medguard-media'),
            'AWS_S3_REGION_NAME': os.environ.get('AWS_S3_REGION_NAME', 'us-east-1'),
            'AWS_S3_CUSTOM_DOMAIN': os.environ.get('AWS_S3_CUSTOM_DOMAIN'),
            
            # Healthcare-specific S3 settings
            'AWS_DEFAULT_ACL': 'private',
            'AWS_S3_OBJECT_PARAMETERS': {
                'CacheControl': 'max-age=86400',  # 24 hours
                'ServerSideEncryption': 'AES256',
                'StorageClass': 'STANDARD_IA',  # Cost-effective for healthcare images
            },
            
            # HIPAA compliance settings
            'AWS_S3_ENCRYPTION': True,
            'AWS_S3_FILE_OVERWRITE': False,
            'AWS_IS_GZIPPED': True,
            'AWS_S3_USE_SSL': True,
            'AWS_S3_VERIFY': True,
            
            # Media URL configuration
            'MEDIA_URL': f"https://{os.environ.get('AWS_S3_CUSTOM_DOMAIN', 'medguard-media.s3.amazonaws.com')}/",
            'MEDIA_ROOT': '',  # Not used with S3
        }
    
    @staticmethod
    def configure_wagtail_image_settings():
        """
        Configure Wagtail 7.0.2 image processing for healthcare applications.
        
        Returns:
            dict: Wagtail image configuration
        """
        return {
            # Wagtail image formats for healthcare
            'WAGTAILIMAGES_FORMATS': {
                'thumbnail': 'fill-150x150|jpegquality-80',
                'small': 'fill-300x300|jpegquality-85',
                'medium': 'fill-600x400|jpegquality-85',
                'large': 'fill-1200x800|jpegquality-90',
                'original': 'original',
                
                # Medical-specific formats
                'medical_thumb': 'fill-200x200|jpegquality-95',
                'medical_preview': 'fill-800x600|jpegquality-95',
                'medical_full': 'width-1920|jpegquality-98',
                
                # Avatar formats for healthcare staff
                'avatar_small': 'fill-50x50|jpegquality-80',
                'avatar_medium': 'fill-100x100|jpegquality-85',
                'avatar_large': 'fill-200x200|jpegquality-85',
            },
            
            # Image processing settings
            'WAGTAILIMAGES_MAX_UPLOAD_SIZE': 50 * 1024 * 1024,  # 50MB for medical images
            'WAGTAILIMAGES_MAX_IMAGE_PIXELS': 200000000,  # 200 megapixels
            'WAGTAILIMAGES_JPEG_QUALITY': 85,
            'WAGTAILIMAGES_WEBP_QUALITY': 85,
            'WAGTAILIMAGES_AVIF_QUALITY': 85,
            
            # Healthcare-specific image validation
            'WAGTAILIMAGES_ALLOWED_EXTENSIONS': [
                'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg',
                'tiff', 'tif',  # Medical imaging formats
                'dicom', 'dcm'  # Medical DICOM format support
            ],
            
            # Image optimization
            'WAGTAILIMAGES_OPTIMIZE': True,
            'WAGTAILIMAGES_AUTO_ORIENT': True,
            'WAGTAILIMAGES_PRESERVE_EXIF': False,  # Remove EXIF for privacy
        }
    
    @staticmethod
    def get_image_processing_pipeline():
        """
        Configure advanced image processing pipeline for healthcare.
        
        Returns:
            dict: Image processing pipeline configuration
        """
        return {
            # Image processing pipeline
            'IMAGE_PROCESSING_BACKEND': 'pillow_simd',  # Faster processing
            'IMAGE_PROCESSING_WORKERS': 4,
            'IMAGE_PROCESSING_TIMEOUT': 300,  # 5 minutes for large medical images
            
            # Batch processing settings
            'IMAGE_BATCH_PROCESSING': True,
            'IMAGE_BATCH_SIZE': 10,
            'IMAGE_BATCH_TIMEOUT': 1800,  # 30 minutes
            
            # Image compression settings
            'IMAGE_COMPRESSION_SETTINGS': {
                'jpeg': {
                    'quality': 85,
                    'optimize': True,
                    'progressive': True,
                },
                'webp': {
                    'quality': 85,
                    'method': 6,
                    'lossless': False,
                },
                'png': {
                    'optimize': True,
                    'compress_level': 6,
                },
                'avif': {
                    'quality': 85,
                    'speed': 6,
                }
            },
            
            # Medical image specific processing
            'MEDICAL_IMAGE_PROCESSING': {
                'preserve_metadata': True,
                'anonymize_dicom': True,
                'validate_medical_format': True,
                'audit_image_access': True,
            },
        }
    
    @staticmethod
    def configure_image_cdn():
        """
        Configure CDN settings for image delivery in healthcare.
        
        Returns:
            dict: Image CDN configuration
        """
        return {
            # CDN configuration for images
            'IMAGE_CDN_ENABLED': True,
            'IMAGE_CDN_URL': os.environ.get('IMAGE_CDN_URL'),
            'IMAGE_CDN_CACHE_CONTROL': 'public, max-age=31536000',  # 1 year
            
            # Healthcare-specific CDN settings
            'IMAGE_CDN_SECURE_URLS': True,
            'IMAGE_CDN_SIGNED_URLS': True,
            'IMAGE_CDN_SIGNED_URL_EXPIRY': 3600,  # 1 hour
            
            # Responsive image delivery
            'IMAGE_CDN_RESPONSIVE': True,
            'IMAGE_CDN_AUTO_FORMAT': True,
            'IMAGE_CDN_AUTO_QUALITY': True,
            
            # Geographic distribution for healthcare
            'IMAGE_CDN_REGIONS': [
                'us-east-1',
                'us-west-2',
                'eu-west-1',
                'ap-southeast-1',
            ],
        }
    
    @staticmethod
    def get_image_security_settings():
        """
        Configure image security for HIPAA compliance.
        
        Returns:
            dict: Image security configuration
        """
        return {
            # Image access control
            'IMAGE_ACCESS_CONTROL': True,
            'IMAGE_PERMISSION_REQUIRED': True,
            'IMAGE_USER_AUTHENTICATION': True,
            
            # Image watermarking for healthcare
            'IMAGE_WATERMARK_ENABLED': True,
            'IMAGE_WATERMARK_TEXT': 'MedGuard SA - Confidential',
            'IMAGE_WATERMARK_OPACITY': 0.3,
            'IMAGE_WATERMARK_POSITION': 'bottom-right',
            
            # Image audit logging
            'IMAGE_AUDIT_LOGGING': True,
            'IMAGE_ACCESS_LOGGING': True,
            'IMAGE_DOWNLOAD_TRACKING': True,
            'IMAGE_AUDIT_RETENTION_DAYS': 365,  # 1 year for compliance
            
            # Image virus scanning
            'IMAGE_VIRUS_SCANNING': True,
            'IMAGE_VIRUS_SCANNER_BACKEND': 'clamav',
            'IMAGE_QUARANTINE_INFECTED': True,
            
            # Content validation
            'IMAGE_CONTENT_VALIDATION': True,
            'IMAGE_BLOCKED_EXTENSIONS': [
                'exe', 'bat', 'com', 'scr', 'pif',
                'vbs', 'js', 'jar', 'zip'
            ],
        }
    
    @staticmethod
    def configure_image_monitoring():
        """
        Configure image processing monitoring for healthcare compliance.
        
        Returns:
            dict: Image monitoring configuration
        """
        return {
            # Image processing monitoring
            'IMAGE_PROCESSING_MONITORING': True,
            'IMAGE_PROCESSING_METRICS': True,
            'IMAGE_ERROR_TRACKING': True,
            
            # Performance monitoring
            'IMAGE_PROCESSING_TIME_THRESHOLD': 30.0,  # 30 seconds
            'IMAGE_SIZE_ALERT_THRESHOLD': 100 * 1024 * 1024,  # 100MB
            'IMAGE_QUEUE_SIZE_ALERT': 1000,
            
            # Healthcare-specific monitoring
            'MEDICAL_IMAGE_COMPLIANCE_CHECK': True,
            'IMAGE_PHI_DETECTION': True,
            'IMAGE_ANONYMIZATION_VERIFICATION': True,
            
            # Storage monitoring
            'IMAGE_STORAGE_QUOTA_MONITORING': True,
            'IMAGE_STORAGE_COST_TRACKING': True,
            'IMAGE_BACKUP_VERIFICATION': True,
        }
    
    @staticmethod
    def get_image_backup_settings():
        """
        Configure image backup and disaster recovery.
        
        Returns:
            dict: Image backup configuration
        """
        return {
            # Image backup settings
            'IMAGE_BACKUP_ENABLED': True,
            'IMAGE_BACKUP_SCHEDULE': '0 2 * * *',  # Daily at 2 AM
            'IMAGE_BACKUP_RETENTION_DAYS': 90,
            
            # Cross-region backup for disaster recovery
            'IMAGE_CROSS_REGION_BACKUP': True,
            'IMAGE_BACKUP_REGIONS': [
                'us-west-2',  # Primary backup region
                'eu-west-1',  # Secondary backup region
            ],
            
            # Backup encryption
            'IMAGE_BACKUP_ENCRYPTION': True,
            'IMAGE_BACKUP_ENCRYPTION_KEY': os.environ.get('IMAGE_BACKUP_ENCRYPTION_KEY'),
            
            # Backup verification
            'IMAGE_BACKUP_INTEGRITY_CHECK': True,
            'IMAGE_BACKUP_TEST_RESTORE': True,
            'IMAGE_BACKUP_CHECKSUM_VERIFICATION': True,
        }
    
    @classmethod
    def apply_image_optimization_configuration(cls):
        """
        Apply all image optimization configurations for production.
        
        Returns:
            dict: Complete image optimization configuration dictionary
        """
        config = {}
        config.update(cls.get_image_storage_settings())
        config.update(cls.configure_wagtail_image_settings())
        config.update(cls.get_image_processing_pipeline())
        config.update(cls.configure_image_cdn())
        config.update(cls.get_image_security_settings())
        config.update(cls.configure_image_monitoring())
        config.update(cls.get_image_backup_settings())
        
        return config


# Apply image optimization configuration
IMAGE_OPTIMIZATION_CONFIG = WagtailImageOptimization.apply_image_optimization_configuration()


# ============================================================================
# 6. WAGTAIL 7.0.2 ENHANCED SECURITY SETTINGS FOR HEALTHCARE PRODUCTION
# ============================================================================

class WagtailHealthcareSecurity:
    """
    Enhanced security settings for healthcare production with Wagtail 7.0.2.
    HIPAA-compliant security configuration with advanced threat protection.
    """
    
    @staticmethod
    def get_django_security_settings():
        """
        Configure Django security settings for healthcare compliance.
        
        Returns:
            dict: Django security configuration
        """
        return {
            # Basic security settings
            'DEBUG': False,
            'SECRET_KEY': os.environ.get('SECRET_KEY', get_random_secret_key()),
            'ALLOWED_HOSTS': os.environ.get('ALLOWED_HOSTS', '').split(','),
            
            # HTTPS and SSL settings
            'SECURE_SSL_REDIRECT': True,
            'SECURE_PROXY_SSL_HEADER': ('HTTP_X_FORWARDED_PROTO', 'https'),
            'SECURE_HSTS_SECONDS': 31536000,  # 1 year
            'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
            'SECURE_HSTS_PRELOAD': True,
            
            # Cookie security for healthcare
            'SESSION_COOKIE_SECURE': True,
            'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Strict',
            'SESSION_COOKIE_AGE': 3600,  # 1 hour
            'SESSION_EXPIRE_AT_BROWSER_CLOSE': True,
            
            'CSRF_COOKIE_SECURE': True,
            'CSRF_COOKIE_HTTPONLY': True,
            'CSRF_COOKIE_SAMESITE': 'Strict',
            'CSRF_COOKIE_AGE': 3600,
            
            # Content security
            'SECURE_CONTENT_TYPE_NOSNIFF': True,
            'SECURE_BROWSER_XSS_FILTER': True,
            'SECURE_REFERRER_POLICY': 'strict-origin-when-cross-origin',
            'X_FRAME_OPTIONS': 'DENY',
        }
    
    @staticmethod
    def configure_wagtail_security_settings():
        """
        Configure Wagtail 7.0.2 specific security settings for healthcare.
        
        Returns:
            dict: Wagtail security configuration
        """
        return {
            # Wagtail admin security
            'WAGTAIL_ADMIN_URL': os.environ.get('WAGTAIL_ADMIN_URL', 'admin'),
            'WAGTAILADMIN_REQUIRE_HTTPS': True,
            'WAGTAILADMIN_SECURE_COOKIES': True,
            
            # Content security policy for Wagtail admin
            'CSP_DEFAULT_SRC': ["'self'"],
            'CSP_SCRIPT_SRC': [
                "'self'",
                "'unsafe-inline'",  # Required for Wagtail admin
                "'unsafe-eval'",   # Required for some Wagtail features
                'cdn.jsdelivr.net',
                'unpkg.com',
            ],
            'CSP_STYLE_SRC': [
                "'self'",
                "'unsafe-inline'",  # Required for Wagtail admin styles
                'fonts.googleapis.com',
            ],
            'CSP_FONT_SRC': [
                "'self'",
                'fonts.gstatic.com',
            ],
            'CSP_IMG_SRC': [
                "'self'",
                'data:',
                os.environ.get('AWS_S3_CUSTOM_DOMAIN', 'medguard-media.s3.amazonaws.com'),
            ],
            'CSP_CONNECT_SRC': ["'self'"],
            'CSP_FRAME_ANCESTORS': ["'none'"],
            'CSP_BASE_URI': ["'self'"],
            'CSP_FORM_ACTION': ["'self'"],
            
            # Wagtail user permissions
            'WAGTAIL_USER_EDIT_FORM': 'security.forms.CustomUserEditForm',
            'WAGTAIL_USER_CREATION_FORM': 'security.forms.CustomUserCreationForm',
            'WAGTAIL_USER_CUSTOM_FIELDS': ['department', 'license_number', 'role'],
        }
    
    @staticmethod
    def get_authentication_settings():
        """
        Configure authentication settings for healthcare compliance.
        
        Returns:
            dict: Authentication configuration
        """
        return {
            # Authentication backends
            'AUTHENTICATION_BACKENDS': [
                'django.contrib.auth.backends.ModelBackend',
                'security.backends.MedicalLicenseBackend',
                'security.backends.TwoFactorBackend',
            ],
            
            # Password validation for healthcare
            'AUTH_PASSWORD_VALIDATORS': [
                {
                    'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
                },
                {
                    'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
                    'OPTIONS': {
                        'min_length': 12,  # Stronger passwords for healthcare
                    }
                },
                {
                    'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
                },
                {
                    'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
                },
                {
                    'NAME': 'security.validators.MedicalPasswordValidator',
                    'OPTIONS': {
                        'require_special_chars': True,
                        'require_uppercase': True,
                        'require_lowercase': True,
                        'require_numbers': True,
                        'min_unique_chars': 8,
                    }
                },
            ],
            
            # Account lockout settings
            'ACCOUNT_LOCKOUT_ENABLED': True,
            'ACCOUNT_LOCKOUT_ATTEMPTS': 5,
            'ACCOUNT_LOCKOUT_DURATION': 1800,  # 30 minutes
            'ACCOUNT_LOCKOUT_NOTIFY_ADMINS': True,
            
            # Session security
            'SESSION_SECURITY_WARN_AFTER': 2700,  # 45 minutes
            'SESSION_SECURITY_EXPIRE_AFTER': 3600,  # 1 hour
            'SESSION_SECURITY_PASSIVE_URLS': ['/api/health/', '/api/ping/'],
        }
    
    @staticmethod
    def configure_two_factor_authentication():
        """
        Configure two-factor authentication for healthcare users.
        
        Returns:
            dict: 2FA configuration
        """
        return {
            # Two-factor authentication
            'TWO_FACTOR_ENABLED': True,
            'TWO_FACTOR_REQUIRED_FOR_ADMIN': True,
            'TWO_FACTOR_REQUIRED_FOR_MEDICAL_STAFF': True,
            
            # TOTP settings
            'TOTP_ISSUER_NAME': 'MedGuard SA',
            'TOTP_VALIDITY_PERIOD': 30,
            'TOTP_DIGITS': 6,
            
            # Backup tokens
            'BACKUP_TOKEN_COUNT': 10,
            'BACKUP_TOKEN_LENGTH': 8,
            
            # SMS settings for 2FA
            'SMS_GATEWAY_ENABLED': True,
            'SMS_GATEWAY_PROVIDER': os.environ.get('SMS_GATEWAY_PROVIDER', 'twilio'),
            'SMS_GATEWAY_API_KEY': os.environ.get('SMS_GATEWAY_API_KEY'),
            'SMS_GATEWAY_SENDER': os.environ.get('SMS_GATEWAY_SENDER', '+27123456789'),
        }
    
    @staticmethod
    def get_rate_limiting_settings():
        """
        Configure rate limiting for API and admin endpoints.
        
        Returns:
            dict: Rate limiting configuration
        """
        return {
            # Rate limiting configuration
            'RATE_LIMITING_ENABLED': True,
            'RATELIMIT_USE_CACHE': 'default',
            
            # API rate limits
            'API_RATE_LIMITS': {
                'default': '1000/hour',
                'login': '10/minute',
                'password_reset': '5/hour',
                'medication_search': '100/minute',
                'prescription_create': '20/minute',
            },
            
            # Admin interface rate limits
            'ADMIN_RATE_LIMITS': {
                'login': '5/minute',
                'bulk_actions': '10/minute',
                'export': '5/hour',
            },
            
            # Healthcare-specific rate limits
            'MEDICAL_RECORD_ACCESS_LIMIT': '50/minute',
            'PATIENT_DATA_EXPORT_LIMIT': '5/hour',
            'PRESCRIPTION_APPROVAL_LIMIT': '100/hour',
        }
    
    @staticmethod
    def configure_audit_logging():
        """
        Configure comprehensive audit logging for healthcare compliance.
        
        Returns:
            dict: Audit logging configuration
        """
        return {
            # Audit logging settings
            'AUDIT_LOGGING_ENABLED': True,
            'AUDIT_LOG_RETENTION_DAYS': 2555,  # 7 years for healthcare compliance
            
            # Audit events to track
            'AUDIT_EVENTS': [
                'user_login',
                'user_logout',
                'user_login_failed',
                'password_change',
                'permission_change',
                'data_access',
                'data_modification',
                'data_export',
                'admin_action',
                'security_event',
                'medication_access',
                'prescription_create',
                'prescription_modify',
                'patient_data_access',
            ],
            
            # Audit log storage
            'AUDIT_LOG_BACKEND': 'database',
            'AUDIT_LOG_ENCRYPTION': True,
            'AUDIT_LOG_INTEGRITY_CHECK': True,
            
            # Real-time audit alerts
            'AUDIT_REAL_TIME_ALERTS': True,
            'AUDIT_ALERT_CHANNELS': ['email', 'slack', 'sms'],
            'AUDIT_CRITICAL_EVENTS': [
                'multiple_failed_logins',
                'privilege_escalation',
                'data_breach_attempt',
                'unauthorized_access',
                'bulk_data_export',
            ],
        }
    
    @staticmethod
    def get_data_encryption_settings():
        """
        Configure data encryption for healthcare data protection.
        
        Returns:
            dict: Encryption configuration
        """
        return {
            # Database encryption
            'DATABASE_ENCRYPTION_ENABLED': True,
            'DATABASE_ENCRYPTION_KEY': os.environ.get('DATABASE_ENCRYPTION_KEY'),
            'DATABASE_FIELD_ENCRYPTION': [
                'users.User.email',
                'users.User.phone_number',
                'medications.Prescription.patient_notes',
                'security.AuditLog.details',
            ],
            
            # File encryption
            'FILE_ENCRYPTION_ENABLED': True,
            'FILE_ENCRYPTION_ALGORITHM': 'AES-256-GCM',
            'FILE_ENCRYPTION_KEY_ROTATION': True,
            'FILE_ENCRYPTION_KEY_ROTATION_DAYS': 90,
            
            # Transit encryption
            'ENCRYPT_IN_TRANSIT': True,
            'TLS_VERSION': 'TLSv1.3',
            'CIPHER_SUITES': [
                'TLS_AES_256_GCM_SHA384',
                'TLS_CHACHA20_POLY1305_SHA256',
                'TLS_AES_128_GCM_SHA256',
            ],
        }
    
    @staticmethod
    def configure_security_headers():
        """
        Configure security headers for healthcare web applications.
        
        Returns:
            dict: Security headers configuration
        """
        return {
            # Security headers middleware
            'SECURITY_HEADERS_MIDDLEWARE': [
                'django_security.middleware.SecurityHeadersMiddleware',
                'csp.middleware.CSPMiddleware',
            ],
            
            # Custom security headers
            'SECURITY_HEADERS': {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
                'X-Permitted-Cross-Domain-Policies': 'none',
                'X-Download-Options': 'noopen',
                'X-DNS-Prefetch-Control': 'off',
            },
            
            # Healthcare-specific headers
            'HEALTHCARE_HEADERS': {
                'X-Healthcare-Compliance': 'HIPAA',
                'X-Data-Classification': 'PHI',
                'X-Audit-Required': 'true',
            },
        }
    
    @staticmethod
    def get_vulnerability_scanning_settings():
        """
        Configure vulnerability scanning and security monitoring.
        
        Returns:
            dict: Vulnerability scanning configuration
        """
        return {
            # Vulnerability scanning
            'VULNERABILITY_SCANNING_ENABLED': True,
            'VULNERABILITY_SCAN_SCHEDULE': '0 3 * * *',  # Daily at 3 AM
            'VULNERABILITY_SCAN_TOOLS': [
                'bandit',  # Python security linter
                'safety',  # Dependency vulnerability checker
                'semgrep',  # Static analysis
            ],
            
            # Dependency monitoring
            'DEPENDENCY_MONITORING': True,
            'DEPENDENCY_UPDATE_ALERTS': True,
            'DEPENDENCY_SECURITY_ALERTS': True,
            
            # Security monitoring
            'SECURITY_MONITORING_ENABLED': True,
            'INTRUSION_DETECTION': True,
            'ANOMALY_DETECTION': True,
            'THREAT_INTELLIGENCE_FEEDS': [
                'mitre_attack',
                'owasp_top10',
                'healthcare_threats',
            ],
        }
    
    @classmethod
    def apply_security_configuration(cls):
        """
        Apply all security configurations for healthcare production.
        
        Returns:
            dict: Complete security configuration dictionary
        """
        config = {}
        config.update(cls.get_django_security_settings())
        config.update(cls.configure_wagtail_security_settings())
        config.update(cls.get_authentication_settings())
        config.update(cls.configure_two_factor_authentication())
        config.update(cls.get_rate_limiting_settings())
        config.update(cls.configure_audit_logging())
        config.update(cls.get_data_encryption_settings())
        config.update(cls.configure_security_headers())
        config.update(cls.get_vulnerability_scanning_settings())
        
        return config


# Apply healthcare security configuration
HEALTHCARE_SECURITY_CONFIG = WagtailHealthcareSecurity.apply_security_configuration()


# ============================================================================
# 7. WAGTAIL 7.0.2 OPTIMIZED ADMIN INTERFACE FOR PRODUCTION HEALTHCARE TEAMS
# ============================================================================

class WagtailHealthcareAdmin:
    """
    Optimized admin interface for production healthcare teams with Wagtail 7.0.2.
    Enhanced user experience and workflow optimization for medical professionals.
    """
    
    @staticmethod
    def get_admin_interface_settings():
        """
        Configure Wagtail admin interface for healthcare workflows.
        
        Returns:
            dict: Admin interface configuration
        """
        return {
            # Wagtail admin branding for healthcare
            'WAGTAIL_SITE_NAME': 'MedGuard SA - Healthcare Management',
            'WAGTAILADMIN_BASE_URL': os.environ.get('WAGTAIL_BASE_URL', 'https://admin.medguard.co.za'),
            'WAGTAIL_APPEND_SLASH': False,
            
            # Healthcare-specific admin settings
            'WAGTAILADMIN_NOTIFICATION_FROM_EMAIL': os.environ.get('ADMIN_FROM_EMAIL', 'noreply@medguard.co.za'),
            'WAGTAILADMIN_NOTIFICATION_USE_HTML': True,
            'WAGTAILADMIN_NOTIFICATION_INCLUDE_SUPERUSERS': False,
            
            # Admin interface customization
            'WAGTAIL_FRONTEND_LOGIN_URL': '/accounts/login/',
            'WAGTAIL_FRONTEND_LOGIN_TEMPLATE': 'security/admin_login.html',
            'WAGTAILADMIN_GLOBAL_SIDE_PANELS': [
                'wagtail.admin.panels.PageChooserPanel',
                'wagtail.admin.panels.DocumentChooserPanel',
                'wagtail.admin.panels.ImageChooserPanel',
            ],
            
            # Healthcare workflow optimization
            'WAGTAIL_AUTO_UPDATE_PREVIEW': True,
            'WAGTAILADMIN_RICH_TEXT_EDITORS': {
                'default': {
                    'WIDGET': 'wagtail.admin.rich_text.DraftailRichTextArea',
                    'OPTIONS': {
                        'features': [
                            'bold', 'italic', 'underline', 'strikethrough',
                            'h2', 'h3', 'h4', 'h5', 'h6',
                            'blockquote', 'ol', 'ul',
                            'link', 'document-link', 'image', 'embed',
                            'code', 'superscript', 'subscript',
                            'hr', 'medical-terminology', 'dosage-calculator'
                        ]
                    }
                },
                'medical': {
                    'WIDGET': 'medications.widgets.MedicalRichTextArea',
                    'OPTIONS': {
                        'features': [
                            'bold', 'italic', 'h3', 'h4',
                            'ol', 'ul', 'link', 'medical-terminology',
                            'dosage-calculator', 'drug-interaction-checker'
                        ]
                    }
                }
            },
        }
    
    @staticmethod
    def configure_admin_permissions():
        """
        Configure role-based permissions for healthcare teams.
        
        Returns:
            dict: Admin permissions configuration
        """
        return {
            # Role-based access control
            'WAGTAIL_PERMISSION_POLICIES': {
                'wagtailcore.Page': 'security.policies.HealthcarePagePermissionPolicy',
                'medications.Medication': 'medications.policies.MedicationPermissionPolicy',
                'medications.Prescription': 'medications.policies.PrescriptionPermissionPolicy',
                'users.User': 'security.policies.UserPermissionPolicy',
            },
            
            # Healthcare team roles
            'HEALTHCARE_ROLES': {
                'doctor': {
                    'permissions': [
                        'medications.add_medication',
                        'medications.change_medication',
                        'medications.view_medication',
                        'medications.add_prescription',
                        'medications.change_prescription',
                        'medications.view_prescription',
                        'medications.approve_prescription',
                        'users.view_patient_data',
                    ],
                    'admin_access': True,
                    'bulk_actions': True,
                },
                'pharmacist': {
                    'permissions': [
                        'medications.view_medication',
                        'medications.change_medication_stock',
                        'medications.view_prescription',
                        'medications.dispense_prescription',
                        'medications.verify_prescription',
                    ],
                    'admin_access': True,
                    'bulk_actions': False,
                },
                'nurse': {
                    'permissions': [
                        'medications.view_medication',
                        'medications.view_prescription',
                        'medications.administer_medication',
                        'users.view_basic_patient_data',
                    ],
                    'admin_access': True,
                    'bulk_actions': False,
                },
                'admin_staff': {
                    'permissions': [
                        'medications.view_medication',
                        'medications.view_prescription',
                        'users.view_user',
                        'security.view_audit_logs',
                    ],
                    'admin_access': True,
                    'bulk_actions': False,
                },
            },
            
            # Permission inheritance
            'PERMISSION_INHERITANCE': True,
            'DEPARTMENT_BASED_PERMISSIONS': True,
            'LOCATION_BASED_PERMISSIONS': True,
        }
    
    @staticmethod
    def get_admin_dashboard_settings():
        """
        Configure healthcare-specific admin dashboard.
        
        Returns:
            dict: Admin dashboard configuration
        """
        return {
            # Dashboard configuration
            'WAGTAILADMIN_HOME_PAGE': 'medguard_backend.admin.HealthcareDashboard',
            'WAGTAIL_ADMIN_MENU_ORDER': [
                'wagtailadmin',
                'medications',
                'users',
                'security',
                'privacy',
                'medguard_notifications',
                'analytics',
                'wagtailcore',
                'wagtailimages',
                'wagtaildocs',
            ],
            
            # Healthcare dashboard widgets
            'DASHBOARD_WIDGETS': {
                'medication_alerts': {
                    'widget': 'medications.widgets.MedicationAlertsWidget',
                    'position': 1,
                    'permissions': ['medications.view_medication'],
                },
                'prescription_queue': {
                    'widget': 'medications.widgets.PrescriptionQueueWidget',
                    'position': 2,
                    'permissions': ['medications.view_prescription'],
                },
                'security_alerts': {
                    'widget': 'security.widgets.SecurityAlertsWidget',
                    'position': 3,
                    'permissions': ['security.view_securityevent'],
                },
                'compliance_status': {
                    'widget': 'privacy.widgets.ComplianceStatusWidget',
                    'position': 4,
                    'permissions': ['privacy.view_compliance'],
                },
                'user_activity': {
                    'widget': 'users.widgets.UserActivityWidget',
                    'position': 5,
                    'permissions': ['users.view_user'],
                },
                'system_health': {
                    'widget': 'analytics.widgets.SystemHealthWidget',
                    'position': 6,
                    'permissions': ['analytics.view_analytics'],
                },
            },
            
            # Quick actions for healthcare teams
            'QUICK_ACTIONS': [
                {
                    'name': 'Add New Medication',
                    'url': 'medications:medication_create',
                    'icon': 'pill',
                    'permissions': ['medications.add_medication'],
                },
                {
                    'name': 'Create Prescription',
                    'url': 'medications:prescription_create',
                    'icon': 'doc-text',
                    'permissions': ['medications.add_prescription'],
                },
                {
                    'name': 'View Security Logs',
                    'url': 'security:audit_logs',
                    'icon': 'warning',
                    'permissions': ['security.view_securityevent'],
                },
                {
                    'name': 'User Management',
                    'url': 'users:user_list',
                    'icon': 'user',
                    'permissions': ['users.view_user'],
                },
            ],
        }
    
    @staticmethod
    def configure_admin_workflows():
        """
        Configure healthcare-specific admin workflows.
        
        Returns:
            dict: Admin workflow configuration
        """
        return {
            # Workflow configuration
            'WAGTAIL_WORKFLOW_ENABLED': True,
            'WAGTAIL_WORKFLOW_REQUIRE_APPROVAL': True,
            
            # Healthcare-specific workflows
            'HEALTHCARE_WORKFLOWS': {
                'medication_approval': {
                    'name': 'Medication Approval Workflow',
                    'steps': [
                        {
                            'name': 'Pharmacist Review',
                            'user_group': 'pharmacists',
                            'required': True,
                        },
                        {
                            'name': 'Doctor Approval',
                            'user_group': 'doctors',
                            'required': True,
                        },
                    ],
                    'models': ['medications.Medication'],
                },
                'prescription_verification': {
                    'name': 'Prescription Verification Workflow',
                    'steps': [
                        {
                            'name': 'Initial Review',
                            'user_group': 'nurses',
                            'required': True,
                        },
                        {
                            'name': 'Doctor Verification',
                            'user_group': 'doctors',
                            'required': True,
                        },
                        {
                            'name': 'Pharmacist Dispensing',
                            'user_group': 'pharmacists',
                            'required': True,
                        },
                    ],
                    'models': ['medications.Prescription'],
                },
                'security_incident': {
                    'name': 'Security Incident Response',
                    'steps': [
                        {
                            'name': 'Initial Assessment',
                            'user_group': 'security_officers',
                            'required': True,
                        },
                        {
                            'name': 'Management Review',
                            'user_group': 'administrators',
                            'required': True,
                        },
                    ],
                    'models': ['security.SecurityEvent'],
                },
            },
            
            # Workflow notifications
            'WORKFLOW_EMAIL_NOTIFICATIONS': True,
            'WORKFLOW_SMS_NOTIFICATIONS': True,
            'WORKFLOW_SLACK_NOTIFICATIONS': True,
        }
    
    @staticmethod
    def get_admin_customization_settings():
        """
        Configure admin interface customization for healthcare.
        
        Returns:
            dict: Admin customization configuration
        """
        return {
            # Custom CSS and JavaScript
            'WAGTAILADMIN_USER_LOGIN_FORM': 'security.forms.HealthcareLoginForm',
            'WAGTAILADMIN_USER_EDIT_FORM': 'security.forms.HealthcareUserEditForm',
            'WAGTAILADMIN_USER_CREATION_FORM': 'security.forms.HealthcareUserCreationForm',
            
            # Healthcare-specific styling
            'ADMIN_CSS_FILES': [
                'css/healthcare-admin.css',
                'css/medical-forms.css',
                'css/dashboard-widgets.css',
            ],
            'ADMIN_JS_FILES': [
                'js/healthcare-admin.js',
                'js/medication-calculator.js',
                'js/drug-interaction-checker.js',
                'js/dosage-validator.js',
            ],
            
            # Custom admin templates
            'ADMIN_TEMPLATE_OVERRIDES': {
                'wagtailadmin/base.html': 'admin/healthcare_base.html',
                'wagtailadmin/home.html': 'admin/healthcare_dashboard.html',
                'wagtailadmin/login.html': 'admin/healthcare_login.html',
            },
            
            # Healthcare branding
            'ADMIN_LOGO_URL': '/static/images/medguard-admin-logo.svg',
            'ADMIN_FAVICON_URL': '/static/images/medguard-favicon.ico',
            'ADMIN_COLOR_SCHEME': 'healthcare-blue',
        }
    
    @staticmethod
    def configure_admin_performance():
        """
        Configure admin interface performance optimization.
        
        Returns:
            dict: Admin performance configuration
        """
        return {
            # Performance optimization
            'WAGTAILADMIN_BULK_ACTION_BATCH_SIZE': 100,
            'WAGTAILADMIN_SEARCH_RESULTS_PER_PAGE': 20,
            'WAGTAILADMIN_RECENT_EDITS_LIMIT': 10,
            
            # Database query optimization
            'ADMIN_QUERY_OPTIMIZATION': True,
            'ADMIN_PREFETCH_RELATED': [
                'medications__prescriptions',
                'users__groups',
                'security_events__user',
            ],
            'ADMIN_SELECT_RELATED': [
                'created_by',
                'modified_by',
                'assigned_to',
            ],
            
            # Caching for admin interface
            'ADMIN_CACHE_ENABLED': True,
            'ADMIN_CACHE_TIMEOUT': 300,  # 5 minutes
            'ADMIN_CACHE_KEY_PREFIX': 'medguard_admin',
            
            # Pagination settings
            'ADMIN_PAGINATION_SETTINGS': {
                'medications': 25,
                'prescriptions': 20,
                'users': 50,
                'security_events': 100,
                'audit_logs': 100,
            },
        }
    
    @staticmethod
    def get_admin_accessibility_settings():
        """
        Configure admin interface accessibility for healthcare teams.
        
        Returns:
            dict: Admin accessibility configuration
        """
        return {
            # Accessibility features
            'ADMIN_ACCESSIBILITY_ENABLED': True,
            'ADMIN_HIGH_CONTRAST_MODE': True,
            'ADMIN_LARGE_TEXT_MODE': True,
            'ADMIN_KEYBOARD_NAVIGATION': True,
            
            # Screen reader support
            'ADMIN_SCREEN_READER_SUPPORT': True,
            'ADMIN_ARIA_LABELS': True,
            'ADMIN_SEMANTIC_MARKUP': True,
            
            # Color contrast compliance
            'ADMIN_COLOR_CONTRAST_RATIO': 4.5,  # WCAG AA compliance
            'ADMIN_COLOR_BLIND_FRIENDLY': True,
            
            # Language and localization
            'ADMIN_LANGUAGE_SUPPORT': ['en-ZA', 'af-ZA'],
            'ADMIN_RTL_SUPPORT': False,  # Not needed for South African languages
            'ADMIN_TIMEZONE_SUPPORT': True,
        }
    
    @classmethod
    def apply_admin_configuration(cls):
        """
        Apply all admin interface configurations for healthcare teams.
        
        Returns:
            dict: Complete admin configuration dictionary
        """
        config = {}
        config.update(cls.get_admin_interface_settings())
        config.update(cls.configure_admin_permissions())
        config.update(cls.get_admin_dashboard_settings())
        config.update(cls.configure_admin_workflows())
        config.update(cls.get_admin_customization_settings())
        config.update(cls.configure_admin_performance())
        config.update(cls.get_admin_accessibility_settings())
        
        return config


# Apply healthcare admin configuration
HEALTHCARE_ADMIN_CONFIG = WagtailHealthcareAdmin.apply_admin_configuration()


# ============================================================================
# 8. WAGTAIL 7.0.2 IMPROVED BACKUP AND DISASTER RECOVERY FOR HEALTHCARE DATA
# ============================================================================

class WagtailHealthcareBackupRecovery:
    """
    Improved backup and disaster recovery for healthcare data with Wagtail 7.0.2.
    HIPAA-compliant backup strategies with automated recovery procedures.
    """
    
    @staticmethod
    def get_database_backup_settings():
        """
        Configure database backup for healthcare data compliance.
        
        Returns:
            dict: Database backup configuration
        """
        return {
            # Database backup configuration
            'DATABASE_BACKUP_ENABLED': True,
            'DATABASE_BACKUP_SCHEDULE': '0 2 * * *',  # Daily at 2 AM
            'DATABASE_BACKUP_RETENTION_DAYS': 2555,  # 7 years for healthcare compliance
            
            # Backup storage locations
            'DATABASE_BACKUP_LOCATIONS': [
                {
                    'name': 'primary',
                    'type': 's3',
                    'bucket': os.environ.get('BACKUP_S3_BUCKET', 'medguard-backups-primary'),
                    'region': os.environ.get('BACKUP_S3_REGION', 'us-east-1'),
                    'encryption': 'AES256',
                },
                {
                    'name': 'secondary',
                    'type': 's3',
                    'bucket': os.environ.get('BACKUP_S3_BUCKET_SECONDARY', 'medguard-backups-secondary'),
                    'region': os.environ.get('BACKUP_S3_REGION_SECONDARY', 'us-west-2'),
                    'encryption': 'AES256',
                },
                {
                    'name': 'offsite',
                    'type': 'azure',
                    'container': os.environ.get('BACKUP_AZURE_CONTAINER', 'medguard-backups'),
                    'account': os.environ.get('BACKUP_AZURE_ACCOUNT'),
                    'encryption': True,
                },
            ],
            
            # Healthcare-specific backup settings
            'BACKUP_COMPRESSION': True,
            'BACKUP_COMPRESSION_LEVEL': 6,
            'BACKUP_ENCRYPTION_KEY': os.environ.get('BACKUP_ENCRYPTION_KEY'),
            'BACKUP_INTEGRITY_CHECK': True,
            'BACKUP_CHECKSUM_ALGORITHM': 'sha256',
            
            # Incremental backup settings
            'INCREMENTAL_BACKUP_ENABLED': True,
            'INCREMENTAL_BACKUP_SCHEDULE': '0 */6 * * *',  # Every 6 hours
            'FULL_BACKUP_SCHEDULE': '0 2 * * 0',  # Weekly full backup on Sunday
            
            # Point-in-time recovery
            'POINT_IN_TIME_RECOVERY': True,
            'TRANSACTION_LOG_BACKUP_INTERVAL': 15,  # 15 minutes
            'RECOVERY_POINT_OBJECTIVE': 15,  # 15 minutes maximum data loss
        }
    
    @staticmethod
    def configure_media_backup_settings():
        """
        Configure media files backup for healthcare images and documents.
        
        Returns:
            dict: Media backup configuration
        """
        return {
            # Media backup configuration
            'MEDIA_BACKUP_ENABLED': True,
            'MEDIA_BACKUP_SCHEDULE': '0 3 * * *',  # Daily at 3 AM
            'MEDIA_BACKUP_RETENTION_DAYS': 2555,  # 7 years for healthcare compliance
            
            # Media backup locations
            'MEDIA_BACKUP_LOCATIONS': [
                {
                    'name': 'primary_media',
                    'type': 's3',
                    'bucket': os.environ.get('MEDIA_BACKUP_S3_BUCKET', 'medguard-media-backups'),
                    'region': os.environ.get('MEDIA_BACKUP_S3_REGION', 'us-east-1'),
                    'storage_class': 'GLACIER',  # Cost-effective long-term storage
                },
                {
                    'name': 'secondary_media',
                    'type': 's3',
                    'bucket': os.environ.get('MEDIA_BACKUP_S3_BUCKET_SECONDARY', 'medguard-media-backups-west'),
                    'region': 'us-west-2',
                    'storage_class': 'DEEP_ARCHIVE',  # Long-term archival
                },
            ],
            
            # Healthcare media backup settings
            'MEDIA_BACKUP_ENCRYPTION': True,
            'MEDIA_BACKUP_VERSIONING': True,
            'MEDIA_BACKUP_DEDUPLICATION': True,
            'MEDIA_BACKUP_COMPRESSION': True,
            
            # Medical image specific settings
            'DICOM_BACKUP_SPECIAL_HANDLING': True,
            'MEDICAL_IMAGE_METADATA_PRESERVATION': True,
            'PHI_ANONYMIZATION_BEFORE_BACKUP': True,
        }
    
    @staticmethod
    def get_disaster_recovery_settings():
        """
        Configure disaster recovery procedures for healthcare systems.
        
        Returns:
            dict: Disaster recovery configuration
        """
        return {
            # Disaster recovery configuration
            'DISASTER_RECOVERY_ENABLED': True,
            'RECOVERY_TIME_OBJECTIVE': 240,  # 4 hours maximum downtime
            'RECOVERY_POINT_OBJECTIVE': 15,  # 15 minutes maximum data loss
            
            # Multi-region disaster recovery
            'DR_REGIONS': [
                {
                    'name': 'primary',
                    'region': 'us-east-1',
                    'status': 'active',
                },
                {
                    'name': 'secondary',
                    'region': 'us-west-2',
                    'status': 'standby',
                },
                {
                    'name': 'tertiary',
                    'region': 'eu-west-1',
                    'status': 'cold_standby',
                },
            ],
            
            # Automated failover settings
            'AUTOMATED_FAILOVER': True,
            'FAILOVER_HEALTH_CHECKS': [
                'database_connectivity',
                'application_health',
                'api_responsiveness',
                'cache_availability',
                'search_index_status',
            ],
            'FAILOVER_THRESHOLD': 3,  # 3 consecutive failures trigger failover
            'FAILOVER_NOTIFICATION_CHANNELS': ['email', 'sms', 'slack', 'pagerduty'],
            
            # Data replication settings
            'DATABASE_REPLICATION': 'synchronous',
            'MEDIA_REPLICATION': 'asynchronous',
            'SEARCH_INDEX_REPLICATION': 'asynchronous',
            'CACHE_REPLICATION': 'disabled',  # Cache rebuilt on failover
        }
    
    @staticmethod
    def configure_backup_monitoring():
        """
        Configure backup monitoring and alerting for healthcare compliance.
        
        Returns:
            dict: Backup monitoring configuration
        """
        return {
            # Backup monitoring
            'BACKUP_MONITORING_ENABLED': True,
            'BACKUP_SUCCESS_NOTIFICATIONS': False,  # Only failures
            'BACKUP_FAILURE_NOTIFICATIONS': True,
            'BACKUP_DELAY_ALERT_THRESHOLD': 3600,  # 1 hour delay alert
            
            # Backup verification
            'BACKUP_VERIFICATION_ENABLED': True,
            'BACKUP_VERIFICATION_SCHEDULE': '0 4 * * *',  # Daily at 4 AM
            'BACKUP_RESTORATION_TESTING': True,
            'BACKUP_RESTORATION_TEST_SCHEDULE': '0 5 * * 0',  # Weekly on Sunday
            
            # Healthcare compliance monitoring
            'BACKUP_AUDIT_LOGGING': True,
            'BACKUP_ACCESS_LOGGING': True,
            'BACKUP_INTEGRITY_MONITORING': True,
            'BACKUP_ENCRYPTION_VERIFICATION': True,
            
            # Alerting configuration
            'BACKUP_ALERT_CHANNELS': ['email', 'slack', 'pagerduty'],
            'BACKUP_CRITICAL_ALERTS': [
                'backup_failure',
                'backup_corruption',
                'backup_encryption_failure',
                'backup_storage_full',
                'backup_access_denied',
            ],
            
            # Metrics and reporting
            'BACKUP_METRICS_ENABLED': True,
            'BACKUP_SIZE_TRACKING': True,
            'BACKUP_DURATION_TRACKING': True,
            'BACKUP_SUCCESS_RATE_TRACKING': True,
        }
    
    @staticmethod
    def get_recovery_procedures():
        """
        Configure automated recovery procedures for healthcare systems.
        
        Returns:
            dict: Recovery procedures configuration
        """
        return {
            # Recovery procedures
            'AUTOMATED_RECOVERY_ENABLED': True,
            'RECOVERY_PROCEDURES': {
                'database_corruption': {
                    'steps': [
                        'stop_application',
                        'assess_corruption_extent',
                        'restore_from_latest_backup',
                        'apply_transaction_logs',
                        'verify_data_integrity',
                        'restart_application',
                        'notify_stakeholders',
                    ],
                    'estimated_time': 120,  # 2 hours
                    'requires_approval': False,
                },
                'complete_system_failure': {
                    'steps': [
                        'activate_disaster_recovery_site',
                        'redirect_traffic',
                        'restore_database',
                        'restore_media_files',
                        'rebuild_search_indexes',
                        'verify_system_functionality',
                        'notify_users',
                    ],
                    'estimated_time': 240,  # 4 hours
                    'requires_approval': True,
                },
                'data_breach_response': {
                    'steps': [
                        'isolate_affected_systems',
                        'preserve_forensic_evidence',
                        'assess_breach_scope',
                        'notify_authorities',
                        'restore_from_clean_backup',
                        'implement_additional_security',
                        'conduct_security_audit',
                    ],
                    'estimated_time': 480,  # 8 hours
                    'requires_approval': True,
                },
            },
            
            # Recovery testing
            'RECOVERY_TESTING_ENABLED': True,
            'RECOVERY_TESTING_SCHEDULE': '0 6 * * 6',  # Weekly on Saturday
            'RECOVERY_TESTING_SCENARIOS': [
                'database_point_in_time_recovery',
                'media_files_restoration',
                'full_system_recovery',
                'cross_region_failover',
            ],
        }
    
    @staticmethod
    def configure_compliance_backup():
        """
        Configure backup procedures for healthcare compliance requirements.
        
        Returns:
            dict: Compliance backup configuration
        """
        return {
            # Healthcare compliance requirements
            'HIPAA_COMPLIANCE_BACKUP': True,
            'POPIA_COMPLIANCE_BACKUP': True,  # South African POPI Act
            'BACKUP_AUDIT_TRAIL': True,
            'BACKUP_ACCESS_CONTROLS': True,
            
            # Long-term archival for compliance
            'LONG_TERM_ARCHIVAL': True,
            'ARCHIVAL_SCHEDULE': '0 1 1 * *',  # Monthly archival
            'ARCHIVAL_RETENTION_YEARS': 7,  # 7 years minimum
            'ARCHIVAL_STORAGE_CLASS': 'DEEP_ARCHIVE',
            
            # Legal hold procedures
            'LEGAL_HOLD_SUPPORT': True,
            'LITIGATION_BACKUP_PRESERVATION': True,
            'REGULATORY_BACKUP_REQUIREMENTS': True,
            
            # Data classification for backups
            'BACKUP_DATA_CLASSIFICATION': {
                'phi': {  # Protected Health Information
                    'encryption': 'required',
                    'retention_years': 7,
                    'access_controls': 'strict',
                    'audit_logging': 'detailed',
                },
                'pii': {  # Personally Identifiable Information
                    'encryption': 'required',
                    'retention_years': 7,
                    'access_controls': 'strict',
                    'audit_logging': 'detailed',
                },
                'medical_records': {
                    'encryption': 'required',
                    'retention_years': 10,  # Extended for medical records
                    'access_controls': 'strict',
                    'audit_logging': 'comprehensive',
                },
                'system_logs': {
                    'encryption': 'optional',
                    'retention_years': 3,
                    'access_controls': 'standard',
                    'audit_logging': 'standard',
                },
            },
        }
    
    @staticmethod
    def get_backup_security_settings():
        """
        Configure backup security for healthcare data protection.
        
        Returns:
            dict: Backup security configuration
        """
        return {
            # Backup encryption settings
            'BACKUP_ENCRYPTION_ENABLED': True,
            'BACKUP_ENCRYPTION_ALGORITHM': 'AES-256-GCM',
            'BACKUP_KEY_MANAGEMENT': 'aws_kms',
            'BACKUP_KEY_ROTATION': True,
            'BACKUP_KEY_ROTATION_DAYS': 90,
            
            # Access controls for backups
            'BACKUP_ACCESS_CONTROL': True,
            'BACKUP_ROLE_BASED_ACCESS': True,
            'BACKUP_MFA_REQUIRED': True,
            'BACKUP_ACCESS_APPROVAL_REQUIRED': True,
            
            # Backup transport security
            'BACKUP_TRANSPORT_ENCRYPTION': True,
            'BACKUP_SIGNED_URLS': True,
            'BACKUP_SECURE_TRANSFER': True,
            'BACKUP_VPN_REQUIRED': True,
            
            # Backup storage security
            'BACKUP_STORAGE_ENCRYPTION': True,
            'BACKUP_IMMUTABLE_STORAGE': True,
            'BACKUP_VERSIONING': True,
            'BACKUP_DELETE_PROTECTION': True,
        }
    
    @classmethod
    def apply_backup_recovery_configuration(cls):
        """
        Apply all backup and disaster recovery configurations.
        
        Returns:
            dict: Complete backup and recovery configuration dictionary
        """
        config = {}
        config.update(cls.get_database_backup_settings())
        config.update(cls.configure_media_backup_settings())
        config.update(cls.get_disaster_recovery_settings())
        config.update(cls.configure_backup_monitoring())
        config.update(cls.get_recovery_procedures())
        config.update(cls.configure_compliance_backup())
        config.update(cls.get_backup_security_settings())
        
        return config


# Apply healthcare backup and recovery configuration
HEALTHCARE_BACKUP_RECOVERY_CONFIG = WagtailHealthcareBackupRecovery.apply_backup_recovery_configuration()


# ============================================================================
# 9. WAGTAIL 7.0.2 ENHANCED MONITORING AND ALERTING FOR PRODUCTION
# ============================================================================

class WagtailHealthcareMonitoring:
    """
    Enhanced monitoring and alerting for production healthcare environments.
    Comprehensive observability with Wagtail 7.0.2 for medical system reliability.
    """
    
    @staticmethod
    def get_application_monitoring_settings():
        """
        Configure application performance monitoring for healthcare systems.
        
        Returns:
            dict: Application monitoring configuration
        """
        return {
            # Application performance monitoring
            'APM_ENABLED': True,
            'APM_SERVICE_NAME': 'medguard-wagtail',
            'APM_ENVIRONMENT': os.environ.get('APM_ENVIRONMENT', 'production'),
            'APM_SERVER_URL': os.environ.get('APM_SERVER_URL', 'http://localhost:8200'),
            
            # Performance metrics
            'PERFORMANCE_MONITORING': {
                'response_time_threshold': 2.0,  # 2 seconds
                'error_rate_threshold': 0.01,  # 1%
                'throughput_monitoring': True,
                'memory_usage_monitoring': True,
                'cpu_usage_monitoring': True,
                'database_query_monitoring': True,
            },
            
            # Healthcare-specific monitoring
            'HEALTHCARE_METRICS': {
                'prescription_processing_time': True,
                'medication_search_performance': True,
                'user_session_duration': True,
                'admin_action_latency': True,
                'api_endpoint_performance': True,
                'wagtail_page_load_time': True,
            },
            
            # Custom metrics collection
            'CUSTOM_METRICS': [
                'medguard.prescriptions.created',
                'medguard.medications.searched',
                'medguard.users.login_attempts',
                'medguard.security.events',
                'medguard.backup.operations',
                'medguard.cache.hit_rate',
            ],
        }
    
    @staticmethod
    def configure_infrastructure_monitoring():
        """
        Configure infrastructure monitoring for healthcare production.
        
        Returns:
            dict: Infrastructure monitoring configuration
        """
        return {
            # Infrastructure monitoring
            'INFRASTRUCTURE_MONITORING_ENABLED': True,
            'MONITORING_AGENT': 'datadog',  # or 'newrelic', 'prometheus'
            'MONITORING_API_KEY': os.environ.get('MONITORING_API_KEY'),
            
            # Server monitoring
            'SERVER_MONITORING': {
                'cpu_usage_alert_threshold': 80,  # 80%
                'memory_usage_alert_threshold': 85,  # 85%
                'disk_usage_alert_threshold': 90,  # 90%
                'network_latency_threshold': 100,  # 100ms
                'load_average_threshold': 5.0,
            },
            
            # Database monitoring
            'DATABASE_MONITORING': {
                'connection_pool_monitoring': True,
                'query_performance_monitoring': True,
                'slow_query_threshold': 5.0,  # 5 seconds
                'deadlock_monitoring': True,
                'replication_lag_monitoring': True,
                'backup_status_monitoring': True,
            },
            
            # Cache monitoring
            'CACHE_MONITORING': {
                'redis_monitoring': True,
                'hit_rate_monitoring': True,
                'memory_usage_monitoring': True,
                'connection_monitoring': True,
                'eviction_monitoring': True,
            },
            
            # Search engine monitoring
            'SEARCH_MONITORING': {
                'elasticsearch_cluster_health': True,
                'index_performance': True,
                'query_latency': True,
                'disk_usage': True,
                'node_status': True,
            },
        }
    
    @staticmethod
    def get_security_monitoring_settings():
        """
        Configure security monitoring for healthcare compliance.
        
        Returns:
            dict: Security monitoring configuration
        """
        return {
            # Security monitoring
            'SECURITY_MONITORING_ENABLED': True,
            'SECURITY_INFORMATION_EVENT_MANAGEMENT': True,
            'INTRUSION_DETECTION_SYSTEM': True,
            
            # Authentication monitoring
            'AUTH_MONITORING': {
                'failed_login_threshold': 5,  # 5 failed attempts
                'suspicious_login_patterns': True,
                'brute_force_detection': True,
                'account_lockout_monitoring': True,
                'password_change_monitoring': True,
                'privilege_escalation_detection': True,
            },
            
            # Access monitoring
            'ACCESS_MONITORING': {
                'unauthorized_access_attempts': True,
                'admin_access_monitoring': True,
                'api_access_monitoring': True,
                'file_access_monitoring': True,
                'database_access_monitoring': True,
                'sensitive_data_access': True,
            },
            
            # Threat detection
            'THREAT_DETECTION': {
                'sql_injection_detection': True,
                'xss_attack_detection': True,
                'csrf_attack_detection': True,
                'ddos_detection': True,
                'malware_detection': True,
                'data_exfiltration_detection': True,
            },
            
            # Compliance monitoring
            'COMPLIANCE_MONITORING': {
                'hipaa_audit_monitoring': True,
                'popia_compliance_monitoring': True,
                'data_retention_monitoring': True,
                'encryption_status_monitoring': True,
                'backup_compliance_monitoring': True,
            },
        }
    
    @staticmethod
    def configure_alerting_system():
        """
        Configure comprehensive alerting system for healthcare operations.
        
        Returns:
            dict: Alerting system configuration
        """
        return {
            # Alerting configuration
            'ALERTING_ENABLED': True,
            'ALERT_ESCALATION_ENABLED': True,
            'ALERT_DEDUPLICATION': True,
            'ALERT_CORRELATION': True,
            
            # Alert channels
            'ALERT_CHANNELS': {
                'email': {
                    'enabled': True,
                    'smtp_server': os.environ.get('SMTP_SERVER'),
                    'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
                    'smtp_username': os.environ.get('SMTP_USERNAME'),
                    'smtp_password': os.environ.get('SMTP_PASSWORD'),
                    'from_address': 'alerts@medguard.co.za',
                },
                'sms': {
                    'enabled': True,
                    'provider': 'twilio',
                    'api_key': os.environ.get('SMS_API_KEY'),
                    'sender_number': os.environ.get('SMS_SENDER_NUMBER'),
                },
                'slack': {
                    'enabled': True,
                    'webhook_url': os.environ.get('SLACK_WEBHOOK_URL'),
                    'channel': '#medguard-alerts',
                },
                'pagerduty': {
                    'enabled': True,
                    'integration_key': os.environ.get('PAGERDUTY_INTEGRATION_KEY'),
                    'service_id': os.environ.get('PAGERDUTY_SERVICE_ID'),
                },
                'microsoft_teams': {
                    'enabled': True,
                    'webhook_url': os.environ.get('TEAMS_WEBHOOK_URL'),
                },
            },
            
            # Alert severity levels
            'ALERT_SEVERITY_LEVELS': {
                'critical': {
                    'channels': ['pagerduty', 'sms', 'email', 'slack'],
                    'escalation_time': 300,  # 5 minutes
                },
                'high': {
                    'channels': ['email', 'slack'],
                    'escalation_time': 900,  # 15 minutes
                },
                'medium': {
                    'channels': ['email'],
                    'escalation_time': 1800,  # 30 minutes
                },
                'low': {
                    'channels': ['email'],
                    'escalation_time': 3600,  # 1 hour
                },
            },
            
            # Healthcare-specific alert rules
            'HEALTHCARE_ALERT_RULES': {
                'medication_system_down': 'critical',
                'prescription_processing_failure': 'critical',
                'security_breach_detected': 'critical',
                'database_connection_lost': 'critical',
                'backup_failure': 'high',
                'high_error_rate': 'high',
                'slow_response_time': 'medium',
                'cache_miss_rate_high': 'low',
            },
        }
    
    @staticmethod
    def get_logging_configuration():
        """
        Configure comprehensive logging for healthcare systems.
        
        Returns:
            dict: Logging configuration
        """
        return {
            # Logging configuration
            'LOGGING_ENABLED': True,
            'LOG_LEVEL': os.environ.get('LOG_LEVEL', 'INFO'),
            'LOG_FORMAT': 'json',  # Structured logging for better parsing
            
            # Log destinations
            'LOG_DESTINATIONS': {
                'file': {
                    'enabled': True,
                    'path': '/var/log/medguard/',
                    'rotation': 'daily',
                    'retention_days': 365,  # 1 year for healthcare compliance
                },
                'elasticsearch': {
                    'enabled': True,
                    'host': os.environ.get('ELASTICSEARCH_LOG_HOST'),
                    'index': 'medguard-logs',
                },
                'cloudwatch': {
                    'enabled': True,
                    'log_group': 'medguard-production',
                    'retention_days': 365,
                },
            },
            
            # Healthcare-specific logging
            'HEALTHCARE_LOGGING': {
                'audit_logging': True,
                'access_logging': True,
                'medication_logging': True,
                'prescription_logging': True,
                'user_activity_logging': True,
                'security_event_logging': True,
                'compliance_logging': True,
            },
            
            # Log correlation
            'LOG_CORRELATION': {
                'request_id_tracking': True,
                'user_session_tracking': True,
                'transaction_tracking': True,
                'trace_id_propagation': True,
            },
            
            # Sensitive data handling
            'LOG_SANITIZATION': {
                'phi_redaction': True,
                'pii_redaction': True,
                'password_redaction': True,
                'credit_card_redaction': True,
                'medical_record_redaction': True,
            },
        }
    
    @staticmethod
    def configure_health_checks():
        """
        Configure health checks for healthcare system components.
        
        Returns:
            dict: Health check configuration
        """
        return {
            # Health check configuration
            'HEALTH_CHECKS_ENABLED': True,
            'HEALTH_CHECK_INTERVAL': 30,  # 30 seconds
            'HEALTH_CHECK_TIMEOUT': 10,  # 10 seconds
            'HEALTH_CHECK_ENDPOINT': '/health/',
            
            # Component health checks
            'HEALTH_CHECK_COMPONENTS': {
                'database': {
                    'check': 'database_connectivity',
                    'timeout': 5,
                    'critical': True,
                },
                'cache': {
                    'check': 'redis_connectivity',
                    'timeout': 3,
                    'critical': True,
                },
                'search': {
                    'check': 'elasticsearch_health',
                    'timeout': 5,
                    'critical': False,
                },
                'storage': {
                    'check': 's3_connectivity',
                    'timeout': 10,
                    'critical': False,
                },
                'email': {
                    'check': 'smtp_connectivity',
                    'timeout': 10,
                    'critical': False,
                },
                'external_apis': {
                    'check': 'external_service_health',
                    'timeout': 15,
                    'critical': False,
                },
            },
            
            # Healthcare-specific health checks
            'HEALTHCARE_HEALTH_CHECKS': {
                'medication_service': {
                    'check': 'medication_api_health',
                    'timeout': 5,
                    'critical': True,
                },
                'prescription_service': {
                    'check': 'prescription_processing_health',
                    'timeout': 5,
                    'critical': True,
                },
                'user_authentication': {
                    'check': 'auth_service_health',
                    'timeout': 3,
                    'critical': True,
                },
                'security_monitoring': {
                    'check': 'security_service_health',
                    'timeout': 5,
                    'critical': True,
                },
            },
            
            # Health check reporting
            'HEALTH_CHECK_REPORTING': {
                'detailed_response': True,
                'include_metrics': True,
                'include_dependencies': True,
                'include_version_info': True,
            },
        }
    
    @staticmethod
    def get_dashboard_configuration():
        """
        Configure monitoring dashboards for healthcare operations.
        
        Returns:
            dict: Dashboard configuration
        """
        return {
            # Dashboard configuration
            'DASHBOARDS_ENABLED': True,
            'DASHBOARD_PLATFORM': 'grafana',  # or 'datadog', 'newrelic'
            'DASHBOARD_URL': os.environ.get('DASHBOARD_URL'),
            
            # Healthcare operation dashboards
            'HEALTHCARE_DASHBOARDS': {
                'system_overview': {
                    'widgets': [
                        'system_health',
                        'response_times',
                        'error_rates',
                        'throughput',
                        'active_users',
                    ],
                    'refresh_interval': 30,
                },
                'medication_operations': {
                    'widgets': [
                        'prescription_queue',
                        'medication_searches',
                        'prescription_processing_time',
                        'medication_alerts',
                        'inventory_status',
                    ],
                    'refresh_interval': 60,
                },
                'security_monitoring': {
                    'widgets': [
                        'security_events',
                        'failed_logins',
                        'suspicious_activities',
                        'compliance_status',
                        'audit_log_summary',
                    ],
                    'refresh_interval': 30,
                },
                'infrastructure_health': {
                    'widgets': [
                        'server_metrics',
                        'database_performance',
                        'cache_statistics',
                        'storage_usage',
                        'network_latency',
                    ],
                    'refresh_interval': 60,
                },
            },
            
            # Alert integration
            'DASHBOARD_ALERTS': {
                'alert_overlay': True,
                'alert_history': True,
                'alert_correlation': True,
                'alert_acknowledgment': True,
            },
        }
    
    @staticmethod
    def configure_synthetic_monitoring():
        """
        Configure synthetic monitoring for healthcare user journeys.
        
        Returns:
            dict: Synthetic monitoring configuration
        """
        return {
            # Synthetic monitoring
            'SYNTHETIC_MONITORING_ENABLED': True,
            'SYNTHETIC_MONITORING_PROVIDER': 'pingdom',  # or 'datadog', 'newrelic'
            
            # Healthcare user journeys
            'SYNTHETIC_TESTS': {
                'user_login_flow': {
                    'url': '/accounts/login/',
                    'interval': 300,  # 5 minutes
                    'locations': ['us-east', 'us-west', 'eu-west'],
                    'assertions': [
                        'response_time < 3000',
                        'status_code == 200',
                        'contains("Login")',
                    ],
                },
                'medication_search': {
                    'url': '/medications/search/',
                    'interval': 600,  # 10 minutes
                    'method': 'POST',
                    'data': {'query': 'aspirin'},
                    'assertions': [
                        'response_time < 2000',
                        'status_code == 200',
                        'json_path("results.length") > 0',
                    ],
                },
                'prescription_creation': {
                    'url': '/prescriptions/create/',
                    'interval': 900,  # 15 minutes
                    'requires_auth': True,
                    'assertions': [
                        'response_time < 5000',
                        'status_code == 200',
                    ],
                },
                'admin_dashboard': {
                    'url': '/admin/',
                    'interval': 300,  # 5 minutes
                    'requires_auth': True,
                    'assertions': [
                        'response_time < 4000',
                        'status_code == 200',
                        'contains("MedGuard SA")',
                    ],
                },
            },
            
            # Mobile app monitoring
            'MOBILE_MONITORING': {
                'enabled': True,
                'app_performance_monitoring': True,
                'crash_reporting': True,
                'user_experience_monitoring': True,
            },
        }
    
    @classmethod
    def apply_monitoring_configuration(cls):
        """
        Apply all monitoring and alerting configurations.
        
        Returns:
            dict: Complete monitoring configuration dictionary
        """
        config = {}
        config.update(cls.get_application_monitoring_settings())
        config.update(cls.configure_infrastructure_monitoring())
        config.update(cls.get_security_monitoring_settings())
        config.update(cls.configure_alerting_system())
        config.update(cls.get_logging_configuration())
        config.update(cls.configure_health_checks())
        config.update(cls.get_dashboard_configuration())
        config.update(cls.configure_synthetic_monitoring())
        
        return config


# Apply healthcare monitoring configuration
HEALTHCARE_MONITORING_CONFIG = WagtailHealthcareMonitoring.apply_monitoring_configuration()


# ============================================================================
# 10. WAGTAIL 7.0.2 OPTIMIZED DOCKER CONFIGURATION FOR HEALTHCARE DEPLOYMENT
# ============================================================================

class WagtailHealthcareDocker:
    """
    Optimized Docker configuration for healthcare deployment with Wagtail 7.0.2.
    Production-ready containerization with security and compliance focus.
    """
    
    @staticmethod
    def get_dockerfile_configuration():
        """
        Generate optimized Dockerfile for healthcare Wagtail deployment.
        
        Returns:
            str: Dockerfile content
        """
        dockerfile_content = '''# MedGuard SA - Healthcare Wagtail 7.0.2 Production Dockerfile
FROM python:3.11-slim-bookworm

# Set environment variables for healthcare compliance
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    DEBIAN_FRONTEND=noninteractive \\
    TZ=Africa/Johannesburg \\
    LANG=en_ZA.UTF-8 \\
    LC_ALL=en_ZA.UTF-8

# Create non-root user for security
RUN groupadd --gid 1000 medguard && \\
    useradd --uid 1000 --gid medguard --shell /bin/bash --create-home medguard

# Install system dependencies for healthcare applications
RUN apt-get update && apt-get install -y --no-install-recommends \\
    build-essential \\
    libpq-dev \\
    libjpeg-dev \\
    libpng-dev \\
    libwebp-dev \\
    libffi-dev \\
    libssl-dev \\
    libxml2-dev \\
    libxslt1-dev \\
    zlib1g-dev \\
    gettext \\
    curl \\
    wget \\
    ca-certificates \\
    gnupg2 \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Install security tools for healthcare compliance
RUN apt-get update && apt-get install -y --no-install-recommends \\
    clamav \\
    clamav-daemon \\
    fail2ban \\
    logrotate \\
    && rm -rf /var/lib/apt/lists/* \\
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt requirements_minimal.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \\
    pip install --no-cache-dir -r requirements.txt && \\
    pip install --no-cache-dir gunicorn[gevent]==21.2.0 && \\
    pip install --no-cache-dir whitenoise[brotli]==6.6.0

# Copy application code
COPY --chown=medguard:medguard . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/media /app/logs /var/log/medguard && \\
    chown -R medguard:medguard /app /var/log/medguard && \\
    chmod -R 755 /app && \\
    chmod -R 750 /app/logs /var/log/medguard

# Collect static files for production
RUN python manage.py collectstatic --noinput --clear

# Create health check script
RUN echo '#!/bin/bash\\n\\
curl -f http://localhost:8000/health/ || exit 1' > /app/healthcheck.sh && \\
    chmod +x /app/healthcheck.sh

# Switch to non-root user
USER medguard

# Expose port
EXPOSE 8000

# Health check for healthcare deployment
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD /app/healthcheck.sh

# Run application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--preload", "--access-logfile", "-", "--error-logfile", "-", "medguard_backend.wsgi:application"]
'''
        return dockerfile_content
    
    @staticmethod
    def get_docker_compose_configuration():
        """
        Generate Docker Compose configuration for healthcare deployment.
        
        Returns:
            str: Docker Compose YAML content
        """
        compose_content = '''# MedGuard SA - Healthcare Docker Compose Production
version: '3.8'

services:
  # Main Wagtail application
  web:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: medguard-web
    restart: unless-stopped
    environment:
      - DJANGO_SETTINGS_MODULE=medguard_backend.settings.production
      - DATABASE_URL=postgres://medguard:${POSTGRES_PASSWORD}@db:5432/medguard
      - REDIS_URL=redis://redis:6379/1
      - ELASTICSEARCH_URL=http://elasticsearch:9200
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - logs_volume:/var/log/medguard
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
      - elasticsearch
    networks:
      - medguard-network
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # PostgreSQL database for healthcare data
  db:
    image: postgres:15-alpine
    container_name: medguard-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=medguard
      - POSTGRES_USER=medguard
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=en_ZA.UTF-8 --lc-ctype=en_ZA.UTF-8
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "5432:5432"
    networks:
      - medguard-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medguard -d medguard"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 1.5G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Redis cache for healthcare sessions
  redis:
    image: redis:7-alpine
    container_name: medguard-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    networks:
      - medguard-network
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 128M

  # Elasticsearch for healthcare content search
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: medguard-elasticsearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=true
      - ELASTIC_PASSWORD=${ELASTIC_PASSWORD}
      - "ES_JAVA_OPTS=-Xms512m -Xmx1g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - medguard-network
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1.5G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Nginx reverse proxy for healthcare security
  nginx:
    image: nginx:alpine
    container_name: medguard-nginx
    restart: unless-stopped
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    networks:
      - medguard-network
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M

  # Celery worker for healthcare background tasks
  celery:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: medguard-celery
    restart: unless-stopped
    command: celery -A medguard_backend worker -l info --concurrency=4
    environment:
      - DJANGO_SETTINGS_MODULE=medguard_backend.settings.production
      - DATABASE_URL=postgres://medguard:${POSTGRES_PASSWORD}@db:5432/medguard
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - logs_volume:/var/log/medguard
    depends_on:
      - db
      - redis
    networks:
      - medguard-network
    healthcheck:
      test: ["CMD", "celery", "-A", "medguard_backend", "inspect", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Celery beat for healthcare scheduled tasks
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: medguard-celery-beat
    restart: unless-stopped
    command: celery -A medguard_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DJANGO_SETTINGS_MODULE=medguard_backend.settings.production
      - DATABASE_URL=postgres://medguard:${POSTGRES_PASSWORD}@db:5432/medguard
      - REDIS_URL=redis://redis:6379/1
    volumes:
      - logs_volume:/var/log/medguard
    depends_on:
      - db
      - redis
    networks:
      - medguard-network
    deploy:
      resources:
        limits:
          cpus: '0.2'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 128M

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  elasticsearch_data:
    driver: local
  static_volume:
    driver: local
  media_volume:
    driver: local
  logs_volume:
    driver: local

networks:
  medguard-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
'''
        return compose_content
    
    @staticmethod
    def get_nginx_configuration():
        """
        Generate Nginx configuration for healthcare security.
        
        Returns:
            str: Nginx configuration content
        """
        nginx_content = '''# MedGuard SA - Healthcare Nginx Configuration
events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Security headers for healthcare compliance
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Healthcare-Compliance "HIPAA" always;
    
    # Performance and security settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;
    
    # Rate limiting for healthcare protection
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
    
    # Logging for healthcare audit
    log_format healthcare '$remote_addr - $remote_user [$time_local] '
                         '"$request" $status $body_bytes_sent '
                         '"$http_referer" "$http_user_agent" '
                         '$request_time $upstream_response_time';
    
    access_log /var/log/nginx/access.log healthcare;
    error_log /var/log/nginx/error.log warn;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/json
        application/xml+rss
        application/atom+xml
        image/svg+xml;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    upstream medguard_backend {
        server web:8000;
        keepalive 32;
    }
    
    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }
    
    # Main HTTPS server
    server {
        listen 443 ssl http2;
        server_name medguard.co.za www.medguard.co.za;
        
        ssl_certificate /etc/nginx/ssl/medguard.crt;
        ssl_certificate_key /etc/nginx/ssl/medguard.key;
        
        client_max_body_size 100M;
        
        # Security headers
        add_header X-Healthcare-System "MedGuard SA" always;
        add_header X-Request-ID $request_id always;
        
        # Health check endpoint
        location /health/ {
            access_log off;
            proxy_pass http://medguard_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static files
        location /static/ {
            alias /app/staticfiles/;
            expires 1y;
            add_header Cache-Control "public, immutable";
            add_header X-Content-Source "nginx-static";
        }
        
        # Media files with access control
        location /media/ {
            alias /app/media/;
            expires 1d;
            add_header Cache-Control "private, no-transform";
            add_header X-Content-Source "nginx-media";
            
            # Restrict access to authenticated users only
            auth_request /auth-check/;
        }
        
        # Authentication check for media files
        location = /auth-check/ {
            internal;
            proxy_pass http://medguard_backend/api/auth-check/;
            proxy_pass_request_body off;
            proxy_set_header Content-Length "";
            proxy_set_header X-Original-URI $request_uri;
        }
        
        # Admin interface with rate limiting
        location /admin/ {
            limit_req zone=login burst=10 nodelay;
            proxy_pass http://medguard_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;
            
            # Additional security for admin
            add_header X-Admin-Access "restricted" always;
        }
        
        # API endpoints with rate limiting
        location /api/ {
            limit_req zone=api burst=200 nodelay;
            proxy_pass http://medguard_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;
            
            # CORS headers for healthcare API
            add_header Access-Control-Allow-Origin "https://medguard.co.za" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;
        }
        
        # Main application
        location / {
            limit_req zone=general burst=20 nodelay;
            proxy_pass http://medguard_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;
            proxy_redirect off;
            
            # Timeout settings for healthcare operations
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }
        
        # Block access to sensitive files
        location ~ /\\. {
            deny all;
            access_log off;
            log_not_found off;
        }
        
        location ~ \\.(env|ini|conf|log)$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
'''
        return nginx_content
    
    @staticmethod
    def get_docker_security_settings():
        """
        Generate Docker security configuration for healthcare compliance.
        
        Returns:
            dict: Docker security settings
        """
        return {
            # Container security settings
            'CONTAINER_SECURITY': {
                'run_as_non_root': True,
                'read_only_root_filesystem': False,  # Django needs write access
                'no_new_privileges': True,
                'drop_capabilities': ['ALL'],
                'add_capabilities': ['CHOWN', 'DAC_OVERRIDE', 'SETGID', 'SETUID'],
                'security_opt': ['no-new-privileges:true'],
            },
            
            # Network security
            'NETWORK_SECURITY': {
                'custom_bridge_network': True,
                'network_isolation': True,
                'internal_communication_only': True,
                'exposed_ports_minimal': True,
            },
            
            # Volume security
            'VOLUME_SECURITY': {
                'named_volumes': True,
                'bind_mounts_minimal': True,
                'volume_permissions': '755',
                'sensitive_data_volumes': ['postgres_data', 'redis_data'],
            },
            
            # Image security
            'IMAGE_SECURITY': {
                'base_image_scanning': True,
                'vulnerability_scanning': True,
                'image_signing': True,
                'minimal_base_image': True,
                'regular_updates': True,
            },
            
            # Runtime security
            'RUNTIME_SECURITY': {
                'resource_limits': True,
                'health_checks': True,
                'restart_policies': 'unless-stopped',
                'logging_driver': 'json-file',
                'log_rotation': True,
            },
        }
    
    @staticmethod
    def get_kubernetes_configuration():
        """
        Generate Kubernetes configuration for healthcare deployment.
        
        Returns:
            str: Kubernetes YAML configuration
        """
        k8s_content = '''# MedGuard SA - Healthcare Kubernetes Configuration
apiVersion: v1
kind: Namespace
metadata:
  name: medguard-healthcare
  labels:
    name: medguard-healthcare
    compliance: hipaa

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medguard-web
  namespace: medguard-healthcare
  labels:
    app: medguard-web
    tier: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: medguard-web
  template:
    metadata:
      labels:
        app: medguard-web
        tier: frontend
    spec:
      serviceAccountName: medguard-service-account
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: medguard-web
        image: medguard/wagtail:latest
        ports:
        - containerPort: 8000
        env:
        - name: DJANGO_SETTINGS_MODULE
          value: "medguard_backend.settings.production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: medguard-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: medguard-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health/
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: false
          capabilities:
            drop:
            - ALL

---
apiVersion: v1
kind: Service
metadata:
  name: medguard-web-service
  namespace: medguard-healthcare
spec:
  selector:
    app: medguard-web
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: medguard-ingress
  namespace: medguard-healthcare
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - medguard.co.za
    secretName: medguard-tls
  rules:
  - host: medguard.co.za
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: medguard-web-service
            port:
              number: 80
'''
        return k8s_content
    
    @classmethod
    def apply_docker_configuration(cls):
        """
        Apply all Docker configurations for healthcare deployment.
        
        Returns:
            dict: Complete Docker configuration dictionary
        """
        config = {
            'dockerfile': cls.get_dockerfile_configuration(),
            'docker_compose': cls.get_docker_compose_configuration(),
            'nginx_config': cls.get_nginx_configuration(),
            'kubernetes_config': cls.get_kubernetes_configuration(),
        }
        config.update(cls.get_docker_security_settings())
        
        return config


# Apply healthcare Docker configuration
HEALTHCARE_DOCKER_CONFIG = WagtailHealthcareDocker.apply_docker_configuration()


# ============================================================================
# COMPLETE WAGTAIL 7.0.2 HEALTHCARE PRODUCTION CONFIGURATION
# ============================================================================

def get_complete_production_config():
    """
    Combine all healthcare production configurations into a single dictionary.
    
    Returns:
        dict: Complete production configuration for MedGuard SA
    """
    complete_config = {}
    
    # Merge all configuration sections
    complete_config.update(CDN_STATIC_CONFIG)
    complete_config.update(PRODUCTION_MIGRATION_CONFIG)
    complete_config.update(HEALTHCARE_CACHE_CONFIG)
    complete_config.update(SEARCH_INDEX_CONFIG)
    complete_config.update(IMAGE_OPTIMIZATION_CONFIG)
    complete_config.update(HEALTHCARE_SECURITY_CONFIG)
    complete_config.update(HEALTHCARE_ADMIN_CONFIG)
    complete_config.update(HEALTHCARE_BACKUP_RECOVERY_CONFIG)
    complete_config.update(HEALTHCARE_MONITORING_CONFIG)
    complete_config.update(HEALTHCARE_DOCKER_CONFIG)
    
    return complete_config


# Export complete production configuration
MEDGUARD_PRODUCTION_CONFIG = get_complete_production_config()
