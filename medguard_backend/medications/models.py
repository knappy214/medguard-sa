from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import render
from decimal import Decimal
from datetime import timedelta
import uuid

# Wagtail imports - Enhanced for 7.0.2
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.blocks import (
    CharBlock, TextBlock, IntegerBlock, DecimalBlock, BooleanBlock,
    DateBlock, TimeBlock, ChoiceBlock, URLBlock, EmailBlock,
    StructBlock, ListBlock, StreamBlock, PageChooserBlock,
    RawHTMLBlock, StaticBlock, RichTextBlock, DateTimeBlock
)
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index
from wagtail.images.models import Image
from wagtail.blocks.field_block import FieldBlock
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.rich_text import expand_db_html
from wagtail.snippets.models import register_snippet
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
        
        # Validate dosage amounts
        if 'amount' in cleaned_data and cleaned_data['amount']:
            amount = cleaned_data['amount']
            if amount <= 0:
                raise StructBlockValidationError(
                    block_errors={'amount': 'Dosage amount must be greater than 0'}
                )
            if amount > 999999.99:
                raise StructBlockValidationError(
                    block_errors={'amount': 'Dosage amount cannot exceed 999,999.99'}
                )
        
        # Validate frequency consistency
        if 'frequency' in cleaned_data and 'timing' in cleaned_data:
            frequency = cleaned_data.get('frequency')
            timing = cleaned_data.get('timing')
            
            if frequency == 'as_needed' and timing != 'custom':
                raise StructBlockValidationError(
                    block_errors={'timing': 'Custom timing is required for "as needed" frequency'}
                )
        
        return cleaned_data


# Enhanced StreamField blocks for Wagtail 7.0.2
class MedicationDosageBlock(MedicationValidationMixin, StructBlock):
    """Enhanced dosage block with better validation and form widgets."""
    
    amount = DecimalBlock(
        min_value=0.01,
        max_digits=8,
        decimal_places=2,
        help_text=_('Dosage amount'),
        label=_('Amount'),
        # Enhanced validation for Wagtail 7.0.2
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('999999.99'))]
    )
    
    unit = ChoiceBlock(
        choices=[
            ('mg', _('Milligrams (mg)')),
            ('mcg', _('Micrograms (mcg)')),
            ('ml', _('Milliliters (ml)')),
            ('g', _('Grams (g)')),
            ('units', _('Units')),
            ('drops', _('Drops')),
            ('puffs', _('Puffs')),
            ('tablets', _('Tablets')),
            ('capsules', _('Capsules')),
        ],
        default='mg',
        help_text=_('Unit of measurement'),
        label=_('Unit')
    )
    
    frequency = ChoiceBlock(
        choices=[
            ('once_daily', _('Once daily')),
            ('twice_daily', _('Twice daily')),
            ('three_times_daily', _('Three times daily')),
            ('four_times_daily', _('Four times daily')),
            ('as_needed', _('As needed')),
            ('weekly', _('Weekly')),
            ('monthly', _('Monthly')),
        ],
        default='once_daily',
        help_text=_('How often to take'),
        label=_('Frequency')
    )
    
    instructions = TextBlock(
        required=False,
        help_text=_('Special instructions for taking this dosage'),
        label=_('Instructions'),
        max_length=500  # Enhanced length validation
    )
    
    class Meta:
        template = 'medications/blocks/medication_dosage_block.html'
        icon = 'medication'
        label = _('Medication Dosage')


class MedicationSideEffectBlock(MedicationValidationMixin, StructBlock):
    """Enhanced side effect block with severity levels."""
    
    effect_name = CharBlock(
        max_length=200,
        help_text=_('Name of the side effect'),
        label=_('Side Effect'),
        # Enhanced validation for Wagtail 7.0.2
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Side effect name contains invalid characters'
        )]
    )
    
    severity = ChoiceBlock(
        choices=[
            ('mild', _('Mild')),
            ('moderate', _('Moderate')),
            ('severe', _('Severe')),
            ('life_threatening', _('Life-threatening')),
        ],
        default='mild',
        help_text=_('Severity of the side effect'),
        label=_('Severity')
    )
    
    frequency = ChoiceBlock(
        choices=[
            ('very_rare', _('Very rare (< 0.1%)')),
            ('rare', _('Rare (0.1-1%)')),
            ('uncommon', _('Uncommon (1-10%)')),
            ('common', _('Common (10-30%)')),
            ('very_common', _('Very common (> 30%)')),
        ],
        default='uncommon',
        help_text=_('How common this side effect is'),
        label=_('Frequency')
    )
    
    description = RichTextBlock(
        required=False,
        help_text=_('Detailed description of the side effect'),
        label=_('Description'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=1000  # Enhanced length validation
    )
    
    class Meta:
        template = 'medications/blocks/medication_side_effect_block.html'
        icon = 'warning'
        label = _('Side Effect')


class MedicationInteractionBlock(MedicationValidationMixin, StructBlock):
    """Enhanced drug interaction block."""
    
    interacting_medication = CharBlock(
        max_length=200,
        help_text=_('Name of the interacting medication or substance'),
        label=_('Interacting Substance'),
        # Enhanced validation for Wagtail 7.0.2
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Medication name contains invalid characters'
        )]
    )
    
    interaction_type = ChoiceBlock(
        choices=[
            ('major', _('Major - Avoid combination')),
            ('moderate', _('Moderate - Monitor closely')),
            ('minor', _('Minor - No action needed')),
        ],
        default='moderate',
        help_text=_('Severity of the interaction'),
        label=_('Interaction Type')
    )
    
    description = RichTextBlock(
        help_text=_('Description of the interaction and recommendations'),
        label=_('Description'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=1500  # Enhanced length validation
    )
    
    recommendation = RichTextBlock(
        required=False,
        help_text=_('Specific recommendations for managing this interaction'),
        label=_('Recommendations'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=1000  # Enhanced length validation
    )
    
    class Meta:
        template = 'medications/blocks/medication_interaction_block.html'
        icon = 'cross'
        label = _('Drug Interaction')


class MedicationStorageBlock(MedicationValidationMixin, StructBlock):
    """Enhanced storage instructions block."""
    
    temperature_range = ChoiceBlock(
        choices=[
            ('room_temp', _('Room temperature (15-25°C)')),
            ('refrigerated', _('Refrigerated (2-8°C)')),
            ('frozen', _('Frozen (-20°C or below)')),
            ('controlled_room', _('Controlled room temperature (20-25°C)')),
            ('cool_dry', _('Cool, dry place')),
        ],
        default='room_temp',
        help_text=_('Required storage temperature'),
        label=_('Temperature')
    )
    
    light_sensitive = BooleanBlock(
        default=False,
        help_text=_('Whether the medication is light sensitive'),
        label=_('Light Sensitive')
    )
    
    humidity_sensitive = BooleanBlock(
        default=False,
        help_text=_('Whether the medication is humidity sensitive'),
        label=_('Humidity Sensitive')
    )
    
    special_instructions = RichTextBlock(
        required=False,
        help_text=_('Special storage instructions'),
        label=_('Special Instructions'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=800  # Enhanced length validation
    )
    
    class Meta:
        template = 'medications/blocks/medication_storage_block.html'
        icon = 'home'
        label = _('Storage Instructions')


class MedicationImageBlock(MedicationValidationMixin, StructBlock):
    """Enhanced image block with focal point improvements and accessibility."""
    
    image = ImageChooserBlock(
        help_text=_('Medication image with improved focal point handling'),
        label=_('Image')
    )
    
    alt_text = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Alternative text for accessibility'),
        label=_('Alt Text'),
        # Enhanced validation for Wagtail 7.0.2
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Alt text contains invalid characters'
        )]
    )
    
    caption = CharBlock(
        max_length=500,
        required=False,
        help_text=_('Image caption'),
        label=_('Caption'),
        # Enhanced validation for Wagtail 7.0.2
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Caption contains invalid characters'
        )]
    )
    
    image_type = ChoiceBlock(
        choices=[
            ('primary', _('Primary Image')),
            ('packaging', _('Packaging')),
            ('tablet', _('Tablet/Capsule')),
            ('injection', _('Injection Device')),
            ('inhaler', _('Inhaler')),
            ('other', _('Other')),
        ],
        default='primary',
        help_text=_('Type of medication image'),
        label=_('Image Type')
    )
    
    class Meta:
        template = 'medications/blocks/medication_image_block.html'
        icon = 'image'
        label = _('Medication Image')


