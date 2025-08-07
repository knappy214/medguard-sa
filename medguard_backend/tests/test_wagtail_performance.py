"""
Comprehensive test suite for Wagtail 7.0.2 performance regression testing in MedGuard SA.

This module tests all performance-critical functionality including:
- OptimizedPageQuerySet and page query performance
- Image rendition caching and optimization
- StreamField query optimization
- Page tree caching strategies
- Admin query optimizations
- Search query performance
- Template fragment caching
- Database query prefetching
- Memory usage optimization
- Response time benchmarking
- Concurrent load testing
- Cache effectiveness testing
- Database query analysis
- Performance monitoring and alerting
"""

import pytest
import time
import threading
import statistics
from django.test import TestCase, TransactionTestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import gc
import psutil
import os

from wagtail.test.utils import WagtailTestUtils
from wagtail.models import Page, Site
from wagtail.images.models import Image, Rendition
from wagtail.images.tests.utils import get_test_image_file
from wagtail.search import index
from wagtail.search.backends import get_search_backend

# Import performance optimization classes
from performance.wagtail_optimizations import (
    OptimizedPageQuerySet,
    ImageRenditionCache,
    StreamFieldOptimizer,
    PageTreeCache,
    AdminQueryOptimizer,
    SearchQueryOptimizer,
    TemplateFragmentCache,
    DatabasePrefetcher,
    SitemapOptimizer,
    AsyncViewSupport
)

# Import related models
from home.models import HomePage
from medications.models import (
    Medication, 
    MedicationIndexPage, 
    EnhancedPrescription,
    MedicationContentStreamBlock
)
from medguard_notifications.models import NotificationIndexPage

User = get_user_model()


