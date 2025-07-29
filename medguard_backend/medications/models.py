from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

# Wagtail imports
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index

User = get_user_model()


class MedicationIndexPage(Page):
    """
    Index page for medications.
    
    This page lists all medications and provides search/filter functionality.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for the medications page'),
        blank=True
    )
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = ['medications.MedicationDetailPage']
    
    # Search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    class Meta:
        verbose_name = _('Medication Index Page')
        verbose_name_plural = _('Medication Index Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Add medications to the template context."""
        context = super().get_context(request, *args, **kwargs)
        
        # Get all medications
        medications = Medication.objects.all().order_by('name')
        
        # Apply filters if provided
        medication_type = request.GET.get('type')
        if medication_type:
            medications = medications.filter(medication_type=medication_type)
        
        prescription_type = request.GET.get('prescription')
        if prescription_type:
            medications = medications.filter(prescription_type=prescription_type)
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            medications = medications.filter(
                models.Q(name__icontains=search_query) |
                models.Q(generic_name__icontains=search_query) |
                models.Q(description__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(medications, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['medications'] = page_obj
        context['medication_types'] = Medication.MedicationType.choices
        context['prescription_types'] = Medication.PrescriptionType.choices
        
        return context


class MedicationDetailPage(Page):
    """
    Detail page for individual medications.
    
    This page displays detailed information about a specific medication.
    """
    
    # Relationship to Medication model
    medication = models.OneToOneField(
        'medications.Medication',
        on_delete=models.SET_NULL,
        null=True,
        related_name='detail_page',
        verbose_name=_('Medication'),
        help_text=_('Associated medication record')
    )
    
    # Additional content
    additional_info = RichTextField(
        verbose_name=_('Additional Information'),
        help_text=_('Additional information about the medication'),
        blank=True
    )
    
    # Page configuration
    parent_page_types = ['medications.MedicationIndexPage']
    subpage_types = []
    
    # Search configuration
    search_fields = Page.search_fields + [
        index.SearchField('additional_info'),
        index.RelatedFields('medication', [
            index.SearchField('name'),
            index.SearchField('generic_name'),
            index.SearchField('description'),
        ]),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('medication'),
        FieldPanel('additional_info'),
    ]
    
    class Meta:
        verbose_name = _('Medication Detail Page')
        verbose_name_plural = _('Medication Detail Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Add medication details to the template context."""
        context = super().get_context(request, *args, **kwargs)
        context['medication'] = self.medication
        return context


class Medication(models.Model):
    """
    Medication model representing different medications in the system.
    """
    
    # Medication type choices
    class MedicationType(models.TextChoices):
        TABLET = 'tablet', _('Tablet')
        CAPSULE = 'capsule', _('Capsule')
        LIQUID = 'liquid', _('Liquid')
        INJECTION = 'injection', _('Injection')
        INHALER = 'inhaler', _('Inhaler')
        CREAM = 'cream', _('Cream')
        OINTMENT = 'ointment', _('Ointment')
        DROPS = 'drops', _('Drops')
        PATCH = 'patch', _('Patch')
        OTHER = 'other', _('Other')
    
    # Prescription type choices
    class PrescriptionType(models.TextChoices):
        PRESCRIPTION = 'prescription', _('Prescription Required')
        OVER_THE_COUNTER = 'otc', _('Over the Counter')
        SUPPLEMENT = 'supplement', _('Supplement')
    
    # Basic medication information
    name = models.CharField(
        max_length=200,
        help_text=_('Name of the medication')
    )
    
    generic_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Generic name of the medication')
    )
    
    brand_name = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Brand name of the medication')
    )
    
    medication_type = models.CharField(
        max_length=20,
        choices=MedicationType.choices,
        default=MedicationType.TABLET,
        help_text=_('Type of medication')
    )
    
    prescription_type = models.CharField(
        max_length=20,
        choices=PrescriptionType.choices,
        default=PrescriptionType.PRESCRIPTION,
        help_text=_('Type of prescription required')
    )
    
    # Dosage information
    strength = models.CharField(
        max_length=50,
        help_text=_('Strength of the medication (e.g., 500mg, 10mg/ml)')
    )
    
    dosage_unit = models.CharField(
        max_length=20,
        help_text=_('Unit of dosage (e.g., mg, ml, mcg)')
    )
    
    # Stock management
    pill_count = models.PositiveIntegerField(
        default=0,
        help_text=_('Current number of pills/units in stock')
    )
    
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        help_text=_('Threshold for low stock alerts')
    )
    
    # Additional information
    description = models.TextField(
        blank=True,
        help_text=_('Description of the medication')
    )
    
    active_ingredients = models.TextField(
        blank=True,
        help_text=_('Active ingredients in the medication')
    )
    
    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        help_text=_('Manufacturer of the medication')
    )
    
    # Safety information
    side_effects = models.TextField(
        blank=True,
        help_text=_('Common side effects')
    )
    
    contraindications = models.TextField(
        blank=True,
        help_text=_('Contraindications and warnings')
    )
    
    # Storage and handling
    storage_instructions = models.TextField(
        blank=True,
        help_text=_('Storage instructions for the medication')
    )
    
    expiration_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Expiration date of the medication')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Medication')
        verbose_name_plural = _('Medications')
        db_table = 'medications'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['generic_name']),
            models.Index(fields=['medication_type']),
            models.Index(fields=['prescription_type']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.strength})"
    
    @property
    def is_low_stock(self):
        """Check if medication is low in stock."""
        return self.pill_count <= self.low_stock_threshold
    
    @property
    def is_expired(self):
        """Check if medication is expired."""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False
    
    @property
    def is_expiring_soon(self):
        """Check if medication is expiring within 30 days."""
        if self.expiration_date:
            from datetime import timedelta
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            return self.expiration_date <= thirty_days_from_now
        return False
    
    def clean(self):
        """Custom validation for the model."""
        # Validate pill count is not negative
        if self.pill_count < 0:
            raise ValidationError({
                'pill_count': _('Pill count cannot be negative')
            })
        
        # Validate low stock threshold
        if self.low_stock_threshold < 1:
            raise ValidationError({
                'low_stock_threshold': _('Low stock threshold must be at least 1')
            })
        
        # Validate expiration date is not in the past
        if self.expiration_date and self.expiration_date < timezone.now().date():
            raise ValidationError({
                'expiration_date': _('Expiration date cannot be in the past')
            })


