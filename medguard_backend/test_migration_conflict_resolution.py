#!/usr/bin/env python
"""
Test script for Migration Conflict Resolution and Post-Rollback Data Reconciliation

This script tests the new features added to the emergency rollback procedures:
- Migration conflict resolution procedures
- Post-rollback data reconciliation processes

Usage:
    python test_migration_conflict_resolution.py
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import unittest

# Set Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')

# Import Django after setting environment
try:
    import django
    django.setup()
    from django.conf import settings
    from django.db import connection
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.recorder import MigrationRecorder
except ImportError as e:
    print(f"Failed to import Django: {e}")
    sys.exit(1)

# Import the rollback procedures
from rollback_migrations import EmergencyRollbackProcedures


class TestMigrationConflictResolution(unittest.TestCase):
    """Test migration conflict resolution procedures."""
    
    def setUp(self):
        """Set up test environment."""
        self.procedures = EmergencyRollbackProcedures()
        self.test_dir = Path(tempfile.mkdtemp())
        self.conflict_reports_dir = self.test_dir / "conflict_reports"
        self.conflict_reports_dir.mkdir(exist_ok=True)
        
        # Mock backup directory
        self.procedures.backup_dir = self.test_dir / "backups"
        self.procedures.backup_dir.mkdir(exist_ok=True)
        
        # Create test migration state
        self.test_migration_state = {
            'medications': [
                {'name': '0001_initial', 'status': 'applied', 'app': 'medications'},
                {'name': '0002_add_prescription', 'status': 'applied', 'app': 'medications'},
                {'name': '0003_missing_file', 'status': 'applied', 'app': 'medications'},  # Missing file
            ],
            'users': [
                {'name': '0001_initial', 'status': 'applied', 'app': 'users'},
                {'name': '0002_unapplied_file', 'status': 'unapplied', 'app': 'users'},  # Unapplied file
            ]
        }
        
        # Create test migration files
        self.create_test_migration_files()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_migration_files(self):
        """Create test migration files for testing."""
        # Create medications migrations directory
        medications_migrations = self.test_dir / "medications" / "migrations"
        medications_migrations.mkdir(parents=True, exist_ok=True)
        
        # Create existing migration files
        (medications_migrations / "0001_initial.py").write_text("# Test migration")
        (medications_migrations / "0002_add_prescription.py").write_text("# Test migration")
        (medications_migrations / "0004_unapplied_file.py").write_text("# Unapplied migration")
        
        # Create users migrations directory
        users_migrations = self.test_dir / "users" / "migrations"
        users_migrations.mkdir(parents=True, exist_ok=True)
        
        # Create existing migration files
        (users_migrations / "0001_initial.py").write_text("# Test migration")
        (users_migrations / "0003_unapplied_file.py").write_text("# Unapplied migration")
    
    @patch('rollback_migrations.settings.BASE_DIR')
    def test_migration_file_exists(self, mock_base_dir):
        """Test migration file existence check."""
        mock_base_dir.__truediv__ = lambda self, other: self.test_dir / other
        
        # Test existing file
        self.assertTrue(self.procedures._migration_file_exists('medications', '0001_initial'))
        
        # Test missing file
        self.assertFalse(self.procedures._migration_file_exists('medications', '0003_missing_file'))
    
    @patch('rollback_migrations.settings.BASE_DIR')
    def test_get_migration_files(self, mock_base_dir):
        """Test getting migration files for an app."""
        mock_base_dir.__truediv__ = lambda self, other: self.test_dir / other
        
        files = self.procedures._get_migration_files('medications')
        expected_files = ['0001_initial', '0002_add_prescription', '0004_unapplied_file']
        
        self.assertEqual(set(files), set(expected_files))
    
    @patch('rollback_migrations.settings.BASE_DIR')
    def test_detect_migration_conflicts(self, mock_base_dir):
        """Test migration conflict detection."""
        mock_base_dir.__truediv__ = lambda self, other: self.test_dir / other
        
        conflicts = self.procedures._detect_migration_conflicts('medications', self.test_migration_state['medications'])
        
        # Should detect missing file conflict
        missing_file_conflicts = [c for c in conflicts if c['type'] == 'missing_file']
        self.assertEqual(len(missing_file_conflicts), 1)
        self.assertEqual(missing_file_conflicts[0]['migration'], '0003_missing_file')
        
        # Should detect unapplied file conflict
        unapplied_file_conflicts = [c for c in conflicts if c['type'] == 'unapplied_file']
        self.assertEqual(len(unapplied_file_conflicts), 1)
        self.assertEqual(unapplied_file_conflicts[0]['migration'], '0004_unapplied_file')
    
    @patch('rollback_migrations.MigrationLoader')
    def test_check_dependency_conflicts(self, mock_loader_class):
        """Test dependency conflict checking."""
        # Mock the loader
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        
        # Mock the graph
        mock_graph = Mock()
        mock_loader.graph = mock_graph
        
        # Mock dependencies
        mock_graph.nodes = [('medications', '0002_add_prescription')]
        mock_graph.get_dependencies.return_value = [('users', '0001_initial')]
        
        conflicts = self.procedures._check_dependency_conflicts('medications', self.test_migration_state['medications'])
        
        # Should not find conflicts since dependency exists
        self.assertEqual(len(conflicts), 0)
    
    @patch('rollback_migrations.MigrationLoader')
    def test_check_circular_dependencies(self, mock_loader_class):
        """Test circular dependency checking."""
        # Mock the loader
        mock_loader = Mock()
        mock_loader_class.return_value = mock_loader
        
        # Mock the graph
        mock_graph = Mock()
        mock_loader.graph = mock_graph
        
        # Mock circular dependency detection
        mock_graph.ensure_not_cyclic.side_effect = Exception("Circular dependency detected")
        
        conflicts = self.procedures._check_circular_dependencies('medications', self.test_migration_state['medications'])
        
        # Should detect circular dependency
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]['type'], 'circular_dependency')
    
    def test_resolve_missing_file_conflict(self):
        """Test missing file conflict resolution."""
        conflict = {
            'type': 'missing_file',
            'app': 'medications',
            'migration': '0003_missing_file',
            'description': 'Migration 0003_missing_file is applied but file is missing'
        }
        
        with patch('rollback_migrations.MigrationRecorder') as mock_recorder_class:
            mock_recorder = Mock()
            mock_recorder_class.return_value = mock_recorder
            
            result = self.procedures._resolve_missing_file_conflict(conflict)
            
            self.assertTrue(result['resolved'])
            self.assertEqual(result['resolution_method'], 'remove_from_database')
            mock_recorder.record_unapplied.assert_called_once_with('medications', '0003_missing_file')
    
    def test_resolve_unapplied_file_conflict(self):
        """Test unapplied file conflict resolution."""
        conflict = {
            'type': 'unapplied_file',
            'app': 'medications',
            'migration': '0004_unapplied_file',
            'description': 'Migration file 0004_unapplied_file exists but is not applied'
        }
        
        with patch.object(self.procedures, '_apply_migration_file', return_value=True):
            result = self.procedures._resolve_unapplied_file_conflict(conflict)
            
            self.assertTrue(result['resolved'])
            self.assertEqual(result['resolution_method'], 'apply_migration')
    
    def test_resolve_circular_dependency_conflict(self):
        """Test circular dependency conflict resolution."""
        conflict = {
            'type': 'circular_dependency',
            'app': 'medications',
            'description': 'Circular dependency detected'
        }
        
        with patch.object(self.procedures, '_create_circular_dependency_report', return_value='test_report.md'):
            result = self.procedures._resolve_circular_dependency_conflict(conflict)
            
            self.assertTrue(result['resolved'])
            self.assertEqual(result['resolution_method'], 'manual_intervention_required')
    
    @patch.object(EmergencyRollbackProcedures, 'get_migration_state')
    def test_resolve_migration_conflicts(self, mock_get_migration_state):
        """Test complete migration conflict resolution."""
        mock_get_migration_state.return_value = self.test_migration_state
        
        with patch.object(self.procedures, '_detect_migration_conflicts') as mock_detect:
            mock_detect.return_value = [
                {
                    'type': 'missing_file',
                    'app': 'medications',
                    'migration': '0003_missing_file',
                    'description': 'Migration 0003_missing_file is applied but file is missing'
                }
            ]
            
            with patch.object(self.procedures, '_resolve_single_conflict') as mock_resolve:
                mock_resolve.return_value = {
                    'conflict': {},
                    'resolved': True,
                    'resolution_method': 'remove_from_database',
                    'error': None
                }
                
                result = self.procedures.resolve_migration_conflicts('medications')
                
                self.assertEqual(result['overall_status'], 'success')
                self.assertEqual(len(result['conflicts_found']), 1)
                self.assertEqual(len(result['conflicts_resolved']), 1)


class TestPostRollbackDataReconciliation(unittest.TestCase):
    """Test post-rollback data reconciliation procedures."""
    
    def setUp(self):
        """Set up test environment."""
        self.procedures = EmergencyRollbackProcedures()
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Mock directories
        self.procedures.backup_dir = self.test_dir / "backups"
        self.procedures.backup_dir.mkdir(exist_ok=True)
        
        # Create test backup file
        self.test_backup_path = self.test_dir / "backups" / "test_backup.sql"
        self.test_backup_path.write_text("-- Test backup content")
        
        # Create test export file
        self.test_export_path = self.test_dir / "test_export.json"
        test_export_data = {
            'medications': {
                'medication': {
                    'count': 10,
                    'data': [{'id': 1, 'name': 'Test Medication'}]
                }
            }
        }
        with open(self.test_export_path, 'w') as f:
            json.dump(test_export_data, f)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch.object(EmergencyRollbackProcedures, 'validate_backup')
    def test_reconcile_post_rollback_data_success(self, mock_validate_backup):
        """Test successful post-rollback data reconciliation."""
        mock_validate_backup.return_value = True
        
        with patch.object(self.procedures, '_compare_with_backup') as mock_compare:
            mock_compare.return_value = {
                'step': 'backup_comparison',
                'status': 'passed',
                'description': 'Comparison with backup data',
                'issues': []
            }
            
            with patch.object(self.procedures, '_reconcile_data_inconsistencies') as mock_reconcile:
                mock_reconcile.return_value = {
                    'step': 'data_reconciliation',
                    'status': 'passed',
                    'description': 'Reconciling data inconsistencies',
                    'resolved_issues': [],
                    'failed_issues': []
                }
                
                with patch.object(self.procedures, '_reconcile_foreign_keys') as mock_fk:
                    mock_fk.return_value = {
                        'step': 'foreign_key_reconciliation',
                        'status': 'passed',
                        'description': 'Reconciling foreign key relationships',
                        'issues': []
                    }
                    
                    with patch.object(self.procedures, 'verify_data_integrity') as mock_integrity:
                        mock_integrity.return_value = {
                            'overall_status': 'passed',
                            'checks_passed': 5,
                            'checks_failed': 0
                        }
                        
                        result = self.procedures.reconcile_post_rollback_data(
                            str(self.test_backup_path),
                            str(self.test_export_path)
                        )
                        
                        self.assertEqual(result['overall_status'], 'success')
                        self.assertEqual(len(result['reconciliation_steps']), 6)
    
    @patch.object(EmergencyRollbackProcedures, 'validate_backup')
    def test_reconcile_post_rollback_data_backup_failure(self, mock_validate_backup):
        """Test post-rollback data reconciliation with backup validation failure."""
        mock_validate_backup.return_value = False
        
        result = self.procedures.reconcile_post_rollback_data(str(self.test_backup_path))
        
        self.assertEqual(result['overall_status'], 'failed')
        self.assertEqual(len(result['data_issues_found']), 1)
        self.assertEqual(result['data_issues_found'][0]['type'], 'backup_integrity')
    
    def test_compare_with_backup_sql(self):
        """Test backup comparison with SQL backup."""
        with patch.object(self.procedures, '_create_temp_database', return_value=True):
            with patch.object(self.procedures, '_restore_to_temp_database', return_value=True):
                with patch.object(self.procedures, '_compare_databases', return_value=[]):
                    with patch.object(self.procedures, '_drop_temp_database', return_value=True):
                        result = self.procedures._compare_with_backup(str(self.test_backup_path))
                        
                        self.assertEqual(result['status'], 'passed')
                        self.assertEqual(len(result['issues']), 0)
    
    def test_compare_with_backup_compressed(self):
        """Test backup comparison with compressed backup."""
        # Create a test zip file
        import zipfile
        test_zip_path = self.test_dir / "test_backup.zip"
        with zipfile.ZipFile(test_zip_path, 'w') as zip_ref:
            zip_ref.writestr('test.txt', 'test content')
        
        with patch.object(self.procedures, '_compare_with_extracted_backup', return_value=[]):
            result = self.procedures._compare_with_backup(str(test_zip_path))
            
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(len(result['issues']), 0)
    
    def test_reconcile_data_inconsistencies(self):
        """Test data inconsistency reconciliation."""
        issues = [
            {
                'type': 'missing_table',
                'table': 'test_table',
                'description': 'Table test_table is missing'
            }
        ]
        
        with patch.object(self.procedures, '_resolve_single_data_issue') as mock_resolve:
            mock_resolve.return_value = {
                'issue': issues[0],
                'resolved': True,
                'resolution_method': 'manual_intervention_required',
                'error': None
            }
            
            result = self.procedures._reconcile_data_inconsistencies(issues)
            
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(len(result['resolved_issues']), 1)
            self.assertEqual(len(result['failed_issues']), 0)
    
    def test_resolve_missing_table_issue(self):
        """Test missing table issue resolution."""
        issue = {
            'type': 'missing_table',
            'table': 'test_table',
            'description': 'Table test_table is missing'
        }
        
        result = self.procedures._resolve_missing_table_issue(issue)
        
        self.assertTrue(result['resolved'])
        self.assertEqual(result['resolution_method'], 'manual_intervention_required')
    
    def test_resolve_count_mismatch_issue(self):
        """Test count mismatch issue resolution."""
        issue = {
            'type': 'count_mismatch',
            'table': 'test_table',
            'current_count': 10,
            'backup_count': 8,
            'description': 'Row count mismatch in table test_table'
        }
        
        result = self.procedures._resolve_count_mismatch_issue(issue)
        
        self.assertTrue(result['resolved'])
        self.assertEqual(result['resolution_method'], 'manual_investigation_required')
    
    def test_restore_missing_data_from_export(self):
        """Test restoring missing data from export."""
        result = self.procedures._restore_missing_data_from_export(str(self.test_export_path))
        
        self.assertEqual(result['status'], 'passed')
        self.assertEqual(len(result['issues']), 0)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios for the new features."""
    
    def setUp(self):
        """Set up test environment."""
        self.procedures = EmergencyRollbackProcedures()
        self.test_dir = Path(tempfile.mkdtemp())
        
        # Mock directories
        self.procedures.backup_dir = self.test_dir / "backups"
        self.procedures.backup_dir.mkdir(exist_ok=True)
        
        # Create test files
        self.test_backup_path = self.test_dir / "backups" / "test_backup.sql"
        self.test_backup_path.write_text("-- Test backup content")
        
        self.test_export_path = self.test_dir / "test_export.json"
        test_export_data = {'medications': {'medication': {'count': 10, 'data': []}}}
        with open(self.test_export_path, 'w') as f:
            json.dump(test_export_data, f)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    @patch.object(EmergencyRollbackProcedures, 'get_migration_state')
    @patch.object(EmergencyRollbackProcedures, 'validate_backup')
    def test_full_rollback_with_conflict_resolution_and_reconciliation(self, mock_validate_backup, mock_get_migration_state):
        """Test a complete rollback scenario with conflict resolution and data reconciliation."""
        # Mock migration state
        mock_get_migration_state.return_value = {
            'medications': [
                {'name': '0001_initial', 'status': 'applied', 'app': 'medications'},
                {'name': '0002_missing_file', 'status': 'applied', 'app': 'medications'},
            ]
        }
        mock_validate_backup.return_value = True
        
        # Mock conflict detection and resolution
        with patch.object(self.procedures, '_detect_migration_conflicts') as mock_detect:
            mock_detect.return_value = [
                {
                    'type': 'missing_file',
                    'app': 'medications',
                    'migration': '0002_missing_file',
                    'description': 'Migration 0002_missing_file is applied but file is missing'
                }
            ]
            
            with patch.object(self.procedures, '_resolve_single_conflict') as mock_resolve:
                mock_resolve.return_value = {
                    'conflict': {},
                    'resolved': True,
                    'resolution_method': 'remove_from_database',
                    'error': None
                }
                
                # Test conflict resolution
                conflict_result = self.procedures.resolve_migration_conflicts('medications')
                self.assertEqual(conflict_result['overall_status'], 'success')
                self.assertEqual(len(conflict_result['conflicts_resolved']), 1)
        
        # Mock data reconciliation
        with patch.object(self.procedures, '_compare_with_backup') as mock_compare:
            mock_compare.return_value = {
                'step': 'backup_comparison',
                'status': 'passed',
                'description': 'Comparison with backup data',
                'issues': []
            }
            
            with patch.object(self.procedures, '_reconcile_data_inconsistencies') as mock_reconcile:
                mock_reconcile.return_value = {
                    'step': 'data_reconciliation',
                    'status': 'passed',
                    'description': 'Reconciling data inconsistencies',
                    'resolved_issues': [],
                    'failed_issues': []
                }
                
                with patch.object(self.procedures, '_reconcile_foreign_keys') as mock_fk:
                    mock_fk.return_value = {
                        'step': 'foreign_key_reconciliation',
                        'status': 'passed',
                        'description': 'Reconciling foreign key relationships',
                        'issues': []
                    }
                    
                    with patch.object(self.procedures, 'verify_data_integrity') as mock_integrity:
                        mock_integrity.return_value = {
                            'overall_status': 'passed',
                            'checks_passed': 5,
                            'checks_failed': 0
                        }
                        
                        # Test data reconciliation
                        reconciliation_result = self.procedures.reconcile_post_rollback_data(
                            str(self.test_backup_path),
                            str(self.test_export_path)
                        )
                        
                        self.assertEqual(reconciliation_result['overall_status'], 'success')
                        self.assertEqual(len(reconciliation_result['reconciliation_steps']), 6)


def run_migration_conflict_tests():
    """Run all migration conflict resolution tests."""
    print("🧪 Running Migration Conflict Resolution Tests...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestMigrationConflictResolution))
    test_suite.addTest(unittest.makeSuite(TestPostRollbackDataReconciliation))
    test_suite.addTest(unittest.makeSuite(TestIntegrationScenarios))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    if result.wasSuccessful():
        print(f"\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ Some tests failed!")
        return False


if __name__ == '__main__':
    success = run_migration_conflict_tests()
    sys.exit(0 if success else 1) 