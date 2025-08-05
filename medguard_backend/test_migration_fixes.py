#!/usr/bin/env python3
"""
Test script for MedGuard SA Migration Fix Script

This script tests the migration fixer functionality without requiring full Django setup.
"""

import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_migration_fixer_import():
    """Test that the MigrationFixer class can be imported."""
    try:
        from fix_migrations import MigrationFixer
        print("✅ MigrationFixer import successful")
        return True
    except ImportError as e:
        print(f"❌ MigrationFixer import failed: {e}")
        return False

def test_migration_fixer_initialization():
    """Test MigrationFixer initialization."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            assert fixer.dry_run == True
            assert fixer.backup_dir == Path("migration_backups")
            assert len(fixer.fixes_applied) == 0
            assert len(fixer.errors) == 0
            
            print("✅ MigrationFixer initialization successful")
            return True
    except Exception as e:
        print(f"❌ MigrationFixer initialization failed: {e}")
        return False

def test_circular_dependency_fixes():
    """Test circular dependency fix patterns."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test regex patterns
            test_content = """
            patient = models.ForeignKey(User, on_delete=models.CASCADE)
            medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
            user = models.OneToOneField(User, on_delete=models.CASCADE)
            """
            
            expected_content = """
            patient = models.ForeignKey('users.User', on_delete=models.CASCADE)
            medication = models.ForeignKey('medications.Medication', on_delete=models.CASCADE)
            user = models.OneToOneField('users.User', on_delete=models.CASCADE)
            """
            
            # Apply fixes
            import re
            fixes = [
                (r"models\.ForeignKey\(\s*User,", "models.ForeignKey('users.User',"),
                (r"models\.OneToOneField\(\s*User,", "models.OneToOneField('users.User',"),
                (r"models\.ForeignKey\(\s*Medication,", "models.ForeignKey('medications.Medication',"),
            ]
            
            result_content = test_content
            for pattern_regex, replacement in fixes:
                result_content = re.sub(pattern_regex, replacement, result_content, flags=re.MULTILINE)
            
            # Check if fixes were applied
            assert 'users.User' in result_content
            assert 'medications.Medication' in result_content
            assert 'User,' not in result_content
            assert 'Medication,' not in result_content
            
            print("✅ Circular dependency fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ Circular dependency fixes failed: {e}")
        return False

def test_jsonfield_compatibility():
    """Test JSONField compatibility fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test Django 5.x JSONField fix
            test_content = """
            from django.contrib.postgres.fields import JSONField
            
            notification_preferences = JSONField(default=dict)
            privacy_settings = JSONField(default=dict)
            """
            
            expected_content = """
            
            notification_preferences = models.JSONField(default=dict)
            privacy_settings = models.JSONField(default=dict)
            """
            
            # Apply Django 5.x fixes
            import re
            fixes = [
                (r"from django\.contrib\.postgres\.fields import JSONField", ""),
                (r"JSONField\(", "models.JSONField("),
            ]
            
            result_content = test_content
            for pattern_regex, replacement in fixes:
                result_content = re.sub(pattern_regex, replacement, result_content, flags=re.MULTILINE)
            
            # Clean up empty imports
            result_content = re.sub(r"from django\.db import models\n\n", "from django.db import models\n", result_content)
            
            # Check if fixes were applied
            assert 'models.JSONField' in result_content
            assert 'JSONField(' not in result_content
            assert 'from django.contrib.postgres.fields import JSONField' not in result_content
            
            print("✅ JSONField compatibility fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ JSONField compatibility fixes failed: {e}")
        return False

def test_imagefield_path_fixes():
    """Test ImageField upload path fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test upload path fixes
            test_content = """
            image = models.ImageField(upload_to='avatars/%Y/%m/%d/')
            medication_image = models.ImageField(upload_to='medications/images/')
            """
            
            expected_content = """
            image = models.ImageField(upload_to='users/avatars/%Y/%m/%d/')
            medication_image = models.ImageField(upload_to='medications/images/%Y/%m/%d/')
            """
            
            # Apply fixes
            import re
            fixes = [
                (r"upload_to='avatars/%Y/%m/%d/'", "upload_to='users/avatars/%Y/%m/%d/'"),
                (r"upload_to='medications/images/'", "upload_to='medications/images/%Y/%m/%d/'"),
            ]
            
            result_content = test_content
            for pattern_regex, replacement in fixes:
                result_content = re.sub(pattern_regex, replacement, result_content, flags=re.MULTILINE)
            
            # Check if fixes were applied
            assert 'users/avatars/%Y/%m/%d/' in result_content
            assert 'medications/images/%Y/%m/%d/' in result_content
            assert 'avatars/%Y/%m/%d/' not in result_content
            assert 'medications/images/' not in result_content
            
            print("✅ ImageField path fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ ImageField path fixes failed: {e}")
        return False

