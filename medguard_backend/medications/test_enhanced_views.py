"""
Tests for enhanced medication views functionality.

This module tests the new batch creation, prescription upload, and stock management features.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Medication, MedicationSchedule, StockTransaction, 
    PrescriptionRenewal, StockAlert
)

User = get_user_model()


class EnhancedMedicationViewsTestCase(TestCase):
    """
    Test case for enhanced medication views functionality.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            user_type='STAFF',
            first_name='Admin',
            last_name='User'
        )
        
        self.patient_user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            user_type='PATIENT',
            first_name='John',
            last_name='Doe'
        )
        
        # Create API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
        
        # Base URL for medication views
        self.medication_list_url = reverse('medication-list')
        self.medication_detail_url = reverse('medication-detail', args=[1])
    
    def test_bulk_create_from_prescription_success(self):
        """Test successful bulk creation from prescription data."""
        prescription_data = {
            'medications': [
                {
                    'name': 'Paracetamol',
                    'generic_name': 'Acetaminophen',
                    'strength': '500mg',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'initial_stock': 30,
                    'schedule_data': {
                        'timing': 'morning',
                        'dosage_amount': 1,
                        'frequency': 'daily',
                        'start_date': timezone.now().date(),
                        'instructions': 'Take with food'
                    }
                },
                {
                    'name': 'Ibuprofen',
                    'generic_name': 'Ibuprofen',
                    'strength': '400mg',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'initial_stock': 20,
                    'schedule_data': {
                        'timing': 'noon',
                        'dosage_amount': 1,
                        'frequency': 'twice_daily',
                        'start_date': timezone.now().date(),
                        'instructions': 'Take as needed for pain'
                    }
                }
            ],
            'patient_id': self.patient_user.id,
            'prescription_number': 'RX123456',
            'prescribed_by': 'Dr. Smith',
            'prescribed_date': '2024-01-01'
        }
        
        url = f"{self.medication_list_url}bulk_create_from_prescription/"
        response = self.client.post(url, prescription_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_medications'], 2)
        self.assertEqual(response.data['created_schedules'], 2)
        self.assertEqual(response.data['created_transactions'], 2)
        
        # Verify medications were created
        medications = Medication.objects.all()
        self.assertEqual(medications.count(), 2)
        
        # Verify schedules were created
        schedules = MedicationSchedule.objects.all()
        self.assertEqual(schedules.count(), 2)
        
        # Verify stock transactions were created
        transactions = StockTransaction.objects.all()
        self.assertEqual(transactions.count(), 2)
        
        # Verify prescription renewals were created
        renewals = PrescriptionRenewal.objects.all()
        self.assertEqual(renewals.count(), 2)
    
    def test_bulk_create_from_prescription_validation_error(self):
        """Test bulk creation with validation errors."""
        invalid_data = {
            'medications': [
                {
                    'name': '',  # Invalid: empty name
                    'strength': '500mg',
                    'medication_type': 'tablet',
                    'initial_stock': 30
                }
            ],
            'patient_id': self.patient_user.id
        }
        
        url = f"{self.medication_list_url}bulk_create_from_prescription/"
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify no medications were created
        self.assertEqual(Medication.objects.count(), 0)
    
    def test_bulk_create_from_prescription_patient_not_found(self):
        """Test bulk creation with non-existent patient."""
        data = {
            'medications': [
                {
                    'name': 'Test Medication',
                    'strength': '500mg',
                    'medication_type': 'tablet',
                    'initial_stock': 30
                }
            ],
            'patient_id': 99999  # Non-existent patient
        }
        
        url = f"{self.medication_list_url}bulk_create_from_prescription/"
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_prescription_upload_success(self):
        """Test successful prescription upload with OCR data."""
        ocr_data = {
            'ocr_data': {
                'medications': [
                    {
                        'name': 'Amoxicillin',
                        'strength': '500mg',
                        'instructions': 'Take one capsule three times daily',
                        'quantity': 21
                    },
                    {
                        'name': 'Omeprazole',
                        'strength': '20mg',
                        'instructions': 'Take one tablet daily',
                        'quantity': 30
                    }
                ],
                'prescription_info': {
                    'prescription_number': 'RX789012',
                    'prescribed_by': 'Dr. Johnson',
                    'prescribed_date': '2024-01-15'
                }
            },
            'patient_id': self.patient_user.id,
            'confidence_score': 0.85
        }
        
        url = f"{self.medication_list_url}prescription_upload/"
        response = self.client.post(url, ocr_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['processed_medications'], 2)
        self.assertEqual(response.data['confidence_score'], 0.85)
        
        # Verify medications were created with enriched data
        medications = Medication.objects.all()
        self.assertEqual(medications.count(), 2)
        
        # Check that medication types were detected
        amoxicillin = Medication.objects.filter(name__icontains='Amoxicillin').first()
        self.assertIsNotNone(amoxicillin)
        self.assertEqual(amoxicillin.medication_type, 'capsule')
        
        omeprazole = Medication.objects.filter(name__icontains='Omeprazole').first()
        self.assertIsNotNone(omeprazole)
        self.assertEqual(omeprazole.medication_type, 'tablet')
    
    def test_prescription_upload_no_ocr_data(self):
        """Test prescription upload with no OCR data."""
        data = {
            'patient_id': self.patient_user.id,
            'confidence_score': 0.85
        }
        
        url = f"{self.medication_list_url}prescription_upload/"
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_stock_success(self):
        """Test successful stock addition to medication."""
        # Create a test medication
        medication = Medication.objects.create(
            name='Test Medication',
            strength='500mg',
            medication_type='tablet',
            prescription_type='prescription',
            pill_count=10
        )
        
        stock_data = {
            'quantity': 30,
            'unit_price': 15.50,
            'batch_number': 'BATCH123',
            'expiry_date': '2025-12-31',
            'notes': 'Restocked from pharmacy'
        }
        
        url = f"{reverse('medication-detail', args=[medication.id])}add_stock/"
        response = self.client.post(url, stock_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_stock'], 40)
        self.assertEqual(response.data['batch_number'], 'BATCH123')
        
        # Verify stock transaction was created
        transactions = StockTransaction.objects.filter(medication=medication)
        self.assertEqual(transactions.count(), 1)
        
        transaction = transactions.first()
        self.assertEqual(transaction.quantity, 30)
        self.assertEqual(transaction.unit_price, Decimal('15.50'))
        self.assertEqual(transaction.total_amount, Decimal('465.00'))
    
    def test_add_stock_invalid_quantity(self):
        """Test stock addition with invalid quantity."""
        medication = Medication.objects.create(
            name='Test Medication',
            strength='500mg',
            medication_type='tablet',
            prescription_type='prescription',
            pill_count=10
        )
        
        stock_data = {
            'quantity': -5,  # Invalid negative quantity
            'unit_price': 15.50
        }
        
        url = f"{reverse('medication-detail', args=[medication.id])}add_stock/"
        response = self.client.post(url, stock_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_stock_invalid_expiry_date(self):
        """Test stock addition with invalid expiry date format."""
        medication = Medication.objects.create(
            name='Test Medication',
            strength='500mg',
            medication_type='tablet',
            prescription_type='prescription',
            pill_count=10
        )
        
        stock_data = {
            'quantity': 30,
            'expiry_date': 'invalid-date'  # Invalid format
        }
        
        url = f"{reverse('medication-detail', args=[medication.id])}add_stock/"
        response = self.client.post(url, stock_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_audit_trail_success(self):
        """Test successful audit trail retrieval."""
        # Create a test medication with some activity
        medication = Medication.objects.create(
            name='Test Medication',
            strength='500mg',
            medication_type='tablet',
            prescription_type='prescription',
            pill_count=30
        )
        
        # Create some stock transactions
        StockTransaction.objects.create(
            medication=medication,
            user=self.admin_user,
            transaction_type='purchase',
            quantity=30,
            stock_before=0,
            stock_after=30,
            notes='Initial stock'
        )
        
        # Create some medication logs
        schedule = MedicationSchedule.objects.create(
            patient=self.patient_user,
            medication=medication,
            timing='morning',
            dosage_amount=1,
            frequency='daily'
        )
        
        from .models import MedicationLog
        MedicationLog.objects.create(
            patient=self.patient_user,
            medication=medication,
            schedule=schedule,
            scheduled_time=timezone.now(),
            actual_time=timezone.now(),
            status='taken',
            dosage_taken=1
        )
        
        # Create a stock alert
        StockAlert.objects.create(
            medication=medication,
            created_by=self.admin_user,
            alert_type='low_stock',
            priority='medium',
            title='Low Stock Alert',
            message='Medication running low',
            current_stock=5,
            threshold_level=10
        )
        
        url = f"{reverse('medication-detail', args=[medication.id])}audit_trail/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        audit_data = response.data
        self.assertEqual(len(audit_data['transactions']), 1)
        self.assertEqual(len(audit_data['logs']), 1)
        self.assertEqual(len(audit_data['alerts']), 1)
        
        # Verify transaction data
        transaction = audit_data['transactions'][0]
        self.assertEqual(transaction['type'], 'purchase')
        self.assertEqual(transaction['quantity'], 30)
        self.assertEqual(transaction['user'], 'Admin User')
    
    def test_medication_enrichment_detection(self):
        """Test medication type detection and enrichment."""
        # Test tablet detection
        med_data = {'name': 'Paracetamol Tablet', 'strength': '500mg'}
        enriched = self._test_enrichment(med_data)
        self.assertEqual(enriched['medication_type'], 'tablet')
        
        # Test capsule detection
        med_data = {'name': 'Amoxicillin Capsule', 'strength': '500mg'}
        enriched = self._test_enrichment(med_data)
        self.assertEqual(enriched['medication_type'], 'capsule')
        
        # Test liquid detection
        med_data = {'name': 'Cough Syrup', 'strength': '100ml'}
        enriched = self._test_enrichment(med_data)
        self.assertEqual(enriched['medication_type'], 'liquid')
    
    def _test_enrichment(self, med_data):
        """Helper method to test medication enrichment."""
        # Create a temporary viewset instance to test enrichment
        from .views import MedicationViewSet
        viewset = MedicationViewSet()
        return viewset._enrich_medication_data(med_data)
    
    def test_generic_name_extraction(self):
        """Test generic name extraction from medication names."""
        # Create a temporary viewset instance
        from .views import MedicationViewSet
        viewset = MedicationViewSet()
        
        # Test common generic names
        test_cases = [
            ('Paracetamol 500mg', 'acetaminophen'),
            ('Ibuprofen 400mg', 'ibuprofen'),
            ('Aspirin 100mg', 'acetylsalicylic acid'),
            ('Unknown Medication', '')  # Should return empty string
        ]
        
        for name, expected_generic in test_cases:
            extracted = viewset._extract_generic_name(name)
            self.assertEqual(extracted, expected_generic)
    
    def test_bulk_create_rollback_on_failure(self):
        """Test that bulk creation rolls back on any failure."""
        prescription_data = {
            'medications': [
                {
                    'name': 'Valid Medication',
                    'strength': '500mg',
                    'medication_type': 'tablet',
                    'initial_stock': 30
                },
                {
                    'name': '',  # Invalid: will cause failure
                    'strength': '500mg',
                    'medication_type': 'tablet',
                    'initial_stock': 30
                }
            ],
            'patient_id': self.patient_user.id
        }
        
        url = f"{self.medication_list_url}bulk_create_from_prescription/"
        response = self.client.post(url, prescription_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Verify no medications were created (rollback occurred)
        self.assertEqual(Medication.objects.count(), 0)
        self.assertEqual(StockTransaction.objects.count(), 0)
        self.assertEqual(MedicationSchedule.objects.count(), 0)
    
    def test_prescription_upload_with_schedule_parsing(self):
        """Test prescription upload with schedule parsing from instructions."""
        ocr_data = {
            'ocr_data': {
                'medications': [
                    {
                        'name': 'Test Medication',
                        'strength': '500mg',
                        'instructions': 'Take two tablets daily at 8h00 and 20h00',
                        'quantity': 60
                    }
                ],
                'prescription_info': {
                    'prescription_number': 'RX123456',
                    'prescribed_by': 'Dr. Smith',
                    'prescribed_date': '2024-01-01'
                }
            },
            'patient_id': self.patient_user.id,
            'confidence_score': 0.90
        }
        
        url = f"{self.medication_list_url}prescription_upload/"
        response = self.client.post(url, ocr_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify medication was created
        medication = Medication.objects.first()
        self.assertIsNotNone(medication)
        
        # Verify schedule was created from parsed instructions
        schedules = MedicationSchedule.objects.filter(medication=medication)
        self.assertEqual(schedules.count(), 1)
        
        schedule = schedules.first()
        self.assertEqual(schedule.dosage_amount, 2)  # "two tablets"
        self.assertEqual(schedule.frequency, 'daily')
        self.assertEqual(schedule.instructions, 'Take two tablets daily at 8h00 and 20h00')


class EnhancedMedicationViewsIntegrationTestCase(TestCase):
    """
    Integration tests for enhanced medication views.
    """
    
    def setUp(self):
        """Set up integration test data."""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            user_type='STAFF',
            first_name='Admin',
            last_name='User'
        )
        
        self.patient_user = User.objects.create_user(
            username='patient',
            email='patient@test.com',
            password='testpass123',
            user_type='PATIENT',
            first_name='John',
            last_name='Doe'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_complete_prescription_workflow(self):
        """Test complete prescription workflow from upload to stock management."""
        # Step 1: Upload prescription via OCR
        ocr_data = {
            'ocr_data': {
                'medications': [
                    {
                        'name': 'Metformin',
                        'strength': '500mg',
                        'instructions': 'Take one tablet twice daily',
                        'quantity': 60
                    }
                ],
                'prescription_info': {
                    'prescription_number': 'RX123456',
                    'prescribed_by': 'Dr. Johnson',
                    'prescribed_date': '2024-01-01'
                }
            },
            'patient_id': self.patient_user.id,
            'confidence_score': 0.85
        }
        
        url = reverse('medication-list') + 'prescription_upload/'
        response = self.client.post(url, ocr_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Step 2: Verify medication was created
        medication = Medication.objects.first()
        self.assertIsNotNone(medication)
        self.assertEqual(medication.name, 'Metformin')
        self.assertEqual(medication.pill_count, 60)
        
        # Step 3: Add additional stock
        stock_data = {
            'quantity': 30,
            'unit_price': 12.50,
            'batch_number': 'BATCH789',
            'expiry_date': '2025-06-30',
            'notes': 'Additional stock from pharmacy'
        }
        
        url = f"{reverse('medication-detail', args=[medication.id])}add_stock/"
        response = self.client.post(url, stock_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['new_stock'], 90)
        
        # Step 4: Check audit trail
        url = f"{reverse('medication-detail', args=[medication.id])}audit_trail/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        audit_data = response.data
        self.assertEqual(len(audit_data['transactions']), 2)  # Initial + additional stock
        self.assertEqual(len(audit_data['logs']), 0)  # No logs yet
        self.assertEqual(len(audit_data['alerts']), 0)  # No alerts yet
        
        # Step 5: Verify prescription renewal was created
        renewals = PrescriptionRenewal.objects.filter(medication=medication)
        self.assertEqual(renewals.count(), 1)
        
        renewal = renewals.first()
        self.assertEqual(renewal.prescription_number, 'RX123456')
        self.assertEqual(renewal.prescribed_by, 'Dr. Johnson')
    
    def test_bulk_creation_with_multiple_patients(self):
        """Test bulk creation for multiple patients."""
        # Create additional patient
        patient2 = User.objects.create_user(
            username='patient2',
            email='patient2@test.com',
            password='testpass123',
            user_type='PATIENT',
            first_name='Jane',
            last_name='Smith'
        )
        
        # Create prescriptions for both patients
        prescription_data = {
            'medications': [
                {
                    'name': 'Aspirin',
                    'strength': '100mg',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'initial_stock': 30
                }
            ],
            'patient_id': self.patient_user.id,
            'prescription_number': 'RX001',
            'prescribed_by': 'Dr. Smith',
            'prescribed_date': '2024-01-01'
        }
        
        url = reverse('medication-list') + 'bulk_create_from_prescription/'
        response = self.client.post(url, prescription_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Create prescription for second patient
        prescription_data['patient_id'] = patient2.id
        prescription_data['prescription_number'] = 'RX002'
        response = self.client.post(url, prescription_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify medications were created for both patients
        medications = Medication.objects.all()
        self.assertEqual(medications.count(), 2)
        
        # Verify schedules were created for both patients
        schedules = MedicationSchedule.objects.all()
        self.assertEqual(schedules.count(), 2)
        
        # Verify prescription renewals were created for both patients
        renewals = PrescriptionRenewal.objects.all()
        self.assertEqual(renewals.count(), 2)
        
        # Verify each patient has their own schedule
        patient1_schedules = schedules.filter(patient=self.patient_user)
        patient2_schedules = schedules.filter(patient=patient2)
        self.assertEqual(patient1_schedules.count(), 1)
        self.assertEqual(patient2_schedules.count(), 1) 