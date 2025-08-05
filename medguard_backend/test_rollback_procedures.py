#!/usr/bin/env python
"""
Test script for Emergency Rollback Procedures

This script tests the core functionality of the rollback_migrations.py module
to ensure it works correctly in the MedGuard SA environment.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

# Set Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')

# Import Django after setting environment
try:
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
except ImportError as e:
    print(f"Failed to import Django: {e}")
    sys.exit(1)

# Import the rollback procedures
try:
    from rollback_migrations import EmergencyRollbackProcedures
except ImportError as e:
    print(f"Failed to import rollback procedures: {e}")
    sys.exit(1)


class TestEmergencyRollbackProcedures(unittest.TestCase):
    """Test cases for Emergency Rollback Procedures."""
    
    def setUp(self):
        """Set up test environment."""
        self.procedures = EmergencyRollbackProcedures()
        
        # Create test directories
        self.procedures.backup_dir.mkdir(exist_ok=True)
        self.procedures.data_export_dir.mkdir(exist_ok=True)
        self.procedures.rollback_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up test files
        for test_file in self.procedures.backup_dir.glob("test_*"):
            test_file.unlink(missing_ok=True)
        
        for test_file in self.procedures.data_export_dir.glob("test_*"):
            test_file.unlink(missing_ok=True)
    
    def test_initialization(self):
        """Test EmergencyRollbackProcedures initialization."""
        self.assertIsNotNone(self.procedures)
        self.assertIsNotNone(self.procedures.backup_dir)
        self.assertIsNotNone(self.procedures.data_export_dir)
        self.assertIsNotNone(self.procedures.rollback_dir)
        self.assertIsNotNone(self.procedures.db_settings)
        self.assertIsNotNone(self.procedures.rollback_state)
    
    def test_run_command_success(self):
        """Test successful command execution."""
        returncode, stdout, stderr = self.procedures.run_command(['echo', 'test'])
        self.assertEqual(returncode, 0)
        self.assertIn('test', stdout)
        self.assertEqual(stderr, '')
    
    def test_run_command_failure(self):
        """Test failed command execution."""
        returncode, stdout, stderr = self.procedures.run_command(['nonexistent_command'])
        self.assertNotEqual(returncode, 0)
    
    def test_calculate_file_checksum(self):
        """Test file checksum calculation."""
        # Create a test file
        test_file = self.procedures.data_export_dir / "test_file.txt"
        test_content = "test content for checksum"
        
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        checksum = self.procedures._calculate_file_checksum(test_file)
        
        # Checksum should be a valid SHA256 hash
        self.assertIsInstance(checksum, str)
        self.assertEqual(len(checksum), 64)  # SHA256 hash length
        
        # Clean up
        test_file.unlink()
    
    def test_get_migration_state(self):
        """Test migration state retrieval."""
        migration_state = self.procedures.get_migration_state()
        
        self.assertIsInstance(migration_state, dict)
        self.assertIn('timestamp', migration_state)
        
        # Should have either applied_migrations or error
        self.assertTrue(
            'applied_migrations' in migration_state or 
            'error' in migration_state
        )
    
    def test_validate_backup_nonexistent(self):
        """Test backup validation with nonexistent file."""
        result = self.procedures.validate_backup("nonexistent_backup.sql")
        self.assertFalse(result)
    
    def test_validate_backup_empty(self):
        """Test backup validation with empty file."""
        # Create empty test file
        test_backup = self.procedures.backup_dir / "test_empty_backup.sql"
        test_backup.touch()
        
        result = self.procedures.validate_backup(str(test_backup))
        self.assertFalse(result)
        
        # Clean up
        test_backup.unlink()
    
    def test_validate_backup_valid(self):
        """Test backup validation with valid PostgreSQL backup."""
        # Create a mock valid PostgreSQL backup
        test_backup = self.procedures.backup_dir / "test_valid_backup.sql"
        
        with open(test_backup, 'wb') as f:
            f.write(b'PGDMP')  # PostgreSQL custom format signature
        
        result = self.procedures.validate_backup(str(test_backup))
        self.assertTrue(result)
        
        # Clean up
        test_backup.unlink()
    
    def test_list_migrations(self):
        """Test migration listing."""
        with patch.object(self.procedures, 'run_command') as mock_run:
            # Mock successful command execution
            mock_run.return_value = (0, """
