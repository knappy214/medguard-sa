"""
Healthcare workflow tasks for MedGuard SA using Wagtail 7.0.2.

This module contains specialized task implementations for healthcare
processes with enhanced task management, due dates, and priorities.
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


class PrescriptionVerificationTask(WorkflowTask):
    """
    Custom task type for prescription verification using Wagtail 7.0.2's task system.
    
    This task handles the verification of prescription details including
    dosage, frequency, interactions, and clinical appropriateness.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
    
    # Verification type choices
    class VerificationType(models.TextChoices):
        DOSAGE_VERIFICATION = 'dosage_verification', _('Dosage Verification')
        INTERACTION_CHECK = 'interaction_check', _('Drug Interaction Check')
        CLINICAL_APPROPRIATENESS = 'clinical_appropriateness', _('Clinical Appropriateness')
        ALLERGY_VERIFICATION = 'allergy_verification', _('Allergy Verification')
        CONTRAINDICATION_CHECK = 'contraindication_check', _('Contraindication Check')
        COMPREHENSIVE_REVIEW = 'comprehensive_review', _('Comprehensive Review')
    
    # Task fields
    prescription = models.ForeignKey(
        'medications.EnhancedPrescription',
        on_delete=models.CASCADE,
        related_name='verification_tasks',
        help_text=_('Associated prescription for verification')
    )
    
    verification_type = models.CharField(
        max_length=50,
        choices=VerificationType.choices,
        help_text=_('Type of verification to perform')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_verifier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_verification_tasks',
        help_text=_('Healthcare professional assigned to verification')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='normal',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=2),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    verification_notes = models.TextField(
        blank=True,
        help_text=_('Notes from verification process')
    )
    
    verification_result = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Detailed verification results')
    )
    
    verification_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Verification confidence score (1-100)')
    )
    
    issues_found = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Issues identified during verification')
    )
    
    recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Recommendations based on verification')
    )
    
    requires_escalation = models.BooleanField(
        default=False,
        help_text=_('Whether task requires escalation')
    )
    
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_verification_tasks',
        help_text=_('User escalated to if needed')
    )
    
    escalation_reason = models.TextField(
        blank=True,
        help_text=_('Reason for escalation if applicable')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Prescription Verification Task')
        verbose_name_plural = _('Prescription Verification Tasks')
        db_table = 'healthcare_prescription_verification_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_verifier', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['verification_type', 'status']),
            models.Index(fields=['prescription', 'status']),
            models.Index(fields=['requires_escalation']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Verification Task: {self.verification_type} - {self.prescription}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign verifier if not assigned
        if not self.assigned_verifier:
            self.assigned_verifier = self._get_available_verifier()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_verifier(self) -> Optional[User]:
        """Get an available healthcare professional for verification."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_verifier:
            self._send_assignment_notification()
        elif self.status == self.Status.COMPLETED:
            self._send_completion_notification()
        elif self.status == self.Status.FAILED:
            self._send_failure_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned verifier."""
        context = {
            'task': self,
            'prescription': self.prescription,
            'due_date': self.due_date,
        }
        self._send_email_notification('verification_task_assigned', self.assigned_verifier, context)
    
    def _send_completion_notification(self):
        """Send notification about task completion."""
        context = {
            'task': self,
            'prescription': self.prescription,
            'result': self.verification_result,
        }
        # Send to relevant stakeholders
        self._send_email_notification('verification_task_completed', self.assigned_verifier, context)
    
    def _send_failure_notification(self):
        """Send notification about task failure."""
        context = {
            'task': self,
            'prescription': self.prescription,
            'issues': self.issues_found,
        }
        self._send_email_notification('verification_task_failed', self.assigned_verifier, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_verification(self, verifier: User = None):
        """Start the verification process."""
        if verifier:
            self.assigned_verifier = verifier
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def complete_verification(self, result: Dict[str, Any], notes: str = None, score: int = None):
        """Complete the verification task."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.verification_result = result
        self.verification_notes = notes or ""
        self.verification_score = score
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def fail_verification(self, issues: List[str], notes: str = None):
        """Mark verification as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.issues_found = issues
        self.verification_notes = notes or ""
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def escalate_task(self, escalated_to: User, reason: str):
        """Escalate task to another user."""
        self.requires_escalation = True
        self.escalated_to = escalated_to
        self.escalation_reason = reason
        self.save()
        
        # Send escalation notification
        context = {
            'task': self,
            'reason': reason,
            'original_verifier': self.assigned_verifier,
        }
        self._send_email_notification('verification_task_escalated', escalated_to, context)
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.verification_notes = f"On hold: {reason}\n\n{self.verification_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_critical_priority(self) -> bool:
        """Check if task is critical priority."""
        return self.priority == 'critical'
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.COMPLETED:
            return 100
        elif self.status == self.Status.FAILED:
            return 0


class PrescriptionRenewalReminderTask(WorkflowTask):
    """
    Prescription renewal reminder task with patient notification integration.
    
    This task handles automated prescription renewal reminders with
    patient notification integration and healthcare provider coordination.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        PATIENT_NOTIFIED = 'patient_notified', _('Patient Notified')
        PROVIDER_NOTIFIED = 'provider_notified', _('Provider Notified')
    
    # Reminder type choices
    class ReminderType(models.TextChoices):
        FIRST_REMINDER = 'first_reminder', _('First Reminder')
        SECOND_REMINDER = 'second_reminder', _('Second Reminder')
        FINAL_REMINDER = 'final_reminder', _('Final Reminder')
        URGENT_REMINDER = 'urgent_reminder', _('Urgent Reminder')
        EXPIRY_WARNING = 'expiry_warning', _('Expiry Warning')
    
    # Task fields
    prescription = models.ForeignKey(
        'medications.EnhancedPrescription',
        on_delete=models.CASCADE,
        related_name='renewal_reminder_tasks',
        help_text=_('Associated prescription for renewal reminder')
    )
    
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='renewal_reminder_tasks',
        help_text=_('Patient receiving renewal reminder')
    )
    
    reminder_type = models.CharField(
        max_length=30,
        choices=ReminderType.choices,
        help_text=_('Type of renewal reminder')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_coordinator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_renewal_reminder_tasks',
        help_text=_('Healthcare coordinator assigned to reminder')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='normal',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=1),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    prescription_expiry_date = models.DateTimeField(
        help_text=_('Date when prescription expires')
    )
    
    reminder_notes = models.TextField(
        blank=True,
        help_text=_('Notes about the renewal reminder')
    )
    
    patient_notification_sent = models.BooleanField(
        default=False,
        help_text=_('Whether patient notification was sent')
    )
    
    patient_notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When patient notification was sent')
    )
    
    patient_response_received = models.BooleanField(
        default=False,
        help_text=_('Whether patient response was received')
    )
    
    patient_response = models.TextField(
        blank=True,
        help_text=_('Patient response to renewal reminder')
    )
    
    provider_notification_sent = models.BooleanField(
        default=False,
        help_text=_('Whether provider notification was sent')
    )
    
    provider_notification_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When provider notification was sent')
    )
    
    renewal_requested = models.BooleanField(
        default=False,
        help_text=_('Whether renewal was requested')
    )
    
    renewal_approved = models.BooleanField(
        default=False,
        help_text=_('Whether renewal was approved')
    )
    
    notification_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('History of notifications sent')
    )
    
    patient_preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Patient notification preferences')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Prescription Renewal Reminder Task')
        verbose_name_plural = _('Prescription Renewal Reminder Tasks')
        db_table = 'healthcare_prescription_renewal_reminder_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_coordinator', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['reminder_type', 'status']),
            models.Index(fields=['prescription', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['prescription_expiry_date']),
            models.Index(fields=['patient_notification_sent']),
            models.Index(fields=['provider_notification_sent']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Renewal Reminder: {self.reminder_type} - {self.patient}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign coordinator if not assigned
        if not self.assigned_coordinator:
            self.assigned_coordinator = self._get_available_coordinator()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_coordinator(self) -> Optional[User]:
        """Get an available healthcare coordinator."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_coordinator:
            self._send_assignment_notification()
        elif self.status == self.Status.PATIENT_NOTIFIED:
            self._send_patient_notification()
        elif self.status == self.Status.PROVIDER_NOTIFIED:
            self._send_provider_notification()
        elif self.status == self.Status.COMPLETED:
            self._send_completion_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned coordinator."""
        context = {
            'task': self,
            'patient': self.patient,
            'prescription': self.prescription,
            'due_date': self.due_date,
        }
        self._send_email_notification('renewal_reminder_assigned', self.assigned_coordinator, context)
    
    def _send_patient_notification(self):
        """Send notification to patient."""
        context = {
            'task': self,
            'patient': self.patient,
            'prescription': self.prescription,
            'expiry_date': self.prescription_expiry_date,
        }
        self._send_email_notification('renewal_reminder_patient', self.patient.user, context)
    
    def _send_provider_notification(self):
        """Send notification to healthcare provider."""
        context = {
            'task': self,
            'patient': self.patient,
            'prescription': self.prescription,
            'expiry_date': self.prescription_expiry_date,
        }
        # Send to prescription prescriber
        if self.prescription.prescriber:
            self._send_email_notification('renewal_reminder_provider', self.prescription.prescriber, context)
    
    def _send_completion_notification(self):
        """Send notification about task completion."""
        context = {
            'task': self,
            'patient': self.patient,
            'prescription': self.prescription,
            'renewal_approved': self.renewal_approved,
        }
        self._send_email_notification('renewal_reminder_completed', self.assigned_coordinator, context)
    
    def _send_email_notification(self, template_name: str, recipient: User, context: Dict[str, Any]):
        """Send email notification using notification service."""
        try:
            notification_service = NotificationService()
            notification_service.send_email_notification(
                template_name=template_name,
                recipient=recipient,
                context=context
            )
            
            # Add to notification history
            notification_entry = {
                'timestamp': timezone.now().isoformat(),
                'template': template_name,
                'recipient_id': recipient.id,
                'recipient_name': recipient.get_full_name() or recipient.username,
                'status': 'sent',
            }
            
            if not self.notification_history:
                self.notification_history = []
            
            self.notification_history.append(notification_entry)
            
        except Exception as e:
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_reminder(self, coordinator: User = None):
        """Start the renewal reminder process."""
        if coordinator:
            self.assigned_coordinator = coordinator
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def send_patient_notification(self):
        """Send notification to patient."""
        self.status = self.Status.PATIENT_NOTIFIED
        self.patient_notification_sent = True
        self.patient_notification_sent_at = timezone.now()
        self.save()
    
    def record_patient_response(self, response: str):
        """Record patient response to renewal reminder."""
        self.patient_response_received = True
        self.patient_response = response
        self.save()
    
    def send_provider_notification(self):
        """Send notification to healthcare provider."""
        self.status = self.Status.PROVIDER_NOTIFIED
        self.provider_notification_sent = True
        self.provider_notification_sent_at = timezone.now()
        self.save()
    
    def request_renewal(self):
        """Mark renewal as requested."""
        self.renewal_requested = True
        self.save()
    
    def approve_renewal(self):
        """Mark renewal as approved."""
        self.renewal_approved = True
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def complete_task(self, notes: str = None):
        """Complete the renewal reminder task."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.reminder_notes = notes or ""
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.reminder_notes = f"On hold: {reason}\n\n{self.reminder_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.COMPLETED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_urgent_reminder(self) -> bool:
        """Check if this is an urgent reminder."""
        return self.reminder_type in [self.ReminderType.URGENT_REMINDER, self.ReminderType.EXPIRY_WARNING]
    
    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until prescription expiry."""
        if not self.prescription_expiry_date:
            return None
        delta = self.prescription_expiry_date - timezone.now()
        return delta.days
    
    @property
    def is_expired(self) -> bool:
        """Check if prescription is expired."""
        if not self.prescription_expiry_date:
            return False
        return timezone.now() > self.prescription_expiry_date
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.COMPLETED:
            return 100
        elif self.status == self.Status.PROVIDER_NOTIFIED:
            return 80
        elif self.status == self.Status.PATIENT_NOTIFIED:
            return 60
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0


class MedicationInteractionReviewTask(WorkflowTask):
    """
    Medication interaction review task for clinical safety.
    
    This task handles the review of potential drug interactions
    for clinical safety and patient risk assessment.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        REQUIRES_ESCALATION = 'requires_escalation', _('Requires Escalation')
    
    # Interaction severity choices
    class InteractionSeverity(models.TextChoices):
        MINOR = 'minor', _('Minor')
        MODERATE = 'moderate', _('Moderate')
        MAJOR = 'major', _('Major')
        CONTRAINDICATED = 'contraindicated', _('Contraindicated')
        UNKNOWN = 'unknown', _('Unknown')
    
    # Task fields
    prescription = models.ForeignKey(
        'medications.EnhancedPrescription',
        on_delete=models.CASCADE,
        related_name='interaction_review_tasks',
        help_text=_('Associated prescription for interaction review')
    )
    
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='interaction_review_tasks',
        help_text=_('Patient whose medications are being reviewed')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_interaction_review_tasks',
        help_text=_('Healthcare professional assigned to interaction review')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='normal',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=3),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    medications_reviewed = models.JSONField(
        default=list,
        help_text=_('List of medications reviewed for interactions')
    )
    
    interactions_found = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Drug interactions identified during review')
    )
    
    highest_severity = models.CharField(
        max_length=20,
        choices=InteractionSeverity.choices,
        null=True,
        blank=True,
        help_text=_('Highest severity interaction found')
    )
    
    risk_assessment_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Overall risk assessment score (1-100)')
    )
    
    clinical_recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Clinical recommendations based on interactions')
    )
    
    review_notes = models.TextField(
        blank=True,
        help_text=_('Notes from interaction review process')
    )
    
    requires_immediate_action = models.BooleanField(
        default=False,
        help_text=_('Whether immediate action is required')
    )
    
    action_taken = models.TextField(
        blank=True,
        help_text=_('Action taken based on interaction review')
    )
    
    patient_notified = models.BooleanField(
        default=False,
        help_text=_('Whether patient was notified of interactions')
    )
    
    provider_notified = models.BooleanField(
        default=False,
        help_text=_('Whether healthcare provider was notified')
    )
    
    escalation_required = models.BooleanField(
        default=False,
        help_text=_('Whether escalation is required')
    )
    
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_interaction_review_tasks',
        help_text=_('User escalated to if needed')
    )
    
    escalation_reason = models.TextField(
        blank=True,
        help_text=_('Reason for escalation if applicable')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Medication Interaction Review Task')
        verbose_name_plural = _('Medication Interaction Review Tasks')
        db_table = 'healthcare_medication_interaction_review_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_reviewer', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['prescription', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['highest_severity']),
            models.Index(fields=['requires_immediate_action']),
            models.Index(fields=['escalation_required']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Interaction Review: {self.prescription} - {self.patient}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign reviewer if not assigned
        if not self.assigned_reviewer:
            self.assigned_reviewer = self._get_available_reviewer()
        
        # Update highest severity based on interactions found
        if self.interactions_found:
            self._update_highest_severity()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_reviewer(self) -> Optional[User]:
        """Get an available healthcare professional for interaction review."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _update_highest_severity(self):
        """Update highest severity based on interactions found."""
        severities = [interaction.get('severity') for interaction in self.interactions_found]
        severity_order = {
            self.InteractionSeverity.CONTRAINDICATED: 4,
            self.InteractionSeverity.MAJOR: 3,
            self.InteractionSeverity.MODERATE: 2,
            self.InteractionSeverity.MINOR: 1,
            self.InteractionSeverity.UNKNOWN: 0,
        }
        
        if severities:
            highest = max(severities, key=lambda s: severity_order.get(s, 0))
            self.highest_severity = highest
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_reviewer:
            self._send_assignment_notification()
        elif self.status == self.Status.COMPLETED:
            self._send_completion_notification()
        elif self.status == self.Status.FAILED:
            self._send_failure_notification()
        elif self.status == self.Status.REQUIRES_ESCALATION:
            self._send_escalation_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned reviewer."""
        context = {
            'task': self,
            'prescription': self.prescription,
            'patient': self.patient,
            'due_date': self.due_date,
        }
        self._send_email_notification('interaction_review_assigned', self.assigned_reviewer, context)
    
    def _send_completion_notification(self):
        """Send notification about task completion."""
        context = {
            'task': self,
            'prescription': self.prescription,
            'patient': self.patient,
            'highest_severity': self.highest_severity,
            'risk_score': self.risk_assessment_score,
        }
        self._send_email_notification('interaction_review_completed', self.assigned_reviewer, context)
    
    def _send_failure_notification(self):
        """Send notification about task failure."""
        context = {
            'task': self,
            'prescription': self.prescription,
            'patient': self.patient,
            'review_notes': self.review_notes,
        }
        self._send_email_notification('interaction_review_failed', self.assigned_reviewer, context)
    
    def _send_escalation_notification(self):
        """Send notification about escalation."""
        context = {
            'task': self,
            'prescription': self.prescription,
            'patient': self.patient,
            'escalation_reason': self.escalation_reason,
        }
        if self.escalated_to:
            self._send_email_notification('interaction_review_escalated', self.escalated_to, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_review(self, reviewer: User = None):
        """Start the interaction review process."""
        if reviewer:
            self.assigned_reviewer = reviewer
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def complete_review(self, interactions: List[Dict], recommendations: List[str], 
                       risk_score: int, notes: str = None):
        """Complete the interaction review task."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.interactions_found = interactions
        self.clinical_recommendations = recommendations
        self.risk_assessment_score = risk_score
        self.review_notes = notes or ""
        
        # Update highest severity
        self._update_highest_severity()
        
        # Check if immediate action is required
        if self.highest_severity in [self.InteractionSeverity.MAJOR, self.InteractionSeverity.CONTRAINDICATED]:
            self.requires_immediate_action = True
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def escalate_task(self, escalated_to: User, reason: str):
        """Escalate task to another user."""
        self.status = self.Status.REQUIRES_ESCALATION
        self.escalation_required = True
        self.escalated_to = escalated_to
        self.escalation_reason = reason
        self.save()
    
    def take_action(self, action: str):
        """Record action taken based on interaction review."""
        self.action_taken = action
        self.save()
    
    def notify_patient(self):
        """Mark patient as notified."""
        self.patient_notified = True
        self.save()
    
    def notify_provider(self):
        """Mark provider as notified."""
        self.provider_notified = True
        self.save()
    
    def fail_review(self, reason: str):
        """Mark review as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.review_notes = reason
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.review_notes = f"On hold: {reason}\n\n{self.review_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_critical_interaction(self) -> bool:
        """Check if this involves critical interactions."""
        return self.highest_severity in [self.InteractionSeverity.MAJOR, self.InteractionSeverity.CONTRAINDICATED]
    
    @property
    def interaction_count(self) -> int:
        """Get count of interactions found."""
        return len(self.interactions_found) if self.interactions_found else 0
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.COMPLETED:
            return 100
        elif self.status == self.Status.FAILED:
            return 0
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0


class PharmacyIntegrationVerificationTask(WorkflowTask):
    """
    Pharmacy integration verification task with external system checks.
    
    This task handles the verification of pharmacy system integrations
    and external system connectivity for medication dispensing.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        SYSTEM_ERROR = 'system_error', _('System Error')
    
    # Integration type choices
    class IntegrationType(models.TextChoices):
        INVENTORY_SYSTEM = 'inventory_system', _('Inventory System')
        DISPENSING_SYSTEM = 'dispensing_system', _('Dispensing System')
        BILLING_SYSTEM = 'billing_system', _('Billing System')
        PATIENT_MANAGEMENT = 'patient_management', _('Patient Management')
        PRESCRIPTION_SYSTEM = 'prescription_system', _('Prescription System')
        COMPREHENSIVE = 'comprehensive', _('Comprehensive Integration')
    
    # Task fields
    pharmacy = models.ForeignKey(
        'medications.Pharmacy',
        on_delete=models.CASCADE,
        related_name='integration_verification_tasks',
        help_text=_('Associated pharmacy for integration verification')
    )
    
    integration_type = models.CharField(
        max_length=50,
        choices=IntegrationType.choices,
        help_text=_('Type of integration to verify')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_pharmacy_integration_tasks',
        help_text=_('IT technician assigned to integration verification')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='normal',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=4),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    external_system_url = models.URLField(
        blank=True,
        help_text=_('URL of external system to verify')
    )
    
    api_endpoints_tested = models.JSONField(
        default=list,
        blank=True,
        help_text=_('API endpoints tested during verification')
    )
    
    connectivity_status = models.CharField(
        max_length=20,
        choices=[
            ('connected', _('Connected')),
            ('disconnected', _('Disconnected')),
            ('intermittent', _('Intermittent')),
            ('error', _('Error')),
            ('unknown', _('Unknown')),
        ],
        default='unknown',
        help_text=_('Current connectivity status')
    )
    
    response_time_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Average response time in milliseconds')
    )
    
    error_count = models.IntegerField(
        default=0,
        help_text=_('Number of errors encountered')
    )
    
    verification_notes = models.TextField(
        blank=True,
        help_text=_('Notes from verification process')
    )
    
    verification_result = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Detailed verification results')
    )
    
    system_health_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Overall system health score (1-100)')
    )
    
    issues_found = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Issues identified during verification')
    )
    
    recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Recommendations for system improvement')
    )
    
    requires_maintenance = models.BooleanField(
        default=False,
        help_text=_('Whether system requires maintenance')
    )
    
    maintenance_scheduled = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When maintenance is scheduled')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Pharmacy Integration Verification Task')
        verbose_name_plural = _('Pharmacy Integration Verification Tasks')
        db_table = 'healthcare_pharmacy_integration_verification_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_technician', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['integration_type', 'status']),
            models.Index(fields=['pharmacy', 'status']),
            models.Index(fields=['connectivity_status']),
            models.Index(fields=['requires_maintenance']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Integration Verification: {self.integration_type} - {self.pharmacy}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign technician if not assigned
        if not self.assigned_technician:
            self.assigned_technician = self._get_available_technician()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_technician(self) -> Optional[User]:
        """Get an available IT technician for integration verification."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_technician:
            self._send_assignment_notification()
        elif self.status == self.Status.COMPLETED:
            self._send_completion_notification()
        elif self.status == self.Status.FAILED:
            self._send_failure_notification()
        elif self.status == self.Status.SYSTEM_ERROR:
            self._send_system_error_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned technician."""
        context = {
            'task': self,
            'pharmacy': self.pharmacy,
            'integration_type': self.integration_type,
            'due_date': self.due_date,
        }
        self._send_email_notification('pharmacy_integration_assigned', self.assigned_technician, context)
    
    def _send_completion_notification(self):
        """Send notification about task completion."""
        context = {
            'task': self,
            'pharmacy': self.pharmacy,
            'system_health_score': self.system_health_score,
            'connectivity_status': self.connectivity_status,
        }
        self._send_email_notification('pharmacy_integration_completed', self.assigned_technician, context)
    
    def _send_failure_notification(self):
        """Send notification about task failure."""
        context = {
            'task': self,
            'pharmacy': self.pharmacy,
            'issues': self.issues_found,
        }
        self._send_email_notification('pharmacy_integration_failed', self.assigned_technician, context)
    
    def _send_system_error_notification(self):
        """Send notification about system error."""
        context = {
            'task': self,
            'pharmacy': self.pharmacy,
            'error_count': self.error_count,
        }
        self._send_email_notification('pharmacy_integration_system_error', self.assigned_technician, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_verification(self, technician: User = None):
        """Start the integration verification process."""
        if technician:
            self.assigned_technician = technician
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def complete_verification(self, result: Dict[str, Any], health_score: int, 
                            response_time: int = None, notes: str = None):
        """Complete the integration verification task."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.verification_result = result
        self.system_health_score = health_score
        self.response_time_ms = response_time
        self.verification_notes = notes or ""
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def fail_verification(self, issues: List[str], notes: str = None):
        """Mark verification as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.issues_found = issues
        self.verification_notes = notes or ""
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def report_system_error(self, error_count: int, issues: List[str]):
        """Report system error during verification."""
        self.status = self.Status.SYSTEM_ERROR
        self.error_count = error_count
        self.issues_found = issues
        self.save()
    
    def schedule_maintenance(self, scheduled_time: datetime):
        """Schedule maintenance for the system."""
        self.requires_maintenance = True
        self.maintenance_scheduled = scheduled_time
        self.save()
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.verification_notes = f"On hold: {reason}\n\n{self.verification_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_system_healthy(self) -> bool:
        """Check if system is healthy."""
        return self.system_health_score and self.system_health_score >= 80
    
    @property
    def is_connectivity_issue(self) -> bool:
        """Check if there are connectivity issues."""
        return self.connectivity_status in ['disconnected', 'intermittent', 'error']
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.COMPLETED:
            return 100
        elif self.status == self.Status.FAILED:
            return 0
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0


class EmergencyAccessLoggingTask(WorkflowTask):
    """
    Emergency access logging task for audit trail compliance.
    
    This task handles the logging and tracking of emergency access
    to patient data and medication systems for audit compliance.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        AUDIT_REQUIRED = 'audit_required', _('Audit Required')
    
    # Access type choices
    class AccessType(models.TextChoices):
        PATIENT_DATA = 'patient_data', _('Patient Data Access')
        MEDICATION_SYSTEM = 'medication_system', _('Medication System Access')
        PRESCRIPTION_SYSTEM = 'prescription_system', _('Prescription System Access')
        PHARMACY_SYSTEM = 'pharmacy_system', _('Pharmacy System Access')
        ADMIN_SYSTEM = 'admin_system', _('Administrative System Access')
        COMPREHENSIVE = 'comprehensive', _('Comprehensive System Access')
    
    # Task fields
    accessing_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='emergency_access_logging_tasks',
        help_text=_('User who accessed the system')
    )
    
    access_type = models.CharField(
        max_length=50,
        choices=AccessType.choices,
        help_text=_('Type of emergency access')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_auditor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_emergency_access_audit_tasks',
        help_text=_('Auditor assigned to review emergency access')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='high',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=2),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    emergency_reason = models.TextField(
        help_text=_('Reason for emergency access')
    )
    
    access_timestamp = models.DateTimeField(
        help_text=_('When the emergency access occurred')
    )
    
    access_duration = models.DurationField(
        help_text=_('Duration of emergency access')
    )
    
    data_accessed = models.JSONField(
        default=list,
        help_text=_('Data that was accessed during emergency')
    )
    
    actions_performed = models.JSONField(
        default=list,
        help_text=_('Actions performed during emergency access')
    )
    
    audit_notes = models.TextField(
        blank=True,
        help_text=_('Notes from audit process')
    )
    
    compliance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Compliance score (1-100)')
    )
    
    violations_found = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Compliance violations identified')
    )
    
    recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Recommendations for improvement')
    )
    
    requires_follow_up = models.BooleanField(
        default=False,
        help_text=_('Whether follow-up action is required')
    )
    
    follow_up_actions = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Follow-up actions required')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Emergency Access Logging Task')
        verbose_name_plural = _('Emergency Access Logging Tasks')
        db_table = 'healthcare_emergency_access_logging_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_auditor', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['access_type', 'status']),
            models.Index(fields=['accessing_user', 'status']),
            models.Index(fields=['access_timestamp']),
            models.Index(fields=['requires_follow_up']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Emergency Access Log: {self.access_type} - {self.accessing_user}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign auditor if not assigned
        if not self.assigned_auditor:
            self.assigned_auditor = self._get_available_auditor()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_auditor(self) -> Optional[User]:
        """Get an available auditor for emergency access review."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_auditor:
            self._send_assignment_notification()
        elif self.status == self.Status.COMPLETED:
            self._send_completion_notification()
        elif self.status == self.Status.AUDIT_REQUIRED:
            self._send_audit_required_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned auditor."""
        context = {
            'task': self,
            'accessing_user': self.accessing_user,
            'access_type': self.access_type,
            'due_date': self.due_date,
        }
        self._send_email_notification('emergency_access_assigned', self.assigned_auditor, context)
    
    def _send_completion_notification(self):
        """Send notification about task completion."""
        context = {
            'task': self,
            'accessing_user': self.accessing_user,
            'compliance_score': self.compliance_score,
        }
        self._send_email_notification('emergency_access_completed', self.assigned_auditor, context)
    
    def _send_audit_required_notification(self):
        """Send notification about audit requirement."""
        context = {
            'task': self,
            'accessing_user': self.accessing_user,
            'violations_found': self.violations_found,
        }
        self._send_email_notification('emergency_access_audit_required', self.assigned_auditor, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_audit(self, auditor: User = None):
        """Start the emergency access audit process."""
        if auditor:
            self.assigned_auditor = auditor
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def complete_audit(self, compliance_score: int, violations: List[str] = None, 
                      recommendations: List[str] = None, notes: str = None):
        """Complete the emergency access audit task."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.compliance_score = compliance_score
        self.violations_found = violations or []
        self.recommendations = recommendations or []
        self.audit_notes = notes or ""
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def require_follow_up(self, actions: List[str]):
        """Mark task as requiring follow-up actions."""
        self.requires_follow_up = True
        self.follow_up_actions = actions
        self.save()
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.audit_notes = f"On hold: {reason}\n\n{self.audit_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.COMPLETED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_compliant(self) -> bool:
        """Check if emergency access was compliant."""
        return self.compliance_score and self.compliance_score >= 80
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.COMPLETED:
            return 100
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0


class MedicationRecallNotificationTask(WorkflowTask):
    """
    Medication recall notification task with patient contact automation.
    
    This task handles medication recall notifications and automated
    patient contact for safety and compliance.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        PATIENTS_NOTIFIED = 'patients_notified', _('Patients Notified')
        PROVIDERS_NOTIFIED = 'providers_notified', _('Providers Notified')
    
    # Recall severity choices
    class RecallSeverity(models.TextChoices):
        CLASS_I = 'class_i', _('Class I - Most Serious')
        CLASS_II = 'class_ii', _('Class II - Moderate')
        CLASS_III = 'class_iii', _('Class III - Least Serious')
        MARKET_WITHDRAWAL = 'market_withdrawal', _('Market Withdrawal')
        MEDICAL_DEVICE_RECALL = 'medical_device_recall', _('Medical Device Recall')
    
    # Task fields
    medication = models.ForeignKey(
        'medications.Medication',
        on_delete=models.CASCADE,
        related_name='recall_notification_tasks',
        help_text=_('Medication subject to recall')
    )
    
    recall_severity = models.CharField(
        max_length=30,
        choices=RecallSeverity.choices,
        help_text=_('Severity of the recall')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_coordinator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_recall_notification_tasks',
        help_text=_('Healthcare coordinator assigned to recall notification')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='high',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=8),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    recall_reason = models.TextField(
        help_text=_('Reason for the medication recall')
    )
    
    recall_date = models.DateTimeField(
        help_text=_('Date when recall was issued')
    )
    
    affected_patients = models.JSONField(
        default=list,
        help_text=_('List of patients affected by recall')
    )
    
    notification_methods = models.JSONField(
        default=list,
        help_text=_('Methods used to notify patients')
    )
    
    notification_notes = models.TextField(
        blank=True,
        help_text=_('Notes about notification process')
    )
    
    patients_notified_count = models.IntegerField(
        default=0,
        help_text=_('Number of patients successfully notified')
    )
    
    patients_responded_count = models.IntegerField(
        default=0,
        help_text=_('Number of patients who responded')
    )
    
    providers_notified_count = models.IntegerField(
        default=0,
        help_text=_('Number of healthcare providers notified')
    )
    
    follow_up_required = models.BooleanField(
        default=False,
        help_text=_('Whether follow-up action is required')
    )
    
    follow_up_actions = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Follow-up actions required')
    )
    
    compliance_verified = models.BooleanField(
        default=False,
        help_text=_('Whether compliance has been verified')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Medication Recall Notification Task')
        verbose_name_plural = _('Medication Recall Notification Tasks')
        db_table = 'healthcare_medication_recall_notification_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_coordinator', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['recall_severity', 'status']),
            models.Index(fields=['medication', 'status']),
            models.Index(fields=['recall_date']),
            models.Index(fields=['follow_up_required']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Recall Notification: {self.recall_severity} - {self.medication}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign coordinator if not assigned
        if not self.assigned_coordinator:
            self.assigned_coordinator = self._get_available_coordinator()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_coordinator(self) -> Optional[User]:
        """Get an available healthcare coordinator."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_coordinator:
            self._send_assignment_notification()
        elif self.status == self.Status.PATIENTS_NOTIFIED:
            self._send_patients_notified_notification()
        elif self.status == self.Status.PROVIDERS_NOTIFIED:
            self._send_providers_notified_notification()
        elif self.status == self.Status.COMPLETED:
            self._send_completion_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned coordinator."""
        context = {
            'task': self,
            'medication': self.medication,
            'recall_severity': self.recall_severity,
            'due_date': self.due_date,
        }
        self._send_email_notification('recall_notification_assigned', self.assigned_coordinator, context)
    
    def _send_patients_notified_notification(self):
        """Send notification about patients being notified."""
        context = {
            'task': self,
            'medication': self.medication,
            'patients_notified_count': self.patients_notified_count,
        }
        self._send_email_notification('recall_patients_notified', self.assigned_coordinator, context)
    
    def _send_providers_notified_notification(self):
        """Send notification about providers being notified."""
        context = {
            'task': self,
            'medication': self.medication,
            'providers_notified_count': self.providers_notified_count,
        }
        self._send_email_notification('recall_providers_notified', self.assigned_coordinator, context)
    
    def _send_completion_notification(self):
        """Send notification about task completion."""
        context = {
            'task': self,
            'medication': self.medication,
            'compliance_verified': self.compliance_verified,
        }
        self._send_email_notification('recall_notification_completed', self.assigned_coordinator, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_notification(self, coordinator: User = None):
        """Start the recall notification process."""
        if coordinator:
            self.assigned_coordinator = coordinator
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def notify_patients(self, notification_methods: List[str], notes: str = None):
        """Mark patients as notified."""
        self.status = self.Status.PATIENTS_NOTIFIED
        self.notification_methods = notification_methods
        self.notification_notes = notes or ""
        self.save()
    
    def notify_providers(self, provider_count: int):
        """Mark providers as notified."""
        self.status = self.Status.PROVIDERS_NOTIFIED
        self.providers_notified_count = provider_count
        self.save()
    
    def update_patient_counts(self, notified_count: int, responded_count: int):
        """Update patient notification counts."""
        self.patients_notified_count = notified_count
        self.patients_responded_count = responded_count
        self.save()
    
    def require_follow_up(self, actions: List[str]):
        """Mark task as requiring follow-up actions."""
        self.follow_up_required = True
        self.follow_up_actions = actions
        self.save()
    
    def verify_compliance(self):
        """Mark compliance as verified."""
        self.compliance_verified = True
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.notification_notes = f"On hold: {reason}\n\n{self.notification_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.COMPLETED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_critical_recall(self) -> bool:
        """Check if this is a critical recall."""
        return self.recall_severity in [self.RecallSeverity.CLASS_I, self.RecallSeverity.MARKET_WITHDRAWAL]
    
    @property
    def notification_success_rate(self) -> Optional[float]:
        """Calculate notification success rate."""
        if self.patients_notified_count > 0:
            return (self.patients_responded_count / self.patients_notified_count) * 100
        return None
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.COMPLETED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.COMPLETED:
            return 100
        elif self.status == self.Status.PROVIDERS_NOTIFIED:
            return 80
        elif self.status == self.Status.PATIENTS_NOTIFIED:
            return 60
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0


class PatientDataAccessApprovalTask(WorkflowTask):
    """
    Patient data access approval task with HIPAA compliance tracking.
    
    This task handles the approval process for accessing patient health
    information with proper HIPAA compliance and audit trail tracking.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        UNDER_REVIEW = 'under_review', _('Under Review')
    
    # Access type choices
    class AccessType(models.TextChoices):
        TREATMENT = 'treatment', _('Treatment')
        PAYMENT = 'payment', _('Payment')
        HEALTHCARE_OPERATIONS = 'healthcare_operations', _('Healthcare Operations')
        RESEARCH = 'research', _('Research')
        LEGAL = 'legal', _('Legal')
        EMERGENCY = 'emergency', _('Emergency')
        PUBLIC_HEALTH = 'public_health', _('Public Health')
    
    # Task fields
    requesting_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='data_access_approval_tasks',
        help_text=_('User requesting data access')
    )
    
    patient = models.ForeignKey(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='data_access_approval_tasks',
        help_text=_('Patient whose data is being accessed')
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
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_data_access_approval_tasks',
        help_text=_('Healthcare professional assigned to approval')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='normal',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=6),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    approval_notes = models.TextField(
        blank=True,
        help_text=_('Notes from approval process')
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
    
    compliance_issues = models.JSONField(
        default=list,
        blank=True,
        help_text=_('HIPAA compliance issues identified')
    )
    
    security_concerns = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Security concerns identified')
    )
    
    audit_trail = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Complete audit trail of approval process')
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
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Patient Data Access Approval Task')
        verbose_name_plural = _('Patient Data Access Approval Tasks')
        db_table = 'healthcare_patient_data_access_approval_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_approver', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['access_type', 'status']),
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['requesting_user', 'status']),
            models.Index(fields=['access_expires_at']),
            models.Index(fields=['emergency_override']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Data Access Approval: {self.access_type} - {self.patient}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign approver if not assigned
        if not self.assigned_approver:
            self.assigned_approver = self._get_available_approver()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_approver(self) -> Optional[User]:
        """Get an available healthcare professional for approval."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_approver:
            self._send_assignment_notification()
        elif self.status == self.Status.APPROVED:
            self._send_approval_notification()
        elif self.status == self.Status.REJECTED:
            self._send_rejection_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned approver."""
        context = {
            'task': self,
            'patient': self.patient,
            'requesting_user': self.requesting_user,
            'due_date': self.due_date,
        }
        self._send_email_notification('data_access_approval_assigned', self.assigned_approver, context)
    
    def _send_approval_notification(self):
        """Send notification about approval."""
        context = {
            'task': self,
            'patient': self.patient,
            'requesting_user': self.requesting_user,
            'access_expires_at': self.access_expires_at,
        }
        self._send_email_notification('data_access_approval_granted', self.requesting_user, context)
    
    def _send_rejection_notification(self):
        """Send notification about rejection."""
        context = {
            'task': self,
            'patient': self.patient,
            'requesting_user': self.requesting_user,
            'approval_notes': self.approval_notes,
        }
        self._send_email_notification('data_access_approval_rejected', self.requesting_user, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_approval(self, approver: User = None):
        """Start the approval process."""
        if approver:
            self.assigned_approver = approver
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def approve_access(self, notes: str = None, scores: Dict[str, int] = None):
        """Approve data access request."""
        self.status = self.Status.APPROVED
        self.completed_at = timezone.now()
        self.approval_notes = notes or ""
        self.access_granted_at = timezone.now()
        self.access_expires_at = timezone.now() + self.access_duration
        
        if scores:
            self.hipaa_compliance_score = scores.get('hipaa_compliance')
            self.security_assessment_score = scores.get('security_assessment')
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        # Add to audit trail
        self._add_audit_entry('approved', self.assigned_approver, notes)
        
        self.save()
    
    def reject_access(self, reason: str, compliance_issues: List[str] = None):
        """Reject data access request."""
        self.status = self.Status.REJECTED
        self.completed_at = timezone.now()
        self.approval_notes = reason
        
        if compliance_issues:
            self.compliance_issues = compliance_issues
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        # Add to audit trail
        self._add_audit_entry('rejected', self.assigned_approver, reason)
        
        self.save()
    
    def emergency_override_approval(self, approver: User, reason: str):
        """Emergency override for data access approval."""
        self.emergency_override = True
        self.assigned_approver = approver
        self.approval_notes = f"Emergency override: {reason}"
        self.status = self.Status.APPROVED
        self.completed_at = timezone.now()
        self.access_granted_at = timezone.now()
        self.access_expires_at = timezone.now() + self.access_duration
        
        # Add to audit trail
        self._add_audit_entry('emergency_override', approver, reason)
        
        self.save()
    
    def _add_audit_entry(self, action: str, user: User, notes: str = None):
        """Add entry to audit trail."""
        audit_entry = {
            'timestamp': timezone.now().isoformat(),
            'action': action,
            'user_id': user.id,
            'user_name': user.get_full_name() or user.username,
            'notes': notes,
        }
        
        if not self.audit_trail:
            self.audit_trail = []
        
        self.audit_trail.append(audit_entry)
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.approval_notes = f"On hold: {reason}\n\n{self.approval_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.APPROVED, self.Status.REJECTED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_emergency_access(self) -> bool:
        """Check if this is emergency access."""
        return self.access_type == self.AccessType.EMERGENCY or self.emergency_override
    
    @property
    def is_access_active(self) -> bool:
        """Check if access is currently active."""
        if self.status != self.Status.APPROVED:
            return False
        if not self.access_expires_at:
            return False
        return timezone.now() < self.access_expires_at
    
    @property
    def is_access_expired(self) -> bool:
        """Check if access has expired."""
        if not self.access_expires_at:
            return False
        return timezone.now() >= self.access_expires_at
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.APPROVED, self.Status.REJECTED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.APPROVED:
            return 100
        elif self.status == self.Status.REJECTED:
            return 0
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0


class MedicationStockAlertTask(WorkflowTask):
    """
    Medication stock alert task with automated escalation.
    
    This task handles medication stock level monitoring and alerts
    with automated escalation to appropriate healthcare professionals.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        RESOLVED = 'resolved', _('Resolved')
        ESCALATED = 'escalated', _('Escalated')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
    
    # Alert type choices
    class AlertType(models.TextChoices):
        LOW_STOCK = 'low_stock', _('Low Stock Alert')
        OUT_OF_STOCK = 'out_of_stock', _('Out of Stock Alert')
        EXPIRING_SOON = 'expiring_soon', _('Expiring Soon Alert')
        RECALL_NOTICE = 'recall_notice', _('Recall Notice Alert')
        SHORTAGE = 'shortage', _('Supply Shortage Alert')
        CRITICAL = 'critical', _('Critical Stock Alert')
    
    # Task fields
    medication = models.ForeignKey(
        'medications.Medication',
        on_delete=models.CASCADE,
        related_name='stock_alert_tasks',
        help_text=_('Associated medication for stock alert')
    )
    
    alert_type = models.CharField(
        max_length=30,
        choices=AlertType.choices,
        help_text=_('Type of stock alert')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_handler = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_stock_alert_tasks',
        help_text=_('Healthcare professional assigned to handle alert')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='normal',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=2),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    current_stock_level = models.IntegerField(
        help_text=_('Current stock level')
    )
    
    minimum_stock_level = models.IntegerField(
        help_text=_('Minimum required stock level')
    )
    
    alert_threshold = models.IntegerField(
        help_text=_('Threshold that triggered the alert')
    )
    
    alert_notes = models.TextField(
        blank=True,
        help_text=_('Notes about the stock alert')
    )
    
    resolution_notes = models.TextField(
        blank=True,
        help_text=_('Notes about how the alert was resolved')
    )
    
    escalation_level = models.IntegerField(
        default=1,
        help_text=_('Current escalation level (1-5)')
    )
    
    escalation_history = models.JSONField(
        default=list,
        blank=True,
        help_text=_('History of escalations')
    )
    
    escalated_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='escalated_stock_alert_tasks',
        help_text=_('User escalated to if needed')
    )
    
    escalation_reason = models.TextField(
        blank=True,
        help_text=_('Reason for escalation')
    )
    
    auto_escalation_enabled = models.BooleanField(
        default=True,
        help_text=_('Whether automatic escalation is enabled')
    )
    
    escalation_delay = models.DurationField(
        default=timedelta(hours=4),
        help_text=_('Delay before auto-escalation')
    )
    
    last_escalation_check = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time escalation was checked')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Medication Stock Alert Task')
        verbose_name_plural = _('Medication Stock Alert Tasks')
        db_table = 'healthcare_medication_stock_alert_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_handler', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['medication', 'status']),
            models.Index(fields=['escalation_level']),
            models.Index(fields=['auto_escalation_enabled']),
            models.Index(fields=['last_escalation_check']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Stock Alert: {self.alert_type} - {self.medication}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign handler if not assigned
        if not self.assigned_handler:
            self.assigned_handler = self._get_available_handler()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_handler(self) -> Optional[User]:
        """Get an available healthcare professional to handle the alert."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_handler:
            self._send_assignment_notification()
        elif self.status == self.Status.RESOLVED:
            self._send_resolution_notification()
        elif self.status == self.Status.ESCALATED:
            self._send_escalation_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned handler."""
        context = {
            'task': self,
            'medication': self.medication,
            'due_date': self.due_date,
        }
        self._send_email_notification('stock_alert_assigned', self.assigned_handler, context)
    
    def _send_resolution_notification(self):
        """Send notification about alert resolution."""
        context = {
            'task': self,
            'medication': self.medication,
            'resolution_notes': self.resolution_notes,
        }
        self._send_email_notification('stock_alert_resolved', self.assigned_handler, context)
    
    def _send_escalation_notification(self):
        """Send notification about escalation."""
        context = {
            'task': self,
            'medication': self.medication,
            'escalation_reason': self.escalation_reason,
        }
        if self.escalated_to:
            self._send_email_notification('stock_alert_escalated', self.escalated_to, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_handling(self, handler: User = None):
        """Start handling the stock alert."""
        if handler:
            self.assigned_handler = handler
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def resolve_alert(self, resolution_notes: str, new_stock_level: int = None):
        """Resolve the stock alert."""
        self.status = self.Status.RESOLVED
        self.completed_at = timezone.now()
        self.resolved_at = timezone.now()
        self.resolution_notes = resolution_notes
        
        if new_stock_level is not None:
            self.current_stock_level = new_stock_level
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def escalate_alert(self, escalated_to: User, reason: str):
        """Escalate the alert to another user."""
        self.status = self.Status.ESCALATED
        self.escalated_to = escalated_to
        self.escalation_reason = reason
        self.escalation_level += 1
        
        # Add to escalation history
        escalation_entry = {
            'timestamp': timezone.now().isoformat(),
            'level': self.escalation_level,
            'escalated_to_id': escalated_to.id,
            'escalated_to_name': escalated_to.get_full_name() or escalated_to.username,
            'reason': reason,
        }
        
        if not self.escalation_history:
            self.escalation_history = []
        
        self.escalation_history.append(escalation_entry)
        
        self.save()
    
    def check_auto_escalation(self):
        """Check if automatic escalation is needed."""
        if not self.auto_escalation_enabled:
            return
        
        if self.status in [self.Status.RESOLVED, self.Status.CANCELLED]:
            return
        
        if self.last_escalation_check and timezone.now() - self.last_escalation_check < self.escalation_delay:
            return
        
        # Check if escalation is needed based on time elapsed
        if self.started_at and timezone.now() - self.started_at > self.escalation_delay:
            self._auto_escalate()
        
        self.last_escalation_check = timezone.now()
        self.save()
    
    def _auto_escalate(self):
        """Automatically escalate the alert."""
        if self.escalation_level >= 5:  # Max escalation level
            return
        
        # Get next level handler
        next_handler = self._get_next_level_handler()
        if next_handler:
            self.escalate_alert(next_handler, "Automatic escalation due to time delay")
    
    def _get_next_level_handler(self) -> Optional[User]:
        """Get handler for next escalation level."""
        # Implementation would get appropriate handler based on escalation level
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.alert_notes = f"On hold: {reason}\n\n{self.alert_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.RESOLVED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def is_critical_alert(self) -> bool:
        """Check if this is a critical alert."""
        return self.alert_type in [self.AlertType.CRITICAL, self.AlertType.OUT_OF_STOCK]
    
    @property
    def stock_deficit(self) -> int:
        """Calculate stock deficit."""
        return max(0, self.minimum_stock_level - self.current_stock_level)
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.RESOLVED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.RESOLVED:
            return 100
        elif self.status == self.Status.ESCALATED:
            return 50 + (self.escalation_level * 10)
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0


class MedicationContentReviewTask(WorkflowTask):
    """
    Medication content review task with healthcare professional assignments.
    
    This task handles the review of medication content for clinical accuracy,
    regulatory compliance, and patient safety information.
    """
    
    # Task status choices
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        ON_HOLD = 'on_hold', _('On Hold')
        REQUIRES_REVISION = 'requires_revision', _('Requires Revision')
    
    # Review type choices
    class ReviewType(models.TextChoices):
        CLINICAL_ACCURACY = 'clinical_accuracy', _('Clinical Accuracy Review')
        REGULATORY_COMPLIANCE = 'regulatory_compliance', _('Regulatory Compliance Review')
        PATIENT_SAFETY = 'patient_safety', _('Patient Safety Review')
        DRUG_INTERACTIONS = 'drug_interactions', _('Drug Interactions Review')
        DOSAGE_GUIDELINES = 'dosage_guidelines', _('Dosage Guidelines Review')
        CONTRAINDICATIONS = 'contraindications', _('Contraindications Review')
        SIDE_EFFECTS = 'side_effects', _('Side Effects Review')
        COMPREHENSIVE = 'comprehensive', _('Comprehensive Review')
    
    # Task fields
    medication = models.ForeignKey(
        'medications.Medication',
        on_delete=models.CASCADE,
        related_name='content_review_tasks',
        help_text=_('Associated medication for content review')
    )
    
    review_type = models.CharField(
        max_length=50,
        choices=ReviewType.choices,
        help_text=_('Type of content review to perform')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text=_('Current task status')
    )
    
    assigned_reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_content_review_tasks',
        help_text=_('Healthcare professional assigned to content review')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('normal', _('Normal')),
            ('high', _('High')),
            ('urgent', _('Urgent')),
            ('critical', _('Critical')),
        ],
        default='normal',
        help_text=_('Task priority level')
    )
    
    due_date = models.DateTimeField(
        help_text=_('Due date for task completion')
    )
    
    estimated_duration = models.DurationField(
        default=timedelta(hours=4),
        help_text=_('Estimated time to complete task')
    )
    
    actual_duration = models.DurationField(
        null=True,
        blank=True,
        help_text=_('Actual time taken to complete task')
    )
    
    review_notes = models.TextField(
        blank=True,
        help_text=_('Notes from content review process')
    )
    
    review_result = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Detailed review results')
    )
    
    accuracy_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Clinical accuracy score (1-100)')
    )
    
    compliance_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Regulatory compliance score (1-100)')
    )
    
    safety_score = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Patient safety score (1-100)')
    )
    
    issues_found = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Issues identified during review')
    )
    
    recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text=_('Recommendations for content improvement')
    )
    
    requires_revision = models.BooleanField(
        default=False,
        help_text=_('Whether content requires revision')
    )
    
    revision_notes = models.TextField(
        blank=True,
        help_text=_('Notes for required revisions')
    )
    
    content_version = models.CharField(
        max_length=20,
        default='1.0',
        help_text=_('Version of content being reviewed')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Medication Content Review Task')
        verbose_name_plural = _('Medication Content Review Tasks')
        db_table = 'healthcare_medication_content_review_tasks'
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_reviewer', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['review_type', 'status']),
            models.Index(fields=['medication', 'status']),
            models.Index(fields=['requires_revision']),
            models.Index(fields=['content_version']),
        ]
        ordering = ['due_date', '-priority']
    
    def __str__(self):
        return f"Content Review Task: {self.review_type} - {self.medication}"
    
    def save(self, *args, **kwargs):
        # Set due date if not provided
        if not self.due_date:
            self.due_date = timezone.now() + self.estimated_duration
        
        # Auto-assign reviewer if not assigned
        if not self.assigned_reviewer:
            self.assigned_reviewer = self._get_available_reviewer()
        
        super().save(*args, **kwargs)
        
        # Send notifications on status change
        if self.pk:
            self._send_status_notifications()
    
    def _get_available_reviewer(self) -> Optional[User]:
        """Get an available healthcare professional for content review."""
        # Implementation would query for available users with appropriate roles
        return User.objects.filter(
            is_active=True,
            # Add role-based filtering here
        ).first()
    
    def _send_status_notifications(self):
        """Send notifications based on task status changes."""
        if self.status == self.Status.IN_PROGRESS and self.assigned_reviewer:
            self._send_assignment_notification()
        elif self.status == self.Status.COMPLETED:
            self._send_completion_notification()
        elif self.status == self.Status.FAILED:
            self._send_failure_notification()
        elif self.status == self.Status.REQUIRES_REVISION:
            self._send_revision_notification()
    
    def _send_assignment_notification(self):
        """Send notification to assigned reviewer."""
        context = {
            'task': self,
            'medication': self.medication,
            'due_date': self.due_date,
        }
        self._send_email_notification('content_review_task_assigned', self.assigned_reviewer, context)
    
    def _send_completion_notification(self):
        """Send notification about task completion."""
        context = {
            'task': self,
            'medication': self.medication,
            'result': self.review_result,
        }
        self._send_email_notification('content_review_task_completed', self.assigned_reviewer, context)
    
    def _send_failure_notification(self):
        """Send notification about task failure."""
        context = {
            'task': self,
            'medication': self.medication,
            'issues': self.issues_found,
        }
        self._send_email_notification('content_review_task_failed', self.assigned_reviewer, context)
    
    def _send_revision_notification(self):
        """Send notification about required revisions."""
        context = {
            'task': self,
            'medication': self.medication,
            'revision_notes': self.revision_notes,
        }
        self._send_email_notification('content_review_task_revision_required', self.assigned_reviewer, context)
    
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
            logger.error(f"Failed to send notification for task {self.id}: {e}")
    
    def start_review(self, reviewer: User = None):
        """Start the content review process."""
        if reviewer:
            self.assigned_reviewer = reviewer
        
        self.status = self.Status.IN_PROGRESS
        self.started_at = timezone.now()
        self.save()
    
    def complete_review(self, result: Dict[str, Any], notes: str = None, scores: Dict[str, int] = None):
        """Complete the content review task."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.review_result = result
        self.review_notes = notes or ""
        
        if scores:
            self.accuracy_score = scores.get('accuracy')
            self.compliance_score = scores.get('compliance')
            self.safety_score = scores.get('safety')
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def require_revision(self, revision_notes: str, issues: List[str] = None):
        """Mark content as requiring revision."""
        self.status = self.Status.REQUIRES_REVISION
        self.revision_notes = revision_notes
        self.requires_revision = True
        
        if issues:
            self.issues_found = issues
        
        self.save()
    
    def fail_review(self, issues: List[str], notes: str = None):
        """Mark review as failed."""
        self.status = self.Status.FAILED
        self.completed_at = timezone.now()
        self.issues_found = issues
        self.review_notes = notes or ""
        
        if self.started_at:
            self.actual_duration = self.completed_at - self.started_at
        
        self.save()
    
    def put_on_hold(self, reason: str):
        """Put task on hold."""
        self.status = self.Status.ON_HOLD
        self.review_notes = f"On hold: {reason}\n\n{self.review_notes or ''}"
        self.save()
    
    def resume_task(self):
        """Resume task from hold."""
        if self.status == self.Status.ON_HOLD:
            self.status = self.Status.IN_PROGRESS
            self.save()
    
    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        return self.due_date < timezone.now() and self.status not in [
            self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED
        ]
    
    @property
    def is_high_priority(self) -> bool:
        """Check if task is high priority."""
        return self.priority in ['high', 'urgent', 'critical']
    
    @property
    def overall_score(self) -> Optional[int]:
        """Calculate overall review score."""
        scores = [s for s in [self.accuracy_score, self.compliance_score, self.safety_score] if s is not None]
        if scores:
            return sum(scores) // len(scores)
        return None
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Get time remaining until due date."""
        if self.status in [self.Status.COMPLETED, self.Status.FAILED, self.Status.CANCELLED]:
            return None
        return self.due_date - timezone.now()
    
    @property
    def progress_percentage(self) -> int:
        """Calculate task progress percentage."""
        if self.status == self.Status.COMPLETED:
            return 100
        elif self.status == self.Status.FAILED:
            return 0
        elif self.status == self.Status.IN_PROGRESS and self.started_at:
            elapsed = timezone.now() - self.started_at
            if self.estimated_duration:
                return min(95, int((elapsed / self.estimated_duration) * 100))
        return 0 