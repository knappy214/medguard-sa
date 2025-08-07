# Medication Management System in MedGuard SA

## Overview

This guide covers the comprehensive medication management system built on Wagtail 7.0.2 for MedGuard SA. The system manages medication information, drug interactions, inventory tracking, and patient medication profiles while ensuring compliance with South African healthcare regulations.

## Medication Data Models

### 1. Core Medication Model

```python
# medications/models.py
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from wagtail import blocks
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class MedicationPage(Page):
    """Main medication information page model"""
    
    # Basic Medication Information
    generic_name = models.CharField(
        max_length=200,
        help_text=_("International Non-proprietary Name (INN)")
    )
    
    brand_names = models.TextField(
        blank=True,
        help_text=_("Commercial brand names (one per line)")
    )
    
    medication_class = models.ForeignKey(
        'medications.MedicationClass',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Regulatory Information
    sahpra_registration = models.CharField(
        max_length=20,
        blank=True,
        help_text=_("SAHPRA registration number")
    )
    
    schedule_status = models.CharField(
        max_length=20,
        choices=[
            ('schedule_0', _('Schedule 0 - General Sale')),
            ('schedule_1', _('Schedule 1 - Pharmacy Medicine')),
            ('schedule_2', _('Schedule 2 - Pharmacy Medicine')),
            ('schedule_3', _('Schedule 3 - Prescription Medicine')),
            ('schedule_4', _('Schedule 4 - Prescription Medicine')),
            ('schedule_5', _('Schedule 5 - Controlled Substance')),
            ('schedule_6', _('Schedule 6 - Controlled Substance')),
            ('schedule_7', _('Schedule 7 - Controlled Substance')),
            ('schedule_8', _('Schedule 8 - Controlled Substance')),
        ],
        default='schedule_0'
    )
    
    # Clinical Information
    active_ingredients = StreamField([
        ('ingredient', blocks.StructBlock([
            ('name', blocks.CharBlock(max_length=200)),
            ('strength', blocks.CharBlock(max_length=100)),
            ('unit', blocks.ChoiceBlock(choices=[
                ('mg', 'mg'),
                ('g', 'g'),
                ('ml', 'ml'),
                ('mcg', 'mcg'),
                ('units', 'units'),
                ('iu', 'IU'),
            ])),
        ]))
    ], blank=True, use_json_field=True)
    
    # Detailed Content
    content = StreamField([
        ('indication', blocks.StructBlock([
            ('condition', blocks.CharBlock(max_length=200)),
            ('description', blocks.RichTextBlock()),
            ('evidence_level', blocks.ChoiceBlock(choices=[
                ('A', _('Strong evidence')),
                ('B', _('Moderate evidence')),
                ('C', _('Limited evidence')),
                ('D', _('Expert opinion')),
            ])),
        ])),
        ('contraindication', blocks.StructBlock([
            ('condition', blocks.CharBlock(max_length=200)),
            ('severity', blocks.ChoiceBlock(choices=[
                ('absolute', _('Absolute contraindication')),
                ('relative', _('Relative contraindication')),
            ])),
            ('description', blocks.RichTextBlock()),
        ])),
        ('dosing', blocks.StructBlock([
            ('population', blocks.ChoiceBlock(choices=[
                ('adult', _('Adult')),
                ('pediatric', _('Pediatric')),
                ('elderly', _('Elderly')),
                ('renal_impairment', _('Renal Impairment')),
                ('hepatic_impairment', _('Hepatic Impairment')),
            ])),
            ('route', blocks.ChoiceBlock(choices=[
                ('oral', _('Oral')),
                ('iv', _('Intravenous')),
                ('im', _('Intramuscular')),
                ('sc', _('Subcutaneous')),
                ('topical', _('Topical')),
                ('inhalation', _('Inhalation')),
            ])),
            ('dose', blocks.CharBlock(max_length=200)),
            ('frequency', blocks.CharBlock(max_length=100)),
            ('duration', blocks.CharBlock(max_length=100)),
            ('notes', blocks.RichTextBlock(required=False)),
        ])),
        ('side_effect', blocks.StructBlock([
            ('effect', blocks.CharBlock(max_length=200)),
            ('frequency', blocks.ChoiceBlock(choices=[
                ('very_common', _('>10% - Very Common')),
                ('common', _('1-10% - Common')),
                ('uncommon', _('0.1-1% - Uncommon')),
                ('rare', _('0.01-0.1% - Rare')),
                ('very_rare', _('<0.01% - Very Rare')),
            ])),
            ('severity', blocks.ChoiceBlock(choices=[
                ('mild', _('Mild')),
                ('moderate', _('Moderate')),
                ('severe', _('Severe')),
                ('life_threatening', _('Life Threatening')),
            ])),
            ('description', blocks.RichTextBlock()),
        ])),
        ('interaction', blocks.StructBlock([
            ('interacting_drug', blocks.PageChooserBlock(
                page_type='medications.MedicationPage',
                required=False
            )),
            ('interaction_type', blocks.ChoiceBlock(choices=[
                ('contraindicated', _('Contraindicated')),
                ('major', _('Major')),
                ('moderate', _('Moderate')),
                ('minor', _('Minor')),
            ])),
            ('mechanism', blocks.TextBlock()),
            ('clinical_effect', blocks.RichTextBlock()),
            ('management', blocks.RichTextBlock()),
        ])),
        ('monitoring', blocks.StructBlock([
            ('parameter', blocks.CharBlock(max_length=200)),
            ('frequency', blocks.CharBlock(max_length=100)),
            ('normal_range', blocks.CharBlock(max_length=100)),
            ('action_required', blocks.RichTextBlock()),
        ])),
    ], blank=True, use_json_field=True)
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    medical_reviewer = models.ForeignKey(
        'users.Physician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_medications'
    )
    
    review_date = models.DateField(null=True, blank=True)
    
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('generic_name'),
            FieldPanel('brand_names'),
            FieldPanel('medication_class'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('sahpra_registration'),
            FieldPanel('schedule_status'),
        ], heading=_("Regulatory Information")),
        
        FieldPanel('active_ingredients'),
        FieldPanel('content'),
        
        MultiFieldPanel([
            FieldPanel('medical_reviewer'),
            FieldPanel('review_date'),
        ], heading=_("Review Information")),
    ]
    
    class Meta:
        verbose_name = _("Medication")
        verbose_name_plural = _("Medications")
    
    def get_brand_names_list(self):
        """Return brand names as a list"""
        return [name.strip() for name in self.brand_names.split('\n') if name.strip()]
    
    def get_active_ingredients_list(self):
        """Return active ingredients as a formatted list"""
        ingredients = []
        for ingredient_block in self.active_ingredients:
            if ingredient_block.block_type == 'ingredient':
                value = ingredient_block.value
                ingredients.append(f"{value['name']} {value['strength']}{value['unit']}")
        return ingredients

@register_snippet
class MedicationClass(models.Model):
    """Therapeutic classification of medications"""
    
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    parent_class = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subclasses'
    )
    
    class Meta:
        verbose_name = _("Medication Class")
        verbose_name_plural = _("Medication Classes")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

@register_snippet
class DrugInteraction(models.Model):
    """Drug-drug interaction model"""
    
    INTERACTION_SEVERITY = [
        ('contraindicated', _('Contraindicated')),
        ('major', _('Major')),
        ('moderate', _('Moderate')),
        ('minor', _('Minor')),
    ]
    
    medication_a = models.ForeignKey(
        MedicationPage,
        on_delete=models.CASCADE,
        related_name='interactions_as_a'
    )
    
    medication_b = models.ForeignKey(
        MedicationPage,
        on_delete=models.CASCADE,
        related_name='interactions_as_b'
    )
    
    severity = models.CharField(
        max_length=20,
        choices=INTERACTION_SEVERITY
    )
    
    mechanism = models.TextField(
        help_text=_("Mechanism of interaction")
    )
    
    clinical_effect = models.TextField(
        help_text=_("Clinical effect of the interaction")
    )
    
    management = models.TextField(
        help_text=_("Management recommendations")
    )
    
    evidence_level = models.CharField(
        max_length=1,
        choices=[
            ('A', _('Strong evidence')),
            ('B', _('Moderate evidence')),
            ('C', _('Limited evidence')),
            ('D', _('Expert opinion')),
        ],
        default='C'
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("Drug Interaction")
        verbose_name_plural = _("Drug Interactions")
        unique_together = ['medication_a', 'medication_b']
    
    def __str__(self):
        return f"{self.medication_a.generic_name} + {self.medication_b.generic_name}"
```

