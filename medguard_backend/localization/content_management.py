"""
MedGuard SA Localization Content Management

This module provides comprehensive localization features for the MedGuard SA platform,
leveraging Wagtail 7.0.2's enhanced translation capabilities for medication pages
and healthcare content management.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.translation import gettext_lazy as _, activate, get_language
from django.utils import timezone
from wagtail.models import Page, Locale
from wagtail.images.models import Image
from wagtail.documents.models import Document
from wagtail.snippets.models import register_snippet
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.blocks import StreamBlock, StructBlock, CharBlock, RichTextBlock, ChoiceBlock
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
import json
import re

logger = logging.getLogger(__name__)

# =============================================================================
# 1. WAGTAIL 7.0.2 IMPROVED TRANSLATION COPYING FOR MEDICATION PAGES
# =============================================================================

class MedicationTranslationManager:
    """
    Enhanced translation manager for medication pages using Wagtail 7.0.2 features.
    
    This class provides improved translation copying capabilities specifically
    designed for medication content, including dosage information, side effects,
    and medical terminology.
    """
    
    def __init__(self):
        self.supported_languages = [lang[0] for lang in settings.LANGUAGES]
        self.medical_terms_mapping = self._load_medical_terms_mapping()
    
    def _load_medical_terms_mapping(self) -> Dict[str, Dict[str, str]]:
        """
        Load medical terminology mappings for different languages.
        
        Returns:
            Dictionary mapping language codes to medical term translations
        """
        return {
            'en-ZA': {
                'dosage': 'Dosage',
                'side_effects': 'Side Effects',
                'interactions': 'Drug Interactions',
                'contraindications': 'Contraindications',
                'precautions': 'Precautions',
                'storage': 'Storage Instructions',
                'administration': 'Administration',
                'frequency': 'Frequency',
                'duration': 'Duration',
                'strength': 'Strength',
                'form': 'Dosage Form',
                'route': 'Route of Administration',
            },
            'af-ZA': {
                'dosage': 'Dosering',
                'side_effects': 'Neweffekte',
                'interactions': 'Geneesmiddelinteraksies',
                'contraindications': 'Kontraindikasies',
                'precautions': 'Voorsorgmaatreëls',
                'storage': 'Berginginstruksies',
                'administration': 'Toediening',
                'frequency': 'Frekwensie',
                'duration': 'Duur',
                'strength': 'Sterkte',
                'form': 'Doseringsvorm',
                'route': 'Toedieningsroete',
            }
        }
    
    def copy_medication_page_translation(
        self, 
        source_page: Page, 
        target_locale: Locale,
        include_related_content: bool = True,
        preserve_structure: bool = True
    ) -> Page:
        """
        Copy a medication page to a new locale with enhanced translation features.
        
        Args:
            source_page: The source medication page to copy
            target_locale: The target locale for the translation
            include_related_content: Whether to copy related content (images, documents)
            preserve_structure: Whether to preserve the page hierarchy structure
            
        Returns:
            The newly created translated page
            
        Raises:
            ValidationError: If the translation cannot be created
        """
        try:
            with transaction.atomic():
                # Validate source page is a medication page
                if not self._is_medication_page(source_page):
                    raise ValidationError(_("Source page must be a medication page"))
                
                # Check if translation already exists
                existing_translation = source_page.get_translation(target_locale)
                if existing_translation:
                    logger.warning(f"Translation already exists for {source_page} in {target_locale}")
                    return existing_translation
                
                # Create the translated page
                translated_page = source_page.copy_for_translation(target_locale)
                
                # Enhanced content translation for medication-specific fields
                self._translate_medication_content(translated_page, target_locale)
                
                # Copy related content if requested
                if include_related_content:
                    self._copy_related_content(source_page, translated_page, target_locale)
                
                # Preserve structure if requested
                if preserve_structure:
                    self._preserve_page_structure(source_page, translated_page)
                
                # Save the translated page
                translated_page.save()
                
                # Update search index
                translated_page.update_index()
                
                logger.info(f"Successfully created translation for {source_page} in {target_locale}")
                return translated_page
                
        except Exception as e:
            logger.error(f"Failed to copy medication page translation: {e}")
            raise ValidationError(_("Failed to create medication page translation"))
    
    def _is_medication_page(self, page: Page) -> bool:
        """Check if a page is a medication-related page."""
        medication_page_types = [
            'medications.MedicationIndexPage',
            'medications.MedicationDetailPage',
            'medications.MedicationCategoryPage'
        ]
        return page.content_type.model_class().__name__ in [
            page_type.split('.')[-1] for page_type in medication_page_types
        ]
    
    def _translate_medication_content(self, page: Page, target_locale: Locale):
        """
        Translate medication-specific content using enhanced Wagtail 7.0.2 features.
        
        Args:
            page: The page to translate
            target_locale: The target locale
        """
        # Get the target language code
        target_language = target_locale.language_code
        
        # Translate StreamField content
        if hasattr(page, 'content') and page.content:
            translated_content = self._translate_streamfield_content(
                page.content, target_language
            )
            page.content = translated_content
        
        # Translate RichTextField content
        rich_text_fields = ['intro', 'description', 'additional_info', 'instructions']
        for field_name in rich_text_fields:
            if hasattr(page, field_name) and getattr(page, field_name):
                translated_text = self._translate_rich_text(
                    getattr(page, field_name), target_language
                )
                setattr(page, field_name, translated_text)
        
        # Translate page title and slug
        if hasattr(page, 'title'):
            page.title = self._translate_text(page.title, target_language)
        
        if hasattr(page, 'slug'):
            page.slug = self._generate_translated_slug(page.slug, target_language)
    
    def _translate_streamfield_content(self, content: StreamField, target_language: str) -> StreamField:
        """
        Translate StreamField content with medication-specific handling.
        
        Args:
            content: The StreamField content to translate
            target_language: The target language code
            
        Returns:
            Translated StreamField content
        """
        if not content:
            return content
        
        translated_blocks = []
        
        for block in content:
            translated_block = self._translate_stream_block(block, target_language)
            translated_blocks.append(translated_block)
        
        return translated_blocks
    
    def _translate_stream_block(self, block, target_language: str):
        """
        Translate a single StreamField block.
        
        Args:
            block: The block to translate
            target_language: The target language code
            
        Returns:
            Translated block
        """
        if hasattr(block, 'value'):
            # Handle StructBlock
            if isinstance(block.value, dict):
                translated_value = {}
                for key, value in block.value.items():
                    if isinstance(value, str):
                        translated_value[key] = self._translate_text(value, target_language)
                    elif isinstance(value, list):
                        translated_value[key] = [
                            self._translate_text(item, target_language) 
                            if isinstance(item, str) else item
                            for item in value
                        ]
                    else:
                        translated_value[key] = value
                block.value = translated_value
            # Handle simple text blocks
            elif isinstance(block.value, str):
                block.value = self._translate_text(block.value, target_language)
        
        return block
    
    def _translate_rich_text(self, rich_text: str, target_language: str) -> str:
        """
        Translate rich text content while preserving HTML structure.
        
        Args:
            rich_text: The rich text content to translate
            target_language: The target language code
            
        Returns:
            Translated rich text
        """
        if not rich_text:
            return rich_text
        
        # Simple translation - in production, this would use a proper translation service
        # For now, we'll use the medical terms mapping
        translated_text = rich_text
        
        # Replace medical terms
        if target_language in self.medical_terms_mapping:
            for english_term, translated_term in self.medical_terms_mapping[target_language].items():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(english_term), re.IGNORECASE)
                translated_text = pattern.sub(translated_term, translated_text)
        
        return translated_text
    
    def _translate_text(self, text: str, target_language: str) -> str:
        """
        Translate simple text content.
        
        Args:
            text: The text to translate
            target_language: The target language code
            
        Returns:
            Translated text
        """
        if not text:
            return text
        
        # Simple translation using medical terms mapping
        translated_text = text
        
        if target_language in self.medical_terms_mapping:
            for english_term, translated_term in self.medical_terms_mapping[target_language].items():
                pattern = re.compile(re.escape(english_term), re.IGNORECASE)
                translated_text = pattern.sub(translated_term, translated_text)
        
        return translated_text
    
    def _generate_translated_slug(self, slug: str, target_language: str) -> str:
        """
        Generate a translated slug for the page.
        
        Args:
            slug: The original slug
            target_language: The target language code
            
        Returns:
            Translated slug
        """
        # Simple slug translation - in production, this would be more sophisticated
        if target_language == 'af-ZA':
            # Basic Afrikaans slug generation
            slug_mapping = {
                'medications': 'medikasie',
                'dosage': 'dosering',
                'side-effects': 'neweffekte',
                'interactions': 'interaksies',
                'storage': 'berging',
                'instructions': 'instruksies'
            }
            
            for english, afrikaans in slug_mapping.items():
                slug = slug.replace(english, afrikaans)
        
        return slug
    
    def _copy_related_content(self, source_page: Page, target_page: Page, target_locale: Locale):
        """
        Copy related content (images, documents) to the translated page.
        
        Args:
            source_page: The source page
            target_page: The target page
            target_locale: The target locale
        """
        # Copy images
        if hasattr(source_page, 'image') and source_page.image:
            # Create a copy of the image for the new locale
            new_image = Image.objects.create(
                title=source_page.image.title,
                file=source_page.image.file,
                collection=source_page.image.collection
            )
            target_page.image = new_image
        
        # Copy documents
        if hasattr(source_page, 'document') and source_page.document:
            new_document = Document.objects.create(
                title=source_page.document.title,
                file=source_page.document.file,
                collection=source_page.document.collection
            )
            target_page.document = new_document
    
    def _preserve_page_structure(self, source_page: Page, target_page: Page):
        """
        Preserve the page hierarchy structure in the translation.
        
        Args:
            source_page: The source page
            target_page: The target page
        """
        # Ensure the translated page has the same parent structure
        if source_page.get_parent():
            parent_translation = source_page.get_parent().get_translation(target_page.locale)
            if parent_translation:
                target_page.move(parent_translation, pos='last-child')
    
    def bulk_copy_medication_translations(
        self, 
        source_locale: Locale, 
        target_locale: Locale,
        page_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Bulk copy medication page translations.
        
        Args:
            source_locale: The source locale
            target_locale: The target locale
            page_ids: Optional list of specific page IDs to translate
            
        Returns:
            Dictionary with translation results
        """
        results = {
            'successful': [],
            'failed': [],
            'skipped': [],
            'total': 0
        }
        
        # Get medication pages to translate
        if page_ids:
            pages = Page.objects.filter(id__in=page_ids, locale=source_locale)
        else:
            pages = Page.objects.filter(locale=source_locale)
        
        # Filter for medication pages
        medication_pages = [
            page for page in pages if self._is_medication_page(page)
        ]
        
        results['total'] = len(medication_pages)
        
        for page in medication_pages:
            try:
                # Check if translation already exists
                existing_translation = page.get_translation(target_locale)
                if existing_translation:
                    results['skipped'].append({
                        'page_id': page.id,
                        'page_title': page.title,
                        'reason': 'Translation already exists'
                    })
                    continue
                
                # Create translation
                translated_page = self.copy_medication_page_translation(
                    page, target_locale
                )
                
                results['successful'].append({
                    'page_id': page.id,
                    'page_title': page.title,
                    'translated_page_id': translated_page.id,
                    'translated_page_title': translated_page.title
                })
                
            except Exception as e:
                results['failed'].append({
                    'page_id': page.id,
                    'page_title': page.title,
                    'error': str(e)
                })
        
        return results

# =============================================================================
# 2. LOCALIZED MEDICATION SEARCH WITH LANGUAGE-SPECIFIC MEDICAL TERMS
# =============================================================================

