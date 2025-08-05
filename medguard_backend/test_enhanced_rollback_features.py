#!/usr/bin/env python
"""
Test script for Enhanced Rollback Features

This script tests the three new features added to the rollback_migrations.py module:
1. Data Integrity Verification
2. Notification Systems
3. Gradual Rollback for Zero-Downtime Scenarios
"""

import os
import sys
import unittest
import json
import tempfile
from unittest.mock import patch, MagicMock, call
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


class TestEnhancedRollbackFeatures(unittest.TestCase):
    """Test cases for Enhanced Rollback Features."""
    
    def setUp(self):
        """Set up test environment."""
        self.procedures = EmergencyRollbackProcedures()
        
        # Create test directories
        self.procedures.backup_dir.mkdir(exist_ok=True)
        self.procedures.data_export_dir.mkdir(exist_ok=True)
        self.procedures.rollback_dir.mkdir(exist_ok=True)
        
        # Create test export data
        self.test_export_data = {
            "medications": {
                "medications_prescription": {
                    "count": 150,
                    "data": []
                },
                "medications_medication": {
                    "count": 75,
                    "data": []
                }
            },
            "users": {
                "users_user": {
                    "count": 25,
                    "data": []
                }
            }
        }
    
    def tearDown(self):
        """Clean up test environment."""
        # Clean up test files
        for test_file in self.procedures.backup_dir.glob("test_*"):
            test_file.unlink(missing_ok=True)
        
        for test_file in self.procedures.data_export_dir.glob("test_*"):
            test_file.unlink(missing_ok=True)
        
        for test_file in self.procedures.rollback_dir.glob("test_*"):
            test_file.unlink(missing_ok=True)
    
    # ============================================================================
    # Data Integrity Verification Tests
    # ============================================================================
    
    def test_verify_data_integrity_basic(self):
        """Test basic data integrity verification."""
        with patch.object(self.procedures, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {
                'medications_prescription': 150,
                'medications_medication': 75,
                'users_user': 25
            }
            
            with patch.object(self.procedures, '_check_foreign_key_constraints') as mock_fk:
                mock_fk.return_value = []
                
                with patch.object(self.procedures, '_check_data_consistency') as mock_consistency:
                    mock_consistency.return_value = []
                    
                    with patch.object(self.procedures, '_check_business_rules') as mock_rules:
                        mock_rules.return_value = []
                        
                        result = self.procedures.verify_data_integrity()
                        
                        self.assertEqual(result['overall_status'], 'passed')
                        self.assertEqual(result['checks_passed'], 5)  # 5 checks passed
                        self.assertEqual(result['checks_failed'], 0)
                        self.assertIn('database_connection', result['details'])
                        self.assertIn('table_counts', result['details'])
    
    def test_verify_data_integrity_with_issues(self):
        """Test data integrity verification with issues."""
        with patch.object(self.procedures, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {
                'medications_prescription': 0,  # Empty critical table
                'medications_medication': 75,
                'users_user': 25
            }
            
            with patch.object(self.procedures, '_check_foreign_key_constraints') as mock_fk:
                mock_fk.return_value = [
                    {
                        'check': 'prescription_patient_orphans',
                        'orphaned_records': 5,
                        'severity': 'medium'
                    }
                ]
                
                with patch.object(self.procedures, '_check_data_consistency') as mock_consistency:
                    mock_consistency.return_value = []
                    
                    with patch.object(self.procedures, '_check_business_rules') as mock_rules:
                        mock_rules.return_value = []
                        
                        result = self.procedures.verify_data_integrity()
                        
                        self.assertEqual(result['overall_status'], 'failed')
                        self.assertGreater(result['checks_failed'], 0)
                        self.assertIn('empty_critical_tables', result['details'])
                        self.assertIn('foreign_key_issues', result['details'])
    
    def test_verify_data_integrity_with_export_comparison(self):
        """Test data integrity verification with export comparison."""
        # Create test export file
        export_file = self.procedures.data_export_dir / "test_export.json"
        with open(export_file, 'w') as f:
            json.dump(self.test_export_data, f)
        
        with patch.object(self.procedures, '_get_table_counts') as mock_counts:
            mock_counts.return_value = {
                'medications_prescription': 150,
                'medications_medication': 75,
                'users_user': 25
            }
            
            with patch.object(self.procedures, '_check_foreign_key_constraints') as mock_fk:
                mock_fk.return_value = []
                
                with patch.object(self.procedures, '_check_data_consistency') as mock_consistency:
                    mock_consistency.return_value = []
                    
                    with patch.object(self.procedures, '_check_business_rules') as mock_rules:
                        mock_rules.return_value = []
                        
                        result = self.procedures.verify_data_integrity(str(export_file))
                        
                        self.assertEqual(result['overall_status'], 'passed')
                        self.assertIn('data_comparison', result['details'])
                        
                        comparison = result['details']['data_comparison']
                        self.assertEqual(comparison['tables_compared'], 3)
                        self.assertEqual(comparison['tables_match'], 3)
                        self.assertFalse(comparison['significant_differences'])
        
        # Clean up
        export_file.unlink()
    
    def test_get_table_counts(self):
        """Test table count retrieval."""
        with patch('rollback_migrations.connection') as mock_connection:
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock table list
            mock_cursor.fetchall.side_effect = [
                [('medications_prescription',), ('medications_medication',), ('users_user',)],
                [(150,)],  # medications_prescription count
                [(75,)],   # medications_medication count
                [(25,)]    # users_user count
            ]
            
            counts = self.procedures._get_table_counts()
            
            self.assertEqual(counts['medications_prescription'], 150)
            self.assertEqual(counts['medications_medication'], 75)
            self.assertEqual(counts['users_user'], 25)
    
    def test_check_foreign_key_constraints(self):
        """Test foreign key constraint checking."""
        with patch('rollback_migrations.connection') as mock_connection:
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock FK check results
            mock_cursor.fetchone.side_effect = [(0,), (5,)]  # No orphans, then 5 orphans
            
            issues = self.procedures._check_foreign_key_constraints()
            
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]['check'], 'medication_prescription_orphans')
            self.assertEqual(issues[0]['orphaned_records'], 5)
    
    def test_check_data_consistency(self):
        """Test data consistency checking."""
        with patch('rollback_migrations.connection') as mock_connection:
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock consistency check results
            mock_cursor.fetchone.side_effect = [(3,), (0,)]  # 3 duplicates, 0 invalid dates
            
            issues = self.procedures._check_data_consistency()
            
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]['check'], 'duplicate_prescriptions')
            self.assertEqual(issues[0]['count'], 3)
    
    def test_check_business_rules(self):
        """Test business rule checking."""
        with patch('rollback_migrations.connection') as mock_connection:
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            
            # Mock business rule check results
            mock_cursor.fetchone.side_effect = [(2,), (0,)]  # 2 violations, 0 future dates
            
            issues = self.procedures._check_business_rules()
            
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0]['rule'], 'active_prescriptions_without_medications')
            self.assertEqual(issues[0]['violations'], 2)
    
    # ============================================================================
    # Notification System Tests
    # ============================================================================
    
    def test_send_notification_basic(self):
        """Test basic notification sending."""
        with patch.object(self.procedures, '_send_email_notification') as mock_email:
            mock_email.return_value = True
            
            with patch.object(self.procedures, '_send_slack_notification') as mock_slack:
                mock_slack.return_value = True
                
                success = self.procedures.send_notification(
                    'test_notification',
                    'Test message',
                    'info'
                )
                
                self.assertTrue(success)
                mock_email.assert_called_once()
                mock_slack.assert_called_once()
    
    def test_send_email_notification(self):
        """Test email notification sending."""
        with patch('rollback_migrations.send_mail') as mock_send_mail:
            mock_send_mail.return_value = 1
            
            with patch('rollback_migrations.settings') as mock_settings:
                mock_settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
                mock_settings.ADMIN_EMAILS = ['admin@test.com']
                mock_settings.DEFAULT_FROM_EMAIL = 'noreply@test.com'
                
                notification_data = {
                    'type': 'test_notification',
                    'message': 'Test message',
                    'severity': 'error',
                    'timestamp': '2024-01-01T12:00:00',
                    'system': 'MedGuard SA',
                    'environment': 'test'
                }
                
                success = self.procedures._send_email_notification(notification_data)
                
                self.assertTrue(success)
                mock_send_mail.assert_called_once()
                
                # Check email content
                call_args = mock_send_mail.call_args
                self.assertIn('[ERROR]', call_args[1]['subject'])
                self.assertIn('Test message', call_args[1]['message'])
                self.assertEqual(call_args[1]['recipient_list'], ['admin@test.com'])
    
    def test_send_slack_notification(self):
        """Test Slack notification sending."""
        with patch('rollback_migrations.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            with patch('rollback_migrations.settings') as mock_settings:
                mock_settings.SLACK_WEBHOOK_URL = 'https://hooks.slack.com/test'
                
                notification_data = {
                    'type': 'test_notification',
                    'message': 'Test message',
                    'severity': 'warning',
                    'timestamp': '2024-01-01T12:00:00',
                    'system': 'MedGuard SA',
                    'environment': 'test'
                }
                
                success = self.procedures._send_slack_notification(notification_data)
                
                self.assertTrue(success)
                mock_post.assert_called_once()
                
                # Check Slack message structure
                call_args = mock_post.call_args
                slack_message = call_args[1]['json']
                self.assertIn('attachments', slack_message)
                self.assertEqual(slack_message['attachments'][0]['title'], 'MedGuard SA - test_notification')
                self.assertEqual(slack_message['attachments'][0]['text'], 'Test message')
    
    def test_send_sms_notification(self):
        """Test SMS notification sending."""
        with patch('rollback_migrations.settings') as mock_settings:
            mock_settings.SMS_PROVIDER = 'test_provider'
            
            notification_data = {
                'type': 'critical_notification',
                'message': 'Critical message',
                'severity': 'critical',
                'timestamp': '2024-01-01T12:00:00',
                'system': 'MedGuard SA',
                'environment': 'test'
            }
            
            success = self.procedures._send_sms_notification(notification_data)
            
            self.assertTrue(success)
    
    # ============================================================================
    # Gradual Rollback Tests
    # ============================================================================
    
    def test_gradual_rollback_basic(self):
        """Test basic gradual rollback functionality."""
        with patch.object(self.procedures, 'create_backup') as mock_backup:
            mock_backup.return_value = "test_backup.sql"
            
            with patch.object(self.procedures, 'export_data') as mock_export:
                mock_export.return_value = "test_export.json"
                
                with patch.object(self.procedures, '_can_perform_gradual_rollback') as mock_can:
                    mock_can.return_value = True
                    
                    with patch.object(self.procedures, '_get_gradual_rollback_steps') as mock_steps:
                        mock_steps.return_value = [
                            {
                                'step': 1,
                                'description': 'Test step 1',
                                'type': 'preparation'
                            },
                            {
                                'step': 2,
                                'description': 'Test step 2',
                                'type': 'verification'
                            }
                        ]
                        
                        with patch.object(self.procedures, '_execute_gradual_rollback_step') as mock_execute:
                            mock_execute.return_value = True
                            
                            with patch.object(self.procedures, '_verify_gradual_rollback_step') as mock_verify:
                                mock_verify.return_value = True
                                
                                with patch.object(self.procedures, 'verify_migration_state') as mock_migration:
                                    mock_migration.return_value = True
                                    
                                    with patch.object(self.procedures, 'verify_data_integrity') as mock_integrity:
                                        mock_integrity.return_value = {'overall_status': 'passed'}
                                        
                                        success = self.procedures.gradual_rollback(
                                            'medications',
                                            '0017_merge_20250805_2014'
                                        )
                                        
                                        self.assertTrue(success)
                                        mock_backup.assert_called_once()
                                        mock_export.assert_called_once()
                                        self.assertEqual(mock_execute.call_count, 2)
    
    def test_gradual_rollback_step_failure(self):
        """Test gradual rollback with step failure."""
        with patch.object(self.procedures, 'create_backup') as mock_backup:
            mock_backup.return_value = "test_backup.sql"
            
            with patch.object(self.procedures, 'export_data') as mock_export:
                mock_export.return_value = "test_export.json"
                
                with patch.object(self.procedures, '_can_perform_gradual_rollback') as mock_can:
                    mock_can.return_value = True
                    
                    with patch.object(self.procedures, '_get_gradual_rollback_steps') as mock_steps:
                        mock_steps.return_value = [
                            {
                                'step': 1,
                                'description': 'Test step 1',
                                'type': 'preparation'
                            }
                        ]
                        
                        with patch.object(self.procedures, '_execute_gradual_rollback_step') as mock_execute:
                            mock_execute.return_value = False  # Step fails
                            
                            with patch.object(self.procedures, '_attempt_gradual_rollback_recovery') as mock_recovery:
                                mock_recovery.return_value = True
                                
                                success = self.procedures.gradual_rollback(
                                    'medications',
                                    '0017_merge_20250805_2014'
                                )
                                
                                self.assertTrue(success)  # Recovery succeeded
                                mock_recovery.assert_called_once()
    
    def test_can_perform_gradual_rollback(self):
        """Test gradual rollback possibility checking."""
        with patch('rollback_migrations.MigrationLoader') as mock_loader:
            mock_loader_instance = MagicMock()
            mock_loader.return_value = mock_loader_instance
            
            # Mock migration exists
            mock_loader_instance.graph.nodes = {
                ('medications', '0017_merge_20250805_2014'): MagicMock()
            }
            
            can_rollback = self.procedures._can_perform_gradual_rollback(
                'medications',
                '0017_merge_20250805_2014'
            )
            
            self.assertTrue(can_rollback)
    
    def test_get_gradual_rollback_steps(self):
        """Test gradual rollback steps generation."""
        with patch('rollback_migrations.MigrationLoader') as mock_loader:
            mock_loader_instance = MagicMock()
            mock_loader.return_value = mock_loader_instance
            
            # Mock current migration
            mock_loader_instance.applied_migrations = [
                ('medications', '0018_remove_prescription_secondary_diagnoses')
            ]
            
            steps = self.procedures._get_gradual_rollback_steps(
                'medications',
                '0017_merge_20250805_2014'
            )
            
            self.assertEqual(len(steps), 4)
            self.assertEqual(steps[0]['type'], 'preparation')
            self.assertEqual(steps[1]['type'], 'data_rollback')
            self.assertEqual(steps[2]['type'], 'schema_rollback')
            self.assertEqual(steps[3]['type'], 'verification')
    
    def test_execute_gradual_rollback_step(self):
        """Test gradual rollback step execution."""
        step = {
            'step': 1,
            'description': 'Test preparation step',
            'type': 'preparation'
        }
        
        with patch.object(self.procedures, '_execute_preparation_step') as mock_prep:
            mock_prep.return_value = True
            
            success = self.procedures._execute_gradual_rollback_step(step, 100, 5)
            
            self.assertTrue(success)
            mock_prep.assert_called_once_with(step)
    
    def test_execute_preparation_step(self):
        """Test preparation step execution."""
        step = {
            'description': 'Test preparation',
            'migration_from': 'medications.0018_remove_prescription_secondary_diagnoses'
        }
        
        with patch.object(self.procedures, 'check_dependencies') as mock_deps:
            mock_deps.return_value = {}
            
            with patch.object(self.procedures, 'create_backup') as mock_backup:
                mock_backup.return_value = "temp_backup.sql"
                
                success = self.procedures._execute_preparation_step(step)
                
                self.assertTrue(success)
                mock_deps.assert_called_once()
                mock_backup.assert_called_once()
    
    def test_execute_data_rollback_step(self):
        """Test data rollback step execution."""
        step = {
            'description': 'Test data rollback',
            'type': 'data_rollback'
        }
        
        success = self.procedures._execute_data_rollback_step(step, 50, 3)
        
        self.assertTrue(success)
    
    def test_execute_schema_rollback_step(self):
        """Test schema rollback step execution."""
        step = {
            'description': 'Test schema rollback',
            'migration_from': 'medications.0018_remove_prescription_secondary_diagnoses'
        }
        
        with patch.object(self.procedures, 'rollback_migration') as mock_rollback:
            mock_rollback.return_value = True
            
            success = self.procedures._execute_schema_rollback_step(step)
            
            self.assertTrue(success)
            mock_rollback.assert_called_once_with('medications', '0018_remove_prescription_secondary_diagnoses')
    
    def test_execute_verification_step(self):
        """Test verification step execution."""
        step = {
            'description': 'Test verification',
            'verification_checks': ['migration_state', 'data_integrity']
        }
        
        with patch.object(self.procedures, 'verify_migration_state') as mock_migration:
            mock_migration.return_value = True
            
            with patch.object(self.procedures, 'verify_data_integrity') as mock_integrity:
                mock_integrity.return_value = {'overall_status': 'passed'}
                
                success = self.procedures._execute_verification_step(step)
                
                self.assertTrue(success)
                mock_migration.assert_called_once()
                mock_integrity.assert_called_once()
    
    def test_verify_gradual_rollback_step(self):
        """Test gradual rollback step verification."""
        step = {
            'type': 'schema_rollback'
        }
        
        with patch.object(self.procedures, 'verify_migration_state') as mock_verify:
            mock_verify.return_value = True
            
            success = self.procedures._verify_gradual_rollback_step(step)
            
            self.assertTrue(success)
            mock_verify.assert_called_once()
    
    def test_attempt_gradual_rollback_recovery(self):
        """Test gradual rollback recovery."""
        with patch.object(self.procedures, 'send_notification') as mock_notify:
            mock_notify.return_value = True
            
            with patch.object(self.procedures, 'restore_backup') as mock_restore:
                mock_restore.return_value = True
                
                success = self.procedures._attempt_gradual_rollback_recovery(
                    "test_backup.sql",
                    "test_export.json"
                )
                
                self.assertTrue(success)
                self.assertEqual(mock_notify.call_count, 2)  # Recovery attempt + success
                mock_restore.assert_called_once_with("test_backup.sql")


def run_enhanced_tests():
    """Run the enhanced rollback features test suite."""
    print("Running Enhanced Rollback Features Tests...")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestEnhancedRollbackFeatures)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
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
    success = run_enhanced_tests()
    sys.exit(0 if success else 1) 