from wagtail import hooks
from wagtail.admin.panels import (
    FieldPanel, MultiFieldPanel, InlinePanel, 
    ObjectList, TabbedInterface, HelpPanel
)
from wagtail_modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register
)
from django_filters import FilterSet
from wagtail.admin.forms import WagtailAdminModelForm
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.db.models import Q, Count
from django.urls import reverse, path
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse
import uuid

# Import models from the main Django app
from medications.models import Medication, MedicationSchedule, MedicationLog, StockAlert


class MedicationAdmin(ModelAdmin):
    """Custom ModelAdmin for Medication model."""
    
    model = Medication
    menu_label = _('Medications')
    menu_icon = 'medicines'
    menu_order = 100
    list_display = (
        'name', 'medication_type', 'strength', 'pill_count', 
        'low_stock_threshold', 'stock_status', 'expiration_status', 
        'prescription_type', 'manufacturer'
    )
    list_filter = (
        'medication_type',
        'prescription_type',
        'manufacturer',
        'expiration_date',
    )
    search_fields = ('name', 'generic_name', 'brand_name', 'manufacturer', 'active_ingredients')
    list_per_page = 20
    ordering = ('name',)
    
    # Custom panels for better organization
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('generic_name'),
            FieldPanel('brand_name'),
            FieldPanel('medication_type'),
            FieldPanel('prescription_type'),
        ], heading=_('Basic Information')),
        
        MultiFieldPanel([
            FieldPanel('strength'),
            FieldPanel('dosage_unit'),
        ], heading=_('Dosage Information')),
        
        MultiFieldPanel([
            FieldPanel('pill_count'),
            FieldPanel('low_stock_threshold'),
        ], heading=_('Stock Management')),
        
        MultiFieldPanel([
            FieldPanel('description'),
            FieldPanel('active_ingredients'),
            FieldPanel('manufacturer'),
        ], heading=_('Additional Information')),
        
        MultiFieldPanel([
            FieldPanel('side_effects'),
            FieldPanel('contraindications'),
        ], heading=_('Safety Information')),
        
        MultiFieldPanel([
            FieldPanel('storage_instructions'),
            FieldPanel('expiration_date'),
        ], heading=_('Storage and Handling')),
    ]
    
    # Custom actions
    def stock_status(self, obj):
        """Display stock status with color coding."""
        if obj.is_low_stock:
            return format_html(
                '<span style="color: #EF4444; font-weight: bold;">⚠️ {}</span>',
                _('Low Stock')
            )
        return format_html(
            '<span style="color: #10B981; font-weight: bold;">✓ {}</span>',
            _('In Stock')
        )
    stock_status.short_description = _('Stock Status')
    stock_status.admin_order_field = 'pill_count'
    
    def expiration_status(self, obj):
        """Display expiration status with color coding."""
        if obj.is_expired:
            return format_html(
                '<span style="color: #EF4444; font-weight: bold;">❌ {}</span>',
                _('Expired')
            )
        elif obj.is_expiring_soon:
            return format_html(
                '<span style="color: #F59E0B; font-weight: bold;">⚠️ {}</span>',
                _('Expiring Soon')
            )
        return format_html(
            '<span style="color: #10B981; font-weight: bold;">✓ {}</span>',
            _('Valid')
        )
    expiration_status.short_description = _('Expiration Status')
    
    # Bulk actions
    def get_queryset(self, request):
        """Custom queryset with annotations."""
        qs = super().get_queryset(request)
        return qs.select_related().annotate(
            schedule_count=Count('schedules'),
            log_count=Count('logs'),
            alert_count=Count('stock_alerts')
        )


class MedicationScheduleAdmin(ModelAdmin):
    """Custom ModelAdmin for MedicationSchedule model."""
    
    model = MedicationSchedule
    menu_label = _('Medication Schedules')
    menu_icon = 'time'
    menu_order = 200
    list_display = (
        'patient', 'medication', 'timing', 'dosage_amount', 
        'frequency', 'status', 'active_status', 'take_today_status',
        'start_date', 'end_date'
    )
    list_filter = (
        'timing',
        'status',
        'frequency',
        'start_date',
        'end_date',
        'patient',
        'medication',
    )
    search_fields = (
        'patient__username', 'patient__first_name', 'patient__last_name',
        'medication__name', 'instructions'
    )
    list_per_page = 20
    ordering = ('patient', 'timing', 'start_date')
    
    panels = [
        MultiFieldPanel([
            FieldPanel('patient'),
            FieldPanel('medication'),
        ], heading=_('Patient and Medication')),
        
        MultiFieldPanel([
            FieldPanel('timing'),
            FieldPanel('custom_time'),
            FieldPanel('dosage_amount'),
            FieldPanel('frequency'),
        ], heading=_('Schedule Information')),
        
        MultiFieldPanel([
            FieldPanel('monday'),
            FieldPanel('tuesday'),
            FieldPanel('wednesday'),
            FieldPanel('thursday'),
            FieldPanel('friday'),
            FieldPanel('saturday'),
            FieldPanel('sunday'),
        ], heading=_('Days of Week')),
        
        MultiFieldPanel([
            FieldPanel('start_date'),
            FieldPanel('end_date'),
        ], heading=_('Schedule Period')),
        
        MultiFieldPanel([
            FieldPanel('status'),
            FieldPanel('instructions'),
        ], heading=_('Status and Instructions')),
    ]
    
    def active_status(self, obj):
        """Display active status with color coding."""
        if obj.is_active:
            return format_html(
                '<span style="color: #10B981; font-weight: bold;">✓ {}</span>',
                _('Active')
            )
        return format_html(
            '<span style="color: #EF4444; font-weight: bold;">❌ {}</span>',
            _('Inactive')
        )
    active_status.short_description = _('Active Status')
    
    def take_today_status(self, obj):
        """Display whether medication should be taken today."""
        if obj.should_take_today:
            return format_html(
                '<span style="color: #10B981; font-weight: bold;">✓ {}</span>',
                _('Today')
            )
        return format_html(
            '<span style="color: #6B7280; font-weight: bold;">- {}</span>',
            _('Not Today')
        )
    take_today_status.short_description = _('Take Today')


