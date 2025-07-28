#!/usr/bin/env python3
"""
PostgreSQL setup script for MedGuard SA (Windows)
This script creates a database user and configures the database for Wagtail CMS.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import secrets
import string
import getpass

def generate_secure_password(length=16):
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def test_postgres_connection():
    """Test different PostgreSQL connection methods."""
    connection_methods = [
        # Try without password first (trust authentication)
        {"host": "localhost", "port": "5432", "database": "postgres", "user": "postgres"},
        # Try with password prompt
        {"host": "localhost", "port": "5432", "database": "postgres", "user": "postgres", "password": ""},
    ]
    
    for i, config in enumerate(connection_methods):
        try:
            print(f"Trying connection method {i+1}...")
            conn = psycopg2.connect(**config)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Connection successful! PostgreSQL version: {version[0]}")
            cursor.close()
            conn.close()
            return True
        except psycopg2.OperationalError as e:
            print(f"   Connection failed: {e}")
            continue
        except Exception as e:
            print(f"   Unexpected error: {e}")
            continue
    
    return False

def create_database_user():
    """Create the database user and configure permissions."""
    
    print("\n🔐 PostgreSQL Authentication")
    print("=" * 40)
    print("Please provide your PostgreSQL superuser credentials.")
    print("If you're not sure, try leaving the password empty first.")
    
    # Try different authentication methods
    auth_methods = [
        {"password": ""},  # Try without password
        {"password": getpass.getpass("Enter PostgreSQL superuser (postgres) password: ")},  # With password
    ]
    
    for auth_config in auth_methods:
        try:
            print(f"\nTrying to connect with {'no password' if not auth_config['password'] else 'password'}...")
            
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                database="postgres",
                user="postgres",
                password=auth_config["password"]
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if medguard_sa database exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'medguard_sa';")
            if not cursor.fetchone():
                print("Creating database 'medguard_sa'...")
                cursor.execute("CREATE DATABASE medguard_sa;")
                print("✅ Database 'medguard_sa' created successfully!")
            else:
                print("✅ Database 'medguard_sa' already exists!")
            
            # Generate a secure password for the new user
            db_password = generate_secure_password()
            
            # Check if user already exists
            cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'medguard_user';")
            if cursor.fetchone():
                print("User 'medguard_user' already exists. Dropping and recreating...")
                cursor.execute("DROP USER medguard_user;")
            
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
            return True
            
        except psycopg2.Error as e:
            print(f"❌ Error with this authentication method: {e}")
            continue
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            continue
    
    return False

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
    print("🐘 MedGuard SA PostgreSQL Setup (Windows)")
    print("=" * 50)
    
    # Test basic PostgreSQL connectivity
    print("Testing PostgreSQL connectivity...")
    if not test_postgres_connection():
        print("\n❌ Cannot connect to PostgreSQL. Please ensure:")
        print("   1. PostgreSQL is installed and running")
        print("   2. You can connect as the 'postgres' user")
        print("   3. The PostgreSQL service is started")
        print("\nTroubleshooting:")
        print("   - Try running: net start postgresql-x64-16")
        print("   - Or: net start postgresql-x64-17")
        print("   - Check if you need to set a password for the postgres user")
        sys.exit(1)
    
    # Create the database user
    if not create_database_user():
        print("\n❌ Failed to create database user.")
        print("Please check your PostgreSQL configuration and try again.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Testing database connection...")
    test_connection()
    
    print("\n🎉 Setup complete! Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Navigate to CMS: cd medguard_cms")
    print("3. Run migrations: python manage.py migrate")
    print("4. Create superuser: python manage.py createsuperuser")
    print("5. Start the development server: python manage.py runserver") 