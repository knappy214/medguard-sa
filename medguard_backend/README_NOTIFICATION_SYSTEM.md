# MedGuard SA Notification System

A comprehensive notification system built with Django, Celery, and Redis for the MedGuard SA healthcare platform.

## Features

### ✅ Core Functionality
- **Redis Message Broker**: Fast and reliable message queuing
- **Periodic Tasks**: Automated medication reminders and stock alerts
- **Multi-channel Delivery**: Email, SMS, Push, and In-app notifications
- **User Preferences**: Granular control over notification timing and channels
- **Notification History**: Complete audit trail and management interface
- **Low Stock Alerts**: 5-day warning system for medication inventory
- **Expiring Medication Alerts**: Automatic detection of soon-to-expire medications

### 🔧 Technical Features
- **Celery Beat Integration**: Database-backed periodic task scheduling
- **Task Routing**: Separate queues for notifications and medications
- **Error Handling**: Comprehensive logging and error recovery
- **Internationalization**: Full i18n support (English/Afrikaans)
- **Template System**: Customizable email and notification templates
- **Quiet Hours**: Respect user-defined quiet hours
- **Bulk Operations**: Efficient batch notification processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django App    │    │   Celery Beat   │    │   Celery Worker │
│                 │    │                 │    │                 │
│ • Models        │───▶│ • Periodic      │───▶│ • Task          │
│ • Views         │    │   Tasks         │    │   Execution     │
│ • Admin         │    │ • Scheduling    │    │ • Email         │
│ • API           │    │ • Database      │    │ • Push          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Email/SMS     │
│                 │    │                 │    │   Services      │
│ • Notifications │    │ • Message Queue │    │ • SMTP          │
│ • User Prefs    │    │ • Cache         │    │ • SMS Gateway   │
│ • Task Results  │    │ • Session Store │    │ • Push Service  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Installation & Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Redis

Ensure Redis is running and accessible:

```bash
# Start Redis (if not already running)
redis-server

# Test connection
redis-cli ping
```

### 3. Run Migrations

```bash
python manage.py migrate
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results
```

### 4. Set Up Periodic Tasks

```bash
# Create all periodic tasks
python manage.py setup_notification_tasks

# List existing tasks
python manage.py setup_notification_tasks --list

# Force recreation of tasks
python manage.py setup_notification_tasks --force
```

### 5. Start Celery Services

```bash
# Terminal 1: Start Celery Worker
celery -A medguard_backend worker --loglevel=info

# Terminal 2: Start Celery Beat
celery -A medguard_backend beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Or run both together (development only)
celery -A medguard_backend worker --beat --scheduler django --loglevel=info
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@medguard-sa.com

# Site Configuration
WAGTAILADMIN_BASE_URL=http://localhost:8000
```

### Django Settings

The notification system is already configured in `settings/base.py`:

```python
# Celery Configuration
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_ROUTES = {
    'notifications.tasks.*': {'queue': 'notifications'},
    'medications.tasks.*': {'queue': 'medications'},
}

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 100},
        }
    }
}
```

## Usage

### 1. Basic Notification Service

```python
from notifications.services import NotificationService
from django.contrib.auth import get_user_model

User = get_user_model()

# Send a simple notification
user = User.objects.get(id=1)
result = NotificationService.send_medication_reminder(
    user=user,
    medication_name="Aspirin",
    dosage="100mg",
    instructions="Take with food"
)

# Send system notification to all staff
result = NotificationService.send_system_notification(
    title="System Maintenance",
    content="Scheduled maintenance tonight at 2 AM",
    priority="medium",
    target_user_types=["staff"]
)
```

### 2. Creating Custom Notifications

```python
from notifications.models import Notification

# Create a notification
notification = NotificationService.create_notification(
    title="Important Update",
    content="Your medication schedule has been updated",
    notification_type="medication",
    priority="high",
    target_users=[user],
    require_acknowledgment=True
)

# Send to specific user
result = NotificationService.send_notification_to_user(
    user=user,
    notification=notification,
    channels=['email', 'in_app']
)
```

### 3. Managing User Preferences

```python
from notifications.models import UserNotificationPreferences

# Get or create user preferences
preferences, created = UserNotificationPreferences.objects.get_or_create(
    user=user,
    defaults={
        'email_notifications_enabled': True,
        'push_notifications_enabled': True,
        'quiet_hours_enabled': True,
        'quiet_hours_start': '22:00',
        'quiet_hours_end': '08:00'
    }
)

# Update preferences
preferences.email_time_preference = 'morning'
preferences.save()
```

### 4. Periodic Task Management

```python
from notifications.periodic_tasks import *

# Create all periodic tasks
create_all_periodic_tasks()

# List all tasks
tasks = list_all_tasks()
for task in tasks:
    print(f"{task['name']}: {task['enabled']}")

# Disable a specific task
disable_task("Morning Medication Reminders")

# Enable a task
enable_task("Morning Medication Reminders")
```

