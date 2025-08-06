"""
Healthcare workflows for MedGuard SA using Wagtail 7.0.2.

This module contains specialized workflow implementations for healthcare
processes with enhanced email notifications and HIPAA compliance.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.workflows.models import Workflow, WorkflowTask
from wagtail.workflows.forms import WorkflowForm

from medguard_notifications.models import NotificationTemplate
from medguard_notifications.services import NotificationService

logger = logging.getLogger(__name__)
User = get_user_model()


class PrescriptionApprovalWorkflow(Workflow):
    """
    Multi-stage healthcare provider approval workflow for prescriptions.
    
    This workflow ensures prescriptions go through proper clinical review
    and approval processes with multiple healthcare provider stages.
    """
    
    # Workflow stages
    STAGES = {
        'initial_review': {
            'name': _('Initial Review'),
            'description': _('Initial clinical review by primary healthcare provider'),
            'required_role': 'DOCTOR',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'prescription_initial_review',
        },
        'specialist_review': {
            'name': _('Specialist Review'),
            'description': _('Specialist consultation for complex cases'),
            'required_role': 'SPECIALIST',
            'estimated_duration': timedelta(hours=24),
            'email_template': 'prescription_specialist_review',
            'optional': True,
        },
        'pharmacy_review': {
            'name': _('Pharmacy Review'),
            'description': _('Pharmacy verification and drug interaction check'),
            'required_role': 'PHARMACIST',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'prescription_pharmacy_review',
        },
        'final_approval': {
            'name': _('Final Approval'),
            'description': _('Final approval by senior healthcare provider'),
            'required_role': 'SENIOR_DOCTOR',
            'estimated_duration': timedelta(hours=8),
            'email_template': 'prescription_final_approval',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Workflow fields
    prescription = models.ForeignKey(
        'medications.EnhancedPrescription',
        on_delete=models.CASCADE,
        related_name='approval_workflows',
        help_text=_('Associated prescription')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='initial_review',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_approval_workflows',
        help_text=_('Currently assigned reviewer')
    )
    
    review_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Review notes for each stage')
    )
    
    approval_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete approval history')
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
        ],
        default='routine',
        help_text=_('Priority level for processing')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Prescription Approval Workflow')
        verbose_name_plural = _('Prescription Approval Workflows')
        db_table = 'healthcare_prescription_approval_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_reviewer', 'status']),
            models.Index(fields=['priority_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Approval Workflow for {self.prescription.prescription_number}"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on priority and stages."""
        base_duration = timedelta(hours=8)  # Base duration for routine cases
        
        if self.priority_level == 'urgent':
            base_duration = timedelta(hours=4)
        elif self.priority_level == 'emergency':
            base_duration = timedelta(hours=1)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name='prescription_workflow_assigned',
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'prescription': self.prescription,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify patient
            self._send_email_notification(
                template_name='prescription_workflow_started',
                recipient=self.prescription.patient,
                context={
                    'workflow': self,
                    'prescription': self.prescription,
                }
            )
            
            logger.info(f"Initial notifications sent for workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'prescription': self.prescription,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, reviewer: User, notes: str = None):
        """Advance workflow to the next stage."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.APPROVED
            self.actual_completion = timezone.now()
            self._complete_workflow(reviewer, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_reviewer = self._get_next_reviewer(next_stage)
            
            # Add to approval history
            self.approval_history.append({
                'stage': self.current_stage,
                'reviewer': reviewer.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'approved'
            })
        
        self.save()
    
    def _get_next_reviewer(self, stage: str) -> Optional[User]:
        """Get the next reviewer for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_reviewers = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_approval_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_reviewers.exists():
            return available_reviewers.first()
        
        # If no available reviewers, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, reviewer: User, notes: str = None):
        """Complete the workflow and update prescription status."""
        # Update prescription status
        self.prescription.status = 'approved'
        self.prescription.approved_by = reviewer
        self.prescription.approved_date = timezone.now()
        self.prescription.save()
        
        # Send completion notifications
        self._send_completion_notifications(reviewer, notes)
    
    def _send_completion_notifications(self, reviewer: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify patient
            self._send_email_notification(
                template_name='prescription_workflow_completed',
                recipient=self.prescription.patient,
                context={
                    'workflow': self,
                    'prescription': self.prescription,
                    'reviewer': reviewer,
                    'notes': notes,
                }
            )
            
            # Notify prescriber
            self._send_email_notification(
                template_name='prescription_workflow_completed_prescriber',
                recipient=self.prescription.prescriber,
                context={
                    'workflow': self,
                    'prescription': self.prescription,
                    'reviewer': reviewer,
                    'notes': notes,
                }
            )
            
            logger.info(f"Completion notifications sent for workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for workflow {self.id}: {e}")
    
    def reject_workflow(self, reviewer: User, reason: str):
        """Reject the workflow and update prescription status."""
        self.status = self.Status.REJECTED
        self.actual_completion = timezone.now()
        
        # Add to approval history
        self.approval_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'rejected'
        })
        
        # Update prescription status
        self.prescription.status = 'cancelled'
        self.prescription.save()
        
        # Send rejection notifications
        self._send_rejection_notifications(reviewer, reason)
        
        self.save()
    
    def _send_rejection_notifications(self, reviewer: User, reason: str):
        """Send notifications when workflow is rejected."""
        try:
            # Notify patient
            self._send_email_notification(
                template_name='prescription_workflow_rejected',
                recipient=self.prescription.patient,
                context={
                    'workflow': self,
                    'prescription': self.prescription,
                    'reviewer': reviewer,
                    'reason': reason,
                }
            )
            
            # Notify prescriber
            self._send_email_notification(
                template_name='prescription_workflow_rejected_prescriber',
                recipient=self.prescription.prescriber,
                context={
                    'workflow': self,
                    'prescription': self.prescription,
                    'reviewer': reviewer,
                    'reason': reason,
                }
            )
            
            logger.info(f"Rejection notifications sent for workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notifications for workflow {self.id}: {e}")
    
    def put_on_hold(self, reviewer: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to approval history
        self.approval_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, reviewer: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to approval history
        self.approval_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.APPROVED, self.Status.REJECTED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len([s for s in self.STAGES.keys() if not self.STAGES[s].get('optional', False)])
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)


