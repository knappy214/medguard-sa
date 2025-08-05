# Generated manually for MedGuard SA - Add prescription renewal automation
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0006_add_interaction_tracking'),
    ]

    operations = [
        # Add prescription renewal automation to Medication model
        
        # Renewal system enabled
        migrations.AddField(
            model_name='medication',
            name='renewal_system_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether prescription renewal automation is enabled')
            ),
        ),
        
        # Auto-renewal enabled
        migrations.AddField(
            model_name='medication',
            name='auto_renewal_enabled',
            field=models.BooleanField(
                default=False,
                help_text=_('Whether automatic prescription renewal is enabled')
            ),
        ),
        
        # Renewal eligibility criteria
        migrations.AddField(
            model_name='medication',
            name='renewal_eligibility_criteria',
            field=models.JSONField(
                default=dict,
                help_text=_('Criteria for prescription renewal eligibility')
            ),
        ),
        
        # Renewal frequency
        migrations.AddField(
            model_name='medication',
            name='renewal_frequency_days',
            field=models.PositiveIntegerField(
                default=30,
                help_text=_('Frequency of prescription renewals in days')
            ),
        ),
        
        # Renewal lead time
        migrations.AddField(
            model_name='medication',
            name='renewal_lead_time_days',
            field=models.PositiveIntegerField(
                default=7,
                help_text=_('Lead time before expiry to initiate renewal (days)')
            ),
        ),
        
        # Renewal reminder frequency
        migrations.AddField(
            model_name='medication',
            name='renewal_reminder_frequency_days',
            field=models.PositiveIntegerField(
                default=3,
                help_text=_('Frequency of renewal reminders (days)')
            ),
        ),
        
        # Renewal approval required
        migrations.AddField(
            model_name='medication',
            name='renewal_approval_required',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether renewal requires approval')
            ),
        ),
        
        # Renewal approval workflow
        migrations.AddField(
            model_name='medication',
            name='renewal_approval_workflow',
            field=models.JSONField(
                default=list,
                help_text=_('Workflow for renewal approval process')
            ),
        ),
        
        # Renewal approval timeout
        migrations.AddField(
            model_name='medication',
            name='renewal_approval_timeout_hours',
            field=models.PositiveIntegerField(
                default=72,
                help_text=_('Timeout for renewal approval (hours)')
            ),
        ),
        
        # Renewal auto-approval conditions
        migrations.AddField(
            model_name='medication',
            name='renewal_auto_approval_conditions',
            field=models.JSONField(
                default=dict,
                help_text=_('Conditions for automatic renewal approval')
            ),
        ),
        
        # Renewal rejection reasons
        migrations.AddField(
            model_name='medication',
            name='renewal_rejection_reasons',
            field=models.JSONField(
                default=list,
                help_text=_('Common reasons for renewal rejection')
            ),
        ),
        
        # Renewal history
        migrations.AddField(
            model_name='medication',
            name='renewal_history',
            field=models.JSONField(
                default=list,
                help_text=_('History of prescription renewals')
            ),
        ),
        
        # Renewal statistics
        migrations.AddField(
            model_name='medication',
            name='renewal_statistics',
            field=models.JSONField(
                default=dict,
                help_text=_('Statistics about prescription renewals')
            ),
        ),
        
        # Renewal success rate
        migrations.AddField(
            model_name='medication',
            name='renewal_success_rate',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Success rate of prescription renewals (0-1)')
            ),
        ),
        
        # Renewal average processing time
        migrations.AddField(
            model_name='medication',
            name='renewal_avg_processing_time_hours',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Average processing time for renewals (hours)')
            ),
        ),
        
        # Renewal notification settings
        migrations.AddField(
            model_name='medication',
            name='renewal_notifications_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether renewal notifications are enabled')
            ),
        ),
        
        # Renewal notification recipients
        migrations.AddField(
            model_name='medication',
            name='renewal_notification_recipients',
            field=models.JSONField(
                default=list,
                help_text=_('Recipients for renewal notifications')
            ),
        ),
        
        # Renewal notification templates
        migrations.AddField(
            model_name='medication',
            name='renewal_notification_templates',
            field=models.JSONField(
                default=dict,
                help_text=_('Templates for renewal notifications')
            ),
        ),
        
        # Renewal notification frequency
        migrations.AddField(
            model_name='medication',
            name='renewal_notification_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of renewal notifications (hours)')
            ),
        ),
        
        # Last renewal notification
        migrations.AddField(
            model_name='medication',
            name='last_renewal_notification',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time a renewal notification was sent')
            ),
        ),
        
        # Renewal scheduling
        migrations.AddField(
            model_name='medication',
            name='renewal_scheduling_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether renewal scheduling is enabled')
            ),
        ),
        
        # Renewal scheduling algorithm
        migrations.AddField(
            model_name='medication',
            name='renewal_scheduling_algorithm',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('simple', _('Simple Scheduling')),
                    ('smart', _('Smart Scheduling')),
                    ('ai_ml', _('AI/ML Based')),
                    ('custom', _('Custom Algorithm')),
                ],
                default='smart',
                help_text=_('Algorithm used for renewal scheduling')
            ),
        ),
        
        # Renewal scheduling parameters
        migrations.AddField(
            model_name='medication',
            name='renewal_scheduling_params',
            field=models.JSONField(
                default=dict,
                help_text=_('Parameters for renewal scheduling algorithm')
            ),
        ),
        
        # Renewal scheduling calendar
        migrations.AddField(
            model_name='medication',
            name='renewal_scheduling_calendar',
            field=models.JSONField(
                default=dict,
                help_text=_('Calendar settings for renewal scheduling')
            ),
        ),
        
        # Renewal scheduling blackout dates
        migrations.AddField(
            model_name='medication',
            name='renewal_scheduling_blackout_dates',
            field=models.JSONField(
                default=list,
                help_text=_('Dates when renewals should not be scheduled')
            ),
        ),
        
        # Renewal scheduling priority
        migrations.AddField(
            model_name='medication',
            name='renewal_scheduling_priority',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('low', _('Low Priority')),
                    ('normal', _('Normal Priority')),
                    ('high', _('High Priority')),
                    ('urgent', _('Urgent Priority')),
                ],
                default='normal',
                help_text=_('Priority level for renewal scheduling')
            ),
        ),
        
        # Renewal batch processing
        migrations.AddField(
            model_name='medication',
            name='renewal_batch_processing_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether batch processing is enabled for renewals')
            ),
        ),
        
        # Renewal batch size
        migrations.AddField(
            model_name='medication',
            name='renewal_batch_size',
            field=models.PositiveIntegerField(
                default=100,
                help_text=_('Size of renewal processing batches')
            ),
        ),
        
        # Renewal batch frequency
        migrations.AddField(
            model_name='medication',
            name='renewal_batch_frequency_hours',
            field=models.PositiveIntegerField(
                default=6,
                help_text=_('Frequency of renewal batch processing (hours)')
            ),
        ),
        
        # Renewal batch processing time
        migrations.AddField(
            model_name='medication',
            name='renewal_batch_processing_time_minutes',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Time taken for batch processing (minutes)')
            ),
        ),
        
        # Renewal batch success rate
        migrations.AddField(
            model_name='medication',
            name='renewal_batch_success_rate',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Success rate of batch processing (0-1)')
            ),
        ),
        
        # Renewal batch errors
        migrations.AddField(
            model_name='medication',
            name='renewal_batch_errors',
            field=models.JSONField(
                default=list,
                help_text=_('Errors encountered during batch processing')
            ),
        ),
        
        # Renewal batch logs
        migrations.AddField(
            model_name='medication',
            name='renewal_batch_logs',
            field=models.JSONField(
                default=list,
                help_text=_('Logs of batch processing activities')
            ),
        ),
        
        # Renewal performance metrics
        migrations.AddField(
            model_name='medication',
            name='renewal_performance_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance metrics for renewal system')
            ),
        ),
        
        # Renewal system configuration
        migrations.AddField(
            model_name='medication',
            name='renewal_system_config',
            field=models.JSONField(
                default=dict,
                help_text=_('Configuration for renewal system')
            ),
        ),
        
        # Renewal system rules
        migrations.AddField(
            model_name='medication',
            name='renewal_system_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Rules for renewal system')
            ),
        ),
        
        # Renewal system exceptions
        migrations.AddField(
            model_name='medication',
            name='renewal_system_exceptions',
            field=models.JSONField(
                default=list,
                help_text=_('Exceptions to renewal system rules')
            ),
        ),
        
        # Renewal system audit trail
        migrations.AddField(
            model_name='medication',
            name='renewal_system_audit_trail',
            field=models.JSONField(
                default=list,
                help_text=_('Audit trail for renewal system activities')
            ),
        ),
        
        # Add indexes for renewal system fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['renewal_system_enabled'], name='medication_renewal_system_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['auto_renewal_enabled'], name='medication_auto_renewal_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['renewal_approval_required'], name='medication_renewal_approval_required_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['renewal_success_rate'], name='medication_renewal_success_rate_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['renewal_scheduling_priority'], name='medication_renewal_scheduling_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['renewal_batch_processing_enabled'], name='medication_renewal_batch_enabled_idx'),
        ),
    ] 