class MedicationSchedule(models.Model):
    """
    Medication schedule model for tracking when medications should be taken.
    """
    
    # Timing choices
    class Timing(models.TextChoices):
        MORNING = 'morning', _('Morning')
        NOON = 'noon', _('Noon')
        NIGHT = 'night', _('Night')
        CUSTOM = 'custom', _('Custom Time')
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PAUSED = 'paused', _('Paused')
        COMPLETED = 'completed', _('Completed')
    
    # Relationships
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medication_schedules',
        limit_choices_to={'user_type': User.UserType.PATIENT},
        help_text=_('Patient for whom this schedule is created')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text=_('Medication to be taken')
    )
    
    # Schedule information
    timing = models.CharField(
        max_length=20,
        choices=Timing.choices,
        default=Timing.MORNING,
        help_text=_('When the medication should be taken')
    )
    
    custom_time = models.TimeField(
        null=True,
        blank=True,
        help_text=_('Custom time for medication (if timing is custom)')
    )
    
    dosage_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Amount of medication to take')
    )
    
    frequency = models.CharField(
        max_length=50,
        default='daily',
        help_text=_('How often to take the medication (e.g., daily, twice daily, weekly)')
    )
    
    # Days of the week (for weekly schedules)
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=True)
    sunday = models.BooleanField(default=True)
    
    # Schedule period
    start_date = models.DateField(
        default=timezone.now,
        help_text=_('Date when medication schedule starts')
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Date when medication schedule ends (optional)')
    )
    
    # Status and tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text=_('Current status of the medication schedule')
    )
    
    instructions = models.TextField(
        blank=True,
        help_text=_('Special instructions for taking the medication')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Medication Schedule')
        verbose_name_plural = _('Medication Schedules')
        db_table = 'medication_schedules'
        indexes = [
            models.Index(fields=['patient', 'medication']),
            models.Index(fields=['timing']),
            models.Index(fields=['status']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        ordering = ['patient', 'timing', 'start_date']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.medication.name} ({self.timing})"
    
    @property
    def is_active(self):
        """Check if schedule is currently active."""
        today = timezone.now().date()
        if self.status != self.Status.ACTIVE:
            return False
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
    
    @property
    def should_take_today(self):
        """Check if medication should be taken today."""
        if not self.is_active:
            return False
        
        today = timezone.now().date()
        weekday = today.weekday()  # Monday=0, Sunday=6
        
        day_fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        return getattr(self, day_fields[weekday])
    
    def clean(self):
        """Custom validation for the model."""
        # Validate custom time is provided when timing is custom
        if self.timing == self.Timing.CUSTOM and not self.custom_time:
            raise ValidationError({
                'custom_time': _('Custom time is required when timing is set to custom')
            })
        
        # Validate end date is after start date
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError({
                'end_date': _('End date must be after start date')
            })
        
        # Validate at least one day is selected
        days_selected = any([
            self.monday, self.tuesday, self.wednesday, self.thursday,
            self.friday, self.saturday, self.sunday
        ])
        if not days_selected:
            raise ValidationError(_('At least one day of the week must be selected'))


class MedicationLog(models.Model):
    """
    Medication log model for tracking medication adherence history.
    """
    
    # Status choices
    class Status(models.TextChoices):
        TAKEN = 'taken', _('Taken')
        MISSED = 'missed', _('Missed')
        SKIPPED = 'skipped', _('Skipped')
        PARTIAL = 'partial', _('Partial Dose')
    
    # Relationships
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='medication_logs',
        limit_choices_to={'user_type': User.UserType.PATIENT},
        help_text=_('Patient who took the medication')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text=_('Medication that was taken')
    )
    
    schedule = models.ForeignKey(
        MedicationSchedule,
        on_delete=models.CASCADE,
        related_name='logs',
        null=True,
        blank=True,
        help_text=_('Associated medication schedule')
    )
    
    # Log information
    scheduled_time = models.DateTimeField(
        help_text=_('When the medication was scheduled to be taken')
    )
    
    actual_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the medication was actually taken')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.MISSED,
        help_text=_('Status of the medication dose')
    )
    
    dosage_taken = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Actual dosage taken')
    )
    
    # Notes and observations
    notes = models.TextField(
        blank=True,
        help_text=_('Notes about the medication dose')
    )
    
    side_effects = models.TextField(
        blank=True,
        help_text=_('Any side effects experienced')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Medication Log')
        verbose_name_plural = _('Medication Logs')
        db_table = 'medication_logs'
        indexes = [
            models.Index(fields=['patient', 'medication']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['status']),
            models.Index(fields=['actual_time']),
        ]
        ordering = ['-scheduled_time']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.medication.name} ({self.status})"
    
    @property
    def is_on_time(self):
        """Check if medication was taken on time (within 1 hour of scheduled time)."""
        if not self.actual_time or self.status != self.Status.TAKEN:
            return False
        
        from datetime import timedelta
        time_diff = abs((self.actual_time - self.scheduled_time).total_seconds() / 3600)
        return time_diff <= 1
    
    @property
    def adherence_score(self):
        """Calculate adherence score for this log entry."""
        if self.status == self.Status.TAKEN:
            if self.is_on_time:
                return 100
            else:
                return 80  # Taken but late
        elif self.status == self.Status.PARTIAL:
            return 50
        elif self.status == self.Status.SKIPPED:
            return 0
        else:  # MISSED
            return 0
    
    def clean(self):
        """Custom validation for the model."""
        # Validate actual time is not in the future
        if self.actual_time and self.actual_time > timezone.now():
            raise ValidationError({
                'actual_time': _('Actual time cannot be in the future')
            })
        
        # Validate dosage taken is provided when status is taken or partial
        if self.status in [self.Status.TAKEN, self.Status.PARTIAL] and not self.dosage_taken:
            raise ValidationError({
                'dosage_taken': _('Dosage taken is required when medication is taken or partially taken')
            })


