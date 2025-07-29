#!/usr/bin/env python
"""
Test script for the MedGuard SA notification system.

This script tests the various components of the notification system
to ensure everything is working correctly.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from medguard_notifications.services import notification_service
from medguard_notifications.models import (
    Notification, UserNotification, UserNotificationPreferences
)
from post_office.models import EmailTemplate

User = get_user_model()


def test_notification_service():
    """Test the notification service functionality."""
    print("🧪 Testing Notification Service...")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@medguard-sa.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': True,
        }
    )
    
    if created:
        print(f"  ✓ Created test user: {user.username}")
    else:
        print(f"  - Using existing test user: {user.username}")
    
    # Test basic notification
    print("\n📧 Testing basic notification...")
    try:
        result = notification_service.send_notification(
            user=user,
            title="Test Notification",
            message="This is a test notification from the MedGuard SA system.",
            notification_type='general',
            channels=['in_app', 'email'],
            priority='medium'
        )
        print(f"  ✓ Basic notification sent: {result}")
    except Exception as e:
        print(f"  ❌ Basic notification failed: {e}")
    
    # Test medication reminder
    print("\n💊 Testing medication reminder...")
    try:
        result = notification_service.send_medication_reminder(
            user=user,
            medication_name="Test Medication",
            dosage="100mg",
            time="08:00",
            channels=['in_app', 'push']
        )
        print(f"  ✓ Medication reminder sent: {result}")
    except Exception as e:
        print(f"  ❌ Medication reminder failed: {e}")
    
    # Test stock alert
    print("\n📦 Testing stock alert...")
    try:
        result = notification_service.send_stock_alert(
            user=user,
            medication_name="Test Medication",
            current_stock=50,
            threshold=100,
            channels=['in_app', 'email']
        )
        print(f"  ✓ Stock alert sent: {result}")
    except Exception as e:
        print(f"  ❌ Stock alert failed: {e}")
    
    # Test bulk notifications
    print("\n📨 Testing bulk notifications...")
    try:
        users = [user]  # Just test with one user for now
        result = notification_service.send_bulk_notifications(
            users=users,
            title="Bulk Test Notification",
            message="This is a bulk test notification.",
            notification_type='general',
            channels=['in_app', 'email']
        )
        print(f"  ✓ Bulk notification sent: {result}")
    except Exception as e:
        print(f"  ❌ Bulk notification failed: {e}")


def test_email_templates():
    """Test email template functionality."""
    print("\n📝 Testing Email Templates...")
    
    try:
        templates = EmailTemplate.objects.all()
        print(f"  ✓ Found {templates.count()} email templates")
        
        for template in templates:
            print(f"    - {template.name}: {template.description}")
            
    except Exception as e:
        print(f"  ❌ Email template test failed: {e}")


def test_user_preferences():
    """Test user notification preferences."""
    print("\n⚙️ Testing User Preferences...")
    
    try:
        user = User.objects.filter(username='test_user').first()
        if user:
            prefs, created = UserNotificationPreferences.objects.get_or_create(user=user)
            if created:
                print(f"  ✓ Created preferences for user: {user.username}")
            else:
                print(f"  - Using existing preferences for user: {user.username}")
            
            print(f"    - Email notifications: {prefs.email_notifications_enabled}")
            print(f"    - In-app notifications: {prefs.in_app_notifications_enabled}")
            print(f"    - Push notifications: {prefs.push_notifications_enabled}")
            print(f"    - SMS notifications: {prefs.sms_notifications_enabled}")
            
    except Exception as e:
        print(f"  ❌ User preferences test failed: {e}")


def test_notification_models():
    """Test notification models and database functionality."""
    print("\n🗄️ Testing Notification Models...")
    
    try:
        # Count notifications
        notification_count = Notification.objects.count()
        user_notification_count = UserNotification.objects.count()
        
        print(f"  ✓ Total notifications: {notification_count}")
        print(f"  ✓ Total user notifications: {user_notification_count}")
        
        # Test creating a notification
        notification = Notification.objects.create(
            title="Test Model Notification",
            content="Testing notification model creation.",
            notification_type='general',
            priority='medium',
            status='active',
            is_active=True
        )
        print(f"  ✓ Created test notification: {notification.id}")
        
        # Clean up
        notification.delete()
        print(f"  ✓ Cleaned up test notification")
        
    except Exception as e:
        print(f"  ❌ Notification models test failed: {e}")


def test_system_maintenance():
    """Test system maintenance notification."""
    print("\n🔧 Testing System Maintenance Notification...")
    
    try:
        user = User.objects.filter(username='test_user').first()
        if user:
            start_time = timezone.now() + timedelta(hours=1)
            end_time = start_time + timedelta(hours=2)
            
            result = notification_service.send_system_maintenance(
                users=[user],
                maintenance_type="Test Maintenance",
                start_time=start_time,
                end_time=end_time,
                description="This is a test maintenance notification.",
                channels=['in_app', 'email']
            )
            print(f"  ✓ System maintenance notification sent: {result}")
        else:
            print("  - No test user found for system maintenance test")
            
    except Exception as e:
        print(f"  ❌ System maintenance test failed: {e}")


def test_rate_limiting():
    """Test rate limiting functionality."""
    print("\n⏱️ Testing Rate Limiting...")
    
    try:
        user = User.objects.filter(username='test_user').first()
        if user:
            # Send multiple notifications quickly to test rate limiting
            for i in range(3):
                result = notification_service.send_notification(
                    user=user,
                    title=f"Rate Limit Test {i+1}",
                    message=f"This is rate limit test notification {i+1}.",
                    notification_type='general',
                    channels=['in_app'],
                    priority='low'
                )
                print(f"  - Rate limit test {i+1}: {result}")
            
            print("  ✓ Rate limiting test completed")
        else:
            print("  - No test user found for rate limiting test")
            
    except Exception as e:
        print(f"  ❌ Rate limiting test failed: {e}")


def cleanup_test_data():
    """Clean up test data."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        # Delete test notifications
        test_notifications = Notification.objects.filter(
            title__startswith='Test'
        )
        deleted_count = test_notifications.count()
        test_notifications.delete()
        print(f"  ✓ Deleted {deleted_count} test notifications")
        
        # Delete test user notifications
        test_user_notifications = UserNotification.objects.filter(
            notification__title__startswith='Test'
        )
        deleted_count = test_user_notifications.count()
        test_user_notifications.delete()
        print(f"  ✓ Deleted {deleted_count} test user notifications")
        
    except Exception as e:
        print(f"  ❌ Cleanup failed: {e}")


def main():
    """Run all notification system tests."""
    print("🚀 MedGuard SA Notification System Test")
    print("=" * 50)
    
    # Run tests
    test_notification_service()
    test_email_templates()
    test_user_preferences()
    test_notification_models()
    test_system_maintenance()
    test_rate_limiting()
    
    # Cleanup
    cleanup_test_data()
    
    print("\n" + "=" * 50)
    print("✅ Notification system test completed!")
    print("\nNext steps:")
    print("1. Check the Django admin for created notifications")
    print("2. Verify email templates in post-office admin")
    print("3. Test real email sending with proper SMTP configuration")
    print("4. Start Celery workers for background processing")
    print("5. Test push notifications with device tokens")


if __name__ == '__main__':
    main() 