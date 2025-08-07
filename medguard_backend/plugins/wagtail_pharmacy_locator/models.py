"""
Pharmacy Locator Models
Models for managing pharmacies, locations, inventory, and integrations.
"""
import uuid
from decimal import Decimal
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet

User = get_user_model()


class PharmacyType(models.TextChoices):
    """Choices for pharmacy types."""
    CHAIN = 'chain', _('Chain Pharmacy')
    INDEPENDENT = 'independent', _('Independent Pharmacy')
    HOSPITAL = 'hospital', _('Hospital Pharmacy')
    CLINIC = 'clinic', _('Clinic Pharmacy')
    SPECIALTY = 'specialty', _('Specialty Pharmacy')
    COMPOUNDING = 'compounding', _('Compounding Pharmacy')
    ONLINE = 'online', _('Online Pharmacy')


class PharmacyStatus(models.TextChoices):
    """Choices for pharmacy operational status."""
    ACTIVE = 'active', _('Active')
    TEMPORARILY_CLOSED = 'temp_closed', _('Temporarily Closed')
    PERMANENTLY_CLOSED = 'perm_closed', _('Permanently Closed')
    UNDER_RENOVATION = 'renovation', _('Under Renovation')
    PENDING_APPROVAL = 'pending', _('Pending Approval')


