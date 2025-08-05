# MedGuard SA - Comprehensive Migration Testing

This document describes the comprehensive migration testing system for MedGuard SA's prescription management platform.

## Overview

The migration testing system verifies that all components of the prescription system work correctly with the 21-medication prescription format, including:

1. **All 21 medications** from the prescription can be created successfully
2. **ICD-10 code mappings** work correctly (E10.4, F90.9, etc.)
3. **Complex medication schedules** for dosing patterns like EPLEPTIN 3x3 daily
4. **Stock calculations** work for different medication types
5. **Prescription workflow state** persistence and transitions

## Test Files

- `test_migrations.py` - Main comprehensive test suite
- `run_migration_tests.py` - Simple test runner script
- `MIGRATION_TESTING_README.md` - This documentation

## Prerequisites

Before running the migration tests, ensure you have:

1. **Django environment** properly configured
2. **Database** set up and migrations applied
3. **Required dependencies** installed
4. **Test database** configured (recommended)

## Running the Tests

### Option 1: Using the Test Runner (Recommended)

```bash
cd medguard_backend
python run_migration_tests.py
```

### Option 2: Using Django Test Framework

```bash
cd medguard_backend
python manage.py test test_migrations.MigrationComprehensiveTest
```

### Option 3: Running Individual Tests

```bash
# Test medication creation only
python manage.py test test_migrations.MigrationComprehensiveTest.test_01_all_21_medications_creation

# Test ICD-10 mappings only
python manage.py test test_migrations.MigrationComprehensiveTest.test_02_icd10_code_mappings

# Test complex schedules only
python manage.py test test_migrations.MigrationComprehensiveTest.test_03_complex_medication_schedules
```

## Test Coverage

### 1. All 21 Medications Creation (`test_01_all_21_medications_creation`)

Tests the creation of all 21 medications from the prescription:

- **NOVORAPID** (Insulin aspart) - 3ml FlexPen x 3
- **LANTUS** (Insulin glargine) - SolarStar Pen x 2
- **ELTROXIN** (Levothyroxine) - 200mg tablets x 30
- **MEDROL** (Methylprednisolone) - 4mg tablets x 30
- **FLORINEF** (Fludrocortisone) - 0.1mg tablets x 30
- **VYVANSE** (Lisdexamfetamine) - 70mg capsules x 30
- **WELBUTRIN XL** (Bupropion) - 300mg tablets x 30
- **RITALIN LA** (Methylphenidate) - 40mg capsules x 30
- **CYMGEN** (Cyanocobalamin) - 500mg tablets x 30
- **TOPZOLE** (Omeprazole) - 20mg tablets x 30
- **FEXO** (Fexofenadine) - 180mg tablets x 30
- **RIVOTRIL** (Clonazepam) - 2mg tablets x 30
- **EPLEPTIN** (Phenytoin) - 400mg tablets x 270
- **TARGINACT** (Oxycodone/naloxone) - 10/5mg tablets x 60
- **CELEBREX** (Celecoxib) - 200mg capsules x 30
- **QUININE** (Quinine sulphate) - 300mg tablets x 30
- **MONTEFLO** (Montelukast) - 10mg tablets x 30
- **BETNOVATE IN UEA** (Betamethasone) - 0.1% cream x 30g
- **SENNA** (Senna glycosides) - 8.6mg tablets x 30
- **DULCOLAX** (Bisacodyl) - 5mg tablets x 30
- **STILPAYNE** (Tramadol) - 50mg capsules x 30

### 2. ICD-10 Code Mappings (`test_02_icd10_code_mappings`)

Tests ICD-10 code validation and mapping:

- **E10.4** - Type 1 diabetes mellitus with neurological complications
- **F90.9** - Attention-deficit hyperactivity disorder, unspecified type
- **G89.4** - Chronic pain syndrome
- **K21.0** - Gastro-esophageal reflux disease with esophagitis
- **J30.9** - Allergic rhinitis, unspecified
- And 9 additional codes covering various medical conditions

### 3. Complex Medication Schedules (`test_03_complex_medication_schedules`)

Tests complex dosing patterns:

- **EPLEPTIN**: 3 tablets 3 times daily (morning, noon, night) = 9 tablets total
- **MEDROL**: 1 tablet morning + 2 tablets noon
- **VYVANSE**: 2 capsules once daily
- **TARGINACT**: 1 tablet twice daily (morning, night)

### 4. Stock Calculations (`test_04_stock_calculations`)

