"""
Medical Forms Models
Models for healthcare-specific form building and data collection.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, Orderable
from wagtail.snippets.models import register_snippet
from wagtail import blocks

User = get_user_model()


class MedicalFormFieldBlock(blocks.StructBlock):
    """Block for defining medical form fields."""
    
    field_type = blocks.ChoiceBlock(
        choices=[
            ('text', _('Text Input')),
            ('textarea', _('Text Area')),
            ('number', _('Number')),
            ('email', _('Email')),
            ('date', _('Date')),
            ('checkbox', _('Checkbox')),
            ('radio', _('Radio Buttons')),
            ('select', _('Dropdown')),
            ('file', _('File Upload')),
            ('signature', _('Digital Signature')),
            ('medical_history', _('Medical History')),
            ('medication_list', _('Medication List')),
            ('vital_signs', _('Vital Signs')),
            ('pain_scale', _('Pain Scale')),
            ('consent', _('Consent Checkbox')),
        ],
        default='text'
    )
    
    label = blocks.CharBlock(
        max_length=255,
        help_text=_("Field label displayed to users")
    )
    
    help_text = blocks.CharBlock(
        max_length=500,
        required=False,
        help_text=_("Additional help text for the field")
    )
    
    required = blocks.BooleanBlock(
        default=False,
        help_text=_("Is this field required?")
    )
    
    choices = blocks.ListBlock(
        blocks.CharBlock(max_length=100),
        required=False,
        help_text=_("Options for radio, select, or checkbox fields")
    )
    
    default_value = blocks.CharBlock(
        max_length=255,
        required=False,
        help_text=_("Default value for the field")
    )
    
    validation_rules = blocks.TextBlock(
        required=False,
        help_text=_("JSON validation rules for the field")
    )
    
    hipaa_sensitive = blocks.BooleanBlock(
        default=False,
        help_text=_("Contains HIPAA-sensitive information")
    )
    
    class Meta:
        icon = 'form'
        label = _("Form Field")


@register_snippet
class MedicalFormTemplate(models.Model):
    """Template for medical forms with predefined fields."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Template Name")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    category = models.CharField(
        max_length=100,
        choices=[
            ('intake', _('Patient Intake')),
            ('assessment', _('Medical Assessment')),
            ('consent', _('Consent Forms')),
            ('history', _('Medical History')),
            ('screening', _('Health Screening')),
            ('discharge', _('Discharge Forms')),
            ('insurance', _('Insurance Forms')),
            ('prescription', _('Prescription Forms')),
            ('referral', _('Referral Forms')),
            ('custom', _('Custom Forms')),
        ],
        default='intake',
        verbose_name=_("Form Category")
    )
    
    # Form structure
    form_fields = StreamField([
        ('field', MedicalFormFieldBlock()),
    ], use_json_field=True, blank=True)
    
    # HIPAA and compliance
    requires_hipaa_consent = models.BooleanField(
        default=True,
        verbose_name=_("Requires HIPAA Consent")
    )
    
    data_retention_days = models.IntegerField(
        default=2555,  # 7 years
        validators=[MinValueValidator(1)],
        verbose_name=_("Data Retention (days)"),
        help_text=_("How long to retain form data")
    )
    
    # Access control
    allowed_roles = models.JSONField(
        default=list,
        verbose_name=_("Allowed User Roles"),
        help_text=_("User roles that can access this form")
    )
    
    # Workflow
    requires_approval = models.BooleanField(
        default=False,
        verbose_name=_("Requires Approval")
    )
    
    approval_workflow = models.JSONField(
        default=list,
        verbose_name=_("Approval Workflow"),
        help_text=_("Steps in the approval process")
    )
    
    # Notifications
    notification_settings = models.JSONField(
        default=dict,
        verbose_name=_("Notification Settings")
    )
    
    # Template metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Created By")
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
        verbose_name = _("Medical Form Template")
        verbose_name_plural = _("Medical Form Templates")
        ordering = ["category", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("description"),
            FieldPanel("category"),
        ], heading=_("Basic Information")),
        
        FieldPanel("form_fields"),
        
        MultiFieldPanel([
            FieldPanel("requires_hipaa_consent"),
            FieldPanel("data_retention_days"),
            FieldPanel("allowed_roles"),
        ], heading=_("Compliance & Access")),
        
        MultiFieldPanel([
            FieldPanel("requires_approval"),
            FieldPanel("approval_workflow"),
            FieldPanel("notification_settings"),
        ], heading=_("Workflow")),
        
        MultiFieldPanel([
            FieldPanel("is_active"),
            FieldPanel("created_by"),
        ], heading=_("Settings")),
    ]


