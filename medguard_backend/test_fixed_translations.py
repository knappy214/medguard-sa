
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
    print("🌍 Testing Fixed Translations")
    print("=" * 40)
    
    # Test Afrikaans
    print("\n🇿🇦 Testing Afrikaans (af-ZA):")
    activate('af-ZA')
    print(f"Active language: {get_language()}")
    
    test_strings = [
        'Medications',
        'Medication Schedules',
        'Medication Logs', 
        'Stock Alerts',
        'Language',
        'Current'
    ]
    
    for test_string in test_strings:
        translated = _(test_string)
        print(f"  '{test_string}' -> '{translated}'")
    
    print("\n✅ Translation test completed!")

if __name__ == '__main__':
    test_translations()
