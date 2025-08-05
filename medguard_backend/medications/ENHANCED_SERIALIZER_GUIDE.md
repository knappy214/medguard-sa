# Enhanced Medication Serializer Guide

## Overview

The `EnhancedMedicationSerializer` provides comprehensive prescription data handling for the MedGuard SA medication management system. It includes advanced features for parsing natural language prescription instructions, validating medical codes, and managing medication schedules.

## Key Features

- **ICD-10 Code Validation**: Validates and cleans ICD-10 diagnosis codes
- **Prescription Instruction Parsing**: Extracts structured data from natural language instructions
- **Multi-Time Support**: Handles complex instructions with multiple specific times
- **Nested Schedule Creation**: Automatically creates medication schedules
- **Drug Interaction Checking**: Validates potential drug interactions
- **Contraindication Validation**: Checks for contraindications based on patient conditions

## Prescription Instruction Parsing

The serializer can parse various prescription instruction formats:

### Basic Instructions
```
"Take one tablet daily"
"Take 2 tablets twice daily"
"Take 1 capsule three times daily"
```

### Custom Time Instructions
```
"Take 2 tablets at 12h00"
"Take 1 tablet at 14:30"
"Take 1 tablet at 8h30"
```

### Multi-Time Instructions (NEW)
```
"Take 2 tablets at 8h00 and 20h00 daily"
"Take 1 tablet at 8h00, 14h00 and 20h00 daily"
"Take 1 tablet at 8:00 and 20:00 daily"
```

The parser automatically:
- Detects multiple times in instructions
- Sets frequency based on number of times (2 times = twice_daily, 3 times = three_times_daily, etc.)
- Creates separate schedules for each time
- Supports both "h" format (8h00) and colon format (8:00)
- Handles comma-separated and "and"-separated time lists

## Usage Examples

### Basic Medication Creation

```python
from medications.serializers import EnhancedMedicationSerializer

# Basic medication data
data = {
    'name': 'Paracetamol',
    'generic_name': 'Acetaminophen',
    'medication_type': 'tablet',
    'prescription_type': 'otc',
    'strength': '500mg',
    'dosage_unit': 'mg',
    'manufacturer': 'Generic Pharma'
}

serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
if serializer.is_valid():
    medication = serializer.save()
```

### Medication with ICD-10 Codes

```python
data = {
    'name': 'Warfarin',
    'generic_name': 'Warfarin sodium',
    'medication_type': 'tablet',
    'prescription_type': 'prescription',
    'strength': '5mg',
    'dosage_unit': 'mg',
    'manufacturer': 'Blood Thinner Pharma',
    'icd10_codes': ['I48.91', 'Z51.11']  # Atrial fibrillation, Encounter for antineoplastic chemotherapy
}

serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
```

### Medication with Prescription Instructions

```python
data = {
    'name': 'Amoxicillin',
    'generic_name': 'Amoxicillin trihydrate',
    'medication_type': 'capsule',
    'prescription_type': 'prescription',
    'strength': '500mg',
    'dosage_unit': 'mg',
    'manufacturer': 'Antibiotic Pharma',
    'prescription_instructions': 'Take one capsule three times daily'
}

serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
if serializer.is_valid():
    medication = serializer.save()
    # This will automatically create 3 schedules: morning, noon, night
```

### Multi-Time Prescription Instructions (NEW)

```python
# Two times daily
data = {
    'name': 'Metformin',
    'generic_name': 'Metformin hydrochloride',
    'medication_type': 'tablet',
    'prescription_type': 'prescription',
    'strength': '500mg',
    'dosage_unit': 'mg',
    'manufacturer': 'Diabetes Pharma',
    'prescription_instructions': 'Take 2 tablets at 8h00 and 20h00 daily with food'
}

serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
if serializer.is_valid():
    medication = serializer.save()
    # This will automatically create 2 schedules: 8h00 and 20h00

# Three times daily with comma separation
data = {
    'name': 'Aspirin',
    'generic_name': 'Acetylsalicylic acid',
    'medication_type': 'tablet',
    'prescription_type': 'otc',
    'strength': '100mg',
    'dosage_unit': 'mg',
    'manufacturer': 'Pain Relief Pharma',
    'prescription_instructions': 'Take 1 tablet at 8h00, 14h00 and 20h00 daily'
}

serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
if serializer.is_valid():
    medication = serializer.save()
    # This will automatically create 3 schedules: 8h00, 14h00, and 20h00
```

### Manual Schedule Configuration

```python
data = {
    'name': 'Insulin',
    'generic_name': 'Insulin glargine',
    'medication_type': 'injection',
    'prescription_type': 'prescription',
    'strength': '100units/ml',
    'dosage_unit': 'units',
    'manufacturer': 'Diabetes Pharma',
    'schedules': [
        {
            'timing': 'custom',
            'custom_time': '08:00:00',
            'dosage_amount': '10.0',
            'frequency': 'daily',
            'instructions': 'Take before breakfast'
        },
        {
            'timing': 'custom',
            'custom_time': '20:00:00',
            'dosage_amount': '8.0',
            'frequency': 'daily',
            'instructions': 'Take before dinner'
        }
    ]
}

serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
```

