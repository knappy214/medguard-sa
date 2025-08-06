# Wagtail 7.0.2 Page Models for MedGuard SA

## Overview

This document describes the implementation of 5 comprehensive Wagtail page models for the MedGuard SA medication management system, built with Wagtail 7.0.2 features and best practices.

## Page Models Implemented

### 1. PrescriptionFormPage
**Interactive prescription submission with Wagtail forms**

**Features:**
- ✅ Wagtail AbstractForm integration with custom form fields
- ✅ Authentication requirements with redirect handling
- ✅ CAPTCHA protection for spam prevention
- ✅ Rich content with StreamField (descriptions, warnings)
- ✅ Form submissions panel in admin
- ✅ User profile auto-population for authenticated users
- ✅ Enhanced search with boost factors

**Key Components:**
- `PrescriptionFormField` - Custom form field model
- `PrescriptionFormStreamBlock` - Rich content blocks
- Authentication middleware integration
- HIPAA-compliant form handling

**Usage:**
```python
# Create form fields in admin
# Users can submit prescriptions with validation
# Form submissions are logged and managed
```

### 2. MedicationComparisonPage
**Side-by-side medication comparison with StreamField**

**Features:**
- ✅ Interactive comparison with session management
- ✅ Configurable maximum comparison items (2-10)
- ✅ Rich comparison blocks with validation
- ✅ Efficacy ratings and cost comparison
- ✅ Side effects and dosage information
- ✅ Notes and additional information

**Key Components:**
- `MedicationComparisonBlock` - Individual medication data
- `MedicationComparisonStreamBlock` - Comparison content
- Session-based comparison state management
- Enhanced validation with regex patterns

**Usage:**
```python
# Add medications to comparison session
# Display side-by-side comparison tables
# Filter and sort comparison data
```

### 3. PharmacyLocatorPage
**Pharmacy finder with Wagtail's geolocation features**

**Features:**
- ✅ Location services integration
- ✅ Configurable search radius (1-100km)
- ✅ Pharmacy location blocks with contact info
- ✅ Service listings (prescription, consultation, delivery)
- ✅ Operating hours and website links
- ✅ Geolocation-based search capabilities

**Key Components:**
- `PharmacyLocationBlock` - Individual pharmacy data
- `PharmacyLocatorStreamBlock` - Location content
- GIS integration for location services
- Service categorization and filtering

**Usage:**
```python
# Enable location services for user's device
# Search pharmacies within specified radius
# Display pharmacy details and services
```

### 4. MedicationGuideIndexPage
**Medication guides with Wagtail 7.0.2 filtering**

**Features:**
- ✅ Advanced filtering by category and difficulty
- ✅ Configurable items per page (1-50)
- ✅ Guide categorization system
- ✅ Difficulty level filtering
- ✅ Enhanced search with filter fields
- ✅ Pagination support

**Key Components:**
- `MedicationGuideBlock` - Individual guide content
- `MedicationGuideStreamBlock` - Guide collections
- `MedicationGuideDetailPage` - Individual guide pages
- Wagtail 7.0.2 filter field integration

**Usage:**
```python
# Filter guides by category (general, dosage, side_effects, etc.)
# Filter by difficulty level (beginner, intermediate, advanced)
# Paginate through guide collections
```

### 5. PrescriptionHistoryPage
**Patient prescription history with privacy controls**

**Features:**
- ✅ HIPAA-compliant privacy controls
- ✅ Authentication requirements
- ✅ Audit logging for access tracking
- ✅ Configurable data retention (365-3650 days)
- ✅ Pagination with configurable items per page
- ✅ User-specific prescription data

**Key Components:**
- `PrescriptionHistoryBlock` - Individual prescription data
- `PrescriptionHistoryStreamBlock` - History content
- Security audit logging integration
- Privacy settings management

**Usage:**
```python
# Require user authentication
# Log all access attempts for audit
# Display user-specific prescription history
# Enforce data retention policies
```

## Technical Implementation

### Wagtail 7.0.2 Features Used

1. **Enhanced StreamField**
   - `use_json_field=True` for performance
   - Block validation with custom mixins
   - Structured content blocks

2. **Advanced Search Configuration**
   - Boost factors for search relevance
   - Filter fields for faceted search
   - Related fields with search integration

