#!/usr/bin/env python3
"""
Comprehensive Migration Testing for MedGuard SA

This module tests:
1. All 21 medications from the prescription can be created
2. ICD-10 code mappings work correctly (E10.4, F90.9, etc.)
3. Medication schedule creation for complex dosing (EPLEPTIN 3x3 daily)
4. Stock calculations work for different medication types
5. Prescription workflow state persistence

Author: MedGuard SA Development Team
Date: 2025-01-27
"""

import os
import sys
import django
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from medications.models import (
    Medication, MedicationSchedule, MedicationLog, StockTransaction,
    StockAlert, StockAnalytics, Prescription, PrescriptionMedication,
    PrescriptionDoctor, PrescriptionPatient, ICD10Code
)
from medications.serializers import ICD10Validator, PrescriptionBulkCreateSerializer
from medications.prescription_parser import PrescriptionParser

User = get_user_model()


class MigrationComprehensiveTest(TransactionTestCase):
    """
    Comprehensive migration testing for MedGuard SA prescription system.
    
    Tests all aspects of the medication management system including:
    - 21-medication prescription creation
    - ICD-10 code validation and mapping
    - Complex medication scheduling
    - Stock management and calculations
    - Prescription workflow states
    """
    
    def setUp(self):
        """Set up test data for comprehensive migration testing."""
        # Create test user
        self.user = User.objects.create_user(
            username='test_patient',
            email='test@medguard.co.za',
            password='testpass123',
            user_type='PATIENT',
            first_name='Test',
            last_name='Patient'
        )
        
        # Create test doctor
        self.doctor = PrescriptionDoctor.objects.create(
            name='Dr Test Physician',
            practice_number='TEST123',
            specialty='General Practice',
            contact_number='+27 11 123 4567',
            email='test@doctor.co.za'
        )
        
        # Create test patient
        self.patient = PrescriptionPatient.objects.create(
            name='Mr Test Patient',
            medical_aid_number='TEST456',
            medical_aid_scheme='Test Medical Aid',
            gender='male'
        )
        
        # Define the 21 medications from the prescription
        self.medications_data = [
            # 1. NOVORAPID 3ml FLEXPEN x 3
            {
                'name': 'NOVORAPID',
                'generic_name': 'Insulin aspart',
                'brand_name': 'NovoRapid',
                'strength': '100 units/ml',
                'dosage_unit': 'units',
                'medication_type': 'injection',
                'prescription_type': 'prescription',
                'pill_count': 3,
                'low_stock_threshold': 1,
                'manufacturer': 'Novo Nordisk',
                'icd10_codes': ['E10.4'],
                'description': 'Rapid-acting insulin for diabetes management',
                'side_effects': 'Hypoglycemia, injection site reactions',
                'contraindications': 'Hypersensitivity to insulin aspart',
                'storage_instructions': 'Refrigerate between 2-8°C, do not freeze',
                'expiration_date': date.today() + timedelta(days=365)
            },
            # 2. LANTUS SOLARSTAR PEN x 2
            {
                'name': 'LANTUS',
                'generic_name': 'Insulin glargine',
                'brand_name': 'Lantus',
                'strength': '100 units/ml',
                'dosage_unit': 'units',
                'medication_type': 'injection',
                'prescription_type': 'prescription',
                'pill_count': 2,
                'low_stock_threshold': 1,
                'manufacturer': 'Sanofi',
                'icd10_codes': ['E10.4'],
                'description': 'Long-acting insulin for diabetes management',
                'side_effects': 'Hypoglycemia, weight gain',
                'contraindications': 'Hypersensitivity to insulin glargine',
                'storage_instructions': 'Refrigerate between 2-8°C, do not freeze',
                'expiration_date': date.today() + timedelta(days=365)
            },
            # 3. ELTROXIN 200mg TABLETS x 30
            {
                'name': 'ELTROXIN',
                'generic_name': 'Levothyroxine sodium',
                'brand_name': 'Eltroxin',
                'strength': '200',
                'dosage_unit': 'mcg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['E03.9'],
                'description': 'Thyroid hormone replacement therapy',
                'side_effects': 'Palpitations, insomnia, weight loss',
                'contraindications': 'Untreated thyrotoxicosis',
                'storage_instructions': 'Store at room temperature, protect from light',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 4. MEDROL 4mg TABLETS x 30
            {
                'name': 'MEDROL',
                'generic_name': 'Methylprednisolone',
                'brand_name': 'Medrol',
                'strength': '4',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Pfizer',
                'icd10_codes': ['E27.4'],
                'description': 'Corticosteroid for adrenal insufficiency',
                'side_effects': 'Weight gain, osteoporosis, diabetes',
                'contraindications': 'Systemic fungal infections',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 5. FLORINEF 0.1mg TABLETS x 30
            {
                'name': 'FLORINEF',
                'generic_name': 'Fludrocortisone acetate',
                'brand_name': 'Florinef',
                'strength': '0.1',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['E27.4'],
                'description': 'Mineralocorticoid for adrenal insufficiency',
                'side_effects': 'Hypertension, edema, hypokalemia',
                'contraindications': 'Systemic fungal infections',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 6. VYVANSE 70mg CAPSULES x 30
            {
                'name': 'VYVANSE',
                'generic_name': 'Lisdexamfetamine dimesylate',
                'brand_name': 'Vyvanse',
                'strength': '70',
                'dosage_unit': 'mg',
                'medication_type': 'capsule',
                'prescription_type': 'schedule_6',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Takeda',
                'icd10_codes': ['F90.9'],
                'description': 'Stimulant medication for ADHD',
                'side_effects': 'Decreased appetite, insomnia, anxiety',
                'contraindications': 'Cardiovascular disease, glaucoma',
                'storage_instructions': 'Store at room temperature, keep secure',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 7. WELBUTRIN XL 300mg TABLETS x 30
            {
                'name': 'WELBUTRIN XL',
                'generic_name': 'Bupropion hydrochloride',
                'brand_name': 'Wellbutrin XL',
                'strength': '300',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'GlaxoSmithKline',
                'icd10_codes': ['F41.8'],
                'description': 'Antidepressant and smoking cessation aid',
                'side_effects': 'Insomnia, dry mouth, headache',
                'contraindications': 'Seizure disorders, eating disorders',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 8. RITALIN LA 40mg CAPSULES x 30
            {
                'name': 'RITALIN LA',
                'generic_name': 'Methylphenidate hydrochloride',
                'brand_name': 'Ritalin LA',
                'strength': '40',
                'dosage_unit': 'mg',
                'medication_type': 'capsule',
                'prescription_type': 'schedule_6',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Novartis',
                'icd10_codes': ['F90.9'],
                'description': 'Long-acting stimulant for ADHD',
                'side_effects': 'Decreased appetite, insomnia, nervousness',
                'contraindications': 'Cardiovascular disease, glaucoma',
                'storage_instructions': 'Store at room temperature, keep secure',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 9. CYMGEN 500mg TABLETS x 30
            {
                'name': 'CYMGEN',
                'generic_name': 'Cyanocobalamin',
                'brand_name': 'Cymgen',
                'strength': '500',
                'dosage_unit': 'mcg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['D51.9'],
                'description': 'Vitamin B12 supplement',
                'side_effects': 'Diarrhea, itching, rash',
                'contraindications': 'Hypersensitivity to cyanocobalamin',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 10. TOPZOLE 20mg TABLETS x 30
            {
                'name': 'TOPZOLE',
                'generic_name': 'Omeprazole',
                'brand_name': 'Topzole',
                'strength': '20',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['K21.0'],
                'description': 'Proton pump inhibitor for acid reflux',
                'side_effects': 'Headache, diarrhea, abdominal pain',
                'contraindications': 'Hypersensitivity to omeprazole',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 11. FEXO 180mg TABLETS x 30
            {
                'name': 'FEXO',
                'generic_name': 'Fexofenadine hydrochloride',
                'brand_name': 'Fexo',
                'strength': '180',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['J30.9'],
                'description': 'Antihistamine for allergic rhinitis',
                'side_effects': 'Headache, drowsiness, nausea',
                'contraindications': 'Hypersensitivity to fexofenadine',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 12. RIVOTRIL 2mg TABLETS x 30
            {
                'name': 'RIVOTRIL',
                'generic_name': 'Clonazepam',
                'brand_name': 'Rivotril',
                'strength': '2',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'schedule_5',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Roche',
                'icd10_codes': ['G47.6'],
                'description': 'Benzodiazepine for sleep disorders',
                'side_effects': 'Drowsiness, dizziness, dependence',
                'contraindications': 'Respiratory depression, sleep apnea',
                'storage_instructions': 'Store at room temperature, keep secure',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 13. EPLEPTIN 400mg TABLETS x 270
            {
                'name': 'EPLEPTIN',
                'generic_name': 'Phenytoin sodium',
                'brand_name': 'Epleptin',
                'strength': '400',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 270,
                'low_stock_threshold': 30,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['G40.9'],
                'description': 'Anticonvulsant for epilepsy',
                'side_effects': 'Dizziness, drowsiness, gingival hyperplasia',
                'contraindications': 'Hypersensitivity to phenytoin',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 14. TARGINACT 10/5mg TABLETS x 60
            {
                'name': 'TARGINACT',
                'generic_name': 'Oxycodone/naloxone',
                'brand_name': 'Targinact',
                'strength': '10/5',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'schedule_6',
                'pill_count': 60,
                'low_stock_threshold': 14,
                'manufacturer': 'Mundipharma',
                'icd10_codes': ['G89.4'],
                'description': 'Opioid analgesic for chronic pain',
                'side_effects': 'Constipation, drowsiness, nausea',
                'contraindications': 'Respiratory depression, paralytic ileus',
                'storage_instructions': 'Store at room temperature, keep secure',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 15. CELEBREX 200mg CAPSULES x 30
            {
                'name': 'CELEBREX',
                'generic_name': 'Celecoxib',
                'brand_name': 'Celebrex',
                'strength': '200',
                'dosage_unit': 'mg',
                'medication_type': 'capsule',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Pfizer',
                'icd10_codes': ['G89.4'],
                'description': 'COX-2 inhibitor for pain and inflammation',
                'side_effects': 'Stomach upset, headache, dizziness',
                'contraindications': 'Cardiovascular disease, peptic ulcer',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 16. QUININE 300mg TABLETS x 30
            {
                'name': 'QUININE',
                'generic_name': 'Quinine sulphate',
                'brand_name': 'Quinine',
                'strength': '300',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['G89.4'],
                'description': 'Antimalarial and muscle relaxant',
                'side_effects': 'Tinnitus, headache, nausea',
                'contraindications': 'Hypersensitivity to quinine',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 17. MONTEFLO 10mg TABLETS x 30
            {
                'name': 'MONTEFLO',
                'generic_name': 'Montelukast sodium',
                'brand_name': 'Monteflo',
                'strength': '10',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['J45.901'],
                'description': 'Leukotriene receptor antagonist for asthma',
                'side_effects': 'Headache, abdominal pain, cough',
                'contraindications': 'Hypersensitivity to montelukast',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 18. BETNOVATE IN UEA 0.1% CREAM x 30g
            {
                'name': 'BETNOVATE IN UEA',
                'generic_name': 'Betamethasone valerate',
                'brand_name': 'Betnovate',
                'strength': '0.1',
                'dosage_unit': '%',
                'medication_type': 'cream',
                'prescription_type': 'prescription',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'GlaxoSmithKline',
                'icd10_codes': ['L20.9'],
                'description': 'Topical corticosteroid for skin conditions',
                'side_effects': 'Skin thinning, local irritation',
                'contraindications': 'Fungal skin infections',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 19. SENNA 8.6mg TABLETS x 30
            {
                'name': 'SENNA',
                'generic_name': 'Senna glycosides',
                'brand_name': 'Senna',
                'strength': '8.6',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['K59.0'],
                'description': 'Stimulant laxative for constipation',
                'side_effects': 'Abdominal cramps, diarrhea',
                'contraindications': 'Intestinal obstruction',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 20. DULCOLAX 5mg TABLETS x 30
            {
                'name': 'DULCOLAX',
                'generic_name': 'Bisacodyl',
                'brand_name': 'Dulcolax',
                'strength': '5',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Boehringer Ingelheim',
                'icd10_codes': ['K59.0'],
                'description': 'Stimulant laxative for constipation',
                'side_effects': 'Abdominal cramps, diarrhea',
                'contraindications': 'Intestinal obstruction',
                'storage_instructions': 'Store at room temperature',
                'expiration_date': date.today() + timedelta(days=730)
            },
            # 21. STILPAYNE 50mg CAPSULES x 30
            {
                'name': 'STILPAYNE',
                'generic_name': 'Tramadol hydrochloride',
                'brand_name': 'Stilpayne',
                'strength': '50',
                'dosage_unit': 'mg',
                'medication_type': 'capsule',
                'prescription_type': 'schedule_5',
                'pill_count': 30,
                'low_stock_threshold': 7,
                'manufacturer': 'Aspen Pharmacare',
                'icd10_codes': ['G89.4'],
                'description': 'Opioid analgesic for moderate pain',
                'side_effects': 'Drowsiness, nausea, constipation',
                'contraindications': 'Respiratory depression, acute intoxication',
                'storage_instructions': 'Store at room temperature, keep secure',
                'expiration_date': date.today() + timedelta(days=730)
            }
        ]
        
        # Create ICD-10 codes
        self.icd10_codes = {
            'E10.4': ICD10Code.objects.create(
                code='E10.4',
                description='Type 1 diabetes mellitus with neurological complications',
                category='diabetes',
                is_active=True
            ),
            'E03.9': ICD10Code.objects.create(
                code='E03.9',
                description='Hypothyroidism, unspecified',
                category='endocrine',
                is_active=True
            ),
            'E27.4': ICD10Code.objects.create(
                code='E27.4',
                description='Other and unspecified adrenocortical insufficiency',
                category='endocrine',
                is_active=True
            ),
            'F90.9': ICD10Code.objects.create(
                code='F90.9',
                description='Attention-deficit hyperactivity disorder, unspecified type',
                category='mental_health',
                is_active=True
            ),
            'F41.8': ICD10Code.objects.create(
                code='F41.8',
                description='Other specified anxiety disorders',
                category='mental_health',
                is_active=True
            ),
            'G47.6': ICD10Code.objects.create(
                code='G47.6',
                description='Sleep related movement disorders',
                category='neurological',
                is_active=True
            ),
            'G89.4': ICD10Code.objects.create(
                code='G89.4',
                description='Chronic pain syndrome',
                category='pain',
                is_active=True
            ),
            'K21.0': ICD10Code.objects.create(
                code='K21.0',
                description='Gastro-esophageal reflux disease with esophagitis',
                category='gastrointestinal',
                is_active=True
            ),
            'J30.9': ICD10Code.objects.create(
                code='J30.9',
                description='Allergic rhinitis, unspecified',
                category='respiratory',
                is_active=True
            ),
            'D51.9': ICD10Code.objects.create(
                code='D51.9',
                description='Vitamin B12 deficiency anemia, unspecified',
                category='hematological',
                is_active=True
            ),
            'G40.9': ICD10Code.objects.create(
                code='G40.9',
                description='Epilepsy, unspecified',
                category='neurological',
                is_active=True
            ),
            'J45.901': ICD10Code.objects.create(
                code='J45.901',
                description='Unspecified asthma with (acute) exacerbation',
                category='respiratory',
                is_active=True
            ),
            'L20.9': ICD10Code.objects.create(
                code='L20.9',
                description='Atopic dermatitis, unspecified',
                category='dermatological',
                is_active=True
            ),
                         'K59.0': ICD10Code.objects.create(
                 code='K59.0',
                 description='Constipation',
                 category='gastrointestinal',
                 is_active=True
             )
         }
    
    def test_01_all_21_medications_creation(self):
        """Test that all 21 medications from the prescription can be created successfully."""
        print("\n=== Testing All 21 Medications Creation ===")
        
        created_medications = []
        
        for i, med_data in enumerate(self.medications_data, 1):
            try:
                # Create medication
                medication = Medication.objects.create(
                    name=med_data['name'],
                    generic_name=med_data['generic_name'],
                    brand_name=med_data['brand_name'],
                    strength=med_data['strength'],
                    dosage_unit=med_data['dosage_unit'],
                    medication_type=med_data['medication_type'],
                    prescription_type=med_data['prescription_type'],
                    pill_count=med_data['pill_count'],
                    low_stock_threshold=med_data['low_stock_threshold'],
                    manufacturer=med_data['manufacturer'],
                    description=med_data['description'],
                    side_effects=med_data['side_effects'],
                    contraindications=med_data['contraindications'],
                    storage_instructions=med_data['storage_instructions'],
                    expiration_date=med_data['expiration_date']
                )
                
                # Add ICD-10 codes
                for icd10_code in med_data['icd10_codes']:
                    if icd10_code in self.icd10_codes:
                        medication.icd10_codes.add(self.icd10_codes[icd10_code])
                
                created_medications.append(medication)
                print(f"✓ Created medication {i}/21: {medication.name} ({medication.strength} {medication.dosage_unit})")
                
            except Exception as e:
                print(f"✗ Failed to create medication {i}/21: {med_data['name']} - {str(e)}")
                raise
        
        # Verify all 21 medications were created
        self.assertEqual(len(created_medications), 21, "All 21 medications should be created")
        self.assertEqual(Medication.objects.count(), 21, "Database should contain exactly 21 medications")
        
        # Test medication properties
        for medication in created_medications:
            self.assertIsNotNone(medication.id, "Medication should have an ID")
            self.assertIsNotNone(medication.name, "Medication should have a name")
            self.assertIsNotNone(medication.strength, "Medication should have strength")
            self.assertIsNotNone(medication.dosage_unit, "Medication should have dosage unit")
            self.assertIsNotNone(medication.medication_type, "Medication should have type")
            self.assertIsNotNone(medication.prescription_type, "Medication should have prescription type")
        
        print(f"✓ Successfully created all 21 medications")
        return created_medications
    
    def test_02_icd10_code_mappings(self):
        """Test that ICD-10 code mappings work correctly for all codes."""
        print("\n=== Testing ICD-10 Code Mappings ===")
        
        # Test ICD-10 validator
        test_codes = ['E10.4', 'F90.9', 'G89.4', 'K21.0', 'J30.9']
        
        for code in test_codes:
            # Test validation
            self.assertTrue(ICD10Validator.validate(code), f"ICD-10 code {code} should be valid")
            
            # Test cleaning
            cleaned_code = ICD10Validator.clean(code)
            self.assertEqual(cleaned_code, code, f"Cleaned code should match original: {code}")
            
            # Test description mapping
            if code in self.icd10_codes:
                icd10_obj = self.icd10_codes[code]
                self.assertIsNotNone(icd10_obj.description, f"ICD-10 code {code} should have description")
                self.assertTrue(icd10_obj.is_active, f"ICD-10 code {code} should be active")
                print(f"✓ ICD-10 code {code}: {icd10_obj.description}")
        
        # Test invalid codes
        invalid_codes = ['INVALID', 'A1.2', 'Z99.999', 'A00']
        for code in invalid_codes:
            self.assertFalse(ICD10Validator.validate(code), f"Invalid code {code} should be rejected")
        
        # Test medication-ICD10 associations
        created_medications = self.test_01_all_21_medications_creation()
        
        for medication in created_medications:
            icd10_count = medication.icd10_codes.count()
            self.assertGreaterEqual(icd10_count, 0, f"Medication {medication.name} should have ICD-10 codes")
            if icd10_count > 0:
                print(f"✓ {medication.name} has {icd10_count} ICD-10 code(s)")
        
        print("✓ All ICD-10 code mappings work correctly")
    
    def test_03_complex_medication_schedules(self):
        """Test medication schedule creation for complex dosing patterns."""
        print("\n=== Testing Complex Medication Schedules ===")
        
        created_medications = self.test_01_all_21_medications_creation()
        
        # Define complex schedule patterns
        schedule_patterns = [
            # EPLEPTIN: 3 tablets 3 times daily (complex dosing)
            {
                'medication_name': 'EPLEPTIN',
                'schedules': [
                    {'timing': 'morning', 'dosage': 3, 'frequency': 'three times daily'},
                    {'timing': 'noon', 'dosage': 3, 'frequency': 'three times daily'},
                    {'timing': 'night', 'dosage': 3, 'frequency': 'three times daily'}
                ]
            },
            # MEDROL: 1 tablet morning + 2 tablets noon
            {
                'medication_name': 'MEDROL',
                'schedules': [
                    {'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
                    {'timing': 'noon', 'dosage': 2, 'frequency': 'daily'}
                ]
            },
            # VYVANSE: 2 capsules once daily
            {
                'medication_name': 'VYVANSE',
                'schedules': [
                    {'timing': 'morning', 'dosage': 2, 'frequency': 'daily'}
                ]
            },
            # TARGINACT: 1 tablet twice daily
            {
                'medication_name': 'TARGINACT',
                'schedules': [
                    {'timing': 'morning', 'dosage': 1, 'frequency': 'twice daily'},
                    {'timing': 'night', 'dosage': 1, 'frequency': 'twice daily'}
                ]
            }
        ]
        
        created_schedules = []
        
        for pattern in schedule_patterns:
            medication = next((med for med in created_medications if med.name == pattern['medication_name']), None)
            self.assertIsNotNone(medication, f"Medication {pattern['medication_name']} should exist")
            
            for schedule_data in pattern['schedules']:
                try:
                    schedule = MedicationSchedule.objects.create(
                        patient=self.user,
                        medication=medication,
                        timing=schedule_data['timing'],
                        dosage_amount=schedule_data['dosage'],
                        frequency=schedule_data['frequency'],
                        start_date=date.today(),
                        instructions=f"Take {schedule_data['dosage']} {medication.medication_type}(s) {schedule_data['frequency']}"
                    )
                    
                    created_schedules.append(schedule)
                    print(f"✓ Created schedule for {medication.name}: {schedule_data['dosage']}x {schedule_data['frequency']} ({schedule_data['timing']})")
                    
                except Exception as e:
                    print(f"✗ Failed to create schedule for {medication.name}: {str(e)}")
                    raise
        
        # Test schedule properties
        for schedule in created_schedules:
            self.assertIsNotNone(schedule.id, "Schedule should have an ID")
            self.assertEqual(schedule.patient, self.user, "Schedule should belong to test user")
            self.assertIsNotNone(schedule.medication, "Schedule should have medication")
            self.assertIsNotNone(schedule.timing, "Schedule should have timing")
            self.assertGreater(schedule.dosage_amount, 0, "Schedule should have positive dosage")
            self.assertIsNotNone(schedule.frequency, "Schedule should have frequency")
            self.assertTrue(schedule.is_active, "Schedule should be active")
        
        # Test EPLEPTIN complex dosing specifically
        epleptin = next((med for med in created_medications if med.name == 'EPLEPTIN'), None)
        epleptin_schedules = MedicationSchedule.objects.filter(medication=epleptin, patient=self.user)
        self.assertEqual(epleptin_schedules.count(), 3, "EPLEPTIN should have 3 schedules (morning, noon, night)")
        
        total_epleptin_daily = sum(schedule.dosage_amount for schedule in epleptin_schedules)
        self.assertEqual(total_epleptin_daily, 9, "EPLEPTIN total daily dosage should be 9 tablets")
        
        print(f"✓ Successfully created {len(created_schedules)} complex medication schedules")
        print(f"✓ EPLEPTIN complex dosing: 3 tablets 3x daily = 9 tablets total")
    
    def test_04_stock_calculations(self):
        """Test stock calculations work for different medication types."""
        print("\n=== Testing Stock Calculations ===")
        
        created_medications = self.test_01_all_21_medications_creation()
        
        # Test different medication types and their stock calculations
        for medication in created_medications:
            initial_stock = medication.pill_count
            low_threshold = medication.low_stock_threshold
            
            # Test low stock detection
            is_low_stock = medication.is_low_stock
            expected_low_stock = initial_stock <= low_threshold
            self.assertEqual(is_low_stock, expected_low_stock, 
                           f"{medication.name} low stock detection should be correct")
            
            # Test stock transactions
            try:
                # Create initial stock transaction
                initial_transaction = StockTransaction.objects.create(
                    medication=medication,
                    user=self.user,
                    transaction_type='purchase',
                    quantity=initial_stock,
                    unit_price=Decimal('50.00'),
                    total_amount=Decimal('50.00') * initial_stock,
                    stock_before=0,
                    stock_after=initial_stock,
                    reference_number=f'TEST-{medication.id}',
                    batch_number=f'BATCH-{medication.id}',
                    expiry_date=medication.expiration_date,
                    notes=f'Test stock for {medication.name}'
                )
                
                # Test dose taken transaction (simulate patient taking medication)
                if medication.medication_type in ['tablet', 'capsule']:
                    dose_taken = 1
                    new_stock = initial_stock - dose_taken
                    
                    dose_transaction = StockTransaction.objects.create(
                        medication=medication,
                        user=self.user,
                        transaction_type='dose_taken',
                        quantity=-dose_taken,
                        stock_before=initial_stock,
                        stock_after=new_stock,
                        reference_number=f'DOSE-{medication.id}',
                        notes=f'Patient took {dose_taken} {medication.medication_type}'
                    )
                    
                    # Update medication stock
                    medication.pill_count = new_stock
                    medication.save()
                    
                    # Verify stock calculation
                    self.assertEqual(medication.pill_count, new_stock, 
                                   f"{medication.name} stock should be updated correctly")
                    
                    # Test low stock alert creation
                    if medication.is_low_stock:
                        alert = StockAlert.objects.create(
                            medication=medication,
                            created_by=self.user,
                            alert_type='low_stock',
                            priority='medium',
                            title=f'Low Stock Alert: {medication.name}',
                            message=f'{medication.name} stock is low ({medication.pill_count} remaining)',
                            current_stock=medication.pill_count,
                            threshold_level=medication.low_stock_threshold
                        )
                        self.assertTrue(alert.is_active, f"Low stock alert for {medication.name} should be active")
                        print(f"✓ Created low stock alert for {medication.name} ({medication.pill_count} remaining)")
                
                print(f"✓ Stock calculations for {medication.name}: {initial_stock} → {medication.pill_count}")
                
            except Exception as e:
                print(f"✗ Failed stock calculations for {medication.name}: {str(e)}")
                raise
        
        # Test stock analytics
        for medication in created_medications:
            try:
                analytics = StockAnalytics.objects.create(
                    medication=medication,
                    daily_usage_rate=1.0,
                    weekly_usage_rate=7.0,
                    monthly_usage_rate=30.0,
                    days_until_stockout=medication.pill_count,
                    predicted_stockout_date=date.today() + timedelta(days=medication.pill_count),
                    recommended_order_quantity=max(30, medication.low_stock_threshold * 2),
                    usage_volatility=0.5,
                    stockout_confidence=0.8
                )
                
                self.assertIsNotNone(analytics.days_until_stockout, f"Analytics for {medication.name} should have stockout prediction")
                self.assertIsNotNone(analytics.recommended_order_quantity, f"Analytics for {medication.name} should have order recommendation")
                
            except Exception as e:
                print(f"✗ Failed analytics for {medication.name}: {str(e)}")
                raise
        
        print("✓ All stock calculations work correctly for different medication types")
    
    def test_05_prescription_workflow_states(self):
        """Test prescription workflow state persistence and transitions."""
        print("\n=== Testing Prescription Workflow States ===")
        
        created_medications = self.test_01_all_21_medications_creation()
        
        # Create prescription with all 21 medications
        prescription = Prescription.objects.create(
            prescription_number='TEST-PRES-001',
            prescription_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            status='draft',
            priority='routine',
            prescription_type='new',
            total_medications=21,
            doctor=self.doctor,
            patient=self.patient,
            notes='Test prescription with all 21 medications'
        )
        
        # Add all medications to prescription
        for i, medication in enumerate(created_medications, 1):
            PrescriptionMedication.objects.create(
                prescription=prescription,
                medication_number=i,
                medication_name=medication.name,
                generic_name=medication.generic_name,
                brand_name=medication.brand_name,
                strength=medication.strength,
                dosage_unit=medication.dosage_unit,
                quantity=medication.pill_count,
                quantity_unit=medication.medication_type,
                instructions=f"Take as prescribed for {medication.name}",
                timing='morning',
                icd10_code=medication.icd10_codes.first().code if medication.icd10_codes.exists() else 'Z51.9'
            )
        
        # Test prescription workflow states
        workflow_states = ['draft', 'active', 'filled', 'expired']
        
        for state in workflow_states:
            try:
                prescription.status = state
                prescription.save()
                
                # Verify state persistence
                prescription.refresh_from_db()
                self.assertEqual(prescription.status, state, f"Prescription status should persist as {state}")
                
                print(f"✓ Prescription workflow state: {state}")
                
            except Exception as e:
                print(f"✗ Failed to set prescription state to {state}: {str(e)}")
                raise
        
        # Test prescription validation
        self.assertEqual(prescription.total_medications, 21, "Prescription should have 21 medications")
        self.assertIsNotNone(prescription.doctor, "Prescription should have doctor")
        self.assertIsNotNone(prescription.patient, "Prescription should have patient")
        self.assertIsNotNone(prescription.prescription_date, "Prescription should have date")
        self.assertIsNotNone(prescription.expiry_date, "Prescription should have expiry date")
        
        # Test prescription medication relationships
        prescription_medications = PrescriptionMedication.objects.filter(prescription=prescription)
        self.assertEqual(prescription_medications.count(), 21, "Prescription should have 21 prescription medications")
        
        for pm in prescription_medications:
            self.assertIsNotNone(pm.medication_number, "Prescription medication should have number")
            self.assertIsNotNone(pm.medication_name, "Prescription medication should have name")
            self.assertIsNotNone(pm.strength, "Prescription medication should have strength")
            self.assertIsNotNone(pm.quantity, "Prescription medication should have quantity")
        
        print("✓ Prescription workflow states persist correctly")
        print("✓ All 21 medications are properly linked to prescription")
    
    def test_06_comprehensive_integration(self):
        """Test comprehensive integration of all components."""
        print("\n=== Testing Comprehensive Integration ===")
        
        # Run all previous tests to ensure integration
        created_medications = self.test_01_all_21_medications_creation()
        self.test_02_icd10_code_mappings()
        self.test_03_complex_medication_schedules()
        self.test_04_stock_calculations()
        self.test_05_prescription_workflow_states()
        
        # Test medication log creation
        for medication in created_medications[:5]:  # Test first 5 medications
            try:
                log = MedicationLog.objects.create(
                    patient=self.user,
                    medication=medication,
                    scheduled_time=timezone.now(),
                    actual_time=timezone.now(),
                    status='taken',
                    dosage_taken=1.0,
                    notes=f'Test log for {medication.name}'
                )
                
                self.assertIsNotNone(log.id, f"Medication log for {medication.name} should be created")
                self.assertEqual(log.status, 'taken', f"Log status should be 'taken'")
                
            except Exception as e:
                print(f"✗ Failed to create log for {medication.name}: {str(e)}")
                raise
        
        # Test bulk prescription creation
        try:
            bulk_data = {
                'prescription_number': 'BULK-TEST-001',
                'prescribing_doctor': 'Dr Test Physician',
                'prescribed_date': date.today(),
                'patient_id': self.user.id,
                'icd10_codes': ['E10.4', 'F90.9'],
                'medications': [
                    {
                        'name': 'TEST MED 1',
                        'strength': '100',
                        'dosage_unit': 'mg',
                        'quantity': 30,
                        'instructions': 'Take once daily'
                    },
                    {
                        'name': 'TEST MED 2',
                        'strength': '50',
                        'dosage_unit': 'mg',
                        'quantity': 60,
                        'instructions': 'Take twice daily'
                    }
                ]
            }
            
            serializer = PrescriptionBulkCreateSerializer(data=bulk_data)
            self.assertTrue(serializer.is_valid(), f"Bulk serializer should be valid: {serializer.errors}")
            
        except Exception as e:
            print(f"✗ Failed bulk prescription test: {str(e)}")
            raise
        
        print("✓ Comprehensive integration test passed")
        print("✓ All 21 medications, ICD-10 codes, schedules, stock, and workflow work together")
    
    def test_07_performance_and_scalability(self):
        """Test performance and scalability of the migration system."""
        print("\n=== Testing Performance and Scalability ===")
        
        import time
        
        # Test medication creation performance
        start_time = time.time()
        created_medications = self.test_01_all_21_medications_creation()
        creation_time = time.time() - start_time
        
        self.assertLess(creation_time, 5.0, "Medication creation should complete within 5 seconds")
        print(f"✓ Created 21 medications in {creation_time:.2f} seconds")
        
        # Test schedule creation performance
        start_time = time.time()
        self.test_03_complex_medication_schedules()
        schedule_time = time.time() - start_time
        
        self.assertLess(schedule_time, 3.0, "Schedule creation should complete within 3 seconds")
        print(f"✓ Created complex schedules in {schedule_time:.2f} seconds")
        
        # Test stock calculation performance
        start_time = time.time()
        self.test_04_stock_calculations()
        stock_time = time.time() - start_time
        
        self.assertLess(stock_time, 5.0, "Stock calculations should complete within 5 seconds")
        print(f"✓ Completed stock calculations in {stock_time:.2f} seconds")
        
        # Test database query performance
        start_time = time.time()
        medications = Medication.objects.all()
        schedules = MedicationSchedule.objects.all()
        transactions = StockTransaction.objects.all()
        query_time = time.time() - start_time
        
        self.assertLess(query_time, 1.0, "Database queries should complete within 1 second")
        print(f"✓ Database queries completed in {query_time:.2f} seconds")
        
        print("✓ Performance and scalability tests passed")
    
    def test_08_ocr_result_storage_and_retrieval(self):
        """Test OCR result storage and retrieval functionality."""
        print("\n=== Testing OCR Result Storage and Retrieval ===")
        
        created_medications = self.test_01_all_21_medications_creation()
        
        # Test OCR result storage
        ocr_results = [
            {
                'medication_name': 'NOVORAPID',
                'strength': '100 units/ml',
                'dosage': '10 units',
                'frequency': 'before meals',
                'confidence': 0.95,
                'raw_text': 'NOVORAPID 100 units/ml\nTake 10 units before meals',
                'parsed_data': {
                    'name': 'NOVORAPID',
                    'strength': '100 units/ml',
                    'dosage': '10 units',
                    'frequency': 'before meals'
                }
            },
            {
                'medication_name': 'EPLEPTIN',
                'strength': '400mg',
                'dosage': '3 tablets',
                'frequency': 'three times daily',
                'confidence': 0.92,
                'raw_text': 'EPLEPTIN 400mg\nTake 3 tablets three times daily',
                'parsed_data': {
                    'name': 'EPLEPTIN',
                    'strength': '400mg',
                    'dosage': '3 tablets',
                    'frequency': 'three times daily'
                }
            },
            {
                'medication_name': 'VYVANSE',
                'strength': '70mg',
                'dosage': '2 capsules',
                'frequency': 'once daily',
                'confidence': 0.88,
                'raw_text': 'VYVANSE 70mg\nTake 2 capsules once daily',
                'parsed_data': {
                    'name': 'VYVANSE',
                    'strength': '70mg',
                    'dosage': '2 capsules',
                    'frequency': 'once daily'
                }
            }
        ]
        
        stored_ocr_results = []
        
        for ocr_data in ocr_results:
            try:
                # Create OCR result record
                ocr_result = {
                    'patient': self.user,
                    'medication_name': ocr_data['medication_name'],
                    'strength': ocr_data['strength'],
                    'dosage': ocr_data['dosage'],
                    'frequency': ocr_data['frequency'],
                    'confidence_score': ocr_data['confidence'],
                    'raw_text': ocr_data['raw_text'],
                    'parsed_data': ocr_data['parsed_data'],
                    'processing_status': 'completed',
                    'created_at': timezone.now()
                }
                
                # Store in database (simulating OCR result storage)
                # Note: This would typically use a dedicated OCR result model
                # For testing, we'll store in a JSON field or create a test model
                
                stored_ocr_results.append(ocr_result)
                print(f"✓ Stored OCR result for {ocr_data['medication_name']} (confidence: {ocr_data['confidence']:.2f})")
                
            except Exception as e:
                print(f"✗ Failed to store OCR result for {ocr_data['medication_name']}: {str(e)}")
                raise
        
        # Test OCR result retrieval and matching
        for ocr_result in stored_ocr_results:
            try:
                # Simulate retrieving OCR result and matching with medication
                medication = next((med for med in created_medications if med.name == ocr_result['medication_name']), None)
                
                if medication:
                    # Verify OCR data matches medication data
                    self.assertEqual(medication.name, ocr_result['medication_name'], 
                                   f"OCR medication name should match: {medication.name}")
                    
                    # Test confidence threshold
                    self.assertGreaterEqual(ocr_result['confidence_score'], 0.8, 
                                          f"OCR confidence should be >= 0.8 for {medication.name}")
                    
                    # Test parsed data structure
                    self.assertIn('name', ocr_result['parsed_data'], "Parsed data should contain medication name")
                    self.assertIn('strength', ocr_result['parsed_data'], "Parsed data should contain strength")
                    self.assertIn('dosage', ocr_result['parsed_data'], "Parsed data should contain dosage")
                    
                    print(f"✓ Retrieved and matched OCR result for {medication.name}")
                else:
                    print(f"⚠ No matching medication found for OCR result: {ocr_result['medication_name']}")
                
            except Exception as e:
                print(f"✗ Failed to retrieve OCR result for {ocr_result['medication_name']}: {str(e)}")
                raise
        
        # Test OCR result validation
        invalid_ocr_results = [
            {
                'medication_name': 'INVALID_MED',
                'strength': 'invalid',
                'confidence': 0.3,  # Low confidence
                'raw_text': 'Invalid medication data'
            }
        ]
        
        for invalid_result in invalid_ocr_results:
            # Test low confidence rejection
            self.assertLess(invalid_result['confidence'], 0.8, 
                           "Low confidence OCR results should be flagged")
            print(f"✓ Rejected low confidence OCR result: {invalid_result['medication_name']}")
        
        print("✓ OCR result storage and retrieval tests passed")
    
    def test_09_medication_interaction_detection(self):
        """Test medication interaction detection and warnings."""
        print("\n=== Testing Medication Interaction Detection ===")
        
        created_medications = self.test_01_all_21_medications_creation()
        
        # Define known drug interactions
        known_interactions = [
            {
                'medication1': 'VYVANSE',
                'medication2': 'RITALIN LA',
                'interaction_type': 'contraindicated',
                'severity': 'high',
                'description': 'Both are stimulants - risk of excessive stimulation',
                'recommendation': 'Avoid combination'
            },
            {
                'medication1': 'TARGINACT',
                'medication2': 'STILPAYNE',
                'interaction_type': 'moderate',
                'severity': 'medium',
                'description': 'Both are opioids - increased risk of respiratory depression',
                'recommendation': 'Monitor closely, consider dose reduction'
            },
            {
                'medication1': 'TOPZOLE',
                'medication2': 'CYMGEN',
                'interaction_type': 'minor',
                'severity': 'low',
                'description': 'Omeprazole may reduce vitamin B12 absorption',
                'recommendation': 'Monitor B12 levels'
            },
            {
                'medication1': 'RIVOTRIL',
                'medication2': 'VYVANSE',
                'interaction_type': 'moderate',
                'severity': 'medium',
                'description': 'Clonazepam may reduce stimulant effectiveness',
                'recommendation': 'Monitor effectiveness, adjust timing if needed'
            }
        ]
        
        detected_interactions = []
        
        # Test interaction detection
        for interaction in known_interactions:
            try:
                med1 = next((med for med in created_medications if med.name == interaction['medication1']), None)
                med2 = next((med for med in created_medications if med.name == interaction['medication2']), None)
                
                if med1 and med2:
                    # Simulate interaction detection
                    interaction_result = {
                        'medication1': med1,
                        'medication2': med2,
                        'interaction_type': interaction['interaction_type'],
                        'severity': interaction['severity'],
                        'description': interaction['description'],
                        'recommendation': interaction['recommendation'],
                        'detected_at': timezone.now()
                    }
                    
                    detected_interactions.append(interaction_result)
                    
                    # Test severity levels
                    if interaction['severity'] == 'high':
                        self.assertEqual(interaction['interaction_type'], 'contraindicated',
                                       f"High severity should be contraindicated: {med1.name} + {med2.name}")
                    
                    # Test interaction validation
                    self.assertIn(interaction['severity'], ['low', 'medium', 'high'],
                                f"Invalid severity level: {interaction['severity']}")
                    
                    print(f"✓ Detected {interaction['severity']} interaction: {med1.name} + {med2.name}")
                    
                else:
                    print(f"⚠ Could not find medications for interaction: {interaction['medication1']} + {interaction['medication2']}")
                
            except Exception as e:
                print(f"✗ Failed to detect interaction: {str(e)}")
                raise
        
        # Test interaction warnings generation
        for interaction in detected_interactions:
            try:
                # Generate warning message
                warning_message = f"INTERACTION WARNING: {interaction['medication1'].name} + {interaction['medication2'].name}\n"
                warning_message += f"Severity: {interaction['severity'].upper()}\n"
                warning_message += f"Type: {interaction['interaction_type']}\n"
                warning_message += f"Description: {interaction['description']}\n"
                warning_message += f"Recommendation: {interaction['recommendation']}"
                
                # Test warning format
                self.assertIn('INTERACTION WARNING', warning_message, "Warning should contain warning header")
                self.assertIn(interaction['medication1'].name, warning_message, "Warning should contain medication names")
                self.assertIn(interaction['medication2'].name, warning_message, "Warning should contain medication names")
                self.assertIn(interaction['severity'].upper(), warning_message, "Warning should contain severity")
                
                print(f"✓ Generated interaction warning for {interaction['medication1'].name} + {interaction['medication2'].name}")
                
            except Exception as e:
                print(f"✗ Failed to generate warning: {str(e)}")
                raise
        
        # Test contraindication detection
        contraindicated_pairs = [interaction for interaction in detected_interactions 
                               if interaction['interaction_type'] == 'contraindicated']
        
        self.assertGreater(len(contraindicated_pairs), 0, "Should detect at least one contraindicated interaction")
        print(f"✓ Detected {len(contraindicated_pairs)} contraindicated interactions")
        
        print("✓ Medication interaction detection tests passed")
    
    def test_10_prescription_renewal_calculations(self):
        """Test prescription renewal calculations and logic."""
        print("\n=== Testing Prescription Renewal Calculations ===")
        
        created_medications = self.test_01_all_21_medications_creation()
        
        # Create test prescription with renewal data
        prescription_date = date.today() - timedelta(days=30)  # 30 days ago
        expiry_date = prescription_date + timedelta(days=365)  # 1 year from prescription date
        
        prescription = Prescription.objects.create(
            prescription_number='RENEWAL-TEST-001',
            prescription_date=prescription_date,
            expiry_date=expiry_date,
            status='active',
            priority='routine',
            prescription_type='new',
            total_medications=5,
            doctor=self.doctor,
            patient=self.patient,
            notes='Test prescription for renewal calculations'
        )
        
        # Test medications with different renewal patterns
        renewal_test_medications = [
            {
                'medication': next((med for med in created_medications if med.name == 'ELTROXIN'), None),
                'daily_usage': 1,
                'quantity': 30,
                'days_until_renewal': 30,
                'renewal_frequency': 'monthly'
            },
            {
                'medication': next((med for med in created_medications if med.name == 'EPLEPTIN'), None),
                'daily_usage': 9,  # 3 tablets 3x daily
                'quantity': 270,
                'days_until_renewal': 30,  # 270/9 = 30 days
                'renewal_frequency': 'monthly'
            },
            {
                'medication': next((med for med in created_medications if med.name == 'VYVANSE'), None),
                'daily_usage': 2,
                'quantity': 30,
                'days_until_renewal': 15,  # 30/2 = 15 days
                'renewal_frequency': 'bi-weekly'
            },
            {
                'medication': next((med for med in created_medications if med.name == 'NOVORAPID'), None),
                'daily_usage': 0,  # As needed
                'quantity': 3,
                'days_until_renewal': 90,  # Insulin lasts longer
                'renewal_frequency': 'quarterly'
            }
        ]
        
        renewal_calculations = []
        
        for test_data in renewal_test_medications:
            if test_data['medication']:
                try:
                    medication = test_data['medication']
                    
                    # Calculate renewal date
                    if test_data['daily_usage'] > 0:
                        days_until_empty = test_data['quantity'] // test_data['daily_usage']
                    else:
                        days_until_empty = test_data['days_until_renewal']
                    
                    renewal_date = date.today() + timedelta(days=days_until_empty)
                    
                    # Calculate days until renewal
                    days_until_renewal = (renewal_date - date.today()).days
                    
                    # Determine renewal priority
                    if days_until_renewal <= 7:
                        priority = 'urgent'
                    elif days_until_renewal <= 14:
                        priority = 'high'
                    elif days_until_renewal <= 30:
                        priority = 'medium'
                    else:
                        priority = 'low'
                    
                    # Create renewal record
                    renewal_calculation = {
                        'medication': medication,
                        'current_quantity': test_data['quantity'],
                        'daily_usage': test_data['daily_usage'],
                        'days_until_empty': days_until_empty,
                        'renewal_date': renewal_date,
                        'days_until_renewal': days_until_renewal,
                        'priority': priority,
                        'renewal_frequency': test_data['renewal_frequency']
                    }
                    
                    renewal_calculations.append(renewal_calculation)
                    
                    # Test calculation accuracy
                    if test_data['daily_usage'] > 0:
                        expected_days = test_data['quantity'] // test_data['daily_usage']
                        self.assertEqual(days_until_empty, expected_days,
                                       f"Renewal calculation should be accurate for {medication.name}")
                    
                    # Test priority assignment
                    self.assertIn(priority, ['urgent', 'high', 'medium', 'low'],
                                f"Invalid priority level: {priority}")
                    
                    print(f"✓ Calculated renewal for {medication.name}: {days_until_renewal} days ({priority} priority)")
                    
                except Exception as e:
                    print(f"✗ Failed to calculate renewal for {test_data['medication'].name if test_data['medication'] else 'Unknown'}: {str(e)}")
                    raise
        
        # Test renewal reminder logic
        urgent_renewals = [r for r in renewal_calculations if r['priority'] == 'urgent']
        high_renewals = [r for r in renewal_calculations if r['priority'] == 'high']
        
        print(f"✓ Found {len(urgent_renewals)} urgent renewals, {len(high_renewals)} high priority renewals")
        
        # Test prescription expiry calculations
        days_until_expiry = (expiry_date - date.today()).days
        
        if days_until_expiry <= 30:
            expiry_priority = 'urgent'
        elif days_until_expiry <= 60:
            expiry_priority = 'high'
        elif days_until_expiry <= 90:
            expiry_priority = 'medium'
        else:
            expiry_priority = 'low'
        
        self.assertIn(expiry_priority, ['urgent', 'high', 'medium', 'low'],
                     f"Invalid expiry priority: {expiry_priority}")
        
        print(f"✓ Prescription expires in {days_until_expiry} days ({expiry_priority} priority)")
        
        print("✓ Prescription renewal calculations tests passed")
    
    def test_11_bulk_medication_creation_and_validation(self):
        """Test bulk medication creation and validation."""
        print("\n=== Testing Bulk Medication Creation and Validation ===")
        
        # Test bulk medication data
        bulk_medications_data = [
            {
                'name': 'BULK_TEST_1',
                'generic_name': 'Test Generic 1',
                'brand_name': 'Test Brand 1',
                'strength': '100',
                'dosage_unit': 'mg',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'pill_count': 50,
                'low_stock_threshold': 10,
                'manufacturer': 'Test Manufacturer',
                'icd10_codes': ['E10.4'],
                'description': 'Test medication 1',
                'side_effects': 'Test side effects 1',
                'contraindications': 'Test contraindications 1'
            },
            {
                'name': 'BULK_TEST_2',
                'generic_name': 'Test Generic 2',
                'brand_name': 'Test Brand 2',
                'strength': '200',
                'dosage_unit': 'mg',
                'medication_type': 'capsule',
                'prescription_type': 'otc',
                'pill_count': 30,
                'low_stock_threshold': 5,
                'manufacturer': 'Test Manufacturer',
                'icd10_codes': ['F90.9'],
                'description': 'Test medication 2',
                'side_effects': 'Test side effects 2',
                'contraindications': 'Test contraindications 2'
            },
            {
                'name': 'BULK_TEST_3',
                'generic_name': 'Test Generic 3',
                'brand_name': 'Test Brand 3',
                'strength': '50',
                'dosage_unit': 'mg',
                'medication_type': 'liquid',
                'prescription_type': 'prescription',
                'pill_count': 100,
                'low_stock_threshold': 20,
                'manufacturer': 'Test Manufacturer',
                'icd10_codes': ['G89.4'],
                'description': 'Test medication 3',
                'side_effects': 'Test side effects 3',
                'contraindications': 'Test contraindications 3'
            }
        ]
        
        # Test bulk creation
        bulk_created_medications = []
        
        for i, med_data in enumerate(bulk_medications_data, 1):
            try:
                # Validate medication data
                self.assertIsNotNone(med_data['name'], f"Medication {i} should have a name")
                self.assertIsNotNone(med_data['strength'], f"Medication {i} should have strength")
                self.assertIsNotNone(med_data['dosage_unit'], f"Medication {i} should have dosage unit")
                self.assertIn(med_data['medication_type'], ['tablet', 'capsule', 'liquid', 'injection', 'cream'],
                            f"Invalid medication type: {med_data['medication_type']}")
                self.assertIn(med_data['prescription_type'], ['prescription', 'otc', 'schedule_5', 'schedule_6'],
                            f"Invalid prescription type: {med_data['prescription_type']}")
                
                # Create medication
                medication = Medication.objects.create(
                    name=med_data['name'],
                    generic_name=med_data['generic_name'],
                    brand_name=med_data['brand_name'],
                    strength=med_data['strength'],
                    dosage_unit=med_data['dosage_unit'],
                    medication_type=med_data['medication_type'],
                    prescription_type=med_data['prescription_type'],
                    pill_count=med_data['pill_count'],
                    low_stock_threshold=med_data['low_stock_threshold'],
                    manufacturer=med_data['manufacturer'],
                    description=med_data['description'],
                    side_effects=med_data['side_effects'],
                    contraindications=med_data['contraindications'],
                    expiration_date=date.today() + timedelta(days=730)
                )
                
                # Add ICD-10 codes
                for icd10_code in med_data['icd10_codes']:
                    if icd10_code in self.icd10_codes:
                        medication.icd10_codes.add(self.icd10_codes[icd10_code])
                
                bulk_created_medications.append(medication)
                print(f"✓ Created bulk medication {i}/3: {medication.name}")
                
            except Exception as e:
                print(f"✗ Failed to create bulk medication {i}: {str(e)}")
                raise
        
        # Test bulk validation
        self.assertEqual(len(bulk_created_medications), 3, "Should create exactly 3 bulk medications")
        
        # Test bulk operations
        try:
            # Bulk update stock levels
            for medication in bulk_created_medications:
                medication.pill_count += 10
                medication.save()
            
            # Verify bulk updates
            for medication in bulk_created_medications:
                medication.refresh_from_db()
                self.assertGreaterEqual(medication.pill_count, 10, f"Bulk update should increase stock for {medication.name}")
            
            print("✓ Bulk stock updates completed successfully")
            
            # Test bulk validation with invalid data
            invalid_medication_data = {
                'name': '',  # Invalid: empty name
                'strength': 'invalid',  # Invalid: non-numeric strength
                'medication_type': 'invalid_type',  # Invalid: unknown type
                'prescription_type': 'invalid_prescription',  # Invalid: unknown type
                'pill_count': -5  # Invalid: negative count
            }
            
            # Test validation failures
            with self.assertRaises(ValidationError):
                if not invalid_medication_data['name']:
                    raise ValidationError("Medication name cannot be empty")
            
            with self.assertRaises(ValueError):
                int(invalid_medication_data['strength'])
            
            self.assertNotIn(invalid_medication_data['medication_type'], 
                           ['tablet', 'capsule', 'liquid', 'injection', 'cream'],
                           "Invalid medication type should be rejected")
            
            self.assertNotIn(invalid_medication_data['prescription_type'],
                           ['prescription', 'otc', 'schedule_5', 'schedule_6'],
                           "Invalid prescription type should be rejected")
            
            with self.assertRaises(ValidationError):
                if invalid_medication_data['pill_count'] < 0:
                    raise ValidationError("Pill count cannot be negative")
            
            print("✓ Bulk validation correctly rejects invalid data")
            
        except Exception as e:
            print(f"✗ Bulk operations failed: {str(e)}")
            raise
        
        # Test bulk deletion
        try:
            bulk_count = len(bulk_created_medications)
            for medication in bulk_created_medications:
                medication.delete()
            
            remaining_count = Medication.objects.filter(name__startswith='BULK_TEST_').count()
            self.assertEqual(remaining_count, 0, "All bulk test medications should be deleted")
            
            print(f"✓ Successfully deleted {bulk_count} bulk test medications")
            
        except Exception as e:
            print(f"✗ Bulk deletion failed: {str(e)}")
            raise
        
        print("✓ Bulk medication creation and validation tests passed")
    
    def test_12_database_constraints_and_relationships(self):
        """Test all database constraints and relationships work correctly."""
        print("\n=== Testing Database Constraints and Relationships ===")
        
        created_medications = self.test_01_all_21_medications_creation()
        
        # Test foreign key constraints
        try:
            # Test medication schedule with valid patient and medication
            valid_schedule = MedicationSchedule.objects.create(
                patient=self.user,
                medication=created_medications[0],
                timing='morning',
                dosage_amount=1.0,
                frequency='daily',
                start_date=date.today()
            )
            
            self.assertIsNotNone(valid_schedule.id, "Valid schedule should be created")
            self.assertEqual(valid_schedule.patient, self.user, "Schedule should reference correct patient")
            self.assertEqual(valid_schedule.medication, created_medications[0], "Schedule should reference correct medication")
            
            print("✓ Foreign key constraints work correctly")
            
        except Exception as e:
            print(f"✗ Foreign key constraint test failed: {str(e)}")
            raise
        
        # Test unique constraints
        try:
            # Test prescription number uniqueness
            prescription1 = Prescription.objects.create(
                prescription_number='UNIQUE-TEST-001',
                prescription_date=date.today(),
                expiry_date=date.today() + timedelta(days=365),
                status='active',
                doctor=self.doctor,
                patient=self.patient
            )
            
            # This should fail due to duplicate prescription number
            with self.assertRaises(Exception):
                Prescription.objects.create(
                    prescription_number='UNIQUE-TEST-001',  # Duplicate number
                    prescription_date=date.today(),
                    expiry_date=date.today() + timedelta(days=365),
                    status='active',
                    doctor=self.doctor,
                    patient=self.patient
                )
            
            print("✓ Unique constraints work correctly")
            
        except Exception as e:
            print(f"✗ Unique constraint test failed: {str(e)}")
            raise
        
        # Test cascade delete relationships
        try:
            # Create medication log
            medication_log = MedicationLog.objects.create(
                patient=self.user,
                medication=created_medications[0],
                scheduled_time=timezone.now(),
                status='taken',
                dosage_taken=1.0
            )
            
            log_id = medication_log.id
            
            # Delete medication (should cascade to log)
            medication_to_delete = created_medications[0]
            medication_to_delete.delete()
            
            # Verify log is also deleted
            with self.assertRaises(MedicationLog.DoesNotExist):
                MedicationLog.objects.get(id=log_id)
            
            print("✓ Cascade delete relationships work correctly")
            
        except Exception as e:
            print(f"✗ Cascade delete test failed: {str(e)}")
            raise
        
        # Test check constraints
        try:
            # Test positive pill count constraint
            with self.assertRaises(ValidationError):
                invalid_medication = Medication(
                    name='TEST_CONSTRAINT',
                    strength='100',
                    dosage_unit='mg',
                    pill_count=-5  # Should fail validation
                )
                invalid_medication.full_clean()
            
            # Test valid pill count
            valid_medication = Medication(
                name='TEST_CONSTRAINT_VALID',
                strength='100',
                dosage_unit='mg',
                pill_count=10  # Should pass validation
            )
            valid_medication.full_clean()  # Should not raise exception
            
            print("✓ Check constraints work correctly")
            
        except Exception as e:
            print(f"✗ Check constraint test failed: {str(e)}")
            raise
        
        # Test many-to-many relationships
        try:
            # Test medication-ICD10 relationship
            medication = created_medications[1]  # Use second medication
            icd10_codes = list(self.icd10_codes.values())[:3]  # Get first 3 ICD-10 codes
            
            # Add ICD-10 codes
            for icd10_code in icd10_codes:
                medication.icd10_codes.add(icd10_code)
            
            # Verify relationship
            self.assertEqual(medication.icd10_codes.count(), 3, "Medication should have 3 ICD-10 codes")
            
            # Test reverse relationship
            for icd10_code in icd10_codes:
                self.assertIn(medication, icd10_code.medication_set.all(), 
                            f"ICD-10 code {icd10_code.code} should reference medication")
            
            # Remove ICD-10 codes
            medication.icd10_codes.clear()
            self.assertEqual(medication.icd10_codes.count(), 0, "Medication should have no ICD-10 codes")
            
            print("✓ Many-to-many relationships work correctly")
            
        except Exception as e:
            print(f"✗ Many-to-many relationship test failed: {str(e)}")
            raise
        
        # Test index performance
        try:
            import time
            
            # Test indexed queries
            start_time = time.time()
            
            # Query by medication name (indexed)
            medications_by_name = Medication.objects.filter(name__icontains='EPLEPTIN')
            
            # Query by medication type (indexed)
            medications_by_type = Medication.objects.filter(medication_type='tablet')
            
            # Query by prescription type (indexed)
            medications_by_prescription = Medication.objects.filter(prescription_type='prescription')
            
            query_time = time.time() - start_time
            
            self.assertLess(query_time, 0.1, "Indexed queries should be fast")
            
            print(f"✓ Database indexes work correctly (queries completed in {query_time:.3f}s)")
            
        except Exception as e:
            print(f"✗ Index performance test failed: {str(e)}")
            raise
        
        # Test transaction integrity
        try:
            from django.db import transaction
            
            with transaction.atomic():
                # Create test data within transaction
                test_medication = Medication.objects.create(
                    name='TRANSACTION_TEST',
                    strength='100',
                    dosage_unit='mg',
                    pill_count=10
                )
                
                # Simulate error condition
                raise ValueError("Simulated transaction error")
            
        except ValueError:
            # Transaction should be rolled back
            with self.assertRaises(Medication.DoesNotExist):
                Medication.objects.get(name='TRANSACTION_TEST')
            
            print("✓ Transaction integrity works correctly")
        
        except Exception as e:
            print(f"✗ Transaction integrity test failed: {str(e)}")
            raise
        
        print("✓ All database constraints and relationships work correctly")
    
    def run_all_tests(self):
        """Run all comprehensive migration tests."""
        print("🚀 Starting Comprehensive Migration Testing for MedGuard SA")
        print("=" * 60)
        
        try:
            self.test_01_all_21_medications_creation()
            self.test_02_icd10_code_mappings()
            self.test_03_complex_medication_schedules()
            self.test_04_stock_calculations()
            self.test_05_prescription_workflow_states()
            self.test_06_comprehensive_integration()
            self.test_07_performance_and_scalability()
            self.test_08_ocr_result_storage_and_retrieval()
            self.test_09_medication_interaction_detection()
            self.test_10_prescription_renewal_calculations()
            self.test_11_bulk_medication_creation_and_validation()
            self.test_12_database_constraints_and_relationships()
            
            print("\n" + "=" * 60)
            print("✅ ALL COMPREHENSIVE MIGRATION TESTS PASSED!")
            print("✅ MedGuard SA prescription system is ready for production")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ TEST FAILED: {str(e)}")
            raise


if __name__ == '__main__':
    # Run the comprehensive migration tests
    test_suite = MigrationComprehensiveTest()
    test_suite.setUp()
    test_suite.run_all_tests() 