#!/usr/bin/env python3
"""
Comprehensive script to fix Django internationalization issues.
This script ensures that translations are properly compiled and Django can find them.
"""

import os
import sys
import shutil
from pathlib import Path
import polib

def fix_i18n():
    """Fix internationalization issues."""
    
    print("🔧 Fixing Django Internationalization")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    locale_dir = base_dir / 'locale'
    
    if not locale_dir.exists():
        print(f"❌ Locale directory not found: {locale_dir}")
        return
    
    # Step 1: Recompile all translations with polib
    print("\n📝 Step 1: Recompiling translations...")
    for lang_dir in locale_dir.iterdir():
        if not lang_dir.is_dir():
            continue
            
        lc_messages_dir = lang_dir / 'LC_MESSAGES'
        if not lc_messages_dir.exists():
            continue
            
        po_file = lc_messages_dir / 'django.po'
        mo_file = lc_messages_dir / 'django.mo'
        
        if po_file.exists():
            print(f"Compiling {po_file}...")
            try:
                # Load the .po file
                po = polib.pofile(str(po_file))
                
                # Save as .mo file
                po.save_as_mofile(str(mo_file))
                print(f"✅ Created {mo_file}")
                
                # Verify translations
                print(f"   Found {len(po)} translation entries")
                for entry in po[:3]:
                    if entry.msgstr:
                        print(f"     '{entry.msgid}' -> '{entry.msgstr}'")
                        
            except Exception as e:
                print(f"❌ Error compiling {po_file}: {e}")
    
    # Step 2: Create a test script to verify translations work
    print("\n🧪 Step 2: Creating verification script...")
    
    test_script = """
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
    print("\\n🇿🇦 Testing Afrikaans (af-ZA):")
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
    
    print("\\n✅ Translation test completed!")

if __name__ == '__main__':
    test_translations()
"""
    
    with open(base_dir / 'test_fixed_translations.py', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ Created test_fixed_translations.py")
    
    # Step 3: Create a Django management command for easy testing
    print("\n⚙️ Step 3: Creating Django management command...")
    
    # Ensure management directories exist
    management_dir = base_dir / 'medications' / 'management'
    commands_dir = management_dir / 'commands'
    
    management_dir.mkdir(exist_ok=True)
    commands_dir.mkdir(exist_ok=True)
    
    # Create __init__.py files
    (management_dir / '__init__.py').touch()
    (commands_dir / '__init__.py').touch()
    
    # Create the management command
    command_script = """from django.core.management.base import BaseCommand
from django.utils.translation import activate, gettext as _, get_language

class Command(BaseCommand):
    help = 'Test fixed internationalization functionality'

    def handle(self, *args, **options):
        self.stdout.write("🌍 Testing Fixed Internationalization")
        self.stdout.write("=" * 50)
        
        # Test Afrikaans
        self.stdout.write("\\n🇿🇦 Testing Afrikaans (af-ZA):")
        activate('af-ZA')
        self.stdout.write(f"Active language: {get_language()}")
        
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
            self.stdout.write(f"  '{test_string}' -> '{translated}'")
        
        self.stdout.write("\\n✅ Fixed translation test completed!")
"""
    
    with open(commands_dir / 'test_fixed_i18n.py', 'w', encoding='utf-8') as f:
        f.write(command_script)
    
    print("✅ Created test_fixed_i18n management command")
    
    # Step 4: Create a language switching view
    print("\n🌐 Step 4: Creating language switching view...")
    
    # Add to medications/views.py
    views_content = '''
# Language switching view
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.translation import activate

@csrf_exempt
def switch_language(request):
    """Switch language via AJAX."""
    if request.method == 'POST':
        language = request.POST.get('language')
        if language in ['en-ZA', 'af-ZA']:
            activate(language)
            request.session['django_language'] = language
            return JsonResponse({
                'success': True,
                'language': language,
                'message': f'Language switched to {language}'
            })
    return JsonResponse({'success': False, 'error': 'Invalid request'})
'''
    
    print("✅ Language switching view ready to add to views.py")
    
    # Step 5: Instructions
    print("\n📋 Step 5: Next Steps")
    print("=" * 30)
    print("1. Run: python test_fixed_translations.py")
    print("2. Run: python manage.py test_fixed_i18n")
    print("3. Start Django server: python manage.py runserver")
    print("4. Visit: http://localhost:8000/medications/test-i18n/")
    print("5. Test language switching in the web interface")
    
    print("\n🎉 Internationalization fix completed!")

if __name__ == '__main__':
    fix_i18n() 