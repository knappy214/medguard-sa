"""
Medication Tracker Models
Models for tracking medication adherence and patient compliance.
"""
import uuid
from datetime import datetime, timedelta
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet

User = get_user_model()


class AdherenceStatus(models.TextChoices):
    """Choices for medication adherence status."""
    EXCELLENT = 'excellent', _('Excellent (90-100%)')
    GOOD = 'good', _('Good (80-89%)')
    MODERATE = 'moderate', _('Moderate (60-79%)')
    POOR = 'poor', _('Poor (40-59%)')
    VERY_POOR = 'very_poor', _('Very Poor (<40%)')


class MedicationFrequency(models.TextChoices):
    """Choices for medication frequency."""
    ONCE_DAILY = 'once_daily', _('Once Daily')
    TWICE_DAILY = 'twice_daily', _('Twice Daily')
    THREE_TIMES_DAILY = 'three_times_daily', _('Three Times Daily')
    FOUR_TIMES_DAILY = 'four_times_daily', _('Four Times Daily')
    AS_NEEDED = 'as_needed', _('As Needed')
    WEEKLY = 'weekly', _('Weekly')
    MONTHLY = 'monthly', _('Monthly')


@register_snippet
class MedicationSchedule(models.Model):
    """Model for tracking medication schedules and adherence."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    # Patient and medication info
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="medication_schedules",
        verbose_name=_("Patient")
    )
    
    medication_name = models.CharField(
        max_length=255,
        verbose_name=_("Medication Name")
    )
    
    dosage = models.CharField(
        max_length=100,
        verbose_name=_("Dosage"),
        help_text=_("e.g., 10mg, 1 tablet")
    )
    
    frequency = models.CharField(
        max_length=20,
        choices=MedicationFrequency.choices,
        default=MedicationFrequency.ONCE_DAILY,
        verbose_name=_("Frequency")
    )
    
    # Schedule details
    start_date = models.DateField(
        verbose_name=_("Start Date")
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("Leave blank for ongoing medication")
    )
    
    scheduled_times = models.JSONField(
        default=list,
        verbose_name=_("Scheduled Times"),
        help_text=_("List of times when medication should be taken (HH:MM format)")
    )
    
    # Adherence tracking
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
    )
    
    adherence_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name=_("Adherence Rate (%)"),
        help_text=_("Calculated adherence percentage")
    )
    
    adherence_status = models.CharField(
        max_length=20,
        choices=AdherenceStatus.choices,
        default=AdherenceStatus.EXCELLENT,
        verbose_name=_("Adherence Status")
    )
    
    # Monitoring settings
    reminder_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Reminders Enabled")
    )
    
    reminder_offset_minutes = models.IntegerField(
        default=0,
        verbose_name=_("Reminder Offset (minutes)",
        help_text=_("Minutes before scheduled time to send reminder")
    )
    
    # Healthcare provider info
    prescribed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescribed_medications",
        verbose_name=_("Prescribed By"),
        limit_choices_to={'groups__name': 'Healthcare Providers'}
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
    
    notes = RichTextField(
        blank=True,
        verbose_name=_("Notes")
    )
    
    class Meta:
        verbose_name = _("Medication Schedule")
        verbose_name_plural = _("Medication Schedules")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['patient', 'is_active']),
            models.Index(fields=['start_date', 'end_date']),
        ]
    
    def __str__(self):
        return f"{self.medication_name} - {self.patient.get_full_name()}"
    
    def calculate_adherence_rate(self, days=30):
        """Calculate adherence rate for the last N days."""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get scheduled doses in the period
        scheduled_count = self.get_scheduled_doses_count(start_date, end_date)
        
        # Get taken doses in the period
        taken_count = self.medication_logs.filter(
            taken_at__date__range=[start_date, end_date],
            status='taken'
        ).count()
        
        if scheduled_count == 0:
            return 0.0
        
        adherence_rate = (taken_count / scheduled_count) * 100
        
        # Update the stored adherence rate
        self.adherence_rate = min(adherence_rate, 100.0)
        self.adherence_status = self.get_adherence_status(self.adherence_rate)
        self.save(update_fields=['adherence_rate', 'adherence_status'])
        
        return self.adherence_rate
    
    def get_scheduled_doses_count(self, start_date, end_date):
        """Calculate expected number of doses in date range."""
        if not self.scheduled_times:
            return 0
        
        daily_doses = len(self.scheduled_times)
        
        # Calculate number of days in range
        current_date = max(start_date, self.start_date)
        end_date = min(end_date, self.end_date or end_date)
        
        if current_date > end_date:
            return 0
        
        days = (end_date - current_date).days + 1
        return days * daily_doses
    
    def get_adherence_status(self, rate):
        """Get adherence status based on rate."""
        if rate >= 90:
            return AdherenceStatus.EXCELLENT
        elif rate >= 80:
            return AdherenceStatus.GOOD
        elif rate >= 60:
            return AdherenceStatus.MODERATE
        elif rate >= 40:
            return AdherenceStatus.POOR
        else:
            return AdherenceStatus.VERY_POOR
    
    panels = [
        MultiFieldPanel([
            FieldPanel("patient"),
            FieldPanel("prescribed_by"),
        ], heading=_("Patient Information")),
        
        MultiFieldPanel([
            FieldPanel("medication_name"),
            FieldPanel("dosage"),
            FieldPanel("frequency"),
        ], heading=_("Medication Details")),
        
        MultiFieldPanel([
            FieldPanel("start_date"),
            FieldPanel("end_date"),
            FieldPanel("scheduled_times"),
            FieldPanel("is_active"),
        ], heading=_("Schedule")),
        
        MultiFieldPanel([
            FieldPanel("reminder_enabled"),
            FieldPanel("reminder_offset_minutes"),
        ], heading=_("Reminders")),
        
        FieldPanel("notes"),
        
        InlinePanel("medication_logs", label=_("Medication Logs")),
    ]


class MedicationLogStatus(models.TextChoices):
    """Choices for medication log status."""
    TAKEN = 'taken', _('Taken')
    MISSED = 'missed', _('Missed')
    DELAYED = 'delayed', _('Delayed')
    SKIPPED = 'skipped', _('Skipped')
    PARTIAL = 'partial', _('Partial Dose')


@register_snippet
class MedicationLog(models.Model):
    """Model for logging individual medication doses."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    schedule = models.ForeignKey(
        MedicationSchedule,
        on_delete=models.CASCADE,
        related_name="medication_logs",
        verbose_name=_("Medication Schedule")
    )
    
    # Timing information
    scheduled_time = models.DateTimeField(
        verbose_name=_("Scheduled Time")
    )
    
    taken_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Taken At")
    )
    
    status = models.CharField(
        max_length=20,
        choices=MedicationLogStatus.choices,
        default=MedicationLogStatus.TAKEN,
        verbose_name=_("Status")
    )
    
    # Dose information
    dose_taken = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Actual Dose Taken"),
        help_text=_("Leave blank if full dose was taken")
    )
    
    # User tracking
    logged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Logged By")
    )
    
    # Additional information
    side_effects = models.TextField(
        blank=True,
        verbose_name=_("Side Effects"),
        help_text=_("Any side effects experienced")
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes")
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
    
    # Mobile app integration
    device_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Device ID"),
        help_text=_("ID of the device used to log the medication")
    )
    
    location_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Location Data"),
        help_text=_("GPS coordinates when medication was logged")
    )
    
    class Meta:
        verbose_name = _("Medication Log")
        verbose_name_plural = _("Medication Logs")
        ordering = ["-scheduled_time"]
        indexes = [
            models.Index(fields=['schedule', 'status']),
            models.Index(fields=['scheduled_time']),
            models.Index(fields=['taken_at']),
        ]
    
    def __str__(self):
        return f"{self.schedule.medication_name} - {self.scheduled_time.strftime('%Y-%m-%d %H:%M')} ({self.status})"
    
    @property
    def is_late(self):
        """Check if medication was taken late."""
        if not self.taken_at or self.status != MedicationLogStatus.TAKEN:
            return False
        
        # Consider late if taken more than 30 minutes after scheduled time
        late_threshold = self.scheduled_time + timedelta(minutes=30)
        return self.taken_at > late_threshold
    
    @property
    def delay_minutes(self):
        """Calculate delay in minutes."""
        if not self.taken_at or self.status != MedicationLogStatus.TAKEN:
            return 0
        
        delay = self.taken_at - self.scheduled_time
        return max(0, int(delay.total_seconds() / 60))
    
    panels = [
        MultiFieldPanel([
            FieldPanel("schedule"),
            FieldPanel("scheduled_time"),
            FieldPanel("taken_at"),
            FieldPanel("status"),
        ], heading=_("Timing")),
        
        MultiFieldPanel([
            FieldPanel("dose_taken"),
            FieldPanel("side_effects"),
            FieldPanel("notes"),
        ], heading=_("Details")),
        
        MultiFieldPanel([
            FieldPanel("logged_by"),
            FieldPanel("device_id"),
        ], heading=_("Tracking")),
    ]