class StockAlert(models.Model):
    """
    Stock alert model for tracking low inventory warnings.
    """
    
    # Alert type choices
    class AlertType(models.TextChoices):
        LOW_STOCK = 'low_stock', _('Low Stock')
        OUT_OF_STOCK = 'out_of_stock', _('Out of Stock')
        EXPIRING_SOON = 'expiring_soon', _('Expiring Soon')
        EXPIRED = 'expired', _('Expired')
    
    # Priority choices
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        ACKNOWLEDGED = 'acknowledged', _('Acknowledged')
        RESOLVED = 'resolved', _('Resolved')
        DISMISSED = 'dismissed', _('Dismissed')
    
    # Relationships
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_alerts',
        help_text=_('Medication associated with this alert')
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_alerts',
        help_text=_('User who created the alert')
    )
    
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='acknowledged_alerts',
        null=True,
        blank=True,
        help_text=_('User who acknowledged the alert')
    )
    
    # Alert information
    alert_type = models.CharField(
        max_length=20,
        choices=AlertType.choices,
        help_text=_('Type of stock alert')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text=_('Priority level of the alert')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text=_('Current status of the alert')
    )
    
    # Alert details
    title = models.CharField(
        max_length=200,
        help_text=_('Title of the alert')
    )
    
    message = models.TextField(
        help_text=_('Detailed message of the alert')
    )
    
    current_stock = models.PositiveIntegerField(
        help_text=_('Current stock level when alert was created')
    )
    
    threshold_level = models.PositiveIntegerField(
        help_text=_('Threshold level that triggered the alert')
    )
    
    # Resolution information
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the alert was resolved')
    )
    
    resolution_notes = models.TextField(
        blank=True,
        help_text=_('Notes about how the alert was resolved')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Stock Alert')
        verbose_name_plural = _('Stock Alerts')
        db_table = 'stock_alerts'
        indexes = [
            models.Index(fields=['medication']),
            models.Index(fields=['alert_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medication.name} - {self.alert_type} ({self.priority})"
    
    @property
    def is_active(self):
        """Check if alert is currently active."""
        return self.status == self.Status.ACTIVE
    
    @property
    def is_critical(self):
        """Check if alert is critical priority."""
        return self.priority == self.Priority.CRITICAL
    
    def acknowledge(self, user):
        """Acknowledge the alert."""
        self.status = self.Status.ACKNOWLEDGED
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, notes=""):
        """Resolve the alert."""
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.save()
    
    def dismiss(self):
        """Dismiss the alert."""
        self.status = self.Status.DISMISSED
        self.save()
    
    def clean(self):
        """Custom validation for the model."""
        # Validate current stock is not negative
        if self.current_stock < 0:
            raise ValidationError({
                'current_stock': _('Current stock cannot be negative')
            })
        
        # Validate threshold level is positive
        if self.threshold_level <= 0:
            raise ValidationError({
                'threshold_level': _('Threshold level must be positive')
            })
        
        # Validate acknowledged_by is set when status is acknowledged
        if self.status == self.Status.ACKNOWLEDGED and not self.acknowledged_by:
            raise ValidationError({
                'acknowledged_by': _('Acknowledged by must be set when status is acknowledged')
            })


class StockTransaction(models.Model):
    """
    Stock transaction model for tracking all stock movements with detailed analytics.
    """
    
    # Transaction type choices
    class TransactionType(models.TextChoices):
        PURCHASE = 'purchase', _('Purchase')
        SALE = 'sale', _('Sale')
        ADJUSTMENT = 'adjustment', _('Adjustment')
        TRANSFER = 'transfer', _('Transfer')
        EXPIRY = 'expiry', _('Expiry')
        DAMAGE = 'damage', _('Damage')
        RETURN = 'return', _('Return')
        PRESCRIPTION_FILLED = 'prescription_filled', _('Prescription Filled')
        DOSE_TAKEN = 'dose_taken', _('Dose Taken')
    
    # Relationships
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        help_text=_('Medication involved in this transaction')
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='stock_transactions',
        help_text=_('User who initiated this transaction')
    )
    
    # Transaction details
    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        help_text=_('Type of stock transaction')
    )
    
    quantity = models.IntegerField(
        help_text=_('Quantity involved in the transaction (positive for additions, negative for removals)')
    )
    
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Unit price for the transaction')
    )
    
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Total amount for the transaction')
    )
    
    # Stock levels before and after
    stock_before = models.PositiveIntegerField(
        help_text=_('Stock level before this transaction')
    )
    
    stock_after = models.PositiveIntegerField(
        help_text=_('Stock level after this transaction')
    )
    
    # Reference information
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Reference number for the transaction (invoice, prescription, etc.)')
    )
    
    batch_number = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Batch number for the medication')
    )
    
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Expiry date for this batch')
    )
    
    # Notes and metadata
    notes = models.TextField(
        blank=True,
        help_text=_('Additional notes about the transaction')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Stock Transaction')
        verbose_name_plural = _('Stock Transactions')
        db_table = 'stock_transactions'
        indexes = [
            models.Index(fields=['medication', 'transaction_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['batch_number']),
            models.Index(fields=['expiry_date']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.medication.name} - {self.get_transaction_type_display()} ({self.quantity})"
    
    def save(self, *args, **kwargs):
        """Override save to update medication stock and calculate totals."""
        if not self.pk:  # New transaction
            self.stock_before = self.medication.pill_count
            self.stock_after = self.stock_before + self.quantity
            
            # Calculate total amount if unit price is provided
            if self.unit_price and not self.total_amount:
                self.total_amount = self.unit_price * abs(self.quantity)
        
        super().save(*args, **kwargs)
        
        # Update medication stock
        self.medication.pill_count = self.stock_after
        self.medication.save(update_fields=['pill_count'])
    
    @property
    def is_addition(self):
        """Check if this transaction adds stock."""
        return self.quantity > 0
    
    @property
    def is_removal(self):
        """Check if this transaction removes stock."""
        return self.quantity < 0


class StockAnalytics(models.Model):
    """
    Stock analytics model for storing calculated metrics and predictions.
    """
    
    # Relationships
    medication = models.OneToOneField(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_analytics',
        help_text=_('Medication for these analytics')
    )
    
    # Usage patterns
    daily_usage_rate = models.FloatField(
        default=0.0,
        help_text=_('Average daily usage rate (units per day)')
    )
    
    weekly_usage_rate = models.FloatField(
        default=0.0,
        help_text=_('Average weekly usage rate (units per week)')
    )
    
    monthly_usage_rate = models.FloatField(
        default=0.0,
        help_text=_('Average monthly usage rate (units per month)')
    )
    
    # Stock predictions
    days_until_stockout = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_('Predicted days until stock runs out')
    )
    
    predicted_stockout_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Predicted date when stock will run out')
    )
    
    recommended_order_quantity = models.PositiveIntegerField(
        default=0,
        help_text=_('Recommended quantity to order')
    )
    
    recommended_order_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Recommended date to place order')
    )
    
    # Seasonal patterns
    seasonal_factor = models.FloatField(
        default=1.0,
        help_text=_('Seasonal adjustment factor for usage patterns')
    )
    
    # Variability metrics
    usage_volatility = models.FloatField(
        default=0.0,
        help_text=_('Standard deviation of daily usage')
    )
    
    # Confidence intervals
    stockout_confidence = models.FloatField(
        default=0.0,
        help_text=_('Confidence level for stockout prediction (0-1)')
    )
    
    # Last calculation
    last_calculated = models.DateTimeField(
        auto_now=True,
        help_text=_('When these analytics were last calculated')
    )
    
    # Calculation parameters
    calculation_window_days = models.PositiveIntegerField(
        default=90,
        help_text=_('Number of days to use for calculations')
    )
    
    class Meta:
        verbose_name = _('Stock Analytics')
        verbose_name_plural = _('Stock Analytics')
        db_table = 'stock_analytics'
        indexes = [
            models.Index(fields=['medication']),
            models.Index(fields=['last_calculated']),
            models.Index(fields=['days_until_stockout']),
        ]
    
    def __str__(self):
        return f"Analytics for {self.medication.name}"
    
    @property
    def is_stockout_imminent(self):
        """Check if stockout is predicted within 7 days."""
        return self.days_until_stockout is not None and self.days_until_stockout <= 7
    
    @property
    def is_order_needed(self):
        """Check if an order is recommended within 14 days."""
        return (self.recommended_order_date and 
                self.recommended_order_date <= timezone.now().date() + timezone.timedelta(days=14))


class PharmacyIntegration(models.Model):
    """
    Pharmacy integration model for managing connections to external pharmacy systems.
    """
    
    # Integration type choices
    class IntegrationType(models.TextChoices):
        API = 'api', _('API Integration')
        EDI = 'edi', _('EDI Integration')
        MANUAL = 'manual', _('Manual Integration')
        WEBHOOK = 'webhook', _('Webhook Integration')
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        TESTING = 'testing', _('Testing')
        ERROR = 'error', _('Error')
    
    # Basic information
    name = models.CharField(
        max_length=200,
        help_text=_('Name of the pharmacy integration')
    )
    
    pharmacy_name = models.CharField(
        max_length=200,
        help_text=_('Name of the pharmacy')
    )
    
    integration_type = models.CharField(
        max_length=20,
        choices=IntegrationType.choices,
        default=IntegrationType.API,
        help_text=_('Type of integration')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INACTIVE,
        help_text=_('Current status of the integration')
    )
    
    # Connection details
    api_endpoint = models.URLField(
        blank=True,
        help_text=_('API endpoint for the integration')
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('API key for authentication')
    )
    
    webhook_url = models.URLField(
        blank=True,
        help_text=_('Webhook URL for receiving updates')
    )
    
    # Configuration
    auto_order_enabled = models.BooleanField(
        default=False,
        help_text=_('Whether to enable automatic ordering')
    )
    
    order_threshold = models.PositiveIntegerField(
        default=10,
        help_text=_('Stock threshold for automatic ordering')
    )
    
    order_quantity_multiplier = models.FloatField(
        default=1.0,
        help_text=_('Multiplier for order quantities')
    )
    
    # Scheduling
    order_lead_time_days = models.PositiveIntegerField(
        default=3,
        help_text=_('Expected lead time for orders in days')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_sync = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Pharmacy Integration')
        verbose_name_plural = _('Pharmacy Integrations')
        db_table = 'pharmacy_integrations'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['integration_type']),
            models.Index(fields=['last_sync']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.pharmacy_name} - {self.get_integration_type_display()}"


class PrescriptionRenewal(models.Model):
    """
    Prescription renewal model for tracking prescription renewals and reminders.
    """
    
    # Status choices
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        PENDING_RENEWAL = 'pending_renewal', _('Pending Renewal')
        RENEWED = 'renewed', _('Renewed')
        EXPIRED = 'expired', _('Expired')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Priority choices
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')
    
    # Relationships
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prescription_renewals',
        limit_choices_to={'user_type': User.UserType.PATIENT},
        help_text=_('Patient for this prescription')
    )
    
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='prescription_renewals',
        help_text=_('Medication for this prescription')
    )
    
    # Prescription details
    prescription_number = models.CharField(
        max_length=100,
        help_text=_('Prescription number')
    )
    
    prescribed_by = models.CharField(
        max_length=200,
        help_text=_('Name of the prescribing doctor')
    )
    
    prescribed_date = models.DateField(
        help_text=_('Date when prescription was issued')
    )
    
    expiry_date = models.DateField(
        help_text=_('Date when prescription expires')
    )
    
    # Renewal information
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        help_text=_('Current status of the prescription')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        help_text=_('Priority level for renewal')
    )
    
    # Reminder settings
    reminder_days_before = models.PositiveIntegerField(
        default=30,
        help_text=_('Days before expiry to start sending reminders')
    )
    
    last_reminder_sent = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the last reminder was sent')
    )
    
    # Renewal tracking
    renewed_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Date when prescription was renewed')
    )
    
    new_expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('New expiry date after renewal')
    )
    
    # Notes
    notes = models.TextField(
        blank=True,
        help_text=_('Additional notes about the prescription')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Prescription Renewal')
        verbose_name_plural = _('Prescription Renewals')
        db_table = 'prescription_renewals'
        indexes = [
            models.Index(fields=['patient', 'medication']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['prescribed_date']),
        ]
        ordering = ['expiry_date']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.medication.name} ({self.prescription_number})"
    
    @property
    def is_expired(self):
        """Check if prescription is expired."""
        return self.expiry_date < timezone.now().date()
    
    @property
    def is_expiring_soon(self):
        """Check if prescription is expiring within reminder period."""
        from datetime import timedelta
        reminder_date = self.expiry_date - timedelta(days=self.reminder_days_before)
        return reminder_date <= timezone.now().date() <= self.expiry_date
    
    @property
    def days_until_expiry(self):
        """Calculate days until prescription expires."""
        return (self.expiry_date - timezone.now().date()).days
    
    @property
    def needs_renewal(self):
        """Check if prescription needs renewal."""
        return self.status == self.Status.ACTIVE and self.is_expiring_soon
    
    def renew(self, new_expiry_date):
        """Renew the prescription."""
        self.status = self.Status.RENEWED
        self.renewed_date = timezone.now().date()
        self.new_expiry_date = new_expiry_date
        self.save()


