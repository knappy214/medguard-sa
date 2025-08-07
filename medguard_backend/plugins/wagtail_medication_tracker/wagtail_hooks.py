"""
Wagtail Hooks for Medication Tracker Plugin
Integrates medication tracking functionality into Wagtail admin interface.
"""
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.contrib.modeladmin.views import IndexView

from .models import MedicationSchedule, MedicationLog, AdherenceReport
from .views import (
    MedicationTrackerDashboardView,
    PatientAdherenceView,
    MedicationLogView,
    AdherenceReportView,
    MedicationReminderView
)


class MedicationScheduleAdmin(ModelAdmin):
    """ModelAdmin for MedicationSchedule."""
    
    model = MedicationSchedule
    menu_label = _("Medication Schedules")
    menu_icon = "date"
    menu_order = 300
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = [
        "medication_name",
        "patient", 
        "frequency",
        "adherence_rate",
        "adherence_status",
        "is_active"
    ]
    list_filter = [
        "is_active", 
        "frequency", 
        "adherence_status",
        "start_date",
        "prescribed_by"
    ]
    search_fields = [
        "medication_name", 
        "patient__first_name", 
        "patient__last_name",
        "prescribed_by__first_name",
        "prescribed_by__last_name"
    ]
    ordering = ["-created_at"]
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        
        # Healthcare providers can only see their own prescribed medications
        if request.user.groups.filter(name='Healthcare Providers').exists():
            qs = qs.filter(prescribed_by=request.user)
        
        # Patients can only see their own medications
        elif not request.user.is_staff:
            qs = qs.filter(patient=request.user)
        
        return qs


class MedicationLogAdmin(ModelAdmin):
    """ModelAdmin for MedicationLog."""
    
    model = MedicationLog
    menu_label = _("Medication Logs")
    menu_icon = "list-ul"
    menu_order = 301
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = [
        "schedule",
        "scheduled_time",
        "taken_at",
        "status",
        "logged_by"
    ]
    list_filter = [
        "status",
        "scheduled_time",
        "taken_at",
        "schedule__medication_name"
    ]
    search_fields = [
        "schedule__medication_name",
        "schedule__patient__first_name",
        "schedule__patient__last_name"
    ]
    ordering = ["-scheduled_time"]
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        
        # Healthcare providers can only see logs for their prescribed medications
        if request.user.groups.filter(name='Healthcare Providers').exists():
            qs = qs.filter(schedule__prescribed_by=request.user)
        
        # Patients can only see their own medication logs
        elif not request.user.is_staff:
            qs = qs.filter(schedule__patient=request.user)
        
        return qs


class AdherenceReportAdmin(ModelAdmin):
    """ModelAdmin for AdherenceReport."""
    
    model = AdherenceReport
    menu_label = _("Adherence Reports")
    menu_icon = "doc-full-inverse"
    menu_order = 302
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = [
        "patient",
        "report_date",
        "overall_adherence_rate",
        "total_medications",
        "generated_by"
    ]
    list_filter = [
        "report_date",
        "overall_adherence_rate",
        "generated_by"
    ]
    search_fields = [
        "patient__first_name",
        "patient__last_name"
    ]
    ordering = ["-report_date"]
    
    def get_queryset(self, request):
        """Filter queryset based on user permissions."""
        qs = super().get_queryset(request)
        
        # Healthcare providers can see reports for their patients
        if request.user.groups.filter(name='Healthcare Providers').exists():
            # Get patients who have medications prescribed by this provider
            patient_ids = MedicationSchedule.objects.filter(
                prescribed_by=request.user
            ).values_list('patient_id', flat=True).distinct()
            qs = qs.filter(patient_id__in=patient_ids)
        
        # Patients can only see their own reports
        elif not request.user.is_staff:
            qs = qs.filter(patient=request.user)
        
        return qs


