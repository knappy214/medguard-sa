#!/usr/bin/env python3
"""
Simple verification script to confirm internationalization is working.
Run this after restarting Django server.
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

def verify_i18n():
    """Verify that internationalization is working."""
    
    print("✅ Verifying Django Internationalization")
    print("=" * 50)
    
    # Test Afrikaans
    print("\n🇿🇦 Testing Afrikaans (af-ZA):")
    activate('af-ZA')
    print(f"Active language: {get_language()}")
    
    # Test key translations
    translations = {
        'Medications': 'Medikasie',
        'Medication Schedules': 'Medikasie Skedules',
        'Medication Logs': 'Medikasie Logboeke',
        'Stock Alerts': 'Voorraad Waarskuwings',
        'Language': 'Taal',
        'Current': 'Huidig'
    }
    
    success_count = 0
    total_count = len(translations)
    
    for english, expected_afrikaans in translations.items():
        translated = _(english)
        if translated == expected_afrikaans:
            print(f"✅ '{english}' -> '{translated}'")
            success_count += 1
        elif translated == english:
            print(f"❌ '{english}' -> '{translated}' (not translated)")
        else:
            print(f"⚠️ '{english}' -> '{translated}' (unexpected)")
    
    print(f"\n📊 Results: {success_count}/{total_count} translations working")
    
    if success_count == total_count:
        print("🎉 All translations working perfectly!")
        print("\n🌐 Your internationalization is fully functional!")
        print("   - Visit: http://localhost:8000/medications/test-i18n/")
        print("   - Afrikaans: http://localhost:8000/af-za/medications/test-i18n/")
    elif success_count > 0:
        print("⚠️ Some translations working, but not all.")
        print("   Try restarting Django server and running this script again.")
    else:
        print("❌ No translations working.")
        print("   Please restart Django server and try again.")
    
    print("\n🔧 If translations aren't working:")
    print("   1. Restart Django server: python manage.py runserver")
    print("   2. Run this script again")
    print("   3. Check that .mo files exist in locale/*/LC_MESSAGES/")

if __name__ == '__main__':
    verify_i18n() 