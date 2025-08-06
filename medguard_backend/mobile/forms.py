"""
Mobile-optimized forms for prescription submission and medication tracking
Wagtail 7.0.2 form improvements
"""

from django import forms
from django.core.validators import RegexValidator
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from wagtail.images.models import Image
from wagtail.images.forms import WagtailImageField
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MobileFormMixin:
    """
    Mixin for mobile-optimized form fields
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_mobile_classes()
    
    def add_mobile_classes(self):
        """
        Add mobile-optimized CSS classes to form fields
        """
        for field_name, field in self.fields.items():
            # Add mobile-specific classes
            if hasattr(field, 'widget'):
                current_classes = field.widget.attrs.get('class', '')
                mobile_classes = 'mobile-form-field touch-optimized'
                
                # Add field-specific classes
                if isinstance(field.widget, forms.TextInput):
                    mobile_classes += ' mobile-text-input'
                elif isinstance(field.widget, forms.Textarea):
                    mobile_classes += ' mobile-textarea'
                elif isinstance(field.widget, forms.Select):
                    mobile_classes += ' mobile-select'
                elif isinstance(field.widget, forms.CheckboxInput):
                    mobile_classes += ' mobile-checkbox'
                elif isinstance(field.widget, forms.RadioSelect):
                    mobile_classes += ' mobile-radio'
                elif isinstance(field.widget, forms.FileInput):
                    mobile_classes += ' mobile-file-input'
                
                field.widget.attrs['class'] = f"{current_classes} {mobile_classes}".strip()
                
                # Add mobile-specific attributes
                field.widget.attrs.update({
                    'autocomplete': 'off',
                    'spellcheck': 'false',
                })


class MobilePrescriptionForm(forms.Form, MobileFormMixin):
    """
    Mobile-optimized prescription submission form
    """
    
    # Patient Information
    patient_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Patient Name',
            'autocomplete': 'name',
        }),
        help_text="Full name of the patient"
    )
    
    patient_id = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': 'Patient ID (optional)',
        }),
        required=False,
        help_text="Patient identification number"
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'max': datetime.now().date().isoformat(),
        }),
        help_text="Patient's date of birth"
    )
    
    # Medication Information
    medication_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Medication Name',
            'autocomplete': 'off',
        }),
        help_text="Name of the medication"
    )
    
    generic_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Generic Name (optional)',
        }),
        required=False,
        help_text="Generic name of the medication"
    )
    
    dosage_form = forms.ChoiceField(
        choices=[
            ('', 'Select Dosage Form'),
            ('tablet', 'Tablet'),
            ('capsule', 'Capsule'),
            ('liquid', 'Liquid'),
            ('injection', 'Injection'),
            ('cream', 'Cream'),
            ('inhaler', 'Inhaler'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={
            'class': 'mobile-select',
        }),
        help_text="Form of the medication"
    )
    
    strength = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., 500mg, 10mg/ml',
        }),
        help_text="Strength/concentration of the medication"
    )
    
    # Prescription Details
    dosage_instructions = forms.CharField(
        max_length=200,
        widget=forms.Textarea(attrs={
            'placeholder': 'e.g., Take 1 tablet twice daily with food',
            'rows': 3,
        }),
        help_text="How to take the medication"
    )
    
    frequency = forms.ChoiceField(
        choices=[
            ('', 'Select Frequency'),
            ('once_daily', 'Once Daily'),
            ('twice_daily', 'Twice Daily'),
            ('three_times_daily', 'Three Times Daily'),
            ('four_times_daily', 'Four Times Daily'),
            ('as_needed', 'As Needed'),
            ('other', 'Other'),
        ],
        widget=forms.Select(attrs={
            'class': 'mobile-select',
        }),
        help_text="How often to take the medication"
    )
    
    duration = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., 7 days, 30 days, until finished',
        }),
        help_text="How long to take the medication"
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Number of units',
            'min': '1',
        }),
        help_text="Quantity to dispense"
    )
    
    # Prescriber Information
    prescriber_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Prescriber Name',
            'autocomplete': 'name',
        }),
        help_text="Name of the prescribing healthcare provider"
    )
    
    prescriber_license = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'License Number',
        }),
        help_text="Prescriber's license number"
    )
    
    # Pharmacy Information
    pharmacy_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Pharmacy Name',
        }),
        help_text="Name of the dispensing pharmacy"
    )
    
    # Additional Information
    special_instructions = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'placeholder': 'Any special instructions or warnings',
            'rows': 3,
        }),
        required=False,
        help_text="Special instructions or warnings"
    )
    
    prescription_image = WagtailImageField(
        required=False,
        help_text="Upload prescription image (optional)"
    )
    
    # Emergency Information
    emergency_contact = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Emergency Contact Name',
        }),
        required=False,
        help_text="Emergency contact person"
    )
    
    emergency_phone = forms.CharField(
        max_length=20,
        widget=forms.TelInput(attrs={
            'placeholder': 'Emergency Phone Number',
            'pattern': '[0-9+\-\s()]+',
        }),
        required=False,
        help_text="Emergency contact phone number"
    )
    
    class Meta:
        fields = '__all__'
    
    def clean(self):
        """
        Custom validation for prescription form
        """
        cleaned_data = super().clean()
        
        # Validate date of birth
        date_of_birth = cleaned_data.get('date_of_birth')
        if date_of_birth and date_of_birth > datetime.now().date():
            raise forms.ValidationError("Date of birth cannot be in the future")
        
        # Validate emergency contact information
        emergency_contact = cleaned_data.get('emergency_contact')
        emergency_phone = cleaned_data.get('emergency_phone')
        
        if emergency_contact and not emergency_phone:
            raise forms.ValidationError("Emergency phone number is required if emergency contact is provided")
        
        if emergency_phone and not emergency_contact:
            raise forms.ValidationError("Emergency contact name is required if emergency phone is provided")
        
        return cleaned_data


class MobileMedicationTrackingForm(forms.Form, MobileFormMixin):
    """
    Mobile-optimized medication tracking form
    """
    
    # Medication Selection
    medication = forms.ChoiceField(
        choices=[],  # Will be populated dynamically
        widget=forms.Select(attrs={
            'class': 'mobile-select',
        }),
        help_text="Select medication to track"
    )
    
    # Tracking Details
    tracking_date = forms.DateField(
        initial=datetime.now().date,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'max': datetime.now().date().isoformat(),
        }),
        help_text="Date of tracking entry"
    )
    
    tracking_time = forms.TimeField(
        initial=datetime.now().time,
        widget=forms.TimeInput(attrs={
            'type': 'time',
        }),
        help_text="Time of medication administration"
    )
    
    # Dosage Information
    dosage_taken = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., 1 tablet, 5ml',
        }),
        help_text="Amount of medication taken"
    )
    
    # Side Effects
    side_effects = forms.MultipleChoiceField(
        choices=[
            ('none', 'None'),
            ('nausea', 'Nausea'),
            ('headache', 'Headache'),
            ('dizziness', 'Dizziness'),
            ('fatigue', 'Fatigue'),
            ('rash', 'Rash'),
            ('other', 'Other'),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'mobile-checkbox-group',
        }),
        required=False,
        help_text="Any side effects experienced"
    )
    
    other_side_effects = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Describe other side effects',
        }),
        required=False,
        help_text="Describe any other side effects"
    )
    
    # Effectiveness
    effectiveness = forms.ChoiceField(
        choices=[
            ('', 'Select Effectiveness'),
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
            ('unknown', 'Unknown'),
        ],
        widget=forms.Select(attrs={
            'class': 'mobile-select',
        }),
        help_text="How effective was the medication"
    )
    
    # Notes
    notes = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'placeholder': 'Additional notes or observations',
            'rows': 3,
        }),
        required=False,
        help_text="Any additional notes or observations"
    )
    
    # Photo Documentation
    photo = WagtailImageField(
        required=False,
        help_text="Photo documentation (optional)"
    )
    
    def __init__(self, *args, **kwargs):
        medications = kwargs.pop('medications', [])
        super().__init__(*args, **kwargs)
        
        # Populate medication choices
        if medications:
            self.fields['medication'].choices = [('', 'Select Medication')] + medications


class MobileStockManagementForm(forms.Form, MobileFormMixin):
    """
    Mobile-optimized stock management form
    """
    
    # Medication Information
    medication = forms.ChoiceField(
        choices=[],  # Will be populated dynamically
        widget=forms.Select(attrs={
            'class': 'mobile-select',
        }),
        help_text="Select medication for stock management"
    )
    
    # Stock Action
    action_type = forms.ChoiceField(
        choices=[
            ('', 'Select Action'),
            ('add', 'Add Stock'),
            ('remove', 'Remove Stock'),
            ('adjust', 'Adjust Stock'),
            ('expired', 'Mark Expired'),
        ],
        widget=forms.Select(attrs={
            'class': 'mobile-select',
        }),
        help_text="Type of stock action"
    )
    
    # Quantity
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Quantity',
            'min': '1',
        }),
        help_text="Quantity for stock action"
    )
    
    # Batch Information
    batch_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Batch Number',
        }),
        required=False,
        help_text="Batch or lot number"
    )
    
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'min': datetime.now().date().isoformat(),
        }),
        required=False,
        help_text="Expiry date of the batch"
    )
    
    # Location
    storage_location = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Storage Location',
        }),
        required=False,
        help_text="Storage location or shelf"
    )
    
    # Notes
    notes = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'placeholder': 'Additional notes',
            'rows': 3,
        }),
        required=False,
        help_text="Additional notes about the stock action"
    )
    
    def __init__(self, *args, **kwargs):
        medications = kwargs.pop('medications', [])
        super().__init__(*args, **kwargs)
        
        # Populate medication choices
        if medications:
            self.fields['medication'].choices = [('', 'Select Medication')] + medications


class MobileFormCSS:
    """
    CSS for mobile-optimized forms
    """
    
    @staticmethod
    def get_mobile_form_css():
        """
        Get CSS for mobile-optimized forms
        """
        css = """
        <style>
        /* Mobile form styles */
        .mobile-form-field {
            width: 100%;
            min-height: 48px;
            font-size: 16px;
            padding: 12px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            background-color: white;
            transition: all 0.2s ease;
            margin-bottom: 1rem;
        }
        
        .mobile-form-field:focus {
            outline: none;
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .mobile-form-field:invalid {
            border-color: #dc2626;
        }
        
        /* Text inputs */
        .mobile-text-input {
            font-size: 16px; /* Prevent zoom on iOS */
        }
        
        /* Textareas */
        .mobile-textarea {
            resize: vertical;
            min-height: 80px;
            font-family: inherit;
        }
        
        /* Select dropdowns */
        .mobile-select {
            background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3e%3cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='m6 8 4 4 4-4'/%3e%3c/svg%3e");
            background-position: right 12px center;
            background-repeat: no-repeat;
            background-size: 16px;
            padding-right: 40px;
            appearance: none;
        }
        
        /* Checkboxes */
        .mobile-checkbox {
            width: 20px;
            height: 20px;
            border: 2px solid #d1d5db;
            border-radius: 4px;
            background-color: white;
            cursor: pointer;
        }
        
        .mobile-checkbox:checked {
            background-color: #2563eb;
            border-color: #2563eb;
            background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3cpath d='M12.207 4.793a1 1 0 010 1.414l-5 5a1 1 0 01-1.414 0l-2-2a1 1 0 011.414-1.414L6.5 9.086l4.293-4.293a1 1 0 011.414 0z'/%3e%3c/svg%3e");
        }
        
        .mobile-checkbox-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .mobile-checkbox-group label {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            cursor: pointer;
            padding: 0.5rem;
            border-radius: 4px;
            transition: background-color 0.2s;
        }
        
        .mobile-checkbox-group label:hover {
            background-color: #f3f4f6;
        }
        
        /* Radio buttons */
        .mobile-radio {
            width: 20px;
            height: 20px;
            border: 2px solid #d1d5db;
            border-radius: 50%;
            background-color: white;
            cursor: pointer;
        }
        
        .mobile-radio:checked {
            border-color: #2563eb;
            background-color: #2563eb;
            background-image: url("data:image/svg+xml,%3csvg viewBox='0 0 16 16' fill='white' xmlns='http://www.w3.org/2000/svg'%3e%3ccircle cx='8' cy='8' r='3'/%3e%3c/svg%3e");
        }
        
        /* File inputs */
        .mobile-file-input {
            padding: 8px;
        }
        
        .mobile-file-input::-webkit-file-upload-button {
            background: #2563eb;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 8px;
        }
        
        /* Form layout */
        .mobile-form {
            max-width: 600px;
            margin: 0 auto;
            padding: 1rem;
        }
        
        .mobile-form-section {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .mobile-form-section h3 {
            margin: 0 0 1rem 0;
            color: #1e293b;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .mobile-form-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        
        .mobile-form-row .mobile-form-field {
            flex: 1;
            margin-bottom: 0;
        }
        
        /* Form buttons */
        .mobile-form-buttons {
            display: flex;
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .mobile-btn {
            flex: 1;
            min-height: 48px;
            font-size: 16px;
            font-weight: 600;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
        }
        
        .mobile-btn-primary {
            background-color: #2563eb;
            color: white;
        }
        
        .mobile-btn-primary:hover {
            background-color: #1d4ed8;
        }
        
        .mobile-btn-secondary {
            background-color: #6b7280;
            color: white;
        }
        
        .mobile-btn-secondary:hover {
            background-color: #4b5563;
        }
        
        .mobile-btn-danger {
            background-color: #dc2626;
            color: white;
        }
        
        .mobile-btn-danger:hover {
            background-color: #b91c1c;
        }
        
        /* Form validation */
        .mobile-form-field.error {
            border-color: #dc2626;
        }
        
        .mobile-error-message {
            color: #dc2626;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        .mobile-help-text {
            color: #6b7280;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }
        
        /* Loading states */
        .mobile-form.loading {
            opacity: 0.6;
            pointer-events: none;
        }
        
        .mobile-btn.loading {
            position: relative;
            color: transparent;
        }
        
        .mobile-btn.loading::after {
            content: '';
            position: absolute;
            width: 20px;
            height: 20px;
            border: 2px solid transparent;
            border-top: 2px solid currentColor;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* Mobile optimizations */
        @media (max-width: 768px) {
            .mobile-form {
                padding: 0.5rem;
            }
            
            .mobile-form-section {
                padding: 1rem;
            }
            
            .mobile-form-row {
                flex-direction: column;
                gap: 0;
            }
            
            .mobile-form-buttons {
                flex-direction: column;
            }
        }
        </style>
        """
        
        return format_html(css)


class MobileFormJavaScript:
    """
    JavaScript for mobile form functionality
    """
    
    @staticmethod
    def get_mobile_form_js():
        """
        Get JavaScript for mobile form functionality
        """
        js = """
        <script>
        class MobileForm {
            constructor(formElement) {
                this.form = formElement;
                this.init();
            }
            
            init() {
                this.setupFormValidation();
                this.setupAutoSave();
                this.setupImageUpload();
                this.setupFormSubmission();
            }
            
            setupFormValidation() {
                // Real-time validation
                this.form.querySelectorAll('.mobile-form-field').forEach(field => {
                    field.addEventListener('blur', () => this.validateField(field));
                    field.addEventListener('input', () => this.clearFieldError(field));
                });
            }
            
            validateField(field) {
                const value = field.value.trim();
                const isRequired = field.hasAttribute('required');
                
                // Clear previous error
                this.clearFieldError(field);
                
                // Check required fields
                if (isRequired && !value) {
                    this.showFieldError(field, 'This field is required');
                    return false;
                }
                
                // Custom validation based on field type
                if (field.type === 'email' && value) {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        this.showFieldError(field, 'Please enter a valid email address');
                        return false;
                    }
                }
                
                if (field.type === 'tel' && value) {
                    const phoneRegex = /^[0-9+\-\s()]+$/;
                    if (!phoneRegex.test(value)) {
                        this.showFieldError(field, 'Please enter a valid phone number');
                        return false;
                    }
                }
                
                return true;
            }
            
            showFieldError(field, message) {
                field.classList.add('error');
                
                const errorElement = document.createElement('div');
                errorElement.className = 'mobile-error-message';
                errorElement.textContent = message;
                
                field.parentNode.insertBefore(errorElement, field.nextSibling);
            }
            
            clearFieldError(field) {
                field.classList.remove('error');
                
                const errorElement = field.parentNode.querySelector('.mobile-error-message');
                if (errorElement) {
                    errorElement.remove();
                }
            }
            
            setupAutoSave() {
                // Auto-save form data to localStorage
                this.form.querySelectorAll('.mobile-form-field').forEach(field => {
                    field.addEventListener('input', () => {
                        this.saveFormData();
                    });
                });
                
                // Load saved data on page load
                this.loadFormData();
            }
            
            saveFormData() {
                const formData = new FormData(this.form);
                const data = {};
                
                for (let [key, value] of formData.entries()) {
                    data[key] = value;
                }
                
                localStorage.setItem('mobile_form_data', JSON.stringify(data));
            }
            
            loadFormData() {
                const savedData = localStorage.getItem('mobile_form_data');
                if (savedData) {
                    const data = JSON.parse(savedData);
                    
                    Object.keys(data).forEach(key => {
                        const field = this.form.querySelector(`[name="${key}"]`);
                        if (field && !field.value) {
                            field.value = data[key];
                        }
                    });
                }
            }
            
            setupImageUpload() {
                const imageInputs = this.form.querySelectorAll('input[type="file"]');
                
                imageInputs.forEach(input => {
                    input.addEventListener('change', (e) => {
                        this.handleImageUpload(e.target);
                    });
                });
            }
            
            handleImageUpload(input) {
                const file = input.files[0];
                if (!file) return;
                
                // Show preview
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.showImagePreview(input, e.target.result);
                };
                reader.readAsDataURL(file);
            }
            
            showImagePreview(input, src) {
                // Remove existing preview
                const existingPreview = input.parentNode.querySelector('.image-preview');
                if (existingPreview) {
                    existingPreview.remove();
                }
                
                // Create preview
                const preview = document.createElement('div');
                preview.className = 'image-preview';
                preview.innerHTML = `
                    <img src="${src}" alt="Preview" style="max-width: 200px; max-height: 200px; border-radius: 8px;">
                    <button type="button" class="remove-image" onclick="this.parentNode.remove()">Remove</button>
                `;
                
                input.parentNode.appendChild(preview);
            }
            
            setupFormSubmission() {
                this.form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.handleFormSubmission();
                });
            }
            
            async handleFormSubmission() {
                // Validate all fields
                const fields = this.form.querySelectorAll('.mobile-form-field');
                let isValid = true;
                
                fields.forEach(field => {
                    if (!this.validateField(field)) {
                        isValid = false;
                    }
                });
                
                if (!isValid) {
                    this.showFormError('Please correct the errors above');
                    return;
                }
                
                // Show loading state
                this.setLoadingState(true);
                
                try {
                    const formData = new FormData(this.form);
                    const response = await fetch(this.form.action, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                        }
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        this.showFormSuccess(result.message || 'Form submitted successfully');
                        this.clearFormData();
                    } else {
                        this.showFormError(result.message || 'Form submission failed');
                    }
                } catch (error) {
                    console.error('Form submission error:', error);
                    this.showFormError('Network error. Please try again.');
                } finally {
                    this.setLoadingState(false);
                }
            }
            
            setLoadingState(loading) {
                this.form.classList.toggle('loading', loading);
                
                const submitBtn = this.form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.classList.toggle('loading', loading);
                    submitBtn.disabled = loading;
                }
            }
            
            showFormSuccess(message) {
                this.showFormMessage(message, 'success');
            }
            
            showFormError(message) {
                this.showFormMessage(message, 'error');
            }
            
            showFormMessage(message, type) {
                // Remove existing messages
                const existingMessages = this.form.querySelectorAll('.form-message');
                existingMessages.forEach(msg => msg.remove());
                
                // Create message
                const messageElement = document.createElement('div');
                messageElement.className = `form-message form-message-${type}`;
                messageElement.textContent = message;
                
                this.form.insertBefore(messageElement, this.form.firstChild);
                
                // Auto-remove after 5 seconds
                setTimeout(() => {
                    messageElement.remove();
                }, 5000);
            }
            
            clearFormData() {
                localStorage.removeItem('mobile_form_data');
            }
        }
        
        // Initialize forms when DOM is ready
        document.addEventListener('DOMContentLoaded', () => {
            document.querySelectorAll('.mobile-form').forEach(form => {
                new MobileForm(form);
            });
        });
        </script>
        """
        
        return format_html(js) 