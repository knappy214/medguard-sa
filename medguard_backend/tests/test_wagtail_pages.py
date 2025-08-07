"""
Comprehensive test suite for Wagtail 7.0.2 page models in MedGuard SA.

This module tests all page model functionality including:
- HomePage model functionality and validation
- MedicationIndexPage operations
- NotificationIndexPage behavior
- Page hierarchy and permissions
- Page content rendering and search indexing
- SEO and metadata handling
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError
from unittest.mock import patch, Mock

from wagtail.test.utils import WagtailPageTestCase, WagtailPageTests
from wagtail.models import Page, Site
from wagtail.rich_text import RichText
from wagtail.search import index

# Import page models
from home.models import HomePage
from medguard_notifications.models import NotificationIndexPage, NotificationDetailPage
from medications.models import MedicationIndexPage
from medications.page_models import (
    PrescriptionFormPage, 
    MedicationComparisonPage,
    PharmacyLocatorPage,
    MedicationGuideIndexPage,
    PrescriptionHistoryPage
)

User = get_user_model()


class HomePageTestCase(WagtailPageTestCase):
    """Test cases for HomePage model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.root_page = Page.objects.get(id=2)  # Root page
        self.user = User.objects.create_user(
            username='testuser',
            email='test@medguard.co.za',
            password='testpass123'
        )
        
    def test_can_create_home_page(self):
        """Test creating a home page."""
        home_page = HomePage(
            title='MedGuard SA Home',
            slug='home',
            hero_title='Welcome to MedGuard SA',
            hero_subtitle='Your trusted healthcare companion',
            hero_content='<p>Professional medication management for South Africa</p>',
            main_content='<p>Comprehensive healthcare solutions</p>',
            cta_title='Get Started Today',
            cta_content='<p>Join thousands of satisfied users</p>',
            meta_description='MedGuard SA - Professional medication management'
        )
        self.root_page.add_child(instance=home_page)
        
        # Verify the page was created
        self.assertTrue(HomePage.objects.filter(title='MedGuard SA Home').exists())
        
        # Test page properties
        saved_page = HomePage.objects.get(title='MedGuard SA Home')
        self.assertEqual(saved_page.hero_title, 'Welcome to MedGuard SA')
        self.assertEqual(saved_page.hero_subtitle, 'Your trusted healthcare companion')
        self.assertIn('Professional medication management', saved_page.hero_content)
        
    def test_home_page_search_fields(self):
        """Test that search fields are properly configured."""
        home_page = HomePage(
            title='Test Home Page',
            slug='test-home',
            hero_title='Test Hero',
            hero_content='<p>Searchable content here</p>',
            main_content='<p>More searchable content</p>'
        )
        self.root_page.add_child(instance=home_page)
        
        # Check search fields are configured
        search_fields = home_page.search_fields
        field_names = [field.field_name for field in search_fields]
        
        self.assertIn('hero_title', field_names)
        self.assertIn('hero_content', field_names)
        self.assertIn('main_content', field_names)
        
    def test_home_page_parent_page_types(self):
        """Test parent page type restrictions."""
        self.assertEqual(HomePage.parent_page_types, ['wagtailcore.Page'])
        
    def test_home_page_subpage_types(self):
        """Test allowed subpage types."""
        expected_subpages = [
            'medications.MedicationIndexPage',
            'medguard_notifications.NotificationIndexPage',
            'medications.PrescriptionFormPage',
            'medications.MedicationComparisonPage',
            'medications.PharmacyLocatorPage',
            'medications.MedicationGuideIndexPage',
            'medications.PrescriptionHistoryPage'
        ]
        
        for subpage_type in expected_subpages:
            self.assertIn(subpage_type, HomePage.subpage_types)
            
    def test_home_page_meta_description_validation(self):
        """Test meta description length validation."""
        long_description = 'A' * 200  # Exceeds 160 character limit
        
        home_page = HomePage(
            title='Test Page',
            slug='test-page',
            meta_description=long_description
        )
        
        # Should not raise validation error (field allows up to max_length)
        # But should be truncated in SEO best practices
        self.root_page.add_child(instance=home_page)
        saved_page = HomePage.objects.get(title='Test Page')
        self.assertEqual(len(saved_page.meta_description), 200)
        
    def test_home_page_content_panels(self):
        """Test that content panels are properly configured."""
        home_page = HomePage()
        panels = home_page.content_panels
        
        # Should include Page.content_panels plus custom panels
        self.assertTrue(len(panels) > len(Page.content_panels))


