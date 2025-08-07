"""
Comprehensive test suite for Wagtail 7.0.2 search functionality in MedGuard SA.

This module tests all search functionality including:
- EnhancedSearchIndex medication indexing and search
- MedicationSearchPromotion and search result promotion
- SearchResultTemplate and result rendering
- SearchSuggestion and autocomplete functionality
- SearchFacet and faceted search
- SearchFilter and advanced filtering
- SearchRanking and relevance scoring
- SearchAnalytics and search tracking
- MultilingualSearchIndex and i18n search
- SearchPerformanceOptimizer and query optimization
- Search caching and performance
- Full-text search integration
- Elasticsearch/database backend testing
"""

import pytest
from django.test import TestCase, TransactionTestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from wagtail.search import index
from wagtail.search.backends import get_search_backend
from wagtail.search.models import Query
from wagtail.contrib.search_promotions.models import SearchPromotion
from wagtail.test.utils import WagtailTestUtils

# Import search models
from search.models import (
    EnhancedSearchIndex,
    MedicationSearchPromotion,
    SearchResultTemplate,
    SearchSuggestion,
    SearchFacet,
    SearchFilter,
    SearchRanking,
    SearchAnalytics,
    SearchPerformance,
    MultilingualSearchIndex,
    SearchTranslation,
    SearchPagination,
    SearchResultCache,
    SearchPerformanceOptimizer,
    SearchHealthMonitor
)

# Import related models
from medications.models import Medication, MedicationIndexPage
from home.models import HomePage
from medguard_notifications.models import NotificationIndexPage

User = get_user_model()


class BaseSearchTestCase(TestCase):
    """Base test case for search testing with common setup."""
    
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
        
        # Create test medications
        self.aspirin = Medication.objects.create(
            name='Aspirin',
            generic_name='Acetylsalicylic acid',
            strength='325mg',
            form='tablet',
            manufacturer='Bayer',
            active_ingredients='Acetylsalicylic acid',
            side_effects='Stomach upset, bleeding',
            interactions='Warfarin, alcohol'
        )
        
        self.ibuprofen = Medication.objects.create(
            name='Ibuprofen',
            generic_name='Ibuprofen',
            strength='200mg',
            form='tablet',
            manufacturer='Advil',
            active_ingredients='Ibuprofen',
            side_effects='Stomach upset, dizziness',
            interactions='Aspirin, blood thinners'
        )
        
        self.paracetamol = Medication.objects.create(
            name='Paracetamol',
            generic_name='Acetaminophen',
            strength='500mg',
            form='tablet',
            manufacturer='Tylenol',
            active_ingredients='Acetaminophen',
            side_effects='Liver damage (overdose)',
            interactions='Alcohol, warfarin'
        )
        
        # Create test pages
        self.root_page = Page.objects.get(id=2)
        
        self.home_page = HomePage(
            title='MedGuard SA Home',
            slug='home',
            hero_title='Welcome to MedGuard SA',
            hero_content='<p>Your trusted healthcare companion</p>',
            main_content='<p>Professional medication management</p>'
        )
        self.root_page.add_child(instance=self.home_page)
        
        # Clear cache and search indexes before each test
        cache.clear()
        self.clear_search_indexes()
        
    def clear_search_indexes(self):
        """Clear search indexes for clean testing."""
        EnhancedSearchIndex.objects.all().delete()
        MultilingualSearchIndex.objects.all().delete()
        SearchResultCache.objects.all().delete()
        
    def get_search_backend(self):
        """Get the search backend for testing."""
        return get_search_backend()


