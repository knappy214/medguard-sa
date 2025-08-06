# MedGuard SA Forms Implementation

This directory contains the Wagtail 7.0.2 form pages implementation for MedGuard SA, providing a comprehensive form system for medication management and healthcare interactions.

## Overview

The forms system implements 8 specialized Wagtail form pages, each leveraging Wagtail 7.0.2's enhanced features for form building, validation, and processing. All forms integrate with existing Django models for seamless data processing and workflow management.

## Implemented Forms

### 1. PrescriptionSubmissionFormPage
- **Feature**: Enhanced form builder with dynamic field configuration
- **Purpose**: Allow patients to submit prescription details for processing
- **Integration**: `medications.models.EnhancedPrescription`, `medications.models.PrescriptionWorkflow`
- **Key Features**:
  - Auto-approval for eligible prescriptions
  - Email notifications to patients and administrators
  - Integration with prescription workflow system

### 2. MedicationReminderFormPage
- **Feature**: Improved form validation with conditional logic
- **Purpose**: Set up medication reminders with various frequencies and types
- **Integration**: `medguard_notifications.models.MedicationReminder`
- **Key Features**:
  - Multiple reminder types (medication, appointment, refill)
  - Frequency validation and compatibility checking
  - Test notification functionality

### 3. PatientRegistrationFormPage
- **Feature**: New form field types and enhanced user experience
- **Purpose**: Register new patients with comprehensive medical information
- **Integration**: `users.models.User`, `users.models.EmailVerification`
- **Key Features**:
  - Email verification workflow
  - Medical history collection
  - Emergency contact information
  - Welcome email notifications

### 4. PharmacyContactFormPage
- **Feature**: Enhanced email integration with multi-recipient support
- **Purpose**: Contact form for pharmacies with priority-based routing
- **Integration**: `medguard_notifications.models.ContactInquiry`
- **Key Features**:
  - Priority-based email routing
  - Auto-reply functionality
  - Department-specific notifications
  - Response time estimation

### 5. MedicationFeedbackFormPage
- **Feature**: Advanced form submission handling with sentiment analysis
- **Purpose**: Collect medication feedback and ratings from patients
- **Integration**: `medguard_notifications.models.MedicationFeedback`
- **Key Features**:
  - Multi-dimensional rating system
  - Sentiment analysis and categorization
  - Negative feedback escalation
  - Feedback analytics

### 6. PrescriptionRenewalFormPage
- **Feature**: Conditional form logic with dynamic field visibility
- **Purpose**: Process prescription renewal requests with compliance checking
- **Integration**: `medications.models.PrescriptionRenewal`, `medications.models.EnhancedPrescription`
- **Key Features**:
  - Conditional field display based on renewal type
  - Auto-approval for compliant patients
  - Compliance history evaluation
  - Renewal approval workflow

### 7. MedicationTransferFormPage
- **Feature**: File upload improvements with security scanning
- **Purpose**: Facilitate medication transfers between pharmacies
- **Integration**: `medguard_notifications.models.MedicationTransfer`, `medguard_notifications.models.TransferDocument`
- **Key Features**:
  - Secure file upload handling
  - Document type validation
  - Virus scanning integration
  - Transfer workflow management

### 8. EmergencyContactFormPage
- **Feature**: Enhanced form security with rate limiting and CAPTCHA
- **Purpose**: Emergency contact form with priority-based escalation
- **Integration**: `medguard_notifications.models.EmergencyContact`
- **Key Features**:
  - Rate limiting to prevent abuse
  - Priority-based emergency escalation
  - Multi-channel notifications (email, SMS)
  - Emergency response coordination

## File Structure

```
forms/
├── __init__.py                 # Package initialization
├── wagtail_forms.py           # Main form page implementations
├── security.py                # File upload security utilities
└── README.md                  # This documentation

templates/forms/
├── base_form.html             # Base form template
├── prescription_submission_form.html  # Specific form template
└── email/                     # Email templates
    ├── prescription_submission.html
    ├── medication_reminder.html
    ├── patient_registration.html
    ├── pharmacy_contact.html
    ├── medication_feedback.html
    ├── prescription_renewal.html
    ├── medication_transfer.html
    └── emergency_contact.html
```

## Key Features

