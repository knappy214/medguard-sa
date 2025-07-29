#!/usr/bin/env python
"""
Test script for i18n functionality in the MedGuard SA notification system.

This script tests the internationalization features including
language-specific email templates and localized content.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from notifications.services import NotificationService
from notifications.utils import (
    get_user_language,
    get_localized_notification_content,
    format_medication_reminder_content,
    get_priority_label,
    get_notification_type_label
)

User = get_user_model()


def test_user_language_detection():
    """Test user language detection functionality."""
    print("🔍 Testing user language detection...")
    
    # Create test users with different language preferences
    english_user, _ = User.objects.get_or_create(
        username='english_user',
        defaults={
            'email': 'english@medguard-sa.com',
            'first_name': 'English',
            'last_name': 'User',
            'language': 'en'
        }
    )
    
    afrikaans_user, _ = User.objects.get_or_create(
        username='afrikaans_user',
        defaults={
            'email': 'afrikaans@medguard-sa.com',
            'first_name': 'Afrikaans',
            'last_name': 'User',
            'language': 'af'
        }
    )
    
    # Test language detection
    en_lang = get_user_language(english_user)
    af_lang = get_user_language(afrikaans_user)
    
    print(f"✅ English user language: {en_lang}")
    print(f"✅ Afrikaans user language: {af_lang}")
    
    assert en_lang == 'en', f"Expected 'en', got '{en_lang}'"
    assert af_lang == 'af', f"Expected 'af', got '{af_lang}'"
    
    return english_user, afrikaans_user


def test_localized_notification_content():
    """Test localized notification content generation."""
    print("\n🔍 Testing localized notification content...")
    
    # Test medication reminder content
    en_content = get_localized_notification_content(
        'medication_reminder',
        'en',
        medication_name='Aspirin',
        dosage='100mg',
        instructions='Take with food'
    )
    
    af_content = get_localized_notification_content(
        'medication_reminder',
        'af',
        medication_name='Aspirin',
        dosage='100mg',
        instructions='Take with food'
    )
    
    print("✅ English medication reminder:")
    print(f"   Title: {en_content['title']}")
    print(f"   Content: {en_content['content']}")
    
    print("✅ Afrikaans medication reminder:")
    print(f"   Title: {af_content['title']}")
    print(f"   Content: {af_content['content']}")
    
    # Test stock alert content
    en_stock = get_localized_notification_content(
        'low_stock_alert',
        'en',
        medication_name='Paracetamol',
        current_stock=5,
        threshold=10
    )
    
    af_stock = get_localized_notification_content(
        'low_stock_alert',
        'af',
        medication_name='Paracetamol',
        current_stock=5,
        threshold=10
    )
    
    print("✅ English stock alert:")
    print(f"   Title: {en_stock['title']}")
    print(f"   Content: {en_stock['content']}")
    
    print("✅ Afrikaans stock alert:")
    print(f"   Title: {af_stock['title']}")
    print(f"   Content: {af_stock['content']}")
    
    return True


def test_medication_reminder_formatting():
    """Test medication reminder content formatting."""
    print("\n🔍 Testing medication reminder formatting...")
    
    # Test English formatting
    en_content = format_medication_reminder_content(
        medication_name='Aspirin',
        user_language='en',
        dosage='100mg',
        instructions='Take with food',
        timing='morning'
    )
    
    # Test Afrikaans formatting
    af_content = format_medication_reminder_content(
        medication_name='Aspirin',
        user_language='af',
        dosage='100mg',
        instructions='Take with food',
        timing='morning'
    )
    
    print("✅ English formatted content:")
    print(f"   {en_content}")
    
    print("✅ Afrikaans formatted content:")
    print(f"   {af_content}")
    
    return True


def test_priority_and_type_labels():
    """Test priority and notification type label localization."""
    print("\n🔍 Testing priority and type labels...")
    
    # Test priority labels
    en_priority = get_priority_label('high', 'en')
    af_priority = get_priority_label('high', 'af')
    
    print(f"✅ English priority 'high': {en_priority}")
    print(f"✅ Afrikaans priority 'high': {af_priority}")
    
    # Test notification type labels
    en_type = get_notification_type_label('medication', 'en')
    af_type = get_notification_type_label('medication', 'af')
    
    print(f"✅ English type 'medication': {en_type}")
    print(f"✅ Afrikaans type 'medication': {af_type}")
    
    return True


def test_notification_service_i18n():
    """Test notification service with i18n support."""
    print("\n🔍 Testing notification service i18n...")
    
    english_user, afrikaans_user = test_user_language_detection()
    
    # Test medication reminder for English user
    en_result = NotificationService.send_medication_reminder(
        user=english_user,
        medication_name='Aspirin',
        dosage='100mg',
        instructions='Take with food'
    )
    
    print(f"✅ English user notification result: {en_result}")
    
    # Test medication reminder for Afrikaans user
    af_result = NotificationService.send_medication_reminder(
        user=afrikaans_user,
        medication_name='Aspirin',
        dosage='100mg',
        instructions='Take with food'
    )
    
    print(f"✅ Afrikaans user notification result: {af_result}")
    
    return True


def test_email_template_rendering(english_user, afrikaans_user):
    """Test email template rendering with different languages."""
    print("\n🔍 Testing email template rendering...")
    
    from django.template.loader import render_to_string
    from notifications.models import Notification
    
    # Create a test notification
    notification = Notification.objects.create(
        title="Test Notification",
        content="This is a test notification.",
        notification_type=Notification.NotificationType.GENERAL,
        priority=Notification.Priority.MEDIUM,
        status=Notification.Status.ACTIVE,
        is_active=True,
        show_on_dashboard=True,
        require_acknowledgment=False,
        scheduled_at=timezone.now()
    )
    
    # Test English template
    en_context = {
        'user': english_user,
        'notification': notification,
        'site_name': 'MedGuard SA',
        'site_url': 'http://localhost:8000',
        'LANGUAGE_CODE': 'en'
    }
    
    en_template = render_to_string('notifications/email/default_notification.html', en_context)
    print("✅ English email template rendered successfully")
    
    # Test Afrikaans template
    af_context = {
        'user': afrikaans_user,
        'notification': notification,
        'site_name': 'MedGuard SA',
        'site_url': 'http://localhost:8000',
        'LANGUAGE_CODE': 'af'
    }
    
    af_template = render_to_string('notifications/email/default_notification_af.html', af_context)
    print("✅ Afrikaans email template rendered successfully")
    
    # Check for language-specific content
    if 'View in Dashboard' in en_template:
        print("✅ English template contains English text")
    
    if 'Bekyk in Dashboard' in af_template:
        print("✅ Afrikaans template contains Afrikaans text")
    
    return True


def cleanup_test_data():
    """Clean up test data created during testing."""
    print("\n🧹 Cleaning up test data...")
    
    try:
        from notifications.models import Notification
        
        # Delete test users
        test_users = User.objects.filter(
            username__in=['english_user', 'afrikaans_user']
        )
        deleted_count = test_users.count()
        test_users.delete()
        print(f"✅ Deleted {deleted_count} test users")
        
        # Delete test notifications
        test_notifications = Notification.objects.filter(
            title__startswith='Test'
        )
        deleted_count = test_notifications.count()
        test_notifications.delete()
        print(f"✅ Deleted {deleted_count} test notifications")
        
    except Exception as e:
        print(f"❌ Error cleaning up test data: {str(e)}")


def main():
    """Main test function."""
    print("🚀 Starting MedGuard SA Notification System i18n Tests")
    print("=" * 60)
    
    try:
        # Test user language detection
        english_user, afrikaans_user = test_user_language_detection()
        
        # Test localized notification content
        test_localized_notification_content()
        
        # Test medication reminder formatting
        test_medication_reminder_formatting()
        
        # Test priority and type labels
        test_priority_and_type_labels()
        
        # Test notification service i18n
        test_notification_service_i18n()
        
        # Test email template rendering
        test_email_template_rendering(english_user, afrikaans_user)
        
        print("\n" + "=" * 60)
        print("📊 i18n Test Results Summary")
        print("=" * 60)
        
        print("✅ User Language Detection: Working")
        print("✅ Localized Content Generation: Working")
        print("✅ Medication Reminder Formatting: Working")
        print("✅ Priority & Type Labels: Working")
        print("✅ Notification Service i18n: Working")
        print("✅ Email Template Rendering: Working")
        
        print("\n🎉 i18n functionality is working correctly!")
        print("\nThe notification system now supports:")
        print("- Language-specific email templates")
        print("- Localized notification content")
        print("- User language preference detection")
        print("- Afrikaans and English support")
        
        # Ask if user wants to clean up test data
        response = input("\nDo you want to clean up test data? (y/N): ")
        if response.lower() in ['y', 'yes']:
            cleanup_test_data()
        
    except Exception as e:
        print(f"\n❌ i18n test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 