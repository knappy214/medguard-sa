# -*- coding: utf-8 -*-
"""
MedGuard SA - Wagtail Privacy Management Module

Implements comprehensive privacy features using Wagtail 7.0.2's enhanced privacy capabilities
for healthcare data compliance (GDPR, POPIA, HIPAA).
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet

logger = logging.getLogger(__name__)
User = get_user_model()


# ============================================================================
# 1. ENHANCED DATA RETENTION POLICIES FOR MEDICAL RECORDS
# ============================================================================

@register_snippet
class MedicalDataRetentionPolicy(models.Model):
    """
    Enhanced data retention policies for medical records using Wagtail 7.0.2 features.
    
    Defines retention periods, automatic deletion schedules, and compliance requirements
    for different types of medical data in accordance with healthcare regulations.
    """
    
    # Retention policy types for different medical data categories
    RETENTION_TYPES = [
        ('prescription', _('Prescription Records')),
        ('medication_history', _('Medication History')),
        ('patient_profile', _('Patient Profile Data')),
        ('consultation_notes', _('Consultation Notes')),
        ('diagnostic_data', _('Diagnostic Data')),
        ('treatment_plans', _('Treatment Plans')),
        ('billing_records', _('Billing Records')),
        ('consent_records', _('Consent Records')),
        ('audit_logs', _('Audit Logs')),
        ('communication_logs', _('Communication Logs')),
    ]
    
    # Compliance frameworks
    COMPLIANCE_FRAMEWORKS = [
        ('popia', _('Protection of Personal Information Act (POPIA)')),
        ('gdpr', _('General Data Protection Regulation (GDPR)')),
        ('hipaa', _('Health Insurance Portability and Accountability Act (HIPAA)')),
        ('custom', _('Custom Healthcare Compliance')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Policy Name"),
        help_text=_("Descriptive name for this retention policy")
    )
    
    data_type = models.CharField(
        max_length=50,
        choices=RETENTION_TYPES,
        verbose_name=_("Data Type"),
        help_text=_("Type of medical data this policy applies to")
    )
    
    compliance_framework = models.CharField(
        max_length=20,
        choices=COMPLIANCE_FRAMEWORKS,
        default='popia',
        verbose_name=_("Compliance Framework"),
        help_text=_("Legal framework this policy complies with")
    )
    
    retention_period_days = models.PositiveIntegerField(
        verbose_name=_("Retention Period (Days)"),
        help_text=_("Number of days to retain this data type")
    )
    
    grace_period_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Grace Period (Days)"),
        help_text=_("Additional days before automatic deletion")
    )
    
    auto_delete_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enable Automatic Deletion"),
        help_text=_("Automatically delete data after retention period expires")
    )
    
    require_manual_review = models.BooleanField(
        default=False,
        verbose_name=_("Require Manual Review"),
        help_text=_("Require manual approval before deletion")
    )
    
    notification_days_before = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Notification Days Before Deletion"),
        help_text=_("Days before deletion to send notifications")
    )
    
    legal_basis = models.TextField(
        verbose_name=_("Legal Basis"),
        help_text=_("Legal justification for this retention policy"),
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('data_type'),
            FieldPanel('compliance_framework'),
        ], heading=_("Policy Identification")),
        
        MultiFieldPanel([
            FieldPanel('retention_period_days'),
            FieldPanel('grace_period_days'),
            FieldPanel('notification_days_before'),
        ], heading=_("Retention Periods")),
        
        MultiFieldPanel([
            FieldPanel('auto_delete_enabled'),
            FieldPanel('require_manual_review'),
            FieldPanel('is_active'),
        ], heading=_("Deletion Settings")),
        
        FieldPanel('legal_basis'),
    ]
    
    class Meta:
        verbose_name = _("Medical Data Retention Policy")
        verbose_name_plural = _("Medical Data Retention Policies")
        unique_together = ['data_type', 'compliance_framework']
    
    def __str__(self):
        return f"{self.name} ({self.get_data_type_display()})"
    
    def clean(self):
        """Validate retention policy settings."""
        super().clean()
        
        if self.retention_period_days < 1:
            raise ValidationError(_("Retention period must be at least 1 day"))
        
        if self.grace_period_days < 0:
            raise ValidationError(_("Grace period cannot be negative"))
        
        if self.notification_days_before > self.retention_period_days:
            raise ValidationError(
                _("Notification period cannot exceed retention period")
            )
    
    def get_total_retention_days(self) -> int:
        """Calculate total retention period including grace period."""
        return self.retention_period_days + self.grace_period_days
    
    def get_deletion_date(self, creation_date: datetime) -> datetime:
        """Calculate when data should be deleted based on creation date."""
        return creation_date + timedelta(days=self.get_total_retention_days())
    
    def get_notification_date(self, creation_date: datetime) -> datetime:
        """Calculate when deletion notification should be sent."""
        deletion_date = self.get_deletion_date(creation_date)
        return deletion_date - timedelta(days=self.notification_days_before)
    
    def is_due_for_deletion(self, creation_date: datetime) -> bool:
        """Check if data created on given date is due for deletion."""
        return timezone.now() >= self.get_deletion_date(creation_date)
    
    def is_due_for_notification(self, creation_date: datetime) -> bool:
        """Check if deletion notification should be sent for data."""
        return timezone.now() >= self.get_notification_date(creation_date)


class DataRetentionMixin(models.Model):
    """
    Mixin to add data retention capabilities to medical record models.
    
    Provides automatic retention policy enforcement and deletion tracking
    for models containing medical data.
    """
    
    retention_policy = models.ForeignKey(
        MedicalDataRetentionPolicy,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Retention Policy"),
        help_text=_("Data retention policy for this record")
    )
    
    retention_override_reason = models.TextField(
        blank=True,
        verbose_name=_("Retention Override Reason"),
        help_text=_("Reason for overriding automatic retention policy")
    )
    
    deletion_scheduled_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled Deletion Date"),
        help_text=_("When this record is scheduled for deletion")
    )
    
    deletion_notification_sent = models.BooleanField(
        default=False,
        verbose_name=_("Deletion Notification Sent"),
        help_text=_("Whether deletion notification has been sent")
    )
    
    manual_review_required = models.BooleanField(
        default=False,
        verbose_name=_("Manual Review Required"),
        help_text=_("Record requires manual review before deletion")
    )
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Override save to set retention policy and deletion schedule."""
        super().save(*args, **kwargs)
        
        if self.retention_policy and not self.deletion_scheduled_date:
            self.deletion_scheduled_date = self.retention_policy.get_deletion_date(
                self.created_at if hasattr(self, 'created_at') else timezone.now()
            )
            self.manual_review_required = self.retention_policy.require_manual_review
            # Save again to update deletion schedule
            super().save(update_fields=[
                'deletion_scheduled_date', 
                'manual_review_required'
            ])
    
    def is_due_for_deletion(self) -> bool:
        """Check if this record is due for deletion."""
        if not self.deletion_scheduled_date:
            return False
        return timezone.now() >= self.deletion_scheduled_date
    
    def is_due_for_notification(self) -> bool:
        """Check if deletion notification should be sent."""
        if not self.retention_policy or self.deletion_notification_sent:
            return False
        
        creation_date = self.created_at if hasattr(self, 'created_at') else timezone.now()
        return self.retention_policy.is_due_for_notification(creation_date)
    
    def extend_retention(self, additional_days: int, reason: str):
        """Extend retention period for this record."""
        if self.deletion_scheduled_date:
            self.deletion_scheduled_date += timedelta(days=additional_days)
            self.retention_override_reason = reason
            self.save(update_fields=[
                'deletion_scheduled_date', 
                'retention_override_reason'
            ])
            
            logger.info(
                f"Extended retention for {self._meta.label} ID {self.pk} "
                f"by {additional_days} days. Reason: {reason}"
            )


