#!/usr/bin/env python3
"""
Database connection test script for MedGuard SA
This script tests the PostgreSQL connection and Django configuration.
"""

import os
import sys
import django
from pathlib import Path

def test_postgresql_connection():
    """Test direct PostgreSQL connection."""
    try:
        import psycopg2
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'medguard_sa'),
            user=os.getenv('DB_USER', 'medguard_user'),
            password=os.getenv('DB_PASSWORD', '')
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ PostgreSQL connection successful!")
        print(f"   Database: {os.getenv('DB_NAME', 'medguard_sa')}")
        print(f"   User: {os.getenv('DB_USER', 'medguard_user')}")
        print(f"   Host: {os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}")
        print(f"   PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_django_connection():
    """Test Django database connection."""
    try:
        # Add the CMS project to Python path
        cms_path = Path(__file__).parent / 'medguard_cms'
        sys.path.insert(0, str(cms_path))
        
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_cms.settings.base')
        
        # Setup Django
        django.setup()
        
        # Import Django database components
        from django.db import connection
        from django.core.management import execute_from_command_line
        
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result[0] == 1:
            print("✅ Django database connection successful!")
            return True
        else:
            print("❌ Django database connection failed: unexpected result")
            return False
            
    except Exception as e:
        print(f"❌ Django database connection failed: {e}")
        return False

def check_environment():
    """Check if environment variables are properly set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please ensure your .env file is properly configured.")
        return False
    else:
        print("✅ All required environment variables are set.")
        return True

def main():
    """Main test function."""
    print("🔍 MedGuard SA Database Connection Test")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    if not env_ok:
        sys.exit(1)
    
    print()
    
    # Test PostgreSQL connection
    pg_ok = test_postgresql_connection()
    
    print()
    
    # Test Django connection
    django_ok = test_django_connection()
    
    print()
    print("=" * 50)
    
    if pg_ok and django_ok:
        print("🎉 All tests passed! Your database is properly configured.")
        print("\nNext steps:")
        print("1. Navigate to the CMS directory: cd medguard_cms")
        print("2. Run migrations: python manage.py migrate")
        print("3. Create superuser: python manage.py createsuperuser")
        print("4. Start the server: python manage.py runserver")
    else:
        print("❌ Some tests failed. Please check your configuration.")
        if not pg_ok:
            print("   - PostgreSQL connection issues")
        if not django_ok:
            print("   - Django configuration issues")
        sys.exit(1)

if __name__ == "__main__":
    main() 