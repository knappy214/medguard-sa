# Generated manually for MedGuard SA medication database seeding
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


def seed_sa_medications(apps, schema_editor):
    """Seed the database with common South African medications."""
    Medication = apps.get_model('medications', 'Medication')
    
    # Common South African medications
    medications = [
        # Diabetes medications
        {
            'name': 'NovoRapid',
            'generic_name': 'Insulin aspart',
            'brand_name': 'NovoRapid',
            'medication_type': 'injection',
            'prescription_type': 'prescription',
            'strength': '100 units/ml',
            'dosage_unit': 'units',
            'description': 'Fast-acting insulin for diabetes management',
            'active_ingredients': 'Insulin aspart',
            'manufacturer': 'Novo Nordisk',
            'side_effects': 'Hypoglycemia, injection site reactions, weight gain',
            'contraindications': 'Hypoglycemia, hypersensitivity to insulin aspart',
            'storage_instructions': 'Store in refrigerator (2-8°C), do not freeze'
        },
        {
            'name': 'Lantus',
            'generic_name': 'Insulin glargine',
            'brand_name': 'Lantus',
            'medication_type': 'injection',
            'prescription_type': 'prescription',
            'strength': '100 units/ml',
            'dosage_unit': 'units',
            'description': 'Long-acting insulin for diabetes management',
            'active_ingredients': 'Insulin glargine',
            'manufacturer': 'Sanofi',
            'side_effects': 'Hypoglycemia, injection site reactions, weight gain',
            'contraindications': 'Hypoglycemia, hypersensitivity to insulin glargine',
            'storage_instructions': 'Store in refrigerator (2-8°C), do not freeze'
        },
        {
            'name': 'Metformin',
            'generic_name': 'Metformin hydrochloride',
            'brand_name': 'Glucophage',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'description': 'Oral medication for type 2 diabetes',
            'active_ingredients': 'Metformin hydrochloride',
            'manufacturer': 'Merck',
            'side_effects': 'Nausea, diarrhea, abdominal discomfort',
            'contraindications': 'Severe kidney disease, metabolic acidosis',
            'storage_instructions': 'Store at room temperature, protect from moisture'
        },
        
        # Cardiovascular medications
        {
            'name': 'Atorvastatin',
            'generic_name': 'Atorvastatin calcium',
            'brand_name': 'Lipitor',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '20mg',
            'dosage_unit': 'mg',
            'description': 'Cholesterol-lowering medication',
            'active_ingredients': 'Atorvastatin calcium',
            'manufacturer': 'Pfizer',
            'side_effects': 'Muscle pain, liver problems, digestive issues',
            'contraindications': 'Liver disease, pregnancy, hypersensitivity',
            'storage_instructions': 'Store at room temperature, protect from light'
        },
        {
            'name': 'Amlodipine',
            'generic_name': 'Amlodipine besylate',
            'brand_name': 'Norvasc',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '5mg',
            'dosage_unit': 'mg',
            'description': 'Calcium channel blocker for hypertension',
            'active_ingredients': 'Amlodipine besylate',
            'manufacturer': 'Pfizer',
            'side_effects': 'Swelling of ankles, dizziness, headache',
            'contraindications': 'Severe aortic stenosis, hypersensitivity',
            'storage_instructions': 'Store at room temperature'
        },
        {
            'name': 'Losartan',
            'generic_name': 'Losartan potassium',
            'brand_name': 'Cozaar',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '50mg',
            'dosage_unit': 'mg',
            'description': 'Angiotensin receptor blocker for hypertension',
            'active_ingredients': 'Losartan potassium',
            'manufacturer': 'Merck',
            'side_effects': 'Dizziness, fatigue, cough',
            'contraindications': 'Pregnancy, hypersensitivity to losartan',
            'storage_instructions': 'Store at room temperature'
        },
        
        # Pain medications
        {
            'name': 'Paracetamol',
            'generic_name': 'Paracetamol',
            'brand_name': 'Panado',
            'medication_type': 'tablet',
            'prescription_type': 'otc',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'description': 'Pain reliever and fever reducer',
            'active_ingredients': 'Paracetamol',
            'manufacturer': 'Aspen Pharmacare',
            'side_effects': 'Rare liver problems with overdose',
            'contraindications': 'Severe liver disease, hypersensitivity',
            'storage_instructions': 'Store at room temperature'
        },
        {
            'name': 'Ibuprofen',
            'generic_name': 'Ibuprofen',
            'brand_name': 'Brufen',
            'medication_type': 'tablet',
            'prescription_type': 'otc',
            'strength': '400mg',
            'dosage_unit': 'mg',
            'description': 'Non-steroidal anti-inflammatory drug for pain and inflammation',
            'active_ingredients': 'Ibuprofen',
            'manufacturer': 'Abbott',
            'side_effects': 'Stomach upset, heartburn, dizziness',
            'contraindications': 'Stomach ulcers, kidney disease, pregnancy (third trimester)',
            'storage_instructions': 'Store at room temperature'
        },
        
        # Respiratory medications
        {
            'name': 'Salbutamol',
            'generic_name': 'Salbutamol sulfate',
            'brand_name': 'Ventolin',
            'medication_type': 'inhaler',
            'prescription_type': 'prescription',
            'strength': '100mcg',
            'dosage_unit': 'mcg',
            'description': 'Bronchodilator for asthma and COPD',
            'active_ingredients': 'Salbutamol sulfate',
            'manufacturer': 'GlaxoSmithKline',
            'side_effects': 'Tremor, increased heart rate, headache',
            'contraindications': 'Hypersensitivity to salbutamol',
            'storage_instructions': 'Store at room temperature, protect from heat'
        },
        {
            'name': 'Fluticasone + Salmeterol',
            'generic_name': 'Fluticasone propionate + Salmeterol xinafoate',
            'brand_name': 'Seretide',
            'medication_type': 'inhaler',
            'prescription_type': 'prescription',
            'strength': '250/25mcg',
            'dosage_unit': 'mcg',
            'description': 'Combination inhaler for asthma control',
            'active_ingredients': 'Fluticasone propionate, Salmeterol xinafoate',
            'manufacturer': 'GlaxoSmithKline',
            'side_effects': 'Thrush, hoarseness, increased heart rate',
            'contraindications': 'Severe asthma attacks, hypersensitivity',
            'storage_instructions': 'Store at room temperature, protect from heat'
        },
        
        # Mental health medications
        {
            'name': 'Fluoxetine',
            'generic_name': 'Fluoxetine hydrochloride',
            'brand_name': 'Prozac',
            'medication_type': 'capsule',
            'prescription_type': 'prescription',
            'strength': '20mg',
            'dosage_unit': 'mg',
            'description': 'Selective serotonin reuptake inhibitor for depression',
            'active_ingredients': 'Fluoxetine hydrochloride',
            'manufacturer': 'Eli Lilly',
            'side_effects': 'Nausea, insomnia, sexual dysfunction',
            'contraindications': 'MAOI use, hypersensitivity to fluoxetine',
            'storage_instructions': 'Store at room temperature'
        },
        {
            'name': 'Methylphenidate',
            'generic_name': 'Methylphenidate hydrochloride',
            'brand_name': 'Ritalin',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '10mg',
            'dosage_unit': 'mg',
            'description': 'Stimulant medication for ADHD',
            'active_ingredients': 'Methylphenidate hydrochloride',
            'manufacturer': 'Novartis',
            'side_effects': 'Decreased appetite, insomnia, increased heart rate',
            'contraindications': 'Anxiety, glaucoma, heart problems',
            'storage_instructions': 'Store at room temperature, controlled substance'
        },
        
        # Antibiotics
        {
            'name': 'Amoxicillin + Clavulanic acid',
            'generic_name': 'Amoxicillin trihydrate + Potassium clavulanate',
            'brand_name': 'Augmentin',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500/125mg',
            'dosage_unit': 'mg',
            'description': 'Broad-spectrum antibiotic for bacterial infections',
            'active_ingredients': 'Amoxicillin trihydrate, Potassium clavulanate',
            'manufacturer': 'GlaxoSmithKline',
            'side_effects': 'Diarrhea, nausea, rash',
            'contraindications': 'Penicillin allergy, mononucleosis',
            'storage_instructions': 'Store at room temperature, complete full course'
        },
        {
            'name': 'Azithromycin',
            'generic_name': 'Azithromycin dihydrate',
            'brand_name': 'Zithromax',
            'medication_type': 'tablet',
            'prescription_type': 'prescription',
            'strength': '500mg',
            'dosage_unit': 'mg',
            'description': 'Macrolide antibiotic for respiratory infections',
            'active_ingredients': 'Azithromycin dihydrate',
            'manufacturer': 'Pfizer',
            'side_effects': 'Nausea, diarrhea, abdominal pain',
            'contraindications': 'Severe liver disease, hypersensitivity',
            'storage_instructions': 'Store at room temperature, complete full course'
        },
        
        # Gastrointestinal medications
        {
            'name': 'Omeprazole',
            'generic_name': 'Omeprazole',
            'brand_name': 'Losec',
            'medication_type': 'capsule',
            'prescription_type': 'prescription',
            'strength': '20mg',
            'dosage_unit': 'mg',
            'description': 'Proton pump inhibitor for acid reflux and ulcers',
            'active_ingredients': 'Omeprazole',
            'manufacturer': 'AstraZeneca',
            'side_effects': 'Headache, diarrhea, abdominal pain',
            'contraindications': 'Hypersensitivity to omeprazole',
            'storage_instructions': 'Store at room temperature, take before meals'
        },
        {
            'name': 'Ranitidine',
            'generic_name': 'Ranitidine hydrochloride',
            'brand_name': 'Zantac',
            'medication_type': 'tablet',
            'prescription_type': 'otc',
            'strength': '150mg',
            'dosage_unit': 'mg',
            'description': 'H2 blocker for acid reflux and ulcers',
            'active_ingredients': 'Ranitidine hydrochloride',
            'manufacturer': 'GlaxoSmithKline',
            'side_effects': 'Headache, dizziness, constipation',
            'contraindications': 'Hypersensitivity to ranitidine',
            'storage_instructions': 'Store at room temperature'
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
            'description': 'Vitamin D supplement for bone health',
            'active_ingredients': 'Cholecalciferol',
            'manufacturer': 'iNova Pharmaceuticals',
            'side_effects': 'Rare with normal doses',
            'contraindications': 'Hypercalcemia, hypersensitivity',
            'storage_instructions': 'Store at room temperature'
        },
        {
            'name': 'Iron Supplement',
            'generic_name': 'Ferrous sulfate',
            'brand_name': 'Ferrimed',
            'medication_type': 'tablet',
            'prescription_type': 'supplement',
            'strength': '200mg',
            'dosage_unit': 'mg',
            'description': 'Iron supplement for anemia',
            'active_ingredients': 'Ferrous sulfate',
            'manufacturer': 'Adcock Ingram',
            'side_effects': 'Constipation, black stools, stomach upset',
            'contraindications': 'Iron overload, hypersensitivity',
            'storage_instructions': 'Store at room temperature, keep away from children'
        },
        
        # Topical medications
        {
            'name': 'Hydrocortisone Cream',
            'generic_name': 'Hydrocortisone acetate',
            'brand_name': 'Cortizone',
            'medication_type': 'cream',
            'prescription_type': 'otc',
            'strength': '1%',
            'dosage_unit': '%',
            'description': 'Topical corticosteroid for skin inflammation',
            'active_ingredients': 'Hydrocortisone acetate',
            'manufacturer': 'Pfizer',
            'side_effects': 'Skin thinning, local irritation',
            'contraindications': 'Fungal infections, hypersensitivity',
            'storage_instructions': 'Store at room temperature, avoid eyes and face'
        },
        {
            'name': 'Antibiotic Ointment',
            'generic_name': 'Neomycin + Bacitracin + Polymyxin B',
            'brand_name': 'Neosporin',
            'medication_type': 'ointment',
            'prescription_type': 'otc',
            'strength': '3.5mg + 400IU + 5000IU per gram',
            'dosage_unit': 'mg/g',
            'description': 'Topical antibiotic for minor cuts and scrapes',
            'active_ingredients': 'Neomycin sulfate, Bacitracin zinc, Polymyxin B sulfate',
            'manufacturer': 'Johnson & Johnson',
            'side_effects': 'Local irritation, allergic reactions',
            'contraindications': 'Hypersensitivity to any component',
            'storage_instructions': 'Store at room temperature'
        }
    ]
    
    for med_data in medications:
        Medication.objects.get_or_create(
            name=med_data['name'],
            defaults=med_data
        )


def reverse_sa_medications(apps, schema_editor):
    """Reverse the South African medication seeding."""
    Medication = apps.get_model('medications', 'Medication')
    # Remove seeded medications (be careful with this in production)
    Medication.objects.filter(
        name__in=[
            'NovoRapid', 'Lantus', 'Metformin', 'Atorvastatin', 'Amlodipine',
            'Losartan', 'Paracetamol', 'Ibuprofen', 'Salbutamol', 'Fluticasone + Salmeterol',
            'Fluoxetine', 'Methylphenidate', 'Amoxicillin + Clavulanic acid', 'Azithromycin',
            'Omeprazole', 'Ranitidine', 'Vitamin D3', 'Iron Supplement',
            'Hydrocortisone Cream', 'Antibiotic Ointment'
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0009_icd10_code_mappings'),
    ]

    operations = [
        # Run data migration to seed medications
        migrations.RunPython(seed_sa_medications, reverse_sa_medications),
    ] 