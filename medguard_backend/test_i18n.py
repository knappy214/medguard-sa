#!/usr/bin/env python
"""
Test script to verify Django internationalization configuration.
"""

import os
import sys
import django
from django.conf import settings
from django.utils.translation import gettext as _
from django.utils.translation import activate, get_language

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

def test_i18n_configuration():
    """Test the internationalization configuration."""
    print("=== Testing Django Internationalization Configuration ===\n")
    
    # Test 1: Check settings
    print("1. Checking Django settings:")
    print(f"   LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
    print(f"   USE_I18N: {settings.USE_I18N}")
    print(f"   USE_L10N: {settings.USE_L10N}")
    print(f"   LANGUAGES: {settings.LANGUAGES}")
    print(f"   LOCALE_PATHS: {settings.LOCALE_PATHS}")
    print()
    
    # Test 2: Check Wagtail settings
    print("2. Checking Wagtail settings:")
    print(f"   WAGTAIL_I18N_ENABLED: {getattr(settings, 'WAGTAIL_I18N_ENABLED', 'Not set')}")
    print(f"   WAGTAIL_CONTENT_LANGUAGES: {getattr(settings, 'WAGTAIL_CONTENT_LANGUAGES', 'Not set')}")
    print()
    
    # Test 3: Test translation functionality
    print("3. Testing translation functionality:")
    
    # Test English
    activate('en')
    current_lang = get_language()
    print(f"   Current language: {current_lang}")
    print(f"   Translated 'Medications': {_('Medications')}")
    
    # Test Afrikaans
    activate('af')
    current_lang = get_language()
    print(f"   Current language: {current_lang}")
    print(f"   Translated 'Medications': {_('Medications')}")
    
    # Reset to default
    activate('en')
    print()
    
    # Test 4: Check locale files
    print("4. Checking locale files:")
    for lang_code, lang_name in settings.LANGUAGES:
        locale_path = os.path.join(settings.LOCALE_PATHS[0], lang_code, 'LC_MESSAGES')
        po_file = os.path.join(locale_path, 'django.po')
        mo_file = os.path.join(locale_path, 'django.mo')
        
        print(f"   {lang_code} ({lang_name}):")
        print(f"     PO file exists: {os.path.exists(po_file)}")
        print(f"     MO file exists: {os.path.exists(mo_file)}")
    
    print()
    print("=== Test completed ===")

if __name__ == '__main__':
    test_i18n_configuration() 