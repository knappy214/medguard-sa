# Healthcare Content Management Guide for MedGuard SA

## Overview

This guide covers content management best practices for healthcare information in Wagtail 7.0.2, ensuring compliance with healthcare regulations while maintaining user-friendly content creation workflows.

## Content Types and Models

### 1. Healthcare Page Models

#### Base Healthcare Page

```python
# home/models.py
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail import blocks
from django.utils.translation import gettext_lazy as _

class HealthcareBasePage(Page):
    """Base class for all healthcare-related pages"""
    
    class Meta:
        abstract = True
    
    # Medical disclaimer
    medical_disclaimer = RichTextField(
        blank=True,
        help_text=_("Standard medical disclaimer text"),
        default=_("This information is for educational purposes only and should not replace professional medical advice.")
    )
    
    # Last medical review
    last_medical_review = models.DateField(
        null=True,
        blank=True,
        help_text=_("Date of last medical review")
    )
    
    # Reviewing physician
    reviewing_physician = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Name and credentials of reviewing physician")
    )
    
    # Content panels
    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('medical_disclaimer'),
            FieldPanel('last_medical_review'),
            FieldPanel('reviewing_physician'),
        ], heading=_("Medical Review Information"))
    ]
```

#### Medication Information Page

```python
# medications/models.py
from wagtail.models import Page
from wagtail.fields import StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.snippets.models import register_snippet
from django.db import models
from django.utils.translation import gettext_lazy as _

class MedicationPage(HealthcareBasePage):
    """Page model for medication information"""
    
    # Basic medication information
    generic_name = models.CharField(
        max_length=200,
        help_text=_("Generic/scientific name of the medication")
    )
    
    brand_names = models.TextField(
        blank=True,
        help_text=_("Common brand names (one per line)")
    )
    
    medication_class = models.CharField(
        max_length=100,
        help_text=_("Therapeutic class (e.g., ACE Inhibitor)")
    )
    
    # Structured content using StreamField
    content = StreamField([
        ('heading', blocks.CharBlock(form_classname="title")),
        ('paragraph', blocks.RichTextBlock()),
        ('medication_info', MedicationInfoBlock()),
        ('dosage_info', DosageInfoBlock()),
        ('side_effects', SideEffectsBlock()),
        ('interactions', InteractionsBlock()),
        ('warnings', WarningsBlock()),
        ('storage_info', StorageInfoBlock()),
    ], blank=True, use_json_field=True)
    
    # SEO and metadata
    search_description = models.CharField(
        max_length=160,
        blank=True,
        help_text=_("Brief description for search engines")
    )
    
    content_panels = HealthcareBasePage.content_panels + [
        MultiFieldPanel([
            FieldPanel('generic_name'),
            FieldPanel('brand_names'),
            FieldPanel('medication_class'),
        ], heading=_("Basic Information")),
        
        FieldPanel('content'),
        
        MultiFieldPanel([
            FieldPanel('search_description'),
        ], heading=_("SEO")),
    ]
    
    class Meta:
        verbose_name = _("Medication Information Page")
        verbose_name_plural = _("Medication Information Pages")
```

### 2. Healthcare Content Blocks

#### Medication Information Block

