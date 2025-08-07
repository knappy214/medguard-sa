"""
HIPAA Compliance Models
Models for HIPAA compliance monitoring, audit trails, and breach management.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet

User = get_user_model()


class PHIAccessReason(models.TextChoices):
    """Choices for PHI access reasons."""
    TREATMENT = 'treatment', _('Treatment')
    PAYMENT = 'payment', _('Payment')
    OPERATIONS = 'operations', _('Healthcare Operations')
    RESEARCH = 'research', _('Research')
    EMERGENCY = 'emergency', _('Emergency')
    LEGAL = 'legal', _('Legal Requirement')
    PATIENT_REQUEST = 'patient_request', _('Patient Request')
    ADMINISTRATIVE = 'administrative', _('Administrative')


class ComplianceStatus(models.TextChoices):
    """Choices for compliance status."""
    COMPLIANT = 'compliant', _('Compliant')
    NON_COMPLIANT = 'non_compliant', _('Non-Compliant')
    UNDER_REVIEW = 'under_review', _('Under Review')
    REMEDIATED = 'remediated', _('Remediated')


@register_snippet
class PHIAccessLog(models.Model):
    """Model for logging access to Protected Health Information."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Access details
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="phi_access_logs",
        verbose_name=_("Patient")
    )
    
    # Access information
    access_reason = models.CharField(
        max_length=20,
        choices=PHIAccessReason.choices,
        verbose_name=_("Access Reason")
    )
    
    resource_type = models.CharField(
        max_length=100,
        verbose_name=_("Resource Type"),
        help_text=_("Type of PHI accessed (e.g., medical_record, prescription)")
    )
    
    resource_id = models.CharField(
        max_length=255,
        verbose_name=_("Resource ID"),
        help_text=_("ID of the specific resource accessed")
    )
    
    action_performed = models.CharField(
        max_length=50,
        choices=[
            ('view', _('View')),
            ('create', _('Create')),
            ('update', _('Update')),
            ('delete', _('Delete')),
            ('export', _('Export')),
            ('print', _('Print')),
            ('share', _('Share')),
        ],
        verbose_name=_("Action Performed")
    )
    
    # Technical details
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP Address")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent")
    )
    
    session_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Session ID")
    )
    
    # Timestamps
    accessed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Accessed At")
    )
    
    session_duration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Session Duration (seconds)"
    )
    
    # Additional context
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Department")
    )
    
    facility = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Facility")
    )
    
    justification = models.TextField(
        blank=True,
        verbose_name=_("Access Justification")
    )
    
    # Compliance flags
    is_authorized = models.BooleanField(
        default=True,
        verbose_name=_("Authorized Access")
    )
    
    requires_review = models.BooleanField(
        default=False,
        verbose_name=_("Requires Review")
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_phi_accesses",
        verbose_name=_("Reviewed By")
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )
    
    class Meta:
        verbose_name = _("PHI Access Log")
        verbose_name_plural = _("PHI Access Logs")
        ordering = ["-accessed_at"]
        indexes = [
            models.Index(fields=['user', 'accessed_at']),
            models.Index(fields=['patient', 'accessed_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['requires_review']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} accessed {self.patient.get_full_name()}'s {self.resource_type}"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("user"),
            FieldPanel("patient"),
            FieldPanel("access_reason"),
        ], heading=_("Access Details")),
        
        MultiFieldPanel([
            FieldPanel("resource_type"),
            FieldPanel("resource_id"),
            FieldPanel("action_performed"),
        ], heading=_("Resource Information")),
        
        MultiFieldPanel([
            FieldPanel("ip_address"),
            FieldPanel("department"),
            FieldPanel("facility"),
            FieldPanel("justification"),
        ], heading=_("Context")),
        
        MultiFieldPanel([
            FieldPanel("is_authorized"),
            FieldPanel("requires_review"),
            FieldPanel("reviewed_by"),
            FieldPanel("reviewed_at"),
        ], heading=_("Compliance")),
    ]