class LocalizedMedicationSearch:
    """
    Enhanced medication search with language-specific medical terminology support.
    
    This class provides intelligent search capabilities that understand medical terms
    in different languages and can match equivalent terms across languages.
    """
    
    def __init__(self):
        self.medical_terminology = self._load_medical_terminology()
        self.search_indexes = self._build_search_indexes()
    
    def _load_medical_terminology(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Load comprehensive medical terminology for different languages.
        
        Returns:
            Dictionary mapping language codes to medical term categories
        """
        return {
            'en-ZA': {
                'medication_types': [
                    'tablet', 'capsule', 'liquid', 'injection', 'inhaler', 'cream',
                    'ointment', 'drops', 'patch', 'suppository', 'syrup', 'suspension'
                ],
                'dosage_forms': [
                    'oral', 'topical', 'intravenous', 'intramuscular', 'subcutaneous',
                    'inhalation', 'rectal', 'vaginal', 'ophthalmic', 'otic'
                ],
                'frequency_terms': [
                    'once daily', 'twice daily', 'three times daily', 'four times daily',
                    'as needed', 'weekly', 'monthly', 'every 6 hours', 'every 8 hours',
                    'every 12 hours', 'before meals', 'after meals', 'with food'
                ],
                'side_effects': [
                    'nausea', 'vomiting', 'diarrhea', 'constipation', 'headache',
                    'dizziness', 'fatigue', 'rash', 'itching', 'swelling',
                    'shortness of breath', 'chest pain', 'irregular heartbeat'
                ],
                'medical_conditions': [
                    'hypertension', 'diabetes', 'asthma', 'arthritis', 'depression',
                    'anxiety', 'infection', 'inflammation', 'pain', 'fever'
                ]
            },
            'af-ZA': {
                'medication_types': [
                    'pille', 'kapsule', 'vloeistof', 'inspuiting', 'inhaleerder', 'salf',
                    'ointment', 'druppels', 'pleister', 'suppositorium', 'stroop', 'suspensie'
                ],
                'dosage_forms': [
                    'oraal', 'topikaal', 'intraveneus', 'intramuskulêr', 'subkutaan',
                    'inaseming', 'rekteel', 'vaginaal', 'oftalmies', 'oties'
                ],
                'frequency_terms': [
                    'een keer daagliks', 'twee keer daagliks', 'drie keer daagliks', 'vier keer daagliks',
                    'soos benodig', 'weekliks', 'maandeliks', 'elke 6 uur', 'elke 8 uur',
                    'elke 12 uur', 'voor maaltye', 'na maaltye', 'met kos'
                ],
                'side_effects': [
                    'naarheid', 'braking', 'diarree', 'hardlywigheid', 'hoofpyn',
                    'duiseligheid', 'moegheid', 'uitslag', 'jeuk', 'swelling',
                    'kortasem', 'borspyn', 'onreëlmatige hartklop'
                ],
                'medical_conditions': [
                    'hipertensie', 'diabetes', 'asma', 'artritis', 'depressie',
                    'angs', 'infeksie', 'ontsteking', 'pyn', 'koors'
                ]
            }
        }
    
    def _build_search_indexes(self) -> Dict[str, Dict[str, str]]:
        """
        Build search indexes for cross-language term matching.
        
        Returns:
            Dictionary mapping terms to their canonical forms
        """
        indexes = {}
        
        # Build cross-language mappings
        term_mappings = {
            # Medication types
            'tablet': ['pille'],
            'capsule': ['kapsule'],
            'liquid': ['vloeistof'],
            'injection': ['inspuiting'],
            'inhaler': ['inhaleerder'],
            'cream': ['salf'],
            'ointment': ['ointment'],
            'drops': ['druppels'],
            'patch': ['pleister'],
            
            # Medical conditions
            'hypertension': ['hipertensie'],
            'diabetes': ['diabetes'],
            'asthma': ['asma'],
            'arthritis': ['artritis'],
            'depression': ['depressie'],
            'anxiety': ['angs'],
            'infection': ['infeksie'],
            'inflammation': ['ontsteking'],
            'pain': ['pyn'],
            'fever': ['koors'],
            
            # Side effects
            'nausea': ['naarheid'],
            'vomiting': ['braking'],
            'diarrhea': ['diarree'],
            'constipation': ['hardlywigheid'],
            'headache': ['hoofpyn'],
            'dizziness': ['duiseligheid'],
            'fatigue': ['moegheid'],
            'rash': ['uitslag'],
            'itching': ['jeuk'],
            'swelling': ['swelling'],
        }
        
        # Create reverse mappings
        for english_term, afrikaans_terms in term_mappings.items():
            indexes[english_term] = english_term
            for afrikaans_term in afrikaans_terms:
                indexes[afrikaans_term] = english_term
        
        return indexes
    
    def search_medications(
        self, 
        query: str, 
        language: str = 'en-ZA',
        search_fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search medications with language-specific term recognition.
        
        Args:
            query: The search query
            language: The language code for the search
            search_fields: Specific fields to search in
            filters: Additional filters to apply
            limit: Maximum number of results
            
        Returns:
            Dictionary containing search results and metadata
        """
        from medications.models import Medication
        
        # Normalize the query
        normalized_query = self._normalize_query(query, language)
        
        # Expand query with related terms
        expanded_terms = self._expand_search_terms(normalized_query, language)
        
        # Build the search query
        search_query = self._build_search_query(expanded_terms, search_fields)
        
        # Apply filters
        queryset = Medication.objects.all()
        if filters:
            queryset = self._apply_filters(queryset, filters)
        
        # Perform the search
        results = queryset.filter(search_query).distinct()[:limit]
        
        # Enhance results with language-specific information
        enhanced_results = self._enhance_search_results(results, language)
        
        return {
            'results': enhanced_results,
            'query': query,
            'normalized_query': normalized_query,
            'expanded_terms': expanded_terms,
            'total_count': len(enhanced_results),
            'language': language,
            'search_metadata': {
                'terms_recognized': len(expanded_terms),
                'medical_terms_found': self._count_medical_terms(normalized_query, language)
            }
        }
    
    def _normalize_query(self, query: str, language: str) -> str:
        """
        Normalize the search query for better matching.
        
        Args:
            query: The original query
            language: The language code
            
        Returns:
            Normalized query string
        """
        import re
        
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Handle common abbreviations
        abbreviation_mappings = {
            'en-ZA': {
                'tab': 'tablet',
                'cap': 'capsule',
                'inj': 'injection',
                'inh': 'inhaler',
                'bid': 'twice daily',
                'tid': 'three times daily',
                'qid': 'four times daily',
                'prn': 'as needed',
                'qd': 'once daily',
            },
            'af-ZA': {
                'pil': 'pille',
                'kap': 'kapsule',
                'inj': 'inspuiting',
                'inh': 'inhaleerder',
                'td': 'twee keer daagliks',
                'dd': 'drie keer daagliks',
                'vd': 'vier keer daagliks',
                'sb': 'soos benodig',
                'ed': 'een keer daagliks',
            }
        }
        
        if language in abbreviation_mappings:
            for abbrev, full_term in abbreviation_mappings[language].items():
                # Replace abbreviations with full terms
                pattern = r'\b' + re.escape(abbrev) + r'\b'
                normalized = re.sub(pattern, full_term, normalized)
        
        return normalized
    
    def _expand_search_terms(self, query: str, language: str) -> List[str]:
        """
        Expand search terms with related medical terminology.
        
        Args:
            query: The normalized query
            language: The language code
            
        Returns:
            List of expanded search terms
        """
        expanded_terms = [query]
        
        # Split query into individual terms
        terms = query.split()
        
        for term in terms:
            # Add canonical form if available
            if term in self.search_indexes:
                canonical = self.search_indexes[term]
                if canonical not in expanded_terms:
                    expanded_terms.append(canonical)
            
            # Add related medical terms
            related_terms = self._get_related_medical_terms(term, language)
            expanded_terms.extend(related_terms)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_terms = []
        for term in expanded_terms:
            if term not in seen:
                seen.add(term)
                unique_terms.append(term)
        
        return unique_terms
    
    def _get_related_medical_terms(self, term: str, language: str) -> List[str]:
        """
        Get related medical terms for a given term.
        
        Args:
            term: The medical term
            language: The language code
            
        Returns:
            List of related medical terms
        """
        related_terms = []
        
        if language in self.medical_terminology:
            terminology = self.medical_terminology[language]
            
            # Check each category for related terms
            for category, terms in terminology.items():
                if term in terms:
                    # Add other terms from the same category
                    related_terms.extend([t for t in terms if t != term])
                    break
        
        return related_terms
    
    def _build_search_query(self, terms: List[str], search_fields: Optional[List[str]] = None) -> Any:
        """
        Build a Django Q object for the search query.
        
        Args:
            terms: List of search terms
            search_fields: Specific fields to search in
            
        Returns:
            Django Q object for the search
        """
        from django.db.models import Q
        
        if not search_fields:
            search_fields = ['name', 'generic_name', 'brand_name', 'description', 'active_ingredients']
        
        query = Q()
        
        for term in terms:
            term_query = Q()
            for field in search_fields:
                term_query |= Q(**{f"{field}__icontains": term})
            query |= term_query
        
        return query
    
    def _apply_filters(self, queryset, filters: Dict[str, Any]):
        """
        Apply additional filters to the queryset.
        
        Args:
            queryset: The base queryset
            filters: Dictionary of filters to apply
            
        Returns:
            Filtered queryset
        """
        # Apply medication type filter
        if 'medication_type' in filters:
            queryset = queryset.filter(medication_type=filters['medication_type'])
        
        # Apply prescription type filter
        if 'prescription_type' in filters:
            queryset = queryset.filter(prescription_type=filters['prescription_type'])
        
        # Apply category filter
        if 'category' in filters:
            queryset = queryset.filter(category=filters['category'])
        
        # Apply active filter
        if 'is_active' in filters:
            queryset = queryset.filter(is_active=filters['is_active'])
        
        return queryset
    
    def _enhance_search_results(self, results, language: str) -> List[Dict[str, Any]]:
        """
        Enhance search results with language-specific information.
        
        Args:
            results: QuerySet of medication results
            language: The language code
            
        Returns:
            List of enhanced result dictionaries
        """
        enhanced_results = []
        
        for medication in results:
            enhanced_result = {
                'id': medication.id,
                'name': medication.name,
                'generic_name': medication.generic_name,
                'brand_name': medication.brand_name,
                'medication_type': medication.medication_type,
                'prescription_type': medication.prescription_type,
                'description': medication.description,
                'localized_info': self._get_localized_medication_info(medication, language),
                'search_relevance': self._calculate_search_relevance(medication, language),
                'related_terms': self._get_related_terms_for_medication(medication, language)
            }
            
            enhanced_results.append(enhanced_result)
        
        # Sort by search relevance
        enhanced_results.sort(key=lambda x: x['search_relevance'], reverse=True)
        
        return enhanced_results
    
    def _get_localized_medication_info(self, medication, language: str) -> Dict[str, Any]:
        """
        Get language-specific information for a medication.
        
        Args:
            medication: The medication object
            language: The language code
            
        Returns:
            Dictionary of localized information
        """
        localized_info = {
            'medication_type_localized': self._translate_medication_type(medication.medication_type, language),
            'prescription_type_localized': self._translate_prescription_type(medication.prescription_type, language),
            'dosage_instructions_localized': self._translate_dosage_instructions(medication, language),
            'side_effects_localized': self._translate_side_effects(medication, language),
        }
        
        return localized_info
    
    def _translate_medication_type(self, medication_type: str, language: str) -> str:
        """Translate medication type to the target language."""
        translations = {
            'en-ZA': {
                'tablet': 'Tablet',
                'capsule': 'Capsule',
                'liquid': 'Liquid',
                'injection': 'Injection',
                'inhaler': 'Inhaler',
                'cream': 'Cream',
                'ointment': 'Ointment',
                'drops': 'Drops',
                'patch': 'Patch',
            },
            'af-ZA': {
                'tablet': 'Pille',
                'capsule': 'Kapsule',
                'liquid': 'Vloeistof',
                'injection': 'Inspuiting',
                'inhaler': 'Inhaleerder',
                'cream': 'Salf',
                'ointment': 'Ointment',
                'drops': 'Druppels',
                'patch': 'Pleister',
            }
        }
        
        return translations.get(language, {}).get(medication_type, medication_type)
    
    def _translate_prescription_type(self, prescription_type: str, language: str) -> str:
        """Translate prescription type to the target language."""
        translations = {
            'en-ZA': {
                'prescription': 'Prescription Required',
                'otc': 'Over the Counter',
                'supplement': 'Supplement',
            },
            'af-ZA': {
                'prescription': 'Voorskrif Benodig',
                'otc': 'Oor die Toonbank',
                'supplement': 'Aanvulling',
            }
        }
        
        return translations.get(language, {}).get(prescription_type, prescription_type)
    
    def _translate_dosage_instructions(self, medication, language: str) -> str:
        """Translate dosage instructions to the target language."""
        # This would typically access the medication's dosage information
        # and translate it based on the language
        return f"Localized dosage instructions for {medication.name} in {language}"
    
    def _translate_side_effects(self, medication, language: str) -> str:
        """Translate side effects to the target language."""
        # This would typically access the medication's side effects
        # and translate them based on the language
        return f"Localized side effects for {medication.name} in {language}"
    
    def _calculate_search_relevance(self, medication, language: str) -> float:
        """
        Calculate search relevance score for a medication.
        
        Args:
            medication: The medication object
            language: The language code
            
        Returns:
            Relevance score (0.0 to 1.0)
        """
        # This is a simplified relevance calculation
        # In production, this would be more sophisticated
        relevance = 0.5  # Base relevance
        
        # Boost for exact name matches
        if hasattr(medication, 'name') and medication.name:
            relevance += 0.2
        
        # Boost for generic name matches
        if hasattr(medication, 'generic_name') and medication.generic_name:
            relevance += 0.1
        
        # Boost for brand name matches
        if hasattr(medication, 'brand_name') and medication.brand_name:
            relevance += 0.1
        
        return min(relevance, 1.0)
    
    def _get_related_terms_for_medication(self, medication, language: str) -> List[str]:
        """
        Get related medical terms for a medication.
        
        Args:
            medication: The medication object
            language: The language code
            
        Returns:
            List of related medical terms
        """
        related_terms = []
        
        # Add medication type terms
        if hasattr(medication, 'medication_type'):
            related_terms.extend(
                self._get_related_medical_terms(medication.medication_type, language)
            )
        
        # Add prescription type terms
        if hasattr(medication, 'prescription_type'):
            related_terms.extend(
                self._get_related_medical_terms(medication.prescription_type, language)
            )
        
        return list(set(related_terms))  # Remove duplicates
    
    def _count_medical_terms(self, query: str, language: str) -> int:
        """
        Count medical terms found in the query.
        
        Args:
            query: The search query
            language: The language code
            
        Returns:
            Number of medical terms found
        """
        count = 0
        
        if language in self.medical_terminology:
            terminology = self.medical_terminology[language]
            
            for category, terms in terminology.items():
                for term in terms:
                    if term.lower() in query.lower():
                        count += 1
        
        return count

# =============================================================================
# 3. REGION-SPECIFIC PHARMACY INTEGRATION FOR SOUTH AFRICAN PHARMACIES
# =============================================================================

class SAPharmacyIntegration:
    """
    Region-specific pharmacy integration for South African pharmacies.
    
    This class provides integration capabilities with South African pharmacy systems,
    including Clicks, Dis-Chem, and independent pharmacies, with localized
    medication availability and pricing information.
    """
    
    def __init__(self):
        self.pharmacy_networks = self._load_pharmacy_networks()
        self.medication_mappings = self._load_medication_mappings()
        self.pricing_zones = self._load_pricing_zones()
    
    def _load_pharmacy_networks(self) -> Dict[str, Dict[str, Any]]:
        """
        Load South African pharmacy network configurations.
        
        Returns:
            Dictionary of pharmacy network configurations
        """
        return {
            'clicks': {
                'name': 'Clicks',
                'name_af': 'Clicks',
                'api_endpoint': 'https://api.clicks.co.za/pharmacy',
                'regions': ['gauteng', 'western_cape', 'kwazulu_natal', 'free_state', 'mpumalanga', 'limpopo', 'north_west', 'eastern_cape', 'northern_cape'],
                'supported_languages': ['en-ZA', 'af-ZA'],
                'payment_methods': ['cash', 'card', 'medical_aid', 'discovery_vitality'],
                'delivery_options': ['store_pickup', 'home_delivery', 'same_day_delivery'],
                'operating_hours': {
                    'weekdays': '08:00-19:00',
                    'saturdays': '08:00-17:00',
                    'sundays': '09:00-15:00'
                }
            },
            'dischem': {
                'name': 'Dis-Chem',
                'name_af': 'Dis-Chem',
                'api_endpoint': 'https://api.dischem.co.za/pharmacy',
                'regions': ['gauteng', 'western_cape', 'kwazulu_natal', 'free_state', 'mpumalanga', 'limpopo', 'north_west', 'eastern_cape', 'northern_cape'],
                'supported_languages': ['en-ZA', 'af-ZA'],
                'payment_methods': ['cash', 'card', 'medical_aid', 'discovery_vitality', 'bonus_points'],
                'delivery_options': ['store_pickup', 'home_delivery', 'same_day_delivery', 'express_delivery'],
                'operating_hours': {
                    'weekdays': '07:00-20:00',
                    'saturdays': '07:00-18:00',
                    'sundays': '08:00-16:00'
                }
            },
            'medirite': {
                'name': 'MediRite',
                'name_af': 'MediRite',
                'api_endpoint': 'https://api.medirite.co.za/pharmacy',
                'regions': ['gauteng', 'western_cape', 'kwazulu_natal'],
                'supported_languages': ['en-ZA', 'af-ZA'],
                'payment_methods': ['cash', 'card', 'medical_aid'],
                'delivery_options': ['store_pickup', 'home_delivery'],
                'operating_hours': {
                    'weekdays': '08:00-18:00',
                    'saturdays': '08:00-16:00',
                    'sundays': '09:00-14:00'
                }
            },
            'independent': {
                'name': 'Independent Pharmacies',
                'name_af': 'Onafhanklike Apteek',
                'api_endpoint': None,  # Individual APIs
                'regions': ['all'],
                'supported_languages': ['en-ZA', 'af-ZA'],
                'payment_methods': ['cash', 'card', 'medical_aid'],
                'delivery_options': ['store_pickup', 'home_delivery'],
                'operating_hours': {
                    'weekdays': '08:00-18:00',
                    'saturdays': '08:00-16:00',
                    'sundays': 'closed'
                }
            }
        }
    
    def _load_medication_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Load medication mappings for different pharmacy networks.
        
        Returns:
            Dictionary mapping generic names to pharmacy-specific codes
        """
        return {
            'paracetamol': {
                'clicks': 'PARA500',
                'dischem': 'PARA500MG',
                'medirite': 'PARA500TAB',
                'generic_name': 'Paracetamol',
                'generic_name_af': 'Parasetamol'
            },
            'ibuprofen': {
                'clicks': 'IBUP400',
                'dischem': 'IBUP400MG',
                'medirite': 'IBUP400TAB',
                'generic_name': 'Ibuprofen',
                'generic_name_af': 'Ibuprofen'
            },
            'amoxicillin': {
                'clicks': 'AMOX500',
                'dischem': 'AMOX500CAP',
                'medirite': 'AMOX500MG',
                'generic_name': 'Amoxicillin',
                'generic_name_af': 'Amoksisillien'
            },
            'omeprazole': {
                'clicks': 'OMEP20',
                'dischem': 'OMEP20MG',
                'medirite': 'OMEP20CAP',
                'generic_name': 'Omeprazole',
                'generic_name_af': 'Omeprasool'
            }
        }
    
    def _load_pricing_zones(self) -> Dict[str, Dict[str, float]]:
        """
        Load pricing zones for different regions in South Africa.
        
        Returns:
            Dictionary of pricing multipliers by region
        """
        return {
            'gauteng': {
                'base_multiplier': 1.0,
                'urban_multiplier': 1.1,
                'rural_multiplier': 0.9
            },
            'western_cape': {
                'base_multiplier': 1.05,
                'urban_multiplier': 1.15,
                'rural_multiplier': 0.95
            },
            'kwazulu_natal': {
                'base_multiplier': 0.95,
                'urban_multiplier': 1.05,
                'rural_multiplier': 0.85
            },
            'free_state': {
                'base_multiplier': 0.9,
                'urban_multiplier': 1.0,
                'rural_multiplier': 0.8
            },
            'mpumalanga': {
                'base_multiplier': 0.9,
                'urban_multiplier': 1.0,
                'rural_multiplier': 0.8
            },
            'limpopo': {
                'base_multiplier': 0.85,
                'urban_multiplier': 0.95,
                'rural_multiplier': 0.75
            },
            'north_west': {
                'base_multiplier': 0.9,
                'urban_multiplier': 1.0,
                'rural_multiplier': 0.8
            },
            'eastern_cape': {
                'base_multiplier': 0.9,
                'urban_multiplier': 1.0,
                'rural_multiplier': 0.8
            },
            'northern_cape': {
                'base_multiplier': 0.95,
                'urban_multiplier': 1.05,
                'rural_multiplier': 0.85
            }
        }
    
    def get_pharmacy_availability(
        self, 
        medication_name: str, 
        region: str = 'gauteng',
        pharmacy_network: Optional[str] = None,
        language: str = 'en-ZA'
    ) -> Dict[str, Any]:
        """
        Get medication availability from South African pharmacies.
        
        Args:
            medication_name: Name of the medication to search for
            region: South African region/province
            pharmacy_network: Specific pharmacy network to query
            language: Language for response
            
        Returns:
            Dictionary containing availability information
        """
        try:
            # Normalize medication name
            normalized_name = self._normalize_medication_name(medication_name)
            
            # Get pharmacy networks to query
            networks_to_query = self._get_networks_to_query(pharmacy_network, region)
            
            availability_results = {}
            
            for network in networks_to_query:
                network_config = self.pharmacy_networks[network]
                
                # Check if network supports the region
                if region not in network_config['regions'] and 'all' not in network_config['regions']:
                    continue
                
                # Get availability from network
                availability = self._query_pharmacy_network(
                    network, normalized_name, region, language
                )
                
                if availability:
                    availability_results[network] = {
                        'network_name': network_config['name'] if language == 'en-ZA' else network_config.get('name_af', network_config['name']),
                        'availability': availability,
                        'pricing': self._calculate_regional_pricing(availability.get('base_price', 0), region),
                        'delivery_options': network_config['delivery_options'],
                        'payment_methods': network_config['payment_methods'],
                        'operating_hours': network_config['operating_hours']
                    }
            
            return {
                'medication_name': medication_name,
                'normalized_name': normalized_name,
                'region': region,
                'language': language,
                'availability': availability_results,
                'total_pharmacies': len(availability_results),
                'best_price': self._find_best_price(availability_results),
                'nearest_pharmacy': self._find_nearest_pharmacy(availability_results, region)
            }
            
        except Exception as e:
            logger.error(f"Error getting pharmacy availability: {e}")
            return {
                'error': str(e),
                'medication_name': medication_name,
                'region': region,
                'language': language
            }
    
    def _normalize_medication_name(self, medication_name: str) -> str:
        """
        Normalize medication name for consistent searching.
        
        Args:
            medication_name: The medication name to normalize
            
        Returns:
            Normalized medication name
        """
        import re
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', medication_name.lower().strip())
        
        # Remove common suffixes and prefixes
        suffixes_to_remove = ['tablet', 'capsule', 'liquid', 'cream', 'ointment', 'mg', 'ml', 'g']
        for suffix in suffixes_to_remove:
            normalized = re.sub(rf'\b{suffix}\b', '', normalized)
        
        # Clean up extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _get_networks_to_query(self, pharmacy_network: Optional[str], region: str) -> List[str]:
        """
        Get list of pharmacy networks to query.
        
        Args:
            pharmacy_network: Specific network to query (if provided)
            region: The region to search in
            
        Returns:
            List of network names to query
        """
        if pharmacy_network:
            if pharmacy_network in self.pharmacy_networks:
                return [pharmacy_network]
            else:
                logger.warning(f"Unknown pharmacy network: {pharmacy_network}")
                return []
        
        # Return all networks that support the region
        supported_networks = []
        for network, config in self.pharmacy_networks.items():
            if region in config['regions'] or 'all' in config['regions']:
                supported_networks.append(network)
        
        return supported_networks
    
    def _query_pharmacy_network(
        self, 
        network: str, 
        medication_name: str, 
        region: str, 
        language: str
    ) -> Optional[Dict[str, Any]]:
        """
        Query a specific pharmacy network for medication availability.
        
        Args:
            network: The pharmacy network to query
            medication_name: The medication name
            region: The region to search in
            language: The language for the response
            
        Returns:
            Availability information or None if not available
        """
        try:
            # This would be a real API call in production
            # For now, we'll simulate the response
            
            # Check if we have a mapping for this medication
            if medication_name in self.medication_mappings:
                mapping = self.medication_mappings[medication_name]
                network_code = mapping.get(network)
                
                if network_code:
                    # Simulate API response
                    return {
                        'available': True,
                        'stock_level': 'high',  # high, medium, low, out_of_stock
                        'base_price': self._get_simulated_price(network, medication_name),
                        'pharmacy_code': network_code,
                        'generic_name': mapping['generic_name'] if language == 'en-ZA' else mapping.get('generic_name_af', mapping['generic_name']),
                        'formulations': ['tablet', 'capsule', 'liquid'],
                        'strengths': ['250mg', '500mg', '1000mg'],
                        'estimated_delivery': '1-2 business days',
                        'prescription_required': False
                    }
            
            # Generic response for unmapped medications
            return {
                'available': True,
                'stock_level': 'medium',
                'base_price': 50.0,  # Default price
                'pharmacy_code': f"{network.upper()}_{medication_name.upper()}",
                'generic_name': medication_name,
                'formulations': ['tablet'],
                'strengths': ['500mg'],
                'estimated_delivery': '2-3 business days',
                'prescription_required': True
            }
            
        except Exception as e:
            logger.error(f"Error querying pharmacy network {network}: {e}")
            return None
    
    def _get_simulated_price(self, network: str, medication_name: str) -> float:
        """
        Get simulated price for a medication from a specific network.
        
        Args:
            network: The pharmacy network
            medication_name: The medication name
            
        Returns:
            Simulated price in ZAR
        """
        # Base prices for common medications
        base_prices = {
            'paracetamol': 15.0,
            'ibuprofen': 25.0,
            'amoxicillin': 45.0,
            'omeprazole': 35.0
        }
        
        base_price = base_prices.get(medication_name, 30.0)
        
        # Network-specific pricing adjustments
        network_multipliers = {
            'clicks': 1.0,
            'dischem': 1.1,
            'medirite': 0.95,
            'independent': 0.9
        }
        
        multiplier = network_multipliers.get(network, 1.0)
        return round(base_price * multiplier, 2)
    
    def _calculate_regional_pricing(self, base_price: float, region: str) -> Dict[str, float]:
        """
        Calculate regional pricing based on location.
        
        Args:
            base_price: The base price of the medication
            region: The region/province
            
        Returns:
            Dictionary with different pricing options
        """
        if region not in self.pricing_zones:
            region = 'gauteng'  # Default to Gauteng
        
        zone_config = self.pricing_zones[region]
        
        return {
            'base_price': base_price,
            'urban_price': round(base_price * zone_config['urban_multiplier'], 2),
            'rural_price': round(base_price * zone_config['rural_multiplier'], 2),
            'delivery_fee': 25.0 if region in ['gauteng', 'western_cape'] else 35.0,
            'express_delivery_fee': 50.0 if region in ['gauteng', 'western_cape'] else 65.0
        }
    
    def _find_best_price(self, availability_results: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find the best price among available pharmacies.
        
        Args:
            availability_results: Results from pharmacy queries
            
        Returns:
            Best price information or None
        """
        best_price = None
        lowest_price = float('inf')
        
        for network, data in availability_results.items():
            pricing = data.get('pricing', {})
            base_price = pricing.get('base_price', float('inf'))
            
            if base_price < lowest_price:
                lowest_price = base_price
                best_price = {
                    'network': network,
                    'network_name': data['network_name'],
                    'price': base_price,
                    'pricing': pricing
                }
        
        return best_price
    
    def _find_nearest_pharmacy(self, availability_results: Dict[str, Any], region: str) -> Optional[Dict[str, Any]]:
        """
        Find the nearest pharmacy based on region.
        
        Args:
            availability_results: Results from pharmacy queries
            region: The current region
            
        Returns:
            Nearest pharmacy information or None
        """
        # In a real implementation, this would use GPS coordinates
        # For now, we'll return the first available pharmacy
        for network, data in availability_results.items():
            return {
                'network': network,
                'network_name': data['network_name'],
                'region': region,
                'estimated_distance': '2-5 km',
                'estimated_travel_time': '10-15 minutes'
            }
        
        return None
    
    def get_pharmacy_locations(
        self, 
        region: str = 'gauteng',
        pharmacy_network: Optional[str] = None,
        language: str = 'en-ZA'
    ) -> Dict[str, Any]:
        """
        Get pharmacy locations for a specific region.
        
        Args:
            region: The region to search in
            pharmacy_network: Specific pharmacy network
            language: Language for response
            
        Returns:
            Dictionary containing pharmacy locations
        """
        locations = []
        
        networks_to_query = self._get_networks_to_query(pharmacy_network, region)
        
        for network in networks_to_query:
            network_config = self.pharmacy_networks[network]
            
            # Simulate pharmacy locations
            network_locations = self._get_simulated_locations(network, region, language)
            locations.extend(network_locations)
        
        return {
            'region': region,
            'language': language,
            'total_locations': len(locations),
            'locations': locations
        }
    
    def _get_simulated_locations(self, network: str, region: str, language: str) -> List[Dict[str, Any]]:
        """
        Get simulated pharmacy locations for a network and region.
        
        Args:
            network: The pharmacy network
            region: The region
            language: The language
            
        Returns:
            List of pharmacy locations
        """
        # Simulate different numbers of locations based on network and region
        location_counts = {
            'clicks': {'gauteng': 15, 'western_cape': 12, 'kwazulu_natal': 10},
            'dischem': {'gauteng': 20, 'western_cape': 18, 'kwazulu_natal': 15},
            'medirite': {'gauteng': 8, 'western_cape': 6, 'kwazulu_natal': 5},
            'independent': {'gauteng': 25, 'western_cape': 20, 'kwazulu_natal': 18}
        }
        
        count = location_counts.get(network, {}).get(region, 5)
        
        locations = []
        for i in range(count):
            locations.append({
                'id': f"{network}_{region}_{i+1}",
                'name': f"{self.pharmacy_networks[network]['name']} {region.title()} {i+1}",
                'address': f"123 Main Street, {region.title()}, South Africa",
                'phone': f"+27 11 {1000000 + i}",
                'email': f"pharmacy{i+1}@{network}.co.za",
                'operating_hours': self.pharmacy_networks[network]['operating_hours'],
                'services': ['prescription_dispensing', 'over_the_counter', 'health_consultation'],
                'payment_methods': self.pharmacy_networks[network]['payment_methods'],
                'delivery_available': True,
                'distance': f"{i+1} km",
                'rating': round(4.0 + (i % 5) * 0.2, 1)
            })
        
        return locations

# =============================================================================
# 4. WAGTAIL 7.0.2 ENHANCED LOCALE-AWARE URL ROUTING
# =============================================================================

class LocaleAwareURLRouting:
    """
    Enhanced locale-aware URL routing for Wagtail 7.0.2.
    
    This class provides advanced URL routing capabilities that respect locale
    preferences and provide intelligent fallbacks for missing translations.
    """
    
    def __init__(self):
        self.locale_configs = self._load_locale_configs()
        self.url_patterns = self._build_url_patterns()
        self.fallback_strategies = self._load_fallback_strategies()
    
    def _load_locale_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load locale-specific configurations for URL routing.
        
        Returns:
            Dictionary of locale configurations
        """
        return {
            'en-ZA': {
                'code': 'en-ZA',
                'name': 'English (South Africa)',
                'name_native': 'English (South Africa)',
                'url_prefix': '',
                'is_default': True,
                'fallback_locale': None,
                'url_patterns': {
                    'medications': 'medications',
                    'pharmacy': 'pharmacy',
                    'healthcare': 'healthcare',
                    'about': 'about',
                    'contact': 'contact',
                    'privacy': 'privacy',
                    'terms': 'terms'
                },
                'seo_settings': {
                    'hreflang': 'en-ZA',
                    'og_locale': 'en_ZA',
                    'default_meta_title': 'MedGuard SA - Medication Management',
                    'default_meta_description': 'Comprehensive medication management for South Africa'
                }
            },
            'af-ZA': {
                'code': 'af-ZA',
                'name': 'Afrikaans (South Africa)',
                'name_native': 'Afrikaans (Suid-Afrika)',
                'url_prefix': 'af',
                'is_default': False,
                'fallback_locale': 'en-ZA',
                'url_patterns': {
                    'medications': 'medikasie',
                    'pharmacy': 'apteek',
                    'healthcare': 'gesondheidsorg',
                    'about': 'oor-ons',
                    'contact': 'kontak',
                    'privacy': 'privaatheid',
                    'terms': 'voorwaardes'
                },
                'seo_settings': {
                    'hreflang': 'af-ZA',
                    'og_locale': 'af_ZA',
                    'default_meta_title': 'MedGuard SA - Medikasie Bestuur',
                    'default_meta_description': 'Omvattende medikasie bestuur vir Suid-Afrika'
                }
            }
        }
    
    def _build_url_patterns(self) -> Dict[str, Dict[str, str]]:
        """
        Build comprehensive URL patterns for different locales.
        
        Returns:
            Dictionary of URL patterns by locale
        """
        patterns = {}
        
        for locale_code, config in self.locale_configs.items():
            patterns[locale_code] = {
                # Page type patterns
                'medication_index': f"{config['url_prefix']}/medications/".lstrip('/'),
                'medication_detail': f"{config['url_prefix']}/medications/{{slug}}/".lstrip('/'),
                'medication_category': f"{config['url_prefix']}/medications/category/{{category}}/".lstrip('/'),
                'medication_search': f"{config['url_prefix']}/medications/search/".lstrip('/'),
                
                # Pharmacy patterns
                'pharmacy_index': f"{config['url_prefix']}/pharmacy/".lstrip('/'),
                'pharmacy_location': f"{config['url_prefix']}/pharmacy/location/{{location_id}}/".lstrip('/'),
                'pharmacy_search': f"{config['url_prefix']}/pharmacy/search/".lstrip('/'),
                
                # Healthcare patterns
                'healthcare_index': f"{config['url_prefix']}/healthcare/".lstrip('/'),
                'healthcare_services': f"{config['url_prefix']}/healthcare/services/".lstrip('/'),
                'healthcare_providers': f"{config['url_prefix']}/healthcare/providers/".lstrip('/'),
                
                # User account patterns
                'user_profile': f"{config['url_prefix']}/account/profile/".lstrip('/'),
                'user_medications': f"{config['url_prefix']}/account/medications/".lstrip('/'),
                'user_prescriptions': f"{config['url_prefix']}/account/prescriptions/".lstrip('/'),
                'user_notifications': f"{config['url_prefix']}/account/notifications/".lstrip('/'),
                
                # Static page patterns
                'about': f"{config['url_prefix']}/about/".lstrip('/'),
                'contact': f"{config['url_prefix']}/contact/".lstrip('/'),
                'privacy': f"{config['url_prefix']}/privacy/".lstrip('/'),
                'terms': f"{config['url_prefix']}/terms/".lstrip('/'),
                'help': f"{config['url_prefix']}/help/".lstrip('/'),
                'faq': f"{config['url_prefix']}/faq/".lstrip('/'),
            }
        
        return patterns
    
    def _load_fallback_strategies(self) -> Dict[str, List[str]]:
        """
        Load fallback strategies for missing translations.
        
        Returns:
            Dictionary mapping locale codes to fallback strategies
        """
        return {
            'en-ZA': [],  # No fallback for default locale
            'af-ZA': ['en-ZA'],  # Fallback to English
        }
    
    def get_page_url(
        self, 
        page: Page, 
        locale: str = None, 
        request = None
    ) -> str:
        """
        Get the URL for a page in the specified locale.
        
        Args:
            page: The Wagtail page object
            locale: The target locale code
            request: The current request object
            
        Returns:
            The URL for the page in the specified locale
        """
        if not locale:
            locale = self._get_current_locale(request)
        
        # Check if page has a translation in the target locale
        translated_page = self._get_translated_page(page, locale)
        
        if translated_page:
            return translated_page.get_url(request)
        
        # If no translation exists, use fallback strategy
        fallback_url = self._get_fallback_url(page, locale, request)
        if fallback_url:
            return fallback_url
        
        # Last resort: return the original page URL
        return page.get_url(request)
    
    def _get_current_locale(self, request) -> str:
        """
        Get the current locale from the request.
        
        Args:
            request: The current request object
            
        Returns:
            The current locale code
        """
        if not request:
            return 'en-ZA'  # Default locale
        
        # Check for locale in URL
        path = request.path_info
        for locale_code, config in self.locale_configs.items():
            if config['url_prefix'] and path.startswith(f"/{config['url_prefix']}/"):
                return locale_code
        
        # Check for locale in session
        if hasattr(request, 'session'):
            locale = request.session.get('django_language')
            if locale:
                return locale
        
        # Check for locale in request headers
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            # Parse Accept-Language header
            preferred_locale = self._parse_accept_language(accept_language)
            if preferred_locale:
                return preferred_locale
        
        return 'en-ZA'  # Default locale
    
    def _parse_accept_language(self, accept_language: str) -> Optional[str]:
        """
        Parse the Accept-Language header to find preferred locale.
        
        Args:
            accept_language: The Accept-Language header value
            
        Returns:
            The preferred locale code or None
        """
        # Simple parsing - in production, this would be more sophisticated
        languages = accept_language.split(',')
        
        for lang in languages:
            # Extract language code
            lang_code = lang.split(';')[0].strip()
            
            # Check if it matches our supported locales
            if lang_code in self.locale_configs:
                return lang_code
            
            # Check for language-only matches (e.g., 'en' matches 'en-ZA')
            for supported_locale in self.locale_configs:
                if supported_locale.startswith(lang_code + '-'):
                    return supported_locale
        
        return None
    
    def _get_translated_page(self, page: Page, locale: str) -> Optional[Page]:
        """
        Get the translated version of a page in the specified locale.
        
        Args:
            page: The original page
            locale: The target locale
            
        Returns:
            The translated page or None if not found
        """
        try:
            # Get the locale object
            from wagtail.models import Locale
            locale_obj = Locale.objects.get(language_code=locale)
            
            # Get the translation
            translated_page = page.get_translation(locale_obj)
            return translated_page
            
        except Locale.DoesNotExist:
            logger.warning(f"Locale {locale} does not exist")
            return None
        except Exception as e:
            logger.error(f"Error getting translated page: {e}")
            return None
    
    def _get_fallback_url(self, page: Page, locale: str, request) -> Optional[str]:
        """
        Get fallback URL when translation is not available.
        
        Args:
            page: The original page
            locale: The target locale
            request: The current request
            
        Returns:
            Fallback URL or None
        """
        fallback_strategy = self.fallback_strategies.get(locale, [])
        
        for fallback_locale in fallback_strategy:
            fallback_page = self._get_translated_page(page, fallback_locale)
            if fallback_page:
                # Return the fallback page URL with locale prefix
                fallback_url = fallback_page.get_url(request)
                return self._add_locale_prefix(fallback_url, locale)
        
        return None
    
    def _add_locale_prefix(self, url: str, locale: str) -> str:
        """
        Add locale prefix to a URL.
        
        Args:
            url: The original URL
            locale: The locale code
            
        Returns:
            URL with locale prefix
        """
        locale_config = self.locale_configs.get(locale)
        if not locale_config or not locale_config['url_prefix']:
            return url
        
        # Add locale prefix to the URL
        if url.startswith('/'):
            return f"/{locale_config['url_prefix']}{url}"
        else:
            return f"/{locale_config['url_prefix']}/{url}"
    
    def build_url_pattern(
        self, 
        pattern_name: str, 
        locale: str = 'en-ZA',
        **kwargs
    ) -> str:
        """
        Build a URL pattern for a specific locale.
        
        Args:
            pattern_name: The name of the URL pattern
            locale: The locale code
            **kwargs: Parameters to substitute in the pattern
            
        Returns:
            The built URL pattern
        """
        patterns = self.url_patterns.get(locale, {})
        pattern = patterns.get(pattern_name, '')
        
        if not pattern:
            logger.warning(f"URL pattern '{pattern_name}' not found for locale '{locale}'")
            return ''
        
        # Substitute parameters in the pattern
        try:
            return pattern.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing parameter {e} for URL pattern '{pattern_name}'")
            return pattern
    
    def get_locale_alternatives(self, page: Page, request = None) -> List[Dict[str, str]]:
        """
        Get alternative locale URLs for a page.
        
        Args:
            page: The page object
            request: The current request
            
        Returns:
            List of alternative locale URLs
        """
        alternatives = []
        
        for locale_code, config in self.locale_configs.items():
            try:
                # Get the translated page
                translated_page = self._get_translated_page(page, locale_code)
                
                if translated_page:
                    url = translated_page.get_url(request)
                else:
                    # Use fallback URL
                    url = self._get_fallback_url(page, locale_code, request)
                    if not url:
                        continue
                
                alternatives.append({
                    'locale': locale_code,
                    'locale_name': config['name'],
                    'locale_name_native': config['name_native'],
                    'url': url,
                    'is_current': locale_code == self._get_current_locale(request),
                    'is_default': config['is_default']
                })
                
            except Exception as e:
                logger.error(f"Error getting locale alternative for {locale_code}: {e}")
                continue
        
        return alternatives
    
    def get_seo_metadata(
        self, 
        page: Page, 
        locale: str = 'en-ZA',
        request = None
    ) -> Dict[str, str]:
        """
        Get SEO metadata for a page in the specified locale.
        
        Args:
            page: The page object
            locale: The locale code
            request: The current request
            
        Returns:
            Dictionary of SEO metadata
        """
        locale_config = self.locale_configs.get(locale, {})
        seo_settings = locale_config.get('seo_settings', {})
        
        # Get page-specific metadata
        meta_title = getattr(page, 'meta_title', None)
        meta_description = getattr(page, 'meta_description', None)
        
        # Use defaults if not set
        if not meta_title:
            meta_title = seo_settings.get('default_meta_title', 'MedGuard SA')
        
        if not meta_description:
            meta_description = seo_settings.get('default_meta_description', '')
        
        # Get locale alternatives for hreflang
        locale_alternatives = self.get_locale_alternatives(page, request)
        
        return {
            'title': meta_title,
            'description': meta_description,
            'hreflang': seo_settings.get('hreflang', 'en-ZA'),
            'og_locale': seo_settings.get('og_locale', 'en_ZA'),
            'locale_alternatives': locale_alternatives,
            'canonical_url': self.get_page_url(page, locale, request)
        }
    
    def redirect_to_locale(
        self, 
        request, 
        target_locale: str = None
    ) -> Optional[str]:
        """
        Determine if a redirect to a different locale is needed.
        
        Args:
            request: The current request
            target_locale: The target locale (if specified)
            
        Returns:
            Redirect URL or None if no redirect needed
        """
        current_locale = self._get_current_locale(request)
        
        if target_locale and target_locale != current_locale:
            # Redirect to specific locale
            current_url = request.path_info
            return self._build_locale_redirect_url(current_url, current_locale, target_locale)
        
        # Check if user should be redirected based on preferences
        if self._should_redirect_based_on_preferences(request, current_locale):
            preferred_locale = self._get_user_preferred_locale(request)
            if preferred_locale and preferred_locale != current_locale:
                current_url = request.path_info
                return self._build_locale_redirect_url(current_url, current_locale, preferred_locale)
        
        return None
    
    def _should_redirect_based_on_preferences(self, request, current_locale: str) -> bool:
        """
        Check if user should be redirected based on their preferences.
        
        Args:
            request: The current request
            current_locale: The current locale
            
        Returns:
            True if redirect is recommended
        """
        # Check if user has explicitly chosen a locale
        if hasattr(request, 'session'):
            chosen_locale = request.session.get('user_chosen_locale')
            if chosen_locale and chosen_locale != current_locale:
                return True
        
        # Check if this is the first visit and we should redirect based on Accept-Language
        if hasattr(request, 'session'):
            first_visit = request.session.get('first_visit', True)
            if first_visit:
                return True
        
        return False
    
    def _get_user_preferred_locale(self, request) -> Optional[str]:
        """
        Get the user's preferred locale.
        
        Args:
            request: The current request
            
        Returns:
            The preferred locale code or None
        """
        # Check session for user choice
        if hasattr(request, 'session'):
            chosen_locale = request.session.get('user_chosen_locale')
            if chosen_locale:
                return chosen_locale
        
        # Check Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            return self._parse_accept_language(accept_language)
        
        return None
    
    def _build_locale_redirect_url(
        self, 
        current_url: str, 
        current_locale: str, 
        target_locale: str
    ) -> str:
        """
        Build a redirect URL for locale change.
        
        Args:
            current_url: The current URL
            current_locale: The current locale
            target_locale: The target locale
            
        Returns:
            The redirect URL
        """
        target_config = self.locale_configs.get(target_locale, {})
        current_config = self.locale_configs.get(current_locale, {})
        
        # Remove current locale prefix if it exists
        if current_config.get('url_prefix'):
            current_url = current_url.replace(f"/{current_config['url_prefix']}", '', 1)
        
        # Add target locale prefix if it exists
        if target_config.get('url_prefix'):
            if current_url.startswith('/'):
                return f"/{target_config['url_prefix']}{current_url}"
            else:
                return f"/{target_config['url_prefix']}/{current_url}"
        
        return current_url

# =============================================================================
# 5. CURRENCY AND MEASUREMENT UNIT LOCALIZATION FOR MEDICATION PRICING
# =============================================================================

class CurrencyAndMeasurementLocalization:
    """
    Currency and measurement unit localization for medication pricing.
    
    This class provides comprehensive localization for currency formatting,
    measurement units, and pricing display across different South African regions
    and languages.
    """
    
    def __init__(self):
        self.currency_configs = self._load_currency_configs()
        self.measurement_units = self._load_measurement_units()
        self.pricing_formats = self._load_pricing_formats()
        self.regional_settings = self._load_regional_settings()
    
    def _load_currency_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Load currency configurations for different regions.
        
        Returns:
            Dictionary of currency configurations
        """
        return {
            'ZAR': {
                'code': 'ZAR',
                'symbol': 'R',
                'symbol_af': 'R',
                'name': 'South African Rand',
                'name_af': 'Suid-Afrikaanse Rand',
                'decimal_places': 2,
                'decimal_separator': '.',
                'thousands_separator': ',',
                'position': 'before',  # R100.00
                'exchange_rates': {
                    'USD': 0.055,  # 1 ZAR = 0.055 USD
                    'EUR': 0.051,  # 1 ZAR = 0.051 EUR
                    'GBP': 0.044,  # 1 ZAR = 0.044 GBP
                },
                'regional_variants': {
                    'gauteng': {'symbol': 'R', 'position': 'before'},
                    'western_cape': {'symbol': 'R', 'position': 'before'},
                    'kwazulu_natal': {'symbol': 'R', 'position': 'before'},
                    'free_state': {'symbol': 'R', 'position': 'before'},
                    'mpumalanga': {'symbol': 'R', 'position': 'before'},
                    'limpopo': {'symbol': 'R', 'position': 'before'},
                    'north_west': {'symbol': 'R', 'position': 'before'},
                    'eastern_cape': {'symbol': 'R', 'position': 'before'},
                    'northern_cape': {'symbol': 'R', 'position': 'before'},
                }
            }
        }
    
    def _load_measurement_units(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """
        Load measurement unit configurations for different languages.
        
        Returns:
            Dictionary of measurement unit configurations
        """
        return {
            'en-ZA': {
                'weight': {
                    'mg': 'milligrams',
                    'g': 'grams',
                    'kg': 'kilograms',
                    'mcg': 'micrograms',
                    'lb': 'pounds',
                    'oz': 'ounces'
                },
                'volume': {
                    'ml': 'milliliters',
                    'l': 'liters',
                    'cl': 'centiliters',
                    'fl_oz': 'fluid ounces',
                    'tsp': 'teaspoons',
                    'tbsp': 'tablespoons'
                },
                'length': {
                    'mm': 'millimeters',
                    'cm': 'centimeters',
                    'm': 'meters',
                    'in': 'inches',
                    'ft': 'feet'
                },
                'temperature': {
                    'c': 'Celsius',
                    'f': 'Fahrenheit'
                },
                'time': {
                    'min': 'minutes',
                    'hr': 'hours',
                    'day': 'days',
                    'week': 'weeks',
                    'month': 'months',
                    'year': 'years'
                }
            },
            'af-ZA': {
                'weight': {
                    'mg': 'milligram',
                    'g': 'gram',
                    'kg': 'kilogram',
                    'mcg': 'mikrogram',
                    'lb': 'pond',
                    'oz': 'ons'
                },
                'volume': {
                    'ml': 'milliliter',
                    'l': 'liter',
                    'cl': 'sentiliter',
                    'fl_oz': 'vloeistof ons',
                    'tsp': 'teelepels',
                    'tbsp': 'eetlepels'
                },
                'length': {
                    'mm': 'millimeter',
                    'cm': 'sentimeter',
                    'm': 'meter',
                    'in': 'duim',
                    'ft': 'voet'
                },
                'temperature': {
                    'c': 'Celsius',
                    'f': 'Fahrenheit'
                },
                'time': {
                    'min': 'minute',
                    'hr': 'uur',
                    'day': 'dae',
                    'week': 'weke',
                    'month': 'maande',
                    'year': 'jare'
                }
            }
        }
    
    def _load_pricing_formats(self) -> Dict[str, Dict[str, str]]:
        """
        Load pricing format configurations for different locales.
        
        Returns:
            Dictionary of pricing format configurations
        """
        return {
            'en-ZA': {
                'currency_format': '{symbol}{amount}',
                'currency_format_with_space': '{symbol} {amount}',
                'range_format': '{symbol}{min_amount} - {symbol}{max_amount}',
                'discount_format': '{symbol}{original_amount} (was {symbol}{discounted_amount})',
                'per_unit_format': '{symbol}{amount} per {unit}',
                'bulk_format': '{symbol}{amount} for {quantity}',
                'free_text': 'Free',
                'free_text_af': 'Gratis',
                'price_on_request': 'Price on request',
                'price_on_request_af': 'Prys op aanvraag'
            },
            'af-ZA': {
                'currency_format': '{symbol}{amount}',
                'currency_format_with_space': '{symbol} {amount}',
                'range_format': '{symbol}{min_amount} - {symbol}{max_amount}',
                'discount_format': '{symbol}{original_amount} (was {symbol}{discounted_amount})',
                'per_unit_format': '{symbol}{amount} per {unit}',
                'bulk_format': '{symbol}{amount} vir {quantity}',
                'free_text': 'Gratis',
                'free_text_af': 'Gratis',
                'price_on_request': 'Prys op aanvraag',
                'price_on_request_af': 'Prys op aanvraag'
            }
        }
    
    def _load_regional_settings(self) -> Dict[str, Dict[str, Any]]:
        """
        Load regional settings for different provinces.
        
        Returns:
            Dictionary of regional settings
        """
        return {
            'gauteng': {
                'currency': 'ZAR',
                'language': 'en-ZA',
                'timezone': 'Africa/Johannesburg',
                'date_format': 'DD/MM/YYYY',
                'time_format': 'HH:mm',
                'number_format': '1,234.56',
                'tax_rate': 0.15,  # 15% VAT
                'shipping_zones': ['local', 'national'],
                'delivery_times': {
                    'local': '1-2 business days',
                    'national': '3-5 business days'
                }
            },
            'western_cape': {
                'currency': 'ZAR',
                'language': 'en-ZA',
                'timezone': 'Africa/Johannesburg',
                'date_format': 'DD/MM/YYYY',
                'time_format': 'HH:mm',
                'number_format': '1,234.56',
                'tax_rate': 0.15,
                'shipping_zones': ['local', 'national'],
                'delivery_times': {
                    'local': '1-2 business days',
                    'national': '3-5 business days'
                }
            },
            'kwazulu_natal': {
                'currency': 'ZAR',
                'language': 'en-ZA',
                'timezone': 'Africa/Johannesburg',
                'date_format': 'DD/MM/YYYY',
                'time_format': 'HH:mm',
                'number_format': '1,234.56',
                'tax_rate': 0.15,
                'shipping_zones': ['local', 'national'],
                'delivery_times': {
                    'local': '1-2 business days',
                    'national': '3-5 business days'
                }
            }
        }
    
    def format_currency(
        self, 
        amount: float, 
        currency: str = 'ZAR',
        locale: str = 'en-ZA',
        region: str = 'gauteng',
        include_symbol: bool = True,
        include_cents: bool = True
    ) -> str:
        """
        Format currency amount according to locale and regional preferences.
        
        Args:
            amount: The amount to format
            currency: The currency code
            locale: The locale code
            region: The region/province
            include_symbol: Whether to include currency symbol
            include_cents: Whether to include cents
            
        Returns:
            Formatted currency string
        """
        try:
            currency_config = self.currency_configs.get(currency, {})
            regional_config = currency_config.get('regional_variants', {}).get(region, {})
            
            # Determine symbol and position
            symbol = regional_config.get('symbol', currency_config.get('symbol', currency))
            position = regional_config.get('position', currency_config.get('position', 'before'))
            
            # Format the amount
            formatted_amount = self._format_number(amount, locale, include_cents)
            
            # Apply currency formatting
            if include_symbol:
                if position == 'before':
                    return f"{symbol}{formatted_amount}"
                else:
                    return f"{formatted_amount}{symbol}"
            else:
                return formatted_amount
                
        except Exception as e:
            logger.error(f"Error formatting currency: {e}")
            return str(amount)
    
    def _format_number(self, number: float, locale: str, include_cents: bool = True) -> str:
        """
        Format a number according to locale preferences.
        
        Args:
            number: The number to format
            locale: The locale code
            include_cents: Whether to include decimal places
            
        Returns:
            Formatted number string
        """
        try:
            # Get regional settings
            regional_settings = self.regional_settings.get('gauteng', {})  # Default to Gauteng
            
            # Format the number
            if include_cents:
                formatted = f"{number:,.2f}"
            else:
                formatted = f"{int(number):,}"
            
            # Apply regional formatting
            if regional_settings.get('number_format') == '1,234.56':
                # Standard South African format
                return formatted
            else:
                # Custom format if needed
                return formatted
                
        except Exception as e:
            logger.error(f"Error formatting number: {e}")
            return str(number)
    
    def format_measurement(
        self, 
        value: float, 
        unit: str, 
        locale: str = 'en-ZA',
        include_unit_name: bool = True
    ) -> str:
        """
        Format measurement values according to locale preferences.
        
        Args:
            value: The measurement value
            unit: The unit code (e.g., 'mg', 'ml', 'kg')
            locale: The locale code
            include_unit_name: Whether to include the full unit name
            
        Returns:
            Formatted measurement string
        """
        try:
            # Format the number
            formatted_value = self._format_number(value, locale, include_cents=True)
            
            # Get unit information
            unit_info = self._get_unit_info(unit, locale)
            
            if include_unit_name and unit_info:
                return f"{formatted_value} {unit_info}"
            else:
                return f"{formatted_value} {unit}"
                
        except Exception as e:
            logger.error(f"Error formatting measurement: {e}")
            return f"{value} {unit}"
    
    def _get_unit_info(self, unit: str, locale: str) -> Optional[str]:
        """
        Get unit information for a given unit and locale.
        
        Args:
            unit: The unit code
            locale: The locale code
            
        Returns:
            Unit information or None
        """
        measurement_units = self.measurement_units.get(locale, {})
        
        # Search through all categories
        for category, units in measurement_units.items():
            if unit in units:
                return units[unit]
        
        return None
    
    def format_medication_price(
        self, 
        price: float,
        medication_name: str,
        unit: str = 'tablet',
        quantity: int = 1,
        locale: str = 'en-ZA',
        region: str = 'gauteng',
        include_tax: bool = True,
        include_delivery: bool = False
    ) -> Dict[str, Any]:
        """
        Format medication pricing with comprehensive localization.
        
        Args:
            price: The base price
            medication_name: Name of the medication
            unit: The unit (tablet, capsule, etc.)
            quantity: The quantity
            locale: The locale code
            region: The region/province
            include_tax: Whether to include tax calculations
            include_delivery: Whether to include delivery costs
            
        Returns:
            Dictionary containing formatted pricing information
        """
        try:
            # Get regional settings
            regional_settings = self.regional_settings.get(region, {})
            tax_rate = regional_settings.get('tax_rate', 0.15)
            
            # Calculate pricing components
            base_price = price
            subtotal = base_price * quantity
            
            # Calculate tax
            tax_amount = 0
            if include_tax:
                tax_amount = subtotal * tax_rate
            
            # Calculate delivery
            delivery_cost = 0
            if include_delivery:
                delivery_cost = self._calculate_delivery_cost(region, quantity)
            
            # Calculate total
            total = subtotal + tax_amount + delivery_cost
            
            # Format all amounts
            formatted_pricing = {
                'base_price': self.format_currency(base_price, 'ZAR', locale, region),
                'subtotal': self.format_currency(subtotal, 'ZAR', locale, region),
                'tax_amount': self.format_currency(tax_amount, 'ZAR', locale, region),
                'delivery_cost': self.format_currency(delivery_cost, 'ZAR', locale, region),
                'total': self.format_currency(total, 'ZAR', locale, region),
                'per_unit': self.format_currency(base_price, 'ZAR', locale, region),
                'unit_formatted': self.format_measurement(quantity, unit, locale),
                'breakdown': {
                    'base_price_numeric': base_price,
                    'subtotal_numeric': subtotal,
                    'tax_amount_numeric': tax_amount,
                    'delivery_cost_numeric': delivery_cost,
                    'total_numeric': total,
                    'tax_rate': tax_rate,
                    'quantity': quantity,
                    'unit': unit
                }
            }
            
            # Add localized pricing formats
            pricing_formats = self.pricing_formats.get(locale, {})
            formatted_pricing['formats'] = {
                'per_unit_display': pricing_formats.get('per_unit_format', '{symbol}{amount} per {unit}').format(
                    symbol=self.currency_configs['ZAR']['symbol'],
                    amount=self.format_currency(base_price, 'ZAR', locale, region, include_symbol=False),
                    unit=self._get_unit_info(unit, locale) or unit
                ),
                'bulk_display': pricing_formats.get('bulk_format', '{symbol}{amount} for {quantity}').format(
                    symbol=self.currency_configs['ZAR']['symbol'],
                    amount=self.format_currency(total, 'ZAR', locale, region, include_symbol=False),
                    quantity=self.format_measurement(quantity, unit, locale)
                )
            }
            
            return formatted_pricing
            
        except Exception as e:
            logger.error(f"Error formatting medication price: {e}")
            return {
                'error': str(e),
                'base_price': str(price),
                'total': str(price)
            }
    
    def _calculate_delivery_cost(self, region: str, quantity: int) -> float:
        """
        Calculate delivery cost based on region and quantity.
        
        Args:
            region: The region/province
            quantity: The quantity ordered
            
        Returns:
            Delivery cost
        """
        # Base delivery costs by region
        base_costs = {
            'gauteng': 25.0,
            'western_cape': 30.0,
            'kwazulu_natal': 35.0,
            'free_state': 40.0,
            'mpumalanga': 45.0,
            'limpopo': 50.0,
            'north_west': 45.0,
            'eastern_cape': 40.0,
            'northern_cape': 55.0
        }
        
        base_cost = base_costs.get(region, 35.0)
        
        # Adjust for quantity (bulk discounts)
        if quantity >= 10:
            base_cost *= 0.8  # 20% discount for bulk orders
        elif quantity >= 5:
            base_cost *= 0.9  # 10% discount for medium orders
        
        return round(base_cost, 2)
    
    def convert_currency(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str
    ) -> float:
        """
        Convert currency using exchange rates.
        
        Args:
            amount: The amount to convert
            from_currency: The source currency
            to_currency: The target currency
            
        Returns:
            Converted amount
        """
        try:
            if from_currency == to_currency:
                return amount
            
            # Get exchange rates
            from_config = self.currency_configs.get(from_currency, {})
            exchange_rates = from_config.get('exchange_rates', {})
            
            if to_currency in exchange_rates:
                rate = exchange_rates[to_currency]
                return round(amount * rate, 2)
            else:
                logger.warning(f"Exchange rate not found for {from_currency} to {to_currency}")
                return amount
                
        except Exception as e:
            logger.error(f"Error converting currency: {e}")
            return amount
    
    def get_price_range_display(
        self, 
        min_price: float, 
        max_price: float,
        locale: str = 'en-ZA',
        region: str = 'gauteng'
    ) -> str:
        """
        Format a price range for display.
        
        Args:
            min_price: The minimum price
            max_price: The maximum price
            locale: The locale code
            region: The region/province
            
        Returns:
            Formatted price range string
        """
        try:
            pricing_formats = self.pricing_formats.get(locale, {})
            range_format = pricing_formats.get('range_format', '{symbol}{min_amount} - {symbol}{max_amount}')
            
            min_formatted = self.format_currency(min_price, 'ZAR', locale, region, include_symbol=False)
            max_formatted = self.format_currency(max_price, 'ZAR', locale, region, include_symbol=False)
            
            symbol = self.currency_configs['ZAR']['symbol']
            
            return range_format.format(
                symbol=symbol,
                min_amount=min_formatted,
                max_amount=max_formatted
            )
            
        except Exception as e:
            logger.error(f"Error formatting price range: {e}")
            return f"R{min_price} - R{max_price}"
    
    def format_discount_display(
        self, 
        original_price: float, 
        discounted_price: float,
        locale: str = 'en-ZA',
        region: str = 'gauteng'
    ) -> str:
        """
        Format discount display with original and discounted prices.
        
        Args:
            original_price: The original price
            discounted_price: The discounted price
            locale: The locale code
            region: The region/province
            
        Returns:
            Formatted discount string
        """
        try:
            pricing_formats = self.pricing_formats.get(locale, {})
            discount_format = pricing_formats.get('discount_format', '{symbol}{original_amount} (was {symbol}{discounted_amount})')
            
            original_formatted = self.format_currency(original_price, 'ZAR', locale, region, include_symbol=False)
            discounted_formatted = self.format_currency(discounted_price, 'ZAR', locale, region, include_symbol=False)
            
            symbol = self.currency_configs['ZAR']['symbol']
            
            return discount_format.format(
                symbol=symbol,
                original_amount=discounted_formatted,
                discounted_amount=original_formatted
            )
            
        except Exception as e:
            logger.error(f"Error formatting discount: {e}")
            return f"R{discounted_price} (was R{original_price})"

# =============================================================================
# 6. LOCALIZED NOTIFICATION TEMPLATES FOR DIFFERENT USER LANGUAGES
# =============================================================================

class LocalizedNotificationTemplates:
    """
    Localized notification templates for different user languages.
    
    This class provides comprehensive notification template management
    with support for multiple languages and notification types.
    """
    
    def __init__(self):
        self.templates = self._load_notification_templates()
        self.variables = self._load_template_variables()
    
    def _load_notification_templates(self) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Load notification templates for different languages."""
        return {
            'en-ZA': {
                'medication_reminder': {
                    'subject': 'Medication Reminder: {medication_name}',
                    'body': 'Time to take your {medication_name} ({dosage}). Please take it now.',
                    'sms': 'MedGuard: Time to take {medication_name} ({dosage}). Take now.',
                    'push': 'Medication Reminder: {medication_name}'
                },
                'prescription_refill': {
                    'subject': 'Prescription Refill Reminder: {medication_name}',
                    'body': 'Your prescription for {medication_name} needs to be refilled. Please contact your pharmacy.',
                    'sms': 'MedGuard: Refill needed for {medication_name}. Contact pharmacy.',
                    'push': 'Refill Reminder: {medication_name}'
                },
                'appointment_reminder': {
                    'subject': 'Appointment Reminder: {appointment_type}',
                    'body': 'You have an appointment for {appointment_type} on {appointment_date} at {appointment_time}.',
                    'sms': 'MedGuard: Appointment reminder - {appointment_type} on {appointment_date}.',
                    'push': 'Appointment Reminder: {appointment_type}'
                }
            },
            'af-ZA': {
                'medication_reminder': {
                    'subject': 'Medikasie Herinnering: {medication_name}',
                    'body': 'Tyd om jou {medication_name} ({dosage}) te neem. Neem dit asseblief nou.',
                    'sms': 'MedGuard: Tyd om {medication_name} ({dosage}) te neem. Neem nou.',
                    'push': 'Medikasie Herinnering: {medication_name}'
                },
                'prescription_refill': {
                    'subject': 'Voorskrif Aanvulling Herinnering: {medication_name}',
                    'body': 'Jou voorskrif vir {medication_name} moet aangevul word. Kontak asseblief jou apteek.',
                    'sms': 'MedGuard: Aanvulling benodig vir {medication_name}. Kontak apteek.',
                    'push': 'Aanvulling Herinnering: {medication_name}'
                },
                'appointment_reminder': {
                    'subject': 'Afspraak Herinnering: {appointment_type}',
                    'body': 'Jy het \'n afspraak vir {appointment_type} op {appointment_date} om {appointment_time}.',
                    'sms': 'MedGuard: Afspraak herinnering - {appointment_type} op {appointment_date}.',
                    'push': 'Afspraak Herinnering: {appointment_type}'
                }
            }
        }
    
    def _load_template_variables(self) -> Dict[str, Dict[str, str]]:
        """Load template variable mappings for different languages."""
        return {
            'en-ZA': {
                'medication_name': 'medication_name',
                'dosage': 'dosage',
                'appointment_type': 'appointment_type',
                'appointment_date': 'appointment_date',
                'appointment_time': 'appointment_time',
                'pharmacy_name': 'pharmacy_name',
                'doctor_name': 'doctor_name'
            },
            'af-ZA': {
                'medication_name': 'medikasie_naam',
                'dosage': 'dosering',
                'appointment_type': 'afspraak_tipe',
                'appointment_date': 'afspraak_datum',
                'appointment_time': 'afspraak_tyd',
                'pharmacy_name': 'apteek_naam',
                'doctor_name': 'dokter_naam'
            }
        }
    
    def get_notification_template(
        self, 
        template_type: str, 
        language: str = 'en-ZA',
        notification_method: str = 'email'
    ) -> Dict[str, str]:
        """
        Get notification template for specific type and language.
        
        Args:
            template_type: Type of notification template
            language: Language code
            notification_method: Method of notification (email, sms, push)
            
        Returns:
            Dictionary containing template strings
        """
        templates = self.templates.get(language, self.templates['en-ZA'])
        template = templates.get(template_type, {})
        
        return {
            'subject': template.get('subject', ''),
            'body': template.get('body', ''),
            'sms': template.get('sms', ''),
            'push': template.get('push', ''),
            'method_specific': template.get(notification_method, template.get('body', ''))
        }
    
    def render_notification(
        self, 
        template_type: str, 
        variables: Dict[str, str],
        language: str = 'en-ZA',
        notification_method: str = 'email'
    ) -> Dict[str, str]:
        """
        Render notification with variables.
        
        Args:
            template_type: Type of notification template
            variables: Variables to substitute in template
            language: Language code
            notification_method: Method of notification
            
        Returns:
            Dictionary containing rendered notification strings
        """
        template = self.get_notification_template(template_type, language, notification_method)
        
        rendered = {}
        for key, template_string in template.items():
            try:
                rendered[key] = template_string.format(**variables)
            except KeyError as e:
                logger.error(f"Missing variable {e} in template {template_type}")
                rendered[key] = template_string
        
        return rendered

# =============================================================================
# 7. WAGTAIL 7.0.2 IMPROVED TRANSLATION SYNCING ACROSS PAGE HIERARCHIES
# =============================================================================

class TranslationHierarchySync:
    """
    Enhanced translation syncing across page hierarchies for Wagtail 7.0.2.
    
    This class provides advanced synchronization capabilities for maintaining
    translation consistency across complex page hierarchies.
    """
    
    def __init__(self):
        self.sync_strategies = self._load_sync_strategies()
    
    def _load_sync_strategies(self) -> Dict[str, Dict[str, Any]]:
        """Load synchronization strategies for different content types."""
        return {
            'cascade': {
                'description': 'Cascade translations down the hierarchy',
                'direction': 'down',
                'include_metadata': True,
                'include_content': True
            },
            'bubble': {
                'description': 'Bubble translations up the hierarchy',
                'direction': 'up',
                'include_metadata': True,
                'include_content': False
            },
            'bidirectional': {
                'description': 'Sync translations in both directions',
                'direction': 'both',
                'include_metadata': True,
                'include_content': True
            }
        }
    
    def sync_page_hierarchy_translations(
        self, 
        root_page: Page, 
        target_locale: str,
        strategy: str = 'cascade'
    ) -> Dict[str, Any]:
        """
        Sync translations across a page hierarchy.
        
        Args:
            root_page: The root page of the hierarchy
            target_locale: The target locale for synchronization
            strategy: The synchronization strategy to use
            
        Returns:
            Dictionary containing sync results
        """
        results = {
            'synced_pages': [],
            'failed_pages': [],
            'skipped_pages': [],
            'total_pages': 0
        }
        
        try:
            # Get all pages in the hierarchy
            hierarchy_pages = self._get_hierarchy_pages(root_page)
            results['total_pages'] = len(hierarchy_pages)
            
            # Apply synchronization strategy
            if strategy == 'cascade':
                self._cascade_sync(hierarchy_pages, target_locale, results)
            elif strategy == 'bubble':
                self._bubble_sync(hierarchy_pages, target_locale, results)
            elif strategy == 'bidirectional':
                self._bidirectional_sync(hierarchy_pages, target_locale, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error syncing page hierarchy translations: {e}")
            results['error'] = str(e)
            return results
    
    def _get_hierarchy_pages(self, root_page: Page) -> List[Page]:
        """Get all pages in the hierarchy starting from root page."""
        pages = [root_page]
        
        # Get all descendants
        descendants = root_page.get_descendants()
        pages.extend(descendants)
        
        return pages
    
    def _cascade_sync(self, pages: List[Page], target_locale: str, results: Dict[str, Any]):
        """Cascade translations down the hierarchy."""
        for page in pages:
            try:
                # Check if page has a translation
                translated_page = self._get_translated_page(page, target_locale)
                
                if translated_page:
                    # Update translation with parent's metadata
                    self._update_translation_metadata(translated_page, page)
                    results['synced_pages'].append({
                        'page_id': page.id,
                        'page_title': page.title,
                        'action': 'metadata_updated'
                    })
                else:
                    # Create new translation
                    new_translation = self._create_page_translation(page, target_locale)
                    if new_translation:
                        results['synced_pages'].append({
                            'page_id': page.id,
                            'page_title': page.title,
                            'action': 'translation_created',
                            'translation_id': new_translation.id
                        })
                    else:
                        results['failed_pages'].append({
                            'page_id': page.id,
                            'page_title': page.title,
                            'error': 'Failed to create translation'
                        })
                        
            except Exception as e:
                results['failed_pages'].append({
                    'page_id': page.id,
                    'page_title': page.title,
                    'error': str(e)
                })
    
    def _bubble_sync(self, pages: List[Page], target_locale: str, results: Dict[str, Any]):
        """Bubble translations up the hierarchy."""
        # Process pages in reverse order (children first)
        for page in reversed(pages):
            try:
                translated_page = self._get_translated_page(page, target_locale)
                
                if translated_page:
                    # Update parent with child's metadata
                    parent = page.get_parent()
                    if parent:
                        parent_translation = self._get_translated_page(parent, target_locale)
                        if parent_translation:
                            self._update_translation_metadata(parent_translation, translated_page)
                            results['synced_pages'].append({
                                'page_id': parent.id,
                                'page_title': parent.title,
                                'action': 'metadata_updated_from_child'
                            })
                            
            except Exception as e:
                results['failed_pages'].append({
                    'page_id': page.id,
                    'page_title': page.title,
                    'error': str(e)
                })
    
    def _bidirectional_sync(self, pages: List[Page], target_locale: str, results: Dict[str, Any]):
        """Sync translations in both directions."""
        # First cascade down
        self._cascade_sync(pages, target_locale, results)
        
        # Then bubble up
        self._bubble_sync(pages, target_locale, results)
    
    def _get_translated_page(self, page: Page, locale: str) -> Optional[Page]:
        """Get the translated version of a page."""
        try:
            from wagtail.models import Locale
            locale_obj = Locale.objects.get(language_code=locale)
            return page.get_translation(locale_obj)
        except Exception:
            return None
    
    def _create_page_translation(self, page: Page, locale: str) -> Optional[Page]:
        """Create a new translation for a page."""
        try:
            from wagtail.models import Locale
            locale_obj = Locale.objects.get(language_code=locale)
            return page.copy_for_translation(locale_obj)
        except Exception as e:
            logger.error(f"Error creating page translation: {e}")
            return None
    
    def _update_translation_metadata(self, translated_page: Page, source_page: Page):
        """Update translation metadata from source page."""
        # Update common metadata fields
        if hasattr(translated_page, 'meta_title') and hasattr(source_page, 'meta_title'):
            translated_page.meta_title = source_page.meta_title
        
        if hasattr(translated_page, 'meta_description') and hasattr(source_page, 'meta_description'):
            translated_page.meta_description = source_page.meta_description
        
        # Save the translation
        translated_page.save()

# =============================================================================
# 8. LOCALIZED ERROR MESSAGES AND VALIDATION TEXT FOR HEALTHCARE FORMS
# =============================================================================

class LocalizedFormValidation:
    """
    Localized error messages and validation text for healthcare forms.
    
    This class provides comprehensive form validation with localized
    error messages and validation text for healthcare applications.
    """
    
    def __init__(self):
        self.validation_messages = self._load_validation_messages()
        self.field_labels = self._load_field_labels()
    
    def _load_validation_messages(self) -> Dict[str, Dict[str, str]]:
        """Load validation messages for different languages."""
        return {
            'en-ZA': {
                'required_field': 'This field is required.',
                'invalid_email': 'Please enter a valid email address.',
                'invalid_phone': 'Please enter a valid phone number.',
                'invalid_date': 'Please enter a valid date.',
                'invalid_time': 'Please enter a valid time.',
                'invalid_number': 'Please enter a valid number.',
                'min_length': 'This field must be at least {min_length} characters long.',
                'max_length': 'This field must be no more than {max_length} characters long.',
                'invalid_medication_name': 'Please enter a valid medication name.',
                'invalid_dosage': 'Please enter a valid dosage amount.',
                'invalid_prescription': 'Please enter a valid prescription number.',
                'future_date_required': 'Please select a future date.',
                'past_date_required': 'Please select a past date.',
                'invalid_medical_aid': 'Please enter a valid medical aid number.',
                'invalid_id_number': 'Please enter a valid South African ID number.'
            },
            'af-ZA': {
                'required_field': 'Hierdie veld is verpligtend.',
                'invalid_email': 'Voer asseblief \'n geldige e-posadres in.',
                'invalid_phone': 'Voer asseblief \'n geldige telefoonnommer in.',
                'invalid_date': 'Voer asseblief \'n geldige datum in.',
                'invalid_time': 'Voer asseblief \'n geldige tyd in.',
                'invalid_number': 'Voer asseblief \'n geldige nommer in.',
                'min_length': 'Hierdie veld moet ten minste {min_length} karakters lank wees.',
                'max_length': 'Hierdie veld moet nie meer as {max_length} karakters lank wees nie.',
                'invalid_medication_name': 'Voer asseblief \'n geldige medikasie naam in.',
                'invalid_dosage': 'Voer asseblief \'n geldige dosering hoeveelheid in.',
                'invalid_prescription': 'Voer asseblief \'n geldige voorskrif nommer in.',
                'future_date_required': 'Kies asseblief \'n toekomstige datum.',
                'past_date_required': 'Kies asseblief \'n verlede datum.',
                'invalid_medical_aid': 'Voer asseblief \'n geldige mediese hulp nommer in.',
                'invalid_id_number': 'Voer asseblief \'n geldige Suid-Afrikaanse ID nommer in.'
            }
        }
    
    def _load_field_labels(self) -> Dict[str, Dict[str, str]]:
        """Load field labels for different languages."""
        return {
            'en-ZA': {
                'medication_name': 'Medication Name',
                'dosage': 'Dosage',
                'frequency': 'Frequency',
                'prescription_number': 'Prescription Number',
                'patient_name': 'Patient Name',
                'doctor_name': 'Doctor Name',
                'pharmacy_name': 'Pharmacy Name',
                'medical_aid_number': 'Medical Aid Number',
                'id_number': 'ID Number',
                'phone_number': 'Phone Number',
                'email_address': 'Email Address',
                'appointment_date': 'Appointment Date',
                'appointment_time': 'Appointment Time'
            },
            'af-ZA': {
                'medication_name': 'Medikasie Naam',
                'dosage': 'Dosering',
                'frequency': 'Frekwensie',
                'prescription_number': 'Voorskrif Nommer',
                'patient_name': 'Pasiënt Naam',
                'doctor_name': 'Dokter Naam',
                'pharmacy_name': 'Apteek Naam',
                'medical_aid_number': 'Mediese Hulp Nommer',
                'id_number': 'ID Nommer',
                'phone_number': 'Telefoon Nommer',
                'email_address': 'E-pos Adres',
                'appointment_date': 'Afspraak Datum',
                'appointment_time': 'Afspraak Tyd'
            }
        }
    
    def get_validation_message(
        self, 
        message_key: str, 
        language: str = 'en-ZA',
        **kwargs
    ) -> str:
        """
        Get localized validation message.
        
        Args:
            message_key: Key for the validation message
            language: Language code
            **kwargs: Variables to substitute in the message
            
        Returns:
            Localized validation message
        """
        messages = self.validation_messages.get(language, self.validation_messages['en-ZA'])
        message = messages.get(message_key, messages.get('required_field', 'This field is required.'))
        
        try:
            return message.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable {e} in validation message {message_key}")
            return message
    
    def get_field_label(self, field_name: str, language: str = 'en-ZA') -> str:
        """
        Get localized field label.
        
        Args:
            field_name: Name of the field
            language: Language code
            
        Returns:
            Localized field label
        """
        labels = self.field_labels.get(language, self.field_labels['en-ZA'])
        return labels.get(field_name, field_name)
    
    def validate_medication_form(
        self, 
        form_data: Dict[str, Any], 
        language: str = 'en-ZA'
    ) -> Dict[str, List[str]]:
        """
        Validate medication form data with localized error messages.
        
        Args:
            form_data: Form data to validate
            language: Language code for error messages
            
        Returns:
            Dictionary of field errors
        """
        errors = {}
        
        # Validate required fields
        required_fields = ['medication_name', 'dosage', 'frequency']
        for field in required_fields:
            if not form_data.get(field):
                errors[field] = [self.get_validation_message('required_field', language)]
        
        # Validate medication name
        medication_name = form_data.get('medication_name', '')
        if medication_name and len(medication_name) < 2:
            errors['medication_name'] = [self.get_validation_message('invalid_medication_name', language)]
        
        # Validate dosage
        dosage = form_data.get('dosage', '')
        if dosage:
            try:
                float(dosage)
            except ValueError:
                errors['dosage'] = [self.get_validation_message('invalid_dosage', language)]
        
        # Validate email if provided
        email = form_data.get('email_address', '')
        if email and '@' not in email:
            errors['email_address'] = [self.get_validation_message('invalid_email', language)]
        
        return errors

# =============================================================================
# 9. REGION-SPECIFIC COMPLIANCE AND LEGAL INFORMATION PAGES
# =============================================================================

class RegionalComplianceManager:
    """
    Region-specific compliance and legal information pages.
    
    This class manages compliance and legal information specific to
    South African healthcare regulations and requirements.
    """
    
    def __init__(self):
        self.compliance_requirements = self._load_compliance_requirements()
        self.legal_templates = self._load_legal_templates()
    
    def _load_compliance_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Load compliance requirements for different regions."""
        return {
            'gauteng': {
                'healthcare_regulations': [
                    'Health Professions Act 56 of 1974',
                    'Pharmacy Act 53 of 1974',
                    'Medicines and Related Substances Act 101 of 1965'
                ],
                'data_protection': [
                    'Protection of Personal Information Act (POPIA)',
                    'Health Information Privacy Guidelines'
                ],
                'licensing_requirements': [
                    'Pharmacy Council Registration',
                    'HPCSA Registration for Healthcare Professionals'
                ]
            },
            'western_cape': {
                'healthcare_regulations': [
                    'Health Professions Act 56 of 1974',
                    'Pharmacy Act 53 of 1974',
                    'Medicines and Related Substances Act 101 of 1965'
                ],
                'data_protection': [
                    'Protection of Personal Information Act (POPIA)',
                    'Western Cape Health Information Privacy Guidelines'
                ],
                'licensing_requirements': [
                    'Pharmacy Council Registration',
                    'HPCSA Registration for Healthcare Professionals'
                ]
            }
        }
    
    def _load_legal_templates(self) -> Dict[str, Dict[str, str]]:
        """Load legal templates for different languages."""
        return {
            'en-ZA': {
                'privacy_policy': 'Privacy Policy for MedGuard SA',
                'terms_of_service': 'Terms of Service for MedGuard SA',
                'data_protection': 'Data Protection and Privacy',
                'healthcare_compliance': 'Healthcare Compliance Information',
                'user_agreement': 'User Agreement and Consent',
                'disclaimer': 'Medical Information Disclaimer'
            },
            'af-ZA': {
                'privacy_policy': 'Privaatheid Beleid vir MedGuard SA',
                'terms_of_service': 'Diens Voorwaardes vir MedGuard SA',
                'data_protection': 'Data Beskerming en Privaatheid',
                'healthcare_compliance': 'Gesondheidsorg Nakoming Inligting',
                'user_agreement': 'Gebruiker Ooreenkoms en Toestemming',
                'disclaimer': 'Mediese Inligting Vrywaring'
            }
        }
    
    def get_compliance_requirements(self, region: str = 'gauteng') -> Dict[str, Any]:
        """
        Get compliance requirements for a specific region.
        
        Args:
            region: The region/province
            
        Returns:
            Dictionary of compliance requirements
        """
        return self.compliance_requirements.get(region, self.compliance_requirements['gauteng'])
    
    def get_legal_template(self, template_type: str, language: str = 'en-ZA') -> str:
        """
        Get legal template for specific type and language.
        
        Args:
            template_type: Type of legal template
            language: Language code
            
        Returns:
            Legal template string
        """
        templates = self.legal_templates.get(language, self.legal_templates['en-ZA'])
        return templates.get(template_type, '')

# =============================================================================
# 10. WAGTAIL 7.0.2 ENHANCED TRANSLATION ANALYTICS AND COMPLETION TRACKING
# =============================================================================

class TranslationAnalytics:
    """
    Enhanced translation analytics and completion tracking for Wagtail 7.0.2.
    
    This class provides comprehensive analytics and tracking capabilities
    for translation progress and completion across the platform.
    """
    
    def __init__(self):
        self.analytics_config = self._load_analytics_config()
    
    def _load_analytics_config(self) -> Dict[str, Any]:
        """Load analytics configuration."""
        return {
            'completion_thresholds': {
                'low': 0.25,
                'medium': 0.50,
                'high': 0.75,
                'complete': 1.0
            },
            'priority_levels': {
                'critical': 1.0,
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4
            }
        }
    
    def get_translation_completion_stats(
        self, 
        locale: str = None,
        content_type: str = None
    ) -> Dict[str, Any]:
        """
        Get translation completion statistics.
        
        Args:
            locale: Specific locale to analyze
            content_type: Specific content type to analyze
            
        Returns:
            Dictionary containing completion statistics
        """
        try:
            from wagtail.models import Page, Locale
            
            # Get all pages
            pages = Page.objects.all()
            
            if content_type:
                pages = pages.filter(content_type__model=content_type)
            
            # Get locale
            if locale:
                locale_obj = Locale.objects.get(language_code=locale)
                pages = pages.filter(locale=locale_obj)
            
            total_pages = pages.count()
            translated_pages = 0
            partially_translated = 0
            
            for page in pages:
                translation_status = self._get_page_translation_status(page)
                if translation_status['completion_rate'] == 1.0:
                    translated_pages += 1
                elif translation_status['completion_rate'] > 0:
                    partially_translated += 1
            
            completion_rate = translated_pages / total_pages if total_pages > 0 else 0
            
            return {
                'total_pages': total_pages,
                'translated_pages': translated_pages,
                'partially_translated': partially_translated,
                'completion_rate': completion_rate,
                'completion_level': self._get_completion_level(completion_rate)
            }
            
        except Exception as e:
            logger.error(f"Error getting translation completion stats: {e}")
            return {
                'error': str(e),
                'total_pages': 0,
                'translated_pages': 0,
                'completion_rate': 0
            }
    
    def _get_page_translation_status(self, page: Page) -> Dict[str, Any]:
        """
        Get translation status for a specific page.
        
        Args:
            page: The page to analyze
            
        Returns:
            Dictionary containing translation status
        """
        try:
            # Check if page has translations
            translations = page.get_translations()
            
            if not translations:
                return {
                    'has_translations': False,
                    'completion_rate': 0.0,
                    'missing_fields': ['all'],
                    'translation_count': 0
                }
            
            # Analyze translation completeness
            total_fields = 0
            translated_fields = 0
            missing_fields = []
            
            # Check common translatable fields
            translatable_fields = ['title', 'slug', 'intro', 'description', 'content']
            
            for field in translatable_fields:
                if hasattr(page, field):
                    total_fields += 1
                    field_value = getattr(page, field)
                    
                    if field_value and str(field_value).strip():
                        translated_fields += 1
                    else:
                        missing_fields.append(field)
            
            completion_rate = translated_fields / total_fields if total_fields > 0 else 0
            
            return {
                'has_translations': True,
                'completion_rate': completion_rate,
                'missing_fields': missing_fields,
                'translation_count': len(translations)
            }
            
        except Exception as e:
            logger.error(f"Error getting page translation status: {e}")
            return {
                'has_translations': False,
                'completion_rate': 0.0,
                'missing_fields': ['error'],
                'translation_count': 0
            }
    
    def _get_completion_level(self, completion_rate: float) -> str:
        """
        Get completion level based on completion rate.
        
        Args:
            completion_rate: The completion rate (0.0 to 1.0)
            
        Returns:
            Completion level string
        """
        thresholds = self.analytics_config['completion_thresholds']
        
        if completion_rate >= thresholds['complete']:
            return 'complete'
        elif completion_rate >= thresholds['high']:
            return 'high'
        elif completion_rate >= thresholds['medium']:
            return 'medium'
        elif completion_rate >= thresholds['low']:
            return 'low'
        else:
            return 'none'
    
    def generate_translation_report(
        self, 
        locale: str = None,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """
        Generate comprehensive translation report.
        
        Args:
            locale: Specific locale to report on
            include_details: Whether to include detailed information
            
        Returns:
            Dictionary containing translation report
        """
        try:
            # Get completion stats
            stats = self.get_translation_completion_stats(locale)
            
            report = {
                'generated_at': timezone.now().isoformat(),
                'locale': locale or 'all',
                'summary': stats,
                'recommendations': self._generate_recommendations(stats)
            }
            
            if include_details:
                report['details'] = self._get_detailed_analysis(locale)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating translation report: {e}")
            return {
                'error': str(e),
                'generated_at': timezone.now().isoformat()
            }
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on translation statistics.
        
        Args:
            stats: Translation statistics
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        completion_rate = stats.get('completion_rate', 0)
        
        if completion_rate < 0.25:
            recommendations.append('Prioritize translation of critical content pages')
            recommendations.append('Consider hiring additional translators')
        elif completion_rate < 0.50:
            recommendations.append('Focus on completing high-priority content')
            recommendations.append('Review translation quality and consistency')
        elif completion_rate < 0.75:
            recommendations.append('Complete remaining content translations')
            recommendations.append('Implement translation review process')
        else:
            recommendations.append('Maintain translation quality standards')
            recommendations.append('Regularly update translations for new content')
        
        return recommendations
    
    def _get_detailed_analysis(self, locale: str = None) -> Dict[str, Any]:
        """
        Get detailed translation analysis.
        
        Args:
            locale: Specific locale to analyze
            
        Returns:
            Dictionary containing detailed analysis
        """
        try:
            from wagtail.models import Page, Locale
            
            # Get pages that need translation
            pages = Page.objects.all()
            if locale:
                locale_obj = Locale.objects.get(language_code=locale)
                pages = pages.filter(locale=locale_obj)
            
            pages_needing_translation = []
            pages_with_issues = []
            
            for page in pages[:100]:  # Limit to first 100 pages for performance
                status = self._get_page_translation_status(page)
                
                if status['completion_rate'] < 1.0:
                    pages_needing_translation.append({
                        'page_id': page.id,
                        'page_title': page.title,
                        'completion_rate': status['completion_rate'],
                        'missing_fields': status['missing_fields']
                    })
                
                if status['missing_fields']:
                    pages_with_issues.append({
                        'page_id': page.id,
                        'page_title': page.title,
                        'issues': status['missing_fields']
                    })
            
            return {
                'pages_needing_translation': pages_needing_translation,
                'pages_with_issues': pages_with_issues,
                'total_analyzed': len(pages)
            }
            
        except Exception as e:
            logger.error(f"Error getting detailed analysis: {e}")
            return {
                'error': str(e),
                'pages_needing_translation': [],
                'pages_with_issues': []
            } 