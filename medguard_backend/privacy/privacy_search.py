# -*- coding: utf-8 -*-
"""
MedGuard SA - Privacy-Aware Search Module

Implements privacy-aware search functionality that respects patient data restrictions
and compliance requirements while providing comprehensive audit trails.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q, Avg
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from wagtail.models import Page
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.snippets.models import register_snippet
from wagtail.search.backends import get_search_backend
from wagtail.search.models import Query

from .wagtail_privacy import AnonymizationProfile, DataAnonymizer, ConsentManager

logger = logging.getLogger(__name__)
User = get_user_model()


@register_snippet
class SearchPrivacyRule(models.Model):
    """
    Rules for controlling search access to patient data.
    
    Defines what data can be searched and by whom, ensuring
    patient privacy is maintained in search operations.
    """
    
    RULE_TYPES = [
        ('field_restriction', _('Field Access Restriction')),
        ('user_role_restriction', _('User Role Restriction')),
        ('consent_based_restriction', _('Consent-Based Restriction')),
        ('time_based_restriction', _('Time-Based Restriction')),
        ('geographic_restriction', _('Geographic Restriction')),
        ('purpose_limitation', _('Purpose Limitation')),
        ('anonymization_requirement', _('Anonymization Requirement')),
    ]
    
    RESTRICTION_LEVELS = [
        ('none', _('No Restriction')),
        ('anonymized_only', _('Anonymized Data Only')),
        ('aggregated_only', _('Aggregated Data Only')),
        ('restricted_fields', _('Restricted Fields')),
        ('no_access', _('No Access')),
        ('consent_required', _('Explicit Consent Required')),
    ]
    
    name = models.CharField(
        max_length=200,
        verbose_name=_("Rule Name"),
        help_text=_("Descriptive name for this search privacy rule")
    )
    
    rule_type = models.CharField(
        max_length=30,
        choices=RULE_TYPES,
        verbose_name=_("Rule Type"),
        help_text=_("Type of privacy restriction this rule enforces")
    )
    
    restriction_level = models.CharField(
        max_length=20,
        choices=RESTRICTION_LEVELS,
        verbose_name=_("Restriction Level"),
        help_text=_("Level of restriction to apply")
    )
    
    affected_models = models.JSONField(
        default=list,
        verbose_name=_("Affected Models"),
        help_text=_("List of Django models this rule applies to")
    )
    
    restricted_fields = models.JSONField(
        default=list,
        verbose_name=_("Restricted Fields"),
        help_text=_("List of fields that are restricted by this rule")
    )
    
    allowed_user_roles = models.JSONField(
        default=list,
        verbose_name=_("Allowed User Roles"),
        help_text=_("User roles that can bypass this restriction")
    )
    
    required_consent_types = models.JSONField(
        default=list,
        verbose_name=_("Required Consent Types"),
        help_text=_("Consent types required to access restricted data")
    )
    
    purpose_limitations = models.JSONField(
        default=list,
        verbose_name=_("Purpose Limitations"),
        help_text=_("Allowed purposes for accessing this data")
    )
    
    time_restrictions = models.JSONField(
        default=dict,
        verbose_name=_("Time Restrictions"),
        help_text=_("Time-based access restrictions (hours, days, etc.)")
    )
    
    geographic_restrictions = models.JSONField(
        default=list,
        verbose_name=_("Geographic Restrictions"),
        help_text=_("Geographic regions where this rule applies")
    )
    
    anonymization_profile = models.ForeignKey(
        AnonymizationProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Anonymization Profile"),
        help_text=_("Profile to use for anonymizing search results")
    )
    
    priority = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Priority"),
        help_text=_("Rule priority (lower numbers = higher priority)")
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('rule_type'),
            FieldPanel('restriction_level'),
            FieldPanel('priority'),
        ], heading=_("Rule Configuration")),
        
        MultiFieldPanel([
            FieldPanel('affected_models'),
            FieldPanel('restricted_fields'),
            FieldPanel('allowed_user_roles'),
        ], heading=_("Access Control")),
        
        MultiFieldPanel([
            FieldPanel('required_consent_types'),
            FieldPanel('purpose_limitations'),
            FieldPanel('anonymization_profile'),
        ], heading=_("Privacy Requirements")),
        
        MultiFieldPanel([
            FieldPanel('time_restrictions'),
            FieldPanel('geographic_restrictions'),
        ], heading=_("Additional Restrictions")),
        
        FieldPanel('is_active'),
    ]
    
    class Meta:
        verbose_name = _("Search Privacy Rule")
        verbose_name_plural = _("Search Privacy Rules")
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_rule_type_display()})"
    
    def applies_to_model(self, model_path: str) -> bool:
        """Check if this rule applies to a specific model."""
        return model_path in self.affected_models or '*' in self.affected_models
    
    def applies_to_user(self, user: User) -> bool:
        """Check if this rule applies to a specific user."""
        if not self.allowed_user_roles:
            return True  # Rule applies to all users
        
        # Check user roles (would integrate with your role system)
        user_roles = getattr(user, 'roles', [])
        return not any(role in self.allowed_user_roles for role in user_roles)
    
    def check_consent_requirements(self, patient: User, searcher: User) -> bool:
        """Check if consent requirements are met."""
        if not self.required_consent_types:
            return True
        
        for consent_type in self.required_consent_types:
            if not ConsentManager.check_patient_consent(patient, consent_type):
                return False
        
        return True


class SearchAuditLog(models.Model):
    """
    Audit log for privacy-aware search operations.
    
    Tracks who searched for what, when, and what privacy
    restrictions were applied.
    """
    
    SEARCH_TYPES = [
        ('patient_search', _('Patient Search')),
        ('medical_record_search', _('Medical Record Search')),
        ('prescription_search', _('Prescription Search')),
        ('audit_search', _('Audit Search')),
        ('research_search', _('Research Search')),
        ('admin_search', _('Administrative Search')),
    ]
    
    search_id = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Search ID"),
        help_text=_("Unique identifier for this search operation")
    )
    
    searcher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Searcher"),
        help_text=_("User who performed the search"),
        related_name='search_audit_logs'
    )
    
    search_type = models.CharField(
        max_length=30,
        choices=SEARCH_TYPES,
        verbose_name=_("Search Type"),
        help_text=_("Type of search performed")
    )
    
    search_query = models.TextField(
        verbose_name=_("Search Query"),
        help_text=_("The search query that was executed")
    )
    
    searched_models = models.JSONField(
        default=list,
        verbose_name=_("Searched Models"),
        help_text=_("List of models that were searched")
    )
    
    privacy_rules_applied = models.JSONField(
        default=list,
        verbose_name=_("Privacy Rules Applied"),
        help_text=_("List of privacy rules that were applied to this search")
    )
    
    results_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Results Count"),
        help_text=_("Number of results returned (before privacy filtering)")
    )
    
    filtered_results_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Filtered Results Count"),
        help_text=_("Number of results after privacy filtering")
    )
    
    anonymized_results_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Anonymized Results Count"),
        help_text=_("Number of results that were anonymized")
    )
    
    access_denied_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Access Denied Count"),
        help_text=_("Number of results that were denied access")
    )
    
    search_purpose = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Search Purpose"),
        help_text=_("Stated purpose for the search")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address from which search was performed")
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Browser/client information")
    )
    
    execution_time_ms = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Execution Time (ms)"),
        help_text=_("Time taken to execute the search in milliseconds")
    )
    
    privacy_violations = models.JSONField(
        default=list,
        verbose_name=_("Privacy Violations"),
        help_text=_("List of privacy violations detected during search")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Search Audit Log")
        verbose_name_plural = _("Search Audit Logs")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.search_id} - {self.searcher} ({self.search_type})"
    
    def save(self, *args, **kwargs):
        """Generate search ID if not provided."""
        if not self.search_id:
            from django.utils.crypto import get_random_string
            self.search_id = f"SEARCH-{get_random_string(10).upper()}"
        
        super().save(*args, **kwargs)


class PrivacyAwareSearchBackend:
    """
    Privacy-aware search backend that applies privacy rules to search operations.
    
    Wraps the default Wagtail search backend to add privacy filtering,
    anonymization, and audit logging.
    """
    
    def __init__(self, user: User, search_purpose: str = "", ip_address: str = "", user_agent: str = ""):
        """Initialize the privacy-aware search backend."""
        self.user = user
        self.search_purpose = search_purpose
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.backend = get_search_backend()
        
    def search(self, query: str, model_classes: List = None, **kwargs) -> Dict[str, Any]:
        """Perform privacy-aware search across specified models."""
        start_time = time.time()
        
        # Create audit log entry
        audit_log = SearchAuditLog.objects.create(
            searcher=self.user,
            search_type=kwargs.get('search_type', 'patient_search'),
            search_query=query,
            searched_models=[f"{m._meta.app_label}.{m._meta.model_name}" for m in (model_classes or [])],
            search_purpose=self.search_purpose,
            ip_address=self.ip_address,
            user_agent=self.user_agent
        )
        
        try:
            # Get applicable privacy rules
            privacy_rules = self._get_applicable_privacy_rules(model_classes)
            
            # Perform search with privacy filtering
            search_results = self._execute_privacy_filtered_search(
                query, model_classes, privacy_rules, **kwargs
            )
            
            # Update audit log with results
            execution_time = int((time.time() - start_time) * 1000)
            audit_log.privacy_rules_applied = [rule.name for rule in privacy_rules]
            audit_log.results_count = search_results['total_results']
            audit_log.filtered_results_count = search_results['accessible_results']
            audit_log.anonymized_results_count = search_results['anonymized_results']
            audit_log.access_denied_count = search_results['denied_results']
            audit_log.execution_time_ms = execution_time
            audit_log.privacy_violations = search_results['privacy_violations']
            audit_log.save()
            
            return search_results
            
        except Exception as e:
            # Log the error
            audit_log.privacy_violations.append({
                'type': 'search_error',
                'message': str(e),
                'timestamp': timezone.now().isoformat()
            })
            audit_log.save()
            raise
    
    def _get_applicable_privacy_rules(self, model_classes: List) -> List[SearchPrivacyRule]:
        """Get privacy rules applicable to the search."""
        if not model_classes:
            return []
        
        model_paths = [f"{m._meta.app_label}.{m._meta.model_name}" for m in model_classes]
        
        rules = SearchPrivacyRule.objects.filter(
            is_active=True
        ).order_by('priority')
        
        applicable_rules = []
        for rule in rules:
            if any(rule.applies_to_model(path) for path in model_paths):
                if rule.applies_to_user(self.user):
                    applicable_rules.append(rule)
        
        return applicable_rules
    
    def _execute_privacy_filtered_search(
        self, 
        query: str, 
        model_classes: List, 
        privacy_rules: List[SearchPrivacyRule], 
        **kwargs
    ) -> Dict[str, Any]:
        """Execute search with privacy filtering applied."""
        
        search_results = {
            'query': query,
            'results': {},
            'total_results': 0,
            'accessible_results': 0,
            'anonymized_results': 0,
            'denied_results': 0,
            'privacy_violations': []
        }
        
        if not model_classes:
            return search_results
        
        for model_class in model_classes:
            model_path = f"{model_class._meta.app_label}.{model_class._meta.model_name}"
            
            try:
                # Get model-specific privacy rules
                model_rules = [rule for rule in privacy_rules if rule.applies_to_model(model_path)]
                
                # Execute search for this model
                model_results = self._search_model_with_privacy(
                    query, model_class, model_rules, **kwargs
                )
                
                search_results['results'][model_path] = model_results
                search_results['total_results'] += model_results['total_count']
                search_results['accessible_results'] += model_results['accessible_count']
                search_results['anonymized_results'] += model_results['anonymized_count']
                search_results['denied_results'] += model_results['denied_count']
                
            except Exception as e:
                search_results['privacy_violations'].append({
                    'model': model_path,
                    'type': 'model_search_error',
                    'message': str(e)
                })
        
        return search_results
    
    def _search_model_with_privacy(
        self, 
        query: str, 
        model_class, 
        privacy_rules: List[SearchPrivacyRule], 
        **kwargs
    ) -> Dict[str, Any]:
        """Search a specific model with privacy rules applied."""
        
        model_results = {
            'model': f"{model_class._meta.app_label}.{model_class._meta.model_name}",
            'total_count': 0,
            'accessible_count': 0,
            'anonymized_count': 0,
            'denied_count': 0,
            'results': [],
            'privacy_summary': {}
        }
        
        # Check if model search is completely blocked
        blocking_rules = [rule for rule in privacy_rules if rule.restriction_level == 'no_access']
        if blocking_rules:
            model_results['privacy_summary']['blocked_by'] = [rule.name for rule in blocking_rules]
            return model_results
        
        # Perform the actual search
        try:
            # Use Wagtail search or Django ORM based on model type
            if hasattr(model_class, 'search'):
                # Wagtail search
                search_queryset = model_class.search(query)
            else:
                # Django ORM search (basic implementation)
                search_queryset = self._django_orm_search(model_class, query)
            
            model_results['total_count'] = len(search_queryset)
            
            # Apply privacy filtering to results
            for obj in search_queryset:
                privacy_decision = self._evaluate_object_privacy(obj, privacy_rules)
                
                if privacy_decision['access_allowed']:
                    if privacy_decision['anonymize_required']:
                        # Anonymize the object
                        anonymized_obj = self._anonymize_search_result(obj, privacy_decision['anonymization_profile'])
                        model_results['results'].append(anonymized_obj)
                        model_results['anonymized_count'] += 1
                    else:
                        # Return object as-is (possibly with field restrictions)
                        filtered_obj = self._apply_field_restrictions(obj, privacy_decision['restricted_fields'])
                        model_results['results'].append(filtered_obj)
                    
                    model_results['accessible_count'] += 1
                else:
                    model_results['denied_count'] += 1
            
            # Add privacy summary
            model_results['privacy_summary'] = {
                'rules_applied': [rule.name for rule in privacy_rules],
                'anonymization_applied': model_results['anonymized_count'] > 0,
                'access_restrictions': any(rule.restriction_level != 'none' for rule in privacy_rules)
            }
            
        except Exception as e:
            logger.error(f"Error searching model {model_class.__name__}: {e}")
            model_results['privacy_summary']['error'] = str(e)
        
        return model_results
    
    def _django_orm_search(self, model_class, query: str):
        """Basic Django ORM search implementation."""
        # This is a simplified implementation
        # In practice, you'd implement more sophisticated search logic
        
        search_fields = []
        
        # Find text fields to search
        for field in model_class._meta.fields:
            if field.get_internal_type() in ['CharField', 'TextField']:
                search_fields.append(field.name)
        
        if not search_fields:
            return model_class.objects.none()
        
        # Build search query
        search_q = Q()
        for field in search_fields:
            search_q |= Q(**{f"{field}__icontains": query})
        
        return model_class.objects.filter(search_q)
    
    def _evaluate_object_privacy(self, obj, privacy_rules: List[SearchPrivacyRule]) -> Dict[str, Any]:
        """Evaluate privacy requirements for a specific object."""
        
        decision = {
            'access_allowed': True,
            'anonymize_required': False,
            'anonymization_profile': None,
            'restricted_fields': [],
            'consent_required': [],
            'violations': []
        }
        
        for rule in privacy_rules:
            # Check consent requirements
            if rule.required_consent_types and hasattr(obj, 'patient'):
                patient = getattr(obj, 'patient', None) or getattr(obj, 'user', None)
                if patient and not rule.check_consent_requirements(patient, self.user):
                    if rule.restriction_level == 'no_access':
                        decision['access_allowed'] = False
                        decision['violations'].append(f"Missing consent: {rule.required_consent_types}")
                    elif rule.restriction_level == 'anonymized_only':
                        decision['anonymize_required'] = True
                        decision['anonymization_profile'] = rule.anonymization_profile
            
            # Check time restrictions
            if rule.time_restrictions:
                if not self._check_time_restrictions(obj, rule.time_restrictions):
                    if rule.restriction_level == 'no_access':
                        decision['access_allowed'] = False
                        decision['violations'].append("Time restriction violated")
                    elif rule.restriction_level == 'anonymized_only':
                        decision['anonymize_required'] = True
            
            # Apply field restrictions
            if rule.restricted_fields:
                decision['restricted_fields'].extend(rule.restricted_fields)
            
            # Check if anonymization is required
            if rule.restriction_level == 'anonymized_only':
                decision['anonymize_required'] = True
                if rule.anonymization_profile:
                    decision['anonymization_profile'] = rule.anonymization_profile
        
        return decision
    
    def _check_time_restrictions(self, obj, time_restrictions: Dict) -> bool:
        """Check if object access violates time restrictions."""
        if not time_restrictions:
            return True
        
        # Check business hours restriction
        if 'business_hours_only' in time_restrictions and time_restrictions['business_hours_only']:
            current_hour = timezone.now().hour
            if current_hour < 8 or current_hour > 17:  # Outside 8 AM - 5 PM
                return False
        
        # Check data age restriction
        if 'max_age_days' in time_restrictions:
            max_age = time_restrictions['max_age_days']
            if hasattr(obj, 'created_at'):
                age_days = (timezone.now() - obj.created_at).days
                if age_days > max_age:
                    return False
        
        return True
    
    def _anonymize_search_result(self, obj, anonymization_profile: AnonymizationProfile) -> Dict[str, Any]:
        """Anonymize a search result object."""
        if not anonymization_profile:
            # Use default anonymization
            anonymized_data = {
                'id': f"anon_{obj.pk}",
                'type': obj._meta.model_name,
                'anonymized': True
            }
        else:
            # Use specified anonymization profile
            anonymizer = DataAnonymizer(anonymization_profile)
            
            # Convert object to dict
            obj_dict = {}
            for field in obj._meta.fields:
                obj_dict[field.name] = getattr(obj, field.name)
            
            # Anonymize
            anonymized_data = anonymizer.anonymize_record(obj_dict)
            anonymized_data['anonymized'] = True
        
        return anonymized_data
    
    def _apply_field_restrictions(self, obj, restricted_fields: List[str]) -> Dict[str, Any]:
        """Apply field restrictions to a search result."""
        result_data = {}
        
        for field in obj._meta.fields:
            field_name = field.name
            
            if field_name in restricted_fields:
                result_data[field_name] = "[RESTRICTED]"
            else:
                value = getattr(obj, field_name)
                
                # Handle special field types
                if hasattr(value, 'isoformat'):  # DateTime fields
                    result_data[field_name] = value.isoformat()
                elif hasattr(value, 'url'):  # File fields
                    result_data[field_name] = value.url if value else None
                else:
                    result_data[field_name] = str(value) if value is not None else None
        
        result_data['id'] = obj.pk
        result_data['type'] = obj._meta.model_name
        result_data['restricted_fields'] = restricted_fields
        
        return result_data


class PrivacySearchManager:
    """
    Manager for privacy-aware search operations and compliance.
    
    Provides high-level interface for performing compliant searches
    and managing search privacy policies.
    """
    
    @staticmethod
    def create_search_session(
        user: User, 
        search_purpose: str, 
        ip_address: str = "", 
        user_agent: str = ""
    ) -> PrivacyAwareSearchBackend:
        """Create a new privacy-aware search session."""
        
        return PrivacyAwareSearchBackend(
            user=user,
            search_purpose=search_purpose,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @staticmethod
    def search_patients(
        user: User, 
        query: str, 
        search_purpose: str = "Patient lookup",
        **kwargs
    ) -> Dict[str, Any]:
        """Search for patients with privacy protection."""
        
        search_backend = PrivacySearchManager.create_search_session(
            user=user,
            search_purpose=search_purpose,
            ip_address=kwargs.get('ip_address', ''),
            user_agent=kwargs.get('user_agent', '')
        )
        
        # Import patient model (adjust based on your model structure)
        Patient = get_user_model()
        
        return search_backend.search(
            query=query,
            model_classes=[Patient],
            search_type='patient_search',
            **kwargs
        )
    
    @staticmethod
    def search_medical_records(
        user: User, 
        query: str, 
        patient: User = None,
        search_purpose: str = "Medical record lookup",
        **kwargs
    ) -> Dict[str, Any]:
        """Search medical records with privacy protection."""
        
        search_backend = PrivacySearchManager.create_search_session(
            user=user,
            search_purpose=search_purpose,
            ip_address=kwargs.get('ip_address', ''),
            user_agent=kwargs.get('user_agent', '')
        )
        
        # Get medical record models (adjust based on your models)
        try:
            from medications.models import Prescription  # Example
            model_classes = [Prescription]  # Add other medical models as needed
        except ImportError:
            # Fallback if medication models don't exist yet
            model_classes = []
        
        search_results = search_backend.search(
            query=query,
            model_classes=model_classes,
            search_type='medical_record_search',
            **kwargs
        )
        
        # Filter by patient if specified
        if patient:
            for model_path, model_results in search_results['results'].items():
                filtered_results = []
                for result in model_results['results']:
                    if (hasattr(result, 'patient_id') and result.get('patient_id') == patient.id) or \
                       (hasattr(result, 'user_id') and result.get('user_id') == patient.id):
                        filtered_results.append(result)
                
                model_results['results'] = filtered_results
                model_results['accessible_count'] = len(filtered_results)
        
        return search_results
    
    @staticmethod
    def get_search_audit_logs(
        user: User = None, 
        start_date: datetime = None, 
        end_date: datetime = None,
        search_type: str = None
    ) -> List[SearchAuditLog]:
        """Get search audit logs with optional filtering."""
        
        queryset = SearchAuditLog.objects.all()
        
        if user:
            queryset = queryset.filter(searcher=user)
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        if search_type:
            queryset = queryset.filter(search_type=search_type)
        
        return list(queryset.order_by('-created_at'))
    
    @staticmethod
    def generate_search_privacy_report() -> Dict[str, Any]:
        """Generate comprehensive search privacy compliance report."""
        
        total_searches = SearchAuditLog.objects.count()
        
        report = {
            'generated_at': timezone.now(),
            'total_searches': total_searches,
            'search_type_breakdown': {},
            'privacy_rule_usage': {},
            'access_patterns': {},
            'compliance_metrics': {}
        }
        
        # Search type breakdown
        for search_type, type_name in SearchAuditLog.SEARCH_TYPES:
            count = SearchAuditLog.objects.filter(search_type=search_type).count()
            report['search_type_breakdown'][search_type] = {
                'name': type_name,
                'count': count,
                'percentage': (count / total_searches * 100) if total_searches > 0 else 0
            }
        
        # Privacy rule usage
        active_rules = SearchPrivacyRule.objects.filter(is_active=True)
        for rule in active_rules:
            usage_count = SearchAuditLog.objects.filter(
                privacy_rules_applied__contains=[rule.name]
            ).count()
            
            report['privacy_rule_usage'][rule.name] = {
                'rule_type': rule.get_rule_type_display(),
                'restriction_level': rule.get_restriction_level_display(),
                'usage_count': usage_count
            }
        
        # Access patterns
        recent_searches = SearchAuditLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        total_results = sum(log.results_count for log in recent_searches)
        total_filtered = sum(log.filtered_results_count for log in recent_searches)
        total_denied = sum(log.access_denied_count for log in recent_searches)
        total_anonymized = sum(log.anonymized_results_count for log in recent_searches)
        
        report['access_patterns'] = {
            'searches_last_30_days': recent_searches.count(),
            'total_results_found': total_results,
            'results_accessible': total_filtered,
            'results_denied': total_denied,
            'results_anonymized': total_anonymized,
        }
        
        # Compliance metrics
        searches_with_violations = SearchAuditLog.objects.exclude(
            privacy_violations=[]
        ).count()
        
        report['compliance_metrics'] = {
            'privacy_compliance_rate': (
                ((total_searches - searches_with_violations) / total_searches * 100)
                if total_searches > 0 else 0
            ),
            'average_execution_time_ms': (
                SearchAuditLog.objects.aggregate(
                    avg_time=Avg('execution_time_ms')
                )['avg_time'] or 0
            ),
            'searches_with_violations': searches_with_violations,
            'data_anonymization_rate': (
                (total_anonymized / total_filtered * 100) if total_filtered > 0 else 0
            )
        }
        
        return report