@register_snippet
class BreachIncident(models.Model):
    """Model for tracking potential HIPAA breach incidents."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Incident details
    incident_title = models.CharField(
        max_length=255,
        verbose_name=_("Incident Title")
    )
    
    description = RichTextField(
        verbose_name=_("Incident Description")
    )
    
    incident_type = models.CharField(
        max_length=50,
        choices=[
            ('unauthorized_access', _('Unauthorized Access')),
            ('data_theft', _('Data Theft')),
            ('accidental_disclosure', _('Accidental Disclosure')),
            ('system_breach', _('System Breach')),
            ('lost_device', _('Lost Device')),
            ('malware', _('Malware/Ransomware')),
            ('insider_threat', _('Insider Threat')),
            ('vendor_breach', _('Vendor Breach')),
            ('other', _('Other')),
        ],
        verbose_name=_("Incident Type")
    )
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
            ('critical', _('Critical')),
        ],
        verbose_name=_("Severity Level")
    )
    
    # Affected data
    affected_patients_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Number of Affected Patients")
    )
    
    affected_records_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Number of Affected Records")
    )
    
    data_types_involved = models.JSONField(
        default=list,
        verbose_name=_("Types of Data Involved"),
        help_text=_("Types of PHI involved in the incident")
    )
    
    # Timeline
    discovered_at = models.DateTimeField(
        verbose_name=_("Discovered At")
    )
    
    incident_occurred_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Incident Occurred At"),
        help_text=_("When the incident actually occurred (if known)")
    )
    
    # Reporting
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Reported By")
    )
    
    reported_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Reported At")
    )
    
    # Investigation
    assigned_investigator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_breach_investigations",
        verbose_name=_("Assigned Investigator")
    )
    
    investigation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('in_progress', _('In Progress')),
            ('completed', _('Completed')),
            ('closed', _('Closed')),
        ],
        default='pending',
        verbose_name=_("Investigation Status")
    )
    
    investigation_notes = RichTextField(
        blank=True,
        verbose_name=_("Investigation Notes")
    )
    
    # Risk assessment
    risk_assessment = RichTextField(
        blank=True,
        verbose_name=_("Risk Assessment")
    )
    
    likelihood_of_compromise = models.CharField(
        max_length=20,
        choices=[
            ('low', _('Low')),
            ('medium', _('Medium')),
            ('high', _('High')),
        ],
        blank=True,
        verbose_name=_("Likelihood of Compromise")
    )
    
    # Regulatory requirements
    requires_hhs_notification = models.BooleanField(
        default=False,
        verbose_name=_("Requires HHS Notification"),
        help_text=_("Must be reported to HHS within 60 days")
    )
    
    requires_patient_notification = models.BooleanField(
        default=False,
        verbose_name=_("Requires Patient Notification"),
        help_text=_("Patients must be notified within 60 days")
    )
    
    requires_media_notification = models.BooleanField(
        default=False,
        verbose_name=_("Requires Media Notification"),
        help_text=_("Required if breach affects 500+ individuals")
    )
    
    # Notifications sent
    hhs_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("HHS Notified At")
    )
    
    patients_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Patients Notified At")
    )
    
    media_notified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Media Notified At")
    )
    
    # Remediation
    remediation_actions = RichTextField(
        blank=True,
        verbose_name=_("Remediation Actions")
    )
    
    remediation_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Remediation Completed At")
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', _('Open')),
            ('under_investigation', _('Under Investigation')),
            ('remediated', _('Remediated')),
            ('closed', _('Closed')),
        ],
        default='open',
        verbose_name=_("Status")
    )
    
    class Meta:
        verbose_name = _("Breach Incident")
        verbose_name_plural = _("Breach Incidents")
        ordering = ["-discovered_at"]
        indexes = [
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['discovered_at']),
            models.Index(fields=['requires_hhs_notification']),
        ]
    
    def __str__(self):
        return f"{self.incident_title} ({self.get_severity_display()})"
    
    @property
    def is_reportable_breach(self):
        """Determine if this is a reportable breach (affects 500+ individuals)."""
        return self.affected_patients_count >= 500
    
    panels = [
        MultiFieldPanel([
            FieldPanel("incident_title"),
            FieldPanel("description"),
            FieldPanel("incident_type"),
            FieldPanel("severity"),
        ], heading=_("Incident Details")),
        
        MultiFieldPanel([
            FieldPanel("affected_patients_count"),
            FieldPanel("affected_records_count"),
            FieldPanel("data_types_involved"),
        ], heading=_("Affected Data")),
        
        MultiFieldPanel([
            FieldPanel("discovered_at"),
            FieldPanel("incident_occurred_at"),
            FieldPanel("reported_by"),
        ], heading=_("Timeline")),
        
        MultiFieldPanel([
            FieldPanel("assigned_investigator"),
            FieldPanel("investigation_status"),
            FieldPanel("investigation_notes"),
        ], heading=_("Investigation")),
        
        MultiFieldPanel([
            FieldPanel("requires_hhs_notification"),
            FieldPanel("requires_patient_notification"),
            FieldPanel("requires_media_notification"),
        ], heading=_("Notification Requirements")),
        
        MultiFieldPanel([
            FieldPanel("hhs_notified_at"),
            FieldPanel("patients_notified_at"),
            FieldPanel("media_notified_at"),
        ], heading=_("Notifications Sent")),
        
        MultiFieldPanel([
            FieldPanel("remediation_actions"),
            FieldPanel("remediation_completed_at"),
            FieldPanel("status"),
        ], heading=_("Remediation")),
    ]


@register_snippet
class ComplianceAssessment(models.Model):
    """Model for HIPAA compliance assessments and audits."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Assessment details
    assessment_name = models.CharField(
        max_length=255,
        verbose_name=_("Assessment Name")
    )
    
    assessment_type = models.CharField(
        max_length=50,
        choices=[
            ('internal_audit', _('Internal Audit')),
            ('external_audit', _('External Audit')),
            ('self_assessment', _('Self Assessment')),
            ('risk_assessment', _('Risk Assessment')),
            ('security_assessment', _('Security Assessment')),
            ('privacy_assessment', _('Privacy Assessment')),
        ],
        verbose_name=_("Assessment Type")
    )
    
    scope = RichTextField(
        verbose_name=_("Assessment Scope")
    )
    
    # Timeline
    start_date = models.DateField(
        verbose_name=_("Start Date")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date")
    )
    
    # Personnel
    conducted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Conducted By")
    )
    
    assessor_organization = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Assessor Organization")
    )
    
    # Results
    overall_compliance_score = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name=_("Overall Compliance Score (%)")
    )
    
    compliance_status = models.CharField(
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.UNDER_REVIEW,
        verbose_name=_("Compliance Status")
    )
    
    # Findings
    findings = RichTextField(
        blank=True,
        verbose_name=_("Assessment Findings")
    )
    
    recommendations = RichTextField(
        blank=True,
        verbose_name=_("Recommendations")
    )
    
    areas_of_concern = models.JSONField(
        default=list,
        verbose_name=_("Areas of Concern")
    )
    
    # Follow-up
    corrective_actions_required = models.BooleanField(
        default=False,
        verbose_name=_("Corrective Actions Required")
    )
    
    corrective_action_plan = RichTextField(
        blank=True,
        verbose_name=_("Corrective Action Plan")
    )
    
    next_assessment_due = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Next Assessment Due")
    )
    
    # Documentation
    report_file = models.FileField(
        upload_to='hipaa_assessments/',
        blank=True,
        verbose_name=_("Assessment Report")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    class Meta:
        verbose_name = _("Compliance Assessment")
        verbose_name_plural = _("Compliance Assessments")
        ordering = ["-start_date"]
    
    def __str__(self):
        return f"{self.assessment_name} ({self.start_date})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("assessment_name"),
            FieldPanel("assessment_type"),
            FieldPanel("scope"),
        ], heading=_("Assessment Details")),
        
        MultiFieldPanel([
            FieldPanel("start_date"),
            FieldPanel("end_date"),
            FieldPanel("conducted_by"),
            FieldPanel("assessor_organization"),
        ], heading=_("Assessment Information")),
        
        MultiFieldPanel([
            FieldPanel("overall_compliance_score"),
            FieldPanel("compliance_status"),
            FieldPanel("findings"),
            FieldPanel("recommendations"),
        ], heading=_("Results")),
        
        MultiFieldPanel([
            FieldPanel("corrective_actions_required"),
            FieldPanel("corrective_action_plan"),
            FieldPanel("next_assessment_due"),
        ], heading=_("Follow-up")),
        
        FieldPanel("report_file"),
    ]
