# Generated manually for MedGuard SA prescription data seeding
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal


def seed_prescription_data(apps, schema_editor):
    """
    Seed the database with prescription data from Dr Owen Nosworthy.
    
    This migration creates:
    1. 21 medications from the prescription
    2. ICD-10 code mappings
    3. Medication categories
    4. Brand-to-generic mappings
    5. Dosage forms
    6. Manufacturer data
    7. Sample prescription with Dr Owen Nosworthy and patient Peter J Knapton
    8. Medication schedules
    9. Stock levels
    10. Audit trail
    """
    
    # Get models
    Medication = apps.get_model('medications', 'Medication')
    ICD10Code = apps.get_model('medications', 'ICD10Code')
    Prescription = apps.get_model('medications', 'Prescription')
    PrescriptionDoctor = apps.get_model('medications', 'PrescriptionDoctor')
    PrescriptionPatient = apps.get_model('medications', 'PrescriptionPatient')
    PrescriptionMedication = apps.get_model('medications', 'PrescriptionMedication')
    MedicationSchedule = apps.get_model('medications', 'MedicationSchedule')
    StockTransaction = apps.get_model('medications', 'StockTransaction')
    User = apps.get_model('users', 'User')
    
    # Create or get ICD-10 codes for the prescription
    icd10_codes = {
        'E10.4': ICD10Code.objects.get_or_create(
            code='E10.4',
            defaults={
                'description': 'Type 1 diabetes mellitus with neurological complications',
                'category': 'diabetes',
                'is_active': True
            }
        )[0],
        'E03.9': ICD10Code.objects.get_or_create(
            code='E03.9',
            defaults={
                'description': 'Hypothyroidism, unspecified',
                'category': 'endocrine',
                'is_active': True
            }
        )[0],
        'E27.4': ICD10Code.objects.get_or_create(
            code='E27.4',
            defaults={
                'description': 'Other and unspecified adrenocortical insufficiency',
                'category': 'endocrine',
                'is_active': True
            }
        )[0],
        'F90.9': ICD10Code.objects.get_or_create(
            code='F90.9',
            defaults={
                'description': 'Attention-deficit hyperactivity disorder, unspecified type',
                'category': 'mental_health',
                'is_active': True
            }
        )[0],
        'F41.8': ICD10Code.objects.get_or_create(
            code='F41.8',
            defaults={
                'description': 'Other specified anxiety disorders',
                'category': 'mental_health',
                'is_active': True
            }
        )[0],
        'G47.6': ICD10Code.objects.get_or_create(
            code='G47.6',
            defaults={
                'description': 'Sleep related movement disorders',
                'category': 'neurological',
                'is_active': True
            }
        )[0],
        'G89.4': ICD10Code.objects.get_or_create(
            code='G89.4',
            defaults={
                'description': 'Chronic pain syndrome',
                'category': 'pain',
                'is_active': True
            }
        )[0],
        'K21.0': ICD10Code.objects.get_or_create(
            code='K21.0',
            defaults={
                'description': 'Gastro-esophageal reflux disease with esophagitis',
                'category': 'gastrointestinal',
                'is_active': True
            }
        )[0],
        'J30.9': ICD10Code.objects.get_or_create(
            code='J30.9',
            defaults={
                'description': 'Allergic rhinitis, unspecified',
                'category': 'respiratory',
                'is_active': True
            }
        )[0],
        'R11.0': ICD10Code.objects.get_or_create(
            code='R11.0',
            defaults={
                'description': 'Nausea',
                'category': 'gastrointestinal',
                'is_active': True
            }
        )[0],
    }
    
    # Create Dr Owen Nosworthy
    doctor = PrescriptionDoctor.objects.get_or_create(
        name='Dr Owen Nosworthy',
        defaults={
            'practice_number': '0292737',
            'specialty': 'Specialist Physician / Medical Oncologist',
            'contact_number': '+27 11 482 3593',
            'email': 'owen@nosworthyonc.com',
            'practice_name': 'Nosworthy Oncology',
            'practice_address': '20 Kent Road, Dunkeld West'
        }
    )[0]
    
    # Create patient Peter J Knapton
    patient = PrescriptionPatient.objects.get_or_create(
        name='Mr Peter J Knapton',
        defaults={
            'medical_aid_number': '045661470',
            'medical_aid_scheme': 'Discovery Health',
            'gender': 'male'
        }
    )[0]
    
    # Create prescription
    prescription_date = date(2025, 6, 28)
    prescription = Prescription.objects.create(
        prescription_number='PRES-2025-001',
        prescription_date=prescription_date,
        expiry_date=prescription_date + timedelta(days=365),
        status='active',
        priority='routine',
        prescription_type='new',
        total_medications=21,
        doctor=doctor,
        patient=patient,
        notes='Comprehensive medication management for chronic conditions'
    )
    
    # Define the 21 medications from the prescription
    medications_data = [
        # 1. NOVORAPID 3ml FLEXPEN x 3
        {
            'medication_number': 1,
            'medication_name': 'NOVORAPID',
            'generic_name': 'Insulin aspart',
            'brand_name': 'NovoRapid',
            'strength': '100 units/ml',
            'dosage_unit': 'units',
            'quantity': 3,
            'quantity_unit': 'FlexPen',
            'instructions': 'Use as directed according to blood glucose',
            'timing': 'as_needed',
            'icd10_code': 'E10.4',
            'medication_type': 'injection',
            'manufacturer': 'Novo Nordisk',
            'unit_price': Decimal('450.00'),
            'category': 'Insulin'
        },
        # 2. LANTUS SOLARSTAR PEN x 2
        {
            'medication_number': 2,
            'medication_name': 'LANTUS',
            'generic_name': 'Insulin glargine',
            'brand_name': 'Lantus',
            'strength': '100 units/ml',
            'dosage_unit': 'units',
            'quantity': 2,
            'quantity_unit': 'SolarStar Pen',
            'instructions': 'Use as directed according to blood glucose',
            'timing': 'as_needed',
            'icd10_code': 'E10.4',
            'medication_type': 'injection',
            'manufacturer': 'Sanofi',
            'unit_price': Decimal('520.00'),
            'category': 'Insulin'
        },
        # 3. ELTROXIN 200mg TABLETS x 30
        {
            'medication_number': 3,
            'medication_name': 'ELTROXIN',
            'generic_name': 'Levothyroxine sodium',
            'brand_name': 'Eltroxin',
            'strength': '200mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet daily',
            'timing': 'morning',
            'icd10_code': 'E03.9',
            'medication_type': 'tablet',
            'manufacturer': 'Aspen Pharmacare',
            'unit_price': Decimal('85.00'),
            'category': 'Thyroid Hormones'
        },
        # 4. MEDROL 16mg TABLETS x 30
        {
            'medication_number': 4,
            'medication_name': 'MEDROL',
            'generic_name': 'Methylprednisolone',
            'brand_name': 'Medrol',
            'strength': '16mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet in the morning',
            'timing': 'morning',
            'icd10_code': 'E27.4',
            'medication_type': 'tablet',
            'manufacturer': 'Pfizer',
            'unit_price': Decimal('120.00'),
            'category': 'Corticosteroids'
        },
        # 5. MEDROL 4mg TABLETS x 60
        {
            'medication_number': 5,
            'medication_name': 'MEDROL',
            'generic_name': 'Methylprednisolone',
            'brand_name': 'Medrol',
            'strength': '4mg',
            'dosage_unit': 'mg',
            'quantity': 60,
            'quantity_unit': 'tablets',
            'instructions': 'Take two tablets at 12h00',
            'timing': 'noon',
            'icd10_code': 'E27.4',
            'medication_type': 'tablet',
            'manufacturer': 'Pfizer',
            'unit_price': Decimal('95.00'),
            'category': 'Corticosteroids'
        },
        # 6. FLORINEF 0.1mg TABLETS x 30
        {
            'medication_number': 6,
            'medication_name': 'FLORINEF',
            'generic_name': 'Fludrocortisone acetate',
            'brand_name': 'Florinef',
            'strength': '0.1mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet daily',
            'timing': 'morning',
            'icd10_code': 'E27.4',
            'medication_type': 'tablet',
            'manufacturer': 'Aspen Pharmacare',
            'unit_price': Decimal('180.00'),
            'category': 'Corticosteroids'
        },
        # 7. VYVANSE 50mg TABLETS x 60
        {
            'medication_number': 7,
            'medication_name': 'VYVANSE',
            'generic_name': 'Lisdexamfetamine dimesylate',
            'brand_name': 'Vyvanse',
            'strength': '50mg',
            'dosage_unit': 'mg',
            'quantity': 60,
            'quantity_unit': 'tablets',
            'instructions': 'Take two tablets daily',
            'timing': 'morning',
            'icd10_code': 'F90.9',
            'medication_type': 'tablet',
            'manufacturer': 'Takeda',
            'unit_price': Decimal('350.00'),
            'category': 'ADHD Medications'
        },
        # 8. RITALIN LA 20mg TABLETS x 60
        {
            'medication_number': 8,
            'medication_name': 'RITALIN LA',
            'generic_name': 'Methylphenidate hydrochloride',
            'brand_name': 'Ritalin LA',
            'strength': '20mg',
            'dosage_unit': 'mg',
            'quantity': 60,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet twice daily',
            'timing': 'twice_daily',
            'icd10_code': 'F90.9',
            'medication_type': 'tablet',
            'manufacturer': 'Novartis',
            'unit_price': Decimal('280.00'),
            'category': 'ADHD Medications'
        },
        # 9. WELBUTRIN XL 300mg TABLETS x 30
        {
            'medication_number': 9,
            'medication_name': 'WELBUTRIN XL',
            'generic_name': 'Bupropion hydrochloride',
            'brand_name': 'Wellbutrin XL',
            'strength': '300mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet daily',
            'timing': 'morning',
            'icd10_code': 'F41.8',
            'medication_type': 'tablet',
            'manufacturer': 'GlaxoSmithKline',
            'unit_price': Decimal('220.00'),
            'category': 'Antidepressants'
        },
        # 10. CYMGEN 60mg TABLETS x 30
        {
            'medication_number': 10,
            'medication_name': 'CYMGEN',
            'generic_name': 'Cymbalta',
            'brand_name': 'Cymgen',
            'strength': '60mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet daily',
            'timing': 'morning',
            'icd10_code': 'F41.8',
            'medication_type': 'tablet',
            'manufacturer': 'Eli Lilly',
            'unit_price': Decimal('380.00'),
            'category': 'Antidepressants'
        },
        # 11. RIVOTRIL 2mg TABLETS x 30
        {
            'medication_number': 11,
            'medication_name': 'RIVOTRIL',
            'generic_name': 'Clonazepam',
            'brand_name': 'Rivotril',
            'strength': '2mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet at night',
            'timing': 'night',
            'icd10_code': 'G47.6',
            'medication_type': 'tablet',
            'manufacturer': 'Roche',
            'unit_price': Decimal('150.00'),
            'category': 'Benzodiazepines'
        },
        # 12. TARGINACT 20/10mg TABLETS x 60
        {
            'medication_number': 12,
            'medication_name': 'TARGINACT',
            'generic_name': 'Oxycodone/Naloxone',
            'brand_name': 'Targinact',
            'strength': '20/10mg',
            'dosage_unit': 'mg',
            'quantity': 60,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet twice a day',
            'timing': 'twice_daily',
            'icd10_code': 'G89.4',
            'medication_type': 'tablet',
            'manufacturer': 'Mundipharma',
            'unit_price': Decimal('420.00'),
            'category': 'Pain Management'
        },
        # 13. EPLEPTIN 400mg TABLETS x 270
        {
            'medication_number': 13,
            'medication_name': 'EPLEPTIN',
            'generic_name': 'Phenytoin sodium',
            'brand_name': 'Epleptin',
            'strength': '400mg',
            'dosage_unit': 'mg',
            'quantity': 270,
            'quantity_unit': 'tablets',
            'instructions': 'Take three tablets three times a day',
            'timing': 'three_times_daily',
            'icd10_code': 'G89.4',
            'medication_type': 'tablet',
            'manufacturer': 'Aspen Pharmacare',
            'unit_price': Decimal('45.00'),
            'category': 'Anticonvulsants'
        },
        # 14. CELEBREX 200mg TABLETS
        {
            'medication_number': 14,
            'medication_name': 'CELEBREX',
            'generic_name': 'Celecoxib',
            'brand_name': 'Celebrex',
            'strength': '200mg',
            'dosage_unit': 'mg',
            'quantity': 60,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet TWICE daily',
            'timing': 'twice_daily',
            'icd10_code': 'G89.4',
            'medication_type': 'tablet',
            'manufacturer': 'Pfizer',
            'unit_price': Decimal('180.00'),
            'category': 'Pain Management'
        },
        # 15. QUININE 150mg TABLETS x 60
        {
            'medication_number': 15,
            'medication_name': 'QUININE',
            'generic_name': 'Quinine sulphate',
            'brand_name': 'Quinine',
            'strength': '150mg',
            'dosage_unit': 'mg',
            'quantity': 60,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet twice a day',
            'timing': 'twice_daily',
            'icd10_code': 'G47.6',
            'medication_type': 'tablet',
            'manufacturer': 'Aspen Pharmacare',
            'unit_price': Decimal('75.00'),
            'category': 'Antimalarials'
        },
        # 16. TOPZOLE 40mg TABLETS x 30
        {
            'medication_number': 16,
            'medication_name': 'TOPZOLE',
            'generic_name': 'Omeprazole',
            'brand_name': 'Topzole',
            'strength': '40mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet daily',
            'timing': 'morning',
            'icd10_code': 'K21.0',
            'medication_type': 'tablet',
            'manufacturer': 'Aspen Pharmacare',
            'unit_price': Decimal('95.00'),
            'category': 'Proton Pump Inhibitors'
        },
        # 17. MONTEFLO 10mg TABLETS x 30
        {
            'medication_number': 17,
            'medication_name': 'MONTEFLO',
            'generic_name': 'Montelukast sodium',
            'brand_name': 'Monteflo',
            'strength': '10mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet daily',
            'timing': 'night',
            'icd10_code': 'J30.9',
            'medication_type': 'tablet',
            'manufacturer': 'Merck',
            'unit_price': Decimal('140.00'),
            'category': 'Leukotriene Modifiers'
        },
        # 18. FEXO 180mg TABLETS x 30
        {
            'medication_number': 18,
            'medication_name': 'FEXO',
            'generic_name': 'Fexofenadine hydrochloride',
            'brand_name': 'Fexo',
            'strength': '180mg',
            'dosage_unit': 'mg',
            'quantity': 30,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet daily',
            'timing': 'morning',
            'icd10_code': 'J30.9',
            'medication_type': 'tablet',
            'manufacturer': 'Sanofi',
            'unit_price': Decimal('110.00'),
            'category': 'Antihistamines'
        },
        # 19. CLOPAMON 10mg TABLETS x 90
        {
            'medication_number': 19,
            'medication_name': 'CLOPAMON',
            'generic_name': 'Metoclopramide hydrochloride',
            'brand_name': 'Clopamon',
            'strength': '10mg',
            'dosage_unit': 'mg',
            'quantity': 90,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet three times a day as required',
            'timing': 'as_needed',
            'icd10_code': 'R11.0',
            'medication_type': 'tablet',
            'manufacturer': 'Aspen Pharmacare',
            'unit_price': Decimal('35.00'),
            'category': 'Antiemetics'
        },
        # 20. OXYNORM 20mg TABLETS x 90
        {
            'medication_number': 20,
            'medication_name': 'OXYNORM',
            'generic_name': 'Oxycodone hydrochloride',
            'brand_name': 'Oxynorm',
            'strength': '20mg',
            'dosage_unit': 'mg',
            'quantity': 90,
            'quantity_unit': 'tablets',
            'instructions': 'Take one tablet three times a day as needed',
            'timing': 'as_needed',
            'icd10_code': 'G89.4',
            'medication_type': 'tablet',
            'manufacturer': 'Mundipharma',
            'unit_price': Decimal('380.00'),
            'category': 'Pain Management'
        },
        # 21. BETNOVATE IN UEA 1:4 x 500g
        {
            'medication_number': 21,
            'medication_name': 'BETNOVATE IN UEA',
            'generic_name': 'Betamethasone valerate',
            'brand_name': 'Betnovate',
            'strength': '1:4',
            'dosage_unit': 'ratio',
            'quantity': 1,
            'quantity_unit': '500g tube',
            'instructions': 'APPLY DAILY',
            'timing': 'morning',
            'icd10_code': None,  # No ICD-10 code provided for this item
            'medication_type': 'cream',
            'manufacturer': 'GlaxoSmithKline',
            'unit_price': Decimal('120.00'),
            'category': 'Topical Corticosteroids'
        }
    ]
    
    # Create medications and prescription medications
    created_medications = []
    total_cost = Decimal('0.00')
    
    for med_data in medications_data:
        # Create or get the medication
        medication = Medication.objects.get_or_create(
            name=med_data['medication_name'],
            defaults={
                'generic_name': med_data['generic_name'],
                'brand_name': med_data['brand_name'],
                'medication_type': med_data['medication_type'],
                'prescription_type': 'prescription',
                'strength': med_data['strength'],
                'dosage_unit': med_data['dosage_unit'],
                'description': f"{med_data['category']} medication for {med_data['medication_name']}",
                'active_ingredients': med_data['generic_name'],
                'manufacturer': med_data['manufacturer'],
                'side_effects': 'Consult healthcare provider for side effects',
                'contraindications': 'Consult healthcare provider for contraindications',
                'storage_instructions': 'Store at room temperature, protect from light and moisture',
                'pill_count': med_data['quantity'] * 2,  # Double the prescription quantity for stock
                'low_stock_threshold': 10,
                'expiration_date': date(2026, 12, 31)
            }
        )[0]
        created_medications.append(medication)
        
        # Calculate total price for this medication
        total_price = med_data['unit_price'] * med_data['quantity']
        total_cost += total_price
        
        # Create prescription medication
        prescription_med = PrescriptionMedication.objects.create(
            prescription=prescription,
            medication_number=med_data['medication_number'],
            medication_name=med_data['medication_name'],
            generic_name=med_data['generic_name'],
            brand_name=med_data['brand_name'],
            strength=med_data['strength'],
            dosage_unit=med_data['dosage_unit'],
            quantity=med_data['quantity'],
            quantity_unit=med_data['quantity_unit'],
            instructions=med_data['instructions'],
            timing=med_data['timing'],
            unit_price=med_data['unit_price'],
            total_price=total_price,
            status='pending',
            medication=medication
        )
        
        # Add ICD-10 code if available
        if med_data['icd10_code']:
            prescription_med.icd10_codes.add(icd10_codes[med_data['icd10_code']])
    
    # Update prescription total cost
    prescription.total_cost = total_cost
    prescription.save()
    
    # Create medication schedules for the patient
    # First, create a test user for the patient if it doesn't exist
    patient_user, created = User.objects.get_or_create(
        email='peter.knapton@example.com',
        defaults={
            'username': 'peter.knapton',
            'first_name': 'Peter',
            'last_name': 'Knapton',
            'user_type': 'PATIENT',
            'phone': '+27 82 123 4567',
            'date_of_birth': date(1980, 1, 1),
            'gender': 'male',
            'address': '123 Main Street, Johannesburg, Gauteng',
            'city': 'Johannesburg',
            'province': 'gauteng',
            'postal_code': '2000',
            'medical_conditions': 'Diabetes, ADHD, Chronic Pain, Thyroid Disorder',
            'allergies': 'Penicillin'
        }
    )
    
    # Create medication schedules for medications that have specific timing
    schedule_data = [
        # Morning medications
        {'med_name': 'ELTROXIN', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'MEDROL', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'FLORINEF', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'VYVANSE', 'timing': 'morning', 'dosage': 2, 'frequency': 'daily'},
        {'med_name': 'WELBUTRIN XL', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'CYMGEN', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'TOPZOLE', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'FEXO', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'BETNOVATE IN UEA', 'timing': 'morning', 'dosage': 1, 'frequency': 'daily'},
        
        # Noon medications
        {'med_name': 'MEDROL', 'timing': 'noon', 'dosage': 2, 'frequency': 'daily'},
        
        # Night medications
        {'med_name': 'RIVOTRIL', 'timing': 'night', 'dosage': 1, 'frequency': 'daily'},
        {'med_name': 'MONTEFLO', 'timing': 'night', 'dosage': 1, 'frequency': 'daily'},
        
        # Twice daily medications
        {'med_name': 'RITALIN LA', 'timing': 'morning', 'dosage': 1, 'frequency': 'twice daily'},
        {'med_name': 'TARGINACT', 'timing': 'morning', 'dosage': 1, 'frequency': 'twice daily'},
        {'med_name': 'CELEBREX', 'timing': 'morning', 'dosage': 1, 'frequency': 'twice daily'},
        {'med_name': 'QUININE', 'timing': 'morning', 'dosage': 1, 'frequency': 'twice daily'},
        
        # Three times daily medications
        {'med_name': 'EPLEPTIN', 'timing': 'morning', 'dosage': 3, 'frequency': 'three times daily'},
    ]
    
    for schedule_info in schedule_data:
        medication = next((med for med in created_medications if med.name == schedule_info['med_name']), None)
        if medication:
            MedicationSchedule.objects.create(
                patient=patient_user,
                medication=medication,
                timing=schedule_info['timing'],
                dosage_amount=schedule_info['dosage'],
                frequency=schedule_info['frequency'],
                start_date=prescription_date,
                instructions=f"Take {schedule_info['dosage']} {medication.medication_type}(s) {schedule_info['frequency']}"
            )
    
    # Create stock transactions for audit trail
    for medication in created_medications:
        # Initial stock transaction
        StockTransaction.objects.create(
            medication=medication,
            user=patient_user,
            transaction_type='purchase',
            quantity=medication.pill_count,
            unit_price=Decimal('50.00'),  # Estimated cost
            total_amount=Decimal('50.00') * medication.pill_count,
            stock_before=0,
            stock_after=medication.pill_count,
            reference_number=f'INIT-{medication.id}',
            batch_number=f'BATCH-{medication.id}-001',
            expiry_date=medication.expiration_date,
            notes=f'Initial stock for {medication.name} prescription'
        )
    
    print(f"Successfully seeded prescription data:")
    print(f"- Created {len(created_medications)} medications")
    print(f"- Created prescription for Dr Owen Nosworthy and Mr Peter J Knapton")
    print(f"- Total prescription cost: R{total_cost}")
    print(f"- Created medication schedules and stock transactions")


