# -*- coding: utf-8 -*-
"""
MedGuard SA - Maintenance Module Tests
=====================================

Unit tests for the Wagtail 7.0.2 healthcare maintenance module.

Author: MedGuard SA Development Team
License: Proprietary
"""

from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from maintenance import (
    HealthcareContentAuditor,
    MedicalLinkChecker,
    MedicationImageCleaner,
    HealthcareSearchIndexManager,
    PageTreeOptimizer,
    HealthcareBackupVerifier,
    HealthcareLogRotator,
    HealthcareCacheWarmer,
    SecurityUpdateChecker,
    HealthcareHealthChecker,
    MaintenanceTaskRunner
)


class HealthcareContentAuditorTests(TestCase):
    """Test healthcare content auditing functionality."""
    
    def setUp(self):
        self.auditor = HealthcareContentAuditor()
    
    def test_auditor_initialization(self):
        """Test that the auditor initializes correctly."""
        self.assertIsInstance(self.auditor.audit_results, dict)
        self.assertIsInstance(self.auditor.medical_terms, dict)
        self.assertIn('medications', self.auditor.medical_terms)
    
    @patch('maintenance.wagtail_maintenance.Page.objects')
    def test_audit_healthcare_content(self, mock_page_objects):
        """Test healthcare content audit process."""
        # Mock page objects
        mock_page_objects.filter.return_value.live.return_value = []
        
        result = self.auditor.audit_healthcare_content()
        
        # Verify result structure
        self.assertIn('timestamp', result)
        self.assertIn('total_pages_audited', result)
        self.assertIn('issues_found', result)
        self.assertIn('recommendations', result)


class MedicalLinkCheckerTests(TestCase):
    """Test medical link checking functionality."""
    
    def setUp(self):
        self.link_checker = MedicalLinkChecker()
    
    def test_trusted_domains_loaded(self):
        """Test that trusted medical domains are loaded."""
        self.assertIn('who.int', self.link_checker.trusted_domains)
        self.assertIn('sahpra.org.za', self.link_checker.trusted_domains)
        self.assertIn('health.gov.za', self.link_checker.trusted_domains)
    
    @patch('maintenance.wagtail_maintenance.Page.objects')
    def test_check_medical_links(self, mock_page_objects):
        """Test medical link checking process."""
        # Mock page objects
        mock_page_objects.filter.return_value.live.return_value = []
        
        result = self.link_checker.check_medical_links()
        
        # Verify result structure
        self.assertIn('timestamp', result)
        self.assertIn('total_links_checked', result)
        self.assertIn('broken_links', result)
        self.assertIn('untrusted_sources', result)


class MedicationImageCleanerTests(TestCase):
    """Test medication image cleanup functionality."""
    
    def setUp(self):
        self.image_cleaner = MedicationImageCleaner()
    
    def test_cleaner_initialization(self):
        """Test that the image cleaner initializes correctly."""
        self.assertIn('images_scanned', self.image_cleaner.cleanup_results)
        self.assertIn('images_removed', self.image_cleaner.cleanup_results)
    
    @patch('maintenance.wagtail_maintenance.Image.objects')
    @patch('maintenance.wagtail_maintenance.Collection.objects')
    def test_cleanup_medication_images_dry_run(self, mock_collection, mock_image):
        """Test image cleanup in dry run mode."""
        # Mock objects
        mock_collection.filter.return_value = []
        mock_image.count.return_value = 0
        
        result = self.image_cleaner.cleanup_medication_images(dry_run=True)
        
        # Verify result structure
        self.assertIn('images_scanned', result)
        self.assertIn('dry_run', result)
        self.assertTrue(result['dry_run'])


class HealthcareSearchIndexManagerTests(TestCase):
    """Test search index management functionality."""
    
    def setUp(self):
        self.index_manager = HealthcareSearchIndexManager()
    
    @patch('maintenance.wagtail_maintenance.IndexEntry.objects')
    def test_maintain_search_index(self, mock_index_entry):
        """Test search index maintenance."""
        # Mock index entry count
        mock_index_entry.count.return_value = 100
        
        result = self.index_manager.maintain_search_index()
        
        # Verify result structure
        self.assertIn('timestamp', result)
        self.assertIn('pages_indexed', result)
        self.assertIn('index_size_before', result)
        self.assertIn('optimization_time', result)


