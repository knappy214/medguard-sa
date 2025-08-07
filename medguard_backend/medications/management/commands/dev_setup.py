"""
Development setup command for Wagtail 7.0.2 optimizations
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from wagtail.models import Page, Site
from medications.models import MedicationIndexPage
from home.models import HomePage

User = get_user_model()

class Command(BaseCommand):
    help = 'Set up development environment with Wagtail 7.0.2 optimizations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-data',
            action='store_true',
            help='Skip creating sample data',
        )

    def handle(self, *args, **options):
        self.stdout.write('🏥 Setting up MedGuard SA Development Environment...')
        
        # Run migrations
        self.stdout.write('📊 Running migrations...')
        call_command('migrate', verbosity=0)
        
        # Collect static files
        self.stdout.write('📁 Collecting static files...')
        call_command('collectstatic', verbosity=0, interactive=False)
        
        # Create superuser if doesn't exist
        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write('👤 Creating superuser...')
            User.objects.create_superuser(
                username='admin',
                email='admin@medguard-sa.com',
                password='admin123',
                first_name='Admin',
                last_name='User'
            )
        
        # Set up Wagtail pages if they don't exist
        if not options['skip_data']:
            self._setup_wagtail_pages()
        
        # Update search index
        self.stdout.write('🔍 Updating search index...')
        call_command('update_index', verbosity=0)
        
        self.stdout.write(
            self.style.SUCCESS('✅ Development environment setup complete!')
        )
        self.stdout.write('🌐 Run: python manage.py runserver --settings=medguard_backend.settings.development_wagtail_optimized')

    def _setup_wagtail_pages(self):
        """Set up basic Wagtail page structure"""
        self.stdout.write('📄 Setting up Wagtail pages...')
        
        # Get or create home page
        try:
            home_page = HomePage.objects.get(slug='home')
        except HomePage.DoesNotExist:
            root_page = Page.objects.get(id=1)
            home_page = HomePage(
                title="MedGuard SA",
                slug='home',
                intro="Your comprehensive medication management system"
            )
            root_page.add_child(instance=home_page)
        
        # Create medication index page if it doesn't exist
        if not MedicationIndexPage.objects.exists():
            medication_index = MedicationIndexPage(
                title="Medications",
                slug='medications',
                intro="Manage your medications with advanced features"
            )
            home_page.add_child(instance=medication_index)
        
        # Set up site if needed
        site, created = Site.objects.get_or_create(
            hostname='localhost',
            defaults={
                'port': 8000,
                'root_page': home_page,
                'is_default_site': True,
                'site_name': 'MedGuard SA Development'
            }
        )