class RetentionPolicyManager:
    """
    Manager class for handling data retention policy operations.
    
    Provides methods for policy enforcement, deletion scheduling,
    and compliance reporting.
    """
    
    @staticmethod
    def get_policy_for_model(model_class, compliance_framework: str = 'popia') -> Optional[MedicalDataRetentionPolicy]:
        """Get appropriate retention policy for a model class."""
        # Map model classes to data types
        model_to_data_type = {
            'Prescription': 'prescription',
            'MedicationHistory': 'medication_history',
            'Patient': 'patient_profile',
            'ConsultationNote': 'consultation_notes',
            # Add more mappings as needed
        }
        
        model_name = model_class.__name__
        data_type = model_to_data_type.get(model_name)
        
        if not data_type:
            logger.warning(f"No data type mapping found for model {model_name}")
            return None
        
        try:
            return MedicalDataRetentionPolicy.objects.get(
                data_type=data_type,
                compliance_framework=compliance_framework,
                is_active=True
            )
        except MedicalDataRetentionPolicy.DoesNotExist:
            logger.warning(
                f"No retention policy found for {data_type} "
                f"under {compliance_framework} framework"
            )
            return None
    
    @staticmethod
    def get_records_due_for_deletion(model_class) -> List[Any]:
        """Get records from a model that are due for deletion."""
        if not hasattr(model_class, 'deletion_scheduled_date'):
            return []
        
        return model_class.objects.filter(
            deletion_scheduled_date__lte=timezone.now(),
            manual_review_required=False
        )
    
    @staticmethod
    def get_records_due_for_notification(model_class) -> List[Any]:
        """Get records that need deletion notifications sent."""
        if not hasattr(model_class, 'deletion_notification_sent'):
            return []
        
        records = []
        for record in model_class.objects.filter(deletion_notification_sent=False):
            if record.is_due_for_notification():
                records.append(record)
        
        return records
    
    @staticmethod
    def generate_retention_report() -> Dict[str, Any]:
        """Generate comprehensive retention policy compliance report."""
        report = {
            'generated_at': timezone.now(),
            'active_policies': MedicalDataRetentionPolicy.objects.filter(is_active=True).count(),
            'compliance_frameworks': {},
            'policy_details': []
        }
        
        # Group by compliance framework
        for framework, framework_name in MedicalDataRetentionPolicy.COMPLIANCE_FRAMEWORKS:
            policies = MedicalDataRetentionPolicy.objects.filter(
                compliance_framework=framework,
                is_active=True
            )
            
            report['compliance_frameworks'][framework] = {
                'name': framework_name,
                'policy_count': policies.count(),
                'data_types_covered': list(policies.values_list('data_type', flat=True))
            }
        
        # Policy details
        for policy in MedicalDataRetentionPolicy.objects.filter(is_active=True):
            report['policy_details'].append({
                'name': policy.name,
                'data_type': policy.get_data_type_display(),
                'framework': policy.get_compliance_framework_display(),
                'retention_days': policy.retention_period_days,
                'auto_delete': policy.auto_delete_enabled,
                'manual_review': policy.require_manual_review
            })
        
        return report


# ============================================================================
# 2. IMPROVED CONSENT MANAGEMENT FOR PATIENT DATA USAGE
# ============================================================================

@register_snippet
class ConsentCategory(models.Model):
    """
    Categories of consent for different types of patient data usage.
    
    Defines granular consent categories that patients can control individually,
    supporting Wagtail 7.0.2's enhanced consent management features.
    """
    
    CONSENT_TYPES = [
        ('data_processing', _('Data Processing')),
        ('medical_research', _('Medical Research')),
        ('marketing_communications', _('Marketing Communications')),
        ('data_sharing_partners', _('Data Sharing with Partners')),
        ('analytics_tracking', _('Analytics and Tracking')),
        ('emergency_access', _('Emergency Access')),
        ('telemedicine', _('Telemedicine Services')),
        ('ai_analysis', _('AI-Powered Analysis')),
        ('quality_improvement', _('Quality Improvement')),
        ('billing_insurance', _('Billing and Insurance')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Category Name"),
        help_text=_("Human-readable name for this consent category")
    )
    
    consent_type = models.CharField(
        max_length=50,
        choices=CONSENT_TYPES,
        unique=True,
        verbose_name=_("Consent Type"),
        help_text=_("Type of consent this category represents")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of what this consent allows")
    )
    
    purpose = models.TextField(
        verbose_name=_("Purpose"),
        help_text=_("Legal purpose for collecting this consent")
    )
    
    legal_basis = models.CharField(
        max_length=100,
        verbose_name=_("Legal Basis"),
        help_text=_("Legal basis for processing under GDPR/POPIA")
    )
    
    is_essential = models.BooleanField(
        default=False,
        verbose_name=_("Essential for Service"),
        help_text=_("Whether consent is essential for providing medical services")
    )
    
    withdrawal_allowed = models.BooleanField(
        default=True,
        verbose_name=_("Withdrawal Allowed"),
        help_text=_("Whether patients can withdraw this consent")
    )
    
    retention_period_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Consent Retention Period (Days)"),
        help_text=_("How long to retain consent records (leave blank for indefinite)")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('consent_type'),
            FieldPanel('description'),
        ], heading=_("Category Information")),
        
        MultiFieldPanel([
            FieldPanel('purpose'),
            FieldPanel('legal_basis'),
            FieldPanel('retention_period_days'),
        ], heading=_("Legal Basis")),
        
        MultiFieldPanel([
            FieldPanel('is_essential'),
            FieldPanel('withdrawal_allowed'),
            FieldPanel('is_active'),
        ], heading=_("Consent Properties")),
    ]
    
    class Meta:
        verbose_name = _("Consent Category")
        verbose_name_plural = _("Consent Categories")
        ordering = ['name']
    
    def __str__(self):
        return self.name


@register_snippet
class ConsentTemplate(models.Model):
    """
    Templates for consent forms with versioning support.
    
    Provides versioned consent templates that can be customized for
    different patient groups or regulatory requirements.
    """
    
    TEMPLATE_TYPES = [
        ('general_medical', _('General Medical Consent')),
        ('research_participation', _('Research Participation')),
        ('data_sharing', _('Data Sharing Consent')),
        ('marketing_opt_in', _('Marketing Opt-in')),
        ('telemedicine', _('Telemedicine Consent')),
        ('minor_consent', _('Minor Patient Consent')),
        ('emergency_contact', _('Emergency Contact Consent')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Template Name")
    )
    
    template_type = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPES,
        verbose_name=_("Template Type")
    )
    
    version = models.CharField(
        max_length=20,
        verbose_name=_("Version"),
        help_text=_("Version number (e.g., 1.0, 1.1)")
    )
    
    content_en = models.TextField(
        verbose_name=_("Content (English)"),
        help_text=_("Consent form content in English")
    )
    
    content_af = models.TextField(
        blank=True,
        verbose_name=_("Content (Afrikaans)"),
        help_text=_("Consent form content in Afrikaans")
    )
    
    categories = models.ManyToManyField(
        ConsentCategory,
        verbose_name=_("Consent Categories"),
        help_text=_("Categories of consent covered by this template")
    )
    
    effective_date = models.DateTimeField(
        verbose_name=_("Effective Date"),
        help_text=_("When this template version becomes effective")
    )
    
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expiry Date"),
        help_text=_("When this template version expires (optional)")
    )
    
    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Current Version"),
        help_text=_("Whether this is the current version of the template")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Created By")
    )
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('template_type'),
            FieldPanel('version'),
        ], heading=_("Template Information")),
        
        MultiFieldPanel([
            FieldPanel('content_en'),
            FieldPanel('content_af'),
        ], heading=_("Content")),
        
        FieldPanel('categories'),
        
        MultiFieldPanel([
            FieldPanel('effective_date'),
            FieldPanel('expiry_date'),
            FieldPanel('is_current'),
        ], heading=_("Version Control")),
    ]
    
    class Meta:
        verbose_name = _("Consent Template")
        verbose_name_plural = _("Consent Templates")
        unique_together = ['template_type', 'version']
        ordering = ['-effective_date', '-version']
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    def clean(self):
        """Validate template settings."""
        super().clean()
        
        if self.expiry_date and self.expiry_date <= self.effective_date:
            raise ValidationError(_("Expiry date must be after effective date"))
    
    def save(self, *args, **kwargs):
        """Override save to manage current version flags."""
        if self.is_current:
            # Ensure only one current version per template type
            ConsentTemplate.objects.filter(
                template_type=self.template_type,
                is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        
        super().save(*args, **kwargs)
    
    def is_effective(self) -> bool:
        """Check if template is currently effective."""
        now = timezone.now()
        if now < self.effective_date:
            return False
        if self.expiry_date and now > self.expiry_date:
            return False
        return True


class PatientConsent(models.Model):
    """
    Individual patient consent records with granular control.
    
    Tracks patient consent for different categories with full audit trail
    and withdrawal capabilities.
    """
    
    CONSENT_STATUS = [
        ('given', _('Consent Given')),
        ('withdrawn', _('Consent Withdrawn')),
        ('expired', _('Consent Expired')),
        ('pending', _('Consent Pending')),
        ('declined', _('Consent Declined')),
    ]
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Patient"),
        related_name='consent_records'
    )
    
    category = models.ForeignKey(
        ConsentCategory,
        on_delete=models.CASCADE,
        verbose_name=_("Consent Category")
    )
    
    template = models.ForeignKey(
        ConsentTemplate,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Consent Template"),
        help_text=_("Template used when consent was given")
    )
    
    status = models.CharField(
        max_length=20,
        choices=CONSENT_STATUS,
        default='pending',
        verbose_name=_("Consent Status")
    )
    
    given_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Given At"),
        help_text=_("When consent was given")
    )
    
    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Withdrawn At"),
        help_text=_("When consent was withdrawn")
    )
    
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Expiry Date"),
        help_text=_("When consent expires (if applicable)")
    )
    
    withdrawal_reason = models.TextField(
        blank=True,
        verbose_name=_("Withdrawal Reason"),
        help_text=_("Reason for withdrawing consent")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address when consent was given")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Browser information when consent was given")
    )
    
    consent_evidence = models.JSONField(
        default=dict,
        verbose_name=_("Consent Evidence"),
        help_text=_("Additional evidence of consent (e.g., signature, timestamps)")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Patient Consent")
        verbose_name_plural = _("Patient Consents")
        unique_together = ['patient', 'category']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.patient} - {self.category.name} ({self.status})"
    
    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if self.status != 'given':
            return False
        
        if self.expiry_date and timezone.now() > self.expiry_date:
            # Auto-expire consent
            self.status = 'expired'
            self.save(update_fields=['status'])
            return False
        
        return True
    
    def withdraw_consent(self, reason: str = ""):
        """Withdraw consent with reason and timestamp."""
        self.status = 'withdrawn'
        self.withdrawn_at = timezone.now()
        self.withdrawal_reason = reason
        self.save(update_fields=['status', 'withdrawn_at', 'withdrawal_reason'])
        
        logger.info(
            f"Consent withdrawn for patient {self.patient.id} "
            f"in category {self.category.consent_type}. Reason: {reason}"
        )
    
    def give_consent(self, template: ConsentTemplate, evidence: Dict = None):
        """Give consent using a specific template."""
        self.status = 'given'
        self.given_at = timezone.now()
        self.template = template
        self.withdrawn_at = None
        self.withdrawal_reason = ""
        
        if evidence:
            self.consent_evidence.update(evidence)
        
        # Set expiry if category has retention period
        if self.category.retention_period_days:
            self.expiry_date = timezone.now() + timedelta(
                days=self.category.retention_period_days
            )
        
        self.save()
        
        logger.info(
            f"Consent given for patient {self.patient.id} "
            f"in category {self.category.consent_type}"
        )


