from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import hashlib
from django.core.paginator import Paginator

# Wagtail 7.0.2 imports
from wagtail.models import Page
from wagtail.search import index
from wagtail.search.backends import get_search_backend
from wagtail.contrib.search_promotions.models import SearchPromotion

# Local imports
from medications.models import Medication, MedicationIndexPage, MedicationDetailPage


class EnhancedSearchIndex(models.Model):
    """
    Enhanced search index model for Wagtail 7.0.2 with improved medication content indexing.
    
    This model provides advanced search capabilities with healthcare-specific relevance
    scoring and multilingual support.
    """
    
    # Search content fields
    title = models.CharField(max_length=255, help_text=_('Searchable title'))
    content = models.TextField(help_text=_('Searchable content'))
    content_type = models.CharField(max_length=50, help_text=_('Type of content'))
    object_id = models.PositiveIntegerField(help_text=_('ID of the indexed object'))
    
    # Healthcare-specific fields
    medication_name = models.CharField(max_length=255, blank=True, help_text=_('Medication name'))
    generic_name = models.CharField(max_length=255, blank=True, help_text=_('Generic medication name'))
    active_ingredients = models.TextField(blank=True, help_text=_('Active ingredients'))
    side_effects = models.TextField(blank=True, help_text=_('Side effects'))
    interactions = models.TextField(blank=True, help_text=_('Drug interactions'))
    dosage_info = models.TextField(blank=True, help_text=_('Dosage information'))
    
    # Multilingual support
    language = models.CharField(max_length=10, default='en-ZA', help_text=_('Content language'))
    
    # Relevance scoring
    relevance_score = models.FloatField(default=1.0, help_text=_('Search relevance score'))
    healthcare_relevance = models.FloatField(default=1.0, help_text=_('Healthcare-specific relevance'))
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True, help_text=_('Last update time'))
    is_active = models.BooleanField(default=True, help_text=_('Whether this index entry is active'))
    
    # Note: This model is a custom search index, not a Wagtail page model
    # It doesn't use Wagtail's search_fields mechanism
    
    class Meta:
        verbose_name = _('Enhanced Search Index')
        verbose_name_plural = _('Enhanced Search Indexes')
        db_table = 'enhanced_search_index'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active']),
            models.Index(fields=['relevance_score']),
            models.Index(fields=['healthcare_relevance']),
        ]
        ordering = ['-relevance_score', '-healthcare_relevance']
    
    def __str__(self):
        return f"{self.title} ({self.content_type})"
    
    @classmethod
    def index_medication(cls, medication):
        """Index a medication with enhanced healthcare relevance scoring."""
        # Calculate healthcare relevance score
        relevance_score = cls._calculate_healthcare_relevance(medication)
        
        # Create or update index entry
        index_entry, created = cls.objects.update_or_create(
            content_type='medication',
            object_id=medication.id,
            defaults={
                'title': medication.name,
                'content': cls._extract_searchable_content(medication),
                'medication_name': medication.name,
                'generic_name': medication.generic_name or '',
                'active_ingredients': medication.active_ingredients or '',
                'side_effects': cls._extract_side_effects(medication),
                'interactions': cls._extract_interactions(medication),
                'dosage_info': cls._extract_dosage_info(medication),
                'relevance_score': relevance_score,
                'healthcare_relevance': relevance_score,
                'is_active': True,
            }
        )
        
        # Index in both languages
        cls._index_multilingual(medication, index_entry)
        
        return index_entry
    
    @classmethod
    def _calculate_healthcare_relevance(cls, medication):
        """Calculate healthcare-specific relevance score."""
        score = 1.0
        
        # Boost for prescription medications
        if medication.prescription_type in ['prescription', 'schedule_1', 'schedule_2']:
            score += 0.5
        
        # Boost for medications with detailed information
        if medication.content:
            score += 0.3
        
        # Boost for medications with side effects
        if hasattr(medication, 'side_effects') and medication.side_effects:
            score += 0.2
        
        # Boost for medications with interactions
        if hasattr(medication, 'interactions') and medication.interactions:
            score += 0.2
        
        return min(score, 5.0)  # Cap at 5.0
    
    @classmethod
    def _extract_searchable_content(cls, medication):
        """Extract searchable content from medication."""
        content_parts = []
        
        if medication.description:
            content_parts.append(medication.description)
        
        if medication.active_ingredients:
            content_parts.append(medication.active_ingredients)
        
        if hasattr(medication, 'content') and medication.content:
            # Extract text from StreamField content
            content_parts.append(cls._extract_streamfield_text(medication.content))
        
        return ' '.join(content_parts)
    
    @classmethod
    def _extract_streamfield_text(cls, streamfield_data):
        """Extract plain text from StreamField data."""
        if not streamfield_data:
            return ''
        
        text_parts = []
        for block in streamfield_data:
            if hasattr(block, 'value'):
                if isinstance(block.value, dict):
                    # Handle StructBlock
                    for key, value in block.value.items():
                        if isinstance(value, str):
                            text_parts.append(value)
                elif isinstance(block.value, str):
                    text_parts.append(block.value)
        
        return ' '.join(text_parts)
    
    @classmethod
    def _extract_side_effects(cls, medication):
        """Extract side effects information."""
        if not hasattr(medication, 'content') or not medication.content:
            return ''
        
        side_effects = []
        for block in medication.content:
            if block.block_type == 'side_effects':
                if hasattr(block.value, 'effect_name'):
                    side_effects.append(block.value.effect_name)
        
        return ', '.join(side_effects)
    
    @classmethod
    def _extract_interactions(cls, medication):
        """Extract drug interactions information."""
        if not hasattr(medication, 'content') or not medication.content:
            return ''
        
        interactions = []
        for block in medication.content:
            if block.block_type == 'interactions':
                if hasattr(block.value, 'interacting_medication'):
                    interactions.append(block.value.interacting_medication)
        
        return ', '.join(interactions)
    
    @classmethod
    def _extract_dosage_info(cls, medication):
        """Extract dosage information."""
        if not hasattr(medication, 'content') or not medication.content:
            return ''
        
        dosage_info = []
        for block in medication.content:
            if block.block_type == 'dosage':
                if hasattr(block.value, 'amount') and hasattr(block.value, 'unit'):
                    dosage_info.append(f"{block.value.amount} {block.value.unit}")
        
        return ', '.join(dosage_info)
    
    @classmethod
    def _index_multilingual(cls, medication, index_entry):
        """Index content in multiple languages."""
        # Index in English
        cls.objects.update_or_create(
            content_type='medication',
            object_id=medication.id,
            language='en-ZA',
            defaults={
                'title': medication.name,
                'content': cls._extract_searchable_content(medication),
                'medication_name': medication.name,
                'generic_name': medication.generic_name or '',
                'relevance_score': index_entry.relevance_score,
                'healthcare_relevance': index_entry.healthcare_relevance,
            }
        )
        
        # Index in Afrikaans (if available)
        # This would be populated by translation system
        cls.objects.update_or_create(
            content_type='medication',
            object_id=medication.id,
            language='af-ZA',
            defaults={
                'title': medication.name,  # Would be translated
                'content': cls._extract_searchable_content(medication),  # Would be translated
                'medication_name': medication.name,  # Would be translated
                'generic_name': medication.generic_name or '',  # Would be translated
                'relevance_score': index_entry.relevance_score,
                'healthcare_relevance': index_entry.healthcare_relevance,
            }
        ) 


class MedicationSearchPromotion(SearchPromotion):
    """
    Enhanced search promotion model for medication content with healthcare-specific features.
    
    Extends Wagtail's SearchPromotion with medication-specific functionality.
    """
    
    # Healthcare-specific promotion types
    class PromotionType(models.TextChoices):
        FEATURED_MEDICATION = 'featured_medication', _('Featured Medication')
        NEW_MEDICATION = 'new_medication', _('New Medication')
        POPULAR_MEDICATION = 'popular_medication', _('Popular Medication')
        SAFETY_ALERT = 'safety_alert', _('Safety Alert')
        DRUG_RECALL = 'drug_recall', _('Drug Recall')
        GENERIC_AVAILABLE = 'generic_available', _('Generic Available')
    
    # Enhanced fields
    promotion_type = models.CharField(
        max_length=30,
        choices=PromotionType.choices,
        default=PromotionType.FEATURED_MEDICATION,
        help_text=_('Type of search promotion')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='search_promotions',
        help_text=_('Associated medication for this promotion')
    )
    
    priority_score = models.IntegerField(
        default=1,
        help_text=_('Priority score for promotion ranking (higher = more important)')
    )
    
    start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this promotion should start appearing')
    )
    
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this promotion should stop appearing')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this promotion is currently active')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for this promotion')
    )
    
    class Meta:
        verbose_name = _('Medication Search Promotion')
        verbose_name_plural = _('Medication Search Promotions')
        db_table = 'medication_search_promotions'
        indexes = [
            models.Index(fields=['promotion_type']),
            models.Index(fields=['priority_score']),
            models.Index(fields=['is_active']),
            models.Index(fields=['language']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['-priority_score', '-start_date']
    
    def __str__(self):
        return f"{self.query} - {self.promotion_type}"
    
    @property
    def is_currently_active(self):
        """Check if promotion is currently active based on dates."""
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.start_date and now < self.start_date:
            return False
        
        if self.end_date and now > self.end_date:
            return False
        
        return True
    
    @classmethod
    def get_active_promotions_for_query(cls, query, language='en-ZA'):
        """Get active promotions for a specific query and language."""
        return cls.objects.filter(
            query__query_string__icontains=query,
            language=language,
            is_active=True
        ).filter(
            models.Q(start_date__isnull=True) | models.Q(start_date__lte=timezone.now())
        ).filter(
            models.Q(end_date__isnull=True) | models.Q(end_date__gte=timezone.now())
        ).order_by('-priority_score')


class SearchResultTemplate(models.Model):
    """
    Custom search result template model for different content types.
    
    Allows for different display templates based on content type and search context.
    """
    
    # Template type choices
    class TemplateType(models.TextChoices):
        MEDICATION_DETAIL = 'medication_detail', _('Medication Detail')
        MEDICATION_LIST = 'medication_list', _('Medication List')
        SIDE_EFFECTS = 'side_effects', _('Side Effects')
        DRUG_INTERACTIONS = 'drug_interactions', _('Drug Interactions')
        DOSAGE_INFO = 'dosage_info', _('Dosage Information')
        GENERIC_ALTERNATIVES = 'generic_alternatives', _('Generic Alternatives')
        SAFETY_ALERTS = 'safety_alerts', _('Safety Alerts')
    
    # Template configuration
    name = models.CharField(max_length=100, help_text=_('Template name'))
    template_type = models.CharField(
        max_length=30,
        choices=TemplateType.choices,
        help_text=_('Type of template')
    )
    
    template_path = models.CharField(
        max_length=255,
        help_text=_('Path to the template file')
    )
    
    description = models.TextField(
        blank=True,
        help_text=_('Description of when this template should be used')
    )
    
    # Display settings
    show_medication_image = models.BooleanField(
        default=True,
        help_text=_('Whether to show medication image in results')
    )
    
    show_side_effects = models.BooleanField(
        default=True,
        help_text=_('Whether to show side effects in results')
    )
    
    show_interactions = models.BooleanField(
        default=True,
        help_text=_('Whether to show drug interactions in results')
    )
    
    show_dosage_info = models.BooleanField(
        default=True,
        help_text=_('Whether to show dosage information in results')
    )
    
    show_generic_alternatives = models.BooleanField(
        default=False,
        help_text=_('Whether to show generic alternatives in results')
    )
    
    # Styling options
    css_class = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('CSS class for styling this template')
    )
    
    # Priority and activation
    priority = models.IntegerField(
        default=1,
        help_text=_('Priority for template selection (higher = more important)')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this template is active')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for this template')
    )
    
    class Meta:
        verbose_name = _('Search Result Template')
        verbose_name_plural = _('Search Result Templates')
        db_table = 'search_result_templates'
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['is_active']),
            models.Index(fields=['language']),
        ]
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"
    
    @classmethod
    def get_template_for_content(cls, content_type, language='en-ZA'):
        """Get the appropriate template for a content type and language."""
        return cls.objects.filter(
            template_type=content_type,
            language=language,
            is_active=True
        ).order_by('-priority').first()
    
    def get_context_data(self, search_result):
        """Get context data for rendering this template."""
        context = {
            'template': self,
            'result': search_result,
            'show_image': self.show_medication_image,
            'show_side_effects': self.show_side_effects,
            'show_interactions': self.show_interactions,
            'show_dosage': self.show_dosage_info,
            'show_generics': self.show_generic_alternatives,
            'css_class': self.css_class,
        }
        
        # Add medication-specific context if available
        if hasattr(search_result, 'medication'):
            context['medication'] = search_result.medication
        
        return context 


