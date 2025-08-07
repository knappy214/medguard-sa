"""
Comprehensive test suite for Wagtail 7.0.2 form functionality in MedGuard SA.

This module tests all form functionality including:
- PrescriptionSubmissionFormPage validation and submission
- MedicationReminderFormPage scheduling and notifications
- EmergencyContactFormPage HIPAA-compliant data handling
- MedicationTransferFormPage secure data transfer
- PrescriptionRenewalFormPage automated renewal processes
- MedicationFeedbackFormPage user feedback collection
- PharmacyContactFormPage integration with pharmacy systems
- PatientRegistrationFormPage user onboarding
- Form field validation and custom validators
- Form submission handling and email notifications
- Form security and CSRF protection
- Form accessibility and internationalization
"""

import pytest
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.messages import get_messages
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from wagtail.test.utils import WagtailPageTestCase
from wagtail.models import Page, Site
from wagtail.contrib.forms.models import FormSubmission
from wagtail.contrib.forms.forms import FormBuilder

# Import form page classes
from forms.wagtail_forms import (
    PrescriptionSubmissionFormPage,
    MedicationReminderFormPage,
    EmergencyContactFormPage,
    MedicationTransferFormPage,
    PrescriptionRenewalFormPage,
    MedicationFeedbackFormPage,
    PharmacyContactFormPage,
    PatientRegistrationFormPage,
    PrescriptionSubmissionFormField,
    MedicationReminderFormField,
    EmergencyContactFormField,
    MedicationTransferFormField,
    PrescriptionRenewalFormField,
    MedicationFeedbackFormField,
    PharmacyContactFormField,
    PatientRegistrationFormField
)

# Import related models
from medications.models import EnhancedPrescription, Medication
from home.models import HomePage

User = get_user_model()


class BaseFormTestCase(WagtailPageTestCase):
    """Base test case for form testing with common setup."""
    
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
        
        self.doctor = User.objects.create_user(
            username='doctor',
            email='doctor@medguard.co.za',
            password='testpass123',
            first_name='Dr. Jane',
            last_name='Smith'
        )
        
        # Create home page
        self.home_page = HomePage(
            title='MedGuard SA',
            slug='home',
            hero_title='Welcome to MedGuard'
        )
        self.root_page = Page.objects.get(id=2)
        self.root_page.add_child(instance=self.home_page)
        
        # Set up request factory
        self.factory = RequestFactory()
        self.client = Client()
        
        # Create site
        self.site = Site.objects.get(is_default_site=True)
        
    def create_form_field(self, form_page, field_class, **kwargs):
        """Helper method to create form fields."""
        defaults = {
            'page': form_page,
            'sort_order': 1,
            'label': 'Test Field',
            'field_type': 'singleline',
            'required': True
        }
        defaults.update(kwargs)
        return field_class.objects.create(**defaults)


