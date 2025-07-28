#!/usr/bin/env python3
"""
Simple PostgreSQL setup for MedGuard SA
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

def main():
    print("🐘 MedGuard SA PostgreSQL Setup")
    print("=" * 40)
    
    # Get PostgreSQL superuser password
    print("Please enter your PostgreSQL superuser (postgres) password.")
    print("If you don't have a password set, try pressing Enter.")
    
    postgres_password = getpass.getpass("PostgreSQL password: ")
    
    try:
        # Connect to PostgreSQL
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="postgres",
            user="postgres",
            password=postgres_password
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
        
        # Generate password for new user
        db_password = generate_secure_password()
        
        # Check if user already exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = 'medguard_user';")
        if cursor.fetchone():
            print("User 'medguard_user' already exists. Dropping and recreating...")
            cursor.execute("DROP USER medguard_user;")
        
        # Create the user
        print("Creating database user 'medguard_user'...")
        cursor.execute(f"CREATE USER medguard_user WITH PASSWORD '{db_password}';")
        
        # Grant permissions
        print("Granting permissions...")
        cursor.execute("GRANT ALL PRIVILEGES ON DATABASE medguard_sa TO medguard_user;")
        
        print("✅ Database user created successfully!")
        print(f"Username: medguard_user")
        print(f"Password: {db_password}")
        print("\n⚠️  IMPORTANT: Save this password securely!")
        
        # Create .env file
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
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"✅ Environment file created: {env_path}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Setup complete! Next steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Navigate to CMS: cd medguard_cms")
        print("3. Run migrations: python manage.py migrate")
        print("4. Create superuser: python manage.py createsuperuser")
        print("5. Start the server: python manage.py runserver")
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection failed: {e}")
        print("\nPossible solutions:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify the password for the 'postgres' user")
        print("3. Try connecting manually: psql -U postgres -h localhost")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 