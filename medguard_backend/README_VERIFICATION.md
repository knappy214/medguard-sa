# MedGuard SA Setup Verification

This directory contains a comprehensive verification script to test the MedGuard SA Django backend setup.

## 📋 Verification Script

The `verify_setup.py` script performs the following comprehensive tests:

### 1. Model Instantiation Verification
- Tests that all Django models can be instantiated without errors
- Verifies `__str__` methods work correctly
- Checks Meta class configurations
- Tests model imports and basic functionality

### 2. Test User Creation
- Creates a comprehensive test user with all healthcare-specific fields
- Tests user model validation and field constraints
- Verifies user type restrictions and choices

### 3. Comprehensive Medication Creation
- Creates a medication with **all fields** populated from the prescription structure
- Tests medication type and prescription type choices
- Verifies dosage, strength, and unit validations
- Tests image processing fields and metadata
- Validates medication properties (is_low_stock, is_expired, etc.)

### 4. Foreign Key Relationship Verification
- Tests creation of related models:
  - `MedicationSchedule` (patient ↔ medication)
  - `MedicationLog` (patient ↔ medication ↔ schedule)
  - `StockAlert` (medication ↔ user)
  - `StockTransaction` (medication ↔ user)
  - `StockAnalytics` (medication)
  - `PrescriptionRenewal` (patient ↔ medication)
- Verifies reverse relationship queries work correctly
- Tests cascade deletion and relationship integrity

### 5. Model Methods and Properties Testing
- Tests custom model methods and properties
- Verifies validation methods (`clean()`)
- Tests computed properties and business logic

### 6. Database Constraints and Validations
- Tests unique constraints
- Verifies field validations
- Tests choice field restrictions

### 7. Bulk Medication Creation (21-Medication Prescription)
- Creates 21 realistic medications covering all major categories:
  - Pain Management (Paracetamol, Ibuprofen)
  - Antibiotics (Amoxicillin, Azithromycin)
  - Cardiovascular (Amlodipine, Lisinopril)
  - Diabetes Management (Metformin, Gliclazide)
  - Respiratory (Salbutamol, Beclomethasone)
  - Gastrointestinal (Omeprazole, Ranitidine)
  - Mental Health (Sertraline, Amitriptyline)
  - Supplements (Vitamin D3, Omega-3)
  - Topical Medications (Hydrocortisone, Betamethasone)
  - Eye Drops (Chloramphenicol, Artificial Tears)
  - Emergency Medications (Adrenaline)
- Tests bulk creation performance and data integrity
- Verifies medication type and prescription type distributions

### 8. Complex Medication Schedule Testing
- Tests complex dosing patterns:
  - Twice daily with food (Paracetamol)
  - Weekly injection (Adrenaline)
  - As needed inhaler (Salbutamol)
  - Four times daily eye drops (Chloramphenicol)
  - Bedtime antidepressant (Amitriptyline)
  - Morning blood pressure medication (Amlodipine)
  - With meals diabetes medication (Metformin)
  - Twice daily topical cream (Hydrocortisone)
- Verifies custom timing, frequency patterns, and day-of-week schedules
- Tests schedule validation and business logic

### 9. Stock Management Calculations
- Tests comprehensive stock tracking:
  - Purchase transactions with pricing
  - Dose taken transactions (negative quantities)
  - Stock adjustments and corrections
  - Real-time stock level calculations
- Creates stock analytics with predictions:
  - Daily, weekly, and monthly usage rates
  - Days until stockout predictions
  - Recommended order quantities and dates
  - Stockout confidence levels
- Tests low stock alerts and threshold monitoring
- Verifies bulk stock operations across all medication types

### 10. OCR Result Storage and Retrieval
- Tests OCR processing result storage:
  - Prescription number and doctor information extraction
  - Extracted text and confidence scores
  - Image quality assessment and metadata
  - Processing time and engine information
  - Extracted medications with dosage and frequency
- Tests OCR result retrieval and search:
  - Retrieval by prescription number
  - Search by doctor name
  - Filtering by confidence score and processing status
  - Validation of required fields and data integrity
- Tests medication extraction from OCR results:
  - Medication name, strength, and dosage parsing
  - Frequency and instruction extraction
  - Confidence scoring for extracted data

### 11. Prescription Workflow State Management
- Tests prescription workflow state tracking:
  - State transitions (draft → submitted → under_review → approved → dispensing → dispensed → completed)
  - Previous state tracking and history
  - State change timestamps and user attribution
  - Notes and comments for state changes
- Tests workflow validation:
  - Valid state transitions based on current state
  - Terminal state identification (completed, cancelled, expired)
  - Required field validation for workflow states
- Tests workflow queries and filtering:
  - Count by workflow state
  - Active vs terminal workflow identification
  - Workflow history tracking

### 12. Admin Interface Functionality
- Tests Django admin site configuration:
  - Custom site header, title, and index title
  - Admin site customization and branding
- Tests admin model registration:
  - Verification of all models registered in admin
  - Admin class configuration and customization
  - List display, filters, and search fields
- Tests admin permissions and access:
  - Superuser access verification
  - Admin URL pattern generation
  - Model admin URL accessibility
- Tests admin customizations:
  - Custom admin actions and bulk operations
  - Custom admin methods and properties
  - Admin fieldsets and field organization
  - Readonly fields and ordering

## 🚀 Usage

### Method 1: Direct Execution
```bash
cd medguard_backend
python verify_setup.py
```

