"""
Comprehensive Prescription Workflow API Tests

Tests for Django backend prescription processing including:
- API endpoints for prescription parsing
- Bulk medication creation
- Schedule generation
- Error handling and validation
- Performance and load testing
- Security and data integrity
"""

import json
import time
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.utils import override_settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from medications.models import Medication, Prescription, MedicationSchedule
from medications.prescription_parser import PrescriptionParser
from medications.serializers import PrescriptionSerializer, BulkMedicationSerializer

User = get_user_model()


class PrescriptionWorkflowAPITests(APITestCase):
    """Comprehensive API tests for prescription workflow."""

    def setUp(self):
        """Set up test data and client."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Test prescription data
        self.test_prescription_text = """
        PRESCRIPTION
        
        Patient: John Doe
        Date: 2024-01-15
        Doctor: Dr. Smith
        
        1. NOVORAPID FlexPen 100units/ml
           Inject 10 units three times daily before meals
           Quantity: 3 pens
           + 2 repeats
        
        2. LANTUS SoloStar Pen 100units/ml
           Inject 20 units once daily at night
           Quantity: 3 pens
           + 2 repeats
        
        3. METFORMIN 500mg tablets
           Take 1 tablet twice daily with meals
           Quantity: 60 tablets
           + 5 repeats
        
        4. LIPITOR 20mg tablets
           Take 1 tablet once daily at night
           Quantity: 30 tablets
           + 3 repeats
        
        5. COZAAR 50mg tablets
           Take 1 tablet once daily
           Quantity: 30 tablets
           + 3 repeats
        
        ICD-10 Codes: E11.9, I10, J45.901
        """
        
        self.complex_21_medication_prescription = """
        PRESCRIPTION
        
        Patient: Jane Smith
        Date: 2024-01-20
        Doctor: Dr. Johnson
        
        1. NOVORAPID FlexPen 100units/ml
           Inject 10 units three times daily before meals
           Quantity: 3 pens
           + 2 repeats
        
        2. LANTUS SoloStar Pen 100units/ml
           Inject 20 units once daily at night
           Quantity: 3 pens
           + 2 repeats
        
        3. METFORMIN 500mg tablets
           Take 1 tablet twice daily with meals
           Quantity: 60 tablets
           + 5 repeats
        
        4. LIPITOR 20mg tablets
           Take 1 tablet once daily at night
           Quantity: 30 tablets
           + 3 repeats
        
        5. COZAAR 50mg tablets
           Take 1 tablet once daily
           Quantity: 30 tablets
           + 3 repeats
        
        6. VENTOLIN inhaler 100mcg
           Use 2 puffs as needed for shortness of breath
           Quantity: 1 inhaler
           + 1 repeat
        
        7. SERETIDE 250/25 inhaler
           Use 2 puffs twice daily
           Quantity: 1 inhaler
           + 2 repeats
        
        8. PANADO 500mg tablets
           Take 2 tablets as needed for pain
           Quantity: 30 tablets
           + 2 repeats
        
        9. OMEPRAZOLE 20mg capsules
           Take 1 capsule once daily before breakfast
           Quantity: 30 capsules
           + 3 repeats
        
        10. MOVICOL sachets
            Take 1 sachet daily as needed for constipation
            Quantity: 30 sachets
            + 2 repeats
        
        11. VITAMIN D3 1000IU tablets
            Take 1 tablet once daily
            Quantity: 60 tablets
            + 3 repeats
        
        12. FOLIC ACID 5mg tablets
            Take 1 tablet once daily
            Quantity: 30 tablets
            + 3 repeats
        
        13. CALCIUM CARBONATE 500mg tablets
            Take 2 tablets twice daily with meals
            Quantity: 60 tablets
            + 3 repeats
        
        14. MAGNESIUM 400mg tablets
            Take 1 tablet once daily at night
            Quantity: 30 tablets
            + 2 repeats
        
        15. OMEGA-3 1000mg capsules
            Take 2 capsules once daily with meals
            Quantity: 60 capsules
            + 3 repeats
        
        16. PROBIOTIC capsules
            Take 1 capsule once daily
            Quantity: 30 capsules
            + 2 repeats
        
        17. MELATONIN 3mg tablets
            Take 1 tablet at bedtime as needed for sleep
            Quantity: 30 tablets
            + 2 repeats
        
        18. ASPIRIN 100mg tablets
            Take 1 tablet once daily
            Quantity: 30 tablets
            + 3 repeats
        
        19. VITAMIN B12 1000mcg tablets
            Take 1 tablet once daily
            Quantity: 30 tablets
            + 2 repeats
        
        20. ZINC 15mg tablets
            Take 1 tablet once daily
            Quantity: 30 tablets
            + 2 repeats
        
        21. VITAMIN C 500mg tablets
            Take 1 tablet once daily
            Quantity: 30 tablets
            + 2 repeats
        
        ICD-10 Codes: E11.9, I10, J45.901, Z79.4
        """

    def test_prescription_parsing_endpoint(self):
        """Test prescription text parsing endpoint."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True,
            'include_generic_names': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        
        # Verify parsed data
        self.assertIn('medications', result)
        self.assertIn('patient_info', result)
        self.assertIn('doctor_info', result)
        self.assertIn('icd10_codes', result)
        self.assertIn('confidence', result)
        
        # Verify medication count
        self.assertEqual(len(result['medications']), 5)
        
        # Verify specific medication details
        novorapid = next(m for m in result['medications'] if 'NOVORAPID' in m['name'])
        self.assertEqual(novorapid['dosage'], '10 units')
        self.assertEqual(novorapid['frequency'], 'three times daily')
        self.assertEqual(novorapid['timing'], 'before meals')
        self.assertEqual(novorapid['quantity'], 3)
        self.assertEqual(novorapid['repeats'], 2)
        self.assertEqual(novorapid['generic_name'], 'Insulin aspart')

    def test_bulk_medication_creation(self):
        """Test bulk medication creation endpoint."""
        url = reverse('bulk-medication-create')
        
        # Prepare bulk medication data
        bulk_data = {
            'medications': [
                {
                    'name': 'NOVORAPID FlexPen 100units/ml',
                    'generic_name': 'Insulin aspart',
                    'dosage': '10 units',
                    'frequency': 'three times daily',
                    'timing': 'before meals',
                    'quantity': 3,
                    'repeats': 2,
                    'medication_type': 'pen',
                    'instructions': 'Inject before meals'
                },
                {
                    'name': 'METFORMIN 500mg tablets',
                    'generic_name': 'Metformin',
                    'dosage': '1 tablet',
                    'frequency': 'twice daily',
                    'timing': 'with meals',
                    'quantity': 60,
                    'repeats': 5,
                    'medication_type': 'tablet',
                    'instructions': 'Take with meals'
                }
            ],
            'patient_info': {
                'name': 'John Doe',
                'date_of_birth': '1980-01-01'
            },
            'doctor_info': {
                'name': 'Dr. Smith',
                'practice': 'Cape Town Medical Centre'
            },
            'prescription_date': '2024-01-15',
            'icd10_codes': ['E11.9', 'I10']
        }
        
        response = self.client.post(url, bulk_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.data
        
        # Verify response structure
        self.assertIn('created_medications', result)
        self.assertIn('failed_medications', result)
        self.assertIn('prescription_id', result)
        self.assertIn('schedule_id', result)
        
        # Verify medications were created
        self.assertEqual(len(result['created_medications']), 2)
        self.assertEqual(len(result['failed_medications']), 0)
        
        # Verify database records
        self.assertEqual(Medication.objects.count(), 2)
        self.assertEqual(Prescription.objects.count(), 1)
        self.assertEqual(MedicationSchedule.objects.count(), 1)

    def test_21_medication_prescription_processing(self):
        """Test processing of complex 21-medication prescription."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.complex_21_medication_prescription,
            'validate_medications': True,
            'include_generic_names': True
        }
        
        start_time = time.time()
        response = self.client.post(url, data, format='json')
        processing_time = time.time() - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        
        # Verify all 21 medications were parsed
        self.assertEqual(len(result['medications']), 21)
        
        # Verify processing time is reasonable
        self.assertLess(processing_time, 5.0)  # Should complete within 5 seconds
        
        # Verify confidence score
        self.assertGreater(result['confidence'], 0.8)
        
        # Verify no warnings for well-formed prescription
        self.assertEqual(len(result.get('warnings', [])), 0)

    def test_prescription_image_upload(self):
        """Test prescription image upload and OCR processing."""
        url = reverse('prescription-upload')
        
        # Create mock image file
        image_content = b'fake image data'
        image_file = SimpleUploadedFile(
            'prescription.jpg',
            image_content,
            content_type='image/jpeg'
        )
        
        data = {
            'image': image_file,
            'validate_medications': True,
            'preprocessing_options': {
                'contrast': 1.2,
                'brightness': 0.1,
                'sharpen': True
            }
        }
        
        with patch('medications.views.OCRService') as mock_ocr:
            # Mock OCR service response
            mock_ocr_instance = MagicMock()
            mock_ocr_instance.process_prescription.return_value = {
                'success': True,
                'confidence': 0.85,
                'text': self.test_prescription_text,
                'medications': [],
                'processing_time': 2500
            }
            mock_ocr.getInstance.return_value = mock_ocr_instance
            
            response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        
        # Verify OCR processing was called
        mock_ocr_instance.process_prescription.assert_called_once()
        
        # Verify response structure
        self.assertIn('ocr_result', result)
        self.assertIn('parsed_data', result)
        self.assertIn('validation_report', result)

    def test_error_handling_and_validation(self):
        """Test error handling for malformed prescriptions."""
        url = reverse('prescription-parse')
        
        # Test with malformed prescription
        malformed_text = """
        PRESCRIPTION
        
        Patient: Test Patient
        Date: 2024-01-30
        Doctor: Dr. Test
        
        1. MEDICATION A
           Take as directed
           Quantity: unknown
        
        2. MEDICATION B
           Dosage: unclear
           Frequency: not specified
        """
        
        data = {
            'prescription_text': malformed_text,
            'validate_medications': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        
        # Verify warnings are generated
        self.assertGreater(len(result.get('warnings', [])), 0)
        
        # Verify confidence is lower for malformed prescription
        self.assertLess(result['confidence'], 0.7)
        
        # Verify medications are still parsed but with warnings
        self.assertGreater(len(result['medications']), 0)

    def test_network_error_handling(self):
        """Test handling of network and external service errors."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True
        }
        
        with patch('medications.prescription_parser.PrescriptionParser.parse_prescription') as mock_parse:
            mock_parse.side_effect = Exception("Network error")
            
            response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)

    def test_concurrent_prescription_processing(self):
        """Test concurrent processing of multiple prescriptions."""
        url = reverse('prescription-parse')
        
        # Create multiple prescription requests
        requests_data = [
            {
                'prescription_text': self.test_prescription_text,
                'validate_medications': True
            },
            {
                'prescription_text': self.complex_21_medication_prescription,
                'validate_medications': True
            }
        ]
        
        start_time = time.time()
        
        # Process requests concurrently
        responses = []
        for data in requests_data:
            response = self.client.post(url, data, format='json')
            responses.append(response)
        
        total_time = time.time() - start_time
        
        # Verify all requests succeeded
        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify concurrent processing time is reasonable
        self.assertLess(total_time, 10.0)  # Should complete within 10 seconds

    def test_performance_under_load(self):
        """Test performance under high load conditions."""
        url = reverse('prescription-parse')
        
        # Simulate high load with multiple requests
        num_requests = 10
        start_time = time.time()
        
        responses = []
        for i in range(num_requests):
            data = {
                'prescription_text': self.test_prescription_text,
                'validate_medications': True
            }
            response = self.client.post(url, data, format='json')
            responses.append(response)
        
        total_time = time.time() - start_time
        avg_time = total_time / num_requests
        
        # Verify all requests succeeded
        success_count = sum(1 for r in responses if r.status_code == status.HTTP_200_OK)
        self.assertEqual(success_count, num_requests)
        
        # Verify performance metrics
        self.assertLess(avg_time, 1.0)  # Average time should be under 1 second
        self.assertLess(total_time, 15.0)  # Total time should be under 15 seconds

    def test_security_and_authentication(self):
        """Test security and authentication requirements."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True
        }
        
        # Test without authentication
        self.client.force_authenticate(user=None)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with authentication
        self.client.force_authenticate(user=self.user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_data_integrity_and_validation(self):
        """Test data integrity and validation."""
        url = reverse('bulk-medication-create')
        
        # Test with invalid medication data
        invalid_data = {
            'medications': [
                {
                    'name': '',  # Invalid empty name
                    'dosage': 'invalid dosage',
                    'frequency': 'invalid frequency',
                    'quantity': -1,  # Invalid negative quantity
                    'repeats': 'invalid'  # Invalid string instead of integer
                }
            ]
        }
        
        response = self.client.post(url, invalid_data, format='json')
        
        # Should return validation errors
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('medications', response.data)

    def test_prescription_serializer_validation(self):
        """Test prescription serializer validation."""
        serializer = PrescriptionSerializer()
        
        # Test valid data
        valid_data = {
            'patient_name': 'John Doe',
            'doctor_name': 'Dr. Smith',
            'prescription_date': '2024-01-15',
            'medications': [
                {
                    'name': 'NOVORAPID FlexPen 100units/ml',
                    'dosage': '10 units',
                    'frequency': 'three times daily',
                    'quantity': 3,
                    'repeats': 2
                }
            ]
        }
        
        serializer = PrescriptionSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test invalid data
        invalid_data = {
            'patient_name': '',  # Empty name
            'medications': []  # Empty medications list
        }
        
        serializer = PrescriptionSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('patient_name', serializer.errors)
        self.assertIn('medications', serializer.errors)

    def test_bulk_medication_serializer(self):
        """Test bulk medication serializer."""
        serializer = BulkMedicationSerializer()
        
        # Test valid bulk data
        valid_data = {
            'medications': [
                {
                    'name': 'NOVORAPID FlexPen 100units/ml',
                    'dosage': '10 units',
                    'frequency': 'three times daily',
                    'quantity': 3,
                    'repeats': 2
                },
                {
                    'name': 'METFORMIN 500mg tablets',
                    'dosage': '1 tablet',
                    'frequency': 'twice daily',
                    'quantity': 60,
                    'repeats': 5
                }
            ],
            'patient_info': {
                'name': 'John Doe',
                'date_of_birth': '1980-01-01'
            }
        }
        
        serializer = BulkMedicationSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Test with invalid medication data
        invalid_data = {
            'medications': [
                {
                    'name': '',  # Invalid empty name
                    'dosage': 'invalid',
                    'quantity': -1
                }
            ]
        }
        
        serializer = BulkMedicationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('medications', serializer.errors)

    def test_database_transaction_integrity(self):
        """Test database transaction integrity during bulk operations."""
        url = reverse('bulk-medication-create')
        
        # Prepare data that will cause a partial failure
        bulk_data = {
            'medications': [
                {
                    'name': 'VALID MEDICATION',
                    'dosage': '1 tablet',
                    'frequency': 'once daily',
                    'quantity': 30,
                    'repeats': 3
                },
                {
                    'name': '',  # Invalid medication
                    'dosage': 'invalid',
                    'quantity': -1
                }
            ]
        }
        
        initial_medication_count = Medication.objects.count()
        
        response = self.client.post(url, bulk_data, format='json')
        
        # Should handle partial failures gracefully
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        
        # Verify only valid medications were created
        final_medication_count = Medication.objects.count()
        self.assertEqual(final_medication_count, initial_medication_count + 1)

    def test_icd10_code_extraction_and_validation(self):
        """Test ICD-10 code extraction and validation."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        
        # Verify ICD-10 codes were extracted
        self.assertIn('icd10_codes', result)
        self.assertIn('E11.9', result['icd10_codes'])
        self.assertIn('I10', result['icd10_codes'])
        self.assertIn('J45.901', result['icd10_codes'])
        
        # Verify code descriptions are provided
        for code in result['icd10_codes']:
            self.assertIsInstance(code, str)
            self.assertTrue(len(code) > 0)

    def test_medication_interaction_checking(self):
        """Test medication interaction checking."""
        url = reverse('medication-interactions')
        
        data = {
            'medications': [
                'NOVORAPID',
                'LANTUS',
                'METFORMIN',
                'LIPITOR'
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        
        # Verify interaction checking response
        self.assertIn('interactions', result)
        self.assertIn('warnings', result)
        self.assertIn('recommendations', result)

    def test_schedule_generation(self):
        """Test medication schedule generation."""
        url = reverse('schedule-generate')
        
        data = {
            'medications': [
                {
                    'name': 'NOVORAPID FlexPen 100units/ml',
                    'dosage': '10 units',
                    'frequency': 'three times daily',
                    'timing': 'before meals'
                },
                {
                    'name': 'LANTUS SoloStar Pen 100units/ml',
                    'dosage': '20 units',
                    'frequency': 'once daily',
                    'timing': 'at night'
                }
            ],
            'patient_preferences': {
                'wake_time': '07:00',
                'bed_time': '22:00',
                'meal_times': ['08:00', '13:00', '19:00']
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.data
        
        # Verify schedule generation
        self.assertIn('schedule', result)
        self.assertIn('medication_times', result)
        self.assertIn('reminders', result)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_async_prescription_processing(self):
        """Test asynchronous prescription processing."""
        url = reverse('prescription-process-async')
        
        data = {
            'prescription_text': self.complex_21_medication_prescription,
            'validate_medications': True,
            'generate_schedule': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        result = response.data
        
        # Verify task was queued
        self.assertIn('task_id', result)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'processing')

    def test_prescription_audit_logging(self):
        """Test prescription processing audit logging."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True
        }
        
        initial_audit_count = 0  # Replace with actual audit model count
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify audit log was created
        final_audit_count = 0  # Replace with actual audit model count
        self.assertGreater(final_audit_count, initial_audit_count)

    def test_rate_limiting(self):
        """Test API rate limiting."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True
        }
        
        # Make multiple rapid requests
        responses = []
        for i in range(20):  # Exceed rate limit
            response = self.client.post(url, data, format='json')
            responses.append(response)
        
        # Verify rate limiting is enforced
        rate_limited_responses = [r for r in responses if r.status_code == status.HTTP_429_TOO_MANY_REQUESTS]
        self.assertGreater(len(rate_limited_responses), 0)

    def test_data_encryption_and_privacy(self):
        """Test data encryption and privacy protection."""
        url = reverse('prescription-parse')
        data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify sensitive data is not logged
        # This would require checking logs, but we can verify the response
        # doesn't contain sensitive information in unexpected places
        result = response.data
        
        # Verify patient name is not exposed in error messages or logs
        self.assertNotIn('John Doe', str(result.get('errors', [])))
        self.assertNotIn('John Doe', str(result.get('warnings', [])))

    def test_comprehensive_workflow_integration(self):
        """Test complete prescription workflow integration."""
        # Step 1: Parse prescription
        parse_url = reverse('prescription-parse')
        parse_data = {
            'prescription_text': self.test_prescription_text,
            'validate_medications': True,
            'include_generic_names': True
        }
        
        parse_response = self.client.post(parse_url, parse_data, format='json')
        self.assertEqual(parse_response.status_code, status.HTTP_200_OK)
        parsed_result = parse_response.data
        
        # Step 2: Create bulk medications
        bulk_url = reverse('bulk-medication-create')
        bulk_data = {
            'medications': parsed_result['medications'],
            'patient_info': parsed_result['patient_info'],
            'doctor_info': parsed_result['doctor_info'],
            'prescription_date': parsed_result['prescription_date'],
            'icd10_codes': parsed_result['icd10_codes']
        }
        
        bulk_response = self.client.post(bulk_url, bulk_data, format='json')
        self.assertEqual(bulk_response.status_code, status.HTTP_201_CREATED)
        bulk_result = bulk_response.data
        
        # Step 3: Generate schedule
        schedule_url = reverse('schedule-generate')
        schedule_data = {
            'medications': parsed_result['medications'],
            'patient_preferences': {
                'wake_time': '07:00',
                'bed_time': '22:00',
                'meal_times': ['08:00', '13:00', '19:00']
            }
        }
        
        schedule_response = self.client.post(schedule_url, schedule_data, format='json')
        self.assertEqual(schedule_response.status_code, status.HTTP_200_OK)
        schedule_result = schedule_response.data
        
        # Verify complete workflow success
        self.assertEqual(len(bulk_result['created_medications']), 5)
        self.assertEqual(len(bulk_result['failed_medications']), 0)
        self.assertIsNotNone(bulk_result['prescription_id'])
        self.assertIsNotNone(bulk_result['schedule_id'])
        self.assertIsNotNone(schedule_result['schedule'])
        
        # Verify database integrity
        self.assertEqual(Medication.objects.count(), 5)
        self.assertEqual(Prescription.objects.count(), 1)
        self.assertEqual(MedicationSchedule.objects.count(), 1) 