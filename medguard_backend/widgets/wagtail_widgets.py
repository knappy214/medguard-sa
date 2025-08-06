"""
Wagtail 7.0.2 Widgets for MedGuard SA.

This module contains modern interactive widgets for the MedGuard SA medication management system.
All widgets use Wagtail 7.0.2's enhanced JavaScript integration and accessibility features.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import json

# Wagtail 7.0.2 imports
from wagtail.admin.widgets import AdminWidget
from wagtail.telepath import register
from wagtail.blocks.field_block import FieldBlock


class MedicationDosageCalculatorWidget(AdminWidget):
    """
    Enhanced medication dosage calculator widget using Wagtail 7.0.2's improved JavaScript integration.
    
    Features:
    - Real-time dosage calculations
    - Weight-based dosing
    - Age-based adjustments
    - Renal/hepatic impairment considerations
    - Interactive visual feedback
    - Accessibility compliant
    """
    
    template_name = 'widgets/medication_dosage_calculator.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default calculation options
        default_options = {
            'weight_based': True,
            'age_based': True,
            'renal_adjustment': True,
            'hepatic_adjustment': True,
            'units': ['mg', 'mcg', 'ml', 'g', 'units'],
            'frequencies': [
                ('once_daily', _('Once daily')),
                ('twice_daily', _('Twice daily')),
                ('three_times_daily', _('Three times daily')),
                ('four_times_daily', _('Four times daily')),
                ('as_needed', _('As needed')),
            ],
            'min_weight': 1.0,
            'max_weight': 300.0,
            'min_age': 0,
            'max_age': 120,
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'dosage_calculator_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        # Generate HTML with ARIA labels and keyboard navigation
        html = f'''
        <div class="dosage-calculator-widget" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="dosage-calculator-label">
                {_('Medication Dosage Calculator')}
            </label>
            
            <div class="dosage-inputs" role="group" aria-labelledby="{context['widget_id']}_inputs_label">
                <label id="{context['widget_id']}_inputs_label" class="sr-only">
                    {_('Dosage calculation inputs')}
                </label>
                
                <div class="input-group">
                    <label for="{context['widget_id']}_amount" class="input-label">
                        {_('Dosage Amount')}
                    </label>
                    <input type="number" 
                           id="{context['widget_id']}_amount"
                           name="{name}_amount"
                           class="dosage-amount-input"
                           step="0.01"
                           min="0.01"
                           aria-describedby="{context['widget_id']}_amount_help"
                           required>
                    <div id="{context['widget_id']}_amount_help" class="help-text">
                        {_('Enter the dosage amount')}
                    </div>
                </div>
                
                <div class="input-group">
                    <label for="{context['widget_id']}_unit" class="input-label">
                        {_('Unit')}
                    </label>
                    <select id="{context['widget_id']}_unit"
                            name="{name}_unit"
                            class="dosage-unit-select"
                            aria-describedby="{context['widget_id']}_unit_help">
                        <option value="mg">{_('Milligrams (mg)')}</option>
                        <option value="mcg">{_('Micrograms (mcg)')}</option>
                        <option value="ml">{_('Milliliters (ml)')}</option>
                        <option value="g">{_('Grams (g)')}</option>
                        <option value="units">{_('Units')}</option>
                    </select>
                    <div id="{context['widget_id']}_unit_help" class="help-text">
                        {_('Select the unit of measurement')}
                    </div>
                </div>
                
                <div class="input-group">
                    <label for="{context['widget_id']}_weight" class="input-label">
                        {_('Patient Weight (kg)')}
                    </label>
                    <input type="number" 
                           id="{context['widget_id']}_weight"
                           name="{name}_weight"
                           class="patient-weight-input"
                           step="0.1"
                           min="1"
                           max="300"
                           aria-describedby="{context['widget_id']}_weight_help">
                    <div id="{context['widget_id']}_weight_help" class="help-text">
                        {_('Enter patient weight for weight-based dosing')}
                    </div>
                </div>
                
                <div class="input-group">
                    <label for="{context['widget_id']}_age" class="input-label">
                        {_('Patient Age (years)')}
                    </label>
                    <input type="number" 
                           id="{context['widget_id']}_age"
                           name="{name}_age"
                           class="patient-age-input"
                           min="0"
                           max="120"
                           aria-describedby="{context['widget_id']}_age_help">
                    <div id="{context['widget_id']}_age_help" class="help-text">
                        {_('Enter patient age for age-based adjustments')}
                    </div>
                </div>
            </div>
            
            <div class="dosage-results" role="region" aria-live="polite" aria-labelledby="{context['widget_id']}_results_label">
                <h3 id="{context['widget_id']}_results_label" class="results-label">
                    {_('Calculated Dosage')}
                </h3>
                <div id="{context['widget_id']}_results" class="calculation-results">
                    <div class="result-item">
                        <span class="result-label">{_('Recommended Dosage:')}</span>
                        <span id="{context['widget_id']}_recommended_dosage" class="result-value">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">{_('Daily Total:')}</span>
                        <span id="{context['widget_id']}_daily_total" class="result-value">-</span>
                    </div>
                    <div class="result-item">
                        <span class="result-label">{_('Adjustments:')}</span>
                        <span id="{context['widget_id']}_adjustments" class="result-value">-</span>
                    </div>
                </div>
            </div>
            
            <div class="dosage-warnings" role="alert" aria-live="assertive">
                <div id="{context['widget_id']}_warnings" class="warning-messages"></div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the calculated dosage value from form data."""
        amount = data.get(f'{name}_amount')
        unit = data.get(f'{name}_unit', 'mg')
        
        if amount:
            try:
                amount = Decimal(amount)
                return f"{amount} {unit}"
            except (ValueError, TypeError):
                return None
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not data.get(f'{name}_amount') and not data.get(name)
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/dosage_calculator.css',)
        }
        js = ('js/widgets/dosage_calculator.js',)


# Register the widget with Wagtail's telepath system
register(MedicationDosageCalculatorWidget)


