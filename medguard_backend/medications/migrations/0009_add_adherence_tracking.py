# Generated manually for MedGuard SA - Add medication adherence monitoring
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0008_add_image_processing'),
    ]

    operations = [
        # Add medication adherence monitoring to Medication model
        
        # Adherence tracking enabled
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether medication adherence tracking is enabled')
            ),
        ),
        
        # Adherence tracking method
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_method',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('manual', _('Manual Entry')),
                    ('smart_pillbox', _('Smart Pillbox')),
                    ('mobile_app', _('Mobile App')),
                    ('bluetooth_device', _('Bluetooth Device')),
                    ('rfid', _('RFID Tracking')),
                    ('qr_code', _('QR Code Scanning')),
                    ('ai_vision', _('AI Vision Recognition')),
                    ('hybrid', _('Hybrid Method')),
                ],
                default='manual',
                help_text=_('Method used for adherence tracking')
            ),
        ),
        
        # Adherence tracking frequency
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of adherence tracking checks (hours)')
            ),
        ),
        
        # Adherence tracking accuracy
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_accuracy',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Accuracy of adherence tracking (0-1)')
            ),
        ),
        
        # Adherence tracking precision
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_precision',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Precision of adherence tracking (0-1)')
            ),
        ),
        
        # Adherence tracking recall
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_recall',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Recall of adherence tracking (0-1)')
            ),
        ),
        
        # Adherence tracking F1 score
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_f1_score',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('F1 score of adherence tracking (0-1)')
            ),
        ),
        
        # Adherence tracking performance metrics
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_performance',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance metrics for adherence tracking')
            ),
        ),
        
        # Adherence tracking algorithm
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_algorithm',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('simple', _('Simple Rule-Based')),
                    ('advanced', _('Advanced Algorithmic')),
                    ('ai_ml', _('AI/ML Based')),
                    ('hybrid', _('Hybrid Approach')),
                    ('custom', _('Custom Algorithm')),
                ],
                default='advanced',
                help_text=_('Algorithm used for adherence tracking')
            ),
        ),
        
        # Adherence tracking parameters
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_params',
            field=models.JSONField(
                default=dict,
                help_text=_('Parameters for adherence tracking algorithm')
            ),
        ),
        
        # Adherence tracking configuration
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_config',
            field=models.JSONField(
                default=dict,
                help_text=_('Configuration for adherence tracking')
            ),
        ),
        
        # Adherence tracking rules
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Rules for adherence tracking')
            ),
        ),
        
        # Adherence tracking exceptions
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_exceptions',
            field=models.JSONField(
                default=list,
                help_text=_('Exceptions to adherence tracking rules')
            ),
        ),
        
        # Adherence tracking whitelist
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_whitelist',
            field=models.JSONField(
                default=list,
                help_text=_('Whitelist for adherence tracking')
            ),
        ),
        
        # Adherence tracking blacklist
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_blacklist',
            field=models.JSONField(
                default=list,
                help_text=_('Blacklist for adherence tracking')
            ),
        ),
        
        # Adherence tracking data sources
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_data_sources',
            field=models.JSONField(
                default=list,
                help_text=_('Data sources used for adherence tracking')
            ),
        ),
        
        # Adherence tracking last data update
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_last_data_update',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time adherence data was updated')
            ),
        ),
        
        # Adherence tracking data version
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_data_version',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text=_('Version of adherence tracking data')
            ),
        ),
        
        # Adherence tracking alerts enabled
        migrations.AddField(
            model_name='medication',
            name='adherence_alerts_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether adherence alerts are enabled')
            ),
        ),
        
        # Adherence alert thresholds
        migrations.AddField(
            model_name='medication',
            name='adherence_alert_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Thresholds for different types of adherence alerts')
            ),
        ),
        
        # Adherence alert recipients
        migrations.AddField(
            model_name='medication',
            name='adherence_alert_recipients',
            field=models.JSONField(
                default=list,
                help_text=_('Recipients for adherence alerts')
            ),
        ),
        
        # Adherence alert frequency
        migrations.AddField(
            model_name='medication',
            name='adherence_alert_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of adherence alerts (hours)')
            ),
        ),
        
        # Last adherence alert
        migrations.AddField(
            model_name='medication',
            name='last_adherence_alert',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time an adherence alert was sent')
            ),
        ),
        
        # Adherence tracking history
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_history',
            field=models.JSONField(
                default=list,
                help_text=_('History of adherence tracking activities')
            ),
        ),
        
        # Adherence tracking logs
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_logs',
            field=models.JSONField(
                default=list,
                help_text=_('Detailed logs of adherence tracking activities')
            ),
        ),
        
        # Adherence tracking audit trail
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_audit_trail',
            field=models.JSONField(
                default=list,
                help_text=_('Audit trail for adherence tracking activities')
            ),
        ),
        
        # Adherence tracking metadata
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_metadata',
            field=models.JSONField(
                default=dict,
                help_text=_('Additional metadata for adherence tracking')
            ),
        ),
        
        # Adherence tracking cost tracking
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_cost_tracking_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether cost tracking is enabled for adherence tracking')
            ),
        ),
        
        # Adherence tracking cost per tracking
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_cost_per_tracking',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=6,
                null=True,
                blank=True,
                help_text=_('Cost per adherence tracking event')
            ),
        ),
        
        # Adherence tracking total cost
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_total_cost',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                help_text=_('Total cost of adherence tracking')
            ),
        ),
        
        # Adherence tracking cost currency
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_cost_currency',
            field=models.CharField(
                max_length=3,
                default='USD',
                help_text=_('Currency for adherence tracking costs')
            ),
        ),
        
        # Adherence tracking cost breakdown
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_cost_breakdown',
            field=models.JSONField(
                default=dict,
                help_text=_('Breakdown of adherence tracking costs')
            ),
        ),
        
        # Adherence tracking monitoring
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_monitoring_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether adherence tracking monitoring is enabled')
            ),
        ),
        
        # Adherence tracking monitoring metrics
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_monitoring_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Monitoring metrics for adherence tracking')
            ),
        ),
        
        # Adherence tracking monitoring alerts
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_monitoring_alerts',
            field=models.JSONField(
                default=list,
                help_text=_('Monitoring alerts for adherence tracking')
            ),
        ),
        
        # Adherence tracking monitoring thresholds
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_monitoring_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Monitoring thresholds for adherence tracking')
            ),
        ),
        
        # Adherence tracking quality assurance
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_qa_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether quality assurance is enabled for adherence tracking')
            ),
        ),
        
        # Adherence tracking QA metrics
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_qa_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Quality assurance metrics for adherence tracking')
            ),
        ),
        
        # Adherence tracking QA thresholds
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_qa_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Quality assurance thresholds for adherence tracking')
            ),
        ),
        
        # Adherence tracking QA alerts
        migrations.AddField(
            model_name='medication',
            name='adherence_tracking_qa_alerts',
            field=models.JSONField(
                default=list,
                help_text=_('Quality assurance alerts for adherence tracking')
            ),
        ),
        
        # Add indexes for adherence tracking fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['adherence_tracking_enabled'], name='medication_adherence_tracking_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['adherence_tracking_method'], name='medication_adherence_tracking_method_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['adherence_tracking_accuracy'], name='medication_adherence_tracking_accuracy_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['adherence_tracking_algorithm'], name='medication_adherence_tracking_algorithm_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['adherence_alerts_enabled'], name='medication_adherence_alerts_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['adherence_tracking_last_data_update'], name='medication_adherence_tracking_last_update_idx'),
        ),
    ] 