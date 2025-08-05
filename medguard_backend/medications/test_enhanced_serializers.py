"""
Tests for enhanced medication serializers.

This module tests the enhanced medication serializer functionality including:
- ICD-10 code validation
- Prescription instruction parsing
- Nested schedule creation
- Drug interaction checking
- Contraindication validation
"""

import json
from decimal import Decimal
from datetime import time, date
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Medication, MedicationSchedule
from .serializers import (
    EnhancedMedicationSerializer, ICD10Validator, PrescriptionParser,
    MedicationInteractionValidator
)

User = get_user_model()


class ICD10ValidatorTestCase(TestCase):
    """Test cases for ICD-10 code validation."""
    
    def test_valid_icd10_codes(self):
        """Test valid ICD-10 code formats."""
        valid_codes = [
            'A00.0', 'B01.1', 'C78.01', 'Z51.11', 'E11.9', 'I10.X1',
            'M79.3', 'R50.9', 'S72.001', 'T78.40'
        ]
        
        for code in valid_codes:
            with self.subTest(code=code):
                self.assertTrue(ICD10Validator.validate(code))
    
    def test_invalid_icd10_codes(self):
        """Test invalid ICD-10 code formats."""
        invalid_codes = [
            'A0.0', 'A000.0', 'A00', 'A00.000', 'a00.0', 'A00.0X',
            'X00.0', '00.0', 'A0.00', 'A00.0X1'
        ]
        
        for code in invalid_codes:
            with self.subTest(code=code):
                self.assertFalse(ICD10Validator.validate(code))
    
    def test_icd10_code_cleaning(self):
        """Test ICD-10 code cleaning and standardization."""
        test_cases = [
            ('a00.0', 'A00.0'),
            ('  B01.1  ', 'B01.1'),
            ('c78.01', 'C78.01'),
            ('', ''),
            (None, None)
        ]
        
        for input_code, expected in test_cases:
            with self.subTest(input_code=input_code):
                self.assertEqual(ICD10Validator.clean(input_code), expected)


class PrescriptionParserTestCase(TestCase):
    """Test cases for prescription instruction parsing."""
    
    def test_dosage_extraction(self):
        """Test extraction of dosage amounts and units."""
        test_cases = [
            ('Take one tablet daily', Decimal('1'), 'tablet'),
            ('Take 2 tablets at 12h00', Decimal('2'), 'tablets'),
            ('Take 1 capsule three times daily', Decimal('1'), 'capsule'),
            ('Take 500mg twice daily', Decimal('500'), 'mg'),
            ('Take 2.5ml four times daily', Decimal('2.5'), 'ml'),
            ('Take 10mcg as needed', Decimal('10'), 'mcg'),
        ]
        
        for instructions, expected_amount, expected_unit in test_cases:
            with self.subTest(instructions=instructions):
                parsed = PrescriptionParser.parse_instructions(instructions)
                self.assertEqual(parsed['dosage_amount'], expected_amount)
                self.assertEqual(parsed['dosage_unit'], expected_unit)
    
    def test_frequency_extraction(self):
        """Test extraction of frequency patterns."""
        test_cases = [
            ('Take one tablet daily', 'daily'),
            ('Take two tablets twice daily', 'twice_daily'),
            ('Take 1 capsule three times daily', 'three_times_daily'),
            ('Take 2 tablets four times daily', 'four_times_daily'),
            ('Take 1 tablet weekly', 'weekly'),
            ('Take 1 tablet monthly', 'monthly'),
            ('Take 1 tablet as needed', 'as_needed'),
        ]
        
        for instructions, expected_frequency in test_cases:
            with self.subTest(instructions=instructions):
                parsed = PrescriptionParser.parse_instructions(instructions)
                self.assertEqual(parsed['frequency'], expected_frequency)
    
    def test_timing_extraction(self):
        """Test extraction of timing patterns."""
        test_cases = [
            ('Take one tablet in the morning', 'morning'),
            ('Take two tablets at noon', 'noon'),
            ('Take 1 capsule in the evening', 'night'),
            ('Take 2 tablets at 12h00', 'custom'),
            ('Take 1 tablet at 14:30', 'custom'),
            ('Take 1 tablet at 8h30', 'custom'),
        ]
        
        for instructions, expected_timing in test_cases:
            with self.subTest(instructions=instructions):
                parsed = PrescriptionParser.parse_instructions(instructions)
                self.assertEqual(parsed['timing'], expected_timing)
    
    def test_custom_time_extraction(self):
        """Test extraction of custom times."""
        test_cases = [
            ('Take 2 tablets at 12h00', time(12, 0)),
            ('Take 1 tablet at 14:30', time(14, 30)),
            ('Take 1 tablet at 8h30', time(8, 30)),
            ('Take 1 tablet at 22:00', time(22, 0)),
        ]
        
        for instructions, expected_time in test_cases:
            with self.subTest(instructions=instructions):
                parsed = PrescriptionParser.parse_instructions(instructions)
                self.assertEqual(parsed['custom_time'], expected_time)
    
    def test_schedule_generation(self):
        """Test generation of schedule configurations."""
        # Test daily schedule
        parsed = PrescriptionParser.parse_instructions('Take one tablet daily')
        schedules = parsed['schedules']
        self.assertEqual(len(schedules), 1)
        self.assertEqual(schedules[0]['timing'], 'morning')
        self.assertEqual(schedules[0]['dosage_amount'], Decimal('1'))
        
        # Test twice daily schedule
        parsed = PrescriptionParser.parse_instructions('Take two tablets twice daily')
        schedules = parsed['schedules']
        self.assertEqual(len(schedules), 2)
        self.assertEqual(schedules[0]['timing'], 'morning')
        self.assertEqual(schedules[1]['timing'], 'night')
        
        # Test three times daily schedule
        parsed = PrescriptionParser.parse_instructions('Take 1 capsule three times daily')
        schedules = parsed['schedules']
        self.assertEqual(len(schedules), 3)
        self.assertEqual(schedules[0]['timing'], 'morning')
        self.assertEqual(schedules[1]['timing'], 'noon')
        self.assertEqual(schedules[2]['timing'], 'night')
        
        # Test four times daily schedule
        parsed = PrescriptionParser.parse_instructions('Take 2 tablets four times daily')
        schedules = parsed['schedules']
        self.assertEqual(len(schedules), 4)
        self.assertEqual(schedules[0]['timing'], 'custom')
        self.assertEqual(schedules[0]['custom_time'], time(6, 0))
    
    def test_complex_instructions(self):
        """Test parsing of complex prescription instructions."""
        instructions = "Take 2 tablets at 8h00 and 20h00 daily with food"
        parsed = PrescriptionParser.parse_instructions(instructions)
        
        self.assertEqual(parsed['dosage_amount'], Decimal('2'))
        self.assertEqual(parsed['dosage_unit'], 'tablets')
        self.assertEqual(parsed['frequency'], 'twice_daily')
        self.assertEqual(len(parsed['schedules']), 2)