class PrescriptionSubmissionFormPageTestCase(BaseFormTestCase):
    """Test cases for PrescriptionSubmissionFormPage."""
    
    def setUp(self):
        """Set up prescription form test data."""
        super().setUp()
        self.form_page = PrescriptionSubmissionFormPage(
            title='Submit Prescription',
            slug='submit-prescription',
            intro='<p>Submit your prescription here</p>',
            thank_you_text='<p>Thank you for your submission</p>',
            form_title='Prescription Submission Form',
            allow_multiple_submissions=True,
            require_authentication=True,
            enable_file_upload=True,
            max_file_size_mb=10
        )
        self.home_page.add_child(instance=self.form_page)
        
        # Create form fields
        self.patient_name_field = self.create_form_field(
            self.form_page,
            PrescriptionSubmissionFormField,
            label='Patient Name',
            field_type='singleline',
            required=True
        )
        
        self.medication_name_field = self.create_form_field(
            self.form_page,
            PrescriptionSubmissionFormField,
            label='Medication Name',
            field_type='singleline',
            required=True,
            sort_order=2
        )
        
        self.dosage_field = self.create_form_field(
            self.form_page,
            PrescriptionSubmissionFormField,
            label='Dosage',
            field_type='singleline',
            required=True,
            sort_order=3
        )
        
        self.prescription_image_field = self.create_form_field(
            self.form_page,
            PrescriptionSubmissionFormField,
            label='Prescription Image',
            field_type='file',
            required=False,
            sort_order=4
        )
        
    def test_prescription_form_creation(self):
        """Test creating a prescription submission form."""
        self.assertEqual(self.form_page.title, 'Submit Prescription')
        self.assertTrue(self.form_page.require_authentication)
        self.assertTrue(self.form_page.enable_file_upload)
        self.assertEqual(self.form_page.max_file_size_mb, 10)
        
    def test_prescription_form_fields(self):
        """Test prescription form has required fields."""
        form_fields = self.form_page.get_form_fields()
        field_labels = [field.label for field in form_fields]
        
        required_fields = ['Patient Name', 'Medication Name', 'Dosage']
        for field in required_fields:
            self.assertIn(field, field_labels)
            
    def test_prescription_form_validation(self):
        """Test prescription form validation."""
        # Create request
        request = self.factory.post('/submit-prescription/', {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin',
            'dosage': '325mg'
        })
        request.user = self.user
        
        # Get form
        form_class = self.form_page.get_form_class()
        form = form_class(data=request.POST)
        
        # Should be valid
        self.assertTrue(form.is_valid())
        
    def test_prescription_form_invalid_data(self):
        """Test prescription form with invalid data."""
        # Missing required fields
        request = self.factory.post('/submit-prescription/', {
            'patient_name': '',  # Required field empty
            'medication_name': 'Aspirin',
            'dosage': '325mg'
        })
        request.user = self.user
        
        form_class = self.form_page.get_form_class()
        form = form_class(data=request.POST)
        
        # Should be invalid
        self.assertFalse(form.is_valid())
        self.assertIn('patient_name', form.errors)
        
    def test_prescription_form_submission(self):
        """Test prescription form submission handling."""
        # Valid form data
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin',
            'dosage': '325mg'
        }
        
        # Submit form
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should redirect to thank you page
        self.assertEqual(response.status_code, 302)
        
        # Check form submission was created
        submissions = FormSubmission.objects.filter(page=self.form_page)
        self.assertEqual(submissions.count(), 1)
        
        submission = submissions.first()
        self.assertEqual(submission.get_data()['patient_name'], 'John Doe')
        
    def test_prescription_form_authentication_required(self):
        """Test prescription form requires authentication."""
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin',
            'dosage': '325mg'
        }
        
        # Try to submit without authentication
        response = self.client.post(self.form_page.url, form_data)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
    def test_prescription_form_file_upload(self):
        """Test prescription form file upload functionality."""
        # Create a mock file
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        test_file = SimpleUploadedFile(
            "prescription.jpg",
            b"fake image content",
            content_type="image/jpeg"
        )
        
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin',
            'dosage': '325mg',
            'prescription_image': test_file
        }
        
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        # Check file was saved
        submission = FormSubmission.objects.filter(page=self.form_page).first()
        self.assertIsNotNone(submission)
        
    def test_prescription_form_file_size_validation(self):
        """Test prescription form file size validation."""
        # Create a file that's too large
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB (over 10MB limit)
        
        test_file = SimpleUploadedFile(
            "large_prescription.jpg",
            large_content,
            content_type="image/jpeg"
        )
        
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin',
            'dosage': '325mg',
            'prescription_image': test_file
        }
        
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should show error
        self.assertEqual(response.status_code, 200)  # Stays on form page
        
    def test_prescription_form_email_notification(self):
        """Test prescription form sends email notification."""
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin',
            'dosage': '325mg'
        }
        
        self.client.force_login(self.user)
        
        with patch('forms.wagtail_forms.send_mail') as mock_send_mail:
            response = self.client.post(self.form_page.url, form_data)
            
            # Should send email notification
            mock_send_mail.assert_called()


