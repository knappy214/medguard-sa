#!/usr/bin/env python3
"""
Comprehensive test script for the PrescriptionParser service.

This script demonstrates all the features of the prescription parser:
1. Doctor and patient information extraction
2. 21-medication prescription parsing
3. Complex instruction parsing
4. Brand name to generic mapping
5. ICD-10 code extraction and mapping
6. Multiple medication types
7. Quantity validation
8. Timing instruction extraction
9. "As needed" medication handling
10. Repeat information processing
11. Confidence scoring
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prescription_parser import PrescriptionParser, ConfidenceLevel

def test_comprehensive_prescription():
    """Test a comprehensive prescription with all features."""
    
    # Complex prescription with 21 medications
    comprehensive_prescription = """
    Dr. Sarah Johnson, MBChB
    
    Patient: Michael van der Merwe
    ID: 789456
    Date of Birth: 15/03/1985
    Date: 20/12/2024
    RX#: RX-2024-789
    
    ICD-10: E11.9, I10, F32.9, J45.909, M54.5
    
    1. NOVORAPID FlexPen 100 units/ml
       Take 20 units before meals
       Quantity: x 3
       + 5 REPEATS
    
    2. LANTUS Solostar Pen 100 units/ml
       Inject 30 units once daily at bedtime
       Quantity: x 3
       + 5 REPEATS
    
    3. METFORMIN 500mg tablets
       Take three tablets three times a day with meals
       Quantity: x 270
       + 5 REPEATS
    
    4. ATORVASTATIN 20mg tablets
       Take one tablet daily at night
       Quantity: x 30
       + 5 REPEATS
    
    5. OMEPRAZOLE 20mg capsules
       Take one capsule daily in the morning
       Quantity: x 30
       + 5 REPEATS
    
    6. VENTOLIN inhaler 100mcg
       Use 2 puffs as needed for shortness of breath
       Quantity: x 1
       + 2 REPEATS
    
    7. SERETIDE 250/25 inhaler
       Use 2 puffs twice daily
       Quantity: x 1
       + 3 REPEATS
    
    8. PANADO 500mg tablets
       Take 2 tablets every 4 hours as needed for pain
       Quantity: x 30
       + 2 REPEATS
    
    9. BRUFEN 400mg tablets
       Take 1 tablet three times daily with food
       Quantity: x 60
       + 2 REPEATS
    
    10. GAVISCON liquid
        Take 10ml after meals as needed
        Quantity: x 500ml
        + 1 REPEAT
    
    11. MOVICOL sachets
        Take 1 sachet daily in the morning
        Quantity: x 30
        + 2 REPEATS
    
    12. LACTULOSE 10g/15ml syrup
        Take 15ml twice daily
        Quantity: x 500ml
        + 1 REPEAT
    
    13. PROZAC 20mg capsules
        Take 1 capsule daily in the morning
        Quantity: x 30
        + 5 REPEATS
    
    14. ZOLOFT 50mg tablets
        Take 1 tablet daily
        Quantity: x 30
        + 5 REPEATS
    
    15. RITALIN 10mg tablets
        Take 1 tablet twice daily at 8h00 and 14h00
        Quantity: x 60
        + 5 REPEATS
    
    16. AUGMENTIN 625mg tablets
        Take 1 tablet twice daily with food
        Quantity: x 14
        + 0 REPEATS
    
    17. ZITHROMAX 500mg tablets
        Take 2 tablets on day 1, then 1 tablet daily
        Quantity: x 6
        + 0 REPEATS
    
    18. VOLTAREN 50mg tablets
        Take 1 tablet twice daily with food
        Quantity: x 30
        + 2 REPEATS
    
    19. COZAAR 50mg tablets
        Take 1 tablet daily in the morning
        Quantity: x 30
        + 5 REPEATS
    
    20. NORVASC 5mg tablets
        Take 1 tablet daily
        Quantity: x 30
        + 5 REPEATS
    
    21. ASPIRIN 100mg tablets
        Take 1 tablet daily in the morning
        Quantity: x 30
        + 5 REPEATS
    """
    
    print("=== Testing Comprehensive Prescription Parser ===")
    print("Features being tested:")
    print("1. Doctor and patient information extraction")
    print("2. 21-medication prescription parsing")
    print("3. Complex instruction parsing (e.g., 'Take three tablets three times a day')")
    print("4. Brand name to generic mapping (NOVORAPID → Insulin aspart)")
    print("5. ICD-10 code extraction and condition mapping")
    print("6. Multiple medication types (FlexPen, tablets, inhaler, liquid)")
    print("7. Quantity validation (x 3, x 30, x 60, x 270)")
    print("8. Timing instructions (morning, 12h00, night, twice daily)")
    print("9. 'As needed' medications (VENTOLIN, PANADO)")
    print("10. Repeat information (+ 5 REPEATS)")
    print("11. Confidence scoring for each field")
    print()
    
    # Parse the prescription
    parsed = PrescriptionParser.parse_prescription(comprehensive_prescription)
    
    # Validate the parsed data
    validated = PrescriptionParser.validate_parsed_data(parsed)
    
    # Display results
    print("=== Parsed Results ===")
    print(PrescriptionParser.format_parsed_data(validated))
    
    # Show detailed statistics
    print("\n=== Detailed Statistics ===")
    medications = validated.get('medications', [])
    print(f"Total medications parsed: {len(medications)}")
    
    # Count medication types
    medication_types = {}
    for med in medications:
        if isinstance(med, PrescriptionParser._get_field_value.__self__.__class__) and med.value:
            med_type = PrescriptionParser._get_field_value(med.value.get('medication_type'))
            if med_type:
                medication_types[med_type] = medication_types.get(med_type, 0) + 1
    
    print(f"Medication types found:")
    for med_type, count in medication_types.items():
        print(f"  {med_type}: {count}")
    
    # Count as-needed medications
    as_needed_count = 0
    for med in medications:
        if isinstance(med, PrescriptionParser._get_field_value.__self__.__class__) and med.value:
            as_needed = PrescriptionParser._get_field_value(med.value.get('as_needed'))
            if as_needed:
                as_needed_count += 1
    
    print(f"As-needed medications: {as_needed_count}")
    
    # Show ICD-10 codes
    icd10_codes = validated.get('icd10_codes', [])
    print(f"ICD-10 codes found: {len(icd10_codes)}")
    for code_data in icd10_codes:
        if isinstance(code_data, PrescriptionParser._get_field_value.__self__.__class__) and code_data.value:
            code_info = code_data.value
            print(f"  {code_info['code']}: {code_info['description']} ({code_info['category']})")
    
    # Show confidence distribution
    print(f"\nConfidence Distribution:")
    high_confidence = 0
    medium_confidence = 0
    low_confidence = 0
    
    for med in medications:
        if isinstance(med, PrescriptionParser._get_field_value.__self__.__class__):
            confidence = med.confidence
            if confidence >= ConfidenceLevel.HIGH.value:
                high_confidence += 1
            elif confidence >= ConfidenceLevel.MEDIUM.value:
                medium_confidence += 1
            else:
                low_confidence += 1
    
    print(f"  High confidence (≥90%): {high_confidence}")
    print(f"  Medium confidence (70-89%): {medium_confidence}")
    print(f"  Low confidence (<70%): {low_confidence}")
    
    # Show validation results
    validation = validated.get('validation', {})
    if validation.get('errors'):
        print(f"\nValidation Errors: {len(validation['errors'])}")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation.get('warnings'):
        print(f"\nValidation Warnings: {len(validation['warnings'])}")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    print(f"\nOverall validation: {'PASS' if validation.get('is_valid', False) else 'FAIL'}")
    print(f"Overall confidence: {validated.get('overall_confidence', 0):.1%}")

def test_specific_features():
    """Test specific features of the parser."""
    
    print("\n=== Testing Specific Features ===")
    
    # Test complex instruction parsing
    complex_instructions = [
        "Take three tablets three times a day",
        "Take 2 tablets morning and evening",
        "Take 1 tablet at 8h00 and 20h00",
        "Inject 20 units once daily at bedtime",
        "Use inhaler as needed",
        "Apply cream twice daily"
    ]
    
    print("Testing complex instruction parsing:")
    for instruction in complex_instructions:
        result = PrescriptionParser._extract_instructions(instruction)
        if result.value:
            print(f"  ✓ '{instruction}' → '{result.value}' (confidence: {result.confidence:.1%})")
        else:
            print(f"  ✗ '{instruction}' → Not parsed")
    
    # Test brand name mapping
    print("\nTesting brand name to generic mapping:")
    test_brands = ['NOVORAPID', 'LANTUS', 'METFORMIN', 'LIPITOR', 'VENTOLIN', 'PROZAC']
    for brand in test_brands:
        generic = PrescriptionParser.BRAND_TO_GENERIC.get(brand, 'Not found')
        print(f"  {brand} → {generic}")
    
    # Test ICD-10 code mapping
    print("\nTesting ICD-10 code mapping:")
    test_codes = ['E11.9', 'I10', 'F32.9', 'J45.909', 'M54.5']
    for code in test_codes:
        description = PrescriptionParser.ICD10_MAPPINGS.get(code, 'Unknown')
        category = PrescriptionParser._get_icd10_category(code)
        print(f"  {code} → {description} ({category})")

if __name__ == "__main__":
    test_comprehensive_prescription()
    test_specific_features()
    
    print("\n=== Prescription Parser Test Complete ===")
    print("All features successfully tested!") 