### 2. Patient Medication Profile

```python
# medications/models.py (continued)
class PatientMedicationProfile(models.Model):
    """Patient's medication profile and history"""
    
    patient = models.OneToOneField(
        'users.Patient',
        on_delete=models.CASCADE,
        related_name='medication_profile'
    )
    
    allergies = models.ManyToManyField(
        'medications.Allergy',
        blank=True,
        related_name='patients'
    )
    
    current_medications = models.ManyToManyField(
        'medications.PatientMedication',
        blank=True,
        related_name='current_profiles'
    )
    
    medical_conditions = models.TextField(
        blank=True,
        help_text=_("Current medical conditions")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Patient Medication Profile")
        verbose_name_plural = _("Patient Medication Profiles")
    
    def get_drug_interactions(self):
        """Check for drug interactions in current medications"""
        interactions = []
        current_meds = list(self.current_medications.all())
        
        for i, med_a in enumerate(current_meds):
            for med_b in current_meds[i+1:]:
                # Check for interactions between med_a and med_b
                interaction = DrugInteraction.objects.filter(
                    models.Q(medication_a=med_a.medication, medication_b=med_b.medication) |
                    models.Q(medication_a=med_b.medication, medication_b=med_a.medication),
                    is_active=True
                ).first()
                
                if interaction:
                    interactions.append(interaction)
        
        return interactions
    
    def check_allergies(self, medication):
        """Check if patient is allergic to medication"""
        for allergy in self.allergies.all():
            if allergy.is_allergic_to(medication):
                return allergy
        return None

class PatientMedication(models.Model):
    """Individual medication in patient's profile"""
    
    patient_profile = models.ForeignKey(
        PatientMedicationProfile,
        on_delete=models.CASCADE,
        related_name='medications'
    )
    
    medication = models.ForeignKey(
        MedicationPage,
        on_delete=models.CASCADE
    )
    
    dosage = models.CharField(
        max_length=200,
        help_text=_("Current dosage")
    )
    
    frequency = models.CharField(
        max_length=100,
        help_text=_("Frequency of administration")
    )
    
    route = models.CharField(
        max_length=50,
        choices=[
            ('oral', _('Oral')),
            ('iv', _('Intravenous')),
            ('im', _('Intramuscular')),
            ('sc', _('Subcutaneous')),
            ('topical', _('Topical')),
            ('inhalation', _('Inhalation')),
        ],
        default='oral'
    )
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    
    prescribing_physician = models.ForeignKey(
        'users.Physician',
        on_delete=models.CASCADE
    )
    
    indication = models.CharField(
        max_length=200,
        help_text=_("Reason for prescription")
    )
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("Patient Medication")
        verbose_name_plural = _("Patient Medications")
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.medication.generic_name} - {self.dosage}"

@register_snippet
class Allergy(models.Model):
    """Patient allergy information"""
    
    ALLERGY_TYPES = [
        ('drug', _('Drug Allergy')),
        ('food', _('Food Allergy')),
        ('environmental', _('Environmental Allergy')),
    ]
    
    SEVERITY_LEVELS = [
        ('mild', _('Mild')),
        ('moderate', _('Moderate')),
        ('severe', _('Severe')),
        ('life_threatening', _('Life Threatening')),
    ]
    
    name = models.CharField(max_length=200)
    allergy_type = models.CharField(max_length=20, choices=ALLERGY_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS)
    
    # Related medications (for cross-allergies)
    related_medications = models.ManyToManyField(
        MedicationPage,
        blank=True,
        related_name='allergies'
    )
    
    symptoms = models.TextField(
        blank=True,
        help_text=_("Typical allergic reactions")
    )
    
    class Meta:
        verbose_name = _("Allergy")
        verbose_name_plural = _("Allergies")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_severity_display()})"
    
    def is_allergic_to(self, medication):
        """Check if this allergy applies to a medication"""
        return self.related_medications.filter(pk=medication.pk).exists()
```