```python
# medications/blocks.py
from wagtail import blocks
from django.utils.translation import gettext_lazy as _

class MedicationInfoBlock(blocks.StructBlock):
    """Block for structured medication information"""
    
    indication = blocks.TextBlock(
        required=True,
        help_text=_("What this medication is used for")
    )
    
    mechanism = blocks.RichTextBlock(
        required=False,
        help_text=_("How this medication works")
    )
    
    onset_of_action = blocks.CharBlock(
        required=False,
        max_length=100,
        help_text=_("How quickly the medication starts working")
    )
    
    duration = blocks.CharBlock(
        required=False,
        max_length=100,
        help_text=_("How long the medication lasts")
    )
    
    class Meta:
        icon = 'pill'
        label = _('Medication Information')
        template = 'blocks/medication_info_block.html'

class DosageInfoBlock(blocks.StructBlock):
    """Block for dosage information"""
    
    adult_dose = blocks.RichTextBlock(
        required=True,
        help_text=_("Standard adult dosage")
    )
    
    pediatric_dose = blocks.RichTextBlock(
        required=False,
        help_text=_("Pediatric dosage (if applicable)")
    )
    
    elderly_dose = blocks.RichTextBlock(
        required=False,
        help_text=_("Elderly dosage adjustments")
    )
    
    renal_adjustment = blocks.RichTextBlock(
        required=False,
        help_text=_("Dose adjustments for kidney disease")
    )
    
    hepatic_adjustment = blocks.RichTextBlock(
        required=False,
        help_text=_("Dose adjustments for liver disease")
    )
    
    class Meta:
        icon = 'list-ul'
        label = _('Dosage Information')
        template = 'blocks/dosage_info_block.html'

class SideEffectsBlock(blocks.StructBlock):
    """Block for side effects information"""
    
    common_side_effects = blocks.ListBlock(
        blocks.CharBlock(max_length=200),
        help_text=_("Common side effects (>10% incidence)")
    )
    
    serious_side_effects = blocks.ListBlock(
        blocks.CharBlock(max_length=200),
        help_text=_("Serious side effects requiring immediate attention")
    )
    
    rare_side_effects = blocks.ListBlock(
        blocks.CharBlock(max_length=200),
        help_text=_("Rare side effects (<1% incidence)")
    )
    
    class Meta:
        icon = 'warning'
        label = _('Side Effects')
        template = 'blocks/side_effects_block.html'

class InteractionsBlock(blocks.StructBlock):
    """Block for drug interactions"""
    
    major_interactions = blocks.ListBlock(
        blocks.StructBlock([
            ('drug_name', blocks.CharBlock(max_length=200)),
            ('interaction_type', blocks.ChoiceBlock(choices=[
                ('contraindicated', _('Contraindicated')),
                ('major', _('Major')),
                ('moderate', _('Moderate')),
                ('minor', _('Minor')),
            ])),
            ('description', blocks.TextBlock()),
        ]),
        help_text=_("Significant drug interactions")
    )
    
    food_interactions = blocks.ListBlock(
        blocks.StructBlock([
            ('food_item', blocks.CharBlock(max_length=200)),
            ('interaction_description', blocks.TextBlock()),
        ]),
        help_text=_("Food and dietary interactions")
    )
    
    class Meta:
        icon = 'warning'
        label = _('Drug Interactions')
        template = 'blocks/interactions_block.html'

class WarningsBlock(blocks.StructBlock):
    """Block for warnings and precautions"""
    
    black_box_warning = blocks.RichTextBlock(
        required=False,
        help_text=_("FDA Black Box Warning (if applicable)")
    )
    
    contraindications = blocks.ListBlock(
        blocks.CharBlock(max_length=200),
        help_text=_("Absolute contraindications")
    )
    
    precautions = blocks.ListBlock(
        blocks.CharBlock(max_length=200),
        help_text=_("Important precautions")
    )
    
    pregnancy_category = blocks.ChoiceBlock(
        choices=[
            ('A', _('Category A - No risk')),
            ('B', _('Category B - No evidence of risk')),
            ('C', _('Category C - Risk cannot be ruled out')),
            ('D', _('Category D - Positive evidence of risk')),
            ('X', _('Category X - Contraindicated')),
        ],
        required=False,
        help_text=_("Pregnancy safety category")
    )
    
    class Meta:
        icon = 'warning'
        label = _('Warnings & Precautions')
        template = 'blocks/warnings_block.html'
```

### 3. Content Templates

#### Medication Info Block Template

```html
<!-- templates/blocks/medication_info_block.html -->
<div class="medication-info-block bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
    <h3 class="text-lg font-semibold text-blue-800 mb-3">
        {% trans "Medication Information" %}
    </h3>
    
    <div class="grid md:grid-cols-2 gap-4">
        <div>
            <h4 class="font-medium text-gray-700 mb-2">{% trans "Indication" %}</h4>
            <p class="text-gray-600">{{ value.indication }}</p>
        </div>
        
        {% if value.mechanism %}
        <div>
            <h4 class="font-medium text-gray-700 mb-2">{% trans "How it works" %}</h4>
            <div class="text-gray-600">{{ value.mechanism|richtext }}</div>
        </div>
        {% endif %}
        
        {% if value.onset_of_action %}
        <div>
            <h4 class="font-medium text-gray-700 mb-2">{% trans "Onset of Action" %}</h4>
            <p class="text-gray-600">{{ value.onset_of_action }}</p>
        </div>
        {% endif %}
        
        {% if value.duration %}
        <div>
            <h4 class="font-medium text-gray-700 mb-2">{% trans "Duration" %}</h4>
            <p class="text-gray-600">{{ value.duration }}</p>
        </div>
        {% endif %}
    </div>
</div>
```