@register_snippet
class AdherenceReport(models.Model):
    """Model for storing adherence reports and analytics."""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_("ID")
    )
    
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="adherence_reports",
        verbose_name=_("Patient")
    )
    
    # Report period
    report_date = models.DateField(
        verbose_name=_("Report Date")
    )
    
    period_start = models.DateField(
        verbose_name=_("Period Start")
    )
    
    period_end = models.DateField(
        verbose_name=_("Period End")
    )
    
    # Adherence metrics
    overall_adherence_rate = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name=_("Overall Adherence Rate (%)")
    )
    
    total_medications = models.IntegerField(
        verbose_name=_("Total Medications")
    )
    
    total_scheduled_doses = models.IntegerField(
        verbose_name=_("Total Scheduled Doses")
    )
    
    total_taken_doses = models.IntegerField(
        verbose_name=_("Total Taken Doses")
    )
    
    total_missed_doses = models.IntegerField(
        verbose_name=_("Total Missed Doses")
    )
    
    # Detailed metrics
    medication_breakdown = models.JSONField(
        default=dict,
        verbose_name=_("Medication Breakdown"),
        help_text=_("Adherence breakdown by medication")
    )
    
    daily_adherence = models.JSONField(
        default=dict,
        verbose_name=_("Daily Adherence"),
        help_text=_("Day-by-day adherence data")
    )
    
    # Insights and recommendations
    insights = models.JSONField(
        default=list,
        verbose_name=_("Insights"),
        help_text=_("AI-generated insights about adherence patterns")
    )
    
    recommendations = models.JSONField(
        default=list,
        verbose_name=_("Recommendations"),
        help_text=_("Recommendations for improving adherence")
    )
    
    # Report metadata
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generated_adherence_reports",
        verbose_name=_("Generated By")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    
    class Meta:
        verbose_name = _("Adherence Report")
        verbose_name_plural = _("Adherence Reports")
        ordering = ["-report_date"]
        unique_together = ['patient', 'report_date']
    
    def __str__(self):
        return f"Adherence Report - {self.patient.get_full_name()} ({self.report_date})"
    
    panels = [
        MultiFieldPanel([
            FieldPanel("patient"),
            FieldPanel("report_date"),
            FieldPanel("period_start"),
            FieldPanel("period_end"),
        ], heading=_("Report Details")),
        
        MultiFieldPanel([
            FieldPanel("overall_adherence_rate"),
            FieldPanel("total_medications"),
            FieldPanel("total_scheduled_doses"),
            FieldPanel("total_taken_doses"),
            FieldPanel("total_missed_doses"),
        ], heading=_("Adherence Metrics")),
        
        MultiFieldPanel([
            FieldPanel("medication_breakdown"),
            FieldPanel("daily_adherence"),
        ], heading=_("Detailed Data")),
        
        MultiFieldPanel([
            FieldPanel("insights"),
            FieldPanel("recommendations"),
        ], heading=_("Analysis")),
    ]