## Medication Inventory Management

### 1. Pharmacy Inventory Model

```python
# medications/inventory.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

class Pharmacy(models.Model):
    """Pharmacy model for inventory management"""
    
    name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Operating hours
    operating_hours = models.JSONField(
        default=dict,
        help_text=_("Operating hours for each day of the week")
    )
    
    # Compliance
    is_authorized = models.BooleanField(default=True)
    sahpra_license = models.CharField(max_length=50, blank=True)
    
    # Location
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Pharmacy")
        verbose_name_plural = _("Pharmacies")
        ordering = ['name']
    
    def __str__(self):
        return self.name

class MedicationInventory(models.Model):
    """Medication inventory for pharmacies"""
    
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name='inventory'
    )
    
    medication = models.ForeignKey(
        MedicationPage,
        on_delete=models.CASCADE
    )
    
    # Stock information
    current_stock = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )
    
    minimum_stock_level = models.PositiveIntegerField(
        default=10,
        help_text=_("Minimum stock level for reorder alerts")
    )
    
    maximum_stock_level = models.PositiveIntegerField(
        default=1000,
        help_text=_("Maximum stock level")
    )
    
    # Batch information
    batch_number = models.CharField(max_length=50)
    expiry_date = models.DateField()
    manufacturer = models.CharField(max_length=200)
    
    # Pricing
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Tracking
    last_restock_date = models.DateTimeField(null=True, blank=True)
    last_dispensed_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Medication Inventory")
        verbose_name_plural = _("Medication Inventories")
        unique_together = ['pharmacy', 'medication', 'batch_number']
        ordering = ['expiry_date']
    
    def __str__(self):
        return f"{self.medication.generic_name} - {self.pharmacy.name}"
    
    def is_low_stock(self):
        """Check if stock is below minimum level"""
        return self.current_stock <= self.minimum_stock_level
    
    def is_expired(self):
        """Check if medication is expired"""
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()
    
    def is_near_expiry(self, days=30):
        """Check if medication expires within specified days"""
        from django.utils import timezone
        from datetime import timedelta
        
        expiry_threshold = timezone.now().date() + timedelta(days=days)
        return self.expiry_date <= expiry_threshold

class InventoryTransaction(models.Model):
    """Track inventory transactions"""
    
    TRANSACTION_TYPES = [
        ('restock', _('Restock')),
        ('dispensing', _('Dispensing')),
        ('adjustment', _('Adjustment')),
        ('expired', _('Expired')),
        ('returned', _('Returned')),
    ]
    
    inventory = models.ForeignKey(
        MedicationInventory,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    
    quantity = models.IntegerField(
        help_text=_("Positive for stock increase, negative for decrease")
    )
    
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("Reference number (e.g., prescription number)")
    )
    
    notes = models.TextField(blank=True)
    
    performed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Inventory Transaction")
        verbose_name_plural = _("Inventory Transactions")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.quantity}"
```

