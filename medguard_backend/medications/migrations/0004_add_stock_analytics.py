# Generated manually for MedGuard SA - Add advanced stock management fields
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0003_add_ocr_fields'),
    ]

    operations = [
        # Add advanced stock management fields to Medication model
        
        # Stock prediction fields
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether stock prediction is enabled for this medication')
            ),
        ),
        
        # Stock prediction algorithm
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_algorithm',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('simple_moving_average', _('Simple Moving Average')),
                    ('exponential_smoothing', _('Exponential Smoothing')),
                    ('linear_regression', _('Linear Regression')),
                    ('arima', _('ARIMA')),
                    ('prophet', _('Prophet')),
                    ('lstm', _('LSTM Neural Network')),
                    ('ensemble', _('Ensemble Method')),
                ],
                default='exponential_smoothing',
                help_text=_('Algorithm used for stock prediction')
            ),
        ),
        
        # Stock prediction accuracy
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_accuracy',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Accuracy of stock prediction model (0-1)')
            ),
        ),
        
        # Stock prediction last update
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_last_update',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time stock prediction was updated')
            ),
        ),
        
        # Stock prediction horizon days
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_horizon_days',
            field=models.PositiveIntegerField(
                default=30,
                help_text=_('Number of days to predict stock levels')
            ),
        ),
        
        # Stock prediction confidence interval
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_confidence_interval',
            field=models.FloatField(
                default=0.95,
                help_text=_('Confidence interval for stock predictions (0-1)')
            ),
        ),
        
        # Stock prediction data points
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_data_points',
            field=models.JSONField(
                default=list,
                help_text=_('Historical data points used for prediction')
            ),
        ),
        
        # Stock prediction model parameters
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_model_params',
            field=models.JSONField(
                default=dict,
                help_text=_('Parameters for the stock prediction model')
            ),
        ),
        
        # Stock prediction results
        migrations.AddField(
            model_name='medication',
            name='stock_prediction_results',
            field=models.JSONField(
                default=dict,
                help_text=_('Latest stock prediction results')
            ),
        ),
        
        # Stock optimization fields
        migrations.AddField(
            model_name='medication',
            name='stock_optimization_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether stock optimization is enabled')
            ),
        ),
        
        # Optimal stock level
        migrations.AddField(
            model_name='medication',
            name='optimal_stock_level',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Optimal stock level calculated by optimization algorithm')
            ),
        ),
        
        # Safety stock level
        migrations.AddField(
            model_name='medication',
            name='safety_stock_level',
            field=models.PositiveIntegerField(
                default=5,
                help_text=_('Safety stock level to prevent stockouts')
            ),
        ),
        
        # Maximum stock level
        migrations.AddField(
            model_name='medication',
            name='max_stock_level',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Maximum stock level to prevent overstocking')
            ),
        ),
        
        # Reorder point
        migrations.AddField(
            model_name='medication',
            name='reorder_point',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Stock level at which to reorder')
            ),
        ),
        
        # Economic order quantity
        migrations.AddField(
            model_name='medication',
            name='economic_order_quantity',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Optimal order quantity to minimize costs')
            ),
        ),
        
        # Stock holding cost
        migrations.AddField(
            model_name='medication',
            name='stock_holding_cost_per_unit',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text=_('Cost of holding one unit in stock per year')
            ),
        ),
        
        # Stock ordering cost
        migrations.AddField(
            model_name='medication',
            name='stock_ordering_cost',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text=_('Fixed cost per order')
            ),
        ),
        
        # Stockout cost
        migrations.AddField(
            model_name='medication',
            name='stockout_cost_per_unit',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text=_('Cost of stockout per unit')
            ),
        ),
        
        # Stock analytics fields
        migrations.AddField(
            model_name='medication',
            name='stock_turnover_rate',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Stock turnover rate (times per year)')
            ),
        ),
        
        # Stock turnover period
        migrations.AddField(
            model_name='medication',
            name='stock_turnover_period_days',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Average days to turn over stock')
            ),
        ),
        
        # Stock velocity
        migrations.AddField(
            model_name='medication',
            name='stock_velocity',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Stock velocity (units per day)')
            ),
        ),
        
        # Stock variability
        migrations.AddField(
            model_name='medication',
            name='stock_variability',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Variability in stock levels (coefficient of variation)')
            ),
        ),
        
        # Stock seasonality
        migrations.AddField(
            model_name='medication',
            name='stock_seasonality_factor',
            field=models.FloatField(
                default=1.0,
                help_text=_('Seasonal adjustment factor for stock levels')
            ),
        ),
        
        # Stock trend
        migrations.AddField(
            model_name='medication',
            name='stock_trend',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('increasing', _('Increasing')),
                    ('decreasing', _('Decreasing')),
                    ('stable', _('Stable')),
                    ('volatile', _('Volatile')),
                ],
                default='stable',
                help_text=_('Trend in stock levels')
            ),
        ),
        
        # Stock forecast accuracy
        migrations.AddField(
            model_name='medication',
            name='stock_forecast_accuracy',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Accuracy of stock forecasts (0-1)')
            ),
        ),
        
        # Stock forecast error
        migrations.AddField(
            model_name='medication',
            name='stock_forecast_error',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Mean absolute error of stock forecasts')
            ),
        ),
        
        # Stock forecast bias
        migrations.AddField(
            model_name='medication',
            name='stock_forecast_bias',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Bias in stock forecasts (positive = over-forecast)')
            ),
        ),
        
        # Stock performance metrics
        migrations.AddField(
            model_name='medication',
            name='stock_performance_metrics',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance metrics for stock management')
            ),
        ),
        
        # Stock alerts configuration
        migrations.AddField(
            model_name='medication',
            name='stock_alerts_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether stock alerts are enabled')
            ),
        ),
        
        # Stock alert thresholds
        migrations.AddField(
            model_name='medication',
            name='stock_alert_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Thresholds for different types of stock alerts')
            ),
        ),
        
        # Stock alert recipients
        migrations.AddField(
            model_name='medication',
            name='stock_alert_recipients',
            field=models.JSONField(
                default=list,
                help_text=_('List of users to notify for stock alerts')
            ),
        ),
        
        # Stock alert frequency
        migrations.AddField(
            model_name='medication',
            name='stock_alert_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of stock alerts in hours')
            ),
        ),
        
        # Stock alert last sent
        migrations.AddField(
            model_name='medication',
            name='stock_alert_last_sent',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time a stock alert was sent')
            ),
        ),
        
        # Add indexes for stock analytics fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['stock_prediction_enabled'], name='medication_stock_prediction_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['stock_optimization_enabled'], name='medication_stock_optimization_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['stock_turnover_rate'], name='medication_stock_turnover_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['stock_trend'], name='medication_stock_trend_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['reorder_point'], name='medication_reorder_point_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['optimal_stock_level'], name='medication_optimal_stock_idx'),
        ),
    ] 