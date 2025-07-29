"""
Django management command to set up the notification system.

This command creates default email templates and initial configuration
for the MedGuard SA notification system.
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone
from post_office.models import EmailTemplate
from medguard_notifications.models import UserNotificationPreferences

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up the notification system with default templates and configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of existing templates',
        )
        parser.add_argument(
            '--skip-migrations',
            action='store_true',
            help='Skip running migrations',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Setting up MedGuard SA notification system...')
        )

        # Run migrations if not skipped
        if not options['skip_migrations']:
            self.stdout.write('Running migrations...')
            call_command('migrate', verbosity=0)
            self.stdout.write(
                self.style.SUCCESS('✓ Migrations completed')
            )

        # Create default email templates
        self.create_email_templates(force=options['force'])

        # Create notification preferences for existing users
        self.create_user_preferences()

        # Set up post-office email backend
        self.setup_post_office()

        self.stdout.write(
            self.style.SUCCESS('✓ Notification system setup completed successfully!')
        )

    def create_email_templates(self, force=False):
        """Create default email templates for notifications."""
        self.stdout.write('Creating email templates...')

        templates = [
            {
                'name': 'base_notification',
                'description': 'Base notification template',
                'subject': '{{ title|default:"MedGuard SA Notification" }}',
                'html_content': self.get_base_template_content(),
                'text_content': self.get_base_template_text(),
            },
            {
                'name': 'medication_reminder',
                'description': 'Medication reminder notification',
                'subject': 'Medication Reminder - {{ medication_name }}',
                'html_content': self.get_medication_reminder_content(),
                'text_content': self.get_medication_reminder_text(),
            },
            {
                'name': 'stock_alert',
                'description': 'Stock alert notification',
                'subject': 'Stock Alert - {{ medication_name }}',
                'html_content': self.get_stock_alert_content(),
                'text_content': self.get_stock_alert_text(),
            },
            {
                'name': 'system_maintenance',
                'description': 'System maintenance notification',
                'subject': 'System Maintenance Scheduled',
                'html_content': self.get_maintenance_content(),
                'text_content': self.get_maintenance_text(),
            },
            {
                'name': 'workflow_task_submitted',
                'description': 'Workflow task submitted notification',
                'subject': 'Content Review Required - {{ title }}',
                'html_content': self.get_workflow_submitted_content(),
                'text_content': self.get_workflow_submitted_text(),
            },
            {
                'name': 'workflow_task_approved',
                'description': 'Workflow task approved notification',
                'subject': 'Content Approved - {{ title }}',
                'html_content': self.get_workflow_approved_content(),
                'text_content': self.get_workflow_approved_text(),
            },
            {
                'name': 'workflow_task_rejected',
                'description': 'Workflow task rejected notification',
                'subject': 'Content Requires Revision - {{ title }}',
                'html_content': self.get_workflow_rejected_content(),
                'text_content': self.get_workflow_rejected_text(),
            },
            {
                'name': 'security_alert',
                'description': 'Security alert notification',
                'subject': 'Security Alert: {{ alert_type }}',
                'html_content': self.get_security_alert_content(),
                'text_content': self.get_security_alert_text(),
            },
            {
                'name': 'daily_digest',
                'description': 'Daily digest notification',
                'subject': 'Daily Digest - {{ date }}',
                'html_content': self.get_daily_digest_content(),
                'text_content': self.get_daily_digest_text(),
            },
            {
                'name': 'weekly_digest',
                'description': 'Weekly digest notification',
                'subject': 'Weekly Digest - {{ week_start }} to {{ week_end }}',
                'html_content': self.get_weekly_digest_content(),
                'text_content': self.get_weekly_digest_text(),
            },
        ]

        for template_data in templates:
            template, created = EmailTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults={
                    'description': template_data['description'],
                    'subject': template_data['subject'],
                    'html_content': template_data['html_content'],
                    'text_content': template_data['text_content'],
                }
            )

            if created:
                self.stdout.write(f'  ✓ Created template: {template_data["name"]}')
            elif force:
                template.description = template_data['description']
                template.subject = template_data['subject']
                template.html_content = template_data['html_content']
                template.text_content = template_data['text_content']
                template.save()
                self.stdout.write(f'  ✓ Updated template: {template_data["name"]}')
            else:
                self.stdout.write(f'  - Template already exists: {template_data["name"]}')

        self.stdout.write(
            self.style.SUCCESS('✓ Email templates setup completed')
        )

    def create_user_preferences(self):
        """Create notification preferences for existing users."""
        self.stdout.write('Creating user notification preferences...')

        users = User.objects.all()
        created_count = 0

        for user in users:
            prefs, created = UserNotificationPreferences.objects.get_or_create(
                user=user,
                defaults={
                    'email_notifications_enabled': True,
                    'in_app_notifications_enabled': True,
                    'push_notifications_enabled': True,
                    'sms_notifications_enabled': False,
                    'medication_reminders_enabled': True,
                    'stock_alerts_enabled': user.is_staff,
                    'system_notifications_enabled': True,
                }
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(f'✓ Created preferences for {created_count} users')
        )

    def setup_post_office(self):
        """Set up post-office email backend."""
        self.stdout.write('Setting up post-office email backend...')

        # Create default email backend configuration
        # This is handled in settings.py, but we can add any additional setup here

        self.stdout.write(
            self.style.SUCCESS('✓ Post-office setup completed')
        )

    def get_base_template_content(self):
        """Get the base notification template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type {{ notification_type|default:'general' }}">
    {{ notification_type|default:'General'|title }}
