"""
Wagtail 7.0.2 StreamField blocks for MedGuard SA medications app.

This module provides enhanced blocks for medication management with improved
validation, admin interfaces, and user experience features.
"""

from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from decimal import Decimal
import re

# Wagtail 7.0.2 imports
from wagtail.blocks import (
    CharBlock, TextBlock, IntegerBlock, DecimalBlock, BooleanBlock,
    DateBlock, TimeBlock, ChoiceBlock, URLBlock, EmailBlock,
    StructBlock, ListBlock, StreamBlock, PageChooserBlock,
    RawHTMLBlock, StaticBlock, RichTextBlock
)
from wagtail.images.blocks import ImageChooserBlock
from wagtail.blocks.field_block import FieldBlock
from wagtail.blocks.struct_block import StructBlockValidationError
from wagtail.blocks.list_block import ListBlockValidationError


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


# 1. MedicationInfoStructBlock - structured medication data with new validation
class MedicationInfoStructBlock(MedicationValidationMixin, StructBlock):
    """Enhanced structured block for medication information with Wagtail 7.0.2 validation."""
    
    name = CharBlock(
        max_length=200,
        help_text=_('Name of the medication'),
        label=_('Medication Name'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Medication name contains invalid characters'
        )]
    )
    
    generic_name = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Generic name of the medication'),
        label=_('Generic Name'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Generic name contains invalid characters'
        )]
    )
    
    brand_name = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Brand name of the medication'),
        label=_('Brand Name'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Brand name contains invalid characters'
        )]
    )
    
    medication_type = ChoiceBlock(
        choices=[
            ('tablet', _('Tablet')),
            ('capsule', _('Capsule')),
            ('liquid', _('Liquid')),
            ('injection', _('Injection')),
            ('inhaler', _('Inhaler')),
            ('cream', _('Cream')),
            ('ointment', _('Ointment')),
            ('drops', _('Drops')),
            ('patch', _('Patch')),
            ('other', _('Other')),
        ],
        default='tablet',
        help_text=_('Type of medication'),
        label=_('Medication Type')
    )
    
    prescription_type = ChoiceBlock(
        choices=[
            ('prescription', _('Prescription Required')),
            ('otc', _('Over the Counter')),
            ('supplement', _('Supplement')),
            ('schedule_1', _('Schedule 1 - Highly Addictive')),
            ('schedule_2', _('Schedule 2 - Addictive')),
            ('schedule_3', _('Schedule 3 - Moderate Risk')),
            ('schedule_4', _('Schedule 4 - Low Risk')),
            ('schedule_5', _('Schedule 5 - Minimal Risk')),
            ('schedule_6', _('Schedule 6 - Poisonous')),
            ('schedule_7', _('Schedule 7 - Dangerous')),
            ('compounded', _('Compounded Medication')),
            ('generic', _('Generic Medication')),
            ('branded', _('Branded Medication')),
        ],
        default='prescription',
        help_text=_('Type of prescription required'),
        label=_('Prescription Type')
    )
    
    active_ingredients = TextBlock(
        required=False,
        help_text=_('Active ingredients in the medication'),
        label=_('Active Ingredients'),
        max_length=1000
    )
    
    strength = CharBlock(
        max_length=100,
        required=False,
        help_text=_('Strength/concentration of the medication'),
        label=_('Strength'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)\/]+$',
            message='Strength contains invalid characters'
        )]
    )
    
    manufacturer = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Manufacturer of the medication'),
        label=_('Manufacturer'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Manufacturer name contains invalid characters'
        )]
    )
    
    description = RichTextBlock(
        required=False,
        help_text=_('Detailed description of the medication'),
        label=_('Description'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=2000
    )
    
    is_active = BooleanBlock(
        default=True,
        help_text=_('Whether this medication is currently active'),
        label=_('Active')
    )
    
    requires_refrigeration = BooleanBlock(
        default=False,
        help_text=_('Whether this medication requires refrigeration'),
        label=_('Requires Refrigeration')
    )
    
    controlled_substance = BooleanBlock(
        default=False,
        help_text=_('Whether this is a controlled substance'),
        label=_('Controlled Substance')
    )
    
    class Meta:
        template = 'medications/blocks/medication_info_struct_block.html'
        icon = 'medication'
        label = _('Medication Information')
        help_text = _('Structured medication information with enhanced validation')


# 2. PrescriptionUploadBlock - OCR prescription processing with file handling
class PrescriptionUploadBlock(MedicationValidationMixin, StructBlock):
    """Enhanced prescription upload block with OCR processing and file handling."""
    
    prescription_image = ImageChooserBlock(
        help_text=_('Upload prescription image for OCR processing'),
        label=_('Prescription Image'),
        required=True
    )
    
    prescription_type = ChoiceBlock(
        choices=[
            ('handwritten', _('Handwritten Prescription')),
            ('printed', _('Printed Prescription')),
            ('digital', _('Digital Prescription')),
            ('fax', _('Fax Prescription')),
            ('photo', _('Photo of Prescription')),
        ],
        default='printed',
        help_text=_('Type of prescription being uploaded'),
        label=_('Prescription Type')
    )
    
    ocr_processing_enabled = BooleanBlock(
        default=True,
        help_text=_('Enable OCR processing for automatic data extraction'),
        label=_('Enable OCR Processing')
    )
    
    manual_override = BooleanBlock(
        default=False,
        help_text=_('Allow manual override of OCR results'),
        label=_('Manual Override')
    )
    
    confidence_threshold = ChoiceBlock(
        choices=[
            ('low', _('Low (60%) - More results, less accurate')),
            ('medium', _('Medium (80%) - Balanced accuracy')),
            ('high', _('High (95%) - Fewer results, more accurate')),
        ],
        default='medium',
        help_text=_('OCR confidence threshold for data extraction'),
        label=_('OCR Confidence Threshold')
    )
    
    extracted_data = RichTextBlock(
        required=False,
        help_text=_('OCR extracted data (read-only)'),
        label=_('Extracted Data'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=5000
    )
    
    processing_notes = TextBlock(
        required=False,
        help_text=_('Notes about OCR processing or manual corrections'),
        label=_('Processing Notes'),
        max_length=1000
    )
    
    is_verified = BooleanBlock(
        default=False,
        help_text=_('Whether the extracted data has been verified'),
        label=_('Verified')
    )
    
    verification_date = DateBlock(
        required=False,
        help_text=_('Date when the prescription was verified'),
        label=_('Verification Date')
    )
    
    verified_by = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Name of person who verified the prescription'),
        label=_('Verified By'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z\s\-\.]+$',
            message='Verifier name contains invalid characters'
        )]
    )
    
    class Meta:
        template = 'medications/blocks/prescription_upload_block.html'
        icon = 'upload'
        label = _('Prescription Upload')
        help_text = _('Upload and process prescriptions with OCR technology')


