# MedGuard SA - Modern Notification System

## Overview

This document describes the implementation of a comprehensive, modern notification system for MedGuard SA using Django 5 and Wagtail 7 compatible libraries. The system provides multi-channel notifications (in-app, email, push, SMS) with advanced features like rate limiting, user preferences, and workflow integration.

## Architecture

The notification system is built on three main pillars:

1. **django-nyt** - In-app notifications with real-time updates
2. **django-post-office** - Email queuing and templating
3. **django-push-notifications** - Mobile and web push notifications
4. **Celery** - Background task processing

## Features

### ✅ Implemented Features

- **Multi-channel notifications**: In-app, email, push, SMS
- **User preferences**: Granular control over notification types and timing
- **Rate limiting**: Prevents notification spam
- **Template system**: Reusable email templates with i18n support
- **Workflow integration**: Automatic notifications for Wagtail workflow events
- **Background processing**: Asynchronous notification delivery
- **Digest notifications**: Daily and weekly summaries
- **Scheduled notifications**: Future-dated notification delivery
- **Cleanup automation**: Automatic purging of old notifications
- **Statistics tracking**: Notification metrics and monitoring

### 🔄 Planned Features

- SMS integration (Twilio/AWS SNS)
- Advanced push notification targeting
- Notification analytics dashboard
- A/B testing for notification content
- Advanced filtering and search

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Update Django Settings

The notification apps are already configured in `settings/base.py`:

```python
THIRD_PARTY_APPS = [
    # ... other apps
    'django_nyt',
    'post_office',
    'push_notifications',
]

LOCAL_APPS = [
    # ... other apps
    'medguard_notifications',
]
```

### 3. Run Migrations

```bash
python manage.py migrate
```

### 4. Set Up the Notification System

```bash
python manage.py setup_notification_system
```

This command will:
- Create default email templates
- Set up user notification preferences
- Configure post-office email backend

### 5. Start Background Workers

```bash
# Start Celery worker
celery -A medguard_backend worker -l info

# Start Celery beat (scheduler)
celery -A medguard_backend beat -l info

# Start post-office email worker
python manage.py send_queued_mail --processes=2 --threads=5
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@medguard-sa.com

# Push Notifications
FCM_SERVER_KEY=your-fcm-server-key
APNS_AUTH_KEY_PATH=/path/to/apns-auth-key.p8
APNS_AUTH_KEY_ID=your-auth-key-id
APNS_TEAM_ID=your-team-id
APNS_TOPIC=com.medguard.sa

# Redis (for Celery and caching)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Settings Configuration

The notification system is configured in `settings/base.py`:

```python
# django-nyt configuration
NYT_USE_CHANNELS = True
NYT_NOTIFICATION_MAX_DAYS = 90
NYT_USE_JSONFIELD = True

# django-post-office configuration
POST_OFFICE = {
    'BACKENDS': {
        'default': 'django.core.mail.backends.smtp.EmailBackend',
        'console': 'django.core.mail.backends.console.EmailBackend',
    },
    'DEFAULT_PRIORITY': 'medium',
    'BATCH_SIZE': 100,
    'THREADS_PER_PROCESS': 5,
}

# django-push-notifications configuration
PUSH_NOTIFICATIONS_SETTINGS = {
    'FCM_DJANGO_SETTINGS': {
        'FCM_SERVER_KEY': os.getenv('FCM_SERVER_KEY', ''),
    },
    'APNS_AUTH_KEY_PATH': os.getenv('APNS_AUTH_KEY_PATH', ''),
    'APNS_AUTH_KEY_ID': os.getenv('APNS_AUTH_KEY_ID', ''),
    'APNS_TEAM_ID': os.getenv('APNS_TEAM_ID', ''),
    'APNS_TOPIC': os.getenv('APNS_TOPIC', 'com.medguard.sa'),
}

# Rate limiting
NOTIFICATION_RATE_LIMITS = {
    'email': {'per_user_per_hour': 10, 'per_user_per_day': 50},
    'sms': {'per_user_per_hour': 5, 'per_user_per_day': 20},
    'push': {'per_user_per_hour': 20, 'per_user_per_day': 100},
}
```

## Usage

### Basic Notification Sending

```python
from medguard_notifications.services import notification_service

# Send a simple notification
result = notification_service.send_notification(
    user=user,
    title="Welcome to MedGuard SA",
    message="Thank you for joining our healthcare platform.",
    notification_type='general',
    channels=['in_app', 'email'],
    priority='medium'
)