class MedicationScheduleBlock(MedicationValidationMixin, StructBlock):
    """Enhanced medication schedule block with improved time handling."""
    
    timing = ChoiceBlock(
        choices=[
            ('morning', _('Morning')),
            ('noon', _('Noon')),
            ('evening', _('Evening')),
            ('night', _('Night')),
            ('custom', _('Custom Time')),
        ],
        default='morning',
        help_text=_('When to take the medication'),
        label=_('Timing')
    )
    
    custom_time = TimeBlock(
        required=False,
        help_text=_('Custom time (if timing is custom)'),
        label=_('Custom Time')
    )
    
    days_of_week = ListBlock(
        ChoiceBlock(
            choices=[
                ('monday', _('Monday')),
                ('tuesday', _('Tuesday')),
                ('wednesday', _('Wednesday')),
                ('thursday', _('Thursday')),
                ('friday', _('Friday')),
                ('saturday', _('Saturday')),
                ('sunday', _('Sunday')),
            ]
        ),
        min_num=1,
        max_num=7,
        help_text=_('Days of the week to take medication'),
        label=_('Days of Week')
    )
    
    instructions = RichTextBlock(
        required=False,
        help_text=_('Special instructions for this schedule'),
        label=_('Instructions'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=600  # Enhanced length validation
    )
    
    class Meta:
        template = 'medications/blocks/medication_schedule_block.html'
        icon = 'time'
        label = _('Medication Schedule')


class MedicationComparisonTableBlock(StructBlock):
    """Enhanced table block for medication comparison with Wagtail 7.0.2 features."""
    
    title = CharBlock(
        max_length=200,
        help_text=_('Title for the comparison table'),
        label=_('Table Title'),
        # Enhanced validation for Wagtail 7.0.2
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Table title contains invalid characters'
        )]
    )
    
    # Custom table implementation using ListBlock of StructBlocks
    table_rows = ListBlock(
        StructBlock([
            ('medication_name', CharBlock(max_length=255, help_text=_('Medication name'))),
            ('dosage', CharBlock(max_length=100, help_text=_('Dosage information'))),
            ('side_effects', CharBlock(max_length=200, help_text=_('Side effects'))),
            ('cost', CharBlock(max_length=100, help_text=_('Cost information'))),
            ('efficacy', CharBlock(max_length=200, help_text=_('Efficacy rating'))),
            ('notes', RichTextBlock(features=['bold', 'italic', 'link'], help_text=_('Additional notes'))),
        ]),
        min_num=1,
        max_num=20,
        help_text=_('Table rows for comparison')
    )
    
    comparison_type = ChoiceBlock(
        choices=[
            ('dosage', _('Dosage Comparison')),
            ('side_effects', _('Side Effects Comparison')),
            ('interactions', _('Drug Interactions Comparison')),
            ('cost', _('Cost Comparison')),
            ('efficacy', _('Efficacy Comparison')),
            ('generic_vs_brand', _('Generic vs Brand Comparison')),
        ],
        default='dosage',
        help_text=_('Type of comparison being made'),
        label=_('Comparison Type')
    )
    
    notes = RichTextBlock(
        required=False,
        help_text=_('Additional notes about the comparison'),
        label=_('Notes'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=1000  # Enhanced length validation
    )
    
    class Meta:
        template = 'medications/blocks/medication_comparison_table_block.html'
        icon = 'table'
        label = _('Medication Comparison Table')


class MedicationWarningBlock(StaticBlock):
    """Enhanced StaticBlock for reusable medication warning content."""
    
    warning_type = ChoiceBlock(
        choices=[
            ('general', _('General Warning')),
            ('contraindication', _('Contraindication')),
            ('side_effect', _('Side Effect Warning')),
            ('interaction', _('Drug Interaction Warning')),
            ('storage', _('Storage Warning')),
            ('expiry', _('Expiry Warning')),
            ('dosage', _('Dosage Warning')),
        ],
        default='general',
        help_text=_('Type of warning'),
        label=_('Warning Type')
    )
    
    severity = ChoiceBlock(
        choices=[
            ('info', _('Information')),
            ('warning', _('Warning')),
            ('danger', _('Danger')),
            ('critical', _('Critical')),
        ],
        default='warning',
        help_text=_('Severity level of the warning'),
        label=_('Severity')
    )
    
    content = RichTextBlock(
        help_text=_('Warning content'),
        label=_('Content'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=2000  # Enhanced length validation
    )
    
    class Meta:
        template = 'medications/blocks/medication_warning_block.html'
        icon = 'warning'
        label = _('Medication Warning')


class MedicationInstructionsBlock(StaticBlock):
    """Enhanced StaticBlock for reusable medication instructions."""
    
    instruction_type = ChoiceBlock(
        choices=[
            ('general', _('General Instructions')),
            ('dosage', _('Dosage Instructions')),
            ('administration', _('Administration Instructions')),
            ('storage', _('Storage Instructions')),
            ('disposal', _('Disposal Instructions')),
            ('missed_dose', _('Missed Dose Instructions')),
            ('precautions', _('Precautions')),
        ],
        default='general',
        help_text=_('Type of instructions'),
        label=_('Instruction Type')
    )
    
    content = RichTextBlock(
        help_text=_('Instruction content'),
        label=_('Content'),
        features=['bold', 'italic', 'link', 'ul', 'ol', 'h3', 'h4'],  # Enhanced HTML sanitization
        max_length=3000  # Enhanced length validation
    )
    
    step_by_step = BooleanBlock(
        default=False,
        help_text=_('Whether to display as step-by-step instructions'),
        label=_('Step by Step')
    )
    
    class Meta:
        template = 'medications/blocks/medication_instructions_block.html'
        icon = 'list-ul'
        label = _('Medication Instructions')


# Enhanced StreamField for medication content
class MedicationContentStreamBlock(StreamBlock):
    """Enhanced StreamField for medication content with improved performance."""
    
    dosage = MedicationDosageBlock()
    side_effects = ListBlock(MedicationSideEffectBlock(), min_num=0, max_num=50)
    interactions = ListBlock(MedicationInteractionBlock(), min_num=0, max_num=100)
    storage = MedicationStorageBlock()
    images = ListBlock(MedicationImageBlock(), min_num=0, max_num=10)
    schedules = ListBlock(MedicationScheduleBlock(), min_num=0, max_num=20)
    
    # Enhanced text blocks with Wagtail 7.0.2 features
    description = RichTextBlock(
        help_text=_('Detailed description of the medication'),
        label=_('Description'),
        features=['bold', 'italic', 'link', 'ul', 'ol', 'h3', 'h4'],  # Enhanced HTML sanitization
        max_length=5000  # Enhanced length validation
    )
    
    instructions = RichTextBlock(
        help_text=_('Instructions for use'),
        label=_('Instructions'),
        features=['bold', 'italic', 'link', 'ul', 'ol', 'h3', 'h4'],  # Enhanced HTML sanitization
        max_length=4000  # Enhanced length validation
    )
    
    warnings = RichTextBlock(
        help_text=_('Important warnings and precautions'),
        label=_('Warnings'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],  # Enhanced HTML sanitization
        max_length=3000  # Enhanced length validation
    )
    
    # New Wagtail 7.0.2 enhanced blocks
    comparison_table = MedicationComparisonTableBlock()
    warning_block = MedicationWarningBlock()
    instructions_block = MedicationInstructionsBlock()
    
    class Meta:
        block_counts = {
            'dosage': {'min_num': 1, 'max_num': 10},
            'side_effects': {'min_num': 0, 'max_num': 50},
            'interactions': {'min_num': 0, 'max_num': 100},
            'storage': {'min_num': 0, 'max_num': 1},
            'images': {'min_num': 0, 'max_num': 10},
            'schedules': {'min_num': 0, 'max_num': 20},
            'comparison_table': {'min_num': 0, 'max_num': 5},
            'warning_block': {'min_num': 0, 'max_num': 10},
            'instructions_block': {'min_num': 0, 'max_num': 5},
        }


class MedicationIndexPage(Page):
    """
    Index page for medications with enhanced StreamField content and Wagtail 7.0.2 features.
    
    This page lists all medications and provides search/filter functionality with
    enhanced performance and SEO capabilities.
    """
    
    # Enhanced page content with StreamField
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for the medications page'),
        blank=True
    )
    
    # Enhanced content with StreamField
    content = StreamField(
        MedicationContentStreamBlock(),
        verbose_name=_('Page Content'),
        help_text=_('Rich content for the medications index page'),
        blank=True,
        use_json_field=True  # Wagtail 7.0.2 performance improvement
    )
    
    # Wagtail 7.0.2: Enhanced page description for better SEO
    page_description = models.CharField(
        max_length=255,
        verbose_name=_('Page Description'),
        help_text=_('Brief description for search engines and social media'),
        blank=True
    )
    
    # Enhanced search configuration with Wagtail 7.0.2 boost factors
    search_fields = Page.search_fields + [
        index.SearchField('intro', boost=2.0),  # Higher boost for intro content
        index.SearchField('content', boost=1.5),  # Medium boost for content
        index.SearchField('page_description', boost=3.0),  # Highest boost for SEO description
    ]
    
    # Enhanced admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        FieldPanel('content'),
        FieldPanel('page_description'),
    ]
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = ['medications.MedicationDetailPage']
    
    class Meta:
        verbose_name = _('Medication Index Page')
        verbose_name_plural = _('Medication Index Pages')
    
    def get_context(self, request, *args, **kwargs):
        """
        Enhanced get_context with Wagtail 7.0.2 query optimization and filtering.
        
        Provides better performance through optimized queries and enhanced
        filtering capabilities.
        """
        context = super().get_context(request, *args, **kwargs)
        
        # Wagtail 7.0.2: Enhanced query optimization with better prefetch_related
        medications = Medication.objects.select_related(
            'stock_analytics'
        ).prefetch_related(
            'stock_alerts',
            'stock_transactions',
            'prescription_renewals'
        ).order_by('name')
        
        # Apply filters if provided with enhanced validation
        medication_type = request.GET.get('type')
        if medication_type and medication_type in dict(Medication.MedicationType.choices):
            medications = medications.filter(medication_type=medication_type)
        
        prescription_type = request.GET.get('prescription')
        if prescription_type and prescription_type in dict(Medication.PrescriptionType.choices):
            medications = medications.filter(prescription_type=prescription_type)
        
        # Enhanced search functionality with Wagtail 7.0.2 improvements
        search_query = request.GET.get('search')
        if search_query:
            medications = medications.filter(
                models.Q(name__icontains=search_query) |
                models.Q(generic_name__icontains=search_query) |
                models.Q(brand_name__icontains=search_query) |
                models.Q(description__icontains=search_query) |
                models.Q(active_ingredients__icontains=search_query) |
                models.Q(manufacturer__icontains=search_query)
            )
        
        # Stock status filtering with enhanced logic
        stock_status = request.GET.get('stock')
        if stock_status == 'low':
            medications = medications.filter(pill_count__lte=models.F('low_stock_threshold'))
        elif stock_status == 'out':
            medications = medications.filter(pill_count=0)
        elif stock_status == 'expiring':
            medications = medications.filter(
                expiration_date__lte=timezone.now().date() + timedelta(days=30),
                expiration_date__gt=timezone.now().date()
            )
        
        # Manufacturer filtering
        manufacturer = request.GET.get('manufacturer')
        if manufacturer:
            medications = medications.filter(manufacturer__icontains=manufacturer)
        
        # Pagination with improved performance
        from django.core.paginator import Paginator
        paginator = Paginator(medications, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['medications'] = page_obj
        context['medication_types'] = Medication.MedicationType.choices
        context['prescription_types'] = Medication.PrescriptionType.choices
        context['manufacturers'] = Medication.objects.values_list(
            'manufacturer', flat=True
        ).distinct().exclude(manufacturer='').order_by('manufacturer')
        
        # Add filter state to context for template
        context['current_filters'] = {
            'type': medication_type,
            'prescription': prescription_type,
            'stock': stock_status,
            'manufacturer': manufacturer,
            'search': search_query,
        }
        
        return context
    
    def get_sitemap_urls(self, request=None):
        """
        Wagtail 7.0.2: Enhanced sitemap generation for medication pages.
        
        Provides better SEO through improved sitemap structure and
        medication-specific metadata.
        """
        urls = super().get_sitemap_urls(request)
        
        # Add medication-specific sitemap entries
        medications = Medication.objects.filter(
            # Exclude expired medications
            models.Q(expiration_date__isnull=True) | 
            models.Q(expiration_date__gt=timezone.now().date()),
            # Only include active medications
            pill_count__gt=0
        ).select_related('detail_page')
        
        for medication in medications:
            if medication.detail_page:
                urls.append({
                    'location': medication.detail_page.get_full_url(request),
                    'lastmod': medication.updated_at,
                    'changefreq': 'weekly',
                    'priority': 0.8,
                    'alternates': [],
                })
        
        return urls
    
    def serve_preview(self, request, mode_name):
        """
        Wagtail 7.0.2: Enhanced preview functionality for medication content.
        
        Provides better preview experience with medication-specific context
        and improved performance.
        """
        # Get preview context with enhanced medication data
        context = self.get_context(request)
        
        # Add preview-specific data
        context['is_preview'] = True
        context['preview_mode'] = mode_name
        
        # Limit medications in preview for performance
        if 'medications' in context:
            context['medications'] = context['medications'][:5]
        
        # Use the same template as the live page
        template = self.get_template(request)
        return render(request, template, context)
    
    def get_meta_description(self):
        """
        Wagtail 7.0.2: Enhanced meta description for better SEO.
        """
        if self.page_description:
            return self.page_description
        return self.intro[:160] if self.intro else _('Browse and search medications with detailed information, dosages, side effects, and stock management.')
    
    def get_meta_title(self):
        """
        Wagtail 7.0.2: Enhanced meta title for better SEO.
        """
        return self.title + ' - ' + _('MedGuard SA')

    def clean(self):
        """
        Wagtail 7.0.2: Enhanced validation for prescription data and page content.
        """
        super().clean()
        
        # Validate page description length for SEO
        if self.page_description and len(self.page_description) > 255:
            raise ValidationError({
                'page_description': _('Page description must be 255 characters or less for optimal SEO.')
            })
        
        # Validate intro content
        if self.intro:
            # Check for minimum content length
            if len(self.intro) < 50:
                raise ValidationError({
                    'intro': _('Introduction should be at least 50 characters for better user experience.')
                })
            
            # Check for maximum content length
            if len(self.intro) > 1000:
                raise ValidationError({
                    'intro': _('Introduction should not exceed 1000 characters.')
                })
        
        # Validate content blocks
        if self.content:
            for block in self.content:
                if hasattr(block.block, 'clean'):
                    try:
                        block.block.clean(block.value)
                    except ValidationError as e:
                        raise ValidationError({
                            'content': _('Content validation error: {}').format(str(e))
                        })

    def get_admin_display_title(self):
        """
        Wagtail 7.0.2: Enhanced admin display title for better page identification.
        """
        base_title = self.title
        if self.page_description:
            return f"{base_title} - {self.page_description[:50]}..."
        return base_title

    def route(self, request, path_components):
        """
        Wagtail 7.0.2: Enhanced routing for custom medication URL patterns.
        
        Supports custom URL patterns like:
        - /medications/search/
        - /medications/filter/type/tablet/
        - /medications/manufacturer/pfizer/
        """
        if path_components:
            first_component = path_components[0]
            
            # Handle search routes
            if first_component == 'search':
                return self.serve_search(request, path_components[1:])
            
            # Handle filter routes
            elif first_component == 'filter':
                return self.serve_filter(request, path_components[1:])
            
            # Handle manufacturer routes
            elif first_component == 'manufacturer':
                return self.serve_manufacturer(request, path_components[1:])
            
            # Handle medication type routes
            elif first_component in ['tablet', 'capsule', 'liquid', 'injection', 'inhaler']:
                return self.serve_medication_type(request, path_components)
        
        # Default to parent routing
        return super().route(request, path_components)

    def serve_search(self, request, path_components):
        """Handle search-specific routes."""
        context = self.get_context(request)
        context['search_mode'] = True
        context['search_query'] = request.GET.get('q', '')
        return self.serve(request)

    def serve_filter(self, request, path_components):
        """Handle filter-specific routes."""
        context = self.get_context(request)
        context['filter_mode'] = True
        
        if len(path_components) >= 2:
            filter_type = path_components[0]
            filter_value = path_components[1]
            context['active_filter'] = {filter_type: filter_value}
        
        return self.serve(request)

    def serve_manufacturer(self, request, path_components):
        """Handle manufacturer-specific routes."""
        context = self.get_context(request)
        context['manufacturer_mode'] = True
        
        if path_components:
            manufacturer = path_components[0]
            context['active_manufacturer'] = manufacturer
        
        return self.serve(request)

    def serve_medication_type(self, request, path_components):
        """Handle medication type-specific routes."""
        context = self.get_context(request)
        context['medication_type_mode'] = True
        
        if path_components:
            medication_type = path_components[0]
            context['active_medication_type'] = medication_type
        
        return self.serve(request)

    def get_cached_paths(self):
        """
        Wagtail 7.0.2: Enhanced caching strategies for medication pages.
        
        Returns additional paths that should be cached for this page,
        including filter variations and search results.
        """
        cached_paths = super().get_cached_paths()
        
        # Add cache paths for common filter combinations
        medication_types = [choice[0] for choice in Medication.MedicationType.choices]
        prescription_types = [choice[0] for choice in Medication.PrescriptionType.choices]
        
        # Cache paths for medication type filters
        for med_type in medication_types:
            cached_paths.append(f"{self.url_path}filter/type/{med_type}/")
        
        # Cache paths for prescription type filters
        for presc_type in prescription_types:
            cached_paths.append(f"{self.url_path}filter/prescription/{presc_type}/")
        
        # Cache paths for stock status filters
        cached_paths.extend([
            f"{self.url_path}filter/stock/low/",
            f"{self.url_path}filter/stock/expiring/",
            f"{self.url_path}filter/stock/expired/",
        ])
        
        # Cache paths for search variations
        cached_paths.extend([
            f"{self.url_path}search/",
            f"{self.url_path}search/?q=common",
            f"{self.url_path}search/?q=prescription",
        ])
        
        return cached_paths


class MedicationDetailPage(Page):
    """
    Detail page for individual medications with enhanced StreamField content.
    
    This page displays detailed information about a specific medication.
    """
    
    # Relationship to Medication model
    medication = models.OneToOneField(
        'medications.Medication',
        on_delete=models.SET_NULL,
        null=True,
        related_name='detail_page',
        verbose_name=_('Medication'),
        help_text=_('Associated medication record')
    )
    
    # Enhanced content with StreamField
    content = StreamField(
        MedicationContentStreamBlock(),
        verbose_name=_('Medication Content'),
        help_text=_('Rich content for the medication detail page'),
        blank=True,
        use_json_field=True  # Wagtail 7.0.2 performance improvement
    )
    
    # Additional content
    additional_info = RichTextField(
        verbose_name=_('Additional Information'),
        help_text=_('Additional information about the medication'),
        blank=True
    )
    
    # Enhanced search configuration
    search_fields = Page.search_fields + [
        index.SearchField('additional_info'),
        index.SearchField('content'),
        index.RelatedFields('medication', [
            index.SearchField('name'),
            index.SearchField('generic_name'),
            index.SearchField('description'),
            index.SearchField('active_ingredients'),
        ]),
    ]
    
    # Enhanced admin panels
    content_panels = Page.content_panels + [
        FieldPanel('medication'),
        FieldPanel('content'),
        FieldPanel('additional_info'),
    ]
    
    # Page configuration
    parent_page_types = ['medications.MedicationIndexPage']
    subpage_types = []
    
    class Meta:
        verbose_name = _('Medication Detail Page')
        verbose_name_plural = _('Medication Detail Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Add medication details to the template context."""
        context = super().get_context(request, *args, **kwargs)
        context['medication'] = self.medication
        return context


class Medication(models.Model):
    """
    Enhanced Medication model with Wagtail 7.0.2 StreamField integration.
    """
    
    # Medication type choices
    class MedicationType(models.TextChoices):
        TABLET = 'tablet', _('Tablet')
        CAPSULE = 'capsule', _('Capsule')
        LIQUID = 'liquid', _('Liquid')
        INJECTION = 'injection', _('Injection')
        INHALER = 'inhaler', _('Inhaler')
        CREAM = 'cream', _('Cream')
        OINTMENT = 'ointment', _('Ointment')
        DROPS = 'drops', _('Drops')
        PATCH = 'patch', _('Patch')
        OTHER = 'other', _('Other')
    
    # Prescription type choices
    class PrescriptionType(models.TextChoices):
        PRESCRIPTION = 'prescription', _('Prescription Required')
        OVER_THE_COUNTER = 'otc', _('Over the Counter')
        SUPPLEMENT = 'supplement', _('Supplement')
        SCHEDULE_1 = 'schedule_1', _('Schedule 1 - Highly Addictive')
        SCHEDULE_2 = 'schedule_2', _('Schedule 2 - Addictive')
        SCHEDULE_3 = 'schedule_3', _('Schedule 3 - Moderate Risk')
        SCHEDULE_4 = 'schedule_4', _('Schedule 4 - Low Risk')
        SCHEDULE_5 = 'schedule_5', _('Schedule 5 - Minimal Risk')
        SCHEDULE_6 = 'schedule_6', _('Schedule 6 - Poisonous')
        SCHEDULE_7 = 'schedule_7', _('Schedule 7 - Dangerous')
        COMPOUNDED = 'compounded', _('Compounded Medication')
        GENERIC = 'generic', _('Generic Medication')
        BRANDED = 'branded', _('Branded Medication')
    
    # Basic medication information
    name = models.CharField(
        max_length=200,
        help_text=_('Name of the medication')
    )
    
    generic_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Generic name of the medication')
    )
    
    brand_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Brand name of the medication')
    )
    
    medication_type = models.CharField(
        max_length=20,
        choices=MedicationType.choices,
        default=MedicationType.TABLET,
        help_text=_('Type of medication')
    )
    
    prescription_type = models.CharField(
        max_length=20,
        choices=PrescriptionType.choices,
        default=PrescriptionType.PRESCRIPTION,
        help_text=_('Type of prescription required')
    )
    
    # Enhanced content with StreamField
    content = StreamField(
        MedicationContentStreamBlock(),
        verbose_name=_('Medication Content'),
        help_text=_('Rich content for the medication including dosages, side effects, interactions, etc.'),
        blank=True,
        use_json_field=True  # Wagtail 7.0.2 performance improvement
    )
    
    # Dosage information
    strength = models.CharField(
        max_length=50,
        help_text=_('Strength of the medication (e.g., 500mg, 10mg/ml)')
    )
    
    dosage_unit = models.CharField(
        max_length=20,
        help_text=_('Unit of dosage (e.g., mg, ml, mcg)')
    )
    
    # Stock management
    pill_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Current number of pills/units in stock')
    )
    
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text=_('Threshold for low stock alerts')
    )
    
    # Additional information
    description = models.TextField(
        blank=True,
        help_text=_('Description of the medication')
    )
    
    active_ingredients = models.TextField(
        blank=True,
        help_text=_('Active ingredients in the medication')
    )
    
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Manufacturer of the medication')
    )
    
    # Wagtail 7.0.2: Enhanced ForeignKey relationships to snippet models
    manufacturer_snippet = models.ForeignKey(
        'medications.MedicationManufacturer',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medications',
        help_text=_('Manufacturer information from snippet')
    )
    
    category = models.ForeignKey(
        'medications.MedicationCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medications',
        help_text=_('Medication category')
    )
    
    dosage_form = models.ForeignKey(
        'medications.DosageForm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medications',
        help_text=_('Dosage form of the medication')
    )
    
    # Many-to-many relationship with active ingredients
    active_ingredients_snippets = models.ManyToManyField(
        'medications.ActiveIngredient',
        blank=True,
        related_name='medications',
        help_text=_('Active ingredients from snippets')
    )
    
    # Safety information
    side_effects = models.TextField(
        blank=True,
        help_text=_('Common side effects')
    )
    
    contraindications = models.TextField(
        blank=True,
        help_text=_('Contraindications and warnings')
    )
    
    # Storage and handling
    storage_instructions = models.TextField(
        blank=True,
        help_text=_('Storage instructions for the medication')
    )
    
    # Enhanced image fields with Wagtail 7.0.2 improvements
    medication_image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_images',
        help_text=_('Primary medication image with enhanced focal point handling')
    )
    
    medication_image_thumbnail = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_thumbnails',
        help_text=_('Thumbnail version of medication image')
    )
    
    medication_image_webp = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_webp',
        help_text=_('WebP optimized version of medication image')
    )
    
    medication_image_avif = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_avif',
        help_text=_('AVIF optimized version of medication image')
    )
    
    medication_image_jpeg_xl = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_jxl',
        help_text=_('JPEG XL optimized version of medication image')
    )
    
    medication_image_original = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_original',
        help_text=_('Original unprocessed medication image')
    )
    
    image_alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Alt text for medication image accessibility')
    )
    
    image_processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('processing', _('Processing')),
            ('completed', _('Completed')),
            ('failed', _('Failed')),
        ],
        default='pending',
        help_text=_('Status of image processing')
    )
    
    image_processing_priority = models.CharField(
        max_length=10,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('urgent', _('Urgent'))
        ],
        default='medium',
        help_text=_('Priority level for image processing')
    )
    
    image_processing_attempts = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of image processing attempts')
    )
    
    image_processing_last_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time image processing was attempted')
    )
    
    image_processing_error = models.TextField(
        blank=True,
        help_text=_('Last error message from image processing')
    )
    
    image_metadata = models.JSONField(
        default=dict,
        help_text=_('Metadata about the medication image (dimensions, format, etc.)')
    )
    
    image_optimization_level = models.CharField(
        max_length=10,
        choices=[
            ('none', _('None')),
            ('basic', _('Basic')),
            ('standard', _('Standard')),
            ('high', _('High')),
            ('maximum', _('Maximum'))
        ],
        default='standard',
        help_text=_('Level of image optimization applied')
    )
    
    # Wagtail 7.0.2: Enhanced image fields with improved integration
    medication_image = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_images',
        help_text=_('Primary medication image with enhanced focal point handling and responsive sizing')
    )
    
    # Additional medication images for different purposes
    medication_image_packaging = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_packaging_images',
        help_text=_('Image of medication packaging')
    )
    
    medication_image_tablet = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_tablet_images',
        help_text=_('Image of tablet/capsule form')
    )
    
    medication_image_injection = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_injection_images',
        help_text=_('Image of injection device if applicable')
    )
    
    medication_image_inhaler = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='medication_inhaler_images',
        help_text=_('Image of inhaler device if applicable')
    )
    
    # Enhanced image processing fields
    image_alt_text = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Alt text for medication image accessibility')
    )
    
    image_caption = models.CharField(
        max_length=500,
        blank=True,
        help_text=_('Caption for the medication image')
    )
    
    image_credit = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Image credit/attribution')
    )
    
    image_license = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('License information for the image')
    )
    
    # Wagtail 7.0.2: Enhanced image processing status
    image_processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('processing', _('Processing')),
            ('completed', _('Completed')),
            ('failed', _('Failed')),
            ('optimized', _('Optimized')),
            ('responsive_ready', _('Responsive Ready')),
        ],
        default='pending',
        help_text=_('Status of image processing and optimization')
    )
    
    image_processing_priority = models.CharField(
        max_length=10,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('urgent', _('Urgent'))
        ],
        default='medium',
        help_text=_('Priority level for image processing')
    )
    
    image_processing_attempts = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of image processing attempts')
    )
    
    image_processing_last_attempt = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time image processing was attempted')
    )
    
    image_processing_error = models.TextField(
        blank=True,
        help_text=_('Last error message from image processing')
    )
    
    # Wagtail 7.0.2: Enhanced image metadata
    image_metadata = models.JSONField(
        default=dict,
        help_text=_('Enhanced metadata about the medication image (dimensions, format, focal points, etc.)')
    )
    
    image_optimization_level = models.CharField(
        max_length=10,
        choices=[
            ('none', _('None')),
            ('basic', _('Basic')),
            ('standard', _('Standard')),
            ('high', _('High')),
            ('maximum', _('Maximum'))
        ],
        default='standard',
        help_text=_('Level of image optimization applied')
    )
    
    # Wagtail 7.0.2: Responsive image configuration
    image_responsive_sizes = models.JSONField(
        default=list,
        help_text=_('Responsive image sizes configuration')
    )
    
    image_focal_point_x = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Focal point X coordinate (0-1)')
    )
    
    image_focal_point_y = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Focal point Y coordinate (0-1)')
    )
    
    image_aspect_ratio = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('Preferred aspect ratio for this image')
    )
    
    # Wagtail 7.0.2: Image accessibility features
    image_accessibility_features = models.JSONField(
        default=dict,
        help_text=_('Accessibility features for the image (high contrast, color blind friendly, etc.)')
    )
    
    image_alt_text_auto_generated = models.BooleanField(
        default=False,
        help_text=_('Whether alt text was auto-generated')
    )
    
    image_alt_text_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text=_('Confidence score for auto-generated alt text (0-1)')
    )
    
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Expiration date of the medication')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this medication was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this medication was last updated')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration with custom indexing
    search_fields = [
        # Primary search fields with high boost factors
        index.SearchField('name', boost=3.0, partial_match=True),
        index.SearchField('generic_name', boost=2.5, partial_match=True),
        index.SearchField('brand_name', boost=2.0, partial_match=True),
        
        # Content fields with medium boost
        index.SearchField('description', boost=1.5),
        index.SearchField('active_ingredients', boost=1.8),
        index.SearchField('side_effects', boost=1.2),
        index.SearchField('contraindications', boost=1.2),
        index.SearchField('storage_instructions', boost=1.0),
        
        # Manufacturer and type fields
        index.SearchField('manufacturer', boost=1.5, partial_match=True),
        index.SearchField('medication_type', boost=1.0),
        index.SearchField('prescription_type', boost=1.0),
        
        # StreamField content with enhanced indexing
        index.SearchField('content', boost=1.3),
        
        # Strength and dosage information
        index.SearchField('strength', boost=1.2, partial_match=True),
        index.SearchField('dosage_unit', boost=0.8),
        
        # Autocomplete fields for quick search
        index.AutocompleteField('name'),
        index.AutocompleteField('generic_name'),
        index.AutocompleteField('brand_name'),
        index.AutocompleteField('manufacturer'),
        
        # Filter fields for faceted search
        index.FilterField('medication_type'),
        index.FilterField('prescription_type'),
        index.FilterField('manufacturer'),
        index.FilterField('expiration_date'),
        index.FilterField('pill_count'),
        index.FilterField('is_low_stock'),
        index.FilterField('is_expired'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        # Basic Information Panel with enhanced ForeignKey panels
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('generic_name'),
            FieldPanel('brand_name'),
            FieldPanel('medication_type'),
            FieldPanel('prescription_type'),
            FieldPanel('category'),  # Enhanced ForeignKey panel with snippet
            FieldPanel('dosage_form'),  # Enhanced ForeignKey panel with snippet
        ], heading=_('Basic Information'), classname='collapsible'),
        
        # Content Panel with StreamField and enhanced relationships
        MultiFieldPanel([
            FieldPanel('content'),
            FieldPanel('description'),
            FieldPanel('active_ingredients'),
            FieldPanel('active_ingredients_snippets'),  # Many-to-many with snippets
        ], heading=_('Content & Description'), classname='collapsible'),
        
        # Dosage Information Panel
        MultiFieldPanel([
            FieldPanel('strength'),
            FieldPanel('dosage_unit'),
        ], heading=_('Dosage Information'), classname='collapsible'),
        
        # Stock Management Panel
        MultiFieldPanel([
            FieldPanel('pill_count'),
            FieldPanel('low_stock_threshold'),
            FieldPanel('expiration_date'),
        ], heading=_('Stock Management'), classname='collapsible'),
        
        # Safety Information Panel
        MultiFieldPanel([
            FieldPanel('side_effects'),
            FieldPanel('contraindications'),
            FieldPanel('storage_instructions'),
        ], heading=_('Safety & Storage'), classname='collapsible'),
        
        # Enhanced Image Panel with Wagtail 7.0.2 features
        MultiFieldPanel([
            FieldPanel('medication_image'),
            FieldPanel('medication_image_packaging'),
            FieldPanel('medication_image_tablet'),
            FieldPanel('medication_image_injection'),
            FieldPanel('medication_image_inhaler'),
        ], heading=_('Primary Images'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('image_alt_text'),
            FieldPanel('image_caption'),
            FieldPanel('image_credit'),
            FieldPanel('image_license'),
        ], heading=_('Image Metadata'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('image_processing_status'),
            FieldPanel('image_processing_priority'),
            FieldPanel('image_optimization_level'),
            FieldPanel('image_focal_point_x'),
            FieldPanel('image_focal_point_y'),
            FieldPanel('image_aspect_ratio'),
        ], heading=_('Image Processing'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('image_accessibility_features'),
            FieldPanel('image_alt_text_auto_generated'),
            FieldPanel('image_alt_text_confidence'),
        ], heading=_('Accessibility'), classname='collapsible'),
        
        # Enhanced Manufacturer Information Panel with snippet integration
        MultiFieldPanel([
            FieldPanel('manufacturer'),  # Legacy field for backward compatibility
            FieldPanel('manufacturer_snippet'),  # Enhanced ForeignKey panel with snippet
        ], heading=_('Manufacturer Information'), classname='collapsible'),
        
        # Wagtail 7.0.2: Enhanced inline panels for medication schedules
        InlinePanel('schedules', label=_('Medication Schedules'), min_num=0, max_num=10),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        # Basic Information Panel with enhanced ForeignKey panels
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('generic_name'),
            FieldPanel('brand_name'),
            FieldPanel('medication_type'),
            FieldPanel('prescription_type'),
            FieldPanel('category'),  # Enhanced ForeignKey panel with snippet
            FieldPanel('dosage_form'),  # Enhanced ForeignKey panel with snippet
        ], heading=_('Basic Information'), classname='collapsible'),
        
        # Content Panel with StreamField and enhanced relationships
        MultiFieldPanel([
            FieldPanel('content'),
            FieldPanel('description'),
            FieldPanel('active_ingredients'),
            FieldPanel('active_ingredients_snippets'),  # Many-to-many with snippets
        ], heading=_('Content & Description'), classname='collapsible'),
        
        # Dosage Information Panel
        MultiFieldPanel([
            FieldPanel('strength'),
            FieldPanel('dosage_unit'),
        ], heading=_('Dosage Information'), classname='collapsible'),
        
        # Stock Management Panel
        MultiFieldPanel([
            FieldPanel('pill_count'),
            FieldPanel('low_stock_threshold'),
            FieldPanel('expiration_date'),
        ], heading=_('Stock Management'), classname='collapsible'),
        
        # Safety Information Panel
        MultiFieldPanel([
            FieldPanel('side_effects'),
            FieldPanel('contraindications'),
            FieldPanel('storage_instructions'),
        ], heading=_('Safety & Storage'), classname='collapsible'),
        
        # Enhanced Image Panel with Wagtail 7.0.2 features
        MultiFieldPanel([
            FieldPanel('medication_image'),
            FieldPanel('image_alt_text'),
            FieldPanel('image_processing_status'),
            FieldPanel('image_processing_priority'),
        ], heading=_('Images & Media'), classname='collapsible'),
        
        # Enhanced Image Panel with Wagtail 7.0.2 features
        MultiFieldPanel([
            FieldPanel('medication_image'),
            FieldPanel('medication_image_packaging'),
            FieldPanel('medication_image_tablet'),
            FieldPanel('medication_image_injection'),
            FieldPanel('medication_image_inhaler'),
        ], heading=_('Primary Images'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('image_alt_text'),
            FieldPanel('image_caption'),
            FieldPanel('image_credit'),
            FieldPanel('image_license'),
        ], heading=_('Image Metadata'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('image_processing_status'),
            FieldPanel('image_processing_priority'),
            FieldPanel('image_optimization_level'),
            FieldPanel('image_focal_point_x'),
            FieldPanel('image_focal_point_y'),
            FieldPanel('image_aspect_ratio'),
        ], heading=_('Image Processing'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('image_accessibility_features'),
            FieldPanel('image_alt_text_auto_generated'),
            FieldPanel('image_alt_text_confidence'),
        ], heading=_('Accessibility'), classname='collapsible'),
        
        # Enhanced Manufacturer Information Panel with snippet integration
        MultiFieldPanel([
            FieldPanel('manufacturer'),  # Legacy field for backward compatibility
            FieldPanel('manufacturer_snippet'),  # Enhanced ForeignKey panel with snippet
        ], heading=_('Manufacturer Information'), classname='collapsible'),
    ]
    
    class Meta:
        verbose_name = _('Medication')
        verbose_name_plural = _('Medications')
        db_table = 'medications'
        indexes = [
            # Single field indexes for basic queries
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['medication_type']),
            models.Index(fields=['prescription_type']),
            models.Index(fields=['manufacturer']),
            models.Index(fields=['expiration_date']),
            models.Index(fields=['created_at']),
            models.Index(fields=['updated_at']),
            
            # Composite indexes for complex queries
            models.Index(fields=['medication_type', 'prescription_type']),
            models.Index(fields=['manufacturer', 'medication_type']),
            models.Index(fields=['name', 'generic_name']),
            
            # Additional composite indexes for performance
            models.Index(fields=['pill_count', 'low_stock_threshold'], name='medication_stock_threshold_idx'),
            models.Index(fields=['expiration_date', 'pill_count'], name='medication_expiry_stock_idx'),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    @property
    def is_low_stock(self):
        """Check if medication is low in stock."""
        return self.pill_count <= self.low_stock_threshold
    
    @property
    def is_expired(self):
        """Check if medication is expired."""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False
    
    @property
    def is_expiring_soon(self):
        """Check if medication is expiring within 30 days."""
        if self.expiration_date:
            from datetime import timedelta
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            return self.expiration_date <= thirty_days_from_now
        return False
    
    def clean(self):
        """Custom validation for the model."""
        # Validate pill count is not negative
        if self.pill_count < 0:
            raise ValidationError({
                'pill_count': _('Pill count cannot be negative')
            })
        
        # Validate low stock threshold
        if self.low_stock_threshold < 1:
            raise ValidationError({
                'low_stock_threshold': _('Low stock threshold must be at least 1')
            })
        
        # Validate expiration date is not in the past
        if self.expiration_date and self.expiration_date < timezone.now().date():
            raise ValidationError({
                'expiration_date': _('Expiration date cannot be in the past')
            })
    
    # Wagtail 7.0.2: Enhanced search methods
    def get_search_display_title(self):
        """Return the title to display in search results."""
        return f"{self.name} ({self.strength})"
    
    def get_search_description(self):
        """Return the description to display in search results."""
        if self.description:
            return self.description[:200] + "..." if len(self.description) > 200 else self.description
        return f"{self.medication_type} medication by {self.manufacturer}" if self.manufacturer else f"{self.medication_type} medication"
    
    def get_search_url(self, request=None):
        """Return the URL for this medication in search results."""
        # This would typically link to a detail page
        return f"/medications/{self.id}/"
    
    def get_search_meta(self):
        """Return additional metadata for search results."""
        return {
            'medication_type': self.get_medication_type_display(),
            'prescription_type': self.get_prescription_type_display(),
            'manufacturer': self.manufacturer,
            'stock_status': 'Low Stock' if self.is_low_stock else 'In Stock',
            'expiration_status': 'Expired' if self.is_expired else 'Valid',
        }


