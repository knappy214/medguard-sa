#!/usr/bin/env python3
"""
Very simple test to isolate the translation issue.
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

def simple_test():
    """Simple translation test."""
    
    print("🧪 Simple Translation Test")
    print("=" * 30)
    
    # Test 1: Basic activation
    print("\n1. Testing basic activation:")
    activate('af-ZA')
    print(f"   Active language: {get_language()}")
    
    # Test 2: Simple translation
    print("\n2. Testing simple translation:")
    result = _('Medications')
    print(f"   _('Medications') = '{result}'")
    
    # Test 3: Check if Django is using the right translation
    print("\n3. Checking Django translation system:")
    from django.utils.translation import translation
    print(f"   Translation object: {translation.get_language()}")
    
    # Test 4: Direct translation object
    print("\n4. Testing direct translation object:")
    t = translation.translation('django', localedir=str(project_dir / 'locale'), languages=['af-ZA'])
    direct_result = t.gettext('Medications')
    print(f"   Direct translation: '{direct_result}'")
    
    # Test 5: Check settings
    print("\n5. Checking settings:")
    print(f"   USE_I18N: {settings.USE_I18N}")
    print(f"   LOCALE_PATHS: {settings.LOCALE_PATHS}")
    print(f"   LANGUAGES: {settings.LANGUAGES}")

if __name__ == '__main__':
    simple_test() 