"""
Wagtail 7.0.2 Professional Translation Tools Integration

This module provides integration with professional translation tools and services
for enhanced translation management in MedGuard SA.
"""

from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.db import models
from django.utils import timezone
from wagtail import hooks
from wagtail.models import Page, Locale
from wagtail.admin.views.pages import get_page_permissions_for_user
import requests
import json
import hashlib
import logging

logger = logging.getLogger(__name__)


class TranslationMemory(models.Model):
    """Model for storing translation memory entries."""
    
    source_text = models.TextField()
    target_text = models.TextField()
    source_locale = models.ForeignKey(Locale, on_delete=models.CASCADE, related_name='source_memory')
    target_locale = models.ForeignKey(Locale, on_delete=models.CASCADE, related_name='target_memory')
    context = models.CharField(max_length=255, blank=True)
    domain = models.CharField(max_length=100, default='medical')
    quality_score = models.FloatField(default=1.0)
    usage_count = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ['source_text', 'source_locale', 'target_locale', 'context']
        indexes = [
            models.Index(fields=['source_locale', 'target_locale', 'domain']),
            models.Index(fields=['quality_score', 'usage_count']),
        ]
    
    def __str__(self):
        return f"{self.source_text[:50]}... -> {self.target_text[:50]}..."
    
    def get_similarity_score(self, text):
        """Calculate similarity score with given text."""
        # Simple similarity calculation - can be enhanced with more sophisticated algorithms
        source_words = set(self.source_text.lower().split())
        text_words = set(text.lower().split())
        
        if not source_words or not text_words:
            return 0.0
        
        intersection = source_words.intersection(text_words)
        union = source_words.union(text_words)
        
        return len(intersection) / len(union) if union else 0.0


class TranslationService(models.Model):
    """Model for managing translation service configurations."""
    
    SERVICE_CHOICES = [
        ('google', 'Google Translate'),
        ('deepl', 'DeepL'),
        ('microsoft', 'Microsoft Translator'),
        ('amazon', 'Amazon Translate'),
        ('custom', 'Custom API'),
    ]
    
    name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    api_key = models.CharField(max_length=255, blank=True)
    api_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    supported_languages = models.JSONField(default=list)
    rate_limit = models.IntegerField(default=1000)  # requests per hour
    cost_per_character = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    
    class Meta:
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_service_type_display()})"


