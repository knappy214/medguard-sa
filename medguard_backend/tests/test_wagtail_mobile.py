"""
Comprehensive test suite for Wagtail 7.0.2 mobile and PWA features in MedGuard SA.

This module tests all mobile and PWA functionality including:
- MobileImageOptimizer and responsive image system
- PushSubscription and push notification handling
- MedicationReminder and PWA notifications
- PWA manifest generation and service worker
- Mobile-optimized admin interface
- Touch-friendly UI components
- Progressive loading and caching
- Mobile search optimization
- Offline functionality testing
- Mobile performance optimization
- PWA installation and updates
- Mobile-specific StreamField blocks
- Responsive template rendering
- Mobile analytics and tracking
"""

import pytest
import json
import base64
from django.test import TestCase, Client, RequestFactory, override_settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.template import Template, Context
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from wagtail.test.utils import WagtailTestUtils
from wagtail.models import Page, Site
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file

# Import mobile and PWA classes
from mobile.wagtail_mobile import (
    MobileImageOptimizer,
    MobilePageOptimizer,
    TouchAdminInterface,
    MobileSearchOptimizer,
    ProgressiveLoadingManager
)
from mobile.pwa import (
    PWAManifestGenerator,
    ServiceWorkerManager,
    OfflineCacheManager,
    PWAInstallPrompt
)
from mobile.streamfield_blocks import (
    MobileMedicationBlock,
    TouchOptimizedFormBlock,
    ResponsiveImageBlock,
    MobileNavigationBlock
)
from mobile.analytics import MobileAnalytics
from mobile.notifications import MobilePushNotificationManager

# Import PWA models
from pwa.models import (
    PushSubscription,
    MedicationReminder,
    PWASession,
    OfflineCache
)

# Import related models
from home.models import HomePage
from medications.models import Medication, MedicationIndexPage

User = get_user_model()


class BaseMobileTestCase(TestCase):
    """Base test case for mobile testing with common setup."""
    
    def setUp(self):
        """Set up common test data."""
        super().setUp()
        
        # Create test users
        self.user = User.objects.create_user(
            username='mobileuser',
            email='mobile@medguard.co.za',
            password='mobilepass123',
            first_name='Mobile',
            last_name='User'
        )
        
        self.admin_user = User.objects.create_user(
            username='mobileadmin',
            email='mobileadmin@medguard.co.za',
            password='adminpass123',
            first_name='Mobile',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Set up clients
        self.client = Client()
        self.factory = RequestFactory()
        
        # Create test pages
        self.root_page = Page.objects.get(id=2)
        
        self.home_page = HomePage(
            title='MedGuard Mobile Home',
            slug='mobile-home',
            hero_title='Mobile Healthcare',
            hero_content='<p>Mobile-optimized healthcare platform</p>'
        )
        self.root_page.add_child(instance=self.home_page)
        
        # Create test images
        self.test_image = Image.objects.create(
            title='Mobile Test Image',
            file=get_test_image_file()
        )
        
        # Create test medications
        self.medication = Medication.objects.create(
            name='Mobile Test Medication',
            strength='500mg',
            form='tablet'
        )
        
        # Create push subscription
        self.push_subscription = PushSubscription.objects.create(
            user=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/test-endpoint',
            p256dh='test-p256dh-key',
            auth='test-auth-key',
            is_active=True
        )
        
        # Clear cache before each test
        cache.clear()
        
    def simulate_mobile_request(self, path='/', user_agent=None):
        """Simulate a mobile request."""
        if user_agent is None:
            user_agent = (
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) '
                'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 '
                'Mobile/15E148 Safari/604.1'
            )
        
        return self.factory.get(path, HTTP_USER_AGENT=user_agent)
        
    def simulate_tablet_request(self, path='/', user_agent=None):
        """Simulate a tablet request."""
        if user_agent is None:
            user_agent = (
                'Mozilla/5.0 (iPad; CPU OS 14_7_1 like Mac OS X) '
                'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 '
                'Mobile/15E148 Safari/604.1'
            )
        
        return self.factory.get(path, HTTP_USER_AGENT=user_agent)
        
    def simulate_pwa_request(self, path='/', user_agent=None):
        """Simulate a PWA request."""
        if user_agent is None:
            user_agent = (
                'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) '
                'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 '
                'Mobile/15E148 Safari/604.1'
            )
        
        request = self.factory.get(path, HTTP_USER_AGENT=user_agent)
        request.META['HTTP_X_REQUESTED_WITH'] = 'PWA'
        return request