# Register ModelAdmins
modeladmin_register(MedicationScheduleAdmin)
modeladmin_register(MedicationLogAdmin)
modeladmin_register(AdherenceReportAdmin)


@hooks.register("register_admin_urls")
def register_medication_tracker_admin_urls():
    """Register custom admin URLs for medication tracking functionality."""
    return [
        path(
            "medication-tracker/",
            MedicationTrackerDashboardView.as_view(),
            name="medication_tracker_dashboard"
        ),
        path(
            "medication-tracker/patient/<int:patient_id>/",
            PatientAdherenceView.as_view(),
            name="patient_adherence"
        ),
        path(
            "medication-tracker/log/<uuid:log_id>/",
            MedicationLogView.as_view(),
            name="medication_log"
        ),
        path(
            "medication-tracker/report/<uuid:report_id>/",
            AdherenceReportView.as_view(),
            name="adherence_report"
        ),
        path(
            "medication-tracker/reminders/",
            MedicationReminderView.as_view(),
            name="medication_reminders"
        ),
    ]


@hooks.register("register_admin_menu_item")
def register_medication_tracker_menu_item():
    """Add Medication Tracker menu item to Wagtail admin menu."""
    return MenuItem(
        _("Medication Tracker"),
        reverse("medication_tracker_dashboard"),
        classname="icon icon-date",
        order=1100
    )


@hooks.register("insert_global_admin_css")
def medication_tracker_admin_css():
    """Add custom CSS for medication tracker admin interface."""
    return format_html(
        '<link rel="stylesheet" href="/static/wagtail_medication_tracker/css/tracker-admin.css">'
    )


@hooks.register("insert_global_admin_js")
def medication_tracker_admin_js():
    """Add custom JavaScript for medication tracking functionality."""
    return format_html(
        '<script src="/static/wagtail_medication_tracker/js/tracker-admin.js"></script>'
    )


@hooks.register("construct_main_menu")
def customize_medication_tracker_menu(request, menu_items):
    """Customize medication tracker menu based on user role."""
    # Hide certain menu items for patients
    if not request.user.is_staff and not request.user.groups.filter(
        name__in=['Healthcare Providers', 'Nurses']
    ).exists():
        menu_items[:] = [
            item for item in menu_items 
            if not (item.url and any(path in item.url for path in [
                'medicationschedule',
                'adherencereport'
            ]))
        ]


@hooks.register("before_create_medication_schedule")
def log_medication_schedule_creation(request, instance):
    """Log medication schedule creation for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='medication_schedule_created',
        user=request.user,
        description=f"Medication schedule created: {instance.medication_name} for {instance.patient.get_full_name()}",
        metadata={
            'schedule_id': str(instance.id),
            'patient_id': instance.patient.id,
            'medication_name': instance.medication_name,
            'prescribed_by': instance.prescribed_by.id if instance.prescribed_by else None
        }
    )


@hooks.register("before_edit_medication_schedule")
def log_medication_schedule_modification(request, instance):
    """Log medication schedule modifications for audit trail."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='medication_schedule_modified',
        user=request.user,
        description=f"Medication schedule modified: {instance.medication_name}",
        metadata={
            'schedule_id': str(instance.id),
            'patient_id': instance.patient.id,
            'modifications': 'Schedule updated'
        }
    )


@hooks.register("before_create_medication_log")
def log_medication_logging(request, instance):
    """Log medication dose logging for compliance tracking."""
    from medguard_backend.security.models import SecurityEvent
    
    SecurityEvent.objects.create(
        event_type='medication_logged',
        user=request.user,
        description=f"Medication dose logged: {instance.schedule.medication_name} - {instance.status}",
        metadata={
            'log_id': str(instance.id),
            'schedule_id': str(instance.schedule.id),
            'patient_id': instance.schedule.patient.id,
            'status': instance.status,
            'scheduled_time': instance.scheduled_time.isoformat(),
            'taken_at': instance.taken_at.isoformat() if instance.taken_at else None
        }
    )