def reverse_prescription_data(apps, schema_editor):
    """Reverse the prescription data seeding."""
    PrescriptionMedication = apps.get_model('medications', 'PrescriptionMedication')
    Prescription = apps.get_model('medications', 'Prescription')
    PrescriptionDoctor = apps.get_model('medications', 'PrescriptionDoctor')
    PrescriptionPatient = apps.get_model('medications', 'PrescriptionPatient')
    MedicationSchedule = apps.get_model('medications', 'MedicationSchedule')
    StockTransaction = apps.get_model('medications', 'StockTransaction')
    User = apps.get_model('users', 'User')
    
    # Delete prescription-related data
    PrescriptionMedication.objects.filter(prescription__prescription_number='PRES-2025-001').delete()
    Prescription.objects.filter(prescription_number='PRES-2025-001').delete()
    PrescriptionDoctor.objects.filter(name='Dr Owen Nosworthy').delete()
    PrescriptionPatient.objects.filter(name='Mr Peter J Knapton').delete()
    
    # Delete medication schedules
    MedicationSchedule.objects.filter(patient__email='peter.knapton@example.com').delete()
    
    # Delete stock transactions
    StockTransaction.objects.filter(reference_number__startswith='INIT-').delete()
    
    # Delete test user
    User.objects.filter(email='peter.knapton@example.com').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0011_optimize_indexes'),
        ('users', '0002_add_user_avatar'),
    ]

    operations = [
        # Run data migration
        migrations.RunPython(seed_prescription_data, reverse_prescription_data),
    ] 