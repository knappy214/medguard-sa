"""
Wagtail Hooks for Drug Interactions Plugin
Integrates drug interaction checking into Wagtail admin interface.
"""
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import DrugInteraction, InteractionCheck, DrugAllergy
from .views import (
    DrugInteractionsDashboardView,
    InteractionCheckerView,
    PatientAllergiesView,
    InteractionDatabaseView
)


class DrugInteractionAdmin(ModelAdmin):
    """ModelAdmin for DrugInteraction."""
    
    model = DrugInteraction
    menu_label = _("Drug Interactions")
    menu_icon = "warning"
    menu_order = 500
    list_display = [
        "drug_name_1",
        "drug_name_2",
        "severity",
        "interaction_type",
        "confidence_level",
        "is_active"
    ]
    list_filter = [
        "severity",
        "interaction_type",
        "is_active",
        "reviewed_by"
    ]
    search_fields = [
        "drug_name_1",
        "drug_name_2",
        "generic_name_1",
        "generic_name_2"
    ]
    ordering = ["-severity", "drug_name_1"]


class InteractionCheckAdmin(ModelAdmin):
    """ModelAdmin for InteractionCheck."""
    
    model = InteractionCheck
    menu_label = _("Interaction Checks")
    menu_icon = "doc-full"
    menu_order = 501
    list_display = [
        "patient",
        "checked_by",
        "total_interactions",
        "major_interactions",
        "contraindicated_interactions",
        "created_at"
    ]
    list_filter = [
        "created_at",
        "total_interactions",
        "data_source"
    ]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "checked_by__first_name",
        "checked_by__last_name"
    ]
    ordering = ["-created_at"]


class DrugAllergyAdmin(ModelAdmin):
    """ModelAdmin for DrugAllergy."""
    
    model = DrugAllergy
    menu_label = _("Drug Allergies")
    menu_icon = "warning"
    menu_order = 502
    list_display = [
        "patient",
        "drug_name",
        "severity",
        "allergy_type",
        "is_verified",
        "is_active"
    ]
    list_filter = [
        "severity",
        "allergy_type",
        "is_verified",
        "is_active"
    ]
    search_fields = [
        "patient__first_name",
        "patient__last_name",
        "drug_name",
        "generic_name"
    ]
    ordering = ["-severity", "drug_name"]


# Register ModelAdmins
modeladmin_register(DrugInteractionAdmin)
modeladmin_register(InteractionCheckAdmin)
modeladmin_register(DrugAllergyAdmin)


