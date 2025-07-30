#!/usr/bin/env python
"""
Performance monitoring script for MedGuard backend.

This script monitors various performance metrics including:
- Database query performance
- Cache hit rates
- API response times
- Image processing performance
- Celery task performance
"""

import os
import sys
import time
import json
import logging
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import django
from django.conf import settings
from django.core.cache import caches
from django.db import connection
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.base')
django.setup()

from medications.models import Medication
from medications.image_tasks import process_medication_image

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring class for MedGuard backend."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()
        self.cache = caches['default']
        self.mobile_cache = caches.get('mobile_api', caches['default'])
        self.image_cache = caches.get('mobile_images', caches['default'])
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Network I/O
            network = psutil.net_io_counters()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'disk_percent': disk.percent,
                'disk_free': disk.free,
                'disk_used': disk.used,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
            }
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def collect_database_metrics(self) -> Dict[str, Any]:
        """Collect database performance metrics."""
        try:
            # Get database connection info
            db_info = connection.get_connection_params()
            
            # Execute a simple query to test performance
            start_time = time.time()
            medication_count = Medication.objects.count()
            query_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Get slow queries (if available)
            slow_queries = self._get_slow_queries()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'database_name': db_info.get('database', 'unknown'),
                'medication_count': medication_count,
                'query_time_ms': query_time,
                'slow_queries_count': len(slow_queries),
                'slow_queries': slow_queries,
            }
        except Exception as e:
            logger.error(f"Error collecting database metrics: {e}")
            return {}
    
    def collect_cache_metrics(self) -> Dict[str, Any]:
        """Collect cache performance metrics."""
        try:
            # Test cache performance
            test_key = 'performance_test'
            test_value = {'test': 'data', 'timestamp': timezone.now().isoformat()}
            
            # Test write performance
            start_time = time.time()
            self.cache.set(test_key, test_value, 60)
            write_time = (time.time() - start_time) * 1000
            
            # Test read performance
            start_time = time.time()
            retrieved_value = self.cache.get(test_key)
            read_time = (time.time() - start_time) * 1000
            
            # Clean up
            self.cache.delete(test_key)
            
            return {
                'timestamp': timezone.now().isoformat(),
                'cache_write_time_ms': write_time,
                'cache_read_time_ms': read_time,
                'cache_hit': retrieved_value is not None,
            }
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
            return {}
    
    def collect_api_metrics(self) -> Dict[str, Any]:
        """Collect API performance metrics."""
        try:
            # Simulate API performance test
            start_time = time.time()
            
            # Test medication list query
            medications = list(Medication.objects.all()[:10].values(
                'id', 'name', 'medication_type', 'pill_count'
            ))
            
            api_time = (time.time() - start_time) * 1000
            
            return {
                'timestamp': timezone.now().isoformat(),
                'api_response_time_ms': api_time,
                'medications_retrieved': len(medications),
                'response_size_bytes': len(json.dumps(medications)),
            }
        except Exception as e:
            logger.error(f"Error collecting API metrics: {e}")
            return {}
    
    def collect_image_processing_metrics(self) -> Dict[str, Any]:
        """Collect image processing performance metrics."""
        try:
            # Get image processing statistics
            pending_images = Medication.objects.filter(
                image_processing_status='pending'
            ).count()
            
            processing_images = Medication.objects.filter(
                image_processing_status='processing'
            ).count()
            
            completed_images = Medication.objects.filter(
                image_processing_status='completed'
            ).count()
            
            failed_images = Medication.objects.filter(
                image_processing_status='failed'
            ).count()
            
            return {
                'timestamp': timezone.now().isoformat(),
                'pending_images': pending_images,
                'processing_images': processing_images,
                'completed_images': completed_images,
                'failed_images': failed_images,
                'total_images': pending_images + processing_images + completed_images + failed_images,
            }
        except Exception as e:
            logger.error(f"Error collecting image processing metrics: {e}")
            return {}
    
    def collect_celery_metrics(self) -> Dict[str, Any]:
        """Collect Celery task performance metrics."""
        try:
            from celery import current_app
            
            # Get Celery stats
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                # Calculate average task time
                total_tasks = 0
                total_time = 0
                
                for worker_stats in stats.values():
                    if 'total' in worker_stats:
                        total_tasks += worker_stats['total'].get('medications.process_medication_image', 0)
                
                avg_task_time = total_time / total_tasks if total_tasks > 0 else 0
                
                return {
                    'timestamp': timezone.now().isoformat(),
                    'active_workers': len(stats),
                    'total_tasks': total_tasks,
                    'average_task_time_ms': avg_task_time,
                }
            else:
                return {
                    'timestamp': timezone.now().isoformat(),
                    'active_workers': 0,
                    'total_tasks': 0,
                    'average_task_time_ms': 0,
                }
        except Exception as e:
            logger.error(f"Error collecting Celery metrics: {e}")
            return {}
    
    def _get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow database queries (placeholder for actual implementation)."""
        # This would typically query a slow query log or use Django Debug Toolbar
        return []
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect all performance metrics."""
        return {
            'system': self.collect_system_metrics(),
            'database': self.collect_database_metrics(),
            'cache': self.collect_cache_metrics(),
            'api': self.collect_api_metrics(),
            'image_processing': self.collect_image_processing_metrics(),
            'celery': self.collect_celery_metrics(),
        }
    
    def save_metrics(self, metrics: Dict[str, Any]) -> None:
        """Save metrics to cache for monitoring."""
        try:
            timestamp = timezone.now().isoformat()
            cache_key = f'performance_metrics:{timestamp}'
            
            # Save to cache with 1 hour expiration
            self.cache.set(cache_key, metrics, 3600)
            
            # Keep only last 24 hours of metrics
            self._cleanup_old_metrics()
            
            logger.info(f"Performance metrics saved: {cache_key}")
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old performance metrics."""
        try:
            # This is a simplified cleanup - in production you might want to use a proper time-series database
            cutoff_time = timezone.now() - timedelta(hours=24)
            
            # Get all performance metric keys
            pattern = 'performance_metrics:*'
            # Note: This is a simplified approach - Redis SCAN would be more efficient
            keys_to_delete = []
            
            # Clean up old keys (simplified implementation)
            for i in range(100):  # Check last 100 keys
                test_key = f'performance_metrics:{i}'
                if self.cache.get(test_key):
                    keys_to_delete.append(test_key)
            
            if keys_to_delete:
                self.cache.delete_many(keys_to_delete)
                logger.info(f"Cleaned up {len(keys_to_delete)} old performance metrics")
        except Exception as e:
            logger.error(f"Error cleaning up old metrics: {e}")
    
    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """Generate a human-readable performance report."""
        report = []
        report.append("=" * 60)
        report.append("MEDGUARD PERFORMANCE REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # System metrics
        if metrics.get('system'):
            sys_metrics = metrics['system']
            report.append("SYSTEM METRICS:")
            report.append(f"  CPU Usage: {sys_metrics.get('cpu_percent', 0):.1f}%")
            report.append(f"  Memory Usage: {sys_metrics.get('memory_percent', 0):.1f}%")
            report.append(f"  Disk Usage: {sys_metrics.get('disk_percent', 0):.1f}%")
            report.append("")
        
        # Database metrics
        if metrics.get('database'):
            db_metrics = metrics['database']
            report.append("DATABASE METRICS:")
            report.append(f"  Medications Count: {db_metrics.get('medication_count', 0)}")
            report.append(f"  Query Time: {db_metrics.get('query_time_ms', 0):.2f}ms")
            report.append(f"  Slow Queries: {db_metrics.get('slow_queries_count', 0)}")
            report.append("")
        
        # Cache metrics
        if metrics.get('cache'):
            cache_metrics = metrics['cache']
            report.append("CACHE METRICS:")
            report.append(f"  Read Time: {cache_metrics.get('cache_read_time_ms', 0):.2f}ms")
            report.append(f"  Write Time: {cache_metrics.get('cache_write_time_ms', 0):.2f}ms")
            report.append(f"  Cache Hit: {cache_metrics.get('cache_hit', False)}")
            report.append("")
        
        # API metrics
        if metrics.get('api'):
            api_metrics = metrics['api']
            report.append("API METRICS:")
            report.append(f"  Response Time: {api_metrics.get('api_response_time_ms', 0):.2f}ms")
            report.append(f"  Response Size: {api_metrics.get('response_size_bytes', 0)} bytes")
            report.append("")
        
        # Image processing metrics
        if metrics.get('image_processing'):
            img_metrics = metrics['image_processing']
            report.append("IMAGE PROCESSING METRICS:")
            report.append(f"  Pending: {img_metrics.get('pending_images', 0)}")
            report.append(f"  Processing: {img_metrics.get('processing_images', 0)}")
            report.append(f"  Completed: {img_metrics.get('completed_images', 0)}")
            report.append(f"  Failed: {img_metrics.get('failed_images', 0)}")
            report.append("")
        
        # Celery metrics
        if metrics.get('celery'):
            celery_metrics = metrics['celery']
            report.append("CELERY METRICS:")
            report.append(f"  Active Workers: {celery_metrics.get('active_workers', 0)}")
            report.append(f"  Total Tasks: {celery_metrics.get('total_tasks', 0)}")
            report.append(f"  Avg Task Time: {celery_metrics.get('average_task_time_ms', 0):.2f}ms")
            report.append("")
        
        report.append("=" * 60)
        return "\n".join(report)


def main():
    """Main function to run performance monitoring."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    monitor = PerformanceMonitor()
    
    try:
        # Collect all metrics
        metrics = monitor.collect_all_metrics()
        
        # Save metrics
        monitor.save_metrics(metrics)
        
        # Generate and print report
        report = monitor.generate_report(metrics)
        print(report)
        
        # Save report to file
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'performance_report_{timestamp}.txt'
        
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Performance report saved to: {report_file}")
        
    except Exception as e:
        logger.error(f"Error in performance monitoring: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 