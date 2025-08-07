# MedGuard SA - Healthcare Quality Assurance Module

This module provides comprehensive quality assurance testing for healthcare applications built with Wagtail 7.0.2, specifically designed for medical content management and HIPAA compliance.

## Features

### 🏥 Healthcare-Focused Testing
- **Medical Content Validation**: Validates medical terminology, drug information, dosage accuracy, and clinical guidelines
- **HIPAA Compliance Testing**: Automated security testing for healthcare data protection
- **Healthcare Accessibility**: WCAG 2.1 AA compliance with healthcare-specific accessibility requirements
- **Medical SEO Optimization**: SEO testing tailored for healthcare and medication content

### 🔒 Security & Compliance
- **HIPAA Security Testing**: Encryption, access controls, audit logging, and PHI protection
- **Medical Data Protection**: Tests for proper handling of Protected Health Information (PHI)
- **Healthcare Authentication**: Role-based access control testing for medical workflows
- **Security Headers Validation**: Comprehensive security header testing

### 🚀 Performance & Compatibility
- **Healthcare Load Testing**: Performance testing under medical workflow scenarios
- **Cross-Browser Testing**: Compatibility testing across all major browsers and devices
- **Mobile Responsiveness**: Healthcare-specific mobile interface testing
- **Prescription Form Testing**: Specialized testing for medical form workflows

### 🌍 Multilingual Support
- **Translation Testing**: Validates en-ZA and af-ZA healthcare translations
- **Medical Terminology**: Ensures proper translation of medical terms
- **Localization Compliance**: Tests for proper healthcare content localization

## Installation

1. Install required dependencies:
```bash
pip install selenium beautifulsoup4 requests psutil
```

2. For browser testing, install browser drivers:
```bash
# Chrome driver
wget https://chromedriver.chromium.org/downloads

# Firefox driver  
wget https://github.com/mozilla/geckodriver/releases
```

## Usage

### Basic Usage

```python
from medguard_backend.qa.wagtail_quality_assurance import WagtailHealthcareQualityAssurance

# Initialize the QA suite
qa_suite = WagtailHealthcareQualityAssurance()

# Run comprehensive testing
results = qa_suite.run_comprehensive_qa_suite(
    page_urls=['https://your-site.com/medications/', 'https://your-site.com/prescriptions/'],
    content_samples=['Sample medical content for validation']
)

print(f"Overall Compliance Score: {results['overall_compliance_score']}/100")
print(f"HIPAA Compliant: {results['compliance_summary']['hipaa_compliant']}")
print(f"Production Ready: {results['compliance_summary']['ready_for_production']}")
```

### Individual Testing Components

#### 1. Accessibility Testing
```python
from medguard_backend.qa.wagtail_quality_assurance import HealthcareAccessibilityTester

tester = HealthcareAccessibilityTester()
tester.setup_accessibility_testing()

results = tester.test_healthcare_page_accessibility('https://your-site.com/page/')
print(f"WCAG Compliance: {results['wcag_compliance']}")
print(f"Healthcare Compliance: {results['healthcare_compliance']}")

tester.cleanup()
```

#### 2. HIPAA Security Testing
```python
from medguard_backend.qa.wagtail_quality_assurance import HIPAASecurityTester

security_tester = HIPAASecurityTester()
results = security_tester.test_hipaa_security_compliance('https://your-site.com/patient-data/')

print(f"HIPAA Compliance Score: {results['hipaa_compliance_score']}/100")
print(f"Security Violations: {len(results['security_violations'])}")
```

#### 3. Medical Content Validation
```python
from medguard_backend.qa.wagtail_quality_assurance import MedicalContentValidator

validator = MedicalContentValidator()
content = "Take aspirin 325mg twice daily. Consult your healthcare provider."

results = validator.validate_medical_content(content, 'medication')
print(f"Medical Accuracy Score: {results['accuracy_score']}/100")
print(f"Compliance Score: {results['compliance_score']}/100")
```

#### 4. Performance Testing
```python
from medguard_backend.qa.wagtail_quality_assurance import HealthcarePerformanceTester

performance_tester = HealthcarePerformanceTester()
results = performance_tester.test_healthcare_page_performance(
    'https://your-site.com/critical-page/', 
    is_critical=True
)

print(f"Performance Score: {results['performance_score']}/100")
print(f"Page Load Time: {results['metrics']['page_load_time_ms']}ms")
```

#### 5. Cross-Browser Testing
```python
from medguard_backend.qa.wagtail_quality_assurance import CrossBrowserTester

browser_tester = CrossBrowserTester()
results = browser_tester.test_cross_browser_compatibility([
    'https://your-site.com/',
    'https://your-site.com/medications/'
])

print(f"Compatibility Score: {results['overall_compatibility_score']}/100")
```

### Django Integration