## Medication Search and Filtering

### 1. Advanced Search Functionality

```python
# medications/search.py
from wagtail.search import index
from django.db import models
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

class MedicationSearchMixin:
    """Mixin for medication search functionality"""
    
    @classmethod
    def search_medications(cls, query, filters=None):
        """Advanced medication search"""
        queryset = cls.objects.live().public()
        
        if query:
            # Use PostgreSQL full-text search
            search_vector = SearchVector(
                'title', weight='A',
                'generic_name', weight='A',
                'brand_names', weight='B',
                'content', weight='C'
            )
            
            search_query = SearchQuery(query)
            
            queryset = queryset.annotate(
                search=search_vector,
                rank=SearchRank(search_vector, search_query)
            ).filter(search=search_query).order_by('-rank')
        
        # Apply filters
        if filters:
            if filters.get('medication_class'):
                queryset = queryset.filter(
                    medication_class=filters['medication_class']
                )
            
            if filters.get('schedule_status'):
                queryset = queryset.filter(
                    schedule_status=filters['schedule_status']
                )
            
            if filters.get('active_ingredient'):
                queryset = queryset.filter(
                    active_ingredients__icontains=filters['active_ingredient']
                )
        
        return queryset
    
    @classmethod
    def get_medication_suggestions(cls, partial_query, limit=10):
        """Get medication name suggestions for autocomplete"""
        suggestions = []
        
        # Search in generic names
        generic_matches = cls.objects.filter(
            generic_name__icontains=partial_query
        ).values_list('generic_name', flat=True)[:limit]
        
        suggestions.extend(generic_matches)
        
        # Search in brand names
        brand_matches = cls.objects.filter(
            brand_names__icontains=partial_query
        ).values_list('title', flat=True)[:limit]
        
        suggestions.extend(brand_matches)
        
        return list(set(suggestions))[:limit]

# Add search mixin to MedicationPage
MedicationPage.__bases__ += (MedicationSearchMixin,)

# Update search fields
MedicationPage.search_fields = Page.search_fields + [
    index.SearchField('generic_name', partial_match=True),
    index.SearchField('brand_names', partial_match=True),
    index.SearchField('content'),
    index.FilterField('medication_class'),
    index.FilterField('schedule_status'),
]
```

