#!/usr/bin/env python3
"""
Working i18n test that demonstrates the correct approach.
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
import polib

def working_test():
    """Working translation test."""
    
    print("✅ Working i18n Test")
    print("=" * 30)
    
    # Test 1: Check if .mo files are readable
    print("\n1. Checking .mo files:")
    af_mo_file = project_dir / 'locale' / 'af-ZA' / 'LC_MESSAGES' / 'django.mo'
    if af_mo_file.exists():
        print(f"   ✅ Afrikaans .mo file exists: {af_mo_file}")
        
        # Read with polib to verify content
        try:
            mo = polib.mofile(str(af_mo_file))
            print(f"   ✅ Polib can read it: {len(mo)} entries")
            
            # Find the Medications translation
            for entry in mo:
                if entry.msgid == 'Medications':
                    print(f"   ✅ Found 'Medications' -> '{entry.msgstr}'")
                    break
            else:
                print("   ❌ 'Medications' not found in .mo file")
        except Exception as e:
            print(f"   ❌ Polib error: {e}")
    else:
        print(f"   ❌ Afrikaans .mo file missing: {af_mo_file}")
    
    # Test 2: Test Django's translation system
    print("\n2. Testing Django translation system:")
    activate('af-ZA')
    print(f"   Active language: {get_language()}")
    
    # Test 3: Test with a simple string
    print("\n3. Testing simple translation:")
    test_string = 'Medications'
    result = _(test_string)
    print(f"   _('{test_string}') = '{result}'")
    
    # Test 4: Test with translation override
    print("\n4. Testing with translation override:")
    from django.utils import translation
    with translation.override('af-ZA'):
        result = _('Medications')
        print(f"   _('Medications') = '{result}'")
    
    # Test 5: Test direct translation object
    print("\n5. Testing direct translation object:")
    try:
        t = translation.translation('django', localedir=str(project_dir / 'locale'), languages=['af-ZA'])
        direct_result = t.gettext('Medications')
        print(f"   Direct translation: '{direct_result}'")
        
        if direct_result == 'Medikasie':
            print("   ✅ Direct translation works!")
        else:
            print("   ❌ Direct translation failed")
    except Exception as e:
        print(f"   ❌ Direct translation error: {e}")
    
    # Test 6: Check if the issue is with Django's translation loading
    print("\n6. Checking Django translation loading:")
    print(f"   USE_I18N: {settings.USE_I18N}")
    print(f"   LOCALE_PATHS: {settings.LOCALE_PATHS}")
    
    # Test 7: Try to force reload translations
    print("\n7. Testing translation reload:")
    from django.utils.translation import reload
    reload()
    activate('af-ZA')
    result = _('Medications')
    print(f"   After reload: _('Medications') = '{result}'")
    
    print("\n🎯 Test completed!")

if __name__ == '__main__':
    working_test() 