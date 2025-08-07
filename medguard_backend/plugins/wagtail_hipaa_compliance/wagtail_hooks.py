"""
Wagtail Hooks for HIPAA Compliance Plugin
Integrates HIPAA compliance monitoring into Wagtail admin interface.
"""
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from .models import PHIAccessLog, BreachIncident, ComplianceAssessment
from .views import HIPAADashboardView, BreachReportingView, ComplianceReportView


class PHIAccessLogAdmin(ModelAdmin):
    """ModelAdmin for PHIAccessLog."""
    
    model = PHIAccessLog
    menu_label = _("PHI Access Logs")
    menu_icon = "view"
    menu_order = 700
    list_display = ["user", "patient", "resource_type", "action_performed", "accessed_at"]
    list_filter = ["access_reason", "action_performed", "is_authorized", "accessed_at"]
    search_fields = ["user__first_name", "user__last_name", "patient__first_name", "patient__last_name"]
    ordering = ["-accessed_at"]


class BreachIncidentAdmin(ModelAdmin):
    """ModelAdmin for BreachIncident."""
    
    model = BreachIncident
    menu_label = _("Breach Incidents")
    menu_icon = "warning"
    menu_order = 701
    list_display = ["incident_title", "severity", "affected_patients_count", "status", "discovered_at"]
    list_filter = ["severity", "status", "incident_type", "requires_hhs_notification"]
    search_fields = ["incident_title", "description"]
    ordering = ["-discovered_at"]


class ComplianceAssessmentAdmin(ModelAdmin):
    """ModelAdmin for ComplianceAssessment."""
    
    model = ComplianceAssessment
    menu_label = _("Compliance Assessments")
    menu_icon = "doc-full-inverse"
    menu_order = 702
    list_display = ["assessment_name", "assessment_type", "compliance_status", "start_date"]
    list_filter = ["assessment_type", "compliance_status", "start_date"]
    search_fields = ["assessment_name", "scope"]
    ordering = ["-start_date"]


# Register ModelAdmins
modeladmin_register(PHIAccessLogAdmin)
modeladmin_register(BreachIncidentAdmin)
modeladmin_register(ComplianceAssessmentAdmin)


@hooks.register("register_admin_urls")
def register_hipaa_compliance_admin_urls():
    """Register custom admin URLs for HIPAA compliance functionality."""
    return [
        path(
            "hipaa-compliance/",
            HIPAADashboardView.as_view(),
            name="hipaa_compliance_dashboard"
        ),
        path(
            "hipaa-compliance/breach-reporting/",
            BreachReportingView.as_view(),
            name="breach_reporting"
        ),
        path(
            "hipaa-compliance/compliance-report/",
            ComplianceReportView.as_view(),
            name="compliance_report"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_hipaa_compliance_menu_item():
    """Add HIPAA Compliance menu item to Wagtail admin menu."""
    return MenuItem(
        _("HIPAA Compliance"),
        reverse("hipaa_compliance_dashboard"),
        classname="icon icon-warning",
        order=1500
    )


@hooks.register("insert_global_admin_css")
def hipaa_compliance_admin_css():
    """Add custom CSS for HIPAA compliance admin interface."""
    return format_html(
        '<link rel="stylesheet" href="/static/wagtail_hipaa_compliance/css/compliance-admin.css">'
    )


@hooks.register("before_create_breachincident")
def log_breach_incident_creation(request, instance):
    """Log breach incident creation for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='breach_incident_reported',
        user=request.user,
        description=f"Breach incident reported: {instance.incident_title}",
        metadata={
            'incident_id': str(instance.id),
            'severity': instance.severity,
            'affected_patients': instance.affected_patients_count
        }
    )


@hooks.register("construct_homepage_panels")
def add_hipaa_compliance_panel(request, panels):
    """Add HIPAA compliance panel to Wagtail admin homepage."""
    from wagtail.admin.ui.components import Component
    
    if request.user.has_perm('wagtail_hipaa_compliance.view_breachincident'):
        # Get compliance statistics
        open_incidents = BreachIncident.objects.filter(status='open').count()
        recent_accesses = PHIAccessLog.objects.filter(
            accessed_at__gte=timezone.now() - timezone.timedelta(days=1)
        ).count()
        
        panel_html = f"""
        <div class="panel summary nice-padding">
            <h3><a href="{reverse('hipaa_compliance_dashboard')}">HIPAA Compliance</a></h3>
            <div class="panel-content">
                <p><strong>Open Incidents:</strong> {open_incidents}</p>
                <p><strong>PHI Accesses (24h):</strong> {recent_accesses}</p>
            </div>
        </div>
        """
        
        panels.append(Component(panel_html))


@hooks.register("register_permissions")
def register_hipaa_compliance_permissions():
    """Register custom permissions for HIPAA compliance."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Get content types
    phi_ct = ContentType.objects.get_for_model(PHIAccessLog)
    breach_ct = ContentType.objects.get_for_model(BreachIncident)
    
    # Define custom permissions
    custom_permissions = [
        ('view_phi_access_logs', 'Can view PHI access logs', phi_ct),
        ('investigate_breaches', 'Can investigate breach incidents', breach_ct),
        ('manage_compliance', 'Can manage HIPAA compliance', breach_ct),
        ('generate_compliance_reports', 'Can generate compliance reports', breach_ct),
    ]
    
    for codename, name, content_type in custom_permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type
        )