class EnhancedSearchIndexTestCase(BaseSearchTestCase):
    """Test cases for EnhancedSearchIndex."""
    
    def test_medication_indexing(self):
        """Test medication indexing functionality."""
        # Index a medication
        EnhancedSearchIndex.index_medication(self.aspirin)
        
        # Check index entry was created
        index_entry = EnhancedSearchIndex.objects.get(
            content_type='medication',
            object_id=self.aspirin.id
        )
        
        self.assertEqual(index_entry.title, 'Aspirin')
        self.assertEqual(index_entry.medication_name, 'Aspirin')
        self.assertEqual(index_entry.generic_name, 'Acetylsalicylic acid')
        self.assertIn('Acetylsalicylic acid', index_entry.active_ingredients)
        
    def test_healthcare_relevance_calculation(self):
        """Test healthcare relevance scoring."""
        EnhancedSearchIndex.index_medication(self.aspirin)
        
        index_entry = EnhancedSearchIndex.objects.get(
            content_type='medication',
            object_id=self.aspirin.id
        )
        
        # Should have calculated healthcare relevance score
        self.assertGreater(index_entry.healthcare_relevance, 0)
        self.assertLessEqual(index_entry.healthcare_relevance, 10)
        
    def test_searchable_content_extraction(self):
        """Test searchable content extraction."""
        EnhancedSearchIndex.index_medication(self.aspirin)
        
        index_entry = EnhancedSearchIndex.objects.get(
            content_type='medication',
            object_id=self.aspirin.id
        )
        
        # Should contain relevant searchable content
        content = index_entry.content.lower()
        self.assertIn('aspirin', content)
        self.assertIn('acetylsalicylic', content)
        self.assertIn('325mg', content)
        self.assertIn('tablet', content)
        
    def test_multilingual_indexing(self):
        """Test multilingual indexing support."""
        # Index in English
        EnhancedSearchIndex.index_medication(self.aspirin)
        
        # Index in Afrikaans (simulated)
        afrikaans_entry = EnhancedSearchIndex.objects.create(
            title='Aspirien',  # Afrikaans translation
            content='Aspirien is 'n pynstiller',
            content_type='medication',
            object_id=self.aspirin.id,
            medication_name='Aspirien',
            language='af-ZA'
        )
        
        # Should have entries in both languages
        english_entries = EnhancedSearchIndex.objects.filter(language='en-ZA')
        afrikaans_entries = EnhancedSearchIndex.objects.filter(language='af-ZA')
        
        self.assertGreater(english_entries.count(), 0)
        self.assertGreater(afrikaans_entries.count(), 0)
        
    def test_search_field_configuration(self):
        """Test search field configuration and boosting."""
        search_fields = EnhancedSearchIndex.search_fields
        
        # Check that medication name has highest boost
        medication_name_field = next(
            (f for f in search_fields if f.field_name == 'medication_name'), 
            None
        )
        
        self.assertIsNotNone(medication_name_field)
        self.assertEqual(medication_name_field.boost, 4.0)
        
        # Check title boost
        title_field = next(
            (f for f in search_fields if f.field_name == 'title'), 
            None
        )
        
        self.assertIsNotNone(title_field)
        self.assertEqual(title_field.boost, 3.0)
        
    def test_index_update_on_medication_change(self):
        """Test index updates when medication changes."""
        # Initial indexing
        EnhancedSearchIndex.index_medication(self.aspirin)
        
        original_entry = EnhancedSearchIndex.objects.get(
            content_type='medication',
            object_id=self.aspirin.id
        )
        original_updated = original_entry.last_updated
        
        # Update medication
        self.aspirin.name = 'Aspirin Updated'
        self.aspirin.save()
        
        # Re-index
        EnhancedSearchIndex.index_medication(self.aspirin)
        
        updated_entry = EnhancedSearchIndex.objects.get(
            content_type='medication',
            object_id=self.aspirin.id
        )
        
        self.assertEqual(updated_entry.title, 'Aspirin Updated')
        self.assertGreater(updated_entry.last_updated, original_updated)


