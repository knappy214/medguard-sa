# -*- coding: utf-8 -*-
"""
MedGuard SA - Healthcare Maintenance Management Command
======================================================

Django management command to run comprehensive Wagtail 7.0.2 healthcare
maintenance tasks.

Usage:
    python manage.py run_healthcare_maintenance
    python manage.py run_healthcare_maintenance --dry-run
    python manage.py run_healthcare_maintenance --task content_audit
    python manage.py run_healthcare_maintenance --verbose

Author: MedGuard SA Development Team
License: Proprietary
"""

import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from maintenance import MaintenanceTaskRunner

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command for running healthcare maintenance tasks.
    """
    
    help = 'Run comprehensive Wagtail 7.0.2 healthcare maintenance tasks'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Perform a dry run without making actual changes'
        )
        
        parser.add_argument(
            '--task',
            type=str,
            choices=[
                'content_audit',
                'link_checker',
                'image_cleaner',
                'search_index',
                'page_tree',
                'backup_verifier',
                'log_rotator',
                'cache_warmer',
                'security_checker',
                'health_checker',
                'all'
            ],
            default='all',
            help='Specific maintenance task to run (default: all)'
        )
        
        parser.add_argument(
            '--output-format',
            type=str,
            choices=['text', 'json'],
            default='text',
            help='Output format for results (default: text)'
        )
        
        parser.add_argument(
            '--save-report',
            action='store_true',
            default=False,
            help='Save maintenance report to file'
        )
    
    def handle(self, *args, **options):
        """Handle the management command."""
        self.verbosity = options['verbosity']
        dry_run = options['dry_run']
        task = options['task']
        output_format = options['output_format']
        save_report = options['save_report']
        
        # Display startup message
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🏥 MedGuard SA Healthcare Maintenance System v1.0.0"
            )
        )
        self.stdout.write(
            self.style.WARNING(
                f"{'=' * 60}"
            )
        )
        self.stdout.write(f"Start Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"Mode: {'DRY RUN' if dry_run else 'LIVE RUN'}")
        self.stdout.write(f"Task: {task}")
        self.stdout.write("")
        
        try:
            # Initialize maintenance runner
            runner = MaintenanceTaskRunner()
            
            # Run maintenance tasks
            if task == 'all':
                results = runner.run_all_maintenance(dry_run=dry_run)
            else:
                results = self._run_single_task(runner, task, dry_run)
            
            # Display results
            self._display_results(results, output_format)
            
            # Save report if requested
            if save_report:
                self._save_report(results)
            
            # Display completion message
            self._display_completion(results, dry_run)
            
        except Exception as e:
            logger.error(f"Maintenance command failed: {e}")
            raise CommandError(f"Maintenance failed: {e}")
    
    def _run_single_task(self, runner, task_name, dry_run):
        """Run a single maintenance task."""
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
            HealthcareHealthChecker
        )
        
        # Map task names to components
        task_map = {
            'content_audit': HealthcareContentAuditor(),
            'link_checker': MedicalLinkChecker(),
            'image_cleaner': MedicationImageCleaner(),
            'search_index': HealthcareSearchIndexManager(),
            'page_tree': PageTreeOptimizer(),
            'backup_verifier': HealthcareBackupVerifier(),
            'log_rotator': HealthcareLogRotator(),
            'cache_warmer': HealthcareCacheWarmer(),
            'security_checker': SecurityUpdateChecker(),
            'health_checker': HealthcareHealthChecker(),
        }
        
        component = task_map.get(task_name)
        if not component:
            raise CommandError(f"Unknown task: {task_name}")
        
        # Run the specific task
        if task_name == 'content_audit':
            result = component.audit_healthcare_content()
        elif task_name == 'link_checker':
            result = component.check_medical_links()
        elif task_name == 'image_cleaner':
            result = component.cleanup_medication_images(dry_run=dry_run)
        elif task_name == 'search_index':
            result = component.maintain_search_index()
        elif task_name == 'page_tree':
            result = component.optimize_page_tree()
        elif task_name == 'backup_verifier':
            result = component.verify_healthcare_backups()
        elif task_name == 'log_rotator':
            result = component.rotate_healthcare_logs()
        elif task_name == 'cache_warmer':
            result = component.warm_healthcare_cache()
        elif task_name == 'security_checker':
            result = component.check_security_updates()
        elif task_name == 'health_checker':
            result = component.perform_health_check()
        
        return {
            'maintenance_run_id': 'single_task',
            'timestamp': timezone.now().isoformat(),
            'dry_run': dry_run,
            'task_name': task_name,
            'result': result
        }
    
    def _display_results(self, results, output_format):
        """Display maintenance results."""
        if output_format == 'json':
            self.stdout.write(json.dumps(results, indent=2, default=str))
            return
        
        # Text format display
        self.stdout.write(self.style.SUCCESS("\n📊 MAINTENANCE RESULTS"))
        self.stdout.write("=" * 50)
        
        if 'task_name' in results:
            # Single task results
            self._display_single_task_results(results)
        else:
            # All tasks results
            self._display_all_tasks_results(results)
    
    def _display_single_task_results(self, results):
        """Display results for a single task."""
        task_name = results['task_name']
        result = results['result']
        
        self.stdout.write(f"\n🔧 Task: {task_name.replace('_', ' ').title()}")
        self.stdout.write("-" * 30)
        
        # Display key metrics
        for key, value in result.items():
            if key not in ['timestamp', 'detailed_results']:
                self.stdout.write(f"  {key.replace('_', ' ').title()}: {value}")
        
        # Display recommendations if available
        if 'recommendations' in result and result['recommendations']:
            self.stdout.write("\n💡 Recommendations:")
            for rec in result['recommendations']:
                self.stdout.write(f"  • {rec}")
    
    def _display_all_tasks_results(self, results):
        """Display results for all tasks."""
        # Summary
        summary = results.get('summary', {})
        self.stdout.write(f"\n📈 SUMMARY")
        self.stdout.write("-" * 20)
        self.stdout.write(f"  Tasks Completed: {results.get('tasks_completed', 0)}")
        self.stdout.write(f"  Tasks Failed: {results.get('tasks_failed', 0)}")
        self.stdout.write(f"  Execution Time: {results.get('total_execution_time', 0):.2f}s")
        self.stdout.write(f"  Critical Issues: {summary.get('critical_issues', 0)}")
        self.stdout.write(f"  Warnings: {summary.get('warnings', 0)}")
        self.stdout.write(f"  Space Freed: {summary.get('space_freed_mb', 0):.2f} MB")
        
        # Task breakdown
        self.stdout.write(f"\n🔧 TASK BREAKDOWN")
        self.stdout.write("-" * 25)
        
        detailed_results = results.get('detailed_results', {})
        for task_name, task_result in detailed_results.items():
            status = task_result['status']
            status_icon = "✅" if status == 'completed' else "❌"
            
            self.stdout.write(f"  {status_icon} {task_name.replace('_', ' ').title()}: {status}")
            
            if status == 'failed' and 'error' in task_result:
                self.stdout.write(f"    Error: {task_result['error']}")
        
        # Recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            self.stdout.write(f"\n💡 RECOMMENDATIONS")
            self.stdout.write("-" * 25)
            for rec in recommendations:
                priority = "🚨" if "URGENT" in rec else "📌"
                self.stdout.write(f"  {priority} {rec}")
    
    def _save_report(self, results):
        """Save maintenance report to file."""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"maintenance_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            self.stdout.write(
                self.style.SUCCESS(f"\n💾 Report saved to: {filename}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"\n❌ Failed to save report: {e}")
            )
    
    def _display_completion(self, results, dry_run):
        """Display completion message."""
        self.stdout.write(f"\n{'=' * 60}")
        
        if 'tasks_failed' in results and results['tasks_failed'] > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"⚠️  Maintenance completed with {results['tasks_failed']} failed tasks"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Maintenance completed successfully!")
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "📝 This was a dry run - no actual changes were made"
                )
            )
        
        self.stdout.write(f"End Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write("")
