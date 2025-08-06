# -*- coding: utf-8 -*-
"""
MedGuard SA - Data Breach Notification System

Implements comprehensive data breach detection, notification, and response
system for healthcare compliance with GDPR, POPIA, and HIPAA requirements.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string

from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet

logger = logging.getLogger(__name__)
User = get_user_model()


@register_snippet
class BreachCategory(models.Model):
    """
    Categories of data breaches with different notification requirements.
    
    Defines breach types and their associated notification timelines
    and compliance requirements.
    """
    
    BREACH_TYPES = [
        ('unauthorized_access', _('Unauthorized Access')),
        ('data_theft', _('Data Theft')),
        ('ransomware', _('Ransomware Attack')),
        ('insider_threat', _('Insider Threat')),
        ('accidental_disclosure', _('Accidental Disclosure')),
        ('system_compromise', _('System Compromise')),
        ('vendor_breach', _('Third-Party Vendor Breach')),
        ('physical_theft', _('Physical Device Theft')),
        ('email_compromise', _('Email Compromise')),
        ('database_breach', _('Database Breach')),
        ('backup_compromise', _('Backup System Compromise')),
        ('cloud_breach', _('Cloud Service Breach')),
    ]
    
    SEVERITY_LEVELS = [
        ('low', _('Low Risk')),
        ('medium', _('Medium Risk')),
        ('high', _('High Risk')),
        ('critical', _('Critical Risk')),
        ('catastrophic', _('Catastrophic Risk')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Category Name"),
        help_text=_("Descriptive name for this breach category")
    )
    
    breach_type = models.CharField(
        max_length=30,
        choices=BREACH_TYPES,
        unique=True,
        verbose_name=_("Breach Type"),
        help_text=_("Type of data breach")
    )
    
    severity_level = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        verbose_name=_("Default Severity Level"),
        help_text=_("Default severity level for this breach type")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of this breach category")
    )
    
    notification_timeline_hours = models.PositiveIntegerField(
        verbose_name=_("Notification Timeline (Hours)"),
        help_text=_("Hours within which authorities must be notified")
    )
    
    patient_notification_required = models.BooleanField(
        default=True,
        verbose_name=_("Patient Notification Required"),
        help_text=_("Whether patients must be notified of this breach type")
    )
    
    patient_notification_timeline_hours = models.PositiveIntegerField(
        default=72,
        verbose_name=_("Patient Notification Timeline (Hours)"),
        help_text=_("Hours within which patients must be notified")
    )
    
    regulatory_notification_required = models.BooleanField(
        default=True,
        verbose_name=_("Regulatory Notification Required"),
        help_text=_("Whether regulatory authorities must be notified")
    )
    
    media_notification_threshold = models.PositiveIntegerField(
        default=1000,
        verbose_name=_("Media Notification Threshold"),
        help_text=_("Number of affected patients that triggers media notification")
    )
    
    automatic_response_actions = models.JSONField(
        default=list,
        verbose_name=_("Automatic Response Actions"),
        help_text=_("List of automatic actions to take for this breach type")
    )
    
    compliance_frameworks = models.JSONField(
        default=list,
        verbose_name=_("Compliance Frameworks"),
        help_text=_("Regulatory frameworks that apply to this breach type")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('breach_type'),
            FieldPanel('severity_level'),
            FieldPanel('description'),
        ], heading=_("Category Information")),
        
        MultiFieldPanel([
            FieldPanel('notification_timeline_hours'),
            FieldPanel('patient_notification_required'),
            FieldPanel('patient_notification_timeline_hours'),
            FieldPanel('regulatory_notification_required'),
        ], heading=_("Notification Requirements")),
        
        MultiFieldPanel([
            FieldPanel('media_notification_threshold'),
            FieldPanel('automatic_response_actions'),
            FieldPanel('compliance_frameworks'),
        ], heading=_("Response Configuration")),
        
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = _("Breach Category")
        verbose_name_plural = _("Breach Categories")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_level_display()})"
    
    def clean(self):
        """Validate breach category settings."""
        super().clean()
        
        if self.notification_timeline_hours < 1:
            raise ValidationError(_("Notification timeline must be at least 1 hour"))
        
        if self.patient_notification_timeline_hours < 1:
            raise ValidationError(_("Patient notification timeline must be at least 1 hour"))


class DataBreachIncident(models.Model):
    """
    Individual data breach incidents with full investigation tracking.
    
    Records breach incidents with comprehensive details for
    compliance reporting and response coordination.
    """
    
    INCIDENT_STATUS = [
        ('reported', _('Reported')),
        ('investigating', _('Under Investigation')),
        ('confirmed', _('Confirmed Breach')),
        ('contained', _('Breach Contained')),
        ('mitigated', _('Breach Mitigated')),
        ('resolved', _('Resolved')),
        ('false_alarm', _('False Alarm')),
        ('closed', _('Closed')),
    ]
    
    DISCOVERY_METHODS = [
        ('automated_alert', _('Automated Security Alert')),
        ('employee_report', _('Employee Report')),
        ('patient_complaint', _('Patient Complaint')),
        ('audit_finding', _('Audit Finding')),
        ('vendor_notification', _('Vendor Notification')),
        ('law_enforcement', _('Law Enforcement')),
        ('media_report', _('Media Report')),
        ('regulatory_inquiry', _('Regulatory Inquiry')),
        ('penetration_test', _('Penetration Test')),
        ('other', _('Other')),
    ]
    
    incident_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Incident ID"),
        help_text=_("Unique identifier for this breach incident")
    )
    
    category = models.ForeignKey(
        BreachCategory,
        on_delete=models.CASCADE,
        verbose_name=_("Breach Category"),
        help_text=_("Category of data breach")
    )
    
    status = models.CharField(
        max_length=20,
        choices=INCIDENT_STATUS,
        default='reported',
        verbose_name=_("Status")
    )
    
    severity_level = models.CharField(
        max_length=20,
        choices=BreachCategory.SEVERITY_LEVELS,
        verbose_name=_("Severity Level"),
        help_text=_("Assessed severity of this incident")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Incident Title"),
        help_text=_("Brief title describing the incident")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of what happened")
    )
    
    discovered_at = models.DateTimeField(
        verbose_name=_("Discovery Date/Time"),
        help_text=_("When the breach was first discovered")
    )
    
    occurred_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Occurrence Date/Time"),
        help_text=_("When the breach actually occurred (if known)")
    )
    
    discovery_method = models.CharField(
        max_length=30,
        choices=DISCOVERY_METHODS,
        verbose_name=_("Discovery Method"),
        help_text=_("How the breach was discovered")
    )
    
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Reported By"),
        help_text=_("User who reported the incident"),
        related_name='reported_breach_incidents'
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Assigned To"),
        help_text=_("User assigned to investigate this incident"),
        related_name='assigned_breach_incidents'
    )
    
    affected_systems = models.JSONField(
        default=list,
        verbose_name=_("Affected Systems"),
        help_text=_("List of systems affected by the breach")
    )
    
    affected_data_types = models.JSONField(
        default=list,
        verbose_name=_("Affected Data Types"),
        help_text=_("Types of data compromised in the breach")
    )
    
    estimated_affected_patients = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Estimated Affected Patients"),
        help_text=_("Estimated number of patients affected")
    )
    
    confirmed_affected_patients = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Confirmed Affected Patients"),
        help_text=_("Confirmed number of patients affected")
    )
    
    root_cause = models.TextField(
        blank=True,
        verbose_name=_("Root Cause"),
        help_text=_("Identified root cause of the breach")
    )
    
    containment_actions = models.TextField(
        blank=True,
        verbose_name=_("Containment Actions"),
        help_text=_("Actions taken to contain the breach")
    )
    
    mitigation_actions = models.TextField(
        blank=True,
        verbose_name=_("Mitigation Actions"),
        help_text=_("Actions taken to mitigate the breach impact")
    )
    
    lessons_learned = models.TextField(
        blank=True,
        verbose_name=_("Lessons Learned"),
        help_text=_("Lessons learned from this incident")
    )
    
    external_parties_notified = models.JSONField(
        default=list,
        verbose_name=_("External Parties Notified"),
        help_text=_("List of external parties that were notified")
    )
    
    regulatory_notifications_sent = models.BooleanField(
        default=False,
        verbose_name=_("Regulatory Notifications Sent"),
        help_text=_("Whether regulatory authorities have been notified")
    )
    
    patient_notifications_sent = models.BooleanField(
        default=False,
        verbose_name=_("Patient Notifications Sent"),
        help_text=_("Whether affected patients have been notified")
    )
    
    media_notification_sent = models.BooleanField(
        default=False,
        verbose_name=_("Media Notification Sent"),
        help_text=_("Whether media has been notified")
    )
    
    investigation_notes = models.TextField(
        blank=True,
        verbose_name=_("Investigation Notes"),
        help_text=_("Detailed investigation notes and findings")
    )
    
    attachments = models.JSONField(
        default=list,
        verbose_name=_("Attachments"),
        help_text=_("List of attached files and evidence")
    )
    
    is_confirmed_breach = models.BooleanField(
        default=False,
        verbose_name=_("Confirmed Breach"),
        help_text=_("Whether this is confirmed as an actual breach")
    )
    
    requires_regulatory_reporting = models.BooleanField(
        default=True,
        verbose_name=_("Requires Regulatory Reporting"),
        help_text=_("Whether this breach requires regulatory reporting")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Data Breach Incident")
        verbose_name_plural = _("Data Breach Incidents")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.incident_id} - {self.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Generate incident ID if not provided."""
        if not self.incident_id:
            self.incident_id = f"BREACH-{timezone.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Set severity from category if not specified
        if not self.severity_level and self.category:
            self.severity_level = self.category.severity_level
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate incident settings."""
        super().clean()
        
        if self.occurred_at and self.discovered_at and self.occurred_at > self.discovered_at:
            raise ValidationError(_("Occurrence date cannot be after discovery date"))
        
        if self.estimated_affected_patients < 0:
            raise ValidationError(_("Estimated affected patients cannot be negative"))
    
    def get_notification_deadlines(self) -> Dict[str, datetime]:
        """Calculate notification deadlines based on category requirements."""
        deadlines = {}
        
        if self.category.regulatory_notification_required:
            deadlines['regulatory'] = self.discovered_at + timedelta(
                hours=self.category.notification_timeline_hours
            )
        
        if self.category.patient_notification_required:
            deadlines['patient'] = self.discovered_at + timedelta(
                hours=self.category.patient_notification_timeline_hours
            )
        
        if (self.confirmed_affected_patients >= self.category.media_notification_threshold):
            # Media notification typically within 24-48 hours
            deadlines['media'] = self.discovered_at + timedelta(hours=48)
        
        return deadlines
    
    def is_notification_overdue(self, notification_type: str) -> bool:
        """Check if a specific notification is overdue."""
        deadlines = self.get_notification_deadlines()
        
        if notification_type not in deadlines:
            return False
        
        deadline = deadlines[notification_type]
        
        if notification_type == 'regulatory':
            return not self.regulatory_notifications_sent and timezone.now() > deadline
        elif notification_type == 'patient':
            return not self.patient_notifications_sent and timezone.now() > deadline
        elif notification_type == 'media':
            return not self.media_notification_sent and timezone.now() > deadline
        
        return False
    
    def get_time_to_notification_deadline(self, notification_type: str) -> Optional[timedelta]:
        """Get time remaining until notification deadline."""
        deadlines = self.get_notification_deadlines()
        
        if notification_type not in deadlines:
            return None
        
        deadline = deadlines[notification_type]
        time_remaining = deadline - timezone.now()
        
        return time_remaining if time_remaining.total_seconds() > 0 else timedelta(0)
    
    def mark_resolved(self, resolution_notes: str = ""):
        """Mark incident as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        
        if resolution_notes:
            self.investigation_notes += f"\n\nResolved at {timezone.now()}: {resolution_notes}"
        
        self.save()
        
        logger.info(f"Breach incident {self.incident_id} marked as resolved")