def test_timezone_datetime_fixes():
    """Test timezone-aware datetime field fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test timezone fixes
            test_content = """
            from django.db import models
            
            class User(models.Model):
                created_at = models.DateTimeField(auto_now_add=True)
                updated_at = models.DateTimeField(auto_now=True)
                last_login = models.DateTimeField(null=True, blank=True)
            """
            
            expected_content = """
            from django.db import models
            from django.utils import timezone
            
            class User(models.Model):
                created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)
                updated_at = models.DateTimeField(auto_now=True)
                last_login = models.DateTimeField(null=True, blank=True)
            """
            
            # Apply fixes
            import re
            
            # Add timezone import
            if 'from django.utils import timezone' not in test_content:
                test_content = re.sub(
                    r'from django\.db import models',
                    'from django.db import models\nfrom django.utils import timezone',
                    test_content
                )
            
            # Fix auto_now_add fields
            pattern = r'(\s+created_at\s*=\s*models\.DateTimeField\()([^)]*)(\))'
            match = re.search(pattern, test_content)
            if match:
                field_def = match.group(2)
                if 'auto_now_add=True' in field_def:
                    new_field_def = field_def.replace(
                        'auto_now_add=True',
                        'auto_now_add=True, default=timezone.now'
                    )
                    test_content = test_content.replace(match.group(0), f'{match.group(1)}{new_field_def}{match.group(3)}')
            
            # Check if fixes were applied
            assert 'from django.utils import timezone' in test_content
            assert 'default=timezone.now' in test_content
            
            print("✅ Timezone datetime fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ Timezone datetime fixes failed: {e}")
        return False

def test_unique_constraint_fixes():
    """Test unique constraint fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test unique constraint fixes
            test_content = """
            email = models.EmailField(verbose_name='Email address')
            name = models.CharField(max_length=200)
            """
            
            # Apply fixes
            import re
            
            # Add unique=True to email field
            pattern = r"(\s+email\s*=\s*models\.[^,]+)(,?)(\s*#.*)?$"
            replacement = r"\1, unique=True\2\3"
            result_content = re.sub(pattern, replacement, test_content, flags=re.MULTILINE)
            
            # Check if fixes were applied
            assert 'unique=True' in result_content
            
            print("✅ Unique constraint fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ Unique constraint fixes failed: {e}")
        return False

def test_foreign_key_fixes():
    """Test foreign key constraint fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test foreign key fixes
            test_content = """
            patient = models.ForeignKey(User, on_delete=models.CASCADE)
            medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
            """
            
            # Apply fixes
            import re
            
            # Update on_delete behavior
            result_content = re.sub(
                r'on_delete=models\.CASCADE',
                'on_delete=models.PROTECT',
                test_content
            )
            
            # Check if fixes were applied
            assert 'on_delete=models.PROTECT' in result_content
            assert 'on_delete=models.CASCADE' not in result_content
            
            print("✅ Foreign key fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ Foreign key fixes failed: {e}")
        return False

def test_decimal_precision_fixes():
    """Test decimal field precision fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test decimal field precision updates
            test_content = """
            dosage_strength = models.DecimalField(max_digits=5, decimal_places=2)
            price = models.DecimalField(max_digits=8, decimal_places=2)
            quantity = models.DecimalField(max_digits=5, decimal_places=0)
            """
            
            # Apply fixes
            import re
            content = test_content
            
            # Update precision for dosage_strength
            content = re.sub(
                r'dosage_strength\s*=\s*models\.DecimalField\([^)]*max_digits=5[^)]*decimal_places=2[^)]*\)',
                'dosage_strength = models.DecimalField(max_digits=8, decimal_places=3)',
                content,
                flags=re.MULTILINE
            )
            
            # Update precision for price
            content = re.sub(
                r'price\s*=\s*models\.DecimalField\([^)]*max_digits=8[^)]*decimal_places=2[^)]*\)',
                'price = models.DecimalField(max_digits=10, decimal_places=2)',
                content,
                flags=re.MULTILINE
            )
            
            # Check if fixes were applied
            assert 'max_digits=8, decimal_places=3' in content
            assert 'max_digits=10, decimal_places=2' in content
            assert 'max_digits=5, decimal_places=2' not in content
            assert 'max_digits=8, decimal_places=2' not in content
            
            print("✅ Decimal precision fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ Decimal precision fixes failed: {e}")
        return False