class MobileImageOptimizerTestCase(BaseMobileTestCase):
    """Test cases for MobileImageOptimizer."""
    
    def test_responsive_image_renditions(self):
        """Test responsive image rendition generation."""
        # Get responsive renditions
        renditions = MobileImageOptimizer.get_responsive_image_renditions(
            self.test_image
        )
        
        # Should generate renditions for all breakpoints
        expected_breakpoints = ['xs', 'sm', 'md', 'lg', 'xl']
        for breakpoint in expected_breakpoints:
            self.assertIn(breakpoint, renditions)
            self.assertIn('url', renditions[breakpoint])
            self.assertIn('width', renditions[breakpoint])
            self.assertIn('height', renditions[breakpoint])
            
    def test_custom_filter_specs(self):
        """Test responsive images with custom filter specs."""
        custom_specs = {
            'mobile': 'fill-400x300',
            'tablet': 'fill-800x600',
            'desktop': 'fill-1200x900'
        }
        
        renditions = MobileImageOptimizer.get_responsive_image_renditions(
            self.test_image,
            filter_specs=custom_specs
        )
        
        # Should use custom breakpoints
        self.assertIn('mobile', renditions)
        self.assertIn('tablet', renditions)
        self.assertIn('desktop', renditions)
        
    def test_picture_element_html_generation(self):
        """Test HTML5 picture element generation."""
        picture_html = MobileImageOptimizer.get_picture_element_html(
            self.test_image,
            css_class='responsive-image'
        )
        
        # Should generate proper picture element
        self.assertIn('<picture', picture_html)
        self.assertIn('<source', picture_html)
        self.assertIn('<img', picture_html)
        self.assertIn('responsive-image', picture_html)
        
    def test_srcset_generation(self):
        """Test srcset attribute generation."""
        srcset = MobileImageOptimizer.get_srcset(self.test_image)
        
        # Should generate srcset with multiple sizes
        self.assertIsInstance(srcset, str)
        self.assertIn('320w', srcset)
        self.assertIn('576w', srcset)
        self.assertIn('768w', srcset)
        
    def test_image_optimization_caching(self):
        """Test image optimization caching."""
        # First call should generate and cache
        renditions1 = MobileImageOptimizer.get_responsive_image_renditions(
            self.test_image
        )
        
        # Second call should use cache
        renditions2 = MobileImageOptimizer.get_responsive_image_renditions(
            self.test_image
        )
        
        # Results should be identical
        self.assertEqual(renditions1, renditions2)
        
    def test_webp_format_support(self):
        """Test WebP format support for modern browsers."""
        webp_renditions = MobileImageOptimizer.get_webp_renditions(
            self.test_image
        )
        
        # Should generate WebP renditions if supported
        if webp_renditions:
            for rendition in webp_renditions.values():
                self.assertIn('.webp', rendition['url'])