## API Endpoints

### Notification Management

```python
# Get user notifications
GET /api/notifications/
GET /api/notifications/?status=unread&type=medication

# Mark notification as read
POST /api/notifications/{id}/mark-read/

# Acknowledge notification
POST /api/notifications/{id}/acknowledge/

# Dismiss notification
POST /api/notifications/{id}/dismiss/
```

### User Preferences

```python
# Get user preferences
GET /api/notification-preferences/

# Update preferences
PUT /api/notification-preferences/
{
    "email_notifications_enabled": true,
    "email_time_preference": "morning",
    "quiet_hours_enabled": true,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "08:00"
}
```

## Periodic Tasks

### Medication Reminders
- **Morning Reminders**: 8:00 AM daily
- **Afternoon Reminders**: 2:00 PM daily  
- **Evening Reminders**: 8:00 PM daily

### Stock Alerts
- **Low Stock Check**: Every 6 hours
- **Expiring Medications**: Daily at 9:00 AM (5-day warning)

### Maintenance
- **Cleanup Old Notifications**: Weekly on Sunday at 2:00 AM

## Monitoring & Logging

### Task Monitoring

```python
from django_celery_beat.models import PeriodicTask

# Check task status
tasks = PeriodicTask.objects.all()
for task in tasks:
    print(f"{task.name}: {task.enabled} (Last run: {task.last_run_at})")
```

### Logging

The system logs all activities to:
- Console output (development)
- File: `logs/django.log` (production)

Key log levels:
- `INFO`: Normal operations
- `WARNING`: Non-critical issues
- `ERROR`: Task failures and errors

### Health Checks

```bash
# Check Celery worker status
celery -A medguard_backend inspect active

# Check task queue
celery -A medguard_backend inspect stats

# Monitor task results
celery -A medguard_backend inspect reserved
```

## Testing

### Unit Tests

```bash
# Run notification tests
python manage.py test notifications.tests

# Run with coverage
coverage run --source='.' manage.py test notifications
coverage report
```

### Manual Testing

```python
# Test notification sending
from notifications.tasks import send_medication_reminder
result = send_medication_reminder.delay(schedule_id=1)
print(result.get())

# Test periodic tasks
from notifications.tasks import check_low_stock_alerts
result = check_low_stock_alerts.delay()
print(result.get())
```

## Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Check Redis status
   redis-cli ping
   
   # Restart Redis
   sudo systemctl restart redis
   ```

2. **Celery Worker Not Starting**
   ```bash
   # Check Celery configuration
   celery -A medguard_backend inspect ping
   
   # Clear task queue
   celery -A medguard_backend purge
   ```

3. **Tasks Not Running**
   ```bash
   # Check periodic tasks
   python manage.py setup_notification_tasks --list
   
   # Reset task counters
   python manage.py setup_notification_tasks --reset
   ```

4. **Email Not Sending**
   ```bash
   # Test email configuration
   python manage.py shell
   >>> from django.core.mail import send_mail
   >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

### Performance Optimization

1. **Redis Connection Pooling**
   ```python
   # Optimize connection pool
   CACHES = {
       'default': {
           'OPTIONS': {
               'CONNECTION_POOL_KWARGS': {'max_connections': 200}
           }
       }
   }
   ```

2. **Task Batching**
   ```python
   # Use bulk operations for multiple notifications
   from notifications.services import NotificationService
   NotificationService.send_notification_to_users(users, notification)
   ```

3. **Database Indexing**
   ```python
   # Ensure proper indexes exist
   python manage.py makemigrations
   python manage.py migrate
   ```

## Security Considerations

1. **Email Security**
   - Use TLS for email transmission
   - Implement rate limiting
   - Validate email addresses

2. **User Privacy**
   - Respect quiet hours
   - Allow users to opt-out
   - Secure notification preferences

3. **Data Protection**
   - Encrypt sensitive data
   - Implement audit logging
   - Regular data cleanup

## Future Enhancements

### Planned Features
- [ ] SMS integration (Twilio/AfricasTalking)
- [ ] Push notification service (Firebase/OneSignal)
- [ ] Advanced notification templates
- [ ] Notification analytics dashboard
- [ ] Mobile app integration
- [ ] Voice notifications
- [ ] Multi-language support expansion

### Scalability Improvements
- [ ] Redis clustering
- [ ] Multiple Celery workers
- [ ] Task result backend optimization
- [ ] Database query optimization
- [ ] Caching strategies

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/django.log`
3. Test individual components
4. Contact the development team

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Use meaningful commit messages
5. Test thoroughly before submitting

---

**MedGuard SA Notification System** - Built with ❤️ for better healthcare 