@hooks.register("register_admin_urls")
def register_drug_interactions_admin_urls():
    """Register custom admin URLs for drug interactions functionality."""
    return [
        path(
            "drug-interactions/",
            DrugInteractionsDashboardView.as_view(),
            name="drug_interactions_dashboard"
        ),
        path(
            "drug-interactions/checker/",
            InteractionCheckerView.as_view(),
            name="interaction_checker"
        ),
        path(
            "drug-interactions/patient/<int:patient_id>/allergies/",
            PatientAllergiesView.as_view(),
            name="patient_allergies"
        ),
        path(
            "drug-interactions/database/",
            InteractionDatabaseView.as_view(),
            name="interaction_database"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_drug_interactions_menu_item():
    """Add Drug Interactions menu item to Wagtail admin menu."""
    return MenuItem(
        _("Drug Interactions"),
        reverse("drug_interactions_dashboard"),
        classname="icon icon-warning",
        order=1300
    )


@hooks.register("insert_global_admin_css")
def drug_interactions_admin_css():
    """Add custom CSS for drug interactions admin interface."""
    return format_html(
        '<link rel="stylesheet" href="/static/wagtail_drug_interactions/css/interactions-admin.css">'
    )


@hooks.register("insert_global_admin_js")
def drug_interactions_admin_js():
    """Add custom JavaScript for drug interactions functionality."""
    return format_html(
        '<script src="/static/wagtail_drug_interactions/js/interactions-admin.js"></script>'
    )


@hooks.register("before_create_druginteraction")
def log_interaction_creation(request, instance):
    """Log drug interaction creation for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='drug_interaction_created',
        user=request.user,
        description=f"Drug interaction created: {instance.drug_name_1} + {instance.drug_name_2}",
        metadata={
            'interaction_id': str(instance.id),
            'drug1': instance.drug_name_1,
            'drug2': instance.drug_name_2,
            'severity': instance.severity
        }
    )


@hooks.register("before_create_drugallergy")
def log_allergy_creation(request, instance):
    """Log drug allergy creation for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='drug_allergy_created',
        user=request.user,
        description=f"Drug allergy created: {instance.drug_name} for {instance.patient.get_full_name()}",
        metadata={
            'allergy_id': str(instance.id),
            'patient_id': instance.patient.id,
            'drug_name': instance.drug_name,
            'severity': instance.severity
        }
    )


@hooks.register("construct_homepage_panels")
def add_drug_interactions_panel(request, panels):
    """Add drug interactions panel to Wagtail admin homepage."""
    from wagtail.admin.ui.components import Component
    
    if request.user.has_perm('wagtail_drug_interactions.view_druginteraction'):
        # Get interaction statistics
        total_interactions = DrugInteraction.objects.filter(is_active=True).count()
        recent_checks = InteractionCheck.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        panel_html = f"""
        <div class="panel summary nice-padding">
            <h3><a href="{reverse('drug_interactions_dashboard')}">Drug Interactions</a></h3>
            <div class="panel-content">
                <p><strong>Active Interactions:</strong> {total_interactions}</p>
                <p><strong>Checks This Week:</strong> {recent_checks}</p>
            </div>
        </div>
        """
        
        panels.append(Component(panel_html))


@hooks.register("construct_wagtail_userbar")
def add_interaction_checker_userbar(request, items):
    """Add interaction checker to Wagtail userbar."""
    if (request.user.groups.filter(name__in=['Healthcare Providers', 'Clinical Pharmacists']).exists() 
        or request.user.is_staff):
        items.append({
            'url': reverse('interaction_checker'),
            'label': _('Check Interactions'),
            'classname': 'icon icon-warning'
        })


@hooks.register("register_permissions")
def register_drug_interactions_permissions():
    """Register custom permissions for drug interactions."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Get content types
    interaction_ct = ContentType.objects.get_for_model(DrugInteraction)
    allergy_ct = ContentType.objects.get_for_model(DrugAllergy)
    
    # Define custom permissions
    custom_permissions = [
        ('perform_interaction_checks', 'Can perform drug interaction checks', interaction_ct),
        ('manage_interaction_database', 'Can manage interaction database', interaction_ct),
        ('view_patient_allergies', 'Can view patient drug allergies', allergy_ct),
        ('override_interaction_warnings', 'Can override interaction warnings', interaction_ct),
    ]
    
    for codename, name, content_type in custom_permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type
        )


@hooks.register("after_create_interactioncheck")
def handle_interaction_check_created(request, instance):
    """Handle actions after interaction check is created."""
    # Send alerts for critical interactions
    if instance.contraindicated_interactions > 0 or instance.major_interactions > 0:
        from medguard_backend.medguard_notifications.services import NotificationService
        
        notification_service = NotificationService()
        
        # Notify the checker
        notification_service.send_notification(
            user=instance.checked_by,
            title="Critical Drug Interactions Found",
            message=f"Critical interactions detected in medication check for {instance.patient.get_full_name() if instance.patient else 'patient'}",
            notification_type="critical_interaction_alert",
            metadata={
                'check_id': str(instance.id),
                'contraindicated': instance.contraindicated_interactions,
                'major': instance.major_interactions
            }
        )
        
        # Notify patient's primary care provider if different
        if instance.patient and hasattr(instance.patient, 'primary_care_provider'):
            if instance.patient.primary_care_provider != instance.checked_by:
                notification_service.send_notification(
                    user=instance.patient.primary_care_provider,
                    title="Patient Drug Interaction Alert",
                    message=f"Critical drug interactions identified for your patient {instance.patient.get_full_name()}",
                    notification_type="patient_interaction_alert",
                    metadata={
                        'check_id': str(instance.id),
                        'patient_id': instance.patient.id
                    }
                )


@hooks.register("construct_main_menu")
def customize_drug_interactions_menu(request, menu_items):
    """Customize drug interactions menu based on user permissions."""
    # Hide certain features for non-clinical users
    if not request.user.groups.filter(
        name__in=['Healthcare Providers', 'Clinical Pharmacists', 'Nurses']
    ).exists() and not request.user.is_staff:
        menu_items[:] = [
            item for item in menu_items 
            if not (item.url and 'drug-interactions' in item.url)
        ]