class PushSubscriptionTestCase(BaseMobileTestCase):
    """Test cases for PushSubscription model."""
    
    def test_push_subscription_creation(self):
        """Test creating push subscriptions."""
        self.assertEqual(self.push_subscription.user, self.user)
        self.assertEqual(
            self.push_subscription.endpoint,
            'https://fcm.googleapis.com/fcm/send/test-endpoint'
        )
        self.assertTrue(self.push_subscription.is_active)
        
    def test_push_subscription_to_dict(self):
        """Test push subscription dictionary conversion."""
        subscription_dict = self.push_subscription.to_dict()
        
        self.assertIn('endpoint', subscription_dict)
        self.assertIn('keys', subscription_dict)
        self.assertIn('p256dh', subscription_dict['keys'])
        self.assertIn('auth', subscription_dict['keys'])
        
    def test_push_subscription_uniqueness(self):
        """Test push subscription uniqueness constraint."""
        # Try to create duplicate subscription
        with self.assertRaises(Exception):
            PushSubscription.objects.create(
                user=self.user,
                endpoint='https://fcm.googleapis.com/fcm/send/test-endpoint',
                p256dh='different-key',
                auth='different-auth'
            )
            
    def test_multiple_subscriptions_per_user(self):
        """Test multiple subscriptions per user."""
        # Create second subscription with different endpoint
        second_subscription = PushSubscription.objects.create(
            user=self.user,
            endpoint='https://fcm.googleapis.com/fcm/send/second-endpoint',
            p256dh='second-p256dh-key',
            auth='second-auth-key'
        )
        
        # User should have multiple subscriptions
        user_subscriptions = PushSubscription.objects.filter(user=self.user)
        self.assertEqual(user_subscriptions.count(), 2)


class MedicationReminderTestCase(BaseMobileTestCase):
    """Test cases for MedicationReminder model."""
    
    def setUp(self):
        """Set up medication reminder test data."""
        super().setUp()
        
        self.reminder = MedicationReminder.objects.create(
            user=self.user,
            medication_name='Test Reminder Medication',
            reminder_type='medication',
            reminder_time=timezone.now() + timedelta(hours=1),
            message='Time to take your medication',
            is_recurring=True,
            recurrence_pattern='daily',
            status='pending'
        )
        
    def test_medication_reminder_creation(self):
        """Test creating medication reminders."""
        self.assertEqual(self.reminder.user, self.user)
        self.assertEqual(self.reminder.medication_name, 'Test Reminder Medication')
        self.assertEqual(self.reminder.reminder_type, 'medication')
        self.assertTrue(self.reminder.is_recurring)
        
    def test_reminder_scheduling(self):
        """Test reminder scheduling functionality."""
        # Check if reminder is scheduled
        self.assertEqual(self.reminder.status, 'pending')
        self.assertGreater(self.reminder.reminder_time, timezone.now())
        
    def test_reminder_recurrence_calculation(self):
        """Test reminder recurrence calculation."""
        next_reminder = self.reminder.calculate_next_reminder()
        
        # Should be 24 hours later for daily recurrence
        expected_time = self.reminder.reminder_time + timedelta(days=1)
        self.assertEqual(next_reminder.date(), expected_time.date())
        
    def test_reminder_acknowledgment(self):
        """Test reminder acknowledgment."""
        # Acknowledge reminder
        self.reminder.acknowledge()
        
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.status, 'acknowledged')
        self.assertIsNotNone(self.reminder.acknowledged_at)
        
    def test_reminder_snoozing(self):
        """Test reminder snoozing functionality."""
        snooze_minutes = 30
        
        # Snooze reminder
        self.reminder.snooze(snooze_minutes)
        
        self.reminder.refresh_from_db()
        self.assertEqual(self.reminder.status, 'snoozed')
        
        # Should reschedule for later
        expected_snooze_time = timezone.now() + timedelta(minutes=snooze_minutes)
        self.assertGreater(self.reminder.reminder_time, expected_snooze_time - timedelta(minutes=1))


