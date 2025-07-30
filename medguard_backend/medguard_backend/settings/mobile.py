"""
Mobile-specific settings for optimized performance.

This module contains settings optimized for mobile applications,
including API response optimization, caching strategies, and
mobile-specific features.
"""

from .base import *

# Mobile-specific cache configuration
CACHES.update({
    'mobile_api': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'socket_keepalive': True,
            },
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'mobile_api',
        'TIMEOUT': 1800,  # 30 minutes for mobile API responses
    },
    'mobile_images': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 20},
        },
        'KEY_PREFIX': 'mobile_images',
        'TIMEOUT': 86400,  # 24 hours for mobile image cache
    },
})

# Mobile API optimization settings
REST_FRAMEWORK.update({
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,  # Smaller page size for mobile
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'mobile_api': '500/hour',
        'mobile_images': '200/hour',
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
})

# Mobile-specific middleware
MIDDLEWARE += [
    'medguard_backend.middleware.mobile.MobileOptimizationMiddleware',
    'medguard_backend.middleware.mobile.MobileCachingMiddleware',
]

# Mobile image optimization settings
MOBILE_IMAGE_SETTINGS = {
    'THUMBNAIL_SIZES': {
        'small': (150, 150),
        'medium': (300, 300),
        'large': (600, 600),
    },
    'FORMATS': ['webp', 'avif', 'jpeg'],
    'QUALITY': {
        'webp': 85,
        'avif': 80,
        'jpeg': 90,
    },
    'COMPRESSION': {
        'webp': 'lossy',
        'avif': 'lossy',
        'jpeg': 'progressive',
    },
    'CACHE_DURATION': 86400,  # 24 hours
    'MAX_FILE_SIZE': 5 * 1024 * 1024,  # 5MB
}

# Mobile API response optimization
MOBILE_API_OPTIMIZATION = {
    'ENABLE_COMPRESSION': True,
    'COMPRESSION_LEVEL': 6,
    'ENABLE_CACHING': True,
    'CACHE_DURATION': 1800,  # 30 minutes
    'ENABLE_PAGINATION': True,
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
    'ENABLE_FIELD_FILTERING': True,
    'ENABLE_SELECT_RELATED': True,
    'ENABLE_PREFETCH_RELATED': True,
}

# Mobile push notification settings
MOBILE_PUSH_SETTINGS = {
    'ENABLE_PUSH_NOTIFICATIONS': True,
    'MAX_RETRY_ATTEMPTS': 3,
    'RETRY_DELAY': 60,  # seconds
    'BATCH_SIZE': 100,
    'ENABLE_SILENT_PUSH': True,
    'ENABLE_RICH_NOTIFICATIONS': True,
    'NOTIFICATION_TTL': 86400,  # 24 hours
}

# Mobile security settings
MOBILE_SECURITY = {
    'ENABLE_API_RATE_LIMITING': True,
    'ENABLE_REQUEST_SIGNING': True,
    'ENABLE_RESPONSE_ENCRYPTION': False,  # Enable if needed
    'ENABLE_DEVICE_FINGERPRINTING': True,
    'ENABLE_SESSION_MANAGEMENT': True,
    'SESSION_TIMEOUT': 3600,  # 1 hour
    'MAX_DEVICES_PER_USER': 5,
}

# Mobile performance monitoring
MOBILE_PERFORMANCE = {
    'ENABLE_PERFORMANCE_MONITORING': True,
    'ENABLE_APM': True,
    'ENABLE_ERROR_TRACKING': True,
    'ENABLE_USAGE_ANALYTICS': True,
    'ENABLE_CRASH_REPORTING': True,
    'PERFORMANCE_THRESHOLDS': {
        'api_response_time': 2000,  # ms
        'image_load_time': 3000,  # ms
        'cache_hit_ratio': 0.8,  # 80%
    },
}

# Mobile offline support
MOBILE_OFFLINE = {
    'ENABLE_OFFLINE_CACHING': True,
    'OFFLINE_CACHE_DURATION': 604800,  # 7 days
    'SYNC_INTERVAL': 300,  # 5 minutes
    'ENABLE_BACKGROUND_SYNC': True,
    'ENABLE_CONFLICT_RESOLUTION': True,
    'MAX_OFFLINE_ACTIONS': 1000,
}

# Mobile data optimization
MOBILE_DATA_OPTIMIZATION = {
    'ENABLE_DATA_COMPRESSION': True,
    'ENABLE_IMAGE_OPTIMIZATION': True,
    'ENABLE_LAZY_LOADING': True,
    'ENABLE_PREFETCHING': True,
    'ENABLE_BACKGROUND_REFRESH': True,
    'DATA_USAGE_LIMITS': {
        'daily_limit': 50 * 1024 * 1024,  # 50MB
        'monthly_limit': 1024 * 1024 * 1024,  # 1GB
    },
}

# Logging for mobile
LOGGING['loggers'].update({
    'mobile_api': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
        'propagate': False,
    },
    'mobile_performance': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
        'propagate': False,
    },
    'mobile_errors': {
        'handlers': ['console', 'file'],
        'level': 'ERROR',
        'propagate': False,
    },
}) 