class MedicalFormPage(Page):
    """Page type for medical forms."""
    
    template_name = "wagtail_medical_forms/form_page.html"
    
    form_template = models.ForeignKey(
        MedicalFormTemplate,
        on_delete=models.PROTECT,
        verbose_name=_("Form Template")
    )
    
    introduction = RichTextField(
        blank=True,
        verbose_name=_("Introduction Text")
    )
    
    thank_you_text = RichTextField(
        blank=True,
        verbose_name=_("Thank You Message")
    )
    
    # Form settings
    allow_multiple_submissions = models.BooleanField(
        default=False,
        verbose_name=_("Allow Multiple Submissions"),
        help_text=_("Allow users to submit this form multiple times")
    )
    
    requires_authentication = models.BooleanField(
        default=True,
        verbose_name=_("Requires Authentication")
    )
    
    # Email notifications
    send_confirmation_email = models.BooleanField(
        default=True,
        verbose_name=_("Send Confirmation Email")
    )
    
    confirmation_email_template = models.TextField(
        blank=True,
        verbose_name=_("Confirmation Email Template")
    )
    
    notification_emails = models.JSONField(
        default=list,
        verbose_name=_("Notification Email Addresses")
    )
    
    content_panels = Page.content_panels + [
        FieldPanel("form_template"),
        FieldPanel("introduction"),
        FieldPanel("thank_you_text"),
        
        MultiFieldPanel([
            FieldPanel("allow_multiple_submissions"),
            FieldPanel("requires_authentication"),
        ], heading=_("Form Settings")),
        
        MultiFieldPanel([
            FieldPanel("send_confirmation_email"),
            FieldPanel("confirmation_email_template"),
            FieldPanel("notification_emails"),
        ], heading=_("Email Notifications")),
    ]
    
    class Meta:
        verbose_name = _("Medical Form Page")


