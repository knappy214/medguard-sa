# Generated manually for MedGuard SA medication interaction tracking
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0012_ocr_processing_results'),
    ]

    operations = [
        # Create MedicationInteraction model
        migrations.CreateModel(
            name='MedicationInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction_type', models.CharField(
                    choices=[
                        ('drug_drug', _('Drug-Drug Interaction')),
                        ('drug_food', _('Drug-Food Interaction')),
                        ('drug_herb', _('Drug-Herb Interaction')),
                        ('drug_alcohol', _('Drug-Alcohol Interaction')),
                        ('drug_disease', _('Drug-Disease Interaction')),
                        ('drug_lab', _('Drug-Lab Test Interaction')),
                        ('drug_pregnancy', _('Drug-Pregnancy Interaction')),
                        ('drug_breastfeeding', _('Drug-Breastfeeding Interaction'))
                    ],
                    max_length=20,
                    help_text=_('Type of medication interaction')
                )),
                ('severity_level', models.CharField(
                    choices=[
                        ('minor', _('Minor')),
                        ('moderate', _('Moderate')),
                        ('major', _('Major')),
                        ('contraindicated', _('Contraindicated'))
                    ],
                    max_length=20,
                    help_text=_('Severity level of the interaction')
                )),
                ('interaction_description', models.TextField(help_text=_('Description of the interaction'))),
                ('mechanism', models.TextField(blank=True, help_text=_('Mechanism of the interaction'))),
                ('clinical_effects', models.TextField(blank=True, help_text=_('Clinical effects of the interaction'))),
                ('management', models.TextField(blank=True, help_text=_('Management recommendations'))),
                ('evidence_level', models.CharField(
                    choices=[
                        ('excellent', _('Excellent')),
                        ('good', _('Good')),
                        ('fair', _('Fair')),
                        ('poor', _('Poor')),
                        ('theoretical', _('Theoretical'))
                    ],
                    max_length=20,
                    help_text=_('Level of evidence for the interaction')
                )),
                ('references', models.JSONField(default=list, help_text=_('References supporting the interaction'))),
                ('is_active', models.BooleanField(default=True, help_text=_('Whether this interaction is active'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this interaction was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this interaction was last updated'))),
            ],
            options={
                'verbose_name': _('Medication Interaction'),
                'verbose_name_plural': _('Medication Interactions'),
                'db_table': 'medication_interactions',
                'ordering': ['severity_level', 'interaction_type'],
            },
        ),
        
        # Create PatientMedicationInteraction model
        migrations.CreateModel(
            name='PatientMedicationInteraction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interaction_date', models.DateTimeField(auto_now_add=True, help_text=_('When this interaction was detected'))),
                ('interaction_status', models.CharField(
                    choices=[
                        ('detected', _('Detected')),
                        ('reviewed', _('Reviewed')),
                        ('acknowledged', _('Acknowledged')),
                        ('resolved', _('Resolved')),
                        ('ignored', _('Ignored'))
                    ],
                    default='detected',
                    max_length=20,
                    help_text=_('Status of the interaction for this patient')
                )),
                ('reviewed_by', models.CharField(blank=True, max_length=200, help_text=_('Who reviewed this interaction'))),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, help_text=_('When this interaction was reviewed'))),
                ('review_notes', models.TextField(blank=True, help_text=_('Notes from the review'))),
                ('action_taken', models.CharField(
                    choices=[
                        ('none', _('No Action')),
                        ('monitor', _('Monitor Patient')),
                        ('adjust_dose', _('Adjust Dose')),
                        ('discontinue', _('Discontinue Medication')),
                        ('substitute', _('Substitute Medication')),
                        ('delay', _('Delay Administration')),
                        ('separate', _('Separate Administration'))
                    ],
                    default='none',
                    max_length=20,
                    help_text=_('Action taken for this interaction')
                )),
                ('action_notes', models.TextField(blank=True, help_text=_('Notes about the action taken'))),
                ('risk_assessment', models.CharField(
                    choices=[
                        ('low', _('Low Risk')),
                        ('medium', _('Medium Risk')),
                        ('high', _('High Risk')),
                        ('critical', _('Critical Risk'))
                    ],
                    max_length=20,
                    help_text=_('Risk assessment for this patient')
                )),
                ('patient_specific_factors', models.JSONField(default=dict, help_text=_('Patient-specific factors affecting risk'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this patient interaction was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this patient interaction was last updated'))),
            ],
            options={
                'verbose_name': _('Patient Medication Interaction'),
                'verbose_name_plural': _('Patient Medication Interactions'),
                'db_table': 'patient_medication_interactions',
                'ordering': ['-interaction_date'],
            },
        ),
        
        # Create InteractionCheck model
        migrations.CreateModel(
            name='InteractionCheck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('check_type', models.CharField(
                    choices=[
                        ('prescription', _('Prescription Check')),
                        ('medication_list', _('Medication List Check')),
                        ('real_time', _('Real-time Check')),
                        ('batch', _('Batch Check')),
                        ('scheduled', _('Scheduled Check'))
                    ],
                    max_length=20,
                    help_text=_('Type of interaction check performed')
                )),
                ('check_status', models.CharField(
                    choices=[
                        ('pending', _('Pending')),
                        ('in_progress', _('In Progress')),
                        ('completed', _('Completed')),
                        ('failed', _('Failed')),
                        ('cancelled', _('Cancelled'))
                    ],
                    default='pending',
                    max_length=20,
                    help_text=_('Status of the interaction check')
                )),
                ('check_date', models.DateTimeField(auto_now_add=True, help_text=_('When this check was performed'))),
                ('checked_by', models.CharField(blank=True, max_length=200, help_text=_('Who performed this check'))),
                ('medications_checked', models.JSONField(default=list, help_text=_('List of medications checked'))),
                ('interactions_found', models.PositiveIntegerField(default=0, help_text=_('Number of interactions found'))),
                ('critical_interactions', models.PositiveIntegerField(default=0, help_text=_('Number of critical interactions'))),
                ('major_interactions', models.PositiveIntegerField(default=0, help_text=_('Number of major interactions'))),
                ('moderate_interactions', models.PositiveIntegerField(default=0, help_text=_('Number of moderate interactions'))),
                ('minor_interactions', models.PositiveIntegerField(default=0, help_text=_('Number of minor interactions'))),
                ('check_notes', models.TextField(blank=True, help_text=_('Notes about the check'))),
                ('check_duration_seconds', models.PositiveIntegerField(blank=True, null=True, help_text=_('Duration of the check in seconds'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this check was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this check was last updated'))),
            ],
            options={
                'verbose_name': _('Interaction Check'),
                'verbose_name_plural': _('Interaction Checks'),
                'db_table': 'interaction_checks',
                'ordering': ['-check_date'],
            },
        ),
        
        # Create InteractionAlert model
        migrations.CreateModel(
            name='InteractionAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alert_type', models.CharField(
                    choices=[
                        ('interaction_detected', _('Interaction Detected')),
                        ('interaction_reviewed', _('Interaction Reviewed')),
                        ('interaction_resolved', _('Interaction Resolved')),
                        ('new_medication', _('New Medication Added')),
                        ('medication_discontinued', _('Medication Discontinued')),
                        ('dose_changed', _('Dose Changed')),
                        ('patient_risk', _('Patient Risk Assessment'))
                    ],
                    max_length=20,
                    help_text=_('Type of interaction alert')
                )),
                ('alert_priority', models.CharField(
                    choices=[
                        ('low', _('Low')),
                        ('medium', _('Medium')),
                        ('high', _('High')),
                        ('critical', _('Critical'))
                    ],
                    default='medium',
                    max_length=20,
                    help_text=_('Priority level of the alert')
                )),
                ('alert_status', models.CharField(
                    choices=[
                        ('active', _('Active')),
                        ('acknowledged', _('Acknowledged')),
                        ('resolved', _('Resolved')),
                        ('dismissed', _('Dismissed'))
                    ],
                    default='active',
                    max_length=20,
                    help_text=_('Status of the alert')
                )),
                ('alert_title', models.CharField(max_length=200, help_text=_('Title of the alert'))),
                ('alert_message', models.TextField(help_text=_('Message content of the alert'))),
                ('alert_data', models.JSONField(default=dict, help_text=_('Additional data for the alert'))),
                ('alert_date', models.DateTimeField(auto_now_add=True, help_text=_('When this alert was created'))),
                ('acknowledged_by', models.CharField(blank=True, max_length=200, help_text=_('Who acknowledged this alert'))),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True, help_text=_('When this alert was acknowledged'))),
                ('resolved_by', models.CharField(blank=True, max_length=200, help_text=_('Who resolved this alert'))),
                ('resolved_at', models.DateTimeField(blank=True, null=True, help_text=_('When this alert was resolved'))),
                ('resolution_notes', models.TextField(blank=True, help_text=_('Notes about how the alert was resolved'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this alert was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this alert was last updated'))),
            ],
            options={
                'verbose_name': _('Interaction Alert'),
                'verbose_name_plural': _('Interaction Alerts'),
                'db_table': 'interaction_alerts',
                'ordering': ['-alert_date'],
            },
        ),
        
        # Add foreign key relationships
        migrations.AddField(
            model_name='medicationinteraction',
            name='medication1',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interactions_as_med1',
                to='medications.medication',
                help_text=_('First medication in the interaction')
            ),
        ),
        migrations.AddField(
            model_name='medicationinteraction',
            name='medication2',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interactions_as_med2',
                to='medications.medication',
                help_text=_('Second medication in the interaction')
            ),
        ),
        migrations.AddField(
            model_name='patientmedicationinteraction',
            name='interaction',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to='medications.medicationinteraction',
                help_text=_('Medication interaction detected')
            ),
        ),
        migrations.AddField(
            model_name='patientmedicationinteraction',
            name='patient',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='medication_interactions',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this interaction')
            ),
        ),
        migrations.AddField(
            model_name='interactioncheck',
            name='patient',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interaction_checks',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this interaction check')
            ),
        ),
        migrations.AddField(
            model_name='interactioncheck',
            name='prescription',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interaction_checks',
                to='medications.prescription',
                help_text=_('Prescription for this interaction check')
            ),
        ),
        migrations.AddField(
            model_name='interactionalert',
            name='patient',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='interaction_alerts',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this alert')
            ),
        ),
        migrations.AddField(
            model_name='interactionalert',
            name='interaction',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to='medications.medicationinteraction',
                help_text=_('Medication interaction related to this alert')
            ),
        ),
        
        # Create indexes for performance
        migrations.AddIndex(
            model_name='medicationinteraction',
            index=models.Index(fields=['medication1', 'medication2'], name='interaction_medications_idx'),
        ),
        migrations.AddIndex(
            model_name='medicationinteraction',
            index=models.Index(fields=['severity_level'], name='interaction_severity_idx'),
        ),
        migrations.AddIndex(
            model_name='medicationinteraction',
            index=models.Index(fields=['interaction_type'], name='interaction_type_idx'),
        ),
        migrations.AddIndex(
            model_name='medicationinteraction',
            index=models.Index(fields=['is_active'], name='interaction_active_idx'),
        ),
        migrations.AddIndex(
            model_name='patientmedicationinteraction',
            index=models.Index(fields=['patient', 'interaction'], name='patient_interaction_idx'),
        ),
        migrations.AddIndex(
            model_name='patientmedicationinteraction',
            index=models.Index(fields=['interaction_status'], name='patient_interaction_status_idx'),
        ),
        migrations.AddIndex(
            model_name='patientmedicationinteraction',
            index=models.Index(fields=['interaction_date'], name='patient_interaction_date_idx'),
        ),
        migrations.AddIndex(
            model_name='interactioncheck',
            index=models.Index(fields=['check_type'], name='check_type_idx'),
        ),
        migrations.AddIndex(
            model_name='interactioncheck',
            index=models.Index(fields=['check_status'], name='check_status_idx'),
        ),
        migrations.AddIndex(
            model_name='interactioncheck',
            index=models.Index(fields=['check_date'], name='check_date_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionalert',
            index=models.Index(fields=['alert_type'], name='alert_type_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionalert',
            index=models.Index(fields=['alert_priority'], name='alert_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionalert',
            index=models.Index(fields=['alert_status'], name='alert_status_idx'),
        ),
        migrations.AddIndex(
            model_name='interactionalert',
            index=models.Index(fields=['alert_date'], name='alert_date_idx'),
        ),
    ] 