# -*- coding: utf-8 -*-
"""
MedGuard SA - Wagtail 7.0.2 Healthcare Integrations
==================================================

This module provides comprehensive healthcare integrations for the South African
healthcare ecosystem using Wagtail 7.0.2 CMS capabilities.

Author: MedGuard SA Development Team
License: Proprietary
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, ObjectList
from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register
from wagtail.core.models import Page
from wagtail.fields import RichTextField
from wagtail.snippets.models import register_snippet
from wagtail.api import APIField
from wagtail.images.api.fields import ImageRenditionField
from rest_framework import serializers

logger = logging.getLogger(__name__)


# =============================================================================
# 1. SOUTH AFRICAN PHARMACY CHAINS INTEGRATION
# =============================================================================

@register_snippet
class PharmacyChain(models.Model):
    """
    Model representing South African pharmacy chains (Clicks, Dis-Chem, etc.)
    
    Provides integration capabilities for:
    - Stock availability checking
    - Prescription fulfillment
    - Loyalty program integration
    - Store locator services
    """
    
    # Basic Information
    name = models.CharField(
        max_length=100,
        verbose_name=_("Pharmacy Chain Name"),
        help_text=_("e.g., Clicks, Dis-Chem, Netcare Medicross")
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Chain Code"),
        help_text=_("Unique identifier for API integration")
    )
    
    # API Configuration
    api_endpoint = models.URLField(
        verbose_name=_("API Endpoint"),
        help_text=_("Base URL for pharmacy chain API")
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("API Key"),
        help_text=_("Authentication key for API access")
    )
    
    # Integration Settings
    supports_stock_check = models.BooleanField(
        default=True,
        verbose_name=_("Supports Stock Checking"),
        help_text=_("Can check medication availability")
    )
    
    supports_prescription_fulfillment = models.BooleanField(
        default=False,
        verbose_name=_("Supports Prescription Fulfillment"),
        help_text=_("Can process digital prescriptions")
    )
    
    supports_loyalty_integration = models.BooleanField(
        default=False,
        verbose_name=_("Supports Loyalty Programs"),
        help_text=_("Integrates with customer loyalty programs")
    )
    
    # Contact Information
    contact_email = models.EmailField(
        blank=True,
        verbose_name=_("Contact Email"),
        help_text=_("Technical contact for integration issues")
    )
    
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Contact Phone"),
        help_text=_("Technical support phone number")
    )
    
    # Status and Metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Integration is currently active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Pharmacy Chain")
        verbose_name_plural = _("Pharmacy Chains")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('code'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('api_endpoint'),
            FieldPanel('api_key'),
        ], heading=_("API Configuration")),
        
        MultiFieldPanel([
            FieldPanel('supports_stock_check'),
            FieldPanel('supports_prescription_fulfillment'),
            FieldPanel('supports_loyalty_integration'),
        ], heading=_("Integration Capabilities")),
        
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('contact_phone'),
            FieldPanel('is_active'),
        ], heading=_("Contact & Status")),
    ]
    
    def check_medication_stock(self, medication_code: str, location: str = None) -> Dict[str, Any]:
        """
        Check stock availability for a specific medication
        
        Args:
            medication_code: Standard medication identifier
            location: Optional location filter (province/city)
            
        Returns:
            Dict containing stock information and store locations
        """
        if not self.supports_stock_check or not self.is_active:
            return {'error': 'Stock checking not supported or chain inactive'}
        
        cache_key = f"pharmacy_stock_{self.code}_{medication_code}_{location or 'all'}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            params = {
                'medication_code': medication_code,
                'location': location
            }
            
            response = requests.get(
                f"{self.api_endpoint}/stock/check",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 15 minutes
                cache.set(cache_key, result, 900)
                return result
            else:
                logger.error(f"Stock check failed for {self.name}: {response.status_code}")
                return {'error': f'API error: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Stock check request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def submit_prescription(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a digital prescription for fulfillment
        
        Args:
            prescription_data: Dictionary containing prescription details
            
        Returns:
            Dict with submission status and tracking information
        """
        if not self.supports_prescription_fulfillment or not self.is_active:
            return {'error': 'Prescription fulfillment not supported or chain inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/prescriptions/submit",
                headers=headers,
                json=prescription_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Prescription submitted to {self.name}: {result.get('tracking_id')}")
                return result
            else:
                logger.error(f"Prescription submission failed for {self.name}: {response.status_code}")
                return {'error': f'Submission failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Prescription submission request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def get_loyalty_points(self, customer_id: str) -> Dict[str, Any]:
        """
        Retrieve customer loyalty points and benefits
        
        Args:
            customer_id: Customer identifier in the loyalty system
            
        Returns:
            Dict with points balance and available benefits
        """
        if not self.supports_loyalty_integration or not self.is_active:
            return {'error': 'Loyalty integration not supported or chain inactive'}
        
        cache_key = f"loyalty_points_{self.code}_{customer_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.get(
                f"{self.api_endpoint}/loyalty/{customer_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 1 hour
                cache.set(cache_key, result, 3600)
                return result
            else:
                logger.error(f"Loyalty check failed for {self.name}: {response.status_code}")
                return {'error': f'API error: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Loyalty check request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}


class PharmacyChainAdmin(ModelAdmin):
    """Wagtail admin configuration for Pharmacy Chain management"""
    
    model = PharmacyChain
    menu_label = _('Pharmacy Chains')
    menu_icon = 'fa-pills'
    menu_order = 100
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'code', 'supports_stock_check', 'supports_prescription_fulfillment', 'is_active')
    list_filter = ('is_active', 'supports_stock_check', 'supports_prescription_fulfillment')
    search_fields = ('name', 'code', 'contact_email')


# Register the admin
modeladmin_register(PharmacyChainAdmin)


class PharmacyIntegrationPage(Page):
    """
    Wagtail page for managing pharmacy chain integrations
    """
    
    intro = RichTextField(
        blank=True,
        features=['bold', 'link', 'ol', 'ul'],
        help_text=_("Introduction text for pharmacy integrations")
    )
    
    # API Settings
    default_timeout = models.IntegerField(
        default=10,
        verbose_name=_("Default API Timeout (seconds)"),
        help_text=_("Default timeout for pharmacy API calls")
    )
    
    enable_caching = models.BooleanField(
        default=True,
        verbose_name=_("Enable Response Caching"),
        help_text=_("Cache API responses to improve performance")
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
        MultiFieldPanel([
            FieldPanel('default_timeout'),
            FieldPanel('enable_caching'),
        ], heading=_("API Configuration")),
    ]
    
    class Meta:
        verbose_name = _("Pharmacy Integration Page")
    
    def get_active_chains(self) -> List[PharmacyChain]:
        """Get all active pharmacy chains"""
        return PharmacyChain.objects.filter(is_active=True).order_by('name')
    
    def check_all_chains_stock(self, medication_code: str, location: str = None) -> Dict[str, Any]:
        """
        Check stock across all active pharmacy chains
        
        Args:
            medication_code: Standard medication identifier
            location: Optional location filter
            
        Returns:
            Dict with results from all chains
        """
        results = {}
        active_chains = self.get_active_chains()
        
        for chain in active_chains:
            if chain.supports_stock_check:
                results[chain.code] = chain.check_medication_stock(medication_code, location)
        
        return results


# API Serializers for Pharmacy Integration
class PharmacyChainSerializer(serializers.ModelSerializer):
    """REST API serializer for PharmacyChain model"""
    
    class Meta:
        model = PharmacyChain
        fields = [
            'id', 'name', 'code', 'supports_stock_check',
            'supports_prescription_fulfillment', 'supports_loyalty_integration',
            'contact_email', 'contact_phone', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Utility Functions for Pharmacy Integration
def get_pharmacy_chain_by_code(code: str) -> Optional[PharmacyChain]:
    """Get pharmacy chain by code"""
    try:
        return PharmacyChain.objects.get(code=code, is_active=True)
    except PharmacyChain.DoesNotExist:
        return None


def check_medication_availability(medication_code: str, location: str = None) -> Dict[str, Any]:
    """
    Check medication availability across all active pharmacy chains
    
    Args:
        medication_code: Standard medication identifier
        location: Optional location filter
        
    Returns:
        Aggregated results from all chains
    """
    results = {
        'medication_code': medication_code,
        'location': location,
        'timestamp': datetime.now().isoformat(),
        'chains': {}
    }
    
    active_chains = PharmacyChain.objects.filter(
        is_active=True,
        supports_stock_check=True
    )
    
    for chain in active_chains:
        results['chains'][chain.code] = chain.check_medication_stock(medication_code, location)
    
    return results


# =============================================================================
# 2. MEDICAL AID SCHEMES INTEGRATION
# =============================================================================

@register_snippet
class MedicalAidScheme(models.Model):
    """
    Model representing South African medical aid schemes (Discovery, Momentum, etc.)
    
    Provides integration capabilities for:
    - Benefits checking and authorization
    - Claims submission and tracking
    - Pre-authorization requests
    - Member verification
    """
    
    # Basic Information
    name = models.CharField(
        max_length=100,
        verbose_name=_("Medical Aid Scheme Name"),
        help_text=_("e.g., Discovery Health, Momentum Health, Bonitas")
    )
    
    scheme_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_("Scheme Code"),
        help_text=_("Unique identifier for medical aid scheme")
    )
    
    registration_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("CMS Registration Number"),
        help_text=_("Council for Medical Schemes registration number")
    )
    
    # API Configuration
    api_endpoint = models.URLField(
        verbose_name=_("API Endpoint"),
        help_text=_("Base URL for medical aid scheme API")
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("API Key"),
        help_text=_("Authentication key for API access")
    )
    
    client_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Client ID"),
        help_text=_("OAuth client identifier")
    )
    
    # Integration Capabilities
    supports_benefits_check = models.BooleanField(
        default=True,
        verbose_name=_("Supports Benefits Checking"),
        help_text=_("Can check member benefits and coverage")
    )
    
    supports_claims_submission = models.BooleanField(
        default=False,
        verbose_name=_("Supports Claims Submission"),
        help_text=_("Can submit claims electronically")
    )
    
    supports_preauth = models.BooleanField(
        default=False,
        verbose_name=_("Supports Pre-authorization"),
        help_text=_("Can request pre-authorization for procedures")
    )
    
    supports_member_verification = models.BooleanField(
        default=True,
        verbose_name=_("Supports Member Verification"),
        help_text=_("Can verify member eligibility")
    )
    
    # Business Rules
    requires_gp_referral = models.BooleanField(
        default=False,
        verbose_name=_("Requires GP Referral"),
        help_text=_("Scheme requires GP referral for specialist consultations")
    )
    
    max_claim_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Claim Amount"),
        help_text=_("Maximum amount for single claim submission")
    )
    
    # Contact Information
    contact_email = models.EmailField(
        blank=True,
        verbose_name=_("Contact Email"),
        help_text=_("Technical contact for integration issues")
    )
    
    support_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Support Phone"),
        help_text=_("Member support phone number")
    )
    
    # Status and Metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Integration is currently active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Medical Aid Scheme")
        verbose_name_plural = _("Medical Aid Schemes")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.scheme_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('scheme_code'),
            FieldPanel('registration_number'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('api_endpoint'),
            FieldPanel('api_key'),
            FieldPanel('client_id'),
        ], heading=_("API Configuration")),
        
        MultiFieldPanel([
            FieldPanel('supports_benefits_check'),
            FieldPanel('supports_claims_submission'),
            FieldPanel('supports_preauth'),
            FieldPanel('supports_member_verification'),
        ], heading=_("Integration Capabilities")),
        
        MultiFieldPanel([
            FieldPanel('requires_gp_referral'),
            FieldPanel('max_claim_amount'),
        ], heading=_("Business Rules")),
        
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('support_phone'),
            FieldPanel('is_active'),
        ], heading=_("Contact & Status")),
    ]
    
    def verify_member(self, member_number: str, id_number: str) -> Dict[str, Any]:
        """
        Verify member eligibility and status
        
        Args:
            member_number: Medical aid member number
            id_number: South African ID number
            
        Returns:
            Dict containing member verification results
        """
        if not self.supports_member_verification or not self.is_active:
            return {'error': 'Member verification not supported or scheme inactive'}
        
        cache_key = f"member_verify_{self.scheme_code}_{member_number}_{id_number}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            data = {
                'member_number': member_number,
                'id_number': id_number
            }
            
            response = requests.post(
                f"{self.api_endpoint}/members/verify",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 30 minutes
                cache.set(cache_key, result, 1800)
                return result
            else:
                logger.error(f"Member verification failed for {self.name}: {response.status_code}")
                return {'error': f'Verification failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Member verification request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def check_benefits(self, member_number: str, procedure_codes: List[str]) -> Dict[str, Any]:
        """
        Check member benefits for specific procedures
        
        Args:
            member_number: Medical aid member number
            procedure_codes: List of ICD-10 or procedure codes
            
        Returns:
            Dict with benefit coverage information
        """
        if not self.supports_benefits_check or not self.is_active:
            return {'error': 'Benefits checking not supported or scheme inactive'}
        
        cache_key = f"benefits_{self.scheme_code}_{member_number}_{'_'.join(procedure_codes)}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            data = {
                'member_number': member_number,
                'procedure_codes': procedure_codes
            }
            
            response = requests.post(
                f"{self.api_endpoint}/benefits/check",
                headers=headers,
                json=data,
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 2 hours
                cache.set(cache_key, result, 7200)
                return result
            else:
                logger.error(f"Benefits check failed for {self.name}: {response.status_code}")
                return {'error': f'Benefits check failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Benefits check request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def submit_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a claim for processing
        
        Args:
            claim_data: Dictionary containing claim details
            
        Returns:
            Dict with claim submission status and reference
        """
        if not self.supports_claims_submission or not self.is_active:
            return {'error': 'Claims submission not supported or scheme inactive'}
        
        # Validate claim amount against maximum
        if self.max_claim_amount and claim_data.get('amount', 0) > self.max_claim_amount:
            return {'error': f'Claim amount exceeds maximum of R{self.max_claim_amount}'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/claims/submit",
                headers=headers,
                json=claim_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Claim submitted to {self.name}: {result.get('claim_reference')}")
                return result
            else:
                logger.error(f"Claim submission failed for {self.name}: {response.status_code}")
                return {'error': f'Submission failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Claim submission request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def request_preauthorization(self, preauth_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Request pre-authorization for procedures
        
        Args:
            preauth_data: Dictionary containing pre-authorization details
            
        Returns:
            Dict with pre-authorization status and reference
        """
        if not self.supports_preauth or not self.is_active:
            return {'error': 'Pre-authorization not supported or scheme inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/preauth/request",
                headers=headers,
                json=preauth_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Pre-auth requested from {self.name}: {result.get('preauth_reference')}")
                return result
            else:
                logger.error(f"Pre-auth request failed for {self.name}: {response.status_code}")
                return {'error': f'Request failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Pre-auth request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}


class MedicalAidSchemeAdmin(ModelAdmin):
    """Wagtail admin configuration for Medical Aid Scheme management"""
    
    model = MedicalAidScheme
    menu_label = _('Medical Aid Schemes')
    menu_icon = 'fa-shield-alt'
    menu_order = 101
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'scheme_code', 'supports_benefits_check', 'supports_claims_submission', 'is_active')
    list_filter = ('is_active', 'supports_benefits_check', 'supports_claims_submission', 'supports_preauth')
    search_fields = ('name', 'scheme_code', 'registration_number')


# Register the admin
modeladmin_register(MedicalAidSchemeAdmin)


# API Serializers for Medical Aid Integration
class MedicalAidSchemeSerializer(serializers.ModelSerializer):
    """REST API serializer for MedicalAidScheme model"""
    
    class Meta:
        model = MedicalAidScheme
        fields = [
            'id', 'name', 'scheme_code', 'registration_number',
            'supports_benefits_check', 'supports_claims_submission',
            'supports_preauth', 'supports_member_verification',
            'requires_gp_referral', 'max_claim_amount',
            'contact_email', 'support_phone', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Utility Functions for Medical Aid Integration
def get_medical_aid_by_code(scheme_code: str) -> Optional[MedicalAidScheme]:
    """Get medical aid scheme by code"""
    try:
        return MedicalAidScheme.objects.get(scheme_code=scheme_code, is_active=True)
    except MedicalAidScheme.DoesNotExist:
        return None


def verify_member_across_schemes(member_number: str, id_number: str) -> Dict[str, Any]:
    """
    Verify member across all active medical aid schemes
    
    Args:
        member_number: Medical aid member number
        id_number: South African ID number
        
    Returns:
        Results from all schemes that support member verification
    """
    results = {
        'member_number': member_number,
        'timestamp': datetime.now().isoformat(),
        'schemes': {}
    }
    
    active_schemes = MedicalAidScheme.objects.filter(
        is_active=True,
        supports_member_verification=True
    )
    
    for scheme in active_schemes:
        results['schemes'][scheme.scheme_code] = scheme.verify_member(member_number, id_number)
    
    return results


# =============================================================================
# 3. HEALTHCARE PROVIDERS AND HOSPITALS INTEGRATION
# =============================================================================

@register_snippet
class HealthcareProvider(models.Model):
    """
    Model representing healthcare providers and hospitals in South Africa
    
    Provides integration capabilities for:
    - Appointment scheduling and management
    - Patient record exchange (HL7 FHIR)
    - Bed availability and capacity management
    - Specialist referrals
    - Emergency department status
    """
    
    PROVIDER_TYPES = [
        ('hospital', _('Hospital')),
        ('clinic', _('Clinic')),
        ('private_practice', _('Private Practice')),
        ('specialist_center', _('Specialist Center')),
        ('emergency_center', _('Emergency Center')),
        ('day_hospital', _('Day Hospital')),
        ('rehabilitation', _('Rehabilitation Center')),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name=_("Provider Name"),
        help_text=_("e.g., Groote Schuur Hospital, Netcare Christiaan Barnard")
    )
    
    provider_type = models.CharField(
        max_length=50,
        choices=PROVIDER_TYPES,
        verbose_name=_("Provider Type"),
        help_text=_("Type of healthcare provider")
    )
    
    registration_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("DOH Registration Number"),
        help_text=_("Department of Health registration number")
    )
    
    # Location Information
    province = models.CharField(
        max_length=50,
        verbose_name=_("Province"),
        help_text=_("South African province")
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name=_("City"),
        help_text=_("City or town location")
    )
    
    address = models.TextField(
        verbose_name=_("Physical Address"),
        help_text=_("Complete physical address")
    )
    
    # API Configuration
    api_endpoint = models.URLField(
        verbose_name=_("API Endpoint"),
        help_text=_("Base URL for provider API (HL7 FHIR compatible)")
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("API Key"),
        help_text=_("Authentication key for API access")
    )
    
    fhir_version = models.CharField(
        max_length=10,
        default='R4',
        verbose_name=_("FHIR Version"),
        help_text=_("HL7 FHIR version supported (e.g., R4, R5)")
    )
    
    # Integration Capabilities
    supports_appointments = models.BooleanField(
        default=True,
        verbose_name=_("Supports Appointments"),
        help_text=_("Can schedule and manage appointments")
    )
    
    supports_patient_records = models.BooleanField(
        default=False,
        verbose_name=_("Supports Patient Records"),
        help_text=_("Can exchange patient records via FHIR")
    )
    
    supports_bed_management = models.BooleanField(
        default=False,
        verbose_name=_("Supports Bed Management"),
        help_text=_("Provides bed availability information")
    )
    
    supports_referrals = models.BooleanField(
        default=True,
        verbose_name=_("Supports Referrals"),
        help_text=_("Accepts electronic referrals")
    )
    
    supports_emergency_status = models.BooleanField(
        default=False,
        verbose_name=_("Supports Emergency Status"),
        help_text=_("Provides emergency department status")
    )
    
    # Capacity Information
    total_beds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Total Beds"),
        help_text=_("Total number of beds available")
    )
    
    icu_beds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("ICU Beds"),
        help_text=_("Number of ICU beds available")
    )
    
    emergency_beds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Emergency Beds"),
        help_text=_("Number of emergency department beds")
    )
    
    # Contact Information
    contact_email = models.EmailField(
        blank=True,
        verbose_name=_("Contact Email"),
        help_text=_("Technical contact for integration")
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Main contact phone number")
    )
    
    emergency_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Emergency Number"),
        help_text=_("Emergency contact number")
    )
    
    # Status and Metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Provider is currently active")
    )
    
    is_24_hour = models.BooleanField(
        default=False,
        verbose_name=_("24 Hour Service"),
        help_text=_("Provides 24-hour services")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Healthcare Provider")
        verbose_name_plural = _("Healthcare Providers")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.provider_type})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('provider_type'),
            FieldPanel('registration_number'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('province'),
            FieldPanel('city'),
            FieldPanel('address'),
        ], heading=_("Location")),
        
        MultiFieldPanel([
            FieldPanel('api_endpoint'),
            FieldPanel('api_key'),
            FieldPanel('fhir_version'),
        ], heading=_("API Configuration")),
        
        MultiFieldPanel([
            FieldPanel('supports_appointments'),
            FieldPanel('supports_patient_records'),
            FieldPanel('supports_bed_management'),
            FieldPanel('supports_referrals'),
            FieldPanel('supports_emergency_status'),
        ], heading=_("Integration Capabilities")),
        
        MultiFieldPanel([
            FieldPanel('total_beds'),
            FieldPanel('icu_beds'),
            FieldPanel('emergency_beds'),
        ], heading=_("Capacity Information")),
        
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('phone_number'),
            FieldPanel('emergency_number'),
            FieldPanel('is_active'),
            FieldPanel('is_24_hour'),
        ], heading=_("Contact & Status")),
    ]
    
    def check_appointment_availability(self, date: str, specialty: str = None) -> Dict[str, Any]:
        """
        Check appointment availability for a specific date
        
        Args:
            date: Date in YYYY-MM-DD format
            specialty: Optional specialty filter
            
        Returns:
            Dict containing available appointment slots
        """
        if not self.supports_appointments or not self.is_active:
            return {'error': 'Appointment booking not supported or provider inactive'}
        
        cache_key = f"appointments_{self.id}_{date}_{specialty or 'all'}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            params = {
                'date': date,
                'status': 'free'
            }
            
            if specialty:
                params['specialty'] = specialty
            
            response = requests.get(
                f"{self.api_endpoint}/Slot",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 30 minutes
                cache.set(cache_key, result, 1800)
                return result
            else:
                logger.error(f"Appointment check failed for {self.name}: {response.status_code}")
                return {'error': f'API error: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Appointment check request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def book_appointment(self, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Book an appointment with the healthcare provider
        
        Args:
            appointment_data: FHIR Appointment resource data
            
        Returns:
            Dict with booking confirmation and details
        """
        if not self.supports_appointments or not self.is_active:
            return {'error': 'Appointment booking not supported or provider inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/Appointment",
                headers=headers,
                json=appointment_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Appointment booked at {self.name}: {result.get('id')}")
                return result
            else:
                logger.error(f"Appointment booking failed for {self.name}: {response.status_code}")
                return {'error': f'Booking failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Appointment booking request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def get_bed_availability(self) -> Dict[str, Any]:
        """
        Get current bed availability status
        
        Returns:
            Dict containing bed availability information
        """
        if not self.supports_bed_management or not self.is_active:
            return {'error': 'Bed management not supported or provider inactive'}
        
        cache_key = f"beds_{self.id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.get(
                f"{self.api_endpoint}/Location",
                headers=headers,
                params={'type': 'bed'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 15 minutes
                cache.set(cache_key, result, 900)
                return result
            else:
                logger.error(f"Bed availability check failed for {self.name}: {response.status_code}")
                return {'error': f'API error: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Bed availability request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def submit_referral(self, referral_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a patient referral to the healthcare provider
        
        Args:
            referral_data: FHIR ServiceRequest resource data
            
        Returns:
            Dict with referral submission status
        """
        if not self.supports_referrals or not self.is_active:
            return {'error': 'Referrals not supported or provider inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/ServiceRequest",
                headers=headers,
                json=referral_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Referral submitted to {self.name}: {result.get('id')}")
                return result
            else:
                logger.error(f"Referral submission failed for {self.name}: {response.status_code}")
                return {'error': f'Submission failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Referral submission request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def get_emergency_status(self) -> Dict[str, Any]:
        """
        Get current emergency department status
        
        Returns:
            Dict containing emergency department information
        """
        if not self.supports_emergency_status or not self.is_active:
            return {'error': 'Emergency status not supported or provider inactive'}
        
        cache_key = f"emergency_{self.id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.get(
                f"{self.api_endpoint}/Location",
                headers=headers,
                params={'type': 'emergency'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 5 minutes (emergency status changes frequently)
                cache.set(cache_key, result, 300)
                return result
            else:
                logger.error(f"Emergency status check failed for {self.name}: {response.status_code}")
                return {'error': f'API error: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Emergency status request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}


class HealthcareProviderAdmin(ModelAdmin):
    """Wagtail admin configuration for Healthcare Provider management"""
    
    model = HealthcareProvider
    menu_label = _('Healthcare Providers')
    menu_icon = 'fa-hospital'
    menu_order = 102
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'provider_type', 'province', 'city', 'is_active')
    list_filter = ('provider_type', 'province', 'is_active', 'is_24_hour')
    search_fields = ('name', 'city', 'registration_number')


# Register the admin
modeladmin_register(HealthcareProviderAdmin)


# API Serializers for Healthcare Provider Integration
class HealthcareProviderSerializer(serializers.ModelSerializer):
    """REST API serializer for HealthcareProvider model"""
    
    class Meta:
        model = HealthcareProvider
        fields = [
            'id', 'name', 'provider_type', 'registration_number',
            'province', 'city', 'address', 'supports_appointments',
            'supports_patient_records', 'supports_bed_management',
            'supports_referrals', 'supports_emergency_status',
            'total_beds', 'icu_beds', 'emergency_beds',
            'contact_email', 'phone_number', 'emergency_number',
            'is_active', 'is_24_hour'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Utility Functions for Healthcare Provider Integration
def find_providers_by_location(province: str = None, city: str = None, provider_type: str = None) -> List[HealthcareProvider]:
    """Find healthcare providers by location and type"""
    queryset = HealthcareProvider.objects.filter(is_active=True)
    
    if province:
        queryset = queryset.filter(province__icontains=province)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if provider_type:
        queryset = queryset.filter(provider_type=provider_type)
    
    return list(queryset.order_by('name'))


def get_emergency_providers_by_location(province: str, city: str = None) -> List[HealthcareProvider]:
    """Get emergency providers by location"""
    queryset = HealthcareProvider.objects.filter(
        is_active=True,
        supports_emergency_status=True,
        province__icontains=province
    )
    
    if city:
        queryset = queryset.filter(city__icontains=city)
    
    return list(queryset.order_by('name'))


# =============================================================================
# 4. SOUTH AFRICAN MEDICINE REGULATORY AUTHORITY (SAHPRA) INTEGRATION
# =============================================================================

@register_snippet
class RegulatoryAuthority(models.Model):
    """
    Model representing South African medicine regulatory authority (SAHPRA)
    
    Provides integration capabilities for:
    - Medicine registration verification
    - Adverse event reporting
    - Regulatory compliance checking
    - Product recall notifications
    - License verification
    """
    
    AUTHORITY_TYPES = [
        ('sahpra', _('SAHPRA - South African Health Products Regulatory Authority')),
        ('mcc', _('MCC - Medicines Control Council (Legacy)')),
        ('department_health', _('Department of Health')),
        ('pharmacy_council', _('South African Pharmacy Council')),
        ('medical_council', _('Health Professions Council of South Africa')),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name=_("Authority Name"),
        help_text=_("e.g., SAHPRA, South African Pharmacy Council")
    )
    
    authority_type = models.CharField(
        max_length=50,
        choices=AUTHORITY_TYPES,
        verbose_name=_("Authority Type"),
        help_text=_("Type of regulatory authority")
    )
    
    registration_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Authority Code"),
        help_text=_("Unique identifier for the regulatory authority")
    )
    
    # API Configuration
    api_endpoint = models.URLField(
        verbose_name=_("API Endpoint"),
        help_text=_("Base URL for regulatory authority API")
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("API Key"),
        help_text=_("Authentication key for API access")
    )
    
    certificate_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("SSL Certificate Path"),
        help_text=_("Path to SSL certificate for secure communication")
    )
    
    # Integration Capabilities
    supports_medicine_verification = models.BooleanField(
        default=True,
        verbose_name=_("Supports Medicine Verification"),
        help_text=_("Can verify medicine registration status")
    )
    
    supports_adverse_reporting = models.BooleanField(
        default=False,
        verbose_name=_("Supports Adverse Event Reporting"),
        help_text=_("Can submit adverse event reports")
    )
    
    supports_recall_notifications = models.BooleanField(
        default=True,
        verbose_name=_("Supports Recall Notifications"),
        help_text=_("Provides product recall notifications")
    )
    
    supports_license_verification = models.BooleanField(
        default=False,
        verbose_name=_("Supports License Verification"),
        help_text=_("Can verify professional licenses")
    )
    
    supports_compliance_check = models.BooleanField(
        default=False,
        verbose_name=_("Supports Compliance Checking"),
        help_text=_("Can check regulatory compliance status")
    )
    
    # Business Rules
    requires_digital_signature = models.BooleanField(
        default=True,
        verbose_name=_("Requires Digital Signature"),
        help_text=_("Submissions require digital signature")
    )
    
    max_batch_size = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Maximum Batch Size"),
        help_text=_("Maximum number of items per batch request")
    )
    
    # Contact Information
    contact_email = models.EmailField(
        blank=True,
        verbose_name=_("Contact Email"),
        help_text=_("Technical contact for integration issues")
    )
    
    support_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Support Phone"),
        help_text=_("Technical support phone number")
    )
    
    website_url = models.URLField(
        blank=True,
        verbose_name=_("Website URL"),
        help_text=_("Official website URL")
    )
    
    # Status and Metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Integration is currently active")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Regulatory Authority")
        verbose_name_plural = _("Regulatory Authorities")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.registration_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('authority_type'),
            FieldPanel('registration_code'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('api_endpoint'),
            FieldPanel('api_key'),
            FieldPanel('certificate_path'),
        ], heading=_("API Configuration")),
        
        MultiFieldPanel([
            FieldPanel('supports_medicine_verification'),
            FieldPanel('supports_adverse_reporting'),
            FieldPanel('supports_recall_notifications'),
            FieldPanel('supports_license_verification'),
            FieldPanel('supports_compliance_check'),
        ], heading=_("Integration Capabilities")),
        
        MultiFieldPanel([
            FieldPanel('requires_digital_signature'),
            FieldPanel('max_batch_size'),
        ], heading=_("Business Rules")),
        
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('support_phone'),
            FieldPanel('website_url'),
            FieldPanel('is_active'),
        ], heading=_("Contact & Status")),
    ]
    
    def verify_medicine_registration(self, medicine_code: str, batch_number: str = None) -> Dict[str, Any]:
        """
        Verify medicine registration with regulatory authority
        
        Args:
            medicine_code: Medicine registration number or code
            batch_number: Optional batch number for specific verification
            
        Returns:
            Dict containing registration verification results
        """
        if not self.supports_medicine_verification or not self.is_active:
            return {'error': 'Medicine verification not supported or authority inactive'}
        
        cache_key = f"medicine_verify_{self.registration_code}_{medicine_code}_{batch_number or 'all'}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            data = {
                'medicine_code': medicine_code,
                'batch_number': batch_number,
                'verification_type': 'registration_status'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/medicines/verify",
                headers=headers,
                json=data,
                timeout=20,
                verify=self.certificate_path if self.certificate_path else True
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 4 hours (registration status doesn't change frequently)
                cache.set(cache_key, result, 14400)
                return result
            else:
                logger.error(f"Medicine verification failed for {self.name}: {response.status_code}")
                return {'error': f'Verification failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Medicine verification request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def submit_adverse_event_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit adverse event report to regulatory authority
        
        Args:
            report_data: Dictionary containing adverse event details
            
        Returns:
            Dict with submission status and reference number
        """
        if not self.supports_adverse_reporting or not self.is_active:
            return {'error': 'Adverse event reporting not supported or authority inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            # Add digital signature if required
            if self.requires_digital_signature:
                report_data['digital_signature'] = self._generate_digital_signature(report_data)
            
            response = requests.post(
                f"{self.api_endpoint}/adverse-events/submit",
                headers=headers,
                json=report_data,
                timeout=30,
                verify=self.certificate_path if self.certificate_path else True
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Adverse event reported to {self.name}: {result.get('report_reference')}")
                return result
            else:
                logger.error(f"Adverse event submission failed for {self.name}: {response.status_code}")
                return {'error': f'Submission failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Adverse event submission request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def get_recall_notifications(self, since_date: str = None) -> Dict[str, Any]:
        """
        Get product recall notifications
        
        Args:
            since_date: Optional date filter (YYYY-MM-DD format)
            
        Returns:
            Dict containing recall notifications
        """
        if not self.supports_recall_notifications or not self.is_active:
            return {'error': 'Recall notifications not supported or authority inactive'}
        
        cache_key = f"recalls_{self.registration_code}_{since_date or 'all'}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            params = {}
            if since_date:
                params['since_date'] = since_date
            
            response = requests.get(
                f"{self.api_endpoint}/recalls/notifications",
                headers=headers,
                params=params,
                timeout=15,
                verify=self.certificate_path if self.certificate_path else True
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 1 hour
                cache.set(cache_key, result, 3600)
                return result
            else:
                logger.error(f"Recall notifications failed for {self.name}: {response.status_code}")
                return {'error': f'API error: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Recall notifications request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def _generate_digital_signature(self, data: Dict[str, Any]) -> str:
        """
        Generate digital signature for data submission
        
        Args:
            data: Data to be signed
            
        Returns:
            Digital signature string
        """
        import hashlib
        import json
        
        # Simple signature generation (in production, use proper cryptographic signing)
        data_string = json.dumps(data, sort_keys=True)
        signature = hashlib.sha256(f"{data_string}{self.api_key}".encode()).hexdigest()
        return signature


class RegulatoryAuthorityAdmin(ModelAdmin):
    """Wagtail admin configuration for Regulatory Authority management"""
    
    model = RegulatoryAuthority
    menu_label = _('Regulatory Authorities')
    menu_icon = 'fa-gavel'
    menu_order = 103
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'authority_type', 'supports_medicine_verification', 'supports_adverse_reporting', 'is_active')
    list_filter = ('authority_type', 'is_active', 'supports_medicine_verification', 'supports_adverse_reporting')
    search_fields = ('name', 'registration_code')


# Register the admin
modeladmin_register(RegulatoryAuthorityAdmin)


# =============================================================================
# 5. PATHOLOGY LABS INTEGRATION FOR TEST RESULTS
# =============================================================================

@register_snippet
class PathologyLab(models.Model):
    """
    Model representing pathology laboratories in South Africa
    
    Provides integration capabilities for:
    - Test result retrieval and delivery
    - Test ordering and scheduling
    - Laboratory information system (LIS) integration
    - Quality control and accreditation verification
    - Specimen tracking and chain of custody
    """
    
    LAB_TYPES = [
        ('pathcare', _('PathCare Pathologists')),
        ('lancet', _('Lancet Laboratories')),
        ('ampath', _('Ampath Laboratories')),
        ('nhls', _('National Health Laboratory Service')),
        ('vermaak', _('Vermaak & Partners Pathologists')),
        ('independent', _('Independent Laboratory')),
        ('hospital_lab', _('Hospital Laboratory')),
        ('specialized', _('Specialized Laboratory')),
    ]
    
    ACCREDITATION_TYPES = [
        ('sanas', _('SANAS Accredited')),
        ('cap', _('CAP Accredited')),
        ('iso15189', _('ISO 15189 Certified')),
        ('other', _('Other Accreditation')),
        ('none', _('No Accreditation')),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name=_("Laboratory Name"),
        help_text=_("e.g., PathCare Cape Town, Lancet Johannesburg")
    )
    
    lab_type = models.CharField(
        max_length=50,
        choices=LAB_TYPES,
        verbose_name=_("Laboratory Type"),
        help_text=_("Type of pathology laboratory")
    )
    
    lab_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Laboratory Code"),
        help_text=_("Unique identifier for the laboratory")
    )
    
    accreditation_type = models.CharField(
        max_length=50,
        choices=ACCREDITATION_TYPES,
        default='sanas',
        verbose_name=_("Accreditation Type"),
        help_text=_("Laboratory accreditation status")
    )
    
    # Location Information
    province = models.CharField(
        max_length=50,
        verbose_name=_("Province"),
        help_text=_("South African province")
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name=_("City"),
        help_text=_("City or town location")
    )
    
    address = models.TextField(
        verbose_name=_("Physical Address"),
        help_text=_("Complete physical address")
    )
    
    # API Configuration
    api_endpoint = models.URLField(
        verbose_name=_("API Endpoint"),
        help_text=_("Base URL for laboratory API (HL7 FHIR compatible)")
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("API Key"),
        help_text=_("Authentication key for API access")
    )
    
    lis_version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("LIS Version"),
        help_text=_("Laboratory Information System version")
    )
    
    # Integration Capabilities
    supports_result_retrieval = models.BooleanField(
        default=True,
        verbose_name=_("Supports Result Retrieval"),
        help_text=_("Can retrieve test results electronically")
    )
    
    supports_test_ordering = models.BooleanField(
        default=False,
        verbose_name=_("Supports Test Ordering"),
        help_text=_("Can accept electronic test orders")
    )
    
    supports_specimen_tracking = models.BooleanField(
        default=False,
        verbose_name=_("Supports Specimen Tracking"),
        help_text=_("Provides specimen tracking capabilities")
    )
    
    supports_quality_control = models.BooleanField(
        default=True,
        verbose_name=_("Supports Quality Control"),
        help_text=_("Provides quality control information")
    )
    
    supports_critical_alerts = models.BooleanField(
        default=False,
        verbose_name=_("Supports Critical Alerts"),
        help_text=_("Can send critical result alerts")
    )
    
    # Service Capabilities
    test_categories = models.TextField(
        blank=True,
        verbose_name=_("Test Categories"),
        help_text=_("Comma-separated list of test categories offered")
    )
    
    turnaround_time_hours = models.PositiveIntegerField(
        default=24,
        verbose_name=_("Standard Turnaround Time (hours)"),
        help_text=_("Standard turnaround time for routine tests")
    )
    
    emergency_turnaround_hours = models.PositiveIntegerField(
        default=2,
        verbose_name=_("Emergency Turnaround Time (hours)"),
        help_text=_("Turnaround time for emergency tests")
    )
    
    # Contact Information
    contact_email = models.EmailField(
        blank=True,
        verbose_name=_("Contact Email"),
        help_text=_("Technical contact for integration")
    )
    
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Main contact phone number")
    )
    
    emergency_contact = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Emergency Contact"),
        help_text=_("24/7 emergency contact number")
    )
    
    # Status and Metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Laboratory is currently active")
    )
    
    is_24_hour = models.BooleanField(
        default=False,
        verbose_name=_("24 Hour Service"),
        help_text=_("Provides 24-hour services")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Pathology Laboratory")
        verbose_name_plural = _("Pathology Laboratories")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.lab_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('lab_type'),
            FieldPanel('lab_code'),
            FieldPanel('accreditation_type'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('province'),
            FieldPanel('city'),
            FieldPanel('address'),
        ], heading=_("Location")),
        
        MultiFieldPanel([
            FieldPanel('api_endpoint'),
            FieldPanel('api_key'),
            FieldPanel('lis_version'),
        ], heading=_("API Configuration")),
        
        MultiFieldPanel([
            FieldPanel('supports_result_retrieval'),
            FieldPanel('supports_test_ordering'),
            FieldPanel('supports_specimen_tracking'),
            FieldPanel('supports_quality_control'),
            FieldPanel('supports_critical_alerts'),
        ], heading=_("Integration Capabilities")),
        
        MultiFieldPanel([
            FieldPanel('test_categories'),
            FieldPanel('turnaround_time_hours'),
            FieldPanel('emergency_turnaround_hours'),
        ], heading=_("Service Capabilities")),
        
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('phone_number'),
            FieldPanel('emergency_contact'),
            FieldPanel('is_active'),
            FieldPanel('is_24_hour'),
        ], heading=_("Contact & Status")),
    ]
    
    def retrieve_test_results(self, patient_id: str, test_date: str = None, test_type: str = None) -> Dict[str, Any]:
        """
        Retrieve test results for a patient
        
        Args:
            patient_id: Patient identifier
            test_date: Optional date filter (YYYY-MM-DD format)
            test_type: Optional test type filter
            
        Returns:
            Dict containing test results
        """
        if not self.supports_result_retrieval or not self.is_active:
            return {'error': 'Result retrieval not supported or laboratory inactive'}
        
        cache_key = f"results_{self.lab_code}_{patient_id}_{test_date or 'all'}_{test_type or 'all'}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            params = {
                'patient': patient_id,
                'status': 'final'
            }
            
            if test_date:
                params['date'] = test_date
            if test_type:
                params['code'] = test_type
            
            response = requests.get(
                f"{self.api_endpoint}/DiagnosticReport",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 1 hour
                cache.set(cache_key, result, 3600)
                return result
            else:
                logger.error(f"Result retrieval failed for {self.name}: {response.status_code}")
                return {'error': f'Retrieval failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Result retrieval request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def submit_test_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Submit a test order to the laboratory
        
        Args:
            order_data: FHIR ServiceRequest resource data
            
        Returns:
            Dict with order submission status and tracking information
        """
        if not self.supports_test_ordering or not self.is_active:
            return {'error': 'Test ordering not supported or laboratory inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/ServiceRequest",
                headers=headers,
                json=order_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Test order submitted to {self.name}: {result.get('id')}")
                return result
            else:
                logger.error(f"Test order submission failed for {self.name}: {response.status_code}")
                return {'error': f'Submission failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Test order submission request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def track_specimen(self, specimen_id: str) -> Dict[str, Any]:
        """
        Track specimen status and location
        
        Args:
            specimen_id: Specimen identifier
            
        Returns:
            Dict containing specimen tracking information
        """
        if not self.supports_specimen_tracking or not self.is_active:
            return {'error': 'Specimen tracking not supported or laboratory inactive'}
        
        cache_key = f"specimen_{self.lab_code}_{specimen_id}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.get(
                f"{self.api_endpoint}/Specimen/{specimen_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 30 minutes
                cache.set(cache_key, result, 1800)
                return result
            else:
                logger.error(f"Specimen tracking failed for {self.name}: {response.status_code}")
                return {'error': f'Tracking failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Specimen tracking request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def get_quality_control_data(self, control_date: str = None) -> Dict[str, Any]:
        """
        Get quality control data and metrics
        
        Args:
            control_date: Optional date filter (YYYY-MM-DD format)
            
        Returns:
            Dict containing quality control information
        """
        if not self.supports_quality_control or not self.is_active:
            return {'error': 'Quality control not supported or laboratory inactive'}
        
        cache_key = f"qc_{self.lab_code}_{control_date or 'all'}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            params = {}
            if control_date:
                params['date'] = control_date
            
            response = requests.get(
                f"{self.api_endpoint}/quality-control",
                headers=headers,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 4 hours
                cache.set(cache_key, result, 14400)
                return result
            else:
                logger.error(f"Quality control data retrieval failed for {self.name}: {response.status_code}")
                return {'error': f'Retrieval failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Quality control request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def get_available_tests(self) -> Dict[str, Any]:
        """
        Get list of available tests and their details
        
        Returns:
            Dict containing available test catalog
        """
        cache_key = f"tests_{self.lab_code}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            return cached_result
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/fhir+json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.get(
                f"{self.api_endpoint}/test-catalog",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                # Cache for 24 hours (test catalog doesn't change frequently)
                cache.set(cache_key, result, 86400)
                return result
            else:
                logger.error(f"Test catalog retrieval failed for {self.name}: {response.status_code}")
                return {'error': f'Catalog retrieval failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Test catalog request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}


class PathologyLabAdmin(ModelAdmin):
    """Wagtail admin configuration for Pathology Laboratory management"""
    
    model = PathologyLab
    menu_label = _('Pathology Labs')
    menu_icon = 'fa-flask'
    menu_order = 104
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'lab_type', 'province', 'city', 'accreditation_type', 'is_active')
    list_filter = ('lab_type', 'province', 'accreditation_type', 'is_active', 'is_24_hour')
    search_fields = ('name', 'lab_code', 'city')


# Register the admin
modeladmin_register(PathologyLabAdmin)


# API Serializers for Pathology Lab Integration
class PathologyLabSerializer(serializers.ModelSerializer):
    """REST API serializer for PathologyLab model"""
    
    class Meta:
        model = PathologyLab
        fields = [
            'id', 'name', 'lab_type', 'lab_code', 'accreditation_type',
            'province', 'city', 'address', 'supports_result_retrieval',
            'supports_test_ordering', 'supports_specimen_tracking',
            'supports_quality_control', 'supports_critical_alerts',
            'test_categories', 'turnaround_time_hours', 'emergency_turnaround_hours',
            'contact_email', 'phone_number', 'emergency_contact',
            'is_active', 'is_24_hour'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Utility Functions for Pathology Lab Integration
def find_labs_by_location(province: str = None, city: str = None, lab_type: str = None) -> List[PathologyLab]:
    """Find pathology laboratories by location and type"""
    queryset = PathologyLab.objects.filter(is_active=True)
    
    if province:
        queryset = queryset.filter(province__icontains=province)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if lab_type:
        queryset = queryset.filter(lab_type=lab_type)
    
    return list(queryset.order_by('name'))


def get_lab_by_code(lab_code: str) -> Optional[PathologyLab]:
    """Get pathology laboratory by code"""
    try:
        return PathologyLab.objects.get(lab_code=lab_code, is_active=True)
    except PathologyLab.DoesNotExist:
        return None


def retrieve_results_across_labs(patient_id: str, test_date: str = None) -> Dict[str, Any]:
    """
    Retrieve test results across all active pathology laboratories
    
    Args:
        patient_id: Patient identifier
        test_date: Optional date filter
        
    Returns:
        Aggregated results from all laboratories
    """
    results = {
        'patient_id': patient_id,
        'test_date': test_date,
        'timestamp': datetime.now().isoformat(),
        'laboratories': {}
    }
    
    active_labs = PathologyLab.objects.filter(
        is_active=True,
        supports_result_retrieval=True
    )
    
    for lab in active_labs:
        results['laboratories'][lab.lab_code] = lab.retrieve_test_results(patient_id, test_date)
    
    return results


# =============================================================================
# 6. TELEMEDICINE PLATFORMS INTEGRATION
# =============================================================================

@register_snippet
class TelemedicinePlatform(models.Model):
    """
    Model representing telemedicine platforms in South Africa
    
    Provides integration capabilities for:
    - Virtual consultation scheduling and management
    - Video/audio call integration
    - Digital prescription and referral management
    - Remote patient monitoring
    - Teleconsultation records and documentation
    """
    
    PLATFORM_TYPES = [
        ('vula_mobile', _('Vula Mobile')),
        ('healthforce', _('HealthForce')),
        ('mediclinic_online', _('Mediclinic Online')),
        ('netcare_virtual', _('Netcare Virtual Care')),
        ('discovery_connect', _('Discovery Connect')),
        ('independent', _('Independent Platform')),
        ('hospital_platform', _('Hospital Platform')),
        ('specialized', _('Specialized Platform')),
    ]
    
    CONSULTATION_TYPES = [
        ('video', _('Video Consultation')),
        ('audio', _('Audio Only')),
        ('chat', _('Chat/Messaging')),
        ('hybrid', _('Hybrid (Multiple Methods)')),
    ]
    
    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name=_("Platform Name"),
        help_text=_("e.g., Vula Mobile, Mediclinic Online")
    )
    
    platform_type = models.CharField(
        max_length=50,
        choices=PLATFORM_TYPES,
        verbose_name=_("Platform Type"),
        help_text=_("Type of telemedicine platform")
    )
    
    platform_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Platform Code"),
        help_text=_("Unique identifier for the platform")
    )
    
    # API Configuration
    api_endpoint = models.URLField(
        verbose_name=_("API Endpoint"),
        help_text=_("Base URL for telemedicine platform API")
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("API Key"),
        help_text=_("Authentication key for API access")
    )
    
    webhook_url = models.URLField(
        blank=True,
        verbose_name=_("Webhook URL"),
        help_text=_("URL for receiving platform webhooks")
    )
    
    # Integration Capabilities
    supports_video_calls = models.BooleanField(
        default=True,
        verbose_name=_("Supports Video Calls"),
        help_text=_("Platform supports video consultations")
    )
    
    supports_audio_calls = models.BooleanField(
        default=True,
        verbose_name=_("Supports Audio Calls"),
        help_text=_("Platform supports audio-only consultations")
    )
    
    supports_chat = models.BooleanField(
        default=False,
        verbose_name=_("Supports Chat"),
        help_text=_("Platform supports text-based consultations")
    )
    
    supports_scheduling = models.BooleanField(
        default=True,
        verbose_name=_("Supports Scheduling"),
        help_text=_("Can schedule consultations in advance")
    )
    
    supports_prescriptions = models.BooleanField(
        default=False,
        verbose_name=_("Supports Digital Prescriptions"),
        help_text=_("Can issue digital prescriptions")
    )
    
    supports_referrals = models.BooleanField(
        default=False,
        verbose_name=_("Supports Digital Referrals"),
        help_text=_("Can issue digital referrals")
    )
    
    supports_monitoring = models.BooleanField(
        default=False,
        verbose_name=_("Supports Remote Monitoring"),
        help_text=_("Supports remote patient monitoring")
    )
    
    # Service Configuration
    consultation_types = models.CharField(
        max_length=50,
        choices=CONSULTATION_TYPES,
        default='hybrid',
        verbose_name=_("Consultation Types"),
        help_text=_("Types of consultations supported")
    )
    
    max_session_duration = models.PositiveIntegerField(
        default=60,
        verbose_name=_("Max Session Duration (minutes)"),
        help_text=_("Maximum duration for consultation sessions")
    )
    
    supported_specialties = models.TextField(
        blank=True,
        verbose_name=_("Supported Specialties"),
        help_text=_("Comma-separated list of medical specialties")
    )
    
    # Quality and Compliance
    is_hipaa_compliant = models.BooleanField(
        default=False,
        verbose_name=_("HIPAA Compliant"),
        help_text=_("Platform meets HIPAA compliance standards")
    )
    
    is_popi_compliant = models.BooleanField(
        default=True,
        verbose_name=_("POPI Act Compliant"),
        help_text=_("Platform complies with SA POPI Act")
    )
    
    encryption_level = models.CharField(
        max_length=50,
        default='AES-256',
        verbose_name=_("Encryption Level"),
        help_text=_("Data encryption standard used")
    )
    
    # Contact Information
    contact_email = models.EmailField(
        blank=True,
        verbose_name=_("Contact Email"),
        help_text=_("Technical contact for integration")
    )
    
    support_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Support Phone"),
        help_text=_("Technical support phone number")
    )
    
    emergency_support = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Emergency Support"),
        help_text=_("Emergency technical support contact")
    )
    
    # Status and Metadata
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Platform is currently active")
    )
    
    is_24_hour = models.BooleanField(
        default=False,
        verbose_name=_("24 Hour Service"),
        help_text=_("Platform available 24/7")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Telemedicine Platform")
        verbose_name_plural = _("Telemedicine Platforms")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.platform_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'),
            FieldPanel('platform_type'),
            FieldPanel('platform_code'),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel('api_endpoint'),
            FieldPanel('api_key'),
            FieldPanel('webhook_url'),
        ], heading=_("API Configuration")),
        
        MultiFieldPanel([
            FieldPanel('supports_video_calls'),
            FieldPanel('supports_audio_calls'),
            FieldPanel('supports_chat'),
            FieldPanel('supports_scheduling'),
            FieldPanel('supports_prescriptions'),
            FieldPanel('supports_referrals'),
            FieldPanel('supports_monitoring'),
        ], heading=_("Integration Capabilities")),
        
        MultiFieldPanel([
            FieldPanel('consultation_types'),
            FieldPanel('max_session_duration'),
            FieldPanel('supported_specialties'),
        ], heading=_("Service Configuration")),
        
        MultiFieldPanel([
            FieldPanel('is_hipaa_compliant'),
            FieldPanel('is_popi_compliant'),
            FieldPanel('encryption_level'),
        ], heading=_("Quality & Compliance")),
        
        MultiFieldPanel([
            FieldPanel('contact_email'),
            FieldPanel('support_phone'),
            FieldPanel('emergency_support'),
            FieldPanel('is_active'),
            FieldPanel('is_24_hour'),
        ], heading=_("Contact & Status")),
    ]
    
    def schedule_consultation(self, consultation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Schedule a telemedicine consultation
        
        Args:
            consultation_data: Dictionary containing consultation details
            
        Returns:
            Dict with scheduling confirmation and session details
        """
        if not self.supports_scheduling or not self.is_active:
            return {'error': 'Consultation scheduling not supported or platform inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/consultations/schedule",
                headers=headers,
                json=consultation_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Consultation scheduled on {self.name}: {result.get('session_id')}")
                return result
            else:
                logger.error(f"Consultation scheduling failed for {self.name}: {response.status_code}")
                return {'error': f'Scheduling failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Consultation scheduling request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}
    
    def issue_digital_prescription(self, prescription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Issue a digital prescription through the platform
        
        Args:
            prescription_data: Dictionary containing prescription details
            
        Returns:
            Dict with prescription issuance status and reference
        """
        if not self.supports_prescriptions or not self.is_active:
            return {'error': 'Digital prescriptions not supported or platform inactive'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'MedGuard-SA/1.0'
            }
            
            response = requests.post(
                f"{self.api_endpoint}/prescriptions/issue",
                headers=headers,
                json=prescription_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Digital prescription issued on {self.name}: {result.get('prescription_id')}")
                return result
            else:
                logger.error(f"Prescription issuance failed for {self.name}: {response.status_code}")
                return {'error': f'Issuance failed: {response.status_code}'}
                
        except requests.RequestException as e:
            logger.error(f"Prescription issuance request failed for {self.name}: {str(e)}")
            return {'error': f'Request failed: {str(e)}'}


class TelemedicinePlatformAdmin(ModelAdmin):
    """Wagtail admin configuration for Telemedicine Platform management"""
    
    model = TelemedicinePlatform
    menu_label = _('Telemedicine Platforms')
    menu_icon = 'fa-video'
    menu_order = 105
    add_to_settings_menu = False
    exclude_from_explorer = False
    list_display = ('name', 'platform_type', 'supports_video_calls', 'supports_prescriptions', 'is_active')
    list_filter = ('platform_type', 'is_active', 'supports_video_calls', 'supports_prescriptions', 'is_24_hour')
    search_fields = ('name', 'platform_code')


# Register the admin
modeladmin_register(TelemedicinePlatformAdmin)


# =============================================================================
# 7. MEDICAL DEVICE MANUFACTURERS INTEGRATION
# =============================================================================

@register_snippet
class MedicalDeviceManufacturer(models.Model):
    """
    Model representing medical device manufacturers
    
    Provides integration capabilities for:
    - Device inventory and availability
    - Maintenance and calibration scheduling
    - Warranty and service tracking
    - Compliance and certification verification
    - Remote monitoring and diagnostics
    """
    
    MANUFACTURER_TYPES = [
        ('global', _('Global Manufacturer')),
        ('local', _('Local Manufacturer')),
        ('distributor', _('Local Distributor')),
        ('service_provider', _('Service Provider')),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, verbose_name=_("Manufacturer Name"))
    manufacturer_code = models.CharField(max_length=50, unique=True, verbose_name=_("Manufacturer Code"))
    manufacturer_type = models.CharField(max_length=50, choices=MANUFACTURER_TYPES, verbose_name=_("Type"))
    
    # API Configuration
    api_endpoint = models.URLField(verbose_name=_("API Endpoint"))
    api_key = models.CharField(max_length=255, blank=True, verbose_name=_("API Key"))
    
    # Integration Capabilities
    supports_inventory = models.BooleanField(default=True, verbose_name=_("Supports Inventory"))
    supports_maintenance = models.BooleanField(default=False, verbose_name=_("Supports Maintenance"))
    supports_monitoring = models.BooleanField(default=False, verbose_name=_("Supports Remote Monitoring"))
    
    # Contact Information
    contact_email = models.EmailField(blank=True, verbose_name=_("Contact Email"))
    support_phone = models.CharField(max_length=20, blank=True, verbose_name=_("Support Phone"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Medical Device Manufacturer")
        verbose_name_plural = _("Medical Device Manufacturers")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.manufacturer_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'), FieldPanel('manufacturer_code'), FieldPanel('manufacturer_type'),
        ], heading=_("Basic Information")),
        MultiFieldPanel([
            FieldPanel('api_endpoint'), FieldPanel('api_key'),
        ], heading=_("API Configuration")),
        MultiFieldPanel([
            FieldPanel('supports_inventory'), FieldPanel('supports_maintenance'), FieldPanel('supports_monitoring'),
        ], heading=_("Capabilities")),
        MultiFieldPanel([
            FieldPanel('contact_email'), FieldPanel('support_phone'), FieldPanel('is_active'),
        ], heading=_("Contact & Status")),
    ]
    
    def check_device_inventory(self, device_model: str) -> Dict[str, Any]:
        """Check device inventory and availability"""
        if not self.supports_inventory or not self.is_active:
            return {'error': 'Inventory checking not supported'}
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}', 'User-Agent': 'MedGuard-SA/1.0'}
            response = requests.get(f"{self.api_endpoint}/inventory/{device_model}", headers=headers, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'API error: {response.status_code}'}
        except requests.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def schedule_maintenance(self, maintenance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule device maintenance"""
        if not self.supports_maintenance or not self.is_active:
            return {'error': 'Maintenance scheduling not supported'}
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            response = requests.post(f"{self.api_endpoint}/maintenance/schedule", 
                                   headers=headers, json=maintenance_data, timeout=30)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {'error': f'Scheduling failed: {response.status_code}'}
        except requests.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}


class MedicalDeviceManufacturerAdmin(ModelAdmin):
    model = MedicalDeviceManufacturer
    menu_label = _('Device Manufacturers')
    menu_icon = 'fa-cogs'
    menu_order = 106
    list_display = ('name', 'manufacturer_type', 'supports_inventory', 'is_active')
    list_filter = ('manufacturer_type', 'is_active')
    search_fields = ('name', 'manufacturer_code')

modeladmin_register(MedicalDeviceManufacturerAdmin)


# =============================================================================
# 8. HEALTHCARE ANALYTICS PLATFORMS INTEGRATION
# =============================================================================

@register_snippet
class HealthcareAnalyticsPlatform(models.Model):
    """
    Model representing healthcare analytics platforms
    
    Provides integration capabilities for:
    - Clinical data analytics and reporting
    - Population health insights
    - Predictive analytics and AI
    - Quality metrics and KPIs
    - Research data aggregation
    """
    
    PLATFORM_TYPES = [
        ('business_intelligence', _('Business Intelligence')),
        ('clinical_analytics', _('Clinical Analytics')),
        ('population_health', _('Population Health')),
        ('ai_ml', _('AI/ML Platform')),
        ('quality_metrics', _('Quality Metrics')),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, verbose_name=_("Platform Name"))
    platform_code = models.CharField(max_length=50, unique=True, verbose_name=_("Platform Code"))
    platform_type = models.CharField(max_length=50, choices=PLATFORM_TYPES, verbose_name=_("Platform Type"))
    
    # API Configuration
    api_endpoint = models.URLField(verbose_name=_("API Endpoint"))
    api_key = models.CharField(max_length=255, blank=True, verbose_name=_("API Key"))
    
    # Integration Capabilities
    supports_real_time = models.BooleanField(default=False, verbose_name=_("Real-time Analytics"))
    supports_predictive = models.BooleanField(default=False, verbose_name=_("Predictive Analytics"))
    supports_reporting = models.BooleanField(default=True, verbose_name=_("Reporting"))
    
    # Contact Information
    contact_email = models.EmailField(blank=True, verbose_name=_("Contact Email"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Healthcare Analytics Platform")
        verbose_name_plural = _("Healthcare Analytics Platforms")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.platform_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'), FieldPanel('platform_code'), FieldPanel('platform_type'),
        ], heading=_("Basic Information")),
        MultiFieldPanel([
            FieldPanel('api_endpoint'), FieldPanel('api_key'),
        ], heading=_("API Configuration")),
        MultiFieldPanel([
            FieldPanel('supports_real_time'), FieldPanel('supports_predictive'), FieldPanel('supports_reporting'),
        ], heading=_("Capabilities")),
        MultiFieldPanel([
            FieldPanel('contact_email'), FieldPanel('is_active'),
        ], heading=_("Contact & Status")),
    ]
    
    def generate_report(self, report_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analytics report"""
        if not self.supports_reporting or not self.is_active:
            return {'error': 'Reporting not supported'}
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            response = requests.post(f"{self.api_endpoint}/reports/generate", 
                                   headers=headers, json=report_params, timeout=60)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {'error': f'Report generation failed: {response.status_code}'}
        except requests.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}


class HealthcareAnalyticsPlatformAdmin(ModelAdmin):
    model = HealthcareAnalyticsPlatform
    menu_label = _('Analytics Platforms')
    menu_icon = 'fa-chart-bar'
    menu_order = 107
    list_display = ('name', 'platform_type', 'supports_real_time', 'is_active')
    list_filter = ('platform_type', 'is_active')
    search_fields = ('name', 'platform_code')

modeladmin_register(HealthcareAnalyticsPlatformAdmin)


# =============================================================================
# 9. EMERGENCY MEDICAL SERVICES INTEGRATION
# =============================================================================

@register_snippet
class EmergencyMedicalService(models.Model):
    """
    Model representing emergency medical services
    
    Provides integration capabilities for:
    - Emergency dispatch and coordination
    - Ambulance tracking and status
    - Hospital capacity and availability
    - Critical alert management
    - Resource allocation and optimization
    """
    
    SERVICE_TYPES = [
        ('public_ems', _('Public EMS')),
        ('private_ems', _('Private EMS')),
        ('hospital_ems', _('Hospital EMS')),
        ('air_rescue', _('Air Rescue')),
        ('specialized', _('Specialized Service')),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, verbose_name=_("Service Name"))
    service_code = models.CharField(max_length=50, unique=True, verbose_name=_("Service Code"))
    service_type = models.CharField(max_length=50, choices=SERVICE_TYPES, verbose_name=_("Service Type"))
    
    # Location
    province = models.CharField(max_length=50, verbose_name=_("Province"))
    coverage_area = models.TextField(verbose_name=_("Coverage Area"))
    
    # API Configuration
    api_endpoint = models.URLField(verbose_name=_("API Endpoint"))
    api_key = models.CharField(max_length=255, blank=True, verbose_name=_("API Key"))
    
    # Integration Capabilities
    supports_dispatch = models.BooleanField(default=True, verbose_name=_("Supports Dispatch"))
    supports_tracking = models.BooleanField(default=False, verbose_name=_("Supports Tracking"))
    supports_alerts = models.BooleanField(default=True, verbose_name=_("Supports Alerts"))
    
    # Contact Information
    emergency_number = models.CharField(max_length=20, verbose_name=_("Emergency Number"))
    dispatch_center = models.CharField(max_length=20, blank=True, verbose_name=_("Dispatch Center"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_24_hour = models.BooleanField(default=True, verbose_name=_("24 Hour Service"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Emergency Medical Service")
        verbose_name_plural = _("Emergency Medical Services")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.service_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'), FieldPanel('service_code'), FieldPanel('service_type'),
        ], heading=_("Basic Information")),
        MultiFieldPanel([
            FieldPanel('province'), FieldPanel('coverage_area'),
        ], heading=_("Coverage")),
        MultiFieldPanel([
            FieldPanel('api_endpoint'), FieldPanel('api_key'),
        ], heading=_("API Configuration")),
        MultiFieldPanel([
            FieldPanel('supports_dispatch'), FieldPanel('supports_tracking'), FieldPanel('supports_alerts'),
        ], heading=_("Capabilities")),
        MultiFieldPanel([
            FieldPanel('emergency_number'), FieldPanel('dispatch_center'), 
            FieldPanel('is_active'), FieldPanel('is_24_hour'),
        ], heading=_("Contact & Status")),
    ]
    
    def dispatch_emergency(self, emergency_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch emergency response"""
        if not self.supports_dispatch or not self.is_active:
            return {'error': 'Emergency dispatch not supported'}
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            response = requests.post(f"{self.api_endpoint}/dispatch", 
                                   headers=headers, json=emergency_data, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                logger.critical(f"Emergency dispatched via {self.name}: {result.get('dispatch_id')}")
                return result
            else:
                return {'error': f'Dispatch failed: {response.status_code}'}
        except requests.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}


class EmergencyMedicalServiceAdmin(ModelAdmin):
    model = EmergencyMedicalService
    menu_label = _('Emergency Services')
    menu_icon = 'fa-ambulance'
    menu_order = 108
    list_display = ('name', 'service_type', 'province', 'is_24_hour', 'is_active')
    list_filter = ('service_type', 'province', 'is_active', 'is_24_hour')
    search_fields = ('name', 'service_code', 'emergency_number')

modeladmin_register(EmergencyMedicalServiceAdmin)


# =============================================================================
# 10. HEALTHCARE COMPLIANCE MONITORING SYSTEMS INTEGRATION
# =============================================================================

@register_snippet
class ComplianceMonitoringSystem(models.Model):
    """
    Model representing healthcare compliance monitoring systems
    
    Provides integration capabilities for:
    - Regulatory compliance tracking
    - Audit trail management
    - Policy adherence monitoring
    - Risk assessment and reporting
    - Certification and accreditation tracking
    """
    
    SYSTEM_TYPES = [
        ('regulatory', _('Regulatory Compliance')),
        ('quality', _('Quality Assurance')),
        ('safety', _('Safety Monitoring')),
        ('privacy', _('Privacy Compliance')),
        ('audit', _('Audit Management')),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200, verbose_name=_("System Name"))
    system_code = models.CharField(max_length=50, unique=True, verbose_name=_("System Code"))
    system_type = models.CharField(max_length=50, choices=SYSTEM_TYPES, verbose_name=_("System Type"))
    
    # API Configuration
    api_endpoint = models.URLField(verbose_name=_("API Endpoint"))
    api_key = models.CharField(max_length=255, blank=True, verbose_name=_("API Key"))
    
    # Integration Capabilities
    supports_real_time = models.BooleanField(default=True, verbose_name=_("Real-time Monitoring"))
    supports_reporting = models.BooleanField(default=True, verbose_name=_("Compliance Reporting"))
    supports_alerts = models.BooleanField(default=True, verbose_name=_("Compliance Alerts"))
    
    # Configuration
    monitoring_frequency = models.CharField(max_length=50, default='daily', verbose_name=_("Monitoring Frequency"))
    alert_threshold = models.CharField(max_length=50, default='medium', verbose_name=_("Alert Threshold"))
    
    # Contact Information
    contact_email = models.EmailField(blank=True, verbose_name=_("Contact Email"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Compliance Monitoring System")
        verbose_name_plural = _("Compliance Monitoring Systems")
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.system_code})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel('name'), FieldPanel('system_code'), FieldPanel('system_type'),
        ], heading=_("Basic Information")),
        MultiFieldPanel([
            FieldPanel('api_endpoint'), FieldPanel('api_key'),
        ], heading=_("API Configuration")),
        MultiFieldPanel([
            FieldPanel('supports_real_time'), FieldPanel('supports_reporting'), FieldPanel('supports_alerts'),
        ], heading=_("Capabilities")),
        MultiFieldPanel([
            FieldPanel('monitoring_frequency'), FieldPanel('alert_threshold'),
        ], heading=_("Configuration")),
        MultiFieldPanel([
            FieldPanel('contact_email'), FieldPanel('is_active'),
        ], heading=_("Contact & Status")),
    ]
    
    def check_compliance_status(self, entity_id: str, compliance_type: str) -> Dict[str, Any]:
        """Check compliance status for an entity"""
        if not self.is_active:
            return {'error': 'System inactive'}
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            data = {'entity_id': entity_id, 'compliance_type': compliance_type}
            response = requests.post(f"{self.api_endpoint}/compliance/check", 
                                   headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'Compliance check failed: {response.status_code}'}
        except requests.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def generate_compliance_report(self, report_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate compliance report"""
        if not self.supports_reporting or not self.is_active:
            return {'error': 'Compliance reporting not supported'}
        
        try:
            headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
            response = requests.post(f"{self.api_endpoint}/reports/compliance", 
                                   headers=headers, json=report_params, timeout=60)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {'error': f'Report generation failed: {response.status_code}'}
        except requests.RequestException as e:
            return {'error': f'Request failed: {str(e)}'}


class ComplianceMonitoringSystemAdmin(ModelAdmin):
    model = ComplianceMonitoringSystem
    menu_label = _('Compliance Systems')
    menu_icon = 'fa-shield-check'
    menu_order = 109
    list_display = ('name', 'system_type', 'supports_real_time', 'is_active')
    list_filter = ('system_type', 'is_active')
    search_fields = ('name', 'system_code')

modeladmin_register(ComplianceMonitoringSystemAdmin)
