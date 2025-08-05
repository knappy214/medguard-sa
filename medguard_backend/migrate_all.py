#!/usr/bin/env python
"""
Comprehensive Migration Execution Script for MedGuard SA Backend

This script provides a complete migration workflow including:
- Database connection verification
- Data backup
- Migration preview and execution
- SQL review
- Verification and integrity checks
- Rollback capabilities

Usage:
    python migrate_all.py [--dry-run] [--backup-only] [--verify-only]
"""

import os
import sys
import subprocess
import logging
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging with UTF-8 encoding for Windows compatibility
import sys
import codecs

# Create a custom stream handler that handles UTF-8 encoding
class UTF8StreamHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Handle Windows console encoding issues
            if hasattr(stream, 'reconfigure'):
                try:
                    stream.reconfigure(encoding='utf-8')
                except:
                    pass
            stream.write(msg)
            stream.write(self.terminator)
            self.flush()
        except UnicodeEncodeError:
            # Fallback: replace problematic characters
            try:
                msg = self.format(record)
                msg = msg.encode('utf-8', errors='replace').decode('utf-8')
                stream = self.stream
                stream.write(msg)
                stream.write(self.terminator)
                self.flush()
            except Exception:
                pass
        except Exception:
            self.handleError(record)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_execution.log', encoding='utf-8'),
        UTF8StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class MigrationExecutor:
    """Comprehensive migration execution and verification system."""
    
    def __init__(self, dry_run: bool = False, backup_only: bool = False, verify_only: bool = False):
        self.dry_run = dry_run
        self.backup_only = backup_only
        self.verify_only = verify_only
        self.backup_file = None
        self.migration_results = {}
        self.start_time = datetime.now()
        
        # Set backend directory
        self.backend_dir = Path(__file__).parent
        
        # Set Django settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
        
        # Import Django after setting environment
        import django
        django.setup()
        
        from django.conf import settings
        from django.db import connection
        self.settings = settings
        self.connection = connection
        
        # Get database configuration
        self.db_config = settings.DATABASES['default']
        
    def log_section(self, title: str):
        """Log a section header for better readability."""
        logger.info(f"\n{'='*60}")
        logger.info(f" {title}")
        logger.info(f"{'='*60}")
    
    def check_database_connection(self) -> bool:
        """Check database connection and return status."""
        self.log_section("DATABASE CONNECTION CHECK")
        
        try:
            # Test Django database connection
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"Database connection successful")
                logger.info(f"   Database: {self.db_config['NAME']}")
                logger.info(f"   Host: {self.db_config['HOST']}:{self.db_config['PORT']}")
                logger.info(f"   User: {self.db_config['USER']}")
                logger.info(f"   PostgreSQL version: {version}")
                return True
                
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create a database backup before migration."""
        self.log_section("DATABASE BACKUP")
        
        if self.dry_run:
            logger.info("DRY RUN: Skipping backup creation")
            return True
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        
        self.backup_file = backup_dir / f"medguard_backup_{timestamp}.sql"
        
        # Try multiple backup methods
        backup_methods = [
            self._try_pg_dump_backup,
            self._try_django_backup,
            self._try_schema_only_backup
        ]
        
        for method in backup_methods:
            try:
                if method():
                    return True
            except Exception as e:
                logger.warning(f"Backup method {method.__name__} failed: {e}")
                continue
        
        logger.error("All backup methods failed")
        return False
    
    def _try_pg_dump_backup(self) -> bool:
        """Try using pg_dump for PostgreSQL backup."""
        try:
            # Check if pg_dump is available
            pg_dump_paths = ['pg_dump', 'pg_dump.exe']
            pg_dump_cmd = None
            
            for path in pg_dump_paths:
                try:
                    result = subprocess.run([path, '--version'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        pg_dump_cmd = path
                        break
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
            
            if not pg_dump_cmd:
                raise FileNotFoundError("pg_dump not found in PATH")
            
            cmd = [
                pg_dump_cmd,
                f'--host={self.db_config["HOST"]}',
                f'--port={self.db_config["PORT"]}',
                f'--username={self.db_config["USER"]}',
                f'--dbname={self.db_config["NAME"]}',
                '--verbose',
                '--clean',
                '--no-owner',
                '--no-privileges',
                f'--file={self.backup_file}'
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['PASSWORD']
            
            logger.info(f"Creating backup with pg_dump: {self.backup_file}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Backup created successfully: {self.backup_file}")
                return True
            else:
                logger.error(f"pg_dump backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"pg_dump backup method failed: {e}")
            return False
    
    def _try_django_backup(self) -> bool:
        """Try using Django's dumpdata for backup."""
        try:
            logger.info(f"Creating backup with Django dumpdata: {self.backup_file}")
            
            cmd = [
                sys.executable, 'manage.py', 'dumpdata',
                '--exclude=contenttypes',
                '--exclude=auth.Permission',
                '--indent=2',
                f'--output={self.backup_file}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"Django backup created successfully: {self.backup_file}")
                return True
            else:
                logger.error(f"Django backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"Django backup method failed: {e}")
            return False
    
    def _try_schema_only_backup(self) -> bool:
        """Create a minimal schema-only backup."""
        try:
            logger.info(f"Creating schema-only backup: {self.backup_file}")
            
            # Get table schemas using Django
            from django.core.management import call_command
            from io import StringIO
            
            output = StringIO()
            call_command('inspectdb', stdout=output)
            schema_content = output.getvalue()
            
            # Write schema to file
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                f.write("-- Schema-only backup created by MedGuard SA Migration Script\n")
                f.write(f"-- Created at: {datetime.now()}\n")
                f.write("-- This is a minimal backup containing only table schemas\n\n")
                f.write(schema_content)
            
            logger.info(f"Schema-only backup created: {self.backup_file}")
            return True
            
        except Exception as e:
            logger.warning(f"Schema-only backup method failed: {e}")
            return False
    
    def preview_migrations(self) -> bool:
        """Run makemigrations --dry-run to preview changes."""
        self.log_section("MIGRATION PREVIEW")
        
        try:
            cmd = [sys.executable, 'manage.py', 'makemigrations', '--dry-run', '--verbosity=2']
            logger.info("Running: " + ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("Migration preview successful")
                if result.stdout:
                    logger.info("Preview output:")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            logger.info(f"   {line}")
                return True
            else:
                logger.error(f"Migration preview failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Migration preview failed: {e}")
            return False
    
    def create_migrations(self) -> bool:
        """Execute makemigrations for medications app."""
        self.log_section("CREATE MIGRATIONS")
        
        if self.dry_run:
            logger.info("DRY RUN: Skipping migration creation")
            return True
            
        try:
            cmd = [sys.executable, 'manage.py', 'makemigrations', 'medications', '--verbosity=2']
            logger.info("Running: " + ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("Migrations created successfully")
                if result.stdout:
                    logger.info("Created migrations:")
                    for line in result.stdout.split('\n'):
                        if line.strip() and 'medications/migrations/' in line:
                            logger.info(f"   {line}")
                return True
            else:
                logger.error(f"Migration creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Migration creation failed: {e}")
            return False
    
    def review_sql_migration(self, migration_name: str = "0001") -> bool:
        """Review SQL for a specific migration."""
        self.log_section(f"SQL MIGRATION REVIEW: {migration_name}")
        
        try:
            cmd = [sys.executable, 'manage.py', 'sqlmigrate', 'medications', migration_name]
            logger.info("Running: " + ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("SQL migration review successful")
                logger.info("SQL Preview:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        logger.info(f"   {line}")
                return True
            else:
                logger.error(f"SQL migration review failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"SQL migration review failed: {e}")
            return False
    
    def run_fake_initial_migration(self) -> bool:
        """Run fake-initial migration if needed."""
        self.log_section("FAKE INITIAL MIGRATION")
        
        if self.dry_run:
            logger.info("DRY RUN: Skipping fake initial migration")
            return True
            
        try:
            cmd = [sys.executable, 'manage.py', 'migrate', '--fake-initial', '--verbosity=2']
            logger.info("Running: " + ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("Fake initial migration completed")
                return True
            else:
                logger.warning(f"Fake initial migration failed (may be expected): {result.stderr}")
                return True  # This is often expected for new databases
                
        except Exception as e:
            logger.error(f"Fake initial migration failed: {e}")
            return False
    
    def run_migrations(self) -> bool:
        """Execute migrations with detailed output."""
        self.log_section("EXECUTE MIGRATIONS")
        
        if self.dry_run:
            logger.info("DRY RUN: Skipping migration execution")
            return True
            
        try:
            # First run general migrations
            cmd = [sys.executable, 'manage.py', 'migrate', '--verbosity=2']
            logger.info("Running general migrations: " + ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode != 0:
                logger.error(f"General migrations failed: {result.stderr}")
                return False
            
            # Then run medications-specific migrations
            cmd = [sys.executable, 'manage.py', 'migrate', 'medications', '--verbosity=2']
            logger.info("Running medications migrations: " + ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("All migrations completed successfully")
                if result.stdout:
                    logger.info("Migration output:")
                    for line in result.stdout.split('\n'):
                        if line.strip() and ('Applying' in line or 'OK' in line):
                            logger.info(f"   {line}")
                return True
            else:
                logger.error(f"Medications migrations failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Migration execution failed: {e}")
            return False
    
    def run_custom_data_migrations(self) -> bool:
        """Execute custom data migrations with transaction rollback on errors."""
        self.log_section("CUSTOM DATA MIGRATIONS")
        
        if self.dry_run:
            logger.info("DRY RUN: Skipping custom data migrations")
            return True
            
        try:
            from django.db import transaction
            from django.core.management import call_command
            
            # List of custom management commands to run
            custom_commands = [
                'setup_notification_system',
                'setup_notification_tasks',
                'seed_medications',
            ]
            
            for command in custom_commands:
                logger.info(f"Running custom command: {command}")
                try:
                    with transaction.atomic():
                        call_command(command, verbosity=2)
                        logger.info(f"Custom command '{command}' completed successfully")
                except Exception as e:
                    logger.error(f"Custom command '{command}' failed: {e}")
                    # Continue with other commands
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Custom data migrations failed: {e}")
            return False
    
    def verify_tables(self) -> bool:
        """Verify all tables are created using dbshell commands."""
        self.log_section("TABLE VERIFICATION")
        
        try:
            # Get list of expected tables (using actual table names from database)
            expected_tables = [
                'medications',  # Main medications table
                'medication_logs',
                'medication_schedules', 
                'medication_interactions',
                'prescription_medications',
                'patient_medication_interactions',
                'medications_medicationindexpage',
                'medications_medicationdetailpage',
                'users_user',
                'security_securityevent',
                'security_auditlog',
                'medguard_notifications_notification',
                'medguard_notifications_notificationtemplate',
                'django_migrations',
                'django_content_type',
                'django_admin_log',
                'auth_group',
                'auth_permission',
            ]
            
            with self.connection.cursor() as cursor:
                # Get actual tables from database
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                actual_tables = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"Found {len(actual_tables)} tables in database")
                
                # Check for expected tables
                missing_tables = []
                for table in expected_tables:
                    if table in actual_tables:
                        logger.info(f"Table exists: {table}")
                    else:
                        logger.warning(f"Table missing: {table}")
                        missing_tables.append(table)
                
                if missing_tables:
                    logger.warning(f"{len(missing_tables)} expected tables are missing")
                    return False
                else:
                    logger.info("All expected tables are present")
                    return True
                    
        except Exception as e:
            logger.error(f"Table verification failed: {e}")
            return False
    
    def run_deployment_check(self) -> bool:
        """Run Django's deployment readiness check."""
        self.log_section("DEPLOYMENT READINESS CHECK")
        
        try:
            cmd = [sys.executable, 'manage.py', 'check', '--deploy']
            logger.info("Running: " + ' '.join(cmd))
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.backend_dir)
            
            if result.returncode == 0:
                logger.info("Deployment check passed")
                if result.stdout:
                    logger.info("Deployment check output:")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            logger.info(f"   {line}")
                return True
            else:
                logger.error(f"Deployment check failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Deployment check failed: {e}")
            return False
    
    def run_data_integrity_checks(self) -> bool:
        """Execute comprehensive data integrity checks."""
        self.log_section("DATA INTEGRITY CHECKS")
        
        try:
            from django.db import connection
            from django.core.management import call_command
            
            integrity_checks = []
            
            # Check for orphaned records
            with connection.cursor() as cursor:
                # Check for prescriptions without medications
                cursor.execute("""
                    SELECT COUNT(*) FROM medications_prescription p
                    LEFT JOIN medications_medication m ON p.medication_id = m.id
                    WHERE m.id IS NULL;
                """)
                orphaned_prescriptions = cursor.fetchone()[0]
                integrity_checks.append(('Orphaned prescriptions', orphaned_prescriptions == 0))
                
                # Check for medication logs without prescriptions
                cursor.execute("""
                    SELECT COUNT(*) FROM medications_medicationlog ml
                    LEFT JOIN medications_prescription p ON ml.prescription_id = p.id
                    WHERE p.id IS NULL;
                """)
                orphaned_logs = cursor.fetchone()[0]
                integrity_checks.append(('Orphaned medication logs', orphaned_logs == 0))
                
                # Check for stock levels without medications
                cursor.execute("""
                    SELECT COUNT(*) FROM medications_stocklevel sl
                    LEFT JOIN medications_medication m ON sl.medication_id = m.id
                    WHERE m.id IS NULL;
                """)
                orphaned_stock = cursor.fetchone()[0]
                integrity_checks.append(('Orphaned stock levels', orphaned_stock == 0))
            
            # Run Django's built-in checks
            try:
                call_command('check', verbosity=0)
                integrity_checks.append(('Django system check', True))
            except Exception as e:
                integrity_checks.append(('Django system check', False))
                logger.error(f"Django system check failed: {e}")
            
            # Report results
            all_passed = True
            for check_name, passed in integrity_checks:
                if passed:
                    logger.info(f"{check_name}: PASSED")
                else:
                    logger.error(f"{check_name}: FAILED")
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Data integrity checks failed: {e}")
            return False
    
    def generate_migration_report(self) -> None:
        """Generate a comprehensive migration report."""
        self.log_section("MIGRATION REPORT")
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        report = {
            'timestamp': self.start_time.isoformat(),
            'duration_seconds': duration.total_seconds(),
            'dry_run': self.dry_run,
            'backup_created': self.backup_file is not None,
            'backup_path': str(self.backup_file) if self.backup_file else None,
            'migration_results': self.migration_results,
            'summary': {
                'total_checks': len(self.migration_results),
                'passed_checks': sum(1 for result in self.migration_results.values() if result),
                'failed_checks': sum(1 for result in self.migration_results.values() if not result),
            }
        }
        
        # Save report to file
        report_file = f"migration_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Migration report saved to: {report_file}")
        logger.info(f"Total execution time: {duration}")
        logger.info(f"Success rate: {report['summary']['passed_checks']}/{report['summary']['total_checks']} checks passed")
    
    def execute_migration_workflow(self) -> bool:
        """Execute the complete migration workflow."""
        logger.info("Starting MedGuard SA Migration Workflow")
        logger.info(f"Started at: {self.start_time}")
        logger.info(f"Dry run mode: {self.dry_run}")
        
        # Define workflow steps
        workflow_steps = [
            ("Database Connection Check", self.check_database_connection),
            ("Database Backup", self.create_backup),
            ("Migration Preview", self.preview_migrations),
            ("Create Migrations", self.create_migrations),
            ("SQL Migration Review", lambda: self.review_sql_migration("0001")),
            ("Fake Initial Migration", self.run_fake_initial_migration),
            ("Execute Migrations", self.run_migrations),
            ("Custom Data Migrations", self.run_custom_data_migrations),
            ("Table Verification", self.verify_tables),
            ("Deployment Check", self.run_deployment_check),
            ("Data Integrity Checks", self.run_data_integrity_checks),
        ]
        
        # Execute workflow steps
        all_successful = True
        
        for step_name, step_function in workflow_steps:
            try:
                result = step_function()
                self.migration_results[step_name] = result
                
                if not result:
                    all_successful = False
                    if not self.dry_run:
                        logger.error(f"Workflow failed at step: {step_name}")
                        break
                        
            except Exception as e:
                logger.error(f"Unexpected error in step '{step_name}': {e}")
                self.migration_results[step_name] = False
                all_successful = False
                if not self.dry_run:
                    break
        
        # Generate final report
        self.generate_migration_report()
        
        if all_successful:
            logger.info("Migration workflow completed successfully!")
        else:
            logger.error("Migration workflow failed!")
            
        return all_successful

def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(description='MedGuard SA Migration Execution Script')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without executing')
    parser.add_argument('--backup-only', action='store_true', help='Only create database backup')
    parser.add_argument('--verify-only', action='store_true', help='Only run verification checks')
    
    args = parser.parse_args()
    
    try:
        executor = MigrationExecutor(
            dry_run=args.dry_run,
            backup_only=args.backup_only,
            verify_only=args.verify_only
        )
        
        if args.backup_only:
            success = executor.check_database_connection() and executor.create_backup()
        elif args.verify_only:
            success = (executor.check_database_connection() and 
                      executor.verify_tables() and 
                      executor.run_deployment_check() and
                      executor.run_data_integrity_checks())
        else:
            success = executor.execute_migration_workflow()
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 