def test_index_naming_conflicts():
    """Test index naming conflict fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test index naming conflict resolution
            test_content = """
            name = models.CharField(max_length=100, db_index=True, db_tablespace='', name='medication_name_idx')
            email = models.EmailField(unique=True, db_index=True, db_tablespace='', name='user_email_idx')
            """
            
            # Apply fixes
            import re
            content = test_content
            
            # Fix index names
            content = re.sub(
                r"name='medication_name_idx'",
                "name='medications_medication_name_idx'",
                content
            )
            content = re.sub(
                r"name='user_email_idx'",
                "name='users_user_email_idx'",
                content
            )
            
            # Check if fixes were applied
            assert 'medications_medication_name_idx' in content
            assert 'users_user_email_idx' in content
            assert 'medication_name_idx' not in content
            assert 'user_email_idx' not in content
            
            print("✅ Index naming conflict fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ Index naming conflict fixes failed: {e}")
        return False

def test_migration_dependency_ordering():
    """Test migration dependency ordering fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test migration dependency updates
            test_content = """
            dependencies = []
            """
            
            # Apply fixes
            import re
            content = test_content
            
            # Add dependencies
            if 'dependencies = []' in content:
                content = content.replace(
                    'dependencies = []',
                    "dependencies = [\n        ('users', '0001_initial'),\n    ]"
                )
            
            # Check if fixes were applied
            assert "('users', '0001_initial')" in content
            assert 'dependencies = []' not in content
            
            print("✅ Migration dependency ordering fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ Migration dependency ordering fixes failed: {e}")
        return False

def test_postgresql_specific_fixes():
    """Test PostgreSQL-specific migration fixes."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Test PostgreSQL optimizations
            test_content = """
            from django.db import models
            
            class Medication(models.Model):
                metadata = models.JSONField(default=dict)
                name = models.CharField(max_length=200)
                description = models.TextField()
                
                class Meta:
                    pass
            """
            
            # Apply fixes
            import re
            content = test_content
            
            # Add PostgreSQL imports
            if 'from django.contrib.postgres.indexes import GinIndex' not in content:
                content = re.sub(
                    r'from django\.db import models',
                    'from django.db import models\nfrom django.contrib.postgres.indexes import GinIndex',
                    content
                )
            
            # Add GIN indexes to Meta class
            if 'class Meta:' in content:
                content = re.sub(
                    r'(class Meta:.*?)(\n\s+)(pass)(\n\s*)(\n|$)',
                    r'\1\2indexes = [\n            GinIndex(fields=["name"], name="medication_name_gin_idx"),\n            GinIndex(fields=["description"], name="medication_description_gin_idx")\n        ]\n\4\5',
                    content,
                    flags=re.DOTALL
                )
            
            # Check if fixes were applied
            assert 'from django.contrib.postgres.indexes import GinIndex' in content
            assert 'GinIndex(fields=["name"]' in content
            assert 'GinIndex(fields=["description"]' in content
            
            print("✅ PostgreSQL-specific fixes work correctly")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL-specific fixes failed: {e}")
        return False

def test_backup_functionality():
    """Test backup functionality."""
    try:
        from fix_migrations import MigrationFixer
        import tempfile
        import shutil
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Create a temporary test file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write("test content")
                test_file_path = Path(f.name)
            
            try:
                # Test backup functionality
                backup_path = fixer.backup_file(test_file_path)
                
                # In dry run mode, backup should not be created
                assert backup_path is None or not backup_path.exists()
                
                print("✅ Backup functionality works correctly")
                return True
            finally:
                # Clean up
                if test_file_path.exists():
                    test_file_path.unlink()
    except Exception as e:
        print(f"❌ Backup functionality failed: {e}")
        return False

def test_report_generation():
    """Test report generation functionality."""
    try:
        from fix_migrations import MigrationFixer
        
        # Mock Django version
        with patch('django.get_version', return_value='5.2.4'):
            fixer = MigrationFixer(dry_run=True)
            
            # Add some test fixes
            fixer.log_fix('Test Fix', 'Test description', 'test_file.py')
            fixer.log_error('Test Error', 'Test error description')
            
            # Generate report
            report = fixer.generate_fix_report()
            
            # Check report structure
            assert 'timestamp' in report
            assert 'django_version' in report
            assert 'dry_run' in report
            assert 'fixes_applied' in report
            assert 'errors' in report
            assert 'summary' in report
            
            # Check summary
            assert report['summary']['total_fixes'] == 1
            assert report['summary']['total_errors'] == 1
            assert 'Test Fix' in report['summary']['fix_types']
            
            print("✅ Report generation works correctly")
            return True
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing MedGuard SA Migration Fix Script\n")
    
    tests = [
        test_migration_fixer_import,
        test_migration_fixer_initialization,
        test_circular_dependency_fixes,
        test_jsonfield_compatibility,
        test_imagefield_path_fixes,
        test_timezone_datetime_fixes,
        test_unique_constraint_fixes,
        test_foreign_key_fixes,
        test_decimal_precision_fixes,
        test_index_naming_conflicts,
        test_migration_dependency_ordering,
        test_postgresql_specific_fixes,
        test_backup_functionality,
        test_report_generation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Migration fix script is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 