# 3. DosageScheduleListBlock - medication scheduling with Wagtail 7.0.2 forms
class DosageScheduleListBlock(MedicationValidationMixin, ListBlock):
    """Enhanced list block for medication dosage schedules with Wagtail 7.0.2 forms."""
    
    def __init__(self, **kwargs):
        # Define the child block structure
        child_block = StructBlock([
            ('medication_name', CharBlock(
                max_length=200,
                help_text=_('Name of the medication'),
                label=_('Medication Name'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                    message='Medication name contains invalid characters'
                )]
            )),
            ('dosage_amount', DecimalBlock(
                min_value=0.01,
                max_digits=8,
                decimal_places=2,
                help_text=_('Dosage amount'),
                label=_('Dosage Amount'),
                validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('999999.99'))]
            )),
            ('dosage_unit', ChoiceBlock(
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
                label=_('Dosage Unit')
            )),
            ('frequency', ChoiceBlock(
                choices=[
                    ('once_daily', _('Once daily')),
                    ('twice_daily', _('Twice daily')),
                    ('three_times_daily', _('Three times daily')),
                    ('four_times_daily', _('Four times daily')),
                    ('as_needed', _('As needed')),
                    ('weekly', _('Weekly')),
                    ('monthly', _('Monthly')),
                    ('custom', _('Custom schedule')),
                ],
                default='once_daily',
                help_text=_('How often to take'),
                label=_('Frequency')
            )),
            ('timing', ChoiceBlock(
                choices=[
                    ('morning', _('Morning')),
                    ('noon', _('Noon')),
                    ('evening', _('Evening')),
                    ('night', _('Night')),
                    ('custom', _('Custom Time')),
                    ('before_meals', _('Before meals')),
                    ('after_meals', _('After meals')),
                    ('with_food', _('With food')),
                    ('empty_stomach', _('Empty stomach')),
                ],
                default='morning',
                help_text=_('When to take the medication'),
                label=_('Timing')
            )),
            ('custom_time', TimeBlock(
                required=False,
                help_text=_('Custom time (if timing is custom)'),
                label=_('Custom Time')
            )),
            ('days_of_week', ListBlock(
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
            )),
            ('start_date', DateBlock(
                help_text=_('Start date for this dosage schedule'),
                label=_('Start Date')
            )),
            ('end_date', DateBlock(
                required=False,
                help_text=_('End date for this dosage schedule (optional)'),
                label=_('End Date')
            )),
            ('instructions', RichTextBlock(
                required=False,
                help_text=_('Special instructions for taking this medication'),
                label=_('Instructions'),
                features=['bold', 'italic', 'ul', 'ol'],
                max_length=1000
            )),
            ('is_active', BooleanBlock(
                default=True,
                help_text=_('Whether this dosage schedule is currently active'),
                label=_('Active')
            )),
        ])
        
        super().__init__(child_block, **kwargs)
    
    class Meta:
        template = 'medications/blocks/dosage_schedule_list_block.html'
        icon = 'time'
        label = _('Dosage Schedules')
        help_text = _('List of medication dosage schedules with enhanced forms')


