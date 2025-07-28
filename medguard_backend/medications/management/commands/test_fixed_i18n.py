from django.core.management.base import BaseCommand
from django.utils.translation import activate, gettext as _, get_language

class Command(BaseCommand):
    help = 'Test fixed internationalization functionality'

    def handle(self, *args, **options):
        self.stdout.write("🌍 Testing Fixed Internationalization")
        self.stdout.write("=" * 50)
        
        # Test Afrikaans
        self.stdout.write("\n🇿🇦 Testing Afrikaans (af-ZA):")
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
        
        self.stdout.write("\n✅ Fixed translation test completed!")
