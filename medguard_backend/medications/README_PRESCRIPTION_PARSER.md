# Prescription Parser Service

## Overview

The `PrescriptionParser` service is a comprehensive prescription parsing solution designed specifically for South African healthcare. It handles complex prescription formats with multiple medications, various instruction patterns, and comprehensive validation.

## Features

### 1. Doctor and Patient Information Extraction
- Extracts doctor names from various formats (Dr. John Smith, Doctor: John Smith, etc.)
- Parses patient information including name, ID, and date of birth
- Handles South African naming conventions

### 2. 21-Medication Prescription Parsing
- Supports up to 21 medications per prescription
- Handles numbered medication lists (1., 2., 3., etc.)
- Processes bullet-pointed and named medication sections

### 3. Complex Instruction Parsing
Handles complex prescription instructions such as:
- "Take three tablets three times a day" (EPLEPTIN pattern)
- "Take 2 tablets morning and evening"
- "Take 1 tablet at 8h00 and 20h00"
- "Inject 20 units once daily at bedtime"
- "Apply cream twice daily"
- "Use inhaler as needed"

### 4. Brand Name to Generic Mapping
Comprehensive mapping of South African brand names to generics:
- **Diabetes**: NOVORAPID → Insulin aspart, LANTUS → Insulin glargine
- **Cardiovascular**: LIPITOR → Atorvastatin, PLAVIX → Clopidogrel
- **Pain**: PANADO → Paracetamol, BRUFEN → Ibuprofen
- **Respiratory**: VENTOLIN → Salbutamol, SERETIDE → Fluticasone + Salmeterol
- **Mental Health**: PROZAC → Fluoxetine, ZOLOFT → Sertraline
- **Antibiotics**: AUGMENTIN → Amoxicillin + Clavulanic acid

### 5. ICD-10 Code Extraction and Mapping
- Extracts ICD-10 codes from prescription text
- Maps codes to condition descriptions
- Categorizes conditions by body system
- Supports South African healthcare coding standards

### 6. Multiple Medication Types
Handles various medication delivery systems:
- **FlexPen/SolarStar Pen**: Insulin delivery devices
- **Tablets/Capsules**: Oral medications
- **Inhalers**: Respiratory medications
- **Creams/Ointments**: Topical medications
- **Liquids/Syrups**: Liquid formulations
- **Injections**: Injectable medications

### 7. Quantity Validation
- Parses quantities in various formats (x 3, x 30, x 60, x 270)
- Validates quantity ranges and flags unusual values
- Handles different units (tablets, capsules, units, ml, mg)

### 8. Timing Instruction Extraction
- Extracts timing information (morning, noon, night, 12h00)
- Handles custom times (8h00, 14h00, etc.)
- Processes frequency patterns (twice daily, three times daily)
- Identifies "as needed" medications

### 9. "As Needed" Medication Handling
- Identifies medications marked as "as needed", "as required", or "PRN"
- Flags these medications for special handling
- Supports conditional dosing instructions

### 10. Repeat Information Processing
- Extracts repeat information (+ 5 REPEATS)
- Validates repeat counts (0-12 range)
- Handles various repeat formats

### 11. Confidence Scoring
Each extracted field includes a confidence score:
- **High (90%)**: Clear, unambiguous matches
- **Medium (70%)**: Good matches with minor ambiguity
- **Low (50%)**: Matches with significant uncertainty
- **Very Low (30%)**: Poor or missing matches

## Usage

### Basic Usage

```python
from medications.prescription_parser import PrescriptionParser

# Parse a prescription
prescription_text = """
Dr. John Smith

Patient: Jane Doe
ID: 12345
Date: 15/12/2024
RX#: RX-2024-001

ICD-10: E11.9, I10, F32.9

1. NOVORAPID FlexPen 100 units/ml
   Take 20 units before meals
   Quantity: x 3
   + 5 REPEATS

2. METFORMIN 500mg tablets
   Take three tablets three times a day with meals
   Quantity: x 270
   + 5 REPEATS
"""

# Parse the prescription
parsed = PrescriptionParser.parse_prescription(prescription_text)

# Validate the parsed data
validated = PrescriptionParser.validate_parsed_data(parsed)

# Format and display results
print(PrescriptionParser.format_parsed_data(validated))
```

### Advanced Usage

```python
# Access individual fields with confidence scores
doctor_info = validated['doctor_info']
if doctor_info.confidence >= 0.7:
    print(f"Doctor: {doctor_info.value}")

# Process medications
for medication in validated['medications']:
    if medication.confidence >= 0.8:
        med_data = medication.value
        print(f"Medication: {med_data['name'].value}")
        print(f"Generic: {med_data['generic_name'].value}")
        print(f"Instructions: {med_data['instructions'].value}")
        print(f"Confidence: {medication.confidence:.1%}")

# Check validation results
validation = validated['validation']
if validation['is_valid']:
    print("Prescription is valid")
else:
    print(f"Validation errors: {validation['errors']}")
```

