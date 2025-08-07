"""
Emergency Access Models
Models for emergency medical data access and break-glass functionality.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet

User = get_user_model()


@register_snippet
class EmergencyAccess(models.Model):
    """Model for logging emergency access to patient data."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Access details
    accessing_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Accessing User")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="emergency_accesses",
        verbose_name=_("Patient")
    )
    
    # Emergency details
    emergency_type = models.CharField(
        max_length=50,
        choices=[
            ('cardiac_arrest', _('Cardiac Arrest')),
            ('trauma', _('Trauma')),
            ('overdose', _('Overdose')),
            ('allergic_reaction', _('Allergic Reaction')),
            ('psychiatric', _('Psychiatric Emergency')),
            ('other', _('Other Emergency')),
        ],
        verbose_name=_("Emergency Type")
    )
    
    justification = RichTextField(
        verbose_name=_("Access Justification"),
        help_text=_("Detailed justification for emergency access")
    )
    
    # Location and context
    facility = models.CharField(
        max_length=255,
        verbose_name=_("Facility/Location")
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Department")
    )
    
    # Access metadata
    accessed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Accessed At")
    )
    
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP Address")
    )
    
    session_duration = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Session Duration (minutes)"
    )
    
    # Data accessed
    data_accessed = models.JSONField(
        default=list,
        verbose_name=_("Data Accessed"),
        help_text=_("Types of data accessed during emergency")
    )
    
    # Review and validation
    requires_review = models.BooleanField(
        default=True,
        verbose_name=_("Requires Review")
    )
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_emergency_accesses",
        verbose_name=_("Reviewed By")
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )
    
    is_justified = models.BooleanField(
        default=True,
        verbose_name=_("Access Justified")
    )
    
    review_notes = models.TextField(
        blank=True,
        verbose_name=_("Review Notes")
    )
    
    class Meta:
        verbose_name = _("Emergency Access")
        verbose_name_plural = _("Emergency Accesses")
        ordering = ["-accessed_at"]
    
    def __str__(self):
        return f"Emergency access by {self.accessing_user.get_full_name()} to {self.patient.get_full_name()}"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("accessing_user"),
            FieldPanel("patient"),
            FieldPanel("emergency_type"),
            FieldPanel("justification"),
        ], heading=_("Emergency Details")),
        
        MultiFieldPanel([
            FieldPanel("facility"),
            FieldPanel("department"),
            FieldPanel("data_accessed"),
        ], heading=_("Access Context")),
        
        MultiFieldPanel([
            FieldPanel("requires_review"),
            FieldPanel("reviewed_by"),
            FieldPanel("is_justified"),
            FieldPanel("review_notes"),
        ], heading=_("Review")),
    ]


@register_snippet
class EmergencyContact(models.Model):
    """Model for patient emergency contacts."""
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="emergency_contacts",
        verbose_name=_("Patient")
    )
    
    name = models.CharField(
        max_length=255,
        verbose_name=_("Contact Name")
    )
    
    relationship = models.CharField(
        max_length=50,
        choices=[
            ('spouse', _('Spouse')),
            ('parent', _('Parent')),
            ('child', _('Child')),
            ('sibling', _('Sibling')),
            ('friend', _('Friend')),
            ('guardian', _('Guardian')),
            ('other', _('Other')),
        ],
        verbose_name=_("Relationship")
    )
    
    phone_primary = models.CharField(
        max_length=20,
        verbose_name=_("Primary Phone")
    )
    
    phone_secondary = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Secondary Phone")
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email")
    )
    
    is_primary = models.BooleanField(
        default=False,
        verbose_name=_("Primary Contact")
    )
    
    can_make_decisions = models.BooleanField(
        default=False,
        verbose_name=_("Can Make Medical Decisions")
    )
    
    class Meta:
        verbose_name = _("Emergency Contact")
        verbose_name_plural = _("Emergency Contacts")
        ordering = ["-is_primary", "name"]
    
    def __str__(self):
        return f"{self.name} ({self.relationship}) - {self.patient.get_full_name()}"
