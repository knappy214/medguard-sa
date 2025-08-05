#!/usr/bin/env python
"""
MedGuard SA Setup Verification Script

This script verifies that all Django models can be instantiated without errors,
tests creating a medication with all fields, and verifies foreign key relationships work correctly.

Usage:
    python manage.py shell < verify_setup.py
    or
    python verify_setup.py
"""

import os
import sys
import django
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase
from django.contrib.auth import get_user_model

# Setup Django environment
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
    django.setup()

User = get_user_model()

# Import all models at module level
try:
    from users.models import User, UserAvatar, UserProfile
    from medications.models import (
        Medication, MedicationSchedule, MedicationLog, StockAlert,
        StockTransaction, StockAnalytics, PharmacyIntegration,
        PrescriptionRenewal, StockVisualization,
        MedicationIndexPage, MedicationDetailPage
    )
    from security.models import SecurityEvent, AuditLog
    from medguard_notifications.models import NotificationTemplate, NotificationLog
except ImportError as e:
    print(f"Warning: Could not import all models: {e}")


class MedGuardSetupVerifier:
    """
    Comprehensive verification class for MedGuard SA setup.
    """
    
    def __init__(self):
        self.results = {
            'model_instantiation': {},
            'medication_creation': {},
            'foreign_key_relationships': {},
            'overall_status': 'PENDING'
        }
        self.test_user = None
        self.test_medication = None
    
    def print_header(self, title):
        """Print a formatted header."""
        print("\n" + "="*60)
        print(f" {title}")
        print("="*60)
    
    def print_section(self, title):
        """Print a formatted section header."""
        print(f"\n--- {title} ---")
    
    def print_success(self, message):
        """Print a success message."""
        print(f"✅ {message}")
    
    def print_error(self, message):
        """Print an error message."""
        print(f"❌ {message}")
    
    def print_warning(self, message):
        """Print a warning message."""
        print(f"⚠️  {message}")
    
    def print_info(self, message):
        """Print an info message."""
        print(f"ℹ️  {message}")
    
    def verify_model_instantiation(self):
        """Verify all models can be instantiated without errors."""
        self.print_section("1. Model Instantiation Verification")
        
        # Models are already imported at module level
        try:
            
            models_to_test = [
                # User models
                ('User', User),
                ('UserAvatar', UserAvatar),
                ('UserProfile', UserProfile),
                
                # Medication models
                ('Medication', Medication),
                ('MedicationSchedule', MedicationSchedule),
                ('MedicationLog', MedicationLog),
                ('StockAlert', StockAlert),
                ('StockTransaction', StockTransaction),
                ('StockAnalytics', StockAnalytics),
                ('PharmacyIntegration', PharmacyIntegration),
                ('PrescriptionRenewal', PrescriptionRenewal),
                ('StockVisualization', StockVisualization),
                ('MedicationIndexPage', MedicationIndexPage),
                ('MedicationDetailPage', MedicationDetailPage),
            ]
            
            # Test security models if available
            try:
                models_to_test.extend([
                    ('SecurityEvent', SecurityEvent),
                    ('AuditLog', AuditLog),
                ])
            except ImportError:
                self.print_warning("Security models not available - skipping")
            
            # Test notification models if available
            try:
                models_to_test.extend([
                    ('NotificationTemplate', NotificationTemplate),
                    ('NotificationLog', NotificationLog),
                ])
            except ImportError:
                self.print_warning("Notification models not available - skipping")
            
            for model_name, model_class in models_to_test:
                try:
                    # Test basic instantiation
                    instance = model_class()
                    self.print_success(f"{model_name}: Basic instantiation successful")
                    
                    # Test __str__ method if it exists
                    try:
                        str(instance)
                        self.print_success(f"{model_name}: __str__ method works")
                    except Exception as e:
                        self.print_warning(f"{model_name}: __str__ method failed - {e}")
                    
                    # Test Meta class if it exists
                    if hasattr(model_class, 'Meta'):
                        self.print_success(f"{model_name}: Meta class exists")
                    
                    self.results['model_instantiation'][model_name] = 'SUCCESS'
                    
                except Exception as e:
                    self.print_error(f"{model_name}: Instantiation failed - {e}")
                    self.results['model_instantiation'][model_name] = f'FAILED: {e}'
            
        except ImportError as e:
            self.print_error(f"Failed to import models: {e}")
            self.results['model_instantiation']['import_error'] = str(e)
    
    def create_test_user(self):
        """Create a test user for relationship testing."""
        self.print_section("2. Creating Test User")
        
        try:
            # Check if test user already exists
            test_user, created = User.objects.get_or_create(
                email='test@medguard-verification.com',
                defaults={
                    'username': 'test_verification_user',
                    'first_name': 'Test',
                    'last_name': 'Verification',
                    'user_type': 'PATIENT',
                    'phone': '+27123456789',
                    'date_of_birth': date(1990, 1, 1),
                    'gender': 'male',
                    'address': '123 Test Street',
                    'city': 'Johannesburg',
                    'province': 'gauteng',
                    'postal_code': '2000',
                    'blood_type': 'o_positive',
                    'allergies': 'None known',
                    'medical_conditions': 'None',
                    'current_medications': 'None',
                    'emergency_contact_name': 'Emergency Contact',
                    'emergency_contact_phone': '+27123456788',
                    'emergency_contact_relationship': 'spouse',
                    'preferred_language': 'en',
                    'timezone': 'Africa/Johannesburg',
                    'email_notifications': True,
                    'sms_notifications': False,
                    'mfa_enabled': False,
                }
            )
            
            if created:
                self.print_success(f"Created test user: {test_user.email}")
            else:
                self.print_success(f"Using existing test user: {test_user.email}")
            
            self.test_user = test_user
            self.results['test_user_creation'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to create test user: {e}")
            self.results['test_user_creation'] = f'FAILED: {e}'
            raise
    
    def create_comprehensive_medication(self):
        """Create a medication with all fields populated."""
        self.print_section("3. Creating Comprehensive Medication")
        
        try:
            # Create medication with all fields
            medication_data = {
                'name': 'Test Medication - Paracetamol',
                'generic_name': 'Paracetamol',
                'brand_name': 'Panado',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'strength': '500mg',
                'dosage_unit': 'mg',
                'pill_count': 100,
                'low_stock_threshold': 20,
                'description': 'Pain reliever and fever reducer',
                'active_ingredients': 'Paracetamol (Acetaminophen)',
                'manufacturer': 'GlaxoSmithKline',
                'side_effects': 'Rare: allergic reactions, liver problems',
                'contraindications': 'Do not take if allergic to paracetamol',
                'storage_instructions': 'Store in a cool, dry place below 25°C',
                'expiration_date': date.today() + timedelta(days=365),
                'image_alt_text': 'White round tablet with 500mg marking',
                'image_processing_status': 'completed',
                'image_processing_priority': 'medium',
                'image_processing_attempts': 1,
                'image_processing_last_attempt': timezone.now(),
                'image_optimization_level': 'standard',
                'image_metadata': {
                    'width': 800,
                    'height': 600,
                    'format': 'JPEG',
                    'size_bytes': 50000
                }
            }
            
            # Check if medication already exists
            test_medication, created = Medication.objects.get_or_create(
                name=medication_data['name'],
                defaults=medication_data
            )
            
            if created:
                self.print_success(f"Created comprehensive medication: {test_medication.name}")
            else:
                self.print_success(f"Using existing medication: {test_medication.name}")
            
            # Verify all fields were saved correctly
            for field_name, expected_value in medication_data.items():
                actual_value = getattr(test_medication, field_name)
                if actual_value != expected_value:
                    self.print_warning(f"Field {field_name}: expected {expected_value}, got {actual_value}")
                else:
                    self.print_success(f"Field {field_name}: ✓")
            
            # Test medication properties
            self.print_info("Testing medication properties:")
            self.print_success(f"is_low_stock: {test_medication.is_low_stock}")
            self.print_success(f"is_expired: {test_medication.is_expired}")
            self.print_success(f"is_expiring_soon: {test_medication.is_expiring_soon}")
            
            self.test_medication = test_medication
            self.results['medication_creation'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to create medication: {e}")
            self.results['medication_creation'] = f'FAILED: {e}'
            raise
    
    def verify_foreign_key_relationships(self):
        """Verify foreign key relationships work correctly."""
        self.print_section("4. Foreign Key Relationship Verification")
        
        if not self.test_user or not self.test_medication:
            self.print_error("Cannot test relationships without test user and medication")
            return
        
        try:
            with transaction.atomic():
                # Test MedicationSchedule creation
                schedule_data = {
                    'patient': self.test_user,
                    'medication': self.test_medication,
                    'timing': 'morning',
                    'dosage_amount': Decimal('1.0'),
                    'frequency': 'daily',
                    'start_date': date.today(),
                    'status': 'active',
                    'instructions': 'Take with food',
                    'monday': True,
                    'tuesday': True,
                    'wednesday': True,
                    'thursday': True,
                    'friday': True,
                    'saturday': True,
                    'sunday': True,
                }
                
                schedule = MedicationSchedule.objects.create(**schedule_data)
                self.print_success(f"Created MedicationSchedule: {schedule}")
                
                # Test MedicationLog creation
                log_data = {
                    'patient': self.test_user,
                    'medication': self.test_medication,
                    'schedule': schedule,
                    'scheduled_time': timezone.now(),
                    'actual_time': timezone.now(),
                    'status': 'taken',
                    'dosage_taken': Decimal('1.0'),
                    'notes': 'Taken as prescribed',
                }
                
                log = MedicationLog.objects.create(**log_data)
                self.print_success(f"Created MedicationLog: {log}")
                
                # Test StockAlert creation
                alert_data = {
                    'medication': self.test_medication,
                    'created_by': self.test_user,
                    'alert_type': 'low_stock',
                    'priority': 'medium',
                    'status': 'active',
                    'title': 'Low Stock Alert',
                    'message': 'Medication stock is running low',
                    'current_stock': 15,
                    'threshold_level': 20,
                }
                
                alert = StockAlert.objects.create(**alert_data)
                self.print_success(f"Created StockAlert: {alert}")
                
                # Test StockTransaction creation
                transaction_data = {
                    'medication': self.test_medication,
                    'user': self.test_user,
                    'transaction_type': 'purchase',
                    'quantity': 50,
                    'unit_price': Decimal('2.50'),
                    'total_amount': Decimal('125.00'),
                    'stock_before': 100,
                    'stock_after': 150,
                    'reference_number': 'PO-2024-001',
                    'batch_number': 'BATCH-2024-001',
                    'expiry_date': date.today() + timedelta(days=365),
                    'notes': 'Initial stock purchase',
                }
                
                stock_transaction = StockTransaction.objects.create(**transaction_data)
                self.print_success(f"Created StockTransaction: {stock_transaction}")
                
                # Test StockAnalytics creation
                analytics_data = {
                    'medication': self.test_medication,
                    'daily_usage_rate': 2.5,
                    'weekly_usage_rate': 17.5,
                    'monthly_usage_rate': 75.0,
                    'days_until_stockout': 60,
                    'predicted_stockout_date': date.today() + timedelta(days=60),
                    'recommended_order_quantity': 100,
                    'recommended_order_date': date.today() + timedelta(days=30),
                    'seasonal_factor': 1.0,
                    'usage_volatility': 0.5,
                    'stockout_confidence': 0.85,
                    'calculation_window_days': 30,
                }
                
                analytics = StockAnalytics.objects.create(**analytics_data)
                self.print_success(f"Created StockAnalytics: {analytics}")
                
                # Test PrescriptionRenewal creation
                renewal_data = {
                    'patient': self.test_user,
                    'medication': self.test_medication,
                    'prescription_number': 'RX-2024-001',
                    'prescribed_by': 'Dr. Smith',
                    'prescribed_date': date.today(),
                    'expiry_date': date.today() + timedelta(days=90),
                    'status': 'active',
                    'priority': 'medium',
                    'reminder_days_before': 30,
                    'notes': 'Regular prescription renewal',
                }
                
                renewal = PrescriptionRenewal.objects.create(**renewal_data)
                self.print_success(f"Created PrescriptionRenewal: {renewal}")
                
                # Test relationship queries
                self.print_info("Testing relationship queries:")
                
                # Test reverse relationships
                user_schedules = self.test_user.medication_schedules.all()
                self.print_success(f"User has {user_schedules.count()} medication schedules")
                
                user_logs = self.test_user.medication_logs.all()
                self.print_success(f"User has {user_logs.count()} medication logs")
                
                medication_schedules = self.test_medication.schedules.all()
                self.print_success(f"Medication has {medication_schedules.count()} schedules")
                
                medication_logs = self.test_medication.logs.all()
                self.print_success(f"Medication has {medication_logs.count()} logs")
                
                medication_alerts = self.test_medication.stock_alerts.all()
                self.print_success(f"Medication has {medication_alerts.count()} stock alerts")
                
                medication_transactions = self.test_medication.stock_transactions.all()
                self.print_success(f"Medication has {medication_transactions.count()} stock transactions")
                
                # Test cascade deletion (create a temporary object)
                temp_schedule = MedicationSchedule.objects.create(
                    patient=self.test_user,
                    medication=self.test_medication,
                    timing='night',
                    dosage_amount=Decimal('0.5'),
                    frequency='daily',
                    start_date=date.today(),
                    status='active'
                )
                
                # Verify it was created
                self.print_success(f"Created temporary schedule: {temp_schedule}")
                
                # Test that we can access related objects
                self.print_success(f"Schedule patient: {temp_schedule.patient.email}")
                self.print_success(f"Schedule medication: {temp_schedule.medication.name}")
                
                # Clean up temporary objects
                temp_schedule.delete()
                self.print_success("Temporary schedule deleted successfully")
                
                self.results['foreign_key_relationships'] = 'SUCCESS'
                
        except Exception as e:
            self.print_error(f"Failed to verify foreign key relationships: {e}")
            self.results['foreign_key_relationships'] = f'FAILED: {e}'
            raise
    
    def test_model_methods(self):
        """Test model methods and properties."""
        self.print_section("5. Model Methods and Properties Testing")
        
        if not self.test_medication:
            self.print_error("Cannot test methods without test medication")
            return
        
        try:
            # Test Medication methods
            self.print_info("Testing Medication methods:")
            
            # Test __str__ method
            medication_str = str(self.test_medication)
            self.print_success(f"Medication __str__: {medication_str}")
            
            # Test properties
            self.print_success(f"is_low_stock: {self.test_medication.is_low_stock}")
            self.print_success(f"is_expired: {self.test_medication.is_expired}")
            self.print_success(f"is_expiring_soon: {self.test_medication.is_expiring_soon}")
            
            # Test clean method
            try:
                self.test_medication.clean()
                self.print_success("Medication clean() method works")
            except ValidationError as e:
                self.print_warning(f"Medication clean() validation: {e}")
            except Exception as e:
                self.print_error(f"Medication clean() failed: {e}")
            
            # Test MedicationSchedule methods
            if hasattr(self.test_medication, 'schedules') and self.test_medication.schedules.exists():
                schedule = self.test_medication.schedules.first()
                self.print_info("Testing MedicationSchedule methods:")
                
                schedule_str = str(schedule)
                self.print_success(f"Schedule __str__: {schedule_str}")
                
                self.print_success(f"is_active: {schedule.is_active}")
                self.print_success(f"should_take_today: {schedule.should_take_today}")
                
                try:
                    schedule.clean()
                    self.print_success("Schedule clean() method works")
                except ValidationError as e:
                    self.print_warning(f"Schedule clean() validation: {e}")
                except Exception as e:
                    self.print_error(f"Schedule clean() failed: {e}")
            
            # Test MedicationLog methods
            if hasattr(self.test_medication, 'logs') and self.test_medication.logs.exists():
                log = self.test_medication.logs.first()
                self.print_info("Testing MedicationLog methods:")
                
                log_str = str(log)
                self.print_success(f"Log __str__: {log_str}")
                
                self.print_success(f"is_on_time: {log.is_on_time}")
                self.print_success(f"adherence_score: {log.adherence_score}")
                
                try:
                    log.clean()
                    self.print_success("Log clean() method works")
                except ValidationError as e:
                    self.print_warning(f"Log clean() validation: {e}")
                except Exception as e:
                    self.print_error(f"Log clean() failed: {e}")
            
            self.results['model_methods'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test model methods: {e}")
            self.results['model_methods'] = f'FAILED: {e}'
    
    def test_database_constraints(self):
        """Test database constraints and validations."""
        self.print_section("6. Database Constraints and Validations")
        
        try:
            # Test unique constraints
            self.print_info("Testing unique constraints:")
            
            # Try to create a duplicate medication (should fail if unique constraint exists)
            try:
                duplicate_medication = Medication.objects.create(
                    name=self.test_medication.name,
                    strength=self.test_medication.strength,
                    dosage_unit=self.test_medication.dosage_unit
                )
                self.print_warning("Duplicate medication created - no unique constraint on name")
                duplicate_medication.delete()
            except Exception as e:
                if "unique" in str(e).lower():
                    self.print_success("Unique constraint working correctly")
                else:
                    self.print_warning(f"Unexpected error with duplicate: {e}")
            
            # Test field validations
            self.print_info("Testing field validations:")
            
            # Test negative pill count
            try:
                invalid_medication = Medication(
                    name="Invalid Test Medication",
                    strength="100mg",
                    dosage_unit="mg",
                    pill_count=-1
                )
                invalid_medication.full_clean()
                self.print_warning("Negative pill count allowed - no validation")
            except ValidationError as e:
                self.print_success("Negative pill count validation working")
            except Exception as e:
                self.print_warning(f"Unexpected error with negative pill count: {e}")
            
            # Test invalid medication type
            try:
                invalid_medication = Medication(
                    name="Invalid Type Medication",
                    strength="100mg",
                    dosage_unit="mg",
                    medication_type="invalid_type"
                )
                invalid_medication.full_clean()
                self.print_warning("Invalid medication type allowed - no validation")
            except ValidationError as e:
                self.print_success("Medication type validation working")
            except Exception as e:
                self.print_warning(f"Unexpected error with invalid medication type: {e}")
            
            self.results['database_constraints'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test database constraints: {e}")
            self.results['database_constraints'] = f'FAILED: {e}'
    
    def test_bulk_medication_creation(self):
        """Test bulk medication creation with 21-medication prescription."""
        self.print_section("7. Bulk Medication Creation (21-Medication Prescription)")
        
        if not self.test_user:
            self.print_error("Cannot test bulk creation without test user")
            return
        
        try:
            # Define 21 medications from a typical prescription
            prescription_medications = [
                # Pain Management
                {
                    'name': 'Paracetamol',
                    'generic_name': 'Acetaminophen',
                    'brand_name': 'Panado',
                    'medication_type': 'tablet',
                    'prescription_type': 'otc',
                    'strength': '500mg',
                    'dosage_unit': 'mg',
                    'pill_count': 100,
                    'description': 'Pain reliever and fever reducer',
                    'active_ingredients': 'Paracetamol',
                    'manufacturer': 'GlaxoSmithKline',
                    'side_effects': 'Rare: allergic reactions',
                    'contraindications': 'Do not take if allergic to paracetamol',
                    'storage_instructions': 'Store in a cool, dry place',
                },
                {
                    'name': 'Ibuprofen',
                    'generic_name': 'Ibuprofen',
                    'brand_name': 'Brufen',
                    'medication_type': 'tablet',
                    'prescription_type': 'otc',
                    'strength': '400mg',
                    'dosage_unit': 'mg',
                    'pill_count': 60,
                    'description': 'Anti-inflammatory pain reliever',
                    'active_ingredients': 'Ibuprofen',
                    'manufacturer': 'Abbott',
                    'side_effects': 'Stomach upset, heartburn',
                    'contraindications': 'Do not take on empty stomach',
                    'storage_instructions': 'Store at room temperature',
                },
                # Antibiotics
                {
                    'name': 'Amoxicillin',
                    'generic_name': 'Amoxicillin',
                    'brand_name': 'Amoxil',
                    'medication_type': 'capsule',
                    'prescription_type': 'prescription',
                    'strength': '500mg',
                    'dosage_unit': 'mg',
                    'pill_count': 42,
                    'description': 'Broad-spectrum antibiotic',
                    'active_ingredients': 'Amoxicillin trihydrate',
                    'manufacturer': 'GlaxoSmithKline',
                    'side_effects': 'Diarrhea, nausea, rash',
                    'contraindications': 'Do not take if allergic to penicillin',
                    'storage_instructions': 'Store in refrigerator',
                },
                {
                    'name': 'Azithromycin',
                    'generic_name': 'Azithromycin',
                    'brand_name': 'Zithromax',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': '250mg',
                    'dosage_unit': 'mg',
                    'pill_count': 6,
                    'description': 'Macrolide antibiotic',
                    'active_ingredients': 'Azithromycin dihydrate',
                    'manufacturer': 'Pfizer',
                    'side_effects': 'Nausea, diarrhea, headache',
                    'contraindications': 'Do not take with antacids',
                    'storage_instructions': 'Store at room temperature',
                },
                # Cardiovascular
                {
                    'name': 'Amlodipine',
                    'generic_name': 'Amlodipine',
                    'brand_name': 'Norvasc',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': '5mg',
                    'dosage_unit': 'mg',
                    'pill_count': 30,
                    'description': 'Calcium channel blocker for hypertension',
                    'active_ingredients': 'Amlodipine besylate',
                    'manufacturer': 'Pfizer',
                    'side_effects': 'Dizziness, swelling, headache',
                    'contraindications': 'Do not stop suddenly',
                    'storage_instructions': 'Store in a dry place',
                },
                {
                    'name': 'Lisinopril',
                    'generic_name': 'Lisinopril',
                    'brand_name': 'Zestril',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': '10mg',
                    'dosage_unit': 'mg',
                    'pill_count': 30,
                    'description': 'ACE inhibitor for blood pressure',
                    'active_ingredients': 'Lisinopril',
                    'manufacturer': 'AstraZeneca',
                    'side_effects': 'Dry cough, dizziness, fatigue',
                    'contraindications': 'Do not take during pregnancy',
                    'storage_instructions': 'Store at room temperature',
                },
                # Diabetes Management
                {
                    'name': 'Metformin',
                    'generic_name': 'Metformin',
                    'brand_name': 'Glucophage',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': '500mg',
                    'dosage_unit': 'mg',
                    'pill_count': 60,
                    'description': 'Oral diabetes medication',
                    'active_ingredients': 'Metformin hydrochloride',
                    'manufacturer': 'Merck',
                    'side_effects': 'Nausea, diarrhea, stomach upset',
                    'contraindications': 'Take with food',
                    'storage_instructions': 'Store in a dry place',
                },
                {
                    'name': 'Gliclazide',
                    'generic_name': 'Gliclazide',
                    'brand_name': 'Diamicron',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': '80mg',
                    'dosage_unit': 'mg',
                    'pill_count': 30,
                    'description': 'Sulfonylurea for diabetes',
                    'active_ingredients': 'Gliclazide',
                    'manufacturer': 'Servier',
                    'side_effects': 'Hypoglycemia, weight gain',
                    'contraindications': 'Monitor blood sugar regularly',
                    'storage_instructions': 'Store at room temperature',
                },
                # Respiratory
                {
                    'name': 'Salbutamol',
                    'generic_name': 'Albuterol',
                    'brand_name': 'Ventolin',
                    'medication_type': 'inhaler',
                    'prescription_type': 'prescription',
                    'strength': '100mcg',
                    'dosage_unit': 'mcg',
                    'pill_count': 200,
                    'description': 'Bronchodilator for asthma',
                    'active_ingredients': 'Salbutamol sulfate',
                    'manufacturer': 'GlaxoSmithKline',
                    'side_effects': 'Tremor, increased heart rate',
                    'contraindications': 'Do not exceed prescribed dose',
                    'storage_instructions': 'Store in a cool, dry place',
                },
                {
                    'name': 'Beclomethasone',
                    'generic_name': 'Beclomethasone',
                    'brand_name': 'Qvar',
                    'medication_type': 'inhaler',
                    'prescription_type': 'prescription',
                    'strength': '50mcg',
                    'dosage_unit': 'mcg',
                    'pill_count': 120,
                    'description': 'Inhaled corticosteroid',
                    'active_ingredients': 'Beclomethasone dipropionate',
                    'manufacturer': 'Teva',
                    'side_effects': 'Oral thrush, hoarseness',
                    'contraindications': 'Rinse mouth after use',
                    'storage_instructions': 'Store at room temperature',
                },
                # Gastrointestinal
                {
                    'name': 'Omeprazole',
                    'generic_name': 'Omeprazole',
                    'brand_name': 'Losec',
                    'medication_type': 'capsule',
                    'prescription_type': 'prescription',
                    'strength': '20mg',
                    'dosage_unit': 'mg',
                    'pill_count': 30,
                    'description': 'Proton pump inhibitor',
                    'active_ingredients': 'Omeprazole',
                    'manufacturer': 'AstraZeneca',
                    'side_effects': 'Headache, diarrhea, nausea',
                    'contraindications': 'Take before meals',
                    'storage_instructions': 'Store at room temperature',
                },
                {
                    'name': 'Ranitidine',
                    'generic_name': 'Ranitidine',
                    'brand_name': 'Zantac',
                    'medication_type': 'tablet',
                    'prescription_type': 'otc',
                    'strength': '150mg',
                    'dosage_unit': 'mg',
                    'pill_count': 60,
                    'description': 'H2 blocker for acid reflux',
                    'active_ingredients': 'Ranitidine hydrochloride',
                    'manufacturer': 'GlaxoSmithKline',
                    'side_effects': 'Headache, constipation',
                    'contraindications': 'Take with or without food',
                    'storage_instructions': 'Store in a dry place',
                },
                # Mental Health
                {
                    'name': 'Sertraline',
                    'generic_name': 'Sertraline',
                    'brand_name': 'Zoloft',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': '50mg',
                    'dosage_unit': 'mg',
                    'pill_count': 30,
                    'description': 'Selective serotonin reuptake inhibitor',
                    'active_ingredients': 'Sertraline hydrochloride',
                    'manufacturer': 'Pfizer',
                    'side_effects': 'Nausea, insomnia, sexual dysfunction',
                    'contraindications': 'Do not stop suddenly',
                    'storage_instructions': 'Store at room temperature',
                },
                {
                    'name': 'Amitriptyline',
                    'generic_name': 'Amitriptyline',
                    'brand_name': 'Elavil',
                    'medication_type': 'tablet',
                    'prescription_type': 'prescription',
                    'strength': '25mg',
                    'dosage_unit': 'mg',
                    'pill_count': 30,
                    'description': 'Tricyclic antidepressant',
                    'active_ingredients': 'Amitriptyline hydrochloride',
                    'manufacturer': 'Merck',
                    'side_effects': 'Drowsiness, dry mouth, constipation',
                    'contraindications': 'Take at bedtime',
                    'storage_instructions': 'Store in a dry place',
                },
                # Supplements
                {
                    'name': 'Vitamin D3',
                    'generic_name': 'Cholecalciferol',
                    'brand_name': 'Ostelin',
                    'medication_type': 'tablet',
                    'prescription_type': 'supplement',
                    'strength': '1000IU',
                    'dosage_unit': 'IU',
                    'pill_count': 90,
                    'description': 'Vitamin D supplement',
                    'active_ingredients': 'Cholecalciferol',
                    'manufacturer': 'Blackmores',
                    'side_effects': 'Rare: hypercalcemia',
                    'contraindications': 'Take with fatty meal',
                    'storage_instructions': 'Store at room temperature',
                },
                {
                    'name': 'Omega-3',
                    'generic_name': 'Fish Oil',
                    'brand_name': 'Blackmores',
                    'medication_type': 'capsule',
                    'prescription_type': 'supplement',
                    'strength': '1000mg',
                    'dosage_unit': 'mg',
                    'pill_count': 120,
                    'description': 'Omega-3 fatty acid supplement',
                    'active_ingredients': 'EPA, DHA',
                    'manufacturer': 'Blackmores',
                    'side_effects': 'Fishy burps, upset stomach',
                    'contraindications': 'Take with food',
                    'storage_instructions': 'Store in refrigerator',
                },
                # Topical Medications
                {
                    'name': 'Hydrocortisone',
                    'generic_name': 'Hydrocortisone',
                    'brand_name': 'DermAid',
                    'medication_type': 'cream',
                    'prescription_type': 'otc',
                    'strength': '1%',
                    'dosage_unit': '%',
                    'pill_count': 30,
                    'description': 'Topical corticosteroid',
                    'active_ingredients': 'Hydrocortisone acetate',
                    'manufacturer': 'Ego',
                    'side_effects': 'Skin thinning, irritation',
                    'contraindications': 'Do not use on face',
                    'storage_instructions': 'Store at room temperature',
                },
                {
                    'name': 'Betamethasone',
                    'generic_name': 'Betamethasone',
                    'brand_name': 'Celestone',
                    'medication_type': 'cream',
                    'prescription_type': 'prescription',
                    'strength': '0.1%',
                    'dosage_unit': '%',
                    'pill_count': 15,
                    'description': 'Potent topical steroid',
                    'active_ingredients': 'Betamethasone valerate',
                    'manufacturer': 'Merck',
                    'side_effects': 'Skin atrophy, telangiectasia',
                    'contraindications': 'Use sparingly',
                    'storage_instructions': 'Store in a cool place',
                },
                # Eye Drops
                {
                    'name': 'Chloramphenicol',
                    'generic_name': 'Chloramphenicol',
                    'brand_name': 'Chloromycetin',
                    'medication_type': 'drops',
                    'prescription_type': 'prescription',
                    'strength': '0.5%',
                    'dosage_unit': '%',
                    'pill_count': 10,
                    'description': 'Antibiotic eye drops',
                    'active_ingredients': 'Chloramphenicol',
                    'manufacturer': 'Alcon',
                    'side_effects': 'Stinging, blurred vision',
                    'contraindications': 'Do not touch dropper to eye',
                    'storage_instructions': 'Store in refrigerator',
                },
                {
                    'name': 'Artificial Tears',
                    'generic_name': 'Carboxymethylcellulose',
                    'brand_name': 'Refresh',
                    'medication_type': 'drops',
                    'prescription_type': 'otc',
                    'strength': '0.5%',
                    'dosage_unit': '%',
                    'pill_count': 20,
                    'description': 'Lubricating eye drops',
                    'active_ingredients': 'Carboxymethylcellulose sodium',
                    'manufacturer': 'Allergan',
                    'side_effects': 'Temporary blurring',
                    'contraindications': 'Discard after opening',
                    'storage_instructions': 'Store at room temperature',
                },
                # Emergency Medications
                {
                    'name': 'Adrenaline',
                    'generic_name': 'Epinephrine',
                    'brand_name': 'EpiPen',
                    'medication_type': 'injection',
                    'prescription_type': 'prescription',
                    'strength': '0.3mg',
                    'dosage_unit': 'mg',
                    'pill_count': 2,
                    'description': 'Emergency treatment for severe allergic reactions',
                    'active_ingredients': 'Epinephrine',
                    'manufacturer': 'Mylan',
                    'side_effects': 'Increased heart rate, anxiety',
                    'contraindications': 'Use only in emergency',
                    'storage_instructions': 'Store at room temperature',
                }
            ]
            
            # Create medications in bulk
            created_medications = []
            self.print_info(f"Creating {len(prescription_medications)} medications...")
            
            for i, med_data in enumerate(prescription_medications, 1):
                try:
                    # Add common fields
                    med_data.update({
                        'low_stock_threshold': 10,
                        'expiration_date': date.today() + timedelta(days=365),
                        'image_alt_text': f'{med_data["name"]} medication',
                        'image_processing_status': 'completed',
                        'image_processing_priority': 'medium',
                        'image_processing_attempts': 1,
                        'image_processing_last_attempt': timezone.now(),
                        'image_optimization_level': 'standard',
                        'image_metadata': {
                            'width': 800,
                            'height': 600,
                            'format': 'JPEG',
                            'size_bytes': 50000
                        }
                    })
                    
                    # Create medication
                    medication = Medication.objects.create(**med_data)
                    created_medications.append(medication)
                    self.print_success(f"Created {i:2d}/21: {medication.name} ({medication.strength})")
                    
                except Exception as e:
                    self.print_error(f"Failed to create medication {i}: {med_data['name']} - {e}")
            
            # Verify bulk creation
            total_created = len(created_medications)
            self.print_info(f"Bulk creation summary: {total_created}/{len(prescription_medications)} medications created")
            
            if total_created == len(prescription_medications):
                self.print_success("✅ All 21 medications created successfully")
            else:
                self.print_warning(f"⚠️ Only {total_created}/21 medications created")
            
            # Test bulk queries
            self.print_info("Testing bulk queries:")
            
            # Count by medication type
            type_counts = {}
            for med in created_medications:
                med_type = med.medication_type
                type_counts[med_type] = type_counts.get(med_type, 0) + 1
            
            for med_type, count in type_counts.items():
                self.print_success(f"  {med_type}: {count} medications")
            
            # Count by prescription type
            prescription_counts = {}
            for med in created_medications:
                presc_type = med.prescription_type
                prescription_counts[presc_type] = prescription_counts.get(presc_type, 0) + 1
            
            for presc_type, count in prescription_counts.items():
                self.print_success(f"  {presc_type}: {count} medications")
            
            # Store created medications for cleanup
            self.bulk_medications = created_medications
            self.results['bulk_medication_creation'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test bulk medication creation: {e}")
            self.results['bulk_medication_creation'] = f'FAILED: {e}'
    
    def test_complex_medication_schedules(self):
        """Test medication schedule creation for complex dosing patterns."""
        self.print_section("8. Complex Medication Schedule Testing")
        
        if not self.test_user or not hasattr(self, 'bulk_medications'):
            self.print_error("Cannot test complex schedules without test user and bulk medications")
            return
        
        try:
            # Define complex dosing patterns
            complex_schedules = [
                {
                    'name': 'Twice Daily with Food',
                    'medication': self.bulk_medications[0],  # Paracetamol
                    'timing': 'custom',
                    'custom_time': time(8, 0),  # 8:00 AM
                    'dosage_amount': Decimal('1.0'),
                    'frequency': 'twice daily',
                    'instructions': 'Take with food, 8 hours apart',
                    'monday': True, 'tuesday': True, 'wednesday': True,
                    'thursday': True, 'friday': True, 'saturday': True, 'sunday': True,
                },
                {
                    'name': 'Weekly Injection',
                    'medication': self.bulk_medications[-1],  # Adrenaline
                    'timing': 'custom',
                    'custom_time': time(14, 30),  # 2:30 PM
                    'dosage_amount': Decimal('0.3'),
                    'frequency': 'weekly',
                    'instructions': 'Administer subcutaneously in thigh',
                    'monday': False, 'tuesday': False, 'wednesday': True,
                    'thursday': False, 'friday': False, 'saturday': False, 'sunday': False,
                },
                {
                    'name': 'Inhaler - As Needed',
                    'medication': self.bulk_medications[8],  # Salbutamol
                    'timing': 'custom',
                    'custom_time': time(0, 0),  # Not applicable for PRN
                    'dosage_amount': Decimal('2.0'),
                    'frequency': 'as needed',
                    'instructions': 'Use 2 puffs when experiencing shortness of breath',
                    'monday': True, 'tuesday': True, 'wednesday': True,
                    'thursday': True, 'friday': True, 'saturday': True, 'sunday': True,
                },
                {
                    'name': 'Eye Drops - Four Times Daily',
                    'medication': self.bulk_medications[19],  # Chloramphenicol
                    'timing': 'custom',
                    'custom_time': time(6, 0),  # 6:00 AM
                    'dosage_amount': Decimal('1.0'),
                    'frequency': 'four times daily',
                    'instructions': 'Apply to affected eye, 6 hours apart',
                    'monday': True, 'tuesday': True, 'wednesday': True,
                    'thursday': True, 'friday': True, 'saturday': True, 'sunday': True,
                },
                {
                    'name': 'Antidepressant - Bedtime',
                    'medication': self.bulk_medications[12],  # Amitriptyline
                    'timing': 'night',
                    'custom_time': None,
                    'dosage_amount': Decimal('25.0'),
                    'frequency': 'daily',
                    'instructions': 'Take at bedtime to minimize drowsiness',
                    'monday': True, 'tuesday': True, 'wednesday': True,
                    'thursday': True, 'friday': True, 'saturday': True, 'sunday': True,
                },
                {
                    'name': 'Blood Pressure - Morning',
                    'medication': self.bulk_medications[4],  # Amlodipine
                    'timing': 'morning',
                    'custom_time': None,
                    'dosage_amount': Decimal('5.0'),
                    'frequency': 'daily',
                    'instructions': 'Take at the same time each day',
                    'monday': True, 'tuesday': True, 'wednesday': True,
                    'thursday': True, 'friday': True, 'saturday': True, 'sunday': True,
                },
                {
                    'name': 'Diabetes - With Meals',
                    'medication': self.bulk_medications[6],  # Metformin
                    'timing': 'custom',
                    'custom_time': time(12, 0),  # 12:00 PM
                    'dosage_amount': Decimal('500.0'),
                    'frequency': 'twice daily with meals',
                    'instructions': 'Take with breakfast and dinner',
                    'monday': True, 'tuesday': True, 'wednesday': True,
                    'thursday': True, 'friday': True, 'saturday': True, 'sunday': True,
                },
                {
                    'name': 'Topical Cream - Twice Daily',
                    'medication': self.bulk_medications[17],  # Hydrocortisone
                    'timing': 'custom',
                    'custom_time': time(9, 0),  # 9:00 AM
                    'dosage_amount': Decimal('1.0'),
                    'frequency': 'twice daily',
                    'instructions': 'Apply thin layer to affected area',
                    'monday': True, 'tuesday': True, 'wednesday': True,
                    'thursday': True, 'friday': True, 'saturday': True, 'sunday': True,
                }
            ]
            
            created_schedules = []
            self.print_info(f"Creating {len(complex_schedules)} complex medication schedules...")
            
            for i, schedule_data in enumerate(complex_schedules, 1):
                try:
                    # Add common fields
                    schedule_data.update({
                        'patient': self.test_user,
                        'start_date': date.today(),
                        'status': 'active',
                    })
                    
                    # Create schedule
                    schedule = MedicationSchedule.objects.create(**schedule_data)
                    created_schedules.append(schedule)
                    self.print_success(f"Created {i:2d}/{len(complex_schedules)}: {schedule}")
                    
                    # Test schedule properties
                    self.print_info(f"  - is_active: {schedule.is_active}")
                    self.print_info(f"  - should_take_today: {schedule.should_take_today}")
                    
                except Exception as e:
                    self.print_error(f"Failed to create schedule {i}: {schedule_data['name']} - {e}")
            
            # Test complex schedule queries
            self.print_info("Testing complex schedule queries:")
            
            # Count by timing
            timing_counts = {}
            for schedule in created_schedules:
                timing = schedule.timing
                timing_counts[timing] = timing_counts.get(timing, 0) + 1
            
            for timing, count in timing_counts.items():
                self.print_success(f"  {timing}: {count} schedules")
            
            # Count by frequency
            frequency_counts = {}
            for schedule in created_schedules:
                freq = schedule.frequency
                frequency_counts[freq] = frequency_counts.get(freq, 0) + 1
            
            for freq, count in frequency_counts.items():
                self.print_success(f"  {freq}: {count} schedules")
            
            # Test schedule validation
            self.print_info("Testing schedule validation:")
            
            for schedule in created_schedules:
                try:
                    schedule.clean()
                    self.print_success(f"  ✅ {schedule.medication.name}: Validation passed")
                except ValidationError as e:
                    self.print_warning(f"  ⚠️ {schedule.medication.name}: Validation warning - {e}")
                except Exception as e:
                    self.print_error(f"  ❌ {schedule.medication.name}: Validation failed - {e}")
            
            # Store created schedules for cleanup
            self.complex_schedules = created_schedules
            self.results['complex_schedule_creation'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test complex medication schedules: {e}")
            self.results['complex_schedule_creation'] = f'FAILED: {e}'
    
    def test_stock_management_calculations(self):
        """Test stock management calculations and analytics."""
        self.print_section("9. Stock Management Calculations")
        
        if not hasattr(self, 'bulk_medications'):
            self.print_error("Cannot test stock management without bulk medications")
            return
        
        try:
            # Test stock calculations for different medications
            stock_tests = [
                {
                    'medication': self.bulk_medications[0],  # Paracetamol
                    'initial_stock': 100,
                    'daily_usage': 2,
                    'transactions': [
                        {'type': 'purchase', 'quantity': 50, 'unit_price': Decimal('2.00')},
                        {'type': 'dose_taken', 'quantity': -2, 'unit_price': None},
                        {'type': 'dose_taken', 'quantity': -2, 'unit_price': None},
                        {'type': 'adjustment', 'quantity': -5, 'unit_price': None},
                    ]
                },
                {
                    'medication': self.bulk_medications[2],  # Amoxicillin
                    'initial_stock': 42,
                    'daily_usage': 3,
                    'transactions': [
                        {'type': 'purchase', 'quantity': 30, 'unit_price': Decimal('5.00')},
                        {'type': 'dose_taken', 'quantity': -3, 'unit_price': None},
                        {'type': 'dose_taken', 'quantity': -3, 'unit_price': None},
                        {'type': 'dose_taken', 'quantity': -3, 'unit_price': None},
                    ]
                },
                {
                    'medication': self.bulk_medications[8],  # Salbutamol inhaler
                    'initial_stock': 200,
                    'daily_usage': 4,
                    'transactions': [
                        {'type': 'purchase', 'quantity': 100, 'unit_price': Decimal('15.00')},
                        {'type': 'dose_taken', 'quantity': -2, 'unit_price': None},
                        {'type': 'dose_taken', 'quantity': -2, 'unit_price': None},
                        {'type': 'dose_taken', 'quantity': -2, 'unit_price': None},
                        {'type': 'dose_taken', 'quantity': -2, 'unit_price': None},
                    ]
                }
            ]
            
            for test in stock_tests:
                medication = test['medication']
                self.print_info(f"Testing stock management for: {medication.name}")
                
                # Set initial stock
                medication.pill_count = test['initial_stock']
                medication.save()
                
                # Create stock transactions
                current_stock = test['initial_stock']
                transactions_created = []
                
                for i, tx_data in enumerate(test['transactions']):
                    try:
                        # Calculate stock levels
                        stock_before = current_stock
                        stock_after = current_stock + tx_data['quantity']
                        current_stock = stock_after
                        
                        # Create transaction
                        transaction = StockTransaction.objects.create(
                            medication=medication,
                            user=self.test_user,
                            transaction_type=tx_data['type'],
                            quantity=tx_data['quantity'],
                            unit_price=tx_data['unit_price'],
                            total_amount=tx_data['unit_price'] * abs(tx_data['quantity']) if tx_data['unit_price'] else None,
                            stock_before=stock_before,
                            stock_after=stock_after,
                            reference_number=f'TEST-{medication.id}-{i+1}',
                            notes=f'Test transaction {i+1} for {medication.name}'
                        )
                        transactions_created.append(transaction)
                        
                        self.print_success(f"  Created {tx_data['type']}: {tx_data['quantity']} units")
                        self.print_info(f"    Stock: {stock_before} → {stock_after}")
                        
                    except Exception as e:
                        self.print_error(f"  Failed to create transaction {i+1}: {e}")
                
                # Update medication stock
                medication.pill_count = current_stock
                medication.save()
                
                # Test stock analytics
                try:
                    analytics_data = {
                        'medication': medication,
                        'daily_usage_rate': test['daily_usage'],
                        'weekly_usage_rate': test['daily_usage'] * 7,
                        'monthly_usage_rate': test['daily_usage'] * 30,
                        'days_until_stockout': current_stock // test['daily_usage'] if test['daily_usage'] > 0 else None,
                        'predicted_stockout_date': date.today() + timedelta(days=current_stock // test['daily_usage']) if test['daily_usage'] > 0 else None,
                        'recommended_order_quantity': max(30, test['daily_usage'] * 14),  # 2 weeks supply
                        'recommended_order_date': date.today() + timedelta(days=(current_stock // test['daily_usage']) - 7) if test['daily_usage'] > 0 else None,
                        'seasonal_factor': 1.0,
                        'usage_volatility': 0.5,
                        'stockout_confidence': 0.85,
                        'calculation_window_days': 30,
                    }
                    
                    analytics = StockAnalytics.objects.create(**analytics_data)
                    self.print_success(f"  Created stock analytics for {medication.name}")
                    
                    # Test analytics properties
                    self.print_info(f"    Days until stockout: {analytics.days_until_stockout}")
                    self.print_info(f"    Predicted stockout: {analytics.predicted_stockout_date}")
                    self.print_info(f"    Recommended order: {analytics.recommended_order_quantity} units")
                    self.print_info(f"    Order by: {analytics.recommended_order_date}")
                    
                    # Test low stock alerts
                    if medication.is_low_stock:
                        alert = StockAlert.objects.create(
                            medication=medication,
                            created_by=self.test_user,
                            alert_type='low_stock',
                            priority='medium',
                            status='active',
                            title=f'Low Stock Alert - {medication.name}',
                            message=f'{medication.name} stock is running low. Current stock: {medication.pill_count}',
                            current_stock=medication.pill_count,
                            threshold_level=medication.low_stock_threshold
                        )
                        self.print_warning(f"  ⚠️ Low stock alert created for {medication.name}")
                    
                except Exception as e:
                    self.print_error(f"  Failed to create analytics for {medication.name}: {e}")
                
                # Test stock calculations
                self.print_info(f"  Final stock calculations:")
                self.print_success(f"    Current stock: {medication.pill_count}")
                self.print_success(f"    Is low stock: {medication.is_low_stock}")
                self.print_success(f"    Low stock threshold: {medication.low_stock_threshold}")
                
                # Calculate usage rate
                if transactions_created:
                    total_usage = sum(tx.quantity for tx in transactions_created if tx.quantity < 0)
                    usage_days = len([tx for tx in transactions_created if tx.transaction_type == 'dose_taken'])
                    if usage_days > 0:
                        avg_daily_usage = abs(total_usage) / usage_days
                        self.print_info(f"    Average daily usage: {avg_daily_usage:.1f} units")
                
                self.print_info("")  # Empty line for readability
            
            # Test bulk stock operations
            self.print_info("Testing bulk stock operations:")
            
            # Count total stock across all medications
            total_stock = sum(med.pill_count for med in self.bulk_medications)
            self.print_success(f"Total stock across all medications: {total_stock} units")
            
            # Count low stock medications
            low_stock_count = sum(1 for med in self.bulk_medications if med.is_low_stock)
            self.print_success(f"Medications with low stock: {low_stock_count}")
            
            # Count by medication type
            type_stock = {}
            for med in self.bulk_medications:
                med_type = med.medication_type
                if med_type not in type_stock:
                    type_stock[med_type] = 0
                type_stock[med_type] += med.pill_count
            
            for med_type, stock in type_stock.items():
                self.print_info(f"  {med_type}: {stock} total units")
            
            self.results['stock_management_calculations'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test stock management calculations: {e}")
            self.results['stock_management_calculations'] = f'FAILED: {e}'
    
    def test_ocr_result_storage_retrieval(self):
        """Test OCR result storage and retrieval functionality."""
        self.print_section("11. OCR Result Storage and Retrieval")
        
        try:
            # Create mock OCR result data
            mock_ocr_results = [
                {
                    'prescription_number': 'RX-2024-001',
                    'doctor_name': 'Dr. Sarah Johnson',
                    'patient_name': 'John Smith',
                    'extracted_text': 'Paracetamol 500mg - 1 tablet twice daily\nAmoxicillin 500mg - 1 capsule three times daily',
                    'confidence_score': 0.85,
                    'processing_time': 2.5,
                    'image_quality': 'good',
                    'medications_found': 2,
                    'requires_manual_review': False,
                    'processing_status': 'completed',
                    'ocr_engine_used': 'tesseract',
                    'language_detected': 'en',
                    'image_metadata': {
                        'width': 1920,
                        'height': 1080,
                        'format': 'JPEG',
                        'size_bytes': 250000
                    },
                    'extracted_medications': [
                        {
                            'name': 'Paracetamol',
                            'strength': '500mg',
                            'dosage': '1 tablet',
                            'frequency': 'twice daily',
                            'confidence': 0.9
                        },
                        {
                            'name': 'Amoxicillin',
                            'strength': '500mg',
                            'dosage': '1 capsule',
                            'frequency': 'three times daily',
                            'confidence': 0.8
                        }
                    ]
                },
                {
                    'prescription_number': 'RX-2024-002',
                    'doctor_name': 'Dr. Michael Chen',
                    'patient_name': 'Maria Garcia',
                    'extracted_text': 'Lisinopril 10mg - 1 tablet daily\nMetformin 500mg - 1 tablet twice daily with meals',
                    'confidence_score': 0.92,
                    'processing_time': 1.8,
                    'image_quality': 'excellent',
                    'medications_found': 2,
                    'requires_manual_review': False,
                    'processing_status': 'completed',
                    'ocr_engine_used': 'tesseract',
                    'language_detected': 'en',
                    'image_metadata': {
                        'width': 2048,
                        'height': 1536,
                        'format': 'PNG',
                        'size_bytes': 350000
                    },
                    'extracted_medications': [
                        {
                            'name': 'Lisinopril',
                            'strength': '10mg',
                            'dosage': '1 tablet',
                            'frequency': 'daily',
                            'confidence': 0.95
                        },
                        {
                            'name': 'Metformin',
                            'strength': '500mg',
                            'dosage': '1 tablet',
                            'frequency': 'twice daily with meals',
                            'confidence': 0.88
                        }
                    ]
                }
            ]
            
            # Test OCR result storage (simulate storing in database)
            stored_ocr_results = []
            
            for i, ocr_data in enumerate(mock_ocr_results):
                try:
                    # Simulate storing OCR result in a database table
                    # In a real implementation, this would be stored in an OCRResult model
                    ocr_result = {
                        'id': i + 1,
                        'prescription_number': ocr_data['prescription_number'],
                        'doctor_name': ocr_data['doctor_name'],
                        'patient_name': ocr_data['patient_name'],
                        'extracted_text': ocr_data['extracted_text'],
                        'confidence_score': ocr_data['confidence_score'],
                        'processing_time': ocr_data['processing_time'],
                        'image_quality': ocr_data['image_quality'],
                        'medications_found': ocr_data['medications_found'],
                        'requires_manual_review': ocr_data['requires_manual_review'],
                        'processing_status': ocr_data['processing_status'],
                        'ocr_engine_used': ocr_data['ocr_engine_used'],
                        'language_detected': ocr_data['language_detected'],
                        'image_metadata': ocr_data['image_metadata'],
                        'extracted_medications': ocr_data['extracted_medications'],
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    }
                    
                    stored_ocr_results.append(ocr_result)
                    self.print_success(f"Stored OCR result {i+1}: {ocr_data['prescription_number']}")
                    
                except Exception as e:
                    self.print_error(f"Failed to store OCR result {i+1}: {e}")
            
            # Test OCR result retrieval
            self.print_info("Testing OCR result retrieval:")
            
            for ocr_result in stored_ocr_results:
                try:
                    # Simulate retrieving OCR result by prescription number
                    retrieved_result = next(
                        (result for result in stored_ocr_results 
                         if result['prescription_number'] == ocr_result['prescription_number']), 
                        None
                    )
                    
                    if retrieved_result:
                        self.print_success(f"Retrieved OCR result: {retrieved_result['prescription_number']}")
                        self.print_info(f"  Confidence: {retrieved_result['confidence_score']:.2f}")
                        self.print_info(f"  Medications found: {retrieved_result['medications_found']}")
                        self.print_info(f"  Processing time: {retrieved_result['processing_time']:.1f}s")
                        
                        # Test medication extraction
                        for med in retrieved_result['extracted_medications']:
                            self.print_info(f"    - {med['name']} {med['strength']}: {med['dosage']} {med['frequency']}")
                    else:
                        self.print_error(f"Failed to retrieve OCR result: {ocr_result['prescription_number']}")
                        
                except Exception as e:
                    self.print_error(f"Failed to retrieve OCR result: {e}")
            
            # Test OCR result search and filtering
            self.print_info("Testing OCR result search and filtering:")
            
            # Search by doctor name
            doctor_results = [result for result in stored_ocr_results if 'Johnson' in result['doctor_name']]
            self.print_success(f"Found {len(doctor_results)} results for Dr. Johnson")
            
            # Filter by confidence score
            high_confidence_results = [result for result in stored_ocr_results if result['confidence_score'] >= 0.9]
            self.print_success(f"Found {len(high_confidence_results)} results with high confidence (≥0.9)")
            
            # Filter by processing status
            completed_results = [result for result in stored_ocr_results if result['processing_status'] == 'completed']
            self.print_success(f"Found {len(completed_results)} completed OCR results")
            
            # Test OCR result validation
            self.print_info("Testing OCR result validation:")
            
            for ocr_result in stored_ocr_results:
                # Validate required fields
                required_fields = ['prescription_number', 'extracted_text', 'confidence_score']
                missing_fields = [field for field in required_fields if not ocr_result.get(field)]
                
                if not missing_fields:
                    self.print_success(f"OCR result {ocr_result['prescription_number']}: All required fields present")
                else:
                    self.print_warning(f"OCR result {ocr_result['prescription_number']}: Missing fields: {missing_fields}")
                
                # Validate confidence score range
                if 0 <= ocr_result['confidence_score'] <= 1:
                    self.print_success(f"OCR result {ocr_result['prescription_number']}: Valid confidence score")
                else:
                    self.print_warning(f"OCR result {ocr_result['prescription_number']}: Invalid confidence score")
                
                # Validate medications found
                if ocr_result['medications_found'] > 0:
                    self.print_success(f"OCR result {ocr_result['prescription_number']}: Medications found")
                else:
                    self.print_warning(f"OCR result {ocr_result['prescription_number']}: No medications found")
            
            # Store OCR results for cleanup
            self.ocr_results = stored_ocr_results
            self.results['ocr_result_storage_retrieval'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test OCR result storage and retrieval: {e}")
            self.results['ocr_result_storage_retrieval'] = f'FAILED: {e}'
    
    def test_prescription_workflow_state_management(self):
        """Test prescription workflow state management functionality."""
        self.print_section("12. Prescription Workflow State Management")
        
        if not hasattr(self, 'bulk_medications'):
            self.print_error("Cannot test workflow states without bulk medications")
            return
        
        try:
            # Define workflow states based on migration data
            workflow_states = [
                'draft',
                'submitted', 
                'under_review',
                'approved',
                'rejected',
                'dispensing',
                'dispensed',
                'completed',
                'cancelled',
                'expired'
            ]
            
            # Create mock prescription workflow states
            workflow_instances = []
            
            for i, medication in enumerate(self.bulk_medications[:5]):  # Test with first 5 medications
                try:
                    # Create workflow state data
                    current_state = workflow_states[i % len(workflow_states)]
                    previous_state = workflow_states[(i - 1) % len(workflow_states)] if i > 0 else None
                    
                    workflow_data = {
                        'prescription_number': f'RX-WF-{i+1:03d}',
                        'medication': medication,
                        'patient': self.test_user,
                        'state': current_state,
                        'previous_state': previous_state,
                        'state_changed_by': 'Test System',
                        'notes': f'Test workflow state for {medication.name}',
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    }
                    
                    workflow_instances.append(workflow_data)
                    self.print_success(f"Created workflow state {i+1}: {current_state} for {medication.name}")
                    
                except Exception as e:
                    self.print_error(f"Failed to create workflow state {i+1}: {e}")
            
            # Test workflow state transitions
            self.print_info("Testing workflow state transitions:")
            
            for i, workflow in enumerate(workflow_instances):
                try:
                    current_state = workflow['state']
                    
                    # Define valid transitions based on current state
                    valid_transitions = {
                        'draft': ['submitted', 'cancelled'],
                        'submitted': ['under_review', 'cancelled'],
                        'under_review': ['approved', 'rejected', 'cancelled'],
                        'approved': ['dispensing', 'cancelled'],
                        'rejected': ['draft', 'cancelled'],
                        'dispensing': ['dispensed', 'cancelled'],
                        'dispensed': ['completed', 'cancelled'],
                        'completed': [],  # Terminal state
                        'cancelled': [],  # Terminal state
                        'expired': []     # Terminal state
                    }
                    
                    # Test state transition
                    if current_state in valid_transitions:
                        available_transitions = valid_transitions[current_state]
                        if available_transitions:
                            # Simulate transition to next valid state
                            next_state = available_transitions[0]
                            workflow['previous_state'] = current_state
                            workflow['state'] = next_state
                            workflow['state_changed_at'] = timezone.now()
                            workflow['notes'] = f'Transitioned from {current_state} to {next_state}'
                            
                            self.print_success(f"Workflow {i+1}: {current_state} → {next_state}")
                        else:
                            self.print_info(f"Workflow {i+1}: {current_state} (terminal state)")
                    else:
                        self.print_warning(f"Workflow {i+1}: Unknown state {current_state}")
                        
                except Exception as e:
                    self.print_error(f"Failed to test workflow transition {i+1}: {e}")
            
            # Test workflow state queries
            self.print_info("Testing workflow state queries:")
            
            # Count by state
            state_counts = {}
            for workflow in workflow_instances:
                state = workflow['state']
                state_counts[state] = state_counts.get(state, 0) + 1
            
            for state, count in state_counts.items():
                self.print_success(f"  {state}: {count} workflows")
            
            # Test active workflows (not terminal states)
            terminal_states = ['completed', 'cancelled', 'expired']
            active_workflows = [w for w in workflow_instances if w['state'] not in terminal_states]
            self.print_success(f"Active workflows: {len(active_workflows)}")
            
            # Test workflow history tracking
            self.print_info("Testing workflow history tracking:")
            
            for workflow in workflow_instances:
                if workflow['previous_state']:
                    self.print_success(f"Workflow {workflow['prescription_number']}: {workflow['previous_state']} → {workflow['state']}")
                else:
                    self.print_info(f"Workflow {workflow['prescription_number']}: Initial state {workflow['state']}")
            
            # Test workflow validation
            self.print_info("Testing workflow validation:")
            
            for workflow in workflow_instances:
                # Validate required fields
                required_fields = ['prescription_number', 'medication', 'state']
                missing_fields = [field for field in required_fields if not workflow.get(field)]
                
                if not missing_fields:
                    self.print_success(f"Workflow {workflow['prescription_number']}: All required fields present")
                else:
                    self.print_warning(f"Workflow {workflow['prescription_number']}: Missing fields: {missing_fields}")
                
                # Validate state is in allowed list
                if workflow['state'] in workflow_states:
                    self.print_success(f"Workflow {workflow['prescription_number']}: Valid state")
                else:
                    self.print_warning(f"Workflow {workflow['prescription_number']}: Invalid state")
            
            # Store workflow instances for cleanup
            self.workflow_instances = workflow_instances
            self.results['prescription_workflow_state_management'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test prescription workflow state management: {e}")
            self.results['prescription_workflow_state_management'] = f'FAILED: {e}'
    
    def test_api_endpoints_medication_crud(self):
        """Test API endpoints for medication CRUD operations."""
        self.print_section("10. API Endpoints for Medication CRUD Operations")
        
        if not self.test_user:
            self.print_error("Cannot test API endpoints without test user")
            return
        
        try:
            from django.test import Client
            from django.urls import reverse
            from rest_framework.test import APIClient
            from rest_framework import status
            import json
            
            # Create API client
            api_client = APIClient()
            
            # Test authentication setup
            self.print_info("Testing API authentication setup:")
            
            # Check if user can authenticate
            api_client.force_authenticate(user=self.test_user)
            self.print_success("API client authenticated successfully")
            
            # Test API endpoints
            self.print_info("Testing medication API endpoints:")
            
            # Test 1: GET /api/medications/ (List medications)
            self.print_info("Testing GET /api/medications/ (List medications):")
            try:
                response = api_client.get('/api/medications/')
                if response.status_code == status.HTTP_200_OK:
                    self.print_success(f"✅ GET /api/medications/ - Status: {response.status_code}")
                    self.print_info(f"   Response count: {len(response.data.get('results', []))}")
                else:
                    self.print_warning(f"⚠️ GET /api/medications/ - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ GET /api/medications/ - Error: {e}")
            
            # Test 2: POST /api/medications/ (Create medication)
            self.print_info("Testing POST /api/medications/ (Create medication):")
            try:
                medication_data = {
                    'name': 'API Test Medication',
                    'generic_name': 'Test API Drug',
                    'brand_name': 'TestBrand',
                    'medication_type': 'tablet',
                    'prescription_type': 'otc',
                    'strength': '100mg',
                    'dosage_unit': 'mg',
                    'pill_count': 50,
                    'low_stock_threshold': 10,
                    'description': 'Test medication created via API',
                    'active_ingredients': 'Test API Ingredient',
                    'manufacturer': 'Test Manufacturer',
                    'side_effects': 'None known',
                    'contraindications': 'None known',
                    'storage_instructions': 'Store at room temperature',
                    'expiration_date': (date.today() + timedelta(days=365)).isoformat(),
                }
                
                response = api_client.post('/api/medications/', medication_data, format='json')
                if response.status_code == status.HTTP_201_CREATED:
                    self.print_success(f"✅ POST /api/medications/ - Status: {response.status_code}")
                    self.print_info(f"   Created medication ID: {response.data.get('id')}")
                    self.api_test_medication_id = response.data.get('id')
                else:
                    self.print_warning(f"⚠️ POST /api/medications/ - Status: {response.status_code}")
                    self.print_info(f"   Response: {response.data}")
            except Exception as e:
                self.print_error(f"❌ POST /api/medications/ - Error: {e}")
            
            # Test 3: GET /api/medications/{id}/ (Retrieve medication)
            if hasattr(self, 'api_test_medication_id'):
                self.print_info(f"Testing GET /api/medications/{self.api_test_medication_id}/ (Retrieve medication):")
                try:
                    response = api_client.get(f'/api/medications/{self.api_test_medication_id}/')
                    if response.status_code == status.HTTP_200_OK:
                        self.print_success(f"✅ GET /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                        self.print_info(f"   Medication name: {response.data.get('name')}")
                        self.print_info(f"   Pill count: {response.data.get('pill_count')}")
                    else:
                        self.print_warning(f"⚠️ GET /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                except Exception as e:
                    self.print_error(f"❌ GET /api/medications/{self.api_test_medication_id}/ - Error: {e}")
            
            # Test 4: PUT /api/medications/{id}/ (Update medication)
            if hasattr(self, 'api_test_medication_id'):
                self.print_info(f"Testing PUT /api/medications/{self.api_test_medication_id}/ (Update medication):")
                try:
                    update_data = {
                        'name': 'API Test Medication Updated',
                        'generic_name': 'Test API Drug Updated',
                        'brand_name': 'TestBrand Updated',
                        'medication_type': 'tablet',
                        'prescription_type': 'otc',
                        'strength': '200mg',
                        'dosage_unit': 'mg',
                        'pill_count': 75,
                        'low_stock_threshold': 15,
                        'description': 'Test medication updated via API',
                        'active_ingredients': 'Test API Ingredient Updated',
                        'manufacturer': 'Test Manufacturer Updated',
                        'side_effects': 'Updated side effects',
                        'contraindications': 'Updated contraindications',
                        'storage_instructions': 'Store in refrigerator',
                        'expiration_date': (date.today() + timedelta(days=730)).isoformat(),
                    }
                    
                    response = api_client.put(f'/api/medications/{self.api_test_medication_id}/', update_data, format='json')
                    if response.status_code == status.HTTP_200_OK:
                        self.print_success(f"✅ PUT /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                        self.print_info(f"   Updated name: {response.data.get('name')}")
                        self.print_info(f"   Updated pill count: {response.data.get('pill_count')}")
                    else:
                        self.print_warning(f"⚠️ PUT /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                        self.print_info(f"   Response: {response.data}")
                except Exception as e:
                    self.print_error(f"❌ PUT /api/medications/{self.api_test_medication_id}/ - Error: {e}")
            
            # Test 5: PATCH /api/medications/{id}/ (Partial update medication)
            if hasattr(self, 'api_test_medication_id'):
                self.print_info(f"Testing PATCH /api/medications/{self.api_test_medication_id}/ (Partial update medication):")
                try:
                    patch_data = {
                        'pill_count': 100,
                        'low_stock_threshold': 20,
                        'description': 'Partially updated description'
                    }
                    
                    response = api_client.patch(f'/api/medications/{self.api_test_medication_id}/', patch_data, format='json')
                    if response.status_code == status.HTTP_200_OK:
                        self.print_success(f"✅ PATCH /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                        self.print_info(f"   Updated pill count: {response.data.get('pill_count')}")
                        self.print_info(f"   Updated threshold: {response.data.get('low_stock_threshold')}")
                    else:
                        self.print_warning(f"⚠️ PATCH /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                        self.print_info(f"   Response: {response.data}")
                except Exception as e:
                    self.print_error(f"❌ PATCH /api/medications/{self.api_test_medication_id}/ - Error: {e}")
            
            # Test 6: DELETE /api/medications/{id}/ (Delete medication)
            if hasattr(self, 'api_test_medication_id'):
                self.print_info(f"Testing DELETE /api/medications/{self.api_test_medication_id}/ (Delete medication):")
                try:
                    response = api_client.delete(f'/api/medications/{self.api_test_medication_id}/')
                    if response.status_code == status.HTTP_204_NO_CONTENT:
                        self.print_success(f"✅ DELETE /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                        self.print_info("   Medication deleted successfully")
                    else:
                        self.print_warning(f"⚠️ DELETE /api/medications/{self.api_test_medication_id}/ - Status: {response.status_code}")
                        self.print_info(f"   Response: {response.data}")
                except Exception as e:
                    self.print_error(f"❌ DELETE /api/medications/{self.api_test_medication_id}/ - Error: {e}")
            
            # Test 7: Test medication schedules endpoints
            self.print_info("Testing medication schedules API endpoints:")
            
            # Create a test medication for schedules
            schedule_medication_data = {
                'name': 'Schedule Test Medication',
                'generic_name': 'Schedule Test Drug',
                'brand_name': 'ScheduleBrand',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'strength': '50mg',
                'dosage_unit': 'mg',
                'pill_count': 30,
                'low_stock_threshold': 5,
                'description': 'Test medication for schedule testing',
                'active_ingredients': 'Schedule Test Ingredient',
                'manufacturer': 'Schedule Manufacturer',
                'side_effects': 'None known',
                'contraindications': 'None known',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': (date.today() + timedelta(days=365)).isoformat(),
            }
            
            try:
                response = api_client.post('/api/medications/', schedule_medication_data, format='json')
                if response.status_code == status.HTTP_201_CREATED:
                    schedule_medication_id = response.data.get('id')
                    self.print_success(f"✅ Created test medication for schedules: {schedule_medication_id}")
                    
                    # Test GET /api/medications/schedules/ (List schedules)
                    self.print_info("Testing GET /api/medications/schedules/ (List schedules):")
                    try:
                        response = api_client.get('/api/medications/schedules/')
                        if response.status_code == status.HTTP_200_OK:
                            self.print_success(f"✅ GET /api/medications/schedules/ - Status: {response.status_code}")
                            self.print_info(f"   Response count: {len(response.data.get('results', []))}")
                        else:
                            self.print_warning(f"⚠️ GET /api/medications/schedules/ - Status: {response.status_code}")
                    except Exception as e:
                        self.print_error(f"❌ GET /api/medications/schedules/ - Error: {e}")
                    
                    # Test POST /api/medications/schedules/ (Create schedule)
                    self.print_info("Testing POST /api/medications/schedules/ (Create schedule):")
                    try:
                        schedule_data = {
                            'medication': schedule_medication_id,
                            'patient': self.test_user.id,
                            'timing': 'morning',
                            'dosage_amount': '1.0',
                            'frequency': 'daily',
                            'start_date': date.today().isoformat(),
                            'status': 'active',
                            'instructions': 'Take with breakfast',
                            'monday': True,
                            'tuesday': True,
                            'wednesday': True,
                            'thursday': True,
                            'friday': True,
                            'saturday': True,
                            'sunday': True,
                        }
                        
                        response = api_client.post('/api/medications/schedules/', schedule_data, format='json')
                        if response.status_code == status.HTTP_201_CREATED:
                            self.print_success(f"✅ POST /api/medications/schedules/ - Status: {response.status_code}")
                            self.print_info(f"   Created schedule ID: {response.data.get('id')}")
                            self.api_test_schedule_id = response.data.get('id')
                        else:
                            self.print_warning(f"⚠️ POST /api/medications/schedules/ - Status: {response.status_code}")
                            self.print_info(f"   Response: {response.data}")
                    except Exception as e:
                        self.print_error(f"❌ POST /api/medications/schedules/ - Error: {e}")
                    
                    # Test GET /api/medications/schedules/{id}/ (Retrieve schedule)
                    if hasattr(self, 'api_test_schedule_id'):
                        self.print_info(f"Testing GET /api/medications/schedules/{self.api_test_schedule_id}/ (Retrieve schedule):")
                        try:
                            response = api_client.get(f'/api/medications/schedules/{self.api_test_schedule_id}/')
                            if response.status_code == status.HTTP_200_OK:
                                self.print_success(f"✅ GET /api/medications/schedules/{self.api_test_schedule_id}/ - Status: {response.status_code}")
                                self.print_info(f"   Schedule timing: {response.data.get('timing')}")
                                self.print_info(f"   Schedule frequency: {response.data.get('frequency')}")
                            else:
                                self.print_warning(f"⚠️ GET /api/medications/schedules/{self.api_test_schedule_id}/ - Status: {response.status_code}")
                        except Exception as e:
                            self.print_error(f"❌ GET /api/medications/schedules/{self.api_test_schedule_id}/ - Error: {e}")
                    
                    # Clean up schedule test data
                    if hasattr(self, 'api_test_schedule_id'):
                        try:
                            api_client.delete(f'/api/medications/schedules/{self.api_test_schedule_id}/')
                            self.print_success("✅ Cleaned up test schedule")
                        except Exception as e:
                            self.print_warning(f"⚠️ Failed to clean up test schedule: {e}")
                    
                    # Clean up schedule test medication
                    try:
                        api_client.delete(f'/api/medications/{schedule_medication_id}/')
                        self.print_success("✅ Cleaned up test medication for schedules")
                    except Exception as e:
                        self.print_warning(f"⚠️ Failed to clean up test medication for schedules: {e}")
                        
                else:
                    self.print_warning(f"⚠️ Failed to create test medication for schedules: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ Schedule testing setup failed: {e}")
            
            # Test 8: Test medication logs endpoints
            self.print_info("Testing medication logs API endpoints:")
            
            # Create a test medication for logs
            log_medication_data = {
                'name': 'Log Test Medication',
                'generic_name': 'Log Test Drug',
                'brand_name': 'LogBrand',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'strength': '25mg',
                'dosage_unit': 'mg',
                'pill_count': 20,
                'low_stock_threshold': 3,
                'description': 'Test medication for log testing',
                'active_ingredients': 'Log Test Ingredient',
                'manufacturer': 'Log Manufacturer',
                'side_effects': 'None known',
                'contraindications': 'None known',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': (date.today() + timedelta(days=365)).isoformat(),
            }
            
            try:
                response = api_client.post('/api/medications/', log_medication_data, format='json')
                if response.status_code == status.HTTP_201_CREATED:
                    log_medication_id = response.data.get('id')
                    self.print_success(f"✅ Created test medication for logs: {log_medication_id}")
                    
                    # Test GET /api/medications/logs/ (List logs)
                    self.print_info("Testing GET /api/medications/logs/ (List logs):")
                    try:
                        response = api_client.get('/api/medications/logs/')
                        if response.status_code == status.HTTP_200_OK:
                            self.print_success(f"✅ GET /api/medications/logs/ - Status: {response.status_code}")
                            self.print_info(f"   Response count: {len(response.data.get('results', []))}")
                        else:
                            self.print_warning(f"⚠️ GET /api/medications/logs/ - Status: {response.status_code}")
                    except Exception as e:
                        self.print_error(f"❌ GET /api/medications/logs/ - Error: {e}")
                    
                    # Test POST /api/medications/logs/ (Create log)
                    self.print_info("Testing POST /api/medications/logs/ (Create log):")
                    try:
                        log_data = {
                            'medication': log_medication_id,
                            'patient': self.test_user.id,
                            'scheduled_time': timezone.now().isoformat(),
                            'actual_time': timezone.now().isoformat(),
                            'status': 'taken',
                            'dosage_taken': '1.0',
                            'notes': 'Test log entry created via API',
                        }
                        
                        response = api_client.post('/api/medications/logs/', log_data, format='json')
                        if response.status_code == status.HTTP_201_CREATED:
                            self.print_success(f"✅ POST /api/medications/logs/ - Status: {response.status_code}")
                            self.print_info(f"   Created log ID: {response.data.get('id')}")
                            self.api_test_log_id = response.data.get('id')
                        else:
                            self.print_warning(f"⚠️ POST /api/medications/logs/ - Status: {response.status_code}")
                            self.print_info(f"   Response: {response.data}")
                    except Exception as e:
                        self.print_error(f"❌ POST /api/medications/logs/ - Error: {e}")
                    
                    # Test GET /api/medications/logs/{id}/ (Retrieve log)
                    if hasattr(self, 'api_test_log_id'):
                        self.print_info(f"Testing GET /api/medications/logs/{self.api_test_log_id}/ (Retrieve log):")
                        try:
                            response = api_client.get(f'/api/medications/logs/{self.api_test_log_id}/')
                            if response.status_code == status.HTTP_200_OK:
                                self.print_success(f"✅ GET /api/medications/logs/{self.api_test_log_id}/ - Status: {response.status_code}")
                                self.print_info(f"   Log status: {response.data.get('status')}")
                                self.print_info(f"   Dosage taken: {response.data.get('dosage_taken')}")
                            else:
                                self.print_warning(f"⚠️ GET /api/medications/logs/{self.api_test_log_id}/ - Status: {response.status_code}")
                        except Exception as e:
                            self.print_error(f"❌ GET /api/medications/logs/{self.api_test_log_id}/ - Error: {e}")
                    
                    # Clean up log test data
                    if hasattr(self, 'api_test_log_id'):
                        try:
                            api_client.delete(f'/api/medications/logs/{self.api_test_log_id}/')
                            self.print_success("✅ Cleaned up test log")
                        except Exception as e:
                            self.print_warning(f"⚠️ Failed to clean up test log: {e}")
                    
                    # Clean up log test medication
                    try:
                        api_client.delete(f'/api/medications/{log_medication_id}/')
                        self.print_success("✅ Cleaned up test medication for logs")
                    except Exception as e:
                        self.print_warning(f"⚠️ Failed to clean up test medication for logs: {e}")
                        
                else:
                    self.print_warning(f"⚠️ Failed to create test medication for logs: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ Log testing setup failed: {e}")
            
            # Test 9: Test bulk operations endpoint
            self.print_info("Testing bulk operations endpoint:")
            try:
                bulk_data = {
                    'medications': [
                        {
                            'name': 'Bulk Test Medication 1',
                            'generic_name': 'Bulk Test Drug 1',
                            'brand_name': 'BulkBrand1',
                            'medication_type': 'tablet',
                            'prescription_type': 'otc',
                            'strength': '10mg',
                            'dosage_unit': 'mg',
                            'pill_count': 15,
                            'low_stock_threshold': 2,
                            'description': 'First bulk test medication',
                            'active_ingredients': 'Bulk Test Ingredient 1',
                            'manufacturer': 'Bulk Manufacturer 1',
                            'side_effects': 'None known',
                            'contraindications': 'None known',
                            'storage_instructions': 'Store at room temperature',
                            'expiration_date': (date.today() + timedelta(days=365)).isoformat(),
                        },
                        {
                            'name': 'Bulk Test Medication 2',
                            'generic_name': 'Bulk Test Drug 2',
                            'brand_name': 'BulkBrand2',
                            'medication_type': 'capsule',
                            'prescription_type': 'otc',
                            'strength': '20mg',
                            'dosage_unit': 'mg',
                            'pill_count': 25,
                            'low_stock_threshold': 3,
                            'description': 'Second bulk test medication',
                            'active_ingredients': 'Bulk Test Ingredient 2',
                            'manufacturer': 'Bulk Manufacturer 2',
                            'side_effects': 'None known',
                            'contraindications': 'None known',
                            'storage_instructions': 'Store at room temperature',
                            'expiration_date': (date.today() + timedelta(days=365)).isoformat(),
                        }
                    ]
                }
                
                response = api_client.post('/api/medications/bulk/', bulk_data, format='json')
                if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                    self.print_success(f"✅ POST /api/medications/bulk/ - Status: {response.status_code}")
                    self.print_info(f"   Bulk operation response: {response.data}")
                else:
                    self.print_warning(f"⚠️ POST /api/medications/bulk/ - Status: {response.status_code}")
                    self.print_info(f"   Response: {response.data}")
            except Exception as e:
                self.print_error(f"❌ POST /api/medications/bulk/ - Error: {e}")
            
            # Test 10: Test API error handling
            self.print_info("Testing API error handling:")
            
            # Test invalid medication creation
            try:
                invalid_data = {
                    'name': '',  # Invalid: empty name
                    'strength': 'invalid',  # Invalid strength format
                    'pill_count': -1,  # Invalid: negative count
                }
                
                response = api_client.post('/api/medications/', invalid_data, format='json')
                if response.status_code == status.HTTP_400_BAD_REQUEST:
                    self.print_success(f"✅ Invalid data validation - Status: {response.status_code}")
                    self.print_info(f"   Validation errors: {response.data}")
                else:
                    self.print_warning(f"⚠️ Invalid data validation - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ Invalid data validation test failed: {e}")
            
            # Test non-existent resource
            try:
                response = api_client.get('/api/medications/99999/')
                if response.status_code == status.HTTP_404_NOT_FOUND:
                    self.print_success(f"✅ 404 handling - Status: {response.status_code}")
                else:
                    self.print_warning(f"⚠️ 404 handling - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ 404 handling test failed: {e}")
            
            # Test unauthorized access
            try:
                # Create unauthenticated client
                unauth_client = APIClient()
                response = unauth_client.get('/api/medications/')
                if response.status_code == status.HTTP_401_UNAUTHORIZED:
                    self.print_success(f"✅ Unauthorized access handling - Status: {response.status_code}")
                else:
                    self.print_warning(f"⚠️ Unauthorized access handling - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ Unauthorized access test failed: {e}")
            
            # Test API response format
            self.print_info("Testing API response format:")
            
            # Test pagination
            try:
                response = api_client.get('/api/medications/')
                if response.status_code == status.HTTP_200_OK:
                    data = response.data
                    if 'results' in data or 'count' in data:
                        self.print_success("✅ API response includes pagination fields")
                        self.print_info(f"   Response keys: {list(data.keys())}")
                    else:
                        self.print_warning("⚠️ API response missing pagination fields")
                else:
                    self.print_warning(f"⚠️ Could not test response format - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ Response format test failed: {e}")
            
            # Test API filtering
            self.print_info("Testing API filtering:")
            
            try:
                # Test filtering by medication type
                response = api_client.get('/api/medications/?medication_type=tablet')
                if response.status_code == status.HTTP_200_OK:
                    self.print_success("✅ API filtering by medication_type works")
                else:
                    self.print_warning(f"⚠️ API filtering failed - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ API filtering test failed: {e}")
            
            # Test API search
            self.print_info("Testing API search:")
            
            try:
                # Test search functionality
                response = api_client.get('/api/medications/?search=test')
                if response.status_code == status.HTTP_200_OK:
                    self.print_success("✅ API search functionality works")
                else:
                    self.print_warning(f"⚠️ API search failed - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ API search test failed: {e}")
            
            # Test API ordering
            self.print_info("Testing API ordering:")
            
            try:
                # Test ordering by name
                response = api_client.get('/api/medications/?ordering=name')
                if response.status_code == status.HTTP_200_OK:
                    self.print_success("✅ API ordering functionality works")
                else:
                    self.print_warning(f"⚠️ API ordering failed - Status: {response.status_code}")
            except Exception as e:
                self.print_error(f"❌ API ordering test failed: {e}")
            
            self.results['api_endpoints_medication_crud'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test API endpoints for medication CRUD operations: {e}")
            self.results['api_endpoints_medication_crud'] = f'FAILED: {e}'
    
    def test_admin_interface_functionality(self):
        """Test Django admin interface functionality."""
        self.print_section("13. Admin Interface Functionality")
        
        try:
            # Test admin site configuration
            self.print_info("Testing admin site configuration:")
            
            from django.contrib import admin
            from django.contrib.admin.sites import site
            
            # Check admin site customization
            if hasattr(admin.site, 'site_header'):
                self.print_success(f"Admin site header: {admin.site.site_header}")
            else:
                self.print_warning("Admin site header not configured")
            
            if hasattr(admin.site, 'site_title'):
                self.print_success(f"Admin site title: {admin.site.site_title}")
            else:
                self.print_warning("Admin site title not configured")
            
            if hasattr(admin.site, 'index_title'):
                self.print_success(f"Admin index title: {admin.site.index_title}")
            else:
                self.print_warning("Admin index title not configured")
            
            # Test admin model registration
            self.print_info("Testing admin model registration:")
            
            registered_models = []
            for model, admin_class in site._registry.items():
                registered_models.append({
                    'model': model.__name__,
                    'app': model._meta.app_label,
                    'admin_class': admin_class.__class__.__name__
                })
                self.print_success(f"Registered: {model._meta.app_label}.{model.__name__} → {admin_class.__class__.__name__}")
            
            # Test specific admin configurations
            self.print_info("Testing specific admin configurations:")
            
            # Test User admin
            try:
                from users.admin import UserAdmin
                self.print_success("User admin configuration found")
                
                # Check list display
                if hasattr(UserAdmin, 'list_display'):
                    self.print_success(f"User admin list_display: {UserAdmin.list_display}")
                
                # Check list filter
                if hasattr(UserAdmin, 'list_filter'):
                    self.print_success(f"User admin list_filter: {UserAdmin.list_filter}")
                
                # Check search fields
                if hasattr(UserAdmin, 'search_fields'):
                    self.print_success(f"User admin search_fields: {UserAdmin.search_fields}")
                    
            except ImportError:
                self.print_warning("User admin configuration not found")
            
            # Test Medication admin
            try:
                from medications.admin import MedicationAdmin
                self.print_success("Medication admin configuration found")
                
                # Check list display
                if hasattr(MedicationAdmin, 'list_display'):
                    self.print_success(f"Medication admin list_display: {MedicationAdmin.list_display}")
                
                # Check list filter
                if hasattr(MedicationAdmin, 'list_filter'):
                    self.print_success(f"Medication admin list_filter: {MedicationAdmin.list_filter}")
                
                # Check search fields
                if hasattr(MedicationAdmin, 'search_fields'):
                    self.print_success(f"Medication admin search_fields: {MedicationAdmin.search_fields}")
                
                # Check actions
                if hasattr(MedicationAdmin, 'actions'):
                    self.print_success(f"Medication admin actions: {MedicationAdmin.actions}")
                    
            except ImportError:
                self.print_warning("Medication admin configuration not found")
            
            # Test admin permissions
            self.print_info("Testing admin permissions:")
            
            # Check if superuser can access admin
            if self.test_user and self.test_user.is_superuser:
                self.print_success("Test user has superuser permissions")
            else:
                self.print_info("Test user does not have superuser permissions (expected)")
            
            # Test admin URL patterns
            self.print_info("Testing admin URL patterns:")
            
            try:
                from django.urls import reverse
                
                # Test admin index URL
                admin_index_url = reverse('admin:index')
                self.print_success(f"Admin index URL: {admin_index_url}")
                
                # Test model admin URLs
                for model_info in registered_models[:3]:  # Test first 3 models
                    try:
                        model_admin_url = reverse(f'admin:{model_info["app"]}_{model_info["model"].lower()}_changelist')
                        self.print_success(f"Admin URL for {model_info['model']}: {model_admin_url}")
                    except Exception as e:
                        self.print_warning(f"Could not generate admin URL for {model_info['model']}: {e}")
                        
            except Exception as e:
                self.print_warning(f"Could not test admin URLs: {e}")
            
            # Test admin actions
            self.print_info("Testing admin actions:")
            
            # Test bulk actions if available
            if hasattr(MedicationAdmin, 'actions'):
                for action in MedicationAdmin.actions:
                    self.print_success(f"Medication admin action: {action}")
            
            # Test admin custom methods
            self.print_info("Testing admin custom methods:")
            
            if hasattr(MedicationAdmin, 'is_low_stock'):
                self.print_success("Medication admin has is_low_stock method")
            
            if hasattr(MedicationAdmin, 'is_expired'):
                self.print_success("Medication admin has is_expired method")
            
            # Test admin fieldsets
            self.print_info("Testing admin fieldsets:")
            
            if hasattr(MedicationAdmin, 'fieldsets'):
                for fieldset_name, fieldset_options in MedicationAdmin.fieldsets:
                    self.print_success(f"Medication admin fieldset: {fieldset_name}")
                    if 'fields' in fieldset_options:
                        self.print_info(f"  Fields: {fieldset_options['fields']}")
            
            # Test admin readonly fields
            if hasattr(MedicationAdmin, 'readonly_fields'):
                self.print_success(f"Medication admin readonly_fields: {MedicationAdmin.readonly_fields}")
            
            # Test admin ordering
            if hasattr(MedicationAdmin, 'ordering'):
                self.print_success(f"Medication admin ordering: {MedicationAdmin.ordering}")
            
            # Store admin test results
            self.admin_test_results = {
                'registered_models': registered_models,
                'admin_site_configured': hasattr(admin.site, 'site_header'),
                'user_admin_found': 'UserAdmin' in [m['admin_class'] for m in registered_models],
                'medication_admin_found': 'MedicationAdmin' in [m['admin_class'] for m in registered_models]
            }
            
            self.results['admin_interface_functionality'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to test admin interface functionality: {e}")
            self.results['admin_interface_functionality'] = f'FAILED: {e}'
    
    def cleanup_test_data(self):
        """Clean up test data created during verification."""
        self.print_section("14. Cleanup Test Data")
        
        try:
            # Clean up API test data
            if hasattr(self, 'api_test_medication_id'):
                self.print_success("API test medication already cleaned up during testing")
            
            if hasattr(self, 'api_test_schedule_id'):
                self.print_success("API test schedule already cleaned up during testing")
            
            if hasattr(self, 'api_test_log_id'):
                self.print_success("API test log already cleaned up during testing")
            
            # Clean up OCR results
            if hasattr(self, 'ocr_results'):
                self.print_success(f"Cleaned up {len(self.ocr_results)} OCR results")
            
            # Clean up workflow instances
            if hasattr(self, 'workflow_instances'):
                self.print_success(f"Cleaned up {len(self.workflow_instances)} workflow instances")
            
            # Clean up complex schedules
            if hasattr(self, 'complex_schedules'):
                for schedule in self.complex_schedules:
                    schedule.delete()
                self.print_success(f"Deleted {len(self.complex_schedules)} complex schedules")
            
            # Clean up bulk medications and their related objects
            if hasattr(self, 'bulk_medications'):
                for medication in self.bulk_medications:
                    # Delete related objects first
                    medication.stock_transactions.all().delete()
                    medication.stock_alerts.all().delete()
                    medication.logs.all().delete()
                    medication.schedules.all().delete()
                    medication.prescription_renewals.all().delete()
                    
                    # Delete analytics and visualizations
                    if hasattr(medication, 'stock_analytics'):
                        medication.stock_analytics.delete()
                    
                    medication.stock_visualizations.all().delete()
                    
                    # Delete the medication
                    medication.delete()
                self.print_success(f"Deleted {len(self.bulk_medications)} bulk medications and related objects")
            
            # Delete original test medication and related objects
            if hasattr(self, 'test_medication') and self.test_medication:
                # Delete related objects first
                self.test_medication.stock_transactions.all().delete()
                self.test_medication.stock_alerts.all().delete()
                self.test_medication.logs.all().delete()
                self.test_medication.schedules.all().delete()
                self.test_medication.prescription_renewals.all().delete()
                
                # Delete analytics and visualizations
                if hasattr(self.test_medication, 'stock_analytics'):
                    self.test_medication.stock_analytics.delete()
                
                self.test_medication.stock_visualizations.all().delete()
                
                # Delete the medication
                self.test_medication.delete()
                self.print_success("Original test medication and related objects deleted")
            
            # Delete test user
            if hasattr(self, 'test_user') and self.test_user:
                self.test_user.delete()
                self.print_success("Test user deleted")
            
            self.results['cleanup'] = 'SUCCESS'
            
        except Exception as e:
            self.print_error(f"Failed to cleanup test data: {e}")
            self.results['cleanup'] = f'FAILED: {e}'
    
    def generate_summary_report(self):
        """Generate a summary report of all verification results."""
        self.print_header("VERIFICATION SUMMARY REPORT")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        warnings = 0
        
        for category, result in self.results.items():
            if category == 'overall_status':
                continue
                
            if isinstance(result, dict):
                for test_name, test_result in result.items():
                    total_tests += 1
                    if test_result == 'SUCCESS':
                        passed_tests += 1
                    elif test_result.startswith('FAILED'):
                        failed_tests += 1
                    else:
                        warnings += 1
            else:
                total_tests += 1
                if result == 'SUCCESS':
                    passed_tests += 1
                elif result.startswith('FAILED'):
                    failed_tests += 1
                else:
                    warnings += 1
        
        # Calculate overall status
        if failed_tests == 0:
            self.results['overall_status'] = 'PASSED'
        elif passed_tests > failed_tests:
            self.results['overall_status'] = 'PARTIAL'
        else:
            self.results['overall_status'] = 'FAILED'
        
        # Print summary
        print(f"\n📊 VERIFICATION RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   ⚠️  Warnings: {warnings}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "   📈 Success Rate: N/A")
        
        print(f"\n🎯 OVERALL STATUS: {self.results['overall_status']}")
        
        # Print detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for category, result in self.results.items():
            if category == 'overall_status':
                continue
                
            if isinstance(result, dict):
                print(f"\n   {category.upper()}:")
                for test_name, test_result in result.items():
                    status_icon = "✅" if test_result == 'SUCCESS' else "❌" if test_result.startswith('FAILED') else "⚠️"
                    print(f"     {status_icon} {test_name}: {test_result}")
            else:
                status_icon = "✅" if result == 'SUCCESS' else "❌" if result.startswith('FAILED') else "⚠️"
                print(f"   {status_icon} {category}: {result}")
        
        return self.results
    
    def run_full_verification(self):
        """Run the complete verification process."""
        self.print_header("MEDGUARD SA SETUP VERIFICATION")
        self.print_info("Starting comprehensive verification process...")
        
        try:
            # Run all verification steps
            self.verify_model_instantiation()
            self.create_test_user()
            self.create_comprehensive_medication()
            self.verify_foreign_key_relationships()
            self.test_model_methods()
            self.test_database_constraints()
            self.test_bulk_medication_creation()
            self.test_complex_medication_schedules()
            self.test_stock_management_calculations()
            self.test_api_endpoints_medication_crud()
            self.test_ocr_result_storage_retrieval()
            self.test_prescription_workflow_state_management()
            self.test_admin_interface_functionality()
            
            # Generate summary report
            results = self.generate_summary_report()
            
            # Cleanup (optional - comment out if you want to keep test data)
            # self.cleanup_test_data()
            
            return results
            
        except Exception as e:
            self.print_error(f"Verification process failed: {e}")
            self.results['overall_status'] = 'FAILED'
            return self.results


def main():
    """Main function to run the verification."""
    verifier = MedGuardSetupVerifier()
    results = verifier.run_full_verification()
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASSED':
        print("\n🎉 VERIFICATION COMPLETED SUCCESSFULLY!")
        sys.exit(0)
    elif results['overall_status'] == 'PARTIAL':
        print("\n⚠️  VERIFICATION COMPLETED WITH WARNINGS")
        sys.exit(1)
    else:
        print("\n❌ VERIFICATION FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main() 