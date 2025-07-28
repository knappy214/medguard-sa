"""
Wagtail hooks for MedGuard SA.

This module contains all the Wagtail hooks for customizing the admin interface
and adding custom functionality.
"""

from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from wagtail import hooks
from wagtail.admin.menu import MenuItem, SubmenuMenuItem
from wagtail.admin.ui.tables import Column, DateColumn, UserColumn
from wagtail.admin.viewsets.model import ModelViewSet
from wagtail.admin.viewsets.chooser import ChooserViewSet
from wagtail.admin.widgets import Button
from wagtail.admin.panels import FieldPanel, ObjectList, TabbedInterface
from wagtail.admin.site_summary import SummaryItem
from django.db import models

from users.models import User
from medications.models import Medication, MedicationSchedule, MedicationLog, StockAlert
from notifications.models import Notification, UserNotification, NotificationTemplate


# ============================================================================
# MODEL VIEWSETS
# ============================================================================

class MedicationViewSet(ModelViewSet):
    """ViewSet for managing medications."""
    model = Medication
    icon = "doc-full"
    menu_label = _("Medications")
    menu_name = "medications"
    add_to_admin_menu = True
    menu_order = 100
    
    list_display = [
        "name", "generic_name", "brand_name", "medication_type", 
        "prescription_type", "strength", "pill_count", "manufacturer"
    ]
    
    list_filter = [
        "medication_type", "prescription_type", "manufacturer"
    ]
    
    search_fields = ["name", "generic_name", "brand_name", "manufacturer"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("name"),
            FieldPanel("generic_name"),
            FieldPanel("brand_name"),
            FieldPanel("medication_type"),
            FieldPanel("prescription_type"),
        ], heading=_("Basic Information")),
        ObjectList([
            FieldPanel("strength"),
            FieldPanel("dosage_unit"),
            FieldPanel("pill_count"),
            FieldPanel("low_stock_threshold"),
        ], heading=_("Dosage & Stock")),
        ObjectList([
            FieldPanel("manufacturer"),
            FieldPanel("description"),
            FieldPanel("active_ingredients"),
            FieldPanel("side_effects"),
            FieldPanel("contraindications"),
        ], heading=_("Additional Details")),
    ])


class MedicationScheduleViewSet(ModelViewSet):
    """ViewSet for managing medication schedules."""
    model = MedicationSchedule
    icon = "date"
    menu_label = _("Medication Schedules")
    menu_name = "medication-schedules"
    add_to_admin_menu = True
    menu_order = 101
    
    list_display = [
        "patient", "medication", "timing", "dosage_amount", "frequency", 
        "start_date", "end_date", "status"
    ]
    
    list_filter = [
        "timing", "status", "start_date", "end_date"
    ]
    
    search_fields = ["patient__username", "medication__name"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("patient"),
            FieldPanel("medication"),
            FieldPanel("timing"),
            FieldPanel("custom_time"),
            FieldPanel("dosage_amount"),
            FieldPanel("frequency"),
        ], heading=_("Schedule Details")),
        ObjectList([
            FieldPanel("start_date"),
            FieldPanel("end_date"),
            FieldPanel("status"),
        ], heading=_("Timing")),
        ObjectList([
            FieldPanel("monday"),
            FieldPanel("tuesday"),
            FieldPanel("wednesday"),
            FieldPanel("thursday"),
            FieldPanel("friday"),
            FieldPanel("saturday"),
            FieldPanel("sunday"),
        ], heading=_("Days of Week")),
        ObjectList([
            FieldPanel("instructions"),
        ], heading=_("Instructions")),
    ])


class MedicationLogViewSet(ModelViewSet):
    """ViewSet for managing medication logs."""
    model = MedicationLog
    icon = "history"
    menu_label = _("Medication Logs")
    menu_name = "medication-logs"
    add_to_admin_menu = True
    menu_order = 102
    
    list_display = [
        "patient", "medication", "scheduled_time", "actual_time", 
        "status", "dosage_taken"
    ]
    
    list_filter = [
        "status", "scheduled_time", "actual_time", "medication__medication_type"
    ]
    
    search_fields = ["patient__username", "medication__name", "notes"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("patient"),
            FieldPanel("medication"),
            FieldPanel("schedule"),
            FieldPanel("scheduled_time"),
            FieldPanel("actual_time"),
        ], heading=_("Log Details")),
        ObjectList([
            FieldPanel("status"),
            FieldPanel("dosage_taken"),
            FieldPanel("notes"),
            FieldPanel("side_effects"),
        ], heading=_("Status & Notes")),
    ])


