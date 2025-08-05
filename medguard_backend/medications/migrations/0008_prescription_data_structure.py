# Generated manually for MedGuard SA prescription data structure
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0007_initial_enhanced_models'),
    ]

    operations = [
        # Create Prescription model for 21-medication structure
        migrations.CreateModel(
            name='Prescription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prescription_number', models.CharField(max_length=100, unique=True, help_text=_('Unique prescription number'))),
                ('prescription_date', models.DateField(help_text=_('Date prescription was issued'))),
                ('expiry_date', models.DateField(help_text=_('Date prescription expires'))),
                ('status', models.CharField(
                    choices=[
                        ('draft', _('Draft')),
                        ('active', _('Active')),
                        ('filled', _('Filled')),
                        ('expired', _('Expired')),
                        ('cancelled', _('Cancelled')),
                        ('renewed', _('Renewed'))
                    ],
                    default='draft',
                    max_length=20,
                    help_text=_('Current status of the prescription')
                )),
                ('priority', models.CharField(
                    choices=[
                        ('routine', _('Routine')),
                        ('urgent', _('Urgent')),
                        ('emergency', _('Emergency'))
                    ],
                    default='routine',
                    max_length=20,
                    help_text=_('Priority level of the prescription')
                )),
                ('prescription_type', models.CharField(
                    choices=[
                        ('new', _('New Prescription')),
                        ('repeat', _('Repeat Prescription')),
                        ('emergency', _('Emergency Prescription')),
                        ('discharge', _('Discharge Prescription'))
                    ],
                    default='new',
                    max_length=20,
                    help_text=_('Type of prescription')
                )),
                ('total_medications', models.PositiveIntegerField(default=0, help_text=_('Total number of medications in prescription'))),
                ('total_cost', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=10,
                    null=True,
                    help_text=_('Total cost of all medications')
                )),
                ('notes', models.TextField(blank=True, help_text=_('Additional notes about the prescription'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this prescription was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this prescription was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription'),
                'verbose_name_plural': _('Prescriptions'),
                'db_table': 'prescriptions',
                'ordering': ['-prescription_date'],
            },
        ),
        
        # Create PrescriptionMedication model for individual medications in prescription
        migrations.CreateModel(
            name='PrescriptionMedication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('medication_number', models.PositiveIntegerField(help_text=_('Order number of medication in prescription (1-21)'))),
                ('medication_name', models.CharField(max_length=200, help_text=_('Name of the medication'))),
                ('generic_name', models.CharField(blank=True, max_length=200, help_text=_('Generic name of the medication'))),
                ('brand_name', models.CharField(blank=True, max_length=200, help_text=_('Brand name of the medication'))),
                ('strength', models.CharField(max_length=50, help_text=_('Strength of the medication (e.g., 500mg, 10mg/ml)'))),
                ('dosage_unit', models.CharField(max_length=20, help_text=_('Unit of dosage (e.g., mg, ml, mcg)'))),
                ('quantity', models.PositiveIntegerField(help_text=_('Quantity prescribed'))),
                ('quantity_unit', models.CharField(max_length=20, help_text=_('Unit for quantity (tablets, capsules, ml, etc.)'))),
                ('instructions', models.TextField(help_text=_('Instructions for taking the medication'))),
                ('timing', models.CharField(
                    choices=[
                        ('morning', _('Morning')),
                        ('noon', _('Noon')),
                        ('night', _('Night')),
                        ('custom', _('Custom Time')),
                        ('as_needed', _('As Needed')),
                        ('twice_daily', _('Twice Daily')),
                        ('three_times_daily', _('Three Times Daily')),
                        ('four_times_daily', _('Four Times Daily'))
                    ],
                    max_length=20,
                    help_text=_('When to take the medication')
                )),
                ('custom_time', models.TimeField(blank=True, null=True, help_text=_('Custom time for medication (if timing is custom)'))),
                ('duration_days', models.PositiveIntegerField(blank=True, null=True, help_text=_('Duration of treatment in days'))),
                ('repeats', models.PositiveIntegerField(default=0, help_text=_('Number of repeats allowed'))),
                ('as_needed', models.BooleanField(default=False, help_text=_('Whether medication is taken as needed'))),
                ('unit_price', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=10,
                    null=True,
                    help_text=_('Unit price of the medication')
                )),
                ('total_price', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=10,
                    null=True,
                    help_text=_('Total price for this medication')
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', _('Pending')),
                        ('dispensed', _('Dispensed')),
                        ('partially_dispensed', _('Partially Dispensed')),
                        ('out_of_stock', _('Out of Stock')),
                        ('cancelled', _('Cancelled'))
                    ],
                    default='pending',
                    max_length=20,
                    help_text=_('Status of this medication in the prescription')
                )),
                ('dispensed_quantity', models.PositiveIntegerField(default=0, help_text=_('Quantity actually dispensed'))),
                ('dispensed_at', models.DateTimeField(blank=True, null=True, help_text=_('When this medication was dispensed'))),
                ('dispensed_by', models.CharField(blank=True, max_length=200, help_text=_('Who dispensed this medication'))),
                ('notes', models.TextField(blank=True, help_text=_('Additional notes about this medication'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this prescription medication was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this prescription medication was last updated'))),
                ('medication', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='medications.medication',
                    help_text=_('Reference to existing medication record')
                )),
                ('prescription', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='medications',
                    to='medications.prescription',
                    help_text=_('Prescription this medication belongs to')
                )),
            ],
            options={
                'verbose_name': _('Prescription Medication'),
                'verbose_name_plural': _('Prescription Medications'),
                'db_table': 'prescription_medications',
                'ordering': ['medication_number'],
                'unique_together': {('prescription', 'medication_number')},
            },
        ),
        
        # Create PrescriptionDoctor model for doctor information
        migrations.CreateModel(
            name='PrescriptionDoctor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, help_text=_('Name of the prescribing doctor'))),
                ('practice_number', models.CharField(blank=True, max_length=50, help_text=_('Doctor\'s practice number'))),
                ('specialty', models.CharField(blank=True, max_length=100, help_text=_('Doctor\'s specialty'))),
                ('contact_number', models.CharField(blank=True, max_length=20, help_text=_('Doctor\'s contact number'))),
                ('email', models.EmailField(blank=True, max_length=254, help_text=_('Doctor\'s email address'))),
                ('practice_name', models.CharField(blank=True, max_length=200, help_text=_('Name of the practice'))),
                ('practice_address', models.TextField(blank=True, help_text=_('Address of the practice'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this doctor record was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this doctor record was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Doctor'),
                'verbose_name_plural': _('Prescription Doctors'),
                'db_table': 'prescription_doctors',
                'ordering': ['name'],
            },
        ),
        
        # Create PrescriptionPatient model for patient information
        migrations.CreateModel(
            name='PrescriptionPatient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, help_text=_('Name of the patient'))),
                ('id_number', models.CharField(blank=True, max_length=20, help_text=_('Patient\'s ID number'))),
                ('date_of_birth', models.DateField(blank=True, null=True, help_text=_('Patient\'s date of birth'))),
                ('age', models.PositiveIntegerField(blank=True, null=True, help_text=_('Patient\'s age'))),
                ('gender', models.CharField(
                    blank=True,
                    choices=[
                        ('male', _('Male')),
                        ('female', _('Female')),
                        ('other', _('Other'))
                    ],
                    max_length=10,
                    help_text=_('Patient\'s gender')
                )),
                ('contact_number', models.CharField(blank=True, max_length=20, help_text=_('Patient\'s contact number'))),
                ('email', models.EmailField(blank=True, max_length=254, help_text=_('Patient\'s email address'))),
                ('address', models.TextField(blank=True, help_text=_('Patient\'s address'))),
                ('medical_aid_number', models.CharField(blank=True, max_length=50, help_text=_('Medical aid number'))),
                ('medical_aid_scheme', models.CharField(blank=True, max_length=100, help_text=_('Medical aid scheme name'))),
                ('allergies', models.TextField(blank=True, help_text=_('Known allergies'))),
                ('chronic_conditions', models.TextField(blank=True, help_text=_('Chronic medical conditions'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this patient record was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this patient record was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Patient'),
                'verbose_name_plural': _('Prescription Patients'),
                'db_table': 'prescription_patients',
                'ordering': ['name'],
            },
        ),
        
        # Add foreign key relationships to Prescription model
        migrations.AddField(
            model_name='prescription',
            name='doctor',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='medications.prescriptiondoctor',
                help_text=_('Prescribing doctor')
            ),
        ),
        migrations.AddField(
            model_name='prescription',
            name='patient',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='medications.prescriptionpatient',
                help_text=_('Patient for this prescription')
            ),
        ),
        
        # Create indexes for performance
        migrations.AddIndex(
            model_name='prescription',
            index=models.Index(fields=['prescription_number'], name='prescription_number_idx'),
        ),
        migrations.AddIndex(
            model_name='prescription',
            index=models.Index(fields=['status', 'priority'], name='prescription_status_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='prescription',
            index=models.Index(fields=['prescription_date', 'expiry_date'], name='prescription_date_range_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionmedication',
            index=models.Index(fields=['prescription', 'medication_number'], name='prescription_medication_order_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionmedication',
            index=models.Index(fields=['status'], name='prescription_medication_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptiondoctor',
            index=models.Index(fields=['practice_number'], name='doctor_practice_number_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionpatient',
            index=models.Index(fields=['id_number'], name='patient_id_number_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionpatient',
            index=models.Index(fields=['medical_aid_number'], name='patient_medical_aid_idx'),
        ),
    ] 