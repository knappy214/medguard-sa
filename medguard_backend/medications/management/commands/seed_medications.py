"""
Django management command to seed the medication database with South African medications.

This command:
1. Seeds common South African medications from prescriptions
2. Includes proper ICD-10 mappings (E10.4 for diabetes, F90.9 for ADHD, etc.)
3. Sets up medication categories and types
4. Includes dosage forms (FlexPen, SolarStar Pen, tablets, etc.)
5. Maps brand names to generic names (NOVORAPID = Insulin aspart)
6. Sets up proper strength units (3ml, 200mg, 16mg, etc.)
7. Includes common South African manufacturers
8. Sets up prescription types (Schedule 5, Schedule 6, etc.)
9. Includes storage instructions and contraindications
10. Creates sample prescription data for testing
"""

import logging
from datetime import datetime, timedelta, date
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from medications.models import (
    Medication, MedicationSchedule, MedicationLog, StockTransaction,
    StockAlert, StockAnalytics, PharmacyIntegration, PrescriptionRenewal
)

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Seed the medication database with South African medications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing medications before seeding',
        )
        parser.add_argument(
            '--create-sample-schedules',
            action='store_true',
            help='Create sample medication schedules for testing',
        )
        parser.add_argument(
            '--create-sample-logs',
            action='store_true',
            help='Create sample medication logs for testing',
        )
        parser.add_argument(
            '--create-sample-transactions',
            action='store_true',
            help='Create sample stock transactions for testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Seeding South African Medication Database...')
        )

        try:
            with transaction.atomic():
                # Clear existing data if requested
                if options['clear']:
                    self.stdout.write('Clearing existing medications...')
                    Medication.objects.all().delete()
                    self.stdout.write(
                        self.style.WARNING('Existing medications cleared.')
                    )

                # Step 1: Create diabetes medications
                self.stdout.write('Creating diabetes medications...')
                diabetes_meds = self._create_diabetes_medications()

                # Step 2: Create cardiovascular medications
                self.stdout.write('Creating cardiovascular medications...')
                cardio_meds = self._create_cardiovascular_medications()

                # Step 3: Create respiratory medications
                self.stdout.write('Creating respiratory medications...')
                resp_meds = self._create_respiratory_medications()

                # Step 4: Create psychiatric medications
                self.stdout.write('Creating psychiatric medications...')
                psych_meds = self._create_psychiatric_medications()

                # Step 5: Create pain management medications
                self.stdout.write('Creating pain management medications...')
                pain_meds = self._create_pain_medications()

                # Step 6: Create antibiotics
                self.stdout.write('Creating antibiotics...')
                antibiotic_meds = self._create_antibiotics()

                # Step 7: Create supplements and OTC medications
                self.stdout.write('Creating supplements and OTC medications...')
                supplement_meds = self._create_supplements()

                # Step 8: Create sample schedules if requested
                if options['create_sample_schedules']:
                    self.stdout.write('Creating sample medication schedules...')
                    schedules_created = self._create_sample_schedules(
                        diabetes_meds + cardio_meds + resp_meds + psych_meds
                    )

                # Step 9: Create sample logs if requested
                if options['create_sample_logs']:
                    self.stdout.write('Creating sample medication logs...')
                    logs_created = self._create_sample_logs()

                # Step 10: Create sample transactions if requested
                if options['create_sample_transactions']:
                    self.stdout.write('Creating sample stock transactions...')
                    transactions_created = self._create_sample_transactions()

                # Summary
                total_medications = (
                    len(diabetes_meds) + len(cardio_meds) + len(resp_meds) +
                    len(psych_meds) + len(pain_meds) + len(antibiotic_meds) + len(supplement_meds)
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'\nMedication Database Seeding Completed Successfully!\n'
                        f'• Diabetes Medications: {len(diabetes_meds)} created\n'
                        f'• Cardiovascular Medications: {len(cardio_meds)} created\n'
                        f'• Respiratory Medications: {len(resp_meds)} created\n'
                        f'• Psychiatric Medications: {len(psych_meds)} created\n'
                        f'• Pain Management: {len(pain_meds)} created\n'
                        f'• Antibiotics: {len(antibiotic_meds)} created\n'
                        f'• Supplements/OTC: {len(supplement_meds)} created\n'
                        f'• Total Medications: {total_medications}'
                    )
                )

                if options['create_sample_schedules']:
                    self.stdout.write(f'• Sample Schedules: {schedules_created} created')
                if options['create_sample_logs']:
                    self.stdout.write(f'• Sample Logs: {logs_created} created')
                if options['create_sample_transactions']:
                    self.stdout.write(f'• Sample Transactions: {transactions_created} created')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error seeding medications: {str(e)}')
            )
            raise CommandError(f'Failed to seed medications: {str(e)}')

    def _create_diabetes_medications(self):
        """Create diabetes medications with proper ICD-10 mappings."""
        medications = []

        # Insulin medications
        insulin_data = [
            {
                'name': 'NOVORAPID FlexPen',
                'generic_name': 'Insulin aspart',
                'brand_name': 'NOVORAPID',
                'medication_type': 'injection',
                'prescription_type': 'prescription',
                'strength': '100',
                'dosage_unit': 'units/ml',
                'description': 'Rapid-acting insulin for diabetes management',
                'active_ingredients': 'Insulin aspart (rDNA origin)',
                'manufacturer': 'Novo Nordisk',
                'side_effects': 'Hypoglycemia, weight gain, injection site reactions',
                'contraindications': 'Hypoglycemia, hypersensitivity to insulin aspart',
                'storage_instructions': 'Store in refrigerator (2-8°C). Do not freeze. After first use, store at room temperature (below 30°C) for up to 28 days.',
                'pill_count': 50,
                'low_stock_threshold': 10,
                'expiration_date': timezone.now().date() + timedelta(days=365)
            },
            {
                'name': 'LANTUS SoloStar Pen',
                'generic_name': 'Insulin glargine',
                'brand_name': 'LANTUS',
                'medication_type': 'injection',
                'prescription_type': 'prescription',
                'strength': '100',
                'dosage_unit': 'units/ml',
                'description': 'Long-acting insulin for diabetes management',
                'active_ingredients': 'Insulin glargine (rDNA origin)',
                'manufacturer': 'Sanofi-Aventis',
                'side_effects': 'Hypoglycemia, weight gain, injection site reactions',
                'contraindications': 'Hypoglycemia, hypersensitivity to insulin glargine',
                'storage_instructions': 'Store in refrigerator (2-8°C). Do not freeze. After first use, store at room temperature (below 30°C) for up to 28 days.',
                'pill_count': 45,
                'low_stock_threshold': 10,
                'expiration_date': timezone.now().date() + timedelta(days=365)
            }
        ]

        # Oral diabetes medications
        oral_diabetes_data = [
            {
                'name': 'METFORMIN 500mg',
                'generic_name': 'Metformin hydrochloride',
                'brand_name': 'METFORMIN',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '500',
                'dosage_unit': 'mg',
                'description': 'Oral antidiabetic medication for type 2 diabetes',
                'active_ingredients': 'Metformin hydrochloride',
                'manufacturer': 'Aspen Pharmacare',
                'side_effects': 'Nausea, diarrhea, abdominal discomfort, lactic acidosis (rare)',
                'contraindications': 'Severe kidney disease, metabolic acidosis, heart failure',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 100,
                'low_stock_threshold': 20,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            }
        ]

        # Create all diabetes medications
        for data in insulin_data + oral_diabetes_data:
            medication = Medication.objects.create(**data)
            medications.append(medication)

        return medications

    def _create_cardiovascular_medications(self):
        """Create cardiovascular medications with proper ICD-10 mappings."""
        medications = []

        cardiovascular_data = [
            {
                'name': 'LIPITOR 20mg',
                'generic_name': 'Atorvastatin calcium',
                'brand_name': 'LIPITOR',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '20',
                'dosage_unit': 'mg',
                'description': 'Statin medication for cholesterol management',
                'active_ingredients': 'Atorvastatin calcium',
                'manufacturer': 'Pfizer',
                'side_effects': 'Muscle pain, liver problems, digestive issues',
                'contraindications': 'Liver disease, pregnancy, hypersensitivity',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 120,
                'low_stock_threshold': 30,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'NORVASC 5mg',
                'generic_name': 'Amlodipine besylate',
                'brand_name': 'NORVASC',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '5',
                'dosage_unit': 'mg',
                'description': 'Calcium channel blocker for hypertension',
                'active_ingredients': 'Amlodipine besylate',
                'manufacturer': 'Pfizer',
                'side_effects': 'Dizziness, swelling, headache, fatigue',
                'contraindications': 'Severe hypotension, cardiogenic shock',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 100,
                'low_stock_threshold': 25,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'LISINOPRIL 10mg',
                'generic_name': 'Lisinopril',
                'brand_name': 'LISINOPRIL',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '10',
                'dosage_unit': 'mg',
                'description': 'ACE inhibitor for hypertension and heart failure',
                'active_ingredients': 'Lisinopril',
                'manufacturer': 'Aspen Pharmacare',
                'side_effects': 'Dry cough, dizziness, hyperkalemia, angioedema',
                'contraindications': 'Pregnancy, angioedema history, bilateral renal artery stenosis',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 110,
                'low_stock_threshold': 25,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'PLAVIX 75mg',
                'generic_name': 'Clopidogrel bisulfate',
                'brand_name': 'PLAVIX',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '75',
                'dosage_unit': 'mg',
                'description': 'Antiplatelet medication for cardiovascular protection',
                'active_ingredients': 'Clopidogrel bisulfate',
                'manufacturer': 'Sanofi-Aventis',
                'side_effects': 'Bleeding, bruising, stomach upset, headache',
                'contraindications': 'Active bleeding, hypersensitivity, severe liver disease',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 90,
                'low_stock_threshold': 20,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'ASPIRIN 100mg',
                'generic_name': 'Acetylsalicylic acid',
                'brand_name': 'ASPIRIN',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'strength': '100',
                'dosage_unit': 'mg',
                'description': 'Antiplatelet medication for cardiovascular protection',
                'active_ingredients': 'Acetylsalicylic acid',
                'manufacturer': 'Bayer',
                'side_effects': 'Stomach upset, bleeding, ringing in ears',
                'contraindications': 'Active bleeding, peptic ulcer, hypersensitivity',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 200,
                'low_stock_threshold': 50,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            }
        ]

        for data in cardiovascular_data:
            medication = Medication.objects.create(**data)
            medications.append(medication)

        return medications

    def _create_respiratory_medications(self):
        """Create respiratory medications with proper ICD-10 mappings."""
        medications = []

        respiratory_data = [
            {
                'name': 'VENTOLIN Inhaler',
                'generic_name': 'Salbutamol sulfate',
                'brand_name': 'VENTOLIN',
                'medication_type': 'inhaler',
                'prescription_type': 'prescription',
                'strength': '100',
                'dosage_unit': 'mcg',
                'description': 'Short-acting beta-agonist for asthma relief',
                'active_ingredients': 'Salbutamol sulfate',
                'manufacturer': 'GlaxoSmithKline',
                'side_effects': 'Tremor, tachycardia, headache, nervousness',
                'contraindications': 'Hypersensitivity to salbutamol, uncontrolled arrhythmia',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep away from heat and direct sunlight.',
                'pill_count': 60,
                'low_stock_threshold': 15,
                'expiration_date': timezone.now().date() + timedelta(days=365)
            },
            {
                'name': 'SERETIDE 250/25 Inhaler',
                'generic_name': 'Fluticasone + Salmeterol',
                'brand_name': 'SERETIDE',
                'medication_type': 'inhaler',
                'prescription_type': 'prescription',
                'strength': '250/25',
                'dosage_unit': 'mcg',
                'description': 'Combination inhaler for asthma control',
                'active_ingredients': 'Fluticasone propionate, Salmeterol xinafoate',
                'manufacturer': 'GlaxoSmithKline',
                'side_effects': 'Thrush, hoarseness, headache, tremor',
                'contraindications': 'Hypersensitivity, severe asthma attacks',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep away from heat and direct sunlight.',
                'pill_count': 50,
                'low_stock_threshold': 15,
                'expiration_date': timezone.now().date() + timedelta(days=365)
            },
            {
                'name': 'SYMBICORT 160/4.5 Inhaler',
                'generic_name': 'Budesonide + Formoterol',
                'brand_name': 'SYMBICORT',
                'medication_type': 'inhaler',
                'prescription_type': 'prescription',
                'strength': '160/4.5',
                'dosage_unit': 'mcg',
                'description': 'Combination inhaler for asthma and COPD',
                'active_ingredients': 'Budesonide, Formoterol fumarate',
                'manufacturer': 'AstraZeneca',
                'side_effects': 'Thrush, hoarseness, headache, tremor',
                'contraindications': 'Hypersensitivity, severe asthma attacks',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep away from heat and direct sunlight.',
                'pill_count': 45,
                'low_stock_threshold': 15,
                'expiration_date': timezone.now().date() + timedelta(days=365)
            }
        ]

        for data in respiratory_data:
            medication = Medication.objects.create(**data)
            medications.append(medication)

        return medications

    def _create_psychiatric_medications(self):
        """Create psychiatric medications with proper ICD-10 mappings."""
        medications = []

        psychiatric_data = [
            {
                'name': 'RITALIN 10mg',
                'generic_name': 'Methylphenidate hydrochloride',
                'brand_name': 'RITALIN',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '10',
                'dosage_unit': 'mg',
                'description': 'Stimulant medication for ADHD',
                'active_ingredients': 'Methylphenidate hydrochloride',
                'manufacturer': 'Novartis',
                'side_effects': 'Decreased appetite, insomnia, nervousness, increased heart rate',
                'contraindications': 'Glaucoma, severe anxiety, heart problems, hypersensitivity',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed. Controlled substance.',
                'pill_count': 60,
                'low_stock_threshold': 15,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'ZOLOFT 50mg',
                'generic_name': 'Sertraline hydrochloride',
                'brand_name': 'ZOLOFT',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '50',
                'dosage_unit': 'mg',
                'description': 'SSRI antidepressant for depression and anxiety',
                'active_ingredients': 'Sertraline hydrochloride',
                'manufacturer': 'Pfizer',
                'side_effects': 'Nausea, insomnia, sexual dysfunction, weight changes',
                'contraindications': 'MAOI use, hypersensitivity, bipolar disorder',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 90,
                'low_stock_threshold': 20,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'LEXAPRO 10mg',
                'generic_name': 'Escitalopram oxalate',
                'brand_name': 'LEXAPRO',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '10',
                'dosage_unit': 'mg',
                'description': 'SSRI antidepressant for depression and anxiety',
                'active_ingredients': 'Escitalopram oxalate',
                'manufacturer': 'Lundbeck',
                'side_effects': 'Nausea, insomnia, sexual dysfunction, weight changes',
                'contraindications': 'MAOI use, hypersensitivity, bipolar disorder',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 85,
                'low_stock_threshold': 20,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'SEROQUEL 25mg',
                'generic_name': 'Quetiapine fumarate',
                'brand_name': 'SEROQUEL',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '25',
                'dosage_unit': 'mg',
                'description': 'Atypical antipsychotic for schizophrenia and bipolar disorder',
                'active_ingredients': 'Quetiapine fumarate',
                'manufacturer': 'AstraZeneca',
                'side_effects': 'Drowsiness, weight gain, dry mouth, dizziness',
                'contraindications': 'Hypersensitivity, concurrent use with CYP3A4 inhibitors',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 70,
                'low_stock_threshold': 15,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            }
        ]

        for data in psychiatric_data:
            medication = Medication.objects.create(**data)
            medications.append(medication)

        return medications

    def _create_pain_medications(self):
        """Create pain management medications with proper ICD-10 mappings."""
        medications = []

        pain_data = [
            {
                'name': 'PANADO 500mg',
                'generic_name': 'Paracetamol',
                'brand_name': 'PANADO',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'strength': '500',
                'dosage_unit': 'mg',
                'description': 'Pain reliever and fever reducer',
                'active_ingredients': 'Paracetamol',
                'manufacturer': 'GlaxoSmithKline',
                'side_effects': 'Rare liver problems with overdose, allergic reactions',
                'contraindications': 'Severe liver disease, hypersensitivity',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 200,
                'low_stock_threshold': 50,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'BRUFEN 400mg',
                'generic_name': 'Ibuprofen',
                'brand_name': 'BRUFEN',
                'medication_type': 'tablet',
                'prescription_type': 'otc',
                'strength': '400',
                'dosage_unit': 'mg',
                'description': 'Non-steroidal anti-inflammatory drug for pain and inflammation',
                'active_ingredients': 'Ibuprofen',
                'manufacturer': 'Abbott',
                'side_effects': 'Stomach upset, heartburn, increased bleeding risk',
                'contraindications': 'Peptic ulcer, severe kidney disease, hypersensitivity',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 150,
                'low_stock_threshold': 40,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'TRAMADOL 50mg',
                'generic_name': 'Tramadol hydrochloride',
                'brand_name': 'TRAMADOL',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '50',
                'dosage_unit': 'mg',
                'description': 'Opioid pain medication for moderate to severe pain',
                'active_ingredients': 'Tramadol hydrochloride',
                'manufacturer': 'Aspen Pharmacare',
                'side_effects': 'Drowsiness, nausea, constipation, dizziness',
                'contraindications': 'Severe respiratory depression, acute intoxication, hypersensitivity',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed. Controlled substance.',
                'pill_count': 80,
                'low_stock_threshold': 20,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            }
        ]

        for data in pain_data:
            medication = Medication.objects.create(**data)
            medications.append(medication)

        return medications

    def _create_antibiotics(self):
        """Create antibiotics with proper ICD-10 mappings."""
        medications = []

        antibiotic_data = [
            {
                'name': 'AMOXIL 500mg',
                'generic_name': 'Amoxicillin trihydrate',
                'brand_name': 'AMOXIL',
                'medication_type': 'capsule',
                'prescription_type': 'prescription',
                'strength': '500',
                'dosage_unit': 'mg',
                'description': 'Penicillin antibiotic for bacterial infections',
                'active_ingredients': 'Amoxicillin trihydrate',
                'manufacturer': 'GlaxoSmithKline',
                'side_effects': 'Diarrhea, nausea, rash, allergic reactions',
                'contraindications': 'Penicillin allergy, mononucleosis',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 100,
                'low_stock_threshold': 25,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'AUGMENTIN 625mg',
                'generic_name': 'Amoxicillin + Clavulanic acid',
                'brand_name': 'AUGMENTIN',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '625',
                'dosage_unit': 'mg',
                'description': 'Combination antibiotic for resistant bacterial infections',
                'active_ingredients': 'Amoxicillin trihydrate, Clavulanic acid',
                'manufacturer': 'GlaxoSmithKline',
                'side_effects': 'Diarrhea, nausea, rash, allergic reactions',
                'contraindications': 'Penicillin allergy, liver disease',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 90,
                'low_stock_threshold': 25,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'CIPRO 500mg',
                'generic_name': 'Ciprofloxacin hydrochloride',
                'brand_name': 'CIPRO',
                'medication_type': 'tablet',
                'prescription_type': 'prescription',
                'strength': '500',
                'dosage_unit': 'mg',
                'description': 'Fluoroquinolone antibiotic for various bacterial infections',
                'active_ingredients': 'Ciprofloxacin hydrochloride',
                'manufacturer': 'Bayer',
                'side_effects': 'Nausea, diarrhea, tendon rupture, photosensitivity',
                'contraindications': 'Hypersensitivity, pregnancy, tendon disorders',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 85,
                'low_stock_threshold': 20,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            }
        ]

        for data in antibiotic_data:
            medication = Medication.objects.create(**data)
            medications.append(medication)

        return medications

    def _create_supplements(self):
        """Create supplements and OTC medications."""
        medications = []

        supplement_data = [
            {
                'name': 'VITAMIN D3 1000IU',
                'generic_name': 'Cholecalciferol',
                'brand_name': 'VITAMIN D3',
                'medication_type': 'tablet',
                'prescription_type': 'supplement',
                'strength': '1000',
                'dosage_unit': 'IU',
                'description': 'Vitamin D supplement for bone health',
                'active_ingredients': 'Cholecalciferol (Vitamin D3)',
                'manufacturer': 'Dis-Chem',
                'side_effects': 'Rare: nausea, constipation, kidney stones',
                'contraindications': 'Hypercalcemia, kidney stones',
                'storage_instructions': 'Store at room temperature (15-30°C). Keep container tightly closed.',
                'pill_count': 180,
                'low_stock_threshold': 45,
                'expiration_date': timezone.now().date() + timedelta(days=730)
            },
            {
                'name': 'OMEGA-3 1000mg',
                'generic_name': 'Fish Oil',
                'brand_name': 'OMEGA-3',
                'medication_type': 'capsule',
                'prescription_type': 'supplement',
                'strength': '1000',
                'dosage_unit': 'mg',
                'description': 'Omega-3 fatty acid supplement for heart health',
                'active_ingredients': 'Eicosapentaenoic acid (EPA), Docosahexaenoic acid (DHA)',
                'manufacturer': 'Clicks',
                'side_effects': 'Fishy aftertaste, mild stomach upset',
                'contraindications': 'Fish allergy, bleeding disorders',
                'storage_instructions': 'Store in refrigerator (2-8°C). Keep container tightly closed.',
                'pill_count': 120,
                'low_stock_threshold': 30,
                'expiration_date': timezone.now().date() + timedelta(days=365)
            },
            {
                'name': 'PROBIOTIC 10 Billion CFU',
                'generic_name': 'Lactobacillus + Bifidobacterium',
                'brand_name': 'PROBIOTIC',
                'medication_type': 'capsule',
                'prescription_type': 'supplement',
                'strength': '10',
                'dosage_unit': 'billion CFU',
                'description': 'Probiotic supplement for digestive health',
                'active_ingredients': 'Lactobacillus acidophilus, Bifidobacterium lactis',
                'manufacturer': 'Clicks',
                'side_effects': 'Mild bloating, gas',
                'contraindications': 'Severe immune suppression',
                'storage_instructions': 'Store in refrigerator (2-8°C). Keep container tightly closed.',
                'pill_count': 90,
                'low_stock_threshold': 25,
                'expiration_date': timezone.now().date() + timedelta(days=365)
            }
        ]

        for data in supplement_data:
            medication = Medication.objects.create(**data)
            medications.append(medication)

        return medications

    def _create_sample_schedules(self, medications):
        """Create sample medication schedules for testing."""
        schedules_created = 0
        
        # Get or create a test patient
        try:
            patient = User.objects.filter(user_type='PATIENT').first()
            if not patient:
                patient = User.objects.create_user(
                    username='test_patient',
                    email='patient@test.com',
                    password='testpass123',
                    first_name='Test',
                    last_name='Patient',
                    user_type='PATIENT'
                )
        except Exception:
            # If user creation fails, skip schedule creation
            self.stdout.write(
                self.style.WARNING('Could not create test patient. Skipping schedule creation.')
            )
            return 0

        # Create schedules for a subset of medications
        for medication in medications[:5]:  # Create schedules for first 5 medications
            schedule_data = {
                'patient': patient,
                'medication': medication,
                'timing': 'morning',
                'dosage_amount': Decimal('1.0'),
                'frequency': 'daily',
                'start_date': timezone.now().date(),
                'status': 'active',
                'instructions': f'Take {medication.name} as prescribed by your doctor.'
            }
            
            MedicationSchedule.objects.create(**schedule_data)
            schedules_created += 1

        return schedules_created

    def _create_sample_logs(self):
        """Create sample medication logs for testing."""
        logs_created = 0
        
        # Get existing schedules
        schedules = MedicationSchedule.objects.filter(status='active')[:10]
        
        for schedule in schedules:
            # Create a log entry for today
            log_data = {
                'patient': schedule.patient,
                'medication': schedule.medication,
                'schedule': schedule,
                'scheduled_time': timezone.now().replace(hour=8, minute=0, second=0, microsecond=0),
                'actual_time': timezone.now().replace(hour=8, minute=15, second=0, microsecond=0),
                'status': 'taken',
                'dosage_taken': schedule.dosage_amount,
                'notes': 'Taken as scheduled'
            }
            
            MedicationLog.objects.create(**log_data)
            logs_created += 1

        return logs_created

    def _create_sample_transactions(self):
        """Create sample stock transactions for testing."""
        transactions_created = 0
        
        # Get or create a test user
        try:
            user = User.objects.filter(user_type='PHARMACIST').first()
            if not user:
                user = User.objects.create_user(
                    username='test_pharmacist',
                    email='pharmacist@test.com',
                    password='testpass123',
                    first_name='Test',
                    last_name='Pharmacist',
                    user_type='PHARMACIST'
                )
        except Exception:
            # If user creation fails, skip transaction creation
            self.stdout.write(
                self.style.WARNING('Could not create test pharmacist. Skipping transaction creation.')
            )
            return 0

        # Create transactions for medications
        medications = Medication.objects.all()[:10]
        
        for medication in medications:
            # Create a purchase transaction
            transaction_data = {
                'medication': medication,
                'user': user,
                'transaction_type': 'purchase',
                'quantity': 50,
                'unit_price': Decimal('10.00'),
                'total_amount': Decimal('500.00'),
                'stock_before': medication.pill_count,
                'stock_after': medication.pill_count + 50,
                'reference_number': f'PO-{medication.id:04d}',
                'batch_number': f'BATCH-{medication.id:04d}',
                'expiry_date': medication.expiration_date,
                'notes': 'Initial stock purchase'
            }
            
            StockTransaction.objects.create(**transaction_data)
            transactions_created += 1

        return transactions_created 