### Wagtail 7.0.2 Integration
- Enhanced form builder interface
- Improved form validation
- New form field types
- Advanced form submission handling
- Conditional form logic
- File upload improvements
- Enhanced form security

### Security Features
- File type validation and virus scanning
- Rate limiting for form submissions
- CSRF protection (inherent to Django)
- Input sanitization and validation
- Secure file upload handling
- File encryption for sensitive documents

### Email Integration
- Multi-recipient notifications
- Priority-based email routing
- Auto-reply functionality
- Template-based email generation
- HTML email templates with responsive design
- Internationalization support (en-ZA, af-ZA)

### Data Processing
- Integration with existing Django models
- Workflow management
- Data validation and sanitization
- Audit logging
- HIPAA compliance considerations

## Configuration

### Django Settings
The forms app has been added to `INSTALLED_APPS` in `medguard_backend/settings/base.py`:

```python
LOCAL_APPS = [
    # ... other apps ...
    'forms',  # Wagtail 7.0.2 form pages
]
```

### Email Configuration
Email settings are configured in `medguard_backend/settings/environment.py`:
- Development: Console backend
- Staging/Production: SMTP with post_office backend

### File Upload Security
File upload security is configured in `forms/security.py`:
- Allowed file types per document category
- Maximum file sizes
- Virus scanning integration
- File encryption capabilities

## Usage

### Creating Form Pages
1. Access the Wagtail admin interface
2. Navigate to Pages
3. Create a new page using one of the form page types
4. Configure form fields and settings
5. Publish the form page

### Form Templates
Each form has a corresponding template in `templates/forms/`:
- `base_form.html`: Base template with common styling and functionality
- Specific form templates extend the base template
- Responsive design with Bootstrap 5
- Form validation and auto-save functionality

### Email Templates
Email templates are located in `templates/forms/email/`:
- HTML email templates with responsive design
- Support for both admin and user notifications
- Internationalization support
- Professional styling with MedGuard SA branding

## Security Considerations

### File Upload Security
- File type validation using MIME type detection
- Virus scanning with ClamAV or Windows Defender
- File size limits per document type
- Dangerous file extension blocking
- Malicious content pattern detection
- File encryption for sensitive documents

### Form Security
- CSRF protection (Django built-in)
- Rate limiting for form submissions
- Input validation and sanitization
- Secure file handling
- Audit logging for compliance

### Data Protection
- HIPAA-compliant data handling
- Secure email transmission
- Encrypted file storage
- Access control and authentication
- Audit trail maintenance

## Dependencies

### Required Python Packages
- `wagtail>=7.0.2` - Wagtail CMS
- `django>=4.2` - Django framework
- `python-magic` - File type detection
- `cryptography` - File encryption (optional)
- `clamd` - Virus scanning (optional)

### Optional Dependencies
- `post_office` - Enhanced email handling
- `django-cors-headers` - CORS support
- `django-filter` - Advanced filtering

## Testing

### Form Validation
- Client-side validation with JavaScript
- Server-side validation with Django forms
- File upload validation
- Security validation

### Email Testing
- Template rendering tests
- Email delivery tests
- Internationalization tests

### Security Testing
- File upload security tests
- Rate limiting tests
- CSRF protection tests
- Input validation tests

## Deployment

### Production Considerations
1. Configure proper email settings
2. Set up virus scanning (ClamAV recommended)
3. Configure file encryption keys
4. Set up monitoring and logging
5. Configure rate limiting
6. Test all form workflows

### Environment Variables
```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@medguard-sa.com

# Security Configuration
FILE_ENCRYPTION_KEY=your-encryption-key
CLAMAV_ENABLED=True

# Rate Limiting
FORM_RATE_LIMIT=10  # submissions per hour
```

## Support

For issues or questions regarding the forms implementation:
1. Check the Django and Wagtail documentation
2. Review the security configuration
3. Test with the provided templates
4. Contact the development team

## Future Enhancements

### Planned Features
- Advanced form analytics
- A/B testing for form optimization
- Integration with external healthcare systems
- Mobile app form support
- Advanced workflow automation
- Machine learning for form optimization

### Performance Optimizations
- Form caching strategies
- Database query optimization
- File upload performance improvements
- Email delivery optimization
- Template rendering optimization 