### 2. Drug Interaction Checker

```python
# medications/interaction_checker.py
from django.db import models
from typing import List, Dict, Any

class DrugInteractionChecker:
    """Service for checking drug interactions"""
    
    @staticmethod
    def check_interactions(medications: List[MedicationPage]) -> List[Dict[str, Any]]:
        """Check for interactions between medications"""
        interactions = []
        
        for i, med_a in enumerate(medications):
            for med_b in medications[i+1:]:
                interaction = DrugInteraction.objects.filter(
                    models.Q(medication_a=med_a, medication_b=med_b) |
                    models.Q(medication_a=med_b, medication_b=med_a),
                    is_active=True
                ).first()
                
                if interaction:
                    interactions.append({
                        'medication_a': med_a,
                        'medication_b': med_b,
                        'severity': interaction.severity,
                        'mechanism': interaction.mechanism,
                        'clinical_effect': interaction.clinical_effect,
                        'management': interaction.management,
                        'evidence_level': interaction.evidence_level,
                    })
        
        return sorted(interactions, key=lambda x: x['severity'])
    
    @staticmethod
    def check_patient_interactions(patient_profile: PatientMedicationProfile) -> List[Dict[str, Any]]:
        """Check interactions for patient's current medications"""
        current_medications = [
            pm.medication for pm in patient_profile.current_medications.filter(is_active=True)
        ]
        
        return DrugInteractionChecker.check_interactions(current_medications)
    
    @staticmethod
    def check_new_medication_interactions(
        patient_profile: PatientMedicationProfile,
        new_medication: MedicationPage
    ) -> List[Dict[str, Any]]:
        """Check interactions when adding a new medication"""
        current_medications = [
            pm.medication for pm in patient_profile.current_medications.filter(is_active=True)
        ]
        current_medications.append(new_medication)
        
        return DrugInteractionChecker.check_interactions(current_medications)
```

## Medication Dosage Calculator

### 1. Dosage Calculation Service

```python
# medications/dosage_calculator.py
from decimal import Decimal
from typing import Dict, Any, Optional
import re

class DosageCalculator:
    """Service for calculating medication dosages"""
    
    @staticmethod
    def calculate_pediatric_dose(
        adult_dose: str,
        child_weight: Decimal,
        calculation_method: str = 'clark'
    ) -> Dict[str, Any]:
        """Calculate pediatric dose based on adult dose"""
        
        # Extract dose amount and unit from string
        dose_match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', adult_dose)
        if not dose_match:
            return {'error': 'Invalid adult dose format'}
        
        adult_amount = Decimal(dose_match.group(1))
        unit = dose_match.group(2)
        
        if calculation_method == 'clark':
            # Clark's rule: Child dose = (Weight in kg / 70) × Adult dose
            child_dose = (child_weight / Decimal('70')) * adult_amount
        elif calculation_method == 'young':
            # Young's rule: Child dose = (Age / (Age + 12)) × Adult dose
            # Note: This requires age, not implemented here
            return {'error': 'Young\'s rule requires age parameter'}
        else:
            return {'error': 'Unknown calculation method'}
        
        return {
            'calculated_dose': f"{child_dose:.2f} {unit}",
            'method_used': calculation_method,
            'adult_dose': adult_dose,
            'child_weight': str(child_weight),
        }
    
    @staticmethod
    def calculate_renal_adjustment(
        normal_dose: str,
        creatinine_clearance: Decimal
    ) -> Dict[str, Any]:
        """Calculate dose adjustment for renal impairment"""
        
        # Extract dose amount
        dose_match = re.match(r'(\d+(?:\.\d+)?)\s*(\w+)', normal_dose)
        if not dose_match:
            return {'error': 'Invalid dose format'}
        
        normal_amount = Decimal(dose_match.group(1))
        unit = dose_match.group(2)
        
        # Simplified renal adjustment (actual implementation would be drug-specific)
        if creatinine_clearance >= 50:
            adjustment_factor = Decimal('1.0')  # No adjustment
        elif creatinine_clearance >= 30:
            adjustment_factor = Decimal('0.75')  # 75% of normal dose
        elif creatinine_clearance >= 15:
            adjustment_factor = Decimal('0.5')   # 50% of normal dose
        else:
            adjustment_factor = Decimal('0.25')  # 25% of normal dose
        
        adjusted_dose = normal_amount * adjustment_factor
        
        return {
            'adjusted_dose': f"{adjusted_dose:.2f} {unit}",
            'normal_dose': normal_dose,
            'creatinine_clearance': str(creatinine_clearance),
            'adjustment_factor': str(adjustment_factor),
            'recommendation': DosageCalculator._get_renal_recommendation(creatinine_clearance)
        }
    
    @staticmethod
    def _get_renal_recommendation(creatinine_clearance: Decimal) -> str:
        """Get recommendation based on creatinine clearance"""
        if creatinine_clearance >= 50:
            return "Normal dose"
        elif creatinine_clearance >= 30:
            return "Reduce dose to 75% or increase dosing interval"
        elif creatinine_clearance >= 15:
            return "Reduce dose to 50% or significantly increase dosing interval"
        else:
            return "Use with extreme caution - consider alternative therapy"
```