class MedicationAutocomplete(models.Model):
    """
    Autocomplete model for medication search with Wagtail 7.0.2 enhanced features.
    
    Provides fast autocomplete suggestions for medication names, generic names,
    and active ingredients.
    """
    
    # Suggestion types
    class SuggestionType(models.TextChoices):
        MEDICATION_NAME = 'medication_name', _('Medication Name')
        GENERIC_NAME = 'generic_name', _('Generic Name')
        ACTIVE_INGREDIENT = 'active_ingredient', _('Active Ingredient')
        BRAND_NAME = 'brand_name', _('Brand Name')
        MANUFACTURER = 'manufacturer', _('Manufacturer')
        CATEGORY = 'category', _('Category')
    
    # Core fields
    suggestion = models.CharField(max_length=255, help_text=_('Autocomplete suggestion'))
    suggestion_type = models.CharField(
        max_length=20,
        choices=SuggestionType.choices,
        help_text=_('Type of suggestion')
    )
    
    # Associated medication
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='autocomplete_suggestions',
        help_text=_('Associated medication')
    )
    
    # Relevance and ranking
    frequency = models.PositiveIntegerField(
        default=1,
        help_text=_('How often this suggestion is used')
    )
    
    relevance_score = models.FloatField(
        default=1.0,
        help_text=_('Relevance score for ranking')
    )
    
    # Search metadata
    search_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of times this suggestion was searched')
    )
    
    last_searched = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this suggestion was last searched')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for this suggestion')
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this suggestion is active')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Medication Autocomplete')
        verbose_name_plural = _('Medication Autocomplete Suggestions')
        db_table = 'medication_autocomplete'
        indexes = [
            models.Index(fields=['suggestion_type']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active']),
            models.Index(fields=['relevance_score']),
            models.Index(fields=['frequency']),
            models.Index(fields=['suggestion', 'suggestion_type']),
        ]
        ordering = ['-relevance_score', '-frequency', 'suggestion']
        unique_together = ['suggestion', 'suggestion_type', 'medication', 'language']
    
    def __str__(self):
        return f"{self.suggestion} ({self.suggestion_type})"
    
    @classmethod
    def get_suggestions(cls, query, suggestion_type=None, language='en-ZA', limit=10):
        """Get autocomplete suggestions for a query."""
        queryset = cls.objects.filter(
            suggestion__icontains=query,
            language=language,
            is_active=True
        )
        
        if suggestion_type:
            queryset = queryset.filter(suggestion_type=suggestion_type)
        
        return queryset.order_by('-relevance_score', '-frequency')[:limit]
    
    @classmethod
    def get_popular_suggestions(cls, language='en-ZA', limit=10):
        """Get popular autocomplete suggestions."""
        return cls.objects.filter(
            language=language,
            is_active=True,
            frequency__gt=1
        ).order_by('-frequency', '-relevance_score')[:limit]
    
    @classmethod
    def update_search_count(cls, suggestion, suggestion_type, language='en-ZA'):
        """Update search count for a suggestion."""
        try:
            autocomplete = cls.objects.get(
                suggestion=suggestion,
                suggestion_type=suggestion_type,
                language=language
            )
            autocomplete.search_count += 1
            autocomplete.last_searched = timezone.now()
            autocomplete.save()
        except cls.DoesNotExist:
            pass
    
    @classmethod
    def generate_suggestions_for_medication(cls, medication, language='en-ZA'):
        """Generate autocomplete suggestions for a medication."""
        suggestions = []
        
        # Medication name suggestions
        if medication.name:
            suggestions.append({
                'suggestion': medication.name,
                'suggestion_type': cls.SuggestionType.MEDICATION_NAME,
                'relevance_score': 5.0
            })
        
        # Generic name suggestions
        if medication.generic_name:
            suggestions.append({
                'suggestion': medication.generic_name,
                'suggestion_type': cls.SuggestionType.GENERIC_NAME,
                'relevance_score': 4.0
            })
        
        # Brand name suggestions
        if medication.brand_name:
            suggestions.append({
                'suggestion': medication.brand_name,
                'suggestion_type': cls.SuggestionType.BRAND_NAME,
                'relevance_score': 3.5
            })
        
        # Active ingredients suggestions
        if medication.active_ingredients:
            ingredients = medication.active_ingredients.split(',')
            for ingredient in ingredients:
                ingredient = ingredient.strip()
                if ingredient:
                    suggestions.append({
                        'suggestion': ingredient,
                        'suggestion_type': cls.SuggestionType.ACTIVE_INGREDIENT,
                        'relevance_score': 3.0
                    })
        
        # Create or update suggestions
        for suggestion_data in suggestions:
            cls.objects.update_or_create(
                suggestion=suggestion_data['suggestion'],
                suggestion_type=suggestion_data['suggestion_type'],
                medication=medication,
                language=language,
                defaults={
                    'relevance_score': suggestion_data['relevance_score'],
                    'is_active': True
                }
            )


class SearchSuggestion(models.Model):
    """
    Model for storing and managing search suggestions and corrections.
    
    Provides spell-checking, synonym matching, and search refinement suggestions.
    """
    
    # Suggestion types
    class SuggestionType(models.TextChoices):
        SPELLING_CORRECTION = 'spelling_correction', _('Spelling Correction')
        SYNONYM = 'synonym', _('Synonym')
        RELATED_TERM = 'related_term', _('Related Term')
        POPULAR_SEARCH = 'popular_search', _('Popular Search')
        CATEGORY_SUGGESTION = 'category_suggestion', _('Category Suggestion')
    
    # Core fields
    original_query = models.CharField(max_length=255, help_text=_('Original search query'))
    suggested_query = models.CharField(max_length=255, help_text=_('Suggested search query'))
    suggestion_type = models.CharField(
        max_length=30,
        choices=SuggestionType.choices,
        help_text=_('Type of suggestion')
    )
    
    # Relevance and usage
    confidence_score = models.FloatField(
        default=1.0,
        help_text=_('Confidence score for this suggestion (0-1)')
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of times this suggestion was used')
    )
    
    # Context
    context = models.TextField(
        blank=True,
        help_text=_('Context information for this suggestion')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for this suggestion')
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this suggestion is active')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Search Suggestion')
        verbose_name_plural = _('Search Suggestions')
        db_table = 'search_suggestions'
        indexes = [
            models.Index(fields=['original_query']),
            models.Index(fields=['suggestion_type']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active']),
            models.Index(fields=['confidence_score']),
        ]
        ordering = ['-confidence_score', '-usage_count']
        unique_together = ['original_query', 'suggested_query', 'language']
    
    def __str__(self):
        return f"{self.original_query} → {self.suggested_query}"
    
    @classmethod
    def get_suggestions_for_query(cls, query, language='en-ZA', limit=5):
        """Get suggestions for a specific query."""
        return cls.objects.filter(
            original_query__iexact=query,
            language=language,
            is_active=True
        ).order_by('-confidence_score', '-usage_count')[:limit]
    
    @classmethod
    def get_popular_suggestions(cls, language='en-ZA', limit=10):
        """Get popular search suggestions."""
        return cls.objects.filter(
            language=language,
            is_active=True,
            usage_count__gt=0
        ).order_by('-usage_count', '-confidence_score')[:limit]
    
    @classmethod
    def record_suggestion_usage(cls, original_query, suggested_query, language='en-ZA'):
        """Record when a suggestion is used."""
        try:
            suggestion = cls.objects.get(
                original_query=original_query,
                suggested_query=suggested_query,
                language=language
            )
            suggestion.usage_count += 1
            suggestion.save()
        except cls.DoesNotExist:
            pass 


class SearchFacet(models.Model):
    """
    Faceted search model for medication categories and filters.
    
    Provides structured filtering capabilities for medication search results.
    """
    
    # Facet types
    class FacetType(models.TextChoices):
        MEDICATION_TYPE = 'medication_type', _('Medication Type')
        PRESCRIPTION_TYPE = 'prescription_type', _('Prescription Type')
        MANUFACTURER = 'manufacturer', _('Manufacturer')
        ACTIVE_INGREDIENT = 'active_ingredient', _('Active Ingredient')
        SIDE_EFFECT = 'side_effect', _('Side Effect')
        INTERACTION_TYPE = 'interaction_type', _('Interaction Type')
        DOSAGE_FORM = 'dosage_form', _('Dosage Form')
        CATEGORY = 'category', _('Category')
        PRICE_RANGE = 'price_range', _('Price Range')
        AVAILABILITY = 'availability', _('Availability')
    
    # Core fields
    name = models.CharField(max_length=100, help_text=_('Facet name'))
    facet_type = models.CharField(
        max_length=30,
        choices=FacetType.choices,
        help_text=_('Type of facet')
    )
    
    value = models.CharField(max_length=255, help_text=_('Facet value'))
    display_name = models.CharField(max_length=255, help_text=_('Display name for the facet'))
    
    # Count and usage
    count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of items matching this facet')
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of times this facet was used in searches')
    )
    
    # Ordering and display
    sort_order = models.IntegerField(
        default=0,
        help_text=_('Sort order for display')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this facet is active')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for this facet')
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text=_('Description of this facet')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Search Facet')
        verbose_name_plural = _('Search Facets')
        db_table = 'search_facets'
        indexes = [
            models.Index(fields=['facet_type']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['count']),
            models.Index(fields=['facet_type', 'value']),
        ]
        ordering = ['facet_type', 'sort_order', 'display_name']
        unique_together = ['facet_type', 'value', 'language']
    
    def __str__(self):
        return f"{self.facet_type}: {self.display_name}"
    
    @classmethod
    def get_facets_for_type(cls, facet_type, language='en-ZA', limit=None):
        """Get facets for a specific type."""
        queryset = cls.objects.filter(
            facet_type=facet_type,
            language=language,
            is_active=True,
            count__gt=0
        ).order_by('sort_order', '-count')
        
        if limit:
            queryset = queryset[:limit]
        
        return queryset
    
    @classmethod
    def get_all_active_facets(cls, language='en-ZA'):
        """Get all active facets grouped by type."""
        facets = cls.objects.filter(
            language=language,
            is_active=True,
            count__gt=0
        ).order_by('facet_type', 'sort_order', '-count')
        
        # Group by facet type
        grouped_facets = {}
        for facet in facets:
            if facet.facet_type not in grouped_facets:
                grouped_facets[facet.facet_type] = []
            grouped_facets[facet.facet_type].append(facet)
        
        return grouped_facets
    
    @classmethod
    def update_facet_counts(cls, facet_type, value, count, language='en-ZA'):
        """Update the count for a specific facet."""
        cls.objects.update_or_create(
            facet_type=facet_type,
            value=value,
            language=language,
            defaults={'count': count}
        )
    
    @classmethod
    def record_facet_usage(cls, facet_type, value, language='en-ZA'):
        """Record when a facet is used in a search."""
        try:
            facet = cls.objects.get(
                facet_type=facet_type,
                value=value,
                language=language
            )
            facet.usage_count += 1
            facet.save()
        except cls.DoesNotExist:
            pass


class SearchFilter(models.Model):
    """
    Advanced search filter model for complex medication queries.
    
    Provides configurable filters for medication search with healthcare-specific options.
    """
    
    # Filter types
    class FilterType(models.TextChoices):
        EXACT_MATCH = 'exact_match', _('Exact Match')
        CONTAINS = 'contains', _('Contains')
        STARTS_WITH = 'starts_with', _('Starts With')
        ENDS_WITH = 'ends_with', _('Ends With')
        RANGE = 'range', _('Range')
        BOOLEAN = 'boolean', _('Boolean')
        MULTIPLE_CHOICE = 'multiple_choice', _('Multiple Choice')
        DATE_RANGE = 'date_range', _('Date Range')
    
    # Core fields
    name = models.CharField(max_length=100, help_text=_('Filter name'))
    field_name = models.CharField(max_length=100, help_text=_('Database field to filter on'))
    filter_type = models.CharField(
        max_length=20,
        choices=FilterType.choices,
        help_text=_('Type of filter')
    )
    
    # Filter configuration
    filter_value = models.TextField(help_text=_('Filter value or configuration'))
    display_name = models.CharField(max_length=255, help_text=_('Display name for the filter'))
    
    # Filter behavior
    is_required = models.BooleanField(
        default=False,
        help_text=_('Whether this filter is required')
    )
    
    is_multiple = models.BooleanField(
        default=False,
        help_text=_('Whether multiple values can be selected')
    )
    
    default_value = models.TextField(
        blank=True,
        help_text=_('Default value for this filter')
    )
    
    # Validation and constraints
    validation_regex = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Regular expression for validation')
    )
    
    min_value = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Minimum value for range filters')
    )
    
    max_value = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Maximum value for range filters')
    )
    
    # Display and ordering
    sort_order = models.IntegerField(
        default=0,
        help_text=_('Sort order for display')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this filter is active')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for this filter')
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text=_('Description of this filter')
    )
    
    help_text = models.TextField(
        blank=True,
        help_text=_('Help text for users')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Search Filter')
        verbose_name_plural = _('Search Filters')
        db_table = 'search_filters'
        indexes = [
            models.Index(fields=['field_name']),
            models.Index(fields=['filter_type']),
            models.Index(fields=['language']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
        ]
        ordering = ['sort_order', 'name']
        unique_together = ['field_name', 'language']
    
    def __str__(self):
        return f"{self.name} ({self.filter_type})"
    
    @classmethod
    def get_active_filters(cls, language='en-ZA'):
        """Get all active filters for a language."""
        return cls.objects.filter(
            language=language,
            is_active=True
        ).order_by('sort_order', 'name')
    
    def apply_filter(self, queryset, value):
        """Apply this filter to a queryset."""
        if not value:
            return queryset
        
        if self.filter_type == self.FilterType.EXACT_MATCH:
            return queryset.filter(**{self.field_name: value})
        
        elif self.filter_type == self.FilterType.CONTAINS:
            return queryset.filter(**{f"{self.field_name}__icontains": value})
        
        elif self.filter_type == self.FilterType.STARTS_WITH:
            return queryset.filter(**{f"{self.field_name}__istartswith": value})
        
        elif self.filter_type == self.FilterType.ENDS_WITH:
            return queryset.filter(**{f"{self.field_name}__iendswith": value})
        
        elif self.filter_type == self.FilterType.RANGE:
            if self.min_value and self.max_value:
                return queryset.filter(**{
                    f"{self.field_name}__gte": self.min_value,
                    f"{self.field_name}__lte": self.max_value
                })
        
        elif self.filter_type == self.FilterType.BOOLEAN:
            return queryset.filter(**{self.field_name: value.lower() == 'true'})
        
        elif self.filter_type == self.FilterType.MULTIPLE_CHOICE:
            if isinstance(value, list):
                return queryset.filter(**{f"{self.field_name}__in": value})
            else:
                return queryset.filter(**{f"{self.field_name}__in": [value]})
        
        return queryset
    
    def validate_value(self, value):
        """Validate a filter value."""
        if not value:
            return True
        
        if self.validation_regex:
            import re
            if not re.match(self.validation_regex, str(value)):
                return False
        
        if self.filter_type == self.FilterType.RANGE:
            try:
                if self.min_value and value < self.min_value:
                    return False
                if self.max_value and value > self.max_value:
                    return False
            except (TypeError, ValueError):
                return False
        
        return True 


class SearchRanking(models.Model):
    """
    Enhanced search ranking model for healthcare-specific relevance scoring.
    
    Provides advanced ranking algorithms tailored for medication and healthcare content.
    """
    
    # Ranking factors
    class RankingFactor(models.TextChoices):
        MEDICATION_NAME = 'medication_name', _('Medication Name')
        GENERIC_NAME = 'generic_name', _('Generic Name')
        ACTIVE_INGREDIENT = 'active_ingredient', _('Active Ingredient')
        SIDE_EFFECT = 'side_effect', _('Side Effect')
        DRUG_INTERACTION = 'drug_interaction', _('Drug Interaction')
        DOSAGE_INFO = 'dosage_info', _('Dosage Information')
        PRESCRIPTION_TYPE = 'prescription_type', _('Prescription Type')
        SAFETY_ALERT = 'safety_alert', _('Safety Alert')
        POPULARITY = 'popularity', _('Popularity')
        RECENCY = 'recency', _('Recency')
        COMPLETENESS = 'completeness', _('Content Completeness')
        ACCURACY = 'accuracy', _('Information Accuracy')
    
    # Core fields
    content_type = models.CharField(max_length=50, help_text=_('Type of content being ranked'))
    object_id = models.PositiveIntegerField(help_text=_('ID of the ranked object'))
    
    # Ranking scores
    base_score = models.FloatField(default=1.0, help_text=_('Base relevance score'))
    healthcare_score = models.FloatField(default=1.0, help_text=_('Healthcare-specific relevance'))
    popularity_score = models.FloatField(default=1.0, help_text=_('Popularity-based score'))
    recency_score = models.FloatField(default=1.0, help_text=_('Recency-based score'))
    completeness_score = models.FloatField(default=1.0, help_text=_('Content completeness score'))
    accuracy_score = models.FloatField(default=1.0, help_text=_('Information accuracy score'))
    
    # Combined scores
    weighted_score = models.FloatField(default=1.0, help_text=_('Weighted combination of all scores'))
    final_rank = models.PositiveIntegerField(default=1, help_text=_('Final ranking position'))
    
    # Factor-specific scores
    medication_name_score = models.FloatField(default=1.0, help_text=_('Medication name match score'))
    generic_name_score = models.FloatField(default=1.0, help_text=_('Generic name match score'))
    active_ingredient_score = models.FloatField(default=1.0, help_text=_('Active ingredient match score'))
    side_effect_score = models.FloatField(default=1.0, help_text=_('Side effect relevance score'))
    interaction_score = models.FloatField(default=1.0, help_text=_('Drug interaction relevance score'))
    dosage_score = models.FloatField(default=1.0, help_text=_('Dosage information score'))
    
    # Usage statistics
    search_count = models.PositiveIntegerField(default=0, help_text=_('Number of times this item was searched'))
    click_count = models.PositiveIntegerField(default=0, help_text=_('Number of times this item was clicked'))
    conversion_count = models.PositiveIntegerField(default=0, help_text=_('Number of conversions from this item'))
    
    # Timestamps
    last_calculated = models.DateTimeField(auto_now=True, help_text=_('When ranking was last calculated'))
    last_searched = models.DateTimeField(null=True, blank=True, help_text=_('When this item was last searched'))
    
    class Meta:
        verbose_name = _('Search Ranking')
        verbose_name_plural = _('Search Rankings')
        db_table = 'search_rankings'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['weighted_score']),
            models.Index(fields=['final_rank']),
            models.Index(fields=['healthcare_score']),
            models.Index(fields=['search_count']),
        ]
        ordering = ['-weighted_score', '-healthcare_score']
        unique_together = ['content_type', 'object_id']
    
    def __str__(self):
        return f"{self.content_type}:{self.object_id} (Score: {self.weighted_score:.2f})"
    
    @classmethod
    def calculate_ranking_for_medication(cls, medication):
        """Calculate comprehensive ranking for a medication."""
        # Get or create ranking object
        ranking, created = cls.objects.get_or_create(
            content_type='medication',
            object_id=medication.id
        )
        
        # Calculate individual scores
        ranking.medication_name_score = cls._calculate_name_score(medication)
        ranking.generic_name_score = cls._calculate_generic_name_score(medication)
        ranking.active_ingredient_score = cls._calculate_ingredient_score(medication)
        ranking.side_effect_score = cls._calculate_side_effect_score(medication)
        ranking.interaction_score = cls._calculate_interaction_score(medication)
        ranking.dosage_score = cls._calculate_dosage_score(medication)
        
        # Calculate composite scores
        ranking.healthcare_score = cls._calculate_healthcare_score(ranking)
        ranking.popularity_score = cls._calculate_popularity_score(ranking)
        ranking.recency_score = cls._calculate_recency_score(medication)
        ranking.completeness_score = cls._calculate_completeness_score(medication)
        ranking.accuracy_score = cls._calculate_accuracy_score(medication)
        
        # Calculate weighted score
        ranking.weighted_score = cls._calculate_weighted_score(ranking)
        
        ranking.save()
        
        # Update final rank
        cls._update_final_ranks()
        
        return ranking
    
    @classmethod
    def _calculate_name_score(cls, medication):
        """Calculate score based on medication name completeness."""
        score = 1.0
        
        if medication.name:
            score += 0.5
        
        if medication.brand_name:
            score += 0.3
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_generic_name_score(cls, medication):
        """Calculate score based on generic name availability."""
        score = 1.0
        
        if medication.generic_name:
            score += 0.5
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_ingredient_score(cls, medication):
        """Calculate score based on active ingredients information."""
        score = 1.0
        
        if medication.active_ingredients:
            ingredients = medication.active_ingredients.split(',')
            score += min(len(ingredients) * 0.2, 1.0)
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_side_effect_score(cls, medication):
        """Calculate score based on side effects information."""
        score = 1.0
        
        if hasattr(medication, 'content') and medication.content:
            side_effects_count = sum(1 for block in medication.content if block.block_type == 'side_effects')
            score += min(side_effects_count * 0.3, 2.0)
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_interaction_score(cls, medication):
        """Calculate score based on drug interactions information."""
        score = 1.0
        
        if hasattr(medication, 'content') and medication.content:
            interactions_count = sum(1 for block in medication.content if block.block_type == 'interactions')
            score += min(interactions_count * 0.3, 2.0)
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_dosage_score(cls, medication):
        """Calculate score based on dosage information."""
        score = 1.0
        
        if hasattr(medication, 'content') and medication.content:
            dosage_count = sum(1 for block in medication.content if block.block_type == 'dosage')
            score += min(dosage_count * 0.4, 2.0)
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_healthcare_score(cls, ranking):
        """Calculate healthcare-specific relevance score."""
        # Weighted average of healthcare-relevant factors
        weights = {
            'medication_name': 0.25,
            'generic_name': 0.20,
            'active_ingredient': 0.20,
            'side_effect': 0.15,
            'interaction': 0.15,
            'dosage': 0.05,
        }
        
        score = (
            ranking.medication_name_score * weights['medication_name'] +
            ranking.generic_name_score * weights['generic_name'] +
            ranking.active_ingredient_score * weights['active_ingredient'] +
            ranking.side_effect_score * weights['side_effect'] +
            ranking.interaction_score * weights['interaction'] +
            ranking.dosage_score * weights['dosage']
        )
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_popularity_score(cls, ranking):
        """Calculate popularity-based score."""
        score = 1.0
        
        # Search count factor
        if ranking.search_count > 0:
            score += min(ranking.search_count / 100.0, 2.0)
        
        # Click count factor
        if ranking.click_count > 0:
            score += min(ranking.click_count / 50.0, 1.5)
        
        # Conversion factor
        if ranking.conversion_count > 0:
            score += min(ranking.conversion_count / 10.0, 1.0)
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_recency_score(cls, medication):
        """Calculate recency-based score."""
        score = 1.0
        
        # Boost for recently updated medications
        if hasattr(medication, 'updated_at'):
            days_since_update = (timezone.now() - medication.updated_at).days
            if days_since_update < 30:
                score += 0.5
            elif days_since_update < 90:
                score += 0.3
            elif days_since_update < 365:
                score += 0.1
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_completeness_score(cls, medication):
        """Calculate content completeness score."""
        score = 1.0
        completeness_factors = 0
        total_factors = 0
        
        # Check various completeness factors
        if medication.name:
            completeness_factors += 1
        total_factors += 1
        
        if medication.generic_name:
            completeness_factors += 1
        total_factors += 1
        
        if medication.active_ingredients:
            completeness_factors += 1
        total_factors += 1
        
        if medication.description:
            completeness_factors += 1
        total_factors += 1
        
        if hasattr(medication, 'content') and medication.content:
            completeness_factors += 1
        total_factors += 1
        
        # Calculate completeness percentage
        if total_factors > 0:
            completeness_percentage = completeness_factors / total_factors
            score += completeness_percentage * 3.0
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_accuracy_score(cls, medication):
        """Calculate information accuracy score."""
        score = 1.0
        
        # This would typically involve more complex logic
        # For now, we'll use a basic scoring based on data quality
        
        # Check for required fields
        if medication.name and len(medication.name.strip()) > 0:
            score += 0.5
        
        if medication.generic_name and len(medication.generic_name.strip()) > 0:
            score += 0.3
        
        if medication.active_ingredients and len(medication.active_ingredients.strip()) > 0:
            score += 0.2
        
        return min(score, 5.0)
    
    @classmethod
    def _calculate_weighted_score(cls, ranking):
        """Calculate final weighted score."""
        weights = {
            'healthcare': 0.40,
            'popularity': 0.25,
            'recency': 0.15,
            'completeness': 0.15,
            'accuracy': 0.05,
        }
        
        weighted_score = (
            ranking.healthcare_score * weights['healthcare'] +
            ranking.popularity_score * weights['popularity'] +
            ranking.recency_score * weights['recency'] +
            ranking.completeness_score * weights['completeness'] +
            ranking.accuracy_score * weights['accuracy']
        )
        
        return min(weighted_score, 5.0)
    
    @classmethod
    def _update_final_ranks(cls):
        """Update final ranking positions for all items."""
        rankings = cls.objects.order_by('-weighted_score', '-healthcare_score')
        
        for rank, ranking in enumerate(rankings, 1):
            ranking.final_rank = rank
            ranking.save(update_fields=['final_rank'])
    
    @classmethod
    def record_search(cls, content_type, object_id):
        """Record a search for ranking calculation."""
        try:
            ranking = cls.objects.get(content_type=content_type, object_id=object_id)
            ranking.search_count += 1
            ranking.last_searched = timezone.now()
            ranking.save(update_fields=['search_count', 'last_searched'])
        except cls.DoesNotExist:
            pass
    
    @classmethod
    def record_click(cls, content_type, object_id):
        """Record a click for ranking calculation."""
        try:
            ranking = cls.objects.get(content_type=content_type, object_id=object_id)
            ranking.click_count += 1
            ranking.save(update_fields=['click_count'])
        except cls.DoesNotExist:
            pass
    
    @classmethod
    def record_conversion(cls, content_type, object_id):
        """Record a conversion for ranking calculation."""
        try:
            ranking = cls.objects.get(content_type=content_type, object_id=object_id)
            ranking.conversion_count += 1
            ranking.save(update_fields=['conversion_count'])
        except cls.DoesNotExist:
            pass 


