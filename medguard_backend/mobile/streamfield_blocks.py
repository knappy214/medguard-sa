"""
Mobile-specific StreamField blocks for medication content
Wagtail 7.0.2 StreamField enhancements
"""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.rich_text.blocks import RichTextBlock
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json


class MobileHeroBlock(blocks.StructBlock):
    """
    Mobile-optimized hero block for medication pages
    """
    
    title = blocks.CharBlock(
        max_length=100,
        help_text="Hero title (max 100 characters)",
        required=True
    )
    
    subtitle = blocks.TextBlock(
        max_length=200,
        help_text="Hero subtitle (max 200 characters)",
        required=False
    )
    
    background_image = ImageChooserBlock(
        help_text="Background image for hero section",
        required=False
    )
    
    cta_text = blocks.CharBlock(
        max_length=50,
        help_text="Call-to-action button text",
        required=False
    )
    
    cta_link = blocks.URLBlock(
        help_text="Call-to-action button link",
        required=False
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_hero_block.html'
        icon = 'image'
        label = 'Mobile Hero'
        help_text = 'Mobile-optimized hero section for medication pages'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobileMedicationCardBlock(blocks.StructBlock):
    """
    Mobile-optimized medication card block
    """
    
    medication_name = blocks.CharBlock(
        max_length=100,
        help_text="Medication name",
        required=True
    )
    
    generic_name = blocks.CharBlock(
        max_length=100,
        help_text="Generic name",
        required=False
    )
    
    dosage_form = blocks.ChoiceBlock(
        choices=[
            ('tablet', 'Tablet'),
            ('capsule', 'Capsule'),
            ('liquid', 'Liquid'),
            ('injection', 'Injection'),
            ('cream', 'Cream'),
            ('inhaler', 'Inhaler'),
            ('other', 'Other'),
        ],
        help_text="Dosage form",
        required=True
    )
    
    strength = blocks.CharBlock(
        max_length=50,
        help_text="Medication strength (e.g., 500mg)",
        required=False
    )
    
    image = ImageChooserBlock(
        help_text="Medication image",
        required=False
    )
    
    description = blocks.RichTextBlock(
        features=['bold', 'italic', 'link'],
        help_text="Brief description",
        required=False
    )
    
    side_effects = blocks.ListBlock(
        blocks.CharBlock(max_length=100),
        help_text="Common side effects",
        required=False
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_medication_card.html'
        icon = 'medal'
        label = 'Mobile Medication Card'
        help_text = 'Mobile-optimized medication information card'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobilePrescriptionFormBlock(blocks.StructBlock):
    """
    Mobile-optimized prescription form block
    """
    
    form_title = blocks.CharBlock(
        max_length=100,
        help_text="Form title",
        required=True
    )
    
    form_description = blocks.TextBlock(
        max_length=300,
        help_text="Form description",
        required=False
    )
    
    required_fields = blocks.MultipleChoiceBlock(
        choices=[
            ('patient_name', 'Patient Name'),
            ('medication_name', 'Medication Name'),
            ('dosage', 'Dosage'),
            ('frequency', 'Frequency'),
            ('duration', 'Duration'),
            ('prescriber', 'Prescriber'),
            ('pharmacy', 'Pharmacy'),
        ],
        help_text="Required form fields",
        required=True
    )
    
    submit_button_text = blocks.CharBlock(
        max_length=50,
        default="Submit Prescription",
        help_text="Submit button text",
        required=True
    )
    
    success_message = blocks.TextBlock(
        max_length=200,
        default="Prescription submitted successfully!",
        help_text="Success message",
        required=True
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_prescription_form.html'
        icon = 'form'
        label = 'Mobile Prescription Form'
        help_text = 'Mobile-optimized prescription submission form'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobileDosageScheduleBlock(blocks.StructBlock):
    """
    Mobile-optimized dosage schedule block
    """
    
    schedule_title = blocks.CharBlock(
        max_length=100,
        help_text="Schedule title",
        required=True
    )
    
    medication_name = blocks.CharBlock(
        max_length=100,
        help_text="Medication name",
        required=True
    )
    
    dosage_times = blocks.ListBlock(
        blocks.StructBlock([
            ('time', blocks.CharBlock(max_length=10, help_text="Time (e.g., 08:00)")),
            ('dosage', blocks.CharBlock(max_length=50, help_text="Dosage amount")),
            ('with_food', blocks.BooleanBlock(default=False, help_text="Take with food")),
        ]),
        help_text="Dosage schedule times",
        required=True
    )
    
    reminder_enabled = blocks.BooleanBlock(
        default=True,
        help_text="Enable medication reminders",
        required=False
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_dosage_schedule.html'
        icon = 'time'
        label = 'Mobile Dosage Schedule'
        help_text = 'Mobile-optimized medication dosage schedule'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobileSideEffectsBlock(blocks.StructBlock):
    """
    Mobile-optimized side effects information block
    """
    
    title = blocks.CharBlock(
        max_length=100,
        default="Side Effects",
        help_text="Block title",
        required=True
    )
    
    common_side_effects = blocks.ListBlock(
        blocks.StructBlock([
            ('effect', blocks.CharBlock(max_length=100, help_text="Side effect")),
            ('frequency', blocks.ChoiceBlock(choices=[
                ('common', 'Common'),
                ('uncommon', 'Uncommon'),
                ('rare', 'Rare'),
            ], help_text="Frequency")),
            ('severity', blocks.ChoiceBlock(choices=[
                ('mild', 'Mild'),
                ('moderate', 'Moderate'),
                ('severe', 'Severe'),
            ], help_text="Severity")),
        ]),
        help_text="Common side effects",
        required=False
    )
    
    serious_side_effects = blocks.ListBlock(
        blocks.CharBlock(max_length=200),
        help_text="Serious side effects requiring immediate medical attention",
        required=False
    )
    
    warning_text = blocks.TextBlock(
        max_length=500,
        help_text="Warning text about side effects",
        required=False
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_side_effects.html'
        icon = 'warning'
        label = 'Mobile Side Effects'
        help_text = 'Mobile-optimized side effects information'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobileInteractionBlock(blocks.StructBlock):
    """
    Mobile-optimized drug interaction block
    """
    
    title = blocks.CharBlock(
        max_length=100,
        default="Drug Interactions",
        help_text="Block title",
        required=True
    )
    
    interactions = blocks.ListBlock(
        blocks.StructBlock([
            ('drug_name', blocks.CharBlock(max_length=100, help_text="Interacting drug")),
            ('interaction_type', blocks.ChoiceBlock(choices=[
                ('major', 'Major'),
                ('moderate', 'Moderate'),
                ('minor', 'Minor'),
            ], help_text="Interaction severity")),
            ('description', blocks.TextBlock(max_length=300, help_text="Interaction description")),
            ('recommendation', blocks.TextBlock(max_length=200, help_text="Recommendation")),
        ]),
        help_text="Drug interactions",
        required=False
    )
    
    food_interactions = blocks.ListBlock(
        blocks.StructBlock([
            ('food_item', blocks.CharBlock(max_length=100, help_text="Food item")),
            ('effect', blocks.TextBlock(max_length=200, help_text="Effect on medication")),
        ]),
        help_text="Food interactions",
        required=False
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_interactions.html'
        icon = 'link'
        label = 'Mobile Drug Interactions'
        help_text = 'Mobile-optimized drug interaction information'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobileEmergencyContactBlock(blocks.StructBlock):
    """
    Mobile-optimized emergency contact block
    """
    
    title = blocks.CharBlock(
        max_length=100,
        default="Emergency Contacts",
        help_text="Block title",
        required=True
    )
    
    contacts = blocks.ListBlock(
        blocks.StructBlock([
            ('name', blocks.CharBlock(max_length=100, help_text="Contact name")),
            ('type', blocks.ChoiceBlock(choices=[
                ('doctor', 'Doctor'),
                ('pharmacy', 'Pharmacy'),
                ('emergency', 'Emergency'),
                ('poison_control', 'Poison Control'),
                ('other', 'Other'),
            ], help_text="Contact type")),
            ('phone', blocks.CharBlock(max_length=20, help_text="Phone number")),
            ('description', blocks.TextBlock(max_length=200, help_text="Description")),
        ]),
        help_text="Emergency contacts",
        required=True
    )
    
    emergency_instructions = blocks.RichTextBlock(
        features=['bold', 'italic'],
        help_text="Emergency instructions",
        required=False
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_emergency_contacts.html'
        icon = 'phone'
        label = 'Mobile Emergency Contacts'
        help_text = 'Mobile-optimized emergency contact information'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobileRichTextBlock(RichTextBlock):
    """
    Mobile-optimized rich text block
    """
    
    def __init__(self, *args, **kwargs):
        # Limit features for mobile optimization
        kwargs.setdefault('features', [
            'bold', 'italic', 'link', 'h2', 'h3', 'h4', 'ul', 'ol', 'blockquote'
        ])
        super().__init__(*args, **kwargs)
    
    class Meta:
        template = 'mobile/blocks/mobile_rich_text.html'
        icon = 'doc-full'
        label = 'Mobile Rich Text'
        help_text = 'Mobile-optimized rich text content'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


class MobileImageBlock(ImageChooserBlock):
    """
    Mobile-optimized image block
    """
    
    caption = blocks.CharBlock(
        max_length=200,
        help_text="Image caption",
        required=False
    )
    
    alt_text = blocks.CharBlock(
        max_length=200,
        help_text="Alt text for accessibility",
        required=False
    )
    
    class Meta:
        template = 'mobile/blocks/mobile_image.html'
        icon = 'image'
        label = 'Mobile Image'
        help_text = 'Mobile-optimized image with caption'
    
    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        context['is_mobile'] = True
        context['mobile_optimized'] = True
        return context


# StreamField container for mobile blocks
class MobileStreamField(blocks.StreamBlock):
    """
    Container for mobile-optimized StreamField blocks
    """
    
    hero = MobileHeroBlock()
    medication_card = MobileMedicationCardBlock()
    prescription_form = MobilePrescriptionFormBlock()
    dosage_schedule = MobileDosageScheduleBlock()
    side_effects = MobileSideEffectsBlock()
    interactions = MobileInteractionBlock()
    emergency_contacts = MobileEmergencyContactBlock()
    rich_text = MobileRichTextBlock()
    image = MobileImageBlock()
    
    class Meta:
        template = 'mobile/blocks/mobile_stream_field.html'
        help_text = 'Mobile-optimized content blocks' 