"""
Serializers for medications app.

This module contains DRF serializers for the medication models.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import F, Q

from .models import (
    Medication, MedicationSchedule, MedicationLog, StockAlert,
    StockAnalytics, StockVisualization, PharmacyIntegration
)

User = get_user_model()


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
        if user.user_type == User.UserType.PATIENT:
            schedules = MedicationSchedule.objects.filter(patient=user)
        elif user.user_type == User.UserType.CAREGIVER:
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
        if user.user_type == User.UserType.PATIENT:
            logs = MedicationLog.objects.filter(patient=user)
        elif user.user_type == User.UserType.CAREGIVER:
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