class StockAlertViewSet(ModelViewSet):
    """ViewSet for managing stock alerts."""
    model = StockAlert
    icon = "warning"
    menu_label = _("Stock Alerts")
    menu_name = "stock-alerts"
    add_to_admin_menu = True
    menu_order = 103
    
    list_display = [
        "medication", "alert_type", "priority", "status", 
        "current_stock", "threshold_level", "created_at"
    ]
    
    list_filter = [
        "alert_type", "priority", "status", "created_at"
    ]
    
    search_fields = ["medication__name", "title", "message"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("medication"),
            FieldPanel("created_by"),
            FieldPanel("alert_type"),
            FieldPanel("priority"),
            FieldPanel("status"),
        ], heading=_("Alert Details")),
        ObjectList([
            FieldPanel("title"),
            FieldPanel("message"),
            FieldPanel("current_stock"),
            FieldPanel("threshold_level"),
        ], heading=_("Alert Information")),
        ObjectList([
            FieldPanel("acknowledged_by"),
            FieldPanel("acknowledged_at"),
            FieldPanel("resolved_at"),
            FieldPanel("resolution_notes"),
        ], heading=_("Resolution")),
    ])


class NotificationViewSet(ModelViewSet):
    """ViewSet for managing notifications."""
    model = Notification
    icon = "mail"
    menu_label = _("Notifications")
    menu_name = "notifications"
    add_to_admin_menu = True
    menu_order = 200
    
    list_display = [
        "title", "notification_type", "priority", "status", 
        "is_active", "show_on_dashboard", "created_at"
    ]
    
    list_filter = [
        "notification_type", "priority", "status", "is_active", 
        "show_on_dashboard", "require_acknowledgment"
    ]
    
    search_fields = ["title", "content"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("title"),
            FieldPanel("content"),
            FieldPanel("notification_type"),
            FieldPanel("priority"),
        ], heading=_("Notification Details")),
        ObjectList([
            FieldPanel("status"),
            FieldPanel("is_active"),
            FieldPanel("show_on_dashboard"),
            FieldPanel("require_acknowledgment"),
        ], heading=_("Display Settings")),
        ObjectList([
            FieldPanel("target_users"),
            FieldPanel("scheduled_at"),
            FieldPanel("expires_at"),
        ], heading=_("Targeting & Timing")),
    ])


class UserNotificationViewSet(ModelViewSet):
    """ViewSet for managing user notifications."""
    model = UserNotification
    icon = "user"
    menu_label = _("User Notifications")
    menu_name = "user-notifications"
    add_to_admin_menu = True
    menu_order = 201
    
    list_display = [
        "user", "notification", "status", "sent_at", 
        "read_at", "acknowledged_at"
    ]
    
    list_filter = [
        "status", "sent_at", "read_at", "acknowledged_at"
    ]
    
    search_fields = ["user__username", "notification__title"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("user"),
            FieldPanel("notification"),
            FieldPanel("status"),
        ], heading=_("User & Notification")),
        ObjectList([
            FieldPanel("read_at"),
            FieldPanel("acknowledged_at"),
            FieldPanel("dismissed_at"),
        ], heading=_("Timestamps")),
    ])


class NotificationTemplateViewSet(ModelViewSet):
    """ViewSet for managing notification templates."""
    model = NotificationTemplate
    icon = "doc-full-inverse"
    menu_label = _("Notification Templates")
    menu_name = "notification-templates"
    add_to_admin_menu = True
    menu_order = 202
    
    list_display = [
        "name", "template_type", "is_active", "created_at"
    ]
    
    list_filter = [
        "template_type", "is_active", "created_at"
    ]
    
    search_fields = ["name", "content"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("name"),
            FieldPanel("template_type"),
            FieldPanel("content"),
        ], heading=_("Template Details")),
        ObjectList([
            FieldPanel("is_active"),
            FieldPanel("variables"),
        ], heading=_("Settings")),
    ])


