"""
Authentication serializers for MedGuard SA.

This module provides serializers for JWT token generation and authentication
that work with the custom User model.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.utils import timezone
from security.jwt_auth import generate_secure_tokens

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that supports email-based login.
    """
    
    username_field = 'username_or_email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username_or_email'] = serializers.CharField(
            label='Username or Email',
            help_text='Enter your username or email address'
        )
    
    def validate(self, attrs):
        """
        Validate the login credentials and generate tokens.
        
        Args:
            attrs: Dictionary containing username_or_email and password
            
        Returns:
            Dictionary containing tokens and user information
            
        Raises:
            serializers.ValidationError: If authentication fails
        """
        username_or_email = attrs.get('username_or_email')
        password = attrs.get('password')
        
        if username_or_email and password:
            # Try to authenticate with the custom backend
            user = authenticate(
                self.context['request'],
                username=username_or_email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'No active account found with the given credentials'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'This account has been disabled.'
                )
            
            # Generate tokens
            tokens = generate_secure_tokens(user, self.context['request'])
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            return {
                'refresh': tokens['refresh'],
                'access': tokens['access'],
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': user.full_name,
                    'preferred_language': user.preferred_language,
                    'avatar_url': user.avatar.url if hasattr(user, 'avatar') and user.avatar else None,
                }
            }
        else:
            raise serializers.ValidationError(
                'Must include "username_or_email" and "password".'
            )


class LoginSerializer(serializers.Serializer):
    """
    Serializer for login requests.
    """
    
    # Accept both field names for compatibility
    username_or_email = serializers.CharField(
        label='Username or Email',
        help_text='Enter your username or email address',
        required=False
    )
    email = serializers.CharField(
        label='Email',
        help_text='Enter your email address',
        required=False
    )
    password = serializers.CharField(
        label='Password',
        style={'input_type': 'password'},
        help_text='Enter your password'
    )
    
    def validate(self, attrs):
        """
        Validate login credentials.
        
        Args:
            attrs: Dictionary containing username_or_email/email and password
            
        Returns:
            Dictionary with user information if authentication succeeds
            
        Raises:
            serializers.ValidationError: If authentication fails
        """
        # Handle both field names for compatibility
        username_or_email = attrs.get('username_or_email') or attrs.get('email')
        password = attrs.get('password')
        
        if not username_or_email:
            raise serializers.ValidationError(
                'Must include either "username_or_email" or "email" field.'
            )
        
        if not password:
            raise serializers.ValidationError(
                'Must include "password" field.'
            )
        
        if username_or_email and password:
            user = authenticate(
                self.context['request'],
                username=username_or_email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Invalid credentials. Please check your username/email and password.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'This account has been disabled. Please contact support.'
                )
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Generate secure tokens with metadata
            tokens = generate_secure_tokens(user, self.context['request'])
            
            attrs['user'] = user
            attrs['refresh'] = tokens['refresh']
            attrs['access'] = tokens['access']
            
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "username_or_email" and "password".'
            )


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        help_text='Password must be at least 8 characters long'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text='Please confirm your password'
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'preferred_language'
        ]
        extra_kwargs = {
            'username': {'help_text': 'Choose a unique username'},
            'email': {'help_text': 'Enter a valid email address'},
            'first_name': {'help_text': 'Enter your first name'},
            'last_name': {'help_text': 'Enter your last name'},
            'phone': {'help_text': 'Enter your phone number (optional)'},
            'preferred_language': {'help_text': 'Choose your preferred language'}
        }
    
    def validate(self, attrs):
        """
        Validate registration data.
        
        Args:
            attrs: Dictionary containing registration data
            
        Returns:
            Validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        
        # Check if username is already taken
        username = attrs.get('username')
        if username and User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError({
                'username': 'A user with this username already exists.'
            })
        
        # Check if email is already taken
        email = attrs.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({
                'email': 'A user with this email already exists.'
            })
        
        return attrs
    
    def create(self, validated_data):
        """
        Create a new user.
        
        Args:
            validated_data: Validated registration data
            
        Returns:
            Newly created User object
        """
        # Remove password_confirm from validated data
        validated_data.pop('password_confirm', None)
        
        # Create user with hashed password
        user = User.objects.create_user(**validated_data)
        
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset requests.
    """
    
    email = serializers.EmailField(
        help_text='Enter the email address associated with your account'
    )
    
    def validate_email(self, value):
        """
        Validate that the email exists in the system.
        
        Args:
            value: Email address to validate
            
        Returns:
            Validated email address
            
        Raises:
            serializers.ValidationError: If email doesn't exist
        """
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                'No user found with this email address.'
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    
    new_password = serializers.CharField(
        min_length=8,
        help_text='New password must be at least 8 characters long'
    )
    confirm_password = serializers.CharField(
        help_text='Please confirm your new password'
    )
    
    def validate(self, attrs):
        """
        Validate password reset data.
        
        Args:
            attrs: Dictionary containing new password data
            
        Returns:
            Validated data
            
        Raises:
            serializers.ValidationError: If validation fails
        """
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password and confirm_password and new_password != confirm_password:
            raise serializers.ValidationError({
                'confirm_password': 'Passwords do not match.'
            })
        
        return attrs 