class StockVisualization(models.Model):
    """
    Stock visualization model for storing chart data and analytics.
    """
    
    # Chart type choices
    class ChartType(models.TextChoices):
        LINE = 'line', _('Line Chart')
        BAR = 'bar', _('Bar Chart')
        PIE = 'pie', _('Pie Chart')
        SCATTER = 'scatter', _('Scatter Plot')
        HEATMAP = 'heatmap', _('Heatmap')
    
    # Relationships
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name='stock_visualizations',
        help_text=_('Medication for this visualization')
    )
    
    # Chart configuration
    chart_type = models.CharField(
        max_length=20,
        choices=ChartType.choices,
        default=ChartType.LINE,
        help_text=_('Type of chart to display')
    )
    
    title = models.CharField(
        max_length=200,
        help_text=_('Title of the chart')
    )
    
    description = models.TextField(
        blank=True,
        help_text=_('Description of the chart')
    )
    
    # Chart data (JSON format)
    chart_data = models.JSONField(
        default=dict,
        help_text=_('Chart data in JSON format')
    )
    
    # Chart options
    chart_options = models.JSONField(
        default=dict,
        help_text=_('Chart configuration options')
    )
    
    # Time range
    start_date = models.DateField(
        help_text=_('Start date for the chart data')
    )
    
    end_date = models.DateField(
        help_text=_('End date for the chart data')
    )
    
    # Settings
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether this visualization is active')
    )
    
    auto_refresh = models.BooleanField(
        default=True,
        help_text=_('Whether to automatically refresh this chart')
    )
    
    refresh_interval_hours = models.PositiveIntegerField(
        default=24,
        help_text=_('Hours between automatic refreshes')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_generated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Stock Visualization')
        verbose_name_plural = _('Stock Visualizations')
        db_table = 'stock_visualizations'
        indexes = [
            models.Index(fields=['medication', 'chart_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_generated']),
        ]
        ordering = ['title']
    
    def __str__(self):
        return f"{self.medication.name} - {self.title}"
    
    @property
    def needs_refresh(self):
        """Check if chart needs to be refreshed."""
        if not self.auto_refresh or not self.last_generated:
            return False
        
        from datetime import timedelta
        refresh_time = self.last_generated + timedelta(hours=self.refresh_interval_hours)
        return timezone.now() > refresh_time
