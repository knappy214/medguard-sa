from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from .models import Medication, MedicationSchedule, MedicationLog, StockAlert


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    """Admin interface for the Medication model."""
    
    list_display = (
        'name', 'medication_type', 'strength', 'pill_count', 
        'low_stock_threshold', 'is_low_stock', 'is_expired', 
        'prescription_type', 'manufacturer'
    )
    
    list_filter = (
        'medication_type', 'prescription_type', 'manufacturer'
    )
    
    search_fields = (
        'name', 'generic_name', 'brand_name', 'manufacturer',
        'active_ingredients'
    )
    
    ordering = ('name',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': (
                'name', 'generic_name', 'brand_name', 'medication_type',
                'prescription_type'
            )
        }),
        (_('Dosage Information'), {
            'fields': ('strength', 'dosage_unit')
        }),
        (_('Stock Management'), {
            'fields': ('pill_count', 'low_stock_threshold')
        }),
        (_('Additional Information'), {
            'fields': (
                'description', 'active_ingredients', 'manufacturer'
            )
        }),
        (_('Safety Information'), {
            'fields': ('side_effects', 'contraindications')
        }),
        (_('Storage and Handling'), {
            'fields': ('storage_instructions', 'expiration_date')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['mark_as_expired', 'update_stock_levels']
    
    def is_low_stock(self, obj):
        """Display low stock status with color coding."""
        if obj.is_low_stock:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ Low Stock</span>'
            )
        return format_html(
            '<span style="color: green;">✓ In Stock</span>'
        )
    is_low_stock.short_description = _('Stock Status')
    is_low_stock.admin_order_field = 'pill_count'
    
    def is_expired(self, obj):
        """Display expiration status with color coding."""
        if obj.is_expired:
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ Expired</span>'
            )
        elif obj.is_expiring_soon:
            return format_html(
                '<span style="color: orange; font-weight: bold;">⚠️ Expiring Soon</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Valid</span>'
        )
    is_expired.short_description = _('Expiration Status')
    
    def mark_as_expired(self, request, queryset):
        """Mark selected medications as expired."""
        from django.utils import timezone
        updated = queryset.update(expiration_date=timezone.now().date())
        self.message_user(
            request,
            f'Successfully marked {updated} medication(s) as expired.'
        )
    mark_as_expired.short_description = _('Mark selected medications as expired')
    
    def update_stock_levels(self, request, queryset):
        """Update stock levels for selected medications."""
        # This would typically be a form action
        self.message_user(
            request,
            'Stock level update functionality would be implemented here.'
        )
    update_stock_levels.short_description = _('Update stock levels')