class MedicationSearchPromotionTestCase(BaseSearchTestCase):
    """Test cases for MedicationSearchPromotion."""
    
    def setUp(self):
        """Set up search promotion test data."""
        super().setUp()
        
        # Create search promotion
        self.promotion = MedicationSearchPromotion.objects.create(
            query_string='pain relief',
            promoted_medication=self.aspirin,
            promotion_type='featured_medication',
            priority=1,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            is_active=True
        )
        
    def test_search_promotion_creation(self):
        """Test creating search promotions."""
        self.assertEqual(self.promotion.query_string, 'pain relief')
        self.assertEqual(self.promotion.promoted_medication, self.aspirin)
        self.assertEqual(self.promotion.promotion_type, 'featured_medication')
        self.assertTrue(self.promotion.is_active)
        
    def test_promotion_matching(self):
        """Test promotion matching for search queries."""
        # Should match exact query
        matches = MedicationSearchPromotion.objects.filter(
            query_string__icontains='pain relief',
            is_active=True
        )
        
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches.first(), self.promotion)
        
    def test_promotion_priority_ordering(self):
        """Test promotion priority ordering."""
        # Create another promotion with higher priority
        high_priority_promotion = MedicationSearchPromotion.objects.create(
            query_string='pain relief',
            promoted_medication=self.ibuprofen,
            promotion_type='featured_medication',
            priority=0,  # Higher priority (lower number)
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=30),
            is_active=True
        )
        
        # Should order by priority
        promotions = MedicationSearchPromotion.objects.filter(
            query_string='pain relief',
            is_active=True
        ).order_by('priority')
        
        self.assertEqual(promotions.first(), high_priority_promotion)
        self.assertEqual(promotions.last(), self.promotion)
        
    def test_promotion_date_range_validation(self):
        """Test promotion date range validation."""
        # Test expired promotion
        expired_promotion = MedicationSearchPromotion.objects.create(
            query_string='expired',
            promoted_medication=self.aspirin,
            promotion_type='featured_medication',
            start_date=timezone.now().date() - timedelta(days=60),
            end_date=timezone.now().date() - timedelta(days=30),
            is_active=True
        )
        
        # Should not be active for current date
        active_promotions = MedicationSearchPromotion.objects.filter(
            query_string='expired',
            is_active=True,
            start_date__lte=timezone.now().date(),
            end_date__gte=timezone.now().date()
        )
        
        self.assertEqual(active_promotions.count(), 0)


class SearchSuggestionTestCase(BaseSearchTestCase):
    """Test cases for SearchSuggestion and autocomplete."""
    
    def setUp(self):
        """Set up search suggestion test data."""
        super().setUp()
        
        # Create search suggestions
        self.aspirin_suggestion = SearchSuggestion.objects.create(
            suggestion_text='Aspirin',
            suggestion_type='medication_name',
            language='en-ZA',
            popularity_score=8.5,
            is_active=True
        )
        
        self.headache_suggestion = SearchSuggestion.objects.create(
            suggestion_text='headache relief',
            suggestion_type='symptom',
            language='en-ZA',
            popularity_score=7.2,
            is_active=True
        )
        
    def test_suggestion_creation(self):
        """Test creating search suggestions."""
        self.assertEqual(self.aspirin_suggestion.suggestion_text, 'Aspirin')
        self.assertEqual(self.aspirin_suggestion.suggestion_type, 'medication_name')
        self.assertEqual(self.aspirin_suggestion.popularity_score, 8.5)
        
    def test_autocomplete_functionality(self):
        """Test autocomplete suggestion retrieval."""
        # Test prefix matching
        suggestions = SearchSuggestion.get_suggestions('Asp', limit=5)
        
        self.assertIn(self.aspirin_suggestion, suggestions)
        
        # Test case insensitive matching
        suggestions = SearchSuggestion.get_suggestions('asp', limit=5)
        
        self.assertIn(self.aspirin_suggestion, suggestions)
        
    def test_suggestion_popularity_ordering(self):
        """Test suggestion ordering by popularity."""
        suggestions = SearchSuggestion.get_suggestions('', limit=10)
        
        # Should be ordered by popularity score descending
        scores = [s.popularity_score for s in suggestions]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
    def test_suggestion_language_filtering(self):
        """Test suggestion filtering by language."""
        # Create Afrikaans suggestion
        afrikaans_suggestion = SearchSuggestion.objects.create(
            suggestion_text='Aspirien',
            suggestion_type='medication_name',
            language='af-ZA',
            popularity_score=6.0,
            is_active=True
        )
        
        # Test English suggestions
        english_suggestions = SearchSuggestion.get_suggestions(
            'Asp', language='en-ZA', limit=5
        )
        
        self.assertIn(self.aspirin_suggestion, english_suggestions)
        self.assertNotIn(afrikaans_suggestion, english_suggestions)
        
        # Test Afrikaans suggestions
        afrikaans_suggestions = SearchSuggestion.get_suggestions(
            'Asp', language='af-ZA', limit=5
        )
        
        self.assertIn(afrikaans_suggestion, afrikaans_suggestions)
        self.assertNotIn(self.aspirin_suggestion, afrikaans_suggestions)
        
    def test_suggestion_usage_tracking(self):
        """Test suggestion usage tracking."""
        initial_count = self.aspirin_suggestion.search_count
        
        # Update search count
        SearchSuggestion.update_search_count(
            self.aspirin_suggestion, 
            'medication_name'
        )
        
        self.aspirin_suggestion.refresh_from_db()
        self.assertEqual(self.aspirin_suggestion.search_count, initial_count + 1)