class MedicationSchedule(models.Model):
    """
    Medication schedule model for tracking when medications should be taken.
    """
    
    # Timing choices
    class Timing(models.TextChoices):
        MORNING = 'morning', _('Morning')
        NOON = 'noon', _('Noon')
        NIGHT = 'night', _('Night')
        CUSTOM = 'custom', _('Custom Time')
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PAUSED = 'paused', _('Paused')
        COMPLETED = 'completed', _('Completed')
    
    # Relationships
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medication_schedules',
        limit_choices_to={'user_type': 'PATIENT'},
        help_text=_('Patient for whom this schedule is created')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text=_('Medication to be taken')
    )
    
    # Schedule information
    timing = models.CharField(
        max_length=20,
        choices=Timing.choices,
        default=Timing.MORNING,
        help_text=_('When the medication should be taken')
    )
    
    custom_time = models.TimeField(
        null=True,
        blank=True,
        help_text=_('Custom time for medication (if timing is custom)')
    )
    
    dosage_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Amount of medication to take')
    )
    
    frequency = models.CharField(
        max_length=50,
        default='daily',
        help_text=_('How often to take the medication (e.g., daily, twice daily, weekly)')
    )
    
    # Days of the week (for weekly schedules)
    monday = models.BooleanField(
        default=True,
        help_text=_('Take medication on Monday')
    )
    tuesday = models.BooleanField(
        default=True,
        help_text=_('Take medication on Tuesday')
    )
    wednesday = models.BooleanField(
        default=True,
        help_text=_('Take medication on Wednesday')
    )
    thursday = models.BooleanField(
        default=True,
        help_text=_('Take medication on Thursday')
    )
    friday = models.BooleanField(
        default=True,
        help_text=_('Take medication on Friday')
    )
    saturday = models.BooleanField(
        default=True,
        help_text=_('Take medication on Saturday')
    )
    sunday = models.BooleanField(
        default=True,
        help_text=_('Take medication on Sunday')
    )
    
    # Schedule period
    start_date = models.DateField(
        default=timezone.now,
        help_text=_('Date when medication schedule starts')
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Date when medication schedule ends (optional)')
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text=_('Current status of the medication schedule')
    )
    
    instructions = models.TextField(
        blank=True,
        help_text=_('Special instructions for taking the medication')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this medication schedule was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this medication schedule was last updated')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('instructions', boost=1.5),
        index.SearchField('frequency', boost=1.2),
        index.RelatedFields('patient', [
            index.SearchField('first_name', boost=1.5),
            index.SearchField('last_name', boost=1.5),
        ]),
        index.RelatedFields('medication', [
            index.SearchField('name', boost=2.0),
        ]),
        index.FilterField('status'),
        index.FilterField('timing'),
        index.FilterField('start_date'),
        index.FilterField('end_date'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels for inline editing
    panels = [
        MultiFieldPanel([
            FieldPanel('patient'),
            FieldPanel('medication'),
            FieldPanel('status'),
        ], heading=_('Basic Information')),
        
        MultiFieldPanel([
            FieldPanel('timing'),
            FieldPanel('custom_time'),
            FieldPanel('dosage_amount'),
            FieldPanel('frequency'),
        ], heading=_('Schedule Details')),
        
        MultiFieldPanel([
            FieldPanel('monday'),
            FieldPanel('tuesday'),
            FieldPanel('wednesday'),
            FieldPanel('thursday'),
            FieldPanel('friday'),
            FieldPanel('saturday'),
            FieldPanel('sunday'),
        ], heading=_('Days of Week')),
        
        MultiFieldPanel([
            FieldPanel('start_date'),
            FieldPanel('end_date'),
        ], heading=_('Schedule Period')),
        
        MultiFieldPanel([
            FieldPanel('instructions'),
        ], heading=_('Instructions')),
    ]
    
    class Meta:
        verbose_name = _('Medication Schedule')
        verbose_name_plural = _('Medication Schedules')
        db_table = 'medication_schedules'
        indexes = [
            models.Index(fields=['patient', 'medication']),
            models.Index(fields=['timing']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['patient', 'timing', 'start_date']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.medication.name} ({self.timing})"
    
    @property
    def is_active(self):
        """Check if schedule is currently active."""
        today = timezone.now().date()
        if self.status != self.Status.ACTIVE:
            return False
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
    
    @property
    def should_take_today(self):
        """Check if medication should be taken today."""
        if not self.is_active:
            return False
        
        today = timezone.now().date()
        weekday = today.weekday()  # Monday=0, Sunday=6
        
        day_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        return getattr(self, day_fields[weekday])
    
    def clean(self):
        """Custom validation for the model."""
        # Validate custom time is provided when timing is custom
        if self.timing == self.Timing.CUSTOM and not self.custom_time:
            raise ValidationError({
                'custom_time': _('Custom time is required when timing is set to custom')
            })
        
        # Validate end date is after start date
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError({
                'end_date': _('End date must be after start date')
            })
        
        # Validate at least one day is selected
        days_selected = any([
            self.monday, self.tuesday, self.wednesday, self.thursday,
            self.friday, self.saturday, self.sunday
        ])
        if not days_selected:
            raise ValidationError(_('At least one day of the week must be selected'))


class MedicationLog(models.Model):
    """
    Medication log model for tracking medication adherence history.
    """
    
    # Status choices
    class Status(models.TextChoices):
        TAKEN = 'taken', _('Taken')
        MISSED = 'missed', _('Missed')
        SKIPPED = 'skipped', _('Skipped')
        PARTIAL = 'partial', _('Partial Dose')
    
    # Relationships
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medication_logs',
        limit_choices_to={'user_type': 'PATIENT'},
        help_text=_('Patient who took the medication')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text=_('Medication that was taken')
    )
    
    schedule = models.ForeignKey(
        MedicationSchedule,
        on_delete=models.CASCADE,
        related_name='medication_logs',
        null=True,
        blank=True,
        help_text=_('Associated medication schedule')
    )
    
    # Log information
    scheduled_time = models.DateTimeField(
        help_text=_('When the medication was scheduled to be taken')
    )
    
    actual_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the medication was actually taken')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.MISSED,
        help_text=_('Status of the medication dose')
    )
    
    dosage_taken = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Actual dosage taken')
    )
    
    # Notes and observations
    notes = models.TextField(
        blank=True,
        help_text=_('Notes about the medication dose')
    )
    
    side_effects = models.TextField(
        blank=True,
        help_text=_('Any side effects experienced')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this medication log was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this medication log was last updated')
    )
    
    class Meta:
        verbose_name = _('Medication Log')
        verbose_name_plural = _('Medication Logs')
        db_table = 'medication_logs'
        indexes = [
            models.Index(fields=['patient', 'medication']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['status']),
            models.Index(fields=['actual_time']),
        ]
        ordering = ['-scheduled_time']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.medication.name} ({self.status})"
    
    @property
    def is_on_time(self):
        """Check if medication was taken on time (within 1 hour of scheduled time)."""
        if not self.actual_time or self.status != self.Status.TAKEN:
            return False
        
        from datetime import timedelta
        time_diff = abs((self.actual_time - self.scheduled_time).total_seconds() / 3600)
        return time_diff <= 1
    
    @property
    def adherence_score(self):
        """Calculate adherence score for this log entry."""
        if self.status == self.Status.TAKEN:
            if self.is_on_time:
                return 100
            else:
                return 80  # Taken but late
        elif self.status == self.Status.PARTIAL:
            return 50
        elif self.status == self.Status.SKIPPED:
            return 0
        else:  # MISSED
            return 0
    
    def clean(self):
        """Custom validation for the model."""
        # Validate actual time is not in the future
        if self.actual_time and self.actual_time > timezone.now():
            raise ValidationError({
                'actual_time': _('Actual time cannot be in the future')
            })
        
        # Validate dosage taken is provided when status is taken or partial
        if self.status in [self.Status.TAKEN, self.Status.PARTIAL] and not self.dosage_taken:
            raise ValidationError({
                'dosage_taken': _('Dosage taken is required when medication is taken or partially taken')
            })