class PrescriptionOCRWidget(AdminWidget):
    """
    Prescription OCR widget for image upload and text extraction with real-time preview.
    
    Features:
    - Image upload with drag & drop
    - Real-time OCR text extraction
    - Prescription data parsing
    - Interactive preview and editing
    - Accessibility compliant
    - Multiple image format support
    """
    
    template_name = 'widgets/prescription_ocr.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default OCR options
        default_options = {
            'supported_formats': ['jpg', 'jpeg', 'png', 'pdf', 'tiff'],
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'ocr_languages': ['en', 'af'],
            'auto_parse': True,
            'confidence_threshold': 0.8,
            'extract_fields': [
                'medication_name',
                'dosage',
                'frequency',
                'duration',
                'prescriber_name',
                'prescription_date',
                'patient_name',
            ],
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'prescription_ocr_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the OCR widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="prescription-ocr-widget" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="ocr-widget-label">
                {_('Prescription OCR Scanner')}
            </label>
            
            <div class="ocr-upload-area" 
                 role="button"
                 tabindex="0"
                 aria-describedby="{context['widget_id']}_upload_help">
                <div class="upload-icon">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="7,10 12,15 17,10"/>
                        <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                </div>
                <div class="upload-text">
                    <p class="upload-title">{_('Upload Prescription Image')}</p>
                    <p class="upload-subtitle">{_('Drag and drop or click to browse')}</p>
                    <p class="upload-formats">{_('Supported formats: JPG, PNG, PDF, TIFF')}</p>
                </div>
                <input type="file" 
                       id="{context['widget_id']}_file_input"
                       name="{name}_file"
                       class="ocr-file-input"
                       accept=".jpg,.jpeg,.png,.pdf,.tiff"
                       aria-hidden="true">
            </div>
            
            <div id="{context['widget_id']}_upload_help" class="help-text">
                {_('Upload a clear image of the prescription for automatic text extraction')}
            </div>
            
            <div class="ocr-preview" style="display: none;" role="region" aria-labelledby="{context['widget_id']}_preview_label">
                <h3 id="{context['widget_id']}_preview_label" class="preview-label">
                    {_('Image Preview')}
                </h3>
                <div class="preview-container">
                    <img id="{context['widget_id']}_preview_image" 
                         class="preview-image" 
                         alt="{_('Prescription image preview')}">
                    <div class="preview-overlay">
                        <button type="button" 
                                class="preview-remove-btn"
                                aria-label="{_('Remove image')}">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="ocr-processing" style="display: none;" role="status" aria-live="polite">
                <div class="processing-spinner"></div>
                <p class="processing-text">{_('Processing image...')}</p>
            </div>
            
            <div class="ocr-results" style="display: none;" role="region" aria-labelledby="{context['widget_id']}_results_label">
                <h3 id="{context['widget_id']}_results_label" class="results-label">
                    {_('Extracted Information')}
                </h3>
                <div class="extracted-fields">
                    <div class="field-group">
                        <label for="{context['widget_id']}_medication_name" class="field-label">
                            {_('Medication Name')}
                        </label>
                        <input type="text" 
                               id="{context['widget_id']}_medication_name"
                               name="{name}_medication_name"
                               class="extracted-field"
                               aria-describedby="{context['widget_id']}_medication_name_help">
                        <div id="{context['widget_id']}_medication_name_help" class="field-help">
                            {_('Automatically extracted medication name')}
                        </div>
                    </div>
                    
                    <div class="field-group">
                        <label for="{context['widget_id']}_dosage" class="field-label">
                            {_('Dosage')}
                        </label>
                        <input type="text" 
                               id="{context['widget_id']}_dosage"
                               name="{name}_dosage"
                               class="extracted-field"
                               aria-describedby="{context['widget_id']}_dosage_help">
                        <div id="{context['widget_id']}_dosage_help" class="field-help">
                            {_('Automatically extracted dosage information')}
                        </div>
                    </div>
                    
                    <div class="field-group">
                        <label for="{context['widget_id']}_frequency" class="field-label">
                            {_('Frequency')}
                        </label>
                        <input type="text" 
                               id="{context['widget_id']}_frequency"
                               name="{name}_frequency"
                               class="extracted-field"
                               aria-describedby="{context['widget_id']}_frequency_help">
                        <div id="{context['widget_id']}_frequency_help" class="field-help">
                            {_('Automatically extracted frequency information')}
                        </div>
                    </div>
                    
                    <div class="field-group">
                        <label for="{context['widget_id']}_prescriber" class="field-label">
                            {_('Prescriber Name')}
                        </label>
                        <input type="text" 
                               id="{context['widget_id']}_prescriber"
                               name="{name}_prescriber"
                               class="extracted-field"
                               aria-describedby="{context['widget_id']}_prescriber_help">
                        <div id="{context['widget_id']}_prescriber_help" class="field-help">
                            {_('Automatically extracted prescriber name')}
                        </div>
                    </div>
                </div>
                
                <div class="ocr-confidence">
                    <span class="confidence-label">{_('Extraction Confidence:')}</span>
                    <span id="{context['widget_id']}_confidence" class="confidence-value">-</span>
                </div>
            </div>
            
            <div class="ocr-raw-text" style="display: none;" role="region" aria-labelledby="{context['widget_id']}_raw_label">
                <h3 id="{context['widget_id']}_raw_label" class="raw-label">
                    {_('Raw Extracted Text')}
                </h3>
                <textarea id="{context['widget_id']}_raw_text"
                          name="{name}_raw_text"
                          class="raw-text-area"
                          rows="6"
                          readonly
                          aria-describedby="{context['widget_id']}_raw_help">
                </textarea>
                <div id="{context['widget_id']}_raw_help" class="help-text">
                    {_('Raw text extracted from the image for verification')}
                </div>
            </div>
            
            <div class="ocr-actions">
                <button type="button" 
                        id="{context['widget_id']}_retry_btn"
                        class="ocr-retry-btn"
                        style="display: none;"
                        aria-describedby="{context['widget_id']}_retry_help">
                    {_('Retry Extraction')}
                </button>
                <div id="{context['widget_id']}_retry_help" class="help-text">
                    {_('Retry OCR extraction if results are inaccurate')}
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the OCR results from form data."""
        medication_name = data.get(f'{name}_medication_name')
        dosage = data.get(f'{name}_dosage')
        frequency = data.get(f'{name}_frequency')
        prescriber = data.get(f'{name}_prescriber')
        raw_text = data.get(f'{name}_raw_text')
        
        if any([medication_name, dosage, frequency, prescriber, raw_text]):
            return {
                'medication_name': medication_name,
                'dosage': dosage,
                'frequency': frequency,
                'prescriber': prescriber,
                'raw_text': raw_text,
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.get(f'{name}_medication_name'),
            data.get(f'{name}_dosage'),
            data.get(f'{name}_frequency'),
            data.get(f'{name}_prescriber'),
            data.get(f'{name}_raw_text'),
            files.get(f'{name}_file'),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/prescription_ocr.css',)
        }
        js = ('js/widgets/prescription_ocr.js',)


# Register the widget with Wagtail's telepath system
register(PrescriptionOCRWidget)


class MedicationInteractionCheckerWidget(AdminWidget):
    """
    Medication interaction checker widget with dynamic drug interaction warnings.
    
    Features:
    - Real-time drug interaction checking
    - Severity-based warnings
    - Alternative medication suggestions
    - Patient-specific risk assessment
    - Interactive risk visualization
    - Accessibility compliant
    """
    
    template_name = 'widgets/medication_interaction_checker.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default interaction checking options
        default_options = {
            'check_severity_levels': ['high', 'moderate', 'low'],
            'include_herbals': True,
            'include_otc': True,
            'include_supplements': True,
            'patient_factors': ['age', 'weight', 'renal_function', 'hepatic_function'],
            'risk_threshold': 'moderate',
            'suggest_alternatives': True,
            'max_interactions': 50,
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'interaction_checker_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the interaction checker widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="medication-interaction-checker" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="interaction-checker-label">
                {_('Medication Interaction Checker')}
            </label>
            
            <div class="medication-selector" role="group" aria-labelledby="{context['widget_id']}_selector_label">
                <label id="{context['widget_id']}_selector_label" class="selector-label">
                    {_('Select Medications to Check')}
                </label>
                
                <div class="medication-search">
                    <label for="{context['widget_id']}_search" class="search-label">
                        {_('Search Medications')}
                    </label>
                    <input type="text" 
                           id="{context['widget_id']}_search"
                           class="medication-search-input"
                           placeholder="{_('Type medication name...')}"
                           aria-describedby="{context['widget_id']}_search_help">
                    <div id="{context['widget_id']}_search_help" class="help-text">
                        {_('Search for medications to add to interaction check')}
                    </div>
                </div>
                
                <div class="selected-medications" role="list" aria-labelledby="{context['widget_id']}_selected_label">
                    <h3 id="{context['widget_id']}_selected_label" class="selected-label">
                        {_('Selected Medications')}
                    </h3>
                    <div id="{context['widget_id']}_medication_list" class="medication-list">
                        <p class="no-medications">{_('No medications selected')}</p>
                    </div>
                </div>
                
                <div class="medication-categories">
                    <fieldset class="category-group">
                        <legend class="category-legend">{_('Include in Check')}</legend>
                        <div class="category-options">
                            <label class="checkbox-label">
                                <input type="checkbox" 
                                       id="{context['widget_id']}_include_herbals"
                                       name="{name}_include_herbals"
                                       class="category-checkbox"
                                       checked>
                                <span class="checkbox-text">{_('Herbal Supplements')}</span>
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" 
                                       id="{context['widget_id']}_include_otc"
                                       name="{name}_include_otc"
                                       class="category-checkbox"
                                       checked>
                                <span class="checkbox-text">{_('Over-the-Counter')}</span>
                            </label>
                            <label class="checkbox-label">
                                <input type="checkbox" 
                                       id="{context['widget_id']}_include_supplements"
                                       name="{name}_include_supplements"
                                       class="category-checkbox"
                                       checked>
                                <span class="checkbox-text">{_('Dietary Supplements')}</span>
                            </label>
                        </div>
                    </fieldset>
                </div>
            </div>
            
            <div class="check-actions">
                <button type="button" 
                        id="{context['widget_id']}_check_btn"
                        class="interaction-check-btn"
                        aria-describedby="{context['widget_id']}_check_help">
                    {_('Check Interactions')}
                </button>
                <div id="{context['widget_id']}_check_help" class="help-text">
                    {_('Analyze selected medications for potential interactions')}
                </div>
            </div>
            
            <div class="interaction-results" style="display: none;" role="region" aria-labelledby="{context['widget_id']}_results_label">
                <h3 id="{context['widget_id']}_results_label" class="results-label">
                    {_('Interaction Results')}
                </h3>
                
                <div class="risk-summary" role="status" aria-live="polite">
                    <div class="risk-level-indicator">
                        <span class="risk-label">{_('Overall Risk Level:')}</span>
                        <span id="{context['widget_id']}_risk_level" class="risk-level">-</span>
                    </div>
                    <div class="interaction-count">
                        <span class="count-label">{_('Interactions Found:')}</span>
                        <span id="{context['widget_id']}_interaction_count" class="count-value">-</span>
                    </div>
                </div>
                
                <div class="interaction-list" role="list" aria-labelledby="{context['widget_id']}_interactions_label">
                    <h4 id="{context['widget_id']}_interactions_label" class="interactions-label">
                        {_('Detected Interactions')}
                    </h4>
                    <div id="{context['widget_id']}_interactions" class="interactions-container">
                        <!-- Interaction items will be dynamically added here -->
                    </div>
                </div>
                
                <div class="severity-filter" role="group" aria-labelledby="{context['widget_id']}_filter_label">
                    <label id="{context['widget_id']}_filter_label" class="filter-label">
                        {_('Filter by Severity')}
                    </label>
                    <div class="severity-buttons">
                        <button type="button" 
                                class="severity-btn active"
                                data-severity="all"
                                aria-pressed="true">
                            {_('All')}
                        </button>
                        <button type="button" 
                                class="severity-btn"
                                data-severity="high"
                                aria-pressed="false">
                            {_('High')}
                        </button>
                        <button type="button" 
                                class="severity-btn"
                                data-severity="moderate"
                                aria-pressed="false">
                            {_('Moderate')}
                        </button>
                        <button type="button" 
                                class="severity-btn"
                                data-severity="low"
                                aria-pressed="false">
                            {_('Low')}
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="alternative-suggestions" style="display: none;" role="region" aria-labelledby="{context['widget_id']}_alternatives_label">
                <h3 id="{context['widget_id']}_alternatives_label" class="alternatives-label">
                    {_('Alternative Medications')}
                </h3>
                <div id="{context['widget_id']}_alternatives" class="alternatives-list">
                    <!-- Alternative suggestions will be dynamically added here -->
                </div>
            </div>
            
            <div class="patient-factors" role="group" aria-labelledby="{context['widget_id']}_factors_label">
                <label id="{context['widget_id']}_factors_label" class="factors-label">
                    {_('Patient Risk Factors')}
                </label>
                <div class="factor-inputs">
                    <div class="factor-group">
                        <label for="{context['widget_id']}_age" class="factor-label">
                            {_('Age (years)')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_age"
                               name="{name}_age"
                               class="factor-input"
                               min="0"
                               max="120"
                               aria-describedby="{context['widget_id']}_age_help">
                        <div id="{context['widget_id']}_age_help" class="factor-help">
                            {_('Patient age for risk assessment')}
                        </div>
                    </div>
                    
                    <div class="factor-group">
                        <label for="{context['widget_id']}_renal_function" class="factor-label">
                            {_('Renal Function')}
                        </label>
                        <select id="{context['widget_id']}_renal_function"
                                name="{name}_renal_function"
                                class="factor-select"
                                aria-describedby="{context['widget_id']}_renal_help">
                            <option value="normal">{_('Normal')}</option>
                            <option value="mild">{_('Mild Impairment')}</option>
                            <option value="moderate">{_('Moderate Impairment')}</option>
                            <option value="severe">{_('Severe Impairment')}</option>
                        </select>
                        <div id="{context['widget_id']}_renal_help" class="factor-help">
                            {_('Patient renal function status')}
                        </div>
                    </div>
                    
                    <div class="factor-group">
                        <label for="{context['widget_id']}_hepatic_function" class="factor-label">
                            {_('Hepatic Function')}
                        </label>
                        <select id="{context['widget_id']}_hepatic_function"
                                name="{name}_hepatic_function"
                                class="factor-select"
                                aria-describedby="{context['widget_id']}_hepatic_help">
                            <option value="normal">{_('Normal')}</option>
                            <option value="mild">{_('Mild Impairment')}</option>
                            <option value="moderate">{_('Moderate Impairment')}</option>
                            <option value="severe">{_('Severe Impairment')}</option>
                        </select>
                        <div id="{context['widget_id']}_hepatic_help" class="factor-help">
                            {_('Patient hepatic function status')}
                        </div>
                    </div>
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the interaction check results from form data."""
        selected_medications = data.getlist(f'{name}_medications')
        include_herbals = data.get(f'{name}_include_herbals') == 'on'
        include_otc = data.get(f'{name}_include_otc') == 'on'
        include_supplements = data.get(f'{name}_include_supplements') == 'on'
        age = data.get(f'{name}_age')
        renal_function = data.get(f'{name}_renal_function')
        hepatic_function = data.get(f'{name}_hepatic_function')
        
        if selected_medications or any([include_herbals, include_otc, include_supplements, age, renal_function, hepatic_function]):
            return {
                'selected_medications': selected_medications,
                'include_herbals': include_herbals,
                'include_otc': include_otc,
                'include_supplements': include_supplements,
                'patient_factors': {
                    'age': age,
                    'renal_function': renal_function,
                    'hepatic_function': hepatic_function,
                }
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.getlist(f'{name}_medications'),
            data.get(f'{name}_include_herbals'),
            data.get(f'{name}_include_otc'),
            data.get(f'{name}_include_supplements'),
            data.get(f'{name}_age'),
            data.get(f'{name}_renal_function'),
            data.get(f'{name}_hepatic_function'),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/medication_interaction_checker.css',)
        }
        js = ('js/widgets/medication_interaction_checker.js',)


# Register the widget with Wagtail's telepath system
register(MedicationInteractionCheckerWidget)


class StockLevelIndicatorWidget(AdminWidget):
    """
    Stock level indicator widget showing real-time medication inventory levels.
    
    Features:
    - Real-time stock level monitoring
    - Visual inventory indicators
    - Low stock alerts
    - Expiry date warnings
    - Reorder suggestions
    - Accessibility compliant
    """
    
    template_name = 'widgets/stock_level_indicator.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default stock monitoring options
        default_options = {
            'refresh_interval': 30,  # seconds
            'low_stock_threshold': 10,
            'critical_stock_threshold': 5,
            'expiry_warning_days': 30,
            'show_trends': True,
            'show_alerts': True,
            'show_reorder_suggestions': True,
            'max_display_items': 20,
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'stock_indicator_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the stock level indicator widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="stock-level-indicator" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="stock-indicator-label">
                {_('Medication Stock Levels')}
            </label>
            
            <div class="stock-summary" role="status" aria-live="polite">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-label">{_('Total Items:')}</span>
                        <span id="{context['widget_id']}_total_items" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Low Stock:')}</span>
                        <span id="{context['widget_id']}_low_stock_count" class="stat-value low-stock">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Critical:')}</span>
                        <span id="{context['widget_id']}_critical_count" class="stat-value critical">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Expiring Soon:')}</span>
                        <span id="{context['widget_id']}_expiring_count" class="stat-value expiring">-</span>
                    </div>
                </div>
                
                <div class="refresh-controls">
                    <button type="button" 
                            id="{context['widget_id']}_refresh_btn"
                            class="refresh-btn"
                            aria-label="{_('Refresh stock levels')}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6"/>
                            <path d="M1 20v-6h6"/>
                            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
                        </svg>
                    </button>
                    <span class="last-updated">
                        {_('Last updated:')} <span id="{context['widget_id']}_last_updated">-</span>
                    </span>
                </div>
            </div>
            
            <div class="stock-filters" role="group" aria-labelledby="{context['widget_id']}_filters_label">
                <label id="{context['widget_id']}_filters_label" class="filters-label">
                    {_('Filter Stock Levels')}
                </label>
                <div class="filter-buttons">
                    <button type="button" 
                            class="filter-btn active"
                            data-filter="all"
                            aria-pressed="true">
                        {_('All')}
                    </button>
                    <button type="button" 
                            class="filter-btn"
                            data-filter="low"
                            aria-pressed="false">
                        {_('Low Stock')}
                    </button>
                    <button type="button" 
                            class="filter-btn"
                            data-filter="critical"
                            aria-pressed="false">
                        {_('Critical')}
                    </button>
                    <button type="button" 
                            class="filter-btn"
                            data-filter="expiring"
                            aria-pressed="false">
                        {_('Expiring')}
                    </button>
                </div>
            </div>
            
            <div class="stock-list" role="list" aria-labelledby="{context['widget_id']}_list_label">
                <h3 id="{context['widget_id']}_list_label" class="list-label">
                    {_('Inventory Items')}
                </h3>
                <div id="{context['widget_id']}_stock_items" class="stock-items">
                    <div class="loading-indicator">
                        <div class="spinner"></div>
                        <p>{_('Loading stock levels...')}</p>
                    </div>
                </div>
            </div>
            
            <div class="stock-alerts" role="alert" aria-live="assertive">
                <div id="{context['widget_id']}_alerts" class="alert-container">
                    <!-- Alerts will be dynamically added here -->
                </div>
            </div>
            
            <div class="reorder-suggestions" style="display: none;" role="region" aria-labelledby="{context['widget_id']}_reorder_label">
                <h3 id="{context['widget_id']}_reorder_label" class="reorder-label">
                    {_('Reorder Suggestions')}
                </h3>
                <div id="{context['widget_id']}_suggestions" class="suggestions-list">
                    <!-- Reorder suggestions will be dynamically added here -->
                </div>
            </div>
            
            <div class="stock-chart" role="region" aria-labelledby="{context['widget_id']}_chart_label">
                <h3 id="{context['widget_id']}_chart_label" class="chart-label">
                    {_('Stock Level Trends')}
                </h3>
                <div id="{context['widget_id']}_chart_container" class="chart-container">
                    <canvas id="{context['widget_id']}_stock_chart" 
                            class="stock-chart-canvas"
                            role="img"
                            aria-label="{_('Stock level trends chart')}">
                    </canvas>
                </div>
            </div>
            
            <div class="stock-settings" role="group" aria-labelledby="{context['widget_id']}_settings_label">
                <label id="{context['widget_id']}_settings_label" class="settings-label">
                    {_('Stock Monitoring Settings')}
                </label>
                <div class="settings-inputs">
                    <div class="setting-group">
                        <label for="{context['widget_id']}_low_threshold" class="setting-label">
                            {_('Low Stock Threshold')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_low_threshold"
                               name="{name}_low_threshold"
                               class="setting-input"
                               min="1"
                               max="100"
                               value="10"
                               aria-describedby="{context['widget_id']}_low_threshold_help">
                        <div id="{context['widget_id']}_low_threshold_help" class="setting-help">
                            {_('Minimum stock level before low stock alert')}
                        </div>
                    </div>
                    
                    <div class="setting-group">
                        <label for="{context['widget_id']}_critical_threshold" class="setting-label">
                            {_('Critical Stock Threshold')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_critical_threshold"
                               name="{name}_critical_threshold"
                               class="setting-input"
                               min="1"
                               max="50"
                               value="5"
                               aria-describedby="{context['widget_id']}_critical_threshold_help">
                        <div id="{context['widget_id']}_critical_threshold_help" class="setting-help">
                            {_('Minimum stock level before critical alert')}
                        </div>
                    </div>
                    
                    <div class="setting-group">
                        <label for="{context['widget_id']}_expiry_warning" class="setting-label">
                            {_('Expiry Warning (days)')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_expiry_warning"
                               name="{name}_expiry_warning"
                               class="setting-input"
                               min="1"
                               max="365"
                               value="30"
                               aria-describedby="{context['widget_id']}_expiry_warning_help">
                        <div id="{context['widget_id']}_expiry_warning_help" class="setting-help">
                            {_('Days before expiry to show warning')}
                        </div>
                    </div>
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the stock monitoring settings from form data."""
        low_threshold = data.get(f'{name}_low_threshold')
        critical_threshold = data.get(f'{name}_critical_threshold')
        expiry_warning = data.get(f'{name}_expiry_warning')
        
        if any([low_threshold, critical_threshold, expiry_warning]):
            return {
                'low_threshold': int(low_threshold) if low_threshold else 10,
                'critical_threshold': int(critical_threshold) if critical_threshold else 5,
                'expiry_warning': int(expiry_warning) if expiry_warning else 30,
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.get(f'{name}_low_threshold'),
            data.get(f'{name}_critical_threshold'),
            data.get(f'{name}_expiry_warning'),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/stock_level_indicator.css',)
        }
        js = ('js/widgets/stock_level_indicator.js',)


# Register the widget with Wagtail's telepath system
register(StockLevelIndicatorWidget)


class MedicationScheduleWidget(AdminWidget):
    """
    Medication schedule widget for visual medication timing setup.
    
    Features:
    - Visual schedule builder
    - Drag & drop time slots
    - Multiple medication support
    - Conflict detection
    - Reminder integration
    - Accessibility compliant
    """
    
    template_name = 'widgets/medication_schedule.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default schedule options
        default_options = {
            'time_slots': [
                '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'
            ],
            'days_of_week': [
                ('monday', _('Monday')),
                ('tuesday', _('Tuesday')),
                ('wednesday', _('Wednesday')),
                ('thursday', _('Thursday')),
                ('friday', _('Friday')),
                ('saturday', _('Saturday')),
                ('sunday', _('Sunday')),
            ],
            'max_medications_per_slot': 5,
            'allow_custom_times': True,
            'show_conflicts': True,
            'enable_reminders': True,
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'medication_schedule_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the medication schedule widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="medication-schedule-widget" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="schedule-widget-label">
                {_('Medication Schedule Builder')}
            </label>
            
            <div class="schedule-controls" role="group" aria-labelledby="{context['widget_id']}_controls_label">
                <label id="{context['widget_id']}_controls_label" class="controls-label">
                    {_('Schedule Controls')}
                </label>
                
                <div class="control-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_add_medication"
                            class="add-medication-btn"
                            aria-describedby="{context['widget_id']}_add_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                        {_('Add Medication')}
                    </button>
                    <div id="{context['widget_id']}_add_help" class="help-text">
                        {_('Add a new medication to the schedule')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_add_time_slot"
                            class="add-time-slot-btn"
                            aria-describedby="{context['widget_id']}_time_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12,6 12,12 16,14"/>
                        </svg>
                        {_('Add Time Slot')}
                    </button>
                    <div id="{context['widget_id']}_time_help" class="help-text">
                        {_('Add a custom time slot to the schedule')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_check_conflicts"
                            class="check-conflicts-btn"
                            aria-describedby="{context['widget_id']}_conflicts_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        {_('Check Conflicts')}
                    </button>
                    <div id="{context['widget_id']}_conflicts_help" class="help-text">
                        {_('Check for medication timing conflicts')}
                    </div>
                </div>
            </div>
            
            <div class="schedule-grid" role="grid" aria-labelledby="{context['widget_id']}_grid_label">
                <h3 id="{context['widget_id']}_grid_label" class="grid-label">
                    {_('Weekly Schedule')}
                </h3>
                
                <div class="schedule-header" role="row">
                    <div class="time-column-header" role="columnheader">
                        {_('Time')}
                    </div>
                    <div class="day-column-header" role="columnheader">
                        {_('Monday')}
                    </div>
                    <div class="day-column-header" role="columnheader">
                        {_('Tuesday')}
                    </div>
                    <div class="day-column-header" role="columnheader">
                        {_('Wednesday')}
                    </div>
                    <div class="day-column-header" role="columnheader">
                        {_('Thursday')}
                    </div>
                    <div class="day-column-header" role="columnheader">
                        {_('Friday')}
                    </div>
                    <div class="day-column-header" role="columnheader">
                        {_('Saturday')}
                    </div>
                    <div class="day-column-header" role="columnheader">
                        {_('Sunday')}
                    </div>
                </div>
                
                <div id="{context['widget_id']}_schedule_rows" class="schedule-rows">
                    <!-- Schedule rows will be dynamically generated here -->
                </div>
            </div>
            
            <div class="medication-panel" role="region" aria-labelledby="{context['widget_id']}_medications_label">
                <h3 id="{context['widget_id']}_medications_label" class="medications-label">
                    {_('Medications')}
                </h3>
                <div id="{context['widget_id']}_medication_list" class="medication-list">
                    <p class="no-medications">{_('No medications added yet')}</p>
                </div>
            </div>
            
            <div class="schedule-summary" role="status" aria-live="polite">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-label">{_('Total Medications:')}</span>
                        <span id="{context['widget_id']}_total_medications" class="stat-value">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Time Slots:')}</span>
                        <span id="{context['widget_id']}_total_slots" class="stat-value">0</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Conflicts:')}</span>
                        <span id="{context['widget_id']}_conflict_count" class="stat-value">0</span>
                    </div>
                </div>
            </div>
            
            <div class="conflict-alerts" role="alert" aria-live="assertive">
                <div id="{context['widget_id']}_conflicts" class="conflict-container">
                    <!-- Conflict alerts will be dynamically added here -->
                </div>
            </div>
            
            <div class="reminder-settings" role="group" aria-labelledby="{context['widget_id']}_reminders_label">
                <label id="{context['widget_id']}_reminders_label" class="reminders-label">
                    {_('Reminder Settings')}
                </label>
                <div class="reminder-options">
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_enable_reminders"
                               name="{name}_enable_reminders"
                               class="reminder-checkbox"
                               checked>
                        <span class="checkbox-text">{_('Enable Reminders')}</span>
                    </label>
                    
                    <div class="reminder-timing">
                        <label for="{context['widget_id']}_reminder_advance" class="timing-label">
                            {_('Remind Before (minutes)')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_reminder_advance"
                               name="{name}_reminder_advance"
                               class="timing-input"
                               min="5"
                               max="60"
                               value="15"
                               aria-describedby="{context['widget_id']}_timing_help">
                        <div id="{context['widget_id']}_timing_help" class="timing-help">
                            {_('Minutes before scheduled time to send reminder')}
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="schedule-export" role="group" aria-labelledby="{context['widget_id']}_export_label">
                <label id="{context['widget_id']}_export_label" class="export-label">
                    {_('Export Schedule')}
                </label>
                <div class="export-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_export_pdf"
                            class="export-btn"
                            aria-describedby="{context['widget_id']}_pdf_help">
                        {_('Export PDF')}
                    </button>
                    <div id="{context['widget_id']}_pdf_help" class="export-help">
                        {_('Export schedule as PDF document')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_export_calendar"
                            class="export-btn"
                            aria-describedby="{context['widget_id']}_calendar_help">
                        {_('Export Calendar')}
                    </button>
                    <div id="{context['widget_id']}_calendar_help" class="export-help">
                        {_('Export schedule to calendar application')}
                    </div>
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the schedule data from form data."""
        enable_reminders = data.get(f'{name}_enable_reminders') == 'on'
        reminder_advance = data.get(f'{name}_reminder_advance')
        
        # Get schedule data from hidden field or form data
        schedule_data = data.get(name)
        
        if schedule_data:
            try:
                schedule_data = json.loads(schedule_data)
            except (ValueError, TypeError):
                schedule_data = {}
        
        if any([enable_reminders, reminder_advance, schedule_data]):
            return {
                'enable_reminders': enable_reminders,
                'reminder_advance': int(reminder_advance) if reminder_advance else 15,
                'schedule': schedule_data,
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.get(f'{name}_enable_reminders'),
            data.get(f'{name}_reminder_advance'),
            data.get(name),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/medication_schedule.css',)
        }
        js = ('js/widgets/medication_schedule.js',)


# Register the widget with Wagtail's telepath system
register(MedicationScheduleWidget)


class PharmacyLocatorWidget(AdminWidget):
    """
    Pharmacy locator widget with map integration and location services.
    
    Features:
    - Interactive map display
    - Location-based pharmacy search
    - Distance and availability filtering
    - Contact information integration
    - Route planning
    - Accessibility compliant
    """
    
    template_name = 'widgets/pharmacy_locator.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default pharmacy locator options
        default_options = {
            'default_location': 'Johannesburg, South Africa',
            'search_radius': 10,  # kilometers
            'max_results': 20,
            'show_24h_pharmacies': True,
            'show_online_pharmacies': True,
            'show_availability': True,
            'enable_routing': True,
            'map_provider': 'openstreetmap',  # or 'google', 'mapbox'
            'api_key': '',  # Will be set from settings
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'pharmacy_locator_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the pharmacy locator widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="pharmacy-locator-widget" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="locator-widget-label">
                {_('Pharmacy Locator')}
            </label>
            
            <div class="location-search" role="group" aria-labelledby="{context['widget_id']}_search_label">
                <label id="{context['widget_id']}_search_label" class="search-label">
                    {_('Find Pharmacies Near')}
                </label>
                
                <div class="search-inputs">
                    <div class="location-input-group">
                        <label for="{context['widget_id']}_location" class="input-label">
                            {_('Location')}
                        </label>
                        <input type="text" 
                               id="{context['widget_id']}_location"
                               name="{name}_location"
                               class="location-input"
                               placeholder="{_('Enter address or city...')}"
                               aria-describedby="{context['widget_id']}_location_help">
                        <div id="{context['widget_id']}_location_help" class="input-help">
                            {_('Enter your location to find nearby pharmacies')}
                        </div>
                    </div>
                    
                    <div class="radius-input-group">
                        <label for="{context['widget_id']}_radius" class="input-label">
                            {_('Search Radius (km)')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_radius"
                               name="{name}_radius"
                               class="radius-input"
                               min="1"
                               max="50"
                               value="10"
                               aria-describedby="{context['widget_id']}_radius_help">
                        <div id="{context['widget_id']}_radius_help" class="input-help">
                            {_('Maximum distance to search for pharmacies')}
                        </div>
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_search_btn"
                            class="search-btn"
                            aria-describedby="{context['widget_id']}_search_btn_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="11" cy="11" r="8"/>
                            <path d="m21 21-4.35-4.35"/>
                        </svg>
                        {_('Search')}
                    </button>
                    <div id="{context['widget_id']}_search_btn_help" class="button-help">
                        {_('Search for pharmacies in the specified area')}
                    </div>
                </div>
                
                <div class="location-options">
                    <button type="button" 
                            id="{context['widget_id']}_use_current_location"
                            class="current-location-btn"
                            aria-describedby="{context['widget_id']}_current_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"/>
                            <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"/>
                        </svg>
                        {_('Use Current Location')}
                    </button>
                    <div id="{context['widget_id']}_current_help" class="location-help">
                        {_('Use your current GPS location')}
                    </div>
                </div>
            </div>
            
            <div class="pharmacy-filters" role="group" aria-labelledby="{context['widget_id']}_filters_label">
                <label id="{context['widget_id']}_filters_label" class="filters-label">
                    {_('Filter Options')}
                </label>
                <div class="filter-options">
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_24h_pharmacies"
                               name="{name}_24h_pharmacies"
                               class="filter-checkbox"
                               checked>
                        <span class="checkbox-text">{_('24-Hour Pharmacies')}</span>
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_online_pharmacies"
                               name="{name}_online_pharmacies"
                               class="filter-checkbox"
                               checked>
                        <span class="checkbox-text">{_('Online Pharmacies')}</span>
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_show_availability"
                               name="{name}_show_availability"
                               class="filter-checkbox"
                               checked>
                        <span class="checkbox-text">{_('Show Availability')}</span>
                    </label>
                </div>
            </div>
            
            <div class="map-container" role="region" aria-labelledby="{context['widget_id']}_map_label">
                <h3 id="{context['widget_id']}_map_label" class="map-label">
                    {_('Pharmacy Map')}
                </h3>
                <div id="{context['widget_id']}_map" class="pharmacy-map">
                    <div class="map-loading">
                        <div class="spinner"></div>
                        <p>{_('Loading map...')}</p>
                    </div>
                </div>
                <div class="map-controls">
                    <button type="button" 
                            id="{context['widget_id']}_zoom_in"
                            class="map-control-btn"
                            aria-label="{_('Zoom in')}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="12" y1="5" x2="12" y2="19"/>
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                    </button>
                    <button type="button" 
                            id="{context['widget_id']}_zoom_out"
                            class="map-control-btn"
                            aria-label="{_('Zoom out')}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="5" y1="12" x2="19" y2="12"/>
                        </svg>
                    </button>
                    <button type="button" 
                            id="{context['widget_id']}_center_map"
                            class="map-control-btn"
                            aria-label="{_('Center map')}">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="3"/>
                            <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1"/>
                        </svg>
                    </button>
                </div>
            </div>
            
            <div class="pharmacy-list" role="list" aria-labelledby="{context['widget_id']}_list_label">
                <h3 id="{context['widget_id']}_list_label" class="list-label">
                    {_('Nearby Pharmacies')}
                </h3>
                <div id="{context['widget_id']}_pharmacies" class="pharmacy-items">
                    <p class="no-pharmacies">{_('Search for pharmacies to see results')}</p>
                </div>
            </div>
            
            <div class="pharmacy-details" style="display: none;" role="region" aria-labelledby="{context['widget_id']}_details_label">
                <h3 id="{context['widget_id']}_details_label" class="details-label">
                    {_('Pharmacy Details')}
                </h3>
                <div id="{context['widget_id']}_details" class="details-content">
                    <!-- Pharmacy details will be dynamically added here -->
                </div>
            </div>
            
            <div class="route-planning" style="display: none;" role="group" aria-labelledby="{context['widget_id']}_route_label">
                <label id="{context['widget_id']}_route_label" class="route-label">
                    {_('Route Planning')}
                </label>
                <div class="route-options">
                    <div class="transport-mode">
                        <label for="{context['widget_id']}_transport_mode" class="mode-label">
                            {_('Transport Mode')}
                        </label>
                        <select id="{context['widget_id']}_transport_mode"
                                name="{name}_transport_mode"
                                class="mode-select"
                                aria-describedby="{context['widget_id']}_mode_help">
                            <option value="driving">{_('Driving')}</option>
                            <option value="walking">{_('Walking')}</option>
                            <option value="transit">{_('Public Transport')}</option>
                            <option value="bicycling">{_('Cycling')}</option>
                        </select>
                        <div id="{context['widget_id']}_mode_help" class="mode-help">
                            {_('Preferred mode of transportation')}
                        </div>
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_get_route"
                            class="route-btn"
                            aria-describedby="{context['widget_id']}_route_help">
                        {_('Get Route')}
                    </button>
                    <div id="{context['widget_id']}_route_help" class="route-help">
                        {_('Get directions to the selected pharmacy')}
                    </div>
                </div>
                
                <div id="{context['widget_id']}_route_info" class="route-info">
                    <!-- Route information will be dynamically added here -->
                </div>
            </div>
            
            <div class="pharmacy-actions" role="group" aria-labelledby="{context['widget_id']}_actions_label">
                <label id="{context['widget_id']}_actions_label" class="actions-label">
                    {_('Quick Actions')}
                </label>
                <div class="action-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_call_pharmacy"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_call_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
                        </svg>
                        {_('Call Pharmacy')}
                    </button>
                    <div id="{context['widget_id']}_call_help" class="action-help">
                        {_('Call the selected pharmacy')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_share_location"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_share_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="18" cy="5" r="3"/>
                            <circle cx="6" cy="12" r="3"/>
                            <circle cx="18" cy="19" r="3"/>
                            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                        </svg>
                        {_('Share Location')}
                    </button>
                    <div id="{context['widget_id']}_share_help" class="action-help">
                        {_('Share pharmacy location')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_save_pharmacy"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_save_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/>
                        </svg>
                        {_('Save Pharmacy')}
                    </button>
                    <div id="{context['widget_id']}_save_help" class="action-help">
                        {_('Save pharmacy to favorites')}
                    </div>
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the pharmacy locator data from form data."""
        location = data.get(f'{name}_location')
        radius = data.get(f'{name}_radius')
        show_24h = data.get(f'{name}_24h_pharmacies') == 'on'
        show_online = data.get(f'{name}_online_pharmacies') == 'on'
        show_availability = data.get(f'{name}_show_availability') == 'on'
        transport_mode = data.get(f'{name}_transport_mode')
        
        if any([location, radius, show_24h, show_online, show_availability, transport_mode]):
            return {
                'location': location,
                'radius': int(radius) if radius else 10,
                'filters': {
                    'show_24h_pharmacies': show_24h,
                    'show_online_pharmacies': show_online,
                    'show_availability': show_availability,
                },
                'transport_mode': transport_mode or 'driving',
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.get(f'{name}_location'),
            data.get(f'{name}_radius'),
            data.get(f'{name}_24h_pharmacies'),
            data.get(f'{name}_online_pharmacies'),
            data.get(f'{name}_show_availability'),
            data.get(f'{name}_transport_mode'),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/pharmacy_locator.css',)
        }
        js = ('js/widgets/pharmacy_locator.js',)


# Register the widget with Wagtail's telepath system
register(PharmacyLocatorWidget)


class PrescriptionHistoryTimelineWidget(AdminWidget):
    """
    Prescription history timeline widget for visual prescription tracking.
    
    Features:
    - Visual timeline display
    - Prescription status tracking
    - Medication adherence visualization
    - Historical data analysis
    - Export capabilities
    - Accessibility compliant
    """
    
    template_name = 'widgets/prescription_history_timeline.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default timeline options
        default_options = {
            'timeline_period': '6_months',  # 1_month, 3_months, 6_months, 1_year, all
            'show_adherence': True,
            'show_side_effects': True,
            'show_dosage_changes': True,
            'show_refills': True,
            'group_by_medication': True,
            'enable_export': True,
            'max_display_items': 50,
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'prescription_timeline_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the prescription history timeline widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="prescription-history-timeline" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="timeline-widget-label">
                {_('Prescription History Timeline')}
            </label>
            
            <div class="timeline-controls" role="group" aria-labelledby="{context['widget_id']}_controls_label">
                <label id="{context['widget_id']}_controls_label" class="controls-label">
                    {_('Timeline Controls')}
                </label>
                
                <div class="period-selector">
                    <label for="{context['widget_id']}_period" class="period-label">
                        {_('Time Period')}
                    </label>
                    <select id="{context['widget_id']}_period"
                            name="{name}_period"
                            class="period-select"
                            aria-describedby="{context['widget_id']}_period_help">
                        <option value="1_month">{_('Last Month')}</option>
                        <option value="3_months">{_('Last 3 Months')}</option>
                        <option value="6_months" selected>{_('Last 6 Months')}</option>
                        <option value="1_year">{_('Last Year')}</option>
                        <option value="all">{_('All Time')}</option>
                    </select>
                    <div id="{context['widget_id']}_period_help" class="period-help">
                        {_('Select the time period to display')}
                    </div>
                </div>
                
                <div class="filter-options">
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_show_adherence"
                               name="{name}_show_adherence"
                               class="filter-checkbox"
                               checked>
                        <span class="checkbox-text">{_('Show Adherence')}</span>
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_show_side_effects"
                               name="{name}_show_side_effects"
                               class="filter-checkbox"
                               checked>
                        <span class="checkbox-text">{_('Show Side Effects')}</span>
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_show_dosage_changes"
                               name="{name}_show_dosage_changes"
                               class="filter-checkbox"
                               checked>
                        <span class="checkbox-text">{_('Show Dosage Changes')}</span>
                    </label>
                    <label class="checkbox-label">
                        <input type="checkbox" 
                               id="{context['widget_id']}_show_refills"
                               name="{name}_show_refills"
                               class="filter-checkbox"
                               checked>
                        <span class="checkbox-text">{_('Show Refills')}</span>
                    </label>
                </div>
            </div>
            
            <div class="timeline-summary" role="status" aria-live="polite">
                <div class="summary-stats">
                    <div class="stat-item">
                        <span class="stat-label">{_('Total Prescriptions:')}</span>
                        <span id="{context['widget_id']}_total_prescriptions" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Active Prescriptions:')}</span>
                        <span id="{context['widget_id']}_active_prescriptions" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Average Adherence:')}</span>
                        <span id="{context['widget_id']}_avg_adherence" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Last Refill:')}</span>
                        <span id="{context['widget_id']}_last_refill" class="stat-value">-</span>
                    </div>
                </div>
            </div>
            
            <div class="timeline-container" role="region" aria-labelledby="{context['widget_id']}_timeline_label">
                <h3 id="{context['widget_id']}_timeline_label" class="timeline-label">
                    {_('Prescription Timeline')}
                </h3>
                
                <div class="timeline-view-controls">
                    <button type="button" 
                            class="view-btn active"
                            data-view="timeline"
                            aria-pressed="true">
                        {_('Timeline')}
                    </button>
                    <button type="button" 
                            class="view-btn"
                            data-view="list"
                            aria-pressed="false">
                        {_('List')}
                    </button>
                    <button type="button" 
                            class="view-btn"
                            data-view="calendar"
                            aria-pressed="false">
                        {_('Calendar')}
                    </button>
                </div>
                
                <div id="{context['widget_id']}_timeline" class="timeline-view">
                    <div class="timeline-line"></div>
                    <div id="{context['widget_id']}_timeline_events" class="timeline-events">
                        <!-- Timeline events will be dynamically added here -->
                    </div>
                </div>
                
                <div id="{context['widget_id']}_list_view" class="list-view" style="display: none;">
                    <div id="{context['widget_id']}_list_events" class="list-events">
                        <!-- List view events will be dynamically added here -->
                    </div>
                </div>
                
                <div id="{context['widget_id']}_calendar_view" class="calendar-view" style="display: none;">
                    <div id="{context['widget_id']}_calendar" class="calendar-container">
                        <!-- Calendar view will be dynamically added here -->
                    </div>
                </div>
            </div>
            
            <div class="adherence-chart" role="region" aria-labelledby="{context['widget_id']}_adherence_label">
                <h3 id="{context['widget_id']}_adherence_label" class="adherence-label">
                    {_('Medication Adherence')}
                </h3>
                <div id="{context['widget_id']}_adherence_chart" class="adherence-chart-container">
                    <canvas id="{context['widget_id']}_adherence_canvas" 
                            class="adherence-canvas"
                            role="img"
                            aria-label="{_('Medication adherence chart')}">
                    </canvas>
                </div>
            </div>
            
            <div class="medication-breakdown" role="region" aria-labelledby="{context['widget_id']}_breakdown_label">
                <h3 id="{context['widget_id']}_breakdown_label" class="breakdown-label">
                    {_('Medication Breakdown')}
                </h3>
                <div id="{context['widget_id']}_medication_breakdown" class="breakdown-container">
                    <!-- Medication breakdown will be dynamically added here -->
                </div>
            </div>
            
            <div class="side-effects-summary" role="region" aria-labelledby="{context['widget_id']}_side_effects_label">
                <h3 id="{context['widget_id']}_side_effects_label" class="side-effects-label">
                    {_('Side Effects Summary')}
                </h3>
                <div id="{context['widget_id']}_side_effects" class="side-effects-container">
                    <!-- Side effects summary will be dynamically added here -->
                </div>
            </div>
            
            <div class="export-options" role="group" aria-labelledby="{context['widget_id']}_export_label">
                <label id="{context['widget_id']}_export_label" class="export-label">
                    {_('Export Options')}
                </label>
                <div class="export-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_export_pdf"
                            class="export-btn"
                            aria-describedby="{context['widget_id']}_pdf_help">
                        {_('Export PDF Report')}
                    </button>
                    <div id="{context['widget_id']}_pdf_help" class="export-help">
                        {_('Export timeline as PDF report')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_export_csv"
                            class="export-btn"
                            aria-describedby="{context['widget_id']}_csv_help">
                        {_('Export CSV Data')}
                    </button>
                    <div id="{context['widget_id']}_csv_help" class="export-help">
                        {_('Export timeline data as CSV file')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_export_json"
                            class="export-btn"
                            aria-describedby="{context['widget_id']}_json_help">
                        {_('Export JSON Data')}
                    </button>
                    <div id="{context['widget_id']}_json_help" class="export-help">
                        {_('Export timeline data as JSON file')}
                    </div>
                </div>
            </div>
            
            <div class="timeline-actions" role="group" aria-labelledby="{context['widget_id']}_actions_label">
                <label id="{context['widget_id']}_actions_label" class="actions-label">
                    {_('Timeline Actions')}
                </label>
                <div class="action-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_refresh_timeline"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_refresh_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M23 4v6h-6"/>
                            <path d="M1 20v-6h6"/>
                            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
                        </svg>
                        {_('Refresh Timeline')}
                    </button>
                    <div id="{context['widget_id']}_refresh_help" class="action-help">
                        {_('Refresh timeline with latest data')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_print_timeline"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_print_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6,9 6,2 18,2 18,9"/>
                            <path d="M6,18H4a2,2,0,0,1-2-2V11a2,2,0,0,1,2-2H20a2,2,0,0,1,2,2v5a2,2,0,0,1-2,2H18"/>
                            <polyline points="6,14 6,22 18,22 18,14"/>
                        </svg>
                        {_('Print Timeline')}
                    </button>
                    <div id="{context['widget_id']}_print_help" class="action-help">
                        {_('Print timeline for physical records')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_share_timeline"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_share_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="18" cy="5" r="3"/>
                            <circle cx="6" cy="12" r="3"/>
                            <circle cx="18" cy="19" r="3"/>
                            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/>
                            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/>
                        </svg>
                        {_('Share Timeline')}
                    </button>
                    <div id="{context['widget_id']}_share_help" class="action-help">
                        {_('Share timeline with healthcare provider')}
                    </div>
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the timeline settings from form data."""
        period = data.get(f'{name}_period')
        show_adherence = data.get(f'{name}_show_adherence') == 'on'
        show_side_effects = data.get(f'{name}_show_side_effects') == 'on'
        show_dosage_changes = data.get(f'{name}_show_dosage_changes') == 'on'
        show_refills = data.get(f'{name}_show_refills') == 'on'
        
        if any([period, show_adherence, show_side_effects, show_dosage_changes, show_refills]):
            return {
                'period': period or '6_months',
                'filters': {
                    'show_adherence': show_adherence,
                    'show_side_effects': show_side_effects,
                    'show_dosage_changes': show_dosage_changes,
                    'show_refills': show_refills,
                }
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.get(f'{name}_period'),
            data.get(f'{name}_show_adherence'),
            data.get(f'{name}_show_side_effects'),
            data.get(f'{name}_show_dosage_changes'),
            data.get(f'{name}_show_refills'),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/prescription_history_timeline.css',)
        }
        js = ('js/widgets/prescription_history_timeline.js',)


# Register the widget with Wagtail's telepath system
register(PrescriptionHistoryTimelineWidget)


class MedicationAdherenceTrackerWidget(AdminWidget):
    """
    Medication adherence tracker widget with progress visualization.
    
    Features:
    - Visual adherence tracking
    - Progress charts and graphs
    - Missed dose tracking
    - Adherence scoring
    - Goal setting and monitoring
    - Accessibility compliant
    """
    
    template_name = 'widgets/medication_adherence_tracker.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default adherence tracking options
        default_options = {
            'tracking_period': '30_days',  # 7_days, 30_days, 90_days, 6_months, 1_year
            'adherence_goal': 90,  # percentage
            'show_missed_doses': True,
            'show_trends': True,
            'show_goals': True,
            'enable_notifications': True,
            'max_display_medications': 10,
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'adherence_tracker_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the medication adherence tracker widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="medication-adherence-tracker" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="adherence-widget-label">
                {_('Medication Adherence Tracker')}
            </label>
            
            <div class="adherence-overview" role="status" aria-live="polite">
                <div class="overview-stats">
                    <div class="stat-item">
                        <span class="stat-label">{_('Overall Adherence:')}</span>
                        <span id="{context['widget_id']}_overall_adherence" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Goal:')}</span>
                        <span id="{context['widget_id']}_adherence_goal" class="stat-value">90%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Missed Doses:')}</span>
                        <span id="{context['widget_id']}_missed_doses" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Streak:')}</span>
                        <span id="{context['widget_id']}_current_streak" class="stat-value">-</span>
                    </div>
                </div>
                
                <div class="adherence-progress">
                    <div class="progress-container">
                        <div class="progress-bar" role="progressbar" aria-valuenow="0" aria-valuemin="0" aria-valuemax="100">
                            <div id="{context['widget_id']}_progress_fill" class="progress-fill"></div>
                        </div>
                        <span class="progress-text" id="{context['widget_id']}_progress_text">0%</span>
                    </div>
                </div>
            </div>
            
            <div class="tracking-controls" role="group" aria-labelledby="{context['widget_id']}_controls_label">
                <label id="{context['widget_id']}_controls_label" class="controls-label">
                    {_('Tracking Controls')}
                </label>
                
                <div class="period-selector">
                    <label for="{context['widget_id']}_tracking_period" class="period-label">
                        {_('Tracking Period')}
                    </label>
                    <select id="{context['widget_id']}_tracking_period"
                            name="{name}_tracking_period"
                            class="period-select"
                            aria-describedby="{context['widget_id']}_period_help">
                        <option value="7_days">{_('Last 7 Days')}</option>
                        <option value="30_days" selected>{_('Last 30 Days')}</option>
                        <option value="90_days">{_('Last 90 Days')}</option>
                        <option value="6_months">{_('Last 6 Months')}</option>
                        <option value="1_year">{_('Last Year')}</option>
                    </select>
                    <div id="{context['widget_id']}_period_help" class="period-help">
                        {_('Select the period to track adherence')}
                    </div>
                </div>
                
                <div class="goal-setting">
                    <label for="{context['widget_id']}_adherence_goal" class="goal-label">
                        {_('Adherence Goal (%)')}
                    </label>
                    <input type="number" 
                           id="{context['widget_id']}_adherence_goal_input"
                           name="{name}_adherence_goal"
                           class="goal-input"
                           min="50"
                           max="100"
                           value="90"
                           aria-describedby="{context['widget_id']}_goal_help">
                    <div id="{context['widget_id']}_goal_help" class="goal-help">
                        {_('Set your target adherence percentage')}
                    </div>
                </div>
            </div>
            
            <div class="medication-adherence-list" role="list" aria-labelledby="{context['widget_id']}_medications_label">
                <h3 id="{context['widget_id']}_medications_label" class="medications-label">
                    {_('Medication Adherence')}
                </h3>
                <div id="{context['widget_id']}_medication_list" class="medication-list">
                    <div class="loading-indicator">
                        <div class="spinner"></div>
                        <p>{_('Loading adherence data...')}</p>
                    </div>
                </div>
            </div>
            
            <div class="adherence-charts" role="region" aria-labelledby="{context['widget_id']}_charts_label">
                <h3 id="{context['widget_id']}_charts_label" class="charts-label">
                    {_('Adherence Analytics')}
                </h3>
                
                <div class="chart-container">
                    <div class="chart-item">
                        <h4 class="chart-title">{_('Daily Adherence')}</h4>
                        <div class="chart-wrapper">
                            <canvas id="{context['widget_id']}_daily_chart" 
                                    class="adherence-chart-canvas"
                                    role="img"
                                    aria-label="{_('Daily adherence chart')}">
                            </canvas>
                        </div>
                    </div>
                    
                    <div class="chart-item">
                        <h4 class="chart-title">{_('Weekly Trends')}</h4>
                        <div class="chart-wrapper">
                            <canvas id="{context['widget_id']}_weekly_chart" 
                                    class="adherence-chart-canvas"
                                    role="img"
                                    aria-label="{_('Weekly adherence trends chart')}">
                            </canvas>
                        </div>
                    </div>
                    
                    <div class="chart-item">
                        <h4 class="chart-title">{_('Medication Comparison')}</h4>
                        <div class="chart-wrapper">
                            <canvas id="{context['widget_id']}_comparison_chart" 
                                    class="adherence-chart-canvas"
                                    role="img"
                                    aria-label="{_('Medication adherence comparison chart')}">
                            </canvas>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="missed-doses-tracking" role="region" aria-labelledby="{context['widget_id']}_missed_label">
                <h3 id="{context['widget_id']}_missed_label" class="missed-label">
                    {_('Missed Doses')}
                </h3>
                <div id="{context['widget_id']}_missed_doses_list" class="missed-doses-list">
                    <!-- Missed doses will be dynamically added here -->
                </div>
            </div>
            
            <div class="adherence-insights" role="region" aria-labelledby="{context['widget_id']}_insights_label">
                <h3 id="{context['widget_id']}_insights_label" class="insights-label">
                    {_('Adherence Insights')}
                </h3>
                <div id="{context['widget_id']}_insights" class="insights-container">
                    <!-- Insights will be dynamically added here -->
                </div>
            </div>
            
            <div class="goal-achievements" role="region" aria-labelledby="{context['widget_id']}_achievements_label">
                <h3 id="{context['widget_id']}_achievements_label" class="achievements-label">
                    {_('Goal Achievements')}
                </h3>
                <div id="{context['widget_id']}_achievements" class="achievements-container">
                    <!-- Achievements will be dynamically added here -->
                </div>
            </div>
            
            <div class="adherence-actions" role="group" aria-labelledby="{context['widget_id']}_actions_label">
                <label id="{context['widget_id']}_actions_label" class="actions-label">
                    {_('Adherence Actions')}
                </label>
                <div class="action-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_log_dose"
                            class="action-btn primary"
                            aria-describedby="{context['widget_id']}_log_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M9 12l2 2 4-4"/>
                            <circle cx="12" cy="12" r="10"/>
                        </svg>
                        {_('Log Dose Taken')}
                    </button>
                    <div id="{context['widget_id']}_log_help" class="action-help">
                        {_('Mark a dose as taken')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_log_missed"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_missed_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="15" y1="9" x2="9" y2="15"/>
                            <line x1="9" y1="9" x2="15" y2="15"/>
                        </svg>
                        {_('Log Missed Dose')}
                    </button>
                    <div id="{context['widget_id']}_missed_help" class="action-help">
                        {_('Mark a dose as missed')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_set_reminder"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_reminder_help">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                            <line x1="12" y1="9" x2="12" y2="13"/>
                            <line x1="12" y1="17" x2="12.01" y2="17"/>
                        </svg>
                        {_('Set Reminder')}
                    </button>
                    <div id="{context['widget_id']}_reminder_help" class="action-help">
                        {_('Set up medication reminders')}
                    </div>
                </div>
            </div>
            
            <div class="adherence-export" role="group" aria-labelledby="{context['widget_id']}_export_label">
                <label id="{context['widget_id']}_export_label" class="export-label">
                    {_('Export Adherence Data')}
                </label>
                <div class="export-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_export_report"
                            class="export-btn"
                            aria-describedby="{context['widget_id']}_report_help">
                        {_('Export Report')}
                    </button>
                    <div id="{context['widget_id']}_report_help" class="export-help">
                        {_('Export adherence report as PDF')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_share_progress"
                            class="export-btn"
                            aria-describedby="{context['widget_id']}_share_help">
                        {_('Share Progress')}
                    </button>
                    <div id="{context['widget_id']}_share_help" class="export-help">
                        {_('Share adherence progress with healthcare provider')}
                    </div>
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the adherence tracking data from form data."""
        tracking_period = data.get(f'{name}_tracking_period')
        adherence_goal = data.get(f'{name}_adherence_goal')
        
        if any([tracking_period, adherence_goal]):
            return {
                'tracking_period': tracking_period or '30_days',
                'adherence_goal': int(adherence_goal) if adherence_goal else 90,
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.get(f'{name}_tracking_period'),
            data.get(f'{name}_adherence_goal'),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/medication_adherence_tracker.css',)
        }
        js = ('js/widgets/medication_adherence_tracker.js',)


# Register the widget with Wagtail's telepath system
register(MedicationAdherenceTrackerWidget)


class NotificationPreferenceWidget(AdminWidget):
    """
    Notification preference widget for setting up medication reminders.
    
    Features:
    - Multi-channel notification setup
    - Customizable reminder schedules
    - Priority-based notifications
    - Integration with existing notification system
    - Accessibility compliant
    """
    
    template_name = 'widgets/notification_preference.html'
    
    def __init__(self, attrs=None, options=None):
        super().__init__(attrs)
        self.options = options or {}
        
    def get_context_data(self, name, value, attrs):
        context = super().get_context_data(name, value, attrs)
        
        # Default notification options
        default_options = {
            'notification_channels': ['email', 'sms', 'push', 'in_app'],
            'reminder_types': ['medication', 'refill', 'appointment', 'side_effects'],
            'default_advance_time': 15,  # minutes
            'enable_smart_notifications': True,
            'quiet_hours': {'start': '22:00', 'end': '08:00'},
            'max_notifications_per_day': 10,
        }
        
        # Merge with provided options
        if self.options:
            default_options.update(self.options)
            
        context.update({
            'widget_options': json.dumps(default_options),
            'widget_id': f'notification_preference_{name}',
            'field_name': name,
            'current_value': value or '',
        })
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render the notification preference widget with enhanced accessibility features."""
        context = self.get_context_data(name, value, attrs)
        
        html = f'''
        <div class="notification-preference-widget" 
             id="{context['widget_id']}"
             data-widget-options='{context["widget_options"]}'
             role="group" 
             aria-labelledby="{context['widget_id']}_label">
            
            <label id="{context['widget_id']}_label" class="notification-widget-label">
                {_('Notification Preferences')}
            </label>
            
            <div class="notification-overview" role="status" aria-live="polite">
                <div class="overview-stats">
                    <div class="stat-item">
                        <span class="stat-label">{_('Active Channels:')}</span>
                        <span id="{context['widget_id']}_active_channels" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Daily Notifications:')}</span>
                        <span id="{context['widget_id']}_daily_count" class="stat-value">-</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">{_('Quiet Hours:')}</span>
                        <span id="{context['widget_id']}_quiet_hours" class="stat-value">22:00 - 08:00</span>
                    </div>
                </div>
            </div>
            
            <div class="notification-channels" role="group" aria-labelledby="{context['widget_id']}_channels_label">
                <label id="{context['widget_id']}_channels_label" class="channels-label">
                    {_('Notification Channels')}
                </label>
                
                <div class="channel-options">
                    <div class="channel-item">
                        <label class="channel-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_email_notifications"
                                   name="{name}_email_notifications"
                                   class="channel-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <div class="channel-info">
                                <span class="channel-name">{_('Email Notifications')}</span>
                                <span class="channel-description">{_('Receive notifications via email')}</span>
                            </div>
                        </label>
                        <div class="channel-settings" id="{context['widget_id']}_email_settings">
                            <label for="{context['widget_id']}_email_frequency" class="setting-label">
                                {_('Frequency')}
                            </label>
                            <select id="{context['widget_id']}_email_frequency"
                                    name="{name}_email_frequency"
                                    class="setting-select">
                                <option value="immediate">{_('Immediate')}</option>
                                <option value="hourly">{_('Hourly')}</option>
                                <option value="daily">{_('Daily Summary')}</option>
                                <option value="weekly">{_('Weekly Summary')}</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="channel-item">
                        <label class="channel-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_sms_notifications"
                                   name="{name}_sms_notifications"
                                   class="channel-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <div class="channel-info">
                                <span class="channel-name">{_('SMS Notifications')}</span>
                                <span class="channel-description">{_('Receive notifications via SMS')}</span>
                            </div>
                        </label>
                        <div class="channel-settings" id="{context['widget_id']}_sms_settings">
                            <label for="{context['widget_id']}_sms_priority" class="setting-label">
                                {_('Priority')}
                            </label>
                            <select id="{context['widget_id']}_sms_priority"
                                    name="{name}_sms_priority"
                                    class="setting-select">
                                <option value="high">{_('High Priority Only')}</option>
                                <option value="medium">{_('Medium Priority')}</option>
                                <option value="low">{_('All Notifications')}</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="channel-item">
                        <label class="channel-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_push_notifications"
                                   name="{name}_push_notifications"
                                   class="channel-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <div class="channel-info">
                                <span class="channel-name">{_('Push Notifications')}</span>
                                <span class="channel-description">{_('Receive notifications on mobile device')}</span>
                            </div>
                        </label>
                        <div class="channel-settings" id="{context['widget_id']}_push_settings">
                            <label for="{context['widget_id']}_push_sound" class="setting-label">
                                {_('Sound')}
                            </label>
                            <select id="{context['widget_id']}_push_sound"
                                    name="{name}_push_sound"
                                    class="setting-select">
                                <option value="default">{_('Default')}</option>
                                <option value="gentle">{_('Gentle')}</option>
                                <option value="urgent">{_('Urgent')}</option>
                                <option value="none">{_('No Sound')}</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="channel-item">
                        <label class="channel-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_in_app_notifications"
                                   name="{name}_in_app_notifications"
                                   class="channel-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <div class="channel-info">
                                <span class="channel-name">{_('In-App Notifications')}</span>
                                <span class="channel-description">{_('Receive notifications within the app')}</span>
                            </div>
                        </label>
                        <div class="channel-settings" id="{context['widget_id']}_in_app_settings">
                            <label for="{context['widget_id']}_in_app_duration" class="setting-label">
                                {_('Display Duration')}
                            </label>
                            <select id="{context['widget_id']}_in_app_duration"
                                    name="{name}_in_app_duration"
                                    class="setting-select">
                                <option value="5">{_('5 seconds')}</option>
                                <option value="10">{_('10 seconds')}</option>
                                <option value="30">{_('30 seconds')}</option>
                                <option value="until_dismissed">{_('Until dismissed')}</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="reminder-settings" role="group" aria-labelledby="{context['widget_id']}_reminders_label">
                <label id="{context['widget_id']}_reminders_label" class="reminders-label">
                    {_('Reminder Settings')}
                </label>
                
                <div class="reminder-types">
                    <div class="reminder-item">
                        <label class="reminder-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_medication_reminders"
                                   name="{name}_medication_reminders"
                                   class="reminder-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <span class="reminder-name">{_('Medication Reminders')}</span>
                        </label>
                        <div class="reminder-settings" id="{context['widget_id']}_medication_settings">
                            <label for="{context['widget_id']}_medication_advance" class="setting-label">
                                {_('Advance Notice (minutes)')}
                            </label>
                            <input type="number" 
                                   id="{context['widget_id']}_medication_advance"
                                   name="{name}_medication_advance"
                                   class="setting-input"
                                   min="5"
                                   max="60"
                                   value="15">
                        </div>
                    </div>
                    
                    <div class="reminder-item">
                        <label class="reminder-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_refill_reminders"
                                   name="{name}_refill_reminders"
                                   class="reminder-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <span class="reminder-name">{_('Refill Reminders')}</span>
                        </label>
                        <div class="reminder-settings" id="{context['widget_id']}_refill_settings">
                            <label for="{context['widget_id']}_refill_advance" class="setting-label">
                                {_('Advance Notice (days)')}
                            </label>
                            <input type="number" 
                                   id="{context['widget_id']}_refill_advance"
                                   name="{name}_refill_advance"
                                   class="setting-input"
                                   min="1"
                                   max="30"
                                   value="7">
                        </div>
                    </div>
                    
                    <div class="reminder-item">
                        <label class="reminder-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_appointment_reminders"
                                   name="{name}_appointment_reminders"
                                   class="reminder-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <span class="reminder-name">{_('Appointment Reminders')}</span>
                        </label>
                        <div class="reminder-settings" id="{context['widget_id']}_appointment_settings">
                            <label for="{context['widget_id']}_appointment_advance" class="setting-label">
                                {_('Advance Notice (hours)')}
                            </label>
                            <input type="number" 
                                   id="{context['widget_id']}_appointment_advance"
                                   name="{name}_appointment_advance"
                                   class="setting-input"
                                   min="1"
                                   max="48"
                                   value="24">
                        </div>
                    </div>
                    
                    <div class="reminder-item">
                        <label class="reminder-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_side_effects_reminders"
                                   name="{name}_side_effects_reminders"
                                   class="reminder-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <span class="reminder-name">{_('Side Effects Tracking')}</span>
                        </label>
                        <div class="reminder-settings" id="{context['widget_id']}_side_effects_settings">
                            <label for="{context['widget_id']}_side_effects_frequency" class="setting-label">
                                {_('Reminder Frequency')}
                            </label>
                            <select id="{context['widget_id']}_side_effects_frequency"
                                    name="{name}_side_effects_frequency"
                                    class="setting-select">
                                <option value="daily">{_('Daily')}</option>
                                <option value="weekly">{_('Weekly')}</option>
                                <option value="monthly">{_('Monthly')}</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="quiet-hours" role="group" aria-labelledby="{context['widget_id']}_quiet_label">
                <label id="{context['widget_id']}_quiet_label" class="quiet-label">
                    {_('Quiet Hours')}
                </label>
                
                <div class="quiet-hours-toggle">
                    <label class="toggle-switch">
                        <input type="checkbox" 
                               id="{context['widget_id']}_enable_quiet_hours"
                               name="{name}_enable_quiet_hours"
                               class="toggle-input"
                               checked>
                        <span class="toggle-slider"></span>
                        <span class="toggle-text">{_('Enable Quiet Hours')}</span>
                    </label>
                </div>
                
                <div class="quiet-hours-settings" id="{context['widget_id']}_quiet_settings">
                    <div class="time-range">
                        <div class="time-input">
                            <label for="{context['widget_id']}_quiet_start" class="time-label">
                                {_('Start Time')}
                            </label>
                            <input type="time" 
                                   id="{context['widget_id']}_quiet_start"
                                   name="{name}_quiet_start"
                                   class="time-input-field"
                                   value="22:00">
                        </div>
                        <div class="time-separator">-</div>
                        <div class="time-input">
                            <label for="{context['widget_id']}_quiet_end" class="time-label">
                                {_('End Time')}
                            </label>
                            <input type="time" 
                                   id="{context['widget_id']}_quiet_end"
                                   name="{name}_quiet_end"
                                   class="time-input-field"
                                   value="08:00">
                        </div>
                    </div>
                    
                    <div class="quiet-exceptions">
                        <label class="exception-checkbox">
                            <input type="checkbox" 
                                   id="{context['widget_id']}_urgent_override"
                                   name="{name}_urgent_override"
                                   class="exception-input"
                                   checked>
                            <span class="checkbox-custom"></span>
                            <span class="exception-text">{_('Allow urgent notifications during quiet hours')}</span>
                        </label>
                    </div>
                </div>
            </div>
            
            <div class="smart-notifications" role="group" aria-labelledby="{context['widget_id']}_smart_label">
                <label id="{context['widget_id']}_smart_label" class="smart-label">
                    {_('Smart Notifications')}
                </label>
                
                <div class="smart-options">
                    <label class="smart-checkbox">
                        <input type="checkbox" 
                               id="{context['widget_id']}_enable_smart_notifications"
                               name="{name}_enable_smart_notifications"
                               class="smart-input"
                               checked>
                        <span class="checkbox-custom"></span>
                        <span class="smart-text">{_('Enable smart notification scheduling')}</span>
                    </label>
                    
                    <div class="smart-settings" id="{context['widget_id']}_smart_settings">
                        <div class="smart-item">
                            <label class="smart-checkbox">
                                <input type="checkbox" 
                                       id="{context['widget_id']}_learn_preferences"
                                       name="{name}_learn_preferences"
                                       class="smart-input"
                                       checked>
                                <span class="checkbox-custom"></span>
                                <span class="smart-text">{_('Learn from user interaction patterns')}</span>
                            </label>
                        </div>
                        
                        <div class="smart-item">
                            <label class="smart-checkbox">
                                <input type="checkbox" 
                                       id="{context['widget_id']}_reduce_frequency"
                                       name="{name}_reduce_frequency"
                                       class="smart-input"
                                       checked>
                                <span class="checkbox-custom"></span>
                                <span class="smart-text">{_('Reduce frequency for less important notifications')}</span>
                            </label>
                        </div>
                        
                        <div class="smart-item">
                            <label class="smart-checkbox">
                                <input type="checkbox" 
                                       id="{context['widget_id']}_batch_notifications"
                                       name="{name}_batch_notifications"
                                       class="smart-input"
                                       checked>
                                <span class="checkbox-custom"></span>
                                <span class="smart-text">{_('Batch similar notifications')}</span>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="notification-limits" role="group" aria-labelledby="{context['widget_id']}_limits_label">
                <label id="{context['widget_id']}_limits_label" class="limits-label">
                    {_('Notification Limits')}
                </label>
                
                <div class="limit-settings">
                    <div class="limit-item">
                        <label for="{context['widget_id']}_max_daily" class="limit-label">
                            {_('Maximum Daily Notifications')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_max_daily"
                               name="{name}_max_daily"
                               class="limit-input"
                               min="1"
                               max="50"
                               value="10">
                    </div>
                    
                    <div class="limit-item">
                        <label for="{context['widget_id']}_max_hourly" class="limit-label">
                            {_('Maximum Hourly Notifications')}
                        </label>
                        <input type="number" 
                               id="{context['widget_id']}_max_hourly"
                               name="{name}_max_hourly"
                               class="limit-input"
                               min="1"
                               max="10"
                               value="3">
                    </div>
                </div>
            </div>
            
            <div class="notification-actions" role="group" aria-labelledby="{context['widget_id']}_actions_label">
                <label id="{context['widget_id']}_actions_label" class="actions-label">
                    {_('Notification Actions')}
                </label>
                <div class="action-buttons">
                    <button type="button" 
                            id="{context['widget_id']}_test_notification"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_test_help">
                        {_('Test Notification')}
                    </button>
                    <div id="{context['widget_id']}_test_help" class="action-help">
                        {_('Send a test notification to verify settings')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_save_preferences"
                            class="action-btn primary"
                            aria-describedby="{context['widget_id']}_save_help">
                        {_('Save Preferences')}
                    </button>
                    <div id="{context['widget_id']}_save_help" class="action-help">
                        {_('Save notification preferences')}
                    </div>
                    
                    <button type="button" 
                            id="{context['widget_id']}_reset_defaults"
                            class="action-btn"
                            aria-describedby="{context['widget_id']}_reset_help">
                        {_('Reset to Defaults')}
                    </button>
                    <div id="{context['widget_id']}_reset_help" class="action-help">
                        {_('Reset all preferences to default values')}
                    </div>
                </div>
            </div>
            
            <input type="hidden" 
                   name="{name}" 
                   id="{context['widget_id']}_hidden"
                   value="{context['current_value']}">
        </div>
        '''
        
        return mark_safe(html)
    
    def value_from_datadict(self, data, files, name):
        """Extract the notification preferences from form data."""
        # Extract channel preferences
        email_notifications = data.get(f'{name}_email_notifications') == 'on'
        sms_notifications = data.get(f'{name}_sms_notifications') == 'on'
        push_notifications = data.get(f'{name}_push_notifications') == 'on'
        in_app_notifications = data.get(f'{name}_in_app_notifications') == 'on'
        
        # Extract reminder preferences
        medication_reminders = data.get(f'{name}_medication_reminders') == 'on'
        refill_reminders = data.get(f'{name}_refill_reminders') == 'on'
        appointment_reminders = data.get(f'{name}_appointment_reminders') == 'on'
        side_effects_reminders = data.get(f'{name}_side_effects_reminders') == 'on'
        
        # Extract settings
        enable_quiet_hours = data.get(f'{name}_enable_quiet_hours') == 'on'
        enable_smart_notifications = data.get(f'{name}_enable_smart_notifications') == 'on'
        
        if any([
            email_notifications, sms_notifications, push_notifications, in_app_notifications,
            medication_reminders, refill_reminders, appointment_reminders, side_effects_reminders,
            enable_quiet_hours, enable_smart_notifications
        ]):
            return {
                'channels': {
                    'email': email_notifications,
                    'sms': sms_notifications,
                    'push': push_notifications,
                    'in_app': in_app_notifications,
                },
                'reminders': {
                    'medication': medication_reminders,
                    'refill': refill_reminders,
                    'appointment': appointment_reminders,
                    'side_effects': side_effects_reminders,
                },
                'settings': {
                    'enable_quiet_hours': enable_quiet_hours,
                    'enable_smart_notifications': enable_smart_notifications,
                }
            }
        return None
    
    def value_omitted_from_data(self, data, files, name):
        """Check if the widget value was omitted from the form data."""
        return not any([
            data.get(f'{name}_email_notifications'),
            data.get(f'{name}_sms_notifications'),
            data.get(f'{name}_push_notifications'),
            data.get(f'{name}_in_app_notifications'),
            data.get(f'{name}_medication_reminders'),
            data.get(f'{name}_refill_reminders'),
            data.get(f'{name}_appointment_reminders'),
            data.get(f'{name}_side_effects_reminders'),
            data.get(f'{name}_enable_quiet_hours'),
            data.get(f'{name}_enable_smart_notifications'),
        ])
    
    class Media:
        """Include required CSS and JavaScript for the widget."""
        css = {
            'all': ('css/widgets/notification_preference.css',)
        }
        js = ('js/widgets/notification_preference.js',)


# Register the widget with Wagtail's telepath system
register(NotificationPreferenceWidget) 