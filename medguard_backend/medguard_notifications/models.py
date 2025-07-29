from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

# Wagtail imports
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.search import index

User = get_user_model()


class NotificationIndexPage(Page):
    """
    Index page for notifications.
    
    This page lists all notifications and provides filtering functionality.
    """
    
    # Page content
    intro = RichTextField(
        verbose_name=_('Introduction'),
        help_text=_('Introduction text for the notifications page'),
        blank=True
    )
    
    # Page configuration
    parent_page_types = ['home.HomePage']
    subpage_types = ['medguard_notifications.NotificationDetailPage']
    
    # Search configuration
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]
    
    class Meta:
        verbose_name = _('Notification Index Page')
        verbose_name_plural = _('Notification Index Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Add notifications to the template context."""
        context = super().get_context(request, *args, **kwargs)
        
        # Get all active notifications
        notifications = Notification.objects.filter(is_active=True).order_by('-created_at')
        
        # Apply filters if provided
        notification_type = request.GET.get('type')
        if notification_type:
            notifications = notifications.filter(notification_type=notification_type)
        
        priority = request.GET.get('priority')
        if priority:
            notifications = notifications.filter(priority=priority)
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            notifications = notifications.filter(
                models.Q(title__icontains=search_query) |
                models.Q(content__icontains=search_query)
            )
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(notifications, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['notifications'] = page_obj
        context['notification_types'] = Notification.NotificationType.choices
        context['priorities'] = Notification.Priority.choices
        
        return context


class NotificationDetailPage(Page):
    """
    Detail page for individual notifications.
    
    This page displays detailed information about a specific notification.
    """
    
    # Relationship to Notification model
    notification = models.OneToOneField(
        'medguard_notifications.Notification',
        on_delete=models.SET_NULL,
        null=True,
        related_name='detail_page',
        verbose_name=_('Notification'),
        help_text=_('Associated notification record')
    )
    
    # Additional content
    additional_info = RichTextField(
        verbose_name=_('Additional Information'),
        help_text=_('Additional information about the notification'),
        blank=True
    )
    
    # Page configuration
    parent_page_types = ['medguard_notifications.NotificationIndexPage']
    subpage_types = []
    
    # Search configuration
    search_fields = Page.search_fields + [
        index.SearchField('additional_info'),
        index.RelatedFields('notification', [
            index.SearchField('title'),
            index.SearchField('content'),
        ]),
    ]
    
    # Admin panels
    content_panels = Page.content_panels + [
        FieldPanel('notification'),
        FieldPanel('additional_info'),
    ]
    
    class Meta:
        verbose_name = _('Notification Detail Page')
        verbose_name_plural = _('Notification Detail Pages')
    
    def get_context(self, request, *args, **kwargs):
        """Add notification details to the template context."""
        context = super().get_context(request, *args, **kwargs)
        context['notification'] = self.notification
        return context


class Notification(models.Model):
    """
    Notification model for system-wide notifications and alerts.
    """
    
    # Notification type choices
    class NotificationType(models.TextChoices):
        SYSTEM = 'system', _('System Notification')
        MEDICATION = 'medication', _('Medication Alert')
        STOCK = 'stock', _('Stock Alert')
        MAINTENANCE = 'maintenance', _('Maintenance Notice')
        SECURITY = 'security', _('Security Alert')
        GENERAL = 'general', _('General Announcement')
    
    # Priority choices
    class Priority(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        CRITICAL = 'critical', _('Critical')
    
    # Status choices
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        ARCHIVED = 'archived', _('Archived')
    
    # Basic notification information
    title = models.CharField(
        max_length=200,
        verbose_name=_('Title'),
        help_text=_('Title of the notification')
    )
    
    content = RichTextField(
        verbose_name=_('Content'),
        help_text=_('Content of the notification')
    )
    
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.GENERAL,
        verbose_name=_('Notification Type'),
        help_text=_('Type of notification')
    )
    
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        verbose_name=_('Priority'),
        help_text=_('Priority level of the notification')
    )
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Status'),
        help_text=_('Current status of the notification')
    )
    
    # Target audience
    target_user_types = models.JSONField(
        default=list,
        verbose_name=_('Target User Types'),
        help_text=_('List of user types this notification targets')
    )
    
    target_users = models.ManyToManyField(
        User,
        blank=True,
        verbose_name=_('Target Users'),
        help_text=_('Specific users to receive this notification')
    )
    
    # Scheduling
    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Scheduled At'),
        help_text=_('When to send this notification (leave empty for immediate)')
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Expires At'),
        help_text=_('When this notification expires (leave empty for no expiration)')
    )
    
    # Display settings
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Whether this notification is currently active')
    )
    
    show_on_dashboard = models.BooleanField(
        default=True,
        verbose_name=_('Show on Dashboard'),
        help_text=_('Whether to show this notification on the dashboard')
    )
    
    require_acknowledgment = models.BooleanField(
        default=False,
        verbose_name=_('Require Acknowledgment'),
        help_text=_('Whether users must acknowledge this notification')
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_notifications',
        verbose_name=_('Created By'),
        help_text=_('User who created this notification')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        db_table = 'medguard_notifications'
        indexes = [
            models.Index(fields=['notification_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['scheduled_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
    
    @property
    def is_expired(self):
        """Check if notification is expired."""
        if self.expires_at:
            return self.expires_at < timezone.now()
        return False
    
    @property
    def is_scheduled(self):
        """Check if notification is scheduled for future delivery."""
        if self.scheduled_at:
            return self.scheduled_at > timezone.now()
        return False
    
    @property
    def is_critical(self):
        """Check if notification is critical priority."""
        return self.priority == self.Priority.CRITICAL
    
    def clean(self):
        """Custom validation for the model."""
        # Validate expires_at is after scheduled_at
        if self.scheduled_at and self.expires_at and self.expires_at <= self.scheduled_at:
            raise ValidationError({
                'expires_at': _('Expiration date must be after scheduled date')
            })
        
        # Validate target_user_types is a list
        if not isinstance(self.target_user_types, list):
            raise ValidationError({
                'target_user_types': _('Target user types must be a list')
            })


class UserNotification(models.Model):
    """
    User notification model for tracking individual user notification states.
    """
    
    # Status choices
    class Status(models.TextChoices):
        UNREAD = 'unread', _('Unread')
        READ = 'read', _('Read')
        ACKNOWLEDGED = 'acknowledged', _('Acknowledged')
        DISMISSED = 'dismissed', _('Dismissed')
    
    # Relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_notifications',
        verbose_name=_('User'),
        help_text=_('User who received this notification')
    )
    
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name='user_notifications',
        verbose_name=_('Notification'),
        help_text=_('Associated notification')
    )
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNREAD,
        verbose_name=_('Status'),
        help_text=_('Current status of this notification for the user')
    )
    
    # Timestamps
    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Sent At'),
        help_text=_('When this notification was sent to the user')
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Read At'),
        help_text=_('When the user read this notification')
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Acknowledged At'),
        help_text=_('When the user acknowledged this notification')
    )
    
    dismissed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Dismissed At'),
        help_text=_('When the user dismissed this notification')
    )
    
    class Meta:
        verbose_name = _('User Notification')
        verbose_name_plural = _('User Notifications')
        db_table = 'medguard_user_notifications'
        indexes = [
            models.Index(fields=['user', 'notification']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['sent_at']),
        ]
        ordering = ['-sent_at']
        unique_together = ['user', 'notification']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.notification.title}"
    
    @property
    def is_unread(self):
        """Check if notification is unread."""
        return self.status == self.Status.UNREAD
    
    @property
    def is_read(self):
        """Check if notification is read."""
        return self.status in [self.Status.READ, self.Status.ACKNOWLEDGED]
    
    def mark_as_read(self):
        """Mark notification as read."""
        if self.status == self.Status.UNREAD:
            self.status = self.Status.READ
            self.read_at = timezone.now()
            self.save()
    
    def acknowledge(self):
        """Acknowledge the notification."""
        if self.notification.require_acknowledgment:
            self.status = self.Status.ACKNOWLEDGED
            self.acknowledged_at = timezone.now()
            self.save()
    
    def dismiss(self):
        """Dismiss the notification."""
        self.status = self.Status.DISMISSED
        self.dismissed_at = timezone.now()
        self.save()
    
    def clean(self):
        """Custom validation for the model."""
        # Validate timestamps are in correct order
        if self.read_at and self.sent_at and self.read_at < self.sent_at:
            raise ValidationError({
                'read_at': _('Read time cannot be before sent time')
            })
        
        if self.acknowledged_at and self.read_at and self.acknowledged_at < self.read_at:
            raise ValidationError({
                'acknowledged_at': _('Acknowledged time cannot be before read time')
            })
        
        if self.dismissed_at and self.sent_at and self.dismissed_at < self.sent_at:
            raise ValidationError({
                'dismissed_at': _('Dismissed time cannot be before sent time')
            })