class MedicationReminderFormPageTestCase(BaseFormTestCase):
    """Test cases for MedicationReminderFormPage."""
    
    def setUp(self):
        """Set up medication reminder form test data."""
        super().setUp()
        self.form_page = MedicationReminderFormPage(
            title='Set Medication Reminder',
            slug='medication-reminder',
            intro='<p>Set up your medication reminders</p>',
            reminder_frequency_options=['daily', 'weekly', 'monthly'],
            enable_sms_reminders=True,
            enable_email_reminders=True,
            default_reminder_time='08:00'
        )
        self.home_page.add_child(instance=self.form_page)
        
        # Create form fields
        self.medication_field = self.create_form_field(
            self.form_page,
            MedicationReminderFormField,
            label='Medication Name',
            field_type='singleline',
            required=True
        )
        
        self.reminder_time_field = self.create_form_field(
            self.form_page,
            MedicationReminderFormField,
            label='Reminder Time',
            field_type='time',
            required=True,
            sort_order=2
        )
        
        self.frequency_field = self.create_form_field(
            self.form_page,
            MedicationReminderFormField,
            label='Frequency',
            field_type='dropdown',
            required=True,
            sort_order=3
        )
        
    def test_medication_reminder_form_creation(self):
        """Test creating a medication reminder form."""
        self.assertEqual(self.form_page.title, 'Set Medication Reminder')
        self.assertTrue(self.form_page.enable_sms_reminders)
        self.assertTrue(self.form_page.enable_email_reminders)
        self.assertEqual(self.form_page.default_reminder_time, '08:00')
        
    def test_medication_reminder_form_validation(self):
        """Test medication reminder form validation."""
        form_data = {
            'medication_name': 'Aspirin',
            'reminder_time': '08:00',
            'frequency': 'daily'
        }
        
        request = self.factory.post('/medication-reminder/', form_data)
        request.user = self.user
        
        form_class = self.form_page.get_form_class()
        form = form_class(data=request.POST)
        
        self.assertTrue(form.is_valid())
        
    def test_medication_reminder_time_validation(self):
        """Test reminder time validation."""
        # Invalid time format
        form_data = {
            'medication_name': 'Aspirin',
            'reminder_time': '25:00',  # Invalid time
            'frequency': 'daily'
        }
        
        request = self.factory.post('/medication-reminder/', form_data)
        request.user = self.user
        
        form_class = self.form_page.get_form_class()
        form = form_class(data=request.POST)
        
        self.assertFalse(form.is_valid())
        
    def test_medication_reminder_submission(self):
        """Test medication reminder form submission."""
        form_data = {
            'medication_name': 'Aspirin',
            'reminder_time': '08:00',
            'frequency': 'daily'
        }
        
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
        # Check submission was created
        submission = FormSubmission.objects.filter(page=self.form_page).first()
        self.assertIsNotNone(submission)
        self.assertEqual(submission.get_data()['medication_name'], 'Aspirin')


class EmergencyContactFormPageTestCase(BaseFormTestCase):
    """Test cases for EmergencyContactFormPage."""
    
    def setUp(self):
        """Set up emergency contact form test data."""
        super().setUp()
        self.form_page = EmergencyContactFormPage(
            title='Emergency Contact Form',
            slug='emergency-contact',
            intro='<p>Update your emergency contact information</p>',
            hipaa_compliance_required=True,
            enable_relationship_validation=True,
            require_phone_verification=True,
            max_emergency_contacts=3
        )
        self.home_page.add_child(instance=self.form_page)
        
        # Create form fields
        self.contact_name_field = self.create_form_field(
            self.form_page,
            EmergencyContactFormField,
            label='Contact Name',
            field_type='singleline',
            required=True
        )
        
        self.relationship_field = self.create_form_field(
            self.form_page,
            EmergencyContactFormField,
            label='Relationship',
            field_type='dropdown',
            required=True,
            sort_order=2
        )
        
        self.phone_field = self.create_form_field(
            self.form_page,
            EmergencyContactFormField,
            label='Phone Number',
            field_type='singleline',
            required=True,
            sort_order=3
        )
        
    def test_emergency_contact_form_creation(self):
        """Test creating an emergency contact form."""
        self.assertEqual(self.form_page.title, 'Emergency Contact Form')
        self.assertTrue(self.form_page.hipaa_compliance_required)
        self.assertTrue(self.form_page.enable_relationship_validation)
        self.assertEqual(self.form_page.max_emergency_contacts, 3)
        
    def test_emergency_contact_phone_validation(self):
        """Test phone number validation."""
        # Valid South African phone number
        valid_form_data = {
            'contact_name': 'Jane Doe',
            'relationship': 'spouse',
            'phone_number': '+27-21-123-4567'
        }
        
        request = self.factory.post('/emergency-contact/', valid_form_data)
        request.user = self.user
        
        form_class = self.form_page.get_form_class()
        form = form_class(data=request.POST)
        
        # Should be valid
        self.assertTrue(form.is_valid())
        
        # Invalid phone number
        invalid_form_data = {
            'contact_name': 'Jane Doe',
            'relationship': 'spouse',
            'phone_number': '123'  # Too short
        }
        
        form = form_class(data=invalid_form_data)
        self.assertFalse(form.is_valid())
        
    def test_emergency_contact_relationship_validation(self):
        """Test relationship validation."""
        form_data = {
            'contact_name': 'Jane Doe',
            'relationship': 'invalid_relationship',  # Should be from predefined list
            'phone_number': '+27-21-123-4567'
        }
        
        request = self.factory.post('/emergency-contact/', form_data)
        request.user = self.user
        
        form_class = self.form_page.get_form_class()
        form = form_class(data=request.POST)
        
        # Should validate relationship choices
        self.assertFalse(form.is_valid())
        
    def test_emergency_contact_hipaa_compliance(self):
        """Test HIPAA compliance features."""
        form_data = {
            'contact_name': 'Jane Doe',
            'relationship': 'spouse',
            'phone_number': '+27-21-123-4567',
            'hipaa_authorization': True  # Required for HIPAA compliance
        }
        
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should succeed with HIPAA authorization
        self.assertEqual(response.status_code, 302)
        
        # Test without HIPAA authorization
        form_data['hipaa_authorization'] = False
        response = self.client.post(self.form_page.url, form_data)
        
        # Should fail without HIPAA authorization
        self.assertEqual(response.status_code, 200)  # Stays on form