class StockAlert(models.Model):
    """
    Stock alert model for tracking low inventory warnings.
    """
    
    # Alert type choices
    class AlertType(models.TextChoices):
        LOW_STOCK = 'low_stock', _('Low Stock')
        OUT_OF_STOCK = 'out_of_stock', _('Out of Stock')
        EXPIRING_SOON = 'expiring_soon', _('Expiring Soon')
        EXPIRED = 'expired', _('Expired')
    
    # Priority choices
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        ACKNOWLEDGED = 'acknowledged', _('Acknowledged')
        RESOLVED = 'resolved', _('Resolved')
        DISMISSED = 'dismissed', _('Dismissed')
    
    # Relationships
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        help_text=_('Medication associated with this alert')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_alerts',
        help_text=_('User who created the alert')
    )
    
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='acknowledged_alerts',
        null=True,
        blank=True,
        help_text=_('User who acknowledged the alert')
    )
    
    # Alert information
    alert_type = models.CharField(
        max_length=20,
        choices=AlertType.choices,
        help_text=_('Type of stock alert')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text=_('Priority level of the alert')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text=_('Current status of the alert')
    )
    
    # Alert details
    title = models.CharField(
        max_length=200,
        help_text=_('Title of the alert')
    )
    
    message = models.TextField(
        help_text=_('Detailed message of the alert')
    )
    
    current_stock = models.PositiveIntegerField(
        help_text=_('Current stock level when alert was created')
    )
    
    threshold_level = models.PositiveIntegerField(
        help_text=_('Threshold level that triggered the alert')
    )
    
    # Resolution information
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the alert was resolved')
    )
    
    resolution_notes = models.TextField(
        blank=True,
        help_text=_('Notes about how the alert was resolved')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this stock alert was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this stock alert was last updated')
    )
    acknowledged_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_('When this alert was acknowledged')
    )
    
    class Meta:
        verbose_name = _('Stock Alert')
        verbose_name_plural = _('Stock Alerts')
        db_table = 'stock_alerts'
        indexes = [
            models.Index(fields=['medication']),
            models.Index(fields=['alert_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medication.name} - {self.alert_type} ({self.priority})"
    
    @property
    def is_active(self):
        """Check if alert is currently active."""
        return self.status == self.Status.ACTIVE
    
    @property
    def is_critical(self):
        """Check if alert is critical priority."""
        return self.priority == self.Priority.CRITICAL
    
    def acknowledge(self, user):
        """Acknowledge the alert."""
        self.status = self.Status.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, notes=""):
        """Resolve the alert."""
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
    
    def dismiss(self):
        """Dismiss the alert."""
        self.status = self.Status.DISMISSED
        self.save()
    
    def clean(self):
        """Custom validation for the model."""
        # Validate current stock is not negative
        if self.current_stock < 0:
            raise ValidationError({
                'current_stock': _('Current stock cannot be negative')
            })
        
        # Validate threshold level is positive
        if self.threshold_level <= 0:
            raise ValidationError({
                'threshold_level': _('Threshold level must be positive')
            })
        
        # Validate acknowledged_by is set when status is acknowledged
        if self.status == self.Status.ACKNOWLEDGED and not self.acknowledged_by:
            raise ValidationError({
                'acknowledged_by': _('Acknowledged by must be set when status is acknowledged')
            })


class StockTransaction(models.Model):
    """
    Stock transaction model for tracking all stock movements with detailed analytics.
    """
    
    # Transaction type choices
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', _('Purchase')
        SALE = 'sale', _('Sale')
        ADJUSTMENT = 'adjustment', _('Adjustment')
        TRANSFER = 'transfer', _('Transfer')
        EXPIRY = 'expiry', _('Expiry')
        DAMAGE = 'damage', _('Damage')
        RETURN = 'return', _('Return')
        PRESCRIPTION_FILLED = 'prescription_filled', _('Prescription Filled')
        DOSE_TAKEN = 'dose_taken', _('Dose Taken')
    
    # Relationships
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        help_text=_('Medication involved in this transaction')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        help_text=_('User who initiated this transaction')
    )
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        help_text=_('Type of stock transaction')
    )
    
    quantity = models.IntegerField(
        help_text=_('Quantity involved in the transaction (positive for additions, negative for removals)')
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Unit price for the transaction')
    )
    
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total amount for the transaction')
    )
    
    # Stock levels before and after
    stock_before = models.PositiveIntegerField(
        help_text=_('Stock level before this transaction')
    )
    
    stock_after = models.PositiveIntegerField(
        help_text=_('Stock level after this transaction')
    )
    
    # Reference information
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Reference number for the transaction (invoice, prescription, etc.)')
    )
    
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Batch number for the medication')
    )
    
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Expiry date for this batch')
    )
    
    # Notes and metadata
    notes = models.TextField(
        blank=True,
        help_text=_('Additional notes about the transaction')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this stock transaction was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this stock transaction was last updated')
    )
    
    class Meta:
        verbose_name = _('Stock Transaction')
        verbose_name_plural = _('Stock Transactions')
        db_table = 'stock_transactions'
        indexes = [
            models.Index(fields=['medication', 'transaction_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medication.name} - {self.get_transaction_type_display()} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        """Override save to update medication stock and calculate totals."""
        if not self.pk:  # New transaction
            self.stock_before = self.medication.pill_count
            self.stock_after = self.stock_before + self.quantity
            
            # Calculate total amount if unit price is provided
            if self.unit_price and not self.total_amount:
                self.total_amount = self.unit_price * abs(self.quantity)
        
        super().save(*args, **kwargs)
        
        # Update medication stock
        self.medication.pill_count = self.stock_after
        self.medication.save(update_fields=['pill_count'])
    
    @property
    def is_addition(self):
        """Check if this transaction adds stock."""
        return self.quantity > 0
    
    @property
    def is_removal(self):
        """Check if this transaction removes stock."""
        return self.quantity < 0


class StockAnalytics(models.Model):
    """
    Stock analytics model for storing calculated metrics and predictions.
    """
    
    # Relationships
    medication = models.OneToOneField(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_analytics',
        help_text=_('Medication for these analytics')
    )
    
    # Usage patterns
    daily_usage_rate = models.FloatField(
        default=0.0,
        help_text=_('Average daily usage rate (units per day)')
    )
    
    weekly_usage_rate = models.FloatField(
        default=0.0,
        help_text=_('Average weekly usage rate (units per week)')
    )
    
    monthly_usage_rate = models.FloatField(
        default=0.0,
        help_text=_('Average monthly usage rate (units per month)')
    )
    
    # Stock predictions
    days_until_stockout = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Predicted days until stock runs out')
    )
    
    predicted_stockout_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Predicted date when stock will run out')
    )
    
    recommended_order_quantity = models.PositiveIntegerField(
        default=0,
        help_text=_('Recommended quantity to order')
    )
    
    recommended_order_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Recommended date to place order')
    )
    
    # Seasonal patterns
    seasonal_factor = models.FloatField(
        default=1.0,
        help_text=_('Seasonal adjustment factor for usage patterns')
    )
    
    # Variability metrics
    usage_volatility = models.FloatField(
        default=0.0,
        help_text=_('Standard deviation of daily usage')
    )
    
    # Confidence intervals
    stockout_confidence = models.FloatField(
        default=0.0,
        help_text=_('Confidence level for stockout prediction (0-1)')
    )
    
    # Last calculation
    last_calculated = models.DateTimeField(
        auto_now=True,
        help_text=_('When these analytics were last calculated')
    )
    
    # Calculation parameters
    calculation_window_days = models.PositiveIntegerField(
        default=90,
        help_text=_('Number of days to use for calculations')
    )
    
    class Meta:
        verbose_name = _('Stock Analytics')
        verbose_name_plural = _('Stock Analytics')
        db_table = 'stock_analytics'
        indexes = [
            models.Index(fields=['medication']),
            models.Index(fields=['last_calculated']),
            models.Index(fields=['days_until_stockout']),
        ]
    
    def __str__(self):
        return f"Analytics for {self.medication.name}"
    
    @property
    def is_stockout_imminent(self):
        """Check if stockout is predicted within 7 days."""
        return self.days_until_stockout is not None and self.days_until_stockout <= 7
    
    @property
    def is_order_needed(self):
        """Check if an order is recommended within 14 days."""
        return (self.recommended_order_date and 
                self.recommended_order_date <= timezone.now().date() + timezone.timedelta(days=14))