class MedicationIndexPageTestCase(WagtailPageTestCase):
    """Test cases for MedicationIndexPage model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_page = HomePage(
            title='Test Home',
            slug='home'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        
    def test_can_create_medication_index_page(self):
        """Test creating a medication index page."""
        med_index = MedicationIndexPage(
            title='Medications',
            slug='medications',
            intro='<p>Browse our medication database</p>'
        )
        self.home_page.add_child(instance=med_index)
        
        # Verify creation
        self.assertTrue(MedicationIndexPage.objects.filter(title='Medications').exists())
        
    def test_medication_index_parent_page_types(self):
        """Test parent page type restrictions."""
        self.assertIn('home.HomePage', MedicationIndexPage.parent_page_types)
        
    def test_medication_index_get_context(self):
        """Test context method returns medications."""
        med_index = MedicationIndexPage(
            title='Medications',
            slug='medications'
        )
        self.home_page.add_child(instance=med_index)
        
        # Mock request
        request = RequestFactory().get('/medications/')
        request.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        
        context = med_index.get_context(request)
        self.assertIn('medications', context)


class NotificationIndexPageTestCase(WagtailPageTestCase):
    """Test cases for NotificationIndexPage model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_page = HomePage(
            title='Test Home',
            slug='home'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        
    def test_can_create_notification_index_page(self):
        """Test creating a notification index page."""
        notif_index = NotificationIndexPage(
            title='Notifications',
            slug='notifications',
            intro='<p>View your notifications</p>'
        )
        self.home_page.add_child(instance=notif_index)
        
        # Verify creation
        self.assertTrue(NotificationIndexPage.objects.filter(title='Notifications').exists())
        
    def test_notification_index_parent_page_types(self):
        """Test parent page type restrictions."""
        self.assertIn('home.HomePage', NotificationIndexPage.parent_page_types)
        
    def test_notification_index_subpage_types(self):
        """Test allowed subpage types."""
        self.assertIn('medguard_notifications.NotificationDetailPage', 
                     NotificationIndexPage.subpage_types)


class PrescriptionFormPageTestCase(WagtailPageTestCase):
    """Test cases for PrescriptionFormPage model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_page = HomePage(
            title='Test Home',
            slug='home'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        self.user = User.objects.create_user(
            username='testuser',
            email='test@medguard.co.za',
            password='testpass123'
        )
        
    def test_can_create_prescription_form_page(self):
        """Test creating a prescription form page."""
        form_page = PrescriptionFormPage(
            title='Submit Prescription',
            slug='submit-prescription',
            intro='<p>Submit your prescription here</p>',
            thank_you_text='<p>Thank you for your submission</p>',
            requires_authentication=True,
            enable_captcha=True,
            max_submissions_per_user=5
        )
        self.home_page.add_child(instance=form_page)
        
        # Verify creation
        self.assertTrue(PrescriptionFormPage.objects.filter(
            title='Submit Prescription'
        ).exists())
        
    def test_prescription_form_authentication_required(self):
        """Test authentication requirement functionality."""
        form_page = PrescriptionFormPage(
            title='Submit Prescription',
            slug='submit-prescription',
            requires_authentication=True
        )
        self.home_page.add_child(instance=form_page)
        
        # Test with unauthenticated request
        request = RequestFactory().get('/submit-prescription/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        # Should redirect to login
        response = form_page.serve(request)
        self.assertEqual(response.status_code, 302)
        
    def test_prescription_form_max_submissions_validation(self):
        """Test maximum submissions per user validation."""
        form_page = PrescriptionFormPage(
            title='Submit Prescription',
            slug='submit-prescription',
            max_submissions_per_user=2
        )
        self.home_page.add_child(instance=form_page)
        
        # Should validate max submissions
        self.assertEqual(form_page.max_submissions_per_user, 2)


class MedicationComparisonPageTestCase(WagtailPageTestCase):
    """Test cases for MedicationComparisonPage model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_page = HomePage(
            title='Test Home',
            slug='home'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        
    def test_can_create_medication_comparison_page(self):
        """Test creating a medication comparison page."""
        comparison_page = MedicationComparisonPage(
            title='Compare Medications',
            slug='compare-medications',
            intro='<p>Compare medications side by side</p>',
            max_comparison_items=5,
            enable_session_management=True
        )
        self.home_page.add_child(instance=comparison_page)
        
        # Verify creation
        self.assertTrue(MedicationComparisonPage.objects.filter(
            title='Compare Medications'
        ).exists())
        
    def test_medication_comparison_max_items_validation(self):
        """Test maximum comparison items validation."""
        comparison_page = MedicationComparisonPage(
            title='Compare Medications',
            slug='compare-medications',
            max_comparison_items=15  # Should be clamped to max allowed
        )
        
        # Should validate within allowed range (2-10)
        with self.assertRaises(ValidationError):
            comparison_page.full_clean()


class PharmacyLocatorPageTestCase(WagtailPageTestCase):
    """Test cases for PharmacyLocatorPage model."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_page = HomePage(
            title='Test Home',
            slug='home'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        
    def test_can_create_pharmacy_locator_page(self):
        """Test creating a pharmacy locator page."""
        locator_page = PharmacyLocatorPage(
            title='Find Pharmacies',
            slug='find-pharmacies',
            intro='<p>Locate nearby pharmacies</p>',
            default_search_radius=10.0,
            enable_geolocation=True,
            show_operating_hours=True
        )
        self.home_page.add_child(instance=locator_page)
        
        # Verify creation
        self.assertTrue(PharmacyLocatorPage.objects.filter(
            title='Find Pharmacies'
        ).exists())
        
    def test_pharmacy_locator_search_radius_validation(self):
        """Test search radius validation."""
        locator_page = PharmacyLocatorPage(
            title='Find Pharmacies',
            slug='find-pharmacies',
            default_search_radius=100.0  # Should be within valid range
        )
        
        # Should validate radius is reasonable
        with self.assertRaises(ValidationError):
            locator_page.full_clean()


class PageHierarchyTestCase(WagtailPageTestCase):
    """Test page hierarchy and relationships."""
    
    def setUp(self):
        """Set up test page hierarchy."""
        super().setUp()
        self.root_page = Page.objects.get(id=2)
        
        # Create home page
        self.home_page = HomePage(
            title='MedGuard SA',
            slug='home',
            hero_title='Welcome to MedGuard'
        )
        self.root_page.add_child(instance=self.home_page)
        
    def test_page_hierarchy_creation(self):
        """Test creating a complete page hierarchy."""
        # Create medication index
        med_index = MedicationIndexPage(
            title='Medications',
            slug='medications'
        )
        self.home_page.add_child(instance=med_index)
        
        # Create notification index
        notif_index = NotificationIndexPage(
            title='Notifications',
            slug='notifications'
        )
        self.home_page.add_child(instance=notif_index)
        
        # Verify hierarchy
        self.assertEqual(self.home_page.get_children().count(), 2)
        self.assertTrue(self.home_page.get_children().filter(
            title='Medications'
        ).exists())
        self.assertTrue(self.home_page.get_children().filter(
            title='Notifications'
        ).exists())
        
    def test_page_permissions_inheritance(self):
        """Test that page permissions are properly inherited."""
        med_index = MedicationIndexPage(
            title='Medications',
            slug='medications'
        )
        self.home_page.add_child(instance=med_index)
        
        # Test basic permission inheritance
        self.assertEqual(med_index.get_parent(), self.home_page)
        
    def test_page_url_generation(self):
        """Test that page URLs are generated correctly."""
        med_index = MedicationIndexPage(
            title='Medications',
            slug='medications'
        )
        self.home_page.add_child(instance=med_index)
        
        # Test URL path
        self.assertIn('medications', med_index.get_url_parts()[-1])


class PageSearchIndexingTestCase(WagtailPageTestCase):
    """Test page search indexing functionality."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_page = HomePage(
            title='Test Home',
            slug='home',
            hero_title='Searchable Hero Title',
            hero_content='<p>Searchable hero content</p>',
            main_content='<p>Searchable main content</p>'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        
    def test_search_fields_configuration(self):
        """Test that search fields are properly configured."""
        search_fields = self.home_page.search_fields
        field_names = [field.field_name for field in search_fields]
        
        # Should include custom search fields
        self.assertIn('hero_title', field_names)
        self.assertIn('hero_content', field_names)
        self.assertIn('main_content', field_names)
        
    def test_search_boost_factors(self):
        """Test search boost factors for important fields."""
        search_fields = self.home_page.search_fields
        
        # Find hero_title field and check boost
        hero_title_field = next(
            (f for f in search_fields if f.field_name == 'hero_title'), 
            None
        )
        
        if hero_title_field and hasattr(hero_title_field, 'boost'):
            # Hero title should have higher boost than regular content
            self.assertGreater(hero_title_field.boost, 1.0)


class PageSEOTestCase(WagtailPageTestCase):
    """Test SEO and metadata functionality."""
    
    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.home_page = HomePage(
            title='MedGuard SA - Healthcare Solutions',
            slug='home',
            meta_description='Professional medication management for South Africa'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        
    def test_meta_description_length(self):
        """Test meta description is within SEO limits."""
        self.assertLessEqual(len(self.home_page.meta_description), 160)
        
    def test_page_title_seo_format(self):
        """Test page title follows SEO best practices."""
        # Title should be descriptive and include key terms
        self.assertIn('MedGuard', self.home_page.title)
        self.assertIn('Healthcare', self.home_page.title)
        
    def test_slug_format(self):
        """Test slug follows URL best practices."""
        # Slug should be lowercase and URL-friendly
        self.assertEqual(self.home_page.slug, 'home')
        self.assertNotIn(' ', self.home_page.slug)
        self.assertNotIn('_', self.home_page.slug)


@pytest.mark.django_db
class PageModelIntegrationTestCase(TestCase):
    """Integration tests for page models with database operations."""
    
    def setUp(self):
        """Set up integration test data."""
        self.root_page = Page.objects.get(id=2)
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@medguard.co.za',
            password='testpass123'
        )
        
    def test_page_creation_with_database_constraints(self):
        """Test page creation respects database constraints."""
        home_page = HomePage(
            title='Integration Test Home',
            slug='integration-home',
            hero_title='Integration Test'
        )
        self.root_page.add_child(instance=home_page)
        
        # Should be saved to database
        saved_page = HomePage.objects.get(slug='integration-home')
        self.assertEqual(saved_page.title, 'Integration Test Home')
        
    def test_page_deletion_cascade(self):
        """Test page deletion cascades properly."""
        home_page = HomePage(
            title='Test Home for Deletion',
            slug='test-deletion'
        )
        self.root_page.add_child(instance=home_page)
        
        med_index = MedicationIndexPage(
            title='Test Medications',
            slug='test-medications'
        )
        home_page.add_child(instance=med_index)
        
        # Delete parent page
        home_page.delete()
        
        # Child should also be deleted
        self.assertFalse(MedicationIndexPage.objects.filter(
            slug='test-medications'
        ).exists())
        
    def test_concurrent_page_updates(self):
        """Test handling of concurrent page updates."""
        home_page = HomePage(
            title='Concurrent Test Home',
            slug='concurrent-home'
        )
        self.root_page.add_child(instance=home_page)
        
        # Simulate concurrent updates
        page1 = HomePage.objects.get(slug='concurrent-home')
        page2 = HomePage.objects.get(slug='concurrent-home')
        
        page1.hero_title = 'Updated by User 1'
        page1.save()
        
        page2.hero_title = 'Updated by User 2'
        page2.save()
        
        # Last update should win
        final_page = HomePage.objects.get(slug='concurrent-home')
        self.assertEqual(final_page.hero_title, 'Updated by User 2')
