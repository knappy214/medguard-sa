# -*- coding: utf-8 -*-
"""
MedGuard SA - Patient-Controlled Privacy Settings Module

Implements comprehensive patient-controlled privacy settings that integrate with
Wagtail's user management system for healthcare compliance and patient empowerment.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet

from .wagtail_privacy import ConsentCategory, AnonymizationProfile

logger = logging.getLogger(__name__)
User = get_user_model()


@register_snippet
class PrivacySettingCategory(models.Model):
    """
    Categories of privacy settings that patients can control.
    
    Defines different aspects of privacy that patients can
    individually configure according to their preferences.
    """
    
    SETTING_TYPES = [
        ('data_sharing', _('Data Sharing')),
        ('communication_preferences', _('Communication Preferences')),
        ('marketing_consent', _('Marketing and Promotional Content')),
        ('research_participation', _('Medical Research Participation')),
        ('analytics_tracking', _('Analytics and Usage Tracking')),
        ('third_party_access', _('Third-Party Service Access')),
        ('emergency_access', _('Emergency Access Permissions')),
        ('family_access', _('Family Member Access')),
        ('provider_sharing', _('Healthcare Provider Sharing')),
        ('insurance_sharing', _('Insurance Provider Sharing')),
        ('appointment_reminders', _('Appointment Reminders')),
        ('health_alerts', _('Health Alerts and Notifications')),
        ('telemedicine', _('Telemedicine Services')),
        ('ai_analysis', _('AI-Powered Health Analysis')),
        ('data_retention', _('Data Retention Preferences')),
    ]
    
    CONTROL_TYPES = [
        ('toggle', _('On/Off Toggle')),
        ('choice', _('Multiple Choice')),
        ('level', _('Privacy Level (1-5)')),
        ('custom', _('Custom Configuration')),
        ('time_based', _('Time-Based Settings')),
        ('conditional', _('Conditional Settings')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Category Name"),
        help_text=_("Human-readable name for this privacy setting category")
    )
    
    setting_type = models.CharField(
        max_length=30,
        choices=SETTING_TYPES,
        unique=True,
        verbose_name=_("Setting Type"),
        help_text=_("Type of privacy setting")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of what this setting controls")
    )
    
    control_type = models.CharField(
        max_length=20,
        choices=CONTROL_TYPES,
        verbose_name=_("Control Type"),
        help_text=_("Type of user interface control for this setting")
    )
    
    default_value = models.JSONField(
        default=dict,
        verbose_name=_("Default Value"),
        help_text=_("Default value for this privacy setting")
    )
    
    available_options = models.JSONField(
        default=list,
        verbose_name=_("Available Options"),
        help_text=_("Available options for choice-based settings")
    )
    
    requires_consent = models.BooleanField(
        default=False,
        verbose_name=_("Requires Explicit Consent"),
        help_text=_("Whether changing this setting requires explicit consent")
    )
    
    consent_categories = models.ManyToManyField(
        ConsentCategory,
        blank=True,
        verbose_name=_("Related Consent Categories"),
        help_text=_("Consent categories affected by this setting")
    )
    
    affects_data_processing = models.BooleanField(
        default=True,
        verbose_name=_("Affects Data Processing"),
        help_text=_("Whether this setting affects how patient data is processed")
    )
    
    legal_basis = models.CharField(
        max_length=200,
        verbose_name=_("Legal Basis"),
        help_text=_("Legal basis for collecting this privacy preference")
    )
    
    patient_education_content = models.TextField(
        blank=True,
        verbose_name=_("Patient Education Content"),
        help_text=_("Educational content to help patients understand this setting")
    )
    
    priority = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Display Priority"),
        help_text=_("Priority for displaying this setting (lower = higher priority)")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('setting_type'),
            FieldPanel('description'),
        ], heading=_("Category Information")),
        
        MultiFieldPanel([
            FieldPanel('control_type'),
            FieldPanel('default_value'),
            FieldPanel('available_options'),
        ], heading=_("User Interface")),
        
        MultiFieldPanel([
            FieldPanel('requires_consent'),
            FieldPanel('consent_categories'),
            FieldPanel('affects_data_processing'),
            FieldPanel('legal_basis'),
        ], heading=_("Compliance Settings")),
        
        MultiFieldPanel([
            FieldPanel('patient_education_content'),
            FieldPanel('priority'),
            FieldPanel('is_active'),
        ], heading=_("Display Settings")),
    ]
    
    class Meta:
        verbose_name = _("Privacy Setting Category")
        verbose_name_plural = _("Privacy Setting Categories")
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_setting_type_display()})"
    
    def get_default_setting_value(self) -> Any:
        """Get the default value for this setting category."""
        if self.control_type == 'toggle':
            return self.default_value.get('enabled', False)
        elif self.control_type == 'choice':
            return self.default_value.get('selected_option', '')
        elif self.control_type == 'level':
            return self.default_value.get('level', 3)
        else:
            return self.default_value


class PatientPrivacySetting(models.Model):
    """
    Individual patient privacy settings with change tracking.
    
    Stores patient-specific privacy preferences with full
    audit trail and consent documentation.
    """
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Patient"),
        related_name='privacy_settings'
    )
    
    category = models.ForeignKey(
        PrivacySettingCategory,
        on_delete=models.CASCADE,
        verbose_name=_("Privacy Setting Category")
    )
    
    setting_value = models.JSONField(
        default=dict,
        verbose_name=_("Setting Value"),
        help_text=_("Current value of the privacy setting")
    )
    
    previous_value = models.JSONField(
        default=dict,
        verbose_name=_("Previous Value"),
        help_text=_("Previous value before last change")
    )
    
    is_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Is Enabled"),
        help_text=_("Whether this privacy setting is currently enabled")
    )
    
    consent_given = models.BooleanField(
        default=False,
        verbose_name=_("Consent Given"),
        help_text=_("Whether patient has given explicit consent for this setting")
    )
    
    consent_given_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Given At")
    )
    
    last_updated_by_patient = models.BooleanField(
        default=True,
        verbose_name=_("Last Updated by Patient"),
        help_text=_("Whether the last update was made by the patient themselves")
    )
    
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Updated By"),
        help_text=_("User who last updated this setting"),
        related_name='updated_privacy_settings'
    )
    
    update_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Update Reason"),
        help_text=_("Reason for the last update")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address when setting was last updated")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Browser information when setting was updated")
    )
    
    effective_from = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Effective From"),
        help_text=_("When this setting becomes effective")
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires At"),
        help_text=_("When this setting expires (if applicable)")
    )
    
    metadata = models.JSONField(
        default=dict,
        verbose_name=_("Metadata"),
        help_text=_("Additional metadata about this setting")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Patient Privacy Setting")
        verbose_name_plural = _("Patient Privacy Settings")
        unique_together = ['patient', 'category']
        ordering = ['category__priority', 'category__name']
    
    def __str__(self):
        return f"{self.patient} - {self.category.name} ({self.is_enabled})"
    
    def save(self, *args, **kwargs):
        """Override save to track changes and update consent."""
        # Track previous value if this is an update
        if self.pk:
            try:
                old_instance = PatientPrivacySetting.objects.get(pk=self.pk)
                if old_instance.setting_value != self.setting_value:
                    self.previous_value = old_instance.setting_value
            except PatientPrivacySetting.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def update_setting(
        self, 
        new_value: Any, 
        updated_by: User, 
        reason: str = "",
        ip_address: str = "",
        user_agent: str = "",
        consent_given: bool = None
    ):
        """Update the privacy setting with full audit trail."""
        
        # Store previous value
        self.previous_value = self.setting_value.copy() if isinstance(self.setting_value, dict) else self.setting_value
        
        # Update setting value
        if isinstance(new_value, dict):
            self.setting_value.update(new_value)
        else:
            self.setting_value = {'value': new_value}
        
        # Update metadata
        self.updated_by = updated_by
        self.last_updated_by_patient = (updated_by == self.patient)
        self.update_reason = reason
        self.ip_address = ip_address
        self.user_agent = user_agent
        
        # Handle consent
        if consent_given is not None:
            self.consent_given = consent_given
            if consent_given:
                self.consent_given_at = timezone.now()
        elif self.category.requires_consent and not self.consent_given:
            # Require consent for settings that need it
            self.consent_given = True
            self.consent_given_at = timezone.now()
        
        self.save()
        
        # Log the change
        PrivacySettingChangeLog.objects.create(
            patient=self.patient,
            setting=self,
            old_value=self.previous_value,
            new_value=self.setting_value,
            changed_by=updated_by,
            change_reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        logger.info(
            f"Privacy setting updated for patient {self.patient.id}: "
            f"{self.category.setting_type} = {self.setting_value}"
        )
    
    def is_effective(self) -> bool:
        """Check if this setting is currently effective."""
        now = timezone.now()
        
        if now < self.effective_from:
            return False
        
        if self.expires_at and now > self.expires_at:
            return False
        
        return self.is_enabled
    
    def get_display_value(self) -> str:
        """Get human-readable display value for this setting."""
        if self.category.control_type == 'toggle':
            return _("Enabled") if self.is_enabled else _("Disabled")
        elif self.category.control_type == 'choice':
            selected = self.setting_value.get('value', '')
            for option in self.category.available_options:
                if option.get('value') == selected:
                    return option.get('label', selected)
            return selected
        elif self.category.control_type == 'level':
            level = self.setting_value.get('value', 3)
            return f"{_('Level')} {level}/5"
        else:
            return str(self.setting_value.get('value', ''))


class PrivacySettingChangeLog(models.Model):
    """
    Audit log for privacy setting changes.
    
    Tracks all changes to patient privacy settings for
    compliance and audit purposes.
    """
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Patient"),
        related_name='privacy_setting_changes'
    )
    
    setting = models.ForeignKey(
        PatientPrivacySetting,
        on_delete=models.CASCADE,
        verbose_name=_("Privacy Setting"),
        related_name='change_logs'
    )
    
    old_value = models.JSONField(
        default=dict,
        verbose_name=_("Old Value")
    )
    
    new_value = models.JSONField(
        default=dict,
        verbose_name=_("New Value")
    )
    
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Changed By"),
        related_name='privacy_changes_made'
    )
    
    change_reason = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Change Reason")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent")
    )
    
    session_id = models.CharField(
        max_length=40,
        blank=True,
        verbose_name=_("Session ID")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Privacy Setting Change Log")
        verbose_name_plural = _("Privacy Setting Change Logs")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient} - {self.setting.category.name} changed at {self.created_at}"


class PrivacyDashboardWidget(models.Model):
    """
    Configurable widgets for the patient privacy dashboard.
    
    Allows customization of the privacy dashboard interface
    to show relevant information and controls to patients.
    """
    
    WIDGET_TYPES = [
        ('privacy_overview', _('Privacy Settings Overview')),
        ('consent_status', _('Consent Status Summary')),
        ('data_usage', _('Data Usage Statistics')),
        ('sharing_permissions', _('Data Sharing Permissions')),
        ('recent_access', _('Recent Data Access Log')),
        ('privacy_alerts', _('Privacy Alerts and Notifications')),
        ('export_requests', _('Data Export Requests')),
        ('deletion_requests', _('Data Deletion Requests')),
        ('cookie_preferences', _('Cookie Preferences')),
        ('communication_settings', _('Communication Preferences')),
        ('security_settings', _('Security Settings')),
        ('educational_content', _('Privacy Education Content')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Widget Name")
    )
    
    widget_type = models.CharField(
        max_length=30,
        choices=WIDGET_TYPES,
        verbose_name=_("Widget Type")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of what this widget displays")
    )
    
    configuration = models.JSONField(
        default=dict,
        verbose_name=_("Widget Configuration"),
        help_text=_("Configuration options for this widget")
    )
    
    display_order = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Display Order"),
        help_text=_("Order in which widget appears on dashboard")
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Default Widget"),
        help_text=_("Whether this widget is shown by default")
    )
    
    requires_consent = models.BooleanField(
        default=False,
        verbose_name=_("Requires Consent"),
        help_text=_("Whether displaying this widget requires patient consent")
    )
    
    patient_configurable = models.BooleanField(
        default=True,
        verbose_name=_("Patient Configurable"),
        help_text=_("Whether patients can show/hide this widget")
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
            FieldPanel('display_order'),
        ], heading=_("Configuration")),
        
        MultiFieldPanel([
            FieldPanel('is_default'),
            FieldPanel('requires_consent'),
            FieldPanel('patient_configurable'),
            FieldPanel('is_active'),
        ], heading=_("Display Settings")),
    ]
    
    class Meta:
        verbose_name = _("Privacy Dashboard Widget")
        verbose_name_plural = _("Privacy Dashboard Widgets")
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_widget_type_display()})"


class PatientDashboardPreference(models.Model):
    """
    Patient-specific dashboard preferences and widget configurations.
    
    Stores individual patient preferences for their privacy
    dashboard layout and widget visibility.
    """
    
    patient = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Patient"),
        related_name='dashboard_preferences'
    )
    
    visible_widgets = models.ManyToManyField(
        PrivacyDashboardWidget,
        verbose_name=_("Visible Widgets"),
        help_text=_("Widgets visible on patient's dashboard")
    )
    
    widget_order = models.JSONField(
        default=list,
        verbose_name=_("Widget Order"),
        help_text=_("Custom order of widgets on dashboard")
    )
    
    dashboard_theme = models.CharField(
        max_length=20,
        choices=[
            ('light', _('Light Theme')),
            ('dark', _('Dark Theme')),
            ('high_contrast', _('High Contrast')),
            ('large_text', _('Large Text')),
        ],
        default='light',
        verbose_name=_("Dashboard Theme")
    )
    
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Notifications Enabled"),
        help_text=_("Whether to show privacy notifications on dashboard")
    )
    
    show_privacy_tips = models.BooleanField(
        default=True,
        verbose_name=_("Show Privacy Tips"),
        help_text=_("Whether to show educational privacy tips")
    )
    
    language_preference = models.CharField(
        max_length=10,
        choices=[
            ('en', _('English')),
            ('af', _('Afrikaans')),
        ],
        default='en',
        verbose_name=_("Language Preference")
    )
    
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Accessed"),
        help_text=_("When patient last accessed their privacy dashboard")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Patient Dashboard Preference")
        verbose_name_plural = _("Patient Dashboard Preferences")
    
    def __str__(self):
        return f"{self.patient} - Dashboard Preferences"
    
    def get_visible_widgets_ordered(self) -> List[PrivacyDashboardWidget]:
        """Get visible widgets in the patient's preferred order."""
        widgets = list(self.visible_widgets.filter(is_active=True))
        
        if self.widget_order:
            # Sort widgets according to patient's custom order
            widget_dict = {w.id: w for w in widgets}
            ordered_widgets = []
            
            for widget_id in self.widget_order:
                if widget_id in widget_dict:
                    ordered_widgets.append(widget_dict[widget_id])
            
            # Add any remaining widgets that aren't in the custom order
            for widget in widgets:
                if widget not in ordered_widgets:
                    ordered_widgets.append(widget)
            
            return ordered_widgets
        else:
            # Use default order
            return sorted(widgets, key=lambda w: w.display_order)
    
    def update_last_accessed(self):
        """Update the last accessed timestamp."""
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])


