#!/bin/bash

# MedGuard SA Database Setup Script
echo "🐘 MedGuard SA PostgreSQL Setup"
echo "================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed or not in PATH"
    exit 1
fi

# Install required dependencies
echo "📦 Installing required dependencies..."
pip install psycopg2-binary python-dotenv

# Run the PostgreSQL setup script
echo "🔧 Running PostgreSQL setup..."
python3 setup_postgres.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Navigate to the CMS directory: cd medguard_cms"
echo "2. Install all dependencies: pip install -r ../requirements.txt"
echo "3. Run migrations: python manage.py migrate"
echo "4. Create superuser: python manage.py createsuperuser"
echo "5. Start the development server: python manage.py runserver"
echo ""
echo "The Wagtail admin will be available at: http://localhost:8000/admin" 