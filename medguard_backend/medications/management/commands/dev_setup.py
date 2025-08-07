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
        home_page = HomePage.objects.first()
        if not home_page:
            # Check if there's already a page with slug 'medguard-home'
            root_page = Page.objects.get(id=1)
            if not Page.objects.filter(slug='medguard-home').exists():
                home_page = HomePage(
                    title="MedGuard SA Home",
                    slug='medguard-home',
                    hero_subtitle="Your comprehensive medication management system"
                )
                root_page.add_child(instance=home_page)
            else:
                self.stdout.write('⚠️  HomePage already exists with different slug')
                # Use the existing root page for medication index
                home_page = root_page
        
        # Create medication index page if it doesn't exist
        if not MedicationIndexPage.objects.exists() and home_page:
            medication_index = MedicationIndexPage(
                title="Medications",
                slug='medications-index',  # Use different slug to avoid conflicts
                intro="Manage your medications with advanced features"
            )
            home_page.add_child(instance=medication_index)
        
        # Set up site if needed (use the actual home page if it exists)
        if home_page and home_page.id != 1:  # Don't use root page as site root
            site, created = Site.objects.get_or_create(
                hostname='localhost',
                defaults={
                    'port': 8000,
                    'root_page': home_page,
                    'is_default_site': True,
                    'site_name': 'MedGuard SA Development'
                }
            )
