#!/usr/bin/env python3
"""
Test script to verify Django internationalization is working correctly.
Run this script to test if translations are being loaded properly.
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

from django.utils.translation import activate, gettext as _, get_language
from django.conf import settings

def test_translations():
    """Test if translations are working for both languages."""
    
    print("🌍 Testing Django Internationalization")
    print("=" * 50)
    
    # Test English
    print("\n🇿🇦 Testing English (en-ZA):")
    activate('en-ZA')
    print(f"Active language: {get_language()}")
    print(f"Translated 'Medications': {_('Medications')}")
    print(f"Translated 'Language': {_('Language')}")
    print(f"Translated 'Current': {_('Current')}")
    
    # Test Afrikaans
    print("\n🇿🇦 Testing Afrikaans (af-ZA):")
    activate('af-ZA')
    print(f"Active language: {get_language()}")
    print(f"Translated 'Medications': {_('Medications')}")
    print(f"Translated 'Language': {_('Language')}")
    print(f"Translated 'Current': {_('Current')}")
    
    # Test with translation override
    print("\n🔧 Testing with translation override:")
    from django.utils.translation import override
    with override('af-ZA'):
        print(f"Active language: {get_language()}")
        print(f"Translated 'Medications': {_('Medications')}")
        print(f"Translated 'Language': {_('Language')}")
        print(f"Translated 'Current': {_('Current')}")
    
    # Test available languages
    print(f"\n📋 Available languages: {settings.LANGUAGES}")
    print(f"📁 Locale paths: {settings.LOCALE_PATHS}")
    print(f"🌐 USE_I18N: {settings.USE_I18N}")
    print(f"📅 USE_L10N: {settings.USE_L10N}")
    
    # Check if .mo files exist
    print("\n📂 Checking translation files:")
    for lang_code, lang_name in settings.LANGUAGES:
        mo_file = project_dir / 'locale' / lang_code / 'LC_MESSAGES' / 'django.mo'
        if mo_file.exists():
            print(f"✅ {lang_code}: {mo_file} exists")
        else:
            print(f"❌ {lang_code}: {mo_file} missing")
    
    # Test specific translations from the .po files
    print("\n🔍 Testing specific translations:")
    test_strings = [
        'Medications',
        'Medication Schedules', 
        'Medication Logs',
        'Stock Alerts',
        'Language',
        'Current'
    ]
    
    for lang_code, lang_name in settings.LANGUAGES:
        print(f"\n{lang_name} ({lang_code}):")
        activate(lang_code)
        for test_string in test_strings:
            translated = _(test_string)
            print(f"  '{test_string}' -> '{translated}'")
    
    print("\n🎉 Internationalization test completed!")

if __name__ == '__main__':
    test_translations() 