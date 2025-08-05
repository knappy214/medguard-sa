# Generated manually for MedGuard SA - Add prescription-specific fields to Medication model
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0001_initial'),
    ]

    operations = [
        # Add prescription-specific fields to Medication model
        
        # Prescription requirements
        migrations.AddField(
            model_name='medication',
            name='requires_prescription',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether this medication requires a prescription')
            ),
        ),
        
        # Prescription validity
        migrations.AddField(
            model_name='medication',
            name='prescription_validity_days',
            field=models.PositiveIntegerField(
                default=30,
                help_text=_('Number of days a prescription is valid for this medication')
            ),
        ),
        
        # Prescription restrictions
        migrations.AddField(
            model_name='medication',
            name='max_prescription_quantity',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Maximum quantity that can be prescribed at once')
            ),
        ),
        
        # Prescription refills
        migrations.AddField(
            model_name='medication',
            name='max_refills',
            field=models.PositiveIntegerField(
                default=0,
                help_text=_('Maximum number of refills allowed')
            ),
        ),
        
        # Prescription scheduling
        migrations.AddField(
            model_name='medication',
            name='schedule_category',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('unscheduled', _('Unscheduled')),
                    ('schedule_1', _('Schedule 1')),
                    ('schedule_2', _('Schedule 2')),
                    ('schedule_3', _('Schedule 3')),
                    ('schedule_4', _('Schedule 4')),
                    ('schedule_5', _('Schedule 5')),
                    ('schedule_6', _('Schedule 6')),
                    ('schedule_7', _('Schedule 7')),
                    ('schedule_8', _('Schedule 8')),
                ],
                default='unscheduled',
                help_text=_('Drug scheduling category')
            ),
        ),
        
        # Prescription monitoring
        migrations.AddField(
            model_name='medication',
            name='requires_monitoring',
            field=models.BooleanField(
                default=False,
                help_text=_('Whether this medication requires regular monitoring')
            ),
        ),
        
        # Monitoring frequency
        migrations.AddField(
            model_name='medication',
            name='monitoring_frequency_days',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Frequency of monitoring required in days')
            ),
        ),
        
        # Prescription notes
        migrations.AddField(
            model_name='medication',
            name='prescription_notes',
            field=models.TextField(
                blank=True,
                help_text=_('Special notes for prescribing this medication')
            ),
        ),
        
        # Prescription warnings
        migrations.AddField(
            model_name='medication',
            name='prescription_warnings',
            field=models.TextField(
                blank=True,
                help_text=_('Warnings that should be displayed when prescribing')
            ),
        ),
        
        # Prescription alternatives
        migrations.AddField(
            model_name='medication',
            name='alternative_medications',
            field=models.ManyToManyField(
                blank=True,
                to='medications.medication',
                help_text=_('Alternative medications that can be prescribed instead')
            ),
        ),
        
        # Prescription cost information
        migrations.AddField(
            model_name='medication',
            name='prescription_cost',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text=_('Cost of prescription for this medication')
            ),
        ),
        
        # Prescription insurance coverage
        migrations.AddField(
            model_name='medication',
            name='insurance_coverage',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('covered', _('Fully Covered')),
                    ('partial', _('Partially Covered')),
                    ('not_covered', _('Not Covered')),
                    ('prior_auth', _('Prior Authorization Required')),
                ],
                default='covered',
                help_text=_('Insurance coverage status for this medication')
            ),
        ),
        
        # Prescription approval workflow
        migrations.AddField(
            model_name='medication',
            name='requires_approval',
            field=models.BooleanField(
                default=False,
                help_text=_('Whether prescription requires approval workflow')
            ),
        ),
        
        # Approval level required
        migrations.AddField(
            model_name='medication',
            name='approval_level',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('none', _('No Approval Required')),
                    ('pharmacist', _('Pharmacist Approval')),
                    ('doctor', _('Doctor Approval')),
                    ('specialist', _('Specialist Approval')),
                    ('committee', _('Committee Approval')),
                ],
                default='none',
                help_text=_('Level of approval required for prescription')
            ),
        ),
        
        # Prescription documentation requirements
        migrations.AddField(
            model_name='medication',
            name='documentation_required',
            field=models.JSONField(
                default=list,
                help_text=_('List of documentation required for prescription')
            ),
        ),
        
        # Prescription patient education
        migrations.AddField(
            model_name='medication',
            name='patient_education_required',
            field=models.BooleanField(
                default=False,
                help_text=_('Whether patient education is required for this medication')
            ),
        ),
        
        # Patient education materials
        migrations.AddField(
            model_name='medication',
            name='patient_education_materials',
            field=models.JSONField(
                default=list,
                help_text=_('List of patient education materials required')
            ),
        ),
        
        # Prescription follow-up requirements
        migrations.AddField(
            model_name='medication',
            name='follow_up_required',
            field=models.BooleanField(
                default=False,
                help_text=_('Whether follow-up is required after prescription')
            ),
        ),
        
        # Follow-up timeline
        migrations.AddField(
            model_name='medication',
            name='follow_up_days',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Days after prescription when follow-up is required')
            ),
        ),
        
        # Prescription success metrics
        migrations.AddField(
            model_name='medication',
            name='success_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Metrics to track prescription success')
            ),
        ),
        
        # Add indexes for prescription fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['requires_prescription'], name='medication_prescription_required_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['schedule_category'], name='medication_schedule_category_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['requires_monitoring'], name='medication_monitoring_required_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['insurance_coverage'], name='medication_insurance_coverage_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['approval_level'], name='medication_approval_level_idx'),
        ),
    ] 