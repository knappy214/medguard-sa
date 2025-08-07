#!/bin/bash

echo "🏥 MedGuard SA - Wagtail 7.0.2 Development Startup"
echo "=================================================="

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "💡 Recommendation: Activate your virtual environment first"
fi

# Install/update development requirements
echo "📦 Installing development dependencies..."
pip install -r requirements_dev.txt

# Check if migrations are needed and run them
echo "🔧 Checking for pending migrations..."
python manage.py showmigrations --plan | grep -q "\[ \]" && {
    echo "📊 Running pending migrations..."
    python manage.py migrate
}

# Set up development environment
echo "🔧 Setting up development environment..."
python /medguard_backend/medications/management/commands/dev_setup.py


# Start development server
echo "🚀 Starting development server with Wagtail 7.0.2 optimizations..."
python scripts/dev_start.py
