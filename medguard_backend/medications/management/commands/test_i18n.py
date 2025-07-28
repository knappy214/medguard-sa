from django.core.management.base import BaseCommand
from django.utils.translation import activate, gettext as _, get_language
from django.conf import settings


class Command(BaseCommand):
    help = 'Test Django internationalization functionality'

    def handle(self, *args, **options):
        self.stdout.write("🌍 Testing Django Internationalization")
        self.stdout.write("=" * 50)
        
        # Test English
        self.stdout.write("\n🇿🇦 Testing English (en-ZA):")
        activate('en-ZA')
        self.stdout.write(f"Active language: {get_language()}")
        self.stdout.write(f"Translated 'Medications': {_('Medications')}")
        self.stdout.write(f"Translated 'Language': {_('Language')}")
        self.stdout.write(f"Translated 'Current': {_('Current')}")
        
        # Test Afrikaans
        self.stdout.write("\n🇿🇦 Testing Afrikaans (af-ZA):")
        activate('af-ZA')
        self.stdout.write(f"Active language: {get_language()}")
        self.stdout.write(f"Translated 'Medications': {_('Medications')}")
        self.stdout.write(f"Translated 'Language': {_('Language')}")
        self.stdout.write(f"Translated 'Current': {_('Current')}")
        
        # Test with translation override
        self.stdout.write("\n🔧 Testing with translation override:")
        from django.utils.translation import override
        with override('af-ZA'):
            self.stdout.write(f"Active language: {get_language()}")
            self.stdout.write(f"Translated 'Medications': {_('Medications')}")
            self.stdout.write(f"Translated 'Language': {_('Language')}")
            self.stdout.write(f"Translated 'Current': {_('Current')}")
        
        # Test available languages
        self.stdout.write(f"\n📋 Available languages: {settings.LANGUAGES}")
        self.stdout.write(f"📁 Locale paths: {settings.LOCALE_PATHS}")
        self.stdout.write(f"🌐 USE_I18N: {settings.USE_I18N}")
        self.stdout.write(f"📅 USE_L10N: {settings.USE_L10N}")
        
        # Check if .mo files exist
        self.stdout.write("\n📂 Checking translation files:")
        for lang_code, lang_name in settings.LANGUAGES:
            import os
            mo_file = os.path.join(settings.BASE_DIR, 'locale', lang_code, 'LC_MESSAGES', 'django.mo')
            if os.path.exists(mo_file):
                self.stdout.write(f"✅ {lang_code}: {mo_file} exists")
            else:
                self.stdout.write(f"❌ {lang_code}: {mo_file} missing")
        
        # Test specific translations from the .po files
        self.stdout.write("\n🔍 Testing specific translations:")
        test_strings = [
            'Medications',
            'Medication Schedules', 
            'Medication Logs',
            'Stock Alerts',
            'Language',
            'Current'
        ]
        
        for lang_code, lang_name in settings.LANGUAGES:
            self.stdout.write(f"\n{lang_name} ({lang_code}):")
            activate(lang_code)
            for test_string in test_strings:
                translated = _(test_string)
                self.stdout.write(f"  '{test_string}' -> '{translated}'")
        
        self.stdout.write("\n🎉 Internationalization test completed!") 