</div>

<div class="title priority-{{ priority|default:'medium' }}">
    {{ title|default:"Notification" }}
</div>

<div class="message">
    {{ message|safe }}
</div>

{% if action_url %}
<div class="action-center">
    <a href="{{ action_url }}" class="button">
        {% if action_text %}{{ action_text }}{% else %}View Details{% endif %}
    </a>
</div>
{% endif %}
{% endblock %}'''

    def get_base_template_text(self):
        """Get the base notification template text content."""
        return '''{{ title|default:"Notification" }}

{{ message }}

{% if action_url %}
View details: {{ action_url }}
{% endif %}

---
MedGuard SA Healthcare Management System
This notification was sent to {{ user.email }}'''

    def get_medication_reminder_content(self):
        """Get medication reminder template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type medication">
    Medication Reminder
</div>

<div class="title priority-high">
    Time to take your medication
</div>

<div class="message">
    <p>Hello {{ user.get_full_name|default:user.username }},</p>
    
    <p>It's time to take your medication:</p>
    
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>Medication:</strong> {{ medication_name }}<br>
        <strong>Dosage:</strong> {{ dosage }}<br>
        <strong>Time:</strong> {{ time }}
    </div>
    
    <p>Please take your medication as prescribed by your healthcare provider.</p>
</div>

<div class="action-center">
    <a href="{{ site_url }}/medications/" class="button">View Medication Schedule</a>
</div>
{% endblock %}'''

    def get_medication_reminder_text(self):
        """Get medication reminder template text content."""
        return '''Medication Reminder

Hello {{ user.get_full_name|default:user.username }},

It's time to take your medication:

Medication: {{ medication_name }}
Dosage: {{ dosage }}
Time: {{ time }}

Please take your medication as prescribed by your healthcare provider.

View your medication schedule: {{ site_url }}/medications/

---
MedGuard SA Healthcare Management System'''

    def get_stock_alert_content(self):
        """Get stock alert template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type stock">
    Stock Alert
</div>

<div class="title priority-{{ priority|default:'medium' }}">
    Low Stock Alert
</div>

<div class="message">
    <p>A medication is running low on stock:</p>
    
    <div style="background-color: #fef3c7; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>Medication:</strong> {{ medication_name }}<br>
        <strong>Current Stock:</strong> {{ current_stock }} units<br>
        <strong>Threshold:</strong> {{ threshold }} units
    </div>
    
    <p>Please reorder this medication to ensure continuous patient care.</p>
</div>

<div class="action-center">
    <a href="{{ site_url }}/admin/medications/" class="button">Manage Inventory</a>
</div>
{% endblock %}'''

    def get_stock_alert_text(self):
        """Get stock alert template text content."""
        return '''Stock Alert

A medication is running low on stock:

Medication: {{ medication_name }}
Current Stock: {{ current_stock }} units
Threshold: {{ threshold }} units

Please reorder this medication to ensure continuous patient care.

Manage inventory: {{ site_url }}/admin/medications/

---
MedGuard SA Healthcare Management System'''

    def get_maintenance_content(self):
        """Get maintenance notification template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type maintenance">
    System Maintenance
</div>

<div class="title priority-medium">
    Scheduled System Maintenance
</div>

<div class="message">
    <p>Hello {{ user.get_full_name|default:user.username }},</p>
    
    <p>We have scheduled system maintenance to ensure optimal performance:</p>
    
    <div style="background-color: #d1fae5; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>Type:</strong> {{ maintenance_type }}<br>
        <strong>Start Time:</strong> {{ start_time }}<br>
        <strong>End Time:</strong> {{ end_time }}
    </div>
    
    {% if description %}
    <p><strong>Details:</strong> {{ description }}</p>
    {% endif %}
    
    <p>During this time, some features may be temporarily unavailable. We apologize for any inconvenience.</p>