class ConsentManager:
    """
    Manager class for handling consent operations and compliance checks.
    
    Provides methods for consent verification, bulk operations,
    and compliance reporting.
    """
    
    @staticmethod
    def check_patient_consent(patient: User, consent_type: str) -> bool:
        """Check if patient has valid consent for a specific type."""
        try:
            category = ConsentCategory.objects.get(
                consent_type=consent_type,
                is_active=True
            )
            
            consent = PatientConsent.objects.get(
                patient=patient,
                category=category
            )
            
            return consent.is_valid()
        
        except (ConsentCategory.DoesNotExist, PatientConsent.DoesNotExist):
            return False
    
    @staticmethod
    def get_patient_consents(patient: User) -> Dict[str, bool]:
        """Get all consent statuses for a patient."""
        consents = {}
        
        for category in ConsentCategory.objects.filter(is_active=True):
            try:
                consent = PatientConsent.objects.get(
                    patient=patient,
                    category=category
                )
                consents[category.consent_type] = consent.is_valid()
            except PatientConsent.DoesNotExist:
                consents[category.consent_type] = False
        
        return consents
    
    @staticmethod
    def create_consent_record(
        patient: User, 
        consent_type: str, 
        template_version: str = None,
        evidence: Dict = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> PatientConsent:
        """Create a new consent record for a patient."""
        try:
            category = ConsentCategory.objects.get(
                consent_type=consent_type,
                is_active=True
            )
        except ConsentCategory.DoesNotExist:
            raise ValueError(f"Invalid consent type: {consent_type}")
        
        # Get appropriate template
        template = None
        if template_version:
            try:
                template = ConsentTemplate.objects.get(
                    categories=category,
                    version=template_version,
                    is_current=True
                )
            except ConsentTemplate.DoesNotExist:
                logger.warning(f"Template version {template_version} not found")
        
        if not template:
            try:
                template = ConsentTemplate.objects.filter(
                    categories=category,
                    is_current=True
                ).first()
            except ConsentTemplate.DoesNotExist:
                logger.warning(f"No current template found for {consent_type}")
        
        # Create or update consent record
        consent, created = PatientConsent.objects.get_or_create(
            patient=patient,
            category=category,
            defaults={
                'template': template,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'consent_evidence': evidence or {}
            }
        )
        
        if not created:
            # Update existing consent
            consent.template = template
            if ip_address:
                consent.ip_address = ip_address
            if user_agent:
                consent.user_agent = user_agent
            if evidence:
                consent.consent_evidence.update(evidence)
        
        # Give consent
        consent.give_consent(template, evidence)
        
        return consent
    
    @staticmethod
    def withdraw_all_consents(patient: User, reason: str = "Patient request"):
        """Withdraw all withdrawable consents for a patient."""
        withdrawable_consents = PatientConsent.objects.filter(
            patient=patient,
            category__withdrawal_allowed=True,
            status='given'
        )
        
        for consent in withdrawable_consents:
            consent.withdraw_consent(reason)
        
        logger.info(
            f"Withdrew {withdrawable_consents.count()} consents "
            f"for patient {patient.id}. Reason: {reason}"
        )
    
    @staticmethod
    def get_expired_consents() -> List[PatientConsent]:
        """Get all consents that have expired."""
        return PatientConsent.objects.filter(
            status='given',
            expiry_date__lt=timezone.now()
        )
    
    @staticmethod
    def generate_consent_report() -> Dict[str, Any]:
        """Generate comprehensive consent compliance report."""
        total_patients = User.objects.count()
        total_consents = PatientConsent.objects.count()
        
        report = {
            'generated_at': timezone.now(),
            'total_patients': total_patients,
            'total_consents': total_consents,
            'consent_categories': {},
            'status_breakdown': {},
            'compliance_summary': {}
        }
        
        # Consent categories breakdown
        for category in ConsentCategory.objects.filter(is_active=True):
            category_consents = PatientConsent.objects.filter(category=category)
            
            report['consent_categories'][category.consent_type] = {
                'name': category.name,
                'total_consents': category_consents.count(),
                'valid_consents': category_consents.filter(status='given').count(),
                'withdrawn_consents': category_consents.filter(status='withdrawn').count(),
                'is_essential': category.is_essential,
                'withdrawal_allowed': category.withdrawal_allowed
            }
        
        # Status breakdown
        for status, status_name in PatientConsent.CONSENT_STATUS:
            report['status_breakdown'][status] = {
                'name': status_name,
                'count': PatientConsent.objects.filter(status=status).count()
            }
        
        # Compliance summary
        essential_categories = ConsentCategory.objects.filter(
            is_essential=True,
            is_active=True
        )
        
        patients_with_all_essential = 0
        for patient in User.objects.all():
            has_all_essential = True
            for category in essential_categories:
                if not ConsentManager.check_patient_consent(patient, category.consent_type):
                    has_all_essential = False
                    break
            
            if has_all_essential:
                patients_with_all_essential += 1
        
        report['compliance_summary'] = {
            'patients_with_all_essential_consents': patients_with_all_essential,
            'essential_consent_compliance_rate': (
                (patients_with_all_essential / total_patients * 100) 
                if total_patients > 0 else 0
            ),
            'expired_consents': ConsentManager.get_expired_consents().count()
        }
        
        return report


# ============================================================================
# 3. AUTOMATIC DATA ANONYMIZATION USING WAGTAIL 7.0.2'S PRIVACY FEATURES
# ============================================================================

import hashlib
import re
import random
import string
from faker import Faker

fake = Faker(['en_ZA', 'af_ZA'])  # South African locales


@register_snippet
class AnonymizationRule(models.Model):
    """
    Rules for automatic data anonymization of medical records.
    
    Defines how different types of sensitive data should be anonymized
    while preserving data utility for research and analytics.
    """
    
    FIELD_TYPES = [
        ('name', _('Personal Names')),
        ('email', _('Email Addresses')),
        ('phone', _('Phone Numbers')),
        ('id_number', _('ID Numbers')),
        ('address', _('Physical Addresses')),
        ('medical_record_number', _('Medical Record Numbers')),
        ('prescription_number', _('Prescription Numbers')),
        ('date_of_birth', _('Date of Birth')),
        ('diagnosis', _('Medical Diagnosis')),
        ('medication_name', _('Medication Names')),
        ('dosage', _('Medication Dosages')),
        ('notes', _('Clinical Notes')),
        ('custom_field', _('Custom Field')),
    ]
    
    ANONYMIZATION_METHODS = [
        ('hash', _('Hash (SHA-256)')),
        ('pseudonym', _('Pseudonymization')),
        ('masking', _('Data Masking')),
        ('generalization', _('Data Generalization')),
        ('suppression', _('Data Suppression')),
        ('synthetic', _('Synthetic Data Replacement')),
        ('date_shift', _('Date Shifting')),
        ('noise_addition', _('Noise Addition')),
        ('k_anonymity', _('K-Anonymity')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Rule Name"),
        help_text=_("Descriptive name for this anonymization rule")
    )
    
    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        verbose_name=_("Field Type"),
        help_text=_("Type of data field this rule applies to")
    )
    
    field_pattern = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Field Pattern"),
        help_text=_("Regex pattern to match field names (optional)")
    )
    
    anonymization_method = models.CharField(
        max_length=20,
        choices=ANONYMIZATION_METHODS,
        verbose_name=_("Anonymization Method"),
        help_text=_("Method to use for anonymizing this field type")
    )
    
    preserve_format = models.BooleanField(
        default=True,
        verbose_name=_("Preserve Format"),
        help_text=_("Maintain original data format (e.g., phone number structure)")
    )
    
    preserve_length = models.BooleanField(
        default=True,
        verbose_name=_("Preserve Length"),
        help_text=_("Maintain original data length")
    )
    
    k_value = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("K-Value"),
        help_text=_("K-value for k-anonymity (minimum group size)")
    )
    
    date_shift_range = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Date Shift Range (Days)"),
        help_text=_("Maximum days to shift dates (for date_shift method)")
    )
    
    custom_parameters = models.JSONField(
        default=dict,
        verbose_name=_("Custom Parameters"),
        help_text=_("Additional parameters for anonymization method")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('field_type'),
            FieldPanel('field_pattern'),
        ], heading=_("Rule Definition")),
        
        MultiFieldPanel([
            FieldPanel('anonymization_method'),
            FieldPanel('preserve_format'),
            FieldPanel('preserve_length'),
        ], heading=_("Anonymization Settings")),
        
        MultiFieldPanel([
            FieldPanel('k_value'),
            FieldPanel('date_shift_range'),
            FieldPanel('custom_parameters'),
        ], heading=_("Advanced Parameters")),
        
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = _("Anonymization Rule")
        verbose_name_plural = _("Anonymization Rules")
        unique_together = ['field_type', 'field_pattern']
    
    def __str__(self):
        return f"{self.name} ({self.get_field_type_display()})"
    
    def clean(self):
        """Validate anonymization rule settings."""
        super().clean()
        
        if self.anonymization_method == 'k_anonymity' and not self.k_value:
            raise ValidationError(_("K-value is required for k-anonymity method"))
        
        if self.anonymization_method == 'date_shift' and not self.date_shift_range:
            raise ValidationError(_("Date shift range is required for date shifting"))
        
        if self.field_pattern:
            try:
                re.compile(self.field_pattern)
            except re.error:
                raise ValidationError(_("Invalid regex pattern"))


