"""
Serializers for security models.

This module provides serializers for audit logs and security events
for API access and data validation.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from .audit import AuditLog
from .models import SecurityEvent

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model in audit logs."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'user_type']


class ContentTypeSerializer(serializers.ModelSerializer):
    """Serializer for ContentType model in audit logs."""
    
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model.
    
    Provides comprehensive serialization of audit log entries
    for API access and compliance reporting.
    """
    
    user = UserSerializer(read_only=True)
    content_type = ContentTypeSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'action_display', 'severity', 'severity_display',
            'content_type', 'object_id', 'object_repr', 'changes', 'previous_values',
            'new_values', 'ip_address', 'user_agent', 'request_path', 'request_method',
            'session_id', 'description', 'metadata', 'timestamp', 'retention_date',
            'is_anonymized'
        ]
        read_only_fields = fields
    
    def to_representation(self, instance):
        """Custom representation to handle sensitive data."""
        data = super().to_representation(instance)
        
        # Mask sensitive information if user is not admin
        request = self.context.get('request')
        if request and not request.user.is_staff:
            # Mask IP addresses for non-admin users
            if data.get('ip_address'):
                ip_parts = data['ip_address'].split('.')
                if len(ip_parts) == 4:
                    data['ip_address'] = f"{ip_parts[0]}.{ip_parts[1]}.*.*"
            
            # Mask user agent for non-admin users
            if data.get('user_agent'):
                data['user_agent'] = data['user_agent'][:50] + '...' if len(data['user_agent']) > 50 else data['user_agent']
        
        return data


class SecurityEventSerializer(serializers.ModelSerializer):
    """
    Serializer for SecurityEvent model.
    
    Provides serialization of security events for monitoring
    and alerting purposes.
    """
    
    user = UserSerializer(read_only=True)
    event_type_display = serializers.CharField(source='get_event_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'user', 'event_type', 'event_type_display', 'severity', 'severity_display',
            'description', 'ip_address', 'user_agent', 'request_path', 'request_method',
            'metadata', 'timestamp', 'is_resolved', 'resolution_notes'
        ]
        read_only_fields = fields
    
    def to_representation(self, instance):
        """Custom representation to handle sensitive data."""
        data = super().to_representation(instance)
        
        # Mask sensitive information if user is not admin
        request = self.context.get('request')
        if request and not request.user.is_staff:
            # Mask IP addresses for non-admin users
            if data.get('ip_address'):
                ip_parts = data['ip_address'].split('.')
                if len(ip_parts) == 4:
                    data['ip_address'] = f"{ip_parts[0]}.{ip_parts[1]}.*.*"
            
            # Mask user agent for non-admin users
            if data.get('user_agent'):
                data['user_agent'] = data['user_agent'][:50] + '...' if len(data['user_agent']) > 50 else data['user_agent']
        
        return data


class AuditLogSummarySerializer(serializers.Serializer):
    """
    Serializer for audit log summary statistics.
    """
    
    total_actions = serializers.IntegerField()
    actions_by_type = serializers.ListField()
    actions_by_severity = serializers.ListField()
    top_users = serializers.ListField()
    recent_security_events = AuditLogSerializer(many=True)
    date_range = serializers.DictField()


class SecurityDashboardSerializer(serializers.Serializer):
    """
    Serializer for security dashboard data.
    """
    
    metrics = serializers.DictField()
    recent_incidents = AuditLogSerializer(many=True)
    suspicious_ips = serializers.ListField()
    date_range = serializers.DictField()


class SecurityEventLogSerializer(serializers.Serializer):
    """
    Serializer for logging security events via API.
    """
    
    event_type = serializers.CharField(max_length=50)
    description = serializers.CharField(max_length=500)
    severity = serializers.ChoiceField(
        choices=AuditLog.Severity.choices,
        default=AuditLog.Severity.MEDIUM
    )
    metadata = serializers.DictField(required=False, default=dict)
    
    def validate_event_type(self, value):
        """Validate event type."""
        valid_types = [
            'login_failed', 'access_denied', 'breach_attempt', 'data_access',
            'data_modification', 'data_export', 'user_creation', 'user_modification',
            'permission_change', 'system_error', 'security_alert'
        ]
        
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid event type. Must be one of: {', '.join(valid_types)}")
        
        return value


class AuditLogFilterSerializer(serializers.Serializer):
    """
    Serializer for audit log filtering parameters.
    """
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    user_id = serializers.IntegerField(required=False)
    action_type = serializers.CharField(max_length=50, required=False)
    severity = serializers.ChoiceField(choices=AuditLog.Severity.choices, required=False)
    ip_address = serializers.IPAddressField(required=False)
    search = serializers.CharField(max_length=100, required=False)
    ordering = serializers.CharField(max_length=50, required=False)
    
    def validate(self, data):
        """Validate date range."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return data


class SecurityEventFilterSerializer(serializers.Serializer):
    """
    Serializer for security event filtering parameters.
    """
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    event_type = serializers.CharField(max_length=50, required=False)
    severity = serializers.ChoiceField(choices=SecurityEvent.Severity.choices, required=False)
    is_resolved = serializers.BooleanField(required=False)
    search = serializers.CharField(max_length=100, required=False)
    ordering = serializers.CharField(max_length=50, required=False)
    
    def validate(self, data):
        """Validate date range."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return data 