# Generated manually for MedGuard SA - Add database performance optimizations
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0010_add_reporting_fields'),
    ]

    operations = [
        # Add database performance optimizations and indexes
        
        # Performance optimization settings
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether performance optimization is enabled')
            ),
        ),
        
        # Performance optimization level
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_level',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('basic', _('Basic Optimization')),
                    ('standard', _('Standard Optimization')),
                    ('advanced', _('Advanced Optimization')),
                    ('maximum', _('Maximum Optimization')),
                ],
                default='standard',
                help_text=_('Level of performance optimization applied')
            ),
        ),
        
        # Performance optimization last applied
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_last_applied',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time performance optimization was applied')
            ),
        ),
        
        # Performance optimization metrics
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Metrics for performance optimization')
            ),
        ),
        
        # Performance optimization configuration
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_config',
            field=models.JSONField(
                default=dict,
                help_text=_('Configuration for performance optimization')
            ),
        ),
        
        # Performance optimization rules
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Rules for performance optimization')
            ),
        ),
        
        # Performance optimization exceptions
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_exceptions',
            field=models.JSONField(
                default=list,
                help_text=_('Exceptions to performance optimization rules')
            ),
        ),
        
        # Performance optimization audit trail
        migrations.AddField(
            model_name='medication',
            name='performance_optimization_audit_trail',
            field=models.JSONField(
                default=list,
                help_text=_('Audit trail for performance optimization activities')
            ),
        ),
        
        # Performance monitoring enabled
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether performance monitoring is enabled')
            ),
        ),
        
        # Performance monitoring metrics
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance monitoring metrics')
            ),
        ),
        
        # Performance monitoring alerts
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_alerts',
            field=models.JSONField(
                default=list,
                help_text=_('Performance monitoring alerts')
            ),
        ),
        
        # Performance monitoring thresholds
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance monitoring thresholds')
            ),
        ),
        
        # Performance monitoring frequency
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_frequency_minutes',
            field=models.PositiveIntegerField(
                default=15,
                help_text=_('Frequency of performance monitoring (minutes)')
            ),
        ),
        
        # Last performance monitoring check
        migrations.AddField(
            model_name='medication',
            name='last_performance_monitoring_check',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time performance monitoring was checked')
            ),
        ),
        
        # Performance monitoring history
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_history',
            field=models.JSONField(
                default=list,
                help_text=_('History of performance monitoring activities')
            ),
        ),
        
        # Performance monitoring logs
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_logs',
            field=models.JSONField(
                default=list,
                help_text=_('Detailed logs of performance monitoring activities')
            ),
        ),
        
        # Performance monitoring configuration
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_config',
            field=models.JSONField(
                default=dict,
                help_text=_('Configuration for performance monitoring')
            ),
        ),
        
        # Performance monitoring rules
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Rules for performance monitoring')
            ),
        ),
        
        # Performance monitoring exceptions
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_exceptions',
            field=models.JSONField(
                default=list,
                help_text=_('Exceptions to performance monitoring rules')
            ),
        ),
        
        # Performance monitoring audit trail
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_audit_trail',
            field=models.JSONField(
                default=list,
                help_text=_('Audit trail for performance monitoring activities')
            ),
        ),
        
        # Performance monitoring metadata
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_metadata',
            field=models.JSONField(
                default=dict,
                help_text=_('Additional metadata for performance monitoring')
            ),
        ),
        
        # Performance monitoring cost tracking
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_cost_tracking_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether cost tracking is enabled for performance monitoring')
            ),
        ),
        
        # Performance monitoring cost per check
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_cost_per_check',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=6,
                null=True,
                blank=True,
                help_text=_('Cost per performance monitoring check')
            ),
        ),
        
        # Performance monitoring total cost
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_total_cost',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                help_text=_('Total cost of performance monitoring')
            ),
        ),
        
        # Performance monitoring cost currency
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_cost_currency',
            field=models.CharField(
                max_length=3,
                default='USD',
                help_text=_('Currency for performance monitoring costs')
            ),
        ),
        
        # Performance monitoring cost breakdown
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_cost_breakdown',
            field=models.JSONField(
                default=dict,
                help_text=_('Breakdown of performance monitoring costs')
            ),
        ),
        
        # Performance monitoring quality assurance
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_qa_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether quality assurance is enabled for performance monitoring')
            ),
        ),
        
        # Performance monitoring QA metrics
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_qa_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Quality assurance metrics for performance monitoring')
            ),
        ),
        
        # Performance monitoring QA thresholds
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_qa_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Quality assurance thresholds for performance monitoring')
            ),
        ),
        
        # Performance monitoring QA alerts
        migrations.AddField(
            model_name='medication',
            name='performance_monitoring_qa_alerts',
            field=models.JSONField(
                default=list,
                help_text=_('Quality assurance alerts for performance monitoring')
            ),
        ),
        
        # Add comprehensive indexes for performance optimization
        
        # Basic field indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['name'], name='medication_name_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['generic_name'], name='medication_generic_name_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['brand_name'], name='medication_brand_name_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['medication_type'], name='medication_type_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['prescription_type'], name='medication_prescription_type_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['manufacturer'], name='medication_manufacturer_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['expiration_date'], name='medication_expiration_date_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['created_at'], name='medication_created_at_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['updated_at'], name='medication_updated_at_perf_idx'),
        ),
        
        # Composite indexes for common queries
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['medication_type', 'prescription_type'], name='medication_type_prescription_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['pill_count', 'low_stock_threshold'], name='medication_stock_threshold_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['expiration_date', 'pill_count'], name='medication_expiry_stock_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['manufacturer', 'medication_type'], name='medication_manufacturer_type_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['name', 'generic_name'], name='medication_name_generic_perf_idx'),
        ),
        
        # Performance optimization indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['performance_optimization_enabled'], name='medication_perf_opt_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['performance_optimization_level'], name='medication_perf_opt_level_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['performance_optimization_last_applied'], name='medication_perf_opt_last_applied_idx'),
        ),
        
        # Performance monitoring indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['performance_monitoring_enabled'], name='medication_perf_monitoring_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['last_performance_monitoring_check'], name='medication_perf_monitoring_last_check_idx'),
        ),
        
        # Additional composite indexes for complex queries
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['medication_type', 'pill_count', 'expiration_date'], name='medication_type_stock_expiry_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['manufacturer', 'medication_type', 'prescription_type'], name='medication_manufacturer_type_prescription_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['created_at', 'medication_type'], name='medication_created_type_perf_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['updated_at', 'medication_type'], name='medication_updated_type_perf_idx'),
        ),
        
        # Partial indexes for specific conditions
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['name'], name='medication_name_active_idx', condition=models.Q(pill_count__gt=0)),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['expiration_date'], name='medication_expiry_active_idx', condition=models.Q(expiration_date__isnull=False)),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['pill_count'], name='medication_stock_low_idx', condition=models.Q(pill_count__lte=models.F('low_stock_threshold'))),
        ),
        
        # Functional indexes for computed fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['name'], name='medication_name_lower_idx', condition=models.Q(name__isnull=False)),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['generic_name'], name='medication_generic_lower_idx', condition=models.Q(generic_name__isnull=False)),
        ),
        
        # Time-based indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['created_at'], name='medication_created_date_idx', condition=models.Q(created_at__isnull=False)),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['updated_at'], name='medication_updated_date_idx', condition=models.Q(updated_at__isnull=False)),
        ),
        
        # Status-based indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['medication_type', 'pill_count'], name='medication_type_stock_status_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['prescription_type', 'medication_type'], name='medication_prescription_type_status_idx'),
        ),
        
        # Search optimization indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['name', 'generic_name', 'brand_name'], name='medication_search_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['manufacturer', 'name'], name='medication_manufacturer_search_idx'),
        ),
        
        # Analytics optimization indexes
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['medication_type', 'created_at'], name='medication_type_analytics_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['manufacturer', 'created_at'], name='medication_manufacturer_analytics_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['prescription_type', 'created_at'], name='medication_prescription_analytics_idx'),
        ),
    ] 