class PWAManifestGeneratorTestCase(BaseMobileTestCase):
    """Test cases for PWA manifest generation."""
    
    def setUp(self):
        """Set up PWA manifest test data."""
        super().setUp()
        self.manifest_generator = PWAManifestGenerator()
        
    def test_manifest_generation(self):
        """Test PWA manifest generation."""
        manifest = self.manifest_generator.generate_manifest()
        
        # Check required manifest fields
        self.assertIn('name', manifest)
        self.assertIn('short_name', manifest)
        self.assertIn('start_url', manifest)
        self.assertIn('display', manifest)
        self.assertIn('background_color', manifest)
        self.assertIn('theme_color', manifest)
        self.assertIn('icons', manifest)
        
        # Check MedGuard-specific values
        self.assertIn('MedGuard', manifest['name'])
        self.assertEqual(manifest['display'], 'standalone')
        
    def test_manifest_icons(self):
        """Test PWA manifest icons."""
        manifest = self.manifest_generator.generate_manifest()
        icons = manifest['icons']
        
        # Should have multiple icon sizes
        self.assertGreater(len(icons), 0)
        
        # Check icon properties
        for icon in icons:
            self.assertIn('src', icon)
            self.assertIn('sizes', icon)
            self.assertIn('type', icon)
            
        # Should have common sizes
        sizes = [icon['sizes'] for icon in icons]
        self.assertIn('192x192', sizes)
        self.assertIn('512x512', sizes)
        
    def test_manifest_customization(self):
        """Test PWA manifest customization."""
        custom_config = {
            'name': 'Custom MedGuard PWA',
            'theme_color': '#ff0000',
            'background_color': '#00ff00'
        }
        
        manifest = self.manifest_generator.generate_manifest(custom_config)
        
        self.assertEqual(manifest['name'], 'Custom MedGuard PWA')
        self.assertEqual(manifest['theme_color'], '#ff0000')
        self.assertEqual(manifest['background_color'], '#00ff00')
        
    def test_manifest_caching(self):
        """Test PWA manifest caching."""
        # Generate manifest twice
        manifest1 = self.manifest_generator.generate_manifest()
        manifest2 = self.manifest_generator.generate_manifest()
        
        # Should be identical (cached)
        self.assertEqual(manifest1, manifest2)


class ServiceWorkerManagerTestCase(BaseMobileTestCase):
    """Test cases for Service Worker management."""
    
    def setUp(self):
        """Set up service worker test data."""
        super().setUp()
        self.sw_manager = ServiceWorkerManager()
        
    def test_service_worker_generation(self):
        """Test service worker JavaScript generation."""
        sw_content = self.sw_manager.generate_service_worker()
        
        # Should contain service worker code
        self.assertIn('self.addEventListener', sw_content)
        self.assertIn('install', sw_content)
        self.assertIn('fetch', sw_content)
        self.assertIn('activate', sw_content)
        
    def test_cache_strategy_configuration(self):
        """Test cache strategy configuration."""
        cache_config = {
            'static_files': 'cache_first',
            'api_requests': 'network_first',
            'images': 'cache_first_fallback'
        }
        
        sw_content = self.sw_manager.generate_service_worker(cache_config)
        
        # Should include cache strategies
        self.assertIn('cache_first', sw_content)
        self.assertIn('network_first', sw_content)
        
    def test_offline_page_configuration(self):
        """Test offline page configuration."""
        offline_config = {
            'offline_page': '/offline/',
            'offline_image': '/static/images/offline.png'
        }
        
        sw_content = self.sw_manager.generate_service_worker(
            offline_config=offline_config
        )
        
        # Should include offline fallbacks
        self.assertIn('/offline/', sw_content)
        self.assertIn('offline.png', sw_content)
        
    def test_service_worker_versioning(self):
        """Test service worker versioning."""
        version1 = self.sw_manager.get_service_worker_version()
        
        # Update configuration
        self.sw_manager.update_cache_list(['new-file.js'])
        
        version2 = self.sw_manager.get_service_worker_version()
        
        # Version should change
        self.assertNotEqual(version1, version2)