class PharmacyIntegration(models.Model):
    """
    Pharmacy integration model for managing connections to external pharmacy systems.
    """
    
    # Integration type choices
    class IntegrationType(models.TextChoices):
        API = 'api', _('API Integration')
        EDI = 'edi', _('EDI Integration')
        MANUAL = 'manual', _('Manual Integration')
        WEBHOOK = 'webhook', _('Webhook Integration')
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        TESTING = 'testing', _('Testing')
        ERROR = 'error', _('Error')
    
    # Basic information
    name = models.CharField(
        max_length=200,
        help_text=_('Name of the pharmacy integration')
    )
    
    pharmacy_name = models.CharField(
        max_length=200,
        help_text=_('Name of the pharmacy')
    )
    
    integration_type = models.CharField(
        max_length=20,
        choices=IntegrationType.choices,
        default=IntegrationType.API,
        help_text=_('Type of integration')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INACTIVE,
        help_text=_('Current status of the integration')
    )
    
    # Connection details
    api_endpoint = models.URLField(
        blank=True,
        help_text=_('API endpoint for the integration')
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('API key for authentication')
    )
    
    webhook_url = models.URLField(
        blank=True,
        help_text=_('Webhook URL for receiving updates')
    )
    
    # Configuration
    auto_order_enabled = models.BooleanField(
        default=False,
        help_text=_('Whether to enable automatic ordering')
    )
    
    order_threshold = models.PositiveIntegerField(
        default=10,
        help_text=_('Stock threshold for automatic ordering')
    )
    
    order_quantity_multiplier = models.FloatField(
        default=1.0,
        help_text=_('Multiplier for order quantities')
    )
    
    # Scheduling
    order_lead_time_days = models.PositiveIntegerField(
        default=3,
        help_text=_('Expected lead time for orders in days')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this pharmacy integration was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this pharmacy integration was last updated')
    )
    last_sync = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_('When this integration was last synchronized')
    )
    
    class Meta:
        verbose_name = _('Pharmacy Integration')
        verbose_name_plural = _('Pharmacy Integrations')
        db_table = 'pharmacy_integrations'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['integration_type']),
            models.Index(fields=['last_sync']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.pharmacy_name} - {self.get_integration_type_display()}"


