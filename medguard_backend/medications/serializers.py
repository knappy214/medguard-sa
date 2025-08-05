"""
Serializers for medications app.

This module contains DRF serializers for the medication models with comprehensive
prescription handling, validation, and compliance features.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta, time
from django.db.models import F, Q
from django.db import transaction
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from .models import (
    Medication, MedicationSchedule, MedicationLog, StockAlert,
    StockAnalytics, StockVisualization, PharmacyIntegration,
    StockTransaction, PrescriptionRenewal
)

# Import audit logging
try:
    from security.audit import AuditLog
    AUDIT_ENABLED = True
except ImportError:
    AUDIT_ENABLED = False
    AuditLog = None

User = get_user_model()
logger = logging.getLogger(__name__)


class ICD10Validator:
    """
    Enhanced validator for ICD-10 codes with comprehensive mapping.
    
    ICD-10 codes follow the pattern: [A-Z][0-9][0-9].[0-9X][0-9X]?
    Examples: A00.0, B01.1, C78.01, Z51.11
    """
    
    ICD10_PATTERN = re.compile(r'^[A-Z][0-9][0-9]\.[0-9X][0-9X]?$')
    
    # Comprehensive ICD-10 code mappings for South African healthcare
    ICD10_MAPPINGS = {
        # Diabetes mellitus
        'E10.4': 'Type 1 diabetes mellitus with neurological complications',
        'E11.4': 'Type 2 diabetes mellitus with neurological complications',
        'E11.9': 'Type 2 diabetes mellitus without complications',
        'E10.9': 'Type 1 diabetes mellitus without complications',
        'E13.4': 'Other specified diabetes mellitus with neurological complications',
        
        # Mental and behavioral disorders
        'F90.9': 'Attention-deficit hyperactivity disorder, unspecified type',
        'F90.0': 'Attention-deficit hyperactivity disorder, predominantly inattentive type',
        'F90.1': 'Attention-deficit hyperactivity disorder, predominantly hyperactive type',
        'F32.9': 'Major depressive disorder, unspecified',
        'F41.9': 'Anxiety disorder, unspecified',
        'F33.9': 'Major depressive disorder, recurrent, unspecified',
        'F31.9': 'Bipolar affective disorder, unspecified',
        
        # Cardiovascular diseases
        'I10': 'Essential (primary) hypertension',
        'I11.9': 'Hypertensive heart disease without heart failure',
        'I12.9': 'Hypertensive chronic kidney disease with stage 1 through stage 4 chronic kidney disease',
        'I25.10': 'Atherosclerotic heart disease of native coronary artery without angina pectoris',
        'I48.91': 'Unspecified atrial fibrillation',
        
        # Respiratory diseases
        'J45.901': 'Unspecified asthma with (acute) exacerbation',
        'J44.9': 'Chronic obstructive pulmonary disease, unspecified',
        'J45.909': 'Unspecified asthma, uncomplicated',
        'J45.990': 'Exercise induced bronchospasm',
        
        # Pain and musculoskeletal
        'M79.3': 'Sciatica, unspecified side',
        'R52.9': 'Pain, unspecified',
        'M54.5': 'Low back pain',
        'M79.1': 'Myalgia',
        
        # Infections
        'N39.0': 'Urinary tract infection, site not specified',
        'A09.9': 'Infectious gastroenteritis and colitis, unspecified',
        'J06.9': 'Acute upper respiratory infection, unspecified',
        
        # Other common conditions
        'Z51.11': 'Encounter for antineoplastic chemotherapy',
        'Z79.4': 'Long term (current) use of insulin',
        'Z79.899': 'Other long term (current) drug therapy',
        'Z00.00': 'Encounter for general adult medical examination without abnormal findings',
    }
    
    @classmethod
    def validate(cls, value: str) -> bool:
        """Validate ICD-10 code format."""
        if not value:
            return True
        return bool(cls.ICD10_PATTERN.match(value.strip().upper()))
    
    @classmethod
    def clean(cls, value: str) -> str:
        """Clean and standardize ICD-10 code."""
        if not value:
            return value
        return value.strip().upper()
    
    @classmethod
    def get_description(cls, code: str) -> Optional[str]:
        """Get description for ICD-10 code."""
        return cls.ICD10_MAPPINGS.get(code.upper())
    
    @classmethod
    def get_category(cls, code: str) -> str:
        """Get category for ICD-10 code."""
        if not code:
            return 'Unknown'
        
        code_upper = code.upper()
        if code_upper.startswith('E'):
            return 'Endocrine, nutritional and metabolic diseases'
        elif code_upper.startswith('F'):
            return 'Mental and behavioral disorders'
        elif code_upper.startswith('I'):
            return 'Diseases of the circulatory system'
        elif code_upper.startswith('J'):
            return 'Diseases of the respiratory system'
        elif code_upper.startswith('M'):
            return 'Diseases of the musculoskeletal system and connective tissue'
        elif code_upper.startswith('N'):
            return 'Diseases of the genitourinary system'
        elif code_upper.startswith('R'):
            return 'Symptoms, signs and abnormal clinical and laboratory findings'
        elif code_upper.startswith('Z'):
            return 'Factors influencing health status and contact with health services'
        elif code_upper.startswith('A'):
            return 'Certain infectious and parasitic diseases'
        else:
            return 'Other'


class StrengthUnitNormalizer:
    """
    Normalizer for medication strength units with comprehensive mapping.
    """
    
    # Unit mappings for normalization
    UNIT_MAPPINGS = {
        # Weight units
        'mg': 'mg',
        'milligram': 'mg',
        'milligrams': 'mg',
        'mcg': 'mcg',
        'microgram': 'mcg',
        'micrograms': 'mcg',
        'μg': 'mcg',
        'g': 'g',
        'gram': 'g',
        'grams': 'g',
        
        # Volume units
        'ml': 'ml',
        'milliliter': 'ml',
        'milliliters': 'ml',
        'l': 'l',
        'liter': 'l',
        'liters': 'l',
        
        # Insulin units
        'units': 'units',
        'unit': 'units',
        'iu': 'IU',
        'international units': 'IU',
        'international unit': 'IU',
        
        # Concentration units
        'mg/ml': 'mg/ml',
        'mcg/ml': 'mcg/ml',
        'g/ml': 'g/ml',
        'units/ml': 'units/ml',
        'iu/ml': 'IU/ml',
        
        # Other units
        'meq': 'mEq',
        'milliequivalent': 'mEq',
        'mmol': 'mmol',
        'millimole': 'mmol',
        '%': '%',
        'percent': '%',
        'billion cfu': 'billion CFU',
        'cfu': 'CFU',
    }
    
    @classmethod
    def normalize_unit(cls, unit: str) -> str:
        """Normalize strength unit to standard format."""
        if not unit:
            return unit
        
        unit_lower = unit.lower().strip()
        return cls.UNIT_MAPPINGS.get(unit_lower, unit)
    
    @classmethod
    def normalize_strength(cls, strength: str) -> str:
        """Normalize complete strength string."""
        if not strength:
            return strength
        
        # Extract number and unit
        match = re.match(r'^(\d+(?:\.\d+)?)\s*(.+)$', strength.strip())
        if not match:
            return strength
        
        number, unit = match.groups()
        normalized_unit = cls.normalize_unit(unit)
        return f"{number}{normalized_unit}"
    
    @classmethod
    def validate_strength_format(cls, strength: str) -> bool:
        """Validate strength format."""
        if not strength:
            return False
        
        # Pattern for valid strength formats
        pattern = re.compile(
            r'^\d+(?:\.\d+)?\s*(mg|mcg|g|ml|l|units?|iu|meq|mmol|%|mg/ml|mcg/ml|g/ml|units/ml|iu/ml|billion\s+cfu|cfu)$',
            re.IGNORECASE
        )
        return bool(pattern.match(strength.strip()))


class SouthAfricanManufacturerValidator:
    """
    Validator for South African pharmaceutical manufacturers.
    """
    
    # Major South African pharmaceutical manufacturers
    VALID_MANUFACTURERS = {
        # International companies with SA presence
        'Novo Nordisk': 'Novo Nordisk South Africa',
        'Sanofi-Aventis': 'Sanofi-Aventis South Africa',
        'Pfizer': 'Pfizer South Africa',
        'GlaxoSmithKline': 'GSK South Africa',
        'AstraZeneca': 'AstraZeneca South Africa',
        'Bayer': 'Bayer South Africa',
        'Merck': 'Merck South Africa',
        'Roche': 'Roche South Africa',
        'Eli Lilly': 'Eli Lilly South Africa',
        'Boehringer Ingelheim': 'Boehringer Ingelheim South Africa',
        
        # South African companies
        'Aspen Pharmacare': 'Aspen Pharmacare Holdings',
        'Adcock Ingram': 'Adcock Ingram Holdings',
        'Dis-Chem': 'Dis-Chem Pharmacies',
        'Clicks': 'Clicks Group',
        'Mediclinic': 'Mediclinic International',
        'Netcare': 'Netcare Limited',
        'Life Healthcare': 'Life Healthcare Group',
        'Discovery Health': 'Discovery Health',
        'Momentum Health': 'Momentum Health',
        'Bonitas Medical Fund': 'Bonitas Medical Fund',
        
        # Generic manufacturers
        'Cipla': 'Cipla South Africa',
        'Ranbaxy': 'Ranbaxy South Africa',
        'Dr Reddy\'s': 'Dr Reddy\'s Laboratories South Africa',
        'Sun Pharmaceutical': 'Sun Pharmaceutical Industries South Africa',
        'Lupin': 'Lupin South Africa',
        
        # Local manufacturers
        'Pharma Dynamics': 'Pharma Dynamics South Africa',
        'Sandoz': 'Sandoz South Africa',
        'Mylan': 'Mylan South Africa',
        'Teva': 'Teva Pharmaceutical Industries South Africa',
        'Fresenius Kabi': 'Fresenius Kabi South Africa',
    }
    
    @classmethod
    def validate_manufacturer(cls, manufacturer: str) -> bool:
        """Validate if manufacturer is recognized."""
        if not manufacturer:
            return True
        
        manufacturer_lower = manufacturer.lower().strip()
        return any(
            valid.lower() in manufacturer_lower or manufacturer_lower in valid.lower()
            for valid in cls.VALID_MANUFACTURERS.keys()
        )
    
    @classmethod
    def get_standardized_name(cls, manufacturer: str) -> str:
        """Get standardized manufacturer name."""
        if not manufacturer:
            return manufacturer
        
        manufacturer_lower = manufacturer.lower().strip()
        for valid, standardized in cls.VALID_MANUFACTURERS.items():
            if valid.lower() in manufacturer_lower or manufacturer_lower in valid.lower():
                return standardized
        
        return manufacturer.strip()
    
    @classmethod
    def get_manufacturer_type(cls, manufacturer: str) -> str:
        """Get manufacturer type (international, local, generic)."""
        if not manufacturer:
            return 'Unknown'
        
        manufacturer_lower = manufacturer.lower().strip()
        
        # International companies
        international = ['novo nordisk', 'sanofi', 'pfizer', 'gsk', 'astrazeneca', 'bayer', 'merck', 'roche']
        if any(company in manufacturer_lower for company in international):
            return 'International'
        
        # South African companies
        sa_companies = ['aspen', 'adcock', 'dis-chem', 'clicks', 'mediclinic', 'netcare', 'life healthcare']
        if any(company in manufacturer_lower for company in sa_companies):
            return 'South African'
        
        # Generic manufacturers
        generic = ['cipla', 'ranbaxy', 'dr reddy', 'sun pharmaceutical', 'lupin', 'sandoz', 'mylan', 'teva']
        if any(company in manufacturer_lower for company in generic):
            return 'Generic'
        
        return 'Other'


class PrescriptionParser:
    """
    Enhanced parser for prescription instructions with comprehensive pattern recognition.
    
    Handles common prescription patterns like:
    - "Take one tablet daily"
    - "Take two tablets at 12h00"
    - "Take 1 capsule three times daily"
    - "Take 2 tablets morning and evening"
    - "Inject 20 units once daily at bedtime"
    """
    
    # Enhanced dosage patterns
    DOSAGE_PATTERNS = [
        r'take\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(tablets|capsules|drops|puffs|tablet|capsule|drop|puff|ml|mg|mcg|units)',
        r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(tablets|capsules|drops|puffs|tablet|capsule|drop|puff|ml|mg|mcg|units)\s+(?:to\s+)?take',
        r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(tablets|capsules|drops|puffs|tablet|capsule|drop|puff|ml|mg|mcg|units)\s+(?:per\s+)?dose',
        r'inject\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(units|ml|mg)',
        r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(units|ml|mg)\s+(?:to\s+)?inject',
    ]
    
    # Enhanced frequency patterns
    FREQUENCY_PATTERNS = [
        (r'four\s+times\s+daily|4x\s+daily|qid', 'four_times_daily'),
        (r'three\s+times\s+daily|thrice\s+daily|3x\s+daily|tid', 'three_times_daily'),
        (r'twice\s+daily|two\s+times\s+daily|2x\s+daily|bid', 'twice_daily'),
        (r'weekly|once\s+a\s+week|qw', 'weekly'),
        (r'monthly|once\s+a\s+month', 'monthly'),
        (r'as\s+needed|prn|when\s+needed|when\s+required', 'as_needed'),
        (r'daily|once\s+a\s+day|every\s+day|qd', 'daily'),
        (r'every\s+(\d+)\s+hours?', 'custom_hours'),
        (r'every\s+(\d+)\s+days?', 'custom_days'),
    ]
    
    # Enhanced time patterns
    TIME_PATTERNS = [
        (r'(\d{1,2})h(\d{2})?|(\d{1,2}):(\d{2})', 'custom'),
        (r'morning|am|before\s+breakfast|with\s+breakfast', 'morning'),
        (r'noon|midday|12h00|12:00|with\s+lunch', 'noon'),
        (r'evening|pm|before\s+bed|night|at\s+bedtime|with\s+dinner', 'night'),
        (r'before\s+meals|ac\s+\(ante\s+cibum\)', 'before_meals'),
        (r'with\s+meals|pc\s+\(post\s+cibum\)', 'with_meals'),
        (r'after\s+meals', 'after_meals'),
    ]
    
    # Multi-time pattern for instructions like "at 8h00 and 20h00" or "at 8h00, 14h00 and 20h00"
    MULTI_TIME_PATTERN = r'at\s+((?:\d{1,2}h\d{2}|\d{1,2}:\d{2})\s*(?:[,]\s*|\s+and\s+)\s*(?:\d{1,2}h\d{2}|\d{1,2}:\d{2})(?:\s*(?:[,]\s*|\s+and\s+)\s*(?:\d{1,2}h\d{2}|\d{1,2}:\d{2}))*)'
    
    @classmethod
    def parse_instructions(cls, instructions: str) -> Dict:
        """
        Parse prescription instructions to extract structured data.
        
        Returns:
            Dict containing:
            - dosage_amount: Decimal
            - dosage_unit: str
            - frequency: str
            - timing: str
            - custom_time: time object (if applicable)
            - custom_times: List of time objects (for multi-time instructions)
            - schedules: List of schedule configurations
            - parsed_confidence: float (0-1)
            - parsing_errors: List[str]
        """
        if not instructions:
            return {}
        
        instructions_lower = instructions.lower().strip()
        result = {
            'dosage_amount': None,
            'dosage_unit': None,
            'frequency': 'daily',
            'timing': 'morning',
            'custom_time': None,
            'custom_times': [],
            'schedules': [],
            'parsed_confidence': 0.0,
            'parsing_errors': []
        }
        
        confidence_score = 0.0
        max_confidence = 3.0  # Maximum possible confidence
        
        # Extract dosage amount and unit
        dosage_found = False
        for pattern in cls.DOSAGE_PATTERNS:
            match = re.search(pattern, instructions_lower)
            if match:
                amount_str = match.group(1)
                # Convert word numbers to digits
                word_to_number = {
                    'one': '1', 'two': '2', 'three': '3', 'four': '4', 'five': '5',
                    'six': '6', 'seven': '7', 'eight': '8', 'nine': '9', 'ten': '10'
                }
                if amount_str in word_to_number:
                    amount_str = word_to_number[amount_str]
                
                try:
                    result['dosage_amount'] = Decimal(amount_str)
                    result['dosage_unit'] = match.group(2)
                    dosage_found = True
                    confidence_score += 1.0
                    break
                except (ValueError, TypeError):
                    result['parsing_errors'].append(f"Invalid dosage amount: {amount_str}")
        
        if not dosage_found:
            result['parsing_errors'].append("Could not extract dosage amount and unit")
        
        # Extract frequency
        frequency_found = False
        for pattern, frequency in cls.FREQUENCY_PATTERNS:
            if re.search(pattern, instructions_lower):
                result['frequency'] = frequency
                frequency_found = True
                confidence_score += 1.0
                break
        
        if not frequency_found:
            result['parsing_errors'].append("Could not determine frequency")
        
        # Check for multi-time instructions first
        multi_time_match = re.search(cls.MULTI_TIME_PATTERN, instructions_lower)
        if multi_time_match and multi_time_match.group(1):
            times_str = multi_time_match.group(1)
            # Split by both comma and "and", then clean up
            time_parts = re.split(r'\s*[,]\s*|\s+and\s+', times_str)
            custom_times = []
            
            for time_part in time_parts:
                time_part = time_part.strip()
                # Parse individual time using the custom time pattern
                time_match = re.search(r'(\d{1,2})h(\d{2})?|(\d{1,2}):(\d{2})', time_part)
                if time_match:
                    if time_match.group(1):  # e.g., 12h00
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2) or '00')
                    elif time_match.group(3):  # e.g., 12:00
                        hour = int(time_match.group(3))
                        minute = int(time_match.group(4) or '00')
                    else:
                        hour = 0
                        minute = 0
                    custom_times.append(time(hour, minute))
            
            if custom_times:
                result['timing'] = 'custom'
                result['custom_times'] = custom_times
                result['custom_time'] = custom_times[0]  # Keep first time for backward compatibility
                confidence_score += 1.0
                
                # Auto-set frequency based on number of times
                if len(custom_times) == 2:
                    result['frequency'] = 'twice_daily'
                elif len(custom_times) == 3:
                    result['frequency'] = 'three_times_daily'
                elif len(custom_times) == 4:
                    result['frequency'] = 'four_times_daily'
        else:
            # Extract single timing
            timing_found = False
            for pattern, timing in cls.TIME_PATTERNS:
                if timing == 'custom':
                    time_match = re.search(pattern, instructions_lower)
                    if time_match:
                        # Handle both 12h00 and 12:00 formats
                        if time_match.group(1):  # e.g., 12h00
                            hour = int(time_match.group(1))
                            minute = int(time_match.group(2) or '00')
                        elif time_match.group(3):  # e.g., 12:00
                            hour = int(time_match.group(3))
                            minute = int(time_match.group(4) or '00')
                        else:
                            hour = 0
                            minute = 0
                        result['timing'] = 'custom'
                        result['custom_time'] = time(hour, minute)
                        result['custom_times'] = [time(hour, minute)]
                        timing_found = True
                        confidence_score += 1.0
                        break
                elif re.search(pattern, instructions_lower):
                    result['timing'] = timing
                    timing_found = True
                    confidence_score += 1.0
                    break
            
            if not timing_found:
                result['parsing_errors'].append("Could not determine timing")
        
        # Generate schedules based on frequency
        result['schedules'] = cls._generate_schedules(result)
        
        # Calculate confidence score
        result['parsed_confidence'] = min(confidence_score / max_confidence, 1.0)
        
        return result
    
    @classmethod
    def _generate_schedules(cls, parsed_data: Dict) -> List[Dict]:
        """Generate schedule configurations based on frequency."""
        schedules = []
        frequency = parsed_data.get('frequency', 'daily')
        custom_times = parsed_data.get('custom_times', [])
        
        # If we have multiple custom times, create a schedule for each
        if custom_times:
            for custom_time in custom_times:
                schedules.append({
                    'timing': 'custom',
                    'custom_time': custom_time,
                    'dosage_amount': parsed_data.get('dosage_amount'),
                    'frequency': 'daily'
                })
            return schedules
        
        # Handle standard frequency patterns
        if frequency == 'daily':
            schedules.append({
                'timing': parsed_data.get('timing', 'morning'),
                'custom_time': parsed_data.get('custom_time'),
                'dosage_amount': parsed_data.get('dosage_amount'),
                'frequency': 'daily'
            })
        elif frequency == 'twice_daily':
            schedules.extend([
                {'timing': 'morning', 'dosage_amount': parsed_data.get('dosage_amount'), 'frequency': 'daily'},
                {'timing': 'night', 'dosage_amount': parsed_data.get('dosage_amount'), 'frequency': 'daily'}
            ])
        elif frequency == 'three_times_daily':
            schedules.extend([
                {'timing': 'morning', 'dosage_amount': parsed_data.get('dosage_amount'), 'frequency': 'daily'},
                {'timing': 'noon', 'dosage_amount': parsed_data.get('dosage_amount'), 'frequency': 'daily'},
                {'timing': 'night', 'dosage_amount': parsed_data.get('dosage_amount'), 'frequency': 'daily'}
            ])
        elif frequency == 'four_times_daily':
            # Custom times for 4x daily: 6am, 12pm, 6pm, 10pm
            custom_times = [time(6, 0), time(12, 0), time(18, 0), time(22, 0)]
            for custom_time in custom_times:
                schedules.append({
                    'timing': 'custom',
                    'custom_time': custom_time,
                    'dosage_amount': parsed_data.get('dosage_amount'),
                    'frequency': 'daily'
                })
        
        return schedules


class MedicationInteractionValidator:
    """
    Enhanced validator for medication interactions and contraindications.
    """
    
    # Enhanced drug interactions (simplified - in production, use a comprehensive drug database)
    KNOWN_INTERACTIONS = {
        'warfarin': {
            'interactions': ['aspirin', 'ibuprofen', 'naproxen', 'heparin', 'clopidogrel'],
            'severity': 'high',
            'description': 'Increased bleeding risk'
        },
        'digoxin': {
            'interactions': ['furosemide', 'spironolactone', 'quinidine', 'amiodarone'],
            'severity': 'high',
            'description': 'Risk of digoxin toxicity'
        },
        'lithium': {
            'interactions': ['ibuprofen', 'naproxen', 'thiazide_diuretics', 'ace_inhibitors'],
            'severity': 'high',
            'description': 'Increased lithium levels'
        },
        'phenytoin': {
            'interactions': ['warfarin', 'oral_contraceptives', 'corticosteroids', 'theophylline'],
            'severity': 'medium',
            'description': 'Altered drug metabolism'
        },
        'theophylline': {
            'interactions': ['ciprofloxacin', 'erythromycin', 'cimetidine', 'phenytoin'],
            'severity': 'medium',
            'description': 'Altered theophylline levels'
        },
        'metformin': {
            'interactions': ['alcohol', 'furosemide', 'corticosteroids'],
            'severity': 'medium',
            'description': 'Risk of lactic acidosis'
        },
        'insulin': {
            'interactions': ['corticosteroids', 'beta_blockers', 'thiazide_diuretics'],
            'severity': 'medium',
            'description': 'Altered blood glucose control'
        },
        'statins': {
            'interactions': ['grapefruit_juice', 'erythromycin', 'cyclosporine'],
            'severity': 'medium',
            'description': 'Increased statin levels'
        },
    }
    
    # Enhanced contraindications
    CONTRAINDICATIONS = {
        'pregnancy': {
            'medications': ['warfarin', 'isotretinoin', 'thalidomide', 'methotrexate', 'ace_inhibitors'],
            'severity': 'high',
            'description': 'Teratogenic risk'
        },
        'liver_disease': {
            'medications': ['acetaminophen', 'statins', 'methotrexate', 'valproic_acid'],
            'severity': 'high',
            'description': 'Risk of liver toxicity'
        },
        'kidney_disease': {
            'medications': ['nsaids', 'aminoglycosides', 'metformin', 'lithium'],
            'severity': 'high',
            'description': 'Risk of kidney damage'
        },
        'heart_disease': {
            'medications': ['sildenafil', 'nitrates', 'beta_blockers', 'calcium_channel_blockers'],
            'severity': 'medium',
            'description': 'Cardiovascular interactions'
        },
        'diabetes': {
            'medications': ['corticosteroids', 'thiazide_diuretics', 'beta_blockers'],
            'severity': 'medium',
            'description': 'Altered blood glucose control'
        },
    }
    
    @classmethod
    def check_interactions(cls, medication_name: str, existing_medications: List[str]) -> List[Dict]:
        """Check for potential drug interactions."""
        interactions = []
        medication_lower = medication_name.lower()
        
        for drug, interaction_data in cls.KNOWN_INTERACTIONS.items():
            if drug in medication_lower:
                for existing_med in existing_medications:
                    if any(interacting_drug in existing_med.lower() for interacting_drug in interaction_data['interactions']):
                        interactions.append({
                            'medication1': medication_name,
                            'medication2': existing_med,
                            'severity': interaction_data['severity'],
                            'description': interaction_data['description'],
                            'recommendation': f"Monitor for {interaction_data['description'].lower()}"
                        })
        
        return interactions
    
    @classmethod
    def check_contraindications(cls, medication_name: str, patient_conditions: List[str]) -> List[Dict]:
        """Check for contraindications based on patient conditions."""
        contraindications = []
        medication_lower = medication_name.lower()
        
        for condition, contraindication_data in cls.CONTRAINDICATIONS.items():
            if condition in patient_conditions:
                for drug in contraindication_data['medications']:
                    if drug in medication_lower:
                        contraindications.append({
                            'medication': medication_name,
                            'condition': condition,
                            'severity': contraindication_data['severity'],
                            'description': contraindication_data['description'],
                            'recommendation': f"Consult healthcare provider before use"
                        })
        
        return contraindications


class PrescriptionRenewalCalculator:
    """
    Calculator for prescription renewal dates based on quantity and frequency.
    """
    
    @classmethod
    def calculate_renewal_date(cls, quantity: int, frequency: str, dosage_amount: Decimal = Decimal('1')) -> datetime.date:
        """
        Calculate prescription renewal date based on quantity and frequency.
        
        Args:
            quantity: Total quantity prescribed
            frequency: Frequency of administration
            dosage_amount: Amount per dose (default 1)
        
        Returns:
            datetime.date: Expected renewal date
        """
        if not quantity or not frequency:
            return timezone.now().date() + timedelta(days=30)  # Default 30 days
        
        # Calculate daily consumption
        daily_consumption = cls._get_daily_consumption(frequency, dosage_amount)
        
        if daily_consumption <= 0:
            return timezone.now().date() + timedelta(days=30)
        
        # Calculate days until renewal
        days_until_renewal = int(quantity / daily_consumption)
        
        # Add buffer days (7 days before running out)
        buffer_days = 7
        renewal_date = timezone.now().date() + timedelta(days=days_until_renewal - buffer_days)
        
        # Ensure minimum 7 days from now
        min_date = timezone.now().date() + timedelta(days=7)
        return max(renewal_date, min_date)
    
    @classmethod
    def _get_daily_consumption(cls, frequency: str, dosage_amount: Decimal) -> Decimal:
        """Get daily consumption based on frequency."""
        frequency_mapping = {
            'daily': 1,
            'twice_daily': 2,
            'three_times_daily': 3,
            'four_times_daily': 4,
            'weekly': 1/7,
            'monthly': 1/30,
            'as_needed': 0.5,  # Estimate
        }
        
        multiplier = frequency_mapping.get(frequency, 1)
        return dosage_amount * Decimal(str(multiplier))


class StockDeductionManager:
    """
    Manager for stock deduction during schedule creation.
    """
    
    @classmethod
    def calculate_required_stock(cls, schedules_data: List[Dict], duration_days: int = 30) -> Dict[str, int]:
        """
        Calculate required stock for medication schedules.
        
        Args:
            schedules_data: List of schedule configurations
            duration_days: Duration in days to calculate for
        
        Returns:
            Dict mapping medication_id to required quantity
        """
        stock_requirements = {}
        
        for schedule in schedules_data:
            medication_id = schedule.get('medication_id')
            if not medication_id:
                continue
            
            # Calculate daily consumption
            frequency = schedule.get('frequency', 'daily')
            dosage_amount = schedule.get('dosage_amount', 1)
            daily_consumption = cls._get_daily_consumption(frequency, dosage_amount)
            
            # Calculate total requirement
            total_requirement = int(daily_consumption * duration_days)
            
            if medication_id in stock_requirements:
                stock_requirements[medication_id] += total_requirement
            else:
                stock_requirements[medication_id] = total_requirement
        
        return stock_requirements
    
    @classmethod
    def check_stock_availability(cls, medication_id: int, required_quantity: int) -> Dict[str, Any]:
        """
        Check if sufficient stock is available.
        
        Returns:
            Dict with availability status and details
        """
        try:
            medication = Medication.objects.get(id=medication_id)
            available_stock = medication.pill_count
            is_available = available_stock >= required_quantity
            
            return {
                'is_available': is_available,
                'available_stock': available_stock,
                'required_quantity': required_quantity,
                'shortfall': max(0, required_quantity - available_stock),
                'medication_name': medication.name
            }
        except Medication.DoesNotExist:
            return {
                'is_available': False,
                'available_stock': 0,
                'required_quantity': required_quantity,
                'shortfall': required_quantity,
                'medication_name': 'Unknown',
                'error': 'Medication not found'
            }
    
    @classmethod
    def deduct_stock(cls, medication_id: int, quantity: int, user: User, reason: str = "Schedule creation") -> bool:
        """
        Deduct stock from medication inventory.
        
        Returns:
            bool: True if deduction was successful
        """
        try:
            with transaction.atomic():
                medication = Medication.objects.select_for_update().get(id=medication_id)
                
                if medication.pill_count < quantity:
                    return False
                
                # Deduct stock
                medication.pill_count -= quantity
                medication.save()
                
                # Create stock transaction record
                StockTransaction.objects.create(
                    medication=medication,
                    user=user,
                    transaction_type=StockTransaction.TransactionType.DOSE_TAKEN,
                    quantity=-quantity,
                    stock_before=medication.pill_count + quantity,
                    stock_after=medication.pill_count,
                    notes=f"Stock deduction: {reason}"
                )
                
                return True
        except Exception as e:
            logger.error(f"Failed to deduct stock for medication {medication_id}: {e}")
            return False
    
    @classmethod
    def _get_daily_consumption(cls, frequency: str, dosage_amount: Decimal) -> Decimal:
        """Get daily consumption based on frequency."""
        frequency_mapping = {
            'daily': 1,
            'twice_daily': 2,
            'three_times_daily': 3,
            'four_times_daily': 4,
            'weekly': 1/7,
            'monthly': 1/30,
            'as_needed': 0.5,  # Estimate
        }
        
        multiplier = frequency_mapping.get(frequency, 1)
        return dosage_amount * Decimal(str(multiplier))


class ErrorCodeManager:
    """
    Manager for comprehensive error handling with specific error codes.
    """
    
    # Error codes for frontend handling
    ERROR_CODES = {
        # Validation errors (1000-1999)
        'INVALID_ICD10_CODE': {'code': 1001, 'message': 'Invalid ICD-10 code format'},
        'INVALID_STRENGTH_FORMAT': {'code': 1002, 'message': 'Invalid strength format'},
        'INVALID_MANUFACTURER': {'code': 1003, 'message': 'Unrecognized manufacturer'},
        'INVALID_PRESCRIPTION_FORMAT': {'code': 1004, 'message': 'Invalid prescription format'},
        'INSUFFICIENT_STOCK': {'code': 1005, 'message': 'Insufficient stock available'},
        'INVALID_DOSAGE_UNIT': {'code': 1006, 'message': 'Invalid dosage unit'},
        'INVALID_FREQUENCY': {'code': 1007, 'message': 'Invalid frequency format'},
        
        # Drug interaction errors (2000-2999)
        'DRUG_INTERACTION': {'code': 2001, 'message': 'Potential drug interaction detected'},
        'CONTRAINDICATION': {'code': 2002, 'message': 'Contraindication detected'},
        'ALLERGY_WARNING': {'code': 2003, 'message': 'Potential allergy risk'},
        
        # Stock management errors (3000-3999)
        'STOCK_DEDUCTION_FAILED': {'code': 3001, 'message': 'Failed to deduct stock'},
        'STOCK_TRANSACTION_FAILED': {'code': 3002, 'message': 'Stock transaction failed'},
        'LOW_STOCK_WARNING': {'code': 3003, 'message': 'Low stock warning'},
        
        # Prescription processing errors (4000-4999)
        'PARSING_ERROR': {'code': 4001, 'message': 'Failed to parse prescription'},
        'RENEWAL_CALCULATION_ERROR': {'code': 4002, 'message': 'Failed to calculate renewal date'},
        'SCHEDULE_CREATION_ERROR': {'code': 4003, 'message': 'Failed to create schedule'},
        
        # System errors (5000-5999)
        'DATABASE_ERROR': {'code': 5001, 'message': 'Database operation failed'},
        'AUDIT_LOG_ERROR': {'code': 5002, 'message': 'Failed to log audit trail'},
        'VALIDATION_ERROR': {'code': 5003, 'message': 'Validation failed'},
    }
    
    @classmethod
    def get_error_response(cls, error_code: str, details: str = None, field: str = None) -> Dict:
        """Get standardized error response."""
        error_info = cls.ERROR_CODES.get(error_code, {
            'code': 9999,
            'message': 'Unknown error'
        })
        
        response = {
            'error_code': error_info['code'],
            'error_message': error_info['message'],
            'error_type': error_code,
        }
        
        if details:
            response['details'] = details
        
        if field:
            response['field'] = field
        
        return response
    
    @classmethod
    def raise_validation_error(cls, error_code: str, details: str = None, field: str = None):
        """Raise validation error with standardized format."""
        error_response = cls.get_error_response(error_code, details, field)
        raise serializers.ValidationError(error_response)


class AuditLogger:
    """
    Comprehensive audit logging for prescription processing compliance.
    """
    
    @classmethod
    def log_prescription_creation(cls, user: User, prescription_data: Dict, success: bool, errors: List[str] = None):
        """Log prescription creation event."""
        if not AUDIT_ENABLED or not AuditLog:
            return
        
        try:
            action = AuditLog.ActionType.CREATE if success else AuditLog.ActionType.SECURITY_EVENT
            severity = AuditLog.Severity.LOW if success else AuditLog.Severity.MEDIUM
            
            description = f"Prescription {'created' if success else 'creation failed'}"
            if errors:
                description += f" - Errors: {', '.join(errors)}"
            
            AuditLog.objects.create(
                user=user,
                action=action,
                severity=severity,
                object_repr=f"Prescription for {user.username}",
                changes=prescription_data,
                description=description,
                ip_address=getattr(user, 'last_login_ip', None),
                user_agent=getattr(user, 'last_user_agent', None),
                request_path='/api/prescriptions/',
                request_method='POST',
                session_id=getattr(user, 'session_key', ''),
                metadata={
                    'prescription_type': 'bulk_create',
                    'medication_count': len(prescription_data.get('medications', [])),
                    'success': success,
                    'errors': errors or []
                }
            )
        except Exception as e:
            logger.error(f"Failed to log prescription creation audit: {e}")
    
    @classmethod
    def log_medication_interaction(cls, user: User, medication_name: str, interactions: List[Dict]):
        """Log medication interaction detection."""
        if not AUDIT_ENABLED or not AuditLog:
            return
        
        try:
            AuditLog.objects.create(
                user=user,
                action=AuditLog.ActionType.SECURITY_EVENT,
                severity=AuditLog.Severity.MEDIUM,
                object_repr=f"Interaction check for {medication_name}",
                description=f"Drug interaction check performed for {medication_name}",
                changes={'interactions': interactions},
                ip_address=getattr(user, 'last_login_ip', None),
                user_agent=getattr(user, 'last_user_agent', None),
                request_path='/api/prescriptions/',
                request_method='POST',
                session_id=getattr(user, 'session_key', ''),
                metadata={
                    'interaction_count': len(interactions),
                    'medication_name': medication_name
                }
            )
        except Exception as e:
            logger.error(f"Failed to log medication interaction audit: {e}")
    
    @classmethod
    def log_stock_deduction(cls, user: User, medication_id: int, quantity: int, success: bool):
        """Log stock deduction event."""
        if not AUDIT_ENABLED or not AuditLog:
            return
        
        try:
            action = AuditLog.ActionType.UPDATE if success else AuditLog.ActionType.SECURITY_EVENT
            severity = AuditLog.Severity.LOW if success else AuditLog.Severity.MEDIUM
            
            AuditLog.objects.create(
                user=user,
                action=action,
                severity=severity,
                object_repr=f"Stock deduction for medication {medication_id}",
                description=f"Stock deduction {'successful' if success else 'failed'} - {quantity} units",
                changes={'medication_id': medication_id, 'quantity': quantity, 'success': success},
                ip_address=getattr(user, 'last_login_ip', None),
                user_agent=getattr(user, 'last_user_agent', None),
                request_path='/api/prescriptions/',
                request_method='POST',
                session_id=getattr(user, 'session_key', ''),
                metadata={
                    'medication_id': medication_id,
                    'quantity': quantity,
                    'success': success
                }
            )
        except Exception as e:
            logger.error(f"Failed to log stock deduction audit: {e}")


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type']
        read_only_fields = ['id']


class PrescriptionBulkCreateSerializer(serializers.Serializer):
    """
    Bulk create serializer for handling 21-medication prescription format.
    
    Features:
    - Handles multiple medications in a single prescription
    - Validates ICD-10 codes with proper mapping
    - Checks drug interactions and contraindications
    - Parses prescription instructions
    - Normalizes strength units
    - Validates South African manufacturers
    - Calculates renewal dates
    - Manages stock deduction
    - Comprehensive error handling
    - Audit logging for compliance
    """
    
    # Prescription metadata
    prescription_number = serializers.CharField(
        max_length=100,
        required=False,
        help_text=_('Prescription number')
    )
    
    prescribing_doctor = serializers.CharField(
        max_length=200,
        required=False,
        help_text=_('Name of prescribing doctor')
    )
    
    prescribed_date = serializers.DateField(
        default=timezone.now,
        help_text=_('Date when prescription was issued')
    )
    
    # Patient information
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type='PATIENT'),
        required=False,
        help_text=_('Patient ID (if not current user)')
    )
    
    patient_conditions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text=_('Patient medical conditions for contraindication checking')
    )
    
    # ICD-10 codes
    icd10_codes = serializers.ListField(
        child=serializers.CharField(max_length=10),
        required=False,
        help_text=_('ICD-10 diagnosis codes')
    )
    
    # Medications list
    medications = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=21,  # Support up to 21 medications
        help_text=_('List of medications in the prescription')
    )
    
    # Processing options
    auto_create_schedules = serializers.BooleanField(
        default=True,
        help_text=_('Automatically create medication schedules')
    )
    
    auto_deduct_stock = serializers.BooleanField(
        default=False,
        help_text=_('Automatically deduct stock when creating schedules')
    )
    
    # Results (read-only)
    created_medications = serializers.SerializerMethodField()
    created_schedules = serializers.SerializerMethodField()
    interaction_warnings = serializers.SerializerMethodField()
    contraindication_warnings = serializers.SerializerMethodField()
    stock_warnings = serializers.SerializerMethodField()
    processing_errors = serializers.SerializerMethodField()
    
    def validate_icd10_codes(self, value):
        """Validate ICD-10 codes."""
        if value:
            validated_codes = []
            for code in value:
                if not ICD10Validator.validate(code):
                    ErrorCodeManager.raise_validation_error(
                        'INVALID_ICD10_CODE',
                        f"Invalid ICD-10 code format: {code}. Expected format: A00.0",
                        'icd10_codes'
                    )
                validated_codes.append(ICD10Validator.clean(code))
            return validated_codes
        return []
    
    def validate_medications(self, value):
        """Validate medications list."""
        if not value:
            ErrorCodeManager.raise_validation_error(
                'VALIDATION_ERROR',
                'At least one medication is required',
                'medications'
            )
        
        validated_medications = []
        for i, medication_data in enumerate(value):
            try:
                validated_medication = self._validate_medication_data(medication_data, i)
                validated_medications.append(validated_medication)
            except serializers.ValidationError as e:
                # Add index to error for frontend identification
                error_detail = e.detail
                if isinstance(error_detail, dict):
                    error_detail['medication_index'] = i
                raise serializers.ValidationError({
                    f'medication_{i}': error_detail
                })
        
        return validated_medications
    
    def _validate_medication_data(self, medication_data: Dict, index: int) -> Dict:
        """Validate individual medication data."""
        required_fields = ['name', 'strength', 'dosage_unit', 'quantity']
        for field in required_fields:
            if field not in medication_data:
                ErrorCodeManager.raise_validation_error(
                    'VALIDATION_ERROR',
                    f"Missing required field: {field}",
                    f'medications[{index}].{field}'
                )
        
        # Validate strength format
        strength = medication_data.get('strength', '')
        if not StrengthUnitNormalizer.validate_strength_format(strength):
            ErrorCodeManager.raise_validation_error(
                'INVALID_STRENGTH_FORMAT',
                f"Invalid strength format: {strength}",
                f'medications[{index}].strength'
            )
        
        # Normalize strength
        medication_data['strength'] = StrengthUnitNormalizer.normalize_strength(strength)
        
        # Validate manufacturer if provided
        manufacturer = medication_data.get('manufacturer', '')
        if manufacturer and not SouthAfricanManufacturerValidator.validate_manufacturer(manufacturer):
            ErrorCodeManager.raise_validation_error(
                'INVALID_MANUFACTURER',
                f"Unrecognized manufacturer: {manufacturer}",
                f'medications[{index}].manufacturer'
            )
        
        # Normalize manufacturer
        if manufacturer:
            medication_data['manufacturer'] = SouthAfricanManufacturerValidator.get_standardized_name(manufacturer)
        
        # Validate prescription instructions if provided
        instructions = medication_data.get('prescription_instructions', '')
        if instructions:
            parsed = PrescriptionParser.parse_instructions(instructions)
            if parsed.get('parsing_errors'):
                ErrorCodeManager.raise_validation_error(
                    'PARSING_ERROR',
                    f"Failed to parse instructions: {', '.join(parsed['parsing_errors'])}",
                    f'medications[{index}].prescription_instructions'
                )
            medication_data['parsed_instructions'] = parsed
        
        return medication_data
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Check for drug interactions
        medications = attrs.get('medications', [])
        patient_conditions = attrs.get('patient_conditions', [])
        
        interaction_warnings = []
        contraindication_warnings = []
        
        for i, medication_data in enumerate(medications):
            medication_name = medication_data.get('name', '')
            
            # Check interactions with other medications
            other_medications = [m.get('name', '') for j, m in enumerate(medications) if j != i]
            interactions = MedicationInteractionValidator.check_interactions(medication_name, other_medications)
            if interactions:
                interaction_warnings.extend(interactions)
            
            # Check contraindications
            contraindications = MedicationInteractionValidator.check_contraindications(medication_name, patient_conditions)
            if contraindications:
                contraindication_warnings.extend(contraindications)
        
        # Store warnings for later use
        attrs['interaction_warnings'] = interaction_warnings
        attrs['contraindication_warnings'] = contraindication_warnings
        
        return attrs
    
    def create(self, validated_data):
        """Create medications and schedules in bulk."""
        user = self.context['request'].user
        patient = validated_data.get('patient_id', user)
        
        # Extract data
        medications_data = validated_data.pop('medications', [])
        icd10_codes = validated_data.pop('icd10_codes', [])
        patient_conditions = validated_data.pop('patient_conditions', [])
        auto_create_schedules = validated_data.pop('auto_create_schedules', True)
        auto_deduct_stock = validated_data.pop('auto_deduct_stock', False)
        
        created_medications = []
        created_schedules = []
        processing_errors = []
        stock_warnings = []
        
        try:
            with transaction.atomic():
                # Create medications
                for medication_data in medications_data:
                    try:
                        medication = self._create_medication(medication_data, user)
                        created_medications.append(medication)
                        
                        # Create schedules if requested
                        if auto_create_schedules:
                            schedules = self._create_schedules(medication, medication_data, patient)
                            created_schedules.extend(schedules)
                            
                            # Deduct stock if requested
                            if auto_deduct_stock:
                                self._deduct_stock_for_schedules(medication, schedules, user, stock_warnings)
                        
                    except Exception as e:
                        processing_errors.append({
                            'medication_name': medication_data.get('name', 'Unknown'),
                            'error': str(e),
                            'error_type': 'MEDICATION_CREATION_FAILED'
                        })
                
                # Log audit trail
                AuditLogger.log_prescription_creation(
                    user=user,
                    prescription_data={
                        'medications': [m.name for m in created_medications],
                        'icd10_codes': icd10_codes,
                        'patient_conditions': patient_conditions
                    },
                    success=len(processing_errors) == 0,
                    errors=[e['error'] for e in processing_errors]
                )
                
        except Exception as e:
            processing_errors.append({
                'error': str(e),
                'error_type': 'TRANSACTION_FAILED'
            })
            AuditLogger.log_prescription_creation(
                user=user,
                prescription_data=validated_data,
                success=False,
                errors=[str(e)]
            )
        
        # Store results for response
        self._created_medications = created_medications
        self._created_schedules = created_schedules
        self._processing_errors = processing_errors
        self._stock_warnings = stock_warnings
        
        return validated_data
    
    def _create_medication(self, medication_data: Dict, user: User) -> Medication:
        """Create a single medication."""
        # Extract parsed instructions
        parsed_instructions = medication_data.pop('parsed_instructions', {})
        
        # Create medication
        medication = Medication.objects.create(**medication_data)
        
        # Store parsed instructions if available
        if parsed_instructions:
            medication.prescription_instructions = self._format_instructions(parsed_instructions)
            medication.save()
        
        return medication
    
    def _create_schedules(self, medication: Medication, medication_data: Dict, patient: User) -> List[MedicationSchedule]:
        """Create medication schedules."""
        schedules = []
        parsed_instructions = medication_data.get('parsed_instructions', {})
        
        if parsed_instructions and parsed_instructions.get('schedules'):
            # Use parsed schedules
            for schedule_data in parsed_instructions['schedules']:
                schedule = self._create_single_schedule(medication, patient, schedule_data)
                schedules.append(schedule)
        else:
            # Create default schedule
            schedule_data = {
                'timing': 'morning',
                'dosage_amount': Decimal('1'),
                'frequency': 'daily'
            }
            schedule = self._create_single_schedule(medication, patient, schedule_data)
            schedules.append(schedule)
        
        return schedules
    
    def _create_single_schedule(self, medication: Medication, patient: User, schedule_data: Dict) -> MedicationSchedule:
        """Create a single medication schedule."""
        schedule_data.update({
            'medication': medication,
            'patient': patient,
            'status': MedicationSchedule.Status.ACTIVE,
            'start_date': timezone.now().date(),
            'monday': True,
            'tuesday': True,
            'wednesday': True,
            'thursday': True,
            'friday': True,
            'saturday': True,
            'sunday': True,
        })
        
        return MedicationSchedule.objects.create(**schedule_data)
    
    def _deduct_stock_for_schedules(self, medication: Medication, schedules: List[MedicationSchedule], user: User, stock_warnings: List):
        """Deduct stock for created schedules."""
        # Calculate required stock for 30 days
        total_required = 0
        for schedule in schedules:
            daily_consumption = StockDeductionManager._get_daily_consumption(
                schedule.frequency, schedule.dosage_amount
            )
            total_required += int(daily_consumption * 30)
        
        # Check availability
        availability = StockDeductionManager.check_stock_availability(medication.id, total_required)
        
        if not availability['is_available']:
            stock_warnings.append({
                'medication_name': medication.name,
                'available_stock': availability['available_stock'],
                'required_quantity': total_required,
                'shortfall': availability['shortfall'],
                'warning_type': 'INSUFFICIENT_STOCK'
            })
            return
        
        # Deduct stock
        success = StockDeductionManager.deduct_stock(medication.id, total_required, user, "Bulk prescription creation")
        
        if not success:
            stock_warnings.append({
                'medication_name': medication.name,
                'warning_type': 'STOCK_DEDUCTION_FAILED',
                'error': 'Failed to deduct stock'
            })
        
        # Log audit trail
        AuditLogger.log_stock_deduction(user, medication.id, total_required, success)
    
    def _format_instructions(self, parsed_instructions: Dict) -> str:
        """Format parsed instructions back to text."""
        parts = []
        
        if parsed_instructions.get('dosage_amount'):
            parts.append(f"Take {parsed_instructions['dosage_amount']} {parsed_instructions.get('dosage_unit', 'units')}")
        
        if parsed_instructions.get('frequency'):
            parts.append(parsed_instructions['frequency'].replace('_', ' '))
        
        if parsed_instructions.get('timing'):
            parts.append(f"at {parsed_instructions['timing']}")
        
        return ' '.join(parts)
    
    def get_created_medications(self, obj):
        """Get created medications."""
        return [
            {
                'id': med.id,
                'name': med.name,
                'strength': med.strength,
                'dosage_unit': med.dosage_unit
            }
            for med in getattr(self, '_created_medications', [])
        ]
    
    def get_created_schedules(self, obj):
        """Get created schedules."""
        return [
            {
                'id': schedule.id,
                'medication_name': schedule.medication.name,
                'timing': schedule.timing,
                'frequency': schedule.frequency
            }
            for schedule in getattr(self, '_created_schedules', [])
        ]
    
    def get_interaction_warnings(self, obj):
        """Get interaction warnings."""
        return getattr(self, '_interaction_warnings', [])
    
    def get_contraindication_warnings(self, obj):
        """Get contraindication warnings."""
        return getattr(self, '_contraindication_warnings', [])
    
    def get_stock_warnings(self, obj):
        """Get stock warnings."""
        return getattr(self, '_stock_warnings', [])
    
    def get_processing_errors(self, obj):
        """Get processing errors."""
        return getattr(self, '_processing_errors', [])


class MedicationSerializer(serializers.ModelSerializer):
    """Basic serializer for Medication model."""
    
    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'brand_name', 'medication_type',
            'prescription_type', 'strength', 'dosage_unit', 'pill_count',
            'low_stock_threshold', 'manufacturer', 'is_low_stock',
            'is_expired', 'is_expiring_soon', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_low_stock', 'is_expired', 'is_expiring_soon', 'created_at', 'updated_at']


class MedicationDetailSerializer(MedicationSerializer):
    """Detailed serializer for Medication model."""
    
    class Meta(MedicationSerializer.Meta):
        fields = MedicationSerializer.Meta.fields + [
            'description', 'active_ingredients', 'side_effects',
            'contraindications', 'storage_instructions', 'expiration_date'
        ]


class EnhancedMedicationSerializer(serializers.ModelSerializer):
    """
    Enhanced medication serializer with complex prescription data handling.
    
    Features:
    - ICD-10 code validation with comprehensive mapping
    - Advanced prescription instruction parsing
    - Nested schedule creation with stock deduction
    - Enhanced drug interaction checking
    - Comprehensive contraindication validation
    - Strength unit normalization
    - South African manufacturer validation
    - Prescription renewal date calculations
    - Audit logging for compliance
    """
    
    # Additional fields for prescription data
    icd10_codes = serializers.ListField(
        child=serializers.CharField(max_length=10),
        required=False,
        help_text=_('ICD-10 diagnosis codes')
    )
    
    prescription_instructions = serializers.CharField(
        max_length=500,
        required=False,
        help_text=_('Prescription instructions (e.g., "Take one tablet daily")')
    )
    
    patient_conditions = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text=_('Patient medical conditions for contraindication checking')
    )
    
    # Nested schedule creation
    schedules = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        write_only=True,
        help_text=_('Schedule configurations to create')
    )
    
    # Stock management
    auto_deduct_stock = serializers.BooleanField(
        default=False,
        required=False,
        help_text=_('Automatically deduct stock when creating schedules')
    )
    
    # Renewal calculation
    calculate_renewal_date = serializers.BooleanField(
        default=True,
        required=False,
        help_text=_('Calculate prescription renewal date')
    )
    
    # Parsed prescription data (read-only)
    parsed_prescription = serializers.SerializerMethodField()
    interaction_warnings = serializers.SerializerMethodField()
    contraindication_warnings = serializers.SerializerMethodField()
    renewal_date = serializers.SerializerMethodField()
    stock_availability = serializers.SerializerMethodField()
    icd10_descriptions = serializers.SerializerMethodField()
    
    class Meta:
        model = Medication
        fields = [
            'id', 'name', 'generic_name', 'brand_name', 'medication_type',
            'prescription_type', 'strength', 'dosage_unit', 'pill_count',
            'low_stock_threshold', 'description', 'active_ingredients',
            'manufacturer', 'side_effects', 'contraindications',
            'storage_instructions', 'expiration_date', 'icd10_codes',
            'prescription_instructions', 'patient_conditions', 'schedules',
            'parsed_prescription', 'interaction_warnings', 'contraindication_warnings',
            'is_low_stock', 'is_expired', 'is_expiring_soon',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'is_low_stock', 'is_expired', 'is_expiring_soon',
            'parsed_prescription', 'interaction_warnings', 'contraindication_warnings',
            'created_at', 'updated_at'
        ]
    
    def validate_icd10_codes(self, value):
        """Validate ICD-10 codes with comprehensive mapping."""
        if value:
            validated_codes = []
            for code in value:
                if not ICD10Validator.validate(code):
                    ErrorCodeManager.raise_validation_error(
                        'INVALID_ICD10_CODE',
                        f"Invalid ICD-10 code format: {code}. Expected format: A00.0",
                        'icd10_codes'
                    )
                validated_codes.append(ICD10Validator.clean(code))
            return validated_codes
        return []
    
    def validate_prescription_type(self, value):
        """Validate prescription type."""
        valid_types = dict(Medication.PrescriptionType.choices)
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid prescription type. Must be one of: {', '.join(valid_types.keys())}"
            )
        return value
    
    def validate_medication_type(self, value):
        """Validate medication type."""
        valid_types = dict(Medication.MedicationType.choices)
        if value not in valid_types:
            raise serializers.ValidationError(
                f"Invalid medication type. Must be one of: {', '.join(valid_types.keys())}"
            )
        return value
    
    def validate_strength(self, value):
        """Validate and normalize medication strength format."""
        if not value:
            ErrorCodeManager.raise_validation_error(
                'VALIDATION_ERROR',
                "Strength is required",
                'strength'
            )
        
        # Validate strength format
        if not StrengthUnitNormalizer.validate_strength_format(value):
            ErrorCodeManager.raise_validation_error(
                'INVALID_STRENGTH_FORMAT',
                f"Invalid strength format: {value}. Examples: 500mg, 10mg/ml, 2.5mg",
                'strength'
            )
        
        # Normalize strength
        return StrengthUnitNormalizer.normalize_strength(value)
    
    def validate_manufacturer(self, value):
        """Validate South African manufacturer."""
        if value and not SouthAfricanManufacturerValidator.validate_manufacturer(value):
            ErrorCodeManager.raise_validation_error(
                'INVALID_MANUFACTURER',
                f"Unrecognized manufacturer: {value}",
                'manufacturer'
            )
        return SouthAfricanManufacturerValidator.get_standardized_name(value) if value else value
    
    def validate(self, attrs):
        """Enhanced cross-field validation."""
        # Validate dosage unit matches strength
        strength = attrs.get('strength', '')
        dosage_unit = attrs.get('dosage_unit', '')
        
        if strength and dosage_unit:
            # Extract unit from strength
            strength_unit_match = re.search(r'(mg|mcg|g|ml|l|units?|iu|meq|mmol|%)$', strength, re.IGNORECASE)
            if strength_unit_match:
                strength_unit = strength_unit_match.group(1).lower()
                if strength_unit != dosage_unit.lower():
                    ErrorCodeManager.raise_validation_error(
                        'INVALID_DOSAGE_UNIT',
                        f"Dosage unit '{dosage_unit}' should match strength unit '{strength_unit}'",
                        'dosage_unit'
                    )
        
        # Validate prescription instructions if provided
        prescription_instructions = attrs.get('prescription_instructions')
        if prescription_instructions:
            parsed = PrescriptionParser.parse_instructions(prescription_instructions)
            if parsed.get('parsing_errors'):
                ErrorCodeManager.raise_validation_error(
                    'PARSING_ERROR',
                    f"Failed to parse instructions: {', '.join(parsed['parsing_errors'])}",
                    'prescription_instructions'
                )
            if not parsed.get('dosage_amount'):
                ErrorCodeManager.raise_validation_error(
                    'PARSING_ERROR',
                    "Could not parse dosage amount from instructions",
                    'prescription_instructions'
                )
        
        # Check for drug interactions if patient conditions provided
        patient_conditions = attrs.get('patient_conditions', [])
        medication_name = attrs.get('name', '')
        
        if medication_name and patient_conditions:
            contraindications = MedicationInteractionValidator.check_contraindications(medication_name, patient_conditions)
            if contraindications:
                # Store warnings for later use
                attrs['contraindication_warnings'] = contraindications
        
        return attrs
    
    def get_parsed_prescription(self, obj):
        """Get parsed prescription data."""
        if hasattr(obj, 'prescription_instructions') and obj.prescription_instructions:
            return PrescriptionParser.parse_instructions(obj.prescription_instructions)
        return None
    
    def get_interaction_warnings(self, obj):
        """Get drug interaction warnings."""
        if not obj.name:
            return []
        
        # Get existing medications for the current user
        user = self.context.get('request').user if self.context.get('request') else None
        if not user:
            return []
        
        existing_medications = []
        if hasattr(user, 'medication_schedules'):
            existing_medications = [
                schedule.medication.name 
                for schedule in user.medication_schedules.filter(status='active')
                if schedule.medication.name != obj.name
            ]
        
        return MedicationInteractionValidator.check_interactions(obj.name, existing_medications)
    
    def get_contraindication_warnings(self, obj):
        """Get contraindication warnings."""
        if not obj.name:
            return []
        
        # Get patient conditions from context or user profile
        patient_conditions = []
        user = self.context.get('request').user if self.context.get('request') else None
        if user and hasattr(user, 'medical_conditions'):
            patient_conditions = user.medical_conditions
        
        return MedicationInteractionValidator.check_contraindications(obj.name, patient_conditions)
    
    def get_renewal_date(self, obj):
        """Get calculated renewal date."""
        if not hasattr(obj, 'pill_count') or not obj.pill_count:
            return None
        
        # Calculate renewal date based on quantity and frequency
        # This is a simplified calculation - in practice, you'd use actual schedule data
        try:
            renewal_date = PrescriptionRenewalCalculator.calculate_renewal_date(
                quantity=obj.pill_count,
                frequency='daily',  # Default frequency
                dosage_amount=Decimal('1')  # Default dosage
            )
            return renewal_date
        except Exception as e:
            logger.error(f"Failed to calculate renewal date for medication {obj.id}: {e}")
            return None
    
    def get_stock_availability(self, obj):
        """Get stock availability information."""
        if not hasattr(obj, 'pill_count'):
            return None
        
        return {
            'current_stock': obj.pill_count,
            'low_stock_threshold': obj.low_stock_threshold,
            'is_low_stock': obj.is_low_stock,
            'days_until_stockout': self._calculate_days_until_stockout(obj),
            'recommended_order_quantity': self._calculate_recommended_order_quantity(obj)
        }
    
    def get_icd10_descriptions(self, obj):
        """Get ICD-10 code descriptions."""
        icd10_codes = getattr(obj, 'icd10_codes', [])
        if not icd10_codes:
            return []
        
        descriptions = []
        for code in icd10_codes:
            description = ICD10Validator.get_description(code)
            category = ICD10Validator.get_category(code)
            descriptions.append({
                'code': code,
                'description': description,
                'category': category
            })
        
        return descriptions
    
    def _calculate_days_until_stockout(self, obj):
        """Calculate days until stockout."""
        if not obj.pill_count or obj.pill_count <= 0:
            return 0
        
        # Simplified calculation - in practice, use actual usage patterns
        daily_usage = 1  # Default daily usage
        return int(obj.pill_count / daily_usage)
    
    def _calculate_recommended_order_quantity(self, obj):
        """Calculate recommended order quantity."""
        if not obj.pill_count:
            return obj.low_stock_threshold
        
        # Order enough to last 30 days plus buffer
        daily_usage = 1  # Default daily usage
        recommended = daily_usage * 30 + obj.low_stock_threshold
        return max(recommended, obj.low_stock_threshold)
    
    def create(self, validated_data):
        """Create medication with enhanced features."""
        # Extract additional data
        schedules_data = validated_data.pop('schedules', [])
        icd10_codes = validated_data.pop('icd10_codes', [])
        prescription_instructions = validated_data.pop('prescription_instructions', None)
        patient_conditions = validated_data.pop('patient_conditions', [])
        auto_deduct_stock = validated_data.pop('auto_deduct_stock', False)
        calculate_renewal_date = validated_data.pop('calculate_renewal_date', True)
        
        user = self.context.get('request').user
        
        try:
            with transaction.atomic():
                # Create the medication
                medication = super().create(validated_data)
                
                # Store ICD-10 codes if provided
                if icd10_codes:
                    medication.icd10_codes = icd10_codes
                    medication.save()
                
                # Create schedules if provided
                created_schedules = []
                if schedules_data:
                    created_schedules = self._create_schedules(medication, schedules_data)
                elif prescription_instructions:
                    # Parse instructions and create schedules
                    parsed = PrescriptionParser.parse_instructions(prescription_instructions)
                    if parsed.get('schedules'):
                        created_schedules = self._create_schedules(medication, parsed['schedules'])
                
                # Deduct stock if requested
                if auto_deduct_stock and created_schedules:
                    self._deduct_stock_for_schedules(medication, created_schedules, user)
                
                # Create prescription renewal record if requested
                if calculate_renewal_date and prescription_instructions:
                    self._create_renewal_record(medication, prescription_instructions, user)
                
                # Log audit trail
                AuditLogger.log_prescription_creation(
                    user=user,
                    prescription_data={
                        'medication_name': medication.name,
                        'icd10_codes': icd10_codes,
                        'patient_conditions': patient_conditions
                    },
                    success=True,
                    errors=[]
                )
                
        except Exception as e:
            logger.error(f"Failed to create medication: {e}")
            AuditLogger.log_prescription_creation(
                user=user,
                prescription_data=validated_data,
                success=False,
                errors=[str(e)]
            )
            raise
        
        return medication
    
    def update(self, instance, validated_data):
        """Update medication with nested schedules."""
        # Extract schedule data
        schedules_data = validated_data.pop('schedules', [])
        icd10_codes = validated_data.pop('icd10_codes', [])
        prescription_instructions = validated_data.pop('prescription_instructions', None)
        patient_conditions = validated_data.pop('patient_conditions', [])
        
        # Update the medication
        medication = super().update(instance, validated_data)
        
        # Update schedules if provided
        if schedules_data:
            # Remove existing schedules and create new ones
            medication.schedules.all().delete()
            self._create_schedules(medication, schedules_data)
        
        return medication
    
    def _create_schedules(self, medication, schedules_data):
        """Create medication schedules from data."""
        user = self.context.get('request').user
        created_schedules = []
        
        for schedule_data in schedules_data:
            schedule_data['medication'] = medication
            schedule_data['patient'] = user
            
            # Set default values
            schedule_data.setdefault('status', MedicationSchedule.Status.ACTIVE)
            schedule_data.setdefault('start_date', timezone.now().date())
            schedule_data.setdefault('monday', True)
            schedule_data.setdefault('tuesday', True)
            schedule_data.setdefault('wednesday', True)
            schedule_data.setdefault('thursday', True)
            schedule_data.setdefault('friday', True)
            schedule_data.setdefault('saturday', True)
            schedule_data.setdefault('sunday', True)
            
            schedule = MedicationSchedule.objects.create(**schedule_data)
            created_schedules.append(schedule)
        
        return created_schedules
    
    def _deduct_stock_for_schedules(self, medication, schedules, user):
        """Deduct stock for created schedules."""
        # Calculate required stock for 30 days
        total_required = 0
        for schedule in schedules:
            daily_consumption = StockDeductionManager._get_daily_consumption(
                schedule.frequency, schedule.dosage_amount
            )
            total_required += int(daily_consumption * 30)
        
        # Check availability and deduct
        availability = StockDeductionManager.check_stock_availability(medication.id, total_required)
        
        if availability['is_available']:
            success = StockDeductionManager.deduct_stock(medication.id, total_required, user, "Schedule creation")
            if not success:
                logger.warning(f"Failed to deduct stock for medication {medication.id}")
        else:
            logger.warning(f"Insufficient stock for medication {medication.id}: {availability['shortfall']} short")
    
    def _create_renewal_record(self, medication, prescription_instructions, user):
        """Create prescription renewal record."""
        try:
            # Calculate renewal date
            renewal_date = PrescriptionRenewalCalculator.calculate_renewal_date(
                quantity=medication.pill_count,
                frequency='daily',  # Default - could be extracted from instructions
                dosage_amount=Decimal('1')
            )
            
            # Create renewal record
            PrescriptionRenewal.objects.create(
                patient=user,
                medication=medication,
                prescription_number=f"RENEWAL-{medication.id}",
                prescribed_by="System Generated",
                prescribed_date=timezone.now().date(),
                expiry_date=renewal_date,
                status=PrescriptionRenewal.Status.ACTIVE,
                priority=PrescriptionRenewal.Priority.MEDIUM,
                notes=f"Auto-generated from prescription: {prescription_instructions[:100]}"
            )
        except Exception as e:
            logger.error(f"Failed to create renewal record for medication {medication.id}: {e}")


class MedicationScheduleSerializer(serializers.ModelSerializer):
    """Basic serializer for MedicationSchedule model."""
    
    patient = UserSerializer(read_only=True)
    medication = MedicationSerializer(read_only=True)
    medication_id = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(),
        source='medication',
        write_only=True
    )
    
    class Meta:
        model = MedicationSchedule
        fields = [
            'id', 'patient', 'medication', 'medication_id', 'timing',
            'custom_time', 'dosage_amount', 'frequency', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'start_date', 'end_date', 'status', 'instructions', 'is_active',
            'should_take_today', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'is_active', 'should_take_today', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Set the patient to the current user."""
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class MedicationScheduleDetailSerializer(MedicationScheduleSerializer):
    """Detailed serializer for MedicationSchedule model."""
    
    class Meta(MedicationScheduleSerializer.Meta):
        fields = MedicationScheduleSerializer.Meta.fields