3. **Form Integration**
   - AbstractForm with custom fields
   - Form submissions management
   - Authentication integration

4. **Settings Management**
   - `@register_setting` decorator
   - Site-wide configuration options
   - Centralized settings management

### Security & Privacy Features

1. **Authentication Controls**
   - Required authentication for sensitive pages
   - Redirect handling for unauthenticated users
   - User profile integration

2. **Audit Logging**
   - HIPAA-compliant access logging
   - Security event tracking
   - Privacy protection measures

3. **Data Validation**
   - Regex validation for medication names
   - Input sanitization
   - Structured data validation

### Performance Optimizations

1. **Database Optimization**
   - JSON field usage for StreamField
   - Proper indexing configuration
   - Efficient query patterns

2. **Caching Strategy**
   - Session-based comparison data
   - Context caching for page data
   - Search result optimization

## File Structure

```
medguard_backend/medications/
├── page_models.py                    # Main page models file
├── WAGTAIL_PAGE_MODELS_README.md     # This documentation
├── models.py                         # Existing medication models
├── views.py                          # Existing views
└── templates/                        # Template directory
    └── medications/
        └── blocks/                   # Block templates
            ├── medication_comparison_block.html
            ├── pharmacy_location_block.html
            ├── medication_guide_block.html
            └── prescription_history_block.html
```

## Template Requirements

The page models reference several template files that need to be created:

### Block Templates
- `medications/blocks/medication_comparison_block.html`
- `medications/blocks/pharmacy_location_block.html`
- `medications/blocks/medication_guide_block.html`
- `medications/blocks/prescription_history_block.html`

### Page Templates
- `medications/prescription_form_page.html`
- `medications/medication_comparison_page.html`
- `medications/pharmacy_locator_page.html`
- `medications/medication_guide_index_page.html`
- `medications/medication_guide_detail_page.html`
- `medications/prescription_history_page.html`

## Migration Requirements

To use these page models, you'll need to:

1. **Run migrations:**
   ```bash
   python manage.py makemigrations medications
   python manage.py migrate
   ```

2. **Create templates** for the block and page components

3. **Configure settings** in Wagtail admin for `MedicationPageSettings`

4. **Set up form fields** for `PrescriptionFormPage` in the admin interface

## Usage Examples

### Creating a Prescription Form Page
```python
# In Wagtail admin:
# 1. Create PrescriptionFormPage under HomePage
# 2. Add form fields (text, email, date, etc.)
# 3. Configure authentication and CAPTCHA settings
# 4. Add rich content with StreamField
```

### Setting Up Medication Comparison
```python
# In Wagtail admin:
# 1. Create MedicationComparisonPage
# 2. Add comparison content with StreamField
# 3. Configure maximum comparison items
# 4. Set up interactive comparison features
```

### Configuring Pharmacy Locator
```python
# In Wagtail admin:
# 1. Create PharmacyLocatorPage
# 2. Add pharmacy locations with StreamField
# 3. Configure search radius and location services
# 4. Set up service categories
```

## Security Considerations

1. **Authentication Required**
   - Prescription form and history pages require authentication
   - Proper redirect handling for unauthenticated users

2. **Audit Logging**
   - All prescription history access is logged
   - HIPAA compliance maintained

3. **Data Validation**
   - Input sanitization for all user data
   - Regex validation for medication names
   - Structured data validation

4. **Privacy Controls**
   - User-specific data isolation
   - Configurable data retention policies
   - Secure session management

## Future Enhancements

1. **API Integration**
   - REST API endpoints for page data
   - Mobile app integration
   - Third-party pharmacy system integration

2. **Advanced Features**
   - Real-time medication availability
   - Prescription renewal automation
   - Drug interaction checking

3. **Analytics**
   - Usage analytics for pages
   - Search term analysis
   - User behavior tracking

## Support

For questions or issues with these page models:

1. Check the Wagtail 7.0.2 documentation
2. Review the Django model documentation
3. Consult the MedGuard SA development team
4. Check the security audit logs for access issues

---

**Created:** 2024  
**Version:** 1.0  
**Wagtail Version:** 7.0.2  
**Django Version:** 4.x  
**MedGuard SA Backend** 