class PrescriptionRenewal(models.Model):
    """
    Prescription renewal model for tracking prescription renewals and reminders.
    """
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        PENDING_RENEWAL = 'pending_renewal', _('Pending Renewal')
        RENEWED = 'renewed', _('Renewed')
        EXPIRED = 'expired', _('Expired')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Priority choices
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    # Relationships
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prescription_renewals',
        limit_choices_to={'user_type': 'PATIENT'},
        help_text=_('Patient for this prescription')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='prescription_renewals',
        help_text=_('Medication for this prescription')
    )
    
    # Prescription details
    prescription_number = models.CharField(
        max_length=100,
        help_text=_('Prescription number')
    )
    
    prescribed_by = models.CharField(
        max_length=200,
        help_text=_('Name of the prescribing doctor')
    )
    
    prescribed_date = models.DateField(
        help_text=_('Date when prescription was issued')
    )
    
    expiry_date = models.DateField(
        help_text=_('Date when prescription expires')
    )
    
    # Renewal information
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text=_('Current status of the prescription')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text=_('Priority level for renewal')
    )
    
    # Reminder settings
    reminder_days_before = models.PositiveIntegerField(
        default=30,
        help_text=_('Days before expiry to start sending reminders')
    )
    
    last_reminder_sent = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the last reminder was sent')
    )
    
    # Renewal tracking
    renewed_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Date when prescription was renewed')
    )
    
    new_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('New expiry date after renewal')
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text=_('Additional notes about the prescription')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this prescription renewal was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this prescription renewal was last updated')
    )
    
    class Meta:
        verbose_name = _('Prescription Renewal')
        verbose_name_plural = _('Prescription Renewals')
        db_table = 'prescription_renewals'
        indexes = [
            models.Index(fields=['patient', 'medication']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['prescribed_date']),
        ]
        ordering = ['expiry_date']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.medication.name} ({self.prescription_number})"
    
    @property
    def is_expired(self):
        """Check if prescription is expired."""
        return self.expiry_date < timezone.now().date()
    
    @property
    def is_expiring_soon(self):
        """Check if prescription is expiring within reminder period."""
        from datetime import timedelta
        reminder_date = self.expiry_date - timedelta(days=self.reminder_days_before)
        return reminder_date <= timezone.now().date() <= self.expiry_date
    
    @property
    def days_until_expiry(self):
        """Calculate days until prescription expires."""
        return (self.expiry_date - timezone.now().date()).days
    
    @property
    def needs_renewal(self):
        """Check if prescription needs renewal."""
        return self.status == self.Status.ACTIVE and self.is_expiring_soon
    
    def renew(self, new_expiry_date):
        """Renew the prescription."""
        self.status = self.Status.RENEWED
        self.renewed_date = timezone.now().date()
        self.new_expiry_date = new_expiry_date
        self.save()


class StockVisualization(models.Model):
    """
    Stock visualization model for storing chart data and analytics.
    """
    
    # Chart type choices
    class ChartType(models.TextChoices):
        LINE = 'line', _('Line Chart')
        BAR = 'bar', _('Bar Chart')
        PIE = 'pie', _('Pie Chart')
        SCATTER = 'scatter', _('Scatter Plot')
        HEATMAP = 'heatmap', _('Heatmap')
    
    # Relationships
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_visualizations',
        help_text=_('Medication for this visualization')
    )
    
    # Chart configuration
    chart_type = models.CharField(
        max_length=20,
        choices=ChartType.choices,
        default=ChartType.LINE,
        help_text=_('Type of chart to display')
    )
    
    title = models.CharField(
        max_length=200,
        help_text=_('Title of the chart')
    )
    
    description = models.TextField(
        blank=True,
        help_text=_('Description of the chart')
    )
    
    # Chart data (JSON format)
    chart_data = models.JSONField(
        default=dict,
        help_text=_('Chart data in JSON format')
    )
    
    # Chart options
    chart_options = models.JSONField(
        default=dict,
        help_text=_('Chart configuration options')
    )
    
    # Time range
    start_date = models.DateField(
        help_text=_('Start date for the chart data')
    )
    
    end_date = models.DateField(
        help_text=_('End date for the chart data')
    )
    
    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this visualization is active')
    )
    
    auto_refresh = models.BooleanField(
        default=True,
        help_text=_('Whether to automatically refresh this chart')
    )
    
    refresh_interval_hours = models.PositiveIntegerField(
        default=24,
        help_text=_('Hours between automatic refreshes')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this stock visualization was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this stock visualization was last updated')
    )
    last_generated = models.DateTimeField(
        null=True, 
        blank=True,
        help_text=_('When this visualization was last generated')
    )
    
    class Meta:
        verbose_name = _('Stock Visualization')
        verbose_name_plural = _('Stock Visualizations')
        db_table = 'stock_visualizations'
        indexes = [
            models.Index(fields=['medication', 'chart_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_generated']),
        ]
        ordering = ['title']
    
    def __str__(self):
        return f"{self.medication.name} - {self.title}"
    
    @property
    def needs_refresh(self):
        """Check if chart needs to be refreshed."""
        if not self.auto_refresh or not self.last_generated:
            return False
        
        from datetime import timedelta
        refresh_time = self.last_generated + timedelta(hours=self.refresh_interval_hours)
        return timezone.now() > refresh_time


# Wagtail 7.0.2: Enhanced snippet models for reusable medication data
@register_snippet
class MedicationManufacturer(models.Model):
    """
    Snippet model for medication manufacturers with enhanced Wagtail 7.0.2 features.
    """
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text=_('Name of the manufacturer')
    )
    
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text=_('Manufacturer code/identifier')
    )
    
    website = models.URLField(
        blank=True,
        help_text=_('Manufacturer website')
    )
    
    email = models.EmailField(
        blank=True,
        help_text=_('Contact email')
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('Contact phone number')
    )
    
    address = models.TextField(
        blank=True,
        help_text=_('Manufacturer address')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Country of origin')
    )
    
    description = RichTextField(
        blank=True,
        help_text=_('Description of the manufacturer'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    logo = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manufacturer_logos',
        help_text=_('Manufacturer logo')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this manufacturer is active')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('name', boost=2.0, partial_match=True),
        index.SearchField('code', boost=1.5, partial_match=True),
        index.SearchField('description', boost=1.0),
        index.SearchField('country', boost=1.0),
        index.AutocompleteField('name'),
        index.AutocompleteField('code'),
        index.FilterField('is_active'),
        index.FilterField('country'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('code'),
            FieldPanel('is_active'),
        ], heading=_('Basic Information')),
        
        MultiFieldPanel([
            FieldPanel('website'),
            FieldPanel('email'),
            FieldPanel('phone'),
        ], heading=_('Contact Information')),
        
        MultiFieldPanel([
            FieldPanel('address'),
            FieldPanel('country'),
        ], heading=_('Location')),
        
        MultiFieldPanel([
            FieldPanel('description'),
            FieldPanel('logo'),
        ], heading=_('Additional Information')),
    ]
    
    class Meta:
        verbose_name = _('Medication Manufacturer')
        verbose_name_plural = _('Medication Manufacturers')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_medication_count(self):
        """Return the number of medications by this manufacturer."""
        return self.medication_set.count()
    
    get_medication_count.short_description = _('Medication Count')


