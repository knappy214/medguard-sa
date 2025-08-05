# Enhanced Medication Serializers

## Overview

The MedGuard SA medication serializers have been significantly enhanced to provide comprehensive prescription handling, validation, and compliance features. This document outlines all the new capabilities and how to use them.

## New Features

### 1. PrescriptionBulkCreateSerializer

A powerful serializer for handling bulk prescription creation with up to 21 medications in a single request.

#### Key Features:
- **Bulk Processing**: Handle multiple medications in one API call
- **ICD-10 Validation**: Comprehensive ICD-10 code validation with descriptions
- **Drug Interactions**: Real-time interaction checking between medications
- **Contraindication Checking**: Validate against patient conditions
- **Prescription Parsing**: Parse natural language instructions
- **Stock Management**: Automatic stock deduction and availability checking
- **Audit Logging**: Comprehensive compliance logging
- **Error Handling**: Detailed error codes for frontend integration

#### Usage Example:

```python
from medications.serializers import PrescriptionBulkCreateSerializer

# Create serializer with request context
serializer = PrescriptionBulkCreateSerializer(
    data=bulk_prescription_data,
    context={'request': request}
)

# Validate and create
if serializer.is_valid():
    result = serializer.save()
    
    # Access results
    created_medications = serializer.get_created_medications(result)
    interaction_warnings = serializer.get_interaction_warnings(result)
    stock_warnings = serializer.get_stock_warnings(result)
    processing_errors = serializer.get_processing_errors(result)
else:
    errors = serializer.errors
```

#### Sample Request Data:

```json
{
  "prescription_number": "RX-2024-001",
  "prescribing_doctor": "Dr. Sarah Johnson",
  "icd10_codes": ["E11.9", "I10", "F90.9"],
  "patient_conditions": ["diabetes", "hypertension"],
  "medications": [
    {
      "name": "Metformin",
      "strength": "500mg",
      "dosage_unit": "mg",
      "quantity": 60,
      "manufacturer": "Aspen Pharmacare",
      "prescription_instructions": "Take one tablet twice daily with meals"
    }
  ],
  "auto_create_schedules": true,
  "auto_deduct_stock": false
}
```

### 2. Enhanced ICD-10 Validation

Comprehensive ICD-10 code validation with detailed mappings for South African healthcare.

#### Supported Codes:
- **E10.4, E11.4, E13.4**: Diabetes with complications
- **F90.9, F90.0, F90.1**: ADHD
- **F32.9, F41.9, F33.9**: Depression and anxiety
- **I10, I11.9, I12.9**: Hypertension
- **J45.901, J44.9, J45.909**: Asthma and COPD
- **M79.3, R52.9**: Pain syndromes
- **N39.0, A09.9**: Infections

#### Usage:

```python
from medications.serializers import ICD10Validator

# Validate code
is_valid = ICD10Validator.validate("E11.9")

# Get description
description = ICD10Validator.get_description("E11.9")
# Returns: "Type 2 diabetes mellitus without complications"

# Get category
category = ICD10Validator.get_category("E11.9")
# Returns: "Endocrine, nutritional and metabolic diseases"
```

### 3. Advanced Prescription Parsing

Intelligent parsing of prescription instructions in natural language.

#### Supported Formats:
- "Take one tablet daily"
- "Take two tablets at 12h00"
- "Take 1 capsule three times daily"
- "Take 2 tablets morning and evening"
- "Inject 20 units once daily at bedtime"
- "Take 500mg at 8h00, 14h00 and 20h00"

#### Usage:

```python
from medications.serializers import PrescriptionParser

# Parse instructions
parsed = PrescriptionParser.parse_instructions("Take two tablets at 12h00")

# Access parsed data
dosage_amount = parsed['dosage_amount']  # 2
dosage_unit = parsed['dosage_unit']      # "tablets"
frequency = parsed['frequency']          # "daily"
timing = parsed['timing']                # "custom"
custom_time = parsed['custom_time']      # time(12, 0)
confidence = parsed['parsed_confidence'] # 0.95
```