print(result)  # {'in_app': True, 'email': True}
```

### Medication Reminders

```python
# Send medication reminder
result = notification_service.send_medication_reminder(
    user=user,
    medication_name="Aspirin",
    dosage="100mg",
    time="08:00",
    channels=['in_app', 'push']
)
```

### Stock Alerts

```python
# Send stock alert
result = notification_service.send_stock_alert(
    user=user,
    medication_name="Paracetamol",
    current_stock=50,
    threshold=100,
    channels=['in_app', 'email']
)
```

### Bulk Notifications

```python
# Send to multiple users
users = User.objects.filter(is_staff=True)
result = notification_service.send_bulk_notifications(
    users=users,
    title="System Maintenance",
    message="Scheduled maintenance will begin in 1 hour.",
    notification_type='maintenance',
    channels=['in_app', 'email']
)
```

### System Maintenance Notifications

```python
from datetime import datetime, timedelta

# Send maintenance notification
start_time = datetime.now() + timedelta(hours=1)
end_time = start_time + timedelta(hours=2)

result = notification_service.send_system_maintenance(
    users=User.objects.all(),
    maintenance_type="Database Update",
    start_time=start_time,
    end_time=end_time,
    description="Routine database maintenance and optimization.",
    channels=['in_app', 'email']
)
```

## Wagtail Integration

### Workflow Notifications

The system automatically sends notifications for Wagtail workflow events:

- **Content submitted for review** → Notifies reviewers
- **Content approved** → Notifies content creators
- **Content rejected** → Notifies content creators with comments
- **Page published** → Notifies relevant staff members

### Custom Notifiers

You can create custom Wagtail notifiers by extending the `Notifier` class:

```python
from wagtail.admin.mail import Notifier
from medguard_notifications.services import notification_service

class CustomPageNotifier(Notifier):
    notification = "custom_page_event"
    
    def get_recipient_users(self, instance, **kwargs):
        return User.objects.filter(is_staff=True)
    
    def send(self, recipient, context):
        notification_service.send_notification(
            user=recipient,
            title="Custom Event",
            message="A custom event occurred.",
            notification_type='custom',
            channels=['in_app', 'email']
        )
```

## Email Templates

### Template Structure

Email templates are stored in the database using django-post-office and can be managed through the Django admin interface.

### Available Templates

- `base_notification` - Base template for all notifications
- `medication_reminder` - Medication reminder notifications
- `stock_alert` - Stock alert notifications
- `system_maintenance` - System maintenance notifications
- `workflow_task_submitted` - Workflow task submitted notifications
- `workflow_task_approved` - Workflow task approved notifications
- `workflow_task_rejected` - Workflow task rejected notifications
- `security_alert` - Security alert notifications
- `daily_digest` - Daily digest notifications
- `weekly_digest` - Weekly digest notifications

### Template Variables

Common template variables available in all templates:

- `user` - The recipient user object
- `title` - Notification title
- `message` - Notification message
- `notification_type` - Type of notification
- `priority` - Notification priority
- `site_name` - Site name from settings
- `site_url` - Base site URL

## Background Tasks

### Celery Tasks

The system uses Celery for background processing:

- `send_email_notification_task` - Send individual email notifications
- `send_bulk_email_notifications_task` - Send bulk email notifications
- `send_daily_digest_notifications` - Send daily digest emails
- `send_weekly_digest_notifications` - Send weekly digest emails
- `cleanup_old_notifications` - Clean up old notifications
- `process_scheduled_notifications` - Process scheduled notifications
- `send_medication_reminders` - Send medication reminders
- `send_stock_alerts` - Send stock alerts
- `update_notification_statistics` - Update notification statistics

### Task Scheduling

Tasks are automatically scheduled using Celery Beat:

- **Daily digest**: Every day at 8:00 AM
- **Weekly digest**: Every Monday at 9:00 AM
- **Scheduled notifications**: Every 5 minutes
- **Medication reminders**: Every 10 minutes
- **Stock alerts**: Every hour
- **Cleanup**: Daily at 2:00 AM
- **Statistics**: Every hour

## User Preferences

### Preference Model

Users can control their notification preferences through the `UserNotificationPreferences` model:

```python
prefs = user.notification_preferences

# Enable/disable channels
prefs.email_notifications_enabled = True
prefs.push_notifications_enabled = True
prefs.sms_notifications_enabled = False
prefs.in_app_notifications_enabled = True

# Enable/disable notification types
prefs.medication_reminders_enabled = True
prefs.stock_alerts_enabled = True
prefs.system_notifications_enabled = True

# Time preferences
prefs.email_time_preference = 'morning'  # immediate, morning, afternoon, evening, custom
prefs.quiet_hours_enabled = True
prefs.quiet_hours_start = time(22, 0)  # 10:00 PM
prefs.quiet_hours_end = time(8, 0)     # 8:00 AM

