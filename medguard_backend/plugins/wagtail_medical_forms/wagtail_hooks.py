"""
Wagtail Hooks for Medical Forms Plugin
Integrates medical form functionality into Wagtail admin interface.
"""
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import MedicalFormTemplate, MedicalFormSubmission
from .views import MedicalFormsDashboardView, FormBuilderView, SubmissionDetailView


class MedicalFormTemplateAdmin(ModelAdmin):
    """ModelAdmin for MedicalFormTemplate."""
    
    model = MedicalFormTemplate
    menu_label = _("Form Templates")
    menu_icon = "form"
    menu_order = 600
    list_display = ["name", "category", "is_active", "created_at"]
    list_filter = ["category", "is_active", "requires_hipaa_consent"]
    search_fields = ["name", "description"]
    ordering = ["category", "name"]


class MedicalFormSubmissionAdmin(ModelAdmin):
    """ModelAdmin for MedicalFormSubmission."""
    
    model = MedicalFormSubmission
    menu_label = _("Form Submissions")
    menu_icon = "doc-full"
    menu_order = 601
    list_display = ["form_template", "patient", "status", "created_at"]
    list_filter = ["status", "form_template", "created_at"]
    search_fields = ["patient__first_name", "patient__last_name"]
    ordering = ["-created_at"]


# Register ModelAdmins
modeladmin_register(MedicalFormTemplateAdmin)
modeladmin_register(MedicalFormSubmissionAdmin)


@hooks.register("register_admin_urls")
def register_medical_forms_admin_urls():
    """Register custom admin URLs for medical forms functionality."""
    return [
        path(
            "medical-forms/",
            MedicalFormsDashboardView.as_view(),
            name="medical_forms_dashboard"
        ),
        path(
            "medical-forms/builder/",
            FormBuilderView.as_view(),
            name="form_builder"
        ),
        path(
            "medical-forms/submission/<uuid:submission_id>/",
            SubmissionDetailView.as_view(),
            name="submission_detail"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_medical_forms_menu_item():
    """Add Medical Forms menu item to Wagtail admin menu."""
    return MenuItem(
        _("Medical Forms"),
        reverse("medical_forms_dashboard"),
        classname="icon icon-form",
        order=1400
    )


@hooks.register("insert_global_admin_css")
def medical_forms_admin_css():
    """Add custom CSS for medical forms admin interface."""
    return format_html(
        '<link rel="stylesheet" href="/static/wagtail_medical_forms/css/forms-admin.css">'
    )


@hooks.register("insert_global_admin_js")
def medical_forms_admin_js():
    """Add custom JavaScript for medical forms functionality."""
    return format_html(
        '<script src="/static/wagtail_medical_forms/js/forms-admin.js"></script>'
    )


@hooks.register("before_create_medicalformsubmission")
def log_form_submission(request, instance):
    """Log form submission for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='medical_form_submitted',
        user=request.user,
        description=f"Medical form submitted: {instance.form_template.name}",
        metadata={
            'submission_id': str(instance.id),
            'form_template': instance.form_template.name,
            'patient_id': instance.patient.id if instance.patient else None
        }
    )


@hooks.register("construct_homepage_panels")
def add_medical_forms_panel(request, panels):
    """Add medical forms panel to Wagtail admin homepage."""
    from wagtail.admin.ui.components import Component
    
    if request.user.has_perm('wagtail_medical_forms.view_medicalformsubmission'):
        # Get recent submissions
        recent_submissions = MedicalFormSubmission.objects.order_by('-created_at')[:5]
        pending_reviews = MedicalFormSubmission.objects.filter(status='under_review').count()
        
        panel_html = f"""
        <div class="panel summary nice-padding">
            <h3><a href="{reverse('medical_forms_dashboard')}">Medical Forms</a></h3>
            <div class="panel-content">
                <p><strong>Pending Reviews:</strong> {pending_reviews}</p>
                <p><strong>Recent Submissions:</strong> {recent_submissions.count()}</p>
            </div>
        </div>
        """
        
        panels.append(Component(panel_html))


@hooks.register("register_permissions")
def register_medical_forms_permissions():
    """Register custom permissions for medical forms."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Get content types
    template_ct = ContentType.objects.get_for_model(MedicalFormTemplate)
    submission_ct = ContentType.objects.get_for_model(MedicalFormSubmission)
    
    # Define custom permissions
    custom_permissions = [
        ('build_medical_forms', 'Can build medical forms', template_ct),
        ('review_form_submissions', 'Can review form submissions', submission_ct),
        ('access_hipaa_data', 'Can access HIPAA-protected form data', submission_ct),
        ('manage_form_workflows', 'Can manage form approval workflows', template_ct),
    ]
    
    for codename, name, content_type in custom_permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type
        )