class OfflineCacheManagerTestCase(BaseMobileTestCase):
    """Test cases for offline cache management."""
    
    def setUp(self):
        """Set up offline cache test data."""
        super().setUp()
        self.cache_manager = OfflineCacheManager()
        
    def test_cache_resource_registration(self):
        """Test registering resources for offline caching."""
        resources = [
            '/static/css/main.css',
            '/static/js/app.js',
            '/api/medications/',
            '/offline/'
        ]
        
        for resource in resources:
            self.cache_manager.register_cache_resource(resource)
        
        cached_resources = self.cache_manager.get_cached_resources()
        
        for resource in resources:
            self.assertIn(resource, cached_resources)
            
    def test_cache_strategy_assignment(self):
        """Test assigning cache strategies to resources."""
        # Assign different strategies
        self.cache_manager.set_cache_strategy('/static/', 'cache_first')
        self.cache_manager.set_cache_strategy('/api/', 'network_first')
        self.cache_manager.set_cache_strategy('/images/', 'stale_while_revalidate')
        
        # Check strategy assignment
        static_strategy = self.cache_manager.get_cache_strategy('/static/css/main.css')
        api_strategy = self.cache_manager.get_cache_strategy('/api/medications/')
        image_strategy = self.cache_manager.get_cache_strategy('/images/logo.png')
        
        self.assertEqual(static_strategy, 'cache_first')
        self.assertEqual(api_strategy, 'network_first')
        self.assertEqual(image_strategy, 'stale_while_revalidate')
        
    def test_cache_size_management(self):
        """Test cache size management."""
        # Set cache size limit
        self.cache_manager.set_cache_size_limit('images', 50)  # 50MB
        
        # Check limit
        limit = self.cache_manager.get_cache_size_limit('images')
        self.assertEqual(limit, 50)
        
        # Test cache cleanup
        cleanup_result = self.cache_manager.cleanup_cache('images')
        self.assertIsInstance(cleanup_result, dict)


class MobileSearchOptimizerTestCase(BaseMobileTestCase):
    """Test cases for mobile search optimization."""
    
    def setUp(self):
        """Set up mobile search test data."""
        super().setUp()
        self.search_optimizer = MobileSearchOptimizer()
        
    def test_mobile_search_interface(self):
        """Test mobile-optimized search interface."""
        request = self.simulate_mobile_request('/search/')
        
        search_interface = self.search_optimizer.get_mobile_search_interface(request)
        
        # Should have mobile-optimized elements
        self.assertIn('mobile-search', search_interface)
        self.assertIn('touch-friendly', search_interface)
        
    def test_search_autocomplete_mobile(self):
        """Test mobile search autocomplete."""
        request = self.simulate_mobile_request()
        
        suggestions = self.search_optimizer.get_mobile_autocomplete(
            query='med',
            request=request
        )
        
        # Should return mobile-optimized suggestions
        self.assertIsInstance(suggestions, list)
        
        if suggestions:
            for suggestion in suggestions:
                self.assertIn('text', suggestion)
                self.assertIn('mobile_optimized', suggestion)
                
    def test_voice_search_support(self):
        """Test voice search support."""
        voice_config = self.search_optimizer.get_voice_search_config()
        
        # Should have voice search configuration
        self.assertIn('enabled', voice_config)
        self.assertIn('language', voice_config)
        self.assertIn('continuous', voice_config)
        
    def test_search_results_mobile_formatting(self):
        """Test mobile search results formatting."""
        request = self.simulate_mobile_request()
        
        # Mock search results
        mock_results = [
            {'title': 'Aspirin', 'type': 'medication'},
            {'title': 'Ibuprofen', 'type': 'medication'}
        ]
        
        formatted_results = self.search_optimizer.format_mobile_results(
            mock_results,
            request
        )
        
        # Should format for mobile display
        self.assertIsInstance(formatted_results, list)
        
        for result in formatted_results:
            self.assertIn('mobile_formatted', result)
            self.assertIn('touch_target', result)