class SearchFacetTestCase(BaseSearchTestCase):
    """Test cases for SearchFacet and faceted search."""
    
    def setUp(self):
        """Set up search facet test data."""
        super().setUp()
        
        # Create search facets
        self.form_facet = SearchFacet.objects.create(
            facet_name='form',
            facet_type='medication_form',
            display_name='Medication Form',
            is_active=True,
            sort_order=1
        )
        
        self.strength_facet = SearchFacet.objects.create(
            facet_name='strength',
            facet_type='medication_strength',
            display_name='Strength',
            is_active=True,
            sort_order=2
        )
        
    def test_facet_creation(self):
        """Test creating search facets."""
        self.assertEqual(self.form_facet.facet_name, 'form')
        self.assertEqual(self.form_facet.display_name, 'Medication Form')
        self.assertTrue(self.form_facet.is_active)
        
    def test_facet_value_aggregation(self):
        """Test facet value aggregation from medications."""
        # Index medications first
        EnhancedSearchIndex.index_medication(self.aspirin)
        EnhancedSearchIndex.index_medication(self.ibuprofen)
        EnhancedSearchIndex.index_medication(self.paracetamol)
        
        # Get facet values for form
        facet_values = self.form_facet.get_facet_values()
        
        # Should include tablet form
        self.assertIn('tablet', [v['value'] for v in facet_values])
        
    def test_facet_filtering(self):
        """Test facet-based filtering."""
        # Index medications
        EnhancedSearchIndex.index_medication(self.aspirin)
        EnhancedSearchIndex.index_medication(self.ibuprofen)
        
        # Apply facet filter
        filtered_results = SearchFacet.apply_facet_filters(
            EnhancedSearchIndex.objects.all(),
            {'form': ['tablet']}
        )
        
        # Should return only tablet medications
        self.assertGreater(filtered_results.count(), 0)
        
    def test_facet_usage_tracking(self):
        """Test facet usage tracking."""
        initial_count = self.form_facet.usage_count
        
        # Update usage count
        self.form_facet.update_usage_count()
        
        self.form_facet.refresh_from_db()
        self.assertEqual(self.form_facet.usage_count, initial_count + 1)