prefs.save()
```

## API Endpoints

### REST API

The notification system provides REST API endpoints:

- `GET /api/notifications/` - List user notifications
- `POST /api/notifications/` - Create notification
- `GET /api/notifications/{id}/` - Get notification details
- `PUT /api/notifications/{id}/` - Update notification
- `DELETE /api/notifications/{id}/` - Delete notification
- `POST /api/notifications/{id}/mark-read/` - Mark as read
- `POST /api/notifications/{id}/acknowledge/` - Acknowledge notification
- `GET /api/notifications/preferences/` - Get user preferences
- `PUT /api/notifications/preferences/` - Update user preferences

### WebSocket Support

For real-time notifications, the system supports WebSockets through django-nyt and Django Channels:

```javascript
// Connect to WebSocket
const socket = new WebSocket('ws://localhost:8000/ws/notifications/');

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('New notification:', data);
};
```

## Monitoring & Analytics

### Statistics

The system tracks various notification statistics:

- Notifications sent by type
- User notification status (read/unread/acknowledged)
- Delivery success rates
- Channel usage statistics

### Logging

All notification activities are logged with appropriate log levels:

```python
import logging
logger = logging.getLogger('medguard_notifications')

# Log notification sent
logger.info(f"Notification sent to user {user.id} via {channels}")

# Log errors
logger.error(f"Failed to send notification: {error}")
```

### Health Checks

Monitor the notification system health:

```bash
# Check Celery worker status
celery -A medguard_backend inspect active

# Check post-office email queue
python manage.py show_queued_mail

# Check notification statistics
python manage.py shell
>>> from medguard_notifications.models import Notification
>>> Notification.objects.count()
```

## Security Considerations

### Rate Limiting

The system implements rate limiting to prevent notification spam:

- Per-user hourly limits
- Per-user daily limits
- Global hourly limits

### Data Privacy

- User preferences are stored securely
- Notification content is sanitized
- Personal data is encrypted in transit

### Access Control

- Notifications are user-scoped
- Admin users can manage system-wide notifications
- API endpoints require authentication

## Troubleshooting

### Common Issues

1. **Emails not sending**
   - Check SMTP configuration
   - Verify post-office worker is running
   - Check email templates exist

2. **Push notifications not working**
   - Verify FCM/APNS configuration
   - Check device tokens are valid
   - Ensure push notifications are enabled

3. **Celery tasks not executing**
   - Check Celery worker is running
   - Verify Redis connection
   - Check task routing configuration

### Debug Commands

```bash
# Test email sending
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])

# Test notification service
python manage.py shell
>>> from medguard_notifications.services import notification_service
>>> from django.contrib.auth import get_user_model
>>> user = get_user_model().objects.first()
>>> notification_service.send_notification(user, "Test", "Test message")

# Check notification preferences
python manage.py shell
>>> from medguard_notifications.models import UserNotificationPreferences
>>> UserNotificationPreferences.objects.all()
```

## Performance Optimization

### Database Optimization

- Indexes on frequently queried fields
- Efficient queries with select_related/prefetch_related
- Regular cleanup of old notifications

### Caching

- Template caching for email templates
- Rate limit caching using Redis
- Statistics caching for quick access

### Background Processing

- Asynchronous email sending
- Bulk notification processing
- Scheduled task execution

## Future Enhancements

### Planned Features

1. **Advanced Analytics Dashboard**
   - Real-time notification metrics
   - User engagement analytics
   - A/B testing capabilities

2. **Enhanced Push Notifications**
   - Rich media support
   - Action buttons
   - Deep linking

3. **SMS Integration**
   - Twilio integration
   - AWS SNS integration
   - Multi-language SMS support

4. **Advanced Filtering**
   - Smart notification grouping
   - Priority-based filtering
   - Custom notification rules

### Integration Opportunities

- **Slack/Teams integration** for team notifications
- **Zapier integration** for external workflows
- **Analytics platforms** for advanced reporting
- **Customer support systems** for ticket notifications

## Contributing

When contributing to the notification system:

1. Follow the existing code style
2. Add comprehensive tests
3. Update documentation
4. Consider backward compatibility
5. Test with multiple notification channels

## License

This notification system is part of the MedGuard SA project and follows the same licensing terms.

---

For more information, contact the development team or refer to the individual library documentation:

- [django-nyt documentation](https://django-nyt.readthedocs.io/)
- [django-post-office documentation](https://django-post-office.readthedocs.io/)
- [django-push-notifications documentation](https://django-push-notifications.readthedocs.io/)
- [Celery documentation](https://docs.celeryproject.org/) 