@admin.register(MedicationSchedule)
class MedicationScheduleAdmin(admin.ModelAdmin):
    """Admin interface for the MedicationSchedule model."""
    
    list_display = (
        'patient', 'medication', 'timing', 'dosage_amount', 
        'frequency', 'status', 'is_active', 'should_take_today',
        'start_date', 'end_date'
    )
    
    list_filter = (
        'timing', 'status', 'frequency', 'start_date', 'end_date',
        'patient__user_type'
    )
    
    search_fields = (
        'patient__username', 'patient__first_name', 'patient__last_name',
        'medication__name', 'instructions'
    )
    
    ordering = ('patient', 'timing', 'start_date')
    
    fieldsets = (
        (_('Patient and Medication'), {
            'fields': ('patient', 'medication')
        }),
        (_('Schedule Information'), {
            'fields': (
                'timing', 'custom_time', 'dosage_amount', 'frequency'
            )
        }),
        (_('Days of Week'), {
            'fields': (
                'monday', 'tuesday', 'wednesday', 'thursday',
                'friday', 'saturday', 'sunday'
            )
        }),
        (_('Schedule Period'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Status and Instructions'), {
            'fields': ('status', 'instructions')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['activate_schedules', 'deactivate_schedules']
    
    def is_active(self, obj):
        """Display active status with color coding."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: red;">❌ Inactive</span>'
        )
    is_active.short_description = _('Active Status')
    
    def should_take_today(self, obj):
        """Display whether medication should be taken today."""
        if obj.should_take_today:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Today</span>'
            )
        return format_html(
            '<span style="color: gray;">- Not Today</span>'
        )
    should_take_today.short_description = _('Take Today')
    
    def activate_schedules(self, request, queryset):
        """Activate selected schedules."""
        updated = queryset.update(status=MedicationSchedule.Status.ACTIVE)
        self.message_user(
            request,
            f'Successfully activated {updated} schedule(s).'
        )
    activate_schedules.short_description = _('Activate selected schedules')
    
    def deactivate_schedules(self, request, queryset):
        """Deactivate selected schedules."""
        updated = queryset.update(status=MedicationSchedule.Status.INACTIVE)
        self.message_user(
            request,
            f'Successfully deactivated {updated} schedule(s).'
        )
    deactivate_schedules.short_description = _('Deactivate selected schedules')


@admin.register(MedicationLog)
class MedicationLogAdmin(admin.ModelAdmin):
    """Admin interface for the MedicationLog model."""
    
    list_display = (
        'patient', 'medication', 'scheduled_time', 'actual_time',
        'status', 'dosage_taken', 'is_on_time', 'adherence_score'
    )
    
    list_filter = (
        'status', 'scheduled_time', 'actual_time', 'patient__user_type'
    )
    
    search_fields = (
        'patient__username', 'patient__first_name', 'patient__last_name',
        'medication__name', 'notes', 'side_effects'
    )
    
    ordering = ('-scheduled_time',)
    
    fieldsets = (
        (_('Patient and Medication'), {
            'fields': ('patient', 'medication', 'schedule')
        }),
        (_('Timing Information'), {
            'fields': ('scheduled_time', 'actual_time')
        }),
        (_('Dose Information'), {
            'fields': ('status', 'dosage_taken')
        }),
        (_('Notes and Observations'), {
            'fields': ('notes', 'side_effects')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['mark_as_taken', 'mark_as_missed']
    
    def is_on_time(self, obj):
        """Display on-time status with color coding."""
        if obj.is_on_time:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ On Time</span>'
            )
        elif obj.status == MedicationLog.Status.TAKEN:
            return format_html(
                '<span style="color: orange;">⚠️ Late</span>'
            )
        return format_html(
            '<span style="color: gray;">- N/A</span>'
        )
    is_on_time.short_description = _('On Time')
    
    def adherence_score(self, obj):
        """Display adherence score with color coding."""
        score = obj.adherence_score
        if score == 100:
            color = 'green'
            icon = '✓'
        elif score >= 80:
            color = 'orange'
            icon = '⚠'
        else:
            color = 'red'
            icon = '❌'
        
        return format_html(
            f'<span style="color: {color}; font-weight: bold;">{icon} {score}%</span>'
        )
    adherence_score.short_description = _('Adherence Score')
    
    def mark_as_taken(self, request, queryset):
        """Mark selected logs as taken."""
        from django.utils import timezone
        updated = queryset.update(
            status=MedicationLog.Status.TAKEN,
            actual_time=timezone.now()
        )
        self.message_user(
            request,
            f'Successfully marked {updated} log(s) as taken.'
        )
    mark_as_taken.short_description = _('Mark selected logs as taken')
    
    def mark_as_missed(self, request, queryset):
        """Mark selected logs as missed."""
        updated = queryset.update(status=MedicationLog.Status.MISSED)
        self.message_user(
            request,
            f'Successfully marked {updated} log(s) as missed.'
        )
    mark_as_missed.short_description = _('Mark selected logs as missed')


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    """Admin interface for the StockAlert model."""
    
    list_display = (
        'medication', 'alert_type', 'priority', 'status', 
        'current_stock', 'threshold_level', 'created_by', 'created_at'
    )
    
    list_filter = (
        'alert_type', 'priority', 'status', 'created_at'
    )
    
    search_fields = (
        'medication__name', 'title', 'message', 'created_by__username'
    )
    
    ordering = ('-created_at',)
    
    fieldsets = (
        (_('Alert Information'), {
            'fields': (
                'medication', 'alert_type', 'priority', 'status'
            )
        }),
        (_('Alert Details'), {
            'fields': ('title', 'message')
        }),
        (_('Stock Information'), {
            'fields': ('current_stock', 'threshold_level')
        }),
        (_('User Information'), {
            'fields': ('created_by', 'acknowledged_by')
        }),
        (_('Resolution'), {
            'fields': ('resolved_at', 'resolution_notes')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'acknowledged_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'acknowledged_at')
    
    actions = ['acknowledge_alerts', 'resolve_alerts', 'dismiss_alerts']
    
    def acknowledge_alerts(self, request, queryset):
        """Acknowledge selected alerts."""
        updated = queryset.update(
            status=StockAlert.Status.ACKNOWLEDGED,
            acknowledged_by=request.user,
            acknowledged_at=timezone.now()
        )
        self.message_user(
            request,
            f'Successfully acknowledged {updated} alert(s).'
        )
    acknowledge_alerts.short_description = _('Acknowledge selected alerts')
    
    def resolve_alerts(self, request, queryset):
        """Resolve selected alerts."""
        from django.utils import timezone
        updated = queryset.update(
            status=StockAlert.Status.RESOLVED,
            resolved_at=timezone.now()
        )
        self.message_user(
            request,
            f'Successfully resolved {updated} alert(s).'
        )
    resolve_alerts.short_description = _('Resolve selected alerts')
    
    def dismiss_alerts(self, request, queryset):
        """Dismiss selected alerts."""
        updated = queryset.update(status=StockAlert.Status.DISMISSED)
        self.message_user(
            request,
            f'Successfully dismissed {updated} alert(s).'
        )
    dismiss_alerts.short_description = _('Dismiss selected alerts')