class SearchAnalyticsTestCase(BaseSearchTestCase):
    """Test cases for SearchAnalytics and search tracking."""
    
    def test_search_query_recording(self):
        """Test recording search queries."""
        # Record a search query
        SearchAnalytics.record_search_query(
            search_query='aspirin',
            results_count=5,
            user_id=self.user.id,
            session_id='test_session_123'
        )
        
        # Check analytics entry was created
        analytics = SearchAnalytics.objects.filter(
            search_query='aspirin',
            user_id=self.user.id
        ).first()
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.search_results_count, 5)
        self.assertEqual(analytics.session_id, 'test_session_123')
        
    def test_result_click_recording(self):
        """Test recording result clicks."""
        # Record a search query first
        SearchAnalytics.record_search_query(
            search_query='aspirin',
            results_count=5,
            user_id=self.user.id
        )
        
        # Record result click
        SearchAnalytics.record_result_click(
            search_query='aspirin',
            result_id=self.aspirin.id,
            content_type='medication',
            object_id=self.aspirin.id,
            user_id=self.user.id
        )
        
        # Check click was recorded
        analytics = SearchAnalytics.objects.filter(
            search_query='aspirin',
            clicked_result=True
        ).first()
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.clicked_result_id, self.aspirin.id)
        
    def test_search_statistics_generation(self):
        """Test search statistics generation."""
        # Record multiple searches
        for i in range(5):
            SearchAnalytics.record_search_query(
                search_query='aspirin',
                results_count=3,
                user_id=self.user.id
            )
            
        for i in range(3):
            SearchAnalytics.record_search_query(
                search_query='ibuprofen',
                results_count=2,
                user_id=self.user.id
            )
        
        # Get search statistics
        stats = SearchAnalytics.get_search_statistics(days=30)
        
        self.assertIn('total_searches', stats)
        self.assertIn('unique_queries', stats)
        self.assertIn('popular_queries', stats)
        
        # Should show aspirin as most popular
        popular_queries = stats['popular_queries']
        self.assertEqual(popular_queries[0]['query'], 'aspirin')
        self.assertEqual(popular_queries[0]['count'], 5)
        
    def test_user_search_history(self):
        """Test user search history retrieval."""
        # Record user searches
        queries = ['aspirin', 'ibuprofen', 'paracetamol']
        for query in queries:
            SearchAnalytics.record_search_query(
                search_query=query,
                results_count=3,
                user_id=self.user.id
            )
        
        # Get user search history
        history = SearchAnalytics.get_user_search_history(
            user_id=self.user.id,
            limit=10
        )
        
        self.assertEqual(len(history), 3)
        
        # Should be ordered by most recent first
        recent_queries = [h.search_query for h in history]
        self.assertEqual(recent_queries, ['paracetamol', 'ibuprofen', 'aspirin'])


class SearchPerformanceTestCase(BaseSearchTestCase):
    """Test cases for search performance optimization."""
    
    def test_search_response_time_tracking(self):
        """Test search response time tracking."""
        # Record search performance
        SearchPerformance.objects.create(
            search_query='aspirin',
            response_time_ms=150,
            results_count=5,
            backend_type='database',
            cache_hit=False
        )
        
        performance = SearchPerformance.objects.filter(
            search_query='aspirin'
        ).first()
        
        self.assertIsNotNone(performance)
        self.assertEqual(performance.response_time_ms, 150)
        self.assertFalse(performance.cache_hit)
        
    def test_slow_query_identification(self):
        """Test identification of slow queries."""
        # Record fast and slow queries
        SearchPerformance.objects.create(
            search_query='fast_query',
            response_time_ms=50,
            results_count=5
        )
        
        SearchPerformance.objects.create(
            search_query='slow_query',
            response_time_ms=2000,
            results_count=5
        )
        
        # Get slow queries
        slow_queries = SearchPerformance.get_slow_queries(threshold_ms=1000)
        
        self.assertEqual(len(slow_queries), 1)
        self.assertEqual(slow_queries[0]['search_query'], 'slow_query')
        
    def test_cache_performance_tracking(self):
        """Test cache performance tracking."""
        # Record cached search
        SearchPerformance.objects.create(
            search_query='cached_query',
            response_time_ms=25,
            results_count=5,
            cache_hit=True
        )
        
        # Get cache statistics
        cache_stats = SearchPerformance.get_cache_statistics()
        
        self.assertIn('cache_hit_rate', cache_stats)
        self.assertIn('avg_cached_response_time', cache_stats)


