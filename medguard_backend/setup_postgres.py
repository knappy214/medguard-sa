#!/usr/bin/env python3
"""
PostgreSQL setup script for MedGuard SA
This script creates a database user and configures the database for Wagtail CMS.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import secrets
import string

def generate_secure_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_database_user():
    """Create the database user and configure permissions."""
    
    # Connect to PostgreSQL as superuser (postgres)
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres",
            password=input("Enter PostgreSQL superuser (postgres) password: ")
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Generate a secure password for the new user
        db_password = generate_secure_password()
        
        # Create the user
        print("Creating database user 'medguard_user'...")
        cursor.execute(f"""
            CREATE USER medguard_user WITH PASSWORD '{db_password}';
        """)
        
        # Grant necessary permissions
        print("Granting permissions...")
        cursor.execute(f"""
            GRANT ALL PRIVILEGES ON DATABASE medguard_sa TO medguard_user;
        """)
        
        # Connect to the medguard_sa database to grant schema permissions
        cursor.execute("""
            GRANT ALL ON SCHEMA public TO medguard_user;
        """)
        
        cursor.execute("""
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medguard_user;
        """)
        
        cursor.execute("""
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO medguard_user;
        """)
        
        cursor.execute("""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO medguard_user;
        """)
        
        cursor.execute("""
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO medguard_user;
        """)
        
        print("✅ Database user created successfully!")
        print(f"Username: medguard_user")
        print(f"Password: {db_password}")
        print("\n⚠️  IMPORTANT: Save this password securely!")
        
        # Create .env file
        create_env_file(db_password)
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creating database user: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def create_env_file(db_password):
    """Create a .env file with the database configuration."""
    
    env_content = f"""# MedGuard SA Environment Configuration
# Database Configuration
DB_NAME=medguard_sa
DB_USER=medguard_user
DB_PASSWORD={db_password}
DB_HOST=localhost
DB_PORT=5432

# Django Configuration
SECRET_KEY={generate_secure_password(50)}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Wagtail Configuration
WAGTAILADMIN_BASE_URL=http://localhost:8000

# Security Note: Change SECRET_KEY in production!
"""
    
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Environment file created: {env_path}")
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")
        print("Please create the .env file manually with the following content:")
        print(env_content)

def test_connection():
    """Test the database connection with the new user."""
    try:
        # Load environment variables
        from dotenv import load_dotenv
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
        
        print("✅ Database connection test successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")

if __name__ == "__main__":
    print("🐘 MedGuard SA PostgreSQL Setup")
    print("=" * 40)
    
    # Check if PostgreSQL is running
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres"
        )
        conn.close()
    except psycopg2.OperationalError:
        print("❌ Cannot connect to PostgreSQL. Please ensure:")
        print("   1. PostgreSQL is installed and running")
        print("   2. You can connect as the 'postgres' user")
        print("   3. The 'medguard_sa' database exists")
        sys.exit(1)
    
    # Create the database user
    create_database_user()
    
    print("\n" + "=" * 40)
    print("Testing database connection...")
    test_connection()
    
    print("\n🎉 Setup complete! Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run migrations: python manage.py migrate")
    print("3. Create superuser: python manage.py createsuperuser")
    print("4. Start the development server: python manage.py runserver") 