@register_snippet
class Pharmacy(models.Model):
    """Model representing a pharmacy location."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Basic information
    name = models.CharField(
        max_length=255,
        verbose_name=_("Pharmacy Name")
    )
    
    chain_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Chain Name"),
        help_text=_("Name of pharmacy chain if applicable")
    )
    
    pharmacy_type = models.CharField(
        max_length=20,
        choices=PharmacyType.choices,
        default=PharmacyType.INDEPENDENT,
        verbose_name=_("Pharmacy Type")
    )
    
    status = models.CharField(
        max_length=20,
        choices=PharmacyStatus.choices,
        default=PharmacyStatus.ACTIVE,
        verbose_name=_("Status")
    )
    
    # Contact information
    phone = models.CharField(
        max_length=20,
        verbose_name=_("Phone Number")
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email Address")
    )
    
    website = models.URLField(
        blank=True,
        verbose_name=_("Website")
    )
    
    # Address and location
    street_address = models.CharField(
        max_length=255,
        verbose_name=_("Street Address")
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name=_("City")
    )
    
    province = models.CharField(
        max_length=100,
        verbose_name=_("Province/State")
    )
    
    postal_code = models.CharField(
        max_length=20,
        verbose_name=_("Postal Code")
    )
    
    country = models.CharField(
        max_length=100,
        default="South Africa",
        verbose_name=_("Country")
    )
    
    # Geographic coordinates
    location = gis_models.PointField(
        null=True,
        blank=True,
        verbose_name=_("Geographic Location"),
        help_text=_("Latitude and longitude coordinates")
    )
    
    # Operating hours
    operating_hours = models.JSONField(
        default=dict,
        verbose_name=_("Operating Hours"),
        help_text=_("Weekly operating hours in JSON format")
    )
    
    # Services offered
    services = models.JSONField(
        default=list,
        verbose_name=_("Services Offered"),
        help_text=_("List of services provided by this pharmacy")
    )
    
    # Insurance and payment
    accepted_insurance = models.JSONField(
        default=list,
        verbose_name=_("Accepted Insurance"),
        help_text=_("List of accepted insurance providers")
    )
    
    payment_methods = models.JSONField(
        default=list,
        verbose_name=_("Payment Methods"),
        help_text=_("Accepted payment methods")
    )
    
    # Ratings and reviews
    average_rating = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        verbose_name=_("Average Rating")
    )
    
    total_reviews = models.IntegerField(
        default=0,
        verbose_name=_("Total Reviews")
    )
    
    # Integration data
    external_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("External System ID"),
        help_text=_("ID in external pharmacy management system")
    )
    
    api_endpoint = models.URLField(
        blank=True,
        verbose_name=_("API Endpoint"),
        help_text=_("API endpoint for real-time inventory checks")
    )
    
    api_credentials = models.JSONField(
        default=dict,
        verbose_name=_("API Credentials"),
        help_text=_("Encrypted API credentials for integration")
    )
    
    # Features and amenities
    has_drive_through = models.BooleanField(
        default=False,
        verbose_name=_("Drive-Through Available")
    )
    
    has_parking = models.BooleanField(
        default=True,
        verbose_name=_("Parking Available")
    )
    
    wheelchair_accessible = models.BooleanField(
        default=True,
        verbose_name=_("Wheelchair Accessible")
    )
    
    has_consultation_room = models.BooleanField(
        default=False,
        verbose_name=_("Private Consultation Room")
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Verified")
    )
    
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Verified By")
    )
    
    notes = RichTextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Pharmacy")
        verbose_name_plural = _("Pharmacies")
        ordering = ["name"]
        indexes = [
            models.Index(fields=['status', 'pharmacy_type']),
            models.Index(fields=['city', 'province']),
            models.Index(fields=['postal_code']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.city}"
    
    def get_full_address(self):
        """Get formatted full address."""
        return f"{self.street_address}, {self.city}, {self.province} {self.postal_code}"
    
    def is_open_now(self):
        """Check if pharmacy is currently open."""
        if self.status != PharmacyStatus.ACTIVE:
            return False
        
        if not self.operating_hours:
            return False
        
        now = timezone.now()
        current_day = now.strftime('%A').lower()
        current_time = now.time()
        
        day_hours = self.operating_hours.get(current_day)
        if not day_hours or not day_hours.get('open'):
            return False
        
        try:
            open_time = timezone.datetime.strptime(day_hours['open'], '%H:%M').time()
            close_time = timezone.datetime.strptime(day_hours['close'], '%H:%M').time()
            
            return open_time <= current_time <= close_time
        except (KeyError, ValueError):
            return False
    
    def get_distance_from(self, latitude, longitude):
        """Calculate distance from given coordinates."""
        if not self.location:
            return None
        
        from django.contrib.gis.geos import Point
        from django.contrib.gis.measure import Distance
        
        point = Point(longitude, latitude)
        return self.location.distance(point)
    
    panels = [
        MultiFieldPanel([
            FieldPanel("name"),
            FieldPanel("chain_name"),
            FieldPanel("pharmacy_type"),
            FieldPanel("status"),
        ], heading=_("Basic Information")),
        
        MultiFieldPanel([
            FieldPanel("phone"),
            FieldPanel("email"),
            FieldPanel("website"),
        ], heading=_("Contact Information")),
        
        MultiFieldPanel([
            FieldPanel("street_address"),
            FieldPanel("city"),
            FieldPanel("province"),
            FieldPanel("postal_code"),
            FieldPanel("country"),
            FieldPanel("location"),
        ], heading=_("Location")),
        
        MultiFieldPanel([
            FieldPanel("operating_hours"),
            FieldPanel("services"),
            FieldPanel("accepted_insurance"),
            FieldPanel("payment_methods"),
        ], heading=_("Services & Hours")),
        
        MultiFieldPanel([
            FieldPanel("has_drive_through"),
            FieldPanel("has_parking"),
            FieldPanel("wheelchair_accessible"),
            FieldPanel("has_consultation_room"),
        ], heading=_("Amenities")),
        
        MultiFieldPanel([
            FieldPanel("external_id"),
            FieldPanel("api_endpoint"),
        ], heading=_("Integration")),
        
        FieldPanel("notes"),
        
        InlinePanel("medication_inventory", label=_("Medication Inventory")),
        InlinePanel("pharmacy_reviews", label=_("Reviews")),
    ]


class InventoryStatus(models.TextChoices):
    """Choices for medication inventory status."""
    IN_STOCK = 'in_stock', _('In Stock')
    LOW_STOCK = 'low_stock', _('Low Stock')
    OUT_OF_STOCK = 'out_of_stock', _('Out of Stock')
    DISCONTINUED = 'discontinued', _('Discontinued')
    SPECIAL_ORDER = 'special_order', _('Special Order')


@register_snippet
class MedicationInventory(models.Model):
    """Model for tracking medication inventory at pharmacies."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name="medication_inventory",
        verbose_name=_("Pharmacy")
    )
    
    # Medication details
    medication_name = models.CharField(
        max_length=255,
        verbose_name=_("Medication Name")
    )
    
    generic_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Generic Name")
    )
    
    strength = models.CharField(
        max_length=50,
        verbose_name=_("Strength"),
        help_text=_("e.g., 10mg, 500mg")
    )
    
    dosage_form = models.CharField(
        max_length=50,
        verbose_name=_("Dosage Form"),
        help_text=_("e.g., Tablet, Capsule, Liquid")
    )
    
    manufacturer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Manufacturer")
    )
    
    ndc_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("NDC Number"),
        help_text=_("National Drug Code")
    )
    
    # Inventory information
    status = models.CharField(
        max_length=20,
        choices=InventoryStatus.choices,
        default=InventoryStatus.IN_STOCK,
        verbose_name=_("Status")
    )
    
    quantity_available = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Quantity Available")
    )
    
    quantity_reserved = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name=_("Quantity Reserved")
    )
    
    reorder_level = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        verbose_name=_("Reorder Level")
    )
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_("Unit Price")
    )
    
    insurance_covered = models.BooleanField(
        default=True,
        verbose_name=_("Insurance Covered")
    )
    
    # Dates
    expiry_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expiry Date")
    )
    
    last_restocked = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Restocked")
    )
    
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Updated")
    )
    
    # Integration data
    external_inventory_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("External Inventory ID")
    )
    
    sync_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Real-time Sync Enabled")
    )
    
    class Meta:
        verbose_name = _("Medication Inventory")
        verbose_name_plural = _("Medication Inventories")
        ordering = ["medication_name", "strength"]
        unique_together = ['pharmacy', 'medication_name', 'strength', 'dosage_form']
        indexes = [
            models.Index(fields=['medication_name', 'generic_name']),
            models.Index(fields=['status']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.medication_name} {self.strength} - {self.pharmacy.name}"
    
    @property
    def is_low_stock(self):
        """Check if inventory is below reorder level."""
        return self.quantity_available <= self.reorder_level
    
    @property
    def is_expired(self):
        """Check if medication has expired."""
        if not self.expiry_date:
            return False
        return self.expiry_date <= timezone.now().date()
    
    @property
    def available_quantity(self):
        """Get actual available quantity (total - reserved)."""
        return max(0, self.quantity_available - self.quantity_reserved)
    
    panels = [
        MultiFieldPanel([
            FieldPanel("pharmacy"),
            FieldPanel("medication_name"),
            FieldPanel("generic_name"),
            FieldPanel("strength"),
            FieldPanel("dosage_form"),
            FieldPanel("manufacturer"),
            FieldPanel("ndc_number"),
        ], heading=_("Medication Details")),
        
        MultiFieldPanel([
            FieldPanel("status"),
            FieldPanel("quantity_available"),
            FieldPanel("quantity_reserved"),
            FieldPanel("reorder_level"),
        ], heading=_("Inventory")),
        
        MultiFieldPanel([
            FieldPanel("unit_price"),
            FieldPanel("insurance_covered"),
        ], heading=_("Pricing")),
        
        MultiFieldPanel([
            FieldPanel("expiry_date"),
            FieldPanel("last_restocked"),
        ], heading=_("Dates")),
        
        MultiFieldPanel([
            FieldPanel("external_inventory_id"),
            FieldPanel("sync_enabled"),
        ], heading=_("Integration")),
    ]


@register_snippet
class PharmacyReview(models.Model):
    """Model for pharmacy reviews and ratings."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    pharmacy = models.ForeignKey(
        Pharmacy,
        on_delete=models.CASCADE,
        related_name="pharmacy_reviews",
        verbose_name=_("Pharmacy")
    )
    
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Reviewer")
    )
    
    # Rating and review
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating (1-5)")
    )
    
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Review Title")
    )
    
    review_text = models.TextField(
        blank=True,
        verbose_name=_("Review Text")
    )
    
    # Review categories
    service_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Service Rating")
    )
    
    wait_time_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Wait Time Rating")
    )
    
    price_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Price Rating")
    )
    
    # Metadata
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified Review")
    )
    
    helpful_count = models.IntegerField(
        default=0,
        verbose_name=_("Helpful Count")
    )
    
    class Meta:
        verbose_name = _("Pharmacy Review")
        verbose_name_plural = _("Pharmacy Reviews")
        ordering = ["-created_at"]
        unique_together = ['pharmacy', 'reviewer']
    
    def __str__(self):
        return f"{self.pharmacy.name} - {self.rating}/5 by {self.reviewer.get_full_name()}"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("pharmacy"),
            FieldPanel("reviewer"),
        ], heading=_("Review Details")),
        
        MultiFieldPanel([
            FieldPanel("rating"),
            FieldPanel("service_rating"),
            FieldPanel("wait_time_rating"),
            FieldPanel("price_rating"),
        ], heading=_("Ratings")),
        
        MultiFieldPanel([
            FieldPanel("title"),
            FieldPanel("review_text"),
        ], heading=_("Review Content")),
        
        MultiFieldPanel([
            FieldPanel("is_verified"),
            FieldPanel("helpful_count"),
        ], heading=_("Verification")),
    ]


class SearchStatus(models.TextChoices):
    """Choices for pharmacy search status."""
    PENDING = 'pending', _('Pending')
    IN_PROGRESS = 'in_progress', _('In Progress')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')


@register_snippet
class PharmacySearchLog(models.Model):
    """Model for logging pharmacy searches and analytics."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User")
    )
    
    # Search parameters
    search_location = gis_models.PointField(
        null=True,
        blank=True,
        verbose_name=_("Search Location")
    )
    
    search_address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Search Address")
    )
    
    search_radius = models.FloatField(
        default=5.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(100.0)],
        verbose_name=_("Search Radius (km)")
    )
    
    medication_searched = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Medication Searched")
    )
    
    filters_applied = models.JSONField(
        default=dict,
        verbose_name=_("Search Filters"),
        help_text=_("Applied search filters")
    )
    
    # Search results
    results_count = models.IntegerField(
        default=0,
        verbose_name=_("Results Count")
    )
    
    pharmacies_found = models.ManyToManyField(
        Pharmacy,
        blank=True,
        verbose_name=_("Pharmacies Found")
    )
    
    # Search metadata
    search_status = models.CharField(
        max_length=20,
        choices=SearchStatus.choices,
        default=SearchStatus.PENDING,
        verbose_name=_("Search Status")
    )
    
    search_duration = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Search Duration (seconds)")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    # Device and location info
    device_info = models.JSONField(
        default=dict,
        verbose_name=_("Device Information")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address")
    )
    
    class Meta:
        verbose_name = _("Pharmacy Search Log")
        verbose_name_plural = _("Pharmacy Search Logs")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['medication_searched']),
            models.Index(fields=['search_status']),
        ]
    
    def __str__(self):
        return f"Search by {self.user.get_full_name() if self.user else 'Anonymous'} - {self.created_at}"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("user"),
            FieldPanel("search_address"),
            FieldPanel("search_location"),
            FieldPanel("search_radius"),
        ], heading=_("Search Parameters")),
        
        MultiFieldPanel([
            FieldPanel("medication_searched"),
            FieldPanel("filters_applied"),
        ], heading=_("Search Criteria")),
        
        MultiFieldPanel([
            FieldPanel("search_status"),
            FieldPanel("results_count"),
            FieldPanel("search_duration"),
        ], heading=_("Search Results")),
        
        MultiFieldPanel([
            FieldPanel("device_info"),
            FieldPanel("ip_address"),
        ], heading=_("Metadata")),
    ]