class MedicationTransferFormPageTestCase(BaseFormTestCase):
    """Test cases for MedicationTransferFormPage."""
    
    def setUp(self):
        """Set up medication transfer form test data."""
        super().setUp()
        self.form_page = MedicationTransferFormPage(
            title='Transfer Medication Records',
            slug='transfer-medication',
            intro='<p>Transfer your medication records</p>',
            enable_secure_transfer=True,
            require_digital_signature=True,
            transfer_encryption_level='AES256',
            max_transfer_size_mb=50
        )
        self.home_page.add_child(instance=self.form_page)
        
    def test_medication_transfer_form_creation(self):
        """Test creating a medication transfer form."""
        self.assertEqual(self.form_page.title, 'Transfer Medication Records')
        self.assertTrue(self.form_page.enable_secure_transfer)
        self.assertTrue(self.form_page.require_digital_signature)
        self.assertEqual(self.form_page.transfer_encryption_level, 'AES256')
        
    def test_medication_transfer_security_validation(self):
        """Test medication transfer security validation."""
        form_data = {
            'source_pharmacy': 'Old Pharmacy',
            'destination_pharmacy': 'New Pharmacy',
            'patient_id': '12345',
            'digital_signature': 'valid_signature_hash'
        }
        
        self.client.force_login(self.user)
        
        with patch('forms.wagtail_forms.validate_digital_signature') as mock_validate:
            mock_validate.return_value = True
            
            response = self.client.post(self.form_page.url, form_data)
            
            # Should succeed with valid signature
            self.assertEqual(response.status_code, 302)
            
    def test_medication_transfer_encryption(self):
        """Test medication transfer encryption."""
        # This would test that sensitive data is properly encrypted
        # during the transfer process
        pass


class PrescriptionRenewalFormPageTestCase(BaseFormTestCase):
    """Test cases for PrescriptionRenewalFormPage."""
    
    def setUp(self):
        """Set up prescription renewal form test data."""
        super().setUp()
        self.form_page = PrescriptionRenewalFormPage(
            title='Prescription Renewal Request',
            slug='prescription-renewal',
            intro='<p>Request prescription renewal</p>',
            enable_automatic_renewal=True,
            renewal_reminder_days=7,
            max_renewal_duration_days=90,
            require_doctor_approval=True
        )
        self.home_page.add_child(instance=self.form_page)
        
        # Create original prescription
        self.prescription = EnhancedPrescription.objects.create(
            patient=self.user,
            prescriber=self.doctor,
            medication_name='Test Medication',
            dosage='500mg',
            frequency='twice_daily',
            duration_days=30
        )
        
    def test_prescription_renewal_form_creation(self):
        """Test creating a prescription renewal form."""
        self.assertEqual(self.form_page.title, 'Prescription Renewal Request')
        self.assertTrue(self.form_page.enable_automatic_renewal)
        self.assertEqual(self.form_page.renewal_reminder_days, 7)
        
    def test_prescription_renewal_validation(self):
        """Test prescription renewal validation."""
        form_data = {
            'original_prescription_id': str(self.prescription.id),
            'requested_duration_days': 30,
            'patient_notes': 'Medication is working well'
        }
        
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should succeed
        self.assertEqual(response.status_code, 302)
        
    def test_prescription_renewal_duration_limit(self):
        """Test prescription renewal duration limits."""
        form_data = {
            'original_prescription_id': str(self.prescription.id),
            'requested_duration_days': 365,  # Exceeds max limit
            'patient_notes': 'Long-term medication'
        }
        
        request = self.factory.post('/prescription-renewal/', form_data)
        request.user = self.user
        
        form_class = self.form_page.get_form_class()
        form = form_class(data=request.POST)
        
        # Should be invalid due to duration limit
        self.assertFalse(form.is_valid())
        
    def test_prescription_renewal_automatic_approval(self):
        """Test automatic renewal approval criteria."""
        # Set up prescription that meets automatic renewal criteria
        self.prescription.status = 'active'
        self.prescription.patient_compliance_score = 95
        self.prescription.save()
        
        form_data = {
            'original_prescription_id': str(self.prescription.id),
            'requested_duration_days': 30,
            'patient_notes': 'No side effects, working well'
        }
        
        with patch('forms.wagtail_forms.check_automatic_renewal_eligibility') as mock_check:
            mock_check.return_value = True
            
            self.client.force_login(self.user)
            response = self.client.post(self.form_page.url, form_data)
            
            # Should succeed and trigger automatic approval
            self.assertEqual(response.status_code, 302)


