# -*- coding: utf-8 -*-
"""
MedGuard SA - Privacy Compliance Dashboard Module

Implements comprehensive compliance dashboard for healthcare privacy monitoring
with real-time metrics, audit trails, and regulatory reporting capabilities.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet

# Import from other privacy modules
from .wagtail_privacy import (
    MedicalDataRetentionPolicy, DataRetentionMixin, ConsentCategory, 
    PatientConsent, ConsentManager, AnonymizationProfile, DataAnonymizer
)
from .data_export import DataExportRequest, DataExportManager
from .privacy_search import SearchAuditLog, PrivacySearchManager
from .cookie_management import UserCookiePreference, CookieManager
from .breach_notification import DataBreachIncident, BreachNotificationManager
from .patient_privacy_settings import PatientPrivacySetting, PatientPrivacyManager

logger = logging.getLogger(__name__)
User = get_user_model()


@register_snippet
class ComplianceDashboardWidget(models.Model):
    """
    Configurable widgets for the compliance monitoring dashboard.
    
    Defines different types of compliance monitoring widgets
    that can be displayed on the privacy compliance dashboard.
    """
    
    WIDGET_TYPES = [
        ('compliance_overview', _('Compliance Overview')),
        ('consent_metrics', _('Consent Management Metrics')),
        ('data_retention_status', _('Data Retention Status')),
        ('breach_incidents', _('Data Breach Incidents')),
        ('export_requests', _('Data Export Requests')),
        ('deletion_workflows', _('Data Deletion Workflows')),
        ('search_audit', _('Search Audit Logs')),
        ('cookie_compliance', _('Cookie Compliance')),
        ('anonymization_stats', _('Data Anonymization Statistics')),
        ('patient_privacy_settings', _('Patient Privacy Settings')),
        ('regulatory_deadlines', _('Regulatory Deadlines')),
        ('audit_trail', _('Audit Trail Summary')),
        ('risk_assessment', _('Privacy Risk Assessment')),
        ('training_compliance', _('Staff Training Compliance')),
        ('vendor_compliance', _('Third-Party Vendor Compliance')),
    ]
    
    REFRESH_INTERVALS = [
        ('realtime', _('Real-time')),
        ('1min', _('Every Minute')),
        ('5min', _('Every 5 Minutes')),
        ('15min', _('Every 15 Minutes')),
        ('1hour', _('Every Hour')),
        ('4hours', _('Every 4 Hours')),
        ('daily', _('Daily')),
        ('weekly', _('Weekly')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Widget Name"),
        help_text=_("Descriptive name for this dashboard widget")
    )
    
    widget_type = models.CharField(
        max_length=30,
        choices=WIDGET_TYPES,
        verbose_name=_("Widget Type"),
        help_text=_("Type of compliance monitoring widget")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of what this widget monitors")
    )
    
    configuration = models.JSONField(
        default=dict,
        verbose_name=_("Widget Configuration"),
        help_text=_("Configuration options for this widget")
    )
    
    refresh_interval = models.CharField(
        max_length=10,
        choices=REFRESH_INTERVALS,
        default='15min',
        verbose_name=_("Refresh Interval"),
        help_text=_("How often widget data should be refreshed")
    )
    
    display_order = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Display Order"),
        help_text=_("Order in which widget appears on dashboard")
    )
    
    required_permissions = models.JSONField(
        default=list,
        verbose_name=_("Required Permissions"),
        help_text=_("Permissions required to view this widget")
    )
    
    alert_thresholds = models.JSONField(
        default=dict,
        verbose_name=_("Alert Thresholds"),
        help_text=_("Thresholds for generating compliance alerts")
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Default Widget"),
        help_text=_("Whether this widget is shown by default")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('widget_type'),
            FieldPanel('description'),
        ], heading=_("Widget Information")),
        
        MultiFieldPanel([
            FieldPanel('configuration'),
            FieldPanel('refresh_interval'),
            FieldPanel('display_order'),
        ], heading=_("Configuration")),
        
        MultiFieldPanel([
            FieldPanel('required_permissions'),
            FieldPanel('alert_thresholds'),
        ], heading=_("Access Control & Alerts")),
        
        MultiFieldPanel([
            FieldPanel('is_default'),
            FieldPanel('is_active'),
        ], heading=_("Display Settings")),
    ]
    
    class Meta:
        verbose_name = _("Compliance Dashboard Widget")
        verbose_name_plural = _("Compliance Dashboard Widgets")
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"


class ComplianceAlert(models.Model):
    """
    Compliance alerts and notifications for privacy monitoring.
    
    Tracks compliance violations, warnings, and notifications
    that require attention from privacy officers.
    """
    
    ALERT_TYPES = [
        ('violation', _('Compliance Violation')),
        ('warning', _('Warning')),
        ('deadline_approaching', _('Deadline Approaching')),
        ('threshold_exceeded', _('Threshold Exceeded')),
        ('system_issue', _('System Issue')),
        ('data_breach', _('Data Breach Alert')),
        ('consent_expired', _('Consent Expired')),
        ('retention_overdue', _('Retention Period Overdue')),
        ('export_overdue', _('Export Request Overdue')),
        ('deletion_overdue', _('Deletion Request Overdue')),
    ]
    
    SEVERITY_LEVELS = [
        ('low', _('Low')),
        ('medium', _('Medium')),
        ('high', _('High')),
        ('critical', _('Critical')),
        ('emergency', _('Emergency')),
    ]
    
    ALERT_STATUS = [
        ('active', _('Active')),
        ('acknowledged', _('Acknowledged')),
        ('in_progress', _('In Progress')),
        ('resolved', _('Resolved')),
        ('dismissed', _('Dismissed')),
        ('escalated', _('Escalated')),
    ]
    
    alert_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Alert ID"),
        help_text=_("Unique identifier for this alert")
    )
    
    alert_type = models.CharField(
        max_length=30,
        choices=ALERT_TYPES,
        verbose_name=_("Alert Type")
    )
    
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        verbose_name=_("Severity Level")
    )
    
    status = models.CharField(
        max_length=20,
        choices=ALERT_STATUS,
        default='active',
        verbose_name=_("Status")
    )
    
    title = models.CharField(
        max_length=200,
        verbose_name=_("Alert Title")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of the compliance issue")
    )
    
    source_system = models.CharField(
        max_length=100,
        verbose_name=_("Source System"),
        help_text=_("System or module that generated this alert")
    )
    
    affected_records = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Affected Records"),
        help_text=_("Number of records affected by this issue")
    )
    
    compliance_framework = models.CharField(
        max_length=50,
        choices=[
            ('gdpr', _('GDPR')),
            ('popia', _('POPIA')),
            ('hipaa', _('HIPAA')),
            ('internal', _('Internal Policy')),
            ('multiple', _('Multiple Frameworks')),
        ],
        verbose_name=_("Compliance Framework")
    )
    
    deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Resolution Deadline"),
        help_text=_("When this issue must be resolved")
    )
    
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Assigned To"),
        related_name='assigned_compliance_alerts'
    )
    
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Acknowledged By"),
        related_name='acknowledged_compliance_alerts'
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Acknowledged At")
    )
    
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Resolved By"),
        related_name='resolved_compliance_alerts'
    )
    
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Resolved At")
    )
    
    resolution_notes = models.TextField(
        blank=True,
        verbose_name=_("Resolution Notes"),
        help_text=_("Notes about how the issue was resolved")
    )
    
    alert_data = models.JSONField(
        default=dict,
        verbose_name=_("Alert Data"),
        help_text=_("Additional data related to the alert")
    )
    
    auto_generated = models.BooleanField(
        default=True,
        verbose_name=_("Auto Generated"),
        help_text=_("Whether this alert was automatically generated")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Compliance Alert")
        verbose_name_plural = _("Compliance Alerts")
        ordering = ['-created_at', 'severity']
    
    def __str__(self):
        return f"{self.alert_id} - {self.title} ({self.get_severity_display()})"
    
    def save(self, *args, **kwargs):
        """Generate alert ID if not provided."""
        if not self.alert_id:
            from django.utils.crypto import get_random_string
            self.alert_id = f"ALERT-{timezone.now().strftime('%Y%m%d')}-{get_random_string(6).upper()}"
        
        super().save(*args, **kwargs)
    
    def acknowledge(self, user: User, notes: str = ""):
        """Acknowledge this alert."""
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        
        if notes:
            self.resolution_notes = notes
        
        self.save()
        
        logger.info(f"Compliance alert {self.alert_id} acknowledged by {user.username}")
    
    def resolve(self, user: User, resolution_notes: str):
        """Resolve this alert."""
        self.status = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_notes = resolution_notes
        self.save()
        
        logger.info(f"Compliance alert {self.alert_id} resolved by {user.username}")
    
    def is_overdue(self) -> bool:
        """Check if this alert is overdue for resolution."""
        if not self.deadline:
            return False
        
        return timezone.now() > self.deadline and self.status not in ['resolved', 'dismissed']
    
    def get_age_hours(self) -> int:
        """Get the age of this alert in hours."""
        return int((timezone.now() - self.created_at).total_seconds() / 3600)


class ComplianceMetric(models.Model):
    """
    Compliance metrics and KPIs for privacy monitoring.
    
    Stores calculated compliance metrics that are displayed
    on the privacy compliance dashboard.
    """
    
    METRIC_TYPES = [
        ('percentage', _('Percentage')),
        ('count', _('Count')),
        ('ratio', _('Ratio')),
        ('duration', _('Duration')),
        ('currency', _('Currency')),
        ('score', _('Score')),
    ]
    
    METRIC_CATEGORIES = [
        ('consent_management', _('Consent Management')),
        ('data_retention', _('Data Retention')),
        ('data_export', _('Data Export')),
        ('data_deletion', _('Data Deletion')),
        ('breach_response', _('Breach Response')),
        ('cookie_compliance', _('Cookie Compliance')),
        ('search_privacy', _('Search Privacy')),
        ('anonymization', _('Data Anonymization')),
        ('patient_settings', _('Patient Privacy Settings')),
        ('overall_compliance', _('Overall Compliance')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Metric Name")
    )
    
    metric_type = models.CharField(
        max_length=20,
        choices=METRIC_TYPES,
        verbose_name=_("Metric Type")
    )
    
    category = models.CharField(
        max_length=30,
        choices=METRIC_CATEGORIES,
        verbose_name=_("Category")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of what this metric measures")
    )
    
    current_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Current Value")
    )
    
    target_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Target Value")
    )
    
    previous_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Previous Value")
    )
    
    trend_direction = models.CharField(
        max_length=10,
        choices=[
            ('up', _('Trending Up')),
            ('down', _('Trending Down')),
            ('stable', _('Stable')),
            ('unknown', _('Unknown')),
        ],
        default='unknown',
        verbose_name=_("Trend Direction")
    )
    
    calculation_method = models.TextField(
        verbose_name=_("Calculation Method"),
        help_text=_("How this metric is calculated")
    )
    
    data_source = models.CharField(
        max_length=200,
        verbose_name=_("Data Source"),
        help_text=_("Source of data for this metric")
    )
    
    update_frequency = models.CharField(
        max_length=20,
        choices=[
            ('realtime', _('Real-time')),
            ('hourly', _('Hourly')),
            ('daily', _('Daily')),
            ('weekly', _('Weekly')),
            ('monthly', _('Monthly')),
        ],
        default='daily',
        verbose_name=_("Update Frequency")
    )
    
    last_calculated = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Calculated")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Compliance Metric")
        verbose_name_plural = _("Compliance Metrics")
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.current_value})"
    
    def update_value(self, new_value: float):
        """Update the metric value and trend."""
        self.previous_value = self.current_value
        self.current_value = new_value
        self.last_calculated = timezone.now()
        
        # Calculate trend
        if self.previous_value is not None:
            if new_value > self.previous_value:
                self.trend_direction = 'up'
            elif new_value < self.previous_value:
                self.trend_direction = 'down'
            else:
                self.trend_direction = 'stable'
        
        self.save()
    
    def is_meeting_target(self) -> Optional[bool]:
        """Check if metric is meeting its target value."""
        if self.target_value is None:
            return None
        
        return self.current_value >= self.target_value
    
    def get_variance_from_target(self) -> Optional[float]:
        """Get variance from target value as percentage."""
        if self.target_value is None or self.target_value == 0:
            return None
        
        return float((self.current_value - self.target_value) / self.target_value * 100)


class ComplianceDashboardManager:
    """
    Manager for privacy compliance dashboard operations.
    
    Provides methods for generating dashboard data, calculating metrics,
    and managing compliance monitoring.
    """
    
    @staticmethod
    def get_dashboard_data(user: User) -> Dict[str, Any]:
        """Get comprehensive compliance dashboard data."""
        
        # Get active widgets for the user
        widgets = ComplianceDashboardWidget.objects.filter(
            is_active=True
        ).order_by('display_order')
        
        # Filter widgets based on user permissions
        accessible_widgets = []
        for widget in widgets:
            if ComplianceDashboardManager._user_can_access_widget(user, widget):
                accessible_widgets.append(widget)
        
        # Generate widget data
        widget_data = {}
        for widget in accessible_widgets:
            widget_data[widget.widget_type] = ComplianceDashboardManager._generate_widget_data(widget)
        
        # Get active alerts
        active_alerts = ComplianceAlert.objects.filter(
            status__in=['active', 'acknowledged']
        ).order_by('-severity', '-created_at')[:20]
        
        # Get key metrics
        key_metrics = ComplianceMetric.objects.filter(
            is_active=True,
            category='overall_compliance'
        ).order_by('name')
        
        dashboard_data = {
            'user': user,
            'widgets': accessible_widgets,
            'widget_data': widget_data,
            'active_alerts': active_alerts,
            'key_metrics': key_metrics,
            'compliance_summary': ComplianceDashboardManager._generate_compliance_summary(),
            'recent_activity': ComplianceDashboardManager._get_recent_activity(),
            'dashboard_stats': ComplianceDashboardManager._get_dashboard_stats(),
        }
        
        return dashboard_data
    
    @staticmethod
    def calculate_all_metrics():
        """Calculate all active compliance metrics."""
        
        metrics = ComplianceMetric.objects.filter(is_active=True)
        
        for metric in metrics:
            try:
                new_value = ComplianceDashboardManager._calculate_metric_value(metric)
                metric.update_value(new_value)
                
                # Check for alert thresholds
                ComplianceDashboardManager._check_metric_alerts(metric)
                
            except Exception as e:
                logger.error(f"Failed to calculate metric {metric.name}: {e}")
        
        logger.info(f"Updated {metrics.count()} compliance metrics")
    
    @staticmethod
    def generate_compliance_alerts():
        """Generate compliance alerts based on system state."""
        
        alerts_generated = 0
        
        # Check for overdue data export requests
        overdue_exports = DataExportRequest.objects.filter(
            status='pending',
            expiry_date__lt=timezone.now()
        )
        
        if overdue_exports.exists():
            ComplianceDashboardManager._create_alert(
                alert_type='export_overdue',
                severity='high',
                title=f'{overdue_exports.count()} Data Export Requests Overdue',
                description=f'There are {overdue_exports.count()} data export requests that have exceeded their deadline.',
                affected_records=overdue_exports.count(),
                compliance_framework='gdpr',
                source_system='data_export'
            )
            alerts_generated += 1
        
        # Check for expired consents
        expired_consents = PatientConsent.objects.filter(
            status='given',
            expiry_date__lt=timezone.now()
        )
        
        if expired_consents.exists():
            ComplianceDashboardManager._create_alert(
                alert_type='consent_expired',
                severity='medium',
                title=f'{expired_consents.count()} Patient Consents Expired',
                description=f'There are {expired_consents.count()} patient consents that have expired and need renewal.',
                affected_records=expired_consents.count(),
                compliance_framework='gdpr',
                source_system='consent_management'
            )
            alerts_generated += 1
        
        # Check for overdue breach notifications
        overdue_breaches = BreachNotificationManager.check_overdue_notifications()
        
        if overdue_breaches:
            ComplianceDashboardManager._create_alert(
                alert_type='violation',
                severity='critical',
                title=f'{len(overdue_breaches)} Breach Notifications Overdue',
                description=f'There are {len(overdue_breaches)} data breach incidents with overdue notification requirements.',
                affected_records=len(overdue_breaches),
                compliance_framework='multiple',
                source_system='breach_notification'
            )
            alerts_generated += 1
        
        # Add more alert checks as needed
        
        logger.info(f"Generated {alerts_generated} compliance alerts")
        
        return alerts_generated
    
    @staticmethod
    def generate_compliance_report(start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        
        if not start_date:
            start_date = timezone.now() - timedelta(days=30)
        if not end_date:
            end_date = timezone.now()
        
        report = {
            'report_period': {
                'start_date': start_date,
                'end_date': end_date,
                'duration_days': (end_date - start_date).days
            },
            'generated_at': timezone.now(),
            'executive_summary': {},
            'detailed_metrics': {},
            'compliance_areas': {},
            'alerts_summary': {},
            'recommendations': []
        }
        
        # Executive Summary
        total_patients = User.objects.count()
        active_alerts = ComplianceAlert.objects.filter(status='active').count()
        resolved_alerts = ComplianceAlert.objects.filter(
            status='resolved',
            resolved_at__range=[start_date, end_date]
        ).count()
        
        report['executive_summary'] = {
            'total_patients': total_patients,
            'active_compliance_alerts': active_alerts,
            'alerts_resolved_in_period': resolved_alerts,
            'overall_compliance_score': ComplianceDashboardManager._calculate_overall_compliance_score(),
        }
        
        # Detailed Metrics by Category
        for category, category_name in ComplianceMetric.METRIC_CATEGORIES:
            metrics = ComplianceMetric.objects.filter(
                category=category,
                is_active=True
            )
            
            category_data = {
                'name': category_name,
                'metrics': {},
                'compliance_score': 0
            }
            
            for metric in metrics:
                category_data['metrics'][metric.name] = {
                    'current_value': float(metric.current_value),
                    'target_value': float(metric.target_value) if metric.target_value else None,
                    'trend': metric.trend_direction,
                    'meeting_target': metric.is_meeting_target(),
                    'variance_from_target': metric.get_variance_from_target()
                }
            
            report['detailed_metrics'][category] = category_data
        
        # Compliance Areas Analysis
        report['compliance_areas'] = {
            'consent_management': ConsentManager.generate_consent_report(),
            'data_export': DataExportManager.generate_compliance_report(),
            'search_privacy': PrivacySearchManager.generate_search_privacy_report(),
            'cookie_compliance': CookieManager.generate_cookie_compliance_report(),
            'breach_response': BreachNotificationManager.generate_breach_report(),
            'patient_privacy_settings': PatientPrivacyManager.generate_privacy_compliance_report(),
        }
        
        # Alerts Summary
        alert_counts = ComplianceAlert.objects.filter(
            created_at__range=[start_date, end_date]
        ).values('severity').annotate(count=Count('id'))
        
        report['alerts_summary'] = {
            'total_alerts': sum(item['count'] for item in alert_counts),
            'by_severity': {item['severity']: item['count'] for item in alert_counts},
            'resolution_rate': (resolved_alerts / sum(item['count'] for item in alert_counts) * 100) if alert_counts else 0,
            'average_resolution_time_hours': 0,  # Would calculate from alert timestamps
        }
        
        # Generate Recommendations
        report['recommendations'] = ComplianceDashboardManager._generate_compliance_recommendations(report)
        
        return report
    
    # Helper methods
    
    @staticmethod
    def _user_can_access_widget(user: User, widget: ComplianceDashboardWidget) -> bool:
        """Check if user can access a specific widget."""
        if not widget.required_permissions:
            return True
        
        # This would integrate with your permission system
        # For now, assume all authenticated users can access
        return user.is_authenticated
    
    @staticmethod
    def _generate_widget_data(widget: ComplianceDashboardWidget) -> Dict[str, Any]:
        """Generate data for a specific dashboard widget."""
        
        widget_data = {
            'widget': widget,
            'configuration': widget.configuration,
            'data': {},
            'last_updated': timezone.now()
        }
        
        if widget.widget_type == 'compliance_overview':
            widget_data['data'] = {
                'total_patients': User.objects.count(),
                'active_alerts': ComplianceAlert.objects.filter(status='active').count(),
                'compliance_score': ComplianceDashboardManager._calculate_overall_compliance_score(),
                'recent_incidents': DataBreachIncident.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).count()
            }
        
        elif widget.widget_type == 'consent_metrics':
            widget_data['data'] = ConsentManager.generate_consent_report()
        
        elif widget.widget_type == 'breach_incidents':
            widget_data['data'] = {
                'total_incidents': DataBreachIncident.objects.count(),
                'active_incidents': DataBreachIncident.objects.filter(
                    status__in=['reported', 'investigating', 'confirmed']
                ).count(),
                'recent_incidents': list(DataBreachIncident.objects.filter(
                    created_at__gte=timezone.now() - timedelta(days=30)
                ).values('incident_id', 'title', 'severity_level', 'status', 'created_at')[:5])
            }
        
        elif widget.widget_type == 'export_requests':
            widget_data['data'] = DataExportManager.generate_compliance_report()
        
        elif widget.widget_type == 'cookie_compliance':
            widget_data['data'] = CookieManager.generate_cookie_compliance_report()
        
        elif widget.widget_type == 'search_audit':
            widget_data['data'] = PrivacySearchManager.generate_search_privacy_report()
        
        elif widget.widget_type == 'patient_privacy_settings':
            widget_data['data'] = PatientPrivacyManager.generate_privacy_compliance_report()
        
        elif widget.widget_type == 'regulatory_deadlines':
            widget_data['data'] = ComplianceDashboardManager._get_upcoming_deadlines()
        
        # Add more widget types as needed
        
        return widget_data
    
    @staticmethod
    def _generate_compliance_summary() -> Dict[str, Any]:
        """Generate overall compliance summary."""
        
        return {
            'overall_score': ComplianceDashboardManager._calculate_overall_compliance_score(),
            'active_alerts': ComplianceAlert.objects.filter(status='active').count(),
            'overdue_alerts': ComplianceAlert.objects.filter(
                status='active',
                deadline__lt=timezone.now()
            ).count(),
            'compliance_trends': {
                'improving': ComplianceMetric.objects.filter(trend_direction='up').count(),
                'declining': ComplianceMetric.objects.filter(trend_direction='down').count(),
                'stable': ComplianceMetric.objects.filter(trend_direction='stable').count(),
            }
        }
    
    @staticmethod
    def _get_recent_activity() -> List[Dict[str, Any]]:
        """Get recent compliance-related activity."""
        
        activities = []
        
        # Recent alerts
        recent_alerts = ComplianceAlert.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:5]
        
        for alert in recent_alerts:
            activities.append({
                'type': 'alert',
                'title': f'Alert: {alert.title}',
                'description': alert.description,
                'severity': alert.severity,
                'timestamp': alert.created_at,
                'url': f'/admin/privacy/compliancealert/{alert.id}/'
            })
        
        # Recent breach incidents
        recent_breaches = DataBreachIncident.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:3]
        
        for breach in recent_breaches:
            activities.append({
                'type': 'breach',
                'title': f'Breach: {breach.title}',
                'description': breach.description,
                'severity': breach.severity_level,
                'timestamp': breach.created_at,
                'url': f'/admin/privacy/databreachincident/{breach.id}/'
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return activities[:10]
    
    @staticmethod
    def _get_dashboard_stats() -> Dict[str, Any]:
        """Get dashboard statistics."""
        
        return {
            'total_widgets': ComplianceDashboardWidget.objects.filter(is_active=True).count(),
            'total_metrics': ComplianceMetric.objects.filter(is_active=True).count(),
            'total_alerts': ComplianceAlert.objects.count(),
            'last_updated': timezone.now(),
        }
    
    @staticmethod
    def _calculate_metric_value(metric: ComplianceMetric) -> float:
        """Calculate the current value for a compliance metric."""
        
        # This is a simplified implementation
        # In practice, each metric would have its own calculation logic
        
        if metric.category == 'consent_management':
            if 'consent_compliance_rate' in metric.name.lower():
                total_patients = User.objects.count()
                patients_with_consent = PatientConsent.objects.filter(
                    status='given'
                ).values('patient').distinct().count()
                return (patients_with_consent / total_patients * 100) if total_patients > 0 else 0
        
        elif metric.category == 'data_export':
            if 'export_completion_rate' in metric.name.lower():
                total_requests = DataExportRequest.objects.count()
                completed_requests = DataExportRequest.objects.filter(status='completed').count()
                return (completed_requests / total_requests * 100) if total_requests > 0 else 0
        
        elif metric.category == 'breach_response':
            if 'notification_compliance_rate' in metric.name.lower():
                total_breaches = DataBreachIncident.objects.filter(is_confirmed_breach=True).count()
                compliant_breaches = DataBreachIncident.objects.filter(
                    is_confirmed_breach=True,
                    regulatory_notifications_sent=True
                ).count()
                return (compliant_breaches / total_breaches * 100) if total_breaches > 0 else 0
        
        # Default calculation
        return float(metric.current_value)
    
    @staticmethod
    def _check_metric_alerts(metric: ComplianceMetric):
        """Check if metric values trigger any alerts."""
        
        # Check if metric is below target threshold
        if metric.target_value and metric.current_value < metric.target_value:
            variance = metric.get_variance_from_target()
            
            if variance and variance < -20:  # More than 20% below target
                ComplianceDashboardManager._create_alert(
                    alert_type='threshold_exceeded',
                    severity='medium',
                    title=f'Metric Below Target: {metric.name}',
                    description=f'Metric {metric.name} is {abs(variance):.1f}% below target value.',
                    compliance_framework='internal',
                    source_system='compliance_dashboard',
                    alert_data={'metric_id': metric.id, 'variance': variance}
                )
    
    @staticmethod
    def _create_alert(
        alert_type: str,
        severity: str,
        title: str,
        description: str,
        compliance_framework: str,
        source_system: str,
        affected_records: int = 0,
        deadline: datetime = None,
        alert_data: Dict = None
    ) -> ComplianceAlert:
        """Create a new compliance alert."""
        
        # Check if similar alert already exists
        existing_alert = ComplianceAlert.objects.filter(
            alert_type=alert_type,
            title=title,
            status__in=['active', 'acknowledged']
        ).first()
        
        if existing_alert:
            # Update existing alert instead of creating duplicate
            existing_alert.description = description
            existing_alert.affected_records = affected_records
            existing_alert.alert_data = alert_data or {}
            existing_alert.save()
            return existing_alert
        
        # Create new alert
        alert = ComplianceAlert.objects.create(
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            compliance_framework=compliance_framework,
            source_system=source_system,
            affected_records=affected_records,
            deadline=deadline,
            alert_data=alert_data or {}
        )
        
        logger.info(f"Created compliance alert: {alert.alert_id}")
        
        return alert
    
    @staticmethod
    def _calculate_overall_compliance_score() -> float:
        """Calculate overall compliance score."""
        
        # This is a simplified implementation
        # In practice, this would be a weighted average of various compliance metrics
        
        metrics = ComplianceMetric.objects.filter(
            is_active=True,
            category='overall_compliance'
        )
        
        if not metrics.exists():
            return 85.0  # Default score
        
        total_score = sum(float(metric.current_value) for metric in metrics)
        return total_score / metrics.count()
    
    @staticmethod
    def _get_upcoming_deadlines() -> List[Dict[str, Any]]:
        """Get upcoming compliance deadlines."""
        
        deadlines = []
        
        # Data export request deadlines
        upcoming_exports = DataExportRequest.objects.filter(
            status='pending',
            expiry_date__gte=timezone.now(),
            expiry_date__lte=timezone.now() + timedelta(days=7)
        )
        
        for export_request in upcoming_exports:
            deadlines.append({
                'type': 'data_export',
                'title': f'Data Export Request: {export_request.request_id}',
                'deadline': export_request.expiry_date,
                'days_remaining': (export_request.expiry_date - timezone.now()).days,
                'priority': 'high' if (export_request.expiry_date - timezone.now()).days <= 2 else 'medium'
            })
        
        # Alert deadlines
        upcoming_alert_deadlines = ComplianceAlert.objects.filter(
            status__in=['active', 'acknowledged'],
            deadline__gte=timezone.now(),
            deadline__lte=timezone.now() + timedelta(days=7)
        )
        
        for alert in upcoming_alert_deadlines:
            deadlines.append({
                'type': 'alert_resolution',
                'title': f'Alert Resolution: {alert.title}',
                'deadline': alert.deadline,
                'days_remaining': (alert.deadline - timezone.now()).days,
                'priority': alert.severity
            })
        
        # Sort by deadline
        deadlines.sort(key=lambda x: x['deadline'])
        
        return deadlines[:10]
    
    @staticmethod
    def _generate_compliance_recommendations(report: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations based on report data."""
        
        recommendations = []
        
        # Check overall compliance score
        overall_score = report['executive_summary']['overall_compliance_score']
        if overall_score < 80:
            recommendations.append(
                "Overall compliance score is below 80%. Consider implementing additional privacy controls and staff training."
            )
        
        # Check active alerts
        active_alerts = report['executive_summary']['active_compliance_alerts']
        if active_alerts > 10:
            recommendations.append(
                f"There are {active_alerts} active compliance alerts. Prioritize resolving high-severity alerts to improve compliance posture."
            )
        
        # Check consent compliance
        consent_data = report['compliance_areas'].get('consent_management', {})
        consent_compliance = consent_data.get('compliance_summary', {}).get('essential_consent_compliance_rate', 0)
        if consent_compliance < 95:
            recommendations.append(
                "Essential consent compliance rate is below 95%. Review consent collection processes and implement automated reminders."
            )
        
        # Check breach response
        breach_data = report['compliance_areas'].get('breach_response', {})
        breach_compliance = breach_data.get('compliance_metrics', {}).get('approval_compliance_rate', 0)
        if breach_compliance < 100:
            recommendations.append(
                "Breach notification compliance is not at 100%. Review breach response procedures and ensure all incidents are properly documented."
            )
        
        # Add more recommendations based on specific metrics
        
        return recommendations