class PatientPrivacyManager:
    """
    Manager for patient-controlled privacy settings and dashboard.
    
    Provides high-level methods for managing patient privacy
    preferences and generating privacy dashboards.
    """
    
    @staticmethod
    def initialize_patient_privacy_settings(patient: User) -> List[PatientPrivacySetting]:
        """Initialize default privacy settings for a new patient."""
        
        settings_created = []
        
        for category in PrivacySettingCategory.objects.filter(is_active=True):
            setting, created = PatientPrivacySetting.objects.get_or_create(
                patient=patient,
                category=category,
                defaults={
                    'setting_value': category.get_default_setting_value(),
                    'is_enabled': True,
                    'updated_by': patient,
                    'last_updated_by_patient': True
                }
            )
            
            if created:
                settings_created.append(setting)
        
        logger.info(f"Initialized {len(settings_created)} privacy settings for patient {patient.id}")
        
        return settings_created
    
    @staticmethod
    def get_patient_privacy_dashboard_data(patient: User) -> Dict[str, Any]:
        """Get comprehensive privacy dashboard data for a patient."""
        
        # Ensure patient has privacy settings initialized
        PatientPrivacyManager.initialize_patient_privacy_settings(patient)
        
        # Get or create dashboard preferences
        dashboard_prefs, created = PatientDashboardPreference.objects.get_or_create(
            patient=patient,
            defaults={
                'dashboard_theme': 'light',
                'notifications_enabled': True,
                'show_privacy_tips': True,
                'language_preference': 'en'
            }
        )
        
        if created:
            # Set default visible widgets
            default_widgets = PrivacyDashboardWidget.objects.filter(
                is_active=True,
                is_default=True
            )
            dashboard_prefs.visible_widgets.set(default_widgets)
        
        # Update last accessed
        dashboard_prefs.update_last_accessed()
        
        # Get privacy settings
        privacy_settings = PatientPrivacySetting.objects.filter(
            patient=patient,
            category__is_active=True
        ).select_related('category')
        
        # Get visible widgets
        visible_widgets = dashboard_prefs.get_visible_widgets_ordered()
        
        # Generate widget data
        widget_data = {}
        for widget in visible_widgets:
            widget_data[widget.widget_type] = PatientPrivacyManager._generate_widget_data(
                widget, patient
            )
        
        # Get recent privacy activity
        recent_changes = PrivacySettingChangeLog.objects.filter(
            patient=patient
        ).order_by('-created_at')[:10]
        
        dashboard_data = {
            'patient': patient,
            'dashboard_preferences': dashboard_prefs,
            'privacy_settings': {
                setting.category.setting_type: setting 
                for setting in privacy_settings
            },
            'visible_widgets': visible_widgets,
            'widget_data': widget_data,
            'recent_changes': recent_changes,
            'privacy_summary': PatientPrivacyManager._generate_privacy_summary(patient),
            'compliance_status': PatientPrivacyManager._check_compliance_status(patient),
        }
        
        return dashboard_data
    
    @staticmethod
    def update_patient_setting(
        patient: User,
        setting_type: str,
        new_value: Any,
        updated_by: User = None,
        reason: str = "",
        ip_address: str = "",
        user_agent: str = ""
    ) -> PatientPrivacySetting:
        """Update a specific patient privacy setting."""
        
        try:
            category = PrivacySettingCategory.objects.get(
                setting_type=setting_type,
                is_active=True
            )
        except PrivacySettingCategory.DoesNotExist:
            raise ValueError(f"Invalid privacy setting type: {setting_type}")
        
        # Get or create the setting
        setting, created = PatientPrivacySetting.objects.get_or_create(
            patient=patient,
            category=category,
            defaults={
                'setting_value': category.get_default_setting_value(),
                'updated_by': updated_by or patient
            }
        )
        
        # Update the setting
        setting.update_setting(
            new_value=new_value,
            updated_by=updated_by or patient,
            reason=reason,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return setting
    
    @staticmethod
    def get_patient_privacy_export(patient: User) -> Dict[str, Any]:
        """Generate a complete privacy settings export for a patient."""
        
        privacy_settings = PatientPrivacySetting.objects.filter(
            patient=patient
        ).select_related('category')
        
        export_data = {
            'patient_id': patient.id,
            'export_generated_at': timezone.now().isoformat(),
            'privacy_settings': {},
            'dashboard_preferences': {},
            'change_history': []
        }
        
        # Export privacy settings
        for setting in privacy_settings:
            export_data['privacy_settings'][setting.category.setting_type] = {
                'category_name': setting.category.name,
                'current_value': setting.setting_value,
                'is_enabled': setting.is_enabled,
                'consent_given': setting.consent_given,
                'consent_given_at': setting.consent_given_at.isoformat() if setting.consent_given_at else None,
                'last_updated': setting.updated_at.isoformat(),
                'updated_by_patient': setting.last_updated_by_patient,
            }
        
        # Export dashboard preferences
        try:
            dashboard_prefs = PatientDashboardPreference.objects.get(patient=patient)
            export_data['dashboard_preferences'] = {
                'theme': dashboard_prefs.dashboard_theme,
                'notifications_enabled': dashboard_prefs.notifications_enabled,
                'show_privacy_tips': dashboard_prefs.show_privacy_tips,
                'language_preference': dashboard_prefs.language_preference,
                'last_accessed': dashboard_prefs.last_accessed.isoformat() if dashboard_prefs.last_accessed else None,
            }
        except PatientDashboardPreference.DoesNotExist:
            pass
        
        # Export change history (last 100 changes)
        recent_changes = PrivacySettingChangeLog.objects.filter(
            patient=patient
        ).order_by('-created_at')[:100]
        
        for change in recent_changes:
            export_data['change_history'].append({
                'setting_type': change.setting.category.setting_type,
                'old_value': change.old_value,
                'new_value': change.new_value,
                'changed_at': change.created_at.isoformat(),
                'changed_by_patient': (change.changed_by == patient),
                'change_reason': change.change_reason,
            })
        
        return export_data
    
    @staticmethod
    def generate_privacy_compliance_report() -> Dict[str, Any]:
        """Generate privacy settings compliance report."""
        
        total_patients = User.objects.count()
        patients_with_settings = PatientPrivacySetting.objects.values('patient').distinct().count()
        
        report = {
            'generated_at': timezone.now(),
            'total_patients': total_patients,
            'patients_with_privacy_settings': patients_with_settings,
            'settings_adoption_rate': (patients_with_settings / total_patients * 100) if total_patients > 0 else 0,
            'setting_category_usage': {},
            'dashboard_usage': {},
            'compliance_metrics': {}
        }
        
        # Setting category usage
        for category in PrivacySettingCategory.objects.filter(is_active=True):
            settings_count = PatientPrivacySetting.objects.filter(category=category).count()
            enabled_count = PatientPrivacySetting.objects.filter(
                category=category,
                is_enabled=True
            ).count()
            
            report['setting_category_usage'][category.setting_type] = {
                'name': category.name,
                'total_settings': settings_count,
                'enabled_settings': enabled_count,
                'adoption_rate': (settings_count / total_patients * 100) if total_patients > 0 else 0,
                'enable_rate': (enabled_count / settings_count * 100) if settings_count > 0 else 0,
            }
        
        # Dashboard usage
        dashboard_users = PatientDashboardPreference.objects.count()
        active_users_30_days = PatientDashboardPreference.objects.filter(
            last_accessed__gte=timezone.now() - timedelta(days=30)
        ).count()
        
        report['dashboard_usage'] = {
            'total_dashboard_users': dashboard_users,
            'dashboard_adoption_rate': (dashboard_users / total_patients * 100) if total_patients > 0 else 0,
            'active_users_last_30_days': active_users_30_days,
            'dashboard_engagement_rate': (active_users_30_days / dashboard_users * 100) if dashboard_users > 0 else 0,
        }
        
        # Compliance metrics
        total_changes = PrivacySettingChangeLog.objects.count()
        patient_initiated_changes = PrivacySettingChangeLog.objects.filter(
            changed_by_id=models.F('patient_id')
        ).count()
        
        report['compliance_metrics'] = {
            'total_privacy_changes': total_changes,
            'patient_initiated_changes': patient_initiated_changes,
            'patient_control_rate': (patient_initiated_changes / total_changes * 100) if total_changes > 0 else 0,
            'changes_last_30_days': PrivacySettingChangeLog.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }
        
        return report
    
    # Helper methods
    
    @staticmethod
    def _generate_widget_data(widget: PrivacyDashboardWidget, patient: User) -> Dict[str, Any]:
        """Generate data for a specific dashboard widget."""
        
        widget_data = {
            'widget': widget,
            'configuration': widget.configuration,
            'data': {}
        }
        
        if widget.widget_type == 'privacy_overview':
            settings = PatientPrivacySetting.objects.filter(patient=patient)
            widget_data['data'] = {
                'total_settings': settings.count(),
                'enabled_settings': settings.filter(is_enabled=True).count(),
                'settings_with_consent': settings.filter(consent_given=True).count(),
            }
        
        elif widget.widget_type == 'recent_access':
            # This would integrate with your access logging system
            widget_data['data'] = {
                'recent_accesses': [],  # Would populate with actual access logs
                'access_count_today': 0,
            }
        
        elif widget.widget_type == 'privacy_alerts':
            # Generate privacy alerts for the patient
            widget_data['data'] = {
                'alerts': PatientPrivacyManager._get_privacy_alerts(patient),
                'alert_count': 0,
            }
        
        # Add more widget types as needed
        
        return widget_data
    
    @staticmethod
    def _generate_privacy_summary(patient: User) -> Dict[str, Any]:
        """Generate privacy summary for a patient."""
        
        settings = PatientPrivacySetting.objects.filter(patient=patient)
        
        return {
            'total_settings': settings.count(),
            'enabled_settings': settings.filter(is_enabled=True).count(),
            'settings_with_consent': settings.filter(consent_given=True).count(),
            'last_updated': settings.order_by('-updated_at').first().updated_at if settings.exists() else None,
        }
    
    @staticmethod
    def _check_compliance_status(patient: User) -> Dict[str, Any]:
        """Check compliance status for a patient's privacy settings."""
        
        compliance_status = {
            'overall_compliant': True,
            'issues': [],
            'recommendations': []
        }
        
        # Check if all required consents are given
        required_consent_categories = PrivacySettingCategory.objects.filter(
            is_active=True,
            requires_consent=True
        )
        
        for category in required_consent_categories:
            try:
                setting = PatientPrivacySetting.objects.get(
                    patient=patient,
                    category=category
                )
                if not setting.consent_given:
                    compliance_status['overall_compliant'] = False
                    compliance_status['issues'].append(
                        f"Missing consent for {category.name}"
                    )
            except PatientPrivacySetting.DoesNotExist:
                compliance_status['overall_compliant'] = False
                compliance_status['issues'].append(
                    f"No setting configured for {category.name}"
                )
        
        return compliance_status
    
    @staticmethod
    def _get_privacy_alerts(patient: User) -> List[Dict[str, Any]]:
        """Get privacy alerts for a patient."""
        alerts = []
        
        # Check for expired consents
        expired_settings = PatientPrivacySetting.objects.filter(
            patient=patient,
            expires_at__lt=timezone.now(),
            is_enabled=True
        )
        
        for setting in expired_settings:
            alerts.append({
                'type': 'warning',
                'title': f'{setting.category.name} setting has expired',
                'message': 'Please review and update your privacy preferences.',
                'action_url': '/privacy/settings/',
                'created_at': timezone.now()
            })
        
        return alerts