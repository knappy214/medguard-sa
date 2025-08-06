"""
Wagtail 7.0.2 Page Models for MedGuard SA Medication Management System.

This module contains page models for medication-related functionality including:
- PrescriptionFormPage: Interactive prescription submission with Wagtail forms
- MedicationComparisonPage: Side-by-side medication comparison with StreamField
- PharmacyLocatorPage: Pharmacy finder with Wagtail's geolocation features
- MedicationGuideIndexPage: Medication guides with Wagtail 7.0.2 filtering
- PrescriptionHistoryPage: Patient prescription history with privacy controls
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from decimal import Decimal
import uuid

# Wagtail imports - Enhanced for 7.0.2
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.blocks import (
    CharBlock, TextBlock, IntegerBlock, DecimalBlock, BooleanBlock,
    DateBlock, TimeBlock, ChoiceBlock, URLBlock, EmailBlock,
    StructBlock, ListBlock, StreamBlock, PageChooserBlock,
    RawHTMLBlock, StaticBlock, RichTextBlock
)
from wagtail.images.blocks import ImageChooserBlock
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.images.models import Image
from wagtail.contrib.forms.models import AbstractForm, AbstractFormField
from wagtail.contrib.forms.panels import FormSubmissionsPanel
from wagtail.blocks.field_block import FieldBlock
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.rich_text import expand_db_html
from wagtail.contrib.settings.models import BaseSetting, register_setting
import re

User = get_user_model()


# Enhanced validation mixin for StructBlock
class MedicationValidationMixin:
    """Mixin providing enhanced validation for medication blocks."""
    
    def clean(self, value):
        """Enhanced validation with custom error messages."""
        cleaned_data = super().clean(value)
        
        # Validate medication name format
        if 'name' in cleaned_data and cleaned_data['name']:
            name = cleaned_data['name']
            if not re.match(r'^[A-Za-z0-9\s\-\.\(\)]+$', name):
                raise StructBlockValidationError(
                    block_errors={'name': 'Medication name contains invalid characters'}
                )
        
        return cleaned_data


# Enhanced StreamField blocks for Wagtail 7.0.2
class MedicationComparisonBlock(MedicationValidationMixin, StructBlock):
    """Enhanced medication comparison block with better validation."""
    
    medication_name = CharBlock(
        max_length=200,
        help_text=_('Name of the medication'),
        label=_('Medication Name'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Medication name contains invalid characters'
        )]
    )
    
    dosage_info = CharBlock(
        max_length=100,
        help_text=_('Dosage information'),
        label=_('Dosage')
    )
    
    side_effects = TextBlock(
        help_text=_('Side effects'),
        label=_('Side Effects'),
        max_length=500
    )
    
    cost = CharBlock(
        max_length=100,
        help_text=_('Cost information'),
        label=_('Cost')
    )
    
    efficacy = ChoiceBlock(
        choices=[
            ('excellent', _('Excellent')),
            ('good', _('Good')),
            ('fair', _('Fair')),
            ('poor', _('Poor')),
        ],
        default='good',
        help_text=_('Efficacy rating'),
        label=_('Efficacy')
    )
    
    notes = RichTextBlock(
        features=['bold', 'italic', 'link'],
        help_text=_('Additional notes'),
        label=_('Notes'),
        max_length=1000
    )
    
    class Meta:
        template = 'medications/blocks/medication_comparison_block.html'
        icon = 'medication'
        label = _('Medication Comparison')


class PharmacyLocationBlock(StructBlock):
    """Pharmacy location block with geolocation features."""
    
    pharmacy_name = CharBlock(
        max_length=200,
        help_text=_('Name of the pharmacy'),
        label=_('Pharmacy Name')
    )
    
    address = TextBlock(
        help_text=_('Full address'),
        label=_('Address'),
        max_length=500
    )
    
    phone = CharBlock(
        max_length=20,
        help_text=_('Phone number'),
        label=_('Phone'),
        required=False
    )
    
    email = EmailBlock(
        help_text=_('Email address'),
        label=_('Email'),
        required=False
    )
    
    website = URLBlock(
        help_text=_('Website URL'),
        label=_('Website'),
        required=False
    )
    
    hours = TextBlock(
        help_text=_('Operating hours'),
        label=_('Hours'),
        max_length=200,
        required=False
    )
    
    services = ListBlock(
        ChoiceBlock([
            ('prescription', _('Prescription Services')),
            ('consultation', _('Pharmacy Consultation')),
            ('delivery', _('Home Delivery')),
            ('emergency', _('Emergency Services')),
            ('vaccination', _('Vaccination Services')),
            ('testing', _('Health Testing')),
        ]),
        help_text=_('Available services'),
        label=_('Services')
    )
    
    class Meta:
        template = 'medications/blocks/pharmacy_location_block.html'
        icon = 'location'
        label = _('Pharmacy Location')


class MedicationGuideBlock(StructBlock):
    """Medication guide block with comprehensive information."""
    
    title = CharBlock(
        max_length=200,
        help_text=_('Guide title'),
        label=_('Title')
    )
    
    category = ChoiceBlock([
        ('general', _('General Information')),
        ('dosage', _('Dosage Guide')),
        ('side_effects', _('Side Effects')),
        ('interactions', _('Drug Interactions')),
        ('storage', _('Storage Guide')),
        ('administration', _('Administration Guide')),
        ('safety', _('Safety Information')),
    ], help_text=_('Guide category'), label=_('Category'))
    
    content = RichTextBlock(
        features=['bold', 'italic', 'link', 'ul', 'ol', 'h3', 'h4'],
        help_text=_('Guide content'),
        label=_('Content'),
        max_length=5000
    )
    
    difficulty_level = ChoiceBlock([
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
    ], default='beginner', help_text=_('Difficulty level'), label=_('Level'))
    
    class Meta:
        template = 'medications/blocks/medication_guide_block.html'
        icon = 'help'
        label = _('Medication Guide')


class PrescriptionHistoryBlock(StructBlock):
    """Prescription history block with privacy controls."""
    
    prescription_date = DateBlock(
        help_text=_('Date of prescription'),
        label=_('Prescription Date')
    )
    
    medication_name = CharBlock(
        max_length=200,
        help_text=_('Medication name'),
        label=_('Medication')
    )
    
    prescribed_by = CharBlock(
        max_length=200,
        help_text=_('Prescribing doctor'),
        label=_('Prescribed By')
    )
    
    dosage = CharBlock(
        max_length=100,
        help_text=_('Prescribed dosage'),
        label=_('Dosage')
    )
    
    status = ChoiceBlock([
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('discontinued', _('Discontinued')),
        ('expired', _('Expired')),
    ], default='active', help_text=_('Prescription status'), label=_('Status'))
    
    notes = TextBlock(
        help_text=_('Additional notes'),
        label=_('Notes'),
        max_length=1000,
        required=False
    )
    
    class Meta:
        template = 'medications/blocks/prescription_history_block.html'
        icon = 'history'
        label = _('Prescription History')


# StreamField content blocks
class PrescriptionFormStreamBlock(StreamBlock):
    """StreamField for prescription form content."""
    
    description = RichTextBlock(
        help_text=_('Form description and instructions'),
        label=_('Description'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=2000
    )
    
    warning = RichTextBlock(
        help_text=_('Important warnings'),
        label=_('Warnings'),
        features=['bold', 'italic'],
        max_length=1000
    )
    
    class Meta:
        block_counts = {
            'description': {'max_num': 1},
            'warning': {'max_num': 3},
        }


class MedicationComparisonStreamBlock(StreamBlock):
    """StreamField for medication comparison content."""
    
    comparison = ListBlock(MedicationComparisonBlock(), min_num=2, max_num=10)
    notes = RichTextBlock(
        help_text=_('Comparison notes'),
        label=_('Notes'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=2000
    )
    
    class Meta:
        block_counts = {
            'comparison': {'min_num': 1, 'max_num': 1},
            'notes': {'max_num': 1},
        }


class PharmacyLocatorStreamBlock(StreamBlock):
    """StreamField for pharmacy locator content."""
    
    introduction = RichTextBlock(
        help_text=_('Introduction text'),
        label=_('Introduction'),
        features=['bold', 'italic', 'link'],
        max_length=1500
    )
    
    pharmacy = ListBlock(PharmacyLocationBlock(), min_num=1, max_num=50)
    
    class Meta:
        block_counts = {
            'introduction': {'max_num': 1},
            'pharmacy': {'min_num': 1},
        }


class MedicationGuideStreamBlock(StreamBlock):
    """StreamField for medication guide content."""
    
    guide = ListBlock(MedicationGuideBlock(), min_num=1, max_num=100)
    
    class Meta:
        block_counts = {
            'guide': {'min_num': 1},
        }


class PrescriptionHistoryStreamBlock(StreamBlock):
    """StreamField for prescription history content."""
    
    history = ListBlock(PrescriptionHistoryBlock(), min_num=0, max_num=1000)
    
    class Meta:
        block_counts = {
            'history': {'min_num': 0},
        }


# Form field models for prescription form
class PrescriptionFormField(AbstractFormField):
    """Custom form field for prescription form."""
    
    page = models.ForeignKey(
        'PrescriptionFormPage',
        on_delete=models.CASCADE,
        related_name='form_fields'
    )


# Page Models
class PrescriptionFormPage(AbstractForm):
    """
    Interactive prescription submission page with Wagtail forms.
    
    This page provides a comprehensive form for prescription submission
    with enhanced validation and user experience features.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for the prescription form'),
        blank=True
    )
    
    content = StreamField(
        PrescriptionFormStreamBlock(),
        verbose_name=_('Page Content'),
        help_text=_('Rich content for the prescription form page'),
        blank=True,
        use_json_field=True  # Wagtail 7.0.2 performance improvement
    )
    
    # Form configuration
    thank_you_text = RichTextField(
        verbose_name=_('Thank You Text'),
        help_text=_('Text to display after successful form submission'),
        blank=True
    )
    
    # Privacy and security
    require_authentication = models.BooleanField(
        default=True,
        verbose_name=_('Require Authentication'),
        help_text=_('Whether users must be logged in to submit the form')
    )
    
    enable_captcha = models.BooleanField(
        default=True,
        verbose_name=_('Enable CAPTCHA'),
        help_text=_('Whether to show CAPTCHA for spam protection')
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
        index.SearchField('content', boost=1.5),
        index.SearchField('thank_you_text', boost=1.0),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('content'),
        FieldPanel('thank_you_text'),
        MultiFieldPanel([
            FieldPanel('require_authentication'),
            FieldPanel('enable_captcha'),
        ], heading=_('Form Settings')),
        InlinePanel('form_fields', label=_('Form Fields')),
    ]
    
    # Form submissions panel
    promote_panels = Page.promote_panels + [
        FormSubmissionsPanel(),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Prescription Form Page')
        verbose_name_plural = _('Prescription Form Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with form validation and user data."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add user information if authenticated
        if request.user.is_authenticated:
            context['user_profile'] = {
                'name': f"{request.user.first_name} {request.user.last_name}".strip(),
                'email': request.user.email,
                'phone': getattr(request.user, 'phone', ''),
            }
        
        return context
    
    def serve(self, request, *args, **kwargs):
        """Enhanced serve method with authentication check."""
        if self.require_authentication and not request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(f"{reverse('login')}?next={request.path}")
        
        return super().serve(request, *args, **kwargs)


class MedicationComparisonPage(Page):
    """
    Side-by-side medication comparison page with StreamField.
    
    This page allows users to compare different medications
    with comprehensive information and visual aids.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for medication comparison'),
        blank=True
    )
    
    content = StreamField(
        MedicationComparisonStreamBlock(),
        verbose_name=_('Comparison Content'),
        help_text=_('Medication comparison content'),
        blank=True,
        use_json_field=True
    )
    
    # Comparison settings
    enable_interactive_comparison = models.BooleanField(
        default=True,
        verbose_name=_('Enable Interactive Comparison'),
        help_text=_('Allow users to add/remove medications for comparison')
    )
    
    max_comparison_items = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Maximum Comparison Items'),
        help_text=_('Maximum number of medications that can be compared'),
        validators=[MinValueValidator(2), MaxValueValidator(10)]
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
        index.SearchField('content', boost=1.5),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('content'),
        MultiFieldPanel([
            FieldPanel('enable_interactive_comparison'),
            FieldPanel('max_comparison_items'),
        ], heading=_('Comparison Settings')),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Medication Comparison Page')
        verbose_name_plural = _('Medication Comparison Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with comparison data."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add comparison session data
        comparison_data = request.session.get('medication_comparison', [])
        context['comparison_data'] = comparison_data
        context['max_items'] = self.max_comparison_items
        
        return context


class PharmacyLocatorPage(Page):
    """
    Pharmacy finder page with Wagtail's geolocation features.
    
    This page helps users find nearby pharmacies with
    location-based search and mapping capabilities.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for pharmacy locator'),
        blank=True
    )
    
    content = StreamField(
        PharmacyLocatorStreamBlock(),
        verbose_name=_('Pharmacy Content'),
        help_text=_('Pharmacy location content'),
        blank=True,
        use_json_field=True
    )
    
    # Geolocation settings
    enable_location_services = models.BooleanField(
        default=True,
        verbose_name=_('Enable Location Services'),
        help_text=_('Allow users to use their current location')
    )
    
    search_radius_km = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Search Radius (km)'),
        help_text=_('Default search radius in kilometers'),
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
        index.SearchField('content', boost=1.5),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('content'),
        MultiFieldPanel([
            FieldPanel('enable_location_services'),
            FieldPanel('search_radius_km'),
        ], heading=_('Location Settings')),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Pharmacy Locator Page')
        verbose_name_plural = _('Pharmacy Locator Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with location data."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add location settings
        context['location_settings'] = {
            'enabled': self.enable_location_services,
            'radius': self.search_radius_km,
        }
        
        return context


class MedicationGuideIndexPage(Page):
    """
    Medication guides index page with Wagtail 7.0.2 filtering.
    
    This page provides a comprehensive index of medication guides
    with advanced filtering and search capabilities.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for medication guides'),
        blank=True
    )
    
    content = StreamField(
        MedicationGuideStreamBlock(),
        verbose_name=_('Guide Content'),
        help_text=_('Medication guide content'),
        blank=True,
        use_json_field=True
    )
    
    # Filtering settings
    enable_category_filter = models.BooleanField(
        default=True,
        verbose_name=_('Enable Category Filter'),
        help_text=_('Allow filtering by guide category')
    )
    
    enable_difficulty_filter = models.BooleanField(
        default=True,
        verbose_name=_('Enable Difficulty Filter'),
        help_text=_('Allow filtering by difficulty level')
    )
    
    items_per_page = models.PositiveIntegerField(
        default=12,
        verbose_name=_('Items Per Page'),
        help_text=_('Number of guides to show per page'),
        validators=[MinValueValidator(1), MaxValueValidator(50)]
    )
    
    # Enhanced search configuration with Wagtail 7.0.2 filtering
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
        index.SearchField('content', boost=1.5),
        index.FilterField('guide_category'),
        index.FilterField('difficulty_level'),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('content'),
        MultiFieldPanel([
            FieldPanel('enable_category_filter'),
            FieldPanel('enable_difficulty_filter'),
            FieldPanel('items_per_page'),
        ], heading=_('Filtering Settings')),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = ['medications.MedicationGuideDetailPage']
    
    class Meta:
        verbose_name = _('Medication Guide Index Page')
        verbose_name_plural = _('Medication Guide Index Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with filtering data."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add filter settings
        context['filter_settings'] = {
            'category_enabled': self.enable_category_filter,
            'difficulty_enabled': self.enable_difficulty_filter,
            'items_per_page': self.items_per_page,
        }
        
        return context


class MedicationGuideDetailPage(Page):
    """
    Individual medication guide detail page.
    """
    
    # Guide content
    content = StreamField(
        MedicationGuideStreamBlock(),
        verbose_name=_('Guide Content'),
        help_text=_('Detailed guide content'),
        blank=True,
        use_json_field=True
    )
    
    # Guide metadata
    category = models.CharField(
        max_length=50,
        choices=[
            ('general', _('General Information')),
            ('dosage', _('Dosage Guide')),
            ('side_effects', _('Side Effects')),
            ('interactions', _('Drug Interactions')),
            ('storage', _('Storage Guide')),
            ('administration', _('Administration Guide')),
            ('safety', _('Safety Information')),
        ],
        default='general',
        verbose_name=_('Category')
    )
    
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', _('Beginner')),
            ('intermediate', _('Intermediate')),
            ('advanced', _('Advanced')),
        ],
        default='beginner',
        verbose_name=_('Difficulty Level')
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('content', boost=1.5),
        index.FilterField('category'),
        index.FilterField('difficulty_level'),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('content'),
        FieldPanel('category'),
        FieldPanel('difficulty_level'),
    ]
    
    # Page configuration
    parent_page_types = ['medications.MedicationGuideIndexPage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Medication Guide Detail Page')
        verbose_name_plural = _('Medication Guide Detail Pages')


class PrescriptionHistoryPage(Page):
    """
    Patient prescription history page with privacy controls.
    
    This page displays prescription history with enhanced
    privacy controls and HIPAA compliance features.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for prescription history'),
        blank=True
    )
    
    content = StreamField(
        PrescriptionHistoryStreamBlock(),
        verbose_name=_('History Content'),
        help_text=_('Prescription history content'),
        blank=True,
        use_json_field=True
    )
    
    # Privacy and security settings
    require_authentication = models.BooleanField(
        default=True,
        verbose_name=_('Require Authentication'),
        help_text=_('Users must be logged in to view history')
    )
    
    enable_audit_logging = models.BooleanField(
        default=True,
        verbose_name=_('Enable Audit Logging'),
        help_text=_('Log all access to prescription history')
    )
    
    data_retention_days = models.PositiveIntegerField(
        default=2555,  # 7 years for HIPAA compliance
        verbose_name=_('Data Retention (Days)'),
        help_text=_('Number of days to retain prescription history data'),
        validators=[MinValueValidator(365), MaxValueValidator(3650)]
    )
    
    # Display settings
    items_per_page = models.PositiveIntegerField(
        default=20,
        verbose_name=_('Items Per Page'),
        help_text=_('Number of prescriptions to show per page'),
        validators=[MinValueValidator(5), MaxValueValidator(100)]
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
        index.SearchField('content', boost=1.5),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('content'),
        MultiFieldPanel([
            FieldPanel('require_authentication'),
            FieldPanel('enable_audit_logging'),
            FieldPanel('data_retention_days'),
            FieldPanel('items_per_page'),
        ], heading=_('Privacy & Display Settings')),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Prescription History Page')
        verbose_name_plural = _('Prescription History Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with privacy controls."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add privacy settings
        context['privacy_settings'] = {
            'require_auth': self.require_authentication,
            'audit_logging': self.enable_audit_logging,
            'items_per_page': self.items_per_page,
        }
        
        # Add user prescription data if authenticated
        if request.user.is_authenticated:
            from .models import Prescription
            prescriptions = Prescription.objects.filter(
                patient=request.user
            ).order_by('-prescribed_date')[:self.items_per_page]
            context['user_prescriptions'] = prescriptions
        
        return context
    
    def serve(self, request, *args, **kwargs):
        """Enhanced serve method with authentication and audit logging."""
        if self.require_authentication and not request.user.is_authenticated:
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(f"{reverse('login')}?next={request.path}")
        
        # Log access if audit logging is enabled
        if self.enable_audit_logging and request.user.is_authenticated:
            from security.audit import log_audit_event
            log_audit_event(
                user=request.user,
                action='prescription_history_access',
                resource=f'page:{self.id}',
                details={'page_title': self.title}
            )
        
        return super().serve(request, *args, **kwargs)


class MedicationInteractionPage(Page):
    """
    Drug interaction checker page with dynamic content.
    
    This page allows users to check for potential drug interactions
    with real-time validation and comprehensive interaction data.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for drug interaction checker'),
        blank=True
    )
    
    # Interaction checking settings
    enable_real_time_checking = models.BooleanField(
        default=True,
        verbose_name=_('Enable Real-time Checking'),
        help_text=_('Check interactions as user types medication names')
    )
    
    max_medications_per_check = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Maximum Medications Per Check'),
        help_text=_('Maximum number of medications to check at once'),
        validators=[MinValueValidator(2), MaxValueValidator(20)]
    )
    
    # Interaction severity levels
    show_minor_interactions = models.BooleanField(
        default=True,
        verbose_name=_('Show Minor Interactions'),
        help_text=_('Display minor drug interactions')
    )
    
    show_moderate_interactions = models.BooleanField(
        default=True,
        verbose_name=_('Show Moderate Interactions'),
        help_text=_('Display moderate drug interactions')
    )
    
    show_major_interactions = models.BooleanField(
        default=True,
        verbose_name=_('Show Major Interactions'),
        help_text=_('Display major drug interactions')
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
    ]
    
    # Admin panels with Wagtail 7.0.2 features
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            FieldPanel('enable_real_time_checking'),
            FieldPanel('max_medications_per_check'),
        ], heading=_('Interaction Checking Settings')),
        MultiFieldPanel([
            FieldPanel('show_minor_interactions'),
            FieldPanel('show_moderate_interactions'),
            FieldPanel('show_major_interactions'),
        ], heading=_('Severity Level Settings')),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Medication Interaction Page')
        verbose_name_plural = _('Medication Interaction Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with interaction checking data."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add interaction settings
        context['interaction_settings'] = {
            'real_time': self.enable_real_time_checking,
            'max_medications': self.max_medications_per_check,
            'show_minor': self.show_minor_interactions,
            'show_moderate': self.show_moderate_interactions,
            'show_major': self.show_major_interactions,
        }
        
        return context


class StockDashboardPage(Page):
    """
    Medication inventory dashboard with real-time Wagtail widgets.
    
    This page provides a comprehensive dashboard for monitoring
    medication stock levels, alerts, and inventory analytics.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for stock dashboard'),
        blank=True
    )
    
    # Dashboard settings
    enable_real_time_updates = models.BooleanField(
        default=True,
        verbose_name=_('Enable Real-time Updates'),
        help_text=_('Update dashboard data in real-time')
    )
    
    refresh_interval_seconds = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Refresh Interval (seconds)'),
        help_text=_('How often to refresh dashboard data'),
        validators=[MinValueValidator(10), MaxValueValidator(300)]
    )
    
    # Widget configuration
    show_stock_alerts = models.BooleanField(
        default=True,
        verbose_name=_('Show Stock Alerts'),
        help_text=_('Display low stock and expiry alerts')
    )
    
    show_inventory_charts = models.BooleanField(
        default=True,
        verbose_name=_('Show Inventory Charts'),
        help_text=_('Display inventory analytics charts')
    )
    
    show_recent_transactions = models.BooleanField(
        default=True,
        verbose_name=_('Show Recent Transactions'),
        help_text=_('Display recent stock transactions')
    )
    
    show_expiry_warnings = models.BooleanField(
        default=True,
        verbose_name=_('Show Expiry Warnings'),
        help_text=_('Display medication expiry warnings')
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
    ]
    
    # Admin panels with Wagtail 7.0.2 features
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            FieldPanel('enable_real_time_updates'),
            FieldPanel('refresh_interval_seconds'),
        ], heading=_('Dashboard Settings')),
        MultiFieldPanel([
            FieldPanel('show_stock_alerts'),
            FieldPanel('show_inventory_charts'),
            FieldPanel('show_recent_transactions'),
            FieldPanel('show_expiry_warnings'),
        ], heading=_('Widget Configuration')),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Stock Dashboard Page')
        verbose_name_plural = _('Stock Dashboard Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with dashboard data."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add dashboard settings
        context['dashboard_settings'] = {
            'real_time': self.enable_real_time_updates,
            'refresh_interval': self.refresh_interval_seconds,
            'show_alerts': self.show_stock_alerts,
            'show_charts': self.show_inventory_charts,
            'show_transactions': self.show_recent_transactions,
            'show_expiry': self.show_expiry_warnings,
        }
        
        return context


class MedicationReminderPage(AbstractForm):
    """
    Medication reminder setup page with Wagtail form integration.
    
    This page allows users to configure medication reminders
    with various notification methods and scheduling options.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for medication reminders'),
        blank=True
    )
    
    # Reminder settings
    enable_email_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Enable Email Reminders'),
        help_text=_('Send medication reminders via email')
    )
    
    enable_sms_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Enable SMS Reminders'),
        help_text=_('Send medication reminders via SMS')
    )
    
    enable_push_notifications = models.BooleanField(
        default=True,
        verbose_name=_('Enable Push Notifications'),
        help_text=_('Send medication reminders via push notifications')
    )
    
    # Default reminder settings
    default_reminder_time = models.TimeField(
        default='09:00',
        verbose_name=_('Default Reminder Time'),
        help_text=_('Default time for medication reminders')
    )
    
    default_reminder_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', _('Daily')),
            ('twice_daily', _('Twice Daily')),
            ('three_times_daily', _('Three Times Daily')),
            ('weekly', _('Weekly')),
            ('custom', _('Custom Schedule')),
        ],
        default='daily',
        verbose_name=_('Default Reminder Frequency')
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
    ]
    
    # Admin panels with Wagtail 7.0.2 features
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            FieldPanel('enable_email_reminders'),
            FieldPanel('enable_sms_reminders'),
            FieldPanel('enable_push_notifications'),
        ], heading=_('Notification Methods')),
        MultiFieldPanel([
            FieldPanel('default_reminder_time'),
            FieldPanel('default_reminder_frequency'),
        ], heading=_('Default Settings')),
        InlinePanel('form_fields', label=_('Reminder Form Fields')),
    ]
    
    # Form submissions panel
    promote_panels = Page.promote_panels + [
        FormSubmissionsPanel(),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Medication Reminder Page')
        verbose_name_plural = _('Medication Reminder Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with reminder settings."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add reminder settings
        context['reminder_settings'] = {
            'email_enabled': self.enable_email_reminders,
            'sms_enabled': self.enable_sms_reminders,
            'push_enabled': self.enable_push_notifications,
            'default_time': self.default_reminder_time,
            'default_frequency': self.default_reminder_frequency,
        }
        
        return context


class PharmacyIntegrationPage(Page):
    """
    Third-party pharmacy API integration dashboard.
    
    This page provides a comprehensive dashboard for managing
    integrations with external pharmacy systems and APIs.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for pharmacy integrations'),
        blank=True
    )
    
    # Integration settings
    enable_api_integrations = models.BooleanField(
        default=True,
        verbose_name=_('Enable API Integrations'),
        help_text=_('Enable third-party pharmacy API integrations')
    )
    
    enable_webhook_integrations = models.BooleanField(
        default=True,
        verbose_name=_('Enable Webhook Integrations'),
        help_text=_('Enable webhook-based pharmacy integrations')
    )
    
    enable_manual_integrations = models.BooleanField(
        default=True,
        verbose_name=_('Enable Manual Integrations'),
        help_text=_('Enable manual pharmacy data entry')
    )
    
    # API configuration
    api_timeout_seconds = models.PositiveIntegerField(
        default=30,
        verbose_name=_('API Timeout (seconds)'),
        help_text=_('Timeout for API requests'),
        validators=[MinValueValidator(5), MaxValueValidator(120)]
    )
    
    max_retry_attempts = models.PositiveIntegerField(
        default=3,
        verbose_name=_('Max Retry Attempts'),
        help_text=_('Maximum number of API retry attempts'),
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    # Dashboard widgets
    show_api_status = models.BooleanField(
        default=True,
        verbose_name=_('Show API Status'),
        help_text=_('Display API connection status')
    )
    
    show_sync_history = models.BooleanField(
        default=True,
        verbose_name=_('Show Sync History'),
        help_text=_('Display data synchronization history')
    )
    
    show_error_logs = models.BooleanField(
        default=True,
        verbose_name=_('Show Error Logs'),
        help_text=_('Display integration error logs')
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),
    ]
    
    # Admin panels with Wagtail 7.0.2 features
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            FieldPanel('enable_api_integrations'),
            FieldPanel('enable_webhook_integrations'),
            FieldPanel('enable_manual_integrations'),
        ], heading=_('Integration Types')),
        MultiFieldPanel([
            FieldPanel('api_timeout_seconds'),
            FieldPanel('max_retry_attempts'),
        ], heading=_('API Configuration')),
        MultiFieldPanel([
            FieldPanel('show_api_status'),
            FieldPanel('show_sync_history'),
            FieldPanel('show_error_logs'),
        ], heading=_('Dashboard Widgets')),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Pharmacy Integration Page')
        verbose_name_plural = _('Pharmacy Integration Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Enhanced context with integration data."""
        context = super().get_context(request, *args, **kwargs)
        
        # Add integration settings
        context['integration_settings'] = {
            'api_enabled': self.enable_api_integrations,
            'webhook_enabled': self.enable_webhook_integrations,
            'manual_enabled': self.enable_manual_integrations,
            'timeout': self.api_timeout_seconds,
            'retry_attempts': self.max_retry_attempts,
            'show_status': self.show_api_status,
            'show_history': self.show_sync_history,
            'show_errors': self.show_error_logs,
        }
        
        return context


# Settings model for medication pages
@register_setting
class MedicationPageSettings(BaseSetting):
    """
    Site-wide settings for medication pages with Wagtail 7.0.2 features.
    """
    
    # General settings
    enable_medication_search = models.BooleanField(
        default=True,
        verbose_name=_('Enable Medication Search'),
        help_text=_('Enable search functionality on medication pages')
    )
    
    enable_medication_comparison = models.BooleanField(
        default=True,
        verbose_name=_('Enable Medication Comparison'),
        help_text=_('Enable medication comparison features')
    )
    
    enable_pharmacy_locator = models.BooleanField(
        default=True,
        verbose_name=_('Enable Pharmacy Locator'),
        help_text=_('Enable pharmacy location services')
    )
    
    # New page settings
    enable_drug_interactions = models.BooleanField(
        default=True,
        verbose_name=_('Enable Drug Interactions'),
        help_text=_('Enable drug interaction checking features')
    )
    
    enable_stock_dashboard = models.BooleanField(
        default=True,
        verbose_name=_('Enable Stock Dashboard'),
        help_text=_('Enable medication inventory dashboard')
    )
    
    enable_medication_reminders = models.BooleanField(
        default=True,
        verbose_name=_('Enable Medication Reminders'),
        help_text=_('Enable medication reminder features')
    )
    
    enable_pharmacy_integrations = models.BooleanField(
        default=True,
        verbose_name=_('Enable Pharmacy Integrations'),
        help_text=_('Enable third-party pharmacy integrations')
    )
    
    # Privacy settings
    enable_prescription_history = models.BooleanField(
        default=True,
        verbose_name=_('Enable Prescription History'),
        help_text=_('Enable prescription history features')
    )
    
    require_authentication_for_history = models.BooleanField(
        default=True,
        verbose_name=_('Require Authentication for History'),
        help_text=_('Require users to be logged in to view prescription history')
    )
    
    # Content settings
    max_comparison_items = models.PositiveIntegerField(
        default=5,
        verbose_name=_('Maximum Comparison Items'),
        help_text=_('Maximum number of medications that can be compared'),
        validators=[MinValueValidator(2), MaxValueValidator(10)]
    )
    
    search_radius_km = models.PositiveIntegerField(
        default=10,
        verbose_name=_('Default Search Radius (km)'),
        help_text=_('Default search radius for pharmacy locator'),
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    
    # Wagtail 7.0.2 specific settings
    enable_enhanced_admin_panels = models.BooleanField(
        default=True,
        verbose_name=_('Enable Enhanced Admin Panels'),
        help_text=_('Use Wagtail 7.0.2 enhanced admin panel features')
    )
    
    enable_streamfield_validation = models.BooleanField(
        default=True,
        verbose_name=_('Enable StreamField Validation'),
        help_text=_('Enable enhanced StreamField validation')
    )
    
    enable_search_boost_factors = models.BooleanField(
        default=True,
        verbose_name=_('Enable Search Boost Factors'),
        help_text=_('Enable search relevance boost factors')
    )
    
    # Performance settings
    enable_json_field_optimization = models.BooleanField(
        default=True,
        verbose_name=_('Enable JSON Field Optimization'),
        help_text=_('Use JSON fields for StreamField performance')
    )
    
    cache_page_contexts = models.BooleanField(
        default=True,
        verbose_name=_('Cache Page Contexts'),
        help_text=_('Cache page context data for performance')
    )
    
    class Meta:
        verbose_name = _('Medication Page Settings')
        verbose_name_plural = _('Medication Page Settings') 