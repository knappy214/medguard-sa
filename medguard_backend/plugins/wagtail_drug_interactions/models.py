"""
Drug Interactions Models
Models for managing drug interactions and clinical decision support.
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


class InteractionSeverity(models.TextChoices):
    """Choices for interaction severity levels."""
    MINOR = 'minor', _('Minor')
    MODERATE = 'moderate', _('Moderate')
    MAJOR = 'major', _('Major')
    CONTRAINDICATED = 'contraindicated', _('Contraindicated')


class InteractionType(models.TextChoices):
    """Choices for interaction types."""
    DRUG_DRUG = 'drug_drug', _('Drug-Drug')
    DRUG_FOOD = 'drug_food', _('Drug-Food')
    DRUG_CONDITION = 'drug_condition', _('Drug-Condition')
    DRUG_ALLERGY = 'drug_allergy', _('Drug-Allergy')
    DUPLICATE_THERAPY = 'duplicate_therapy', _('Duplicate Therapy')


@register_snippet
class DrugInteraction(models.Model):
    """Model for storing drug interaction data."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Primary drug
    drug_name_1 = models.CharField(
        max_length=255,
        verbose_name=_("Primary Drug"),
        db_index=True
    )
    
    generic_name_1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Primary Generic Name")
    )
    
    # Interacting drug/substance
    drug_name_2 = models.CharField(
        max_length=255,
        verbose_name=_("Interacting Drug/Substance"),
        db_index=True
    )
    
    generic_name_2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Interacting Generic Name")
    )
    
    # Interaction details
    interaction_type = models.CharField(
        max_length=20,
        choices=InteractionType.choices,
        default=InteractionType.DRUG_DRUG,
        verbose_name=_("Interaction Type")
    )
    
    severity = models.CharField(
        max_length=20,
        choices=InteractionSeverity.choices,
        verbose_name=_("Severity Level")
    )
    
    confidence_level = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name=_("Confidence Level"),
        help_text=_("Confidence in the interaction data (0-1)")
    )
    
    # Clinical information
    mechanism = RichTextField(
        verbose_name=_("Mechanism of Interaction"),
        help_text=_("How the interaction occurs")
    )
    
    clinical_effects = RichTextField(
        verbose_name=_("Clinical Effects"),
        help_text=_("What effects to expect")
    )
    
    management = RichTextField(
        verbose_name=_("Management Recommendations"),
        help_text=_("How to manage the interaction")
    )
    
    monitoring_parameters = models.JSONField(
        default=list,
        verbose_name=_("Monitoring Parameters"),
        help_text=_("What to monitor when drugs are used together")
    )
    
    # Evidence and references
    evidence_level = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Evidence Level"),
        help_text=_("Level of clinical evidence")
    )
    
    references = models.JSONField(
        default=list,
        verbose_name=_("References"),
        help_text=_("Clinical references and studies")
    )
    
    # External database IDs
    rxnorm_id_1 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("RxNorm ID 1")
    )
    
    rxnorm_id_2 = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("RxNorm ID 2")
    )
    
    # Metadata
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
    
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Reviewed By"),
        limit_choices_to={'groups__name': 'Clinical Pharmacists'}
    )
    
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Reviewed At")
    )
    
    class Meta:
        verbose_name = _("Drug Interaction")
        verbose_name_plural = _("Drug Interactions")
        ordering = ["-severity", "drug_name_1", "drug_name_2"]
        indexes = [
            models.Index(fields=['drug_name_1', 'drug_name_2']),
            models.Index(fields=['severity', 'interaction_type']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['drug_name_1', 'drug_name_2', 'interaction_type']
    
    def __str__(self):
        return f"{self.drug_name_1} + {self.drug_name_2} ({self.get_severity_display()})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("drug_name_1"),
            FieldPanel("generic_name_1"),
            FieldPanel("rxnorm_id_1"),
        ], heading=_("Primary Drug")),
        
        MultiFieldPanel([
            FieldPanel("drug_name_2"),
            FieldPanel("generic_name_2"),
            FieldPanel("rxnorm_id_2"),
        ], heading=_("Interacting Drug/Substance")),
        
        MultiFieldPanel([
            FieldPanel("interaction_type"),
            FieldPanel("severity"),
            FieldPanel("confidence_level"),
            FieldPanel("evidence_level"),
        ], heading=_("Interaction Details")),
        
        MultiFieldPanel([
            FieldPanel("mechanism"),
            FieldPanel("clinical_effects"),
            FieldPanel("management"),
            FieldPanel("monitoring_parameters"),
        ], heading=_("Clinical Information")),
        
        MultiFieldPanel([
            FieldPanel("references"),
            FieldPanel("is_active"),
            FieldPanel("reviewed_by"),
            FieldPanel("reviewed_at"),
        ], heading=_("Validation")),
    ]


