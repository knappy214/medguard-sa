# Generated manually for MedGuard SA - Add medication interaction monitoring
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0005_add_workflow_state'),
    ]

    operations = [
        # Add medication interaction monitoring to Medication model
        
        # Interaction monitoring enabled
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether medication interaction monitoring is enabled')
            ),
        ),
        
        # Known interactions
        migrations.AddField(
            model_name='medication',
            name='known_interactions',
            field=models.JSONField(
                default=list,
                help_text=_('List of known drug interactions for this medication')
            ),
        ),
        
        # Interaction severity levels
        migrations.AddField(
            model_name='medication',
            name='interaction_severity_levels',
            field=models.JSONField(
                default=dict,
                help_text=_('Severity levels for different types of interactions')
            ),
        ),
        
        # Interaction categories
        migrations.AddField(
            model_name='medication',
            name='interaction_categories',
            field=models.JSONField(
                default=list,
                help_text=_('Categories of interactions for this medication')
            ),
        ),
        
        # Interaction monitoring frequency
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of interaction monitoring checks (hours)')
            ),
        ),
        
        # Last interaction check
        migrations.AddField(
            model_name='medication',
            name='last_interaction_check',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time interaction monitoring was performed')
            ),
        ),
        
        # Interaction check results
        migrations.AddField(
            model_name='medication',
            name='interaction_check_results',
            field=models.JSONField(
                default=dict,
                help_text=_('Results of the last interaction monitoring check')
            ),
        ),
        
        # Active interactions
        migrations.AddField(
            model_name='medication',
            name='active_interactions',
            field=models.JSONField(
                default=list,
                help_text=_('Currently active interactions for this medication')
            ),
        ),
        
        # Interaction alerts
        migrations.AddField(
            model_name='medication',
            name='interaction_alerts',
            field=models.JSONField(
                default=list,
                help_text=_('Alerts generated for medication interactions')
            ),
        ),
        
        # Interaction risk score
        migrations.AddField(
            model_name='medication',
            name='interaction_risk_score',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Overall interaction risk score (0-1)')
            ),
        ),
        
        # Interaction risk level
        migrations.AddField(
            model_name='medication',
            name='interaction_risk_level',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('low', _('Low Risk')),
                    ('moderate', _('Moderate Risk')),
                    ('high', _('High Risk')),
                    ('severe', _('Severe Risk')),
                    ('contraindicated', _('Contraindicated')),
                ],
                default='low',
                help_text=_('Overall interaction risk level')
            ),
        ),
        
        # Interaction monitoring algorithm
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_algorithm',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('basic', _('Basic Rule-Based')),
                    ('advanced', _('Advanced Algorithmic')),
                    ('ai_ml', _('AI/ML Based')),
                    ('hybrid', _('Hybrid Approach')),
                    ('custom', _('Custom Algorithm')),
                ],
                default='advanced',
                help_text=_('Algorithm used for interaction monitoring')
            ),
        ),
        
        # Interaction monitoring parameters
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_params',
            field=models.JSONField(
                default=dict,
                help_text=_('Parameters for interaction monitoring algorithm')
            ),
        ),
        
        # Interaction monitoring accuracy
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_accuracy',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Accuracy of interaction monitoring (0-1)')
            ),
        ),
        
        # Interaction monitoring false positives
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_false_positives',
            field=models.PositiveIntegerField(
                default=0,
                help_text=_('Number of false positive interactions detected')
            ),
        ),
        
        # Interaction monitoring false negatives
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_false_negatives',
            field=models.PositiveIntegerField(
                default=0,
                help_text=_('Number of false negative interactions missed')
            ),
        ),
        
        # Interaction monitoring precision
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_precision',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Precision of interaction monitoring (0-1)')
            ),
        ),
        
        # Interaction monitoring recall
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_recall',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Recall of interaction monitoring (0-1)')
            ),
        ),
        
        # Interaction monitoring F1 score
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_f1_score',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('F1 score of interaction monitoring (0-1)')
            ),
        ),
        
        # Interaction monitoring performance metrics
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_performance',
            field=models.JSONField(
                default=dict,
                help_text=_('Performance metrics for interaction monitoring')
            ),
        ),
        
        # Interaction monitoring alerts enabled
        migrations.AddField(
            model_name='medication',
            name='interaction_alerts_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether interaction alerts are enabled')
            ),
        ),
        
        # Interaction alert thresholds
        migrations.AddField(
            model_name='medication',
            name='interaction_alert_thresholds',
            field=models.JSONField(
                default=dict,
                help_text=_('Thresholds for different types of interaction alerts')
            ),
        ),
        
        # Interaction alert recipients
        migrations.AddField(
            model_name='medication',
            name='interaction_alert_recipients',
            field=models.JSONField(
                default=list,
                help_text=_('Recipients for interaction alerts')
            ),
        ),
        
        # Interaction alert frequency
        migrations.AddField(
            model_name='medication',
            name='interaction_alert_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of interaction alerts (hours)')
            ),
        ),
        
        # Last interaction alert
        migrations.AddField(
            model_name='medication',
            name='last_interaction_alert',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time an interaction alert was sent')
            ),
        ),
        
        # Interaction monitoring history
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_history',
            field=models.JSONField(
                default=list,
                help_text=_('History of interaction monitoring activities')
            ),
        ),
        
        # Interaction monitoring logs
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_logs',
            field=models.JSONField(
                default=list,
                help_text=_('Detailed logs of interaction monitoring activities')
            ),
        ),
        
        # Interaction monitoring configuration
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_config',
            field=models.JSONField(
                default=dict,
                help_text=_('Configuration for interaction monitoring')
            ),
        ),
        
        # Interaction monitoring rules
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_rules',
            field=models.JSONField(
                default=list,
                help_text=_('Rules for interaction monitoring')
            ),
        ),
        
        # Interaction monitoring exceptions
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_exceptions',
            field=models.JSONField(
                default=list,
                help_text=_('Exceptions to interaction monitoring rules')
            ),
        ),
        
        # Interaction monitoring whitelist
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_whitelist',
            field=models.JSONField(
                default=list,
                help_text=_('Whitelist of medications that don\'t interact')
            ),
        ),
        
        # Interaction monitoring blacklist
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_blacklist',
            field=models.JSONField(
                default=list,
                help_text=_('Blacklist of medications that always interact')
            ),
        ),
        
        # Interaction monitoring data sources
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_data_sources',
            field=models.JSONField(
                default=list,
                help_text=_('Data sources used for interaction monitoring')
            ),
        ),
        
        # Interaction monitoring last data update
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_last_data_update',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time interaction data was updated')
            ),
        ),
        
        # Interaction monitoring data version
        migrations.AddField(
            model_name='medication',
            name='interaction_monitoring_data_version',
            field=models.CharField(
                max_length=50,
                blank=True,
                help_text=_('Version of interaction monitoring data')
            ),
        ),
        
        # Add indexes for interaction tracking fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['interaction_monitoring_enabled'], name='medication_interaction_monitoring_enabled_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['interaction_risk_level'], name='medication_interaction_risk_level_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['interaction_risk_score'], name='medication_interaction_risk_score_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['last_interaction_check'], name='medication_last_interaction_check_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['interaction_monitoring_algorithm'], name='medication_interaction_algorithm_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['interaction_alerts_enabled'], name='medication_interaction_alerts_enabled_idx'),
        ),
    ] 