@register_snippet
class AnonymizationProfile(models.Model):
    """
    Profiles that group anonymization rules for different use cases.
    
    Allows different anonymization strategies for research, analytics,
    data sharing, etc.
    """
    
    PROFILE_TYPES = [
        ('research', _('Medical Research')),
        ('analytics', _('Data Analytics')),
        ('data_sharing', _('External Data Sharing')),
        ('backup', _('Data Backup')),
        ('testing', _('Testing Environment')),
        ('quality_assurance', _('Quality Assurance')),
        ('compliance_audit', _('Compliance Audit')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Profile Name")
    )
    
    profile_type = models.CharField(
        max_length=50,
        choices=PROFILE_TYPES,
        verbose_name=_("Profile Type")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Purpose and scope of this anonymization profile")
    )
    
    rules = models.ManyToManyField(
        AnonymizationRule,
        verbose_name=_("Anonymization Rules"),
        help_text=_("Rules to apply in this profile")
    )
    
    anonymization_level = models.CharField(
        max_length=20,
        choices=[
            ('minimal', _('Minimal Anonymization')),
            ('standard', _('Standard Anonymization')),
            ('high', _('High Anonymization')),
            ('maximum', _('Maximum Anonymization')),
        ],
        default='standard',
        verbose_name=_("Anonymization Level")
    )
    
    preserve_relationships = models.BooleanField(
        default=True,
        verbose_name=_("Preserve Relationships"),
        help_text=_("Maintain relationships between anonymized records")
    )
    
    salt_key = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Salt Key"),
        help_text=_("Salt for hashing (auto-generated if blank)")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('profile_type'),
            FieldPanel('description'),
        ], heading=_("Profile Information")),
        
        FieldPanel('rules'),
        
        MultiFieldPanel([
            FieldPanel('anonymization_level'),
            FieldPanel('preserve_relationships'),
            FieldPanel('salt_key'),
        ], heading=_("Anonymization Settings")),
        
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = _("Anonymization Profile")
        verbose_name_plural = _("Anonymization Profiles")
    
    def __str__(self):
        return f"{self.name} ({self.get_profile_type_display()})"
    
    def save(self, *args, **kwargs):
        """Generate salt key if not provided."""
        if not self.salt_key:
            self.salt_key = ''.join(random.choices(
                string.ascii_letters + string.digits, k=32
            ))
        super().save(*args, **kwargs)


