"""
Enhanced development server startup script
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start development server with all optimizations"""
    
    print("🏥 Starting MedGuard SA Development Server...")
    print("🚀 Wagtail 7.0.2 Optimized Configuration")
    
    # Set environment variables
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development_wagtail_optimized')
    
    # Check if migrations are needed
    print("📊 Checking for migrations...")
    result = subprocess.run([
        sys.executable, 'manage.py', 'showmigrations', '--plan'
    ], capture_output=True, text=True)
    
    if '[ ]' in result.stdout:
        print("⚠️  Unapplied migrations found. Running migrations...")
        subprocess.run([sys.executable, 'manage.py', 'migrate'])
    
    # Update search index
    print("🔍 Updating search index...")
    subprocess.run([sys.executable, 'manage.py', 'update_index'])
    
    # Start development server
    print("🌐 Starting development server...")
    print("📱 Admin: http://localhost:8000/admin/")
    print("🏥 Wagtail Admin: http://localhost:8000/wagtail-admin/")
    print("📊 Debug Toolbar: Enabled")
    
    subprocess.run([
        sys.executable, 'manage.py', 'runserver', 
        '--settings=medguard_backend.settings.development_wagtail_optimized'
    ])

if __name__ == '__main__':
    main()