class MedicationInteractionValidatorTestCase(TestCase):
    """Test cases for medication interaction validation."""
    
    def test_drug_interactions(self):
        """Test detection of drug interactions."""
        # Test warfarin interactions
        interactions = MedicationInteractionValidator.check_interactions(
            'warfarin', ['aspirin', 'paracetamol', 'ibuprofen']
        )
        self.assertIn('Potential interaction between warfarin and aspirin', interactions)
        self.assertIn('Potential interaction between warfarin and ibuprofen', interactions)
        self.assertNotIn('Potential interaction between warfarin and paracetamol', interactions)
        
        # Test digoxin interactions
        interactions = MedicationInteractionValidator.check_interactions(
            'digoxin', ['furosemide', 'vitamin_d', 'spironolactone']
        )
        self.assertIn('Potential interaction between digoxin and furosemide', interactions)
        self.assertIn('Potential interaction between digoxin and spironolactone', interactions)
    
    def test_contraindications(self):
        """Test detection of contraindications."""
        # Test pregnancy contraindications
        contraindications = MedicationInteractionValidator.check_contraindications(
            'warfarin', ['pregnancy', 'diabetes']
        )
        self.assertIn('warfarin may be contraindicated for pregnancy', contraindications)
        
        # Test liver disease contraindications
        contraindications = MedicationInteractionValidator.check_contraindications(
            'acetaminophen', ['liver_disease', 'hypertension']
        )
        self.assertIn('acetaminophen may be contraindicated for liver_disease', contraindications)
    
    def test_no_interactions(self):
        """Test when no interactions are found."""
        interactions = MedicationInteractionValidator.check_interactions(
            'vitamin_d', ['paracetamol', 'vitamin_c']
        )
        self.assertEqual(len(interactions), 0)
        
        contraindications = MedicationInteractionValidator.check_contraindications(
            'vitamin_d', ['diabetes', 'hypertension']
        )
        self.assertEqual(len(contraindications), 0)


