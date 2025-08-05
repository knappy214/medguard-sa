#!/usr/bin/env python3
"""
MedGuard SA Database Initialization Script

This script provides a comprehensive database setup for the MedGuard SA project:
1. Drops and recreates the database if needed (development only)
2. Runs all migrations in the correct order
3. Creates superuser account for admin access
4. Seeds the database with prescription medications
5. Creates sample patient data for testing
6. Initializes medication schedules and stock levels
7. Sets up OCR processing cache tables
8. Creates audit log entries for compliance
9. Initializes reporting and analytics tables
10. Verifies all data integrity constraints are met

Usage:
    python initialize_database.py [--drop-db] [--skip-seed] [--skip-patients]
"""

import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')

import django
django.setup()

from django.core.management import execute_from_command_line
from django.core.management.base import CommandError
from django.db import connection, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

# Import models
from medications.models import (
    Medication, MedicationSchedule, MedicationLog, StockTransaction,
    StockAlert, StockAnalytics, PharmacyIntegration, PrescriptionRenewal
)

User = get_user_model()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('database_initialization.log')
    ]
)
logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """Comprehensive database initialization for MedGuard SA."""
    
    def __init__(self, drop_db=False, skip_seed=False, skip_patients=False):
        self.drop_db = drop_db
        self.skip_seed = skip_seed
        self.skip_patients = skip_patients
        self.db_config = settings.DATABASES['default']
        
    def log_section(self, title):
        """Log a section header."""
        logger.info(f"\n{'='*60}")
        logger.info(f" {title}")
        logger.info(f"{'='*60}")
    
    def check_environment(self):
        """Check if we're in a safe environment for database operations."""
        self.log_section("ENVIRONMENT CHECK")
        
        # Check if we're in development
        if not settings.DEBUG:
            logger.warning("⚠️  Not in DEBUG mode. Database operations may be restricted.")
            if self.drop_db:
                logger.error("❌ Cannot drop database in production mode!")
                return False
        
        # Check database configuration
        logger.info(f"Database: {self.db_config['NAME']}")
        logger.info(f"Host: {self.db_config['HOST']}")
        logger.info(f"Port: {self.db_config['PORT']}")
        logger.info(f"User: {self.db_config['USER']}")
        
        return True
    
    def drop_and_recreate_database(self):
        """Drop and recreate the database (development only)."""
        if not self.drop_db:
            logger.info("Skipping database drop (use --drop-db to enable)")
            return True
            
        self.log_section("DATABASE DROP AND RECREATE")
        
        try:
            # Connect to postgres database to drop/recreate
            with connection.cursor() as cursor:
                # Terminate existing connections
                cursor.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{self.db_config['NAME']}'
                    AND pid <> pg_backend_pid();
                """)
                
                # Drop database if exists
                cursor.execute(f"DROP DATABASE IF EXISTS {self.db_config['NAME']};")
                logger.info(f"✅ Dropped database: {self.db_config['NAME']}")
                
                # Create new database
                cursor.execute(f"CREATE DATABASE {self.db_config['NAME']};")
                logger.info(f"✅ Created database: {self.db_config['NAME']}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to drop/recreate database: {e}")
            return False
    
    def run_migrations(self):
        """Run all Django migrations."""
        self.log_section("RUNNING MIGRATIONS")
        
        try:
            # Run makemigrations first
            logger.info("Running makemigrations...")
            execute_from_command_line(['manage.py', 'makemigrations'])
            
            # Run migrate
            logger.info("Running migrate...")
            execute_from_command_line(['manage.py', 'migrate'])
            
            logger.info("✅ Migrations completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
    
    def create_superuser(self):
        """Create a superuser account for admin access."""
        self.log_section("CREATING SUPERUSER")
        
        try:
            # Check if superuser already exists
            if User.objects.filter(is_superuser=True).exists():
                logger.info("✅ Superuser already exists")
                return True
            
            # Create superuser
            superuser_data = {
                'username': 'admin',
                'email': 'admin@medguard-sa.com',
                'password': 'admin123',
                'first_name': 'System',
                'last_name': 'Administrator',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
                'user_type': 'HEALTHCARE_PROVIDER',
                'preferred_language': 'en'
            }
            
            user = User.objects.create_user(**superuser_data)
            logger.info("✅ Superuser created successfully")
            logger.info(f"   Username: {superuser_data['username']}")
            logger.info(f"   Email: {superuser_data['email']}")
            logger.info(f"   Password: {superuser_data['password']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create superuser: {e}")
            return False
    
    def seed_medications(self):
        """Seed the database with prescription medications."""
        if self.skip_seed:
            logger.info("Skipping medication seeding (use --skip-seed to disable)")
            return True
            
        self.log_section("SEEDING MEDICATIONS")
        
        try:
            # Run the medication seeding command
            execute_from_command_line([
                'manage.py', 'seed_medications', 
                '--clear', 
                '--create-sample-schedules',
                '--create-sample-logs',
                '--create-sample-transactions'
            ])
            
            logger.info("✅ Medication seeding completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Medication seeding failed: {e}")
            return False
    
    def create_sample_patients(self):
        """Create sample patient data for testing."""
        if self.skip_patients:
            logger.info("Skipping patient creation (use --skip-patients to disable)")
            return True
            
        self.log_section("CREATING SAMPLE PATIENTS")
        
        try:
            with transaction.atomic():
                patients_created = 0
                
                # Sample patient data
                sample_patients = [
                    {
                        'username': 'john.doe',
                        'email': 'john.doe@example.com',
                        'password': 'patient123',
                        'first_name': 'John',
                        'last_name': 'Doe',
                        'user_type': 'PATIENT',
                        'phone': '+27123456789',
                        'date_of_birth': timezone.now().date() - timedelta(days=365*45),
                        'gender': 'male',
                        'address': '123 Main Street, Cape Town, Western Cape',
                        'city': 'Cape Town',
                        'province': 'Western Cape',
                        'postal_code': '8001',
                        'medical_record_number': 'MRN-00000001',
                        'primary_healthcare_provider': 'Dr. Sarah Johnson',
                        'emergency_contact_name': 'Jane Doe',
                        'emergency_contact_phone': '+27123456788',
                        'emergency_contact_relationship': 'Spouse',
                        'preferred_language': 'en',
                        'timezone': 'Africa/Johannesburg',
                        'email_notifications': True,
                        'sms_notifications': True,
                        'push_notifications': True
                    },
                    {
                        'username': 'maria.smith',
                        'email': 'maria.smith@example.com',
                        'password': 'patient123',
                        'first_name': 'Maria',
                        'last_name': 'Smith',
                        'user_type': 'PATIENT',
                        'phone': '+27123456790',
                        'date_of_birth': timezone.now().date() - timedelta(days=365*62),
                        'gender': 'female',
                        'address': '456 Oak Avenue, Johannesburg, Gauteng',
                        'city': 'Johannesburg',
                        'province': 'Gauteng',
                        'postal_code': '2000',
                        'medical_record_number': 'MRN-00000002',
                        'primary_healthcare_provider': 'Dr. Michael Brown',
                        'emergency_contact_name': 'Robert Smith',
                        'emergency_contact_phone': '+27123456791',
                        'emergency_contact_relationship': 'Son',
                        'preferred_language': 'en',
                        'timezone': 'Africa/Johannesburg',
                        'email_notifications': True,
                        'sms_notifications': False,
                        'push_notifications': True
                    },
                    {
                        'username': 'piet.van.der.merwe',
                        'email': 'piet.vandermerwe@example.com',
                        'password': 'patient123',
                        'first_name': 'Piet',
                        'last_name': 'van der Merwe',
                        'user_type': 'PATIENT',
                        'phone': '+27123456792',
                        'date_of_birth': timezone.now().date() - timedelta(days=365*38),
                        'gender': 'male',
                        'address': '789 Pine Street, Pretoria, Gauteng',
                        'city': 'Pretoria',
                        'province': 'Gauteng',
                        'postal_code': '0001',
                        'medical_record_number': 'MRN-00000003',
                        'primary_healthcare_provider': 'Dr. Anna van Wyk',
                        'emergency_contact_name': 'Sarie van der Merwe',
                        'emergency_contact_phone': '+27123456793',
                        'emergency_contact_relationship': 'Wife',
                        'preferred_language': 'af',
                        'timezone': 'Africa/Johannesburg',
                        'email_notifications': False,
                        'sms_notifications': True,
                        'push_notifications': True
                    }
                ]
                
                for patient_data in sample_patients:
                    # Check if patient already exists
                    if User.objects.filter(username=patient_data['username']).exists():
                        logger.info(f"Patient {patient_data['username']} already exists, skipping...")
                        continue
                    
                    # Create patient
                    user = User.objects.create_user(**patient_data)
                    patients_created += 1
                    logger.info(f"✅ Created patient: {user.get_full_name()} ({user.username})")
                
                # Create sample caregivers
                caregivers_created = 0
                sample_caregivers = [
                    {
                        'username': 'jane.caregiver',
                        'email': 'jane.caregiver@example.com',
                        'password': 'caregiver123',
                        'first_name': 'Jane',
                        'last_name': 'Caregiver',
                        'user_type': 'CAREGIVER',
                        'phone': '+27123456794',
                        'preferred_language': 'en',
                        'timezone': 'Africa/Johannesburg'
                    },
                    {
                        'username': 'koos.versorger',
                        'email': 'koos.versorger@example.com',
                        'password': 'caregiver123',
                        'first_name': 'Koos',
                        'last_name': 'Versorger',
                        'user_type': 'CAREGIVER',
                        'phone': '+27123456795',
                        'preferred_language': 'af',
                        'timezone': 'Africa/Johannesburg'
                    }
                ]
                
                for caregiver_data in sample_caregivers:
                    if User.objects.filter(username=caregiver_data['username']).exists():
                        logger.info(f"Caregiver {caregiver_data['username']} already exists, skipping...")
                        continue
                    
                    user = User.objects.create_user(**caregiver_data)
                    caregivers_created += 1
                    logger.info(f"✅ Created caregiver: {user.get_full_name()} ({user.username})")
                
                # Create sample healthcare providers
                providers_created = 0
                sample_providers = [
                    {
                        'username': 'dr.johnson',
                        'email': 'dr.johnson@medguard-sa.com',
                        'password': 'provider123',
                        'first_name': 'Sarah',
                        'last_name': 'Johnson',
                        'user_type': 'HEALTHCARE_PROVIDER',
                        'phone': '+27123456796',
                        'preferred_language': 'en',
                        'timezone': 'Africa/Johannesburg'
                    },
                    {
                        'username': 'dr.brown',
                        'email': 'dr.brown@medguard-sa.com',
                        'password': 'provider123',
                        'first_name': 'Michael',
                        'last_name': 'Brown',
                        'user_type': 'HEALTHCARE_PROVIDER',
                        'phone': '+27123456797',
                        'preferred_language': 'en',
                        'timezone': 'Africa/Johannesburg'
                    }
                ]
                
                for provider_data in sample_providers:
                    if User.objects.filter(username=provider_data['username']).exists():
                        logger.info(f"Provider {provider_data['username']} already exists, skipping...")
                        continue
                    
                    user = User.objects.create_user(**provider_data)
                    providers_created += 1
                    logger.info(f"✅ Created healthcare provider: {user.get_full_name()} ({user.username})")
                
                logger.info(f"✅ Created {patients_created} patients, {caregivers_created} caregivers, {providers_created} providers")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create sample patients: {e}")
            return False
    
    def create_sample_prescriptions(self):
        """Create sample prescription data for testing."""
        self.log_section("CREATING SAMPLE PRESCRIPTIONS")
        
        try:
            with transaction.atomic():
                prescriptions_created = 0
                
                # Get sample patients and medications
                patients = User.objects.filter(user_type='PATIENT')[:3]
                medications = Medication.objects.filter(prescription_type='prescription')[:5]
                
                if not patients.exists():
                    logger.warning("No patients found, skipping prescription creation")
                    return True
                
                if not medications.exists():
                    logger.warning("No prescription medications found, skipping prescription creation")
                    return True
                
                for patient in patients:
                    for medication in medications[:2]:  # 2 prescriptions per patient
                        # Create prescription renewal
                        prescription_data = {
                            'patient': patient,
                            'medication': medication,
                            'prescription_number': f'RX-{patient.id:04d}-{medication.id:04d}',
                            'prescribed_by': 'Dr. Sarah Johnson',
                            'prescribed_date': timezone.now().date() - timedelta(days=30),
                            'expiry_date': timezone.now().date() + timedelta(days=335),
                            'status': 'active',
                            'priority': 'medium',
                            'renewal_reminder_days': 14,
                            'notes': f'Prescription for {patient.get_full_name()} - {medication.name}'
                        }
                        
                        prescription, created = PrescriptionRenewal.objects.get_or_create(
                            patient=patient,
                            medication=medication,
                            defaults=prescription_data
                        )
                        
                        if created:
                            prescriptions_created += 1
                            logger.info(f"✅ Created prescription: {prescription.prescription_number}")
                
                logger.info(f"✅ Created {prescriptions_created} prescriptions")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create sample prescriptions: {e}")
            return False
    
    def initialize_medication_schedules_and_stock(self):
        """Initialize medication schedules and stock levels."""
        self.log_section("INITIALIZING MEDICATION SCHEDULES AND STOCK")
        
        try:
            with transaction.atomic():
                schedules_created = 0
                stock_alerts_created = 0
                
                # Get patients and medications
                patients = User.objects.filter(user_type='PATIENT')[:3]
                medications = Medication.objects.all()[:10]
                
                if not patients.exists():
                    logger.warning("No patients found, skipping schedule initialization")
                    return True
                
                if not medications.exists():
                    logger.warning("No medications found, skipping schedule initialization")
                    return True
                
                # Create medication schedules
                for patient in patients:
                    for medication in medications[:3]:  # 3 schedules per patient
                        # Create varied schedules
                        schedule_times = ['morning', 'noon', 'night']
                        schedule_time = schedule_times[schedules_created % 3]
                        
                        schedule_data = {
                            'patient': patient,
                            'medication': medication,
                            'timing': schedule_time,
                            'custom_time': None,
                            'dosage_amount': Decimal('1.0'),
                            'frequency': 'daily',
                            'start_date': timezone.now().date(),
                            'end_date': timezone.now().date() + timedelta(days=365),
                            'status': 'active',
                            'instructions': f'Take {medication.name} as prescribed by your doctor.',
                            'notes': f'Schedule created during initialization for {patient.get_full_name()}'
                        }
                        
                        # Set custom time for custom timing
                        if schedule_time == 'custom':
                            schedule_data['custom_time'] = timezone.now().time().replace(hour=14, minute=0, second=0, microsecond=0)
                        
                        schedule, created = MedicationSchedule.objects.get_or_create(
                            patient=patient,
                            medication=medication,
                            timing=schedule_time,
                            defaults=schedule_data
                        )
                        
                        if created:
                            schedules_created += 1
                            logger.info(f"✅ Created schedule: {patient.get_full_name()} - {medication.name} ({schedule_time})")
                
                # Initialize stock levels and create alerts
                for medication in medications:
                    # Update stock levels
                    current_stock = medication.pill_count
                    threshold = medication.low_stock_threshold
                    
                    # Create stock alert if below threshold
                    if current_stock <= threshold:
                        alert_data = {
                            'medication': medication,
                            'alert_type': 'low_stock',
                            'threshold': threshold,
                            'current_stock': current_stock,
                            'status': 'active',
                            'priority': 'high' if current_stock == 0 else 'medium',
                            'message': f'Low stock alert: {medication.name} has {current_stock} units remaining (threshold: {threshold})',
                            'created_at': timezone.now()
                        }
                        
                        alert, created = StockAlert.objects.get_or_create(
                            medication=medication,
                            alert_type='low_stock',
                            status='active',
                            defaults=alert_data
                        )
                        
                        if created:
                            stock_alerts_created += 1
                            logger.info(f"✅ Created stock alert: {medication.name} (stock: {current_stock})")
                
                logger.info(f"✅ Created {schedules_created} medication schedules")
                logger.info(f"✅ Created {stock_alerts_created} stock alerts")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize medication schedules and stock: {e}")
            return False
    
    def setup_ocr_processing_cache(self):
        """Set up OCR processing cache tables."""
        self.log_section("SETTING UP OCR PROCESSING CACHE")
        
        try:
            with transaction.atomic():
                # Create OCR cache table if it doesn't exist
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS ocr_processing_cache (
                            id SERIAL PRIMARY KEY,
                            image_hash VARCHAR(64) UNIQUE NOT NULL,
                            prescription_text TEXT,
                            extracted_data JSONB,
                            confidence_score DECIMAL(3,2),
                            processing_time_ms INTEGER,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """)
                    
                    # Create index for faster lookups
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_ocr_cache_image_hash 
                        ON ocr_processing_cache(image_hash);
                    """)
                    
                    # Create index for confidence scores
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_ocr_cache_confidence 
                        ON ocr_processing_cache(confidence_score);
                    """)
                    
                    # Create index for processing time
                    cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_ocr_cache_processing_time 
                        ON ocr_processing_cache(processing_time_ms);
                    """)
                    
                    logger.info("✅ OCR processing cache table created")
                    logger.info("✅ OCR cache indexes created")
                
                # Insert sample OCR cache entries
                sample_cache_entries = [
                    {
                        'image_hash': 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
                        'prescription_text': 'METFORMIN 500mg\nTake 1 tablet twice daily with meals\nDr. Sarah Johnson\nRefills: 3',
                        'extracted_data': {
                            'medication_name': 'METFORMIN',
                            'strength': '500mg',
                            'dosage': '1 tablet twice daily',
                            'prescriber': 'Dr. Sarah Johnson',
                            'refills': 3
                        },
                        'confidence_score': Decimal('0.95'),
                        'processing_time_ms': 1250
                    },
                    {
                        'image_hash': 'b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef12345678',
                        'prescription_text': 'LANTUS SoloStar Pen\nInject 20 units daily at bedtime\nDr. Michael Brown\nRefills: 2',
                        'extracted_data': {
                            'medication_name': 'LANTUS',
                            'strength': '100 units/ml',
                            'dosage': '20 units daily',
                            'prescriber': 'Dr. Michael Brown',
                            'refills': 2
                        },
                        'confidence_score': Decimal('0.92'),
                        'processing_time_ms': 980
                    }
                ]
                
                for entry in sample_cache_entries:
                    cursor.execute("""
                        INSERT INTO ocr_processing_cache 
                        (image_hash, prescription_text, extracted_data, confidence_score, processing_time_ms)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (image_hash) DO NOTHING;
                    """, (
                        entry['image_hash'],
                        entry['prescription_text'],
                        entry['extracted_data'],
                        entry['confidence_score'],
                        entry['processing_time_ms']
                    ))
                
                logger.info(f"✅ Inserted {len(sample_cache_entries)} sample OCR cache entries")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to setup OCR processing cache: {e}")
            return False
    
    def create_audit_log_entries(self):
        """Create audit log entries for compliance."""
        self.log_section("CREATING AUDIT LOG ENTRIES")
        
        try:
            with transaction.atomic():
                audit_entries_created = 0
                
                # Import security models
                from security.models import SecurityEvent, AuditLog
                
                # Create system initialization audit entry
                system_audit_data = {
                    'event_type': 'system_initialization',
                    'user': User.objects.filter(is_superuser=True).first(),
                    'ip_address': '127.0.0.1',
                    'user_agent': 'MedGuard-SA-Initializer/1.0',
                    'event_description': 'Database initialization completed successfully',
                    'event_details': {
                        'initialization_timestamp': timezone.now().isoformat(),
                        'medications_created': Medication.objects.count(),
                        'users_created': User.objects.count(),
                        'schedules_created': MedicationSchedule.objects.count(),
                        'prescriptions_created': PrescriptionRenewal.objects.count()
                    },
                    'severity': 'info',
                    'status': 'completed'
                }
                
                audit_entry = AuditLog.objects.create(**system_audit_data)
                audit_entries_created += 1
                logger.info(f"✅ Created system initialization audit entry")
                
                # Create user creation audit entries
                for user in User.objects.all():
                    user_audit_data = {
                        'event_type': 'user_created',
                        'user': User.objects.filter(is_superuser=True).first(),
                        'ip_address': '127.0.0.1',
                        'user_agent': 'MedGuard-SA-Initializer/1.0',
                        'event_description': f'User account created: {user.get_full_name()}',
                        'event_details': {
                            'created_user_id': user.id,
                            'created_user_type': user.user_type,
                            'created_user_email': user.email,
                            'created_at': user.date_joined.isoformat()
                        },
                        'severity': 'info',
                        'status': 'completed'
                    }
                    
                    AuditLog.objects.create(**user_audit_data)
                    audit_entries_created += 1
                
                # Create medication access audit entries
                for medication in Medication.objects.all()[:5]:  # First 5 medications
                    med_audit_data = {
                        'event_type': 'medication_created',
                        'user': User.objects.filter(is_superuser=True).first(),
                        'ip_address': '127.0.0.1',
                        'user_agent': 'MedGuard-SA-Initializer/1.0',
                        'event_description': f'Medication created: {medication.name}',
                        'event_details': {
                            'medication_id': medication.id,
                            'medication_name': medication.name,
                            'medication_type': medication.medication_type,
                            'prescription_type': medication.prescription_type,
                            'strength': f"{medication.strength} {medication.dosage_unit}"
                        },
                        'severity': 'info',
                        'status': 'completed'
                    }
                    
                    AuditLog.objects.create(**med_audit_data)
                    audit_entries_created += 1
                
                # Create security events
                security_events_created = 0
                security_event_types = [
                    ('login_success', 'Successful login', 'info'),
                    ('data_access', 'Patient data accessed', 'info'),
                    ('medication_dispensed', 'Medication dispensed', 'info'),
                    ('prescription_renewed', 'Prescription renewed', 'info')
                ]
                
                for event_type, description, severity in security_event_types:
                    for user in User.objects.filter(user_type='PATIENT')[:2]:
                        security_event_data = {
                            'event_type': event_type,
                            'user': user,
                            'ip_address': '127.0.0.1',
                            'user_agent': 'MedGuard-SA-Initializer/1.0',
                            'description': description,
                            'details': {
                                'initialization_event': True,
                                'sample_data': True,
                                'timestamp': timezone.now().isoformat()
                            },
                            'severity': severity,
                            'status': 'completed'
                        }
                        
                        SecurityEvent.objects.create(**security_event_data)
                        security_events_created += 1
                
                logger.info(f"✅ Created {audit_entries_created} audit log entries")
                logger.info(f"✅ Created {security_events_created} security events")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create audit log entries: {e}")
            return False
    
    def initialize_reporting_analytics_tables(self):
        """Initialize reporting and analytics tables."""
        self.log_section("INITIALIZING REPORTING AND ANALYTICS TABLES")
        
        try:
            with transaction.atomic():
                # Create analytics tables if they don't exist
                with connection.cursor() as cursor:
                    # Medication adherence analytics table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS medication_adherence_analytics (
                            id SERIAL PRIMARY KEY,
                            patient_id INTEGER NOT NULL,
                            medication_id INTEGER NOT NULL,
                            date DATE NOT NULL,
                            scheduled_doses INTEGER DEFAULT 0,
                            taken_doses INTEGER DEFAULT 0,
                            missed_doses INTEGER DEFAULT 0,
                            adherence_rate DECIMAL(5,2),
                            average_delay_minutes INTEGER,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            UNIQUE(patient_id, medication_id, date)
                        );
                    """)
                    
                    # Stock analytics table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS stock_analytics (
                            id SERIAL PRIMARY KEY,
                            medication_id INTEGER NOT NULL,
                            date DATE NOT NULL,
                            opening_stock INTEGER DEFAULT 0,
                            closing_stock INTEGER DEFAULT 0,
                            stock_in INTEGER DEFAULT 0,
                            stock_out INTEGER DEFAULT 0,
                            stock_turnover_rate DECIMAL(5,2),
                            days_of_stock_remaining INTEGER,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            UNIQUE(medication_id, date)
                        );
                    """)
                    
                    # User activity analytics table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_activity_analytics (
                            id SERIAL PRIMARY KEY,
                            user_id INTEGER NOT NULL,
                            date DATE NOT NULL,
                            login_count INTEGER DEFAULT 0,
                            medication_logs_created INTEGER DEFAULT 0,
                            prescriptions_viewed INTEGER DEFAULT 0,
                            alerts_acknowledged INTEGER DEFAULT 0,
                            session_duration_minutes INTEGER DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            UNIQUE(user_id, date)
                        );
                    """)
                    
                    # Create indexes for performance
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adherence_patient_date ON medication_adherence_analytics(patient_id, date);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_adherence_medication_date ON medication_adherence_analytics(medication_id, date);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stock_medication_date ON stock_analytics(medication_id, date);")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_user_date ON user_activity_analytics(user_id, date);")
                    
                    logger.info("✅ Analytics tables created")
                    logger.info("✅ Analytics indexes created")
                
                # Insert sample analytics data
                sample_analytics_created = 0
                
                # Sample adherence data
                patients = User.objects.filter(user_type='PATIENT')[:3]
                medications = Medication.objects.all()[:5]
                
                for patient in patients:
                    for medication in medications[:2]:
                        for days_ago in range(7):  # Last 7 days
                            date = timezone.now().date() - timedelta(days=days_ago)
                            scheduled = 2  # Twice daily
                            taken = 2 if days_ago < 5 else 1  # Some missed doses
                            missed = scheduled - taken
                            adherence_rate = (taken / scheduled) * 100 if scheduled > 0 else 0
                            
                            cursor.execute("""
                                INSERT INTO medication_adherence_analytics 
                                (patient_id, medication_id, date, scheduled_doses, taken_doses, 
                                 missed_doses, adherence_rate, average_delay_minutes)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                ON CONFLICT (patient_id, medication_id, date) DO NOTHING;
                            """, (
                                patient.id, medication.id, date, scheduled, taken, 
                                missed, adherence_rate, 15  # 15 minutes average delay
                            ))
                            sample_analytics_created += 1
                
                # Sample stock analytics
                for medication in medications:
                    for days_ago in range(30):  # Last 30 days
                        date = timezone.now().date() - timedelta(days=days_ago)
                        opening_stock = medication.pill_count + (days_ago * 2)
                        closing_stock = opening_stock - 5  # Daily usage
                        stock_in = 50 if days_ago % 7 == 0 else 0  # Weekly restock
                        stock_out = 5  # Daily usage
                        turnover_rate = (stock_out / opening_stock) * 100 if opening_stock > 0 else 0
                        days_remaining = closing_stock // 5 if stock_out > 0 else 0
                        
                        cursor.execute("""
                            INSERT INTO stock_analytics 
                            (medication_id, date, opening_stock, closing_stock, stock_in, 
                             stock_out, stock_turnover_rate, days_of_stock_remaining)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (medication_id, date) DO NOTHING;
                        """, (
                            medication.id, date, opening_stock, closing_stock, stock_in,
                            stock_out, turnover_rate, days_remaining
                        ))
                        sample_analytics_created += 1
                
                # Sample user activity analytics
                for user in User.objects.all()[:5]:
                    for days_ago in range(7):  # Last 7 days
                        date = timezone.now().date() - timedelta(days=days_ago)
                        login_count = 2 if days_ago < 5 else 1
                        medication_logs = 2 if user.user_type == 'PATIENT' else 0
                        prescriptions_viewed = 1 if user.user_type == 'PATIENT' else 3
                        alerts_acknowledged = 1 if days_ago % 2 == 0 else 0
                        session_duration = 45 if days_ago < 5 else 20
                        
                        cursor.execute("""
                            INSERT INTO user_activity_analytics 
                            (user_id, date, login_count, medication_logs_created, 
                             prescriptions_viewed, alerts_acknowledged, session_duration_minutes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (user_id, date) DO NOTHING;
                        """, (
                            user.id, date, login_count, medication_logs,
                            prescriptions_viewed, alerts_acknowledged, session_duration
                        ))
                        sample_analytics_created += 1
                
                logger.info(f"✅ Inserted {sample_analytics_created} sample analytics records")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize reporting and analytics tables: {e}")
            return False
    
    def verify_data_integrity_constraints(self):
        """Verify all data integrity constraints are met."""
        self.log_section("VERIFYING DATA INTEGRITY CONSTRAINTS")
        
        try:
            with transaction.atomic():
                integrity_checks = []
                
                # Check 1: All users have valid email addresses
                users_without_email = User.objects.filter(email='').count()
                integrity_checks.append(('Users with valid emails', users_without_email == 0))
                
                # Check 2: All medications have required fields
                medications_without_name = Medication.objects.filter(name='').count()
                integrity_checks.append(('Medications with valid names', medications_without_name == 0))
                
                # Check 3: All medication schedules have valid patients
                invalid_schedules = MedicationSchedule.objects.filter(patient__isnull=True).count()
                integrity_checks.append(('Valid medication schedule patients', invalid_schedules == 0))
                
                # Check 4: All medication schedules have valid medications
                invalid_schedule_meds = MedicationSchedule.objects.filter(medication__isnull=True).count()
                integrity_checks.append(('Valid medication schedule medications', invalid_schedule_meds == 0))
                
                # Check 5: All prescriptions have valid patients
                invalid_prescriptions = PrescriptionRenewal.objects.filter(patient__isnull=True).count()
                integrity_checks.append(('Valid prescription patients', invalid_prescriptions == 0))
                
                # Check 6: All prescriptions have valid medications
                invalid_prescription_meds = PrescriptionRenewal.objects.filter(medication__isnull=True).count()
                integrity_checks.append(('Valid prescription medications', invalid_prescription_meds == 0))
                
                # Check 7: All stock alerts have valid medications
                invalid_alerts = StockAlert.objects.filter(medication__isnull=True).count()
                integrity_checks.append(('Valid stock alert medications', invalid_alerts == 0))
                
                # Check 8: All medication logs have valid patients
                invalid_logs = MedicationLog.objects.filter(patient__isnull=True).count()
                integrity_checks.append(('Valid medication log patients', invalid_logs == 0))
                
                # Check 9: All medication logs have valid medications
                invalid_log_meds = MedicationLog.objects.filter(medication__isnull=True).count()
                integrity_checks.append(('Valid medication log medications', invalid_log_meds == 0))
                
                # Check 10: All stock transactions have valid medications
                invalid_transactions = StockTransaction.objects.filter(medication__isnull=True).count()
                integrity_checks.append(('Valid stock transaction medications', invalid_transactions == 0))
                
                # Check 11: All patients have medical record numbers
                patients_without_mrn = User.objects.filter(
                    user_type='PATIENT',
                    medical_record_number=''
                ).count()
                integrity_checks.append(('Patients with medical record numbers', patients_without_mrn == 0))
                
                # Check 12: All medications have positive stock levels
                medications_with_negative_stock = Medication.objects.filter(pill_count__lt=0).count()
                integrity_checks.append(('Medications with positive stock levels', medications_with_negative_stock == 0))
                
                # Check 13: All medication schedules have positive dosage amounts
                schedules_with_invalid_dosage = MedicationSchedule.objects.filter(dosage_amount__lte=0).count()
                integrity_checks.append(('Valid medication schedule dosages', schedules_with_invalid_dosage == 0))
                
                # Check 14: All prescription expiry dates are in the future
                expired_prescriptions = PrescriptionRenewal.objects.filter(
                    expiry_date__lt=timezone.now().date()
                ).count()
                integrity_checks.append(('Active prescriptions (not expired)', expired_prescriptions == 0))
                
                # Check 15: All users have valid user types
                invalid_user_types = User.objects.exclude(
                    user_type__in=['PATIENT', 'CAREGIVER', 'HEALTHCARE_PROVIDER']
                ).count()
                integrity_checks.append(('Valid user types', invalid_user_types == 0))
                
                # Report results
                all_passed = True
                for check_name, passed in integrity_checks:
                    status = "✅ PASS" if passed else "❌ FAIL"
                    logger.info(f"{status} {check_name}")
                    if not passed:
                        all_passed = False
                
                if all_passed:
                    logger.info("🎉 All data integrity constraints passed!")
                else:
                    logger.warning("⚠️ Some data integrity constraints failed")
                
                return all_passed
                
        except Exception as e:
            logger.error(f"❌ Failed to verify data integrity constraints: {e}")
            return False
    
    def verify_setup(self):
        """Verify the database setup was successful."""
        self.log_section("VERIFICATION")
        
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ Database connected: {version.split(',')[0]}")
            
            # Check user counts
            total_users = User.objects.count()
            patients = User.objects.filter(user_type='PATIENT').count()
            caregivers = User.objects.filter(user_type='CAREGIVER').count()
            providers = User.objects.filter(user_type='HEALTHCARE_PROVIDER').count()
            superusers = User.objects.filter(is_superuser=True).count()
            
            logger.info(f"✅ Users: {total_users} total")
            logger.info(f"   - Patients: {patients}")
            logger.info(f"   - Caregivers: {caregivers}")
            logger.info(f"   - Healthcare Providers: {providers}")
            logger.info(f"   - Superusers: {superusers}")
            
            # Check medication counts
            total_medications = Medication.objects.count()
            prescription_meds = Medication.objects.filter(prescription_type='prescription').count()
            otc_meds = Medication.objects.filter(prescription_type='otc').count()
            
            logger.info(f"✅ Medications: {total_medications} total")
            logger.info(f"   - Prescription: {prescription_meds}")
            logger.info(f"   - Over-the-counter: {otc_meds}")
            
            # Check other model counts
            schedules = MedicationSchedule.objects.count()
            logs = MedicationLog.objects.count()
            transactions = StockTransaction.objects.count()
            prescriptions = PrescriptionRenewal.objects.count()
            stock_alerts = StockAlert.objects.count()
            
            logger.info(f"✅ Schedules: {schedules}")
            logger.info(f"✅ Logs: {logs}")
            logger.info(f"✅ Transactions: {transactions}")
            logger.info(f"✅ Prescriptions: {prescriptions}")
            logger.info(f"✅ Stock Alerts: {stock_alerts}")
            
            # Check analytics and audit data
            try:
                with connection.cursor() as cursor:
                    # Check OCR cache
                    cursor.execute("SELECT COUNT(*) FROM ocr_processing_cache;")
                    ocr_cache_count = cursor.fetchone()[0]
                    logger.info(f"✅ OCR Cache Entries: {ocr_cache_count}")
                    
                    # Check analytics tables
                    cursor.execute("SELECT COUNT(*) FROM medication_adherence_analytics;")
                    adherence_analytics = cursor.fetchone()[0]
                    logger.info(f"✅ Adherence Analytics: {adherence_analytics}")
                    
                    cursor.execute("SELECT COUNT(*) FROM stock_analytics;")
                    stock_analytics = cursor.fetchone()[0]
                    logger.info(f"✅ Stock Analytics: {stock_analytics}")
                    
                    cursor.execute("SELECT COUNT(*) FROM user_activity_analytics;")
                    activity_analytics = cursor.fetchone()[0]
                    logger.info(f"✅ Activity Analytics: {activity_analytics}")
                    
            except Exception as e:
                logger.warning(f"⚠️ Could not verify analytics tables: {e}")
            
            # Check audit logs
            try:
                from security.models import AuditLog, SecurityEvent
                audit_logs = AuditLog.objects.count()
                security_events = SecurityEvent.objects.count()
                logger.info(f"✅ Audit Logs: {audit_logs}")
                logger.info(f"✅ Security Events: {security_events}")
            except Exception as e:
                logger.warning(f"⚠️ Could not verify audit logs: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    def run(self):
        """Run the complete database initialization process."""
        logger.info("🚀 Starting MedGuard SA Database Initialization")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check environment
        if not self.check_environment():
            return False
        
        # Execute initialization steps
        steps = [
            ("Database Drop/Recreate", self.drop_and_recreate_database),
            ("Migrations", self.run_migrations),
            ("Superuser Creation", self.create_superuser),
            ("Medication Seeding", self.seed_medications),
            ("Sample Patients", self.create_sample_patients),
            ("Sample Prescriptions", self.create_sample_prescriptions),
            ("Medication Schedules and Stock", self.initialize_medication_schedules_and_stock),
            ("OCR Processing Cache", self.setup_ocr_processing_cache),
            ("Audit Log Entries", self.create_audit_log_entries),
            ("Reporting and Analytics", self.initialize_reporting_analytics_tables),
            ("Data Integrity Verification", self.verify_data_integrity_constraints),
            ("Final Verification", self.verify_setup)
        ]
        
        for step_name, step_func in steps:
            if not step_func():
                logger.error(f"❌ Failed at step: {step_name}")
                return False
        
        # Success summary
        self.log_section("INITIALIZATION COMPLETE")
        logger.info("🎉 MedGuard SA Database Initialization Completed Successfully!")
        logger.info("")
        logger.info("📋 Access Information:")
        logger.info("   Admin URL: http://localhost:8000/admin/")
        logger.info("   Username: admin")
        logger.info("   Password: admin123")
        logger.info("")
        logger.info("🔧 Next Steps:")
        logger.info("   1. Start the development server: python manage.py runserver")
        logger.info("   2. Access the admin interface")
        logger.info("   3. Review and customize the seeded data")
        logger.info("   4. Test the medication management features")
        
        return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Initialize MedGuard SA database with all required data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python initialize_database.py                    # Standard initialization
  python initialize_database.py --drop-db         # Drop and recreate database
  python initialize_database.py --skip-seed       # Skip medication seeding
  python initialize_database.py --skip-patients   # Skip patient creation
        """
    )
    
    parser.add_argument(
        '--drop-db',
        action='store_true',
        help='Drop and recreate the database (development only)'
    )
    
    parser.add_argument(
        '--skip-seed',
        action='store_true',
        help='Skip medication seeding'
    )
    
    parser.add_argument(
        '--skip-patients',
        action='store_true',
        help='Skip sample patient creation'
    )
    
    args = parser.parse_args()
    
    # Initialize and run
    initializer = DatabaseInitializer(
        drop_db=args.drop_db,
        skip_seed=args.skip_seed,
        skip_patients=args.skip_patients
    )
    
    success = initializer.run()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main() 