</div>
{% endblock %}'''

    def get_maintenance_text(self):
        """Get maintenance notification template text content."""
        return '''System Maintenance

Hello {{ user.get_full_name|default:user.username }},

We have scheduled system maintenance to ensure optimal performance:

Type: {{ maintenance_type }}
Start Time: {{ start_time }}
End Time: {{ end_time }}

{% if description %}
Details: {{ description }}
{% endif %}

During this time, some features may be temporarily unavailable. We apologize for any inconvenience.

---
MedGuard SA Healthcare Management System'''

    def get_workflow_submitted_content(self):
        """Get workflow task submitted template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type workflow">
    Content Review
</div>

<div class="title priority-medium">
    Content Review Required
</div>

<div class="message">
    <p>Hello {{ user.get_full_name|default:user.username }},</p>
    
    <p>Content has been submitted for your review:</p>
    
    <div style="background-color: #e0e7ff; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>Title:</strong> {{ title }}<br>
        <strong>Task:</strong> {{ task_name }}<br>
        <strong>Submitted by:</strong> {{ submitted_by }}
    </div>
    
    <p>Please review and approve or reject this content as appropriate.</p>
</div>

<div class="action-center">
    <a href="{{ site_url }}/admin/pages/{{ page_id }}/edit/" class="button">Review Content</a>
</div>
{% endblock %}'''

    def get_workflow_submitted_text(self):
        """Get workflow task submitted template text content."""
        return '''Content Review Required

Hello {{ user.get_full_name|default:user.username }},

Content has been submitted for your review:

Title: {{ title }}
Task: {{ task_name }}
Submitted by: {{ submitted_by }}

Please review and approve or reject this content as appropriate.

Review content: {{ site_url }}/admin/pages/{{ page_id }}/edit/

---
MedGuard SA Healthcare Management System'''

    def get_workflow_approved_content(self):
        """Get workflow task approved template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type workflow">
    Content Approved
</div>

<div class="title priority-low">
    Content Approved
</div>

<div class="message">
    <p>Hello {{ user.get_full_name|default:user.username }},</p>
    
    <p>Your content has been approved:</p>
    
    <div style="background-color: #d1fae5; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>Title:</strong> {{ title }}<br>
        <strong>Task:</strong> {{ task_name }}<br>
        <strong>Approved by:</strong> {{ approved_by }}
    </div>
    
    <p>Your content is now live and available to users.</p>
</div>

<div class="action-center">
    <a href="{{ site_url }}/admin/pages/{{ page_id }}/" class="button">View Content</a>
</div>
{% endblock %}'''

    def get_workflow_approved_text(self):
        """Get workflow task approved template text content."""
        return '''Content Approved

Hello {{ user.get_full_name|default:user.username }},

Your content has been approved:

Title: {{ title }}
Task: {{ task_name }}
Approved by: {{ approved_by }}

Your content is now live and available to users.

View content: {{ site_url }}/admin/pages/{{ page_id }}/

---
MedGuard SA Healthcare Management System'''

    def get_workflow_rejected_content(self):
        """Get workflow task rejected template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type workflow">
    Content Revision Required
</div>

<div class="title priority-high">
    Content Requires Revision
</div>

<div class="message">
    <p>Hello {{ user.get_full_name|default:user.username }},</p>
    
    <p>Your content requires revision before it can be approved:</p>
    
    <div style="background-color: #fee2e2; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>Title:</strong> {{ title }}<br>
        <strong>Task:</strong> {{ task_name }}<br>
        <strong>Rejected by:</strong> {{ rejected_by }}<br>
        <strong>Comments:</strong> {{ comments }}
    </div>
    
    <p>Please review the comments and make the necessary changes.</p>
</div>

<div class="action-center">
    <a href="{{ site_url }}/admin/pages/{{ page_id }}/edit/" class="button">Edit Content</a>
</div>
{% endblock %}'''

    def get_workflow_rejected_text(self):
        """Get workflow task rejected template text content."""
        return '''Content Revision Required

Hello {{ user.get_full_name|default:user.username }},

Your content requires revision before it can be approved:

Title: {{ title }}
Task: {{ task_name }}
Rejected by: {{ rejected_by }}
Comments: {{ comments }}

Please review the comments and make the necessary changes.

Edit content: {{ site_url }}/admin/pages/{{ page_id }}/edit/

