# Generated manually for MedGuard SA prescription renewal and reminder systems
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0014_stock_analytics_reporting'),
    ]

    operations = [
        # Create PrescriptionReminder model
        migrations.CreateModel(
            name='PrescriptionReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(
                    choices=[
                        ('renewal_due', _('Renewal Due')),
                        ('expiry_warning', _('Expiry Warning')),
                        ('refill_reminder', _('Refill Reminder')),
                        ('follow_up', _('Follow-up Reminder')),
                        ('medication_review', _('Medication Review')),
                        ('appointment_reminder', _('Appointment Reminder')),
                        ('custom', _('Custom Reminder'))
                    ],
                    max_length=20,
                    help_text=_('Type of prescription reminder')
                )),
                ('reminder_status', models.CharField(
                    choices=[
                        ('scheduled', _('Scheduled')),
                        ('sent', _('Sent')),
                        ('delivered', _('Delivered')),
                        ('read', _('Read')),
                        ('acknowledged', _('Acknowledged')),
                        ('cancelled', _('Cancelled')),
                        ('failed', _('Failed'))
                    ],
                    default='scheduled',
                    max_length=20,
                    help_text=_('Status of the reminder')
                )),
                ('reminder_date', models.DateTimeField(help_text=_('When the reminder should be sent'))),
                ('reminder_sent_at', models.DateTimeField(blank=True, null=True, help_text=_('When the reminder was actually sent'))),
                ('reminder_delivered_at', models.DateTimeField(blank=True, null=True, help_text=_('When the reminder was delivered'))),
                ('reminder_read_at', models.DateTimeField(blank=True, null=True, help_text=_('When the reminder was read'))),
                ('reminder_acknowledged_at', models.DateTimeField(blank=True, null=True, help_text=_('When the reminder was acknowledged'))),
                ('reminder_message', models.TextField(help_text=_('Message content of the reminder'))),
                ('reminder_subject', models.CharField(blank=True, max_length=200, help_text=_('Subject line for the reminder'))),
                ('notification_channels', models.JSONField(default=list, help_text=_('Channels for sending the reminder'))),
                ('reminder_priority', models.CharField(
                    choices=[
                        ('low', _('Low')),
                        ('medium', _('Medium')),
                        ('high', _('High')),
                        ('urgent', _('Urgent'))
                    ],
                    default='medium',
                    max_length=20,
                    help_text=_('Priority level of the reminder')
                )),
                ('reminder_frequency', models.CharField(
                    choices=[
                        ('once', _('Once')),
                        ('daily', _('Daily')),
                        ('weekly', _('Weekly')),
                        ('monthly', _('Monthly')),
                        ('custom', _('Custom'))
                    ],
                    default='once',
                    max_length=20,
                    help_text=_('Frequency of the reminder')
                )),
                ('max_reminders', models.PositiveIntegerField(default=1, help_text=_('Maximum number of reminders to send'))),
                ('reminder_count', models.PositiveIntegerField(default=0, help_text=_('Number of reminders sent so far'))),
                ('reminder_notes', models.TextField(blank=True, help_text=_('Additional notes about the reminder'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this reminder was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this reminder was last updated'))),
            ],
            options={
                'verbose_name': _('Prescription Reminder'),
                'verbose_name_plural': _('Prescription Reminders'),
                'db_table': 'prescription_reminders',
                'ordering': ['reminder_date'],
            },
        ),
        
        # Create RenewalRequest model
        migrations.CreateModel(
            name='RenewalRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('request_number', models.CharField(max_length=100, unique=True, help_text=_('Unique renewal request number'))),
                ('request_status', models.CharField(
                    choices=[
                        ('draft', _('Draft')),
                        ('submitted', _('Submitted')),
                        ('under_review', _('Under Review')),
                        ('approved', _('Approved')),
                        ('rejected', _('Rejected')),
                        ('cancelled', _('Cancelled')),
                        ('completed', _('Completed'))
                    ],
                    default='draft',
                    max_length=20,
                    help_text=_('Status of the renewal request')
                )),
                ('request_date', models.DateTimeField(auto_now_add=True, help_text=_('When this request was created'))),
                ('requested_by', models.CharField(max_length=200, help_text=_('Who requested the renewal'))),
                ('requested_for', models.CharField(max_length=200, help_text=_('Patient name for the renewal'))),
                ('original_prescription_number', models.CharField(max_length=100, help_text=_('Original prescription number'))),
                ('original_prescription_date', models.DateField(help_text=_('Date of original prescription'))),
                ('original_expiry_date', models.DateField(help_text=_('Original prescription expiry date'))),
                ('requested_renewal_date', models.DateField(help_text=_('Requested renewal date'))),
                ('requested_expiry_date', models.DateField(blank=True, null=True, help_text=_('Requested new expiry date'))),
                ('renewal_reason', models.TextField(help_text=_('Reason for renewal request'))),
                ('clinical_justification', models.TextField(blank=True, help_text=_('Clinical justification for renewal'))),
                ('reviewed_by', models.CharField(blank=True, max_length=200, help_text=_('Who reviewed this request'))),
                ('reviewed_at', models.DateTimeField(blank=True, null=True, help_text=_('When this request was reviewed'))),
                ('review_notes', models.TextField(blank=True, help_text=_('Notes from the review'))),
                ('approval_conditions', models.TextField(blank=True, help_text=_('Conditions for approval'))),
                ('rejection_reason', models.TextField(blank=True, help_text=_('Reason for rejection if applicable'))),
                ('approved_expiry_date', models.DateField(blank=True, null=True, help_text=_('Approved expiry date'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this request was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this request was last updated'))),
            ],
            options={
                'verbose_name': _('Renewal Request'),
                'verbose_name_plural': _('Renewal Requests'),
                'db_table': 'renewal_requests',
                'ordering': ['-request_date'],
            },
        ),
        
        # Create RenewalSchedule model
        migrations.CreateModel(
            name='RenewalSchedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('schedule_type', models.CharField(
                    choices=[
                        ('automatic', _('Automatic Renewal')),
                        ('manual', _('Manual Renewal')),
                        ('conditional', _('Conditional Renewal')),
                        ('scheduled', _('Scheduled Renewal'))
                    ],
                    max_length=20,
                    help_text=_('Type of renewal schedule')
                )),
                ('renewal_frequency', models.CharField(
                    choices=[
                        ('monthly', _('Monthly')),
                        ('quarterly', _('Quarterly')),
                        ('biannual', _('Biannual')),
                        ('annual', _('Annual')),
                        ('custom', _('Custom'))
                    ],
                    max_length=20,
                    help_text=_('Frequency of renewals')
                )),
                ('renewal_interval_days', models.PositiveIntegerField(help_text=_('Interval between renewals in days'))),
                ('next_renewal_date', models.DateField(help_text=_('Next scheduled renewal date'))),
                ('last_renewal_date', models.DateField(blank=True, null=True, help_text=_('Last renewal date'))),
                ('total_renewals', models.PositiveIntegerField(default=0, help_text=_('Total number of renewals made'))),
                ('max_renewals', models.PositiveIntegerField(blank=True, null=True, help_text=_('Maximum number of renewals allowed'))),
                ('is_active', models.BooleanField(default=True, help_text=_('Whether this schedule is active'))),
                ('auto_renewal_enabled', models.BooleanField(default=False, help_text=_('Whether automatic renewal is enabled'))),
                ('renewal_conditions', models.JSONField(default=dict, help_text=_('Conditions for renewal'))),
                ('renewal_notes', models.TextField(blank=True, help_text=_('Notes about the renewal schedule'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this schedule was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this schedule was last updated'))),
            ],
            options={
                'verbose_name': _('Renewal Schedule'),
                'verbose_name_plural': _('Renewal Schedules'),
                'db_table': 'renewal_schedules',
                'ordering': ['next_renewal_date'],
            },
        ),
        
        # Create RenewalHistory model
        migrations.CreateModel(
            name='RenewalHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('renewal_date', models.DateTimeField(auto_now_add=True, help_text=_('When this renewal was made'))),
                ('renewal_type', models.CharField(
                    choices=[
                        ('automatic', _('Automatic Renewal')),
                        ('manual', _('Manual Renewal')),
                        ('emergency', _('Emergency Renewal')),
                        ('conditional', _('Conditional Renewal'))
                    ],
                    max_length=20,
                    help_text=_('Type of renewal')
                )),
                ('renewal_method', models.CharField(
                    choices=[
                        ('system', _('System Generated')),
                        ('pharmacist', _('Pharmacist')),
                        ('doctor', _('Doctor')),
                        ('patient', _('Patient Request')),
                        ('caregiver', _('Caregiver'))
                    ],
                    max_length=20,
                    help_text=_('Method of renewal')
                )),
                ('renewed_by', models.CharField(max_length=200, help_text=_('Who made the renewal'))),
                ('previous_expiry_date', models.DateField(help_text=_('Previous expiry date'))),
                ('new_expiry_date', models.DateField(help_text=_('New expiry date'))),
                ('renewal_duration_days', models.PositiveIntegerField(help_text=_('Duration of renewal in days'))),
                ('renewal_reason', models.TextField(blank=True, help_text=_('Reason for renewal'))),
                ('renewal_notes', models.TextField(blank=True, help_text=_('Notes about the renewal'))),
                ('renewal_conditions', models.JSONField(default=dict, help_text=_('Conditions applied to this renewal'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this history record was created'))),
            ],
            options={
                'verbose_name': _('Renewal History'),
                'verbose_name_plural': _('Renewal Histories'),
                'db_table': 'renewal_histories',
                'ordering': ['-renewal_date'],
            },
        ),
        
        # Create NotificationTemplate model
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('template_name', models.CharField(max_length=200, unique=True, help_text=_('Name of the notification template'))),
                ('template_type', models.CharField(
                    choices=[
                        ('email', _('Email Template')),
                        ('sms', _('SMS Template')),
                        ('push', _('Push Notification Template')),
                        ('in_app', _('In-App Notification Template')),
                        ('letter', _('Letter Template'))
                    ],
                    max_length=20,
                    help_text=_('Type of notification template')
                )),
                ('template_subject', models.CharField(blank=True, max_length=200, help_text=_('Subject line for the notification'))),
                ('template_body', models.TextField(help_text=_('Body content of the notification template'))),
                ('template_variables', models.JSONField(default=list, help_text=_('Variables available in this template'))),
                ('template_language', models.CharField(default='en', max_length=10, help_text=_('Language of the template'))),
                ('is_active', models.BooleanField(default=True, help_text=_('Whether this template is active'))),
                ('template_description', models.TextField(blank=True, help_text=_('Description of the template'))),
                ('created_by', models.CharField(blank=True, max_length=200, help_text=_('Who created this template'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this template was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this template was last updated'))),
            ],
            options={
                'verbose_name': _('Notification Template'),
                'verbose_name_plural': _('Notification Templates'),
                'db_table': 'notification_templates',
                'ordering': ['template_name'],
            },
        ),
        
        # Add foreign key relationships
        migrations.AddField(
            model_name='prescriptionreminder',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='reminders',
                to='medications.prescription',
                help_text=_('Prescription for this reminder')
            ),
        ),
        migrations.AddField(
            model_name='prescriptionreminder',
            name='patient',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='prescription_reminders',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this reminder')
            ),
        ),
        migrations.AddField(
            model_name='renewalrequest',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='renewal_requests',
                to='medications.prescription',
                help_text=_('Prescription for this renewal request')
            ),
        ),
        migrations.AddField(
            model_name='renewalrequest',
            name='patient',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='renewal_requests',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this renewal request')
            ),
        ),
        migrations.AddField(
            model_name='renewalschedule',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='renewal_schedules',
                to='medications.prescription',
                help_text=_('Prescription for this renewal schedule')
            ),
        ),
        migrations.AddField(
            model_name='renewalschedule',
            name='patient',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='renewal_schedules',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this renewal schedule')
            ),
        ),
        migrations.AddField(
            model_name='renewalhistory',
            name='prescription',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='renewal_history',
                to='medications.prescription',
                help_text=_('Prescription for this renewal history')
            ),
        ),
        migrations.AddField(
            model_name='renewalhistory',
            name='patient',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='renewal_history',
                to='medications.prescriptionpatient',
                help_text=_('Patient for this renewal history')
            ),
        ),
        
        # Create indexes for performance
        migrations.AddIndex(
            model_name='prescriptionreminder',
            index=models.Index(fields=['reminder_type'], name='prescription_reminder_type_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionreminder',
            index=models.Index(fields=['reminder_status'], name='prescription_reminder_status_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionreminder',
            index=models.Index(fields=['reminder_date'], name='prescription_reminder_date_idx'),
        ),
        migrations.AddIndex(
            model_name='prescriptionreminder',
            index=models.Index(fields=['patient', 'reminder_type'], name='prescription_reminder_patient_type_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['request_status'], name='renewal_request_status_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['request_date'], name='renewal_request_date_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalrequest',
            index=models.Index(fields=['original_prescription_number'], name='renewal_request_prescription_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalschedule',
            index=models.Index(fields=['schedule_type'], name='renewal_schedule_type_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalschedule',
            index=models.Index(fields=['next_renewal_date'], name='renewal_schedule_next_date_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalschedule',
            index=models.Index(fields=['is_active'], name='renewal_schedule_active_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalhistory',
            index=models.Index(fields=['renewal_type'], name='renewal_history_type_idx'),
        ),
        migrations.AddIndex(
            model_name='renewalhistory',
            index=models.Index(fields=['renewal_date'], name='renewal_history_date_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['template_type'], name='notification_template_type_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['template_language'], name='notification_template_language_idx'),
        ),
        migrations.AddIndex(
            model_name='notificationtemplate',
            index=models.Index(fields=['is_active'], name='notification_template_active_idx'),
        ),
    ] 