# Generated manually for MedGuard SA ICD-10 code mappings
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


def create_icd10_mappings(apps, schema_editor):
    """Create ICD-10 code mappings for South African healthcare."""
    ICD10Code = apps.get_model('medications', 'ICD10Code')
    
    # Diabetes mellitus codes
    icd10_codes = [
        # Diabetes mellitus
        {'code': 'E10.4', 'description': 'Type 1 diabetes mellitus with neurological complications', 'category': 'diabetes'},
        {'code': 'E11.4', 'description': 'Type 2 diabetes mellitus with neurological complications', 'category': 'diabetes'},
        {'code': 'E11.9', 'description': 'Type 2 diabetes mellitus without complications', 'category': 'diabetes'},
        {'code': 'E10.9', 'description': 'Type 1 diabetes mellitus without complications', 'category': 'diabetes'},
        {'code': 'E13.4', 'description': 'Other specified diabetes mellitus with neurological complications', 'category': 'diabetes'},
        {'code': 'E11.65', 'description': 'Type 2 diabetes mellitus with hyperglycemia', 'category': 'diabetes'},
        {'code': 'E11.22', 'description': 'Type 2 diabetes mellitus with diabetic chronic kidney disease', 'category': 'diabetes'},
        {'code': 'E11.21', 'description': 'Type 2 diabetes mellitus with diabetic nephropathy', 'category': 'diabetes'},
        {'code': 'E11.40', 'description': 'Type 2 diabetes mellitus with diabetic neuropathy, unspecified', 'category': 'diabetes'},
        {'code': 'E11.41', 'description': 'Type 2 diabetes mellitus with diabetic mononeuropathy', 'category': 'diabetes'},
        {'code': 'E11.42', 'description': 'Type 2 diabetes mellitus with diabetic polyneuropathy', 'category': 'diabetes'},
        {'code': 'E11.43', 'description': 'Type 2 diabetes mellitus with diabetic autonomic (poly)neuropathy', 'category': 'diabetes'},
        {'code': 'E11.44', 'description': 'Type 2 diabetes mellitus with diabetic amyotrophy', 'category': 'diabetes'},
        {'code': 'E11.49', 'description': 'Type 2 diabetes mellitus with other diabetic neurological complication', 'category': 'diabetes'},
        
        # Mental and behavioral disorders
        {'code': 'F90.9', 'description': 'Attention-deficit hyperactivity disorder, unspecified type', 'category': 'mental_health'},
        {'code': 'F90.0', 'description': 'Attention-deficit hyperactivity disorder, predominantly inattentive type', 'category': 'mental_health'},
        {'code': 'F90.1', 'description': 'Attention-deficit hyperactivity disorder, predominantly hyperactive type', 'category': 'mental_health'},
        {'code': 'F90.2', 'description': 'Attention-deficit hyperactivity disorder, combined type', 'category': 'mental_health'},
        {'code': 'F32.9', 'description': 'Major depressive disorder, unspecified', 'category': 'mental_health'},
        {'code': 'F32.0', 'description': 'Major depressive disorder, single episode, mild', 'category': 'mental_health'},
        {'code': 'F32.1', 'description': 'Major depressive disorder, single episode, moderate', 'category': 'mental_health'},
        {'code': 'F32.2', 'description': 'Major depressive disorder, single episode, severe without psychotic features', 'category': 'mental_health'},
        {'code': 'F41.9', 'description': 'Anxiety disorder, unspecified', 'category': 'mental_health'},
        {'code': 'F41.1', 'description': 'Generalized anxiety disorder', 'category': 'mental_health'},
        {'code': 'F41.0', 'description': 'Panic disorder [episodic paroxysmal anxiety]', 'category': 'mental_health'},
        {'code': 'F33.9', 'description': 'Major depressive disorder, recurrent, unspecified', 'category': 'mental_health'},
        {'code': 'F31.9', 'description': 'Bipolar affective disorder, unspecified', 'category': 'mental_health'},
        {'code': 'F31.1', 'description': 'Bipolar affective disorder, current episode manic without psychotic features', 'category': 'mental_health'},
        {'code': 'F31.2', 'description': 'Bipolar affective disorder, current episode manic with psychotic features', 'category': 'mental_health'},
        {'code': 'F31.3', 'description': 'Bipolar affective disorder, current episode mild or moderate depression', 'category': 'mental_health'},
        {'code': 'F43.1', 'description': 'Post-traumatic stress disorder', 'category': 'mental_health'},
        {'code': 'F43.2', 'description': 'Adjustment disorders', 'category': 'mental_health'},
        
        # Cardiovascular diseases
        {'code': 'I10', 'description': 'Essential (primary) hypertension', 'category': 'cardiovascular'},
        {'code': 'I11.9', 'description': 'Hypertensive heart disease without heart failure', 'category': 'cardiovascular'},
        {'code': 'I12.9', 'description': 'Hypertensive chronic kidney disease with stage 1 through stage 4 chronic kidney disease', 'category': 'cardiovascular'},
        {'code': 'I25.10', 'description': 'Atherosclerotic heart disease of native coronary artery without angina pectoris', 'category': 'cardiovascular'},
        {'code': 'I25.110', 'description': 'Atherosclerotic heart disease of native coronary artery with angina pectoris with documented spasm', 'category': 'cardiovascular'},
        {'code': 'I25.119', 'description': 'Atherosclerotic heart disease of native coronary artery with angina pectoris with other documented spasm', 'category': 'cardiovascular'},
        {'code': 'I48.91', 'description': 'Unspecified atrial fibrillation', 'category': 'cardiovascular'},
        {'code': 'I48.0', 'description': 'Paroxysmal atrial fibrillation', 'category': 'cardiovascular'},
        {'code': 'I48.1', 'description': 'Persistent atrial fibrillation', 'category': 'cardiovascular'},
        {'code': 'I48.2', 'description': 'Chronic atrial fibrillation', 'category': 'cardiovascular'},
        {'code': 'I25.2', 'description': 'Old myocardial infarction', 'category': 'cardiovascular'},
        {'code': 'I50.9', 'description': 'Heart failure, unspecified', 'category': 'cardiovascular'},
        {'code': 'I50.22', 'description': 'Chronic systolic (congestive) heart failure', 'category': 'cardiovascular'},
        {'code': 'I50.32', 'description': 'Chronic diastolic (congestive) heart failure', 'category': 'cardiovascular'},
        {'code': 'I50.42', 'description': 'Chronic combined systolic (congestive) and diastolic (congestive) heart failure', 'category': 'cardiovascular'},
        {'code': 'I63.9', 'description': 'Cerebral infarction, unspecified', 'category': 'cardiovascular'},
        {'code': 'I63.0', 'description': 'Cerebral infarction due to thrombosis of precerebral arteries', 'category': 'cardiovascular'},
        {'code': 'I63.1', 'description': 'Cerebral infarction due to embolism of precerebral arteries', 'category': 'cardiovascular'},
        {'code': 'I63.2', 'description': 'Cerebral infarction due to unspecified occlusion or stenosis of precerebral arteries', 'category': 'cardiovascular'},
        
        # Respiratory diseases
        {'code': 'J45.901', 'description': 'Unspecified asthma with (acute) exacerbation', 'category': 'respiratory'},
        {'code': 'J44.9', 'description': 'Chronic obstructive pulmonary disease, unspecified', 'category': 'respiratory'},
        {'code': 'J45.909', 'description': 'Unspecified asthma, uncomplicated', 'category': 'respiratory'},
        {'code': 'J45.990', 'description': 'Exercise induced bronchospasm', 'category': 'respiratory'},
        {'code': 'J44.1', 'description': 'Chronic obstructive pulmonary disease with (acute) exacerbation', 'category': 'respiratory'},
        {'code': 'J45.20', 'description': 'Mild intermittent asthma, uncomplicated', 'category': 'respiratory'},
        {'code': 'J45.30', 'description': 'Mild persistent asthma, uncomplicated', 'category': 'respiratory'},
        {'code': 'J45.40', 'description': 'Moderate persistent asthma, uncomplicated', 'category': 'respiratory'},
        {'code': 'J45.50', 'description': 'Severe persistent asthma, uncomplicated', 'category': 'respiratory'},
        {'code': 'J45.901', 'description': 'Unspecified asthma with (acute) exacerbation', 'category': 'respiratory'},
        {'code': 'J45.902', 'description': 'Unspecified asthma with status asthmaticus', 'category': 'respiratory'},
        {'code': 'J44.0', 'description': 'Chronic obstructive pulmonary disease with acute lower respiratory infection', 'category': 'respiratory'},
        {'code': 'J44.2', 'description': 'Chronic obstructive pulmonary disease with acute bronchitis', 'category': 'respiratory'},
        
        # Pain and musculoskeletal
        {'code': 'M79.3', 'description': 'Sciatica, unspecified side', 'category': 'musculoskeletal'},
        {'code': 'R52.9', 'description': 'Pain, unspecified', 'category': 'pain'},
        {'code': 'M54.5', 'description': 'Low back pain', 'category': 'musculoskeletal'},
        {'code': 'M79.1', 'description': 'Myalgia', 'category': 'musculoskeletal'},
        {'code': 'M15.9', 'description': 'Polyosteoarthritis, unspecified site', 'category': 'musculoskeletal'},
        {'code': 'M16.9', 'description': 'Osteoarthritis of hip, unspecified', 'category': 'musculoskeletal'},
        {'code': 'M17.9', 'description': 'Osteoarthritis of knee, unspecified', 'category': 'musculoskeletal'},
        {'code': 'M25.50', 'description': 'Pain in unspecified joint', 'category': 'musculoskeletal'},
        {'code': 'M25.51', 'description': 'Pain in right shoulder', 'category': 'musculoskeletal'},
        {'code': 'M25.52', 'description': 'Pain in left shoulder', 'category': 'musculoskeletal'},
        {'code': 'M25.55', 'description': 'Pain in right hip', 'category': 'musculoskeletal'},
        {'code': 'M25.56', 'description': 'Pain in left hip', 'category': 'musculoskeletal'},
        {'code': 'M25.57', 'description': 'Pain in right ankle and joints of right foot', 'category': 'musculoskeletal'},
        {'code': 'M25.58', 'description': 'Pain in left ankle and joints of left foot', 'category': 'musculoskeletal'},
        
        # Infections
        {'code': 'N39.0', 'description': 'Urinary tract infection, site not specified', 'category': 'infection'},
        {'code': 'A09.9', 'description': 'Infectious gastroenteritis and colitis, unspecified', 'category': 'infection'},
        {'code': 'J06.9', 'description': 'Acute upper respiratory infection, unspecified', 'category': 'infection'},
        {'code': 'B20', 'description': 'Human immunodeficiency virus [HIV] disease', 'category': 'infection'},
        {'code': 'B20.9', 'description': 'Human immunodeficiency virus [HIV] disease, unspecified', 'category': 'infection'},
        {'code': 'B20.1', 'description': 'HIV disease resulting in other bacterial infections', 'category': 'infection'},
        {'code': 'B20.2', 'description': 'HIV disease resulting in cytomegaloviral disease', 'category': 'infection'},
        {'code': 'B20.3', 'description': 'HIV disease resulting in other viral infections', 'category': 'infection'},
        {'code': 'B20.4', 'description': 'HIV disease resulting in candidiasis', 'category': 'infection'},
        {'code': 'B20.5', 'description': 'HIV disease resulting in other mycoses', 'category': 'infection'},
        {'code': 'B20.6', 'description': 'HIV disease resulting in Pneumocystis carinii pneumonia', 'category': 'infection'},
        {'code': 'B20.7', 'description': 'HIV disease resulting in multiple infections', 'category': 'infection'},
        {'code': 'B20.8', 'description': 'HIV disease resulting in other infectious and parasitic diseases', 'category': 'infection'},
        {'code': 'A15.9', 'description': 'Respiratory tuberculosis unspecified, unspecified', 'category': 'infection'},
        {'code': 'A15.0', 'description': 'Respiratory tuberculosis unspecified, bacteriologically and histologically confirmed', 'category': 'infection'},
        {'code': 'A15.3', 'description': 'Respiratory tuberculosis unspecified, bacteriological and histological examination not done', 'category': 'infection'},
        
        # Other common conditions
        {'code': 'Z51.11', 'description': 'Encounter for antineoplastic chemotherapy', 'category': 'oncology'},
        {'code': 'Z79.4', 'description': 'Long term (current) use of insulin', 'category': 'medication_use'},
        {'code': 'Z79.899', 'description': 'Other long term (current) drug therapy', 'category': 'medication_use'},
        {'code': 'Z00.00', 'description': 'Encounter for general adult medical examination without abnormal findings', 'category': 'preventive'},
        {'code': 'Z51.12', 'description': 'Encounter for antineoplastic immunotherapy', 'category': 'oncology'},
        {'code': 'Z79.01', 'description': 'Long term (current) use of anticoagulants', 'category': 'medication_use'},
        {'code': 'Z79.02', 'description': 'Long term (current) use of antithrombotics/antiplatelets', 'category': 'medication_use'},
        {'code': 'Z79.3', 'description': 'Long term (current) use of hormonal contraceptives', 'category': 'medication_use'},
        {'code': 'Z79.5', 'description': 'Long term (current) use of systemic steroids', 'category': 'medication_use'},
        {'code': 'Z79.6', 'description': 'Long term (current) use of aspirin', 'category': 'medication_use'},
        {'code': 'Z79.8', 'description': 'Other long term (current) drug therapy', 'category': 'medication_use'},
        {'code': 'Z79.9', 'description': 'Long term (current) drug therapy, unspecified', 'category': 'medication_use'},
        
        # Gastrointestinal conditions
        {'code': 'K21.9', 'description': 'Gastro-esophageal reflux disease without esophagitis', 'category': 'gastrointestinal'},
        {'code': 'K25.9', 'description': 'Gastric ulcer, unspecified as acute or chronic, without hemorrhage or perforation', 'category': 'gastrointestinal'},
        {'code': 'K29.70', 'description': 'Gastritis, unspecified, without bleeding', 'category': 'gastrointestinal'},
        {'code': 'K59.0', 'description': 'Constipation, unspecified', 'category': 'gastrointestinal'},
        {'code': 'K59.1', 'description': 'Functional diarrhea', 'category': 'gastrointestinal'},
        {'code': 'K59.9', 'description': 'Functional intestinal disorder, unspecified', 'category': 'gastrointestinal'},
        
        # Endocrine conditions
        {'code': 'E03.9', 'description': 'Hypothyroidism, unspecified', 'category': 'endocrine'},
        {'code': 'E04.9', 'description': 'Nontoxic goiter, unspecified', 'category': 'endocrine'},
        {'code': 'E05.90', 'description': 'Thyrotoxicosis, unspecified without thyrotoxic crisis or storm', 'category': 'endocrine'},
        {'code': 'E27.1', 'description': 'Primary adrenocortical insufficiency', 'category': 'endocrine'},
        {'code': 'E27.2', 'description': 'Addisonian crisis', 'category': 'endocrine'},
        {'code': 'E27.9', 'description': 'Disorder of adrenal gland, unspecified', 'category': 'endocrine'},
        
        # Neurological conditions
        {'code': 'G40.909', 'description': 'Epilepsy, unspecified, not intractable, without status epilepticus', 'category': 'neurological'},
        {'code': 'G40.901', 'description': 'Epilepsy, unspecified, not intractable, with status epilepticus', 'category': 'neurological'},
        {'code': 'G40.911', 'description': 'Epilepsy, unspecified, intractable, with status epilepticus', 'category': 'neurological'},
        {'code': 'G40.919', 'description': 'Epilepsy, unspecified, intractable, without status epilepticus', 'category': 'neurological'},
        {'code': 'G25.1', 'description': 'Drug-induced tremor', 'category': 'neurological'},
        {'code': 'G25.9', 'description': 'Extrapyramidal movement disorder, unspecified', 'category': 'neurological'},
        {'code': 'G93.1', 'description': 'Anoxic brain damage, not elsewhere classified', 'category': 'neurological'},
        {'code': 'G93.9', 'description': 'Disorder of brain, unspecified', 'category': 'neurological'},
    ]
    
    for code_data in icd10_codes:
        ICD10Code.objects.get_or_create(
            code=code_data['code'],
            defaults={
                'description': code_data['description'],
                'category': code_data['category'],
                'is_active': True
            }
        )