class MedicationContentReviewWorkflow(Workflow):
    """
    Clinical accuracy verification workflow for medication content.
    
    This workflow ensures medication information is clinically accurate,
    up-to-date, and meets regulatory standards before publication.
    """
    
    # Workflow stages
    STAGES = {
        'content_analysis': {
            'name': _('Content Analysis'),
            'description': _('Initial analysis of medication content for completeness'),
            'required_role': 'CLINICAL_EDITOR',
            'estimated_duration': timedelta(hours=6),
            'email_template': 'medication_content_analysis',
        },
        'clinical_verification': {
            'name': _('Clinical Verification'),
            'description': _('Clinical accuracy verification by healthcare professionals'),
            'required_role': 'DOCTOR',
            'estimated_duration': timedelta(hours=12),
            'email_template': 'medication_clinical_verification',
        },
        'regulatory_compliance': {
            'name': _('Regulatory Compliance'),
            'description': _('Regulatory compliance verification and approval'),
            'required_role': 'REGULATORY_OFFICER',
            'estimated_duration': timedelta(hours=8),
            'email_template': 'medication_regulatory_compliance',
        },
        'final_approval': {
            'name': _('Final Approval'),
            'description': _('Final approval for publication'),
            'required_role': 'SENIOR_CLINICAL_EDITOR',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'medication_final_approval',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Workflow fields
    medication = models.ForeignKey(
        'medications.Medication',
        on_delete=models.CASCADE,
        related_name='content_review_workflows',
        help_text=_('Associated medication')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='content_analysis',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_content_review_workflows',
        help_text=_('Currently assigned reviewer')
    )
    
    review_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Review notes for each stage')
    )
    
    review_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete review history')
    )
    
    content_version = models.CharField(
        max_length=20,
        default='1.0',
        help_text=_('Content version being reviewed')
    )
    
    clinical_accuracy_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Clinical accuracy score (1-100)')
    )
    
    regulatory_compliance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Regulatory compliance score (1-100)')
    )
    
    content_quality_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Content quality score (1-100)')
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
        ],
        default='routine',
        help_text=_('Priority level for processing')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Medication Content Review Workflow')
        verbose_name_plural = _('Medication Content Review Workflows')
        db_table = 'healthcare_medication_content_review_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_reviewer', 'status']),
            models.Index(fields=['priority_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['clinical_accuracy_score']),
            models.Index(fields=['regulatory_compliance_score']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Content Review for {self.medication.name} (v{self.content_version})"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on priority and stages."""
        base_duration = timedelta(hours=24)  # Base duration for routine cases
        
        if self.priority_level == 'urgent':
            base_duration = timedelta(hours=12)
        elif self.priority_level == 'emergency':
            base_duration = timedelta(hours=4)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name='medication_content_review_assigned',
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            logger.info(f"Initial notifications sent for content review workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for content review workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for content review workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for content review workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, reviewer: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.APPROVED
            self.actual_completion = timezone.now()
            self._complete_workflow(reviewer, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_reviewer = self._get_next_reviewer(next_stage)
            
            # Add to review history
            self.review_history.append({
                'stage': self.current_stage,
                'reviewer': reviewer.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'approved',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update quality scores based on review."""
        if 'clinical_accuracy' in scores:
            self.clinical_accuracy_score = scores['clinical_accuracy']
        if 'regulatory_compliance' in scores:
            self.regulatory_compliance_score = scores['regulatory_compliance']
        if 'content_quality' in scores:
            self.content_quality_score = scores['content_quality']
    
    def _get_next_reviewer(self, stage: str) -> Optional[User]:
        """Get the next reviewer for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_reviewers = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_content_review_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_reviewers.exists():
            return available_reviewers.first()
        
        # If no available reviewers, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, reviewer: User, notes: str = None):
        """Complete the workflow and update medication status."""
        # Update medication status to approved for publication
        self.medication.is_approved_for_publication = True
        self.medication.last_review_date = timezone.now()
        self.medication.reviewed_by = reviewer
        self.medication.save()
        
        # Send completion notifications
        self._send_completion_notifications(reviewer, notes)
    
    def _send_completion_notifications(self, reviewer: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify content creators
            content_creators = User.objects.filter(
                user_type__in=['CLINICAL_EDITOR', 'CONTENT_CREATOR']
            )
            
            for creator in content_creators:
                self._send_email_notification(
                    template_name='medication_content_review_completed',
                    recipient=creator,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                        'reviewer': reviewer,
                        'notes': notes,
                        'scores': {
                            'clinical_accuracy': self.clinical_accuracy_score,
                            'regulatory_compliance': self.regulatory_compliance_score,
                            'content_quality': self.content_quality_score,
                        }
                    }
                )
            
            logger.info(f"Completion notifications sent for content review workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for content review workflow {self.id}: {e}")
    
    def reject_workflow(self, reviewer: User, reason: str, required_changes: str = None):
        """Reject the workflow and specify required changes."""
        self.status = self.Status.REJECTED
        self.actual_completion = timezone.now()
        
        # Add to review history
        self.review_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'required_changes': required_changes,
            'action': 'rejected'
        })
        
        # Send rejection notifications
        self._send_rejection_notifications(reviewer, reason, required_changes)
        
        self.save()
    
    def _send_rejection_notifications(self, reviewer: User, reason: str, required_changes: str = None):
        """Send notifications when workflow is rejected."""
        try:
            # Notify content creators
            content_creators = User.objects.filter(
                user_type__in=['CLINICAL_EDITOR', 'CONTENT_CREATOR']
            )
            
            for creator in content_creators:
                self._send_email_notification(
                    template_name='medication_content_review_rejected',
                    recipient=creator,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                        'reviewer': reviewer,
                        'reason': reason,
                        'required_changes': required_changes,
                    }
                )
            
            logger.info(f"Rejection notifications sent for content review workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notifications for content review workflow {self.id}: {e}")
    
    def put_on_hold(self, reviewer: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to review history
        self.review_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, reviewer: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to review history
        self.review_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.APPROVED, self.Status.REJECTED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len([s for s in self.STAGES.keys() if not self.STAGES[s].get('optional', False)])
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def overall_quality_score(self) -> Optional[int]:
        """Calculate overall quality score."""
        scores = []
        if self.clinical_accuracy_score:
            scores.append(self.clinical_accuracy_score)
        if self.regulatory_compliance_score:
            scores.append(self.regulatory_compliance_score)
        if self.content_quality_score:
            scores.append(self.content_quality_score)
        
        return sum(scores) // len(scores) if scores else None


class PatientDataAccessWorkflow(Workflow):
    """
    HIPAA-compliant patient data access workflow.
    
    This workflow ensures secure and compliant access to patient health
    information with proper authorization and audit trails.
    """
    
    # Workflow stages
    STAGES = {
        'access_request': {
            'name': _('Access Request'),
            'description': _('Initial access request validation and documentation'),
            'required_role': 'DATA_ACCESS_OFFICER',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'patient_data_access_request',
        },
        'authorization_verification': {
            'name': _('Authorization Verification'),
            'description': _('Verify user authorization and purpose of access'),
            'required_role': 'COMPLIANCE_OFFICER',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'patient_data_authorization_verification',
        },
        'patient_consent_check': {
            'name': _('Patient Consent Check'),
            'description': _('Verify patient consent for data access'),
            'required_role': 'PRIVACY_OFFICER',
            'estimated_duration': timedelta(hours=6),
            'email_template': 'patient_data_consent_check',
            'optional': True,
        },
        'security_review': {
            'name': _('Security Review'),
            'description': _('Security assessment and access method validation'),
            'required_role': 'SECURITY_OFFICER',
            'estimated_duration': timedelta(hours=3),
            'email_template': 'patient_data_security_review',
        },
        'final_approval': {
            'name': _('Final Approval'),
            'description': _('Final approval for data access'),
            'required_role': 'SENIOR_COMPLIANCE_OFFICER',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'patient_data_final_approval',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Access type choices
    class AccessType(models.TextChoices):
        TREATMENT = 'treatment', _('Treatment')
        PAYMENT = 'payment', _('Payment')
        HEALTHCARE_OPERATIONS = 'healthcare_operations', _('Healthcare Operations')
        RESEARCH = 'research', _('Research')
        LEGAL = 'legal', _('Legal')
        EMERGENCY = 'emergency', _('Emergency')
        PUBLIC_HEALTH = 'public_health', _('Public Health')
    
    # Workflow fields
    requesting_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='data_access_requests',
        help_text=_('User requesting data access')
    )
    
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='data_access_workflows',
        help_text=_('Patient whose data is being accessed')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='access_request',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_data_access_workflows',
        help_text=_('Currently assigned reviewer')
    )
    
    access_type = models.CharField(
        max_length=30,
        choices=AccessType.choices,
        help_text=_('Type of data access requested')
    )
    
    access_purpose = models.TextField(
        help_text=_('Detailed purpose of data access')
    )
    
    requested_data_types = models.JSONField(
        default=list,
        help_text=_('Types of patient data requested')
    )
    
    access_duration = models.DurationField(
        help_text=_('Requested duration of access')
    )
    
    review_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Review notes for each stage')
    )
    
    access_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete access history')
    )
    
    hipaa_compliance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('HIPAA compliance score (1-100)')
    )
    
    security_assessment_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Security assessment score (1-100)')
    )
    
    patient_consent_verified = models.BooleanField(
        default=False,
        help_text=_('Whether patient consent has been verified')
    )
    
    emergency_override = models.BooleanField(
        default=False,
        help_text=_('Whether emergency override was used')
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
        ],
        default='routine',
        help_text=_('Priority level for processing')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    access_granted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When access was actually granted')
    )
    
    access_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When access expires')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Patient Data Access Workflow')
        verbose_name_plural = _('Patient Data Access Workflows')
        db_table = 'healthcare_patient_data_access_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_reviewer', 'status']),
            models.Index(fields=['priority_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['access_type', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['requesting_user', 'status']),
            models.Index(fields=['access_expires_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Data Access for {self.patient} by {self.requesting_user} ({self.access_type})"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on priority and stages."""
        base_duration = timedelta(hours=12)  # Base duration for routine cases
        
        if self.priority_level == 'urgent':
            base_duration = timedelta(hours=6)
        elif self.priority_level == 'emergency':
            base_duration = timedelta(hours=2)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name='patient_data_access_assigned',
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_user': self.requesting_user,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify requesting user
            self._send_email_notification(
                template_name='patient_data_access_requested',
                recipient=self.requesting_user,
                context={
                    'workflow': self,
                    'patient': self.patient,
                }
            )
            
            logger.info(f"Initial notifications sent for data access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for data access workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_user': self.requesting_user,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for data access workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for data access workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, reviewer: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.APPROVED
            self.actual_completion = timezone.now()
            self._complete_workflow(reviewer, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_reviewer = self._get_next_reviewer(next_stage)
            
            # Add to access history
            self.access_history.append({
                'stage': self.current_stage,
                'reviewer': reviewer.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'approved',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update compliance scores based on review."""
        if 'hipaa_compliance' in scores:
            self.hipaa_compliance_score = scores['hipaa_compliance']
        if 'security_assessment' in scores:
            self.security_assessment_score = scores['security_assessment']
    
    def _get_next_reviewer(self, stage: str) -> Optional[User]:
        """Get the next reviewer for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_reviewers = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_data_access_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_reviewers.exists():
            return available_reviewers.first()
        
        # If no available reviewers, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, reviewer: User, notes: str = None):
        """Complete the workflow and grant data access."""
        # Grant access
        self.access_granted_at = timezone.now()
        self.access_expires_at = timezone.now() + self.access_duration
        
        # Send completion notifications
        self._send_completion_notifications(reviewer, notes)
    
    def _send_completion_notifications(self, reviewer: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify requesting user
            self._send_email_notification(
                template_name='patient_data_access_granted',
                recipient=self.requesting_user,
                context={
                    'workflow': self,
                    'patient': self.patient,
                    'reviewer': reviewer,
                    'notes': notes,
                    'access_expires_at': self.access_expires_at,
                }
            )
            
            # Notify patient (if consent is required)
            if self.access_type in ['research', 'marketing']:
                self._send_email_notification(
                    template_name='patient_data_access_notification',
                    recipient=self.patient.user,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_user': self.requesting_user,
                        'access_type': self.access_type,
                        'access_expires_at': self.access_expires_at,
                    }
                )
            
            logger.info(f"Completion notifications sent for data access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for data access workflow {self.id}: {e}")
    
    def reject_workflow(self, reviewer: User, reason: str, compliance_issues: str = None):
        """Reject the workflow and specify compliance issues."""
        self.status = self.Status.REJECTED
        self.actual_completion = timezone.now()
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'compliance_issues': compliance_issues,
            'action': 'rejected'
        })
        
        # Send rejection notifications
        self._send_rejection_notifications(reviewer, reason, compliance_issues)
        
        self.save()
    
    def _send_rejection_notifications(self, reviewer: User, reason: str, compliance_issues: str = None):
        """Send notifications when workflow is rejected."""
        try:
            # Notify requesting user
            self._send_email_notification(
                template_name='patient_data_access_rejected',
                recipient=self.requesting_user,
                context={
                    'workflow': self,
                    'patient': self.patient,
                    'reviewer': reviewer,
                    'reason': reason,
                    'compliance_issues': compliance_issues,
                }
            )
            
            logger.info(f"Rejection notifications sent for data access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notifications for data access workflow {self.id}: {e}")
    
    def put_on_hold(self, reviewer: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, reviewer: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    def emergency_override_access(self, reviewer: User, reason: str):
        """Grant emergency override access."""
        self.emergency_override = True
        self.status = self.Status.APPROVED
        self.actual_completion = timezone.now()
        self.access_granted_at = timezone.now()
        self.access_expires_at = timezone.now() + timedelta(hours=24)  # Emergency access expires in 24 hours
        
        # Add to access history
        self.access_history.append({
            'stage': 'emergency_override',
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': f"Emergency override: {reason}",
            'action': 'emergency_override'
        })
        
        # Send emergency notifications
        self._send_emergency_notifications(reviewer, reason)
        
        self.save()
    
    def _send_emergency_notifications(self, reviewer: User, reason: str):
        """Send notifications for emergency override."""
        try:
            # Notify requesting user
            self._send_email_notification(
                template_name='patient_data_emergency_access_granted',
                recipient=self.requesting_user,
                context={
                    'workflow': self,
                    'patient': self.patient,
                    'reviewer': reviewer,
                    'reason': reason,
                    'access_expires_at': self.access_expires_at,
                }
            )
            
            # Notify compliance officers
            compliance_officers = User.objects.filter(
                user_type__in=['COMPLIANCE_OFFICER', 'SENIOR_COMPLIANCE_OFFICER']
            )
            
            for officer in compliance_officers:
                self._send_email_notification(
                    template_name='patient_data_emergency_override_notification',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_user': self.requesting_user,
                        'reviewer': reviewer,
                        'reason': reason,
                    }
                )
            
            logger.info(f"Emergency notifications sent for data access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send emergency notifications for data access workflow {self.id}: {e}")
    
    def revoke_access(self, reviewer: User, reason: str):
        """Revoke granted access."""
        self.access_expires_at = timezone.now()
        
        # Add to access history
        self.access_history.append({
            'stage': 'access_revoked',
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'access_revoked'
        })
        
        # Send revocation notifications
        self._send_revocation_notifications(reviewer, reason)
        
        self.save()
    
    def _send_revocation_notifications(self, reviewer: User, reason: str):
        """Send notifications when access is revoked."""
        try:
            # Notify requesting user
            self._send_email_notification(
                template_name='patient_data_access_revoked',
                recipient=self.requesting_user,
                context={
                    'workflow': self,
                    'patient': self.patient,
                    'reviewer': reviewer,
                    'reason': reason,
                }
            )
            
            logger.info(f"Revocation notifications sent for data access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send revocation notifications for data access workflow {self.id}: {e}")
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.APPROVED, self.Status.REJECTED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len([s for s in self.STAGES.keys() if not self.STAGES[s].get('optional', False)])
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def overall_compliance_score(self) -> Optional[int]:
        """Calculate overall compliance score."""
        scores = []
        if self.hipaa_compliance_score:
            scores.append(self.hipaa_compliance_score)
        if self.security_assessment_score:
            scores.append(self.security_assessment_score)
        
        return sum(scores) // len(scores) if scores else None
    
    @property
    def is_access_active(self) -> bool:
        """Check if access is currently active."""
        if not self.access_granted_at or not self.access_expires_at:
            return False
        
        now = timezone.now()
        return self.access_granted_at <= now <= self.access_expires_at
    
    @property
    def is_access_expired(self) -> bool:
        """Check if access has expired."""
        if not self.access_expires_at:
            return False
        
        return timezone.now() > self.access_expires_at


class PharmacyIntegrationWorkflow(Workflow):
    """
    Third-party pharmacy system integration approval workflow.
    
    This workflow manages the approval process for integrating with
    external pharmacy systems, ensuring security and compliance standards.
    """
    
    # Workflow stages
    STAGES = {
        'integration_request': {
            'name': _('Integration Request'),
            'description': _('Initial integration request validation and documentation'),
            'required_role': 'INTEGRATION_SPECIALIST',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'pharmacy_integration_request',
        },
        'security_assessment': {
            'name': _('Security Assessment'),
            'description': _('Security assessment of the pharmacy system and integration'),
            'required_role': 'SECURITY_OFFICER',
            'estimated_duration': timedelta(hours=8),
            'email_template': 'pharmacy_integration_security_assessment',
        },
        'compliance_review': {
            'name': _('Compliance Review'),
            'description': _('Regulatory compliance verification for pharmacy integration'),
            'required_role': 'COMPLIANCE_OFFICER',
            'estimated_duration': timedelta(hours=6),
            'email_template': 'pharmacy_integration_compliance_review',
        },
        'technical_validation': {
            'name': _('Technical Validation'),
            'description': _('Technical validation of integration capabilities and APIs'),
            'required_role': 'TECHNICAL_LEAD',
            'estimated_duration': timedelta(hours=12),
            'email_template': 'pharmacy_integration_technical_validation',
        },
        'legal_review': {
            'name': _('Legal Review'),
            'description': _('Legal review of terms, conditions, and data sharing agreements'),
            'required_role': 'LEGAL_OFFICER',
            'estimated_duration': timedelta(hours=8),
            'email_template': 'pharmacy_integration_legal_review',
        },
        'final_approval': {
            'name': _('Final Approval'),
            'description': _('Final approval for pharmacy system integration'),
            'required_role': 'SENIOR_INTEGRATION_MANAGER',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'pharmacy_integration_final_approval',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Integration type choices
    class IntegrationType(models.TextChoices):
        API_INTEGRATION = 'api_integration', _('API Integration')
        HL7_INTEGRATION = 'hl7_integration', _('HL7 Integration')
        FHIR_INTEGRATION = 'fhir_integration', _('FHIR Integration')
        DIRECT_CONNECTION = 'direct_connection', _('Direct Connection')
        CLOUD_INTEGRATION = 'cloud_integration', _('Cloud Integration')
    
    # Workflow fields
    requesting_organization = models.CharField(
        max_length=200,
        help_text=_('Name of the requesting pharmacy organization')
    )
    
    pharmacy_system_name = models.CharField(
        max_length=200,
        help_text=_('Name of the pharmacy system to integrate with')
    )
    
    integration_type = models.CharField(
        max_length=30,
        choices=IntegrationType.choices,
        help_text=_('Type of integration requested')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='integration_request',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_pharmacy_integration_workflows',
        help_text=_('Currently assigned reviewer')
    )
    
    integration_purpose = models.TextField(
        help_text=_('Purpose and benefits of the integration')
    )
    
    technical_specifications = models.JSONField(
        default=dict,
        help_text=_('Technical specifications and requirements')
    )
    
    security_requirements = models.JSONField(
        default=dict,
        help_text=_('Security requirements and protocols')
    )
    
    compliance_requirements = models.JSONField(
        default=dict,
        help_text=_('Compliance requirements and certifications')
    )
    
    review_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Review notes for each stage')
    )
    
    integration_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete integration approval history')
    )
    
    security_assessment_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Security assessment score (1-100)')
    )
    
    compliance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Compliance score (1-100)')
    )
    
    technical_feasibility_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Technical feasibility score (1-100)')
    )
    
    risk_assessment_level = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('critical', _('Critical')),
        ],
        default='medium',
        help_text=_('Risk assessment level')
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
        ],
        default='routine',
        help_text=_('Priority level for processing')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    integration_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When integration was approved')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Pharmacy Integration Workflow')
        verbose_name_plural = _('Pharmacy Integration Workflows')
        db_table = 'healthcare_pharmacy_integration_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_reviewer', 'status']),
            models.Index(fields=['priority_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['integration_type', 'status']),
            models.Index(fields=['requesting_organization', 'status']),
            models.Index(fields=['risk_assessment_level']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Integration for {self.pharmacy_system_name} by {self.requesting_organization}"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on priority and stages."""
        base_duration = timedelta(hours=36)  # Base duration for routine cases
        
        if self.priority_level == 'urgent':
            base_duration = timedelta(hours=24)
        elif self.priority_level == 'emergency':
            base_duration = timedelta(hours=12)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name='pharmacy_integration_assigned',
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify integration specialists
            integration_specialists = User.objects.filter(
                user_type='INTEGRATION_SPECIALIST'
            )
            
            for specialist in integration_specialists:
                self._send_email_notification(
                    template_name='pharmacy_integration_requested',
                    recipient=specialist,
                    context={
                        'workflow': self,
                    }
                )
            
            logger.info(f"Initial notifications sent for pharmacy integration workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for pharmacy integration workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for pharmacy integration workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for pharmacy integration workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, reviewer: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.APPROVED
            self.actual_completion = timezone.now()
            self.integration_approved_at = timezone.now()
            self._complete_workflow(reviewer, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_reviewer = self._get_next_reviewer(next_stage)
            
            # Add to integration history
            self.integration_history.append({
                'stage': self.current_stage,
                'reviewer': reviewer.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'approved',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update assessment scores based on review."""
        if 'security_assessment' in scores:
            self.security_assessment_score = scores['security_assessment']
        if 'compliance' in scores:
            self.compliance_score = scores['compliance']
        if 'technical_feasibility' in scores:
            self.technical_feasibility_score = scores['technical_feasibility']
    
    def _get_next_reviewer(self, stage: str) -> Optional[User]:
        """Get the next reviewer for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_reviewers = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_pharmacy_integration_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_reviewers.exists():
            return available_reviewers.first()
        
        # If no available reviewers, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, reviewer: User, notes: str = None):
        """Complete the workflow and approve integration."""
        # Send completion notifications
        self._send_completion_notifications(reviewer, notes)
    
    def _send_completion_notifications(self, reviewer: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify integration specialists
            integration_specialists = User.objects.filter(
                user_type='INTEGRATION_SPECIALIST'
            )
            
            for specialist in integration_specialists:
                self._send_email_notification(
                    template_name='pharmacy_integration_approved',
                    recipient=specialist,
                    context={
                        'workflow': self,
                        'reviewer': reviewer,
                        'notes': notes,
                        'scores': {
                            'security_assessment': self.security_assessment_score,
                            'compliance': self.compliance_score,
                            'technical_feasibility': self.technical_feasibility_score,
                        }
                    }
                )
            
            # Notify technical leads
            technical_leads = User.objects.filter(
                user_type='TECHNICAL_LEAD'
            )
            
            for lead in technical_leads:
                self._send_email_notification(
                    template_name='pharmacy_integration_technical_approval',
                    recipient=lead,
                    context={
                        'workflow': self,
                        'reviewer': reviewer,
                        'notes': notes,
                    }
                )
            
            logger.info(f"Completion notifications sent for pharmacy integration workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for pharmacy integration workflow {self.id}: {e}")
    
    def reject_workflow(self, reviewer: User, reason: str, technical_issues: str = None):
        """Reject the workflow and specify technical issues."""
        self.status = self.Status.REJECTED
        self.actual_completion = timezone.now()
        
        # Add to integration history
        self.integration_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'technical_issues': technical_issues,
            'action': 'rejected'
        })
        
        # Send rejection notifications
        self._send_rejection_notifications(reviewer, reason, technical_issues)
        
        self.save()
    
    def _send_rejection_notifications(self, reviewer: User, reason: str, technical_issues: str = None):
        """Send notifications when workflow is rejected."""
        try:
            # Notify integration specialists
            integration_specialists = User.objects.filter(
                user_type='INTEGRATION_SPECIALIST'
            )
            
            for specialist in integration_specialists:
                self._send_email_notification(
                    template_name='pharmacy_integration_rejected',
                    recipient=specialist,
                    context={
                        'workflow': self,
                        'reviewer': reviewer,
                        'reason': reason,
                        'technical_issues': technical_issues,
                    }
                )
            
            logger.info(f"Rejection notifications sent for pharmacy integration workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notifications for pharmacy integration workflow {self.id}: {e}")
    
    def put_on_hold(self, reviewer: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to integration history
        self.integration_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, reviewer: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to integration history
        self.integration_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.APPROVED, self.Status.REJECTED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len([s for s in self.STAGES.keys() if not self.STAGES[s].get('optional', False)])
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def overall_assessment_score(self) -> Optional[int]:
        """Calculate overall assessment score."""
        scores = []
        if self.security_assessment_score:
            scores.append(self.security_assessment_score)
        if self.compliance_score:
            scores.append(self.compliance_score)
        if self.technical_feasibility_score:
            scores.append(self.technical_feasibility_score)
        
        return sum(scores) // len(scores) if scores else None


class PrescriptionRenewalWorkflow(Workflow):
    """
    Automated prescription renewal workflow.
    
    This workflow manages the automated process of prescription renewals,
    including clinical review, patient communication, and approval processes.
    """
    
    # Workflow stages
    STAGES = {
        'renewal_trigger': {
            'name': _('Renewal Trigger'),
            'description': _('Automatic detection of prescriptions requiring renewal'),
            'required_role': 'SYSTEM_AUTOMATION',
            'estimated_duration': timedelta(minutes=30),
            'email_template': 'prescription_renewal_triggered',
        },
        'patient_notification': {
            'name': _('Patient Notification'),
            'description': _('Notify patient about upcoming prescription renewal'),
            'required_role': 'PATIENT_COORDINATOR',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'prescription_renewal_patient_notification',
        },
        'clinical_review': {
            'name': _('Clinical Review'),
            'description': _('Clinical review of renewal request and patient status'),
            'required_role': 'DOCTOR',
            'estimated_duration': timedelta(hours=8),
            'email_template': 'prescription_renewal_clinical_review',
        },
        'pharmacy_verification': {
            'name': _('Pharmacy Verification'),
            'description': _('Pharmacy verification of medication availability and interactions'),
            'required_role': 'PHARMACIST',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'prescription_renewal_pharmacy_verification',
        },
        'patient_consent': {
            'name': _('Patient Consent'),
            'description': _('Obtain patient consent for prescription renewal'),
            'required_role': 'PATIENT_COORDINATOR',
            'estimated_duration': timedelta(hours=24),
            'email_template': 'prescription_renewal_patient_consent',
            'optional': True,
        },
        'final_approval': {
            'name': _('Final Approval'),
            'description': _('Final approval and prescription renewal'),
            'required_role': 'SENIOR_DOCTOR',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'prescription_renewal_final_approval',
        },
        'renewal_processing': {
            'name': _('Renewal Processing'),
            'description': _('Process the renewed prescription and update records'),
            'required_role': 'PRESCRIPTION_COORDINATOR',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'prescription_renewal_processing',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')
    
    # Renewal type choices
    class RenewalType(models.TextChoices):
        AUTOMATIC = 'automatic', _('Automatic')
        PATIENT_REQUESTED = 'patient_requested', _('Patient Requested')
        DOCTOR_INITIATED = 'doctor_initiated', _('Doctor Initiated')
        PHARMACY_REQUESTED = 'pharmacy_requested', _('Pharmacy Requested')
        SYSTEM_TRIGGERED = 'system_triggered', _('System Triggered')
    
    # Workflow fields
    original_prescription = models.ForeignKey(
        'medications.EnhancedPrescription',
        on_delete=models.CASCADE,
        related_name='renewal_workflows',
        help_text=_('Original prescription being renewed')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='renewal_trigger',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_renewal_workflows',
        help_text=_('Currently assigned reviewer')
    )
    
    renewal_type = models.CharField(
        max_length=30,
        choices=RenewalType.choices,
        default=RenewalType.AUTOMATIC,
        help_text=_('Type of renewal request')
    )
    
    renewal_reason = models.TextField(
        blank=True,
        help_text=_('Reason for prescription renewal')
    )
    
    patient_response = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected')),
            ('needs_clarification', _('Needs Clarification')),
        ],
        default='pending',
        help_text=_('Patient response to renewal request')
    )
    
    clinical_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Clinical notes for renewal review')
    )
    
    renewal_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete renewal history')
    )
    
    medication_changes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Any changes to medication, dosage, or instructions')
    )
    
    patient_consent_obtained = models.BooleanField(
        default=False,
        help_text=_('Whether patient consent has been obtained')
    )
    
    clinical_appropriateness_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Clinical appropriateness score (1-100)')
    )
    
    patient_safety_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Patient safety assessment score (1-100)')
    )
    
    renewal_efficiency_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Renewal process efficiency score (1-100)')
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
        ],
        default='routine',
        help_text=_('Priority level for processing')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    renewal_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When renewal was approved')
    )
    
    renewed_prescription = models.ForeignKey(
        'medications.EnhancedPrescription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='renewed_from_workflow',
        help_text=_('Newly created prescription from renewal')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Prescription Renewal Workflow')
        verbose_name_plural = _('Prescription Renewal Workflows')
        db_table = 'healthcare_prescription_renewal_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_reviewer', 'status']),
            models.Index(fields=['priority_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['renewal_type', 'status']),
            models.Index(fields=['original_prescription', 'status']),
            models.Index(fields=['patient_response']),
            models.Index(fields=['renewal_approved_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Renewal for {self.original_prescription} - {self.renewal_type}"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on priority and stages."""
        base_duration = timedelta(days=3)  # Base duration for routine cases
        
        if self.priority_level == 'urgent':
            base_duration = timedelta(days=1)
        elif self.priority_level == 'emergency':
            base_duration = timedelta(hours=12)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name='prescription_renewal_assigned',
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify patient
            if self.original_prescription.patient:
                self._send_email_notification(
                    template_name='prescription_renewal_patient_notified',
                    recipient=self.original_prescription.patient.user,
                    context={
                        'workflow': self,
                        'prescription': self.original_prescription,
                    }
                )
            
            # Notify prescribing doctor
            if self.original_prescription.prescribing_doctor:
                self._send_email_notification(
                    template_name='prescription_renewal_doctor_notified',
                    recipient=self.original_prescription.prescribing_doctor,
                    context={
                        'workflow': self,
                        'prescription': self.original_prescription,
                    }
                )
            
            logger.info(f"Initial notifications sent for prescription renewal workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for prescription renewal workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned reviewer
            if self.assigned_reviewer:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_reviewer,
                    context={
                        'workflow': self,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for prescription renewal workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for prescription renewal workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, reviewer: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.COMPLETED
            self.actual_completion = timezone.now()
            self._complete_workflow(reviewer, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_reviewer = self._get_next_reviewer(next_stage)
            
            # Add to renewal history
            self.renewal_history.append({
                'stage': self.current_stage,
                'reviewer': reviewer.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'advanced',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update assessment scores based on review."""
        if 'clinical_appropriateness' in scores:
            self.clinical_appropriateness_score = scores['clinical_appropriateness']
        if 'patient_safety' in scores:
            self.patient_safety_score = scores['patient_safety']
        if 'renewal_efficiency' in scores:
            self.renewal_efficiency_score = scores['renewal_efficiency']
    
    def _get_next_reviewer(self, stage: str) -> Optional[User]:
        """Get the next reviewer for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_reviewers = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_renewal_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_reviewers.exists():
            return available_reviewers.first()
        
        # If no available reviewers, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, reviewer: User, notes: str = None):
        """Complete the workflow and create renewed prescription."""
        self.renewal_approved_at = timezone.now()
        
        # Create renewed prescription
        self._create_renewed_prescription(reviewer)
        
        # Send completion notifications
        self._send_completion_notifications(reviewer, notes)
    
    def _create_renewed_prescription(self, reviewer: User):
        """Create a new prescription based on the renewal."""
        try:
            from medications.models import EnhancedPrescription
            
            # Create new prescription with updated information
            renewed_prescription = EnhancedPrescription.objects.create(
                patient=self.original_prescription.patient,
                prescribing_doctor=self.original_prescription.prescribing_doctor,
                medication=self.original_prescription.medication,
                dosage=self.original_prescription.dosage,
                frequency=self.original_prescription.frequency,
                duration=self.original_prescription.duration,
                instructions=self.original_prescription.instructions,
                # Apply any medication changes
                **self.medication_changes,
                # Set renewal-specific fields
                is_renewal=True,
                original_prescription=self.original_prescription,
                renewal_workflow=self,
            )
            
            self.renewed_prescription = renewed_prescription
            self.save()
            
            logger.info(f"Renewed prescription created: {renewed_prescription.id}")
            
        except Exception as e:
            logger.error(f"Failed to create renewed prescription: {e}")
    
    def _send_completion_notifications(self, reviewer: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify patient
            if self.original_prescription.patient:
                self._send_email_notification(
                    template_name='prescription_renewal_completed_patient',
                    recipient=self.original_prescription.patient.user,
                    context={
                        'workflow': self,
                        'prescription': self.renewed_prescription,
                        'reviewer': reviewer,
                        'notes': notes,
                    }
                )
            
            # Notify prescribing doctor
            if self.original_prescription.prescribing_doctor:
                self._send_email_notification(
                    template_name='prescription_renewal_completed_doctor',
                    recipient=self.original_prescription.prescribing_doctor,
                    context={
                        'workflow': self,
                        'prescription': self.renewed_prescription,
                        'reviewer': reviewer,
                        'notes': notes,
                        'scores': {
                            'clinical_appropriateness': self.clinical_appropriateness_score,
                            'patient_safety': self.patient_safety_score,
                            'renewal_efficiency': self.renewal_efficiency_score,
                        }
                    }
                )
            
            # Notify pharmacy if applicable
            if self.original_prescription.pharmacy:
                self._send_email_notification(
                    template_name='prescription_renewal_completed_pharmacy',
                    recipient=self.original_prescription.pharmacy.contact_person,
                    context={
                        'workflow': self,
                        'prescription': self.renewed_prescription,
                        'reviewer': reviewer,
                    }
                )
            
            logger.info(f"Completion notifications sent for prescription renewal workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for prescription renewal workflow {self.id}: {e}")
    
    def reject_workflow(self, reviewer: User, reason: str, clinical_concerns: str = None):
        """Reject the renewal workflow."""
        self.status = self.Status.REJECTED
        
        # Add to renewal history
        self.renewal_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'rejected',
            'clinical_concerns': clinical_concerns or ''
        })
        
        # Send rejection notifications
        self._send_rejection_notifications(reviewer, reason, clinical_concerns)
        
        self.save()
    
    def _send_rejection_notifications(self, reviewer: User, reason: str, clinical_concerns: str = None):
        """Send notifications when renewal is rejected."""
        try:
            # Notify patient
            if self.original_prescription.patient:
                self._send_email_notification(
                    template_name='prescription_renewal_rejected_patient',
                    recipient=self.original_prescription.patient.user,
                    context={
                        'workflow': self,
                        'prescription': self.original_prescription,
                        'reviewer': reviewer,
                        'reason': reason,
                        'clinical_concerns': clinical_concerns,
                    }
                )
            
            # Notify prescribing doctor
            if self.original_prescription.prescribing_doctor:
                self._send_email_notification(
                    template_name='prescription_renewal_rejected_doctor',
                    recipient=self.original_prescription.prescribing_doctor,
                    context={
                        'workflow': self,
                        'prescription': self.original_prescription,
                        'reviewer': reviewer,
                        'reason': reason,
                        'clinical_concerns': clinical_concerns,
                    }
                )
            
            logger.info(f"Rejection notifications sent for prescription renewal workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notifications for prescription renewal workflow {self.id}: {e}")
    
    def put_on_hold(self, reviewer: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to renewal history
        self.renewal_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, reviewer: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to renewal history
        self.renewal_history.append({
            'stage': self.current_stage,
            'reviewer': reviewer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    def update_patient_response(self, response: str, notes: str = None):
        """Update patient response to renewal request."""
        self.patient_response = response
        
        # Add to renewal history
        self.renewal_history.append({
            'stage': self.current_stage,
            'timestamp': timezone.now().isoformat(),
            'notes': notes or '',
            'action': 'patient_response',
            'response': response
        })
        
        # Update patient consent status
        if response == 'approved':
            self.patient_consent_obtained = True
        
        self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.COMPLETED, self.Status.APPROVED, self.Status.REJECTED, self.Status.CANCELLED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len([s for s in self.STAGES.keys() if not self.STAGES[s].get('optional', False)])
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def overall_renewal_score(self) -> Optional[int]:
        """Calculate overall renewal assessment score."""
        scores = []
        if self.clinical_appropriateness_score:
            scores.append(self.clinical_appropriateness_score)
        if self.patient_safety_score:
            scores.append(self.patient_safety_score)
        if self.renewal_efficiency_score:
            scores.append(self.renewal_efficiency_score)
        
        return sum(scores) // len(scores) if scores else None
    
    @property
    def requires_patient_consent(self) -> bool:
        """Check if patient consent is required for this renewal."""
        return self.renewal_type in [
            self.RenewalType.PATIENT_REQUESTED,
            self.RenewalType.SYSTEM_TRIGGERED
        ]
    
    @property
    def is_automatic_renewal(self) -> bool:
        """Check if this is an automatic renewal."""
        return self.renewal_type == self.RenewalType.AUTOMATIC


class MedicationRecallWorkflow(Workflow):
    """
    Medication safety alerts and recall management workflow.
    
    This workflow manages the process of handling medication safety alerts,
    recalls, and adverse event reporting in compliance with regulatory requirements.
    """
    
    # Workflow stages
    STAGES = {
        'alert_received': {
            'name': _('Alert Received'),
            'description': _('Initial safety alert or recall notification received'),
            'required_role': 'SAFETY_OFFICER',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'medication_recall_alert_received',
        },
        'risk_assessment': {
            'name': _('Risk Assessment'),
            'description': _('Assessment of patient safety risk and impact'),
            'required_role': 'CLINICAL_PHARMACIST',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'medication_recall_risk_assessment',
        },
        'regulatory_notification': {
            'name': _('Regulatory Notification'),
            'description': _('Notification to regulatory authorities and stakeholders'),
            'required_role': 'REGULATORY_OFFICER',
            'estimated_duration': timedelta(hours=6),
            'email_template': 'medication_recall_regulatory_notification',
        },
        'patient_communication': {
            'name': _('Patient Communication'),
            'description': _('Communication to affected patients and healthcare providers'),
            'required_role': 'PATIENT_SAFETY_OFFICER',
            'estimated_duration': timedelta(hours=8),
            'email_template': 'medication_recall_patient_communication',
        },
        'inventory_management': {
            'name': _('Inventory Management'),
            'description': _('Management of affected medication inventory and disposal'),
            'required_role': 'INVENTORY_MANAGER',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'medication_recall_inventory_management',
        },
        'monitoring_followup': {
            'name': _('Monitoring & Follow-up'),
            'description': _('Ongoing monitoring and follow-up of recall effectiveness'),
            'required_role': 'SAFETY_OFFICER',
            'estimated_duration': timedelta(days=7),
            'email_template': 'medication_recall_monitoring_followup',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        ESCALATED = 'escalated', _('Escalated')
    
    # Alert type choices
    class AlertType(models.TextChoices):
        SAFETY_ALERT = 'safety_alert', _('Safety Alert')
        RECALL = 'recall', _('Recall')
        ADVERSE_EVENT = 'adverse_event', _('Adverse Event')
        QUALITY_ISSUE = 'quality_issue', _('Quality Issue')
        CONTAMINATION = 'contamination', _('Contamination')
        LABELING_ERROR = 'labeling_error', _('Labeling Error')
        MANUFACTURING_DEFECT = 'manufacturing_defect', _('Manufacturing Defect')
    
    # Risk level choices
    class RiskLevel(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # Workflow fields
    medication_name = models.CharField(
        max_length=200,
        help_text=_('Name of the affected medication')
    )
    
    manufacturer = models.CharField(
        max_length=200,
        help_text=_('Manufacturer of the affected medication')
    )
    
    lot_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Affected lot number(s)')
    )
    
    alert_type = models.CharField(
        max_length=30,
        choices=AlertType.choices,
        help_text=_('Type of safety alert or recall')
    )
    
    risk_level = models.CharField(
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
        help_text=_('Risk level assessment')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='alert_received',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_officer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_medication_recall_workflows',
        help_text=_('Currently assigned safety officer')
    )
    
    alert_description = models.TextField(
        help_text=_('Description of the safety alert or recall')
    )
    
    affected_patients_count = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Estimated number of affected patients')
    )
    
    affected_inventory_count = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Quantity of affected inventory')
    )
    
    regulatory_requirements = models.JSONField(
        default=dict,
        help_text=_('Regulatory requirements and reporting obligations')
    )
    
    patient_impact_assessment = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Assessment of patient impact and safety concerns')
    )
    
    communication_plan = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Communication plan for stakeholders')
    )
    
    recall_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete recall management history')
    )
    
    safety_assessment_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Safety assessment score (1-100)')
    )
    
    regulatory_compliance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Regulatory compliance score (1-100)')
    )
    
    communication_effectiveness_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Communication effectiveness score (1-100)')
    )
    
    urgency_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
            ('immediate', _('Immediate')),
        ],
        default='urgent',
        help_text=_('Urgency level for response')
    )
    
    regulatory_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Regulatory reporting deadline')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    recall_initiated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When recall was initiated')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Medication Recall Workflow')
        verbose_name_plural = _('Medication Recall Workflows')
        db_table = 'healthcare_medication_recall_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_officer', 'status']),
            models.Index(fields=['urgency_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['medication_name', 'status']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['regulatory_deadline']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recall for {self.medication_name} - {self.alert_type}"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
            self._set_regulatory_deadline()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on urgency and stages."""
        base_duration = timedelta(days=7)  # Base duration for routine cases
        
        if self.urgency_level == 'urgent':
            base_duration = timedelta(days=3)
        elif self.urgency_level == 'emergency':
            base_duration = timedelta(days=1)
        elif self.urgency_level == 'immediate':
            base_duration = timedelta(hours=12)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _set_regulatory_deadline(self):
        """Set regulatory deadline based on alert type and risk level."""
        base_deadline = timezone.now() + timedelta(days=1)  # Default 24 hours
        
        if self.risk_level == self.RiskLevel.CRITICAL:
            base_deadline = timezone.now() + timedelta(hours=4)
        elif self.risk_level == self.RiskLevel.HIGH:
            base_deadline = timezone.now() + timedelta(hours=12)
        elif self.risk_level == self.RiskLevel.MEDIUM:
            base_deadline = timezone.now() + timedelta(days=1)
        elif self.risk_level == self.RiskLevel.LOW:
            base_deadline = timezone.now() + timedelta(days=3)
        
        self.regulatory_deadline = base_deadline
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned officer
            if self.assigned_officer:
                self._send_email_notification(
                    template_name='medication_recall_assigned',
                    recipient=self.assigned_officer,
                    context={
                        'workflow': self,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify safety officers
            safety_officers = User.objects.filter(
                user_type='SAFETY_OFFICER'
            )
            
            for officer in safety_officers:
                self._send_email_notification(
                    template_name='medication_recall_alerted',
                    recipient=officer,
                    context={
                        'workflow': self,
                    }
                )
            
            # Notify clinical pharmacists for high/critical risk
            if self.risk_level in [self.RiskLevel.HIGH, self.RiskLevel.CRITICAL]:
                clinical_pharmacists = User.objects.filter(
                    user_type='CLINICAL_PHARMACIST'
                )
                
                for pharmacist in clinical_pharmacists:
                    self._send_email_notification(
                        template_name='medication_recall_high_risk_alert',
                        recipient=pharmacist,
                        context={
                            'workflow': self,
                        }
                    )
            
            logger.info(f"Initial notifications sent for medication recall workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for medication recall workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned officer
            if self.assigned_officer:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_officer,
                    context={
                        'workflow': self,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for medication recall workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for medication recall workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, officer: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.COMPLETED
            self.actual_completion = timezone.now()
            self._complete_workflow(officer, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_officer = self._get_next_officer(next_stage)
            
            # Add to recall history
            self.recall_history.append({
                'stage': self.current_stage,
                'officer': officer.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'advanced',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update assessment scores based on review."""
        if 'safety_assessment' in scores:
            self.safety_assessment_score = scores['safety_assessment']
        if 'regulatory_compliance' in scores:
            self.regulatory_compliance_score = scores['regulatory_compliance']
        if 'communication_effectiveness' in scores:
            self.communication_effectiveness_score = scores['communication_effectiveness']
    
    def _get_next_officer(self, stage: str) -> Optional[User]:
        """Get the next officer for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_officers = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_medication_recall_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_officers.exists():
            return available_officers.first()
        
        # If no available officers, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, officer: User, notes: str = None):
        """Complete the workflow and finalize recall."""
        self.recall_initiated_at = timezone.now()
        
        # Send completion notifications
        self._send_completion_notifications(officer, notes)
    
    def _send_completion_notifications(self, officer: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify safety officers
            safety_officers = User.objects.filter(
                user_type='SAFETY_OFFICER'
            )
            
            for safety_officer in safety_officers:
                self._send_email_notification(
                    template_name='medication_recall_completed',
                    recipient=safety_officer,
                    context={
                        'workflow': self,
                        'officer': officer,
                        'notes': notes,
                        'scores': {
                            'safety_assessment': self.safety_assessment_score,
                            'regulatory_compliance': self.regulatory_compliance_score,
                            'communication_effectiveness': self.communication_effectiveness_score,
                        }
                    }
                )
            
            # Notify regulatory officers
            regulatory_officers = User.objects.filter(
                user_type='REGULATORY_OFFICER'
            )
            
            for reg_officer in regulatory_officers:
                self._send_email_notification(
                    template_name='medication_recall_regulatory_complete',
                    recipient=reg_officer,
                    context={
                        'workflow': self,
                        'officer': officer,
                        'notes': notes,
                    }
                )
            
            logger.info(f"Completion notifications sent for medication recall workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for medication recall workflow {self.id}: {e}")
    
    def escalate_workflow(self, officer: User, reason: str, escalation_level: str = 'management'):
        """Escalate the workflow to higher authority."""
        self.status = self.Status.ESCALATED
        
        # Add to recall history
        self.recall_history.append({
            'stage': self.current_stage,
            'officer': officer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'escalated',
            'escalation_level': escalation_level
        })
        
        # Send escalation notifications
        self._send_escalation_notifications(officer, reason, escalation_level)
        
        self.save()
    
    def _send_escalation_notifications(self, officer: User, reason: str, escalation_level: str):
        """Send notifications when workflow is escalated."""
        try:
            # Notify management based on escalation level
            if escalation_level == 'management':
                managers = User.objects.filter(
                    user_type__in=['SAFETY_MANAGER', 'CLINICAL_MANAGER']
                )
            elif escalation_level == 'executive':
                executives = User.objects.filter(
                    user_type__in=['CHIEF_SAFETY_OFFICER', 'CHIEF_MEDICAL_OFFICER']
                )
            
            recipients = managers if escalation_level == 'management' else executives
            
            for recipient in recipients:
                self._send_email_notification(
                    template_name='medication_recall_escalated',
                    recipient=recipient,
                    context={
                        'workflow': self,
                        'officer': officer,
                        'reason': reason,
                        'escalation_level': escalation_level,
                    }
                )
            
            logger.info(f"Escalation notifications sent for medication recall workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send escalation notifications for medication recall workflow {self.id}: {e}")
    
    def put_on_hold(self, officer: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to recall history
        self.recall_history.append({
            'stage': self.current_stage,
            'officer': officer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, officer: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to recall history
        self.recall_history.append({
            'stage': self.current_stage,
            'officer': officer.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.COMPLETED, self.Status.CANCELLED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def is_escalated(self) -> bool:
        """Check if workflow is escalated."""
        return self.status == self.Status.ESCALATED
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len([s for s in self.STAGES.keys() if not self.STAGES[s].get('optional', False)])
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def is_regulatory_deadline_approaching(self) -> bool:
        """Check if regulatory deadline is approaching (within 24 hours)."""
        if not self.regulatory_deadline:
            return False
        
        time_until_deadline = self.regulatory_deadline - timezone.now()
        return timedelta(0) < time_until_deadline <= timedelta(hours=24)
    
    @property
    def is_regulatory_deadline_overdue(self) -> bool:
        """Check if regulatory deadline has passed."""
        if not self.regulatory_deadline:
            return False
        
        return timezone.now() > self.regulatory_deadline
    
    @property
    def overall_safety_score(self) -> Optional[int]:
        """Calculate overall safety assessment score."""
        scores = []
        if self.safety_assessment_score:
            scores.append(self.safety_assessment_score)
        if self.regulatory_compliance_score:
            scores.append(self.regulatory_compliance_score)
        if self.communication_effectiveness_score:
            scores.append(self.communication_effectiveness_score)
        
        return sum(scores) // len(scores) if scores else None


class MedicationStockWorkflow(Workflow):
    """
    Inventory management and reorder approval workflow.
    
    This workflow manages medication inventory levels, automated reorder
    requests, and approval processes for stock management.
    """
    
    # Workflow stages
    STAGES = {
        'inventory_assessment': {
            'name': _('Inventory Assessment'),
            'description': _('Assessment of current inventory levels and usage patterns'),
            'required_role': 'INVENTORY_MANAGER',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'medication_stock_inventory_assessment',
        },
        'reorder_analysis': {
            'name': _('Reorder Analysis'),
            'description': _('Analysis of reorder requirements and supplier options'),
            'required_role': 'INVENTORY_MANAGER',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'medication_stock_reorder_analysis',
        },
        'clinical_review': {
            'name': _('Clinical Review'),
            'description': _('Clinical review of medication usage and reorder necessity'),
            'required_role': 'CLINICAL_PHARMACIST',
            'estimated_duration': timedelta(hours=6),
            'email_template': 'medication_stock_clinical_review',
        },
        'financial_approval': {
            'name': _('Financial Approval'),
            'description': _('Financial approval for reorder costs and budget allocation'),
            'required_role': 'FINANCIAL_OFFICER',
            'estimated_duration': timedelta(hours=8),
            'email_template': 'medication_stock_financial_approval',
        },
        'supplier_selection': {
            'name': _('Supplier Selection'),
            'description': _('Selection of supplier and negotiation of terms'),
            'required_role': 'PROCUREMENT_OFFICER',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'medication_stock_supplier_selection',
        },
        'final_approval': {
            'name': _('Final Approval'),
            'description': _('Final approval for reorder and purchase order generation'),
            'required_role': 'SENIOR_INVENTORY_MANAGER',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'medication_stock_final_approval',
        },
        'order_processing': {
            'name': _('Order Processing'),
            'description': _('Processing of purchase order and order confirmation'),
            'required_role': 'PROCUREMENT_OFFICER',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'medication_stock_order_processing',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')
    
    # Reorder type choices
    class ReorderType(models.TextChoices):
        AUTOMATIC = 'automatic', _('Automatic')
        MANUAL = 'manual', _('Manual')
        EMERGENCY = 'emergency', _('Emergency')
        SEASONAL = 'seasonal', _('Seasonal')
        BULK = 'bulk', _('Bulk Order')
    
    # Priority level choices
    class PriorityLevel(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
        CRITICAL = 'critical', _('Critical')
    
    # Workflow fields
    medication = models.ForeignKey(
        'medications.Medication',
        on_delete=models.CASCADE,
        related_name='stock_workflows',
        help_text=_('Associated medication')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='inventory_assessment',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_stock_workflows',
        help_text=_('Currently assigned inventory manager')
    )
    
    reorder_type = models.CharField(
        max_length=20,
        choices=ReorderType.choices,
        default=ReorderType.AUTOMATIC,
        help_text=_('Type of reorder request')
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=PriorityLevel.choices,
        default=PriorityLevel.MEDIUM,
        help_text=_('Priority level for processing')
    )
    
    current_stock_level = models.IntegerField(
        help_text=_('Current stock level in units')
    )
    
    reorder_point = models.IntegerField(
        help_text=_('Reorder point threshold')
    )
    
    requested_quantity = models.IntegerField(
        help_text=_('Requested reorder quantity')
    )
    
    estimated_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Estimated cost of reorder')
    )
    
    approved_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Approved budget for reorder')
    )
    
    supplier_options = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Available supplier options and quotes')
    )
    
    selected_supplier = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Selected supplier for reorder')
    )
    
    supplier_contact = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Supplier contact information')
    )
    
    delivery_requirements = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Delivery requirements and timeline')
    )
    
    review_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Review notes for each stage')
    )
    
    stock_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete stock management history')
    )
    
    inventory_efficiency_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Inventory efficiency score (1-100)')
    )
    
    cost_optimization_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Cost optimization score (1-100)')
    )
    
    supplier_performance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Supplier performance score (1-100)')
    )
    
    urgency_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
            ('immediate', _('Immediate')),
        ],
        default='routine',
        help_text=_('Urgency level for processing')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    reorder_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When reorder was approved')
    )
    
    purchase_order_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Generated purchase order number')
    )
    
    expected_delivery_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Expected delivery date')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Medication Stock Workflow')
        verbose_name_plural = _('Medication Stock Workflows')
        db_table = 'healthcare_medication_stock_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_manager', 'status']),
            models.Index(fields=['priority_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['reorder_type', 'status']),
            models.Index(fields=['medication', 'status']),
            models.Index(fields=['urgency_level']),
            models.Index(fields=['current_stock_level']),
            models.Index(fields=['expected_delivery_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Stock workflow for {self.medication} - {self.reorder_type}"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on priority and stages."""
        base_duration = timedelta(days=3)  # Base duration for routine cases
        
        if self.urgency_level == 'urgent':
            base_duration = timedelta(days=1)
        elif self.urgency_level == 'emergency':
            base_duration = timedelta(hours=12)
        elif self.urgency_level == 'immediate':
            base_duration = timedelta(hours=6)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned manager
            if self.assigned_manager:
                self._send_email_notification(
                    template_name='medication_stock_assigned',
                    recipient=self.assigned_manager,
                    context={
                        'workflow': self,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify clinical pharmacist
            clinical_pharmacists = User.objects.filter(
                user_type='CLINICAL_PHARMACIST',
                is_active=True
            )
            for pharmacist in clinical_pharmacists[:3]:  # Notify up to 3 pharmacists
                self._send_email_notification(
                    template_name='medication_stock_clinical_notified',
                    recipient=pharmacist,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                    }
                )
            
            logger.info(f"Initial notifications sent for medication stock workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for medication stock workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned manager
            if self.assigned_manager:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_manager,
                    context={
                        'workflow': self,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for medication stock workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for medication stock workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, manager: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.COMPLETED
            self.actual_completion = timezone.now()
            self._complete_workflow(manager, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_manager = self._get_next_manager(next_stage)
            
            # Add to stock history
            self.stock_history.append({
                'stage': self.current_stage,
                'manager': manager.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'advanced',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update assessment scores based on review."""
        if 'inventory_efficiency' in scores:
            self.inventory_efficiency_score = scores['inventory_efficiency']
        if 'cost_optimization' in scores:
            self.cost_optimization_score = scores['cost_optimization']
        if 'supplier_performance' in scores:
            self.supplier_performance_score = scores['supplier_performance']
    
    def _get_next_manager(self, stage: str) -> Optional[User]:
        """Get the next manager for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_managers = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_stock_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_managers.exists():
            return available_managers.first()
        
        # If no available managers, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, manager: User, notes: str = None):
        """Complete the workflow and generate purchase order."""
        self.reorder_approved_at = timezone.now()
        
        # Generate purchase order
        self._generate_purchase_order(manager)
        
        # Send completion notifications
        self._send_completion_notifications(manager, notes)
    
    def _generate_purchase_order(self, manager: User):
        """Generate purchase order for the reorder."""
        try:
            # Generate unique purchase order number
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            self.purchase_order_number = f"PO-{self.medication.id}-{timestamp}"
            
            # Calculate expected delivery date (typically 7-14 days)
            delivery_days = 10 if self.urgency_level == 'routine' else 3
            self.expected_delivery_date = timezone.now() + timedelta(days=delivery_days)
            
            self.save()
            
            logger.info(f"Purchase order generated: {self.purchase_order_number}")
            
        except Exception as e:
            logger.error(f"Failed to generate purchase order: {e}")
    
    def _send_completion_notifications(self, manager: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify clinical pharmacist
            clinical_pharmacists = User.objects.filter(
                user_type='CLINICAL_PHARMACIST',
                is_active=True
            )
            for pharmacist in clinical_pharmacists[:3]:
                self._send_email_notification(
                    template_name='medication_stock_completed_clinical',
                    recipient=pharmacist,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                        'manager': manager,
                        'notes': notes,
                    }
                )
            
            # Notify procurement officer
            procurement_officers = User.objects.filter(
                user_type='PROCUREMENT_OFFICER',
                is_active=True
            )
            for officer in procurement_officers[:2]:
                self._send_email_notification(
                    template_name='medication_stock_completed_procurement',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                        'manager': manager,
                        'purchase_order': self.purchase_order_number,
                        'expected_delivery': self.expected_delivery_date,
                    }
                )
            
            # Notify supplier if selected
            if self.selected_supplier and self.supplier_contact:
                # This would typically be sent to external supplier
                logger.info(f"Supplier notification prepared for {self.selected_supplier}")
            
            logger.info(f"Completion notifications sent for medication stock workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for medication stock workflow {self.id}: {e}")
    
    def reject_workflow(self, manager: User, reason: str, cost_concerns: str = None):
        """Reject the stock workflow."""
        self.status = self.Status.REJECTED
        
        # Add to stock history
        self.stock_history.append({
            'stage': self.current_stage,
            'manager': manager.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'rejected',
            'cost_concerns': cost_concerns or ''
        })
        
        # Send rejection notifications
        self._send_rejection_notifications(manager, reason, cost_concerns)
        
        self.save()
    
    def _send_rejection_notifications(self, manager: User, reason: str, cost_concerns: str = None):
        """Send notifications when stock workflow is rejected."""
        try:
            # Notify clinical pharmacist
            clinical_pharmacists = User.objects.filter(
                user_type='CLINICAL_PHARMACIST',
                is_active=True
            )
            for pharmacist in clinical_pharmacists[:3]:
                self._send_email_notification(
                    template_name='medication_stock_rejected_clinical',
                    recipient=pharmacist,
                    context={
                        'workflow': self,
                        'medication': self.medication,
                        'manager': manager,
                        'reason': reason,
                        'cost_concerns': cost_concerns,
                    }
                )
            
            logger.info(f"Rejection notifications sent for medication stock workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notifications for medication stock workflow {self.id}: {e}")
    
    def put_on_hold(self, manager: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to stock history
        self.stock_history.append({
            'stage': self.current_stage,
            'manager': manager.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, manager: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to stock history
        self.stock_history.append({
            'stage': self.current_stage,
            'manager': manager.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    def update_supplier_selection(self, supplier: str, contact_info: Dict[str, Any], quote: Dict[str, Any]):
        """Update supplier selection and quote information."""
        self.selected_supplier = supplier
        self.supplier_contact = contact_info
        
        # Add quote to supplier options if not already present
        quote_entry = {
            'supplier': supplier,
            'contact': contact_info,
            'quote': quote,
            'timestamp': timezone.now().isoformat()
        }
        
        if quote_entry not in self.supplier_options:
            self.supplier_options.append(quote_entry)
        
        # Add to stock history
        self.stock_history.append({
            'stage': self.current_stage,
            'timestamp': timezone.now().isoformat(),
            'action': 'supplier_selected',
            'supplier': supplier,
            'quote': quote
        })
        
        self.save()
    
    def update_delivery_requirements(self, requirements: Dict[str, Any]):
        """Update delivery requirements and timeline."""
        self.delivery_requirements = requirements
        
        # Add to stock history
        self.stock_history.append({
            'stage': self.current_stage,
            'timestamp': timezone.now().isoformat(),
            'action': 'delivery_requirements_updated',
            'requirements': requirements
        })
        
        self.save()
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.COMPLETED, self.Status.APPROVED, self.Status.REJECTED, self.Status.CANCELLED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len(self.STAGES)
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def overall_stock_score(self) -> Optional[int]:
        """Calculate overall stock management assessment score."""
        scores = []
        if self.inventory_efficiency_score:
            scores.append(self.inventory_efficiency_score)
        if self.cost_optimization_score:
            scores.append(self.cost_optimization_score)
        if self.supplier_performance_score:
            scores.append(self.supplier_performance_score)
        
        return sum(scores) // len(scores) if scores else None
    
    @property
    def is_stock_critical(self) -> bool:
        """Check if current stock level is critical."""
        return self.current_stock_level <= self.reorder_point
    
    @property
    def is_emergency_reorder(self) -> bool:
        """Check if this is an emergency reorder."""
        return self.reorder_type == self.ReorderType.EMERGENCY
    
    @property
    def cost_per_unit(self) -> Optional[Decimal]:
        """Calculate cost per unit if estimated cost is available."""
        if self.estimated_cost and self.requested_quantity:
            return self.estimated_cost / self.requested_quantity
        return None
    
    @property
    def days_until_stockout(self) -> Optional[int]:
        """Calculate estimated days until stockout based on usage patterns."""
        # This would typically be calculated based on historical usage data
        # For now, return None as this requires additional data
        return None


class PatientConsentWorkflow(Workflow):
    """
    Healthcare data usage permissions management workflow.
    
    This workflow manages patient consent for healthcare data usage,
    ensuring compliance with privacy regulations and patient rights.
    """
    
    # Workflow stages
    STAGES = {
        'consent_request': {
            'name': _('Consent Request'),
            'description': _('Initial consent request creation and documentation'),
            'required_role': 'PATIENT_COORDINATOR',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'patient_consent_request',
        },
        'consent_verification': {
            'name': _('Consent Verification'),
            'description': _('Verification of patient identity and consent capacity'),
            'required_role': 'PRIVACY_OFFICER',
            'estimated_duration': timedelta(hours=4),
            'email_template': 'patient_consent_verification',
        },
        'legal_review': {
            'name': _('Legal Review'),
            'description': _('Legal review of consent terms and conditions'),
            'required_role': 'LEGAL_OFFICER',
            'estimated_duration': timedelta(hours=6),
            'email_template': 'patient_consent_legal_review',
        },
        'patient_education': {
            'name': _('Patient Education'),
            'description': _('Patient education about data usage and rights'),
            'required_role': 'PATIENT_COORDINATOR',
            'estimated_duration': timedelta(hours=3),
            'email_template': 'patient_consent_education',
            'optional': True,
        },
        'consent_approval': {
            'name': _('Consent Approval'),
            'description': _('Final approval of consent terms and conditions'),
            'required_role': 'SENIOR_PRIVACY_OFFICER',
            'estimated_duration': timedelta(hours=2),
            'email_template': 'patient_consent_approval',
        },
        'consent_execution': {
            'name': _('Consent Execution'),
            'description': _('Execution of consent agreement with patient'),
            'required_role': 'PATIENT_COORDINATOR',
            'estimated_duration': timedelta(hours=1),
            'email_template': 'patient_consent_execution',
        },
        'consent_monitoring': {
            'name': _('Consent Monitoring'),
            'description': _('Ongoing monitoring of consent compliance and renewal'),
            'required_role': 'COMPLIANCE_OFFICER',
            'estimated_duration': timedelta(days=30),
            'email_template': 'patient_consent_monitoring',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        ON_HOLD = 'on_hold', _('On Hold')
        CANCELLED = 'cancelled', _('Cancelled')
        COMPLETED = 'completed', _('Completed')
        EXPIRED = 'expired', _('Expired')
        REVOKED = 'revoked', _('Revoked')
    
    # Consent type choices
    class ConsentType(models.TextChoices):
        TREATMENT = 'treatment', _('Treatment')
        RESEARCH = 'research', _('Research')
        MARKETING = 'marketing', _('Marketing')
        THIRD_PARTY = 'third_party', _('Third Party')
        EMERGENCY = 'emergency', _('Emergency')
        MINOR = 'minor', _('Minor Consent')
        GUARDIAN = 'guardian', _('Guardian Consent')
    
    # Consent scope choices
    class ConsentScope(models.TextChoices):
        SPECIFIC = 'specific', _('Specific')
        GENERAL = 'general', _('General')
        LIMITED = 'limited', _('Limited')
        COMPREHENSIVE = 'comprehensive', _('Comprehensive')
    
    # Workflow fields
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='consent_workflows',
        help_text=_('Patient providing consent')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='consent_request',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_coordinator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_consent_workflows',
        help_text=_('Currently assigned patient coordinator')
    )
    
    consent_type = models.CharField(
        max_length=30,
        choices=ConsentType.choices,
        help_text=_('Type of consent being requested')
    )
    
    consent_scope = models.CharField(
        max_length=30,
        choices=ConsentScope.choices,
        default=ConsentScope.SPECIFIC,
        help_text=_('Scope of consent')
    )
    
    data_usage_purpose = models.TextField(
        help_text=_('Purpose of data usage')
    )
    
    data_types_covered = models.JSONField(
        default=list,
        help_text=_('Types of data covered by consent')
    )
    
    third_parties = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Third parties with data access')
    )
    
    consent_duration = models.DurationField(
        help_text=_('Duration of consent validity')
    )
    
    consent_terms = models.TextField(
        help_text=_('Terms and conditions of consent')
    )
    
    review_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Review notes for each stage')
    )
    
    consent_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete consent history')
    )
    
    patient_verification_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Patient verification score (1-100)')
    )
    
    legal_compliance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Legal compliance score (1-100)')
    )
    
    patient_understanding_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Patient understanding score (1-100)')
    )
    
    consent_capacity_verified = models.BooleanField(
        default=False,
        help_text=_('Whether patient consent capacity has been verified')
    )
    
    guardian_consent_required = models.BooleanField(
        default=False,
        help_text=_('Whether guardian consent is required')
    )
    
    guardian_information = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Guardian information if applicable')
    )
    
    emergency_override = models.BooleanField(
        default=False,
        help_text=_('Whether emergency override was used')
    )
    
    priority_level = models.CharField(
        max_length=20,
        choices=[
            ('routine', _('Routine')),
            ('urgent', _('Urgent')),
            ('emergency', _('Emergency')),
        ],
        default='routine',
        help_text=_('Priority level for processing')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    consent_granted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When consent was granted')
    )
    
    consent_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When consent expires')
    )
    
    consent_revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When consent was revoked')
    )
    
    renewal_reminder_sent = models.BooleanField(
        default=False,
        help_text=_('Whether renewal reminder has been sent')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Patient Consent Workflow')
        verbose_name_plural = _('Patient Consent Workflows')
        db_table = 'healthcare_patient_consent_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_coordinator', 'status']),
            models.Index(fields=['priority_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['consent_type', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['consent_expires_at']),
            models.Index(fields=['consent_granted_at']),
            models.Index(fields=['guardian_consent_required']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Consent workflow for {self.patient} - {self.consent_type}"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
            self._calculate_consent_expiry()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on priority and stages."""
        base_duration = timedelta(days=5)  # Base duration for routine cases
        
        if self.priority_level == 'urgent':
            base_duration = timedelta(days=2)
        elif self.priority_level == 'emergency':
            base_duration = timedelta(hours=12)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _calculate_consent_expiry(self):
        """Calculate consent expiry date based on duration."""
        if self.consent_duration:
            self.consent_expires_at = timezone.now() + self.consent_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify assigned coordinator
            if self.assigned_coordinator:
                self._send_email_notification(
                    template_name='patient_consent_assigned',
                    recipient=self.assigned_coordinator,
                    context={
                        'workflow': self,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify privacy officer
            privacy_officers = User.objects.filter(
                user_type='PRIVACY_OFFICER',
                is_active=True
            )
            for officer in privacy_officers[:2]:  # Notify up to 2 officers
                self._send_email_notification(
                    template_name='patient_consent_privacy_notified',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                    }
                )
            
            # Notify legal officer if required
            if self.consent_type in [self.ConsentType.RESEARCH, self.ConsentType.THIRD_PARTY]:
                legal_officers = User.objects.filter(
                    user_type='LEGAL_OFFICER',
                    is_active=True
                )
                for officer in legal_officers[:2]:
                    self._send_email_notification(
                        template_name='patient_consent_legal_notified',
                        recipient=officer,
                        context={
                            'workflow': self,
                            'patient': self.patient,
                        }
                    )
            
            logger.info(f"Initial notifications sent for patient consent workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for patient consent workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned coordinator
            if self.assigned_coordinator:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_coordinator,
                    context={
                        'workflow': self,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for patient consent workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for patient consent workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, coordinator: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.COMPLETED
            self.actual_completion = timezone.now()
            self._complete_workflow(coordinator, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_coordinator = self._get_next_coordinator(next_stage)
            
            # Add to consent history
            self.consent_history.append({
                'stage': self.current_stage,
                'coordinator': coordinator.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'advanced',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update assessment scores based on review."""
        if 'patient_verification' in scores:
            self.patient_verification_score = scores['patient_verification']
        if 'legal_compliance' in scores:
            self.legal_compliance_score = scores['legal_compliance']
        if 'patient_understanding' in scores:
            self.patient_understanding_score = scores['patient_understanding']
    
    def _get_next_coordinator(self, stage: str) -> Optional[User]:
        """Get the next coordinator for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_coordinators = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_consent_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.ON_HOLD
            ]
        )
        
        if available_coordinators.exists():
            return available_coordinators.first()
        
        # If no available coordinators, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, coordinator: User, notes: str = None):
        """Complete the workflow and grant consent."""
        self.consent_granted_at = timezone.now()
        
        # Send completion notifications
        self._send_completion_notifications(coordinator, notes)
    
    def _send_completion_notifications(self, coordinator: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify privacy officer
            privacy_officers = User.objects.filter(
                user_type='PRIVACY_OFFICER',
                is_active=True
            )
            for officer in privacy_officers[:2]:
                self._send_email_notification(
                    template_name='patient_consent_completed_privacy',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'notes': notes,
                    }
                )
            
            # Notify compliance officer
            compliance_officers = User.objects.filter(
                user_type='COMPLIANCE_OFFICER',
                is_active=True
            )
            for officer in compliance_officers[:2]:
                self._send_email_notification(
                    template_name='patient_consent_completed_compliance',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'consent_expiry': self.consent_expires_at,
                    }
                )
            
            # Notify patient (if contact information available)
            if hasattr(self.patient, 'email') and self.patient.email:
                self._send_email_notification(
                    template_name='patient_consent_completed_patient',
                    recipient=self.patient,
                    context={
                        'workflow': self,
                        'consent_expiry': self.consent_expires_at,
                    }
                )
            
            logger.info(f"Completion notifications sent for patient consent workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for patient consent workflow {self.id}: {e}")
    
    def reject_workflow(self, coordinator: User, reason: str, legal_concerns: str = None):
        """Reject the consent workflow."""
        self.status = self.Status.REJECTED
        
        # Add to consent history
        self.consent_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'rejected',
            'legal_concerns': legal_concerns or ''
        })
        
        # Send rejection notifications
        self._send_rejection_notifications(coordinator, reason, legal_concerns)
        
        self.save()
    
    def _send_rejection_notifications(self, coordinator: User, reason: str, legal_concerns: str = None):
        """Send notifications when consent workflow is rejected."""
        try:
            # Notify privacy officer
            privacy_officers = User.objects.filter(
                user_type='PRIVACY_OFFICER',
                is_active=True
            )
            for officer in privacy_officers[:2]:
                self._send_email_notification(
                    template_name='patient_consent_rejected_privacy',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'reason': reason,
                        'legal_concerns': legal_concerns,
                    }
                )
            
            logger.info(f"Rejection notifications sent for patient consent workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send rejection notifications for patient consent workflow {self.id}: {e}")
    
    def put_on_hold(self, coordinator: User, reason: str):
        """Put workflow on hold."""
        self.status = self.Status.ON_HOLD
        
        # Add to consent history
        self.consent_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'on_hold'
        })
        
        self.save()
    
    def resume_workflow(self, coordinator: User):
        """Resume workflow from hold status."""
        self.status = self.Status.IN_PROGRESS
        
        # Add to consent history
        self.consent_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': 'Workflow resumed',
            'action': 'resumed'
        })
        
        self.save()
    
    def revoke_consent(self, coordinator: User, reason: str):
        """Revoke patient consent."""
        self.status = self.Status.REVOKED
        self.consent_revoked_at = timezone.now()
        
        # Add to consent history
        self.consent_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'revoked'
        })
        
        # Send revocation notifications
        self._send_revocation_notifications(coordinator, reason)
        
        self.save()
    
    def _send_revocation_notifications(self, coordinator: User, reason: str):
        """Send notifications when consent is revoked."""
        try:
            # Notify privacy officer
            privacy_officers = User.objects.filter(
                user_type='PRIVACY_OFFICER',
                is_active=True
            )
            for officer in privacy_officers[:2]:
                self._send_email_notification(
                    template_name='patient_consent_revoked_privacy',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'reason': reason,
                    }
                )
            
            # Notify compliance officer
            compliance_officers = User.objects.filter(
                user_type='COMPLIANCE_OFFICER',
                is_active=True
            )
            for officer in compliance_officers[:2]:
                self._send_email_notification(
                    template_name='patient_consent_revoked_compliance',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'reason': reason,
                    }
                )
            
            logger.info(f"Revocation notifications sent for patient consent workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send revocation notifications for patient consent workflow {self.id}: {e}")
    
    def update_guardian_information(self, guardian_info: Dict[str, Any]):
        """Update guardian information for minor consent."""
        self.guardian_information = guardian_info
        self.guardian_consent_required = True
        
        # Add to consent history
        self.consent_history.append({
            'stage': self.current_stage,
            'timestamp': timezone.now().isoformat(),
            'action': 'guardian_info_updated',
            'guardian_info': guardian_info
        })
        
        self.save()
    
    def send_renewal_reminder(self, coordinator: User):
        """Send renewal reminder for expiring consent."""
        try:
            # Notify patient
            if hasattr(self.patient, 'email') and self.patient.email:
                self._send_email_notification(
                    template_name='patient_consent_renewal_reminder',
                    recipient=self.patient,
                    context={
                        'workflow': self,
                        'consent_expiry': self.consent_expires_at,
                    }
                )
            
            # Notify coordinator
            self._send_email_notification(
                template_name='patient_consent_renewal_coordinator',
                recipient=coordinator,
                context={
                    'workflow': self,
                    'patient': self.patient,
                    'consent_expiry': self.consent_expires_at,
                }
            )
            
            self.renewal_reminder_sent = True
            self.save()
            
            logger.info(f"Renewal reminder sent for patient consent workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send renewal reminder for patient consent workflow {self.id}: {e}")
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.COMPLETED, self.Status.APPROVED, self.Status.REJECTED, self.Status.CANCELLED, self.Status.REVOKED]
    
    @property
    def is_on_hold(self) -> bool:
        """Check if workflow is on hold."""
        return self.status == self.Status.ON_HOLD
    
    @property
    def is_expired(self) -> bool:
        """Check if consent is expired."""
        return self.consent_expires_at and timezone.now() > self.consent_expires_at
    
    @property
    def is_revoked(self) -> bool:
        """Check if consent is revoked."""
        return self.status == self.Status.REVOKED
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len(self.STAGES)
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def overall_compliance_score(self) -> Optional[int]:
        """Calculate overall compliance assessment score."""
        scores = []
        if self.patient_verification_score:
            scores.append(self.patient_verification_score)
        if self.legal_compliance_score:
            scores.append(self.legal_compliance_score)
        if self.patient_understanding_score:
            scores.append(self.patient_understanding_score)
        
        return sum(scores) // len(scores) if scores else None
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until consent expires."""
        if not self.consent_expires_at:
            return None
        
        remaining = self.consent_expires_at - timezone.now()
        return max(0, remaining.days) if remaining > timedelta(0) else 0
    
    @property
    def requires_renewal_reminder(self) -> bool:
        """Check if renewal reminder should be sent."""
        if not self.consent_expires_at or self.renewal_reminder_sent:
            return False
        
        days_until_expiry = self.days_until_expiry
        return days_until_expiry is not None and days_until_expiry <= 30
    
    @property
    def is_emergency_consent(self) -> bool:
        """Check if this is an emergency consent."""
        return self.consent_type == self.ConsentType.EMERGENCY
    
    @property
    def is_minor_consent(self) -> bool:
        """Check if this is a minor consent requiring guardian."""
        return self.consent_type in [self.ConsentType.MINOR, self.ConsentType.GUARDIAN]
    
    @property
    def is_research_consent(self) -> bool:
        """Check if this is a research consent."""
        return self.consent_type == self.ConsentType.RESEARCH
    
    @property
    def consent_duration_days(self) -> Optional[int]:
        """Get consent duration in days."""
        if self.consent_duration:
            return self.consent_duration.days
        return None


class EmergencyAccessWorkflow(Workflow):
    """
    Urgent medical data access workflow for emergency scenarios.
    
    This workflow provides expedited access to patient health information
    in emergency situations while maintaining security and audit trails.
    """
    
    # Workflow stages
    STAGES = {
        'emergency_declaration': {
            'name': _('Emergency Declaration'),
            'description': _('Declaration of emergency situation and initial assessment'),
            'required_role': 'EMERGENCY_COORDINATOR',
            'estimated_duration': timedelta(minutes=15),
            'email_template': 'emergency_access_declaration',
        },
        'identity_verification': {
            'name': _('Identity Verification'),
            'description': _('Rapid verification of requesting healthcare provider identity'),
            'required_role': 'SECURITY_OFFICER',
            'estimated_duration': timedelta(minutes=10),
            'email_template': 'emergency_access_identity_verification',
        },
        'emergency_justification': {
            'name': _('Emergency Justification'),
            'description': _('Documentation of emergency situation and medical necessity'),
            'required_role': 'SENIOR_DOCTOR',
            'estimated_duration': timedelta(minutes=20),
            'email_template': 'emergency_access_justification',
        },
        'access_grant': {
            'name': _('Access Grant'),
            'description': _('Immediate grant of emergency access to patient data'),
            'required_role': 'EMERGENCY_COORDINATOR',
            'estimated_duration': timedelta(minutes=5),
            'email_template': 'emergency_access_grant',
        },
        'post_emergency_review': {
            'name': _('Post-Emergency Review'),
            'description': _('Review of emergency access after situation is resolved'),
            'required_role': 'COMPLIANCE_OFFICER',
            'estimated_duration': timedelta(hours=24),
            'email_template': 'emergency_access_post_review',
        },
    }
    
    # Workflow status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        ACCESS_GRANTED = 'access_granted', _('Access Granted')
        ACCESS_REVOKED = 'access_revoked', _('Access Revoked')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        UNDER_REVIEW = 'under_review', _('Under Review')
    
    # Emergency type choices
    class EmergencyType(models.TextChoices):
        MEDICAL_EMERGENCY = 'medical_emergency', _('Medical Emergency')
        TRAUMA = 'trauma', _('Trauma')
        CARDIAC_ARREST = 'cardiac_arrest', _('Cardiac Arrest')
        RESPIRATORY_FAILURE = 'respiratory_failure', _('Respiratory Failure')
        SEVERE_BLEEDING = 'severe_bleeding', _('Severe Bleeding')
        ALLERGIC_REACTION = 'allergic_reaction', _('Allergic Reaction')
        OVERDOSE = 'overdose', _('Overdose')
        UNCONSCIOUS = 'unconscious', _('Unconscious Patient')
        OTHER = 'other', _('Other Emergency')
    
    # Urgency level choices
    class UrgencyLevel(models.TextChoices):
        CRITICAL = 'critical', _('Critical')
        URGENT = 'urgent', _('Urgent')
        EMERGENCY = 'emergency', _('Emergency')
        IMMEDIATE = 'immediate', _('Immediate')
    
    # Workflow fields
    requesting_provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='emergency_access_requests',
        help_text=_('Healthcare provider requesting emergency access')
    )
    
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='emergency_access_workflows',
        help_text=_('Patient whose data is being accessed')
    )
    
    current_stage = models.CharField(
        max_length=50,
        default='emergency_declaration',
        help_text=_('Current workflow stage')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current workflow status')
    )
    
    assigned_coordinator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_emergency_access_workflows',
        help_text=_('Currently assigned emergency coordinator')
    )
    
    emergency_type = models.CharField(
        max_length=30,
        choices=EmergencyType.choices,
        help_text=_('Type of emergency situation')
    )
    
    urgency_level = models.CharField(
        max_length=20,
        choices=UrgencyLevel.choices,
        default=UrgencyLevel.URGENT,
        help_text=_('Urgency level of the emergency')
    )
    
    emergency_description = models.TextField(
        help_text=_('Detailed description of the emergency situation')
    )
    
    medical_necessity = models.TextField(
        help_text=_('Medical necessity for accessing patient data')
    )
    
    requested_data_types = models.JSONField(
        default=list,
        help_text=_('Types of patient data needed for emergency')
    )
    
    emergency_location = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Location where emergency is occurring')
    )
    
    emergency_contact = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Emergency contact information')
    )
    
    review_notes = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Review notes for each stage')
    )
    
    access_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete emergency access history')
    )
    
    security_verification_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Security verification score (1-100)')
    )
    
    medical_necessity_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Medical necessity assessment score (1-100)')
    )
    
    emergency_justification_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Emergency justification score (1-100)')
    )
    
    identity_verified = models.BooleanField(
        default=False,
        help_text=_('Whether requesting provider identity has been verified')
    )
    
    medical_necessity_confirmed = models.BooleanField(
        default=False,
        help_text=_('Whether medical necessity has been confirmed')
    )
    
    access_scope = models.CharField(
        max_length=50,
        choices=[
            ('limited', _('Limited')),
            ('standard', _('Standard')),
            ('comprehensive', _('Comprehensive')),
            ('full', _('Full Access')),
        ],
        default='standard',
        help_text=_('Scope of emergency access granted')
    )
    
    access_duration = models.DurationField(
        default=timedelta(hours=24),
        help_text=_('Duration of emergency access')
    )
    
    estimated_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Estimated completion time')
    )
    
    actual_completion = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Actual completion time')
    )
    
    access_granted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When emergency access was granted')
    )
    
    access_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When emergency access expires')
    )
    
    access_revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When emergency access was revoked')
    )
    
    emergency_resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When emergency situation was resolved')
    )
    
    post_emergency_notes = models.TextField(
        blank=True,
        help_text=_('Notes from post-emergency review')
    )
    
    compliance_issues = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Any compliance issues identified during review')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Emergency Access Workflow')
        verbose_name_plural = _('Emergency Access Workflows')
        db_table = 'healthcare_emergency_access_workflows'
        indexes = [
            models.Index(fields=['status', 'current_stage']),
            models.Index(fields=['assigned_coordinator', 'status']),
            models.Index(fields=['urgency_level', 'created_at']),
            models.Index(fields=['estimated_completion']),
            models.Index(fields=['emergency_type', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['requesting_provider', 'status']),
            models.Index(fields=['access_expires_at']),
            models.Index(fields=['access_granted_at']),
            models.Index(fields=['emergency_resolved_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Emergency access for {self.patient} - {self.emergency_type}"
    
    def save(self, *args, **kwargs):
        """Override save to handle workflow logic and notifications."""
        is_new = self.pk is None
        
        if is_new:
            self.started_at = timezone.now()
            self._calculate_estimated_completion()
            self._calculate_access_expiry()
        
        super().save(*args, **kwargs)
        
        if is_new:
            self._send_initial_notifications()
        else:
            self._send_stage_notifications()
    
    def _calculate_estimated_completion(self):
        """Calculate estimated completion time based on urgency and stages."""
        base_duration = timedelta(hours=1)  # Base duration for urgent cases
        
        if self.urgency_level == self.UrgencyLevel.CRITICAL:
            base_duration = timedelta(minutes=30)
        elif self.urgency_level == self.UrgencyLevel.IMMEDIATE:
            base_duration = timedelta(minutes=15)
        
        # Add time for each required stage
        total_duration = timedelta()
        for stage_key, stage_config in self.STAGES.items():
            if not stage_config.get('optional', False):
                total_duration += stage_config['estimated_duration']
        
        self.estimated_completion = timezone.now() + total_duration
    
    def _calculate_access_expiry(self):
        """Calculate access expiry date based on duration."""
        if self.access_duration:
            self.access_expires_at = timezone.now() + self.access_duration
    
    def _send_initial_notifications(self):
        """Send initial notifications when workflow is created."""
        try:
            # Notify emergency coordinator
            if self.assigned_coordinator:
                self._send_email_notification(
                    template_name='emergency_access_assigned',
                    recipient=self.assigned_coordinator,
                    context={
                        'workflow': self,
                        'stage': self.STAGES[self.current_stage],
                    }
                )
            
            # Notify security officer
            security_officers = User.objects.filter(
                user_type='SECURITY_OFFICER',
                is_active=True
            )
            for officer in security_officers[:2]:  # Notify up to 2 officers
                self._send_email_notification(
                    template_name='emergency_access_security_notified',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_provider': self.requesting_provider,
                    }
                )
            
            # Notify senior doctor
            senior_doctors = User.objects.filter(
                user_type='SENIOR_DOCTOR',
                is_active=True
            )
            for doctor in senior_doctors[:2]:
                self._send_email_notification(
                    template_name='emergency_access_doctor_notified',
                    recipient=doctor,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'emergency_type': self.emergency_type,
                    }
                )
            
            # Notify compliance officer
            compliance_officers = User.objects.filter(
                user_type='COMPLIANCE_OFFICER',
                is_active=True
            )
            for officer in compliance_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_compliance_notified',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_provider': self.requesting_provider,
                    }
                )
            
            logger.info(f"Initial notifications sent for emergency access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send initial notifications for emergency access workflow {self.id}: {e}")
    
    def _send_stage_notifications(self):
        """Send notifications for stage changes."""
        try:
            stage_config = self.STAGES.get(self.current_stage)
            if not stage_config:
                return
            
            # Notify assigned coordinator
            if self.assigned_coordinator:
                self._send_email_notification(
                    template_name=stage_config['email_template'],
                    recipient=self.assigned_coordinator,
                    context={
                        'workflow': self,
                        'stage': stage_config,
                    }
                )
            
            logger.info(f"Stage notifications sent for emergency access workflow {self.id}, stage {self.current_stage}")
            
        except Exception as e:
            logger.error(f"Failed to send stage notifications for emergency access workflow {self.id}: {e}")
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    def advance_to_next_stage(self, coordinator: User, notes: str = None, scores: Dict[str, int] = None):
        """Advance workflow to the next stage with optional scores."""
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        next_stage_index = current_stage_index + 1
        
        # Update scores if provided
        if scores:
            self._update_scores(scores)
        
        if next_stage_index >= len(self.STAGES):
            # Workflow completed
            self.status = self.Status.COMPLETED
            self.actual_completion = timezone.now()
            self._complete_workflow(coordinator, notes)
        else:
            # Move to next stage
            next_stage = list(self.STAGES.keys())[next_stage_index]
            self.current_stage = next_stage
            self.assigned_coordinator = self._get_next_coordinator(next_stage)
            
            # Add to access history
            self.access_history.append({
                'stage': self.current_stage,
                'coordinator': coordinator.id,
                'timestamp': timezone.now().isoformat(),
                'notes': notes or '',
                'action': 'advanced',
                'scores': scores or {}
            })
        
        self.save()
    
    def _update_scores(self, scores: Dict[str, int]):
        """Update assessment scores based on review."""
        if 'security_verification' in scores:
            self.security_verification_score = scores['security_verification']
        if 'medical_necessity' in scores:
            self.medical_necessity_score = scores['medical_necessity']
        if 'emergency_justification' in scores:
            self.emergency_justification_score = scores['emergency_justification']
    
    def _get_next_coordinator(self, stage: str) -> Optional[User]:
        """Get the next coordinator for the given stage."""
        stage_config = self.STAGES.get(stage)
        if not stage_config:
            return None
        
        required_role = stage_config['required_role']
        
        # Find available users with the required role
        available_coordinators = User.objects.filter(
            user_type=required_role,
            is_active=True
        ).exclude(
            assigned_emergency_access_workflows__status__in=[
                self.Status.IN_PROGRESS,
                self.Status.UNDER_REVIEW
            ]
        )
        
        if available_coordinators.exists():
            return available_coordinators.first()
        
        # If no available coordinators, return None (will be assigned manually)
        return None
    
    def _complete_workflow(self, coordinator: User, notes: str = None):
        """Complete the workflow and grant access."""
        self.access_granted_at = timezone.now()
        
        # Send completion notifications
        self._send_completion_notifications(coordinator, notes)
    
    def _send_completion_notifications(self, coordinator: User, notes: str = None):
        """Send notifications when workflow is completed."""
        try:
            # Notify security officer
            security_officers = User.objects.filter(
                user_type='SECURITY_OFFICER',
                is_active=True
            )
            for officer in security_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_completed_security',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'notes': notes,
                    }
                )
            
            # Notify compliance officer
            compliance_officers = User.objects.filter(
                user_type='COMPLIANCE_OFFICER',
                is_active=True
            )
            for officer in compliance_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_completed_compliance',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'access_expiry': self.access_expires_at,
                    }
                )
            
            # Notify requesting provider
            self._send_email_notification(
                template_name='emergency_access_completed_provider',
                recipient=self.requesting_provider,
                context={
                    'workflow': self,
                    'access_expiry': self.access_expires_at,
                }
            )
            
            logger.info(f"Completion notifications sent for emergency access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send completion notifications for emergency access workflow {self.id}: {e}")
    
    def grant_emergency_access(self, coordinator: User, access_scope: str = None, duration: timedelta = None):
        """Grant emergency access immediately."""
        self.status = self.Status.ACCESS_GRANTED
        self.access_granted_at = timezone.now()
        
        if access_scope:
            self.access_scope = access_scope
        
        if duration:
            self.access_duration = duration
            self._calculate_access_expiry()
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'action': 'access_granted',
            'access_scope': self.access_scope,
            'access_duration': str(self.access_duration),
        })
        
        # Send access granted notifications
        self._send_access_granted_notifications(coordinator)
        
        self.save()
    
    def _send_access_granted_notifications(self, coordinator: User):
        """Send notifications when emergency access is granted."""
        try:
            # Notify requesting provider
            self._send_email_notification(
                template_name='emergency_access_granted_provider',
                recipient=self.requesting_provider,
                context={
                    'workflow': self,
                    'access_expiry': self.access_expires_at,
                    'access_scope': self.access_scope,
                }
            )
            
            # Notify security officer
            security_officers = User.objects.filter(
                user_type='SECURITY_OFFICER',
                is_active=True
            )
            for officer in security_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_granted_security',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_provider': self.requesting_provider,
                        'access_expiry': self.access_expires_at,
                    }
                )
            
            logger.info(f"Access granted notifications sent for emergency access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send access granted notifications for emergency access workflow {self.id}: {e}")
    
    def revoke_emergency_access(self, coordinator: User, reason: str):
        """Revoke emergency access."""
        self.status = self.Status.ACCESS_REVOKED
        self.access_revoked_at = timezone.now()
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'access_revoked'
        })
        
        # Send revocation notifications
        self._send_revocation_notifications(coordinator, reason)
        
        self.save()
    
    def _send_revocation_notifications(self, coordinator: User, reason: str):
        """Send notifications when emergency access is revoked."""
        try:
            # Notify requesting provider
            self._send_email_notification(
                template_name='emergency_access_revoked_provider',
                recipient=self.requesting_provider,
                context={
                    'workflow': self,
                    'reason': reason,
                }
            )
            
            # Notify security officer
            security_officers = User.objects.filter(
                user_type='SECURITY_OFFICER',
                is_active=True
            )
            for officer in security_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_revoked_security',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_provider': self.requesting_provider,
                        'reason': reason,
                    }
                )
            
            logger.info(f"Revocation notifications sent for emergency access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send revocation notifications for emergency access workflow {self.id}: {e}")
    
    def resolve_emergency(self, coordinator: User, resolution_notes: str = None):
        """Mark emergency as resolved."""
        self.emergency_resolved_at = timezone.now()
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': resolution_notes or 'Emergency resolved',
            'action': 'emergency_resolved'
        })
        
        self.save()
    
    def start_post_emergency_review(self, coordinator: User):
        """Start post-emergency review process."""
        self.status = self.Status.UNDER_REVIEW
        self.current_stage = 'post_emergency_review'
        self.assigned_coordinator = coordinator
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'action': 'post_emergency_review_started'
        })
        
        self.save()
    
    def complete_post_emergency_review(self, coordinator: User, review_notes: str, compliance_issues: List[str] = None):
        """Complete post-emergency review."""
        self.status = self.Status.COMPLETED
        self.actual_completion = timezone.now()
        self.post_emergency_notes = review_notes
        
        if compliance_issues:
            self.compliance_issues = compliance_issues
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': review_notes,
            'action': 'post_emergency_review_completed',
            'compliance_issues': compliance_issues or []
        })
        
        # Send review completion notifications
        self._send_review_completion_notifications(coordinator, review_notes, compliance_issues)
        
        self.save()
    
    def _send_review_completion_notifications(self, coordinator: User, review_notes: str, compliance_issues: List[str] = None):
        """Send notifications when post-emergency review is completed."""
        try:
            # Notify compliance officer
            compliance_officers = User.objects.filter(
                user_type='COMPLIANCE_OFFICER',
                is_active=True
            )
            for officer in compliance_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_review_completed_compliance',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'review_notes': review_notes,
                        'compliance_issues': compliance_issues or [],
                    }
                )
            
            # Notify security officer
            security_officers = User.objects.filter(
                user_type='SECURITY_OFFICER',
                is_active=True
            )
            for officer in security_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_review_completed_security',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'coordinator': coordinator,
                        'review_notes': review_notes,
                        'compliance_issues': compliance_issues or [],
                    }
                )
            
            logger.info(f"Review completion notifications sent for emergency access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send review completion notifications for emergency access workflow {self.id}: {e}")
    
    def cancel_workflow(self, coordinator: User, reason: str):
        """Cancel the emergency access workflow."""
        self.status = self.Status.CANCELLED
        
        # Add to access history
        self.access_history.append({
            'stage': self.current_stage,
            'coordinator': coordinator.id,
            'timestamp': timezone.now().isoformat(),
            'notes': reason,
            'action': 'cancelled'
        })
        
        # Send cancellation notifications
        self._send_cancellation_notifications(coordinator, reason)
        
        self.save()
    
    def _send_cancellation_notifications(self, coordinator: User, reason: str):
        """Send notifications when emergency access workflow is cancelled."""
        try:
            # Notify requesting provider
            self._send_email_notification(
                template_name='emergency_access_cancelled_provider',
                recipient=self.requesting_provider,
                context={
                    'workflow': self,
                    'reason': reason,
                }
            )
            
            # Notify security officer
            security_officers = User.objects.filter(
                user_type='SECURITY_OFFICER',
                is_active=True
            )
            for officer in security_officers[:2]:
                self._send_email_notification(
                    template_name='emergency_access_cancelled_security',
                    recipient=officer,
                    context={
                        'workflow': self,
                        'patient': self.patient,
                        'requesting_provider': self.requesting_provider,
                        'reason': reason,
                    }
                )
            
            logger.info(f"Cancellation notifications sent for emergency access workflow {self.id}")
            
        except Exception as e:
            logger.error(f"Failed to send cancellation notifications for emergency access workflow {self.id}: {e}")
    
    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed."""
        return self.status in [self.Status.COMPLETED, self.Status.ACCESS_REVOKED, self.Status.CANCELLED]
    
    @property
    def is_access_active(self) -> bool:
        """Check if emergency access is currently active."""
        return (
            self.status == self.Status.ACCESS_GRANTED and
            self.access_expires_at and
            timezone.now() < self.access_expires_at
        )
    
    @property
    def is_access_expired(self) -> bool:
        """Check if emergency access has expired."""
        return (
            self.access_expires_at and
            timezone.now() > self.access_expires_at
        )
    
    @property
    def current_stage_config(self) -> Dict[str, Any]:
        """Get current stage configuration."""
        return self.STAGES.get(self.current_stage, {})
    
    @property
    def progress_percentage(self) -> int:
        """Calculate workflow progress percentage."""
        total_stages = len(self.STAGES)
        current_stage_index = list(self.STAGES.keys()).index(self.current_stage)
        return min(100, int((current_stage_index / total_stages) * 100))
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """Calculate estimated remaining time."""
        if not self.estimated_completion:
            return None
        
        remaining = self.estimated_completion - timezone.now()
        return remaining if remaining > timedelta(0) else timedelta(0)
    
    @property
    def overall_assessment_score(self) -> Optional[int]:
        """Calculate overall emergency assessment score."""
        scores = []
        if self.security_verification_score:
            scores.append(self.security_verification_score)
        if self.medical_necessity_score:
            scores.append(self.medical_necessity_score)
        if self.emergency_justification_score:
            scores.append(self.emergency_justification_score)
        
        return sum(scores) // len(scores) if scores else None
    
    @property
    def minutes_until_access_expiry(self) -> Optional[int]:
        """Calculate minutes until access expires."""
        if not self.access_expires_at:
            return None
        
        remaining = self.access_expires_at - timezone.now()
        return max(0, int(remaining.total_seconds() / 60)) if remaining > timedelta(0) else 0
    
    @property
    def is_critical_emergency(self) -> bool:
        """Check if this is a critical emergency."""
        return self.urgency_level in [self.UrgencyLevel.CRITICAL, self.UrgencyLevel.IMMEDIATE]
    
    @property
    def is_medical_emergency(self) -> bool:
        """Check if this is a medical emergency."""
        return self.emergency_type == self.EmergencyType.MEDICAL_EMERGENCY
    
    @property
    def is_trauma_emergency(self) -> bool:
        """Check if this is a trauma emergency."""
        return self.emergency_type == self.EmergencyType.TRAUMA
    
    @property
    def is_cardiac_emergency(self) -> bool:
        """Check if this is a cardiac emergency."""
        return self.emergency_type == self.EmergencyType.CARDIAC_ARREST
    
    @property
    def requires_immediate_attention(self) -> bool:
        """Check if this requires immediate attention."""
        return (
            self.urgency_level in [self.UrgencyLevel.CRITICAL, self.UrgencyLevel.IMMEDIATE] or
            self.emergency_type in [
                self.EmergencyType.CARDIAC_ARREST,
                self.EmergencyType.RESPIRATORY_FAILURE,
                self.EmergencyType.SEVERE_BLEEDING,
                self.EmergencyType.ALLERGIC_REACTION,
                self.EmergencyType.OVERDOSE,
                self.EmergencyType.UNCONSCIOUS
            ]
        )
    
    @property
    def emergency_duration_minutes(self) -> Optional[int]:
        """Calculate emergency duration in minutes."""
        if not self.emergency_resolved_at or not self.created_at:
            return None
        
        duration = self.emergency_resolved_at - self.created_at
        return int(duration.total_seconds() / 60)
    
    @property
    def access_duration_hours(self) -> Optional[int]:
        """Get access duration in hours."""
        if self.access_duration:
            return int(self.access_duration.total_seconds() / 3600)
        return None