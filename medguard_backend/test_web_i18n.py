#!/usr/bin/env python3
"""
Test internationalization in a web context using Django's test client.
This simulates how translations work in actual web requests.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.base')
django.setup()

from django.test import Client
from django.urls import reverse
from django.utils.translation import activate, get_language

def test_web_i18n():
    """Test internationalization in web context."""
    
    print("🌐 Testing Web-based Internationalization")
    print("=" * 50)
    
    client = Client()
    
    # Test the i18n test page
    print("\n📄 Testing i18n test page...")
    
    # Test with English
    print("\n🇿🇦 Testing English:")
    response = client.get('/medications/test-i18n/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Medications' in content:
            print("✅ Found 'Medications' in English response")
        if 'Medikasie' in content:
            print("✅ Found 'Medikasie' in English response (should not happen)")
        else:
            print("✅ No Afrikaans found in English response (correct)")
    
    # Test with Afrikaans
    print("\n🇿🇦 Testing Afrikaans:")
    response = client.get('/af-za/medications/test-i18n/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Medikasie' in content:
            print("✅ Found 'Medikasie' in Afrikaans response")
        if 'Medications' in content:
            print("⚠️ Found 'Medications' in Afrikaans response (might be untranslated)")
    
    # Test language switching
    print("\n🔄 Testing language switching...")
    
    # Set language in session
    session = client.session
    session['django_language'] = 'af-ZA'
    session.save()
    
    response = client.get('/medications/test-i18n/')
    print(f"Status after language switch: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'Medikasie' in content:
            print("✅ Language switching works - found 'Medikasie'")
        else:
            print("❌ Language switching not working")
    
    print("\n🎯 Web i18n test completed!")

if __name__ == '__main__':
    test_web_i18n() 