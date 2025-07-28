"""
Serializers for users app.

This module contains DRF serializers for the User model.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Basic serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'user_type', 'date_of_birth', 'gender', 'phone_number',
            'medical_record_number', 'preferred_language', 'timezone',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'medical_record_number', 'created_at', 'updated_at']


class UserDetailSerializer(UserSerializer):
    """Detailed serializer for User model with additional fields."""
    
    age = serializers.ReadOnlyField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'primary_healthcare_provider',
            'healthcare_provider_phone', 'email_notifications',
            'sms_notifications', 'push_notifications', 'age'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'password',
            'password_confirm', 'user_type', 'date_of_birth', 'gender',
            'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'primary_healthcare_provider',
            'healthcare_provider_phone', 'preferred_language', 'timezone',
            'email_notifications', 'sms_notifications', 'push_notifications'
        ]
    
    def validate(self, data):
        """Validate password confirmation."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return data
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user information."""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'date_of_birth', 'gender',
            'phone_number', 'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'primary_healthcare_provider',
            'healthcare_provider_phone', 'preferred_language', 'timezone',
            'email_notifications', 'sms_notifications', 'push_notifications'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing user password."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, data):
        """Validate password change data."""
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New passwords do not match.'
            })
        return data
    
    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information."""
    
    age = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField(source='get_full_name')
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'user_type',
            'date_of_birth', 'age', 'gender', 'phone_number',
            'medical_record_number', 'preferred_language', 'timezone',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'primary_healthcare_provider',
            'healthcare_provider_phone', 'email_notifications',
            'sms_notifications', 'push_notifications', 'created_at'
        ]
        read_only_fields = ['id', 'username', 'medical_record_number', 'created_at']


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list views."""
    
    full_name = serializers.ReadOnlyField(source='get_full_name')
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email', 'user_type',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at'] 