# 4. InteractionWarningBlock - drug interaction alerts with conditional display
class InteractionWarningBlock(MedicationValidationMixin, StructBlock):
    """Enhanced drug interaction warning block with conditional display logic."""
    
    warning_title = CharBlock(
        max_length=200,
        help_text=_('Title of the interaction warning'),
        label=_('Warning Title'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Warning title contains invalid characters'
        )]
    )
    
    interaction_severity = ChoiceBlock(
        choices=[
            ('major', _('Major - Avoid combination')),
            ('moderate', _('Moderate - Monitor closely')),
            ('minor', _('Minor - No action needed')),
            ('contraindicated', _('Contraindicated - Never combine')),
        ],
        default='moderate',
        help_text=_('Severity level of the interaction'),
        label=_('Interaction Severity')
    )
    
    primary_medication = CharBlock(
        max_length=200,
        help_text=_('Primary medication involved in interaction'),
        label=_('Primary Medication'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Medication name contains invalid characters'
        )]
    )
    
    interacting_substances = ListBlock(
        CharBlock(
            max_length=200,
            validators=[RegexValidator(
                regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                message='Substance name contains invalid characters'
            )]
        ),
        min_num=1,
        max_num=10,
        help_text=_('List of substances that interact with the primary medication'),
        label=_('Interacting Substances')
    )
    
    interaction_description = RichTextBlock(
        help_text=_('Detailed description of the interaction'),
        label=_('Interaction Description'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=2000
    )
    
    clinical_effects = RichTextBlock(
        required=False,
        help_text=_('Clinical effects of the interaction'),
        label=_('Clinical Effects'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1500
    )
    
    recommendations = RichTextBlock(
        help_text=_('Recommendations for managing the interaction'),
        label=_('Recommendations'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=2000
    )
    
    monitoring_required = BooleanBlock(
        default=False,
        help_text=_('Whether monitoring is required for this interaction'),
        label=_('Monitoring Required')
    )
    
    monitoring_frequency = ChoiceBlock(
        choices=[
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
            ('monthly', _('Monthly')),
            ('as_needed', _('As needed')),
            ('continuous', _('Continuous')),
        ],
        required=False,
        help_text=_('Frequency of monitoring required'),
        label=_('Monitoring Frequency')
    )
    
    alternative_medications = ListBlock(
        CharBlock(
            max_length=200,
            validators=[RegexValidator(
                regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                message='Medication name contains invalid characters'
            )]
        ),
        min_num=0,
        max_num=10,
        help_text=_('Alternative medications that can be used instead'),
        label=_('Alternative Medications')
    )
    
    evidence_level = ChoiceBlock(
        choices=[
            ('high', _('High - Strong clinical evidence')),
            ('moderate', _('Moderate - Some clinical evidence')),
            ('low', _('Low - Limited clinical evidence')),
            ('theoretical', _('Theoretical - Based on mechanism of action')),
        ],
        default='moderate',
        help_text=_('Level of evidence supporting this interaction'),
        label=_('Evidence Level')
    )
    
    show_warning = BooleanBlock(
        default=True,
        help_text=_('Whether to display this warning to users'),
        label=_('Show Warning')
    )
    
    warning_conditions = RichTextBlock(
        required=False,
        help_text=_('Conditions under which this warning should be displayed'),
        label=_('Warning Conditions'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1000
    )
    
    class Meta:
        template = 'medications/blocks/interaction_warning_block.html'
        icon = 'warning'
        label = _('Drug Interaction Warning')
        help_text = _('Drug interaction warnings with conditional display logic')


# 5. StockLevelBlock - inventory tracking with real-time updates
class StockLevelBlock(MedicationValidationMixin, StructBlock):
    """Enhanced stock level block with real-time inventory tracking."""
    
    medication_name = CharBlock(
        max_length=200,
        help_text=_('Name of the medication for stock tracking'),
        label=_('Medication Name'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Medication name contains invalid characters'
        )]
    )
    
    current_stock = IntegerBlock(
        min_value=0,
        help_text=_('Current stock level'),
        label=_('Current Stock'),
        validators=[MinValueValidator(0)]
    )
    
    minimum_stock = IntegerBlock(
        min_value=0,
        help_text=_('Minimum stock level before reorder alert'),
        label=_('Minimum Stock'),
        validators=[MinValueValidator(0)]
    )
    
    maximum_stock = IntegerBlock(
        min_value=1,
        help_text=_('Maximum stock level for storage capacity'),
        label=_('Maximum Stock'),
        validators=[MinValueValidator(1)]
    )
    
    reorder_point = IntegerBlock(
        min_value=0,
        help_text=_('Stock level at which to reorder'),
        label=_('Reorder Point'),
        validators=[MinValueValidator(0)]
    )
    
    reorder_quantity = IntegerBlock(
        min_value=1,
        help_text=_('Quantity to order when reorder point is reached'),
        label=_('Reorder Quantity'),
        validators=[MinValueValidator(1)]
    )
    
    unit_of_measure = ChoiceBlock(
        choices=[
            ('tablets', _('Tablets')),
            ('capsules', _('Capsules')),
            ('bottles', _('Bottles')),
            ('vials', _('Vials')),
            ('tubes', _('Tubes')),
            ('packs', _('Packs')),
            ('units', _('Units')),
            ('grams', _('Grams')),
            ('milliliters', _('Milliliters')),
        ],
        default='tablets',
        help_text=_('Unit of measurement for stock'),
        label=_('Unit of Measure')
    )
    
    stock_status = ChoiceBlock(
        choices=[
            ('in_stock', _('In Stock')),
            ('low_stock', _('Low Stock')),
            ('out_of_stock', _('Out of Stock')),
            ('on_order', _('On Order')),
            ('discontinued', _('Discontinued')),
        ],
        default='in_stock',
        help_text=_('Current stock status'),
        label=_('Stock Status')
    )
    
    last_updated = DateBlock(
        help_text=_('Date when stock level was last updated'),
        label=_('Last Updated')
    )
    
    expiry_date = DateBlock(
        required=False,
        help_text=_('Expiry date of current stock'),
        label=_('Expiry Date')
    )
    
    batch_number = CharBlock(
        max_length=100,
        required=False,
        help_text=_('Batch number for current stock'),
        label=_('Batch Number'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.]+$',
            message='Batch number contains invalid characters'
        )]
    )
    
    supplier = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Supplier of the medication'),
        label=_('Supplier'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Supplier name contains invalid characters'
        )]
    )
    
    unit_cost = DecimalBlock(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        required=False,
        help_text=_('Unit cost of the medication'),
        label=_('Unit Cost'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    auto_reorder_enabled = BooleanBlock(
        default=False,
        help_text=_('Whether automatic reordering is enabled'),
        label=_('Auto Reorder Enabled')
    )
    
    reorder_lead_time_days = IntegerBlock(
        min_value=1,
        max_value=365,
        default=7,
        help_text=_('Expected lead time for reorders in days'),
        label=_('Reorder Lead Time (Days)'),
        validators=[MinValueValidator(1), MaxValueValidator(365)]
    )
    
    stock_alerts_enabled = BooleanBlock(
        default=True,
        help_text=_('Whether stock alerts are enabled'),
        label=_('Stock Alerts Enabled')
    )
    
    alert_threshold_percentage = IntegerBlock(
        min_value=1,
        max_value=100,
        default=20,
        help_text=_('Percentage of minimum stock to trigger alerts'),
        label=_('Alert Threshold (%)'),
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    
    notes = RichTextBlock(
        required=False,
        help_text=_('Additional notes about stock management'),
        label=_('Notes'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1000
    )
    
    class Meta:
        template = 'medications/blocks/stock_level_block.html'
        icon = 'box'
        label = _('Stock Level')
        help_text = _('Real-time inventory tracking with automated alerts')


# 6. MedicationSearchFilterBlock - advanced search with Wagtail 7.0.2 filtering
class MedicationSearchFilterBlock(MedicationValidationMixin, StructBlock):
    """Enhanced search and filter block with Wagtail 7.0.2 advanced filtering."""
    
    search_title = CharBlock(
        max_length=200,
        help_text=_('Title for the search interface'),
        label=_('Search Title'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Search title contains invalid characters'
        )]
    )
    
    search_placeholder = CharBlock(
        max_length=100,
        default=_('Search medications...'),
        help_text=_('Placeholder text for search input'),
        label=_('Search Placeholder')
    )
    
    enable_advanced_search = BooleanBlock(
        default=True,
        help_text=_('Whether to enable advanced search options'),
        label=_('Enable Advanced Search')
    )
    
    search_fields = ListBlock(
        ChoiceBlock(
            choices=[
                ('name', _('Medication Name')),
                ('generic_name', _('Generic Name')),
                ('brand_name', _('Brand Name')),
                ('active_ingredients', _('Active Ingredients')),
                ('manufacturer', _('Manufacturer')),
                ('description', _('Description')),
                ('strength', _('Strength')),
                ('medication_type', _('Medication Type')),
                ('prescription_type', _('Prescription Type')),
            ]
        ),
        min_num=1,
        max_num=9,
        help_text=_('Fields to include in search'),
        label=_('Search Fields')
    )
    
    filter_options = ListBlock(
        ChoiceBlock(
            choices=[
                ('medication_type', _('Medication Type')),
                ('prescription_type', _('Prescription Type')),
                ('manufacturer', _('Manufacturer')),
                ('strength', _('Strength')),
                ('is_active', _('Active Status')),
                ('requires_refrigeration', _('Refrigeration Required')),
                ('controlled_substance', _('Controlled Substance')),
                ('stock_status', _('Stock Status')),
                ('price_range', _('Price Range')),
                ('expiry_date', _('Expiry Date')),
            ]
        ),
        min_num=0,
        max_num=10,
        help_text=_('Filter options to display'),
        label=_('Filter Options')
    )
    
    sort_options = ListBlock(
        ChoiceBlock(
            choices=[
                ('name_asc', _('Name (A-Z)')),
                ('name_desc', _('Name (Z-A)')),
                ('price_asc', _('Price (Low to High)')),
                ('price_desc', _('Price (High to Low)')),
                ('stock_asc', _('Stock (Low to High)')),
                ('stock_desc', _('Stock (High to Low)')),
                ('expiry_asc', _('Expiry (Earliest First)')),
                ('expiry_desc', _('Expiry (Latest First)')),
                ('recently_added', _('Recently Added')),
                ('most_popular', _('Most Popular')),
            ]
        ),
        min_num=1,
        max_num=10,
        help_text=_('Sort options to display'),
        label=_('Sort Options')
    )
    
    default_sort = ChoiceBlock(
        choices=[
            ('name_asc', _('Name (A-Z)')),
            ('name_desc', _('Name (Z-A)')),
            ('price_asc', _('Price (Low to High)')),
            ('price_desc', _('Price (High to Low)')),
            ('stock_asc', _('Stock (Low to High)')),
            ('stock_desc', _('Stock (High to Low)')),
            ('expiry_asc', _('Expiry (Earliest First)')),
            ('expiry_desc', _('Expiry (Latest First)')),
            ('recently_added', _('Recently Added')),
            ('most_popular', _('Most Popular')),
        ],
        default='name_asc',
        help_text=_('Default sort order'),
        label=_('Default Sort')
    )
    
    results_per_page = ChoiceBlock(
        choices=[
            ('10', _('10 results per page')),
            ('20', _('20 results per page')),
            ('50', _('50 results per page')),
            ('100', _('100 results per page')),
        ],
        default='20',
        help_text=_('Number of results to display per page'),
        label=_('Results Per Page')
    )
    
    enable_autocomplete = BooleanBlock(
        default=True,
        help_text=_('Whether to enable search autocomplete'),
        label=_('Enable Autocomplete')
    )
    
    autocomplete_min_length = IntegerBlock(
        min_value=1,
        max_value=10,
        default=3,
        help_text=_('Minimum characters for autocomplete'),
        label=_('Autocomplete Min Length'),
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    
    enable_fuzzy_search = BooleanBlock(
        default=True,
        help_text=_('Whether to enable fuzzy search (typo tolerance)'),
        label=_('Enable Fuzzy Search')
    )
    
    fuzzy_search_threshold = ChoiceBlock(
        choices=[
            ('0.7', _('Low (70% similarity)')),
            ('0.8', _('Medium (80% similarity)')),
            ('0.9', _('High (90% similarity)')),
        ],
        default='0.8',
        help_text=_('Fuzzy search similarity threshold'),
        label=_('Fuzzy Search Threshold')
    )
    
    enable_search_history = BooleanBlock(
        default=True,
        help_text=_('Whether to save and display search history'),
        label=_('Enable Search History')
    )
    
    max_search_history = IntegerBlock(
        min_value=5,
        max_value=50,
        default=10,
        help_text=_('Maximum number of search history items'),
        label=_('Max Search History'),
        validators=[MinValueValidator(5), MaxValueValidator(50)]
    )
    
    search_instructions = RichTextBlock(
        required=False,
        help_text=_('Instructions for using the search interface'),
        label=_('Search Instructions'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1000
    )
    
    class Meta:
        template = 'medications/blocks/medication_search_filter_block.html'
        icon = 'search'
        label = _('Medication Search & Filter')
        help_text = _('Advanced search and filtering interface for medications')


# 7. PrescriptionTimelineBlock - prescription history visualization
class PrescriptionTimelineBlock(MedicationValidationMixin, StructBlock):
    """Enhanced prescription timeline block for history visualization."""
    
    timeline_title = CharBlock(
        max_length=200,
        help_text=_('Title for the prescription timeline'),
        label=_('Timeline Title'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Timeline title contains invalid characters'
        )]
    )
    
    patient_name = CharBlock(
        max_length=200,
        help_text=_('Name of the patient for the timeline'),
        label=_('Patient Name'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z\s\-\.]+$',
            message='Patient name contains invalid characters'
        )]
    )
    
    timeline_type = ChoiceBlock(
        choices=[
            ('medication_history', _('Medication History')),
            ('prescription_changes', _('Prescription Changes')),
            ('dosage_adjustments', _('Dosage Adjustments')),
            ('refill_history', _('Refill History')),
            ('interaction_events', _('Interaction Events')),
            ('adherence_tracking', _('Adherence Tracking')),
        ],
        default='medication_history',
        help_text=_('Type of timeline to display'),
        label=_('Timeline Type')
    )
    
    date_range = ChoiceBlock(
        choices=[
            ('last_30_days', _('Last 30 Days')),
            ('last_3_months', _('Last 3 Months')),
            ('last_6_months', _('Last 6 Months')),
            ('last_year', _('Last Year')),
            ('all_time', _('All Time')),
            ('custom', _('Custom Range')),
        ],
        default='last_6_months',
        help_text=_('Date range for the timeline'),
        label=_('Date Range')
    )
    
    start_date = DateBlock(
        required=False,
        help_text=_('Start date for custom date range'),
        label=_('Start Date')
    )
    
    end_date = DateBlock(
        required=False,
        help_text=_('End date for custom date range'),
        label=_('End Date')
    )
    
    timeline_events = ListBlock(
        StructBlock([
            ('event_date', DateBlock(
                help_text=_('Date of the timeline event'),
                label=_('Event Date')
            )),
            ('event_type', ChoiceBlock(
                choices=[
                    ('prescription_started', _('Prescription Started')),
                    ('prescription_stopped', _('Prescription Stopped')),
                    ('dosage_changed', _('Dosage Changed')),
                    ('medication_added', _('Medication Added')),
                    ('medication_removed', _('Medication Removed')),
                    ('refill_requested', _('Refill Requested')),
                    ('refill_completed', _('Refill Completed')),
                    ('interaction_detected', _('Interaction Detected')),
                    ('side_effect_reported', _('Side Effect Reported')),
                    ('adherence_missed', _('Adherence Missed')),
                    ('adherence_completed', _('Adherence Completed')),
                ],
                help_text=_('Type of timeline event'),
                label=_('Event Type')
            )),
            ('medication_name', CharBlock(
                max_length=200,
                help_text=_('Medication involved in the event'),
                label=_('Medication Name'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                    message='Medication name contains invalid characters'
                )]
            )),
            ('event_description', RichTextBlock(
                help_text=_('Description of the timeline event'),
                label=_('Event Description'),
                features=['bold', 'italic', 'ul', 'ol'],
                max_length=1000
            )),
            ('prescriber', CharBlock(
                max_length=200,
                required=False,
                help_text=_('Name of the prescribing doctor'),
                label=_('Prescriber'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z\s\-\.]+$',
                    message='Prescriber name contains invalid characters'
                )]
            )),
            ('dosage_info', CharBlock(
                max_length=200,
                required=False,
                help_text=_('Dosage information for the event'),
                label=_('Dosage Info'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)\/]+$',
                    message='Dosage info contains invalid characters'
                )]
            )),
            ('is_important', BooleanBlock(
                default=False,
                help_text=_('Whether this is an important event to highlight'),
                label=_('Important Event')
            )),
        ]),
        min_num=0,
        max_num=100,
        help_text=_('Timeline events to display'),
        label=_('Timeline Events')
    )
    
    display_options = ListBlock(
        ChoiceBlock(
            choices=[
                ('show_dates', _('Show Dates')),
                ('show_times', _('Show Times')),
                ('show_durations', _('Show Durations')),
                ('show_icons', _('Show Event Icons')),
                ('show_colors', _('Show Color Coding')),
                ('show_filters', _('Show Event Filters')),
                ('show_search', _('Show Search')),
                ('show_export', _('Show Export Options')),
            ]
        ),
        min_num=1,
        max_num=8,
        help_text=_('Display options for the timeline'),
        label=_('Display Options')
    )
    
    timeline_style = ChoiceBlock(
        choices=[
            ('vertical', _('Vertical Timeline')),
            ('horizontal', _('Horizontal Timeline')),
            ('compact', _('Compact Timeline')),
            ('detailed', _('Detailed Timeline')),
            ('interactive', _('Interactive Timeline')),
        ],
        default='vertical',
        help_text=_('Visual style of the timeline'),
        label=_('Timeline Style')
    )
    
    enable_interactions = BooleanBlock(
        default=True,
        help_text=_('Whether to enable timeline interactions'),
        label=_('Enable Interactions')
    )
    
    allow_editing = BooleanBlock(
        default=False,
        help_text=_('Whether to allow editing of timeline events'),
        label=_('Allow Editing')
    )
    
    timeline_notes = RichTextBlock(
        required=False,
        help_text=_('Additional notes about the timeline'),
        label=_('Timeline Notes'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1000
    )
    
    class Meta:
        template = 'medications/blocks/prescription_timeline_block.html'
        icon = 'time'
        label = _('Prescription Timeline')
        help_text = _('Visual timeline of prescription history and events')


# 8. MedicationComparisonTableBlock - side-by-side medication comparison
class MedicationComparisonTableBlock(MedicationValidationMixin, StructBlock):
    """Enhanced table block for side-by-side medication comparison."""
    
    comparison_title = CharBlock(
        max_length=200,
        help_text=_('Title for the medication comparison table'),
        label=_('Comparison Title'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Comparison title contains invalid characters'
        )]
    )
    
    comparison_type = ChoiceBlock(
        choices=[
            ('dosage_comparison', _('Dosage Comparison')),
            ('side_effects_comparison', _('Side Effects Comparison')),
            ('interactions_comparison', _('Drug Interactions Comparison')),
            ('cost_comparison', _('Cost Comparison')),
            ('efficacy_comparison', _('Efficacy Comparison')),
            ('generic_vs_brand', _('Generic vs Brand Comparison')),
            ('strength_comparison', _('Strength Comparison')),
            ('administration_comparison', _('Administration Comparison')),
        ],
        default='dosage_comparison',
        help_text=_('Type of comparison being made'),
        label=_('Comparison Type')
    )
    
    medications_to_compare = ListBlock(
        StructBlock([
            ('medication_name', CharBlock(
                max_length=200,
                help_text=_('Name of the medication'),
                label=_('Medication Name'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                    message='Medication name contains invalid characters'
                )]
            )),
            ('generic_name', CharBlock(
                max_length=200,
                required=False,
                help_text=_('Generic name of the medication'),
                label=_('Generic Name'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                    message='Generic name contains invalid characters'
                )]
            )),
            ('brand_name', CharBlock(
                max_length=200,
                required=False,
                help_text=_('Brand name of the medication'),
                label=_('Brand Name'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                    message='Brand name contains invalid characters'
                )]
            )),
            ('strength', CharBlock(
                max_length=100,
                required=False,
                help_text=_('Strength of the medication'),
                label=_('Strength'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)\/]+$',
                    message='Strength contains invalid characters'
                )]
            )),
            ('manufacturer', CharBlock(
                max_length=200,
                required=False,
                help_text=_('Manufacturer of the medication'),
                label=_('Manufacturer'),
                validators=[RegexValidator(
                    regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                    message='Manufacturer name contains invalid characters'
                )]
            )),
        ]),
        min_num=2,
        max_num=10,
        help_text=_('Medications to compare'),
        label=_('Medications to Compare')
    )
    
    comparison_columns = ListBlock(
        ChoiceBlock(
            choices=[
                ('name', _('Medication Name')),
                ('generic_name', _('Generic Name')),
                ('brand_name', _('Brand Name')),
                ('strength', _('Strength')),
                ('dosage_form', _('Dosage Form')),
                ('manufacturer', _('Manufacturer')),
                ('active_ingredients', _('Active Ingredients')),
                ('side_effects', _('Side Effects')),
                ('interactions', _('Drug Interactions')),
                ('cost', _('Cost')),
                ('efficacy', _('Efficacy')),
                ('safety', _('Safety')),
                ('administration', _('Administration')),
                ('storage', _('Storage Requirements')),
                ('expiry', _('Expiry Information')),
                ('availability', _('Availability')),
            ]
        ),
        min_num=3,
        max_num=16,
        help_text=_('Columns to include in the comparison table'),
        label=_('Comparison Columns')
    )
    
    table_style = ChoiceBlock(
        choices=[
            ('standard', _('Standard Table')),
            ('striped', _('Striped Rows')),
            ('bordered', _('Bordered Table')),
            ('compact', _('Compact Table')),
            ('detailed', _('Detailed Table')),
            ('interactive', _('Interactive Table')),
        ],
        default='standard',
        help_text=_('Visual style of the comparison table'),
        label=_('Table Style')
    )
    
    enable_sorting = BooleanBlock(
        default=True,
        help_text=_('Whether to enable column sorting'),
        label=_('Enable Sorting')
    )
    
    enable_filtering = BooleanBlock(
        default=True,
        help_text=_('Whether to enable row filtering'),
        label=_('Enable Filtering')
    )
    
    enable_search = BooleanBlock(
        default=True,
        help_text=_('Whether to enable table search'),
        label=_('Enable Search')
    )
    
    show_highlights = BooleanBlock(
        default=True,
        help_text=_('Whether to highlight differences between medications'),
        label=_('Show Highlights')
    )
    
    highlight_color = ChoiceBlock(
        choices=[
            ('green', _('Green - Positive differences')),
            ('red', _('Red - Negative differences')),
            ('yellow', _('Yellow - Neutral differences')),
            ('blue', _('Blue - Informational differences')),
        ],
        default='green',
        help_text=_('Color for highlighting differences'),
        label=_('Highlight Color')
    )
    
    comparison_notes = RichTextBlock(
        required=False,
        help_text=_('Additional notes about the comparison'),
        label=_('Comparison Notes'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=2000
    )
    
    disclaimer = RichTextBlock(
        required=False,
        help_text=_('Disclaimer text for the comparison'),
        label=_('Disclaimer'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1000
    )
    
    class Meta:
        template = 'medications/blocks/medication_comparison_table_block.html'
        icon = 'table'
        label = _('Medication Comparison Table')
        help_text = _('Side-by-side comparison table for medications')


# 9. PharmacyContactBlock - pharmacy information with contact integration
class PharmacyContactBlock(MedicationValidationMixin, StructBlock):
    """Enhanced pharmacy contact block with integration features."""
    
    pharmacy_name = CharBlock(
        max_length=200,
        help_text=_('Name of the pharmacy'),
        label=_('Pharmacy Name'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
            message='Pharmacy name contains invalid characters'
        )]
    )
    
    pharmacy_type = ChoiceBlock(
        choices=[
            ('retail', _('Retail Pharmacy')),
            ('hospital', _('Hospital Pharmacy')),
            ('clinic', _('Clinic Pharmacy')),
            ('compounding', _('Compounding Pharmacy')),
            ('specialty', _('Specialty Pharmacy')),
            ('online', _('Online Pharmacy')),
            ('mail_order', _('Mail Order Pharmacy')),
            ('veterinary', _('Veterinary Pharmacy')),
        ],
        default='retail',
        help_text=_('Type of pharmacy'),
        label=_('Pharmacy Type')
    )
    
    contact_person = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Primary contact person at the pharmacy'),
        label=_('Contact Person'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z\s\-\.]+$',
            message='Contact person name contains invalid characters'
        )]
    )
    
    phone_number = CharBlock(
        max_length=20,
        required=False,
        help_text=_('Primary phone number for the pharmacy'),
        label=_('Phone Number'),
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)]+$',
            message='Phone number contains invalid characters'
        )]
    )
    
    fax_number = CharBlock(
        max_length=20,
        required=False,
        help_text=_('Fax number for the pharmacy'),
        label=_('Fax Number'),
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)]+$',
            message='Fax number contains invalid characters'
        )]
    )
    
    email_address = EmailBlock(
        required=False,
        help_text=_('Email address for the pharmacy'),
        label=_('Email Address')
    )
    
    website_url = URLBlock(
        required=False,
        help_text=_('Website URL for the pharmacy'),
        label=_('Website URL')
    )
    
    physical_address = TextBlock(
        required=False,
        help_text=_('Physical address of the pharmacy'),
        label=_('Physical Address'),
        max_length=500
    )
    
    postal_address = TextBlock(
        required=False,
        help_text=_('Postal address of the pharmacy'),
        label=_('Postal Address'),
        max_length=500
    )
    
    operating_hours = RichTextBlock(
        required=False,
        help_text=_('Operating hours of the pharmacy'),
        label=_('Operating Hours'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1000
    )
    
    services_offered = ListBlock(
        ChoiceBlock(
            choices=[
                ('prescription_filling', _('Prescription Filling')),
                ('medication_reviews', _('Medication Reviews')),
                ('immunizations', _('Immunizations')),
                ('health_screenings', _('Health Screenings')),
                ('compounding', _('Compounding')),
                ('delivery', _('Delivery Service')),
                ('consultation', _('Pharmacy Consultation')),
                ('emergency_supply', _('Emergency Supply')),
                ('refill_reminders', _('Refill Reminders')),
                ('medication_synchronization', _('Medication Synchronization')),
            ]
        ),
        min_num=0,
        max_num=10,
        help_text=_('Services offered by the pharmacy'),
        label=_('Services Offered')
    )
    
    specializations = ListBlock(
        CharBlock(
            max_length=100,
            validators=[RegexValidator(
                regex=r'^[A-Za-z0-9\s\-\.\(\)]+$',
                message='Specialization contains invalid characters'
            )]
        ),
        min_num=0,
        max_num=10,
        help_text=_('Specializations of the pharmacy'),
        label=_('Specializations')
    )
    
    license_number = CharBlock(
        max_length=100,
        required=False,
        help_text=_('Pharmacy license number'),
        label=_('License Number'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z0-9\s\-\.]+$',
            message='License number contains invalid characters'
        )]
    )
    
    pharmacist_in_charge = CharBlock(
        max_length=200,
        required=False,
        help_text=_('Name of the pharmacist in charge'),
        label=_('Pharmacist in Charge'),
        validators=[RegexValidator(
            regex=r'^[A-Za-z\s\-\.]+$',
            message='Pharmacist name contains invalid characters'
        )]
    )
    
    integration_enabled = BooleanBlock(
        default=False,
        help_text=_('Whether pharmacy integration is enabled'),
        label=_('Integration Enabled')
    )
    
    integration_type = ChoiceBlock(
        choices=[
            ('api', _('API Integration')),
            ('edi', _('EDI Integration')),
            ('manual', _('Manual Integration')),
            ('webhook', _('Webhook Integration')),
        ],
        required=False,
        help_text=_('Type of integration with the pharmacy'),
        label=_('Integration Type')
    )
    
    auto_order_enabled = BooleanBlock(
        default=False,
        help_text=_('Whether automatic ordering is enabled'),
        label=_('Auto Order Enabled')
    )
    
    order_lead_time_days = IntegerBlock(
        min_value=1,
        max_value=30,
        default=3,
        required=False,
        help_text=_('Expected lead time for orders in days'),
        label=_('Order Lead Time (Days)'),
        validators=[MinValueValidator(1), MaxValueValidator(30)]
    )
    
    emergency_contact = BooleanBlock(
        default=False,
        help_text=_('Whether this is an emergency contact pharmacy'),
        label=_('Emergency Contact')
    )
    
    after_hours_contact = CharBlock(
        max_length=20,
        required=False,
        help_text=_('After hours contact number'),
        label=_('After Hours Contact'),
        validators=[RegexValidator(
            regex=r'^[\d\s\-\+\(\)]+$',
            message='Contact number contains invalid characters'
        )]
    )
    
    notes = RichTextBlock(
        required=False,
        help_text=_('Additional notes about the pharmacy'),
        label=_('Notes'),
        features=['bold', 'italic', 'ul', 'ol'],
        max_length=1000
    )
    
    class Meta:
        template = 'medications/blocks/pharmacy_contact_block.html'
        icon = 'phone'
        label = _('Pharmacy Contact')
        help_text = _('Pharmacy information with contact integration features')