@hooks.register("construct_homepage_panels")
def add_medication_tracker_panel(request, panels):
    """Add medication tracker panel to Wagtail admin homepage."""
    from wagtail.admin.ui.components import Component
    
    if request.user.has_perm('wagtail_medication_tracker.view_medicationschedule'):
        # Get recent medication logs
        recent_logs = MedicationLog.objects.select_related(
            'schedule', 'schedule__patient'
        ).order_by('-created_at')[:5]
        
        # Get adherence alerts
        low_adherence_schedules = MedicationSchedule.objects.filter(
            adherence_rate__lt=80,
            is_active=True
        ).count()
        
        panel_html = f"""
        <div class="panel summary nice-padding">
            <h3><a href="{reverse('medication_tracker_dashboard')}">Medication Tracker</a></h3>
            <div class="panel-content">
                <p><strong>Low Adherence Alerts:</strong> {low_adherence_schedules}</p>
                <p><strong>Recent Activity:</strong> {recent_logs.count()} recent logs</p>
            </div>
        </div>
        """
        
        panels.append(Component(panel_html))


@hooks.register("register_permissions")
def register_medication_tracker_permissions():
    """Register custom permissions for medication tracker."""
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    # Get content types
    schedule_ct = ContentType.objects.get_for_model(MedicationSchedule)
    log_ct = ContentType.objects.get_for_model(MedicationLog)
    report_ct = ContentType.objects.get_for_model(AdherenceReport)
    
    # Define custom permissions
    custom_permissions = [
        ('view_patient_medications', 'Can view patient medications', schedule_ct),
        ('manage_medication_reminders', 'Can manage medication reminders', schedule_ct),
        ('generate_adherence_reports', 'Can generate adherence reports', report_ct),
        ('view_all_patient_data', 'Can view all patient medication data', schedule_ct),
    ]
    
    for codename, name, content_type in custom_permissions:
        Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type
        )


@hooks.register("construct_settings_menu")
def add_medication_tracker_settings(request, menu_items):
    """Add medication tracker settings to admin settings menu."""
    from wagtail.admin.menu import MenuItem
    
    if request.user.has_perm('wagtail_medication_tracker.manage_medication_reminders'):
        menu_items.append(
            MenuItem(
                _("Medication Tracker Settings"),
                reverse("medication_reminders"),
                classname="icon icon-cogs",
                order=850
            )
        )


@hooks.register("after_create_user")
def setup_patient_medication_tracking(request, user):
    """Set up medication tracking for new patients."""
    # Check if user is a patient (not staff or healthcare provider)
    if not user.is_staff and not user.groups.filter(
        name__in=['Healthcare Providers', 'Nurses']
    ).exists():
        
        # Initialize patient-specific tracking settings
        from .services import MedicationTrackerService
        
        tracker_service = MedicationTrackerService()
        # Additional setup logic can be added here
        
        logger.info(f"Medication tracking initialized for patient {user.id}")


@hooks.register("register_rich_text_features")
def register_medication_tracker_rich_text_features(features):
    """Register custom rich text features for medication notes."""
    # Add medication-specific rich text features
    features.register_editor_plugin(
        'hallo', 'medication-highlight',
        HalloPlugin(
            js=['wagtail_medication_tracker/js/hallo-medication-highlight.js'],
        )
    )


# Custom dashboard widgets
@hooks.register("construct_wagtail_userbar")
def add_medication_tracker_userbar(request, items):
    """Add medication tracker items to Wagtail userbar for patients."""
    if not request.user.is_anonymous and not request.user.is_staff:
        # Add quick medication log button for patients
        items.append({
            'url': reverse('medication_log'),
            'label': _('Log Medication'),
            'classname': 'icon icon-plus'
        })
        
        # Add upcoming medications view
        items.append({
            'url': reverse('patient_adherence', args=[request.user.id]),
            'label': _('My Medications'),
            'classname': 'icon icon-date'
        })