class TouchAdminInterfaceTestCase(BaseMobileTestCase):
    """Test cases for touch-optimized admin interface."""
    
    def setUp(self):
        """Set up touch admin test data."""
        super().setUp()
        self.touch_admin = TouchAdminInterface()
        
    def test_touch_admin_detection(self):
        """Test touch device detection."""
        # Mobile request
        mobile_request = self.simulate_mobile_request('/admin/')
        is_touch_mobile = self.touch_admin.is_touch_device(mobile_request)
        self.assertTrue(is_touch_mobile)
        
        # Tablet request
        tablet_request = self.simulate_tablet_request('/admin/')
        is_touch_tablet = self.touch_admin.is_touch_device(tablet_request)
        self.assertTrue(is_touch_tablet)
        
        # Desktop request
        desktop_request = self.factory.get('/admin/')
        is_touch_desktop = self.touch_admin.is_touch_device(desktop_request)
        self.assertFalse(is_touch_desktop)
        
    def test_touch_optimized_controls(self):
        """Test touch-optimized control generation."""
        request = self.simulate_mobile_request('/admin/')
        
        controls = self.touch_admin.get_touch_controls(request)
        
        # Should have touch-optimized elements
        self.assertIn('touch-button', controls)
        self.assertIn('min-height', controls)  # Minimum touch target size
        
    def test_mobile_admin_navigation(self):
        """Test mobile admin navigation."""
        request = self.simulate_mobile_request('/admin/')
        
        navigation = self.touch_admin.get_mobile_navigation(request)
        
        # Should have mobile navigation elements
        self.assertIn('mobile-nav', navigation)
        self.assertIn('hamburger-menu', navigation)
        
    def test_admin_responsive_tables(self):
        """Test responsive table handling in admin."""
        request = self.simulate_mobile_request('/admin/pages/')
        
        table_config = self.touch_admin.get_responsive_table_config(request)
        
        # Should have responsive table configuration
        self.assertIn('horizontal_scroll', table_config)
        self.assertIn('column_priority', table_config)


class MobileStreamFieldBlocksTestCase(BaseMobileTestCase):
    """Test cases for mobile-optimized StreamField blocks."""
    
    def test_mobile_medication_block(self):
        """Test mobile medication block."""
        mobile_block = MobileMedicationBlock()
        
        test_data = {
            'medication_name': 'Mobile Test Med',
            'dosage': '500mg',
            'instructions': 'Take with food',
            'mobile_optimized': True
        }
        
        # Test block validation
        try:
            cleaned_data = mobile_block.clean(test_data)
            self.assertEqual(cleaned_data['medication_name'], 'Mobile Test Med')
            self.assertTrue(cleaned_data['mobile_optimized'])
        except Exception as e:
            self.fail(f"Mobile medication block validation failed: {e}")
            
    def test_touch_optimized_form_block(self):
        """Test touch-optimized form block."""
        touch_form_block = TouchOptimizedFormBlock()
        
        form_data = {
            'form_title': 'Touch Form',
            'fields': [
                {'type': 'text', 'label': 'Name', 'touch_optimized': True},
                {'type': 'email', 'label': 'Email', 'touch_optimized': True}
            ],
            'submit_button_size': 'large'
        }
        
        # Test form rendering
        try:
            rendered = touch_form_block.render(form_data)
            self.assertIn('touch-optimized', rendered)
            self.assertIn('large-button', rendered)
        except Exception as e:
            self.fail(f"Touch form block rendering failed: {e}")
            
    def test_responsive_image_block(self):
        """Test responsive image block."""
        responsive_block = ResponsiveImageBlock()
        
        image_data = {
            'image': self.test_image,
            'mobile_breakpoints': True,
            'lazy_loading': True,
            'webp_support': True
        }
        
        # Test image block rendering
        try:
            rendered = responsive_block.render(image_data)
            self.assertIn('loading="lazy"', rendered)
            self.assertIn('srcset', rendered)
        except Exception as e:
            self.fail(f"Responsive image block rendering failed: {e}")


class ProgressiveLoadingManagerTestCase(BaseMobileTestCase):
    """Test cases for progressive loading management."""
    
    def setUp(self):
        """Set up progressive loading test data."""
        super().setUp()
        self.loading_manager = ProgressiveLoadingManager()
        
    def test_critical_css_identification(self):
        """Test critical CSS identification."""
        request = self.simulate_mobile_request('/')
        
        critical_css = self.loading_manager.get_critical_css(request)
        
        # Should identify critical CSS
        self.assertIsInstance(critical_css, str)
        self.assertGreater(len(critical_css), 0)
        
    def test_lazy_loading_configuration(self):
        """Test lazy loading configuration."""
        lazy_config = self.loading_manager.get_lazy_loading_config()
        
        # Should have lazy loading settings
        self.assertIn('images', lazy_config)
        self.assertIn('iframes', lazy_config)
        self.assertIn('intersection_observer', lazy_config)
        
    def test_resource_prioritization(self):
        """Test resource loading prioritization."""
        resources = [
            {'url': '/static/css/critical.css', 'type': 'css'},
            {'url': '/static/js/app.js', 'type': 'js'},
            {'url': '/static/images/hero.jpg', 'type': 'image'}
        ]
        
        prioritized = self.loading_manager.prioritize_resources(resources)
        
        # CSS should be prioritized
        self.assertEqual(prioritized[0]['type'], 'css')
        
    def test_progressive_enhancement(self):
        """Test progressive enhancement features."""
        request = self.simulate_mobile_request('/')
        
        enhancement_config = self.loading_manager.get_progressive_enhancement(request)
        
        # Should have enhancement configuration
        self.assertIn('base_experience', enhancement_config)
        self.assertIn('enhanced_features', enhancement_config)