class EnhancedMedicationSerializerTestCase(APITestCase):
    """Test cases for the enhanced medication serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='PATIENT'
        )
        self.client.force_authenticate(user=self.user)
        
        # Create a test medication
        self.medication = Medication.objects.create(
            name='Test Medication',
            generic_name='Test Generic',
            medication_type='tablet',
            prescription_type='prescription',
            strength='500mg',
            dosage_unit='mg',
            manufacturer='Test Pharma'
        )
    
    def test_icd10_validation(self):
        """Test ICD-10 code validation in serializer."""
        data = {
            'name': 'Test Medication',
            'generic_name': 'Test Generic',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma',
            'icd10_codes': ['A00.0', 'B01.1', 'INVALID_CODE']
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('icd10_codes', serializer.errors)
    
    def test_prescription_instruction_parsing(self):
        """Test prescription instruction parsing in serializer."""
        data = {
            'name': 'Test Medication',
            'generic_name': 'Test Generic',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma',
            'prescription_instructions': 'Take one tablet daily'
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        
        # Test that parsed prescription data is available
        medication = serializer.save()
        self.assertIsNotNone(serializer.data.get('parsed_prescription'))
    
    def test_nested_schedule_creation(self):
        """Test creation of medication with nested schedules."""
        data = {
            'name': 'Test Medication',
            'generic_name': 'Test Generic',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma',
            'schedules': [
                {
                    'timing': 'morning',
                    'dosage_amount': '1.0',
                    'frequency': 'daily',
                    'instructions': 'Take with breakfast'
                },
                {
                    'timing': 'night',
                    'dosage_amount': '1.0',
                    'frequency': 'daily',
                    'instructions': 'Take before bed'
                }
            ]
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        
        medication = serializer.save()
        
        # Check that schedules were created
        schedules = medication.schedules.all()
        self.assertEqual(schedules.count(), 2)
        self.assertEqual(schedules[0].timing, 'morning')
        self.assertEqual(schedules[1].timing, 'night')
    
    def test_automatic_schedule_creation_from_instructions(self):
        """Test automatic schedule creation from prescription instructions."""
        data = {
            'name': 'Test Medication',
            'generic_name': 'Test Generic',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma',
            'prescription_instructions': 'Take two tablets twice daily'
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        
        medication = serializer.save()
        
        # Check that schedules were automatically created
        schedules = medication.schedules.all()
        self.assertEqual(schedules.count(), 2)
        self.assertEqual(schedules[0].timing, 'morning')
        self.assertEqual(schedules[1].timing, 'night')
        self.assertEqual(schedules[0].dosage_amount, Decimal('2'))
        self.assertEqual(schedules[1].dosage_amount, Decimal('2'))
    
    def test_strength_validation(self):
        """Test medication strength format validation."""
        invalid_strengths = [
            'invalid', '500', 'mg', '500invalid', '500 mg invalid'
        ]
        
        for strength in invalid_strengths:
            with self.subTest(strength=strength):
                data = {
                    'name': 'Test Medication',
                    'generic_name': 'Test Generic',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': strength,
                    'dosage_unit': 'mg',
                    'manufacturer': 'Test Pharma'
                }
                
                serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
                self.assertFalse(serializer.is_valid())
                self.assertIn('strength', serializer.errors)
    
    def test_dosage_unit_validation(self):
        """Test dosage unit matches strength unit."""
        data = {
            'name': 'Test Medication',
            'generic_name': 'Test Generic',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'ml',  # Mismatch
            'manufacturer': 'Test Pharma'
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertFalse(serializer.is_valid())
        self.assertIn('dosage_unit', serializer.errors)
    
    def test_interaction_warnings(self):
        """Test drug interaction warnings."""
        # Create another medication that interacts
        interacting_med = Medication.objects.create(
            name='Aspirin',
            generic_name='Acetylsalicylic acid',
            medication_type='tablet',
            prescription_type='otc',
            strength='100mg',
            dosage_unit='mg',
            manufacturer='Test Pharma'
        )
        
        # Create a schedule for the interacting medication
        MedicationSchedule.objects.create(
            patient=self.user,
            medication=interacting_med,
            timing='morning',
            dosage_amount=Decimal('1'),
            frequency='daily',
            status='active'
        )
        
        # Test interaction detection
        data = {
            'name': 'Warfarin',
            'generic_name': 'Warfarin sodium',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '5mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma'
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        
        medication = serializer.save()
        
        # Check for interaction warnings
        warnings = serializer.get_interaction_warnings(medication)
        self.assertIn('Potential interaction between Warfarin and Aspirin', warnings)
    
    def test_contraindication_warnings(self):
        """Test contraindication warnings."""
        # Add medical conditions to user (if supported by user model)
        if hasattr(self.user, 'medical_conditions'):
            self.user.medical_conditions = ['pregnancy']
            self.user.save()
        
        data = {
            'name': 'Warfarin',
            'generic_name': 'Warfarin sodium',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '5mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma',
            'patient_conditions': ['pregnancy']
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        
        medication = serializer.save()
        
        # Check for contraindication warnings
        warnings = serializer.get_contraindication_warnings(medication)
        self.assertIn('Warfarin may be contraindicated for pregnancy', warnings)
    
    def test_complete_medication_creation(self):
        """Test complete medication creation with all enhanced features."""
        data = {
            'name': 'Test Enhanced Medication',
            'generic_name': 'Test Generic Enhanced',
            'brand_name': 'Test Brand',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '250mg',
            'dosage_unit': 'mg',
            'pill_count': 30,
            'low_stock_threshold': 5,
            'description': 'Test medication description',
            'active_ingredients': 'Test active ingredient',
            'manufacturer': 'Test Pharma',
            'side_effects': 'Drowsiness, nausea',
            'contraindications': 'Allergy to test ingredient',
            'storage_instructions': 'Store in cool, dry place',
            'expiration_date': '2025-12-31',
            'icd10_codes': ['A00.0', 'B01.1'],
            'prescription_instructions': 'Take one tablet three times daily',
            'patient_conditions': ['diabetes', 'hypertension']
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        
        medication = serializer.save()
        
        # Verify all fields were saved correctly
        self.assertEqual(medication.name, 'Test Enhanced Medication')
        self.assertEqual(medication.strength, '250mg')
        self.assertEqual(medication.dosage_unit, 'mg')
        
        # Verify schedules were created from instructions
        schedules = medication.schedules.all()
        self.assertEqual(schedules.count(), 3)  # Three times daily
        
        # Verify parsed prescription data
        parsed_data = serializer.data.get('parsed_prescription')
        self.assertIsNotNone(parsed_data)
        self.assertEqual(parsed_data['frequency'], 'three_times_daily')
        self.assertEqual(parsed_data['dosage_amount'], '1.0')
    
    def test_medication_update_with_schedules(self):
        """Test updating medication with new schedules."""
        # Create initial medication
        data = {
            'name': 'Test Medication',
            'generic_name': 'Test Generic',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma',
            'prescription_instructions': 'Take one tablet daily'
        }
        
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        medication = serializer.save()
        
        # Update with new schedules
        update_data = {
            'name': 'Updated Test Medication',
            'schedules': [
                {
                    'timing': 'morning',
                    'dosage_amount': '2.0',
                    'frequency': 'daily',
                    'instructions': 'Take with breakfast'
                }
            ]
        }
        
        update_serializer = EnhancedMedicationSerializer(
            medication, data=update_data, partial=True, context={'request': self.client.request}
        )
        self.assertTrue(update_serializer.is_valid())
        
        updated_medication = update_serializer.save()
        
        # Verify old schedules were replaced
        schedules = updated_medication.schedules.all()
        self.assertEqual(schedules.count(), 1)
        self.assertEqual(schedules[0].dosage_amount, Decimal('2.0'))


class EnhancedMedicationSerializerIntegrationTestCase(APITestCase):
    """Integration tests for the enhanced medication serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='PATIENT'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_api_endpoint_with_enhanced_serializer(self):
        """Test API endpoint using the enhanced serializer."""
        # This test assumes you have an API endpoint that uses the enhanced serializer
        # You would need to create the appropriate view and URL for this test
        
        data = {
            'name': 'API Test Medication',
            'generic_name': 'API Test Generic',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '100mg',
            'dosage_unit': 'mg',
            'manufacturer': 'Test Pharma',
            'prescription_instructions': 'Take two tablets twice daily',
            'icd10_codes': ['A00.0'],
            'patient_conditions': ['diabetes']
        }
        
        # This would be the actual API call
        # response = self.client.post('/api/medications/', data, format='json')
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # For now, test the serializer directly
        serializer = EnhancedMedicationSerializer(data=data, context={'request': self.client.request})
        self.assertTrue(serializer.is_valid())
        
        medication = serializer.save()
        
        # Verify the response includes all enhanced fields
        response_data = serializer.data
        self.assertIn('parsed_prescription', response_data)
        self.assertIn('interaction_warnings', response_data)
        self.assertIn('contraindication_warnings', response_data)
        self.assertIn('icd10_codes', response_data)
        
        # Verify schedules were created
        self.assertEqual(medication.schedules.count(), 2)
    
    def test_error_handling(self):
        """Test error handling in the enhanced serializer."""
        # Test with invalid data
        invalid_data = {
            'name': '',  # Empty name
            'strength': 'invalid',  # Invalid strength
            'icd10_codes': ['INVALID'],  # Invalid ICD-10
            'prescription_instructions': 'invalid instructions'  # Can't parse dosage
        }
        
        serializer = EnhancedMedicationSerializer(data=invalid_data, context={'request': self.client.request})
        self.assertFalse(serializer.is_valid())
        
        # Check for specific error messages
        self.assertIn('name', serializer.errors)
        self.assertIn('strength', serializer.errors)
        self.assertIn('icd10_codes', serializer.errors)
        self.assertIn('prescription_instructions', serializer.errors) 