class SearchAnalytics(models.Model):
    """
    Search analytics model for tracking search behavior and performance.
    
    Provides comprehensive analytics for medication search queries, user behavior,
    and search result effectiveness.
    """
    
    # Analytics types
    class AnalyticsType(models.TextChoices):
        SEARCH_QUERY = 'search_query', _('Search Query')
        SEARCH_RESULT = 'search_result', _('Search Result')
        USER_BEHAVIOR = 'user_behavior', _('User Behavior')
        PERFORMANCE = 'performance', _('Performance')
        ERROR = 'error', _('Error')
    
    # Core fields
    analytics_type = models.CharField(
        max_length=20,
        choices=AnalyticsType.choices,
        help_text=_('Type of analytics event')
    )
    
    event_name = models.CharField(max_length=100, help_text=_('Name of the analytics event'))
    
    # Search context
    search_query = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Search query that triggered this event')
    )
    
    search_results_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of search results returned')
    )
    
    # User context
    user_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of the user who triggered this event')
    )
    
    session_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Session ID for tracking user sessions')
    )
    
    # Performance metrics
    response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Response time in milliseconds')
    )
    
    # Content context
    content_type = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('Type of content involved')
    )
    
    object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of the content object involved')
    )
    
    # Filter and facet information
    applied_filters = models.JSONField(
        default=dict,
        help_text=_('Filters applied to the search')
    )
    
    selected_facets = models.JSONField(
        default=dict,
        help_text=_('Facets selected by the user')
    )
    
    # User interaction
    clicked_result = models.BooleanField(
        default=False,
        help_text=_('Whether user clicked on a search result')
    )
    
    clicked_result_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of the clicked result')
    )
    
    time_on_page = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Time spent on page in seconds')
    )
    
    # Error tracking
    error_message = models.TextField(
        blank=True,
        help_text=_('Error message if applicable')
    )
    
    error_code = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('Error code if applicable')
    )
    
    # Metadata
    user_agent = models.TextField(
        blank=True,
        help_text=_('User agent string')
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address of the user')
    )
    
    referrer = models.URLField(
        blank=True,
        help_text=_('Referrer URL')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language of the search')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, help_text=_('When this analytics event occurred'))
    
    class Meta:
        verbose_name = _('Search Analytics')
        verbose_name_plural = _('Search Analytics')
        db_table = 'search_analytics'
        indexes = [
            models.Index(fields=['analytics_type']),
            models.Index(fields=['event_name']),
            models.Index(fields=['search_query']),
            models.Index(fields=['user_id']),
            models.Index(fields=['session_id']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['language']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.analytics_type}: {self.event_name} ({self.created_at})"
    
    @classmethod
    def record_search_query(cls, search_query, results_count, user_id=None, session_id=None, 
                          response_time=None, filters=None, facets=None, language='en-ZA'):
        """Record a search query event."""
        return cls.objects.create(
            analytics_type=cls.AnalyticsType.SEARCH_QUERY,
            event_name='search_performed',
            search_query=search_query,
            search_results_count=results_count,
            user_id=user_id,
            session_id=session_id,
            response_time_ms=response_time,
            applied_filters=filters or {},
            selected_facets=facets or {},
            language=language
        )
    
    @classmethod
    def record_result_click(cls, search_query, result_id, content_type, object_id, 
                          user_id=None, session_id=None, language='en-ZA'):
        """Record a search result click event."""
        return cls.objects.create(
            analytics_type=cls.AnalyticsType.SEARCH_RESULT,
            event_name='result_clicked',
            search_query=search_query,
            user_id=user_id,
            session_id=session_id,
            content_type=content_type,
            object_id=object_id,
            clicked_result=True,
            clicked_result_id=result_id,
            language=language
        )
    
    @classmethod
    def record_user_behavior(cls, event_name, user_id=None, session_id=None, 
                           content_type=None, object_id=None, language='en-ZA'):
        """Record user behavior events."""
        return cls.objects.create(
            analytics_type=cls.AnalyticsType.USER_BEHAVIOR,
            event_name=event_name,
            user_id=user_id,
            session_id=session_id,
            content_type=content_type,
            object_id=object_id,
            language=language
        )
    
    @classmethod
    def record_performance(cls, event_name, response_time, user_id=None, session_id=None):
        """Record performance metrics."""
        return cls.objects.create(
            analytics_type=cls.AnalyticsType.PERFORMANCE,
            event_name=event_name,
            user_id=user_id,
            session_id=session_id,
            response_time_ms=response_time
        )
    
    @classmethod
    def record_error(cls, event_name, error_message, error_code=None, user_id=None, session_id=None):
        """Record error events."""
        return cls.objects.create(
            analytics_type=cls.AnalyticsType.ERROR,
            event_name=event_name,
            user_id=user_id,
            session_id=session_id,
            error_message=error_message,
            error_code=error_code
        )
    
    @classmethod
    def get_search_statistics(cls, days=30, language='en-ZA'):
        """Get search statistics for the specified period."""
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get search queries
        search_queries = cls.objects.filter(
            analytics_type=cls.AnalyticsType.SEARCH_QUERY,
            created_at__range=(start_date, end_date),
            language=language
        )
        
        # Get result clicks
        result_clicks = cls.objects.filter(
            analytics_type=cls.AnalyticsType.SEARCH_RESULT,
            created_at__range=(start_date, end_date),
            language=language
        )
        
        # Calculate statistics
        total_searches = search_queries.count()
        total_clicks = result_clicks.count()
        click_through_rate = (total_clicks / total_searches * 100) if total_searches > 0 else 0
        
        # Average response time
        avg_response_time = search_queries.aggregate(
            avg_time=models.Avg('response_time_ms')
        )['avg_time'] or 0
        
        # Popular search queries
        popular_queries = search_queries.values('search_query').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        # Popular clicked results
        popular_results = result_clicks.values('content_type', 'object_id').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]
        
        return {
            'total_searches': total_searches,
            'total_clicks': total_clicks,
            'click_through_rate': round(click_through_rate, 2),
            'avg_response_time': round(avg_response_time, 2),
            'popular_queries': list(popular_queries),
            'popular_results': list(popular_results),
            'period_days': days,
            'language': language
        }
    
    @classmethod
    def get_user_search_history(cls, user_id, limit=50):
        """Get search history for a specific user."""
        return cls.objects.filter(
            user_id=user_id,
            analytics_type__in=[cls.AnalyticsType.SEARCH_QUERY, cls.AnalyticsType.SEARCH_RESULT]
        ).order_by('-created_at')[:limit]
    
    @classmethod
    def get_session_analytics(cls, session_id):
        """Get analytics for a specific session."""
        return cls.objects.filter(
            session_id=session_id
        ).order_by('created_at')


class SearchPerformance(models.Model):
    """
    Search performance tracking model for monitoring search system performance.
    
    Tracks response times, throughput, and system health metrics.
    """
    
    # Performance metrics
    avg_response_time_ms = models.FloatField(help_text=_('Average response time in milliseconds'))
    max_response_time_ms = models.FloatField(help_text=_('Maximum response time in milliseconds'))
    min_response_time_ms = models.FloatField(help_text=_('Minimum response time in milliseconds'))
    
    # Throughput metrics
    requests_per_minute = models.FloatField(help_text=_('Requests per minute'))
    requests_per_hour = models.FloatField(help_text=_('Requests per hour'))
    
    # Error metrics
    error_rate = models.FloatField(help_text=_('Error rate as percentage'))
    total_errors = models.PositiveIntegerField(help_text=_('Total number of errors'))
    total_requests = models.PositiveIntegerField(help_text=_('Total number of requests'))
    
    # Cache metrics
    cache_hit_rate = models.FloatField(help_text=_('Cache hit rate as percentage'))
    cache_misses = models.PositiveIntegerField(help_text=_('Number of cache misses'))
    cache_hits = models.PositiveIntegerField(help_text=_('Number of cache hits'))
    
    # System metrics
    memory_usage_mb = models.FloatField(help_text=_('Memory usage in MB'))
    cpu_usage_percent = models.FloatField(help_text=_('CPU usage percentage'))
    
    # Timestamp
    recorded_at = models.DateTimeField(auto_now_add=True, help_text=_('When these metrics were recorded'))
    
    class Meta:
        verbose_name = _('Search Performance')
        verbose_name_plural = _('Search Performance Metrics')
        db_table = 'search_performance'
        indexes = [
            models.Index(fields=['recorded_at']),
        ]
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"Performance at {self.recorded_at} (Avg: {self.avg_response_time_ms:.2f}ms)"
    
    @classmethod
    def record_performance_metrics(cls, avg_response_time, max_response_time, min_response_time,
                                 requests_per_minute, requests_per_hour, error_rate, total_errors,
                                 total_requests, cache_hit_rate, cache_misses, cache_hits,
                                 memory_usage, cpu_usage):
        """Record performance metrics."""
        return cls.objects.create(
            avg_response_time_ms=avg_response_time,
            max_response_time_ms=max_response_time,
            min_response_time_ms=min_response_time,
            requests_per_minute=requests_per_minute,
            requests_per_hour=requests_per_hour,
            error_rate=error_rate,
            total_errors=total_errors,
            total_requests=total_requests,
            cache_hit_rate=cache_hit_rate,
            cache_misses=cache_misses,
            cache_hits=cache_hits,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )
    
    @classmethod
    def get_performance_trends(cls, hours=24):
        """Get performance trends over the specified period."""
        from django.utils import timezone
        from datetime import timedelta
        
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = cls.objects.filter(
            recorded_at__range=(start_time, end_time)
        ).order_by('recorded_at')
        
        return {
            'avg_response_times': list(metrics.values_list('avg_response_time_ms', flat=True)),
            'error_rates': list(metrics.values_list('error_rate', flat=True)),
            'cache_hit_rates': list(metrics.values_list('cache_hit_rate', flat=True)),
            'timestamps': list(metrics.values_list('recorded_at', flat=True)),
            'period_hours': hours
        } 


class MultilingualSearchIndex(models.Model):
    """
    Multilingual search index model for English and Afrikaans content.
    
    Provides language-specific search capabilities with translation support.
    """
    
    # Language choices
    class Language(models.TextChoices):
        ENGLISH = 'en-ZA', _('English (South Africa)')
        AFRIKAANS = 'af-ZA', _('Afrikaans (South Africa)')
    
    # Core fields
    content_type = models.CharField(max_length=50, help_text=_('Type of content'))
    object_id = models.PositiveIntegerField(help_text=_('ID of the content object'))
    language = models.CharField(
        max_length=10,
        choices=Language.choices,
        help_text=_('Language of the content')
    )
    
    # Searchable content
    title = models.CharField(max_length=255, help_text=_('Translated title'))
    content = models.TextField(help_text=_('Translated content'))
    keywords = models.TextField(blank=True, help_text=_('Translated keywords'))
    
    # Healthcare-specific translations
    medication_name = models.CharField(max_length=255, blank=True, help_text=_('Translated medication name'))
    generic_name = models.CharField(max_length=255, blank=True, help_text=_('Translated generic name'))
    active_ingredients = models.TextField(blank=True, help_text=_('Translated active ingredients'))
    side_effects = models.TextField(blank=True, help_text=_('Translated side effects'))
    interactions = models.TextField(blank=True, help_text=_('Translated drug interactions'))
    dosage_info = models.TextField(blank=True, help_text=_('Translated dosage information'))
    
    # Translation metadata
    is_auto_translated = models.BooleanField(
        default=False,
        help_text=_('Whether this content was auto-translated')
    )
    
    translation_confidence = models.FloatField(
        default=1.0,
        help_text=_('Confidence score for translation quality (0-1)')
    )
    
    original_language = models.CharField(
        max_length=10,
        choices=Language.choices,
        help_text=_('Original language of the content')
    )
    
    # Search relevance
    relevance_score = models.FloatField(default=1.0, help_text=_('Language-specific relevance score'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_translated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Multilingual Search Index')
        verbose_name_plural = _('Multilingual Search Indexes')
        db_table = 'multilingual_search_index'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['language']),
            models.Index(fields=['original_language']),
            models.Index(fields=['relevance_score']),
            models.Index(fields=['is_auto_translated']),
        ]
        ordering = ['-relevance_score', '-updated_at']
        unique_together = ['content_type', 'object_id', 'language']
    
    def __str__(self):
        return f"{self.content_type}:{self.object_id} ({self.language})"
    
    @classmethod
    def index_medication_multilingual(cls, medication, original_language='en-ZA'):
        """Index a medication in multiple languages."""
        # Index in original language
        cls._index_medication_language(medication, original_language, is_original=True)
        
        # Index in other language
        other_language = 'af-ZA' if original_language == 'en-ZA' else 'en-ZA'
        cls._index_medication_language(medication, other_language, is_original=False)
    
    @classmethod
    def _index_medication_language(cls, medication, language, is_original=False):
        """Index medication content for a specific language."""
        if is_original:
            # Use original content
            title = medication.name
            content = cls._extract_searchable_content(medication)
            medication_name = medication.name
            generic_name = medication.generic_name or ''
            active_ingredients = medication.active_ingredients or ''
            side_effects = cls._extract_side_effects(medication)
            interactions = cls._extract_interactions(medication)
            dosage_info = cls._extract_dosage_info(medication)
            is_auto_translated = False
            translation_confidence = 1.0
        else:
            # Translate content
            title = cls._translate_text(medication.name, language)
            content = cls._translate_text(cls._extract_searchable_content(medication), language)
            medication_name = cls._translate_text(medication.name, language)
            generic_name = cls._translate_text(medication.generic_name or '', language)
            active_ingredients = cls._translate_text(medication.active_ingredients or '', language)
            side_effects = cls._translate_text(cls._extract_side_effects(medication), language)
            interactions = cls._translate_text(cls._extract_interactions(medication), language)
            dosage_info = cls._translate_text(cls._extract_dosage_info(medication), language)
            is_auto_translated = True
            translation_confidence = 0.8  # Default confidence for auto-translation
        
        # Create or update index entry
        cls.objects.update_or_create(
            content_type='medication',
            object_id=medication.id,
            language=language,
            defaults={
                'title': title,
                'content': content,
                'medication_name': medication_name,
                'generic_name': generic_name,
                'active_ingredients': active_ingredients,
                'side_effects': side_effects,
                'interactions': interactions,
                'dosage_info': dosage_info,
                'is_auto_translated': is_auto_translated,
                'translation_confidence': translation_confidence,
                'original_language': 'en-ZA' if is_original else language,
                'relevance_score': cls._calculate_language_relevance(medication, language),
                'last_translated': timezone.now() if not is_original else None,
            }
        )
    
    @classmethod
    def _translate_text(cls, text, target_language):
        """Translate text to target language."""
        if not text:
            return ''
        
        # This would integrate with a translation service
        # For now, we'll use a simple mapping for common terms
        
        if target_language == 'af-ZA':
            # Simple English to Afrikaans mapping for common medical terms
            translations = {
                'tablet': 'tablet',
                'capsule': 'kapsule',
                'liquid': 'vloeistof',
                'injection': 'inspuiting',
                'cream': 'room',
                'ointment': 'salf',
                'drops': 'druppels',
                'side effects': 'newe-effekte',
                'drug interactions': 'medikasie-interaksies',
                'dosage': 'dosis',
                'prescription': 'voorskrif',
                'generic': 'generiese',
                'brand': 'handelsmerk',
                'active ingredients': 'aktiewe bestanddele',
                'warning': 'waarskuwing',
                'precaution': 'voorsorgmaatreël',
                'contraindication': 'kontra-indikasie',
            }
            
            translated_text = text
            for english, afrikaans in translations.items():
                translated_text = translated_text.replace(english.lower(), afrikaans)
            
            return translated_text
        
        return text  # Return original if no translation needed
    
    @classmethod
    def _extract_searchable_content(cls, medication):
        """Extract searchable content from medication."""
        content_parts = []
        
        if medication.description:
            content_parts.append(medication.description)
        
        if medication.active_ingredients:
            content_parts.append(medication.active_ingredients)
        
        if hasattr(medication, 'content') and medication.content:
            content_parts.append(cls._extract_streamfield_text(medication.content))
        
        return ' '.join(content_parts)
    
    @classmethod
    def _extract_streamfield_text(cls, streamfield_data):
        """Extract plain text from StreamField data."""
        if not streamfield_data:
            return ''
        
        text_parts = []
        for block in streamfield_data:
            if hasattr(block, 'value'):
                if isinstance(block.value, dict):
                    for key, value in block.value.items():
                        if isinstance(value, str):
                            text_parts.append(value)
                elif isinstance(block.value, str):
                    text_parts.append(block.value)
        
        return ' '.join(text_parts)
    
    @classmethod
    def _extract_side_effects(cls, medication):
        """Extract side effects information."""
        if not hasattr(medication, 'content') or not medication.content:
            return ''
        
        side_effects = []
        for block in medication.content:
            if block.block_type == 'side_effects':
                if hasattr(block.value, 'effect_name'):
                    side_effects.append(block.value.effect_name)
        
        return ', '.join(side_effects)
    
    @classmethod
    def _extract_interactions(cls, medication):
        """Extract drug interactions information."""
        if not hasattr(medication, 'content') or not medication.content:
            return ''
        
        interactions = []
        for block in medication.content:
            if block.block_type == 'interactions':
                if hasattr(block.value, 'interacting_medication'):
                    interactions.append(block.value.interacting_medication)
        
        return ', '.join(interactions)
    
    @classmethod
    def _extract_dosage_info(cls, medication):
        """Extract dosage information."""
        if not hasattr(medication, 'content') or not medication.content:
            return ''
        
        dosage_info = []
        for block in medication.content:
            if block.block_type == 'dosage':
                if hasattr(block.value, 'amount') and hasattr(block.value, 'unit'):
                    dosage_info.append(f"{block.value.amount} {block.value.unit}")
        
        return ', '.join(dosage_info)
    
    @classmethod
    def _calculate_language_relevance(cls, medication, language):
        """Calculate language-specific relevance score."""
        score = 1.0
        
        # Boost for content in the user's preferred language
        if language == 'en-ZA':
            score += 0.2  # English is primary language
        elif language == 'af-ZA':
            score += 0.1  # Afrikaans is secondary language
        
        # Boost for complete translations
        if hasattr(medication, 'content') and medication.content:
            score += 0.3
        
        return min(score, 5.0)
    
    @classmethod
    def search_multilingual(cls, query, language='en-ZA', limit=20):
        """Search content in a specific language."""
        queryset = cls.objects.filter(
            language=language
        ).filter(
            models.Q(title__icontains=query) |
            models.Q(content__icontains=query) |
            models.Q(medication_name__icontains=query) |
            models.Q(generic_name__icontains=query) |
            models.Q(active_ingredients__icontains=query)
        ).order_by('-relevance_score', '-translation_confidence')
        return queryset[:limit]
    
    @classmethod
    def get_translation_status(cls, content_type, object_id):
        """Get translation status for a content object."""
        translations = cls.objects.filter(
            content_type=content_type,
            object_id=object_id
        )
        
        status = {
            'en-ZA': {'exists': False, 'auto_translated': False, 'confidence': 0.0},
            'af-ZA': {'exists': False, 'auto_translated': False, 'confidence': 0.0},
        }
        
        for translation in translations:
            status[translation.language] = {
                'exists': True,
                'auto_translated': translation.is_auto_translated,
                'confidence': translation.translation_confidence,
                'last_updated': translation.updated_at,
            }
        
        return status


class SearchTranslation(models.Model):
    """
    Search translation model for managing translation mappings and quality.
    
    Provides translation memory and quality control for search content.
    """
    
    # Translation types
    class TranslationType(models.TextChoices):
        MEDICATION_NAME = 'medication_name', _('Medication Name')
        GENERIC_NAME = 'generic_name', _('Generic Name')
        ACTIVE_INGREDIENT = 'active_ingredient', _('Active Ingredient')
        SIDE_EFFECT = 'side_effect', _('Side Effect')
        DRUG_INTERACTION = 'drug_interaction', _('Drug Interaction')
        DOSAGE_INFO = 'dosage_info', _('Dosage Information')
        CATEGORY = 'category', _('Category')
        WARNING = 'warning', _('Warning')
        INSTRUCTION = 'instruction', _('Instruction')
    
    # Core fields
    source_language = models.CharField(max_length=10, help_text=_('Source language'))
    target_language = models.CharField(max_length=10, help_text=_('Target language'))
    translation_type = models.CharField(
        max_length=30,
        choices=TranslationType.choices,
        help_text=_('Type of translation')
    )
    
    # Translation content
    source_text = models.TextField(help_text=_('Source text to translate'))
    target_text = models.TextField(help_text=_('Translated text'))
    
    # Quality and usage
    confidence_score = models.FloatField(
        default=1.0,
        help_text=_('Confidence score for translation quality (0-1)')
    )
    
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of times this translation was used')
    )
    
    # Approval and review
    is_approved = models.BooleanField(
        default=False,
        help_text=_('Whether this translation has been approved')
    )
    
    approved_by = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('ID of user who approved this translation')
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this translation was approved')
    )
    
    # Context and metadata
    context = models.TextField(
        blank=True,
        help_text=_('Context information for the translation')
    )
    
    notes = models.TextField(
        blank=True,
        help_text=_('Notes about the translation')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Search Translation')
        verbose_name_plural = _('Search Translations')
        db_table = 'search_translations'
        indexes = [
            models.Index(fields=['source_language', 'target_language']),
            models.Index(fields=['translation_type']),
            models.Index(fields=['confidence_score']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['usage_count']),
        ]
        ordering = ['-confidence_score', '-usage_count']
        unique_together = ['source_language', 'target_language', 'translation_type', 'source_text']
    
    def __str__(self):
        return f"{self.source_text} → {self.target_text} ({self.translation_type})"
    
    @classmethod
    def get_translation(cls, source_text, source_language, target_language, translation_type):
        """Get existing translation for text."""
        try:
            translation = cls.objects.get(
                source_text__iexact=source_text,
                source_language=source_language,
                target_language=target_language,
                translation_type=translation_type,
                is_approved=True
            )
            
            # Update usage count
            translation.usage_count += 1
            translation.save(update_fields=['usage_count'])
            
            return translation.target_text
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_translation(cls, source_text, target_text, source_language, target_language, 
                         translation_type, confidence_score=1.0, context=''):
        """Create a new translation entry."""
        translation, created = cls.objects.get_or_create(
            source_text=source_text,
            source_language=source_language,
            target_language=target_language,
            translation_type=translation_type,
            defaults={
                'target_text': target_text,
                'confidence_score': confidence_score,
                'context': context,
            }
        )
        
        if not created:
            # Update existing translation if confidence is higher
            if confidence_score > translation.confidence_score:
                translation.target_text = target_text
                translation.confidence_score = confidence_score
                translation.context = context
                translation.save()
        
        return translation
    
    @classmethod
    def approve_translation(cls, translation_id, approved_by_user_id):
        """Approve a translation."""
        try:
            translation = cls.objects.get(id=translation_id)
            translation.is_approved = True
            translation.approved_by = approved_by_user_id
            translation.approved_at = timezone.now()
            translation.save()
            return translation
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def get_popular_translations(cls, source_language, target_language, limit=20):
        """Get popular translations for a language pair."""
        return cls.objects.filter(
            source_language=source_language,
            target_language=target_language,
            is_approved=True,
            usage_count__gt=0
        ).order_by('-usage_count', '-confidence_score')[:limit] 


class SearchPagination(models.Model):
    """
    Enhanced search pagination model for Wagtail 7.0.2 with healthcare-specific features.
    
    Provides advanced pagination capabilities with performance optimization and
    user experience enhancements.
    """
    
    # Pagination types
    class PaginationType(models.TextChoices):
        STANDARD = 'standard', _('Standard Pagination')
        INFINITE_SCROLL = 'infinite_scroll', _('Infinite Scroll')
        LOAD_MORE = 'load_more', _('Load More Button')
        CURSOR_BASED = 'cursor_based', _('Cursor-based Pagination')
        OFFSET_BASED = 'offset_based', _('Offset-based Pagination')
    
    # Core fields
    pagination_type = models.CharField(
        max_length=20,
        choices=PaginationType.choices,
        default=PaginationType.STANDARD,
        help_text=_('Type of pagination to use')
    )
    
    # Pagination settings
    items_per_page = models.PositiveIntegerField(
        default=10,
        help_text=_('Number of items per page')
    )
    
    max_pages = models.PositiveIntegerField(
        default=100,
        help_text=_('Maximum number of pages to show')
    )
    
    show_first_last = models.BooleanField(
        default=True,
        help_text=_('Whether to show first/last page links')
    )
    
    show_prev_next = models.BooleanField(
        default=True,
        help_text=_('Whether to show previous/next links')
    )
    
    # Performance settings
    cache_results = models.BooleanField(
        default=True,
        help_text=_('Whether to cache paginated results')
    )
    
    cache_timeout = models.PositiveIntegerField(
        default=300,
        help_text=_('Cache timeout in seconds')
    )
    
    # User experience settings
    show_page_numbers = models.BooleanField(
        default=True,
        help_text=_('Whether to show page numbers')
    )
    
    show_item_count = models.BooleanField(
        default=True,
        help_text=_('Whether to show total item count')
    )
    
    show_loading_indicator = models.BooleanField(
        default=True,
        help_text=_('Whether to show loading indicator')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for pagination labels')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Search Pagination')
        verbose_name_plural = _('Search Pagination Settings')
        db_table = 'search_pagination'
        indexes = [
            models.Index(fields=['pagination_type']),
            models.Index(fields=['language']),
        ]
        ordering = ['pagination_type', 'items_per_page']
    
    def __str__(self):
        return f"{self.pagination_type} - {self.items_per_page} items/page"
    
    @classmethod
    def get_pagination_settings(cls, pagination_type='standard', language='en-ZA'):
        """Get pagination settings for a specific type and language."""
        try:
            return cls.objects.get(
                pagination_type=pagination_type,
                language=language
            )
        except cls.DoesNotExist:
            # Return default settings
            return cls(
                pagination_type=pagination_type,
                language=language,
                items_per_page=10,
                max_pages=100,
                show_first_last=True,
                show_prev_next=True,
                cache_results=True,
                cache_timeout=300,
                show_page_numbers=True,
                show_item_count=True,
                show_loading_indicator=True
            )
    
    def get_cache_key(self, search_query, page_number):
        """Generate cache key for paginated results."""
        query_hash = hashlib.md5(search_query.encode()).hexdigest()
        return f"search_pagination_{self.pagination_type}_{query_hash}_{page_number}_{self.language}"
    
    def get_paginated_results(self, queryset, page_number, search_query=''):
        """Get paginated results with caching."""
        # Try to get from cache
        if self.cache_results:
            cached_results = cache.get(self.get_cache_key(search_query, page_number))
            if cached_results:
                return cached_results
        
        # Create paginator
        paginator = Paginator(queryset, self.items_per_page)
        
        try:
            page = paginator.page(page_number)
        except (ValueError, TypeError):
            page = paginator.page(1)
        
        # Prepare pagination data
        pagination_data = {
            'page': page,
            'paginator': paginator,
            'has_previous': page.has_previous(),
            'has_next': page.has_next(),
            'previous_page_number': page.previous_page_number() if page.has_previous() else None,
            'next_page_number': page.next_page_number() if page.has_next() else None,
            'num_pages': paginator.num_pages,
            'page_range': self._get_page_range(paginator, page_number),
            'show_first_last': self.show_first_last,
            'show_prev_next': self.show_prev_next,
            'show_page_numbers': self.show_page_numbers,
            'show_item_count': self.show_item_count,
            'show_loading_indicator': self.show_loading_indicator,
            'pagination_type': self.pagination_type,
        }
        
        # Cache results
        if self.cache_results:
            cache.set(self.get_cache_key(search_query, page_number), pagination_data, self.cache_timeout)
        
        return pagination_data
    
    def _get_page_range(self, paginator, current_page):
        """Get page range for pagination display."""
        if not self.show_page_numbers:
            return []
        
        num_pages = paginator.num_pages
        current_page = int(current_page)
        
        # Calculate page range
        if num_pages <= self.max_pages:
            return list(range(1, num_pages + 1))
        
        # Show pages around current page
        half_pages = self.max_pages // 2
        start_page = max(1, current_page - half_pages)
        end_page = min(num_pages, start_page + self.max_pages - 1)
        
        # Adjust if we're near the end
        if end_page - start_page < self.max_pages - 1:
            start_page = max(1, end_page - self.max_pages + 1)
        
        return list(range(start_page, end_page + 1))


class SearchResultCache(models.Model):
    """
    Search result cache model for storing and retrieving cached search results.
    
    Provides performance optimization for frequently searched queries.
    """
    
    # Cache types
    class CacheType(models.TextChoices):
        SEARCH_RESULTS = 'search_results', _('Search Results')
        FACET_RESULTS = 'facet_results', _('Facet Results')
        AUTocomplete_RESULTS = 'autocomplete_results', _('Autocomplete Results')
        SUGGESTION_RESULTS = 'suggestion_results', _('Suggestion Results')
    
    # Core fields
    cache_key = models.CharField(max_length=255, help_text=_('Unique cache key'))
    cache_type = models.CharField(
        max_length=30,
        choices=CacheType.choices,
        help_text=_('Type of cached data')
    )
    
    # Cached data
    cached_data = models.JSONField(help_text=_('Cached data in JSON format'))
    
    # Cache metadata
    search_query = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Original search query')
    )
    
    filters_applied = models.JSONField(
        default=dict,
        help_text=_('Filters applied to the search')
    )
    
    facets_selected = models.JSONField(
        default=dict,
        help_text=_('Facets selected for the search')
    )
    
    # Performance metrics
    hit_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of times this cache was hit')
    )
    
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this cache was last accessed')
    )
    
    # Cache settings
    expires_at = models.DateTimeField(help_text=_('When this cache expires'))
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language of the cached data')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Search Result Cache')
        verbose_name_plural = _('Search Result Caches')
        db_table = 'search_result_cache'
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['cache_type']),
            models.Index(fields=['search_query']),
            models.Index(fields=['language']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['hit_count']),
        ]
        ordering = ['-hit_count', '-last_accessed']
        unique_together = ['cache_key', 'language']
    
    def __str__(self):
        return f"{self.cache_type}: {self.cache_key} (Hits: {self.hit_count})"
    
    @classmethod
    def get_cached_results(cls, cache_key, cache_type, language='en-ZA'):
        """Get cached results if available and not expired."""
        try:
            cache_entry = cls.objects.get(
                cache_key=cache_key,
                cache_type=cache_type,
                language=language
            )
            
            # Check if expired
            if cache_entry.expires_at <= timezone.now():
                cache_entry.delete()
                return None
            
            # Update hit count and last accessed
            cache_entry.hit_count += 1
            cache_entry.last_accessed = timezone.now()
            cache_entry.save(update_fields=['hit_count', 'last_accessed'])
            
            return cache_entry.cached_data
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def set_cached_results(cls, cache_key, cache_type, data, search_query='', 
                          filters=None, facets=None, language='en-ZA', 
                          cache_duration_hours=1):
        """Set cached results with expiration."""
        from django.utils import timezone
        from datetime import timedelta
        
        expires_at = timezone.now() + timedelta(hours=cache_duration_hours)
        
        cls.objects.update_or_create(
            cache_key=cache_key,
            cache_type=cache_type,
            language=language,
            defaults={
                'cached_data': data,
                'search_query': search_query,
                'filters_applied': filters or {},
                'facets_selected': facets or {},
                'expires_at': expires_at,
            }
        )
    
    @classmethod
    def clear_expired_cache(cls):
        """Clear all expired cache entries."""
        cls.objects.filter(expires_at__lte=timezone.now()).delete()
    
    @classmethod
    def get_cache_statistics(cls):
        """Get cache statistics."""
        total_entries = cls.objects.count()
        active_entries = cls.objects.filter(expires_at__gt=timezone.now()).count()
        total_hits = cls.objects.aggregate(total=models.Sum('hit_count'))['total'] or 0
        
        # Most popular cache entries
        popular_entries = cls.objects.order_by('-hit_count')[:10]
        
        return {
            'total_entries': total_entries,
            'active_entries': active_entries,
            'expired_entries': total_entries - active_entries,
            'total_hits': total_hits,
            'popular_entries': list(popular_entries.values('cache_key', 'cache_type', 'hit_count')),
        }
    
    @property
    def is_expired(self):
        """Check if cache entry is expired."""
        return self.expires_at <= timezone.now()
    
    @property
    def age_hours(self):
        """Get age of cache entry in hours."""
        return (timezone.now() - self.created_at).total_seconds() / 3600