class UserViewSet(ModelViewSet):
    """ViewSet for managing users."""
    model = User
    icon = "user"
    menu_label = _("Users")
    menu_name = "users"
    add_to_admin_menu = True
    menu_order = 300
    
    list_display = [
        "username", "email", "first_name", "last_name", 
        "user_type", "is_active", "date_joined"
    ]
    
    list_filter = [
        "user_type", "is_active", "is_staff", "is_superuser", "date_joined"
    ]
    
    search_fields = ["username", "email", "first_name", "last_name"]
    
    edit_handler = TabbedInterface([
        ObjectList([
            FieldPanel("username"),
            FieldPanel("email"),
            FieldPanel("first_name"),
            FieldPanel("last_name"),
        ], heading=_("Basic Information")),
        ObjectList([
            FieldPanel("user_type"),
            FieldPanel("is_active"),
            FieldPanel("is_staff"),
            FieldPanel("is_superuser"),
        ], heading=_("Account Status")),
        ObjectList([
            FieldPanel("date_joined"),
            FieldPanel("last_login"),
        ], heading=_("Timestamps")),
    ])


# ============================================================================
# VIEWSET INSTANCES
# ============================================================================

medication_viewset = MedicationViewSet("medication")
medication_schedule_viewset = MedicationScheduleViewSet("medication-schedule")
medication_log_viewset = MedicationLogViewSet("medication-log")
stock_alert_viewset = StockAlertViewSet("stock-alert")
notification_viewset = NotificationViewSet("notification")
user_notification_viewset = UserNotificationViewSet("user-notification")
notification_template_viewset = NotificationTemplateViewSet("notification-template")
user_viewset = UserViewSet("user")


# ============================================================================
# HOOK REGISTRATIONS
# ============================================================================

@hooks.register("register_admin_viewset")
def register_medication_viewsets():
    """Register all medication-related viewsets."""
    return [
        medication_viewset,
        medication_schedule_viewset,
        medication_log_viewset,
        stock_alert_viewset,
    ]


@hooks.register("register_admin_viewset")
def register_notification_viewsets():
    """Register all notification-related viewsets."""
    return [
        notification_viewset,
        user_notification_viewset,
        notification_template_viewset,
    ]


@hooks.register("register_admin_viewset")
def register_user_viewset():
    """Register user viewset."""
    return [user_viewset]


# ============================================================================
# CUSTOM ADMIN FEATURES
# ============================================================================

class MedicationSummaryItem(SummaryItem):
    """Custom summary item for medication statistics."""
    
    def __init__(self, request, count, label, url, icon_name, status_class='info'):
        self.count = count
        self.label = label
        self.url = url
        self.icon_name = icon_name
        self.status_class = status_class
        super().__init__(request)
    
    def render_html(self, parent_context):
        """Render the summary item HTML with enhanced styling."""
        return format_html(
            '<div class="medguard-summary-item {}">'
            '<a href="{}" class="medguard-summary-link">'
            '<div class="medguard-summary-icon">'
            '<svg class="medguard-summary-icon__svg" aria-hidden="true" width="48" height="48">'
            '<use href="#icon-{}"></use>'
            '</svg>'
            '</div>'
            '<div class="medguard-summary-content">'
            '<div class="medguard-summary-count">{}</div>'
            '<div class="medguard-summary-label">{}</div>'
            '</div>'
            '</a>'
            '</div>',
            self.status_class,
            self.url,
            self.icon_name,
            self.count,
            self.label
        )