class MobileAnalyticsTestCase(BaseMobileTestCase):
    """Test cases for mobile analytics."""
    
    def setUp(self):
        """Set up mobile analytics test data."""
        super().setUp()
        self.analytics = MobileAnalytics()
        
    def test_mobile_event_tracking(self):
        """Test mobile event tracking."""
        request = self.simulate_mobile_request('/')
        
        # Track mobile event
        event_data = {
            'event_type': 'page_view',
            'page_url': '/',
            'device_type': 'mobile',
            'user_agent': request.META.get('HTTP_USER_AGENT')
        }
        
        result = self.analytics.track_mobile_event(event_data, request)
        
        self.assertTrue(result)
        
    def test_pwa_usage_tracking(self):
        """Test PWA usage tracking."""
        pwa_request = self.simulate_pwa_request('/')
        
        # Track PWA usage
        pwa_data = {
            'event_type': 'pwa_usage',
            'standalone_mode': True,
            'installation_prompt': False
        }
        
        result = self.analytics.track_pwa_usage(pwa_data, pwa_request)
        
        self.assertTrue(result)
        
    def test_performance_metrics_collection(self):
        """Test mobile performance metrics collection."""
        request = self.simulate_mobile_request('/')
        
        # Collect performance metrics
        metrics = self.analytics.collect_performance_metrics(request)
        
        # Should have performance data
        self.assertIn('device_type', metrics)
        self.assertIn('connection_type', metrics)
        self.assertIn('viewport_size', metrics)
        
    def test_offline_usage_tracking(self):
        """Test offline usage tracking."""
        offline_data = {
            'offline_duration': 300,  # 5 minutes
            'cached_pages_accessed': 3,
            'sync_events': 2
        }
        
        result = self.analytics.track_offline_usage(offline_data)
        
        self.assertTrue(result)


class PWAInstallPromptTestCase(BaseMobileTestCase):
    """Test cases for PWA installation prompt."""
    
    def setUp(self):
        """Set up PWA install prompt test data."""
        super().setUp()
        self.install_prompt = PWAInstallPrompt()
        
    def test_install_criteria_checking(self):
        """Test PWA install criteria checking."""
        request = self.simulate_mobile_request('/')
        
        # Check install criteria
        can_install = self.install_prompt.can_show_install_prompt(request)
        
        # Should check various criteria
        self.assertIsInstance(can_install, bool)
        
    def test_install_prompt_configuration(self):
        """Test install prompt configuration."""
        prompt_config = self.install_prompt.get_prompt_config()
        
        # Should have prompt configuration
        self.assertIn('trigger_events', prompt_config)
        self.assertIn('delay_seconds', prompt_config)
        self.assertIn('max_dismissals', prompt_config)
        
    def test_install_prompt_customization(self):
        """Test install prompt customization."""
        custom_config = {
            'title': 'Install MedGuard PWA',
            'message': 'Get quick access to your medications',
            'icon': '/static/images/pwa-icon.png'
        }
        
        prompt_html = self.install_prompt.generate_prompt_html(custom_config)
        
        # Should contain custom content
        self.assertIn('Install MedGuard PWA', prompt_html)
        self.assertIn('quick access', prompt_html)
        
    def test_install_event_tracking(self):
        """Test PWA install event tracking."""
        install_data = {
            'prompt_shown': True,
            'user_action': 'accepted',
            'install_source': 'banner'
        }
        
        result = self.install_prompt.track_install_event(install_data)
        
        self.assertTrue(result)