### 4. Strength Unit Normalization

Comprehensive strength unit validation and normalization.

#### Supported Units:
- **Weight**: mg, mcg, g
- **Volume**: ml, l
- **Insulin**: units, IU
- **Concentration**: mg/ml, mcg/ml, g/ml, units/ml, IU/ml
- **Other**: mEq, mmol, %, billion CFU

#### Usage:

```python
from medications.serializers import StrengthUnitNormalizer

# Normalize strength
normalized = StrengthUnitNormalizer.normalize_strength("500mg")
# Returns: "500mg"

# Validate format
is_valid = StrengthUnitNormalizer.validate_strength_format("10mg/ml")
# Returns: True
```

### 5. South African Manufacturer Validation

Validation against recognized South African pharmaceutical manufacturers.

#### Supported Manufacturers:
- **International**: Novo Nordisk, Pfizer, GSK, AstraZeneca, Bayer
- **South African**: Aspen Pharmacare, Adcock Ingram, Dis-Chem, Clicks
- **Generic**: Cipla, Ranbaxy, Dr Reddy's, Sun Pharmaceutical

#### Usage:

```python
from medications.serializers import SouthAfricanManufacturerValidator

# Validate manufacturer
is_valid = SouthAfricanManufacturerValidator.validate_manufacturer("Aspen Pharmacare")

# Get standardized name
standardized = SouthAfricanManufacturerValidator.get_standardized_name("GSK")
# Returns: "GSK South Africa"

# Get manufacturer type
manufacturer_type = SouthAfricanManufacturerValidator.get_manufacturer_type("Novo Nordisk")
# Returns: "International"
```

### 6. Drug Interaction Validation

Comprehensive drug interaction and contraindication checking.

#### Supported Interactions:
- **Warfarin**: Aspirin, ibuprofen, heparin
- **Digoxin**: Furosemide, spironolactone, quinidine
- **Lithium**: Ibuprofen, thiazide diuretics
- **Metformin**: Alcohol, furosemide, corticosteroids
- **Insulin**: Corticosteroids, beta-blockers

#### Usage:

```python
from medications.serializers import MedicationInteractionValidator

# Check interactions
interactions = MedicationInteractionValidator.check_interactions(
    "Warfarin", 
    ["Aspirin", "Metformin"]
)

# Check contraindications
contraindications = MedicationInteractionValidator.check_contraindications(
    "Warfarin", 
    ["pregnancy", "liver_disease"]
)
```

### 7. Prescription Renewal Calculator

Automatic calculation of prescription renewal dates based on quantity and frequency.

#### Usage:

```python
from medications.serializers import PrescriptionRenewalCalculator

# Calculate renewal date
renewal_date = PrescriptionRenewalCalculator.calculate_renewal_date(
    quantity=60,
    frequency='twice_daily',
    dosage_amount=Decimal('1')
)
```

### 8. Stock Deduction Manager

Intelligent stock management with automatic deduction and availability checking.

#### Features:
- **Stock Calculation**: Calculate required stock for schedules
- **Availability Checking**: Check if sufficient stock is available
- **Automatic Deduction**: Deduct stock when creating schedules
- **Transaction Logging**: Log all stock movements

#### Usage:

```python
from medications.serializers import StockDeductionManager

# Check stock availability
availability = StockDeductionManager.check_stock_availability(
    medication_id=1, 
    required_quantity=30
)

# Deduct stock
success = StockDeductionManager.deduct_stock(
    medication_id=1,
    quantity=30,
    user=request.user,
    reason="Schedule creation"
)
```

### 9. Comprehensive Error Handling

Standardized error codes and messages for frontend integration.

#### Error Codes:
- **1000-1999**: Validation errors
- **2000-2999**: Drug interaction errors
- **3000-3999**: Stock management errors
- **4000-4999**: Prescription processing errors
- **5000-5999**: System errors