[medications]
[X] 0001_initial
[X] 0002_add_prescription_fields
[ ] 0018_remove_prescription_secondary_diagnoses
""", "")
            
            migrations = self.procedures.list_migrations()
            
            self.assertIsInstance(migrations, dict)
            self.assertIn('medications', migrations)
            self.assertEqual(len(migrations['medications']), 3)
            
            # Check migration status
            applied_migrations = [m for m in migrations['medications'] if m['status'] == 'applied']
            unapplied_migrations = [m for m in migrations['medications'] if m['status'] == 'unapplied']
            
            self.assertEqual(len(applied_migrations), 2)
            self.assertEqual(len(unapplied_migrations), 1)
    
    def test_check_dependencies(self):
        """Test dependency checking."""
        with patch('rollback_migrations.MigrationLoader') as mock_loader:
            # Mock migration loader
            mock_loader_instance = MagicMock()
            mock_loader.return_value = mock_loader_instance
            
            # Mock migration node
            mock_node = MagicMock()
            mock_node.dependencies = {('medications', '0001_initial')}
            mock_node.dependents = {('medications', '0002_add_prescription_fields')}
            
            mock_loader_instance.graph.nodes = {
                ('medications', '0018_remove_prescription_secondary_diagnoses'): mock_node
            }
            mock_loader_instance.applied_migrations = {
                ('medications', '0018_remove_prescription_secondary_diagnoses')
            }
            
            deps = self.procedures.check_dependencies('medications', '0018_remove_prescription_secondary_diagnoses')
            
            self.assertIsInstance(deps, dict)
            self.assertEqual(deps['migration'], 'medications.0018_remove_prescription_secondary_diagnoses')
            self.assertTrue(deps['applied'])
            self.assertIn(('medications', '0001_initial'), deps['dependencies'])
            self.assertIn(('medications', '0002_add_prescription_fields'), deps['dependents'])
    
    def test_export_data_structure(self):
        """Test data export structure."""
        with patch('rollback_migrations.apps') as mock_apps:
            # Mock app configuration
            mock_app_config = MagicMock()
            mock_model = MagicMock()
            mock_model._meta.db_table = 'test_table'
            mock_model._meta.fields = []
            mock_model.objects.all.return_value = []
            
            mock_app_config.get_models.return_value = [mock_model]
            mock_apps.get_app_config.return_value = mock_app_config
            
            # Mock settings
            with patch('rollback_migrations.settings') as mock_settings:
                mock_settings.INSTALLED_APPS = ['medications']
                
                export_path = self.procedures.export_data('medications')
                
                if export_path:
                    # Check if export file exists
                    self.assertTrue(Path(export_path).exists())
                    
                    # Check if checksum file exists
                    checksum_path = Path(export_path).with_suffix('.checksum')
                    self.assertTrue(checksum_path.exists())
                    
                    # Clean up
                    Path(export_path).unlink()
                    checksum_path.unlink()
    
    def test_verify_migration_state(self):
        """Test migration state verification."""
        with patch.object(self.procedures, 'run_command') as mock_run:
            # Mock successful command executions
            mock_run.return_value = (0, "success", "")
            
            result = self.procedures.verify_migration_state()
            
            # Should call run_command multiple times
            self.assertGreater(mock_run.call_count, 0)
    
    def test_validate_schema(self):
        """Test schema validation."""
        with patch.object(self.procedures, 'run_command') as mock_run:
            # Mock successful command execution
            mock_run.return_value = (0, "success", "")
            
            result = self.procedures.validate_schema()
            
            # Should call run_command for Django checks
            mock_run.assert_called()
    
    def test_emergency_recovery_workflow(self):
        """Test emergency recovery workflow."""
        with patch.object(self.procedures, 'create_backup') as mock_backup, \
             patch.object(self.procedures, 'export_data') as mock_export, \
             patch.object(self.procedures, 'verify_migration_state') as mock_verify, \
             patch.object(self.procedures, 'validate_schema') as mock_schema, \
             patch.object(self.procedures, 'run_command') as mock_run:
            
            # Mock successful operations
            mock_backup.return_value = "test_backup.sql"
            mock_export.return_value = "test_export.json"
            mock_verify.return_value = True
            mock_schema.return_value = True
            mock_run.return_value = (0, "success", "")
            
            result = self.procedures.emergency_recovery()
            
            # Should call all recovery steps
            mock_backup.assert_called_once()
            mock_export.assert_called_once()
            mock_verify.assert_called()
            mock_schema.assert_called()
            mock_run.assert_called()
    
    def test_rollback_state_tracking(self):
        """Test rollback state tracking."""
        # Check initial state
        self.assertIsNone(self.procedures.rollback_state['started_at'])
        self.assertFalse(self.procedures.rollback_state['backup_created'])
        self.assertFalse(self.procedures.rollback_state['data_exported'])
        self.assertEqual(len(self.procedures.rollback_state['migrations_rolled_back']), 0)
        self.assertEqual(len(self.procedures.rollback_state['errors']), 0)
        
        # Simulate some operations
        self.procedures.rollback_state['backup_created'] = True
        self.procedures.rollback_state['data_exported'] = True
        self.procedures.rollback_state['migrations_rolled_back'].append('test_migration')
        self.procedures.rollback_state['errors'].append('test_error')
        
        # Check updated state
        self.assertTrue(self.procedures.rollback_state['backup_created'])
        self.assertTrue(self.procedures.rollback_state['data_exported'])
        self.assertEqual(len(self.procedures.rollback_state['migrations_rolled_back']), 1)
        self.assertEqual(len(self.procedures.rollback_state['errors']), 1)


def run_tests():
    """Run the test suite."""
    print("Running Emergency Rollback Procedures Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEmergencyRollbackProcedures)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1) 