### Method 2: Django Shell
```bash
cd medguard_backend
python manage.py shell < verify_setup.py
```

### Method 3: Interactive Mode
```bash
cd medguard_backend
python manage.py shell
```

Then in the shell:
```python
from verify_setup import MedGuardSetupVerifier
verifier = MedGuardSetupVerifier()
results = verifier.run_full_verification()
```

## 📊 Expected Output

The script provides detailed, color-coded output:

```
============================================================
 MEDGUARD SA SETUP VERIFICATION
============================================================

--- 1. Model Instantiation Verification ---
✅ User: Basic instantiation successful
✅ User: __str__ method works
✅ User: Meta class exists
✅ Medication: Basic instantiation successful
✅ Medication: __str__ method works
✅ Medication: Meta class exists
...

--- 2. Creating Test User ---
✅ Created test user: test@medguard-verification.com

--- 3. Creating Comprehensive Medication ---
✅ Created comprehensive medication: Test Medication - Paracetamol
✅ Field name: ✓
✅ Field generic_name: ✓
✅ Field strength: ✓
...

--- 4. Foreign Key Relationship Verification ---
✅ Created MedicationSchedule: Test Verification - Test Medication - Paracetamol (Morning)
✅ Created MedicationLog: Test Verification - Test Medication - Paracetamol (Taken)
✅ Created StockAlert: Low Stock Alert
...

📊 VERIFICATION RESULTS:
   Total Tests: 108
   ✅ Passed: 105
   ❌ Failed: 0
   ⚠️  Warnings: 3
   📈 Success Rate: 97.2%

🎯 OVERALL STATUS: PASSED

🎉 VERIFICATION COMPLETED SUCCESSFULLY!
```

## 🔧 Exit Codes

- `0` - All tests passed successfully
- `1` - Some tests failed or warnings occurred

## 🧹 Test Data Cleanup

By default, the script **keeps** test data for inspection. To enable automatic cleanup, uncomment this line in the script:

```python
# self.cleanup_test_data()
```

## 📝 Test Data Created

The script creates the following test data:

### Test User
- Email: `test@medguard-verification.com`
- Type: Patient
- Complete healthcare profile with all fields

### Test Medication
- Name: "Test Medication - Paracetamol"
- Generic: Paracetamol
- Brand: Panado
- All fields populated including image processing metadata

### Bulk Medications (21 total)
- **Pain Management**: Paracetamol, Ibuprofen
- **Antibiotics**: Amoxicillin, Azithromycin
- **Cardiovascular**: Amlodipine, Lisinopril
- **Diabetes**: Metformin, Gliclazide
- **Respiratory**: Salbutamol, Beclomethasone
- **Gastrointestinal**: Omeprazole, Ranitidine
- **Mental Health**: Sertraline, Amitriptyline
- **Supplements**: Vitamin D3, Omega-3
- **Topical**: Hydrocortisone, Betamethasone
- **Eye Drops**: Chloramphenicol, Artificial Tears
- **Emergency**: Adrenaline
- Plus 8 additional medications covering various categories

### Complex Schedules (8 total)
- Twice daily with food
- Weekly injection
- As needed inhaler
- Four times daily eye drops
- Bedtime medication
- Morning medication
- With meals medication
- Twice daily topical

### OCR Results (2 total)
- **RX-2024-001**: Dr. Sarah Johnson prescription with Paracetamol and Amoxicillin
- **RX-2024-002**: Dr. Michael Chen prescription with Lisinopril and Metformin
- Extracted text, confidence scores, and medication details
- Image quality assessment and processing metadata

### Workflow States (5 total)
- **RX-WF-001**: Draft state for Paracetamol
- **RX-WF-002**: Submitted state for Amoxicillin  
- **RX-WF-003**: Under Review state for Amlodipine
- **RX-WF-004**: Approved state for Metformin
- **RX-WF-005**: Dispensing state for Salbutamol
- State transitions and workflow history tracking

### Admin Interface Tests
- Admin site configuration verification
- Model registration testing
- Admin class customization validation
- URL pattern and permission testing

### Related Objects
- Medication schedules (simple and complex)
- Medication logs
- Stock alerts
- Stock transactions (purchase, dose taken, adjustments)
- Stock analytics with predictions
- Prescription renewals

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all apps are properly installed in `INSTALLED_APPS`
2. **Database Connection**: Verify database settings and connectivity
3. **Migration Issues**: Run `python manage.py migrate` before verification
4. **Permission Errors**: Ensure database user has appropriate permissions

### Debug Mode

For detailed debugging, modify the script to add more verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Continuous Integration

This script can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Verify Django Setup
  run: |
    cd medguard_backend
    python verify_setup.py
```

## 📈 Performance Notes

- The script uses database transactions for data integrity
- Test data is minimal and focused on verification
- Cleanup is optional to allow inspection of created data
- The script is designed to be idempotent (can run multiple times safely)

## 🎯 Success Criteria

A successful verification should show:
- ✅ All model instantiations successful
- ✅ Test user and medication created with all fields
- ✅ All foreign key relationships working
- ✅ Model methods and properties functioning
- ✅ Database constraints properly enforced
- 📈 Success rate > 90%

## 📞 Support

If verification fails, check:
1. Django settings configuration
2. Database connectivity and migrations
3. Model field definitions and relationships
4. Custom validation methods
5. Import paths and app configurations 