### Medication with Patient Conditions

```python
data = {
    'name': 'Warfarin',
    'generic_name': 'Warfarin sodium',
    'medication_type': 'tablet',
    'prescription_type': 'prescription',
    'strength': '5mg',
    'dosage_unit': 'mg',
    'manufacturer': 'Blood Thinner Pharma',
    'patient_conditions': ['pregnancy', 'liver_disease']
}

serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
if serializer.is_valid():
    medication = serializer.save()
    # This will generate contraindication warnings
```

## Prescription Instruction Patterns

The parser supports various prescription instruction patterns:

### Dosage Patterns
- "Take one tablet daily"
- "Take 2 tablets at 12h00"
- "Take 1 capsule three times daily"
- "Take 500mg twice daily"
- "Take 2.5ml four times daily"
- "Take 10mcg as needed"

### Frequency Patterns
- `daily` / `once a day` / `every day`
- `twice daily` / `two times daily` / `2x daily`
- `three times daily` / `thrice daily` / `3x daily`
- `four times daily` / `4x daily`
- `weekly` / `once a week`
- `monthly` / `once a month`
- `as needed` / `prn` / `when needed`

### Timing Patterns
- `morning` / `am` / `before breakfast`
- `noon` / `midday` / `12h00` / `12:00`
- `evening` / `pm` / `before bed` / `night`
- Custom times: `8h00`, `14:30`, `22h00`

## Schedule Generation

Based on frequency, the parser automatically generates schedules:

### Daily
- Creates 1 schedule with morning timing

### Twice Daily
- Creates 2 schedules: morning and night

### Three Times Daily
- Creates 3 schedules: morning, noon, and night

### Four Times Daily
- Creates 4 schedules with custom times: 6:00, 12:00, 18:00, 22:00

## Validation Features

### ICD-10 Code Validation
```python
# Valid codes
'A00.0', 'B01.1', 'C78.01', 'Z51.11', 'E11.9', 'I10.X1'

# Invalid codes
'A0.0', 'A000.0', 'A00', 'A00.000', 'a00.0'
```

### Strength Validation
```python
# Valid strengths
'500mg', '10mg/ml', '2.5mg', '100units/ml', '5mcg'

# Invalid strengths
'invalid', '500', 'mg', '500invalid'
```

### Cross-field Validation
- Dosage unit must match strength unit
- Prescription instructions must be parseable
- Medication type and prescription type must be valid

## Response Format

The enhanced serializer returns additional fields:

```json
{
    "id": 1,
    "name": "Test Medication",
    "generic_name": "Test Generic",
    "medication_type": "tablet",
    "prescription_type": "prescription",
    "strength": "500mg",
    "dosage_unit": "mg",
    "manufacturer": "Test Pharma",
    "icd10_codes": ["A00.0", "B01.1"],
    "prescription_instructions": "Take one tablet three times daily",
    "patient_conditions": ["diabetes"],
    "parsed_prescription": {
        "dosage_amount": "1.0",
        "dosage_unit": "tablet",
        "frequency": "three_times_daily",
        "timing": "morning",
        "custom_time": null,
        "schedules": [
            {
                "timing": "morning",
                "dosage_amount": "1.0",
                "frequency": "daily"
            },
            {
                "timing": "noon",
                "dosage_amount": "1.0",
                "frequency": "daily"
            },
            {
                "timing": "night",
                "dosage_amount": "1.0",
                "frequency": "daily"
            }
        ]
    },
    "interaction_warnings": [
        "Potential interaction between Test Medication and Aspirin"
    ],
    "contraindication_warnings": [
        "Test Medication may be contraindicated for pregnancy"
    ],
    "is_low_stock": false,
    "is_expired": false,
    "is_expiring_soon": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

## Error Handling

The serializer provides detailed error messages:

```python
# Invalid ICD-10 code
{
    "icd10_codes": [
        "Invalid ICD-10 code format: INVALID. Expected format: A00.0"
    ]
}

# Invalid strength
{
    "strength": [
        "Invalid strength format. Examples: 500mg, 10mg/ml, 2.5mg"
    ]
}

# Dosage unit mismatch
{
    "dosage_unit": [
        "Dosage unit 'ml' should match strength unit 'mg'"
    ]
}

# Unparseable instructions
{
    "prescription_instructions": [
        "Could not parse dosage amount from instructions"
    ]
}
```

## API Integration

### Creating a View

```python
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .serializers import EnhancedMedicationSerializer
from .models import Medication

class EnhancedMedicationCreateView(generics.CreateAPIView):
    serializer_class = EnhancedMedicationSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save()

class EnhancedMedicationUpdateView(generics.UpdateAPIView):
    queryset = Medication.objects.all()
    serializer_class = EnhancedMedicationSerializer
    permission_classes = [IsAuthenticated]
```

### URL Configuration

```python
from django.urls import path
from .views import EnhancedMedicationCreateView, EnhancedMedicationUpdateView