def reverse_icd10_mappings(apps, schema_editor):
    """Reverse the ICD-10 code mappings."""
    ICD10Code = apps.get_model('medications', 'ICD10Code')
    ICD10Code.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0008_prescription_data_structure'),
    ]

    operations = [
        # Create ICD10Code model
        migrations.CreateModel(
            name='ICD10Code',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20, unique=True, help_text=_('ICD-10 code'))),
                ('description', models.TextField(help_text=_('Description of the condition'))),
                ('category', models.CharField(
                    choices=[
                        ('diabetes', _('Diabetes')),
                        ('mental_health', _('Mental Health')),
                        ('cardiovascular', _('Cardiovascular')),
                        ('respiratory', _('Respiratory')),
                        ('musculoskeletal', _('Musculoskeletal')),
                        ('pain', _('Pain')),
                        ('infection', _('Infection')),
                        ('oncology', _('Oncology')),
                        ('medication_use', _('Medication Use')),
                        ('preventive', _('Preventive Care')),
                        ('gastrointestinal', _('Gastrointestinal')),
                        ('endocrine', _('Endocrine')),
                        ('neurological', _('Neurological')),
                        ('other', _('Other'))
                    ],
                    max_length=20,
                    help_text=_('Category of the condition')
                )),
                ('is_active', models.BooleanField(default=True, help_text=_('Whether this code is active'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this code was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this code was last updated'))),
            ],
            options={
                'verbose_name': _('ICD-10 Code'),
                'verbose_name_plural': _('ICD-10 Codes'),
                'db_table': 'icd10_codes',
                'ordering': ['code'],
            },
        ),
        
        # Create indexes
        migrations.AddIndex(
            model_name='icd10code',
            index=models.Index(fields=['code'], name='icd10_code_idx'),
        ),
        migrations.AddIndex(
            model_name='icd10code',
            index=models.Index(fields=['category'], name='icd10_category_idx'),
        ),
        migrations.AddIndex(
            model_name='icd10code',
            index=models.Index(fields=['is_active'], name='icd10_active_idx'),
        ),
        
        # Run data migration
        migrations.RunPython(create_icd10_mappings, reverse_icd10_mappings),
    ] 