class MedicationLogSerializer(serializers.ModelSerializer):
    """Basic serializer for MedicationLog model."""
    
    patient = UserSerializer(read_only=True)
    medication = MedicationSerializer(read_only=True)
    schedule = MedicationScheduleSerializer(read_only=True)
    medication_id = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(),
        source='medication',
        write_only=True
    )
    schedule_id = serializers.PrimaryKeyRelatedField(
        queryset=MedicationSchedule.objects.all(),
        source='schedule',
        write_only=True,
        required=False,
        allow_null=True
    )
    
    class Meta:
        model = MedicationLog
        fields = [
            'id', 'patient', 'medication', 'medication_id', 'schedule',
            'schedule_id', 'scheduled_time', 'actual_time', 'status',
            'dosage_taken', 'notes', 'side_effects', 'is_on_time',
            'adherence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'patient', 'is_on_time', 'adherence_score', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Set the patient to the current user."""
        validated_data['patient'] = self.context['request'].user
        return super().create(validated_data)


class MedicationLogDetailSerializer(MedicationLogSerializer):
    """Detailed serializer for MedicationLog model."""
    
    class Meta(MedicationLogSerializer.Meta):
        fields = MedicationLogSerializer.Meta.fields


class StockAlertSerializer(serializers.ModelSerializer):
    """Basic serializer for StockAlert model."""
    
    medication = MedicationSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    acknowledged_by = UserSerializer(read_only=True)
    medication_id = serializers.PrimaryKeyRelatedField(
        queryset=Medication.objects.all(),
        source='medication',
        write_only=True
    )
    
    class Meta:
        model = StockAlert
        fields = [
            'id', 'medication', 'medication_id', 'created_by', 'acknowledged_by',
            'alert_type', 'priority', 'status', 'title', 'message',
            'current_stock', 'threshold_level', 'resolved_at', 'resolution_notes',
            'is_active', 'is_critical', 'created_at', 'updated_at', 'acknowledged_at'
        ]
        read_only_fields = [
            'id', 'created_by', 'acknowledged_by', 'is_active', 'is_critical',
            'created_at', 'updated_at', 'acknowledged_at'
        ]
    
    def create(self, validated_data):
        """Set the created_by to the current user."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class StockAlertDetailSerializer(StockAlertSerializer):
    """Detailed serializer for StockAlert model."""
    
    class Meta(StockAlertSerializer.Meta):
        fields = StockAlertSerializer.Meta.fields


class StockAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for StockAnalytics model."""
    
    medication = MedicationSerializer(read_only=True)
    
    class Meta:
        model = StockAnalytics
        fields = [
            'id', 'medication', 'daily_usage_rate', 'weekly_usage_rate',
            'monthly_usage_rate', 'days_until_stockout', 'predicted_stockout_date',
            'recommended_order_quantity', 'recommended_order_date',
            'seasonal_factor', 'usage_volatility', 'stockout_confidence',
            'last_calculated', 'calculation_window_days', 'is_stockout_imminent',
            'is_order_needed'
        ]
        read_only_fields = [
            'id', 'is_stockout_imminent', 'is_order_needed', 'last_calculated'
        ]


class StockVisualizationSerializer(serializers.ModelSerializer):
    """Serializer for StockVisualization model."""
    
    medication = MedicationSerializer(read_only=True)
    
    class Meta:
        model = StockVisualization
        fields = [
            'id', 'medication', 'chart_type', 'title', 'description',
            'chart_data', 'chart_options', 'start_date', 'end_date',
            'is_active', 'auto_refresh', 'refresh_interval_hours',
            'last_generated', 'needs_refresh', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'needs_refresh', 'last_generated', 'created_at', 'updated_at'
        ]


class PharmacyIntegrationSerializer(serializers.ModelSerializer):
    """Serializer for PharmacyIntegration model."""
    
    class Meta:
        model = PharmacyIntegration
        fields = [
            'id', 'name', 'pharmacy_name', 'integration_type', 'status',
            'api_endpoint', 'api_key', 'webhook_url', 'auto_order_enabled',
            'order_threshold', 'order_quantity_multiplier', 'order_lead_time_days',
            'last_sync', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_sync', 'created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True}
        }
    
    def to_representation(self, instance):
        """Remove sensitive data from response."""
        data = super().to_representation(instance)
        if 'api_key' in data:
            data['api_key'] = '***' if instance.api_key else None
        return data