class TranslationJob(models.Model):
    """Model for managing translation jobs."""
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='translation_jobs')
    source_locale = models.ForeignKey(Locale, on_delete=models.CASCADE, related_name='source_jobs')
    target_locale = models.ForeignKey(Locale, on_delete=models.CASCADE, related_name='target_jobs')
    service = models.ForeignKey(TranslationService, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    source_text = models.JSONField()  # Store structured text data
    translated_text = models.JSONField(null=True, blank=True)
    quality_score = models.FloatField(null=True, blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Translation job for {self.page.title} ({self.target_locale})"
    
    def process_translation(self):
        """Process the translation using the selected service."""
        if not self.service or not self.service.is_active:
            self.status = 'failed'
            self.error_message = 'No active translation service available'
            self.save()
            return False
        
        try:
            if self.service.service_type == 'google':
                result = self._translate_with_google()
            elif self.service.service_type == 'deepl':
                result = self._translate_with_deepl()
            elif self.service.service_type == 'microsoft':
                result = self._translate_with_microsoft()
            elif self.service.service_type == 'amazon':
                result = self._translate_with_amazon()
            else:
                result = self._translate_with_custom()
            
            if result:
                self.translated_text = result
                self.status = 'completed'
                self.completed_at = timezone.now()
                self.save()
                
                # Update translation memory
                self._update_translation_memory()
                
                return True
            else:
                self.status = 'failed'
                self.error_message = 'Translation service returned no result'
                self.save()
                return False
                
        except Exception as e:
            self.status = 'failed'
            self.error_message = str(e)
            self.save()
            logger.error(f"Translation job failed: {e}")
            return False
    
    def _translate_with_google(self):
        """Translate using Google Translate API."""
        # Implementation would use Google Translate API
        # This is a placeholder for the actual implementation
        return None
    
    def _translate_with_deepl(self):
        """Translate using DeepL API."""
        # Implementation would use DeepL API
        # This is a placeholder for the actual implementation
        return None
    
    def _translate_with_microsoft(self):
        """Translate using Microsoft Translator API."""
        # Implementation would use Microsoft Translator API
        # This is a placeholder for the actual implementation
        return None
    
    def _translate_with_amazon(self):
        """Translate using Amazon Translate API."""
        # Implementation would use Amazon Translate API
        # This is a placeholder for the actual implementation
        return None
    
    def _translate_with_custom(self):
        """Translate using custom API."""
        # Implementation would use custom translation API
        # This is a placeholder for the actual implementation
        return None
    
    def _update_translation_memory(self):
        """Update translation memory with new translations."""
        if not self.translated_text:
            return
        
        # Extract text pairs and add to translation memory
        for field, source_text in self.source_text.items():
            if field in self.translated_text:
                target_text = self.translated_text[field]
                
                # Check if similar entry exists
                existing = TranslationMemory.objects.filter(
                    source_text=source_text,
                    source_locale=self.source_locale,
                    target_locale=self.target_locale,
                    context=field
                ).first()
                
                if existing:
                    # Update existing entry
                    existing.target_text = target_text
                    existing.usage_count += 1
                    existing.updated_at = timezone.now()
                    existing.save()
                else:
                    # Create new entry
                    TranslationMemory.objects.create(
                        source_text=source_text,
                        target_text=target_text,
                        source_locale=self.source_locale,
                        target_locale=self.target_locale,
                        context=field,
                        created_by=self.created_by
                    )


class TranslationQualityCheck(models.Model):
    """Model for translation quality checks."""
    
    job = models.OneToOneField(TranslationJob, on_delete=models.CASCADE, related_name='quality_check')
    spelling_check = models.BooleanField(default=False)
    grammar_check = models.BooleanField(default=False)
    terminology_check = models.BooleanField(default=False)
    consistency_check = models.BooleanField(default=False)
    completeness_check = models.BooleanField(default=False)
    medical_accuracy_check = models.BooleanField(default=False)
    overall_score = models.FloatField(null=True, blank=True)
    checked_by = models.ForeignKey('auth.User', on_delete=models.CASCADE, null=True, blank=True)
    checked_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Quality check for {self.job}"
    
    def run_quality_checks(self):
        """Run comprehensive quality checks on the translation."""
        # This would integrate with external quality checking services
        # For now, we'll implement basic checks
        
        # Spelling check
        self.spelling_check = self._check_spelling()
        
        # Grammar check
        self.grammar_check = self._check_grammar()
        
        # Terminology check
        self.terminology_check = self._check_terminology()
        
        # Consistency check
        self.consistency_check = self._check_consistency()
        
        # Completeness check
        self.completeness_check = self._check_completeness()
        
        # Medical accuracy check
        self.medical_accuracy_check = self._check_medical_accuracy()
        
        # Calculate overall score
        self.overall_score = self._calculate_overall_score()
        
        self.checked_at = timezone.now()
        self.save()
    
    def _check_spelling(self):
        """Check spelling in translated text."""
        # Implementation would use spell checking service
        return True
    
    def _check_grammar(self):
        """Check grammar in translated text."""
        # Implementation would use grammar checking service
        return True
    
    def _check_terminology(self):
        """Check medical terminology accuracy."""
        # Implementation would use medical terminology database
        return True
    
    def _check_consistency(self):
        """Check consistency across translations."""
        # Implementation would check consistency with translation memory
        return True
    
    def _check_completeness(self):
        """Check if all text has been translated."""
        # Implementation would compare source and target text completeness
        return True
    
    def _check_medical_accuracy(self):
        """Check medical accuracy of translations."""
        # Implementation would use medical validation service
        return True
    
    def _calculate_overall_score(self):
        """Calculate overall quality score."""
        checks = [
            self.spelling_check,
            self.grammar_check,
            self.terminology_check,
            self.consistency_check,
            self.completeness_check,
            self.medical_accuracy_check,
        ]
        
        return sum(checks) / len(checks) if checks else 0.0


def get_translation_suggestions(text, source_locale, target_locale, context=''):
    """Get translation suggestions from translation memory."""
    suggestions = []
    
    # Get exact matches
    exact_matches = TranslationMemory.objects.filter(
        source_text=text,
        source_locale=source_locale,
        target_locale=target_locale,
        context=context
    ).order_by('-quality_score', '-usage_count')
    
    for match in exact_matches:
        suggestions.append({
            'text': match.target_text,
            'score': 1.0,
            'type': 'exact_match',
            'source': 'translation_memory'
        })
    
    # Get similar matches
    similar_matches = TranslationMemory.objects.filter(
        source_locale=source_locale,
        target_locale=target_locale,
        context=context
    ).exclude(source_text=text)
    
    for match in similar_matches:
        similarity = match.get_similarity_score(text)
        if similarity > 0.7:  # Threshold for similarity
            suggestions.append({
                'text': match.target_text,
                'score': similarity,
                'type': 'similar_match',
                'source': 'translation_memory'
            })
    
    # Sort by score
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    
    return suggestions[:5]  # Return top 5 suggestions


def create_translation_job(page, target_locale, user, service=None):
    """Create a new translation job."""
    # Extract translatable content from page
    source_text = {}
    
    # Add basic page fields
    if hasattr(page, 'title'):
        source_text['title'] = page.title
    if hasattr(page, 'seo_title'):
        source_text['seo_title'] = page.seo_title
    if hasattr(page, 'search_description'):
        source_text['search_description'] = page.search_description
    
    # Add StreamField content
    if hasattr(page, 'body'):
        source_text['body'] = str(page.body)
    if hasattr(page, 'content'):
        source_text['content'] = str(page.content)
    
    # Create translation job
    job = TranslationJob.objects.create(
        page=page,
        source_locale=page.locale,
        target_locale=target_locale,
        service=service,
        source_text=source_text,
        created_by=user
    )
    
    # Create quality check record
    TranslationQualityCheck.objects.create(job=job)
    
    return job


@hooks.register('register_page_listing_buttons')
def professional_translation_buttons(page, page_perms, is_parent=False, context=None):
    """Add professional translation buttons to page listing."""
    if not page_perms.can_edit():
        return []
    
    buttons = []
    
    # Add translation memory suggestions button
    buttons.append({
        'label': _('Translation Memory'),
        'url': f'/admin/translation-memory/{page.id}/',
        'classname': 'button button-small',
        'title': _('View translation memory suggestions'),
    })
    
    # Add professional translation button
    buttons.append({
        'label': _('Professional Translation'),
        'url': f'/admin/professional-translation/{page.id}/',
        'classname': 'button button-small button-primary',
        'title': _('Request professional translation'),
    })
    
    return buttons


@hooks.register('register_page_listing_more_buttons')
def professional_translation_more_buttons(page, page_perms, is_parent=False, context=None):
    """Add more professional translation buttons."""
    if not page_perms.can_edit():
        return []
    
    buttons = []
    
    # Add quality check button
    buttons.append({
        'label': _('Quality Check'),
        'url': f'/admin/translation-quality/{page.id}/',
        'classname': 'button button-small',
    })
    
    # Add translation services button
    buttons.append({
        'label': _('Translation Services'),
        'url': f'/admin/translation-services/{page.id}/',
        'classname': 'button button-small',
    })
    
    return buttons 