## Content Workflow and Approval

### 1. Content Review Process

```python
# workflows/healthcare_workflows.py
from wagtail.models import WorkflowState, TaskState
from django.contrib.auth.models import Group
from django.db import models
from django.utils.translation import gettext_lazy as _

class MedicalReviewTask(Task):
    """Custom task for medical content review"""
    
    reviewer_group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text=_("Group of medical reviewers")
    )
    
    require_physician_approval = models.BooleanField(
        default=True,
        help_text=_("Require approval from licensed physician")
    )
    
    class Meta:
        verbose_name = _("Medical Review Task")
        verbose_name_plural = _("Medical Review Tasks")
    
    def get_actors(self):
        """Return users who can perform this task"""
        return self.reviewer_group.user_set.all()
    
    def user_can_access_editor(self, page, user):
        """Check if user can access the editor"""
        return user.groups.filter(pk=self.reviewer_group.pk).exists()

class PharmacyReviewTask(Task):
    """Task for pharmacy/clinical review"""
    
    pharmacist_group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        help_text=_("Group of licensed pharmacists")
    )
    
    class Meta:
        verbose_name = _("Pharmacy Review Task")
        verbose_name_plural = _("Pharmacy Review Tasks")
```

### 2. Content Approval Workflow

```python
# Set up in Wagtail admin
# 1. Create Groups:
#    - Medical Reviewers
#    - Licensed Physicians  
#    - Clinical Pharmacists
#    - Content Editors
#
# 2. Create Workflow:
#    - Medical Review Task (Medical Reviewers)
#    - Physician Approval Task (Licensed Physicians)
#    - Final Review Task (Clinical Pharmacists)
```

## Multi-language Content Management

### 1. Translation Setup

```python
# settings/base.py
WAGTAIL_I18N_ENABLED = True

WAGTAIL_CONTENT_LANGUAGES = [
    ('en-ZA', _('English (South Africa)')),
    ('af-ZA', _('Afrikaans (South Africa)')),
]

# Translation workflow
WAGTAIL_LOCALIZE_POFILE_CREATION_MODE = 'manual'
WAGTAIL_LOCALIZE_SYNC_TREE = True
```

### 2. Content Translation Guidelines

```markdown
## Translation Best Practices

### English (en-ZA) - Primary Language
- Use South African English spelling and terminology
- Include local medical terminology where appropriate
- Reference South African healthcare regulations

### Afrikaans (af-ZA) - Secondary Language
- Ensure medical accuracy in translation
- Use proper Afrikaans medical terminology
- Maintain consistent terminology across all content
- Consider cultural context for health advice

### Translation Process
1. Content created in English first
2. Medical review and approval
3. Professional translation to Afrikaans
4. Medical review of Afrikaans content
5. Final approval and publication
```

## Content Quality Guidelines

### 1. Medical Content Standards

```markdown
## Medical Content Requirements

### Accuracy
- All medical information must be evidence-based
- Include publication dates and review dates
- Reference reputable medical sources
- Regular content audits (every 6 months)

### Readability
- Use plain language for patient-facing content
- Define medical terms when first used
- Use bullet points and short paragraphs
- Include visual aids where helpful

### Compliance
- Include appropriate disclaimers
- Follow SAHPRA guidelines for medication information
- Ensure POPI Act compliance for patient data
- Regular legal review of content
```

### 2. Content Validation

```python
# medications/validators.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re

def validate_medication_name(value):
    """Validate medication name format"""
    if not re.match(r'^[A-Za-z0-9\s\-\.]+$', value):
        raise ValidationError(
            _('Medication name can only contain letters, numbers, spaces, hyphens, and periods.')
        )

def validate_dosage_format(value):
    """Validate dosage format"""
    dosage_pattern = r'\d+(\.\d+)?\s?(mg|g|ml|mcg|units?|tablets?|capsules?)'
    if not re.search(dosage_pattern, value.lower()):
        raise ValidationError(
            _('Dosage must include a number and unit (e.g., "10 mg", "2 tablets").')
        )

def validate_medical_content_length(value):
    """Ensure medical content is comprehensive"""
    if len(value.strip()) < 100:
        raise ValidationError(
            _('Medical content must be at least 100 characters long.')
        )
```

## SEO and Accessibility

### 1. SEO Best Practices