@hooks.register('construct_homepage_summary_items')
def add_medication_summary_items(request, summary_items):
    """Add medication-related summary items and enhance default summary items to the admin homepage."""
    from medications.models import Medication, MedicationLog, StockAlert
    from notifications.models import Notification
    from django.utils import timezone
    from wagtail.models import Page
    from wagtail.images.models import Image
    from wagtail.documents.models import Document
    
    # Store original summary items to replace them
    original_summary_items = summary_items[:]
    summary_items.clear()
    
    # Add enhanced default summary items
    # Pages
    page_count = Page.objects.count()
    summary_items.append(
        MedicationSummaryItem(
            request,
            count=page_count,
            label=_('Pages'),
            url=reverse('wagtailadmin_explore_root'),
            icon_name='doc-full',
            status_class='success' if page_count > 0 else 'info'
        )
    )
    
    # Images
    image_count = Image.objects.count()
    summary_items.append(
        MedicationSummaryItem(
            request,
            count=image_count,
            label=_('Images'),
            url=reverse('wagtailimages:index'),
            icon_name='image',
            status_class='success' if image_count > 0 else 'info'
        )
    )
    
    # Documents
    document_count = Document.objects.count()
    summary_items.append(
        MedicationSummaryItem(
            request,
            count=document_count,
            label=_('Documents'),
            url=reverse('wagtaildocs:index'),
            icon_name='doc-full-inverse',
            status_class='success' if document_count > 0 else 'info'
        )
    )
    
    # Add medication count
    medication_count = Medication.objects.count()
    summary_items.append(
        MedicationSummaryItem(
            request,
            count=medication_count,
            label=_('Total Medications'),
            url='/admin/medications/',
            icon_name='doc-full',
            status_class='success' if medication_count > 0 else 'info'
        )
    )
    
    # Add recent medication logs
    recent_logs = MedicationLog.objects.filter(
        scheduled_time__date=timezone.now().date()
    ).count()
    summary_items.append(
        MedicationSummaryItem(
            request,
            count=recent_logs,
            label=_('Today\'s Medication Logs'),
            url='/admin/medication-logs/',
            icon_name='history',
            status_class='info'
        )
    )
    
    # Add active stock alerts
    active_alerts = StockAlert.objects.filter(status='active').count()
    summary_items.append(
        MedicationSummaryItem(
            request,
            count=active_alerts,
            label=_('Active Stock Alerts'),
            url='/admin/stock-alerts/',
            icon_name='warning',
            status_class='alert' if active_alerts > 0 else 'success'
        )
    )
    
    # Add active notifications
    active_notifications = Notification.objects.filter(
        is_active=True, status='active'
    ).count()
    summary_items.append(
        MedicationSummaryItem(
            request,
            count=active_notifications,
            label=_('Active Notifications'),
            url='/admin/notifications/',
            icon_name='mail',
            status_class='warning' if active_notifications > 0 else 'info'
        )
    )


@hooks.register('insert_global_admin_css')
def global_admin_css():
    """Add custom CSS for the admin interface."""
    return format_html(
        '<style>{}</style>',
        '''
        /* MedGuard SA Enhanced Summary Items */
        .medguard-summary-item {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid #E5E7EB;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 1rem;
        }

        .medguard-summary-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .medguard-summary-link {
            text-decoration: none;
            color: inherit;
            display: block;
        }

        .medguard-summary-link:hover {
            text-decoration: none;
            color: inherit;
        }

        .medguard-summary-icon {
            margin-bottom: 1rem;
            display: flex;
            justify-content: center;
        }

        .medguard-summary-icon__svg {
            color: #2563EB;
            width: 48px;
            height: 48px;
        }

        .medguard-summary-content {
            text-align: center;
        }

        .medguard-summary-count {
            font-size: 2.5rem;
            font-weight: 700;
            color: #2563EB;
            margin: 0;
            line-height: 1;
        }

        .medguard-summary-label {
            font-size: 0.875rem;
            color: #6B7280;
            margin: 0.5rem 0 0 0;
            font-weight: 500;
            line-height: 1.2;
        }

        /* Enhanced Summary Grid Layout */
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }

        /* Override default Wagtail summary items to use our enhanced styling */
        .w-summary {
            display: grid !important;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
            gap: 1.5rem !important;
            margin-bottom: 2rem !important;
        }

        .w-summary .w-summary-item {
            display: none !important;
        }

        /* Ensure our enhanced items are properly spaced */
        .medguard-summary-item {
            margin: 0 !important;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .summary-stats {
                grid-template-columns: repeat(2, 1fr);
                gap: 1rem;
            }
            
            .medguard-summary-item {
                padding: 1rem;
            }
            
            .medguard-summary-count {
                font-size: 2rem;
            }
            
            .medguard-summary-icon__svg {
                width: 36px;
                height: 36px;
            }
        }

        @media (max-width: 480px) {
            .summary-stats {
                grid-template-columns: 1fr;
            }
        }

        /* Animation for loading */
        .medguard-summary-item {
            animation: fadeInUp 0.6s ease-out;
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Status indicators */
        .medguard-summary-item.alert {
            border-left: 4px solid #EF4444;
        }

        .medguard-summary-item.warning {
            border-left: 4px solid #F59E0B;
        }

        .medguard-summary-item.success {
            border-left: 4px solid #10B981;
        }

        .medguard-summary-item.info {
            border-left: 4px solid #2563EB;
        }
        '''
    )


@hooks.register('insert_global_admin_js')
def global_admin_js():
    """Add custom JavaScript for the admin interface."""
    return format_html(
        '<script src="{}"></script>',
        '/static/js/medguard-admin.js'
    ) 