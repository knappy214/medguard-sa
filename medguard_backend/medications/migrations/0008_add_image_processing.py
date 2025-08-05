# Generated manually for MedGuard SA - Add medication image processing fields
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0007_add_renewal_system'),
    ]

    operations = [
        # Add medication image processing fields to Medication model
        
        # Image processing system enabled
        migrations.AddField(
            model_name='medication',
            name='image_processing_system_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether image processing system is enabled')
            ),
        ),
        
        # Image processing pipeline
        migrations.AddField(
            model_name='medication',
            name='image_processing_pipeline',
            field=models.JSONField(
                default=list,
                help_text=_('Pipeline of image processing steps')
            ),
        ),
        
        # Image processing quality settings
        migrations.AddField(
            model_name='medication',
            name='image_processing_quality_settings',
            field=models.JSONField(
                default=dict,
                help_text=_('Quality settings for image processing')
            ),
        ),
        
        # Image processing formats
        migrations.AddField(
            model_name='medication',
            name='image_processing_formats',
            field=models.JSONField(
                default=list,
                help_text=_('Supported image formats for processing')
            ),
        ),
        
        # Image processing algorithms
        migrations.AddField(
            model_name='medication',
            name='image_processing_algorithms',
            field=models.JSONField(
                default=dict,
                help_text=_('Algorithms used for different image processing tasks')
            ),
        ),
        
        # Image processing parameters
        migrations.AddField(
            model_name='medication',
            name='image_processing_parameters',
            field=models.JSONField(
                default=dict,
                help_text=_('Parameters for image processing algorithms')
            ),
        ),
        
        # Image processing performance metrics
        migrations.AddField(
            model_name='medication',
            name='image_processing_performance',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance metrics for image processing')
            ),
        ),
        
        # Image processing accuracy
        migrations.AddField(
            model_name='medication',
            name='image_processing_accuracy',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Accuracy of image processing (0-1)')
            ),
        ),
        
        # Image processing speed
        migrations.AddField(
            model_name='medication',
            name='image_processing_speed_ms',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Average processing speed in milliseconds')
            ),
        ),
        
        # Image processing throughput
        migrations.AddField(
            model_name='medication',
            name='image_processing_throughput',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Images processed per second')
            ),
        ),
        
        # Image processing queue management
        migrations.AddField(
            model_name='medication',
            name='image_processing_queue_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether image processing queue is enabled')
            ),
        ),
        
        # Image processing queue priority
        migrations.AddField(
            model_name='medication',
            name='image_processing_queue_priority',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('low', _('Low Priority')),
                    ('normal', _('Normal Priority')),
                    ('high', _('High Priority')),
                    ('urgent', _('Urgent Priority')),
                ],
                default='normal',
                help_text=_('Priority level for image processing queue')
            ),
        ),
        
        # Image processing queue position
        migrations.AddField(
            model_name='medication',
            name='image_processing_queue_position',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Position in image processing queue')
            ),
        ),
        
        # Image processing queue estimated time
        migrations.AddField(
            model_name='medication',
            name='image_processing_queue_estimated_time_minutes',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Estimated time to complete processing (minutes)')
            ),
        ),
        
        # Image processing batch processing
        migrations.AddField(
            model_name='medication',
            name='image_processing_batch_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether batch processing is enabled for images')
            ),
        ),
        
        # Image processing batch size
        migrations.AddField(
            model_name='medication',
            name='image_processing_batch_size',
            field=models.PositiveIntegerField(
                default=50,
                help_text=_('Size of image processing batches')
            ),
        ),
        
        # Image processing batch frequency
        migrations.AddField(
            model_name='medication',
            name='image_processing_batch_frequency_minutes',
            field=models.PositiveIntegerField(
                default=30,
                help_text=_('Frequency of batch processing (minutes)')
            ),
        ),
        
        # Image processing batch success rate
        migrations.AddField(
            model_name='medication',
            name='image_processing_batch_success_rate',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Success rate of batch processing (0-1)')
            ),
        ),
        
        # Image processing batch errors
        migrations.AddField(
            model_name='medication',
            name='image_processing_batch_errors',
            field=models.JSONField(
                default=list,
                help_text=_('Errors encountered during batch processing')
            ),
        ),
        
        # Image processing batch logs
        migrations.AddField(
            model_name='medication',
            name='image_processing_batch_logs',
            field=models.JSONField(
                default=list,
                help_text=_('Logs of batch processing activities')
            ),
        ),
        
        # Image processing error handling
        migrations.AddField(
            model_name='medication',
            name='image_processing_error_handling',
            field=models.JSONField(
                default=dict,
                help_text=_('Error handling configuration for image processing')
            ),
        ),
        
        # Image processing retry settings
        migrations.AddField(
            model_name='medication',
            name='image_processing_retry_settings',
            field=models.JSONField(
                default=dict,
                help_text=_('Retry settings for failed image processing')
            ),
        ),
        
        # Image processing fallback options
        migrations.AddField(
            model_name='medication',
            name='image_processing_fallback_options',
            field=models.JSONField(
                default=list,
                help_text=_('Fallback options for image processing failures')
            ),
        ),
        
        # Image processing validation
        migrations.AddField(
            model_name='medication',
            name='image_processing_validation_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether image processing validation is enabled')
            ),
        ),
        
        # Image processing validation rules
        migrations.AddField(
            model_name='medication',
            name='image_processing_validation_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Validation rules for image processing results')
            ),
        ),
        
        # Image processing validation results
        migrations.AddField(
            model_name='medication',
            name='image_processing_validation_results',
            field=models.JSONField(
                default=dict,
                help_text=_('Results of image processing validation')
            ),
        ),
        
        # Image processing quality assurance
        migrations.AddField(
            model_name='medication',
            name='image_processing_qa_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether quality assurance is enabled for image processing')
            ),
        ),
        
        # Image processing QA metrics
        migrations.AddField(
            model_name='medication',
            name='image_processing_qa_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Quality assurance metrics for image processing')
            ),
        ),
        
        # Image processing QA thresholds
        migrations.AddField(
            model_name='medication',
            name='image_processing_qa_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Quality assurance thresholds for image processing')
            ),
        ),
        
        # Image processing QA alerts
        migrations.AddField(
            model_name='medication',
            name='image_processing_qa_alerts',
            field=models.JSONField(
                default=list,
                help_text=_('Quality assurance alerts for image processing')
            ),
        ),
        
        # Image processing monitoring
        migrations.AddField(
            model_name='medication',
            name='image_processing_monitoring_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether image processing monitoring is enabled')
            ),
        ),
        
        # Image processing monitoring metrics
        migrations.AddField(
            model_name='medication',
            name='image_processing_monitoring_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Monitoring metrics for image processing')
            ),
        ),
        
        # Image processing monitoring alerts
        migrations.AddField(
            model_name='medication',
            name='image_processing_monitoring_alerts',
            field=models.JSONField(
                default=list,
                help_text=_('Monitoring alerts for image processing')
            ),
        ),
        
        # Image processing monitoring thresholds
        migrations.AddField(
            model_name='medication',
            name='image_processing_monitoring_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Monitoring thresholds for image processing')
            ),
        ),
        
        # Image processing cost tracking
        migrations.AddField(
            model_name='medication',
            name='image_processing_cost_tracking_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether cost tracking is enabled for image processing')
            ),
        ),
        
        # Image processing cost per image
        migrations.AddField(
            model_name='medication',
            name='image_processing_cost_per_image',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=6,
                null=True,
                blank=True,
                help_text=_('Cost per image for processing')
            ),
        ),
        
        # Image processing total cost
        migrations.AddField(
            model_name='medication',
            name='image_processing_total_cost',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                help_text=_('Total cost of image processing')
            ),
        ),
        
        # Image processing cost currency
        migrations.AddField(
            model_name='medication',
            name='image_processing_cost_currency',
            field=models.CharField(
                max_length=3,
                default='USD',
                help_text=_('Currency for image processing costs')
            ),
        ),
        
        # Image processing cost breakdown
        migrations.AddField(
            model_name='medication',
            name='image_processing_cost_breakdown',
            field=models.JSONField(
                default=dict,
                help_text=_('Breakdown of image processing costs')
            ),
        ),
        
        # Image processing audit trail
        migrations.AddField(
            model_name='medication',
            name='image_processing_audit_trail',
            field=models.JSONField(
                default=list,
                help_text=_('Audit trail for image processing activities')
            ),
        ),
        
        # Image processing configuration
        migrations.AddField(
            model_name='medication',
            name='image_processing_config',
            field=models.JSONField(
                default=dict,
                help_text=_('Configuration for image processing system')
            ),
        ),
        
        # Image processing rules
        migrations.AddField(
            model_name='medication',
            name='image_processing_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Rules for image processing')
            ),
        ),
        
        # Image processing exceptions
        migrations.AddField(
            model_name='medication',
            name='image_processing_exceptions',
            field=models.JSONField(
                default=list,
                help_text=_('Exceptions to image processing rules')
            ),
        ),
        
        # Add indexes for image processing fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['image_processing_system_enabled'], name='medication_image_processing_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['image_processing_queue_priority'], name='medication_image_processing_priority_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['image_processing_accuracy'], name='medication_image_processing_accuracy_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['image_processing_speed_ms'], name='medication_image_processing_speed_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['image_processing_batch_enabled'], name='medication_image_processing_batch_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['image_processing_validation_enabled'], name='medication_image_processing_validation_idx'),
        ),
    ] 