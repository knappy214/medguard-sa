from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()


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