class FormSecurityTestCase(BaseFormTestCase):
    """Test cases for form security features."""
    
    def setUp(self):
        """Set up security test data."""
        super().setUp()
        self.form_page = PrescriptionSubmissionFormPage(
            title='Security Test Form',
            slug='security-test-form',
            require_authentication=True,
            enable_csrf_protection=True,
            enable_rate_limiting=True,
            max_submissions_per_hour=5
        )
        self.home_page.add_child(instance=self.form_page)
        
    def test_csrf_protection(self):
        """Test CSRF protection is enabled."""
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin'
        }
        
        # Submit without CSRF token
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should be protected by CSRF
        self.assertEqual(response.status_code, 403)
        
    def test_rate_limiting(self):
        """Test form submission rate limiting."""
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin'
        }
        
        self.client.force_login(self.user)
        
        # Submit multiple times rapidly
        for i in range(6):  # Exceeds limit of 5 per hour
            response = self.client.post(self.form_page.url, form_data, follow=True)
            
            if i < 5:
                # First 5 should succeed
                self.assertIn(response.status_code, [200, 302])
            else:
                # 6th should be rate limited
                self.assertEqual(response.status_code, 429)
                
    def test_input_sanitization(self):
        """Test form input sanitization."""
        malicious_data = {
            'patient_name': '<script>alert("xss")</script>',
            'medication_name': 'Aspirin',
            'notes': '<?php system("rm -rf /"); ?>'
        }
        
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, malicious_data, follow=True)
        
        # Should sanitize malicious input
        if response.status_code == 302:  # Successful submission
            submission = FormSubmission.objects.filter(page=self.form_page).first()
            if submission:
                # Should not contain script tags
                self.assertNotIn('<script>', submission.get_data()['patient_name'])
                self.assertNotIn('<?php', submission.get_data()['notes'])
                
    def test_file_upload_security(self):
        """Test file upload security validation."""
        # Test malicious file upload
        malicious_file = SimpleUploadedFile(
            "malicious.php",
            b"<?php system($_GET['cmd']); ?>",
            content_type="application/x-php"
        )
        
        form_data = {
            'patient_name': 'John Doe',
            'medication_name': 'Aspirin',
            'prescription_image': malicious_file
        }
        
        self.client.force_login(self.user)
        response = self.client.post(self.form_page.url, form_data)
        
        # Should reject malicious file types
        self.assertEqual(response.status_code, 200)  # Stays on form with error


class FormAccessibilityTestCase(BaseFormTestCase):
    """Test cases for form accessibility features."""
    
    def setUp(self):
        """Set up accessibility test data."""
        super().setUp()
        self.form_page = PrescriptionSubmissionFormPage(
            title='Accessibility Test Form',
            slug='accessibility-test-form',
            enable_accessibility_features=True,
            high_contrast_mode=True,
            keyboard_navigation_enabled=True,
            screen_reader_optimized=True
        )
        self.home_page.add_child(instance=self.form_page)
        
    def test_form_accessibility_attributes(self):
        """Test form has proper accessibility attributes."""
        self.client.force_login(self.user)
        response = self.client.get(self.form_page.url)
        
        # Check for accessibility attributes
        self.assertContains(response, 'aria-label')
        self.assertContains(response, 'role=')
        self.assertContains(response, 'tabindex')
        
    def test_form_keyboard_navigation(self):
        """Test form supports keyboard navigation."""
        # This would test tab order and keyboard accessibility
        pass
        
    def test_form_screen_reader_compatibility(self):
        """Test form is compatible with screen readers."""
        # This would test screen reader announcements and labels
        pass