class BreachNotification(models.Model):
    """
    Individual breach notifications sent to various parties.
    
    Tracks all notifications sent regarding a breach incident
    for compliance documentation and audit trails.
    """
    
    NOTIFICATION_TYPES = [
        ('regulatory', _('Regulatory Authority')),
        ('patient', _('Affected Patient')),
        ('media', _('Media/Public')),
        ('internal', _('Internal Stakeholder')),
        ('vendor', _('Third-Party Vendor')),
        ('law_enforcement', _('Law Enforcement')),
        ('insurance', _('Insurance Provider')),
        ('legal_counsel', _('Legal Counsel')),
    ]
    
    DELIVERY_METHODS = [
        ('email', _('Email')),
        ('postal_mail', _('Postal Mail')),
        ('phone', _('Phone Call')),
        ('sms', _('SMS')),
        ('secure_portal', _('Secure Patient Portal')),
        ('website', _('Website Publication')),
        ('press_release', _('Press Release')),
        ('regulatory_portal', _('Regulatory Portal')),
    ]
    
    NOTIFICATION_STATUS = [
        ('pending', _('Pending')),
        ('sent', _('Sent')),
        ('delivered', _('Delivered')),
        ('failed', _('Failed')),
        ('bounced', _('Bounced')),
        ('acknowledged', _('Acknowledged')),
    ]
    
    incident = models.ForeignKey(
        DataBreachIncident,
        on_delete=models.CASCADE,
        verbose_name=_("Breach Incident"),
        related_name='notifications'
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        verbose_name=_("Notification Type")
    )
    
    recipient_name = models.CharField(
        max_length=200,
        verbose_name=_("Recipient Name"),
        help_text=_("Name of the notification recipient")
    )
    
    recipient_contact = models.CharField(
        max_length=500,
        verbose_name=_("Recipient Contact"),
        help_text=_("Contact information (email, phone, address, etc.)")
    )
    
    delivery_method = models.CharField(
        max_length=20,
        choices=DELIVERY_METHODS,
        verbose_name=_("Delivery Method")
    )
    
    status = models.CharField(
        max_length=20,
        choices=NOTIFICATION_STATUS,
        default='pending',
        verbose_name=_("Status")
    )
    
    subject = models.CharField(
        max_length=200,
        verbose_name=_("Subject/Title"),
        help_text=_("Subject line or title of the notification")
    )
    
    message_content = models.TextField(
        verbose_name=_("Message Content"),
        help_text=_("Full content of the notification message")
    )
    
    template_used = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Template Used"),
        help_text=_("Template used to generate this notification")
    )
    
    scheduled_send_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled Send Time"),
        help_text=_("When notification is scheduled to be sent")
    )
    
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Sent At")
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Delivered At")
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Acknowledged At")
    )
    
    failure_reason = models.TextField(
        blank=True,
        verbose_name=_("Failure Reason"),
        help_text=_("Reason for delivery failure")
    )
    
    delivery_confirmation = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Delivery Confirmation"),
        help_text=_("Delivery confirmation ID or reference")
    )
    
    attachments = models.JSONField(
        default=list,
        verbose_name=_("Attachments"),
        help_text=_("List of files attached to the notification")
    )
    
    metadata = models.JSONField(
        default=dict,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata about the notification")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Breach Notification")
        verbose_name_plural = _("Breach Notifications")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.incident.incident_id} - {self.get_notification_type_display()} to {self.recipient_name}"
    
    def send_notification(self):
        """Send the notification using the specified delivery method."""
        try:
            if self.delivery_method == 'email':
                self._send_email_notification()
            elif self.delivery_method == 'sms':
                self._send_sms_notification()
            elif self.delivery_method == 'postal_mail':
                self._send_postal_notification()
            # Add other delivery methods as needed
            
            self.status = 'sent'
            self.sent_at = timezone.now()
            self.save()
            
            logger.info(f"Sent breach notification {self.id} to {self.recipient_name}")
            
        except Exception as e:
            self.status = 'failed'
            self.failure_reason = str(e)
            self.save()
            
            logger.error(f"Failed to send breach notification {self.id}: {e}")
            raise
    
    def _send_email_notification(self):
        """Send notification via email."""
        send_mail(
            subject=self.subject,
            message=self.message_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[self.recipient_contact],
            fail_silently=False
        )
    
    def _send_sms_notification(self):
        """Send notification via SMS."""
        # Implement SMS sending logic
        # This would integrate with your SMS provider
        pass
    
    def _send_postal_notification(self):
        """Schedule postal mail notification."""
        # Implement postal mail scheduling
        # This would integrate with your postal service provider
        pass
    
    def mark_delivered(self, confirmation_id: str = ""):
        """Mark notification as delivered."""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        if confirmation_id:
            self.delivery_confirmation = confirmation_id
        self.save()
    
    def mark_acknowledged(self):
        """Mark notification as acknowledged by recipient."""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.save()