class MaintenanceTaskRunnerTests(TestCase):
    """Test comprehensive maintenance task runner."""
    
    def setUp(self):
        self.runner = MaintenanceTaskRunner()
    
    @patch('maintenance.wagtail_maintenance_extended.HealthcareContentAuditor')
    @patch('maintenance.wagtail_maintenance_extended.MedicalLinkChecker')
    def test_run_all_maintenance_dry_run(self, mock_link_checker, mock_auditor):
        """Test running all maintenance tasks in dry run mode."""
        # Mock component methods
        mock_auditor_instance = MagicMock()
        mock_auditor_instance.audit_healthcare_content.return_value = {
            'timestamp': timezone.now().isoformat(),
            'total_pages_audited': 0,
            'issues_found': 0,
            'critical_issues': 0,
            'warnings': 0,
            'recommendations': []
        }
        mock_auditor.return_value = mock_auditor_instance
        
        mock_link_checker_instance = MagicMock()
        mock_link_checker_instance.check_medical_links.return_value = {
            'timestamp': timezone.now().isoformat(),
            'total_links_checked': 0,
            'broken_links': 0,
            'untrusted_sources': 0,
            'recommendations': []
        }
        mock_link_checker.return_value = mock_link_checker_instance
        
        # Run maintenance
        result = self.runner.run_all_maintenance(dry_run=True)
        
        # Verify result structure
        self.assertIn('maintenance_run_id', result)
        self.assertIn('timestamp', result)
        self.assertIn('dry_run', result)
        self.assertIn('total_execution_time', result)
        self.assertIn('summary', result)
        self.assertIn('recommendations', result)
        self.assertTrue(result['dry_run'])


class HealthcareHealthCheckerTests(TestCase):
    """Test healthcare health checking functionality."""
    
    def setUp(self):
        self.health_checker = HealthcareHealthChecker()
    
    @patch('maintenance.wagtail_maintenance_extended.connection')
    @patch('maintenance.wagtail_maintenance_extended.cache')
    @patch('maintenance.wagtail_maintenance_extended.psutil')
    def test_perform_health_check(self, mock_psutil, mock_cache, mock_connection):
        """Test comprehensive health check."""
        # Mock database connection
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock cache
        mock_cache.set.return_value = True
        mock_cache.get.return_value = 'test_value'
        mock_cache.delete.return_value = True
        
        # Mock system resources
        mock_psutil.cpu_percent.return_value = 50.0
        mock_psutil.virtual_memory.return_value.percent = 60.0
        mock_psutil.disk_usage.return_value.free = 10 * 1024**3  # 10GB free
        
        result = self.health_checker.perform_health_check()
        
        # Verify result structure
        self.assertIn('overall_status', result)
        self.assertIn('checks_performed', result)
        self.assertIn('checks_passed', result)
        self.assertIn('detailed_results', result)
        self.assertIn('uptime_percentage', result)


class IntegrationTests(TestCase):
    """Integration tests for the maintenance module."""
    
    def test_all_components_importable(self):
        """Test that all maintenance components can be imported."""
        components = [
            HealthcareContentAuditor,
            MedicalLinkChecker,
            MedicationImageCleaner,
            HealthcareSearchIndexManager,
            PageTreeOptimizer,
            HealthcareBackupVerifier,
            HealthcareLogRotator,
            HealthcareCacheWarmer,
            SecurityUpdateChecker,
            HealthcareHealthChecker,
            MaintenanceTaskRunner
        ]
        
        for component in components:
            self.assertTrue(callable(component))
            instance = component()
            self.assertIsNotNone(instance)
    
    def test_maintenance_runner_component_mapping(self):
        """Test that maintenance runner can initialize all components."""
        runner = MaintenanceTaskRunner()
        
        # Test that runner can be initialized
        self.assertIsNotNone(runner)
        self.assertIsInstance(runner.task_results, dict)