@register_snippet
class ActiveIngredient(models.Model):
    """
    Snippet model for active ingredients with enhanced Wagtail 7.0.2 features.
    """
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text=_('Name of the active ingredient')
    )
    
    chemical_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Chemical name of the ingredient')
    )
    
    molecular_formula = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Molecular formula')
    )
    
    molecular_weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Molecular weight')
    )
    
    description = RichTextField(
        blank=True,
        help_text=_('Description of the active ingredient'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    mechanism_of_action = RichTextField(
        blank=True,
        help_text=_('How this ingredient works'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    therapeutic_class = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Therapeutic class of the ingredient')
    )
    
    side_effects = RichTextField(
        blank=True,
        help_text=_('Common side effects'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    contraindications = RichTextField(
        blank=True,
        help_text=_('Contraindications and warnings'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    interactions = RichTextField(
        blank=True,
        help_text=_('Drug interactions'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    is_controlled_substance = models.BooleanField(
        default=False,
        help_text=_('Whether this is a controlled substance')
    )
    
    schedule = models.CharField(
        max_length=20,
        choices=[
            ('none', _('Not Scheduled')),
            ('schedule_1', _('Schedule 1')),
            ('schedule_2', _('Schedule 2')),
            ('schedule_3', _('Schedule 3')),
            ('schedule_4', _('Schedule 4')),
            ('schedule_5', _('Schedule 5')),
        ],
        default='none',
        help_text=_('Drug schedule classification')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('name', boost=3.0, partial_match=True),
        index.SearchField('chemical_name', boost=2.5, partial_match=True),
        index.SearchField('description', boost=1.5),
        index.SearchField('mechanism_of_action', boost=1.3),
        index.SearchField('therapeutic_class', boost=1.2),
        index.SearchField('side_effects', boost=1.0),
        index.SearchField('contraindications', boost=1.0),
        index.SearchField('interactions', boost=1.0),
        index.AutocompleteField('name'),
        index.AutocompleteField('chemical_name'),
        index.AutocompleteField('therapeutic_class'),
        index.FilterField('is_controlled_substance'),
        index.FilterField('schedule'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('chemical_name'),
            FieldPanel('molecular_formula'),
            FieldPanel('molecular_weight'),
        ], heading=_('Basic Information')),
        
        MultiFieldPanel([
            FieldPanel('description'),
            FieldPanel('mechanism_of_action'),
            FieldPanel('therapeutic_class'),
        ], heading=_('Description & Action')),
        
        MultiFieldPanel([
            FieldPanel('side_effects'),
            FieldPanel('contraindications'),
            FieldPanel('interactions'),
        ], heading=_('Safety Information')),
        
        MultiFieldPanel([
            FieldPanel('is_controlled_substance'),
            FieldPanel('schedule'),
        ], heading=_('Regulatory Information')),
    ]
    
    class Meta:
        verbose_name = _('Active Ingredient')
        verbose_name_plural = _('Active Ingredients')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_medication_count(self):
        """Return the number of medications containing this ingredient."""
        return self.medication_set.count()
    
    get_medication_count.short_description = _('Medication Count')


@register_snippet
class MedicationCategory(models.Model):
    """
    Snippet model for medication categories with enhanced Wagtail 7.0.2 features.
    """
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text=_('Name of the medication category')
    )
    
    code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        help_text=_('Category code/identifier')
    )
    
    description = RichTextField(
        blank=True,
        help_text=_('Description of the category'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text=_('Parent category')
    )
    
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('Icon class for the category')
    )
    
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text=_('Color code for the category (hex format)')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this category is active')
    )
    
    sort_order = models.PositiveIntegerField(
        default=0,
        help_text=_('Sort order for display')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('name', boost=2.0, partial_match=True),
        index.SearchField('code', boost=1.5, partial_match=True),
        index.SearchField('description', boost=1.0),
        index.AutocompleteField('name'),
        index.AutocompleteField('code'),
        index.FilterField('is_active'),
        index.FilterField('parent'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('code'),
            FieldPanel('parent'),
            FieldPanel('is_active'),
            FieldPanel('sort_order'),
        ], heading=_('Basic Information')),
        
        MultiFieldPanel([
            FieldPanel('description'),
        ], heading=_('Description')),
        
        MultiFieldPanel([
            FieldPanel('icon'),
            FieldPanel('color'),
        ], heading=_('Display Options')),
    ]
    
    class Meta:
        verbose_name = _('Medication Category')
        verbose_name_plural = _('Medication Categories')
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def get_medication_count(self):
        """Return the number of medications in this category."""
        return self.medication_set.count()
    
    get_medication_count.short_description = _('Medication Count')
    
    def get_all_children(self):
        """Get all child categories recursively."""
        children = []
        for child in self.children.all():
            children.append(child)
            children.extend(child.get_all_children())
        return children
    
    def get_all_medications(self):
        """Get all medications in this category and its children."""
        from django.db.models import Q
        category_ids = [self.id] + [child.id for child in self.get_all_children()]
        return Medication.objects.filter(category_id__in=category_ids)


@register_snippet
class DosageForm(models.Model):
    """
    Snippet model for dosage forms with enhanced Wagtail 7.0.2 features.
    """
    
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_('Name of the dosage form')
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text=_('Dosage form code')
    )
    
    description = RichTextField(
        blank=True,
        help_text=_('Description of the dosage form'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    administration_method = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('How this form is administered')
    )
    
    absorption_rate = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Typical absorption rate')
    )
    
    onset_of_action = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Typical onset of action')
    )
    
    duration_of_action = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Typical duration of action')
    )
    
    storage_requirements = RichTextField(
        blank=True,
        help_text=_('Special storage requirements'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this dosage form is active')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('name', boost=2.0, partial_match=True),
        index.SearchField('code', boost=1.5, partial_match=True),
        index.SearchField('description', boost=1.0),
        index.SearchField('administration_method', boost=1.2),
        index.AutocompleteField('name'),
        index.AutocompleteField('code'),
        index.FilterField('is_active'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('code'),
            FieldPanel('is_active'),
        ], heading=_('Basic Information')),
        
        MultiFieldPanel([
            FieldPanel('description'),
            FieldPanel('administration_method'),
        ], heading=_('Description & Administration')),
        
        MultiFieldPanel([
            FieldPanel('absorption_rate'),
            FieldPanel('onset_of_action'),
            FieldPanel('duration_of_action'),
        ], heading=_('Pharmacokinetics')),
        
        MultiFieldPanel([
            FieldPanel('storage_requirements'),
        ], heading=_('Storage Requirements')),
    ]
    
    class Meta:
        verbose_name = _('Dosage Form')
        verbose_name_plural = _('Dosage Forms')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_medication_count(self):
        """Return the number of medications in this dosage form."""
        return self.medication_set.count()
    
    get_medication_count.short_description = _('Medication Count')


# Wagtail 7.0.2: Enhanced Prescription model with improved admin features
class EnhancedPrescription(models.Model):
    """
    Enhanced Prescription model with Wagtail 7.0.2 admin improvements.
    This is separate from the original Prescription model to avoid conflicts.
    """
    
    # Status choices
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending Approval')
        APPROVED = 'approved', _('Approved')
        DISPENSED = 'dispensed', _('Dispensed')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        EXPIRED = 'expired', _('Expired')
    
    # Priority choices
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        NORMAL = 'normal', _('Normal')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
        EMERGENCY = 'emergency', _('Emergency')
    
    # Relationships
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        limit_choices_to={'user_type': 'PATIENT'},
        help_text=_('Patient for this prescription')
    )
    
    prescriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prescribed_medications',
        limit_choices_to={'user_type__in': ['DOCTOR', 'PHARMACIST', 'NURSE']},
        help_text=_('Healthcare provider who prescribed the medication')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='prescriptions',
        help_text=_('Prescribed medication')
    )
    
    # Prescription details
    prescription_number = models.CharField(
        max_length=100,
        unique=True,
        help_text=_('Unique prescription number')
    )
    
    prescribed_date = models.DateField(
        default=timezone.now,
        help_text=_('Date when prescription was issued')
    )
    
    expiry_date = models.DateField(
        help_text=_('Date when prescription expires')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text=_('Current status of the prescription')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
        help_text=_('Priority level of the prescription')
    )
    
    # Dosage information
    dosage_instructions = RichTextField(
        help_text=_('Detailed dosage instructions'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    dosage_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Amount of medication to take')
    )
    
    dosage_unit = models.CharField(
        max_length=20,
        help_text=_('Unit of dosage (e.g., mg, ml, tablets)')
    )
    
    frequency = models.CharField(
        max_length=100,
        help_text=_('How often to take the medication')
    )
    
    duration = models.CharField(
        max_length=100,
        help_text=_('Duration of treatment')
    )
    
    # Quantity and refills
    quantity_prescribed = models.PositiveIntegerField(
        help_text=_('Quantity prescribed')
    )
    
    refills_allowed = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of refills allowed')
    )
    
    refills_used = models.PositiveIntegerField(
        default=0,
        help_text=_('Number of refills already used')
    )
    
    # Additional information
    diagnosis = models.TextField(
        blank=True,
        help_text=_('Diagnosis or reason for prescription')
    )
    
    allergies = models.TextField(
        blank=True,
        help_text=_('Known allergies or contraindications')
    )
    
    special_instructions = RichTextField(
        blank=True,
        help_text=_('Special instructions for the patient'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    prescriber_notes = RichTextField(
        blank=True,
        help_text=_('Private notes from the prescriber'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    # Workflow tracking
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_prescriptions',
        help_text=_('User who approved the prescription')
    )
    
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the prescription was approved')
    )
    
    dispensed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dispensed_prescriptions',
        help_text=_('User who dispensed the medication')
    )
    
    dispensed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the medication was dispensed')
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When this prescription was created')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_('When this prescription was last updated')
    )
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        # Primary search fields
        index.SearchField('prescription_number', boost=3.0, partial_match=True),
        index.SearchField('dosage_instructions', boost=2.0),
        index.SearchField('diagnosis', boost=1.5),
        index.SearchField('special_instructions', boost=1.2),
        index.SearchField('prescriber_notes', boost=1.0),
        
        # Related fields
        index.RelatedFields('patient', [
            index.SearchField('first_name', boost=1.5),
            index.SearchField('last_name', boost=1.5),
            index.SearchField('email', boost=1.0),
        ]),
        index.RelatedFields('prescriber', [
            index.SearchField('first_name', boost=1.5),
            index.SearchField('last_name', boost=1.5),
        ]),
        index.RelatedFields('medication', [
            index.SearchField('name', boost=2.0),
            index.SearchField('generic_name', boost=1.8),
        ]),
        
        # Autocomplete fields
        index.AutocompleteField('prescription_number'),
        index.AutocompleteField('patient__first_name'),
        index.AutocompleteField('patient__last_name'),
        index.AutocompleteField('prescriber__first_name'),
        index.AutocompleteField('prescriber__last_name'),
        index.AutocompleteField('medication__name'),
        
        # Filter fields
        index.FilterField('status'),
        index.FilterField('priority'),
        index.FilterField('prescribed_date'),
        index.FilterField('expiry_date'),
        index.FilterField('patient'),
        index.FilterField('prescriber'),
        index.FilterField('medication'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels with workflow integration
    panels = [
        # Basic Information Panel
        MultiFieldPanel([
            FieldPanel('prescription_number'),
            FieldPanel('patient'),
            FieldPanel('prescriber'),
            FieldPanel('medication'),
        ], heading=_('Basic Information'), classname='collapsible'),
        
        # Prescription Details Panel
        MultiFieldPanel([
            FieldPanel('prescribed_date'),
            FieldPanel('expiry_date'),
            FieldPanel('status'),
            FieldPanel('priority'),
        ], heading=_('Prescription Details'), classname='collapsible'),
        
        # Dosage Information Panel
        MultiFieldPanel([
            FieldPanel('dosage_instructions'),
            FieldPanel('dosage_amount'),
            FieldPanel('dosage_unit'),
            FieldPanel('frequency'),
            FieldPanel('duration'),
        ], heading=_('Dosage Information'), classname='collapsible'),
        
        # Quantity and Refills Panel
        MultiFieldPanel([
            FieldPanel('quantity_prescribed'),
            FieldPanel('refills_allowed'),
            FieldPanel('refills_used'),
        ], heading=_('Quantity & Refills'), classname='collapsible'),
        
        # Medical Information Panel
        MultiFieldPanel([
            FieldPanel('diagnosis'),
            FieldPanel('allergies'),
            FieldPanel('special_instructions'),
            FieldPanel('prescriber_notes'),
        ], heading=_('Medical Information'), classname='collapsible'),
        
        # Workflow Tracking Panel
        MultiFieldPanel([
            FieldPanel('approved_by'),
            FieldPanel('approved_date'),
            FieldPanel('dispensed_by'),
            FieldPanel('dispensed_date'),
        ], heading=_('Workflow Tracking'), classname='collapsible'),
    ]
    
    class Meta:
        verbose_name = _('Enhanced Prescription')
        verbose_name_plural = _('Enhanced Prescriptions')
        db_table = 'medications_enhanced_prescription'
        indexes = [
            models.Index(fields=['prescription_number']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['prescriber', 'status']),
            models.Index(fields=['medication', 'status']),
            models.Index(fields=['prescribed_date']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['status', 'priority']),
        ]
        ordering = ['-prescribed_date']
    
    def __str__(self):
        return f"{self.prescription_number} - {self.patient.get_full_name()} - {self.medication.name}"
    
    @property
    def is_expired(self):
        """Check if prescription is expired."""
        return self.expiry_date < timezone.now().date()
    
    @property
    def is_expiring_soon(self):
        """Check if prescription is expiring within 30 days."""
        from datetime import timedelta
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        return self.expiry_date <= thirty_days_from_now
    
    @property
    def can_refill(self):
        """Check if prescription can be refilled."""
        return (self.status == self.Status.DISPENSED and 
                self.refills_used < self.refills_allowed and 
                not self.is_expired)
    
    @property
    def refills_remaining(self):
        """Get number of refills remaining."""
        return max(0, self.refills_allowed - self.refills_used)
    
    def approve(self, approved_by_user):
        """Approve the prescription."""
        self.status = self.Status.APPROVED
        self.approved_by = approved_by_user
        self.approved_date = timezone.now()
        self.save()
    
    def dispense(self, dispensed_by_user):
        """Dispense the medication."""
        self.status = self.Status.DISPENSED
        self.dispensed_by = dispensed_by_user
        self.dispensed_date = timezone.now()
        self.save()
    
    def refill(self):
        """Refill the prescription."""
        if self.can_refill:
            self.refills_used += 1
            self.status = self.Status.DISPENSED
            self.save()
            return True
        return False
    
    def cancel(self):
        """Cancel the prescription."""
        self.status = self.Status.CANCELLED
        self.save()
    
    def clean(self):
        """Custom validation for the model."""
        # Validate expiry date is after prescribed date
        if self.expiry_date and self.prescribed_date and self.expiry_date <= self.prescribed_date:
            raise ValidationError({
                'expiry_date': _('Expiry date must be after prescribed date')
            })
        
        # Validate refills used doesn't exceed refills allowed
        if self.refills_used > self.refills_allowed:
            raise ValidationError({
                'refills_used': _('Refills used cannot exceed refills allowed')
            })
        
        # Validate quantity is positive
        if self.quantity_prescribed <= 0:
            raise ValidationError({
                'quantity_prescribed': _('Quantity prescribed must be positive')
            })
    
    # Wagtail 7.0.2: Enhanced admin methods
    def get_admin_display_title(self):
        """Return the title to display in admin."""
        return f"{self.prescription_number} - {self.patient.get_full_name()}"
    
    def get_admin_display_subtitle(self):
        """Return the subtitle to display in admin."""
        return f"{self.medication.name} - {self.get_status_display()}"
    
    def get_admin_url(self):
        """Return the admin URL for this prescription."""
        from django.urls import reverse
        return reverse('admin:medications_prescription_change', args=[self.id])
    
    def get_absolute_url(self):
        """Return the public URL for this prescription."""
        return f"/prescriptions/{self.id}/"


class PrescriptionWorkflow(models.Model):
    """
    Enhanced prescription workflow model with Wagtail 7.0.2 form integration.
    
    This model tracks the complete workflow of prescription processing from
    creation to completion, with enhanced form validation and admin integration.
    """
    
    # Workflow status choices
    class WorkflowStatus(models.TextChoices):
        CREATED = 'created', _('Created')
        UNDER_REVIEW = 'under_review', _('Under Review')
        PHARMACY_REVIEW = 'pharmacy_review', _('Pharmacy Review')
        APPROVED = 'approved', _('Approved')
        DISPENSED = 'dispensed', _('Dispensed')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        REQUIRES_CLARIFICATION = 'requires_clarification', _('Requires Clarification')
    
    # Workflow step choices
    class WorkflowStep(models.TextChoices):
        INITIAL_REVIEW = 'initial_review', _('Initial Review')
        PHARMACY_VERIFICATION = 'pharmacy_verification', _('Pharmacy Verification')
        INSURANCE_VERIFICATION = 'insurance_verification', _('Insurance Verification')
        CLINICAL_REVIEW = 'clinical_review', _('Clinical Review')
        DISPENSING = 'dispensing', _('Dispensing')
        PATIENT_EDUCATION = 'patient_education', _('Patient Education')
        FOLLOW_UP = 'follow_up', _('Follow-up')
    
    # Relationships
    prescription = models.OneToOneField(
        EnhancedPrescription,
        on_delete=models.CASCADE,
        related_name='workflow',
        help_text=_('Associated prescription')
    )
    
    # Workflow tracking
    current_status = models.CharField(
        max_length=30,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.CREATED,
        help_text=_('Current workflow status')
    )
    
    current_step = models.CharField(
        max_length=30,
        choices=WorkflowStep.choices,
        default=WorkflowStep.INITIAL_REVIEW,
        help_text=_('Current workflow step')
    )
    
    # Workflow history with StreamField for rich content
    workflow_history = StreamField([
        ('status_change', StructBlock([
            ('status', ChoiceBlock(choices=WorkflowStatus.choices)),
            ('step', ChoiceBlock(choices=WorkflowStep.choices)),
            ('notes', RichTextBlock(features=['bold', 'italic', 'link', 'ul', 'ol'])),
            ('timestamp', DateTimeBlock()),
            ('user', SnippetChooserBlock('users.User')),
        ])),
        ('review_notes', RichTextBlock(features=['bold', 'italic', 'link', 'ul', 'ol'])),
        ('verification_result', StructBlock([
            ('verified', BooleanBlock()),
            ('notes', RichTextBlock(features=['bold', 'italic', 'link', 'ul', 'ol'])),
            ('verifier', SnippetChooserBlock('users.User')),
            ('timestamp', DateTimeBlock()),
        ])),
        ('clinical_decision', StructBlock([
            ('decision', ChoiceBlock(choices=[
                ('approve', _('Approve')),
                ('reject', _('Reject')),
                ('modify', _('Modify')),
                ('hold', _('Hold')),
            ])),
            ('reasoning', RichTextBlock(features=['bold', 'italic', 'link', 'ul', 'ol'])),
            ('clinician', SnippetChooserBlock('users.User')),
            ('timestamp', DateTimeBlock()),
        ])),
    ], blank=True, use_json_field=True, help_text=_('Complete workflow history'))
    
    # Enhanced form fields for workflow management
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
            ('stat', _('STAT')),
        ],
        default='routine',
        help_text=_('Priority level for processing')
    )
    
    estimated_completion_time = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Estimated time to complete workflow')
    )
    
    actual_completion_time = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete workflow')
    )
    
    # Quality assurance fields
    quality_check_passed = models.BooleanField(
        default=False,
        help_text=_('Whether quality assurance checks passed')
    )
    
    quality_check_notes = RichTextField(
        blank=True,
        help_text=_('Quality assurance notes'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    quality_checker = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quality_checked_workflows',
        help_text=_('User who performed quality check')
    )
    
    quality_check_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When quality check was performed')
    )
    
    # Compliance and audit fields
    compliance_verified = models.BooleanField(
        default=False,
        help_text=_('Whether compliance requirements are met')
    )
    
    compliance_notes = RichTextField(
        blank=True,
        help_text=_('Compliance verification notes'),
        features=['bold', 'italic', 'link', 'ul', 'ol']
    )
    
    audit_trail = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Audit trail for compliance tracking')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('prescription__prescription_number', boost=3.0),
        index.SearchField('workflow_history', boost=2.0),
        index.SearchField('quality_check_notes', boost=1.5),
        index.SearchField('compliance_notes', boost=1.5),
        index.RelatedFields('prescription__patient', [
            index.SearchField('first_name', boost=1.5),
            index.SearchField('last_name', boost=1.5),
        ]),
        index.RelatedFields('prescription__medication', [
            index.SearchField('name', boost=2.0),
        ]),
        index.AutocompleteField('prescription__prescription_number'),
        index.FilterField('current_status'),
        index.FilterField('current_step'),
        index.FilterField('priority_level'),
        index.FilterField('quality_check_passed'),
        index.FilterField('compliance_verified'),
        index.FilterField('created_at'),
        index.FilterField('completed_at'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels with form integration
    panels = [
        MultiFieldPanel([
            FieldPanel('prescription'),
            FieldPanel('current_status'),
            FieldPanel('current_step'),
            FieldPanel('priority_level'),
        ], heading=_('Workflow Status'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('workflow_history'),
        ], heading=_('Workflow History'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('estimated_completion_time'),
            FieldPanel('actual_completion_time'),
            FieldPanel('started_at'),
            FieldPanel('completed_at'),
        ], heading=_('Timing Information'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('quality_check_passed'),
            FieldPanel('quality_check_notes'),
            FieldPanel('quality_checker'),
            FieldPanel('quality_check_date'),
        ], heading=_('Quality Assurance'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('compliance_verified'),
            FieldPanel('compliance_notes'),
            FieldPanel('audit_trail'),
        ], heading=_('Compliance & Audit'), classname='collapsible'),
        
        MultiFieldPanel([
            FieldPanel('created_at'),
            FieldPanel('updated_at'),
        ], heading=_('Timestamps'), classname='collapsible'),
    ]
    
    class Meta:
        verbose_name = _('Prescription Workflow')
        verbose_name_plural = _('Prescription Workflows')
        db_table = 'prescription_workflows'
        indexes = [
            models.Index(fields=['current_status', 'priority_level']),
            models.Index(fields=['current_step', 'created_at']),
            models.Index(fields=['quality_check_passed', 'compliance_verified']),
            models.Index(fields=['created_at']),
            models.Index(fields=['completed_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Workflow for {self.prescription.prescription_number}"
    
    def save(self, *args, **kwargs):
        """Override save to track workflow timing."""
        if not self.pk:  # New workflow
            self.started_at = timezone.now()
        elif self.current_status == self.WorkflowStatus.COMPLETED and not self.completed_at:
            self.completed_at = timezone.now()
            if self.started_at:
                self.actual_completion_time = self.completed_at - self.started_at
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Enhanced validation for workflow model."""
        super().clean()
        
        # Validate workflow status transitions
        if self.pk:
            old_instance = PrescriptionWorkflow.objects.get(pk=self.pk)
            valid_transitions = {
                self.WorkflowStatus.CREATED: [self.WorkflowStatus.UNDER_REVIEW, self.WorkflowStatus.CANCELLED],
                self.WorkflowStatus.UNDER_REVIEW: [self.WorkflowStatus.PHARMACY_REVIEW, self.WorkflowStatus.REQUIRES_CLARIFICATION, self.WorkflowStatus.CANCELLED],
                self.WorkflowStatus.PHARMACY_REVIEW: [self.WorkflowStatus.APPROVED, self.WorkflowStatus.REQUIRES_CLARIFICATION, self.WorkflowStatus.CANCELLED],
                self.WorkflowStatus.APPROVED: [self.WorkflowStatus.DISPENSED, self.WorkflowStatus.ON_HOLD, self.WorkflowStatus.CANCELLED],
                self.WorkflowStatus.DISPENSED: [self.WorkflowStatus.COMPLETED, self.WorkflowStatus.ON_HOLD],
                self.WorkflowStatus.ON_HOLD: [self.WorkflowStatus.UNDER_REVIEW, self.WorkflowStatus.CANCELLED],
                self.WorkflowStatus.REQUIRES_CLARIFICATION: [self.WorkflowStatus.UNDER_REVIEW, self.WorkflowStatus.CANCELLED],
            }
            
            if (old_instance.current_status in valid_transitions and 
                self.current_status not in valid_transitions[old_instance.current_status]):
                raise ValidationError({
                    'current_status': _('Invalid status transition')
                })
        
        # Validate completion time
        if self.actual_completion_time and self.estimated_completion_time:
            if self.actual_completion_time > self.estimated_completion_time * 2:
                raise ValidationError({
                    'actual_completion_time': _('Actual completion time is significantly longer than estimated')
                })
    
    # Wagtail 7.0.2: Enhanced admin methods
    def get_admin_display_title(self):
        """Return the title to display in admin."""
        return f"Workflow: {self.prescription.prescription_number}"
    
    def get_admin_display_subtitle(self):
        """Return the subtitle to display in admin."""
        return f"{self.get_current_status_display()} • {self.get_current_step_display()}"
    
    def get_admin_url(self):
        """Return the admin URL for this workflow."""
        from django.urls import reverse
        return reverse('admin:medications_prescriptionworkflow_change', args=[self.id])
    
    def get_absolute_url(self):
        """Return the public URL for this workflow."""
        return f"/workflows/{self.id}/"
    
    def get_search_display_title(self):
        """Return the title to display in search results."""
        return self.get_admin_display_title()
    
    def get_search_description(self):
        """Return the description to display in search results."""
        return f"{self.get_current_status_display()} • {self.prescription.patient.get_full_name()}"
    
    def get_search_url(self, request=None):
        """Return the URL to display in search results."""
        return self.get_admin_url()
    
    def get_search_meta(self):
        """Return additional metadata for search results."""
        return {
            'status': self.current_status,
            'step': self.current_step,
            'priority': self.priority_level,
            'patient': self.prescription.patient.get_full_name(),
            'medication': self.prescription.medication.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    # Workflow management methods
    def advance_workflow(self, new_status, new_step, notes=None, user=None):
        """Advance the workflow to a new status and step."""
        self.current_status = new_status
        self.current_step = new_step
        
        # Add to workflow history
        if not self.workflow_history:
            self.workflow_history = []
        
        history_entry = {
            'type': 'status_change',
            'value': {
                'status': new_status,
                'step': new_step,
                'notes': notes or '',
                'timestamp': timezone.now(),
                'user': user.id if user else None,
            }
        }
        
        self.workflow_history.append(history_entry)
        self.save()
    
    def add_review_notes(self, notes, user=None):
        """Add review notes to the workflow history."""
        if not self.workflow_history:
            self.workflow_history = []
        
        history_entry = {
            'type': 'review_notes',
            'value': notes
        }
        
        self.workflow_history.append(history_entry)
        self.save()
    
    def perform_quality_check(self, passed, notes, user):
        """Perform quality assurance check."""
        self.quality_check_passed = passed
        self.quality_check_notes = notes
        self.quality_checker = user
        self.quality_check_date = timezone.now()
        self.save()
    
    def verify_compliance(self, verified, notes):
        """Verify compliance requirements."""
        self.compliance_verified = verified
        self.compliance_notes = notes
        self.save()
    
    @property
    def is_completed(self):
        """Check if workflow is completed."""
        return self.current_status == self.WorkflowStatus.COMPLETED
    
    @property
    def is_on_hold(self):
        """Check if workflow is on hold."""
        return self.current_status == self.WorkflowStatus.ON_HOLD
    
    @property
    def requires_attention(self):
        """Check if workflow requires attention."""
        return self.current_status in [
            self.WorkflowStatus.REQUIRES_CLARIFICATION,
            self.WorkflowStatus.ON_HOLD
        ]
    
    @property
    def workflow_duration(self):
        """Get the duration of the workflow."""
        if self.completed_at and self.started_at:
            return self.completed_at - self.started_at
        return None