class BreachNotificationManager:
    """
    Manager for data breach notification operations.
    
    Provides methods for creating, sending, and tracking
    breach notifications according to compliance requirements.
    """
    
    @staticmethod
    def create_incident(
        category: BreachCategory,
        title: str,
        description: str,
        discovered_at: datetime,
        reported_by: User,
        **kwargs
    ) -> DataBreachIncident:
        """Create a new breach incident."""
        
        incident = DataBreachIncident.objects.create(
            category=category,
            title=title,
            description=description,
            discovered_at=discovered_at,
            reported_by=reported_by,
            **kwargs
        )
        
        # Trigger automatic response actions
        BreachNotificationManager.trigger_automatic_responses(incident)
        
        logger.info(f"Created breach incident {incident.incident_id}")
        
        return incident
    
    @staticmethod
    def trigger_automatic_responses(incident: DataBreachIncident):
        """Trigger automatic response actions for a breach incident."""
        
        for action in incident.category.automatic_response_actions:
            try:
                if action == 'disable_affected_accounts':
                    BreachNotificationManager._disable_affected_accounts(incident)
                elif action == 'reset_passwords':
                    BreachNotificationManager._reset_affected_passwords(incident)
                elif action == 'notify_security_team':
                    BreachNotificationManager._notify_security_team(incident)
                elif action == 'create_incident_response_team':
                    BreachNotificationManager._create_incident_response_team(incident)
                # Add more automatic actions as needed
                
            except Exception as e:
                logger.error(f"Failed to execute automatic action '{action}' for incident {incident.incident_id}: {e}")
    
    @staticmethod
    def generate_regulatory_notifications(incident: DataBreachIncident) -> List[BreachNotification]:
        """Generate regulatory notifications for a breach incident."""
        notifications = []
        
        if not incident.category.regulatory_notification_required:
            return notifications
        
        # Generate notifications for different regulatory bodies
        regulatory_bodies = [
            {
                'name': 'Information Regulator (POPIA)',
                'contact': 'complaints@justice.gov.za',
                'template': 'breach_notification_popia'
            },
            {
                'name': 'Health Professions Council of South Africa',
                'contact': 'info@hpcsa.co.za',
                'template': 'breach_notification_hpcsa'
            },
            # Add more regulatory bodies as needed
        ]
        
        for body in regulatory_bodies:
            notification = BreachNotification.objects.create(
                incident=incident,
                notification_type='regulatory',
                recipient_name=body['name'],
                recipient_contact=body['contact'],
                delivery_method='email',
                subject=f"Data Breach Notification - {incident.incident_id}",
                message_content=BreachNotificationManager._generate_regulatory_message(incident, body),
                template_used=body['template'],
                scheduled_send_time=timezone.now()
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def generate_patient_notifications(incident: DataBreachIncident) -> List[BreachNotification]:
        """Generate patient notifications for a breach incident."""
        notifications = []
        
        if not incident.category.patient_notification_required:
            return notifications
        
        # Get affected patients (this would integrate with your patient data system)
        affected_patients = BreachNotificationManager._get_affected_patients(incident)
        
        for patient in affected_patients:
            # Determine preferred contact method
            contact_method = BreachNotificationManager._get_patient_preferred_contact_method(patient)
            
            notification = BreachNotification.objects.create(
                incident=incident,
                notification_type='patient',
                recipient_name=f"{patient.first_name} {patient.last_name}",
                recipient_contact=patient.email if contact_method == 'email' else patient.phone,
                delivery_method=contact_method,
                subject="Important: Data Security Incident Notification",
                message_content=BreachNotificationManager._generate_patient_message(incident, patient),
                template_used='breach_notification_patient',
                scheduled_send_time=timezone.now()
            )
            notifications.append(notification)
        
        return notifications
    
    @staticmethod
    def send_pending_notifications():
        """Send all pending notifications that are due."""
        pending_notifications = BreachNotification.objects.filter(
            status='pending',
            scheduled_send_time__lte=timezone.now()
        )
        
        sent_count = 0
        failed_count = 0
        
        for notification in pending_notifications:
            try:
                notification.send_notification()
                sent_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to send notification {notification.id}: {e}")
        
        logger.info(f"Sent {sent_count} breach notifications, {failed_count} failed")
        
        return {'sent': sent_count, 'failed': failed_count}
    
    @staticmethod
    def check_overdue_notifications() -> List[Dict[str, Any]]:
        """Check for overdue notifications and return violations."""
        overdue_incidents = []
        
        active_incidents = DataBreachIncident.objects.filter(
            status__in=['reported', 'investigating', 'confirmed', 'contained'],
            is_confirmed_breach=True
        )
        
        for incident in active_incidents:
            violations = []
            
            if incident.is_notification_overdue('regulatory'):
                violations.append({
                    'type': 'regulatory',
                    'deadline': incident.get_notification_deadlines().get('regulatory'),
                    'overdue_by': timezone.now() - incident.get_notification_deadlines().get('regulatory')
                })
            
            if incident.is_notification_overdue('patient'):
                violations.append({
                    'type': 'patient',
                    'deadline': incident.get_notification_deadlines().get('patient'),
                    'overdue_by': timezone.now() - incident.get_notification_deadlines().get('patient')
                })
            
            if incident.is_notification_overdue('media'):
                violations.append({
                    'type': 'media',
                    'deadline': incident.get_notification_deadlines().get('media'),
                    'overdue_by': timezone.now() - incident.get_notification_deadlines().get('media')
                })
            
            if violations:
                overdue_incidents.append({
                    'incident': incident,
                    'violations': violations
                })
        
        return overdue_incidents
    
    @staticmethod
    def generate_breach_report() -> Dict[str, Any]:
        """Generate comprehensive breach incident report."""
        
        total_incidents = DataBreachIncident.objects.count()
        
        report = {
            'generated_at': timezone.now(),
            'total_incidents': total_incidents,
            'status_breakdown': {},
            'category_breakdown': {},
            'severity_breakdown': {},
            'notification_metrics': {},
            'compliance_metrics': {}
        }
        
        # Status breakdown
        for status, status_name in DataBreachIncident.INCIDENT_STATUS:
            count = DataBreachIncident.objects.filter(status=status).count()
            report['status_breakdown'][status] = {
                'name': status_name,
                'count': count,
                'percentage': (count / total_incidents * 100) if total_incidents > 0 else 0
            }
        
        # Category breakdown
        for category in BreachCategory.objects.filter(is_active=True):
            count = DataBreachIncident.objects.filter(category=category).count()
            report['category_breakdown'][category.breach_type] = {
                'name': category.name,
                'count': count,
                'severity_level': category.get_severity_level_display()
            }
        
        # Severity breakdown
        for severity, severity_name in BreachCategory.SEVERITY_LEVELS:
            count = DataBreachIncident.objects.filter(severity_level=severity).count()
            report['severity_breakdown'][severity] = {
                'name': severity_name,
                'count': count
            }
        
        # Notification metrics
        total_notifications = BreachNotification.objects.count()
        sent_notifications = BreachNotification.objects.filter(status='sent').count()
        delivered_notifications = BreachNotification.objects.filter(status='delivered').count()
        
        report['notification_metrics'] = {
            'total_notifications': total_notifications,
            'sent_notifications': sent_notifications,
            'delivered_notifications': delivered_notifications,
            'delivery_rate': (delivered_notifications / total_notifications * 100) if total_notifications > 0 else 0,
            'pending_notifications': BreachNotification.objects.filter(status='pending').count(),
            'failed_notifications': BreachNotification.objects.filter(status='failed').count()
        }
        
        # Compliance metrics
        confirmed_breaches = DataBreachIncident.objects.filter(is_confirmed_breach=True)
        regulatory_compliant = confirmed_breaches.filter(regulatory_notifications_sent=True).count()
        patient_compliant = confirmed_breaches.filter(patient_notifications_sent=True).count()
        
        overdue_notifications = BreachNotificationManager.check_overdue_notifications()
        
        report['compliance_metrics'] = {
            'confirmed_breaches': confirmed_breaches.count(),
            'regulatory_notification_compliance': (
                (regulatory_compliant / confirmed_breaches.count() * 100) 
                if confirmed_breaches.count() > 0 else 0
            ),
            'patient_notification_compliance': (
                (patient_compliant / confirmed_breaches.count() * 100) 
                if confirmed_breaches.count() > 0 else 0
            ),
            'overdue_notifications': len(overdue_notifications),
            'average_resolution_time_days': 0,  # Would calculate from incident timestamps
            'incidents_last_30_days': DataBreachIncident.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count()
        }
        
        return report
    
    # Helper methods
    
    @staticmethod
    def _disable_affected_accounts(incident: DataBreachIncident):
        """Disable accounts affected by the breach."""
        # Implementation would depend on your user management system
        logger.info(f"Disabling affected accounts for incident {incident.incident_id}")
    
    @staticmethod
    def _reset_affected_passwords(incident: DataBreachIncident):
        """Reset passwords for affected accounts."""
        # Implementation would depend on your authentication system
        logger.info(f"Resetting passwords for incident {incident.incident_id}")
    
    @staticmethod
    def _notify_security_team(incident: DataBreachIncident):
        """Notify security team of the incident."""
        # Implementation would send notifications to security team
        logger.info(f"Notifying security team of incident {incident.incident_id}")
    
    @staticmethod
    def _create_incident_response_team(incident: DataBreachIncident):
        """Create incident response team for the breach."""
        # Implementation would set up incident response team
        logger.info(f"Creating incident response team for {incident.incident_id}")
    
    @staticmethod
    def _get_affected_patients(incident: DataBreachIncident) -> List[User]:
        """Get list of patients affected by the breach."""
        # This would integrate with your patient data system
        # Return affected patients based on incident details
        return []
    
    @staticmethod
    def _get_patient_preferred_contact_method(patient: User) -> str:
        """Get patient's preferred contact method."""
        # This would check patient preferences
        # Default to email for now
        return 'email'
    
    @staticmethod
    def _generate_regulatory_message(incident: DataBreachIncident, regulatory_body: Dict) -> str:
        """Generate message content for regulatory notification."""
        try:
            return render_to_string(f'privacy/notifications/{regulatory_body["template"]}.txt', {
                'incident': incident,
                'regulatory_body': regulatory_body
            })
        except:
            # Fallback to basic template
            return f"""
Data Breach Notification - {incident.incident_id}

Dear {regulatory_body['name']},

We are writing to notify you of a data security incident that occurred at MedGuard SA.

Incident Details:
- Incident ID: {incident.incident_id}
- Discovery Date: {incident.discovered_at}
- Breach Type: {incident.category.get_breach_type_display()}
- Severity: {incident.get_severity_level_display()}
- Estimated Affected Patients: {incident.estimated_affected_patients}

Description: {incident.description}

We are taking this matter seriously and have implemented immediate containment measures.

Sincerely,
MedGuard SA Privacy Officer
            """
    
    @staticmethod
    def _generate_patient_message(incident: DataBreachIncident, patient: User) -> str:
        """Generate message content for patient notification."""
        try:
            return render_to_string('privacy/notifications/breach_notification_patient.txt', {
                'incident': incident,
                'patient': patient
            })
        except:
            # Fallback to basic template
            return f"""
Dear {patient.first_name} {patient.last_name},

We are writing to inform you of a data security incident that may have affected your personal health information at MedGuard SA.

What Happened: {incident.description}

What Information Was Involved: {', '.join(incident.affected_data_types)}

What We Are Doing: We have taken immediate steps to secure our systems and are working with cybersecurity experts and law enforcement as appropriate.

What You Can Do: We recommend that you monitor your accounts and report any suspicious activity.

We sincerely apologize for this incident and any inconvenience it may cause.

If you have questions, please contact us at privacy@medguard.co.za

Sincerely,
MedGuard SA Privacy Team
            """