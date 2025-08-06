# -*- coding: utf-8 -*-
"""
MedGuard SA - Enhanced Cookie Management Module

Implements healthcare-compliant cookie management with enhanced privacy controls,
consent management, and audit trails for GDPR and POPIA compliance.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.middleware.csrf import get_token

from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet

logger = logging.getLogger(__name__)
User = get_user_model()


@register_snippet
class CookieCategory(models.Model):
    """
    Categories of cookies with different privacy and compliance requirements.
    
    Defines cookie categories that users can control individually,
    supporting healthcare compliance and privacy regulations.
    """
    
    COOKIE_TYPES = [
        ('essential', _('Essential/Strictly Necessary')),
        ('functional', _('Functional')),
        ('analytics', _('Analytics and Performance')),
        ('marketing', _('Marketing and Advertising')),
        ('personalization', _('Personalization')),
        ('social_media', _('Social Media')),
        ('security', _('Security and Fraud Prevention')),
        ('medical_tracking', _('Medical Data Tracking')),
        ('research', _('Medical Research')),
        ('third_party', _('Third-Party Services')),
    ]
    
    COMPLIANCE_LEVELS = [
        ('required', _('Required (Cannot be disabled)')),
        ('opt_out', _('Opt-out (Enabled by default)')),
        ('opt_in', _('Opt-in (Disabled by default)')),
        ('explicit_consent', _('Explicit Consent Required')),
        ('medical_consent', _('Medical Data Consent Required')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Category Name"),
        help_text=_("Human-readable name for this cookie category")
    )
    
    cookie_type = models.CharField(
        max_length=30,
        choices=COOKIE_TYPES,
        unique=True,
        verbose_name=_("Cookie Type"),
        help_text=_("Type of cookies in this category")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of what these cookies do")
    )
    
    purpose = models.TextField(
        verbose_name=_("Purpose"),
        help_text=_("Legal purpose for using these cookies")
    )
    
    compliance_level = models.CharField(
        max_length=20,
        choices=COMPLIANCE_LEVELS,
        verbose_name=_("Compliance Level"),
        help_text=_("Level of consent required for this category")
    )
    
    retention_period_days = models.PositiveIntegerField(
        verbose_name=_("Retention Period (Days)"),
        help_text=_("How long cookies in this category are retained")
    )
    
    legal_basis = models.CharField(
        max_length=200,
        verbose_name=_("Legal Basis"),
        help_text=_("Legal basis for processing under GDPR/POPIA")
    )
    
    data_processor = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Data Processor"),
        help_text=_("Third-party processor of cookie data (if applicable)")
    )
    
    privacy_policy_section = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Privacy Policy Section"),
        help_text=_("Section in privacy policy covering these cookies")
    )
    
    is_healthcare_related = models.BooleanField(
        default=False,
        verbose_name=_("Healthcare Related"),
        help_text=_("Whether these cookies handle healthcare data")
    )
    
    requires_medical_consent = models.BooleanField(
        default=False,
        verbose_name=_("Requires Medical Consent"),
        help_text=_("Whether medical data consent is required")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('cookie_type'),
            FieldPanel('description'),
        ], heading=_("Category Information")),
        
        MultiFieldPanel([
            FieldPanel('purpose'),
            FieldPanel('compliance_level'),
            FieldPanel('legal_basis'),
        ], heading=_("Legal Compliance")),
        
        MultiFieldPanel([
            FieldPanel('retention_period_days'),
            FieldPanel('data_processor'),
            FieldPanel('privacy_policy_section'),
        ], heading=_("Data Processing")),
        
        MultiFieldPanel([
            FieldPanel('is_healthcare_related'),
            FieldPanel('requires_medical_consent'),
            FieldPanel('is_active'),
        ], heading=_("Healthcare Compliance")),
    ]
    
    class Meta:
        verbose_name = _("Cookie Category")
        verbose_name_plural = _("Cookie Categories")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_cookie_type_display()})"
    
    def clean(self):
        """Validate cookie category settings."""
        super().clean()
        
        if self.retention_period_days < 1:
            raise ValidationError(_("Retention period must be at least 1 day"))
        
        if self.requires_medical_consent and not self.is_healthcare_related:
            raise ValidationError(_("Medical consent can only be required for healthcare-related cookies"))


@register_snippet
class CookieDefinition(models.Model):
    """
    Individual cookie definitions with detailed metadata.
    
    Defines specific cookies, their purposes, and compliance requirements
    for transparent cookie management.
    """
    
    COOKIE_SCOPES = [
        ('session', _('Session Cookie')),
        ('persistent', _('Persistent Cookie')),
        ('secure', _('Secure Cookie')),
        ('httponly', _('HTTP Only Cookie')),
        ('samesite_strict', _('SameSite Strict')),
        ('samesite_lax', _('SameSite Lax')),
        ('samesite_none', _('SameSite None')),
    ]
    
    name = models.CharField(
        max_length=100,
        verbose_name=_("Cookie Name"),
        help_text=_("Technical name of the cookie")
    )
    
    category = models.ForeignKey(
        CookieCategory,
        on_delete=models.CASCADE,
        verbose_name=_("Category"),
        help_text=_("Category this cookie belongs to")
    )
    
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("What this cookie does and why it's needed")
    )
    
    domain = models.CharField(
        max_length=200,
        verbose_name=_("Domain"),
        help_text=_("Domain where this cookie is set")
    )
    
    path = models.CharField(
        max_length=200,
        default='/',
        verbose_name=_("Path"),
        help_text=_("Path where this cookie is active")
    )
    
    scope = models.CharField(
        max_length=20,
        choices=COOKIE_SCOPES,
        verbose_name=_("Cookie Scope"),
        help_text=_("Security and scope settings for this cookie")
    )
    
    expiry_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Expiry (Days)"),
        help_text=_("How many days until cookie expires (null for session)")
    )
    
    data_collected = models.TextField(
        verbose_name=_("Data Collected"),
        help_text=_("What data this cookie collects or stores")
    )
    
    third_party_service = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Third-Party Service"),
        help_text=_("Third-party service that sets this cookie")
    )
    
    privacy_policy_url = models.URLField(
        blank=True,
        verbose_name=_("Privacy Policy URL"),
        help_text=_("URL to third-party privacy policy")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('category'),
            FieldPanel('description'),
        ], heading=_("Cookie Information")),
        
        MultiFieldPanel([
            FieldPanel('domain'),
            FieldPanel('path'),
            FieldPanel('scope'),
            FieldPanel('expiry_days'),
        ], heading=_("Technical Settings")),
        
        MultiFieldPanel([
            FieldPanel('data_collected'),
            FieldPanel('third_party_service'),
            FieldPanel('privacy_policy_url'),
        ], heading=_("Data Processing")),
        
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = _("Cookie Definition")
        verbose_name_plural = _("Cookie Definitions")
        unique_together = ['name', 'domain']
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.domain})"


class UserCookiePreference(models.Model):
    """
    Individual user cookie preferences with consent tracking.
    
    Tracks user consent for different cookie categories with
    full audit trail and compliance documentation.
    """
    
    CONSENT_STATUS = [
        ('granted', _('Consent Granted')),
        ('denied', _('Consent Denied')),
        ('withdrawn', _('Consent Withdrawn')),
        ('expired', _('Consent Expired')),
        ('pending', _('Consent Pending')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("User"),
        help_text=_("User (null for anonymous users)"),
        related_name='cookie_preferences'
    )
    
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name=_("Session Key"),
        help_text=_("Session key for anonymous users")
    )
    
    category = models.ForeignKey(
        CookieCategory,
        on_delete=models.CASCADE,
        verbose_name=_("Cookie Category"),
        help_text=_("Cookie category this preference applies to")
    )
    
    consent_status = models.CharField(
        max_length=20,
        choices=CONSENT_STATUS,
        default='pending',
        verbose_name=_("Consent Status")
    )
    
    granted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Granted At")
    )
    
    withdrawn_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Withdrawn At")
    )
    
    expiry_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Consent Expiry Date")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address when consent was given")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Browser information when consent was given")
    )
    
    consent_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Consent Method"),
        help_text=_("How consent was obtained (banner, settings, etc.)")
    )
    
    consent_evidence = models.JSONField(
        default=dict,
        verbose_name=_("Consent Evidence"),
        help_text=_("Additional evidence of consent")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("User Cookie Preference")
        verbose_name_plural = _("User Cookie Preferences")
        unique_together = [
            ['user', 'category'],
            ['session_key', 'category']
        ]
        ordering = ['-updated_at']
    
    def __str__(self):
        identifier = self.user.username if self.user else f"Session {self.session_key}"
        return f"{identifier} - {self.category.name} ({self.consent_status})"
    
    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if self.consent_status != 'granted':
            return False
        
        if self.expiry_date and timezone.now() > self.expiry_date:
            # Auto-expire consent
            self.consent_status = 'expired'
            self.save(update_fields=['consent_status'])
            return False
        
        return True
    
    def grant_consent(self, method: str = "banner", evidence: Dict = None):
        """Grant consent for this cookie category."""
        self.consent_status = 'granted'
        self.granted_at = timezone.now()
        self.consent_method = method
        self.withdrawn_at = None
        
        if evidence:
            self.consent_evidence.update(evidence)
        
        # Set expiry based on category retention period
        if self.category.retention_period_days:
            self.expiry_date = timezone.now() + timedelta(
                days=self.category.retention_period_days
            )
        
        self.save()
        
        logger.info(
            f"Cookie consent granted for category {self.category.cookie_type} "
            f"by {'user ' + str(self.user.id) if self.user else 'session ' + self.session_key}"
        )
    
    def withdraw_consent(self, reason: str = ""):
        """Withdraw consent for this cookie category."""
        self.consent_status = 'withdrawn'
        self.withdrawn_at = timezone.now()
        
        if reason:
            self.consent_evidence['withdrawal_reason'] = reason
        
        self.save()
        
        logger.info(
            f"Cookie consent withdrawn for category {self.category.cookie_type} "
            f"by {'user ' + str(self.user.id) if self.user else 'session ' + self.session_key}"
        )


class CookieAuditLog(models.Model):
    """
    Audit log for cookie-related activities.
    
    Tracks cookie setting, consent changes, and compliance activities
    for regulatory audit purposes.
    """
    
    ACTION_TYPES = [
        ('cookie_set', _('Cookie Set')),
        ('cookie_read', _('Cookie Read')),
        ('cookie_deleted', _('Cookie Deleted')),
        ('consent_granted', _('Consent Granted')),
        ('consent_withdrawn', _('Consent Withdrawn')),
        ('consent_expired', _('Consent Expired')),
        ('banner_shown', _('Cookie Banner Shown')),
        ('preferences_updated', _('Preferences Updated')),
        ('compliance_check', _('Compliance Check')),
    ]
    
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPES,
        verbose_name=_("Action Type")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
        related_name='cookie_audit_logs'
    )
    
    session_key = models.CharField(
        max_length=40,
        null=True,
        blank=True,
        verbose_name=_("Session Key")
    )
    
    cookie_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Cookie Name")
    )
    
    cookie_category = models.ForeignKey(
        CookieCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Cookie Category")
    )
    
    action_details = models.JSONField(
        default=dict,
        verbose_name=_("Action Details"),
        help_text=_("Additional details about the action")
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
    
    request_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Request Path")
    )
    
    compliance_status = models.CharField(
        max_length=20,
        choices=[
            ('compliant', _('Compliant')),
            ('non_compliant', _('Non-Compliant')),
            ('warning', _('Warning')),
            ('unknown', _('Unknown')),
        ],
        default='unknown',
        verbose_name=_("Compliance Status")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Cookie Audit Log")
        verbose_name_plural = _("Cookie Audit Logs")
        ordering = ['-created_at']
    
    def __str__(self):
        identifier = self.user.username if self.user else f"Session {self.session_key}"
        return f"{self.get_action_type_display()} - {identifier} ({self.created_at})"


class CookieConsentMiddleware:
    """
    Middleware for managing cookie consent and compliance.
    
    Intercepts requests to check and enforce cookie consent
    requirements for healthcare compliance.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Process request before view
        self.process_request(request)
        
        # Get response from view
        response = self.get_response(request)
        
        # Process response after view
        self.process_response(request, response)
        
        return response
    
    def process_request(self, request):
        """Process incoming request for cookie compliance."""
        # Add cookie consent status to request
        request.cookie_consent = self.get_user_cookie_consent(request)
        
        # Log cookie reads if any cookies are present
        if request.COOKIES:
            self.log_cookie_reads(request)
    
    def process_response(self, request, response):
        """Process outgoing response for cookie compliance."""
        # Check if response sets any cookies
        if hasattr(response, 'cookies') and response.cookies:
            self.validate_cookie_consent(request, response)
        
        # Add consent banner if needed
        if self.should_show_consent_banner(request):
            self.inject_consent_banner(request, response)
        
        return response
    
    def get_user_cookie_consent(self, request) -> Dict[str, bool]:
        """Get user's cookie consent status for all categories."""
        consent_status = {}
        
        user = getattr(request, 'user', None) if hasattr(request, 'user') else None
        session_key = request.session.session_key if hasattr(request, 'session') else None
        
        for category in CookieCategory.objects.filter(is_active=True):
            try:
                if user and user.is_authenticated:
                    preference = UserCookiePreference.objects.get(
                        user=user,
                        category=category
                    )
                elif session_key:
                    preference = UserCookiePreference.objects.get(
                        session_key=session_key,
                        category=category
                    )
                else:
                    # No user or session, check if category is required
                    consent_status[category.cookie_type] = (
                        category.compliance_level == 'required'
                    )
                    continue
                
                consent_status[category.cookie_type] = preference.is_valid()
                
            except UserCookiePreference.DoesNotExist:
                # No preference set, use default based on compliance level
                if category.compliance_level == 'required':
                    consent_status[category.cookie_type] = True
                elif category.compliance_level == 'opt_out':
                    consent_status[category.cookie_type] = True
                else:
                    consent_status[category.cookie_type] = False
        
        return consent_status
    
    def log_cookie_reads(self, request):
        """Log cookie read activities for audit purposes."""
        user = getattr(request, 'user', None) if hasattr(request, 'user') else None
        session_key = request.session.session_key if hasattr(request, 'session') else None
        
        for cookie_name, cookie_value in request.COOKIES.items():
            # Find cookie definition
            try:
                cookie_def = CookieDefinition.objects.get(
                    name=cookie_name,
                    domain=request.get_host()
                )
                
                CookieAuditLog.objects.create(
                    action_type='cookie_read',
                    user=user,
                    session_key=session_key,
                    cookie_name=cookie_name,
                    cookie_category=cookie_def.category,
                    action_details={
                        'cookie_value_length': len(str(cookie_value)),
                        'has_consent': request.cookie_consent.get(
                            cookie_def.category.cookie_type, False
                        )
                    },
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    compliance_status='compliant' if request.cookie_consent.get(
                        cookie_def.category.cookie_type, False
                    ) else 'non_compliant'
                )
                
            except CookieDefinition.DoesNotExist:
                # Unknown cookie
                CookieAuditLog.objects.create(
                    action_type='cookie_read',
                    user=user,
                    session_key=session_key,
                    cookie_name=cookie_name,
                    action_details={
                        'cookie_value_length': len(str(cookie_value)),
                        'unknown_cookie': True
                    },
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    compliance_status='warning'
                )
    
    def validate_cookie_consent(self, request, response):
        """Validate that response cookies have proper consent."""
        user = getattr(request, 'user', None) if hasattr(request, 'user') else None
        session_key = request.session.session_key if hasattr(request, 'session') else None
        
        for cookie_name, cookie in response.cookies.items():
            try:
                cookie_def = CookieDefinition.objects.get(
                    name=cookie_name,
                    domain=request.get_host()
                )
                
                has_consent = request.cookie_consent.get(
                    cookie_def.category.cookie_type, False
                )
                
                if not has_consent and cookie_def.category.compliance_level != 'required':
                    # Remove cookie if no consent
                    response.delete_cookie(cookie_name)
                    
                    logger.warning(
                        f"Blocked cookie {cookie_name} due to lack of consent "
                        f"for category {cookie_def.category.cookie_type}"
                    )
                
                # Log cookie setting
                CookieAuditLog.objects.create(
                    action_type='cookie_set',
                    user=user,
                    session_key=session_key,
                    cookie_name=cookie_name,
                    cookie_category=cookie_def.category,
                    action_details={
                        'has_consent': has_consent,
                        'cookie_blocked': not has_consent and cookie_def.category.compliance_level != 'required'
                    },
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    compliance_status='compliant' if has_consent else 'non_compliant'
                )
                
            except CookieDefinition.DoesNotExist:
                # Unknown cookie - allow essential cookies, block others
                if cookie_name in ['sessionid', 'csrftoken']:
                    continue  # Essential cookies
                
                logger.warning(f"Unknown cookie {cookie_name} being set")
                
                CookieAuditLog.objects.create(
                    action_type='cookie_set',
                    user=user,
                    session_key=session_key,
                    cookie_name=cookie_name,
                    action_details={'unknown_cookie': True},
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_path=request.path,
                    compliance_status='warning'
                )
    
    def should_show_consent_banner(self, request) -> bool:
        """Determine if consent banner should be shown."""
        # Check if user has made consent decisions for all categories
        consent_status = request.cookie_consent
        
        for category in CookieCategory.objects.filter(is_active=True):
            if category.compliance_level in ['opt_in', 'explicit_consent', 'medical_consent']:
                if category.cookie_type not in consent_status:
                    return True
        
        return False
    
    def inject_consent_banner(self, request, response):
        """Inject consent banner into HTML response."""
        if (response.get('Content-Type', '').startswith('text/html') and 
            hasattr(response, 'content')):
            
            # Simple banner injection (in practice, you'd use a template)
            banner_html = '''
            <div id="cookie-consent-banner" style="
                position: fixed; bottom: 0; left: 0; right: 0; 
                background: #2c3e50; color: white; padding: 15px; 
                text-align: center; z-index: 9999;">
                <p>We use cookies to provide healthcare services and improve your experience. 
                <a href="/privacy/cookie-settings/" style="color: #3498db;">Manage your preferences</a> 
                or <button onclick="acceptAllCookies()" style="background: #27ae60; color: white; 
                border: none; padding: 5px 10px; margin-left: 10px;">Accept All</button></p>
            </div>
            <script>
            function acceptAllCookies() {
                fetch('/privacy/accept-all-cookies/', {method: 'POST', 
                headers: {'X-CSRFToken': '{{ csrf_token }}'}})
                .then(() => document.getElementById('cookie-consent-banner').style.display = 'none');
            }
            </script>
            '''
            
            # Insert before closing body tag
            content = response.content.decode('utf-8')
            if '</body>' in content:
                content = content.replace('</body>', banner_html + '</body>')
                response.content = content.encode('utf-8')
    
    def get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CookieManager:
    """
    Manager for healthcare-compliant cookie operations.
    
    Provides methods for managing cookie consent, preferences,
    and compliance reporting.
    """
    
    @staticmethod
    def set_user_cookie_preference(
        user_or_session: Any,
        category_type: str,
        consent_granted: bool,
        method: str = "settings",
        ip_address: str = "",
        user_agent: str = "",
        evidence: Dict = None
    ) -> UserCookiePreference:
        """Set cookie preference for a user or session."""
        
        try:
            category = CookieCategory.objects.get(
                cookie_type=category_type,
                is_active=True
            )
        except CookieCategory.DoesNotExist:
            raise ValueError(f"Invalid cookie category: {category_type}")
        
        # Determine if this is a user or session
        if hasattr(user_or_session, 'is_authenticated'):
            user = user_or_session if user_or_session.is_authenticated else None
            session_key = None
        else:
            user = None
            session_key = str(user_or_session)
        
        # Get or create preference
        if user:
            preference, created = UserCookiePreference.objects.get_or_create(
                user=user,
                category=category,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'consent_evidence': evidence or {}
                }
            )
        else:
            preference, created = UserCookiePreference.objects.get_or_create(
                session_key=session_key,
                category=category,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'consent_evidence': evidence or {}
                }
            )
        
        # Update preference
        if consent_granted:
            preference.grant_consent(method, evidence)
        else:
            preference.withdraw_consent("User preference")
        
        return preference
    
    @staticmethod
    def get_user_cookie_preferences(user_or_session: Any) -> Dict[str, bool]:
        """Get all cookie preferences for a user or session."""
        preferences = {}
        
        # Determine if this is a user or session
        if hasattr(user_or_session, 'is_authenticated'):
            user = user_or_session if user_or_session.is_authenticated else None
            session_key = None
        else:
            user = None
            session_key = str(user_or_session)
        
        for category in CookieCategory.objects.filter(is_active=True):
            try:
                if user:
                    preference = UserCookiePreference.objects.get(
                        user=user,
                        category=category
                    )
                else:
                    preference = UserCookiePreference.objects.get(
                        session_key=session_key,
                        category=category
                    )
                
                preferences[category.cookie_type] = preference.is_valid()
                
            except UserCookiePreference.DoesNotExist:
                # Default based on compliance level
                if category.compliance_level == 'required':
                    preferences[category.cookie_type] = True
                elif category.compliance_level == 'opt_out':
                    preferences[category.cookie_type] = True
                else:
                    preferences[category.cookie_type] = False
        
        return preferences
    
    @staticmethod
    def cleanup_expired_consents():
        """Clean up expired cookie consents."""
        expired_preferences = UserCookiePreference.objects.filter(
            consent_status='granted',
            expiry_date__lt=timezone.now()
        )
        
        count = 0
        for preference in expired_preferences:
            preference.consent_status = 'expired'
            preference.save(update_fields=['consent_status'])
            count += 1
        
        logger.info(f"Expired {count} cookie consent preferences")
        return count
    
    @staticmethod
    def generate_cookie_compliance_report() -> Dict[str, Any]:
        """Generate comprehensive cookie compliance report."""
        
        total_users = User.objects.count()
        total_preferences = UserCookiePreference.objects.count()
        
        report = {
            'generated_at': timezone.now(),
            'total_users': total_users,
            'total_preferences': total_preferences,
            'category_breakdown': {},
            'consent_status_breakdown': {},
            'compliance_metrics': {}
        }
        
        # Category breakdown
        for category in CookieCategory.objects.filter(is_active=True):
            category_preferences = UserCookiePreference.objects.filter(category=category)
            
            report['category_breakdown'][category.cookie_type] = {
                'name': category.name,
                'compliance_level': category.get_compliance_level_display(),
                'total_preferences': category_preferences.count(),
                'granted_consents': category_preferences.filter(consent_status='granted').count(),
                'withdrawn_consents': category_preferences.filter(consent_status='withdrawn').count(),
                'is_healthcare_related': category.is_healthcare_related,
            }
        
        # Consent status breakdown
        for status, status_name in UserCookiePreference.CONSENT_STATUS:
            count = UserCookiePreference.objects.filter(consent_status=status).count()
            report['consent_status_breakdown'][status] = {
                'name': status_name,
                'count': count,
                'percentage': (count / total_preferences * 100) if total_preferences > 0 else 0
            }
        
        # Compliance metrics
        recent_logs = CookieAuditLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        compliant_actions = recent_logs.filter(compliance_status='compliant').count()
        total_actions = recent_logs.count()
        
        report['compliance_metrics'] = {
            'actions_last_30_days': total_actions,
            'compliance_rate': (compliant_actions / total_actions * 100) if total_actions > 0 else 0,
            'non_compliant_actions': recent_logs.filter(compliance_status='non_compliant').count(),
            'warning_actions': recent_logs.filter(compliance_status='warning').count(),
            'expired_consents': UserCookiePreference.objects.filter(consent_status='expired').count(),
        }
        
        return report