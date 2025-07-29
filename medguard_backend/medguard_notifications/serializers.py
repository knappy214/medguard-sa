"""
Serializers for notifications app.

This module contains DRF serializers for the notification models.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from wagtail.rich_text import expand_db_html

from .models import Notification, UserNotification, NotificationTemplate

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['id']


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model."""
    
    created_by = UserSerializer(read_only=True)
    target_users = UserSerializer(many=True, read_only=True)
    content_html = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'content', 'content_html', 'notification_type',
            'priority', 'status', 'target_user_types', 'target_users',
            'scheduled_at', 'expires_at', 'is_active', 'show_on_dashboard',
            'require_acknowledgment', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_content_html(self, obj):
        """Convert rich text content to HTML."""
        if obj.content:
            return expand_db_html(obj.content)
        return ""
    
    def validate(self, data):
        """Custom validation for notification data."""
        # Validate expires_at is after scheduled_at
        if data.get('scheduled_at') and data.get('expires_at'):
            if data['expires_at'] <= data['scheduled_at']:
                raise serializers.ValidationError({
                    'expires_at': 'Expiration date must be after scheduled date'
                })
        
        return data


class NotificationDetailSerializer(NotificationSerializer):
    """Detailed serializer for Notification model with additional fields."""
    
    class Meta(NotificationSerializer.Meta):
        fields = NotificationSerializer.Meta.fields + [
            'is_expired', 'is_scheduled', 'is_critical'
        ]


class UserNotificationSerializer(serializers.ModelSerializer):
    """Serializer for UserNotification model."""
    
    notification = NotificationSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserNotification
        fields = [
            'id', 'user', 'notification', 'status', 'sent_at',
            'read_at', 'acknowledged_at', 'dismissed_at'
        ]
        read_only_fields = ['id', 'sent_at']


class UserNotificationDetailSerializer(UserNotificationSerializer):
    """Detailed serializer for UserNotification model."""
    
    class Meta(UserNotificationSerializer.Meta):
        fields = UserNotificationSerializer.Meta.fields + [
            'is_unread', 'is_read'
        ]


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model."""
    
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'content',
            'variables', 'is_active', 'created_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Custom validation for template data."""
        # Validate subject is provided for email templates
        if data.get('template_type') == NotificationTemplate.TemplateType.EMAIL:
            if not data.get('subject'):
                raise serializers.ValidationError({
                    'subject': 'Subject is required for email templates'
                })
        
        return data


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'title', 'content', 'notification_type', 'priority', 'status',
            'target_user_types', 'scheduled_at', 'expires_at', 'is_active',
            'show_on_dashboard', 'require_acknowledgment'
        ]
    
    def create(self, validated_data):
        """Create notification with current user as creator."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class NotificationTemplateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new notification templates."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'name', 'template_type', 'subject', 'content', 'variables', 'is_active'
        ]
    
    def create(self, validated_data):
        """Create template with current user as creator."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class NotificationBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on notifications."""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of notification IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'archive', 'delete'],
        help_text="Action to perform on selected notifications"
    )


class UserNotificationBulkActionSerializer(serializers.Serializer):
    """Serializer for bulk actions on user notifications."""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of user notification IDs to perform action on"
    )
    action = serializers.ChoiceField(
        choices=['mark_as_read', 'dismiss'],
        help_text="Action to perform on selected user notifications"
    ) 