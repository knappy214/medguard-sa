"""
Performance Monitoring for PWA
Uses Wagtail 7.0.2's enhanced performance monitoring for PWA optimization
"""

import logging
import time
import json
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
from wagtail.models import Page
from wagtail.images.models import Image
from wagtail.images.utils import generate_signature
from wagtail.images.views.serve import serve
from wagtail.core.signals import page_published, page_unpublished
from wagtail.images.signals import image_rendition_created
from django.dispatch import receiver
from .models import PWAInstallation, OfflineData

logger = logging.getLogger(__name__)


class PWAPerformanceMonitor:
    """
    Performance monitoring for PWA using Wagtail 7.0.2 features
    """
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.query_count = 0
        self.query_time = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.init_monitoring()
    
    def init_monitoring(self):
        """Initialize performance monitoring"""
        # Set up signal handlers
        self.setup_signal_handlers()
        
        # Initialize metrics storage
        self.reset_metrics()
        
        logger.info('[PWA Performance] Monitoring initialized')
    
    def setup_signal_handlers(self):
        """Set up Wagtail signal handlers for performance monitoring"""
        
        @receiver(page_published)
        def handle_page_published(sender, instance, **kwargs):
            """Monitor page publishing performance"""
            self.record_page_publish(instance)
        
        @receiver(page_unpublished)
        def handle_page_unpublished(sender, instance, **kwargs):
            """Monitor page unpublishing performance"""
            self.record_page_unpublish(instance)
        
        @receiver(image_rendition_created)
        def handle_image_rendition(sender, instance, **kwargs):
            """Monitor image rendition creation performance"""
            self.record_image_rendition(instance)
    
    def start_monitoring(self, request_type: str = 'unknown'):
        """Start monitoring a request"""
        self.start_time = time.time()
        self.current_request_type = request_type
        self.query_count = 0
        self.query_time = 0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Record initial database state
        self.initial_db_queries = len(connection.queries)
        
        logger.debug(f'[PWA Performance] Started monitoring {request_type}')
    
    def end_monitoring(self) -> Dict[str, Any]:
        """End monitoring and return metrics"""
        if not self.start_time:
            return {}
        
        end_time = time.time()
        total_time = end_time - self.start_time
        
        # Calculate database metrics
        final_db_queries = len(connection.queries)
        db_queries = final_db_queries - self.initial_db_queries
        
        # Calculate query time
        query_time = sum(float(query.get('time', 0)) for query in connection.queries[-db_queries:])
        
        metrics = {
            'request_type': self.current_request_type,
            'total_time': total_time,
            'db_queries': db_queries,
            'query_time': query_time,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0,
            'timestamp': timezone.now().isoformat(),
            'memory_usage': self.get_memory_usage(),
            'cpu_usage': self.get_cpu_usage()
        }
        
        # Store metrics
        self.store_metrics(metrics)
        
        # Reset for next request
        self.reset_metrics()
        
        logger.debug(f'[PWA Performance] Completed monitoring: {total_time:.3f}s')
        
        return metrics
    
    def record_page_publish(self, page: Page):
        """Record page publishing performance"""
        metrics = {
            'event_type': 'page_publish',
            'page_id': page.id,
            'page_type': page.content_type.model,
            'timestamp': timezone.now().isoformat(),
            'performance_impact': self.measure_page_publish_impact(page)
        }
        
        self.store_event_metrics(metrics)
        logger.info(f'[PWA Performance] Page published: {page.title} ({page.id})')
    
    def record_page_unpublish(self, page: Page):
        """Record page unpublishing performance"""
        metrics = {
            'event_type': 'page_unpublish',
            'page_id': page.id,
            'page_type': page.content_type.model,
            'timestamp': timezone.now().isoformat()
        }
        
        self.store_event_metrics(metrics)
        logger.info(f'[PWA Performance] Page unpublished: {page.title} ({page.id})')
    
    def record_image_rendition(self, rendition):
        """Record image rendition creation performance"""
        metrics = {
            'event_type': 'image_rendition',
            'image_id': rendition.image.id,
            'filter_spec': rendition.filter_spec,
            'file_size': rendition.file.size if rendition.file else 0,
            'timestamp': timezone.now().isoformat()
        }
        
        self.store_event_metrics(metrics)
        logger.debug(f'[PWA Performance] Image rendition created: {rendition.filter_spec}')
    
    def measure_page_publish_impact(self, page: Page) -> Dict[str, Any]:
        """Measure the performance impact of publishing a page"""
        start_time = time.time()
        
        # Measure cache invalidation time
        cache_start = time.time()
        self.invalidate_page_cache(page)
        cache_time = time.time() - cache_start
        
        # Measure search index update time
        search_start = time.time()
        self.update_search_index(page)
        search_time = time.time() - search_start
        
        total_time = time.time() - start_time
        
        return {
            'total_time': total_time,
            'cache_invalidation_time': cache_time,
            'search_index_time': search_time,
            'dependencies_updated': self.count_page_dependencies(page)
        }
    
    def invalidate_page_cache(self, page: Page):
        """Invalidate page-related caches"""
        # Clear page-specific cache
        cache_key = f"page_{page.id}"
        cache.delete(cache_key)
        
        # Clear parent page cache
        if page.get_parent():
            parent_cache_key = f"page_{page.get_parent().id}"
            cache.delete(parent_cache_key)
        
        # Clear navigation cache
        cache.delete('navigation_cache')
        
        # Clear PWA app shell cache
        cache.delete_pattern(f"pwa_app_shell_*")
    
    def update_search_index(self, page: Page):
        """Update search index for the page"""
        try:
            # This would integrate with Wagtail's search backend
            # For now, we'll just simulate the operation
            time.sleep(0.01)  # Simulate search index update
        except Exception as e:
            logger.error(f'[PWA Performance] Search index update failed: {e}')
    
    def count_page_dependencies(self, page: Page) -> int:
        """Count the number of dependencies that need to be updated"""
        dependencies = 0
        
        # Count child pages
        dependencies += page.get_children().count()
        
        # Count related pages (if any)
        if hasattr(page, 'related_pages'):
            dependencies += page.related_pages.count()
        
        return dependencies
    
    def record_cache_hit(self):
        """Record a cache hit"""
        self.cache_hits += 1
    
    def record_cache_miss(self):
        """Record a cache miss"""
        self.cache_misses += 1
    
    def record_database_query(self, query_time: float):
        """Record a database query"""
        self.query_count += 1
        self.query_time += query_time
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except ImportError:
            return {'rss': 0, 'vms': 0, 'percent': 0}
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except ImportError:
            return 0.0
    
    def store_metrics(self, metrics: Dict[str, Any]):
        """Store performance metrics"""
        timestamp = timezone.now()
        date_key = timestamp.strftime('%Y-%m-%d')
        
        # Store daily metrics
        daily_key = f"pwa_performance_daily_{date_key}"
        daily_metrics = cache.get(daily_key, [])
        daily_metrics.append(metrics)
        
        # Keep only last 1000 metrics per day
        if len(daily_metrics) > 1000:
            daily_metrics = daily_metrics[-1000:]
        
        cache.set(daily_key, daily_metrics, timeout=86400)  # 24 hours
        
        # Store aggregated metrics
        self.update_aggregated_metrics(metrics)
    
    def store_event_metrics(self, metrics: Dict[str, Any]):
        """Store event-specific metrics"""
        timestamp = timezone.now()
        date_key = timestamp.strftime('%Y-%m-%d')
        
        event_key = f"pwa_performance_events_{date_key}"
        event_metrics = cache.get(event_key, [])
        event_metrics.append(metrics)
        
        # Keep only last 500 events per day
        if len(event_metrics) > 500:
            event_metrics = event_metrics[-500:]
        
        cache.set(event_key, event_metrics, timeout=86400)  # 24 hours
    
    def update_aggregated_metrics(self, metrics: Dict[str, Any]):
        """Update aggregated performance metrics"""
        timestamp = timezone.now()
        date_key = timestamp.strftime('%Y-%m-%d')
        
        agg_key = f"pwa_performance_aggregated_{date_key}"
        aggregated = cache.get(agg_key, {
            'total_requests': 0,
            'total_time': 0,
            'total_queries': 0,
            'total_query_time': 0,
            'total_cache_hits': 0,
            'total_cache_misses': 0,
            'request_types': {},
            'slowest_requests': [],
            'fastest_requests': []
        })
        
        # Update basic metrics
        aggregated['total_requests'] += 1
        aggregated['total_time'] += metrics['total_time']
        aggregated['total_queries'] += metrics['db_queries']
        aggregated['total_query_time'] += metrics['query_time']
        aggregated['total_cache_hits'] += metrics['cache_hits']
        aggregated['total_cache_misses'] += metrics['cache_misses']
        
        # Update request type metrics
        request_type = metrics['request_type']
        if request_type not in aggregated['request_types']:
            aggregated['request_types'][request_type] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0
            }
        
        req_type_metrics = aggregated['request_types'][request_type]
        req_type_metrics['count'] += 1
        req_type_metrics['total_time'] += metrics['total_time']
        req_type_metrics['avg_time'] = req_type_metrics['total_time'] / req_type_metrics['count']
        
        # Update slowest/fastest requests
        request_record = {
            'type': request_type,
            'time': metrics['total_time'],
            'timestamp': metrics['timestamp']
        }
        
        aggregated['slowest_requests'].append(request_record)
        aggregated['fastest_requests'].append(request_record)
        
        # Keep only top 10 slowest and fastest
        aggregated['slowest_requests'] = sorted(
            aggregated['slowest_requests'], 
            key=lambda x: x['time'], 
            reverse=True
        )[:10]
        
        aggregated['fastest_requests'] = sorted(
            aggregated['fastest_requests'], 
            key=lambda x: x['time']
        )[:10]
        
        cache.set(agg_key, aggregated, timeout=86400)  # 24 hours
    
    def get_performance_report(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get performance report for a specific date"""
        if not date:
            date = timezone.now().strftime('%Y-%m-%d')
        
        # Get aggregated metrics
        agg_key = f"pwa_performance_aggregated_{date}"
        aggregated = cache.get(agg_key, {})
        
        if not aggregated:
            return {'error': 'No data available for this date'}
        
        # Calculate averages
        total_requests = aggregated.get('total_requests', 0)
        if total_requests > 0:
            avg_response_time = aggregated['total_time'] / total_requests
            avg_queries_per_request = aggregated['total_queries'] / total_requests
            avg_query_time = aggregated['total_query_time'] / total_requests
            cache_hit_rate = aggregated['total_cache_hits'] / (aggregated['total_cache_hits'] + aggregated['total_cache_misses']) if (aggregated['total_cache_hits'] + aggregated['total_cache_misses']) > 0 else 0
        else:
            avg_response_time = 0
            avg_queries_per_request = 0
            avg_query_time = 0
            cache_hit_rate = 0
        
        return {
            'date': date,
            'total_requests': total_requests,
            'avg_response_time': avg_response_time,
            'avg_queries_per_request': avg_queries_per_request,
            'avg_query_time': avg_query_time,
            'cache_hit_rate': cache_hit_rate,
            'total_cache_hits': aggregated.get('total_cache_hits', 0),
            'total_cache_misses': aggregated.get('total_cache_misses', 0),
            'request_types': aggregated.get('request_types', {}),
            'slowest_requests': aggregated.get('slowest_requests', []),
            'fastest_requests': aggregated.get('fastest_requests', [])
        }
    
    def get_pwa_specific_metrics(self) -> Dict[str, Any]:
        """Get PWA-specific performance metrics"""
        timestamp = timezone.now()
        
        # Get PWA installation metrics
        installations_today = PWAInstallation.objects.filter(
            created_at__date=timestamp.date()
        ).count()
        
        # Get offline data sync metrics
        offline_data_count = OfflineData.objects.filter(
            is_synced=False
        ).count()
        
        # Get cache performance for PWA
        pwa_cache_hits = cache.get('pwa_cache_hits', 0)
        pwa_cache_misses = cache.get('pwa_cache_misses', 0)
        
        return {
            'pwa_installations_today': installations_today,
            'offline_data_pending_sync': offline_data_count,
            'pwa_cache_hit_rate': pwa_cache_hits / (pwa_cache_hits + pwa_cache_misses) if (pwa_cache_hits + pwa_cache_misses) > 0 else 0,
            'pwa_cache_hits': pwa_cache_hits,
            'pwa_cache_misses': pwa_cache_misses
        }
    
    def optimize_pwa_performance(self) -> Dict[str, Any]:
        """Analyze and suggest PWA performance optimizations"""
        report = self.get_performance_report()
        pwa_metrics = self.get_pwa_specific_metrics()
        
        optimizations = []
        
        # Check response time
        if report.get('avg_response_time', 0) > 1.0:
            optimizations.append({
                'type': 'response_time',
                'issue': 'Average response time is high',
                'suggestion': 'Consider implementing more aggressive caching or database optimization'
            })
        
        # Check cache hit rate
        if report.get('cache_hit_rate', 0) < 0.7:
            optimizations.append({
                'type': 'caching',
                'issue': 'Low cache hit rate',
                'suggestion': 'Review cache keys and implement more strategic caching'
            })
        
        # Check database queries
        if report.get('avg_queries_per_request', 0) > 10:
            optimizations.append({
                'type': 'database',
                'issue': 'High number of database queries per request',
                'suggestion': 'Optimize queries and consider using select_related/prefetch_related'
            })
        
        # Check PWA-specific metrics
        if pwa_metrics.get('offline_data_pending_sync', 0) > 100:
            optimizations.append({
                'type': 'offline_sync',
                'issue': 'High number of pending offline data syncs',
                'suggestion': 'Review background sync implementation and increase sync frequency'
            })
        
        return {
            'current_performance': report,
            'pwa_metrics': pwa_metrics,
            'optimizations': optimizations,
            'timestamp': timezone.now().isoformat()
        }
    
    def reset_metrics(self):
        """Reset current request metrics"""
        self.metrics = {}
        self.start_time = None
        self.current_request_type = None
        self.query_count = 0
        self.query_time = 0
        self.cache_hits = 0
        self.cache_misses = 0


# Global performance monitor instance
performance_monitor = PWAPerformanceMonitor()


class PerformanceMiddleware:
    """
    Django middleware for automatic performance monitoring
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Start monitoring
        request_type = self.get_request_type(request)
        performance_monitor.start_monitoring(request_type)
        
        # Process request
        response = self.get_response(request)
        
        # End monitoring and store metrics
        metrics = performance_monitor.end_monitoring()
        
        # Add performance headers to response
        if metrics:
            response['X-Performance-Total-Time'] = f"{metrics['total_time']:.3f}"
            response['X-Performance-DB-Queries'] = str(metrics['db_queries'])
            response['X-Performance-Cache-Hit-Rate'] = f"{metrics['cache_hit_rate']:.2f}"
        
        return response
    
    def get_request_type(self, request) -> str:
        """Determine the type of request for monitoring"""
        path = request.path
        
        if path.startswith('/api/pwa/'):
            return 'pwa_api'
        elif path.startswith('/admin/'):
            return 'admin'
        elif path.startswith('/static/'):
            return 'static'
        elif path.startswith('/media/'):
            return 'media'
        else:
            return 'page'


class CachePerformanceMiddleware:
    """
    Middleware for monitoring cache performance
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Monitor cache performance
        original_cache_get = cache.get
        
        def monitored_cache_get(key, *args, **kwargs):
            result = original_cache_get(key, *args, **kwargs)
            if result is None:
                performance_monitor.record_cache_miss()
            else:
                performance_monitor.record_cache_hit()
            return result
        
        # Temporarily replace cache.get
        cache.get = monitored_cache_get
        
        response = self.get_response(request)
        
        # Restore original cache.get
        cache.get = original_cache_get
        
        return response 