#### Usage:

```python
from medications.serializers import ErrorCodeManager

# Raise validation error
ErrorCodeManager.raise_validation_error(
    'INVALID_ICD10_CODE',
    'Invalid ICD-10 code format: E10. Expected format: A00.0',
    'icd10_codes'
)
```

### 10. Audit Logging

Comprehensive audit logging for HIPAA compliance and South African POPIA regulations.

#### Logged Events:
- **Prescription Creation**: All prescription processing
- **Drug Interactions**: Interaction detection and warnings
- **Stock Deduction**: All stock movements
- **Validation Errors**: Failed validations
- **System Errors**: Processing failures

#### Usage:

```python
from medications.serializers import AuditLogger

# Log prescription creation
AuditLogger.log_prescription_creation(
    user=request.user,
    prescription_data=prescription_data,
    success=True,
    errors=[]
)

# Log stock deduction
AuditLogger.log_stock_deduction(
    user=request.user,
    medication_id=1,
    quantity=30,
    success=True
)
```

## EnhancedMedicationSerializer Features

The existing `EnhancedMedicationSerializer` has been upgraded with:

### New Fields:
- `auto_deduct_stock`: Automatically deduct stock when creating schedules
- `calculate_renewal_date`: Calculate prescription renewal date
- `renewal_date`: Calculated renewal date (read-only)
- `stock_availability`: Stock availability information (read-only)
- `icd10_descriptions`: ICD-10 code descriptions (read-only)

### Enhanced Validation:
- **ICD-10 Codes**: Comprehensive validation with descriptions
- **Strength Units**: Normalization and validation
- **Manufacturers**: South African manufacturer validation
- **Prescription Instructions**: Advanced parsing and validation
- **Drug Interactions**: Real-time interaction checking

### Enhanced Processing:
- **Stock Deduction**: Automatic stock management
- **Renewal Records**: Automatic prescription renewal tracking
- **Audit Logging**: Comprehensive compliance logging
- **Error Handling**: Detailed error codes and messages

## API Response Format

### Success Response:
```json
{
  "created_medications": [
    {
      "id": 1,
      "name": "Metformin",
      "strength": "500mg",
      "dosage_unit": "mg"
    }
  ],
  "created_schedules": [
    {
      "id": 1,
      "medication_name": "Metformin",
      "timing": "morning",
      "frequency": "daily"
    }
  ],
  "interaction_warnings": [],
  "contraindication_warnings": [],
  "stock_warnings": [],
  "processing_errors": []
}
```

### Error Response:
```json
{
  "error_code": 1001,
  "error_message": "Invalid ICD-10 code format",
  "error_type": "INVALID_ICD10_CODE",
  "field": "icd10_codes",
  "details": "Invalid ICD-10 code format: E10. Expected format: A00.0"
}
```

## Integration Examples

### Django View Example:

```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from medications.serializers import PrescriptionBulkCreateSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_bulk_prescription(request):
    """Create multiple medications from a prescription."""
    serializer = PrescriptionBulkCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        try:
            result = serializer.save()
            
            response_data = {
                'success': True,
                'created_medications': serializer.get_created_medications(result),
                'created_schedules': serializer.get_created_schedules(result),
                'interaction_warnings': serializer.get_interaction_warnings(result),
                'contraindication_warnings': serializer.get_contraindication_warnings(result),
                'stock_warnings': serializer.get_stock_warnings(result),
                'processing_errors': serializer.get_processing_errors(result)
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
```

### Frontend Integration Example:

```javascript
// Vue.js component example
export default {
  data() {
    return {
      prescriptionData: {
        prescription_number: '',
        prescribing_doctor: '',
        icd10_codes: [],
        patient_conditions: [],
        medications: [],
        auto_create_schedules: true,
        auto_deduct_stock: false
      },
      warnings: [],
      errors: []
    }
  },
  
  methods: {
    async submitPrescription() {
      try {
        const response = await this.$api.post('/api/prescriptions/bulk/', this.prescriptionData)
        
        if (response.data.success) {
          // Handle success
          this.$notify.success('Prescription created successfully')
          
          // Show warnings if any
          if (response.data.interaction_warnings.length > 0) {
            this.warnings = response.data.interaction_warnings
            this.$notify.warning('Drug interactions detected')
          }
          
          if (response.data.stock_warnings.length > 0) {
            this.warnings = [...this.warnings, ...response.data.stock_warnings]
            this.$notify.warning('Stock warnings detected')
          }
        }
      } catch (error) {
        if (error.response?.data?.error_code) {
          // Handle specific error codes
          const errorData = error.response.data
          this.$notify.error(`${errorData.error_message}: ${errorData.details}`)
        } else {
          this.$notify.error('Failed to create prescription')
        }
      }
    }
  }
}
```

## Testing

Run the example file to see all features in action:

```bash
cd medguard_backend
python manage.py shell

# In the shell:
from medications.examples import run_all_examples
run_all_examples()
```

## Compliance Features

### HIPAA Compliance:
- **Audit Logging**: All prescription processing logged
- **Data Encryption**: Sensitive data encrypted at rest
- **Access Controls**: Role-based access to prescription data
- **Data Retention**: 7-year retention for audit logs

### South African POPIA Compliance:
- **Data Minimization**: Only necessary data collected
- **Purpose Limitation**: Data used only for intended purposes
- **Consent Management**: Patient consent for data processing
- **Data Subject Rights**: Right to access, correct, and delete data

### Medical Device Compliance:
- **Validation**: Comprehensive input validation
- **Error Handling**: Detailed error reporting
- **Traceability**: Full audit trail for all operations
- **Safety Checks**: Drug interaction and contraindication validation

## Performance Considerations

### Optimization Features:
- **Bulk Processing**: Handle multiple medications efficiently
- **Database Transactions**: Atomic operations for data integrity
- **Caching**: ICD-10 codes and manufacturer data cached
- **Async Processing**: Non-blocking audit logging

### Scalability:
- **Batch Processing**: Support for large prescription batches
- **Database Indexing**: Optimized queries for large datasets
- **Memory Management**: Efficient memory usage for bulk operations
- **Error Recovery**: Graceful handling of partial failures

## Security Features

### Data Protection:
- **Input Validation**: Comprehensive validation of all inputs
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Output encoding
- **CSRF Protection**: Cross-site request forgery protection

### Access Control:
- **Authentication**: User authentication required
- **Authorization**: Role-based access control
- **Session Management**: Secure session handling
- **API Rate Limiting**: Protection against abuse

## Future Enhancements

### Planned Features:
- **Machine Learning**: AI-powered drug interaction detection
- **Natural Language Processing**: Advanced prescription parsing
- **Integration APIs**: Pharmacy and healthcare system integration
- **Mobile Support**: Enhanced mobile app integration
- **Real-time Notifications**: Instant interaction warnings
- **Advanced Analytics**: Prescription pattern analysis

### Roadmap:
- **Q1 2024**: Machine learning integration
- **Q2 2024**: Advanced NLP capabilities
- **Q3 2024**: External API integrations
- **Q4 2024**: Advanced analytics dashboard

## Support and Documentation

### Resources:
- **API Documentation**: Complete API reference
- **Code Examples**: Comprehensive usage examples
- **Testing Guide**: Testing strategies and examples
- **Deployment Guide**: Production deployment instructions

### Contact:
- **Technical Support**: tech-support@medguard-sa.co.za
- **Documentation**: docs.medguard-sa.co.za
- **GitHub**: github.com/medguard-sa/medguard-backend

---

*This documentation is maintained by the MedGuard SA development team. For questions or contributions, please contact the team.* 