class MedicationLogAdmin(ModelAdmin):
    """Custom ModelAdmin for MedicationLog model."""
    
    model = MedicationLog
    menu_label = _('Medication Logs')
    menu_icon = 'list-ul'
    menu_order = 300
    list_display = (
        'patient', 'medication', 'scheduled_time', 'actual_time',
        'status', 'dosage_taken', 'on_time_status', 'adherence_score_display'
    )
    list_filter = (
        'status',
        'scheduled_time',
        'actual_time',
        'patient',
        'medication',
    )
    search_fields = (
        'patient__username', 'patient__first_name', 'patient__last_name',
        'medication__name', 'notes', 'side_effects'
    )
    list_per_page = 25
    ordering = ('-scheduled_time',)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('patient'),
            FieldPanel('medication'),
            FieldPanel('schedule'),
        ], heading=_('Patient and Medication')),
        
        MultiFieldPanel([
            FieldPanel('scheduled_time'),
            FieldPanel('actual_time'),
        ], heading=_('Timing Information')),
        
        MultiFieldPanel([
            FieldPanel('status'),
            FieldPanel('dosage_taken'),
        ], heading=_('Dose Information')),
        
        MultiFieldPanel([
            FieldPanel('notes'),
            FieldPanel('side_effects'),
        ], heading=_('Notes and Observations')),
    ]
    
    def on_time_status(self, obj):
        """Display on-time status with color coding."""
        if obj.is_on_time:
            return format_html(
                '<span style="color: #10B981; font-weight: bold;">✓ {}</span>',
                _('On Time')
            )
        elif obj.status == MedicationLog.Status.TAKEN:
            return format_html(
                '<span style="color: #F59E0B; font-weight: bold;">⚠️ {}</span>',
                _('Late')
            )
        return format_html(
            '<span style="color: #6B7280; font-weight: bold;">- {}</span>',
            _('N/A')
        )
    on_time_status.short_description = _('On Time')
    
    def adherence_score_display(self, obj):
        """Display adherence score with color coding."""
        score = obj.adherence_score
        if score == 100:
            color = '#10B981'
            icon = '✓'
        elif score >= 80:
            color = '#F59E0B'
            icon = '⚠'
        else:
            color = '#EF4444'
            icon = '❌'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}%</span>',
            color, icon, score
        )
    adherence_score_display.short_description = _('Adherence Score')


class StockAlertAdmin(ModelAdmin):
    """Custom ModelAdmin for StockAlert model."""
    
    model = StockAlert
    menu_label = _('Stock Alerts')
    menu_icon = 'warning'
    menu_order = 400
    list_display = (
        'medication', 'alert_type', 'priority', 'status', 
        'current_stock', 'threshold_level', 'created_by', 'created_at'
    )
    list_filter = (
        'alert_type',
        'priority',
        'status',
        'created_at',
        'medication',
        'created_by',
    )
    search_fields = (
        'medication__name', 'title', 'message', 'created_by__username'
    )
    list_per_page = 20
    ordering = ('-created_at',)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('medication'),
            FieldPanel('alert_type'),
            FieldPanel('priority'),
            FieldPanel('status'),
        ], heading=_('Alert Information')),
        
        MultiFieldPanel([
            FieldPanel('title'),
            FieldPanel('message'),
        ], heading=_('Alert Details')),
        
        MultiFieldPanel([
            FieldPanel('current_stock'),
            FieldPanel('threshold_level'),
        ], heading=_('Stock Information')),
        
        MultiFieldPanel([
            FieldPanel('created_by'),
            FieldPanel('acknowledged_by'),
        ], heading=_('User Information')),
        
        MultiFieldPanel([
            FieldPanel('resolved_at'),
            FieldPanel('resolution_notes'),
        ], heading=_('Resolution')),
    ]
    
    def get_queryset(self, request):
        """Custom queryset with priority ordering."""
        qs = super().get_queryset(request)
        return qs.select_related('medication', 'created_by', 'acknowledged_by')


class MedicationManagementGroup(ModelAdminGroup):
    """Group for all medication management ModelAdmins."""
    
    menu_label = _('Medication Management')
    menu_icon = 'medicines'
    menu_order = 100
    items = (
        MedicationAdmin,
        MedicationScheduleAdmin,
        MedicationLogAdmin,
        StockAlertAdmin,
    )


# Register the ModelAdmin group
modeladmin_register(MedicationManagementGroup)


# Add custom CSS for healthcare theme
@hooks.register('insert_global_admin_css')
def global_admin_css():
    """Add custom CSS for healthcare theme."""
    return format_html(
        '<link rel="stylesheet" href="{}">',
        '/static/css/medication-admin.css'
    )


# Add custom JavaScript for enhanced functionality
@hooks.register('insert_global_admin_js')
def global_admin_js():
    """Add custom JavaScript for enhanced functionality."""
    return format_html(
        '<script src="{}"></script>',
        '/static/js/medication-admin.js'
    ) 