class SearchCacheTestCase(BaseSearchTestCase):
    """Test cases for search result caching."""
    
    def test_search_result_caching(self):
        """Test caching of search results."""
        # Set cached results
        search_query = 'aspirin'
        results_data = [
            {'id': self.aspirin.id, 'name': 'Aspirin', 'score': 0.95}
        ]
        
        SearchResultCache.set_cached_results(
            cache_key=f'search:{search_query}',
            cache_type='medication_search',
            data=results_data,
            search_query=search_query
        )
        
        # Retrieve cached results
        cached_results = SearchResultCache.get_cached_results(
            cache_key=f'search:{search_query}',
            cache_type='medication_search'
        )
        
        self.assertIsNotNone(cached_results)
        self.assertEqual(len(cached_results['data']), 1)
        self.assertEqual(cached_results['data'][0]['name'], 'Aspirin')
        
    def test_cache_expiration(self):
        """Test cache expiration handling."""
        # Set cached results with short expiration
        SearchResultCache.set_cached_results(
            cache_key='expiring_search',
            cache_type='medication_search',
            data=[],
            expiration_hours=0.001  # Very short expiration
        )
        
        # Wait for expiration (simulate)
        import time
        time.sleep(0.1)
        
        # Should be expired
        cached_results = SearchResultCache.get_cached_results(
            cache_key='expiring_search',
            cache_type='medication_search'
        )
        
        self.assertIsNone(cached_results)
        
    def test_cache_invalidation(self):
        """Test cache invalidation on data changes."""
        # Set cached results
        SearchResultCache.set_cached_results(
            cache_key='invalidation_test',
            cache_type='medication_search',
            data=[{'id': 1, 'name': 'Test'}]
        )
        
        # Invalidate cache
        SearchResultCache.invalidate_cache('medication_search')
        
        # Should be invalidated
        cached_results = SearchResultCache.get_cached_results(
            cache_key='invalidation_test',
            cache_type='medication_search'
        )
        
        self.assertIsNone(cached_results)


class MultilingualSearchTestCase(BaseSearchTestCase):
    """Test cases for multilingual search functionality."""
    
    def setUp(self):
        """Set up multilingual search test data."""
        super().setUp()
        
        # Create multilingual index entries
        MultilingualSearchIndex.objects.create(
            original_text='Aspirin',
            translated_text='Aspirien',
            source_language='en-ZA',
            target_language='af-ZA',
            content_type='medication',
            object_id=self.aspirin.id
        )
        
    def test_multilingual_indexing(self):
        """Test multilingual content indexing."""
        # Index medication in multiple languages
        MultilingualSearchIndex.index_multilingual_medication(self.aspirin)
        
        # Should have entries for both languages
        english_entry = MultilingualSearchIndex.objects.filter(
            content_type='medication',
            object_id=self.aspirin.id,
            source_language='en-ZA'
        ).first()
        
        self.assertIsNotNone(english_entry)
        
    def test_cross_language_search(self):
        """Test cross-language search functionality."""
        # Search in Afrikaans should find English content
        results = MultilingualSearchIndex.search_multilingual(
            query='Aspirien',
            language='af-ZA',
            limit=10
        )
        
        self.assertGreater(len(results), 0)
        
    def test_language_detection(self):
        """Test automatic language detection."""
        # Test language detection for queries
        detected_language = MultilingualSearchIndex.detect_query_language(
            'Aspirien pynstiller'
        )
        
        # Should detect Afrikaans
        self.assertEqual(detected_language, 'af-ZA')


class SearchIntegrationTestCase(TransactionTestCase):
    """Integration tests for search with other system components."""
    
    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='integration_user',
            email='integration@medguard.co.za',
            password='testpass123'
        )
        
        self.medication = Medication.objects.create(
            name='Integration Test Med',
            strength='100mg',
            form='tablet'
        )
        
    def test_search_with_wagtail_backend(self):
        """Test search integration with Wagtail search backend."""
        # Index content using Wagtail's search backend
        search_backend = get_search_backend()
        
        # Add medication to search index
        search_backend.add(self.medication)
        search_backend.refresh_index()
        
        # Search for medication
        results = search_backend.search('Integration Test', Medication)
        
        self.assertGreater(len(results), 0)
        
    def test_search_with_page_indexing(self):
        """Test search integration with page indexing."""
        # Create a page with searchable content
        root_page = Page.objects.get(id=2)
        
        home_page = HomePage(
            title='Integration Test Page',
            slug='integration-test',
            hero_title='Integration Test',
            hero_content='<p>This page contains integration test content</p>'
        )
        root_page.add_child(instance=home_page)
        
        # Search for page content
        search_backend = get_search_backend()
        results = search_backend.search('Integration Test', Page)
        
        self.assertGreater(len(results), 0)
        
    def test_search_result_ranking_integration(self):
        """Test search result ranking integration."""
        # Create multiple medications with different relevance
        medications = []
        for i in range(5):
            med = Medication.objects.create(
                name=f'Ranking Test Med {i}',
                strength='100mg',
                form='tablet'
            )
            medications.append(med)
            
            # Record different search counts for ranking
            SearchRanking.record_search(
                content_type='medication',
                object_id=med.id
            )
            
            # Simulate different popularity
            for j in range(i + 1):
                SearchRanking.record_search(
                    content_type='medication',
                    object_id=med.id
                )
        
        # Search should return results ranked by popularity
        search_backend = get_search_backend()
        results = search_backend.search('Ranking Test', Medication)
        
        # Results should be ordered by relevance
        self.assertGreater(len(results), 0)


