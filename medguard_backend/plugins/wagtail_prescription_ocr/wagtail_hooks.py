"""
Wagtail Hooks for Prescription OCR Plugin
Integrates OCR functionality into Wagtail admin interface.
"""
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.contrib.modeladmin.views import CreateView, EditView
from wagtailimages.models import Image

from .models import PrescriptionOCRResult, OCRTemplate
from .views import OCRProcessingView, OCRResultsView, OCRValidationView


class PrescriptionOCRResultAdmin(ModelAdmin):
    """ModelAdmin for PrescriptionOCRResult."""
    
    model = PrescriptionOCRResult
    menu_label = _("OCR Results")
    menu_icon = "doc-full"
    menu_order = 200
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = [
        "medication_name", 
        "confidence_score", 
        "is_verified", 
        "processed_at"
    ]
    list_filter = ["is_verified", "processed_at", "confidence_score"]
    search_fields = ["medication_name", "prescriber_name", "extracted_text"]
    ordering = ["-processed_at"]
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        # Add HIPAA compliance filtering here
        return qs


class OCRTemplateAdmin(ModelAdmin):
    """ModelAdmin for OCRTemplate."""
    
    model = OCRTemplate
    menu_label = _("OCR Templates")
    menu_icon = "form"
    menu_order = 201
    add_to_settings_menu = True
    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name", "description"]
    ordering = ["name"]


# Register ModelAdmins
modeladmin_register(PrescriptionOCRResultAdmin)
modeladmin_register(OCRTemplateAdmin)


@hooks.register("register_admin_urls")
def register_ocr_admin_urls():
    """Register custom admin URLs for OCR functionality."""
    return [
        path(
            "prescription-ocr/process/",
            OCRProcessingView.as_view(),
            name="prescription_ocr_process"
        ),
        path(
            "prescription-ocr/results/",
            OCRResultsView.as_view(),
            name="prescription_ocr_results"
        ),
        path(
            "prescription-ocr/validate/<uuid:ocr_id>/",
            OCRValidationView.as_view(),
            name="prescription_ocr_validate"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_ocr_menu_item():
    """Add OCR menu item to Wagtail admin menu."""
    return MenuItem(
        _("Prescription OCR"),
        reverse("prescription_ocr_process"),
        classname="icon icon-doc-full",
        order=1000
    )


@hooks.register("insert_global_admin_css")
def global_admin_css():
    """Add custom CSS for OCR admin interface."""
    return format_html(
        '<link rel="stylesheet" href="/static/wagtail_prescription_ocr/css/ocr-admin.css">'
    )


@hooks.register("insert_global_admin_js")
def global_admin_js():
    """Add custom JavaScript for OCR functionality."""
    return format_html(
        '<script src="/static/wagtail_prescription_ocr/js/ocr-admin.js"></script>'
    )


@hooks.register("construct_image_chooser_queryset")
def limit_image_chooser_for_prescriptions(images, request):
    """Limit image chooser to prescription-related images when appropriate."""
    # Add logic to filter images based on context
    return images


@hooks.register("after_create_image")
def process_prescription_image_on_upload(request, image):
    """Automatically process prescription images when uploaded."""
    from .tasks import process_prescription_ocr_async
    
    # Check if image is tagged as prescription
    if hasattr(image, 'tags') and 'prescription' in [tag.name for tag in image.tags.all()]:
        # Queue OCR processing
        process_prescription_ocr_async.delay(image.id, request.user.id)


@hooks.register("construct_main_menu")
def hide_ocr_menu_for_non_medical_staff(request, menu_items):
    """Hide OCR menu items for users without medical permissions."""
    if not request.user.has_perm('wagtail_prescription_ocr.view_prescriptionocrresult'):
        menu_items[:] = [
            item for item in menu_items 
            if not item.url or 'prescription-ocr' not in item.url
        ]


@hooks.register("before_create_prescription_ocr_result")
def log_ocr_creation(request, instance):
    """Log OCR result creation for HIPAA compliance."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='prescription_ocr_created',
        user=request.user,
        description=f"OCR result created for prescription image {instance.prescription_image.id}",
        metadata={
            'ocr_result_id': str(instance.id),
            'image_id': instance.prescription_image.id,
            'confidence_score': instance.confidence_score
        }
    )


@hooks.register("before_edit_prescription_ocr_result")
def log_ocr_modification(request, instance):
    """Log OCR result modifications for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='prescription_ocr_modified',
        user=request.user,
        description=f"OCR result modified: {instance.id}",
        metadata={
            'ocr_result_id': str(instance.id),
            'modifications': 'OCR result updated'
        }
    )


@hooks.register("construct_settings_menu")
def add_ocr_settings_menu(request, menu_items):
    """Add OCR settings to admin settings menu."""
    from wagtail.admin.menu import MenuItem
    
    menu_items.append(
        MenuItem(
            _("OCR Configuration"),
            reverse("wagtailadmin_explore", args=[]),  # Replace with actual settings view
            classname="icon icon-cogs",
            order=800
        )
    )
