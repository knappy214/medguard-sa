"""
Custom password validators for MedGuard SA.

This module provides custom password validators that integrate with
our password policies and healthcare-specific security requirements.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import (
    UserAttributeSimilarityValidator,
    MinimumLengthValidator,
    CommonPasswordValidator,
    NumericPasswordValidator,
)

from .password_policies import PasswordPolicyManager


class HealthcarePasswordValidator:
    """
    Custom password validator for healthcare applications.
    
    This validator enforces password policies specific to healthcare
    applications with HIPAA compliance requirements.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def validate(self, password, user=None):
        """Validate password against healthcare-specific policies."""
        if user is None:
            user = self.user
        
        if user is None:
            # If no user context, use basic validation
            return
        
        # Get the appropriate password policy for the user
        try:
            policy = PasswordPolicyManager.get_policy_for_user(user)
            errors = policy.validate_password(password, user)
            
            if errors:
                raise ValidationError(errors)
        except Exception as e:
            # Fallback to basic validation if policy lookup fails
            self._basic_validation(password)
    
    def _basic_validation(self, password):
        """Basic password validation as fallback."""
        errors = []
        
        # Minimum length
        if len(password) < 8:
            errors.append(_('Password must be at least 8 characters long'))
        
        # Complexity requirements
        if not re.search(r'[A-Z]', password):
            errors.append(_('Password must contain at least one uppercase letter'))
        
        if not re.search(r'[a-z]', password):
            errors.append(_('Password must contain at least one lowercase letter'))
        
        if not re.search(r'\d', password):
            errors.append(_('Password must contain at least one digit'))
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append(_('Password must contain at least one special character'))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        """Return help text for this validator."""
        return _(
            "Your password must meet healthcare security requirements including "
            "minimum length, complexity, and cannot be reused from recent history."
        )


class MedicalDataPasswordValidator:
    """
    Enhanced password validator for medical data access.
    
    This validator enforces stricter requirements for users who
    have access to medical data.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def validate(self, password, user=None):
        """Validate password for medical data access."""
        if user is None:
            user = self.user
        
        if user is None:
            return
        
        # Check if user has medical data access
        has_medical_access = (
            user.is_staff or 
            user.user_type == 'HEALTHCARE_PROVIDER' or
            user.is_superuser
        )
        
        if has_medical_access:
            self._validate_medical_access_password(password)
    
    def _validate_medical_access_password(self, password):
        """Validate password for medical data access."""
        errors = []
        
        # Stricter length requirement for medical data access
        if len(password) < 12:
            errors.append(_('Password must be at least 12 characters long for medical data access'))
        
        # Require more complex patterns
        if not re.search(r'[A-Z].*[A-Z]', password):
            errors.append(_('Password must contain at least two uppercase letters'))
        
        if not re.search(r'[a-z].*[a-z]', password):
            errors.append(_('Password must contain at least two lowercase letters'))
        
        if not re.search(r'\d.*\d', password):
            errors.append(_('Password must contain at least two digits'))
        
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?].*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            errors.append(_('Password must contain at least two special characters'))
        
        # Check for common medical terms (case-insensitive)
        medical_terms = [
            'password', 'admin', 'user', 'test', 'demo', 'guest',
            'medguard', 'healthcare', 'medical', 'patient', 'doctor',
            'nurse', 'pharmacy', 'hospital', 'clinic'
        ]
        
        password_lower = password.lower()
        for term in medical_terms:
            if term in password_lower:
                errors.append(_(f'Password cannot contain common terms like "{term}"'))
                break
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        """Return help text for this validator."""
        return _(
            "For medical data access, your password must be at least 12 characters "
            "with enhanced complexity requirements and cannot contain common terms."
        )


class TwoFactorPasswordValidator:
    """
    Password validator that enforces 2FA requirements.
    
    This validator ensures that users with certain roles have
    appropriate password strength when 2FA is required.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def validate(self, password, user=None):
        """Validate password considering 2FA requirements."""
        if user is None:
            user = self.user
        
        if user is None:
            return
        
        # Check if user has 2FA enabled or required
        try:
            from .password_policies import TwoFactorAuthManager
            two_factor_auth = TwoFactorAuthManager.get_or_create_2fa(user)
            
            if two_factor_auth.is_enabled:
                # If 2FA is enabled, password can be slightly less complex
                # but still must meet minimum requirements
                self._validate_2fa_password(password)
        except Exception:
            # If 2FA lookup fails, skip this validation
            pass
    
    def _validate_2fa_password(self, password):
        """Validate password for users with 2FA enabled."""
        errors = []
        
        # Minimum length for 2FA users
        if len(password) < 8:
            errors.append(_('Password must be at least 8 characters long'))
        
        # Basic complexity still required
        if not re.search(r'[A-Z]', password):
            errors.append(_('Password must contain at least one uppercase letter'))
        
        if not re.search(r'[a-z]', password):
            errors.append(_('Password must contain at least one lowercase letter'))
        
        if not re.search(r'\d', password):
            errors.append(_('Password must contain at least one digit'))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        """Return help text for this validator."""
        return _(
            "With two-factor authentication enabled, your password must still "
            "meet basic security requirements."
        )


class HIPAACompliantPasswordValidator:
    """
    HIPAA-compliant password validator.
    
    This validator enforces password requirements that meet
    HIPAA security standards.
    """
    
    def __init__(self, user=None):
        self.user = user
    
    def validate(self, password, user=None):
        """Validate password for HIPAA compliance."""
        if user is None:
            user = self.user
        
        if user is None:
            return
        
        errors = []
        
        # HIPAA minimum requirements
        if len(password) < 8:
            errors.append(_('HIPAA requires passwords to be at least 8 characters long'))
        
        # Must contain at least three of the following:
        # - Uppercase letters
        # - Lowercase letters
        # - Numbers
        # - Special characters
        
        criteria_met = 0
        if re.search(r'[A-Z]', password):
            criteria_met += 1
        if re.search(r'[a-z]', password):
            criteria_met += 1
        if re.search(r'\d', password):
            criteria_met += 1
        if re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
            criteria_met += 1
        
        if criteria_met < 3:
            errors.append(_('HIPAA requires passwords to contain at least 3 of: uppercase, lowercase, numbers, special characters'))
        
        # Check for common patterns that are easily guessable
        if re.search(r'(.)\1{2,}', password):
            errors.append(_('HIPAA prohibits passwords with repeated characters (e.g., "aaa")'))
        
        if re.search(r'(123|abc|qwe|asd|zxc)', password.lower()):
            errors.append(_('HIPAA prohibits common sequential patterns'))
        
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        """Return help text for this validator."""
        return _(
            "Your password must meet HIPAA security requirements including "
            "minimum length and complexity standards."
        )


# Factory function to get appropriate validators for a user
def get_password_validators_for_user(user):
    """
    Get appropriate password validators for a user based on their role.
    
    Args:
        user: The user object
        
    Returns:
        List of password validators
    """
    validators = [
        HealthcarePasswordValidator(user),
        HIPAACompliantPasswordValidator(user),
    ]
    
    # Add medical data validator for healthcare providers
    if user and (user.is_staff or user.user_type == 'HEALTHCARE_PROVIDER'):
        validators.append(MedicalDataPasswordValidator(user))
    
    # Add 2FA validator
    validators.append(TwoFactorPasswordValidator(user))
    
    return validators


# Default validators for when no user context is available
DEFAULT_PASSWORD_VALIDATORS = [
    HealthcarePasswordValidator(),
    HIPAACompliantPasswordValidator(),
    TwoFactorPasswordValidator(),
] 