class SearchAPIIntegrationTestCase(BaseSearchTestCase):
    """Test cases for search API integration."""
    
    def test_search_api_endpoint(self):
        """Test search API endpoint functionality."""
        # Index medications
        EnhancedSearchIndex.index_medication(self.aspirin)
        
        # Test search API
        self.client.force_login(self.user)
        response = self.client.get('/api/v2/search/?query=aspirin')
        
        self.assertEqual(response.status_code, 200)
        
    def test_autocomplete_api_endpoint(self):
        """Test autocomplete API endpoint."""
        # Create suggestions
        SearchSuggestion.objects.create(
            suggestion_text='Aspirin',
            suggestion_type='medication_name',
            language='en-ZA',
            is_active=True
        )
        
        # Test autocomplete API
        self.client.force_login(self.user)
        response = self.client.get('/api/v2/search/autocomplete/?q=asp')
        
        self.assertEqual(response.status_code, 200)
        
    def test_faceted_search_api(self):
        """Test faceted search API endpoint."""
        # Test faceted search API
        self.client.force_login(self.user)
        response = self.client.get('/api/v2/search/faceted/?query=medication&facets=form,strength')
        
        self.assertEqual(response.status_code, 200)


@pytest.mark.django_db
class SearchPerformanceIntegrationTestCase(TestCase):
    """Performance integration tests for search functionality."""
    
    def setUp(self):
        """Set up performance test data."""
        # Create many medications for performance testing
        medications = []
        for i in range(100):
            medications.append(Medication(
                name=f'Performance Test Med {i}',
                strength=f'{(i % 10 + 1) * 100}mg',
                form='tablet',
                manufacturer=f'Pharma {i % 5}'
            ))
        
        Medication.objects.bulk_create(medications)
        
        # Index all medications
        for medication in Medication.objects.all():
            EnhancedSearchIndex.index_medication(medication)
            
    def test_large_dataset_search_performance(self):
        """Test search performance with large dataset."""
        import time
        
        # Test search performance
        start_time = time.time()
        
        results = EnhancedSearchIndex.objects.filter(
            content__icontains='Performance Test'
        )[:20]
        
        # Force evaluation
        list(results)
        
        search_time = time.time() - start_time
        
        # Should complete within reasonable time
        self.assertLess(search_time, 2.0)
        
    def test_concurrent_search_performance(self):
        """Test concurrent search performance."""
        from threading import Thread
        import time
        
        results = []
        
        def search_worker():
            start_time = time.time()
            search_results = EnhancedSearchIndex.objects.filter(
                content__icontains='Performance Test'
            )[:10]
            list(search_results)  # Force evaluation
            end_time = time.time()
            results.append(end_time - start_time)
        
        # Run concurrent searches
        threads = []
        for i in range(5):
            thread = Thread(target=search_worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All searches should complete within reasonable time
        for search_time in results:
            self.assertLess(search_time, 3.0)
            
    def test_search_index_optimization(self):
        """Test search index optimization."""
        # Test index optimization
        optimizer = SearchPerformanceOptimizer.objects.create(
            optimization_type='index_rebuild',
            is_active=True
        )
        
        # Run optimization
        optimizer.optimize_search_indexes()
        
        # Should complete successfully
        optimizer.refresh_from_db()
        self.assertTrue(optimizer.last_optimization_successful)
