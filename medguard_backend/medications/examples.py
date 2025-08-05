"""
Examples demonstrating the enhanced medication serializers.

This file shows how to use the new PrescriptionBulkCreateSerializer and
EnhancedMedicationSerializer with all their features.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from .serializers import (
    PrescriptionBulkCreateSerializer, EnhancedMedicationSerializer,
    ICD10Validator, PrescriptionParser, MedicationInteractionValidator,
    StrengthUnitNormalizer, SouthAfricanManufacturerValidator,
    PrescriptionRenewalCalculator, StockDeductionManager
)


def example_icd10_validation():
    """Example of ICD-10 code validation and mapping."""
    print("=== ICD-10 Code Validation Examples ===")
    
    # Valid ICD-10 codes
    valid_codes = ['E10.4', 'F90.9', 'I10', 'J45.901', 'M79.3']
    
    for code in valid_codes:
        is_valid = ICD10Validator.validate(code)
        description = ICD10Validator.get_description(code)
        category = ICD10Validator.get_category(code)
        
        print(f"Code: {code}")
        print(f"  Valid: {is_valid}")
        print(f"  Description: {description}")
        print(f"  Category: {category}")
        print()
    
    # Invalid codes
    invalid_codes = ['E10', 'F90.99', 'INVALID', '123.45']
    
    for code in invalid_codes:
        is_valid = ICD10Validator.validate(code)
        print(f"Code: {code} - Valid: {is_valid}")


def example_prescription_parsing():
    """Example of prescription instruction parsing."""
    print("\n=== Prescription Parsing Examples ===")
    
    instructions = [
        "Take one tablet daily",
        "Take two tablets at 12h00",
        "Take 1 capsule three times daily",
        "Take 2 tablets morning and evening",
        "Inject 20 units once daily at bedtime",
        "Take 500mg at 8h00, 14h00 and 20h00"
    ]
    
    for instruction in instructions:
        print(f"Instruction: {instruction}")
        parsed = PrescriptionParser.parse_instructions(instruction)
        
        print(f"  Dosage: {parsed.get('dosage_amount')} {parsed.get('dosage_unit')}")
        print(f"  Frequency: {parsed.get('frequency')}")
        print(f"  Timing: {parsed.get('timing')}")
        print(f"  Custom times: {parsed.get('custom_times')}")
        print(f"  Confidence: {parsed.get('parsed_confidence', 0):.2f}")
        print(f"  Errors: {parsed.get('parsing_errors', [])}")
        print()


def example_strength_normalization():
    """Example of strength unit normalization."""
    print("\n=== Strength Unit Normalization Examples ===")
    
    strengths = [
        "500mg",
        "10mg/ml",
        "2.5mg",
        "100 units",
        "1000IU",
        "5ml",
        "2.5mcg",
        "50mg/ml"
    ]
    
    for strength in strengths:
        normalized = StrengthUnitNormalizer.normalize_strength(strength)
        is_valid = StrengthUnitNormalizer.validate_strength_format(strength)
        
        print(f"Original: {strength}")
        print(f"  Normalized: {normalized}")
        print(f"  Valid: {is_valid}")
        print()


def example_manufacturer_validation():
    """Example of South African manufacturer validation."""
    print("\n=== Manufacturer Validation Examples ===")
    
    manufacturers = [
        "Novo Nordisk",
        "Aspen Pharmacare",
        "Dis-Chem",
        "Unknown Company",
        "Pfizer",
        "GSK"
    ]
    
    for manufacturer in manufacturers:
        is_valid = SouthAfricanManufacturerValidator.validate_manufacturer(manufacturer)
        standardized = SouthAfricanManufacturerValidator.get_standardized_name(manufacturer)
        manufacturer_type = SouthAfricanManufacturerValidator.get_manufacturer_type(manufacturer)
        
        print(f"Manufacturer: {manufacturer}")
        print(f"  Valid: {is_valid}")
        print(f"  Standardized: {standardized}")
        print(f"  Type: {manufacturer_type}")
        print()


def example_drug_interactions():
    """Example of drug interaction checking."""
    print("\n=== Drug Interaction Examples ===")
    
    # Example patient with existing medications
    existing_medications = ['Aspirin', 'Metformin', 'Lisinopril']
    
    # New medications to check
    new_medications = ['Warfarin', 'Digoxin', 'Insulin']
    
    for new_med in new_medications:
        interactions = MedicationInteractionValidator.check_interactions(new_med, existing_medications)
        
        print(f"Checking interactions for: {new_med}")
        if interactions:
            for interaction in interactions:
                print(f"  ⚠️  {interaction['description']}")
                print(f"     Severity: {interaction['severity']}")
                print(f"     Recommendation: {interaction['recommendation']}")
        else:
            print("  ✅ No interactions detected")
        print()


def example_contraindications():
    """Example of contraindication checking."""
    print("\n=== Contraindication Examples ===")
    
    # Example patient conditions
    patient_conditions = ['pregnancy', 'liver_disease', 'diabetes']
    
    # Medications to check
    medications = ['Warfarin', 'Acetaminophen', 'Corticosteroids']
    
    for medication in medications:
        contraindications = MedicationInteractionValidator.check_contraindications(medication, patient_conditions)
        
        print(f"Checking contraindications for: {medication}")
        if contraindications:
            for contraindication in contraindications:
                print(f"  ⚠️  {contraindication['description']}")
                print(f"     Severity: {contraindication['severity']}")
                print(f"     Recommendation: {contraindication['recommendation']}")
        else:
            print("  ✅ No contraindications detected")
        print()


def example_renewal_calculation():
    """Example of prescription renewal date calculation."""
    print("\n=== Renewal Date Calculation Examples ===")
    
    scenarios = [
        {'quantity': 30, 'frequency': 'daily', 'dosage': 1},
        {'quantity': 60, 'frequency': 'twice_daily', 'dosage': 1},
        {'quantity': 90, 'frequency': 'three_times_daily', 'dosage': 1},
        {'quantity': 7, 'frequency': 'weekly', 'dosage': 1},
    ]
    
    for scenario in scenarios:
        renewal_date = PrescriptionRenewalCalculator.calculate_renewal_date(
            quantity=scenario['quantity'],
            frequency=scenario['frequency'],
            dosage_amount=Decimal(str(scenario['dosage']))
        )
        
        print(f"Quantity: {scenario['quantity']}, Frequency: {scenario['frequency']}")
        print(f"  Renewal date: {renewal_date}")
        print(f"  Days from now: {(renewal_date - timezone.now().date()).days}")
        print()


def example_bulk_prescription_data():
    """Example data for bulk prescription creation."""
    print("\n=== Bulk Prescription Data Example ===")
    
    bulk_prescription_data = {
        "prescription_number": "RX-2024-001",
        "prescribing_doctor": "Dr. Sarah Johnson",
        "prescribed_date": timezone.now().date(),
        "icd10_codes": ["E11.9", "I10", "F90.9"],
        "patient_conditions": ["diabetes", "hypertension"],
        "medications": [
            {
                "name": "Metformin",
                "generic_name": "Metformin hydrochloride",
                "brand_name": "Glucophage",
                "medication_type": "tablet",
                "prescription_type": "prescription",
                "strength": "500mg",
                "dosage_unit": "mg",
                "quantity": 60,
                "manufacturer": "Aspen Pharmacare",
                "prescription_instructions": "Take one tablet twice daily with meals",
                "description": "Oral antidiabetic medication",
                "active_ingredients": "Metformin hydrochloride",
                "side_effects": "Nausea, diarrhea, abdominal discomfort",
                "contraindications": "Severe kidney disease, metabolic acidosis",
                "storage_instructions": "Store at room temperature",
                "expiration_date": (timezone.now().date() + timedelta(days=365)),
                "pill_count": 60,
                "low_stock_threshold": 10
            },
            {
                "name": "Lantus",
                "generic_name": "Insulin glargine",
                "brand_name": "Lantus SoloStar",
                "medication_type": "injection",
                "prescription_type": "prescription",
                "strength": "100units/ml",
                "dosage_unit": "units",
                "quantity": 3,
                "manufacturer": "Sanofi-Aventis",
                "prescription_instructions": "Inject 20 units once daily at bedtime",
                "description": "Long-acting insulin",
                "active_ingredients": "Insulin glargine",
                "side_effects": "Hypoglycemia, injection site reactions",
                "contraindications": "Hypoglycemia, hypersensitivity to insulin",
                "storage_instructions": "Refrigerate at 2-8°C",
                "expiration_date": (timezone.now().date() + timedelta(days=180)),
                "pill_count": 3,
                "low_stock_threshold": 1
            },
            {
                "name": "Ritalin",
                "generic_name": "Methylphenidate hydrochloride",
                "brand_name": "Ritalin LA",
                "medication_type": "capsule",
                "prescription_type": "prescription",
                "strength": "20mg",
                "dosage_unit": "mg",
                "quantity": 30,
                "manufacturer": "Novartis",
                "prescription_instructions": "Take one capsule daily in the morning",
                "description": "Central nervous system stimulant",
                "active_ingredients": "Methylphenidate hydrochloride",
                "side_effects": "Decreased appetite, insomnia, nervousness",
                "contraindications": "Glaucoma, severe anxiety, heart disease",
                "storage_instructions": "Store at room temperature",
                "expiration_date": (timezone.now().date() + timedelta(days=365)),
                "pill_count": 30,
                "low_stock_threshold": 5
            }
        ],
        "auto_create_schedules": True,
        "auto_deduct_stock": False
    }
    
    print("Sample bulk prescription data structure:")
    print(f"  Prescription number: {bulk_prescription_data['prescription_number']}")
    print(f"  Doctor: {bulk_prescription_data['prescribing_doctor']}")
    print(f"  ICD-10 codes: {bulk_prescription_data['icd10_codes']}")
    print(f"  Patient conditions: {bulk_prescription_data['patient_conditions']}")
    print(f"  Number of medications: {len(bulk_prescription_data['medications'])}")
    print(f"  Auto create schedules: {bulk_prescription_data['auto_create_schedules']}")
    print(f"  Auto deduct stock: {bulk_prescription_data['auto_deduct_stock']}")
    
    return bulk_prescription_data


def example_enhanced_medication_data():
    """Example data for enhanced medication creation."""
    print("\n=== Enhanced Medication Data Example ===")
    
    enhanced_medication_data = {
        "name": "Ventolin",
        "generic_name": "Salbutamol sulfate",
        "brand_name": "Ventolin Evohaler",
        "medication_type": "inhaler",
        "prescription_type": "prescription",
        "strength": "100mcg",
        "dosage_unit": "mcg",
        "pill_count": 200,
        "low_stock_threshold": 20,
        "description": "Short-acting beta-2 agonist for asthma",
        "active_ingredients": "Salbutamol sulfate",
        "manufacturer": "GlaxoSmithKline",
        "side_effects": "Tremor, headache, nervousness",
        "contraindications": "Hypersensitivity to salbutamol",
        "storage_instructions": "Store at room temperature, avoid heat and direct sunlight",
        "expiration_date": (timezone.now().date() + timedelta(days=365)),
        "icd10_codes": ["J45.901", "J45.909"],
        "prescription_instructions": "Take 2 puffs as needed for shortness of breath",
        "patient_conditions": ["asthma", "copd"],
        "schedules": [
            {
                "timing": "as_needed",
                "dosage_amount": 2,
                "frequency": "as_needed",
                "instructions": "Use when experiencing shortness of breath"
            }
        ],
        "auto_deduct_stock": True,
        "calculate_renewal_date": True
    }
    
    print("Sample enhanced medication data structure:")
    print(f"  Name: {enhanced_medication_data['name']}")
    print(f"  Strength: {enhanced_medication_data['strength']}")
    print(f"  Manufacturer: {enhanced_medication_data['manufacturer']}")
    print(f"  ICD-10 codes: {enhanced_medication_data['icd10_codes']}")
    print(f"  Instructions: {enhanced_medication_data['prescription_instructions']}")
    print(f"  Patient conditions: {enhanced_medication_data['patient_conditions']}")
    print(f"  Auto deduct stock: {enhanced_medication_data['auto_deduct_stock']}")
    print(f"  Calculate renewal: {enhanced_medication_data['calculate_renewal_date']}")
    
    return enhanced_medication_data


def run_all_examples():
    """Run all examples to demonstrate the features."""
    print("MedGuard SA - Enhanced Medication Serializers Examples")
    print("=" * 60)
    
    example_icd10_validation()
    example_prescription_parsing()
    example_strength_normalization()
    example_manufacturer_validation()
    example_drug_interactions()
    example_contraindications()
    example_renewal_calculation()
    example_bulk_prescription_data()
    example_enhanced_medication_data()
    
    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("\nTo use these serializers in your views:")
    print("1. Import the serializers from medications.serializers")
    print("2. Create serializer instances with request context")
    print("3. Validate and save the data")
    print("4. Handle the response with warnings and errors")


if __name__ == "__main__":
    run_all_examples() 