#### Test Cases
```python
# In your Django tests
from medguard_backend.qa.wagtail_quality_assurance import HealthcareQualityAssuranceTestCase

class MyHealthcareTests(HealthcareQualityAssuranceTestCase):
    def test_medication_pages(self):
        # Your custom healthcare tests
        pass
```

#### Management Command
```python
# Create management command: management/commands/run_healthcare_qa.py
from django.core.management.base import BaseCommand
from medguard_backend.qa.wagtail_quality_assurance import HealthcareQualityAssuranceManagementCommand

class Command(BaseCommand, HealthcareQualityAssuranceManagementCommand):
    help = 'Run healthcare quality assurance tests'
    
    def add_arguments(self, parser):
        parser.add_argument('--urls', type=str, help='Comma-separated URLs to test')
        parser.add_argument('--content-samples', type=str, help='Comma-separated content samples')

# Usage: python manage.py run_healthcare_qa --urls "url1,url2" --content-samples "sample1,sample2"
```

## Test Categories

### 1. Accessibility Testing
- WCAG 2.1 AA compliance
- Healthcare-specific accessibility requirements
- Screen reader compatibility for medical content
- Keyboard navigation for medical forms
- Color contrast for medical alerts

### 2. SEO Testing
- Medical content optimization
- Healthcare keyword analysis
- Schema.org structured data for medical content
- Medical disclaimer validation
- Healthcare content quality assessment

### 3. Performance Testing
- Page load time optimization
- Database query optimization
- Memory usage monitoring
- Concurrent user handling
- Healthcare workflow performance

### 4. Security Testing
- HTTPS enforcement
- PHI data protection
- Access control validation
- Audit logging verification
- Session security testing

### 5. Content Validation
- Medical terminology accuracy
- Drug interaction warnings
- Dosage information validation
- Clinical guidelines compliance
- Medical disclaimer presence

### 6. Cross-Browser Testing
- JavaScript functionality across browsers
- CSS rendering consistency
- Form functionality validation
- Healthcare workflow compatibility
- Mobile browser testing

### 7. Mobile Testing
- Responsive design validation
- Touch interaction testing
- Mobile navigation testing
- Healthcare form usability
- Viewport optimization

## Configuration

### Environment Variables
```bash
# Optional: Configure browser testing
SELENIUM_HUB_URL=http://localhost:4444/wd/hub
BROWSER_TIMEOUT=30

# Optional: Configure performance thresholds
PERFORMANCE_THRESHOLD_MS=3000
CRITICAL_PAGE_THRESHOLD_MS=1500
```

### Settings
```python
# In your Django settings
HEALTHCARE_QA_SETTINGS = {
    'ACCESSIBILITY_THRESHOLD': 85,
    'SECURITY_THRESHOLD': 90,
    'PERFORMANCE_THRESHOLD': 80,
    'MEDICAL_ACCURACY_THRESHOLD': 95,
    'SUPPORTED_LOCALES': ['en-ZA', 'af-ZA'],
    'CRITICAL_PAGES': [
        '/emergency/',
        '/prescriptions/',
        '/patient-data/'
    ]
}
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Healthcare QA Testing
on: [push, pull_request]

jobs:
  healthcare-qa:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install selenium beautifulsoup4 psutil
      - name: Run Healthcare QA Suite
        run: |
          python manage.py run_healthcare_qa --urls "http://localhost:8000/"
```

## Compliance Standards

This module tests against the following standards:

- **HIPAA**: Health Insurance Portability and Accountability Act
- **WCAG 2.1 AA**: Web Content Accessibility Guidelines
- **Section 508**: US Federal accessibility requirements
- **ISO 27001**: Information security management
- **FDA Guidelines**: Medical device software guidance
- **GDPR**: General Data Protection Regulation (where applicable)

## Reporting

### Report Structure
```json
{
  "overall_compliance_score": 87.5,
  "overall_healthcare_compliance": true,
  "compliance_summary": {
    "hipaa_compliant": true,
    "accessibility_compliant": true,
    "performance_acceptable": true,
    "ready_for_production": true
  },
  "suite_results": {
    "accessibility": {...},
    "security": {...},
    "performance": {...},
    "content_validation": {...},
    "mobile": {...}
  },
  "critical_issues": [],
  "recommendations": [
    "Implement continuous monitoring for healthcare compliance",
    "Schedule regular QA audits for medical content accuracy"
  ]
}
```

## Support

For issues or questions about the Healthcare QA module:

1. Check the test results and recommendations
2. Review the compliance summary
3. Address critical issues first
4. Implement suggested improvements
5. Re-run tests to verify fixes

## Contributing

When contributing to this module:

1. Follow healthcare compliance standards
2. Add tests for new functionality
3. Update documentation
4. Ensure HIPAA compliance
5. Test with medical content samples

## License

This module is part of the MedGuard SA project and follows the same licensing terms.