class NotificationTemplate(models.Model):
    """
    Notification template model for reusable notification formats.
    """
    
    # Template type choices
    class TemplateType(models.TextChoices):
        EMAIL = 'email', _('Email Template')
        SMS = 'sms', _('SMS Template')
        PUSH = 'push', _('Push Notification Template')
        IN_APP = 'in_app', _('In-App Notification Template')
    
    # Basic template information
    name = models.CharField(
        max_length=200,
        verbose_name=_('Template Name'),
        help_text=_('Name of the notification template')
    )
    
    template_type = models.CharField(
        max_length=20,
        choices=TemplateType.choices,
        verbose_name=_('Template Type'),
        help_text=_('Type of notification template')
    )
    
    subject = models.CharField(
        max_length=200,
        verbose_name=_('Subject'),
        help_text=_('Subject line for email templates'),
        blank=True
    )
    
    content = models.TextField(
        verbose_name=_('Content'),
        help_text=_('Template content with placeholders')
    )
    
    # Template variables
    variables = models.JSONField(
        default=dict,
        verbose_name=_('Variables'),
        help_text=_('Available variables for this template')
    )
    
    # Settings
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        help_text=_('Whether this template is active')
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_templates',
        verbose_name=_('Created By'),
        help_text=_('User who created this template')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Notification Template')
        verbose_name_plural = _('Notification Templates')
        db_table = 'medguard_notification_templates'
        indexes = [
            models.Index(fields=['template_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['name']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render_content(self, context):
        """Render template content with provided context."""
        try:
            from django.template import Template, Context
            template = Template(self.content)
            return template.render(Context(context))
        except Exception as e:
            return f"Template rendering error: {str(e)}"
    
    def clean(self):
        """Custom validation for the model."""
        # Validate variables is a dictionary
        if not isinstance(self.variables, dict):
            raise ValidationError({
                'variables': _('Variables must be a dictionary')
            })
        
        # Validate subject is provided for email templates
        if self.template_type == self.TemplateType.EMAIL and not self.subject:
            raise ValidationError({
                'subject': _('Subject is required for email templates')
            })


class UserNotificationPreferences(models.Model):
    """
    User notification preferences model for managing notification settings.
    """
    
    # Notification channel choices
    class Channel(models.TextChoices):
        EMAIL = 'email', _('Email')
        SMS = 'sms', _('SMS')
        PUSH = 'push', _('Push Notification')
        IN_APP = 'in_app', _('In-App Notification')
    
    # Time preference choices
    class TimePreference(models.TextChoices):
        IMMEDIATE = 'immediate', _('Immediate')
        MORNING = 'morning', _('Morning (8:00 AM)')
        AFTERNOON = 'afternoon', _('Afternoon (2:00 PM)')
        EVENING = 'evening', _('Evening (8:00 PM)')
        CUSTOM = 'custom', _('Custom Time')
    
    # Relationships
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        verbose_name=_('User'),
        help_text=_('User who owns these preferences')
    )
    
    # Email preferences
    email_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Email Notifications Enabled'),
        help_text=_('Whether to send email notifications')
    )
    
    email_time_preference = models.CharField(
        max_length=20,
        choices=TimePreference.choices,
        default=TimePreference.IMMEDIATE,
        verbose_name=_('Email Time Preference'),
        help_text=_('When to send email notifications')
    )
    
    email_custom_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name=_('Email Custom Time'),
        help_text=_('Custom time for email notifications')
    )
    
    # SMS preferences
    sms_notifications_enabled = models.BooleanField(
        default=False,
        verbose_name=_('SMS Notifications Enabled'),
        help_text=_('Whether to send SMS notifications')
    )
    
    sms_phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('SMS Phone Number'),
        help_text=_('Phone number for SMS notifications')
    )
    
    sms_time_preference = models.CharField(
        max_length=20,
        choices=TimePreference.choices,
        default=TimePreference.IMMEDIATE,
        verbose_name=_('SMS Time Preference'),
        help_text=_('When to send SMS notifications')
    )
    
    # Push notification preferences
    push_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Push Notifications Enabled'),
        help_text=_('Whether to send push notifications')
    )
    
    push_device_token = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Push Device Token'),
        help_text=_('Device token for push notifications')
    )
    
    # In-app notification preferences
    in_app_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('In-App Notifications Enabled'),
        help_text=_('Whether to show in-app notifications')
    )
    
    # Notification type preferences
    medication_reminders_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Medication Reminders Enabled'),
        help_text=_('Whether to receive medication reminders')
    )
    
    stock_alerts_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Stock Alerts Enabled'),
        help_text=_('Whether to receive stock alerts')
    )
    
    system_notifications_enabled = models.BooleanField(
        default=True,
        verbose_name=_('System Notifications Enabled'),
        help_text=_('Whether to receive system notifications')
    )
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(
        default=False,
        verbose_name=_('Quiet Hours Enabled'),
        help_text=_('Whether to enable quiet hours')
    )
    
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        default='22:00',
        verbose_name=_('Quiet Hours Start'),
        help_text=_('Start time for quiet hours')
    )
    
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        default='08:00',
        verbose_name=_('Quiet Hours End'),
        help_text=_('End time for quiet hours')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User Notification Preference')
        verbose_name_plural = _('User Notification Preferences')
        db_table = 'medguard_user_notification_preferences'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['email_notifications_enabled']),
            models.Index(fields=['push_notifications_enabled']),
        ]
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
    
    @property
    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours."""
        if not self.quiet_hours_enabled:
            return False
        
        now = timezone.now().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:
            # Quiet hours span midnight
            return now >= start or now <= end
    
    def get_preferred_time(self, channel):
        """Get the preferred time for a specific channel."""
        if channel == self.Channel.EMAIL:
            if self.email_time_preference == self.TimePreference.CUSTOM:
                return self.email_custom_time
            elif self.email_time_preference == self.TimePreference.MORNING:
                return timezone.datetime.strptime('08:00', '%H:%M').time()
            elif self.email_time_preference == self.TimePreference.AFTERNOON:
                return timezone.datetime.strptime('14:00', '%H:%M').time()
            elif self.email_time_preference == self.TimePreference.EVENING:
                return timezone.datetime.strptime('20:00', '%H:%M').time()
        elif channel == self.Channel.SMS:
            if self.sms_time_preference == self.TimePreference.CUSTOM:
                return self.email_custom_time  # Reuse email custom time for now
            elif self.sms_time_preference == self.TimePreference.MORNING:
                return timezone.datetime.strptime('08:00', '%H:%M').time()
            elif self.sms_time_preference == self.TimePreference.AFTERNOON:
                return timezone.datetime.strptime('14:00', '%H:%M').time()
            elif self.sms_time_preference == self.TimePreference.EVENING:
                return timezone.datetime.strptime('20:00', '%H:%M').time()
        
        return None  # Immediate delivery
    
    def clean(self):
        """Validate notification preferences."""
        if self.quiet_hours_enabled and (not self.quiet_hours_start or not self.quiet_hours_end):
            raise ValidationError(_('Quiet hours start and end times are required when quiet hours are enabled.'))
        
        if self.email_time_preference == self.TimePreference.CUSTOM and not self.email_custom_time:
            raise ValidationError(_('Custom time is required when email time preference is set to custom.'))
        
        if self.sms_notifications_enabled and not self.sms_phone_number:
            raise ValidationError(_('SMS phone number is required when SMS notifications are enabled.'))
        
        if self.push_notifications_enabled and not self.push_device_token:
            # Warning but not error - token might be set later
            pass