# 10. All blocks using Wagtail 7.0.2's improved block templates and admin interfaces
class MedicationContentStreamBlock(StreamBlock):
    """Enhanced StreamField for medication content with Wagtail 7.0.2 features."""
    
    # Core medication information blocks
    medication_info = MedicationInfoStructBlock()
    prescription_upload = PrescriptionUploadBlock()
    dosage_schedules = DosageScheduleListBlock()
    
    # Safety and interaction blocks
    interaction_warning = InteractionWarningBlock()
    
    # Inventory and management blocks
    stock_level = StockLevelBlock()
    
    # Search and discovery blocks
    search_filter = MedicationSearchFilterBlock()
    
    # History and comparison blocks
    prescription_timeline = PrescriptionTimelineBlock()
    comparison_table = MedicationComparisonTableBlock()
    
    # Contact and integration blocks
    pharmacy_contact = PharmacyContactBlock()
    
    # Enhanced text blocks with Wagtail 7.0.2 features
    description = RichTextBlock(
        help_text=_('Detailed description of the medication'),
        label=_('Description'),
        features=['bold', 'italic', 'link', 'ul', 'ol', 'h3', 'h4'],
        max_length=5000
    )
    
    instructions = RichTextBlock(
        help_text=_('Instructions for use'),
        label=_('Instructions'),
        features=['bold', 'italic', 'link', 'ul', 'ol', 'h3', 'h4'],
        max_length=4000
    )
    
    warnings = RichTextBlock(
        help_text=_('Important warnings and precautions'),
        label=_('Warnings'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=3000
    )
    
    side_effects = RichTextBlock(
        help_text=_('Side effects information'),
        label=_('Side Effects'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=3000
    )
    
    interactions = RichTextBlock(
        help_text=_('Drug interactions information'),
        label=_('Drug Interactions'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=3000
    )
    
    storage = RichTextBlock(
        help_text=_('Storage instructions'),
        label=_('Storage Instructions'),
        features=['bold', 'italic', 'link', 'ul', 'ol'],
        max_length=2000
    )
    
    # Enhanced media blocks
    image = ImageChooserBlock(
        help_text=_('Medication image'),
        label=_('Medication Image')
    )
    
    # Enhanced HTML blocks for custom content
    custom_html = RawHTMLBlock(
        help_text=_('Custom HTML content'),
        label=_('Custom HTML')
    )
    
    class Meta:
        block_counts = {
            'medication_info': {'min_num': 0, 'max_num': 1},
            'prescription_upload': {'min_num': 0, 'max_num': 5},
            'dosage_schedules': {'min_num': 0, 'max_num': 1},
            'interaction_warning': {'min_num': 0, 'max_num': 10},
            'stock_level': {'min_num': 0, 'max_num': 1},
            'search_filter': {'min_num': 0, 'max_num': 1},
            'prescription_timeline': {'min_num': 0, 'max_num': 1},
            'comparison_table': {'min_num': 0, 'max_num': 5},
            'pharmacy_contact': {'min_num': 0, 'max_num': 10},
            'description': {'min_num': 0, 'max_num': 1},
            'instructions': {'min_num': 0, 'max_num': 1},
            'warnings': {'min_num': 0, 'max_num': 1},
            'side_effects': {'min_num': 0, 'max_num': 1},
            'interactions': {'min_num': 0, 'max_num': 1},
            'storage': {'min_num': 0, 'max_num': 1},
            'image': {'min_num': 0, 'max_num': 10},
            'custom_html': {'min_num': 0, 'max_num': 5},
        }
        template = 'medications/blocks/medication_content_stream_block.html'
        icon = 'medication'
        label = _('Medication Content')
        help_text = _('Comprehensive medication content with Wagtail 7.0.2 enhanced features')


# Export all blocks for easy import
__all__ = [
    'MedicationValidationMixin',
    'MedicationInfoStructBlock',
    'PrescriptionUploadBlock',
    'DosageScheduleListBlock',
    'InteractionWarningBlock',
    'StockLevelBlock',
    'MedicationSearchFilterBlock',
    'PrescriptionTimelineBlock',
    'MedicationComparisonTableBlock',
    'PharmacyContactBlock',
    'MedicationContentStreamBlock',
] 