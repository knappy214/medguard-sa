# Generated manually for MedGuard SA stock analytics and reporting tables
from django.db import migrations, models
import django.db.models.deletion
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0013_medication_interaction_tracking'),
    ]

    operations = [
        # Create StockReport model
        migrations.CreateModel(
            name='StockReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_type', models.CharField(
                    choices=[
                        ('daily', _('Daily Report')),
                        ('weekly', _('Weekly Report')),
                        ('monthly', _('Monthly Report')),
                        ('quarterly', _('Quarterly Report')),
                        ('annual', _('Annual Report')),
                        ('custom', _('Custom Period Report'))
                    ],
                    max_length=20,
                    help_text=_('Type of stock report')
                )),
                ('report_period_start', models.DateField(help_text=_('Start date of the report period'))),
                ('report_period_end', models.DateField(help_text=_('End date of the report period'))),
                ('report_date', models.DateTimeField(auto_now_add=True, help_text=_('When this report was generated'))),
                ('report_status', models.CharField(
                    choices=[
                        ('generating', _('Generating')),
                        ('completed', _('Completed')),
                        ('failed', _('Failed')),
                        ('cancelled', _('Cancelled'))
                    ],
                    default='generating',
                    max_length=20,
                    help_text=_('Status of the report generation')
                )),
                ('total_medications', models.PositiveIntegerField(default=0, help_text=_('Total number of medications in stock'))),
                ('low_stock_medications', models.PositiveIntegerField(default=0, help_text=_('Number of medications with low stock'))),
                ('out_of_stock_medications', models.PositiveIntegerField(default=0, help_text=_('Number of medications out of stock'))),
                ('expiring_medications', models.PositiveIntegerField(default=0, help_text=_('Number of medications expiring soon'))),
                ('expired_medications', models.PositiveIntegerField(default=0, help_text=_('Number of expired medications'))),
                ('total_stock_value', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=15,
                    null=True,
                    help_text=_('Total value of stock')
                )),
                ('report_data', models.JSONField(default=dict, help_text=_('Detailed report data in JSON format'))),
                ('report_summary', models.TextField(blank=True, help_text=_('Summary of the report'))),
                ('generated_by', models.CharField(blank=True, max_length=200, help_text=_('Who generated this report'))),
                ('report_notes', models.TextField(blank=True, help_text=_('Additional notes about the report'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this report was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this report was last updated'))),
            ],
            options={
                'verbose_name': _('Stock Report'),
                'verbose_name_plural': _('Stock Reports'),
                'db_table': 'stock_reports',
                'ordering': ['-report_date'],
            },
        ),
        
        # Create StockTrend model
        migrations.CreateModel(
            name='StockTrend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trend_date', models.DateField(help_text=_('Date for this trend data point'))),
                ('trend_type', models.CharField(
                    choices=[
                        ('daily', _('Daily Trend')),
                        ('weekly', _('Weekly Trend')),
                        ('monthly', _('Monthly Trend')),
                        ('quarterly', _('Quarterly Trend'))
                    ],
                    max_length=20,
                    help_text=_('Type of trend analysis')
                )),
                ('opening_stock', models.PositiveIntegerField(default=0, help_text=_('Opening stock level'))),
                ('closing_stock', models.PositiveIntegerField(default=0, help_text=_('Closing stock level'))),
                ('stock_in', models.PositiveIntegerField(default=0, help_text=_('Stock received'))),
                ('stock_out', models.PositiveIntegerField(default=0, help_text=_('Stock dispensed/used'))),
                ('stock_adjustments', models.IntegerField(default=0, help_text=_('Stock adjustments (positive or negative)'))),
                ('stock_loss', models.PositiveIntegerField(default=0, help_text=_('Stock lost due to expiry/damage'))),
                ('usage_rate', models.FloatField(default=0.0, help_text=_('Daily usage rate'))),
                ('turnover_rate', models.FloatField(default=0.0, help_text=_('Stock turnover rate'))),
                ('days_of_stock_remaining', models.PositiveIntegerField(blank=True, null=True, help_text=_('Days of stock remaining'))),
                ('stock_value', models.DecimalField(
                    blank=True,
                    decimal_places=2,
                    max_digits=12,
                    null=True,
                    help_text=_('Stock value for this period')
                )),
                ('trend_metadata', models.JSONField(default=dict, help_text=_('Additional trend metadata'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this trend was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this trend was last updated'))),
            ],
            options={
                'verbose_name': _('Stock Trend'),
                'verbose_name_plural': _('Stock Trends'),
                'db_table': 'stock_trends',
                'ordering': ['-trend_date'],
            },
        ),
        
        # Create StockForecast model
        migrations.CreateModel(
            name='StockForecast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('forecast_date', models.DateField(help_text=_('Date for this forecast'))),
                ('forecast_period_days', models.PositiveIntegerField(help_text=_('Number of days to forecast'))),
                ('forecast_type', models.CharField(
                    choices=[
                        ('demand', _('Demand Forecast')),
                        ('supply', _('Supply Forecast')),
                        ('stockout', _('Stockout Forecast')),
                        ('reorder', _('Reorder Forecast'))
                    ],
                    max_length=20,
                    help_text=_('Type of forecast')
                )),
                ('predicted_demand', models.PositiveIntegerField(default=0, help_text=_('Predicted demand for the period'))),
                ('predicted_stock_level', models.PositiveIntegerField(default=0, help_text=_('Predicted stock level at end of period'))),
                ('predicted_stockout_date', models.DateField(blank=True, null=True, help_text=_('Predicted date of stockout'))),
                ('recommended_order_quantity', models.PositiveIntegerField(default=0, help_text=_('Recommended order quantity'))),
                ('recommended_order_date', models.DateField(blank=True, null=True, help_text=_('Recommended order date'))),
                ('confidence_level', models.FloatField(default=0.0, help_text=_('Confidence level of the forecast (0-1)'))),
                ('forecast_accuracy', models.FloatField(blank=True, null=True, help_text=_('Accuracy of previous forecasts'))),
                ('seasonal_factors', models.JSONField(default=dict, help_text=_('Seasonal adjustment factors'))),
                ('forecast_algorithm', models.CharField(blank=True, max_length=100, help_text=_('Algorithm used for forecasting'))),
                ('forecast_parameters', models.JSONField(default=dict, help_text=_('Parameters used for forecasting'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this forecast was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this forecast was last updated'))),
            ],
            options={
                'verbose_name': _('Stock Forecast'),
                'verbose_name_plural': _('Stock Forecasts'),
                'db_table': 'stock_forecasts',
                'ordering': ['-forecast_date'],
            },
        ),
        
        # Create StockAlertRule model
        migrations.CreateModel(
            name='StockAlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rule_name', models.CharField(max_length=200, help_text=_('Name of the alert rule'))),
                ('rule_type', models.CharField(
                    choices=[
                        ('low_stock', _('Low Stock Alert')),
                        ('out_of_stock', _('Out of Stock Alert')),
                        ('expiring_soon', _('Expiring Soon Alert')),
                        ('expired', _('Expired Alert')),
                        ('high_usage', _('High Usage Alert')),
                        ('unusual_activity', _('Unusual Activity Alert')),
                        ('custom', _('Custom Alert'))
                    ],
                    max_length=20,
                    help_text=_('Type of alert rule')
                )),
                ('rule_conditions', models.JSONField(default=dict, help_text=_('Conditions for triggering the alert'))),
                ('threshold_value', models.FloatField(help_text=_('Threshold value for the alert'))),
                ('threshold_unit', models.CharField(max_length=20, help_text=_('Unit for the threshold value'))),
                ('alert_priority', models.CharField(
                    choices=[
                        ('low', _('Low')),
                        ('medium', _('Medium')),
                        ('high', _('High')),
                        ('critical', _('Critical'))
                    ],
                    default='medium',
                    max_length=20,
                    help_text=_('Priority level of alerts from this rule')
                )),
                ('notification_channels', models.JSONField(default=list, help_text=_('Channels for sending notifications'))),
                ('is_active', models.BooleanField(default=True, help_text=_('Whether this rule is active'))),
                ('rule_description', models.TextField(blank=True, help_text=_('Description of the rule'))),
                ('created_by', models.CharField(blank=True, max_length=200, help_text=_('Who created this rule'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this rule was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this rule was last updated'))),
            ],
            options={
                'verbose_name': _('Stock Alert Rule'),
                'verbose_name_plural': _('Stock Alert Rules'),
                'db_table': 'stock_alert_rules',
                'ordering': ['rule_name'],
            },
        ),
        
        # Create StockPerformance model
        migrations.CreateModel(
            name='StockPerformance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('performance_date', models.DateField(help_text=_('Date for this performance data'))),
                ('performance_metric', models.CharField(
                    choices=[
                        ('stock_turnover', _('Stock Turnover Rate')),
                        ('fill_rate', _('Fill Rate')),
                        ('stockout_rate', _('Stockout Rate')),
                        ('expiry_rate', _('Expiry Rate')),
                        ('accuracy_rate', _('Inventory Accuracy Rate')),
                        ('carrying_cost', _('Carrying Cost')),
                        ('order_frequency', _('Order Frequency')),
                        ('lead_time', _('Lead Time')),
                        ('service_level', _('Service Level'))
                    ],
                    max_length=20,
                    help_text=_('Type of performance metric')
                )),
                ('metric_value', models.FloatField(help_text=_('Value of the performance metric'))),
                ('metric_unit', models.CharField(blank=True, max_length=20, help_text=_('Unit for the metric value'))),
                ('target_value', models.FloatField(blank=True, null=True, help_text=_('Target value for this metric'))),
                ('performance_status', models.CharField(
                    choices=[
                        ('excellent', _('Excellent')),
                        ('good', _('Good')),
                        ('acceptable', _('Acceptable')),
                        ('poor', _('Poor')),
                        ('critical', _('Critical'))
                    ],
                    max_length=20,
                    help_text=_('Performance status based on target')
                )),
                ('performance_trend', models.CharField(
                    choices=[
                        ('improving', _('Improving')),
                        ('stable', _('Stable')),
                        ('declining', _('Declining')),
                        ('fluctuating', _('Fluctuating'))
                    ],
                    max_length=20,
                    help_text=_('Trend of the performance metric')
                )),
                ('performance_notes', models.TextField(blank=True, help_text=_('Notes about the performance'))),
                ('created_at', models.DateTimeField(auto_now_add=True, help_text=_('When this performance data was created'))),
                ('updated_at', models.DateTimeField(auto_now=True, help_text=_('When this performance data was last updated'))),
            ],
            options={
                'verbose_name': _('Stock Performance'),
                'verbose_name_plural': _('Stock Performance'),
                'db_table': 'stock_performance',
                'ordering': ['-performance_date'],
            },
        ),
        
        # Add foreign key relationships
        migrations.AddField(
            model_name='stocktrend',
            name='medication',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='stock_trends',
                to='medications.medication',
                help_text=_('Medication for this trend data')
            ),
        ),
        migrations.AddField(
            model_name='stockforecast',
            name='medication',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='stock_forecasts',
                to='medications.medication',
                help_text=_('Medication for this forecast')
            ),
        ),
        migrations.AddField(
            model_name='stockalertrule',
            name='medication',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='alert_rules',
                to='medications.medication',
                help_text=_('Medication for this alert rule (null for all medications)')
            ),
        ),
        migrations.AddField(
            model_name='stockperformance',
            name='medication',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='stock_performance',
                to='medications.medication',
                help_text=_('Medication for this performance data (null for overall performance)')
            ),
        ),
        
        # Create indexes for performance
        migrations.AddIndex(
            model_name='stockreport',
            index=models.Index(fields=['report_type', 'report_period_start'], name='stock_report_type_period_idx'),
        ),
        migrations.AddIndex(
            model_name='stockreport',
            index=models.Index(fields=['report_status'], name='stock_report_status_idx'),
        ),
        migrations.AddIndex(
            model_name='stockreport',
            index=models.Index(fields=['report_date'], name='stock_report_date_idx'),
        ),
        migrations.AddIndex(
            model_name='stocktrend',
            index=models.Index(fields=['medication', 'trend_date'], name='stock_trend_medication_date_idx'),
        ),
        migrations.AddIndex(
            model_name='stocktrend',
            index=models.Index(fields=['trend_type'], name='stock_trend_type_idx'),
        ),
        migrations.AddIndex(
            model_name='stockforecast',
            index=models.Index(fields=['medication', 'forecast_date'], name='stock_forecast_medication_date_idx'),
        ),
        migrations.AddIndex(
            model_name='stockforecast',
            index=models.Index(fields=['forecast_type'], name='stock_forecast_type_idx'),
        ),
        migrations.AddIndex(
            model_name='stockalertrule',
            index=models.Index(fields=['rule_type'], name='stock_alert_rule_type_idx'),
        ),
        migrations.AddIndex(
            model_name='stockalertrule',
            index=models.Index(fields=['is_active'], name='stock_alert_rule_active_idx'),
        ),
        migrations.AddIndex(
            model_name='stockperformance',
            index=models.Index(fields=['medication', 'performance_date'], name='stock_performance_medication_date_idx'),
        ),
        migrations.AddIndex(
            model_name='stockperformance',
            index=models.Index(fields=['performance_metric'], name='stock_performance_metric_idx'),
        ),
        migrations.AddIndex(
            model_name='stockperformance',
            index=models.Index(fields=['performance_status'], name='stock_performance_status_idx'),
        ),
    ] 