class DataAnonymizer:
    """
    Core anonymization engine that applies anonymization rules to data.
    
    Provides methods for anonymizing individual fields, records, and datasets
    according to configured rules and profiles.
    """
    
    def __init__(self, profile: AnonymizationProfile):
        """Initialize anonymizer with a specific profile."""
        self.profile = profile
        self.rules = profile.rules.filter(is_active=True)
        self.pseudonym_mapping = {}  # For consistent pseudonymization
        
    def anonymize_field(self, field_name: str, value: Any, field_type: str = None) -> Any:
        """Anonymize a single field value."""
        if value is None or value == '':
            return value
        
        # Find applicable rule
        rule = self._get_rule_for_field(field_name, field_type)
        if not rule:
            return value
        
        method = rule.anonymization_method
        
        if method == 'hash':
            return self._hash_value(value, rule)
        elif method == 'pseudonym':
            return self._pseudonymize_value(value, rule)
        elif method == 'masking':
            return self._mask_value(value, rule)
        elif method == 'generalization':
            return self._generalize_value(value, rule)
        elif method == 'suppression':
            return self._suppress_value(value, rule)
        elif method == 'synthetic':
            return self._synthetic_value(value, rule)
        elif method == 'date_shift':
            return self._shift_date(value, rule)
        elif method == 'noise_addition':
            return self._add_noise(value, rule)
        elif method == 'k_anonymity':
            return self._k_anonymize_value(value, rule)
        
        return value
    
    def anonymize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize a complete record."""
        anonymized = {}
        
        for field_name, value in record.items():
            anonymized[field_name] = self.anonymize_field(field_name, value)
        
        return anonymized
    
    def _get_rule_for_field(self, field_name: str, field_type: str = None) -> Optional[AnonymizationRule]:
        """Find the most appropriate rule for a field."""
        # First try exact field type match
        if field_type:
            rule = self.rules.filter(field_type=field_type).first()
            if rule:
                return rule
        
        # Try pattern matching
        for rule in self.rules:
            if rule.field_pattern:
                if re.search(rule.field_pattern, field_name, re.IGNORECASE):
                    return rule
        
        # Try field name inference
        field_lower = field_name.lower()
        
        if any(term in field_lower for term in ['name', 'first_name', 'last_name']):
            return self.rules.filter(field_type='name').first()
        elif any(term in field_lower for term in ['email', 'mail']):
            return self.rules.filter(field_type='email').first()
        elif any(term in field_lower for term in ['phone', 'tel', 'mobile']):
            return self.rules.filter(field_type='phone').first()
        elif any(term in field_lower for term in ['address', 'street', 'city']):
            return self.rules.filter(field_type='address').first()
        elif any(term in field_lower for term in ['birth', 'dob']):
            return self.rules.filter(field_type='date_of_birth').first()
        
        return None
    
    def _hash_value(self, value: Any, rule: AnonymizationRule) -> str:
        """Hash a value using SHA-256."""
        salt = self.profile.salt_key.encode('utf-8')
        value_str = str(value).encode('utf-8')
        hash_obj = hashlib.sha256(salt + value_str)
        
        if rule.preserve_length:
            # Truncate hash to preserve original length
            original_length = len(str(value))
            return hash_obj.hexdigest()[:original_length]
        
        return hash_obj.hexdigest()
    
    def _pseudonymize_value(self, value: Any, rule: AnonymizationRule) -> str:
        """Replace value with consistent pseudonym."""
        value_key = f"{rule.field_type}_{value}"
        
        if value_key in self.pseudonym_mapping:
            return self.pseudonym_mapping[value_key]
        
        if rule.field_type == 'name':
            pseudonym = fake.name()
        elif rule.field_type == 'email':
            pseudonym = fake.email()
        elif rule.field_type == 'phone':
            pseudonym = fake.phone_number()
        elif rule.field_type == 'address':
            pseudonym = fake.address()
        elif rule.field_type == 'medical_record_number':
            pseudonym = fake.bothify(text='MRN-#######')
        else:
            # Generic pseudonym
            pseudonym = fake.bothify(text='???-####')
        
        self.pseudonym_mapping[value_key] = pseudonym
        return pseudonym
    
    def _mask_value(self, value: Any, rule: AnonymizationRule) -> str:
        """Mask parts of the value."""
        value_str = str(value)
        
        if rule.field_type == 'email':
            # Mask email: j***@example.com
            parts = value_str.split('@')
            if len(parts) == 2:
                username = parts[0]
                domain = parts[1]
                masked_username = username[0] + '*' * (len(username) - 1)
                return f"{masked_username}@{domain}"
        
        elif rule.field_type == 'phone':
            # Mask phone: +27 ** *** ****
            if len(value_str) > 4:
                return value_str[:3] + '*' * (len(value_str) - 6) + value_str[-3:]
        
        elif rule.field_type == 'id_number':
            # Mask ID number: 12****8901234
            if len(value_str) > 6:
                return value_str[:2] + '*' * (len(value_str) - 4) + value_str[-2:]
        
        # Default masking
        if len(value_str) > 2:
            return value_str[0] + '*' * (len(value_str) - 2) + value_str[-1]
        
        return '*' * len(value_str)
    
    def _generalize_value(self, value: Any, rule: AnonymizationRule) -> str:
        """Generalize value to broader category."""
        if rule.field_type == 'date_of_birth':
            # Generalize to age range
            if isinstance(value, datetime):
                age = (timezone.now().date() - value.date()).days // 365
                if age < 18:
                    return "Under 18"
                elif age < 30:
                    return "18-29"
                elif age < 50:
                    return "30-49"
                elif age < 65:
                    return "50-64"
                else:
                    return "65+"
        
        elif rule.field_type == 'address':
            # Generalize to city/province only
            address_parts = str(value).split(',')
            if len(address_parts) >= 2:
                return address_parts[-2:][0].strip()  # City
        
        return str(value)
    
    def _suppress_value(self, value: Any, rule: AnonymizationRule) -> str:
        """Suppress (remove) sensitive value."""
        return "[REDACTED]"
    
    def _synthetic_value(self, value: Any, rule: AnonymizationRule) -> Any:
        """Replace with synthetic data of same type."""
        if rule.field_type == 'name':
            return fake.name()
        elif rule.field_type == 'email':
            return fake.email()
        elif rule.field_type == 'phone':
            return fake.phone_number()
        elif rule.field_type == 'address':
            return fake.address()
        elif rule.field_type == 'date_of_birth':
            return fake.date_of_birth()
        elif rule.field_type == 'medication_name':
            medications = ['Paracetamol', 'Ibuprofen', 'Aspirin', 'Amoxicillin']
            return random.choice(medications)
        
        return fake.word()
    
    def _shift_date(self, value: Any, rule: AnonymizationRule) -> datetime:
        """Shift date by random amount within range."""
        if not isinstance(value, (datetime, models.DateTimeField)):
            return value
        
        shift_days = random.randint(-rule.date_shift_range, rule.date_shift_range)
        return value + timedelta(days=shift_days)
    
    def _add_noise(self, value: Any, rule: AnonymizationRule) -> Any:
        """Add statistical noise to numeric values."""
        if not isinstance(value, (int, float)):
            return value
        
        noise_factor = rule.custom_parameters.get('noise_factor', 0.1)
        noise = random.uniform(-noise_factor, noise_factor) * value
        return value + noise
    
    def _k_anonymize_value(self, value: Any, rule: AnonymizationRule) -> Any:
        """Apply k-anonymity by generalizing to ensure minimum group size."""
        # This is a simplified implementation
        # In practice, k-anonymity requires analyzing the entire dataset
        return self._generalize_value(value, rule)


class AnonymizationMixin(models.Model):
    """
    Mixin to add anonymization capabilities to models.
    
    Provides methods for anonymizing model instances and
    tracking anonymization status.
    """
    
    is_anonymized = models.BooleanField(
        default=False,
        verbose_name=_("Is Anonymized"),
        help_text=_("Whether this record has been anonymized")
    )
    
    anonymization_profile = models.ForeignKey(
        AnonymizationProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Anonymization Profile"),
        help_text=_("Profile used for anonymization")
    )
    
    anonymized_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Anonymized At"),
        help_text=_("When this record was anonymized")
    )
    
    original_data_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Original Data Hash"),
        help_text=_("Hash of original data for verification")
    )
    
    class Meta:
        abstract = True
    
    def anonymize(self, profile: AnonymizationProfile, save: bool = True) -> Dict[str, Any]:
        """Anonymize this model instance."""
        anonymizer = DataAnonymizer(profile)
        
        # Create record dict from model fields
        record = {}
        for field in self._meta.fields:
            if field.name not in ['is_anonymized', 'anonymization_profile', 
                                 'anonymized_at', 'original_data_hash']:
                record[field.name] = getattr(self, field.name)
        
        # Store original data hash
        if not self.original_data_hash:
            original_str = str(sorted(record.items()))
            self.original_data_hash = hashlib.sha256(
                original_str.encode('utf-8')
            ).hexdigest()
        
        # Anonymize the record
        anonymized_record = anonymizer.anonymize_record(record)
        
        # Update model fields
        for field_name, anonymized_value in anonymized_record.items():
            if hasattr(self, field_name):
                setattr(self, field_name, anonymized_value)
        
        # Mark as anonymized
        self.is_anonymized = True
        self.anonymization_profile = profile
        self.anonymized_at = timezone.now()
        
        if save:
            self.save()
        
        logger.info(
            f"Anonymized {self._meta.label} record ID {self.pk} "
            f"using profile {profile.name}"
        )
        
        return anonymized_record
    
    def is_anonymization_valid(self) -> bool:
        """Check if anonymization is still valid."""
        if not self.is_anonymized:
            return False
        
        if not self.anonymization_profile or not self.anonymization_profile.is_active:
            return False
        
        return True


# ============================================================================
# 4. ENHANCED USER DATA EXPORT FOR GDPR/POPIA COMPLIANCE
# ============================================================================

import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO, BytesIO
import zipfile
from django.http import HttpResponse
from django.apps import apps
from django.core.serializers import serialize
from django.template.loader import render_to_string


@register_snippet
class DataExportTemplate(models.Model):
    """
    Templates for structuring data exports in different formats.
    
    Provides customizable templates for exporting patient data
    in compliance with GDPR and POPIA requirements.
    """
    
    EXPORT_FORMATS = [
        ('json', _('JSON Format')),
        ('csv', _('CSV Format')),
        ('xml', _('XML Format')),
        ('pdf', _('PDF Report')),
        ('html', _('HTML Report')),
        ('excel', _('Excel Spreadsheet')),
    ]
    
    COMPLIANCE_TYPES = [
        ('gdpr_full', _('GDPR Full Data Export')),
        ('gdpr_summary', _('GDPR Summary Export')),
        ('popia_full', _('POPIA Full Data Export')),
        ('popia_summary', _('POPIA Summary Export')),
        ('medical_records', _('Medical Records Export')),
        ('consent_history', _('Consent History Export')),
        ('audit_trail', _('Audit Trail Export')),
        ('custom', _('Custom Export')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Template Name"),
        help_text=_("Descriptive name for this export template")
    )
    
    compliance_type = models.CharField(
        max_length=50,
        choices=COMPLIANCE_TYPES,
        verbose_name=_("Compliance Type"),
        help_text=_("Type of compliance export this template supports")
    )
    
    export_format = models.CharField(
        max_length=20,
        choices=EXPORT_FORMATS,
        verbose_name=_("Export Format"),
        help_text=_("Output format for the exported data")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Purpose and contents of this export template")
    )
    
    included_models = models.JSONField(
        default=list,
        verbose_name=_("Included Models"),
        help_text=_("List of Django models to include in export")
    )
    
    excluded_fields = models.JSONField(
        default=list,
        verbose_name=_("Excluded Fields"),
        help_text=_("Fields to exclude from export for privacy/security")
    )
    
    anonymize_data = models.BooleanField(
        default=False,
        verbose_name=_("Anonymize Data"),
        help_text=_("Apply anonymization rules to exported data")
    )
    
    anonymization_profile = models.ForeignKey(
        AnonymizationProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Anonymization Profile"),
        help_text=_("Profile to use for data anonymization")
    )
    
    template_content = models.TextField(
        blank=True,
        verbose_name=_("Template Content"),
        help_text=_("Custom template for formatting exported data")
    )
    
    include_metadata = models.BooleanField(
        default=True,
        verbose_name=_("Include Metadata"),
        help_text=_("Include export metadata (timestamps, compliance info)")
    )
    
    digital_signature = models.BooleanField(
        default=False,
        verbose_name=_("Digital Signature"),
        help_text=_("Add digital signature to verify export integrity")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('compliance_type'),
            FieldPanel('export_format'),
            FieldPanel('description'),
        ], heading=_("Template Information")),
        
        MultiFieldPanel([
            FieldPanel('included_models'),
            FieldPanel('excluded_fields'),
            FieldPanel('template_content'),
        ], heading=_("Export Configuration")),
        
        MultiFieldPanel([
            FieldPanel('anonymize_data'),
            FieldPanel('anonymization_profile'),
        ], heading=_("Anonymization Settings")),
        
        MultiFieldPanel([
            FieldPanel('include_metadata'),
            FieldPanel('digital_signature'),
            FieldPanel('is_active'),
        ], heading=_("Export Options")),
    ]
    
    class Meta:
        verbose_name = _("Data Export Template")
        verbose_name_plural = _("Data Export Templates")
        unique_together = ['compliance_type', 'export_format']
    
    def __str__(self):
        return f"{self.name} ({self.get_export_format_display()})"
    
    def clean(self):
        """Validate export template settings."""
        super().clean()
        
        if self.anonymize_data and not self.anonymization_profile:
            raise ValidationError(_("Anonymization profile is required when anonymize_data is enabled"))
        
        # Validate included_models format
        if self.included_models:
            for model_path in self.included_models:
                if not isinstance(model_path, str) or '.' not in model_path:
                    raise ValidationError(_("Invalid model path format. Use 'app.ModelName'"))


class DataExportRequest(models.Model):
    """
    Individual data export requests from patients or administrators.
    
    Tracks export requests with full audit trail and compliance
    documentation for GDPR and POPIA requirements.
    """
    
    REQUEST_STATUS = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
        ('expired', _('Expired')),
    ]
    
    REQUEST_TYPES = [
        ('patient_self', _('Patient Self-Request')),
        ('patient_representative', _('Patient Representative')),
        ('legal_request', _('Legal/Court Request')),
        ('admin_export', _('Administrative Export')),
        ('compliance_audit', _('Compliance Audit')),
        ('data_migration', _('Data Migration')),
    ]
    
    request_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Request ID"),
        help_text=_("Unique identifier for this export request")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Patient"),
        help_text=_("Patient whose data is being exported"),
        related_name='data_export_requests'
    )
    
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Requested By"),
        help_text=_("User who requested the export"),
        related_name='initiated_export_requests'
    )
    
    request_type = models.CharField(
        max_length=30,
        choices=REQUEST_TYPES,
        verbose_name=_("Request Type"),
        help_text=_("Type of export request")
    )
    
    template = models.ForeignKey(
        DataExportTemplate,
        on_delete=models.CASCADE,
        verbose_name=_("Export Template"),
        help_text=_("Template to use for this export")
    )
    
    status = models.CharField(
        max_length=20,
        choices=REQUEST_STATUS,
        default='pending',
        verbose_name=_("Status")
    )
    
    date_range_start = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date Range Start"),
        help_text=_("Start date for data to export (optional)")
    )
    
    date_range_end = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Date Range End"),
        help_text=_("End date for data to export (optional)")
    )
    
    legal_basis = models.TextField(
        verbose_name=_("Legal Basis"),
        help_text=_("Legal basis for this data export request")
    )
    
    purpose = models.TextField(
        verbose_name=_("Purpose"),
        help_text=_("Purpose of the data export")
    )
    
    requester_identity_verified = models.BooleanField(
        default=False,
        verbose_name=_("Identity Verified"),
        help_text=_("Whether requester's identity has been verified")
    )
    
    verification_method = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Verification Method"),
        help_text=_("Method used to verify requester's identity")
    )
    
    export_file_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Export File Path"),
        help_text=_("Path to the generated export file")
    )
    
    export_file_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Export File Hash"),
        help_text=_("SHA-256 hash of the export file for integrity verification")
    )
    
    total_records = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Records"),
        help_text=_("Total number of records included in export")
    )
    
    file_size_bytes = models.PositiveIntegerField(
        default=0,
        verbose_name=_("File Size (Bytes)"),
        help_text=_("Size of the export file in bytes")
    )
    
    expiry_date = models.DateTimeField(
        verbose_name=_("Expiry Date"),
        help_text=_("When this export request expires")
    )
    
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Download Count"),
        help_text=_("Number of times the export has been downloaded")
    )
    
    last_downloaded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Downloaded At")
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error Message"),
        help_text=_("Error message if export failed")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Data Export Request")
        verbose_name_plural = _("Data Export Requests")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request_id} - {self.patient} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Generate request ID and set expiry date if not provided."""
        if not self.request_id:
            from django.utils.crypto import get_random_string
            self.request_id = f"EXP-{get_random_string(12).upper()}"
        
        if not self.expiry_date:
            # Set expiry to 30 days from now (GDPR compliance)
            self.expiry_date = timezone.now() + timedelta(days=30)
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate export request settings."""
        super().clean()
        
        if self.date_range_start and self.date_range_end:
            if self.date_range_start >= self.date_range_end:
                raise ValidationError(_("Start date must be before end date"))
        
        if self.expiry_date and self.expiry_date <= timezone.now():
            raise ValidationError(_("Expiry date must be in the future"))
    
    def is_expired(self) -> bool:
        """Check if export request has expired."""
        return timezone.now() > self.expiry_date
    
    def can_download(self) -> bool:
        """Check if export can be downloaded."""
        return (
            self.status == 'completed' and 
            not self.is_expired() and 
            self.export_file_path
        )
    
    def record_download(self):
        """Record a download of this export."""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        self.save(update_fields=['download_count', 'last_downloaded_at'])


# ============================================================================
# 5. IMPROVED DATA DELETION WORKFLOWS FOR PATIENT PRIVACY
# ============================================================================

@register_snippet
class DataDeletionPolicy(models.Model):
    """
    Policies for systematic data deletion workflows.
    
    Defines rules and procedures for deleting patient data
    in compliance with privacy regulations and medical requirements.
    """
    
    DELETION_TRIGGERS = [
        ('patient_request', _('Patient Deletion Request')),
        ('retention_expired', _('Retention Period Expired')),
        ('consent_withdrawn', _('Consent Withdrawn')),
        ('legal_requirement', _('Legal Requirement')),
        ('data_breach', _('Data Breach Response')),
        ('account_closure', _('Account Closure')),
        ('inactivity', _('Extended Inactivity')),
        ('admin_initiated', _('Administrator Initiated')),
    ]
    
    DELETION_METHODS = [
        ('soft_delete', _('Soft Delete (Mark as Deleted)')),
        ('hard_delete', _('Hard Delete (Permanent Removal)')),
        ('anonymize', _('Anonymize Data')),
        ('archive', _('Archive to Secure Storage')),
        ('pseudonymize', _('Pseudonymize Identifiers')),
    ]
    
    APPROVAL_LEVELS = [
        ('none', _('No Approval Required')),
        ('supervisor', _('Supervisor Approval')),
        ('privacy_officer', _('Privacy Officer Approval')),
        ('medical_director', _('Medical Director Approval')),
        ('legal_team', _('Legal Team Approval')),
        ('patient_consent', _('Patient Consent Required')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Policy Name"),
        help_text=_("Descriptive name for this deletion policy")
    )
    
    trigger_type = models.CharField(
        max_length=30,
        choices=DELETION_TRIGGERS,
        verbose_name=_("Deletion Trigger"),
        help_text=_("What triggers this deletion policy")
    )
    
    deletion_method = models.CharField(
        max_length=20,
        choices=DELETION_METHODS,
        verbose_name=_("Deletion Method"),
        help_text=_("How data should be deleted")
    )
    
    approval_level = models.CharField(
        max_length=20,
        choices=APPROVAL_LEVELS,
        default='supervisor',
        verbose_name=_("Approval Level"),
        help_text=_("Level of approval required for deletion")
    )
    
    affected_models = models.JSONField(
        default=list,
        verbose_name=_("Affected Models"),
        help_text=_("List of Django models affected by this policy")
    )
    
    grace_period_days = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Grace Period (Days)"),
        help_text=_("Days to wait before executing deletion")
    )
    
    notification_recipients = models.JSONField(
        default=list,
        verbose_name=_("Notification Recipients"),
        help_text=_("List of user roles/emails to notify about deletions")
    )
    
    backup_required = models.BooleanField(
        default=True,
        verbose_name=_("Backup Required"),
        help_text=_("Whether to create backup before deletion")
    )
    
    audit_retention_days = models.PositiveIntegerField(
        default=2555,  # 7 years
        verbose_name=_("Audit Retention (Days)"),
        help_text=_("How long to retain deletion audit logs")
    )
    
    legal_basis = models.TextField(
        verbose_name=_("Legal Basis"),
        help_text=_("Legal justification for this deletion policy")
    )
    
    exceptions = models.TextField(
        blank=True,
        verbose_name=_("Exceptions"),
        help_text=_("Circumstances where this policy doesn't apply")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('trigger_type'),
            FieldPanel('deletion_method'),
            FieldPanel('approval_level'),
        ], heading=_("Policy Configuration")),
        
        MultiFieldPanel([
            FieldPanel('affected_models'),
            FieldPanel('grace_period_days'),
            FieldPanel('notification_recipients'),
        ], heading=_("Execution Settings")),
        
        MultiFieldPanel([
            FieldPanel('backup_required'),
            FieldPanel('audit_retention_days'),
            FieldPanel('legal_basis'),
            FieldPanel('exceptions'),
        ], heading=_("Compliance & Audit")),
        
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = _("Data Deletion Policy")
        verbose_name_plural = _("Data Deletion Policies")
    
    def __str__(self):
        return f"{self.name} ({self.get_trigger_type_display()})"
    
    def clean(self):
        """Validate deletion policy settings."""
        super().clean()
        
        if self.grace_period_days < 0:
            raise ValidationError(_("Grace period cannot be negative"))
        
        if self.audit_retention_days < 365:
            raise ValidationError(_("Audit retention must be at least 1 year"))


class DataDeletionRequest(models.Model):
    """
    Individual data deletion requests with approval workflow.
    
    Tracks deletion requests through approval process with
    full audit trail and compliance documentation.
    """
    
    REQUEST_STATUS = [
        ('pending', _('Pending')),
        ('under_review', _('Under Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('scheduled', _('Scheduled for Deletion')),
        ('in_progress', _('Deletion in Progress')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    request_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Request ID"),
        help_text=_("Unique identifier for this deletion request")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Patient"),
        help_text=_("Patient whose data is being deleted"),
        related_name='data_deletion_requests'
    )
    
    requested_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Requested By"),
        help_text=_("User who requested the deletion"),
        related_name='initiated_deletion_requests'
    )
    
    policy = models.ForeignKey(
        DataDeletionPolicy,
        on_delete=models.CASCADE,
        verbose_name=_("Deletion Policy"),
        help_text=_("Policy governing this deletion request")
    )
    
    status = models.CharField(
        max_length=20,
        choices=REQUEST_STATUS,
        default='pending',
        verbose_name=_("Status")
    )
    
    trigger_reason = models.TextField(
        verbose_name=_("Trigger Reason"),
        help_text=_("Specific reason that triggered this deletion request")
    )
    
    scope_description = models.TextField(
        verbose_name=_("Scope Description"),
        help_text=_("Description of what data will be deleted")
    )
    
    affected_records_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Affected Records Count"),
        help_text=_("Estimated number of records to be deleted")
    )
    
    scheduled_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Scheduled Deletion Date"),
        help_text=_("When deletion is scheduled to occur")
    )
    
    approval_required = models.BooleanField(
        default=True,
        verbose_name=_("Approval Required"),
        help_text=_("Whether this deletion requires approval")
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Approved By"),
        help_text=_("User who approved this deletion"),
        related_name='approved_deletion_requests'
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Approved At")
    )
    
    approval_notes = models.TextField(
        blank=True,
        verbose_name=_("Approval Notes"),
        help_text=_("Notes from the approver")
    )
    
    backup_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Backup Path"),
        help_text=_("Path to backup created before deletion")
    )
    
    backup_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name=_("Backup Hash"),
        help_text=_("SHA-256 hash of backup for integrity verification")
    )
    
    deletion_log = models.JSONField(
        default=dict,
        verbose_name=_("Deletion Log"),
        help_text=_("Detailed log of deletion operations")
    )
    
    verification_required = models.BooleanField(
        default=True,
        verbose_name=_("Verification Required"),
        help_text=_("Whether deletion needs to be verified")
    )
    
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Verified By"),
        help_text=_("User who verified the deletion"),
        related_name='verified_deletion_requests'
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verified At")
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error Message"),
        help_text=_("Error message if deletion failed")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Data Deletion Request")
        verbose_name_plural = _("Data Deletion Requests")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request_id} - {self.patient} ({self.status})"
    
    def save(self, *args, **kwargs):
        """Generate request ID if not provided."""
        if not self.request_id:
            from django.utils.crypto import get_random_string
            self.request_id = f"DEL-{get_random_string(12).upper()}"
        
        # Set scheduled date based on policy grace period
        if not self.scheduled_date and self.policy:
            self.scheduled_date = timezone.now() + timedelta(
                days=self.policy.grace_period_days
            )
        
        super().save(*args, **kwargs)
    
    def approve(self, approver: User, notes: str = ""):
        """Approve this deletion request."""
        if self.status != 'pending':
            raise ValueError("Only pending requests can be approved")
        
        self.status = 'approved'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.approval_notes = notes
        
        if self.scheduled_date <= timezone.now():
            self.status = 'scheduled'
        
        self.save()
        
        logger.info(
            f"Deletion request {self.request_id} approved by {approver.username}"
        )
    
    def reject(self, approver: User, reason: str):
        """Reject this deletion request."""
        if self.status != 'pending':
            raise ValueError("Only pending requests can be rejected")
        
        self.status = 'rejected'
        self.approved_by = approver
        self.approved_at = timezone.now()
        self.approval_notes = reason
        self.save()
        
        logger.info(
            f"Deletion request {self.request_id} rejected by {approver.username}: {reason}"
        )
    
    def cancel(self, reason: str = ""):
        """Cancel this deletion request."""
        if self.status in ['completed', 'failed']:
            raise ValueError("Cannot cancel completed or failed requests")
        
        self.status = 'cancelled'
        self.approval_notes = reason
        self.save()
        
        logger.info(f"Deletion request {self.request_id} cancelled: {reason}")
    
    def is_ready_for_execution(self) -> bool:
        """Check if deletion request is ready for execution."""
        return (
            self.status in ['approved', 'scheduled'] and
            self.scheduled_date <= timezone.now() and
            (not self.approval_required or self.approved_by is not None)
        )


class DataDeletionExecutor:
    """
    Engine for executing data deletion requests safely and compliantly.
    
    Handles the actual deletion operations with backup, verification,
    and audit trail generation.
    """
    
    def __init__(self, deletion_request: DataDeletionRequest):
        """Initialize executor with a deletion request."""
        self.deletion_request = deletion_request
        self.policy = deletion_request.policy
        self.patient = deletion_request.patient
        
    def execute_deletion(self) -> bool:
        """Execute the deletion request according to policy."""
        try:
            # Verify request is ready for execution
            if not self.deletion_request.is_ready_for_execution():
                raise ValueError("Deletion request is not ready for execution")
            
            # Mark as in progress
            self.deletion_request.status = 'in_progress'
            self.deletion_request.save(update_fields=['status'])
            
            # Create backup if required
            if self.policy.backup_required:
                self._create_backup()
            
            # Execute deletion based on method
            deletion_results = self._execute_deletion_method()
            
            # Update deletion log
            self.deletion_request.deletion_log.update({
                'execution_timestamp': timezone.now().isoformat(),
                'method': self.policy.deletion_method,
                'results': deletion_results,
                'records_processed': sum(result.get('count', 0) for result in deletion_results.values())
            })
            
            # Mark as completed
            self.deletion_request.status = 'completed'
            self.deletion_request.completed_at = timezone.now()
            self.deletion_request.affected_records_count = sum(
                result.get('count', 0) for result in deletion_results.values()
            )
            self.deletion_request.save()
            
            # Send notifications
            self._send_completion_notifications()
            
            logger.info(
                f"Deletion request {self.deletion_request.request_id} completed successfully. "
                f"Records affected: {self.deletion_request.affected_records_count}"
            )
            
            return True
            
        except Exception as e:
            # Mark as failed
            self.deletion_request.status = 'failed'
            self.deletion_request.error_message = str(e)
            self.deletion_request.save(update_fields=['status', 'error_message'])
            
            logger.error(
                f"Deletion request {self.deletion_request.request_id} failed: {e}"
            )
            
            # Send failure notifications
            self._send_failure_notifications(str(e))
            
            return False
    
    def _create_backup(self):
        """Create backup of data before deletion."""
        from .data_export import DataExporter, DataExportTemplate, DataExportRequest
        
        # Create a backup export template
        backup_template, created = DataExportTemplate.objects.get_or_create(
            name="Deletion Backup Template",
            compliance_type='custom',
            export_format='json',
            defaults={
                'description': 'Backup template for data deletion',
                'included_models': self.policy.affected_models,
                'include_metadata': True,
                'is_active': True
            }
        )
        
        # Create backup export request
        backup_request = DataExportRequest.objects.create(
            patient=self.patient,
            requested_by=self.deletion_request.requested_by,
            request_type='admin_export',
            template=backup_template,
            legal_basis=f"Backup before deletion - Request {self.deletion_request.request_id}",
            purpose="Data backup before deletion for compliance"
        )
        
        # Generate backup
        exporter = DataExporter(backup_request)
        backup_path = exporter.generate_export()
        
        # Calculate backup hash
        backup_hash = hashlib.sha256()
        with open(backup_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                backup_hash.update(chunk)
        
        # Update deletion request with backup info
        self.deletion_request.backup_path = backup_path
        self.deletion_request.backup_hash = backup_hash.hexdigest()
        self.deletion_request.save(update_fields=['backup_path', 'backup_hash'])
        
        logger.info(f"Backup created for deletion request {self.deletion_request.request_id}: {backup_path}")
    
    def _execute_deletion_method(self) -> Dict[str, Any]:
        """Execute deletion according to the specified method."""
        deletion_results = {}
        
        for model_path in self.policy.affected_models:
            try:
                app_label, model_name = model_path.split('.')
                model_class = apps.get_model(app_label, model_name)
                
                # Get records to delete
                records = self._get_patient_records(model_class)
                record_count = len(records)
                
                if record_count == 0:
                    deletion_results[model_path] = {'count': 0, 'status': 'no_records'}
                    continue
                
                # Apply deletion method
                if self.policy.deletion_method == 'soft_delete':
                    result = self._soft_delete_records(records)
                elif self.policy.deletion_method == 'hard_delete':
                    result = self._hard_delete_records(records)
                elif self.policy.deletion_method == 'anonymize':
                    result = self._anonymize_records(records)
                elif self.policy.deletion_method == 'archive':
                    result = self._archive_records(records)
                elif self.policy.deletion_method == 'pseudonymize':
                    result = self._pseudonymize_records(records)
                else:
                    result = {'count': 0, 'status': 'unknown_method'}
                
                deletion_results[model_path] = result
                
            except Exception as e:
                deletion_results[model_path] = {
                    'count': 0,
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"Error deleting records from {model_path}: {e}")
        
        return deletion_results
    
    def _get_patient_records(self, model_class) -> List[Any]:
        """Get patient records from a model."""
        records = []
        
        # Try different field names to find patient relationship
        patient_fields = ['patient', 'user', 'created_by', 'owner']
        
        for field_name in patient_fields:
            if hasattr(model_class, field_name):
                try:
                    queryset = model_class.objects.filter(**{field_name: self.patient})
                    records = list(queryset)
                    break
                except Exception as e:
                    logger.debug(f"Failed to query {model_class.__name__} with {field_name}: {e}")
                    continue
        
        return records
    
    def _soft_delete_records(self, records) -> Dict[str, Any]:
        """Soft delete records (mark as deleted)."""
        count = 0
        
        for record in records:
            if hasattr(record, 'is_deleted'):
                record.is_deleted = True
                record.deleted_at = timezone.now()
                record.save(update_fields=['is_deleted', 'deleted_at'])
                count += 1
            elif hasattr(record, 'is_active'):
                record.is_active = False
                record.save(update_fields=['is_active'])
                count += 1
        
        return {'count': count, 'status': 'soft_deleted'}
    
    def _hard_delete_records(self, records) -> Dict[str, Any]:
        """Hard delete records (permanent removal)."""
        count = len(records)
        
        for record in records:
            record.delete()
        
        return {'count': count, 'status': 'hard_deleted'}
    
    def _anonymize_records(self, records) -> Dict[str, Any]:
        """Anonymize records using anonymization profile."""
        if not hasattr(records[0], 'anonymize'):
            return {'count': 0, 'status': 'anonymization_not_supported'}
        
        # Use default anonymization profile or create one
        from .wagtail_privacy import AnonymizationProfile
        
        profile = AnonymizationProfile.objects.filter(
            profile_type='data_sharing',
            is_active=True
        ).first()
        
        if not profile:
            return {'count': 0, 'status': 'no_anonymization_profile'}
        
        count = 0
        for record in records:
            try:
                record.anonymize(profile)
                count += 1
            except Exception as e:
                logger.error(f"Failed to anonymize record {record.pk}: {e}")
        
        return {'count': count, 'status': 'anonymized'}
    
    def _archive_records(self, records) -> Dict[str, Any]:
        """Archive records to secure storage."""
        # This would typically move records to an archive database or storage
        # For now, we'll implement as soft delete with archive flag
        count = 0
        
        for record in records:
            if hasattr(record, 'is_archived'):
                record.is_archived = True
                record.archived_at = timezone.now()
                record.save(update_fields=['is_archived', 'archived_at'])
                count += 1
        
        return {'count': count, 'status': 'archived'}
    
    def _pseudonymize_records(self, records) -> Dict[str, Any]:
        """Pseudonymize identifying fields in records."""
        count = 0
        
        for record in records:
            # Pseudonymize common identifying fields
            if hasattr(record, 'email'):
                record.email = f"pseudonym_{record.pk}@medguard.local"
            if hasattr(record, 'first_name'):
                record.first_name = f"Patient_{record.pk}"
            if hasattr(record, 'last_name'):
                record.last_name = "Anonymous"
            if hasattr(record, 'phone'):
                record.phone = "000-000-0000"
            
            record.save()
            count += 1
        
        return {'count': count, 'status': 'pseudonymized'}
    
    def _send_completion_notifications(self):
        """Send notifications about deletion completion."""
        # This would integrate with the notification system
        # For now, just log the completion
        logger.info(
            f"Deletion completed for request {self.deletion_request.request_id}. "
            f"Notifications should be sent to: {self.policy.notification_recipients}"
        )
    
    def _send_failure_notifications(self, error_message: str):
        """Send notifications about deletion failure."""
        logger.error(
            f"Deletion failed for request {self.deletion_request.request_id}: {error_message}. "
            f"Notifications should be sent to: {self.policy.notification_recipients}"
        )


class DataDeletionManager:
    """
    Manager for handling data deletion operations and workflows.
    
    Provides high-level methods for creating, approving, and executing
    data deletion requests.
    """
    
    @staticmethod
    def create_deletion_request(
        patient: User,
        trigger_type: str,
        trigger_reason: str,
        requested_by: User = None,
        policy: DataDeletionPolicy = None
    ) -> DataDeletionRequest:
        """Create a new data deletion request."""
        
        # Find appropriate policy if not provided
        if not policy:
            policy = DataDeletionPolicy.objects.filter(
                trigger_type=trigger_type,
                is_active=True
            ).first()
            
            if not policy:
                raise ValueError(f"No active deletion policy found for trigger: {trigger_type}")
        
        # Create deletion request
        deletion_request = DataDeletionRequest.objects.create(
            patient=patient,
            requested_by=requested_by or patient,
            policy=policy,
            trigger_reason=trigger_reason,
            scope_description=f"Delete patient data according to {policy.name}",
            approval_required=(policy.approval_level != 'none')
        )
        
        logger.info(
            f"Created deletion request {deletion_request.request_id} "
            f"for patient {patient.id} using policy {policy.name}"
        )
        
        return deletion_request
    
    @staticmethod
    def get_pending_approvals(approver_role: str = None) -> List[DataDeletionRequest]:
        """Get deletion requests pending approval."""
        queryset = DataDeletionRequest.objects.filter(
            status='pending',
            approval_required=True
        )
        
        if approver_role:
            queryset = queryset.filter(policy__approval_level=approver_role)
        
        return list(queryset.order_by('created_at'))
    
    @staticmethod
    def get_scheduled_deletions() -> List[DataDeletionRequest]:
        """Get deletion requests scheduled for execution."""
        return DataDeletionRequest.objects.filter(
            status__in=['approved', 'scheduled'],
            scheduled_date__lte=timezone.now()
        ).order_by('scheduled_date')
    
    @staticmethod
    def execute_scheduled_deletions() -> Dict[str, int]:
        """Execute all scheduled deletion requests."""
        scheduled_requests = DataDeletionManager.get_scheduled_deletions()
        
        results = {
            'total_scheduled': len(scheduled_requests),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for request in scheduled_requests:
            try:
                executor = DataDeletionExecutor(request)
                success = executor.execute_deletion()
                
                if success:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Request {request.request_id}: {request.error_message}")
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Request {request.request_id}: {str(e)}")
                logger.error(f"Failed to execute deletion request {request.request_id}: {e}")
        
        logger.info(
            f"Executed {results['total_scheduled']} scheduled deletions. "
            f"Successful: {results['successful']}, Failed: {results['failed']}"
        )
        
        return results
    
    @staticmethod
    def cleanup_old_deletion_logs():
        """Clean up old deletion audit logs according to retention policies."""
        cutoff_date = timezone.now() - timedelta(days=2555)  # 7 years default
        
        old_requests = DataDeletionRequest.objects.filter(
            completed_at__lt=cutoff_date,
            status='completed'
        )
        
        cleaned_count = 0
        for request in old_requests:
            # Archive the deletion log before cleanup
            if request.deletion_log:
                # In a real implementation, this would be archived to long-term storage
                logger.info(f"Archiving deletion log for request {request.request_id}")
            
            # Clear sensitive data but keep basic audit info
            request.deletion_log = {'archived': True, 'archived_at': timezone.now().isoformat()}
            request.backup_path = ""
            request.save(update_fields=['deletion_log', 'backup_path'])
            
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old deletion audit logs")
        return cleaned_count
    
    @staticmethod
    def generate_deletion_report() -> Dict[str, Any]:
        """Generate comprehensive deletion compliance report."""
        total_requests = DataDeletionRequest.objects.count()
        
        report = {
            'generated_at': timezone.now(),
            'total_requests': total_requests,
            'status_breakdown': {},
            'trigger_breakdown': {},
            'policy_usage': {},
            'compliance_metrics': {}
        }
        
        # Status breakdown
        for status, status_name in DataDeletionRequest.REQUEST_STATUS:
            count = DataDeletionRequest.objects.filter(status=status).count()
            report['status_breakdown'][status] = {
                'name': status_name,
                'count': count,
                'percentage': (count / total_requests * 100) if total_requests > 0 else 0
            }
        
        # Trigger breakdown
        for trigger, trigger_name in DataDeletionPolicy.DELETION_TRIGGERS:
            count = DataDeletionRequest.objects.filter(policy__trigger_type=trigger).count()
            report['trigger_breakdown'][trigger] = {
                'name': trigger_name,
                'count': count
            }
        
        # Policy usage
        for policy in DataDeletionPolicy.objects.filter(is_active=True):
            count = DataDeletionRequest.objects.filter(policy=policy).count()
            report['policy_usage'][policy.name] = {
                'trigger_type': policy.get_trigger_type_display(),
                'deletion_method': policy.get_deletion_method_display(),
                'usage_count': count
            }
        
        # Compliance metrics
        recent_requests = DataDeletionRequest.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        completed_requests = DataDeletionRequest.objects.filter(status='completed')
        total_records_deleted = sum(
            request.affected_records_count for request in completed_requests
        )
        
        report['compliance_metrics'] = {
            'requests_last_30_days': recent_requests.count(),
            'total_records_deleted': total_records_deleted,
            'average_completion_time_days': 0,  # Would calculate from timestamps
            'approval_compliance_rate': (
                DataDeletionRequest.objects.filter(
                    approval_required=True,
                    approved_by__isnull=False
                ).count() / 
                DataDeletionRequest.objects.filter(approval_required=True).count() * 100
            ) if DataDeletionRequest.objects.filter(approval_required=True).count() > 0 else 0,
        }
        
        return report