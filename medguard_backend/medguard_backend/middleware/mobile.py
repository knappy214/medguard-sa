"""
Mobile optimization middleware for enhanced performance.

This module provides middleware components for:
- Mobile API response optimization
- Mobile-specific caching strategies
- Performance monitoring and analytics
- Mobile device detection and optimization
"""

import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.core.cache import caches
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from rest_framework.response import Response

logger = logging.getLogger('mobile_performance')


class MobileOptimizationMiddleware(MiddlewareMixin):
    """
    Middleware for mobile-specific optimizations.
    
    Provides:
    - Mobile device detection
    - API response optimization
    - Performance monitoring
    - Data compression
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.mobile_cache = caches.get('mobile_api', caches['default'])
        self.image_cache = caches.get('mobile_images', caches['default'])
    
    def process_request(self, request: HttpRequest) -> None:
        """Process incoming request for mobile optimizations."""
        # Detect mobile device
        request.is_mobile = self._detect_mobile_device(request)
        
        # Add mobile-specific headers
        if request.is_mobile:
            request.mobile_optimizations = self._get_mobile_optimizations(request)
            self._add_mobile_headers(request)
        
        # Start performance timer
        request.start_time = time.time()
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process outgoing response for mobile optimizations."""
        if not hasattr(request, 'is_mobile'):
            return response
        
        if request.is_mobile:
            # Apply mobile optimizations
            response = self._apply_mobile_optimizations(request, response)
            
            # Add performance headers
            self._add_performance_headers(request, response)
            
            # Log performance metrics
            self._log_performance_metrics(request, response)
        
        return response
    
    def _detect_mobile_device(self, request: HttpRequest) -> bool:
        """Detect if the request is from a mobile device."""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        mobile_keywords = [
            'mobile', 'android', 'iphone', 'ipad', 'ipod',
            'blackberry', 'windows phone', 'opera mini',
            'mobile safari', 'mobile chrome'
        ]
        
        return any(keyword in user_agent for keyword in mobile_keywords)
    
    def _get_mobile_optimizations(self, request: HttpRequest) -> Dict[str, Any]:
        """Get mobile optimization settings for the request."""
        return {
            'enable_compression': settings.MOBILE_API_OPTIMIZATION.get('ENABLE_COMPRESSION', True),
            'enable_caching': settings.MOBILE_API_OPTIMIZATION.get('ENABLE_CACHING', True),
            'cache_duration': settings.MOBILE_API_OPTIMIZATION.get('CACHE_DURATION', 1800),
            'enable_pagination': settings.MOBILE_API_OPTIMIZATION.get('ENABLE_PAGINATION', True),
            'page_size': settings.MOBILE_API_OPTIMIZATION.get('DEFAULT_PAGE_SIZE', 20),
        }
    
    def _add_mobile_headers(self, request: HttpRequest) -> None:
        """Add mobile-specific headers to the request."""
        request.META['HTTP_X_MOBILE_OPTIMIZED'] = 'true'
        request.META['HTTP_X_DEVICE_TYPE'] = 'mobile'
    
    def _apply_mobile_optimizations(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Apply mobile-specific optimizations to the response."""
        # Apply compression if enabled
        if request.mobile_optimizations.get('enable_compression'):
            response = self._apply_compression(response)
        
        # Apply caching if enabled
        if request.mobile_optimizations.get('enable_caching'):
            response = self._apply_caching(request, response)
        
        # Add mobile-specific response headers
        response['X-Mobile-Optimized'] = 'true'
        response['X-Response-Time'] = str(self._get_response_time(request))
        
        return response
    
    def _apply_compression(self, response: HttpResponse) -> HttpResponse:
        """Apply compression to the response."""
        if hasattr(response, 'content') and len(response.content) > 1024:
            # Add compression headers
            response['Content-Encoding'] = 'gzip'
            response['Vary'] = 'Accept-Encoding'
        
        return response
    
    def _apply_caching(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Apply caching to the response."""
        if request.method == 'GET' and response.status_code == 200:
            cache_key = self._generate_cache_key(request)
            cache_duration = request.mobile_optimizations.get('cache_duration', 1800)
            
            # Cache the response
            self.mobile_cache.set(cache_key, {
                'content': response.content,
                'headers': dict(response.headers),
                'status_code': response.status_code,
            }, cache_duration)
            
            # Add cache headers
            response['X-Cache-Status'] = 'MISS'
            response['Cache-Control'] = f'public, max-age={cache_duration}'
        
        return response
    
    def _generate_cache_key(self, request: HttpRequest) -> str:
        """Generate a cache key for the request."""
        key_data = {
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None),
            'query_params': dict(request.GET.items()),
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_response_time(self, request: HttpRequest) -> float:
        """Get the response time for the request."""
        if hasattr(request, 'start_time'):
            return (time.time() - request.start_time) * 1000  # Convert to milliseconds
        return 0.0
    
    def _add_performance_headers(self, request: HttpRequest, response: HttpResponse) -> None:
        """Add performance-related headers to the response."""
        response_time = self._get_response_time(request)
        
        response['X-Response-Time'] = f'{response_time:.2f}ms'
        response['X-Request-ID'] = self._generate_request_id(request)
        
        # Add performance thresholds
        thresholds = settings.MOBILE_PERFORMANCE.get('PERFORMANCE_THRESHOLDS', {})
        api_threshold = thresholds.get('api_response_time', 2000)
        
        if response_time > api_threshold:
            response['X-Performance-Warning'] = 'slow'
            logger.warning(f'Slow API response: {response_time:.2f}ms for {request.path}')
    
    def _generate_request_id(self, request: HttpRequest) -> str:
        """Generate a unique request ID."""
        return hashlib.md5(f"{request.path}{time.time()}".encode()).hexdigest()[:16]
    
    def _log_performance_metrics(self, request: HttpRequest, response: HttpResponse) -> None:
        """Log performance metrics for monitoring."""
        response_time = self._get_response_time(request)
        
        metrics = {
            'path': request.path,
            'method': request.method,
            'response_time': response_time,
            'status_code': response.status_code,
            'content_length': len(response.content) if hasattr(response, 'content') else 0,
            'user_id': getattr(request.user, 'id', None),
            'timestamp': timezone.now().isoformat(),
        }
        
        logger.info(f'Mobile API Performance: {json.dumps(metrics)}')


class MobileCachingMiddleware(MiddlewareMixin):
    """
    Middleware for mobile-specific caching strategies.
    
    Provides:
    - Intelligent caching based on mobile context
    - Cache warming for frequently accessed data
    - Cache invalidation strategies
    - Offline data support
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.mobile_cache = caches.get('mobile_api', caches['default'])
        self.image_cache = caches.get('mobile_images', caches['default'])
    
    def process_request(self, request: HttpRequest) -> None:
        """Process request for mobile caching."""
        if not hasattr(request, 'is_mobile') or not request.is_mobile:
            return
        
        # Check for cached response
        if request.method == 'GET':
            cached_response = self._get_cached_response(request)
            if cached_response:
                request.cached_response = cached_response
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process response for mobile caching."""
        if not hasattr(request, 'is_mobile') or not request.is_mobile:
            return response
        
        # Cache the response if appropriate
        if self._should_cache_response(request, response):
            self._cache_response(request, response)
        
        # Add cache headers
        self._add_cache_headers(request, response)
        
        return response
    
    def _get_cached_response(self, request: HttpRequest) -> Optional[Dict[str, Any]]:
        """Get cached response for the request."""
        cache_key = self._generate_cache_key(request)
        return self.mobile_cache.get(cache_key)
    
    def _should_cache_response(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Determine if the response should be cached."""
        # Only cache successful GET requests
        if request.method != 'GET' or response.status_code != 200:
            return False
        
        # Don't cache responses that are too large
        if hasattr(response, 'content') and len(response.content) > 1024 * 1024:  # 1MB
            return False
        
        # Don't cache responses with certain headers
        no_cache_headers = ['no-cache', 'no-store', 'private']
        cache_control = response.get('Cache-Control', '').lower()
        
        return not any(header in cache_control for header in no_cache_headers)
    
    def _cache_response(self, request: HttpRequest, response: HttpResponse) -> None:
        """Cache the response."""
        cache_key = self._generate_cache_key(request)
        cache_duration = getattr(request, 'mobile_optimizations', {}).get('cache_duration', 1800)
        
        cache_data = {
            'content': response.content,
            'headers': dict(response.headers),
            'status_code': response.status_code,
            'cached_at': timezone.now().isoformat(),
        }
        
        self.mobile_cache.set(cache_key, cache_data, cache_duration)
        logger.info(f'Cached mobile response for {request.path}')
    
    def _generate_cache_key(self, request: HttpRequest) -> str:
        """Generate a cache key for the request."""
        key_data = {
            'path': request.path,
            'method': request.method,
            'user_id': getattr(request.user, 'id', None),
            'query_params': dict(request.GET.items()),
            'mobile': True,
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _add_cache_headers(self, request: HttpRequest, response: HttpResponse) -> None:
        """Add cache-related headers to the response."""
        cache_key = self._generate_cache_key(request)
        
        response['X-Cache-Key'] = cache_key
        response['X-Cache-Status'] = 'MISS'
        
        # Add cache control headers for mobile
        if request.method == 'GET':
            cache_duration = getattr(request, 'mobile_optimizations', {}).get('cache_duration', 1800)
            response['Cache-Control'] = f'public, max-age={cache_duration}, s-maxage={cache_duration}'
            response['Vary'] = 'Accept-Encoding, User-Agent' 