Tests stock management for different medication types:

- **Stock transactions** (purchase, dose taken)
- **Low stock detection** and alerts
- **Stock analytics** and predictions
- **Different medication types** (tablets, capsules, injections, creams)

### 5. Prescription Workflow States (`test_05_prescription_workflow_states`)

Tests prescription workflow:

- **State transitions**: draft → active → filled → expired
- **21-medication prescription** creation
- **Prescription-medication relationships**
- **Workflow validation**

### 6. Comprehensive Integration (`test_06_comprehensive_integration`)

Tests all components working together:

- **Medication logs** creation
- **Bulk prescription** creation
- **Cross-component** functionality

### 7. Performance and Scalability (`test_07_performance_and_scalability`)

Tests system performance:

- **Medication creation** performance (< 5 seconds)
- **Schedule creation** performance (< 3 seconds)
- **Stock calculations** performance (< 5 seconds)
- **Database queries** performance (< 1 second)

### 8. OCR Result Storage and Retrieval (`test_08_ocr_result_storage_and_retrieval`)

Tests OCR functionality:

- **OCR result storage** with confidence scores
- **Medication matching** from OCR data
- **Parsed data validation** (name, strength, dosage)
- **Low confidence rejection** (< 0.8 threshold)
- **Raw text and structured data** handling

### 9. Medication Interaction Detection (`test_09_medication_interaction_detection`)

Tests drug interaction system:

- **Known interactions** detection (VYVANSE + RITALIN LA, TARGINACT + STILPAYNE)
- **Severity levels** (low, medium, high)
- **Interaction types** (contraindicated, moderate, minor)
- **Warning generation** with recommendations
- **Contraindication detection** and alerts

### 10. Prescription Renewal Calculations (`test_10_prescription_renewal_calculations`)

Tests renewal logic:

- **Daily usage calculations** (EPLEPTIN: 9 tablets/day)
- **Renewal date prediction** based on stock and usage
- **Priority assignment** (urgent, high, medium, low)
- **Different medication patterns** (monthly, bi-weekly, quarterly)
- **Prescription expiry** calculations

### 11. Bulk Medication Creation and Validation (`test_11_bulk_medication_creation_and_validation`)

Tests bulk operations:

- **Bulk medication creation** with validation
- **Data integrity checks** (name, strength, type)
- **Bulk stock updates** and verification
- **Invalid data rejection** (empty names, negative counts)
- **Bulk deletion** and cleanup

### 12. Database Constraints and Relationships (`test_12_database_constraints_and_relationships`)

Tests database integrity:

- **Foreign key constraints** (patient, medication relationships)
- **Unique constraints** (prescription numbers)
- **Cascade delete** relationships
- **Check constraints** (positive pill counts)
- **Many-to-many relationships** (medication-ICD10)
- **Index performance** and query optimization
- **Transaction integrity** and rollback

## Expected Output

When tests pass successfully, you should see output like:

```
🚀 Starting Comprehensive Migration Testing for MedGuard SA
============================================================

=== Testing All 21 Medications Creation ===
✓ Created medication 1/21: NOVORAPID (100 units/ml units)
✓ Created medication 2/21: LANTUS (100 units/ml units)
...
✓ Successfully created all 21 medications

=== Testing ICD-10 Code Mappings ===
✓ ICD-10 code E10.4: Type 1 diabetes mellitus with neurological complications
✓ ICD-10 code F90.9: Attention-deficit hyperactivity disorder, unspecified type
...
✓ All ICD-10 code mappings work correctly

=== Testing Complex Medication Schedules ===
✓ Created schedule for EPLEPTIN: 3x three times daily (morning)
✓ Created schedule for EPLEPTIN: 3x three times daily (noon)
✓ Created schedule for EPLEPTIN: 3x three times daily (night)
...
✓ EPLEPTIN complex dosing: 3 tablets 3x daily = 9 tablets total

=== Testing Stock Calculations ===
✓ Stock calculations for NOVORAPID: 3 → 2
✓ Stock calculations for LANTUS: 2 → 1
...
✓ All stock calculations work correctly for different medication types

=== Testing Prescription Workflow States ===
✓ Prescription workflow state: draft
✓ Prescription workflow state: active
✓ Prescription workflow state: filled
✓ Prescription workflow state: expired
✓ Prescription workflow states persist correctly
✓ All 21 medications are properly linked to prescription

=== Testing Comprehensive Integration ===
✓ Comprehensive integration test passed
✓ All 21 medications, ICD-10 codes, schedules, stock, and workflow work together

=== Testing Performance and Scalability ===
✓ Created 21 medications in 1.23 seconds
✓ Created complex schedules in 0.87 seconds
✓ Completed stock calculations in 2.15 seconds
✓ Database queries completed in 0.12 seconds
✓ Performance and scalability tests passed

=== Testing OCR Result Storage and Retrieval ===
✓ Stored OCR result for NOVORAPID (confidence: 0.95)
✓ Stored OCR result for EPLEPTIN (confidence: 0.92)
✓ Stored OCR result for VYVANSE (confidence: 0.88)
✓ Retrieved and matched OCR result for NOVORAPID
✓ Retrieved and matched OCR result for EPLEPTIN
✓ Retrieved and matched OCR result for VYVANSE
✓ Rejected low confidence OCR result: INVALID_MED
✓ OCR result storage and retrieval tests passed

=== Testing Medication Interaction Detection ===
✓ Detected high interaction: VYVANSE + RITALIN LA
✓ Detected medium interaction: TARGINACT + STILPAYNE
✓ Detected low interaction: TOPZOLE + CYMGEN
✓ Detected medium interaction: RIVOTRIL + VYVANSE
✓ Generated interaction warning for VYVANSE + RITALIN LA
✓ Generated interaction warning for TARGINACT + STILPAYNE
✓ Generated interaction warning for TOPZOLE + CYMGEN
✓ Generated interaction warning for RIVOTRIL + VYVANSE
✓ Detected 1 contraindicated interactions
✓ Medication interaction detection tests passed

=== Testing Prescription Renewal Calculations ===
✓ Calculated renewal for ELTROXIN: 30 days (medium priority)
✓ Calculated renewal for EPLEPTIN: 30 days (medium priority)
✓ Calculated renewal for VYVANSE: 15 days (high priority)
✓ Calculated renewal for NOVORAPID: 90 days (low priority)
✓ Found 0 urgent renewals, 1 high priority renewals
✓ Prescription expires in 335 days (low priority)
✓ Prescription renewal calculations tests passed

=== Testing Bulk Medication Creation and Validation ===
✓ Created bulk medication 1/3: BULK_TEST_1
✓ Created bulk medication 2/3: BULK_TEST_2
✓ Created bulk medication 3/3: BULK_TEST_3
✓ Bulk stock updates completed successfully
✓ Bulk validation correctly rejects invalid data
✓ Successfully deleted 3 bulk test medications
✓ Bulk medication creation and validation tests passed

=== Testing Database Constraints and Relationships ===
✓ Foreign key constraints work correctly
✓ Unique constraints work correctly
✓ Cascade delete relationships work correctly
✓ Check constraints work correctly
✓ Many-to-many relationships work correctly
✓ Database indexes work correctly (queries completed in 0.045s)
✓ Transaction integrity works correctly
✓ All database constraints and relationships work correctly

============================================================
✅ ALL COMPREHENSIVE MIGRATION TESTS PASSED!
✅ MedGuard SA prescription system is ready for production
============================================================
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure database is running and accessible
   - Check database settings in `settings/development.py`

2. **Model Import Errors**
   - Ensure all migrations are applied: `python manage.py migrate`
   - Check that all required models exist

3. **ICD-10 Code Errors**
   - Ensure ICD-10 codes are created in the database
   - Check the migration `0012_seed_prescription_data.py`

4. **Performance Test Failures**
   - Tests may fail on slower systems
   - Adjust performance thresholds in `test_07_performance_and_scalability`

### Debug Mode

To run tests with more detailed output:

```bash
python manage.py test test_migrations.MigrationComprehensiveTest --verbosity=2
```

### Database Reset

If tests fail due to database state, reset the test database:

```bash
python manage.py flush --noinput
python manage.py migrate
```

## Integration with CI/CD

The migration tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Migration Tests
  run: |
    cd medguard_backend
    python run_migration_tests.py
```

## Contributing

When adding new medications or modifying the prescription system:

1. **Update test data** in `test_migrations.py`
2. **Add new test cases** as needed
3. **Run all tests** to ensure compatibility
4. **Update documentation** if necessary

## Support

For issues with the migration testing system:

1. Check the troubleshooting section above
2. Review Django logs for detailed error messages
3. Ensure all dependencies are up to date
4. Contact the MedGuard SA development team

---

**MedGuard SA Development Team**  
*Last updated: 2025-01-27* 