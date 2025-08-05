# Generated manually for MedGuard SA - Add comprehensive reporting capabilities
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0009_add_adherence_tracking'),
    ]

    operations = [
        # Add comprehensive reporting capabilities to Medication model
        
        # Reporting system enabled
        migrations.AddField(
            model_name='medication',
            name='reporting_system_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether comprehensive reporting system is enabled')
            ),
        ),
        
        # Reporting types
        migrations.AddField(
            model_name='medication',
            name='reporting_types',
            field=models.JSONField(
                default=list,
                help_text=_('Types of reports available for this medication')
            ),
        ),
        
        # Reporting frequency
        migrations.AddField(
            model_name='medication',
            name='reporting_frequency',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('real_time', _('Real Time')),
                    ('hourly', _('Hourly')),
                    ('daily', _('Daily')),
                    ('weekly', _('Weekly')),
                    ('monthly', _('Monthly')),
                    ('quarterly', _('Quarterly')),
                    ('yearly', _('Yearly')),
                    ('on_demand', _('On Demand')),
                ],
                default='daily',
                help_text=_('Frequency of report generation')
            ),
        ),
        
        # Reporting schedule
        migrations.AddField(
            model_name='medication',
            name='reporting_schedule',
            field=models.JSONField(
                default=dict,
                help_text=_('Schedule for automated report generation')
            ),
        ),
        
        # Reporting recipients
        migrations.AddField(
            model_name='medication',
            name='reporting_recipients',
            field=models.JSONField(
                default=list,
                help_text=_('Recipients for automated reports')
            ),
        ),
        
        # Reporting delivery methods
        migrations.AddField(
            model_name='medication',
            name='reporting_delivery_methods',
            field=models.JSONField(
                default=list,
                help_text=_('Methods for delivering reports')
            ),
        ),
        
        # Reporting formats
        migrations.AddField(
            model_name='medication',
            name='reporting_formats',
            field=models.JSONField(
                default=list,
                help_text=_('Formats available for reports')
            ),
        ),
        
        # Reporting templates
        migrations.AddField(
            model_name='medication',
            name='reporting_templates',
            field=models.JSONField(
                default=dict,
                help_text=_('Templates for different types of reports')
            ),
        ),
        
        # Reporting customization
        migrations.AddField(
            model_name='medication',
            name='reporting_customization',
            field=models.JSONField(
                default=dict,
                help_text=_('Customization options for reports')
            ),
        ),
        
        # Reporting filters
        migrations.AddField(
            model_name='medication',
            name='reporting_filters',
            field=models.JSONField(
                default=dict,
                help_text=_('Filters available for reports')
            ),
        ),
        
        # Reporting aggregations
        migrations.AddField(
            model_name='medication',
            name='reporting_aggregations',
            field=models.JSONField(
                default=list,
                help_text=_('Aggregation functions available for reports')
            ),
        ),
        
        # Reporting metrics
        migrations.AddField(
            model_name='medication',
            name='reporting_metrics',
            field=models.JSONField(
                default=list,
                help_text=_('Metrics available for reporting')
            ),
        ),
        
        # Reporting KPIs
        migrations.AddField(
            model_name='medication',
            name='reporting_kpis',
            field=models.JSONField(
                default=list,
                help_text=_('Key Performance Indicators for reporting')
            ),
        ),
        
        # Reporting thresholds
        migrations.AddField(
            model_name='medication',
            name='reporting_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Thresholds for reporting alerts')
            ),
        ),
        
        # Reporting alerts enabled
        migrations.AddField(
            model_name='medication',
            name='reporting_alerts_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether reporting alerts are enabled')
            ),
        ),
        
        # Reporting alert conditions
        migrations.AddField(
            model_name='medication',
            name='reporting_alert_conditions',
            field=models.JSONField(
                default=list,
                help_text=_('Conditions that trigger reporting alerts')
            ),
        ),
        
        # Reporting alert recipients
        migrations.AddField(
            model_name='medication',
            name='reporting_alert_recipients',
            field=models.JSONField(
                default=list,
                help_text=_('Recipients for reporting alerts')
            ),
        ),
        
        # Reporting alert frequency
        migrations.AddField(
            model_name='medication',
            name='reporting_alert_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of reporting alerts (hours)')
            ),
        ),
        
        # Last reporting alert
        migrations.AddField(
            model_name='medication',
            name='last_reporting_alert',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time a reporting alert was sent')
            ),
        ),
        
        # Reporting data retention
        migrations.AddField(
            model_name='medication',
            name='reporting_data_retention_days',
            field=models.PositiveIntegerField(
                default=365,
                help_text=_('Number of days to retain reporting data')
            ),
        ),
        
        # Reporting data archival
        migrations.AddField(
            model_name='medication',
            name='reporting_data_archival_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether reporting data archival is enabled')
            ),
        ),
        
        # Reporting data archival schedule
        migrations.AddField(
            model_name='medication',
            name='reporting_data_archival_schedule',
            field=models.JSONField(
                default=dict,
                help_text=_('Schedule for reporting data archival')
            ),
        ),
        
        # Reporting data archival location
        migrations.AddField(
            model_name='medication',
            name='reporting_data_archival_location',
            field=models.CharField(
                max_length=200,
                blank=True,
                help_text=_('Location for archived reporting data')
            ),
        ),
        
        # Reporting data archival format
        migrations.AddField(
            model_name='medication',
            name='reporting_data_archival_format',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('json', _('JSON')),
                    ('csv', _('CSV')),
                    ('xml', _('XML')),
                    ('parquet', _('Parquet')),
                    ('avro', _('Avro')),
                    ('compressed', _('Compressed')),
                ],
                default='json',
                help_text=_('Format for archived reporting data')
            ),
        ),
        
        # Reporting data archival compression
        migrations.AddField(
            model_name='medication',
            name='reporting_data_archival_compression',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('none', _('None')),
                    ('gzip', _('Gzip')),
                    ('bzip2', _('Bzip2')),
                    ('lz4', _('LZ4')),
                    ('snappy', _('Snappy')),
                ],
                default='gzip',
                help_text=_('Compression for archived reporting data')
            ),
        ),
        
        # Reporting performance metrics
        migrations.AddField(
            model_name='medication',
            name='reporting_performance_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance metrics for reporting system')
            ),
        ),
        
        # Reporting generation time
        migrations.AddField(
            model_name='medication',
            name='reporting_generation_time_seconds',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Average time to generate reports (seconds)')
            ),
        ),
        
        # Reporting success rate
        migrations.AddField(
            model_name='medication',
            name='reporting_success_rate',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Success rate of report generation (0-1)')
            ),
        ),
        
        # Reporting error rate
        migrations.AddField(
            model_name='medication',
            name='reporting_error_rate',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Error rate of report generation (0-1)')
            ),
        ),
        
        # Reporting throughput
        migrations.AddField(
            model_name='medication',
            name='reporting_throughput',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Reports generated per hour')
            ),
        ),
        
        # Reporting queue management
        migrations.AddField(
            model_name='medication',
            name='reporting_queue_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether reporting queue is enabled')
            ),
        ),
        
        # Reporting queue priority
        migrations.AddField(
            model_name='medication',
            name='reporting_queue_priority',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('low', _('Low Priority')),
                    ('normal', _('Normal Priority')),
                    ('high', _('High Priority')),
                    ('urgent', _('Urgent Priority')),
                ],
                default='normal',
                help_text=_('Priority level for reporting queue')
            ),
        ),
        
        # Reporting queue position
        migrations.AddField(
            model_name='medication',
            name='reporting_queue_position',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Position in reporting queue')
            ),
        ),
        
        # Reporting queue estimated time
        migrations.AddField(
            model_name='medication',
            name='reporting_queue_estimated_time_minutes',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Estimated time to complete reporting (minutes)')
            ),
        ),
        
        # Reporting batch processing
        migrations.AddField(
            model_name='medication',
            name='reporting_batch_processing_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether batch processing is enabled for reporting')
            ),
        ),
        
        # Reporting batch size
        migrations.AddField(
            model_name='medication',
            name='reporting_batch_size',
            field=models.PositiveIntegerField(
                default=100,
                help_text=_('Size of reporting processing batches')
            ),
        ),
        
        # Reporting batch frequency
        migrations.AddField(
            model_name='medication',
            name='reporting_batch_frequency_hours',
            field=models.PositiveIntegerField(
                default=6,
                help_text=_('Frequency of batch processing (hours)')
            ),
        ),
        
        # Reporting batch success rate
        migrations.AddField(
            model_name='medication',
            name='reporting_batch_success_rate',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Success rate of batch processing (0-1)')
            ),
        ),
        
        # Reporting batch errors
        migrations.AddField(
            model_name='medication',
            name='reporting_batch_errors',
            field=models.JSONField(
                default=list,
                help_text=_('Errors encountered during batch processing')
            ),
        ),
        
        # Reporting batch logs
        migrations.AddField(
            model_name='medication',
            name='reporting_batch_logs',
            field=models.JSONField(
                default=list,
                help_text=_('Logs of batch processing activities')
            ),
        ),
        
        # Reporting cost tracking
        migrations.AddField(
            model_name='medication',
            name='reporting_cost_tracking_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether cost tracking is enabled for reporting')
            ),
        ),
        
        # Reporting cost per report
        migrations.AddField(
            model_name='medication',
            name='reporting_cost_per_report',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=6,
                null=True,
                blank=True,
                help_text=_('Cost per report generation')
            ),
        ),
        
        # Reporting total cost
        migrations.AddField(
            model_name='medication',
            name='reporting_total_cost',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                help_text=_('Total cost of reporting')
            ),
        ),
        
        # Reporting cost currency
        migrations.AddField(
            model_name='medication',
            name='reporting_cost_currency',
            field=models.CharField(
                max_length=3,
                default='USD',
                help_text=_('Currency for reporting costs')
            ),
        ),
        
        # Reporting cost breakdown
        migrations.AddField(
            model_name='medication',
            name='reporting_cost_breakdown',
            field=models.JSONField(
                default=dict,
                help_text=_('Breakdown of reporting costs')
            ),
        ),
        
        # Reporting audit trail
        migrations.AddField(
            model_name='medication',
            name='reporting_audit_trail',
            field=models.JSONField(
                default=list,
                help_text=_('Audit trail for reporting activities')
            ),
        ),
        
        # Reporting configuration
        migrations.AddField(
            model_name='medication',
            name='reporting_config',
            field=models.JSONField(
                default=dict,
                help_text=_('Configuration for reporting system')
            ),
        ),
        
        # Reporting rules
        migrations.AddField(
            model_name='medication',
            name='reporting_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Rules for reporting system')
            ),
        ),
        
        # Reporting exceptions
        migrations.AddField(
            model_name='medication',
            name='reporting_exceptions',
            field=models.JSONField(
                default=list,
                help_text=_('Exceptions to reporting rules')
            ),
        ),
        
        # Add indexes for reporting fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['reporting_system_enabled'], name='medication_reporting_system_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['reporting_frequency'], name='medication_reporting_frequency_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['reporting_queue_priority'], name='medication_reporting_queue_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['reporting_success_rate'], name='medication_reporting_success_rate_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['reporting_generation_time_seconds'], name='medication_reporting_generation_time_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['reporting_alerts_enabled'], name='medication_reporting_alerts_enabled_idx'),
        ),
    ] 