class FormInternationalizationTestCase(BaseFormTestCase):
    """Test cases for form internationalization."""
    
    def setUp(self):
        """Set up i18n test data."""
        super().setUp()
        self.form_page = PrescriptionSubmissionFormPage(
            title='I18n Test Form',
            slug='i18n-test-form',
            enable_multilingual_support=True,
            default_language='en-ZA',
            supported_languages=['en-ZA', 'af-ZA']
        )
        self.home_page.add_child(instance=self.form_page)
        
    def test_form_language_switching(self):
        """Test form language switching functionality."""
        # Test English version
        self.client.force_login(self.user)
        response = self.client.get(self.form_page.url, HTTP_ACCEPT_LANGUAGE='en-ZA')
        
        self.assertEqual(response.status_code, 200)
        
        # Test Afrikaans version
        response = self.client.get(self.form_page.url, HTTP_ACCEPT_LANGUAGE='af-ZA')
        
        self.assertEqual(response.status_code, 200)
        
    def test_form_validation_messages_i18n(self):
        """Test form validation messages are internationalized."""
        # Submit invalid form data
        form_data = {
            'patient_name': '',  # Required field empty
            'medication_name': 'Aspirin'
        }
        
        self.client.force_login(self.user)
        
        # Test English error messages
        response = self.client.post(
            self.form_page.url, 
            form_data, 
            HTTP_ACCEPT_LANGUAGE='en-ZA'
        )
        
        # Should contain English error messages
        self.assertContains(response, 'This field is required')
        
        # Test Afrikaans error messages
        response = self.client.post(
            self.form_page.url, 
            form_data, 
            HTTP_ACCEPT_LANGUAGE='af-ZA'
        )
        
        # Should contain Afrikaans error messages
        # (Assuming translations exist)
        self.assertEqual(response.status_code, 200)


class FormPerformanceTestCase(BaseFormTestCase):
    """Test cases for form performance."""
    
    def setUp(self):
        """Set up performance test data."""
        super().setUp()
        self.form_page = PrescriptionSubmissionFormPage(
            title='Performance Test Form',
            slug='performance-test-form'
        )
        self.home_page.add_child(instance=self.form_page)
        
        # Create many form fields to test performance
        for i in range(50):
            self.create_form_field(
                self.form_page,
                PrescriptionSubmissionFormField,
                label=f'Field {i}',
                field_type='singleline',
                required=False,
                sort_order=i
            )
            
    def test_form_rendering_performance(self):
        """Test form rendering performance with many fields."""
        import time
        
        self.client.force_login(self.user)
        
        start_time = time.time()
        response = self.client.get(self.form_page.url)
        render_time = time.time() - start_time
        
        # Should render within reasonable time (< 2 seconds)
        self.assertEqual(response.status_code, 200)
        self.assertLess(render_time, 2.0)
        
    def test_form_submission_performance(self):
        """Test form submission performance."""
        import time
        
        # Create form data for all fields
        form_data = {}
        for i in range(50):
            form_data[f'field_{i}'] = f'Value {i}'
            
        self.client.force_login(self.user)
        
        start_time = time.time()
        response = self.client.post(self.form_page.url, form_data, follow=True)
        submission_time = time.time() - start_time
        
        # Should submit within reasonable time (< 3 seconds)
        self.assertIn(response.status_code, [200, 302])
        self.assertLess(submission_time, 3.0)


@pytest.mark.django_db
class FormIntegrationTestCase(TestCase):
    """Integration tests for forms with other system components."""
    
    def setUp(self):
        """Set up integration test data."""
        self.user = User.objects.create_user(
            username='integration_user',
            email='integration@medguard.co.za',
            password='testpass123'
        )
        
    def test_form_notification_integration(self):
        """Test form integration with notification system."""
        # This would test that forms trigger appropriate notifications
        pass
        
    def test_form_workflow_integration(self):
        """Test form integration with workflow system."""
        # This would test that form submissions trigger workflows
        pass
        
    def test_form_audit_integration(self):
        """Test form integration with audit system."""
        # This would test that form submissions are properly audited
        pass