urlpatterns = [
    path('medications/enhanced/', EnhancedMedicationCreateView.as_view(), name='enhanced-medication-create'),
    path('medications/enhanced/<int:pk>/', EnhancedMedicationUpdateView.as_view(), name='enhanced-medication-update'),
]
```

## Testing

Run the comprehensive test suite:

```bash
python manage.py test medications.test_enhanced_serializers
```

The test suite covers:
- ICD-10 validation
- Prescription instruction parsing
- Schedule generation
- Drug interaction checking
- Contraindication validation
- Error handling
- API integration

## Best Practices

### 1. Always Validate Input
```python
serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
if not serializer.is_valid():
    return Response(serializer.errors, status=400)
```

### 2. Handle Warnings Appropriately
```python
medication = serializer.save()
warnings = {
    'interactions': serializer.get_interaction_warnings(medication),
    'contraindications': serializer.get_contraindication_warnings(medication)
}
```

### 3. Use Appropriate Context
```python
# Always provide request context for user-specific features
serializer = EnhancedMedicationSerializer(data=data, context={'request': request})
```

### 4. Handle Complex Instructions
```python
# For complex instructions, consider manual schedule configuration
data = {
    'prescription_instructions': 'Take 2 tablets at 8h00 and 20h00 daily with food',
    # Or use manual schedules for more control
    'schedules': [
        {'timing': 'custom', 'custom_time': '08:00:00', 'dosage_amount': '2.0'},
        {'timing': 'custom', 'custom_time': '20:00:00', 'dosage_amount': '2.0'}
    ]
}
```

### 5. Validate Patient Conditions
```python
# Always validate patient conditions before medication assignment
if 'pregnancy' in patient_conditions and medication_name.lower() == 'warfarin':
    # Handle contraindication
    pass
```

## Extending the Serializer

### Adding New Drug Interactions

```python
class MedicationInteractionValidator:
    KNOWN_INTERACTIONS = {
        'warfarin': ['aspirin', 'ibuprofen', 'naproxen', 'heparin'],
        'digoxin': ['furosemide', 'spironolactone', 'quinidine'],
        # Add new interactions here
        'new_medication': ['interacting_drug1', 'interacting_drug2']
    }
```

### Adding New Contraindications

```python
class MedicationInteractionValidator:
    CONTRAINDICATIONS = {
        'pregnancy': ['warfarin', 'isotretinoin', 'thalidomide', 'methotrexate'],
        'liver_disease': ['acetaminophen', 'statins', 'methotrexate'],
        # Add new contraindications here
        'new_condition': ['contraindicated_drug1', 'contraindicated_drug2']
    }
```

### Custom Prescription Patterns

```python
class PrescriptionParser:
    # Add new dosage patterns
    DOSAGE_PATTERNS = [
        r'take\s+(\d+(?:\.\d+)?)\s+(tablet|tablets|capsule|capsules|ml|mg|mcg|drops?|puffs?)',
        # Add custom patterns here
        r'(\d+(?:\.\d+)?)\s+(custom_unit)\s+to\s+take',
    ]
    
    # Add new frequency patterns
    FREQUENCY_PATTERNS = [
        (r'daily|once\s+a\s+day|every\s+day', 'daily'),
        # Add custom patterns here
        (r'every\s+(\d+)\s+hours?', 'custom_hourly'),
    ]
```

## Security Considerations

1. **Input Validation**: All user input is validated and sanitized
2. **SQL Injection**: Uses Django ORM to prevent SQL injection
3. **XSS Protection**: Output is properly escaped
4. **Authentication**: Requires user authentication for all operations
5. **Authorization**: Implement appropriate permissions for medication access

## Performance Considerations

1. **Database Queries**: Minimizes database queries through efficient ORM usage
2. **Caching**: Consider caching parsed prescription data for frequently used medications
3. **Batch Operations**: For bulk medication creation, consider batch processing
4. **Indexing**: Ensure proper database indexing for medication queries

## Troubleshooting

### Common Issues

1. **ICD-10 Validation Fails**
   - Ensure codes follow the pattern: [A-Z][0-9][0-9].[0-9X][0-9X]?
   - Check for extra spaces or invalid characters

2. **Prescription Instructions Not Parsed**
   - Verify instructions follow supported patterns
   - Check for typos or unusual formatting
   - Consider using manual schedule configuration

3. **Schedules Not Created**
   - Ensure prescription instructions are parseable
   - Check that frequency patterns are recognized
   - Verify user context is provided

4. **Interaction Warnings Not Generated**
   - Ensure user has existing medication schedules
   - Check that medication names match interaction database
   - Verify request context is provided

### Debug Mode

Enable debug mode for detailed parsing information:

```python
import logging
logging.getLogger('medications.serializers').setLevel(logging.DEBUG)
```

## Support

For issues or questions about the enhanced medication serializer:

1. Check the test suite for usage examples
2. Review the validation error messages
3. Consult the Django REST Framework documentation
4. Contact the development team for complex issues 