class MobilePerformanceTestCase(BaseMobileTestCase):
    """Test cases for mobile performance optimization."""
    
    def test_mobile_page_load_performance(self):
        """Test mobile page load performance."""
        import time
        
        # Test mobile page load time
        start_time = time.time()
        response = self.client.get(self.home_page.url, HTTP_USER_AGENT=(
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 '
            'Mobile/15E148 Safari/604.1'
        ))
        load_time = time.time() - start_time
        
        # Should load quickly on mobile
        self.assertEqual(response.status_code, 200)
        self.assertLess(load_time, 2.0)  # Under 2 seconds
        
    def test_image_optimization_performance(self):
        """Test image optimization performance."""
        import time
        
        # Test responsive image generation time
        start_time = time.time()
        renditions = MobileImageOptimizer.get_responsive_image_renditions(
            self.test_image
        )
        generation_time = time.time() - start_time
        
        # Should generate quickly
        self.assertLess(generation_time, 1.0)  # Under 1 second
        self.assertGreater(len(renditions), 0)
        
    def test_service_worker_caching_performance(self):
        """Test service worker caching performance."""
        # Test cached resource access
        cached_resources = [
            '/static/css/main.css',
            '/static/js/app.js',
            '/'
        ]
        
        cache_manager = OfflineCacheManager()
        
        for resource in cached_resources:
            cache_manager.register_cache_resource(resource)
        
        # Should cache resources efficiently
        cached_count = len(cache_manager.get_cached_resources())
        self.assertEqual(cached_count, len(cached_resources))


@pytest.mark.django_db
class MobileIntegrationTestCase(TestCase):
    """Integration tests for mobile features."""
    
    def setUp(self):
        """Set up mobile integration test data."""
        self.user = User.objects.create_user(
            username='mobile_integration',
            email='mobile@medguard.co.za',
            password='mobilepass123'
        )
        
        self.client = Client()
        
    def test_mobile_admin_integration(self):
        """Test mobile admin integration."""
        # Login as admin
        admin_user = User.objects.create_user(
            username='mobile_admin',
            email='mobileadmin@medguard.co.za',
            password='adminpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.client.force_login(admin_user)
        
        # Test mobile admin access
        response = self.client.get('/admin/', HTTP_USER_AGENT=(
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 '
            'Mobile/15E148 Safari/604.1'
        ))
        
        # Should work on mobile
        self.assertEqual(response.status_code, 200)
        
    def test_pwa_manifest_integration(self):
        """Test PWA manifest integration."""
        # Test manifest endpoint
        response = self.client.get('/manifest.json')
        
        # Should return valid manifest
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Should be valid JSON
        try:
            manifest_data = response.json()
            self.assertIn('name', manifest_data)
            self.assertIn('start_url', manifest_data)
        except ValueError:
            self.fail("Manifest should be valid JSON")
            
    def test_service_worker_integration(self):
        """Test service worker integration."""
        # Test service worker endpoint
        response = self.client.get('/sw.js')
        
        # Should return service worker
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/javascript')
        
        # Should contain service worker code
        content = response.content.decode('utf-8')
        self.assertIn('addEventListener', content)
        self.assertIn('install', content)
        
    def test_push_notification_integration(self):
        """Test push notification integration."""
        # Test push subscription endpoint
        subscription_data = {
            'endpoint': 'https://fcm.googleapis.com/fcm/send/test',
            'keys': {
                'p256dh': 'test-key',
                'auth': 'test-auth'
            }
        }
        
        self.client.force_login(self.user)
        response = self.client.post(
            '/api/push/subscribe/',
            data=json.dumps(subscription_data),
            content_type='application/json'
        )
        
        # Should create subscription
        self.assertEqual(response.status_code, 201)
        
        # Verify subscription was created
        subscription = PushSubscription.objects.filter(user=self.user).first()
        self.assertIsNotNone(subscription)
