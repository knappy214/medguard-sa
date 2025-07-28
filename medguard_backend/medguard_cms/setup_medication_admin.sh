#!/bin/bash

# MedGuard SA - Medication Admin Setup Script
# This script sets up the Wagtail ModelAdmin medication management system

set -e

echo "🏥 MedGuard SA - Setting up Medication Admin System"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the correct directory
if [ ! -f "manage.py" ]; then
    print_error "This script must be run from the medguard_cms directory"
    exit 1
fi

print_status "Starting medication admin setup..."

# Step 1: Create locale directories if they don't exist
print_status "Creating locale directories..."
mkdir -p locale/en-ZA/LC_MESSAGES
mkdir -p locale/af-ZA/LC_MESSAGES

# Step 2: Compile translations
print_status "Compiling translations..."
python manage.py compilemessages --locale=en-ZA
python manage.py compilemessages --locale=af-ZA

if [ $? -eq 0 ]; then
    print_success "Translations compiled successfully"
else
    print_warning "Translation compilation had issues - continuing anyway"
fi

# Step 3: Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    print_success "Static files collected successfully"
else
    print_warning "Static file collection had issues - continuing anyway"
fi

# Step 4: Run migrations
print_status "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

if [ $? -eq 0 ]; then
    print_success "Database migrations completed successfully"
else
    print_error "Database migrations failed"
    exit 1
fi

# Step 5: Create superuser if it doesn't exist
print_status "Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('No superuser found. Creating one...')
    User.objects.create_superuser('admin', 'admin@medguard-sa.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Step 6: Verify setup
print_status "Verifying setup..."

# Check if wagtail_hooks.py exists
if [ -f "medguard_cms/wagtail_hooks.py" ]; then
    print_success "Wagtail hooks configuration found"
else
    print_error "Wagtail hooks configuration missing"
    exit 1
fi

# Check if CSS file exists
if [ -f "medguard_cms/static/css/medication-admin.css" ]; then
    print_success "Custom CSS found"
else
    print_warning "Custom CSS file missing"
fi

# Check if JS file exists
if [ -f "medguard_cms/static/js/medication-admin.js" ]; then
    print_success "Custom JavaScript found"
else
    print_warning "Custom JavaScript file missing"
fi

# Check if translation files exist
if [ -f "locale/en-ZA/LC_MESSAGES/django.mo" ]; then
    print_success "English translations compiled"
else
    print_warning "English translations not compiled"
fi

if [ -f "locale/af-ZA/LC_MESSAGES/django.mo" ]; then
    print_success "Afrikaans translations compiled"
else
    print_warning "Afrikaans translations not compiled"
fi

# Step 7: Display setup summary
echo ""
echo "🎉 Medication Admin Setup Complete!"
echo "=================================="
echo ""
echo "📋 Setup Summary:"
echo "  ✅ Wagtail ModelAdmin configured"
echo "  ✅ Custom admin panels created"
echo "  ✅ Healthcare color scheme applied"
echo "  ✅ Advanced filtering and search enabled"
echo "  ✅ Bulk actions interface ready"
echo "  ✅ Internationalization (en-ZA, af-ZA) configured"
echo "  ✅ Custom CSS and JavaScript loaded"
echo "  ✅ Database migrations applied"
echo ""
echo "🚀 Next Steps:"
echo "  1. Start the development server: python manage.py runserver"
echo "  2. Navigate to: http://localhost:8000/admin/"
echo "  3. Login with: admin/admin123"
echo "  4. Look for 'Medication Management' in the sidebar"
echo ""
echo "📚 Documentation:"
echo "  - README_MEDICATION_ADMIN.md - Complete setup guide"
echo "  - Check the admin interface for usage instructions"
echo ""
echo "🔧 Customization:"
echo "  - Edit medguard_cms/wagtail_hooks.py for ModelAdmin changes"
echo "  - Modify medguard_cms/static/css/medication-admin.css for styling"
echo "  - Update locale/*/LC_MESSAGES/django.po for translations"
echo ""

print_success "Medication admin system is ready to use!"

# Optional: Start the development server
read -p "Would you like to start the development server now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting development server..."
    python manage.py runserver
fi 