```python
# home/models.py - SEO Mixin
class SEOMixin(models.Model):
    """Mixin for SEO fields"""
    
    class Meta:
        abstract = True
    
    seo_title = models.CharField(
        max_length=60,
        blank=True,
        help_text=_("Title for search engines (60 chars max)")
    )
    
    search_description = models.CharField(
        max_length=160,
        blank=True,
        help_text=_("Description for search engines (160 chars max)")
    )
    
    keywords = models.CharField(
        max_length=200,
        blank=True,
        help_text=_("Keywords for search engines (comma-separated)")
    )
    
    promote_panels = [
        MultiFieldPanel([
            FieldPanel('seo_title'),
            FieldPanel('search_description'),
            FieldPanel('keywords'),
        ], heading=_("Search Engine Optimization"))
    ]
```

### 2. Accessibility Features

```python
# Accessibility validation
def validate_alt_text(value):
    """Ensure images have meaningful alt text"""
    if not value or len(value.strip()) < 10:
        raise ValidationError(
            _('Alt text must be descriptive and at least 10 characters long.')
        )

# Image model with accessibility
class AccessibleImage(AbstractImage):
    alt_text = models.CharField(
        max_length=255,
        validators=[validate_alt_text],
        help_text=_("Descriptive text for screen readers")
    )
    
    admin_form_fields = Image.admin_form_fields + ('alt_text',)
```

## Content Analytics and Performance

### 1. Content Analytics

```python
# analytics/models.py
class ContentAnalytics(models.Model):
    """Track content performance"""
    
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    average_time_on_page = models.DurationField(null=True, blank=True)
    bounce_rate = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Content Analytics")
        verbose_name_plural = _("Content Analytics")
```

### 2. Performance Monitoring

```python
# Monitor content performance
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate content performance report'
    
    def handle(self, *args, **options):
        # Generate weekly content performance report
        last_week = timezone.now() - timedelta(days=7)
        
        # Identify low-performing content
        # Suggest content updates
        # Generate accessibility audit
        # Check for outdated medical information
```

## Content Management Best Practices

### 1. Editorial Guidelines

```markdown
## Editorial Workflow

### Content Creation
1. Research and fact-checking
2. Draft creation in English (en-ZA)
3. Internal review for accuracy
4. Medical professional review
5. SEO optimization
6. Accessibility check

### Content Updates
1. Regular content audits (every 6 months)
2. Update medical information based on new research
3. Review and update translations
4. Performance analysis and optimization

### Content Governance
- Assign content owners for each section
- Maintain editorial calendar
- Regular training for content creators
- Compliance audits
```

### 2. Content Maintenance

```python
# Management command for content maintenance
class Command(BaseCommand):
    help = 'Perform content maintenance tasks'
    
    def handle(self, *args, **options):
        # Check for outdated content
        # Validate links and references
        # Update medical review dates
        # Generate content audit report
        # Check translation completeness
```

## Integration with Mobile and Web

### 1. API Content Delivery

```python
# api/serializers.py
from rest_framework import serializers
from medications.models import MedicationPage

class MedicationPageSerializer(serializers.ModelSerializer):
    """Serializer for medication pages"""
    
    content_blocks = serializers.SerializerMethodField()
    
    class Meta:
        model = MedicationPage
        fields = [
            'id', 'title', 'generic_name', 'brand_names',
            'medication_class', 'content_blocks', 'last_medical_review'
        ]
    
    def get_content_blocks(self, obj):
        """Serialize StreamField content for API"""
        return [
            {
                'type': block.block_type,
                'value': block.value,
                'id': block.id
            }
            for block in obj.content
        ]
```

### 2. Mobile Content Optimization

```python
# Mobile-specific content rendering
class MobileContentMixin:
    """Mixin for mobile-optimized content"""
    
    def get_mobile_content(self):
        """Return mobile-optimized content"""
        # Simplify complex blocks for mobile
        # Optimize images for mobile screens
        # Provide condensed information
        pass
```

## Next Steps

1. **Security Implementation**: See `wagtail_security.md`
2. **API Integration**: Check `wagtail_api.md`
3. **Prescription Workflow**: Review `prescription_workflow.md`
4. **Compliance Setup**: Follow `wagtail_compliance.md`

## Resources

- [Wagtail Documentation](https://docs.wagtail.io/)
- [Healthcare Content Guidelines](https://www.sahpra.org.za/)
- [POPI Act Compliance](https://popia.co.za/)
- [South African Medical Association](https://www.samedical.org/)
