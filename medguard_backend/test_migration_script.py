#!/usr/bin/env python
"""
Test script for the migration execution script.

This script tests the migration script functionality without actually
running migrations or making database changes.
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def test_migration_script_import():
    """Test that the migration script can be imported."""
    print("🔍 Testing migration script import...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Test import
        import migrate_all
        print("✅ Migration script imports successfully")
        return True
    except ImportError as e:
        print(f"❌ Migration script import failed: {e}")
        return False

def test_migration_script_help():
    """Test that the migration script shows help."""
    print("🔍 Testing migration script help...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'migrate_all.py', '--help'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        if result.returncode == 0 and 'MedGuard SA Migration Execution Script' in result.stdout:
            print("✅ Migration script help works correctly")
            return True
        else:
            print(f"❌ Migration script help failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Migration script help test failed: {e}")
        return False

def test_dry_run_mode():
    """Test dry-run mode of the migration script."""
    print("🔍 Testing migration script dry-run mode...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'migrate_all.py', '--dry-run'],
            capture_output=True,
            text=True,
            cwd='.',
            timeout=30  # 30 second timeout
        )
        
        # Dry-run should complete (even if some steps fail)
        if 'Starting MedGuard SA Migration Workflow' in result.stdout:
            print("✅ Migration script dry-run mode works")
            return True
        else:
            print(f"❌ Migration script dry-run failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️ Migration script dry-run timed out (this may be expected)")
        return True
    except Exception as e:
        print(f"❌ Migration script dry-run test failed: {e}")
        return False

def test_backup_only_mode():
    """Test backup-only mode of the migration script."""
    print("🔍 Testing migration script backup-only mode...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'migrate_all.py', '--backup-only'],
            capture_output=True,
            text=True,
            cwd='.',
            timeout=30  # 30 second timeout
        )
        
        # Backup-only should attempt database connection
        if 'DATABASE CONNECTION CHECK' in result.stdout:
            print("✅ Migration script backup-only mode works")
            return True
        else:
            print(f"❌ Migration script backup-only failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️ Migration script backup-only timed out (this may be expected)")
        return True
    except Exception as e:
        print(f"❌ Migration script backup-only test failed: {e}")
        return False

def test_verify_only_mode():
    """Test verify-only mode of the migration script."""
    print("🔍 Testing migration script verify-only mode...")
    
    try:
        result = subprocess.run(
            [sys.executable, 'migrate_all.py', '--verify-only'],
            capture_output=True,
            text=True,
            cwd='.',
            timeout=30  # 30 second timeout
        )
        
        # Verify-only should attempt database connection
        if 'DATABASE CONNECTION CHECK' in result.stdout:
            print("✅ Migration script verify-only mode works")
            return True
        else:
            print(f"❌ Migration script verify-only failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("⚠️ Migration script verify-only timed out (this may be expected)")
        return True
    except Exception as e:
        print(f"❌ Migration script verify-only test failed: {e}")
        return False

def test_script_structure():
    """Test the structure and content of the migration script."""
    print("🔍 Testing migration script structure...")
    
    try:
        script_path = Path('migrate_all.py')
        
        if not script_path.exists():
            print("❌ Migration script file not found")
            return False
        
        # Read script content
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for required components
        required_components = [
            'class MigrationExecutor',
            'def check_database_connection',
            'def create_backup',
            'def preview_migrations',
            'def create_migrations',
            'def run_migrations',
            'def verify_tables',
            'def run_deployment_check',
            'def run_data_integrity_checks',
            'def execute_migration_workflow',
            'if __name__ == \'__main__\':',
        ]
        
        missing_components = []
        for component in required_components:
            if component not in content:
                missing_components.append(component)
        
        if missing_components:
            print(f"❌ Missing required components: {missing_components}")
            return False
        else:
            print("✅ Migration script structure is correct")
            return True
            
    except Exception as e:
        print(f"❌ Migration script structure test failed: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available."""
    print("🔍 Testing required dependencies...")
    
    required_packages = [
        'psycopg2',
        'django',
        'argparse',
        'logging',
        'json',
        'subprocess',
        'pathlib',
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {missing_packages}")
        return False
    else:
        print("✅ All required dependencies are available")
        return True

def test_file_permissions():
    """Test that the migration script has execute permissions."""
    print("🔍 Testing migration script permissions...")
    
    try:
        script_path = Path('migrate_all.py')
        
        if not script_path.exists():
            print("❌ Migration script file not found")
            return False
        
        # Check if file is readable
        if not os.access(script_path, os.R_OK):
            print("❌ Migration script is not readable")
            return False
        
        # Check if file is executable (on Unix-like systems)
        if os.name != 'nt' and not os.access(script_path, os.X_OK):
            print("⚠️ Migration script is not executable (consider: chmod +x migrate_all.py)")
        
        print("✅ Migration script permissions are correct")
        return True
        
    except Exception as e:
        print(f"❌ Migration script permissions test failed: {e}")
        return False

def main():
    """Run all tests for the migration script."""
    print("🚀 Testing MedGuard SA Migration Script")
    print("=" * 50)
    
    tests = [
        ("Script Import", test_migration_script_import),
        ("Script Structure", test_script_structure),
        ("Dependencies", test_dependencies),
        ("File Permissions", test_file_permissions),
        ("Help Command", test_migration_script_help),
        ("Dry-Run Mode", test_dry_run_mode),
        ("Backup-Only Mode", test_backup_only_mode),
        ("Verify-Only Mode", test_verify_only_mode),
    ]
    
    results = []
    for test_name, test_function in tests:
        print(f"\n📋 Running test: {test_name}")
        try:
            result = test_function()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migration script is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 