class MedicationStatsSerializer(serializers.Serializer):
    """Serializer for medication statistics."""
    
    total_medications = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    expiring_soon_count = serializers.IntegerField()
    expired_count = serializers.IntegerField()
    active_schedules = serializers.IntegerField()
    today_schedules = serializers.IntegerField()
    active_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    adherence_rate = serializers.FloatField()
    
    def to_representation(self, instance):
        """Calculate and return medication statistics."""
        user = self.context['request'].user
        
        # Medication counts
        medications = Medication.objects.all()
        total_medications = medications.count()
        low_stock_count = medications.filter(
            pill_count__lte=F('low_stock_threshold')
        ).count()
        
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        expiring_soon_count = medications.filter(
            expiration_date__lte=thirty_days_from_now,
            expiration_date__gte=timezone.now().date()
        ).count()
        
        expired_count = medications.filter(
            expiration_date__lt=timezone.now().date()
        ).count()
        
        # Schedule counts
        if user.user_type == 'PATIENT':
            schedules = MedicationSchedule.objects.filter(patient=user)
        elif user.user_type == 'CAREGIVER':
            schedules = MedicationSchedule.objects.filter(patient__caregiver=user)
        else:
            schedules = MedicationSchedule.objects.all()
        
        active_schedules = schedules.filter(status=MedicationSchedule.Status.ACTIVE).count()
        
        # Today's schedules
        today = timezone.now().date()
        weekday = today.strftime('%A').lower()
        today_schedules = schedules.filter(
            Q(status=MedicationSchedule.Status.ACTIVE) &
            Q(start_date__lte=today) &
            (Q(end_date__isnull=True) | Q(end_date__gte=today))
        )
        
        # Filter by day of week
        day_filter = Q()
        if weekday == 'monday':
            day_filter = Q(monday=True)
        elif weekday == 'tuesday':
            day_filter = Q(tuesday=True)
        elif weekday == 'wednesday':
            day_filter = Q(wednesday=True)
        elif weekday == 'thursday':
            day_filter = Q(thursday=True)
        elif weekday == 'friday':
            day_filter = Q(friday=True)
        elif weekday == 'saturday':
            day_filter = Q(saturday=True)
        elif weekday == 'sunday':
            day_filter = Q(sunday=True)
        
        today_schedules = today_schedules.filter(day_filter).count()
        
        # Alert counts
        alerts = StockAlert.objects.all()
        active_alerts = alerts.filter(status=StockAlert.Status.ACTIVE).count()
        critical_alerts = alerts.filter(
            priority=StockAlert.Priority.CRITICAL,
            status=StockAlert.Status.ACTIVE
        ).count()
        
        # Adherence rate
        if user.user_type == 'PATIENT':
            logs = MedicationLog.objects.filter(patient=user)
        elif user.user_type == 'CAREGIVER':
            logs = MedicationLog.objects.filter(patient__caregiver=user)
        else:
            logs = MedicationLog.objects.all()
        
        total_logs = logs.count()
        taken_logs = logs.filter(status=MedicationLog.Status.TAKEN).count()
        adherence_rate = (taken_logs / total_logs * 100) if total_logs > 0 else 0
        
        return {
            'total_medications': total_medications,
            'low_stock_count': low_stock_count,
            'expiring_soon_count': expiring_soon_count,
            'expired_count': expired_count,
            'active_schedules': active_schedules,
            'today_schedules': today_schedules,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
            'adherence_rate': round(adherence_rate, 2)
        } 