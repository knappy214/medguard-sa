"""
Serializers for users app.

This module contains DRF serializers for the User model.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.validators import FileExtensionValidator
from .models import User, UserAvatar, UserProfile
import os

User = get_user_model()


class UserAvatarSerializer(serializers.ModelSerializer):
    """Serializer for user avatar"""
    url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAvatar
        fields = ['id', 'image', 'url', 'thumbnail_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'url', 'thumbnail_url', 'created_at', 'updated_at']
    
    def get_url(self, obj):
        """Get the avatar URL"""
        if obj and obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_thumbnail_url(self, obj):
        """Get the thumbnail URL"""
        if obj and obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.get_thumbnail_url())
            return obj.get_thumbnail_url()
        return None


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for extended user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'professional_title', 'license_number', 'specialization',
            'facility_name', 'facility_address', 'facility_phone',
            'notification_preferences', 'privacy_settings',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Main user serializer with all profile fields"""
    avatar = UserAvatarSerializer(read_only=True)
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.ReadOnlyField()
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'full_name', 'display_name',
            'phone', 'date_of_birth', 'gender',
            'address', 'city', 'province', 'postal_code',
            'blood_type', 'allergies', 'medical_conditions', 'current_medications',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'preferred_language', 'timezone',
            'email_notifications', 'sms_notifications', 'mfa_enabled',
            'avatar', 'profile',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def to_representation(self, instance):
        """Custom representation to include avatar URL"""
        data = super().to_representation(instance)
        
        # Add avatar URL if user has an avatar
        if hasattr(instance, 'avatar') and instance.avatar:
            data['avatar_url'] = instance.avatar.url
        else:
            data['avatar_url'] = None
        
        return data


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    avatar = UserAvatarSerializer(read_only=True)
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email',
            'phone', 'date_of_birth', 'gender',
            'address', 'city', 'province', 'postal_code',
            'blood_type', 'allergies', 'medical_conditions', 'current_medications',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'preferred_language', 'timezone',
            'email_notifications', 'sms_notifications', 'mfa_enabled',
            'avatar', 'profile'
        ]
        read_only_fields = ['avatar', 'profile']
    
    def update(self, instance, validated_data):
        """Update user instance and related profile data"""
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update or create profile
        profile_data = self.context.get('profile_data', {})
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class AvatarUploadSerializer(serializers.Serializer):
    """Serializer for avatar upload"""
    image = serializers.ImageField(
        max_length=None,
        allow_empty_file=False,
        use_url=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    
    def validate_image(self, value):
        """Validate uploaded image"""
        # Check file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Image file size must be less than 5MB.")
        
        # Check image dimensions
        if hasattr(value, 'image'):
            width, height = value.image.size
            if width > 2048 or height > 2048:
                raise serializers.ValidationError("Image dimensions must be less than 2048x2048 pixels.")
        
        return value
    
    def create(self, validated_data):
        """Create or update user avatar"""
        user = self.context['request'].user
        image = validated_data['image']
        
        # Delete existing avatar if it exists
        if hasattr(user, 'avatar') and user.avatar:
            user.avatar.delete()
        
        # Create new avatar
        avatar = UserAvatar.objects.create(user=user, image=image)
        return avatar
    
    def update(self, instance, validated_data):
        """Update existing avatar"""
        if 'image' in validated_data:
            # Delete old image file
            if instance.image:
                if hasattr(instance.image, 'path') and os.path.isfile(instance.image.path):
                    os.remove(instance.image.path)
            
            instance.image = validated_data['image']
            instance.save()
        
        return instance


class ProfilePreferencesSerializer(serializers.Serializer):
    """Serializer for user preferences"""
    notification_preferences = serializers.JSONField(required=False)
    privacy_settings = serializers.JSONField(required=False)
    
    def update(self, instance, validated_data):
        """Update user profile preferences"""
        profile, created = UserProfile.objects.get_or_create(user=instance)
        
        if 'notification_preferences' in validated_data:
            profile.notification_preferences = validated_data['notification_preferences']
        
        if 'privacy_settings' in validated_data:
            profile.privacy_settings = validated_data['privacy_settings']
        
        profile.save()
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change"""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password change data"""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError("Current password is incorrect.")
        
        return attrs
    
    def save(self):
        """Change user password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for user summary"""
    avatar_url = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'avatar_url', 'preferred_language']
    
    def get_avatar_url(self, obj):
        """Get avatar URL"""
        if hasattr(obj, 'avatar') and obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None 