"""
Serializers for medications app.

This module contains DRF serializers for the medication models.
"""

import re
from typing import Dict, List, Optional, Tuple
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import datetime, timedelta, time
from django.db.models import F, Q
from decimal import Decimal

from .models import (
    Medication, MedicationSchedule, MedicationLog, StockAlert,
    StockAnalytics, StockVisualization, PharmacyIntegration,
    StockTransaction, PrescriptionRenewal
)

User = get_user_model()


class ICD10Validator:
    """
    Validator for ICD-10 codes.
    
    ICD-10 codes follow the pattern: [A-Z][0-9][0-9].[0-9X][0-9X]?
    Examples: A00.0, B01.1, C78.01, Z51.11
    """
    
    ICD10_PATTERN = re.compile(r'^[A-Z][0-9][0-9]\.[0-9X][0-9X]?$')
    
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


class PrescriptionParser:
    """
    Parser for prescription instructions to extract dosage and timing information.
    
    Handles common prescription patterns like:
    - "Take one tablet daily"
    - "Take two tablets at 12h00"
    - "Take 1 capsule three times daily"
    - "Take 2 tablets morning and evening"
    """
    
    # Common dosage patterns
    DOSAGE_PATTERNS = [
        r'take\s+(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(tablets|capsules|drops|puffs|tablet|capsule|drop|puff|ml|mg|mcg)',
        r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(tablets|capsules|drops|puffs|tablet|capsule|drop|puff|ml|mg|mcg)\s+(?:to\s+)?take',
        r'(one|two|three|four|five|six|seven|eight|nine|ten|\d+(?:\.\d+)?)\s*(tablets|capsules|drops|puffs|tablet|capsule|drop|puff|ml|mg|mcg)\s+(?:per\s+)?dose',
    ]
    
    # Frequency patterns
    FREQUENCY_PATTERNS = [
        (r'four\s+times\s+daily|4x\s+daily', 'four_times_daily'),
        (r'three\s+times\s+daily|thrice\s+daily|3x\s+daily', 'three_times_daily'),
        (r'twice\s+daily|two\s+times\s+daily|2x\s+daily', 'twice_daily'),
        (r'weekly|once\s+a\s+week', 'weekly'),
        (r'monthly|once\s+a\s+month', 'monthly'),
        (r'as\s+needed|prn|when\s+needed', 'as_needed'),
        (r'daily|once\s+a\s+day|every\s+day', 'daily'),
    ]
    
    # Time patterns
    TIME_PATTERNS = [
        (r'(\d{1,2})h(\d{2})?|(\d{1,2}):(\d{2})', 'custom'),
        (r'morning|am|before\s+breakfast', 'morning'),
        (r'noon|midday|12h00|12:00', 'noon'),
        (r'evening|pm|before\s+bed|night', 'night'),
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
            'schedules': []
        }
        
        # Extract dosage amount and unit
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
                result['dosage_amount'] = Decimal(amount_str)
                result['dosage_unit'] = match.group(2)
                break
        
        # Extract frequency
        for pattern, frequency in cls.FREQUENCY_PATTERNS:
            if re.search(pattern, instructions_lower):
                result['frequency'] = frequency
                break
        
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
                
                # Auto-set frequency based on number of times
                if len(custom_times) == 2:
                    result['frequency'] = 'twice_daily'
                elif len(custom_times) == 3:
                    result['frequency'] = 'three_times_daily'
                elif len(custom_times) == 4:
                    result['frequency'] = 'four_times_daily'
        else:
            # Extract single timing
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
                        break
                elif re.search(pattern, instructions_lower):
                    result['timing'] = timing
                    break
        
        # Generate schedules based on frequency
        result['schedules'] = cls._generate_schedules(result)
        
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
    Validator for medication interactions and contraindications.
    """
    
    # Common drug interactions (simplified - in production, use a comprehensive drug database)
    KNOWN_INTERACTIONS = {
        'warfarin': ['aspirin', 'ibuprofen', 'naproxen', 'heparin'],
        'digoxin': ['furosemide', 'spironolactone', 'quinidine'],
        'lithium': ['ibuprofen', 'naproxen', 'thiazide_diuretics'],
        'phenytoin': ['warfarin', 'oral_contraceptives', 'corticosteroids'],
        'theophylline': ['ciprofloxacin', 'erythromycin', 'cimetidine'],
    }
    
    # Common contraindications
    CONTRAINDICATIONS = {
        'pregnancy': ['warfarin', 'isotretinoin', 'thalidomide', 'methotrexate'],
        'liver_disease': ['acetaminophen', 'statins', 'methotrexate'],
        'kidney_disease': ['nsaids', 'aminoglycosides', 'metformin'],
        'heart_disease': ['sildenafil', 'nitrates', 'beta_blockers'],
    }
    
    @classmethod
    def check_interactions(cls, medication_name: str, existing_medications: List[str]) -> List[str]:
        """Check for potential drug interactions."""
        interactions = []
        medication_lower = medication_name.lower()
        
        for drug, interacting_drugs in cls.KNOWN_INTERACTIONS.items():
            if drug in medication_lower:
                for existing_med in existing_medications:
                    if any(interacting_drug in existing_med.lower() for interacting_drug in interacting_drugs):
                        interactions.append(f"Potential interaction between {medication_name} and {existing_med}")
        
        return interactions
    
    @classmethod
    def check_contraindications(cls, medication_name: str, patient_conditions: List[str]) -> List[str]:
        """Check for contraindications based on patient conditions."""
        contraindications = []
        medication_lower = medication_name.lower()
        
        for condition, contraindicated_drugs in cls.CONTRAINDICATIONS.items():
            if condition in patient_conditions:
                for drug in contraindicated_drugs:
                    if drug in medication_lower:
                        contraindications.append(f"{medication_name} may be contraindicated for {condition}")
        
        return contraindications


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'user_type']
        read_only_fields = ['id']


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
    - ICD-10 code validation
    - Prescription instruction parsing
    - Nested schedule creation
    - Drug interaction checking
    - Contraindication validation
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
    
    # Parsed prescription data (read-only)
    parsed_prescription = serializers.SerializerMethodField()
    interaction_warnings = serializers.SerializerMethodField()
    contraindication_warnings = serializers.SerializerMethodField()
    
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
        """Validate ICD-10 codes."""
        if value:
            for code in value:
                if not ICD10Validator.validate(code):
                    raise serializers.ValidationError(
                        f"Invalid ICD-10 code format: {code}. Expected format: A00.0"
                    )
        return [ICD10Validator.clean(code) for code in value] if value else []
    
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
        """Validate medication strength format."""
        if not value:
            raise serializers.ValidationError("Strength is required")
        
        # Basic strength validation (e.g., "500mg", "10mg/ml", "2.5mg")
        strength_pattern = re.compile(r'^\d+(?:\.\d+)?\s*(mg|mcg|g|ml|l|units?|iu|meq|mmol|%|mg/ml|mcg/ml|g/ml)$', re.IGNORECASE)
        if not strength_pattern.match(value.strip()):
            raise serializers.ValidationError(
                "Invalid strength format. Examples: 500mg, 10mg/ml, 2.5mg"
            )
        return value.strip()
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Validate dosage unit matches strength
        strength = attrs.get('strength', '')
        dosage_unit = attrs.get('dosage_unit', '')
        
        if strength and dosage_unit:
            # Extract unit from strength
            strength_unit_match = re.search(r'(mg|mcg|g|ml|l|units?|iu|meq|mmol|%)$', strength, re.IGNORECASE)
            if strength_unit_match:
                strength_unit = strength_unit_match.group(1).lower()
                if strength_unit != dosage_unit.lower():
                    raise serializers.ValidationError({
                        'dosage_unit': f"Dosage unit '{dosage_unit}' should match strength unit '{strength_unit}'"
                    })
        
        # Validate prescription instructions if provided
        prescription_instructions = attrs.get('prescription_instructions')
        if prescription_instructions:
            parsed = PrescriptionParser.parse_instructions(prescription_instructions)
            if not parsed.get('dosage_amount'):
                raise serializers.ValidationError({
                    'prescription_instructions': "Could not parse dosage amount from instructions"
                })
        
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
    
    def create(self, validated_data):
        """Create medication with nested schedules."""
        # Extract schedule data
        schedules_data = validated_data.pop('schedules', [])
        icd10_codes = validated_data.pop('icd10_codes', [])
        prescription_instructions = validated_data.pop('prescription_instructions', None)
        patient_conditions = validated_data.pop('patient_conditions', [])
        
        # Create the medication
        medication = super().create(validated_data)
        
        # Create schedules if provided
        if schedules_data:
            self._create_schedules(medication, schedules_data)
        elif prescription_instructions:
            # Parse instructions and create schedules
            parsed = PrescriptionParser.parse_instructions(prescription_instructions)
            if parsed.get('schedules'):
                self._create_schedules(medication, parsed['schedules'])
        
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
            
            MedicationSchedule.objects.create(**schedule_data)


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