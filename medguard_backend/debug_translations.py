#!/usr/bin/env python3
"""
Debug script to understand why Django translations aren't working.
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

from django.utils.translation import activate, gettext as _, get_language, check_for_language
from django.utils import translation
from django.conf import settings
import polib

def debug_translations():
    """Debug translation issues."""
    
    print("🔍 Debugging Django Translations")
    print("=" * 50)
    
    # Check settings
    print(f"USE_I18N: {settings.USE_I18N}")
    print(f"USE_L10N: {settings.USE_L10N}")
    print(f"LANGUAGE_CODE: {settings.LANGUAGE_CODE}")
    print(f"LANGUAGES: {settings.LANGUAGES}")
    print(f"LOCALE_PATHS: {settings.LOCALE_PATHS}")
    
    # Check if .mo files exist and are readable
    print("\n📂 Checking .mo files:")
    for lang_code, lang_name in settings.LANGUAGES:
        mo_file = project_dir / 'locale' / lang_code / 'LC_MESSAGES' / 'django.mo'
        if mo_file.exists():
            print(f"✅ {lang_code}: {mo_file} exists ({mo_file.stat().st_size} bytes)")
            
            # Try to read with polib
            try:
                mo = polib.mofile(str(mo_file))
                print(f"   Polib can read it: {len(mo)} entries")
                for entry in mo[:2]:
                    print(f"     '{entry.msgid}' -> '{entry.msgstr}'")
            except Exception as e:
                print(f"   Polib error: {e}")
        else:
            print(f"❌ {lang_code}: {mo_file} missing")
    
    # Test Django's translation system directly
    print("\n🌐 Testing Django translation system:")
    
    # Test Afrikaans
    print("\n🇿🇦 Testing Afrikaans:")
    activate('af-ZA')
    print(f"Active language: {get_language()}")
    
    # Test specific translations
    test_strings = ['Medications', 'Language', 'Current']
    for test_string in test_strings:
        django_translation = _(test_string)
        print(f"  '{test_string}' -> '{django_translation}'")
    
    # Check if Django is finding the translation files
    print("\n🔍 Checking Django's translation discovery:")
    print(f"check_for_language('af-ZA'): {check_for_language('af-ZA')}")
    
    # Test with translation override
    print("\n🧪 Translation override test:")
    with translation.override('af-ZA'):
        print(f"Active language: {get_language()}")
        print(f"'Medications' -> '{_('Medications')}'")
        print(f"'Language' -> '{_('Language')}'")
        print(f"'Current' -> '{_('Current')}'")
    
    # Test with direct activation
    print("\n🔧 Direct activation test:")
    activate('af-ZA')
    print(f"Active language: {get_language()}")
    print(f"'Medications' -> '{_('Medications')}'")
    
    # Test with a fresh Django setup
    print("\n🔄 Fresh Django setup test:")
    import django.utils.translation
    django.utils.translation.activate('af-ZA')
    print(f"Active language: {django.utils.translation.get_language()}")
    print(f"'Medications' -> '{django.utils.translation.gettext('Medications')}'")
    
    print("\n🎯 Debug completed!")

if __name__ == '__main__':
    debug_translations() 