## Medication Adherence Tracking

### 1. Adherence Monitoring

```python
# medications/adherence.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
from typing import Dict, Any

class MedicationAdherence(models.Model):
    """Track patient medication adherence"""
    
    patient_medication = models.ForeignKey(
        PatientMedication,
        on_delete=models.CASCADE,
        related_name='adherence_records'
    )
    
    scheduled_date = models.DateTimeField()
    taken_date = models.DateTimeField(null=True, blank=True)
    
    was_taken = models.BooleanField(default=False)
    missed_reason = models.CharField(
        max_length=200,
        blank=True,
        choices=[
            ('forgot', _('Forgot to take')),
            ('side_effects', _('Side effects')),
            ('feeling_better', _('Feeling better')),
            ('cost', _('Cost concerns')),
            ('other', _('Other')),
        ]
    )
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Medication Adherence")
        verbose_name_plural = _("Medication Adherence Records")
        ordering = ['-scheduled_date']
    
    def __str__(self):
        status = "Taken" if self.was_taken else "Missed"
        return f"{self.patient_medication} - {status}"

class AdherenceAnalytics:
    """Analytics for medication adherence"""
    
    @staticmethod
    def calculate_adherence_rate(
        patient_medication: PatientMedication,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Calculate adherence rate for a specific medication"""
        
        start_date = timezone.now() - timedelta(days=period_days)
        
        adherence_records = MedicationAdherence.objects.filter(
            patient_medication=patient_medication,
            scheduled_date__gte=start_date
        )
        
        total_doses = adherence_records.count()
        taken_doses = adherence_records.filter(was_taken=True).count()
        
        if total_doses == 0:
            return {'adherence_rate': 0, 'total_doses': 0, 'taken_doses': 0}
        
        adherence_rate = (taken_doses / total_doses) * 100
        
        return {
            'adherence_rate': round(adherence_rate, 2),
            'total_doses': total_doses,
            'taken_doses': taken_doses,
            'missed_doses': total_doses - taken_doses,
            'period_days': period_days,
        }
    
    @staticmethod
    def get_adherence_trends(
        patient_profile: PatientMedicationProfile,
        period_days: int = 90
    ) -> Dict[str, Any]:
        """Get adherence trends for all patient medications"""
        
        trends = {}
        
        for patient_med in patient_profile.current_medications.filter(is_active=True):
            trends[patient_med.id] = AdherenceAnalytics.calculate_adherence_rate(
                patient_med, period_days
            )
        
        return trends
```

## Wagtail Admin Integration

### 1. Medication Admin Interface

