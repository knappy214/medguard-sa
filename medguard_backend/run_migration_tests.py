#!/usr/bin/env python3
"""
Migration Test Runner for MedGuard SA

This script runs the comprehensive migration tests to verify:
1. All 21 medications can be created
2. ICD-10 code mappings work correctly
3. Complex medication schedules function properly
4. Stock calculations work for different medication types
5. Prescription workflow state persistence

Usage:
    python run_migration_tests.py

Author: MedGuard SA Development Team
Date: 2025-01-27
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
django.setup()

from test_migrations import MigrationComprehensiveTest


def main():
    """Run the comprehensive migration tests."""
    print("🏥 MedGuard SA - Comprehensive Migration Testing")
    print("=" * 60)
    print("Testing prescription system with 21 medications...")
    print()
    
    try:
        # Create test instance and run all tests
        test_suite = MigrationComprehensiveTest()
        test_suite.setUp()
        test_suite.run_all_tests()
        
        print("\n🎉 SUCCESS: All migration tests passed!")
        print("✅ MedGuard SA prescription system is production-ready")
        return 0
        
    except Exception as e:
        print(f"\n❌ FAILURE: Migration tests failed")
        print(f"Error: {str(e)}")
        print("\nPlease check the error details above and fix any issues.")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code) 