class SearchPerformanceOptimizer(models.Model):
    """
    Search performance optimizer model for Wagtail 7.0.2 with advanced caching and optimization.
    
    Provides comprehensive performance optimization for search operations including
    result caching, query optimization, and system monitoring.
    """
    
    # Optimization types
    class OptimizationType(models.TextChoices):
        QUERY_OPTIMIZATION = 'query_optimization', _('Query Optimization')
        RESULT_CACHING = 'result_caching', _('Result Caching')
        INDEX_OPTIMIZATION = 'index_optimization', _('Index Optimization')
        DATABASE_OPTIMIZATION = 'database_optimization', _('Database Optimization')
        CACHE_OPTIMIZATION = 'cache_optimization', _('Cache Optimization')
    
    # Core fields
    optimization_type = models.CharField(
        max_length=30,
        choices=OptimizationType.choices,
        help_text=_('Type of optimization')
    )
    
    # Performance settings
    enable_query_cache = models.BooleanField(
        default=True,
        help_text=_('Whether to enable query result caching')
    )
    
    enable_result_cache = models.BooleanField(
        default=True,
        help_text=_('Whether to enable search result caching')
    )
    
    enable_autocomplete_cache = models.BooleanField(
        default=True,
        help_text=_('Whether to enable autocomplete caching')
    )
    
    # Cache settings
    query_cache_timeout = models.PositiveIntegerField(
        default=300,
        help_text=_('Query cache timeout in seconds')
    )
    
    result_cache_timeout = models.PositiveIntegerField(
        default=600,
        help_text=_('Result cache timeout in seconds')
    )
    
    autocomplete_cache_timeout = models.PositiveIntegerField(
        default=1800,
        help_text=_('Autocomplete cache timeout in seconds')
    )
    
    # Database optimization
    enable_query_optimization = models.BooleanField(
        default=True,
        help_text=_('Whether to enable database query optimization')
    )
    
    max_query_time = models.PositiveIntegerField(
        default=5000,
        help_text=_('Maximum query execution time in milliseconds')
    )
    
    enable_slow_query_logging = models.BooleanField(
        default=True,
        help_text=_('Whether to log slow queries')
    )
    
    # Index optimization
    enable_index_optimization = models.BooleanField(
        default=True,
        help_text=_('Whether to enable search index optimization')
    )
    
    index_update_frequency = models.PositiveIntegerField(
        default=3600,
        help_text=_('Index update frequency in seconds')
    )
    
    # Performance monitoring
    enable_performance_monitoring = models.BooleanField(
        default=True,
        help_text=_('Whether to enable performance monitoring')
    )
    
    monitoring_interval = models.PositiveIntegerField(
        default=300,
        help_text=_('Performance monitoring interval in seconds')
    )
    
    # Multilingual support
    language = models.CharField(
        max_length=10,
        default='en-ZA',
        help_text=_('Language for optimization settings')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_optimized = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Search Performance Optimizer')
        verbose_name_plural = _('Search Performance Optimizers')
        db_table = 'search_performance_optimizer'
        indexes = [
            models.Index(fields=['optimization_type']),
            models.Index(fields=['language']),
            models.Index(fields=['last_optimized']),
        ]
        ordering = ['optimization_type', 'language']
        unique_together = ['optimization_type', 'language']
    
    def __str__(self):
        return f"{self.optimization_type} - {self.language}"
    
    @classmethod
    def get_optimization_settings(cls, optimization_type='query_optimization', language='en-ZA'):
        """Get optimization settings for a specific type and language."""
        try:
            return cls.objects.get(
                optimization_type=optimization_type,
                language=language
            )
        except cls.DoesNotExist:
            # Return default settings
            return cls(
                optimization_type=optimization_type,
                language=language,
                enable_query_cache=True,
                enable_result_cache=True,
                enable_autocomplete_cache=True,
                query_cache_timeout=300,
                result_cache_timeout=600,
                autocomplete_cache_timeout=1800,
                enable_query_optimization=True,
                max_query_time=5000,
                enable_slow_query_logging=True,
                enable_index_optimization=True,
                index_update_frequency=3600,
                enable_performance_monitoring=True,
                monitoring_interval=300
            )
    
    def optimize_search_query(self, queryset, search_query):
        """Optimize search query for better performance."""
        if not self.enable_query_optimization:
            return queryset
        
        # Add select_related for foreign keys
        if hasattr(queryset.model, 'medication'):
            queryset = queryset.select_related('medication')
        
        # Add prefetch_related for many-to-many relationships
        if hasattr(queryset.model, 'content'):
            queryset = queryset.prefetch_related('content')
        
        # Add database hints
        queryset = queryset.using('default')
        
        return queryset
    
    def get_cache_key(self, cache_type, search_query, filters=None, facets=None):
        """Generate cache key for different cache types."""
        import hashlib
        import json
        
        # Create cache key components
        key_components = [
            cache_type,
            search_query,
            json.dumps(filters or {}, sort_keys=True),
            json.dumps(facets or {}, sort_keys=True),
            self.language
        ]
        
        # Generate hash
        key_string = '|'.join(str(comp) for comp in key_components)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"search_{cache_type}_{key_hash}"
    
    def get_cache_timeout(self, cache_type):
        """Get cache timeout for specific cache type."""
        timeouts = {
            'query': self.query_cache_timeout,
            'result': self.result_cache_timeout,
            'autocomplete': self.autocomplete_cache_timeout,
        }
        return timeouts.get(cache_type, 300)
    
    def should_cache(self, cache_type):
        """Check if caching should be enabled for specific type."""
        cache_settings = {
            'query': self.enable_query_cache,
            'result': self.enable_result_cache,
            'autocomplete': self.enable_autocomplete_cache,
        }
        return cache_settings.get(cache_type, True)
    
    def log_slow_query(self, query, execution_time):
        """Log slow queries for analysis."""
        if not self.enable_slow_query_logging or execution_time <= self.max_query_time:
            return
        
        # Log slow query
        from django.core.cache import cache
        slow_query_key = f"slow_query_{hash(query)}"
        
        slow_query_data = {
            'query': query,
            'execution_time': execution_time,
            'timestamp': timezone.now().isoformat(),
            'language': self.language,
        }
        
        cache.set(slow_query_key, slow_query_data, 86400)  # Cache for 24 hours
    
    def update_optimization_timestamp(self):
        """Update last optimization timestamp."""
        self.last_optimized = timezone.now()
        self.save(update_fields=['last_optimized'])
    
    @classmethod
    def get_performance_metrics(cls):
        """Get overall performance metrics."""
        optimizers = cls.objects.all()
        
        metrics = {
            'total_optimizers': optimizers.count(),
            'active_optimizers': optimizers.filter(enable_performance_monitoring=True).count(),
            'cache_enabled': optimizers.filter(enable_result_cache=True).count(),
            'query_optimization_enabled': optimizers.filter(enable_query_optimization=True).count(),
            'index_optimization_enabled': optimizers.filter(enable_index_optimization=True).count(),
        }
        
        return metrics


class SearchHealthMonitor(models.Model):
    """
    Search health monitoring model for tracking system health and performance.
    
    Provides comprehensive monitoring of search system health, performance metrics,
    and automated health checks.
    """
    
    # Health status choices
    class HealthStatus(models.TextChoices):
        HEALTHY = 'healthy', _('Healthy')
        WARNING = 'warning', _('Warning')
        CRITICAL = 'critical', _('Critical')
        OFFLINE = 'offline', _('Offline')
    
    # Monitor types
    class MonitorType(models.TextChoices):
        SEARCH_PERFORMANCE = 'search_performance', _('Search Performance')
        CACHE_HEALTH = 'cache_health', _('Cache Health')
        DATABASE_HEALTH = 'database_health', _('Database Health')
        INDEX_HEALTH = 'index_health', _('Index Health')
        SYSTEM_RESOURCES = 'system_resources', _('System Resources')
    
    # Core fields
    monitor_type = models.CharField(
        max_length=30,
        choices=MonitorType.choices,
        help_text=_('Type of health monitor')
    )
    
    health_status = models.CharField(
        max_length=20,
        choices=HealthStatus.choices,
        default=HealthStatus.HEALTHY,
        help_text=_('Current health status')
    )
    
    # Performance metrics
    response_time_ms = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Average response time in milliseconds')
    )
    
    error_rate = models.FloatField(
        default=0.0,
        help_text=_('Error rate as percentage')
    )
    
    throughput = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Requests per second')
    )
    
    # System metrics
    cpu_usage = models.FloatField(
        null=True,
        blank=True,
        help_text=_('CPU usage percentage')
    )
    
    memory_usage = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Memory usage percentage')
    )
    
    disk_usage = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Disk usage percentage')
    )
    
    # Health check details
    last_check = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the last health check was performed')
    )
    
    check_interval = models.PositiveIntegerField(
        default=300,
        help_text=_('Health check interval in seconds')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this monitor is active')
    )
    
    # Alert settings
    enable_alerts = models.BooleanField(
        default=True,
        help_text=_('Whether to enable health alerts')
    )
    
    alert_threshold = models.FloatField(
        default=80.0,
        help_text=_('Alert threshold percentage')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Search Health Monitor')
        verbose_name_plural = _('Search Health Monitors')
        db_table = 'search_health_monitor'
        indexes = [
            models.Index(fields=['monitor_type']),
            models.Index(fields=['health_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_check']),
        ]
        ordering = ['monitor_type', '-last_check']
        unique_together = ['monitor_type']
    
    def __str__(self):
        return f"{self.monitor_type} - {self.health_status}"
    
    @classmethod
    def perform_health_check(cls, monitor_type):
        """Perform health check for specific monitor type."""
        try:
            monitor = cls.objects.get(monitor_type=monitor_type, is_active=True)
            
            # Perform health check based on type
            if monitor_type == cls.MonitorType.SEARCH_PERFORMANCE:
                health_data = cls._check_search_performance()
            elif monitor_type == cls.MonitorType.CACHE_HEALTH:
                health_data = cls._check_cache_health()
            elif monitor_type == cls.MonitorType.DATABASE_HEALTH:
                health_data = cls._check_database_health()
            elif monitor_type == cls.MonitorType.INDEX_HEALTH:
                health_data = cls._check_index_health()
            elif monitor_type == cls.MonitorType.SYSTEM_RESOURCES:
                health_data = cls._check_system_resources()
            else:
                health_data = {'status': cls.HealthStatus.HEALTHY}
            
            # Update monitor with health data
            monitor.health_status = health_data.get('status', cls.HealthStatus.HEALTHY)
            monitor.response_time_ms = health_data.get('response_time')
            monitor.error_rate = health_data.get('error_rate', 0.0)
            monitor.throughput = health_data.get('throughput')
            monitor.cpu_usage = health_data.get('cpu_usage')
            monitor.memory_usage = health_data.get('memory_usage')
            monitor.disk_usage = health_data.get('disk_usage')
            monitor.last_check = timezone.now()
            monitor.save()
            
            # Send alert if needed
            if monitor.enable_alerts and monitor.health_status in [cls.HealthStatus.WARNING, cls.HealthStatus.CRITICAL]:
                cls._send_health_alert(monitor)
            
            return monitor
            
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def _check_search_performance(cls):
        """Check search performance health."""
        # This would implement actual performance checks
        # For now, return mock data
        return {
            'status': cls.HealthStatus.HEALTHY,
            'response_time': 150.0,
            'error_rate': 0.1,
            'throughput': 50.0,
        }
    
    @classmethod
    def _check_cache_health(cls):
        """Check cache health."""
        # This would implement actual cache health checks
        return {
            'status': cls.HealthStatus.HEALTHY,
            'response_time': 10.0,
            'error_rate': 0.0,
        }
    
    @classmethod
    def _check_database_health(cls):
        """Check database health."""
        # This would implement actual database health checks
        return {
            'status': cls.HealthStatus.HEALTHY,
            'response_time': 50.0,
            'error_rate': 0.0,
        }
    
    @classmethod
    def _check_index_health(cls):
        """Check search index health."""
        # This would implement actual index health checks
        return {
            'status': cls.HealthStatus.HEALTHY,
            'response_time': 25.0,
            'error_rate': 0.0,
        }
    
    @classmethod
    def _check_system_resources(cls):
        """Check system resource usage."""
        # This would implement actual system resource checks
        return {
            'status': cls.HealthStatus.HEALTHY,
            'cpu_usage': 45.0,
            'memory_usage': 60.0,
            'disk_usage': 30.0,
        }
    
    @classmethod
    def _send_health_alert(cls, monitor):
        """Send health alert."""
        # This would implement actual alert sending
        # For now, just log the alert
        print(f"Health Alert: {monitor.monitor_type} is {monitor.health_status}")
    
    @classmethod
    def get_overall_health_status(cls):
        """Get overall system health status."""
        monitors = cls.objects.filter(is_active=True)
        
        if not monitors.exists():
            return cls.HealthStatus.HEALTHY
        
        # Check if any monitor is critical
        if monitors.filter(health_status=cls.HealthStatus.CRITICAL).exists():
            return cls.HealthStatus.CRITICAL
        
        # Check if any monitor is warning
        if monitors.filter(health_status=cls.HealthStatus.WARNING).exists():
            return cls.HealthStatus.WARNING
        
        return cls.HealthStatus.HEALTHY
    
    @property
    def needs_attention(self):
        """Check if this monitor needs attention."""
        return self.health_status in [self.HealthStatus.WARNING, self.HealthStatus.CRITICAL]
    
    @property
    def is_healthy(self):
        """Check if this monitor is healthy."""
        return self.health_status == self.HealthStatus.HEALTHY