```python
# medications/wagtail_hooks.py
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.contrib.modeladmin.views import CreateView, EditView
from wagtail import hooks
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _

class MedicationAdmin(ModelAdmin):
    """Wagtail admin for medications"""
    
    model = MedicationPage
    menu_label = _('Medications')
    menu_icon = 'pill'
    menu_order = 100
    
    list_display = [
        'title', 'generic_name', 'medication_class',
        'schedule_status', 'last_updated'
    ]
    
    list_filter = ['medication_class', 'schedule_status', 'last_updated']
    search_fields = ['title', 'generic_name', 'brand_names']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('medication_class')

class DrugInteractionAdmin(ModelAdmin):
    """Admin for drug interactions"""
    
    model = DrugInteraction
    menu_label = _('Drug Interactions')
    menu_icon = 'warning'
    menu_order = 110
    
    list_display = [
        'medication_a', 'medication_b', 'severity',
        'evidence_level', 'is_active'
    ]
    
    list_filter = ['severity', 'evidence_level', 'is_active']
    search_fields = [
        'medication_a__generic_name',
        'medication_b__generic_name'
    ]

class PharmacyAdmin(ModelAdmin):
    """Admin for pharmacies"""
    
    model = Pharmacy
    menu_label = _('Pharmacies')
    menu_icon = 'site'
    menu_order = 120
    
    list_display = [
        'name', 'license_number', 'phone',
        'is_authorized', 'created_at'
    ]
    
    list_filter = ['is_authorized', 'created_at']
    search_fields = ['name', 'license_number', 'address']

class InventoryAdmin(ModelAdmin):
    """Admin for medication inventory"""
    
    model = MedicationInventory
    menu_label = _('Inventory')
    menu_icon = 'list-ul'
    menu_order = 130
    
    list_display = [
        'medication', 'pharmacy', 'current_stock',
        'minimum_stock_level', 'expiry_date'
    ]
    
    list_filter = ['pharmacy', 'expiry_date']
    search_fields = ['medication__generic_name', 'pharmacy__name']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('medication', 'pharmacy')

# Register admin classes
modeladmin_register(MedicationAdmin)
modeladmin_register(DrugInteractionAdmin)
modeladmin_register(PharmacyAdmin)
modeladmin_register(InventoryAdmin)

@hooks.register('register_admin_menu_item')
def register_medication_menu():
    from wagtail.admin.menu import Menu, MenuItem, SubmenuMenuItem
    
    return SubmenuMenuItem(
        _('Medication Management'),
        Menu([
            MenuItem(_('Medications'), reverse('wagtail_modeladmin_medications_medicationpage_index')),
            MenuItem(_('Drug Interactions'), reverse('wagtail_modeladmin_medications_druginteraction_index')),
            MenuItem(_('Pharmacies'), reverse('wagtail_modeladmin_medications_pharmacy_index')),
            MenuItem(_('Inventory'), reverse('wagtail_modeladmin_medications_medicationinventory_index')),
        ]),
        icon_name='pill'
    )
```

### 2. Custom Dashboard Widgets

```python
# medications/dashboard.py
from wagtail.admin.ui.components import Component
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta

class MedicationDashboardWidget(Component):
    """Dashboard widget for medication management"""
    
    def render_html(self, parent_context):
        # Get medication statistics
        total_medications = MedicationPage.objects.live().count()
        
        # Low stock alerts
        low_stock_items = MedicationInventory.objects.filter(
            current_stock__lte=models.F('minimum_stock_level')
        ).count()
        
        # Expiring medications
        thirty_days = timezone.now().date() + timedelta(days=30)
        expiring_items = MedicationInventory.objects.filter(
            expiry_date__lte=thirty_days
        ).count()
        
        # Recent interactions added
        recent_interactions = DrugInteraction.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        context = {
            'total_medications': total_medications,
            'low_stock_items': low_stock_items,
            'expiring_items': expiring_items,
            'recent_interactions': recent_interactions,
        }
        
        return render_to_string(
            'admin/medication_dashboard_widget.html',
            context
        )

@hooks.register('construct_homepage_panels')
def add_medication_dashboard_widget(request, panels):
    panels.append(MedicationDashboardWidget())
```

## API Integration

### 1. Medication API Endpoints

