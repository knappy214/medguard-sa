# Generated manually for MedGuard SA prescription workflow state tables
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0010_sa_medication_database'),
    ]

    operations = [
        # Create PrescriptionWorkflowState model
        migrations.CreateModel(
            name='PrescriptionWorkflowState',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(
                    choices=[
                        ('draft', _('Draft')),
                        ('submitted', _('Submitted')),
                        ('under_review', _('Under Review')),
                        ('approved', _('Approved')),
                        ('rejected', _('Rejected')),
                        ('dispensing', _('Dispensing')),
                        ('dispensed', _('Dispensed')),
                        ('completed', _('Completed')),
                        ('cancelled', _('Cancelled')),
                        ('expired', _('Expired'))
                    ],
                    max_length=20,
                    help_text=_('Current workflow state')
                )),
                ('previous_state', models.CharField(
                    blank=True,
                    max_length=20,
                    help_text=_('Previous workflow state')
                )),
                ('state_changed_at', models.DateTimeField(auto_now_add=True, help_text=_('When this state was set'))),
                ('state_changed_by', models.CharField(blank=True, max_length=200, help_text=_('Who changed this state'))),
                ('notes', models.TextField(blank=True, help_text=_('Notes about this state change'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this workflow state was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this workflow state was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Workflow State'),
                'verbose_name_plural': _('Prescription Workflow States'),
                'db_table': 'prescription_workflow_states',
                'ordering': ['-state_changed_at'],
            },
        ),
        
        # Create PrescriptionReview model
        migrations.CreateModel(
            name='PrescriptionReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_type', models.CharField(
                    choices=[
                        ('clinical', _('Clinical Review')),
                        ('pharmaceutical', _('Pharmaceutical Review')),
                        ('insurance', _('Insurance Review')),
                        ('regulatory', _('Regulatory Review')),
                        ('quality', _('Quality Assurance Review'))
                    ],
                    max_length=20,
                    help_text=_('Type of review being performed')
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending', _('Pending')),
                        ('in_progress', _('In Progress')),
                        ('approved', _('Approved')),
                        ('rejected', _('Rejected')),
                        ('requires_changes', _('Requires Changes'))
                    ],
                    default='pending',
                    max_length=20,
                    help_text=_('Status of the review')
                )),
                ('reviewer_name', models.CharField(max_length=200, help_text=_('Name of the reviewer'))),
                ('reviewer_role', models.CharField(blank=True, max_length=100, help_text=_('Role of the reviewer'))),
                ('review_date', models.DateTimeField(help_text=_('Date and time of the review'))),
                ('review_notes', models.TextField(blank=True, help_text=_('Notes from the review'))),
                ('approval_conditions', models.TextField(blank=True, help_text=_('Conditions for approval'))),
                ('rejection_reason', models.TextField(blank=True, help_text=_('Reason for rejection if applicable'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this review was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this review was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Review'),
                'verbose_name_plural': _('Prescription Reviews'),
                'db_table': 'prescription_reviews',
                'ordering': ['-review_date'],
            },
        ),
        
        # Create PrescriptionDispensing model
        migrations.CreateModel(
            name='PrescriptionDispensing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dispensing_status', models.CharField(
                    choices=[
                        ('pending', _('Pending')),
                        ('in_progress', _('In Progress')),
                        ('partially_dispensed', _('Partially Dispensed')),
                        ('fully_dispensed', _('Fully Dispensed')),
                        ('cancelled', _('Cancelled')),
                        ('on_hold', _('On Hold'))
                    ],
                    default='pending',
                    max_length=20,
                    help_text=_('Status of the dispensing process')
                )),
                ('dispenser_name', models.CharField(max_length=200, help_text=_('Name of the person dispensing'))),
                ('dispenser_role', models.CharField(blank=True, max_length=100, help_text=_('Role of the dispenser'))),
                ('dispensing_date', models.DateTimeField(help_text=_('Date and time of dispensing'))),
                ('total_medications', models.PositiveIntegerField(default=0, help_text=_('Total number of medications to dispense'))),
                ('dispensed_medications', models.PositiveIntegerField(default=0, help_text=_('Number of medications dispensed'))),
                ('dispensing_notes', models.TextField(blank=True, help_text=_('Notes about the dispensing process'))),
                ('quality_check_passed', models.BooleanField(default=False, help_text=_('Whether quality check was passed'))),
                ('quality_check_by', models.CharField(blank=True, max_length=200, help_text=_('Who performed the quality check'))),
                ('quality_check_date', models.DateTimeField(blank=True, null=True, help_text=_('When quality check was performed'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this dispensing record was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this dispensing record was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Dispensing'),
                'verbose_name_plural': _('Prescription Dispensings'),
                'db_table': 'prescription_dispensings',
                'ordering': ['-dispensing_date'],
            },
        ),
        
        # Create PrescriptionValidation model
        migrations.CreateModel(
            name='PrescriptionValidation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('validation_type', models.CharField(
                    choices=[
                        ('dosage', _('Dosage Validation')),
                        ('interaction', _('Drug Interaction Check')),
                        ('allergy', _('Allergy Check')),
                        ('contraindication', _('Contraindication Check')),
                        ('pregnancy', _('Pregnancy Safety Check')),
                        ('renal', _('Renal Function Check')),
                        ('hepatic', _('Hepatic Function Check')),
                        ('age', _('Age-Appropriate Check')),
                        ('weight', _('Weight-Based Dosage Check')),
                        ('comprehensive', _('Comprehensive Validation'))
                    ],
                    max_length=20,
                    help_text=_('Type of validation performed')
                )),
                ('validation_status', models.CharField(
                    choices=[
                        ('passed', _('Passed')),
                        ('failed', _('Failed')),
                        ('warning', _('Warning')),
                        ('requires_review', _('Requires Review'))
                    ],
                    max_length=20,
                    help_text=_('Status of the validation')
                )),
                ('validation_date', models.DateTimeField(auto_now_add=True, help_text=_('When validation was performed'))),
                ('validated_by', models.CharField(blank=True, max_length=200, help_text=_('Who performed the validation'))),
                ('validation_notes', models.TextField(blank=True, help_text=_('Notes from the validation'))),
                ('warnings', models.JSONField(default=list, help_text=_('List of warnings found during validation'))),
                ('errors', models.JSONField(default=list, help_text=_('List of errors found during validation'))),
                ('recommendations', models.JSONField(default=list, help_text=_('Recommendations from validation'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this validation was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this validation was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Validation'),
                'verbose_name_plural': _('Prescription Validations'),
                'db_table': 'prescription_validations',
                'ordering': ['-validation_date'],
            },
        ),
        
        # Create PrescriptionAudit model
        migrations.CreateModel(
            name='PrescriptionAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('audit_type', models.CharField(
                    choices=[
                        ('creation', _('Prescription Creation')),
                        ('modification', _('Prescription Modification')),
                        ('state_change', _('State Change')),
                        ('review', _('Review Action')),
                        ('dispensing', _('Dispensing Action')),
                        ('validation', _('Validation Action')),
                        ('cancellation', _('Cancellation')),
                        ('completion', _('Completion'))
                    ],
                    max_length=20,
                    help_text=_('Type of audit event')
                )),
                ('action_performed', models.CharField(max_length=200, help_text=_('Action that was performed'))),
                ('performed_by', models.CharField(max_length=200, help_text=_('Who performed the action'))),
                ('performed_at', models.DateTimeField(auto_now_add=True, help_text=_('When the action was performed'))),
                ('previous_value', models.JSONField(blank=True, null=True, help_text=_('Previous value before change'))),
                ('new_value', models.JSONField(blank=True, null=True, help_text=_('New value after change'))),
                ('reason', models.TextField(blank=True, help_text=_('Reason for the action'))),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, help_text=_('IP address of the user'))),
                ('user_agent', models.TextField(blank=True, help_text=_('User agent string'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this audit record was created'))),
            ],
            options={
                'verbose_name': _('Prescription Audit'),
                'verbose_name_plural': _('Prescription Audits'),
                'db_table': 'prescription_audits',
                'ordering': ['-performed_at'],
            },
        ),
        
        # Add foreign key relationships
        migrations.AddField(
            model_name='prescriptionworkflowstate',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='workflow_states',
                to='medications.prescription',
                help_text=_('Prescription this workflow state belongs to')
            ),
        ),
        migrations.AddField(
            model_name='prescriptionreview',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='reviews',
                to='medications.prescription',
                help_text=_('Prescription being reviewed')
            ),
        ),
        migrations.AddField(
            model_name='prescriptiondispensing',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='dispensings',
                to='medications.prescription',
                help_text=_('Prescription being dispensed')
            ),
        ),
        migrations.AddField(
            model_name='prescriptionvalidation',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='validations',
                to='medications.prescription',
                help_text=_('Prescription being validated')
            ),
        ),
        migrations.AddField(
            model_name='prescriptionaudit',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='audits',
                to='medications.prescription',
                help_text=_('Prescription being audited')
            ),
        ),
        
        # Create indexes for performance
        migrations.AddIndex(
            model_name='prescriptionworkflowstate',
            index=models.Index(fields=['prescription', 'state'], name='workflow_prescription_state_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionworkflowstate',
            index=models.Index(fields=['state_changed_at'], name='workflow_state_changed_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionreview',
            index=models.Index(fields=['prescription', 'review_type'], name='review_prescription_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionreview',
            index=models.Index(fields=['status'], name='review_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptiondispensing',
            index=models.Index(fields=['prescription', 'dispensing_status'], name='dispensing_prescription_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptiondispensing',
            index=models.Index(fields=['dispensing_date'], name='dispensing_date_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionvalidation',
            index=models.Index(fields=['prescription', 'validation_type'], name='validation_prescription_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionvalidation',
            index=models.Index(fields=['validation_status'], name='validation_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionaudit',
            index=models.Index(fields=['prescription', 'audit_type'], name='audit_prescription_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionaudit',
            index=models.Index(fields=['performed_at'], name='audit_performed_at_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionaudit',
            index=models.Index(fields=['performed_by'], name='audit_performed_by_idx'),
        ),
    ] 