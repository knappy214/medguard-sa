from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending AbstractUser for healthcare application.
    Includes additional fields relevant to medication management.
    """
    
    # User type choices
    class UserType(models.TextChoices):
        PATIENT = 'patient', _('Patient')
        CAREGIVER = 'caregiver', _('Caregiver')
        HEALTHCARE_PROVIDER = 'healthcare_provider', _('Healthcare Provider')
        ADMIN = 'admin', _('Administrator')
    
    # Gender choices
    class Gender(models.TextChoices):
        MALE = 'male', _('Male')
        FEMALE = 'female', _('Female')
        OTHER = 'other', _('Other')
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', _('Prefer not to say')
    
    # Additional fields
    user_type = models.CharField(
        max_length=20,
        choices=UserType.choices,
        default=UserType.PATIENT,
        help_text=_('Type of user in the healthcare system')
    )
    
    # Personal information
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text=_('User\'s date of birth')
    )
    
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        null=True,
        blank=True,
        help_text=_('User\'s gender')
    )
    
    # Contact information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Phone number in international format')
    )
    
    # Medical information
    medical_record_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text=_('Unique medical record number')
    )
    
    emergency_contact_name = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Name of emergency contact')
    )
    
    emergency_contact_phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Emergency contact phone number')
    )
    
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('Relationship to emergency contact')
    )
    
    # Healthcare provider information
    primary_healthcare_provider = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Name of primary healthcare provider')
    )
    
    healthcare_provider_phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Healthcare provider phone number')
    )
    
    # Preferences and settings
    preferred_language = models.CharField(
        max_length=10,
        default='en',
        choices=[
            ('en', 'English'),
            ('af', 'Afrikaans'),
        ],
        help_text=_('Preferred language for communications')
    )
    
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        help_text=_('User\'s timezone for medication scheduling')
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive email notifications')
    )
    
    sms_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive SMS notifications')
    )
    
    push_notifications = models.BooleanField(
        default=True,
        help_text=_('Receive push notifications')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
        indexes = [
            models.Index(fields=['user_type']),
            models.Index(fields=['medical_record_number']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def get_short_name(self):
        """Return the short name of the user."""
        return self.first_name or self.username
    
    @property
    def is_patient(self):
        """Check if user is a patient."""
        return self.user_type == self.UserType.PATIENT
    
    @property
    def is_caregiver(self):
        """Check if user is a caregiver."""
        return self.user_type == self.UserType.CAREGIVER
    
    @property
    def is_healthcare_provider(self):
        """Check if user is a healthcare provider."""
        return self.user_type == self.UserType.HEALTHCARE_PROVIDER
    
    @property
    def age(self):
        """Calculate user's age based on date of birth."""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    def clean(self):
        """Custom validation for the model."""
        from django.core.exceptions import ValidationError
        
        # Validate medical record number format for patients
        if self.is_patient and self.medical_record_number:
            if not self.medical_record_number.startswith('MRN-'):
                raise ValidationError({
                    'medical_record_number': _('Medical record number must start with "MRN-"')
                })
        
        # Validate emergency contact information
        if self.emergency_contact_name and not self.emergency_contact_phone:
            raise ValidationError({
                'emergency_contact_phone': _('Emergency contact phone is required when emergency contact name is provided')
            })
        
        if self.emergency_contact_phone and not self.emergency_contact_name:
            raise ValidationError({
                'emergency_contact_name': _('Emergency contact name is required when emergency contact phone is provided')
            })
    
    def save(self, *args, **kwargs):
        """Override save to ensure medical record number is generated for patients."""
        if self.is_patient and not self.medical_record_number:
            # Generate medical record number
            import uuid
            self.medical_record_number = f"MRN-{uuid.uuid4().hex[:8].upper()}"
        
        self.full_clean()
        super().save(*args, **kwargs)