@register_snippet
class MedicalFormSubmission(models.Model):
    """Model for storing medical form submissions."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Form information
    form_template = models.ForeignKey(
        MedicalFormTemplate,
        on_delete=models.CASCADE,
        verbose_name=_("Form Template")
    )
    
    form_page = models.ForeignKey(
        MedicalFormPage,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Form Page")
    )
    
    # Submission data
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Submitted By")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="medical_form_submissions",
        null=True,
        blank=True,
        verbose_name=_("Patient"),
        help_text=_("Patient this form is about (may be different from submitter)")
    )
    
    # Form data (encrypted for HIPAA compliance)
    form_data = models.JSONField(
        verbose_name=_("Form Data"),
        help_text=_("Submitted form data (encrypted)")
    )
    
    form_data_hash = models.CharField(
        max_length=64,
        verbose_name=_("Data Hash"),
        help_text=_("Hash of form data for integrity checking")
    )
    
    # Submission metadata
    submission_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("Submission IP Address")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent")
    )
    
    submission_source = models.CharField(
        max_length=50,
        choices=[
            ('web', _('Web Form')),
            ('mobile', _('Mobile App')),
            ('kiosk', _('Patient Kiosk')),
            ('staff', _('Staff Entry')),
            ('import', _('Data Import')),
        ],
        default='web',
        verbose_name=_("Submission Source")
    )
    
    # Status and workflow
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', _('Draft')),
            ('submitted', _('Submitted')),
            ('under_review', _('Under Review')),
            ('approved', _('Approved')),
            ('rejected', _('Rejected')),
            ('archived', _('Archived')),
        ],
        default='submitted',
        verbose_name=_("Status")
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_form_submissions",
        verbose_name=_("Reviewed By")
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )
    
    review_notes = models.TextField(
        blank=True,
        verbose_name=_("Review Notes")
    )
    
    # HIPAA compliance
    access_log = models.JSONField(
        default=list,
        verbose_name=_("Access Log"),
        help_text=_("Log of who accessed this submission")
    )
    
    consent_given = models.BooleanField(
        default=False,
        verbose_name=_("HIPAA Consent Given")
    )
    
    consent_timestamp = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Timestamp")
    )
    
    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    # Data retention
    retention_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Retention Expires At")
    )
    
    class Meta:
        verbose_name = _("Medical Form Submission")
        verbose_name_plural = _("Medical Form Submissions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['submitted_by', 'created_at']),
            models.Index(fields=['patient', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['form_template']),
        ]
    
    def __str__(self):
        patient_name = self.patient.get_full_name() if self.patient else "Unknown"
        return f"{self.form_template.name} - {patient_name} ({self.created_at})"
    
    def save(self, *args, **kwargs):
        """Override save to set retention expiry."""
        if not self.retention_expires_at and self.form_template.data_retention_days:
            from datetime import timedelta
            self.retention_expires_at = timezone.now() + timedelta(
                days=self.form_template.data_retention_days
            )
        super().save(*args, **kwargs)
    
    panels = [
        MultiFieldPanel([
            FieldPanel("form_template"),
            FieldPanel("form_page"),
            FieldPanel("submitted_by"),
            FieldPanel("patient"),
        ], heading=_("Form Information")),
        
        MultiFieldPanel([
            FieldPanel("status"),
            FieldPanel("reviewed_by"),
            FieldPanel("reviewed_at"),
            FieldPanel("review_notes"),
        ], heading=_("Review Status")),
        
        MultiFieldPanel([
            FieldPanel("consent_given"),
            FieldPanel("consent_timestamp"),
            FieldPanel("retention_expires_at"),
        ], heading=_("HIPAA Compliance")),
        
        MultiFieldPanel([
            FieldPanel("submission_source"),
            FieldPanel("submission_ip"),
        ], heading=_("Submission Details")),
    ]


@register_snippet
class MedicalFormField(Orderable):
    """Individual field in a medical form (for dynamic forms)."""
    
    form_template = models.ForeignKey(
        MedicalFormTemplate,
        on_delete=models.CASCADE,
        related_name="dynamic_fields"
    )
    
    field_name = models.CharField(
        max_length=100,
        verbose_name=_("Field Name")
    )
    
    field_type = models.CharField(
        max_length=50,
        choices=[
            ('text', _('Text Input')),
            ('textarea', _('Text Area')),
            ('number', _('Number')),
            ('email', _('Email')),
            ('date', _('Date')),
            ('checkbox', _('Checkbox')),
            ('radio', _('Radio Buttons')),
            ('select', _('Dropdown')),
            ('file', _('File Upload')),
            ('signature', _('Digital Signature')),
        ],
        verbose_name=_("Field Type")
    )
    
    label = models.CharField(
        max_length=255,
        verbose_name=_("Field Label")
    )
    
    help_text = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Help Text")
    )
    
    required = models.BooleanBlock(
        default=False,
        verbose_name=_("Required")
    )
    
    choices = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_("Field Choices")
    )
    
    default_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Default Value")
    )
    
    validation_rules = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Validation Rules")
    )
    
    class Meta(Orderable.Meta):
        verbose_name = _("Medical Form Field")
        verbose_name_plural = _("Medical Form Fields")
    
    def __str__(self):
        return f"{self.label} ({self.field_type})"
    
    panels = [
        FieldPanel("field_name"),
        FieldPanel("field_type"),
        FieldPanel("label"),
        FieldPanel("help_text"),
        FieldPanel("required"),
        FieldPanel("choices"),
        FieldPanel("default_value"),
        FieldPanel("validation_rules"),
    ]
