#!/usr/bin/env python
"""
Simple test script for enhanced serializer components.
This script tests the core functionality without requiring the full Django test environment.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import time

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

# Now we can import our components
from medications.serializers import ICD10Validator, PrescriptionParser, MedicationInteractionValidator

def test_icd10_validator():
    """Test ICD-10 validator functionality."""
    print("Testing ICD-10 Validator...")
    
    # Test valid codes
    valid_codes = ['A00.0', 'B01.1', 'C78.01', 'Z51.11', 'E11.9', 'I10.X1']
    for code in valid_codes:
        result = ICD10Validator.validate(code)
        print(f"  {code}: {result}")
        assert result, f"ICD-10 code {code} should be valid"
    
    # Test invalid codes
    invalid_codes = ['A0.0', 'A000.0', 'A00', 'A00.000']
    for code in invalid_codes:
        result = ICD10Validator.validate(code)
        print(f"  {code}: {result}")
        assert not result, f"ICD-10 code {code} should be invalid"
    
    # Test cleaning
    test_cases = [
        ('a00.0', 'A00.0'),
        ('  B01.1  ', 'B01.1'),
        ('c78.01', 'C78.01'),
    ]
    for input_code, expected in test_cases:
        result = ICD10Validator.clean(input_code)
        print(f"  Clean '{input_code}' -> '{result}'")
        assert result == expected, f"Cleaning failed for {input_code}"
    
    print("✓ ICD-10 Validator tests passed!\n")

def test_prescription_parser():
    """Test prescription parser functionality."""
    print("Testing Prescription Parser...")
    
    # Test dosage extraction
    test_cases = [
        ('Take one tablet daily', Decimal('1'), 'tablet'),
        ('Take 2 tablets at 12h00', Decimal('2'), 'tablets'),
        ('Take 1 capsule three times daily', Decimal('1'), 'capsule'),
        ('Take 500mg twice daily', Decimal('500'), 'mg'),
        ('Take 2.5ml four times daily', Decimal('2.5'), 'ml'),
    ]
    
    for instructions, expected_amount, expected_unit in test_cases:
        parsed = PrescriptionParser.parse_instructions(instructions)
        print(f"  '{instructions}' -> Amount: {parsed['dosage_amount']}, Unit: {parsed['dosage_unit']} (expected: {expected_unit})")
        assert parsed['dosage_amount'] == expected_amount, f"Dosage amount mismatch for '{instructions}'"
        assert parsed['dosage_unit'] == expected_unit, f"Dosage unit mismatch for '{instructions}'"
    
    # Test frequency extraction
    frequency_tests = [
        ('Take one tablet daily', 'daily'),
        ('Take two tablets twice daily', 'twice_daily'),
        ('Take 1 capsule three times daily', 'three_times_daily'),
        ('Take 2 tablets four times daily', 'four_times_daily'),
    ]
    
    for instructions, expected_frequency in frequency_tests:
        parsed = PrescriptionParser.parse_instructions(instructions)
        print(f"  '{instructions}' -> Frequency: {parsed['frequency']}")
        assert parsed['frequency'] == expected_frequency, f"Frequency mismatch for '{instructions}'"
    
    # Test timing extraction
    timing_tests = [
        ('Take one tablet in the morning', 'morning'),
        ('Take two tablets at noon', 'noon'),
        ('Take 1 capsule in the evening', 'night'),
        ('Take 2 tablets at 12h00', 'custom'),
    ]
    
    for instructions, expected_timing in timing_tests:
        parsed = PrescriptionParser.parse_instructions(instructions)
        print(f"  '{instructions}' -> Timing: {parsed['timing']}")
        assert parsed['timing'] == expected_timing, f"Timing mismatch for '{instructions}'"
    
    # Test custom time extraction
    time_tests = [
        ('Take 2 tablets at 12h00', time(12, 0)),
        ('Take 1 tablet at 14:30', time(14, 30)),
        ('Take 1 tablet at 8h30', time(8, 30)),
    ]
    
    for instructions, expected_time in time_tests:
        parsed = PrescriptionParser.parse_instructions(instructions)
        print(f"  '{instructions}' -> Custom time: {parsed['custom_time']}")
        assert parsed['custom_time'] == expected_time, f"Custom time mismatch for '{instructions}'"
    
    # Test schedule generation
    schedule_tests = [
        ('Take one tablet daily', 1),
        ('Take two tablets twice daily', 2),
        ('Take 1 capsule three times daily', 3),
        ('Take 2 tablets four times daily', 4),
    ]
    
    for instructions, expected_count in schedule_tests:
        parsed = PrescriptionParser.parse_instructions(instructions)
        print(f"  '{instructions}' -> {len(parsed['schedules'])} schedules")
        assert len(parsed['schedules']) == expected_count, f"Schedule count mismatch for '{instructions}'"
    
    print("✓ Prescription Parser tests passed!\n")

def test_medication_interaction_validator():
    """Test medication interaction validator functionality."""
    print("Testing Medication Interaction Validator...")
    
    # Test drug interactions
    interactions = MedicationInteractionValidator.check_interactions(
        'warfarin', ['aspirin', 'paracetamol', 'ibuprofen']
    )
    print(f"  Warfarin interactions: {interactions}")
    assert 'Potential interaction between warfarin and aspirin' in interactions
    assert 'Potential interaction between warfarin and ibuprofen' in interactions
    assert 'Potential interaction between warfarin and paracetamol' not in interactions
    
    # Test digoxin interactions
    interactions = MedicationInteractionValidator.check_interactions(
        'digoxin', ['furosemide', 'vitamin_d', 'spironolactone']
    )
    print(f"  Digoxin interactions: {interactions}")
    assert 'Potential interaction between digoxin and furosemide' in interactions
    assert 'Potential interaction between digoxin and spironolactone' in interactions
    
    # Test contraindications
    contraindications = MedicationInteractionValidator.check_contraindications(
        'warfarin', ['pregnancy', 'diabetes']
    )
    print(f"  Warfarin contraindications: {contraindications}")
    assert 'warfarin may be contraindicated for pregnancy' in contraindications
    
    # Test liver disease contraindications
    contraindications = MedicationInteractionValidator.check_contraindications(
        'acetaminophen', ['liver_disease', 'hypertension']
    )
    print(f"  Acetaminophen contraindications: {contraindications}")
    assert 'acetaminophen may be contraindicated for liver_disease' in contraindications
    
    # Test no interactions
    interactions = MedicationInteractionValidator.check_interactions(
        'vitamin_d', ['paracetamol', 'vitamin_c']
    )
    print(f"  Vitamin D interactions: {interactions}")
    assert len(interactions) == 0
    
    contraindications = MedicationInteractionValidator.check_contraindications(
        'vitamin_d', ['diabetes', 'hypertension']
    )
    print(f"  Vitamin D contraindications: {contraindications}")
    assert len(contraindications) == 0
    
    print("✓ Medication Interaction Validator tests passed!\n")

def test_complex_instructions():
    """Test complex prescription instructions."""
    print("Testing Complex Instructions...")
    
    # Test complex instruction
    instructions = "Take 2 tablets at 8h00 and 20h00 daily with food"
    parsed = PrescriptionParser.parse_instructions(instructions)
    
    print(f"  Complex instruction: '{instructions}'")
    print(f"    Dosage amount: {parsed['dosage_amount']}")
    print(f"    Dosage unit: {parsed['dosage_unit']}")
    print(f"    Frequency: {parsed['frequency']}")
    print(f"    Schedules: {len(parsed['schedules'])}")
    
    assert parsed['dosage_amount'] == Decimal('2')
    assert parsed['dosage_unit'] == 'tablets'
    assert parsed['frequency'] == 'twice_daily'
    assert len(parsed['schedules']) == 2
    
    # Test three times daily
    instructions = "Take 1 tablet at 8h00, 14h00 and 20h00 daily"
    parsed = PrescriptionParser.parse_instructions(instructions)
    
    print(f"  Three times instruction: '{instructions}'")
    print(f"    Frequency: {parsed['frequency']}")
    print(f"    Schedules: {len(parsed['schedules'])}")
    
    assert parsed['frequency'] == 'three_times_daily'
    assert len(parsed['schedules']) == 3
    
    # Test with colon format
    instructions = "Take 1 tablet at 8:00 and 20:00 daily"
    parsed = PrescriptionParser.parse_instructions(instructions)
    
    print(f"  Colon format instruction: '{instructions}'")
    print(f"    Frequency: {parsed['frequency']}")
    print(f"    Schedules: {len(parsed['schedules'])}")
    
    assert parsed['frequency'] == 'twice_daily'
    assert len(parsed['schedules']) == 2
    
    print("✓ Complex Instructions tests passed!\n")

def main():
    """Run all tests."""
    print("Enhanced Medication Serializer Component Tests")
    print("=" * 50)
    
    try:
        test_icd10_validator()
        test_prescription_parser()
        test_medication_interaction_validator()
        test_complex_instructions()
        
        print("🎉 All tests passed successfully!")
        print("\nThe enhanced medication serializer components are working correctly.")
        print("Key features validated:")
        print("- ICD-10 code validation and cleaning")
        print("- Prescription instruction parsing")
        print("- Dosage, frequency, and timing extraction")
        print("- Schedule generation")
        print("- Drug interaction checking")
        print("- Contraindication validation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main()) 