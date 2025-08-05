# Generated manually for MedGuard SA - Add prescription workflow state tracking
from django.db import migrations, models
from django.utils.translation import gettext_lazy as _


class Migration(migrations.Migration):

    dependencies = [
        ('medications', '0004_add_stock_analytics'),
    ]

    operations = [
        # Add prescription workflow state tracking to Medication model
        
        # Workflow state management
        migrations.AddField(
            model_name='medication',
            name='workflow_state_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether workflow state tracking is enabled')
            ),
        ),
        
        # Current workflow state
        migrations.AddField(
            model_name='medication',
            name='current_workflow_state',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('draft', _('Draft')),
                    ('pending_review', _('Pending Review')),
                    ('under_review', _('Under Review')),
                    ('approved', _('Approved')),
                    ('rejected', _('Rejected')),
                    ('pending_approval', _('Pending Approval')),
                    ('pending_verification', _('Pending Verification')),
                    ('verified', _('Verified')),
                    ('active', _('Active')),
                    ('inactive', _('Inactive')),
                    ('suspended', _('Suspended')),
                    ('archived', _('Archived')),
                    ('pending_activation', _('Pending Activation')),
                    ('pending_deactivation', _('Pending Deactivation')),
                    ('error', _('Error')),
                    ('processing', _('Processing')),
                    ('completed', _('Completed')),
                    ('cancelled', _('Cancelled')),
                ],
                default='draft',
                help_text=_('Current state in the prescription workflow')
            ),
        ),
        
        # Workflow state history
        migrations.AddField(
            model_name='medication',
            name='workflow_state_history',
            field=models.JSONField(
                default=list,
                help_text=_('History of workflow state changes')
            ),
        ),
        
        # Workflow state transition rules
        migrations.AddField(
            model_name='medication',
            name='workflow_transition_rules',
            field=models.JSONField(
                default=dict,
                help_text=_('Rules for workflow state transitions')
            ),
        ),
        
        # Workflow state permissions
        migrations.AddField(
            model_name='medication',
            name='workflow_state_permissions',
            field=models.JSONField(
                default=dict,
                help_text=_('Permissions required for each workflow state')
            ),
        ),
        
        # Workflow state timestamps
        migrations.AddField(
            model_name='medication',
            name='workflow_state_entered_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('When current workflow state was entered')
            ),
        ),
        
        # Workflow state duration
        migrations.AddField(
            model_name='medication',
            name='workflow_state_duration_hours',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Duration in current workflow state (hours)')
            ),
        ),
        
        # Workflow state timeout
        migrations.AddField(
            model_name='medication',
            name='workflow_state_timeout_hours',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('Timeout for current workflow state (hours)')
            ),
        ),
        
        # Workflow state timeout action
        migrations.AddField(
            model_name='medication',
            name='workflow_state_timeout_action',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('none', _('No Action')),
                    ('escalate', _('Escalate')),
                    ('auto_approve', _('Auto Approve')),
                    ('auto_reject', _('Auto Reject')),
                    ('notify', _('Notify')),
                    ('reassign', _('Reassign')),
                    ('rollback', _('Rollback')),
                ],
                default='none',
                help_text=_('Action to take when workflow state times out')
            ),
        ),
        
        # Workflow state assignee
        migrations.AddField(
            model_name='medication',
            name='workflow_state_assignee',
            field=models.CharField(
                max_length=200,
                blank=True,
                help_text=_('User assigned to current workflow state')
            ),
        ),
        
        # Workflow state assignee ID
        migrations.AddField(
            model_name='medication',
            name='workflow_state_assignee_id',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('ID of user assigned to current workflow state')
            ),
        ),
        
        # Workflow state comments
        migrations.AddField(
            model_name='medication',
            name='workflow_state_comments',
            field=models.TextField(
                blank=True,
                help_text=_('Comments for current workflow state')
            ),
        ),
        
        # Workflow state notes
        migrations.AddField(
            model_name='medication',
            name='workflow_state_notes',
            field=models.JSONField(
                default=list,
                help_text=_('Notes and comments for workflow state')
            ),
        ),
        
        # Workflow state attachments
        migrations.AddField(
            model_name='medication',
            name='workflow_state_attachments',
            field=models.JSONField(
                default=list,
                help_text=_('Attachments for current workflow state')
            ),
        ),
        
        # Workflow state validation
        migrations.AddField(
            model_name='medication',
            name='workflow_state_validation_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('not_validated', _('Not Validated')),
                    ('pending_validation', _('Pending Validation')),
                    ('validated', _('Validated')),
                    ('validation_failed', _('Validation Failed')),
                    ('validation_error', _('Validation Error')),
                ],
                default='not_validated',
                help_text=_('Validation status for current workflow state')
            ),
        ),
        
        # Workflow state validation errors
        migrations.AddField(
            model_name='medication',
            name='workflow_state_validation_errors',
            field=models.JSONField(
                default=list,
                help_text=_('Validation errors for current workflow state')
            ),
        ),
        
        # Workflow state approval chain
        migrations.AddField(
            model_name='medication',
            name='workflow_approval_chain',
            field=models.JSONField(
                default=list,
                help_text=_('Chain of approvals required for workflow')
            ),
        ),
        
        # Workflow state approval status
        migrations.AddField(
            model_name='medication',
            name='workflow_approval_status',
            field=models.JSONField(
                default=dict,
                help_text=_('Status of approvals in the workflow chain')
            ),
        ),
        
        # Workflow state escalation level
        migrations.AddField(
            model_name='medication',
            name='workflow_escalation_level',
            field=models.PositiveIntegerField(
                default=0,
                help_text=_('Current escalation level in workflow')
            ),
        ),
        
        # Workflow state escalation history
        migrations.AddField(
            model_name='medication',
            name='workflow_escalation_history',
            field=models.JSONField(
                default=list,
                help_text=_('History of workflow escalations')
            ),
        ),
        
        # Workflow state SLA tracking
        migrations.AddField(
            model_name='medication',
            name='workflow_sla_target_hours',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text=_('SLA target for current workflow state (hours)')
            ),
        ),
        
        # Workflow state SLA status
        migrations.AddField(
            model_name='medication',
            name='workflow_sla_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('on_track', _('On Track')),
                    ('at_risk', _('At Risk')),
                    ('breached', _('Breached')),
                    ('completed', _('Completed')),
                ],
                default='on_track',
                help_text=_('SLA status for current workflow state')
            ),
        ),
        
        # Workflow state SLA remaining time
        migrations.AddField(
            model_name='medication',
            name='workflow_sla_remaining_hours',
            field=models.FloatField(
                null=True,
                blank=True,
                help_text=_('Remaining time to meet SLA (hours)')
            ),
        ),
        
        # Workflow state notifications
        migrations.AddField(
            model_name='medication',
            name='workflow_notifications_enabled',
            field=models.BooleanField(
                default=True,
                help_text=_('Whether workflow notifications are enabled')
            ),
        ),
        
        # Workflow state notification recipients
        migrations.AddField(
            model_name='medication',
            name='workflow_notification_recipients',
            field=models.JSONField(
                default=list,
                help_text=_('Recipients for workflow state notifications')
            ),
        ),
        
        # Workflow state notification frequency
        migrations.AddField(
            model_name='medication',
            name='workflow_notification_frequency_hours',
            field=models.PositiveIntegerField(
                default=24,
                help_text=_('Frequency of workflow notifications (hours)')
            ),
        ),
        
        # Workflow state last notification
        migrations.AddField(
            model_name='medication',
            name='workflow_last_notification',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text=_('Last time workflow notification was sent')
            ),
        ),
        
        # Workflow state audit trail
        migrations.AddField(
            model_name='medication',
            name='workflow_audit_trail',
            field=models.JSONField(
                default=list,
                help_text=_('Audit trail for workflow state changes')
            ),
        ),
        
        # Workflow state metadata
        migrations.AddField(
            model_name='medication',
            name='workflow_metadata',
            field=models.JSONField(
                default=dict,
                help_text=_('Additional metadata for workflow state')
            ),
        ),
        
        # Add indexes for workflow state fields
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['current_workflow_state'], name='medication_workflow_state_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['workflow_state_assignee_id'], name='medication_workflow_assignee_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['workflow_state_entered_at'], name='medication_workflow_entered_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['workflow_escalation_level'], name='medication_workflow_escalation_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['workflow_sla_status'], name='medication_workflow_sla_idx'),
        ),
        migrations.AddIndex(
            model_name='medication',
            index=models.Index(fields=['workflow_state_validation_status'], name='medication_workflow_validation_idx'),
        ),
    ] 