```python
# api/medication_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.translation import gettext_lazy as _

class MedicationViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for medications"""
    
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MedicationPage.objects.live().public().select_related('medication_class')
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search medications"""
        query = request.query_params.get('q', '')
        filters = {
            'medication_class': request.query_params.get('class'),
            'schedule_status': request.query_params.get('schedule'),
        }
        
        medications = MedicationPage.search_medications(query, filters)
        serializer = self.get_serializer(medications, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Get medication name suggestions"""
        query = request.query_params.get('q', '')
        suggestions = MedicationPage.get_medication_suggestions(query)
        
        return Response({'suggestions': suggestions})
    
    @action(detail=True, methods=['get'])
    def interactions(self, request, pk=None):
        """Get drug interactions for medication"""
        medication = self.get_object()
        
        interactions = DrugInteraction.objects.filter(
            models.Q(medication_a=medication) | models.Q(medication_b=medication),
            is_active=True
        )
        
        serializer = DrugInteractionSerializer(interactions, many=True)
        return Response(serializer.data)

class DrugInteractionViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for drug interactions"""
    
    serializer_class = DrugInteractionSerializer
    permission_classes = [IsAuthenticated]
    queryset = DrugInteraction.objects.filter(is_active=True)
    
    @action(detail=False, methods=['post'])
    def check_interactions(self, request):
        """Check interactions between medications"""
        medication_ids = request.data.get('medication_ids', [])
        
        if not medication_ids:
            return Response(
                {'error': _('Medication IDs required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        medications = MedicationPage.objects.filter(id__in=medication_ids)
        interactions = DrugInteractionChecker.check_interactions(list(medications))
        
        return Response({
            'interactions': interactions,
            'total_interactions': len(interactions)
        })

class PharmacyViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for pharmacies"""
    
    serializer_class = PharmacySerializer
    permission_classes = [IsAuthenticated]
    queryset = Pharmacy.objects.filter(is_authorized=True)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find nearby pharmacies"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = float(request.query_params.get('radius', 10))  # km
        
        if not lat or not lng:
            return Response(
                {'error': _('Latitude and longitude required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use PostGIS for geographic queries in production
        # For now, simple distance calculation
        pharmacies = self.get_queryset()
        
        # Filter by availability of specific medication if provided
        medication_id = request.query_params.get('medication_id')
        if medication_id:
            pharmacies = pharmacies.filter(
                inventory__medication_id=medication_id,
                inventory__current_stock__gt=0
            )
        
        serializer = self.get_serializer(pharmacies, many=True)
        return Response(serializer.data)
```

## Testing

### 1. Medication Management Tests

```python
# medications/tests/test_medication_management.py
from django.test import TestCase
from django.utils import timezone
from medications.models import MedicationPage, DrugInteraction, PatientMedicationProfile
from medications.interaction_checker import DrugInteractionChecker

class MedicationManagementTest(TestCase):
    """Test medication management functionality"""
    
    def setUp(self):
        # Create test medications
        self.medication_a = self.create_test_medication("Warfarin")
        self.medication_b = self.create_test_medication("Aspirin")
        
        # Create test interaction
        self.interaction = DrugInteraction.objects.create(
            medication_a=self.medication_a,
            medication_b=self.medication_b,
            severity='major',
            mechanism='Increased bleeding risk',
            clinical_effect='Enhanced anticoagulant effect',
            management='Monitor INR closely'
        )
    
    def test_drug_interaction_detection(self):
        """Test drug interaction detection"""
        medications = [self.medication_a, self.medication_b]
        interactions = DrugInteractionChecker.check_interactions(medications)
        
        self.assertEqual(len(interactions), 1)
        self.assertEqual(interactions[0]['severity'], 'major')
    
    def test_medication_search(self):
        """Test medication search functionality"""
        results = MedicationPage.search_medications('Warfarin')
        self.assertIn(self.medication_a, results)
    
    def test_patient_medication_profile(self):
        """Test patient medication profile"""
        patient = self.create_test_patient()
        profile = PatientMedicationProfile.objects.create(patient=patient)
        
        # Add medications to profile
        patient_med_a = self.create_patient_medication(profile, self.medication_a)
        patient_med_b = self.create_patient_medication(profile, self.medication_b)
        
        # Check for interactions
        interactions = profile.get_drug_interactions()
        self.assertEqual(len(interactions), 1)
```

## Next Steps

1. **Security Implementation**: See `wagtail_security.md`
2. **API Documentation**: Review `wagtail_api.md`
3. **Compliance Setup**: Follow `wagtail_compliance.md`
4. **Deployment Guide**: Check `wagtail_deployment.md`

## Resources

- [SAHPRA Medication Guidelines](https://www.sahpra.org.za/)
- [South African Pharmacy Council](https://www.sapc.za.org/)
- [WHO Drug Information](https://www.who.int/medicines/publications/druginformation/en/)
- [Wagtail Documentation](https://docs.wagtail.io/)
