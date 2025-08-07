"""
Prescription OCR Models
Models for managing prescription image processing and OCR results.
"""
import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet
from wagtailimages.models import Image

User = get_user_model()


@register_snippet
class PrescriptionOCRResult(models.Model):
    """Model to store OCR results from prescription images."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Image and processing info
    prescription_image = models.ForeignKey(
        Image,
        on_delete=models.CASCADE,
        related_name="ocr_results",
        verbose_name=_("Prescription Image")
    )
    
    # OCR Results
    extracted_text = models.TextField(
        verbose_name=_("Extracted Text"),
        help_text=_("Raw text extracted from the prescription image")
    )
    
    confidence_score = models.FloatField(
        default=0.0,
        verbose_name=_("Confidence Score"),
        help_text=_("OCR confidence score (0-1)")
    )
    
    # Parsed medication data
    medication_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Medication Name")
    )
    
    dosage = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Dosage")
    )
    
    frequency = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Frequency")
    )
    
    prescriber_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Prescriber Name")
    )
    
    prescription_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Prescription Date")
    )
    
    # Processing metadata
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Processed By")
    )
    
    processed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Processed At")
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified"),
        help_text=_("Has this OCR result been manually verified?")
    )
    
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_ocr_results",
        verbose_name=_("Verified By")
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verified At")
    )
    
    # HIPAA compliance
    encrypted_data = models.JSONField(
        default=dict,
        verbose_name=_("Encrypted PHI"),
        help_text=_("Encrypted personally identifiable health information")
    )
    
    access_log = models.JSONField(
        default=list,
        verbose_name=_("Access Log"),
        help_text=_("Log of who accessed this prescription data")
    )
    
    notes = RichTextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional notes about the OCR processing")
    )
    
    class Meta:
        verbose_name = _("Prescription OCR Result")
        verbose_name_plural = _("Prescription OCR Results")
        ordering = ["-processed_at"]
    
    def __str__(self):
        return f"OCR Result - {self.medication_name or 'Unknown'} ({self.processed_at})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("prescription_image"),
            FieldPanel("extracted_text"),
            FieldPanel("confidence_score"),
        ], heading=_("OCR Processing")),
        
        MultiFieldPanel([
            FieldPanel("medication_name"),
            FieldPanel("dosage"),
            FieldPanel("frequency"),
            FieldPanel("prescriber_name"),
            FieldPanel("prescription_date"),
        ], heading=_("Extracted Medication Data")),
        
        MultiFieldPanel([
            FieldPanel("is_verified"),
            FieldPanel("verified_by"),
            FieldPanel("verified_at"),
            FieldPanel("notes"),
        ], heading=_("Verification")),
    ]


@register_snippet
class OCRTemplate(models.Model):
    """Template for different prescription formats to improve OCR accuracy."""
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Template Name")
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_("Description")
    )
    
    # Template configuration
    field_mappings = models.JSONField(
        default=dict,
        verbose_name=_("Field Mappings"),
        help_text=_("JSON mapping of field positions and patterns")
    )
    
    regex_patterns = models.JSONField(
        default=dict,
        verbose_name=_("Regex Patterns"),
        help_text=_("Regular expressions for extracting specific data")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
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
        verbose_name = _("OCR Template")
        verbose_name_plural = _("OCR Templates")
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    panels = [
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("field_mappings"),
        FieldPanel("regex_patterns"),
        FieldPanel("is_active"),
    ]