@register_snippet
class InteractionCheck(models.Model):
    """Model for logging interaction checks performed."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # User information
    checked_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Checked By")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="interaction_checks",
        null=True,
        blank=True,
        verbose_name=_("Patient")
    )
    
    # Medications checked
    medications_checked = models.JSONField(
        verbose_name=_("Medications Checked"),
        help_text=_("List of medications included in the check")
    )
    
    # Results
    interactions_found = models.ManyToManyField(
        DrugInteraction,
        blank=True,
        verbose_name=_("Interactions Found")
    )
    
    total_interactions = models.IntegerField(
        default=0,
        verbose_name=_("Total Interactions Found")
    )
    
    major_interactions = models.IntegerField(
        default=0,
        verbose_name=_("Major Interactions")
    )
    
    contraindicated_interactions = models.IntegerField(
        default=0,
        verbose_name=_("Contraindicated Interactions")
    )
    
    # Check metadata
    check_duration_ms = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Check Duration (ms)")
    )
    
    data_source = models.CharField(
        max_length=100,
        default="internal",
        verbose_name=_("Data Source"),
        help_text=_("Source of interaction data used")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    # Clinical decision
    clinical_decision = models.TextField(
        blank=True,
        verbose_name=_("Clinical Decision"),
        help_text=_("Clinical decision made based on interactions")
    )
    
    override_reason = models.TextField(
        blank=True,
        verbose_name=_("Override Reason"),
        help_text=_("Reason for overriding interaction warnings")
    )
    
    class Meta:
        verbose_name = _("Interaction Check")
        verbose_name_plural = _("Interaction Checks")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['checked_by', 'created_at']),
            models.Index(fields=['patient', 'created_at']),
            models.Index(fields=['total_interactions']),
        ]
    
    def __str__(self):
        patient_name = self.patient.get_full_name() if self.patient else "Unknown"
        return f"Interaction Check - {patient_name} ({self.created_at})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("checked_by"),
            FieldPanel("patient"),
            FieldPanel("medications_checked"),
        ], heading=_("Check Details")),
        
        MultiFieldPanel([
            FieldPanel("total_interactions"),
            FieldPanel("major_interactions"),
            FieldPanel("contraindicated_interactions"),
            FieldPanel("data_source"),
        ], heading=_("Results")),
        
        MultiFieldPanel([
            FieldPanel("clinical_decision"),
            FieldPanel("override_reason"),
        ], heading=_("Clinical Decision")),
    ]


@register_snippet
class DrugAllergy(models.Model):
    """Model for managing drug allergies and sensitivities."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="drug_allergies",
        verbose_name=_("Patient")
    )
    
    # Allergen information
    drug_name = models.CharField(
        max_length=255,
        verbose_name=_("Drug Name"),
        db_index=True
    )
    
    generic_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Generic Name")
    )
    
    drug_class = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Drug Class"),
        help_text=_("Pharmacological class of the drug")
    )
    
    # Allergy details
    allergy_type = models.CharField(
        max_length=50,
        choices=[
            ('allergy', _('True Allergy')),
            ('intolerance', _('Intolerance')),
            ('adverse_reaction', _('Adverse Reaction')),
            ('contraindication', _('Contraindication')),
        ],
        default='allergy',
        verbose_name=_("Allergy Type")
    )
    
    severity = models.CharField(
        max_length=20,
        choices=[
            ('mild', _('Mild')),
            ('moderate', _('Moderate')),
            ('severe', _('Severe')),
            ('life_threatening', _('Life Threatening')),
        ],
        verbose_name=_("Severity")
    )
    
    # Reaction details
    reaction_description = models.TextField(
        verbose_name=_("Reaction Description"),
        help_text=_("Description of the allergic reaction")
    )
    
    symptoms = models.JSONField(
        default=list,
        verbose_name=_("Symptoms"),
        help_text=_("List of symptoms experienced")
    )
    
    onset_time = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Onset Time"),
        help_text=_("Time from drug administration to reaction")
    )
    
    # Clinical information
    date_of_reaction = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Reaction")
    )
    
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_allergies",
        verbose_name=_("Reported By")
    )
    
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_allergies",
        verbose_name=_("Verified By"),
        limit_choices_to={'groups__name__in': ['Healthcare Providers', 'Clinical Pharmacists']}
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    # Cross-reactivity
    cross_reactive_drugs = models.JSONField(
        default=list,
        verbose_name=_("Cross-Reactive Drugs"),
        help_text=_("Drugs that may cause similar reactions")
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    notes = RichTextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Drug Allergy")
        verbose_name_plural = _("Drug Allergies")
        ordering = ["-severity", "drug_name"]
        indexes = [
            models.Index(fields=['patient', 'is_active']),
            models.Index(fields=['drug_name']),
            models.Index(fields=['severity']),
        ]
        unique_together = ['patient', 'drug_name']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.drug_name} ({self.get_severity_display()})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("patient"),
            FieldPanel("drug_name"),
            FieldPanel("generic_name"),
            FieldPanel("drug_class"),
        ], heading=_("Drug Information")),
        
        MultiFieldPanel([
            FieldPanel("allergy_type"),
            FieldPanel("severity"),
            FieldPanel("reaction_description"),
            FieldPanel("symptoms"),
            FieldPanel("onset_time"),
        ], heading=_("Allergy Details")),
        
        MultiFieldPanel([
            FieldPanel("date_of_reaction"),
            FieldPanel("reported_by"),
            FieldPanel("verified_by"),
            FieldPanel("is_verified"),
            FieldPanel("is_active"),
        ], heading=_("Clinical Information")),
        
        MultiFieldPanel([
            FieldPanel("cross_reactive_drugs"),
            FieldPanel("notes"),
        ], heading=_("Additional Information")),
    ]