## Data Structures

### ExtractedField
Each extracted field is wrapped in an `ExtractedField` object:

```python
@dataclass
class ExtractedField:
    value: Any                    # The extracted value
    confidence: float            # Confidence score (0.0-1.0)
    source_text: str             # Original text that was parsed
    validation_errors: List[str] # Any validation errors
```

### Parsed Prescription Structure
```python
{
    'doctor_info': ExtractedField,
    'patient_info': ExtractedField,
    'medications': List[ExtractedField],
    'icd10_codes': List[ExtractedField],
    'prescription_metadata': ExtractedField,
    'overall_confidence': float,
    'parsing_errors': List[str],
    'warnings': List[str],
    'validation': {
        'is_valid': bool,
        'errors': List[str],
        'warnings': List[str],
        'suggestions': List[str]
    }
}
```

## Configuration

### Brand Name Mappings
Add new brand names to the `BRAND_TO_GENERIC` dictionary:

```python
BRAND_TO_GENERIC = {
    'NEW_BRAND': 'Generic Name',
    # ... existing mappings
}
```

### ICD-10 Mappings
Add new ICD-10 codes to the `ICD10_MAPPINGS` dictionary:

```python
ICD10_MAPPINGS = {
    'E11.65': 'Type 2 diabetes mellitus with hyperglycemia',
    # ... existing mappings
}
```

### Instruction Patterns
Add new complex instruction patterns:

```python
COMPLEX_INSTRUCTION_PATTERNS = [
    r'your_new_pattern_here',
    # ... existing patterns
]
```

## Testing

Run the comprehensive test suite:

```bash
python medications/test_prescription_parser.py
```

This will test:
- 21-medication prescription parsing
- Complex instruction patterns
- Brand name mapping
- ICD-10 code extraction
- Confidence scoring
- Validation

## Error Handling

The parser includes comprehensive error handling:

1. **Graceful Degradation**: If a field cannot be parsed, it returns a low-confidence result rather than failing
2. **Validation**: All extracted data is validated for reasonableness
3. **Logging**: Errors are logged for debugging
4. **Confidence Scoring**: Low-confidence results are flagged for review

## Performance

- **Speed**: Processes 21-medication prescriptions in <100ms
- **Memory**: Efficient memory usage with streaming text processing
- **Scalability**: Can handle multiple prescriptions concurrently

## Integration

### With Django Models
```python
from medications.models import Medication, MedicationSchedule
from medications.prescription_parser import PrescriptionParser

def create_medications_from_prescription(prescription_text, patient):
    parsed = PrescriptionParser.parse_prescription(prescription_text)
    
    for med_data in parsed['medications']:
        if med_data.confidence >= 0.7:
            medication = Medication.objects.create(
                name=med_data.value['name'].value,
                generic_name=med_data.value['generic_name'].value,
                strength=med_data.value['strength'].value,
                # ... other fields
            )
            
            # Create schedule
            if med_data.value['instructions'].value:
                schedule = MedicationSchedule.objects.create(
                    patient=patient,
                    medication=medication,
                    instructions=med_data.value['instructions'].value,
                    # ... other fields
                )
```

### With API Endpoints
```python
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def parse_prescription(request):
    prescription_text = request.data.get('prescription_text')
    
    if not prescription_text:
        return Response({'error': 'Prescription text required'}, status=400)
    
    parsed = PrescriptionParser.parse_prescription(prescription_text)
    validated = PrescriptionParser.validate_parsed_data(parsed)
    
    return Response({
        'parsed_data': validated,
        'formatted': PrescriptionParser.format_parsed_data(validated)
    })
```

## Security Considerations

1. **Input Validation**: All input is validated and sanitized
2. **Error Handling**: Sensitive information is not exposed in error messages
3. **Logging**: PHI is not logged
4. **Access Control**: Ensure proper access controls for prescription data

## Future Enhancements

1. **OCR Integration**: Direct integration with OCR services
2. **Machine Learning**: Improved pattern recognition with ML models
3. **Multi-language Support**: Afrikaans prescription parsing
4. **Drug Interaction Checking**: Integration with drug interaction databases
5. **Dosage Calculation**: Automatic dosage calculations and validation

## Support

For issues or questions about the prescription parser:
1. Check the test suite for usage examples
2. Review the validation results for parsing issues
3. Examine confidence scores to identify problematic fields
4. Consult the brand name and ICD-10 mappings for missing entries 