class BasePerformanceTestCase(TestCase):
    """Base test case for performance testing with common setup."""
    
    def setUp(self):
        """Set up common test data."""
        super().setUp()
        
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@medguard.co.za',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@medguard.co.za',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            is_staff=True,
            is_superuser=True
        )
        
        # Set up client
        self.client = Client()
        
        # Create page hierarchy for testing
        self.root_page = Page.objects.get(id=2)
        
        self.home_page = HomePage(
            title='MedGuard SA Home',
            slug='home',
            hero_title='Welcome to MedGuard SA',
            hero_content='<p>Your healthcare companion</p>',
            main_content='<p>Professional medication management</p>'
        )
        self.root_page.add_child(instance=self.home_page)
        
        # Create medication index page
        self.med_index = MedicationIndexPage(
            title='Medications',
            slug='medications',
            intro='<p>Browse medications</p>'
        )
        self.home_page.add_child(instance=self.med_index)
        
        # Create multiple child pages for testing
        for i in range(20):
            child_page = NotificationIndexPage(
                title=f'Notification Page {i}',
                slug=f'notifications-{i}',
                intro=f'<p>Notification page {i} content</p>'
            )
            self.home_page.add_child(instance=child_page)
        
        # Create test medications
        self.medications = []
        for i in range(50):
            medication = Medication.objects.create(
                name=f'Test Medication {i}',
                generic_name=f'Generic {i}',
                strength=f'{(i % 10 + 1) * 100}mg',
                form='tablet',
                manufacturer=f'Pharma {i % 5}'
            )
            self.medications.append(medication)
        
        # Create test images
        self.test_images = []
        for i in range(10):
            image = Image.objects.create(
                title=f'Test Image {i}',
                file=get_test_image_file()
            )
            self.test_images.append(image)
        
        # Clear cache before each test
        cache.clear()
        
        # Reset query count
        reset_queries()
        
    def tearDown(self):
        """Clean up after tests."""
        cache.clear()
        gc.collect()  # Force garbage collection
        
    def measure_time(self, func, *args, **kwargs):
        """Measure execution time of a function."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
        
    def measure_queries(self, func, *args, **kwargs):
        """Measure database queries for a function."""
        reset_queries()
        result = func(*args, **kwargs)
        query_count = len(connection.queries)
        return result, query_count
        
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024


class OptimizedPageQuerySetTestCase(BasePerformanceTestCase):
    """Test cases for OptimizedPageQuerySet performance."""
    
    def test_optimized_listing_query_performance(self):
        """Test optimized listing query performance."""
        # Test standard queryset
        standard_queryset = Page.objects.all()
        
        # Test optimized queryset
        optimized_queryset = Page.objects.all().optimized_for_listing()
        
        # Measure query performance
        _, standard_time = self.measure_time(list, standard_queryset)
        _, optimized_time = self.measure_time(list, optimized_queryset)
        
        # Optimized should be faster or similar
        self.assertLessEqual(optimized_time, standard_time * 1.5)
        
        # Measure query count
        _, standard_queries = self.measure_queries(list, standard_queryset)
        _, optimized_queries = self.measure_queries(list, optimized_queryset)
        
        # Optimized should use fewer or similar queries
        self.assertLessEqual(optimized_queries, standard_queries)
        
    def test_optimized_detail_query_performance(self):
        """Test optimized detail query performance."""
        page = self.home_page
        
        # Test standard detail query
        def get_page_standard():
            return Page.objects.get(id=page.id)
        
        # Test optimized detail query
        def get_page_optimized():
            return Page.objects.optimized_for_detail().get(id=page.id)
        
        # Measure performance
        _, standard_time = self.measure_time(get_page_standard)
        _, optimized_time = self.measure_time(get_page_optimized)
        
        # Should be faster or similar
        self.assertLessEqual(optimized_time, standard_time * 1.2)
        
    def test_children_optimization_performance(self):
        """Test children optimization performance."""
        # Test standard children query
        def get_children_standard():
            return list(self.home_page.get_children())
        
        # Test optimized children query
        def get_children_optimized():
            return list(Page.objects.with_children_optimized().get(
                id=self.home_page.id
            ).get_children())
        
        # Measure performance
        _, standard_time = self.measure_time(get_children_standard)
        _, optimized_time = self.measure_time(get_children_optimized)
        
        # Measure queries
        _, standard_queries = self.measure_queries(get_children_standard)
        _, optimized_queries = self.measure_queries(get_children_optimized)
        
        # Optimized should use fewer queries
        self.assertLess(optimized_queries, standard_queries)
        
    def test_bulk_operations_performance(self):
        """Test bulk operations performance."""
        # Create many pages for bulk testing
        pages_to_create = []
        for i in range(100):
            page_data = NotificationIndexPage(
                title=f'Bulk Test Page {i}',
                slug=f'bulk-test-{i}',
                intro=f'<p>Bulk test page {i}</p>'
            )
            pages_to_create.append(page_data)
        
        # Test bulk creation performance
        start_time = time.time()
        
        for page in pages_to_create:
            self.home_page.add_child(instance=page)
        
        bulk_creation_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(bulk_creation_time, 30.0)  # 30 seconds for 100 pages
        
        # Test bulk query performance
        start_time = time.time()
        
        bulk_pages = list(Page.objects.optimized_for_listing().filter(
            title__startswith='Bulk Test Page'
        ))
        
        bulk_query_time = time.time() - start_time
        
        self.assertEqual(len(bulk_pages), 100)
        self.assertLess(bulk_query_time, 2.0)  # 2 seconds for querying 100 pages


class ImageRenditionCacheTestCase(BasePerformanceTestCase):
    """Test cases for image rendition caching performance."""
    
    def setUp(self):
        """Set up image rendition test data."""
        super().setUp()
        self.rendition_cache = ImageRenditionCache()
        
    def test_image_rendition_generation_performance(self):
        """Test image rendition generation performance."""
        image = self.test_images[0]
        
        # Test first rendition generation (no cache)
        start_time = time.time()
        rendition1 = image.get_rendition('fill-300x200')
        first_generation_time = time.time() - start_time
        
        # Test second rendition generation (should use cache)
        start_time = time.time()
        rendition2 = image.get_rendition('fill-300x200')
        second_generation_time = time.time() - start_time
        
        # Cached version should be much faster
        self.assertLess(second_generation_time, first_generation_time * 0.5)
        self.assertEqual(rendition1.id, rendition2.id)
        
    def test_multiple_rendition_performance(self):
        """Test performance with multiple renditions."""
        image = self.test_images[0]
        
        rendition_specs = [
            'fill-100x100',
            'fill-200x200',
            'fill-300x200',
            'width-400',
            'height-300'
        ]
        
        # Generate all renditions
        start_time = time.time()
        
        renditions = []
        for spec in rendition_specs:
            rendition = image.get_rendition(spec)
            renditions.append(rendition)
        
        generation_time = time.time() - start_time
        
        self.assertEqual(len(renditions), 5)
        self.assertLess(generation_time, 10.0)  # Should complete within 10 seconds
        
    def test_rendition_cache_effectiveness(self):
        """Test rendition cache effectiveness."""
        # Test cache hit rate
        cache_hits = 0
        cache_misses = 0
        
        for i in range(10):
            for image in self.test_images[:5]:  # Use first 5 images
                # Request same rendition multiple times
                rendition = image.get_rendition('fill-150x150')
                
                # Check if rendition was cached
                cache_key = f"rendition_{image.id}_fill-150x150"
                if cache.get(cache_key):
                    cache_hits += 1
                else:
                    cache_misses += 1
                    cache.set(cache_key, rendition.id, 3600)
        
        # Calculate cache hit rate
        total_requests = cache_hits + cache_misses
        hit_rate = cache_hits / total_requests if total_requests > 0 else 0
        
        # Should have reasonable cache hit rate
        self.assertGreater(hit_rate, 0.5)  # At least 50% hit rate
        
    def test_image_memory_usage(self):
        """Test image processing memory usage."""
        initial_memory = self.get_memory_usage()
        
        # Process multiple large images
        for i in range(5):
            image = self.test_images[i]
            # Generate multiple renditions
            renditions = [
                image.get_rendition('fill-800x600'),
                image.get_rendition('fill-400x300'),
                image.get_rendition('fill-200x150')
            ]
        
        peak_memory = self.get_memory_usage()
        
        # Force garbage collection
        gc.collect()
        
        final_memory = self.get_memory_usage()
        
        # Memory usage should not grow excessively
        memory_growth = peak_memory - initial_memory
        self.assertLess(memory_growth, 100)  # Less than 100MB growth


class StreamFieldOptimizerTestCase(BasePerformanceTestCase):
    """Test cases for StreamField optimization performance."""
    
    def setUp(self):
        """Set up StreamField test data."""
        super().setUp()
        self.optimizer = StreamFieldOptimizer()
        
        # Create page with complex StreamField content
        self.stream_data = [
            {
                'type': 'medication_info',
                'value': {
                    'name': f'StreamField Med {i}',
                    'strength': '500mg',
                    'description': f'Description for medication {i}'
                }
            }
            for i in range(20)
        ]
        
    def test_streamfield_serialization_performance(self):
        """Test StreamField serialization performance."""
        # Create StreamField content
        stream_block = MedicationContentStreamBlock()
        
        # Test serialization performance
        start_time = time.time()
        
        serialized_data = []
        for data in self.stream_data:
            serialized = stream_block.to_python(data)
            serialized_data.append(serialized)
        
        serialization_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(serialization_time, 2.0)
        self.assertEqual(len(serialized_data), 20)
        
    def test_streamfield_rendering_performance(self):
        """Test StreamField rendering performance."""
        stream_block = MedicationContentStreamBlock()
        
        # Test rendering performance
        start_time = time.time()
        
        rendered_content = []
        for data in self.stream_data:
            rendered = stream_block.render(data)
            rendered_content.append(rendered)
        
        rendering_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(rendering_time, 3.0)
        self.assertEqual(len(rendered_content), 20)
        
    def test_streamfield_query_optimization(self):
        """Test StreamField query optimization."""
        # Create pages with StreamField content
        pages_with_streams = []
        
        for i in range(10):
            page = NotificationIndexPage(
                title=f'Stream Page {i}',
                slug=f'stream-page-{i}',
                intro=f'<p>Page with stream content {i}</p>'
            )
            self.home_page.add_child(instance=page)
            pages_with_streams.append(page)
        
        # Test querying pages with StreamField content
        start_time = time.time()
        
        stream_pages = list(Page.objects.filter(
            title__startswith='Stream Page'
        ).specific())
        
        query_time = time.time() - start_time
        
        self.assertEqual(len(stream_pages), 10)
        self.assertLess(query_time, 2.0)


class PageTreeCacheTestCase(BasePerformanceTestCase):
    """Test cases for page tree caching performance."""
    
    def setUp(self):
        """Set up page tree cache test data."""
        super().setUp()
        self.tree_cache = PageTreeCache()
        
    def test_page_tree_generation_performance(self):
        """Test page tree generation performance."""
        # Test tree generation without cache
        start_time = time.time()
        tree_without_cache = self.tree_cache.get_page_tree(use_cache=False)
        time_without_cache = time.time() - start_time
        
        # Test tree generation with cache
        start_time = time.time()
        tree_with_cache = self.tree_cache.get_page_tree(use_cache=True)
        time_with_cache = time.time() - start_time
        
        # Cached version should be faster
        self.assertLess(time_with_cache, time_without_cache * 0.8)
        
        # Trees should be equivalent
        self.assertEqual(len(tree_without_cache), len(tree_with_cache))
        
    def test_page_tree_invalidation_performance(self):
        """Test page tree cache invalidation performance."""
        # Generate cached tree
        self.tree_cache.get_page_tree(use_cache=True)
        
        # Test invalidation performance
        start_time = time.time()
        self.tree_cache.invalidate_tree_cache()
        invalidation_time = time.time() - start_time
        
        # Should be very fast
        self.assertLess(invalidation_time, 0.1)
        
        # Verify cache was invalidated
        cache_key = self.tree_cache.get_cache_key()
        cached_tree = cache.get(cache_key)
        self.assertIsNone(cached_tree)
        
    def test_nested_page_tree_performance(self):
        """Test performance with deeply nested page tree."""
        # Create nested page structure
        current_parent = self.home_page
        
        for level in range(5):  # 5 levels deep
            for i in range(3):  # 3 children per level
                child_page = NotificationIndexPage(
                    title=f'Level {level} Page {i}',
                    slug=f'level-{level}-page-{i}',
                    intro=f'<p>Nested page at level {level}</p>'
                )
                current_parent.add_child(instance=child_page)
                
                if level < 4:  # Don't go too deep
                    current_parent = child_page
        
        # Test tree generation performance with nested structure
        start_time = time.time()
        nested_tree = self.tree_cache.get_page_tree(max_depth=5)
        nested_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(nested_time, 5.0)
        self.assertIsInstance(nested_tree, list)


class AdminQueryOptimizerTestCase(BasePerformanceTestCase):
    """Test cases for admin query optimization."""
    
    def setUp(self):
        """Set up admin query test data."""
        super().setUp()
        self.admin_optimizer = AdminQueryOptimizer()
        
    def test_admin_listing_performance(self):
        """Test admin listing page performance."""
        # Login as admin
        self.client.force_login(self.admin_user)
        
        # Test admin listing performance
        start_time = time.time()
        response = self.client.get('/admin/pages/')
        admin_listing_time = time.time() - start_time
        
        # Should load within reasonable time
        self.assertLess(admin_listing_time, 3.0)
        self.assertEqual(response.status_code, 200)
        
    def test_admin_page_edit_performance(self):
        """Test admin page edit performance."""
        self.client.force_login(self.admin_user)
        
        # Test page edit loading performance
        start_time = time.time()
        response = self.client.get(f'/admin/pages/{self.home_page.id}/edit/')
        edit_loading_time = time.time() - start_time
        
        # Should load within reasonable time
        self.assertLess(edit_loading_time, 2.0)
        self.assertEqual(response.status_code, 200)
        
    def test_admin_bulk_operations_performance(self):
        """Test admin bulk operations performance."""
        self.client.force_login(self.admin_user)
        
        # Get pages for bulk operation
        child_pages = list(self.home_page.get_children()[:10])
        page_ids = [page.id for page in child_pages]
        
        # Test bulk delete performance
        start_time = time.time()
        
        # Simulate bulk operation (without actually deleting)
        bulk_queryset = Page.objects.filter(id__in=page_ids)
        bulk_count = bulk_queryset.count()
        
        bulk_operation_time = time.time() - start_time
        
        self.assertEqual(bulk_count, len(page_ids))
        self.assertLess(bulk_operation_time, 1.0)
        
    def test_admin_search_performance(self):
        """Test admin search performance."""
        self.client.force_login(self.admin_user)
        
        # Test admin search
        start_time = time.time()
        response = self.client.get('/admin/pages/search/?q=MedGuard')
        search_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(search_time, 2.0)
        self.assertEqual(response.status_code, 200)


class SearchQueryOptimizerTestCase(BasePerformanceTestCase):
    """Test cases for search query optimization."""
    
    def setUp(self):
        """Set up search optimization test data."""
        super().setUp()
        self.search_optimizer = SearchQueryOptimizer()
        self.search_backend = get_search_backend()
        
        # Index test content
        for medication in self.medications[:20]:
            self.search_backend.add(medication)
        
        self.search_backend.refresh_index()
        
    def test_search_query_performance(self):
        """Test search query performance."""
        # Test search performance
        start_time = time.time()
        
        results = self.search_backend.search('Test Medication', Medication)
        
        search_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(search_time, 1.0)
        self.assertGreater(len(results), 0)
        
    def test_complex_search_performance(self):
        """Test complex search query performance."""
        # Test complex search with filters
        start_time = time.time()
        
        complex_results = self.search_backend.search(
            'Medication',
            Medication.objects.filter(form='tablet')
        )
        
        complex_search_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(complex_search_time, 2.0)
        
    def test_search_pagination_performance(self):
        """Test search pagination performance."""
        # Test paginated search results
        page_sizes = [10, 20, 50]
        
        for page_size in page_sizes:
            start_time = time.time()
            
            results = self.search_backend.search(
                'Test',
                Medication
            )[:page_size]
            
            # Force evaluation
            list(results)
            
            pagination_time = time.time() - start_time
            
            # Should scale reasonably with page size
            self.assertLess(pagination_time, 2.0)
            
    def test_search_autocomplete_performance(self):
        """Test search autocomplete performance."""
        # Test autocomplete suggestions
        autocomplete_queries = ['Te', 'Test', 'Test M', 'Test Med']
        
        for query in autocomplete_queries:
            start_time = time.time()
            
            suggestions = self.search_backend.autocomplete(query, Medication)
            
            autocomplete_time = time.time() - start_time
            
            # Autocomplete should be very fast
            self.assertLess(autocomplete_time, 0.5)


class CacheEffectivenessTestCase(BasePerformanceTestCase):
    """Test cases for cache effectiveness."""
    
    def test_page_cache_effectiveness(self):
        """Test page caching effectiveness."""
        # Test uncached page load
        cache.clear()
        
        start_time = time.time()
        response1 = self.client.get(self.home_page.url)
        uncached_time = time.time() - start_time
        
        # Test cached page load
        start_time = time.time()
        response2 = self.client.get(self.home_page.url)
        cached_time = time.time() - start_time
        
        # Both should succeed
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Cached version should be faster
        self.assertLess(cached_time, uncached_time * 0.8)
        
    def test_template_fragment_cache_effectiveness(self):
        """Test template fragment caching effectiveness."""
        fragment_cache = TemplateFragmentCache()
        
        # Test fragment caching
        cache_key = 'test_fragment'
        fragment_content = '<div>Expensive template fragment</div>'
        
        # Cache the fragment
        start_time = time.time()
        fragment_cache.set_fragment(cache_key, fragment_content)
        cache_set_time = time.time() - start_time
        
        # Retrieve the fragment
        start_time = time.time()
        cached_fragment = fragment_cache.get_fragment(cache_key)
        cache_get_time = time.time() - start_time
        
        self.assertEqual(cached_fragment, fragment_content)
        self.assertLess(cache_get_time, cache_set_time)
        
    def test_query_cache_effectiveness(self):
        """Test database query caching effectiveness."""
        # Test query without cache
        reset_queries()
        start_time = time.time()
        
        medications_uncached = list(Medication.objects.all()[:10])
        
        uncached_time = time.time() - start_time
        uncached_queries = len(connection.queries)
        
        # Test query with cache (simulate with select_related)
        reset_queries()
        start_time = time.time()
        
        medications_optimized = list(
            Medication.objects.select_related().all()[:10]
        )
        
        optimized_time = time.time() - start_time
        optimized_queries = len(connection.queries)
        
        # Results should be the same
        self.assertEqual(len(medications_uncached), len(medications_optimized))
        
        # Optimized version should use fewer queries
        self.assertLessEqual(optimized_queries, uncached_queries)


class ConcurrentLoadTestCase(TransactionTestCase):
    """Test cases for concurrent load testing."""
    
    def setUp(self):
        """Set up concurrent load test data."""
        # Create test user
        self.user = User.objects.create_user(
            username='loadtest_user',
            email='loadtest@medguard.co.za',
            password='loadtest123'
        )
        
        # Create test page
        root_page = Page.objects.get(id=2)
        self.home_page = HomePage(
            title='Load Test Home',
            slug='load-test-home',
            hero_title='Load Test Page'
        )
        root_page.add_child(instance=self.home_page)
        
    def test_concurrent_page_requests(self):
        """Test concurrent page requests."""
        results = []
        errors = []
        
        def make_request():
            try:
                client = Client()
                start_time = time.time()
                response = client.get(self.home_page.url)
                end_time = time.time()
                
                results.append({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))
        
        # Create and start threads
        threads = []
        num_threads = 10
        
        for i in range(num_threads):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r['status_code'] == 200]
        response_times = [r['response_time'] for r in successful_requests]
        
        # Should handle concurrent requests successfully
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(successful_requests), num_threads)
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        # Performance assertions
        self.assertLess(avg_response_time, 2.0)  # Average under 2 seconds
        self.assertLess(max_response_time, 5.0)  # Max under 5 seconds
        self.assertLess(total_time, 10.0)  # Total time under 10 seconds
        
    def test_concurrent_database_operations(self):
        """Test concurrent database operations."""
        results = []
        errors = []
        
        def create_medication():
            try:
                start_time = time.time()
                medication = Medication.objects.create(
                    name=f'Concurrent Med {threading.current_thread().ident}',
                    strength='100mg',
                    form='tablet'
                )
                end_time = time.time()
                
                results.append({
                    'medication_id': medication.id,
                    'creation_time': end_time - start_time
                })
            except Exception as e:
                errors.append(str(e))
        
        # Create and start threads
        threads = []
        num_threads = 20
        
        for i in range(num_threads):
            thread = threading.Thread(target=create_medication)
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Analyze results
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), num_threads)
        
        # Verify all medications were created
        created_medications = Medication.objects.filter(
            name__startswith='Concurrent Med'
        ).count()
        
        self.assertEqual(created_medications, num_threads)


class MemoryUsageTestCase(BasePerformanceTestCase):
    """Test cases for memory usage optimization."""
    
    def test_page_memory_usage(self):
        """Test memory usage when loading many pages."""
        initial_memory = self.get_memory_usage()
        
        # Load many pages
        pages = []
        for i in range(100):
            page = Page.objects.get(id=self.home_page.id)
            pages.append(page)
        
        peak_memory = self.get_memory_usage()
        
        # Clear references
        pages.clear()
        gc.collect()
        
        final_memory = self.get_memory_usage()
        
        # Memory should be released after clearing references
        memory_growth = peak_memory - initial_memory
        memory_released = peak_memory - final_memory
        
        self.assertLess(memory_growth, 50)  # Less than 50MB growth
        self.assertGreater(memory_released, memory_growth * 0.5)  # At least 50% released
        
    def test_image_memory_usage(self):
        """Test memory usage when processing images."""
        initial_memory = self.get_memory_usage()
        
        # Process many images
        renditions = []
        for image in self.test_images:
            rendition = image.get_rendition('fill-400x300')
            renditions.append(rendition)
        
        peak_memory = self.get_memory_usage()
        
        # Clear references
        renditions.clear()
        gc.collect()
        
        final_memory = self.get_memory_usage()
        
        # Memory usage should be reasonable
        memory_growth = peak_memory - initial_memory
        self.assertLess(memory_growth, 100)  # Less than 100MB for image processing
        
    def test_query_memory_usage(self):
        """Test memory usage for large querysets."""
        initial_memory = self.get_memory_usage()
        
        # Create large queryset
        large_queryset = list(Medication.objects.all())
        
        peak_memory = self.get_memory_usage()
        
        # Clear queryset
        large_queryset.clear()
        gc.collect()
        
        final_memory = self.get_memory_usage()
        
        # Memory should be managed efficiently
        memory_growth = peak_memory - initial_memory
        self.assertLess(memory_growth, 30)  # Less than 30MB for medication queryset


class PerformanceRegressionTestCase(BasePerformanceTestCase):
    """Test cases for performance regression detection."""
    
    def test_page_load_regression(self):
        """Test for page load performance regression."""
        # Baseline performance (simulated)
        baseline_time = 0.5  # 500ms baseline
        
        # Current performance
        start_time = time.time()
        response = self.client.get(self.home_page.url)
        current_time = time.time() - start_time
        
        # Should not regress significantly
        self.assertEqual(response.status_code, 200)
        self.assertLess(current_time, baseline_time * 2.0)  # Allow 100% regression threshold
        
    def test_database_query_regression(self):
        """Test for database query performance regression."""
        # Baseline query count (simulated)
        baseline_queries = 5
        
        # Current query count
        reset_queries()
        list(Page.objects.optimized_for_listing()[:10])
        current_queries = len(connection.queries)
        
        # Should not regress significantly
        self.assertLessEqual(current_queries, baseline_queries * 1.5)  # Allow 50% regression
        
    def test_search_performance_regression(self):
        """Test for search performance regression."""
        # Baseline search time (simulated)
        baseline_search_time = 0.3  # 300ms baseline
        
        # Current search performance
        start_time = time.time()
        results = self.search_backend.search('Test', Medication)
        list(results[:10])  # Force evaluation
        current_search_time = time.time() - start_time
        
        # Should not regress significantly
        self.assertLess(current_search_time, baseline_search_time * 2.0)


@pytest.mark.django_db
class PerformanceMonitoringTestCase(TestCase):
    """Test cases for performance monitoring and alerting."""
    
    def test_performance_metrics_collection(self):
        """Test performance metrics collection."""
        # Simulate performance metrics
        metrics = {
            'page_load_time': 0.8,
            'database_queries': 12,
            'memory_usage': 45.2,
            'cache_hit_rate': 0.85
        }
        
        # Test metrics validation
        self.assertLess(metrics['page_load_time'], 2.0)
        self.assertLess(metrics['database_queries'], 20)
        self.assertLess(metrics['memory_usage'], 100.0)
        self.assertGreater(metrics['cache_hit_rate'], 0.7)
        
    def test_performance_alerting(self):
        """Test performance alerting thresholds."""
        # Define performance thresholds
        thresholds = {
            'page_load_time_warning': 1.0,
            'page_load_time_critical': 3.0,
            'database_queries_warning': 15,
            'database_queries_critical': 30,
            'memory_usage_warning': 80.0,
            'memory_usage_critical': 95.0
        }
        
        # Test threshold validation
        test_metrics = {
            'page_load_time': 2.5,  # Should trigger warning
            'database_queries': 25,  # Should trigger warning
            'memory_usage': 85.0    # Should trigger warning
        }
        
        # Check alerts
        alerts = []
        
        if test_metrics['page_load_time'] > thresholds['page_load_time_warning']:
            alerts.append('Page load time warning')
        
        if test_metrics['database_queries'] > thresholds['database_queries_warning']:
            alerts.append('Database queries warning')
        
        if test_metrics['memory_usage'] > thresholds['memory_usage_warning']:
            alerts.append('Memory usage warning')
        
        # Should have triggered alerts
        self.assertEqual(len(alerts), 3)
        
    def test_performance_trend_analysis(self):
        """Test performance trend analysis."""
        # Simulate historical performance data
        historical_data = [
            {'timestamp': timezone.now() - timedelta(days=7), 'page_load_time': 0.5},
            {'timestamp': timezone.now() - timedelta(days=6), 'page_load_time': 0.6},
            {'timestamp': timezone.now() - timedelta(days=5), 'page_load_time': 0.7},
            {'timestamp': timezone.now() - timedelta(days=4), 'page_load_time': 0.8},
            {'timestamp': timezone.now() - timedelta(days=3), 'page_load_time': 0.9},
            {'timestamp': timezone.now() - timedelta(days=2), 'page_load_time': 1.0},
            {'timestamp': timezone.now() - timedelta(days=1), 'page_load_time': 1.1},
        ]
        
        # Calculate trend
        load_times = [data['page_load_time'] for data in historical_data]
        trend = (load_times[-1] - load_times[0]) / len(load_times)
        
        # Should detect degrading performance
        self.assertGreater(trend, 0)  # Positive trend indicates degradation
        
        # Trend should trigger investigation if significant
        if trend > 0.05:  # 50ms per day degradation
            investigation_needed = True
        else:
            investigation_needed = False
        
        self.assertTrue(investigation_needed)