---
MedGuard SA Healthcare Management System'''

    def get_security_alert_content(self):
        """Get security alert template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="notification-type security">
    Security Alert
</div>

<div class="title priority-critical">
    Security Alert: {{ alert_type }}
</div>

<div class="message">
    <p>A security alert has been triggered:</p>
    
    <div style="background-color: #fee2e2; padding: 15px; border-radius: 6px; margin: 15px 0;">
        <strong>Alert Type:</strong> {{ alert_type }}<br>
        <strong>Severity:</strong> {{ severity|title }}<br>
        <strong>Description:</strong> {{ description }}
    </div>
    
    <p>Please review this alert and take appropriate action if necessary.</p>
</div>

<div class="action-center">
    <a href="{{ site_url }}/admin/security/" class="button">Review Security</a>
</div>
{% endblock %}'''

    def get_security_alert_text(self):
        """Get security alert template text content."""
        return '''Security Alert

A security alert has been triggered:

Alert Type: {{ alert_type }}
Severity: {{ severity|title }}
Description: {{ description }}

Please review this alert and take appropriate action if necessary.

Review security: {{ site_url }}/admin/security/

---
MedGuard SA Healthcare Management System'''

    def get_daily_digest_content(self):
        """Get daily digest template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="title priority-low">
    Daily Digest - {{ date }}
</div>

<div class="message">
    <p>Hello {{ user.get_full_name|default:user.username }},</p>
    
    <p>Here's a summary of your notifications from {{ date }}:</p>
    
    {% if notifications %}
    <div style="margin: 20px 0;">
        {% for notification in notifications %}
        <div style="border-left: 3px solid #2563eb; padding: 10px; margin: 10px 0; background-color: #f8f9fa;">
            <strong>{{ notification.title }}</strong><br>
            <small>Type: {{ notification.type|title }} | Priority: {{ notification.priority|title }} | {{ notification.sent_at|date:"H:i" }}</small>
        </div>
        {% endfor %}
    </div>
    
    <p>You received {{ count }} notification{{ count|pluralize }} today.</p>
    {% else %}
    <p>You had no new notifications today.</p>
    {% endif %}
</div>

<div class="action-center">
    <a href="{{ site_url }}/notifications/" class="button">View All Notifications</a>
</div>
{% endblock %}'''

    def get_daily_digest_text(self):
        """Get daily digest template text content."""
        return '''Daily Digest - {{ date }}

Hello {{ user.get_full_name|default:user.username }},

Here's a summary of your notifications from {{ date }}:

{% if notifications %}
{% for notification in notifications %}
- {{ notification.title }} ({{ notification.type|title }}, {{ notification.priority|title }}, {{ notification.sent_at|date:"H:i" }})
{% endfor %}

You received {{ count }} notification{{ count|pluralize }} today.
{% else %}
You had no new notifications today.
{% endif %}

View all notifications: {{ site_url }}/notifications/

---
MedGuard SA Healthcare Management System'''

    def get_weekly_digest_content(self):
        """Get weekly digest template HTML content."""
        return '''{% extends "notifications/email/base_notification.html" %}

{% block content %}
<div class="title priority-low">
    Weekly Digest - {{ week_start }} to {{ week_end }}
</div>

<div class="message">
    <p>Hello {{ user.get_full_name|default:user.username }},</p>
    
    <p>Here's a summary of your notifications from {{ week_start }} to {{ week_end }}:</p>
    
    {% if notifications %}
    <div style="margin: 20px 0;">
        {% for notification in notifications %}
        <div style="border-left: 3px solid #2563eb; padding: 10px; margin: 10px 0; background-color: #f8f9fa;">
            <strong>{{ notification.title }}</strong><br>
            <small>Type: {{ notification.type|title }} | Priority: {{ notification.priority|title }} | {{ notification.sent_at|date:"M d, H:i" }}</small>
        </div>
        {% endfor %}
    </div>
    
    <p>You received {{ count }} notification{{ count|pluralize }} this week.</p>
    {% else %}
    <p>You had no new notifications this week.</p>
    {% endif %}
</div>

<div class="action-center">
    <a href="{{ site_url }}/notifications/" class="button">View All Notifications</a>
</div>
{% endblock %}'''

    def get_weekly_digest_text(self):
        """Get weekly digest template text content."""
        return '''Weekly Digest - {{ week_start }} to {{ week_end }}

Hello {{ user.get_full_name|default:user.username }},

Here's a summary of your notifications from {{ week_start }} to {{ week_end }}:

{% if notifications %}
{% for notification in notifications %}
- {{ notification.title }} ({{ notification.type|title }}, {{ notification.priority|title }}, {{ notification.sent_at|date:"M d, H:i" }})
{% endfor %}

You received {{ count }} notification{{ count|pluralize }} this week.
{% else %}
You had no new notifications this week.
{% endif %}

View all notifications: {{ site_url }}/notifications/

---
MedGuard SA Healthcare Management System''' 