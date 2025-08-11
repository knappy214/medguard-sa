import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from PIL import Image as PILImage
from io import BytesIO
from django.core.files import File
from wagtail.search import index


class User(AbstractUser):
    """
    Custom User model with healthcare-specific fields
    """
    # Override email to be unique and required
    email = models.EmailField(_('email address'), unique=True)
    
    # User type for role-based access
    user_type = models.CharField(
        max_length=20,
        choices=[
            ('PATIENT', _('Patient')),
            ('CAREGIVER', _('Caregiver')),
            ('HEALTHCARE_PROVIDER', _('Healthcare Provider')),
        ],
        default='PATIENT',
        verbose_name=_('User Type')
    )
    
    # Additional healthcare fields
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone Number'))
    date_of_birth = models.DateField(null=True, blank=True, verbose_name=_('Date of Birth'))
    gender = models.CharField(
        max_length=20,
        choices=[
            ('male', _('Male')),
            ('female', _('Female')),
            ('other', _('Other')),
            ('prefer_not_to_say', _('Prefer not to say')),
        ],
        blank=True,
        verbose_name=_('Gender')
    )
    
    # Address fields
    address = models.TextField(blank=True, verbose_name=_('Address'))
    city = models.CharField(max_length=100, blank=True, verbose_name=_('City'))
    province = models.CharField(
        max_length=50,
        choices=[
            ('gauteng', _('Gauteng')),
            ('western_cape', _('Western Cape')),
            ('kwazulu_natal', _('KwaZulu-Natal')),
            ('eastern_cape', _('Eastern Cape')),
            ('free_state', _('Free State')),
            ('mpumalanga', _('Mpumalanga')),
            ('limpopo', _('Limpopo')),
            ('north_west', _('North West')),
            ('northern_cape', _('Northern Cape')),
        ],
        blank=True,
        verbose_name=_('Province')
    )
    postal_code = models.CharField(max_length=10, blank=True, verbose_name=_('Postal Code'))
    
    # Medical information
    blood_type = models.CharField(
        max_length=15,
        choices=[
            ('a_positive', 'A+'),
            ('a_negative', 'A-'),
            ('b_positive', 'B+'),
            ('b_negative', 'B-'),
            ('ab_positive', 'AB+'),
            ('ab_negative', 'AB-'),
            ('o_positive', 'O+'),
            ('o_negative', 'O-'),
        ],
        blank=True,
        verbose_name=_('Blood Type')
    )
    allergies = models.TextField(blank=True, verbose_name=_('Allergies'))
    medical_conditions = models.TextField(blank=True, verbose_name=_('Medical Conditions'))
    current_medications = models.TextField(blank=True, verbose_name=_('Current Medications'))
    
    # Emergency contact
    emergency_contact_name = models.CharField(max_length=100, blank=True, verbose_name=_('Emergency Contact Name'))
    emergency_contact_phone = models.CharField(max_length=20, blank=True, verbose_name=_('Emergency Contact Phone'))
    emergency_contact_relationship = models.CharField(
        max_length=20,
        choices=[
            ('spouse', _('Spouse')),
            ('parent', _('Parent')),
            ('child', _('Child')),
            ('sibling', _('Sibling')),
            ('friend', _('Friend')),
            ('other', _('Other')),
        ],
        blank=True,
        verbose_name=_('Relationship to Emergency Contact')
    )
    
    # Account settings
    preferred_language = models.CharField(
        max_length=2,
        choices=[
            ('en', _('English')),
            ('af', _('Afrikaans')),
        ],
        default='en',
        verbose_name=_('Preferred Language')
    )
    timezone = models.CharField(
        max_length=50,
        choices=[
            ('Africa/Johannesburg', _('South Africa Standard Time (SAST)')),
            ('UTC', 'UTC'),
        ],
        default='Africa/Johannesburg',
        verbose_name=_('Timezone')
    )
    email_notifications = models.BooleanField(default=True, verbose_name=_('Email Notifications'))
    sms_notifications = models.BooleanField(default=False, verbose_name=_('SMS Notifications'))
    mfa_enabled = models.BooleanField(default=False, verbose_name=_('Two-Factor Authentication'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Wagtail 7.0.2: Enhanced search configuration with improved indexing
    search_fields = [
        # Primary search fields with boost factors
        index.SearchField('username', boost=2.0),
        index.SearchField('email', boost=2.0),
        index.SearchField('first_name', boost=1.5),
        index.SearchField('last_name', boost=1.5),
        index.SearchField('phone', boost=1.0),
        index.SearchField('address', boost=1.0),
        index.SearchField('city', boost=1.0),
        
        # Autocomplete fields for quick search
        index.AutocompleteField('username'),
        index.AutocompleteField('email'),
        index.AutocompleteField('first_name'),
        index.AutocompleteField('last_name'),
        index.AutocompleteField('phone'),
        
        # Filter fields for faceted search
        index.FilterField('user_type'),
        index.FilterField('gender'),
        index.FilterField('province'),
        index.FilterField('blood_type'),
        index.FilterField('preferred_language'),
        index.FilterField('timezone'),
        index.FilterField('is_active'),
        index.FilterField('is_staff'),
        index.FilterField('date_joined'),
        index.FilterField('last_login'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels with improved widgets
    panels = []
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.email
    
    @property
    def display_name(self):
        """Return a display name for the user"""
        return self.full_name or self.email
    
    # Wagtail 7.0.2: Enhanced admin display methods
    def get_admin_display_title(self):
        """Return the title to display in the admin interface"""
        return f"{self.display_name} ({self.email})"
    
    def get_admin_display_subtitle(self):
        """Return the subtitle to display in the admin interface"""
        return f"{self.get_user_type_display()} • {self.city or 'No city'}"
    
    def get_admin_url(self):
        """Return the admin URL for this user"""
        from django.urls import reverse
        return reverse('admin:users_user_change', args=[self.pk])
    
    def get_absolute_url(self):
        """Return the absolute URL for this user"""
        from django.urls import reverse
        return reverse('user_detail', args=[self.pk])
    
    def get_search_display_title(self):
        """Return the title to display in search results"""
        return self.get_admin_display_title()
    
    def get_search_description(self):
        """Return the description to display in search results"""
        return f"{self.get_user_type_display()} • {self.phone or 'No phone'}"
    
    def get_search_url(self, request=None):
        """Return the URL to display in search results"""
        return self.get_admin_url()
    
    def get_search_meta(self):
        """Return additional metadata for search results"""
        return {
            'user_type': self.user_type,
            'is_active': self.is_active,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None,
        }


class UserAvatar(models.Model):
    """
    User avatar model with optimized image upload support
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='avatar')
    image = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])],
        verbose_name=_('Avatar Image')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('user__username', boost=2.0),
        index.SearchField('user__email', boost=2.0),
        index.SearchField('user__first_name', boost=1.5),
        index.SearchField('user__last_name', boost=1.5),
        index.FilterField('created_at'),
        index.FilterField('updated_at'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = []
    
    class Meta:
        verbose_name = _('User Avatar')
        verbose_name_plural = _('User Avatars')
        db_table = 'users_user_avatar'
    
    def __str__(self):
        return f"Avatar for {self.user.email}"
    
    def save(self, *args, **kwargs):
        """Override save to optimize image before saving"""
        if self.image:
            self.optimize_image()
        super().save(*args, **kwargs)
    
    def optimize_image(self):
        """Optimize the uploaded image for web use"""
        if not self.image:
            return
        
        try:
            # Open the image
            img = PILImage.open(self.image)
            
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large (max 512x512 for avatars)
            max_size = (512, 512)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, PILImage.Resampling.LANCZOS)
            
            # Save optimized image
            output = BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            # Create a new file name
            name = self.image.name
            if not name.endswith('.jpg'):
                name = os.path.splitext(name)[0] + '.jpg'
            
            # Save the optimized image
            self.image.save(name, File(output), save=False)
            
        except Exception as e:
            # If optimization fails, keep the original image
            print(f"Image optimization failed: {e}")
    
    def delete(self, *args, **kwargs):
        """Delete the image file when the model is deleted"""
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)
    
    @property
    def url(self):
        """Return the avatar URL"""
        if self.image:
            return self.image.url
        return None
    
    def get_thumbnail_url(self, size='150x150'):
        """Return a thumbnail URL for the avatar"""
        if self.image:
            # For now, return the original image URL
            # In production, you could generate actual thumbnails
            return self.image.url
        return None


class UserProfile(models.Model):
    """
    Extended user profile model for additional healthcare data
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Professional information
    professional_title = models.CharField(max_length=100, blank=True, verbose_name=_('Professional Title'))
    license_number = models.CharField(max_length=50, blank=True, verbose_name=_('License Number'))
    specialization = models.CharField(max_length=100, blank=True, verbose_name=_('Specialization'))
    
    # Healthcare facility information
    facility_name = models.CharField(max_length=200, blank=True, verbose_name=_('Facility Name'))
    facility_address = models.TextField(blank=True, verbose_name=_('Facility Address'))
    facility_phone = models.CharField(max_length=20, blank=True, verbose_name=_('Facility Phone'))
    
    # Additional preferences
    notification_preferences = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Notification Preferences')
    )
    privacy_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Privacy Settings')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Wagtail 7.0.2: Enhanced search configuration
    search_fields = [
        index.SearchField('user__username', boost=2.0),
        index.SearchField('user__email', boost=2.0),
        index.SearchField('professional_title', boost=1.5),
        index.SearchField('license_number', boost=1.5),
        index.SearchField('specialization', boost=1.5),
        index.SearchField('facility_name', boost=1.0),
        index.SearchField('facility_address', boost=1.0),
        index.SearchField('facility_phone', boost=1.0),
        index.FilterField('created_at'),
        index.FilterField('updated_at'),
    ]
    
    # Wagtail 7.0.2: Enhanced admin panels
    panels = []
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        db_table = 'users_user_profile'
    
    def __str__(self):
        return f"Profile for {self.user.email}"
    
    # Wagtail 7.0.2: Enhanced admin display methods
    def get_admin_display_title(self):
        """Return the title to display in the admin interface"""
        return f"Profile: {self.user.display_name}"
    
    def get_admin_display_subtitle(self):
        """Return the subtitle to display in the admin interface"""
        return f"{self.professional_title or 'No title'} • {self.facility_name or 'No facility'}"
    
    def get_admin_url(self):
        """Return the admin URL for this profile"""
        from django.urls import reverse
        return reverse('admin:users_userprofile_change', args=[self.pk])
    
    def get_absolute_url(self):
        """Return the absolute URL for this profile"""
        from django.urls import reverse
        return reverse('user_profile_detail', args=[self.pk])
    
    def get_search_display_title(self):
        """Return the title to display in search results"""
        return self.get_admin_display_title()
    
    def get_search_description(self):
        """Return the description to display in search results"""
        return f"{self.professional_title or 'No title'} • {self.specialization or 'No specialization'}"
    
    def get_search_url(self, request=None):
        """Return the URL to display in search results"""
        return self.get_admin_url()
    
    def get_search_meta(self):
        """Return additional metadata for search results"""
        return {
            'professional_title': self.professional_title,
            'specialization': self.specialization,
            'facility_name': self.facility_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def avatar_url(self):
        """Return the user's avatar URL"""
        if hasattr(self.user, 'avatar') and self.user.avatar:
            return self.user.avatar.url
        return None
