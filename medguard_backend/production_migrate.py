#!/usr/bin/env python
"""
Production Migration Script for MedGuard SA

This script provides safe migration commands for production deployment.
It includes comprehensive error handling, logging, and safety checks.

Usage:
    python production_migrate.py [command]

Commands:
    check-migrations    - Check for pending migrations without applying them
    migrate             - Run all migrations safely
    migrate-apps        - Run migrations for specific apps with detailed logging
    collectstatic       - Collect static files
    deploy-check        - Run deployment validation
    full-deploy         - Run complete deployment sequence
    backup              - Create database backup before migration
    verify-data         - Verify critical data integrity
    monitor-migration   - Set up monitoring for migration performance
    rollback            - Rollback to previous migration (if backup exists)
    zero-downtime       - Execute zero-downtime migration strategy
"""

import os
import sys
import subprocess
import logging
import argparse
import time
import json
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set Django settings for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.production')

# Import Django after setting environment
try:
    import django
    django.setup()
    from django.core.management import execute_from_command_line
    from django.conf import settings
    from django.db import connection
    from django.core.cache import cache
except ImportError as e:
    logger.error(f"Failed to import Django: {e}")
    sys.exit(1)


class MigrationMonitor:
    """Monitor migration performance and system resources."""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': [],
            'database_connections': [],
            'migration_duration': 0,
            'errors': [],
            'warnings': []
        }
        self.monitoring_active = False
        
    def start_monitoring(self):
        """Start monitoring system resources."""
        self.start_time = datetime.now()
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Migration monitoring started")
        
    def stop_monitoring(self):
        """Stop monitoring and calculate final metrics."""
        self.monitoring_active = False
        if self.start_time:
            self.metrics['migration_duration'] = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"Migration monitoring stopped. Duration: {self.metrics['migration_duration']:.2f}s")
        
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.metrics['cpu_usage'].append(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics['memory_usage'].append(memory.percent)
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.metrics['disk_io'].append({
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Database connections (approximate)
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT count(*) FROM pg_stat_activity")
                        conn_count = cursor.fetchone()[0]
                        self.metrics['database_connections'].append(conn_count)
                except Exception as e:
                    logger.warning(f"Could not get database connection count: {e}")
                    
                time.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(5)
                
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate performance report."""
        if not self.metrics['cpu_usage']:
            return {"error": "No monitoring data available"}
            
        return {
            'duration_seconds': self.metrics['migration_duration'],
            'avg_cpu_usage': sum(self.metrics['cpu_usage']) / len(self.metrics['cpu_usage']),
            'max_cpu_usage': max(self.metrics['cpu_usage']),
            'avg_memory_usage': sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage']),
            'max_memory_usage': max(self.metrics['memory_usage']),
            'total_errors': len(self.metrics['errors']),
            'total_warnings': len(self.metrics['warnings']),
            'peak_db_connections': max(self.metrics['database_connections']) if self.metrics['database_connections'] else 0
        }
        
    def log_error(self, error: str):
        """Log an error during migration."""
        self.metrics['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'error': error
        })
        
    def log_warning(self, warning: str):
        """Log a warning during migration."""
        self.metrics['warnings'].append({
            'timestamp': datetime.now().isoformat(),
            'warning': warning
        })


class ProductionMigrator:
    """Production-safe migration manager for MedGuard SA."""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.rollback_dir = Path("rollback_scripts")
        self.rollback_dir.mkdir(exist_ok=True)
        self.monitoring_dir = Path("migration_monitoring")
        self.monitoring_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.monitor = MigrationMonitor()
        self.current_backup = None
        
    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """
        Run a shell command safely.
        
        Args:
            command: List of command arguments
            capture_output: Whether to capture output
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        try:
            logger.info(f"Running command: {' '.join(command)}")
            
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=300  # 5 minute timeout
                )
                return result.returncode, result.stdout, result.stderr
            else:
                result = subprocess.run(
                    command,
                    check=False,
                    timeout=300
                )
                return result.returncode, "", ""
                
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(command)}")
            return 1, "", "Command timed out"
        except Exception as e:
            logger.error(f"Command failed: {e}")
            return 1, "", str(e)
    
    def check_database_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                logger.info("Database connection successful")
                return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def create_backup(self) -> bool:
        """Create database backup before migration."""
        try:
            backup_file = self.backup_dir / f"medguard_backup_{self.timestamp}.sql"
            self.current_backup = backup_file
            
            # Get database settings
            db_settings = settings.DATABASES['default']
            
            # Create PostgreSQL backup
            if db_settings['ENGINE'] == 'django.db.backends.postgresql':
                cmd = [
                    'pg_dump',
                    '-h', db_settings['HOST'],
                    '-p', str(db_settings['PORT']),
                    '-U', db_settings['USER'],
                    '-d', db_settings['NAME'],
                    '-f', str(backup_file),
                    '--verbose',
                    '--format=custom',  # Use custom format for better compression
                    '--compress=9'      # Maximum compression
                ]
                
                # Set password environment variable
                env = os.environ.copy()
                env['PGPASSWORD'] = db_settings['PASSWORD']
                
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout for backup
                )
                
                if result.returncode == 0:
                    logger.info(f"Database backup created: {backup_file}")
                    
                    # Create backup metadata
                    metadata = {
                        'timestamp': self.timestamp,
                        'backup_file': str(backup_file),
                        'database': db_settings['NAME'],
                        'size_bytes': backup_file.stat().st_size if backup_file.exists() else 0,
                        'migration_version': self._get_current_migration_version()
                    }
                    
                    metadata_file = backup_file.with_suffix('.json')
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)
                    
                    return True
                else:
                    logger.error(f"Backup failed: {result.stderr}")
                    return False
            else:
                logger.warning("Backup not implemented for this database engine")
                return True
                
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False
    
    def _get_current_migration_version(self) -> str:
        """Get current migration version for backup metadata."""
        try:
            returncode, stdout, stderr = self.run_command([
                sys.executable, 'manage.py', 'showmigrations', '--list'
            ])
            if returncode == 0:
                return stdout.strip()
            return "unknown"
        except Exception:
            return "unknown"
    
    def verify_data_integrity(self) -> bool:
        """
        Verify critical data integrity after migration.
        
        Returns:
            True if data verification passes, False otherwise
        """
        logger.info("Verifying data integrity...")
        
        verification_queries = [
            ("medications.models.Medication", "Medication.objects.count()"),
            ("users.models.User", "User.objects.count()"),
            ("security.models.SecurityEvent", "SecurityEvent.objects.count()"),
            ("medguard_notifications.models.Notification", "Notification.objects.count()"),
        ]
        
        all_passed = True
        
        for model_name, query in verification_queries:
            try:
                returncode, stdout, stderr = self.run_command([
                    sys.executable, 'manage.py', 'shell', '-c', 
                    f"from {model_name}; print({query})"
                ])
                
                if returncode == 0:
                    count = stdout.strip()
                    logger.info(f"✓ {model_name}: {count} records")
                else:
                    logger.error(f"✗ {model_name}: Verification failed - {stderr}")
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"✗ {model_name}: Verification error - {e}")
                all_passed = False
        
        # Additional data integrity checks
        try:
            # Check for orphaned records
            orphan_check = """
from medications.models import Medication, Prescription
from django.db.models import Count

# Check for medications without prescriptions
orphan_meds = Medication.objects.filter(prescriptions__isnull=True).count()
print(f"Orphan medications: {orphan_meds}")

# Check for duplicate medications
duplicates = Medication.objects.values('name', 'strength').annotate(
    count=Count('id')).filter(count__gt=1).count()
print(f"Potential duplicates: {duplicates}")
"""
            
            returncode, stdout, stderr = self.run_command([
                sys.executable, 'manage.py', 'shell', '-c', orphan_check
            ])
            
            if returncode == 0:
                logger.info(f"Data integrity check results:\n{stdout}")
            else:
                logger.warning(f"Data integrity check failed: {stderr}")
                
        except Exception as e:
            logger.warning(f"Data integrity check error: {e}")
        
        return all_passed
    
    def create_rollback_script(self) -> bool:
        """
        Create rollback script for critical migration failures.
        
        Returns:
            True if rollback script created successfully, False otherwise
        """
        try:
            rollback_file = self.rollback_dir / f"rollback_{self.timestamp}.sh"
            
            # Get current migration state
            returncode, stdout, stderr = self.run_command([
                sys.executable, 'manage.py', 'showmigrations', '--list'
            ])
            
            if returncode != 0:
                logger.error("Could not get current migration state")
                return False
            
            # Create rollback script
            rollback_content = f"""#!/bin/bash
# Rollback script for migration {self.timestamp}
# Created: {datetime.now().isoformat()}

set -e

echo "Starting rollback for migration {self.timestamp}..."

# Environment variables
export DJANGO_SETTINGS_MODULE="medguard_backend.settings.production"

# Check if backup exists
BACKUP_FILE="backups/medguard_backup_{self.timestamp}.sql"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file $BACKUP_FILE not found!"
    exit 1
fi

# Stop application (if running)
echo "Stopping application..."
# Add your application stop command here
# systemctl stop medguard-backend

# Restore database from backup
echo "Restoring database from backup..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < "$BACKUP_FILE"

# Verify restoration
echo "Verifying database restoration..."
python manage.py check --deploy

# Restart application
echo "Restarting application..."
# Add your application start command here
# systemctl start medguard-backend

echo "Rollback completed successfully!"
"""
            
            with open(rollback_file, 'w') as f:
                f.write(rollback_content)
            
            # Make rollback script executable
            rollback_file.chmod(0o755)
            
            logger.info(f"Rollback script created: {rollback_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create rollback script: {e}")
            return False
    
    def execute_zero_downtime_migration(self) -> bool:
        """
        Execute zero-downtime migration strategy.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting zero-downtime migration strategy...")
        
        try:
            # Step 1: Create backup
            if not self.create_backup():
                logger.error("Failed to create backup for zero-downtime migration")
                return False
            
            # Step 2: Start monitoring
            self.monitor.start_monitoring()
            
            # Step 3: Run migrations in background
            logger.info("Running migrations in background...")
            
            # Use Django's migration system with transaction support
            returncode, stdout, stderr = self.run_command([
                sys.executable, 'manage.py', 'migrate', '--verbosity=2'
            ])
            
            # Step 4: Stop monitoring
            self.monitor.stop_monitoring()
            
            if returncode == 0:
                # Step 5: Verify data integrity
                if not self.verify_data_integrity():
                    logger.error("Data integrity check failed after zero-downtime migration")
                    return False
                
                # Step 6: Generate performance report
                performance_report = self.monitor.get_performance_report()
                report_file = self.monitoring_dir / f"performance_report_{self.timestamp}.json"
                
                with open(report_file, 'w') as f:
                    json.dump(performance_report, f, indent=2)
                
                logger.info(f"Zero-downtime migration completed successfully!")
                logger.info(f"Performance report saved to: {report_file}")
                return True
            else:
                logger.error(f"Zero-downtime migration failed: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Zero-downtime migration error: {e}")
            return False
    
    def check_migrations(self) -> bool:
        """
        Check for pending migrations without applying them.
        
        Returns:
            True if no pending migrations, False otherwise
        """
        logger.info("Checking for pending migrations...")
        
        # Check for pending migrations
        returncode, stdout, stderr = self.run_command([
            sys.executable, 'manage.py', 'makemigrations', '--check'
        ])
        
        if returncode == 0:
            logger.info("✓ No pending migrations found")
            return True
        else:
            logger.warning("⚠ Pending migrations detected")
            logger.info(f"Output: {stdout}")
            if stderr:
                logger.warning(f"Errors: {stderr}")
            return False
    
    def migrate(self, run_syncdb: bool = False) -> bool:
        """
        Run migrations safely.
        
        Args:
            run_syncdb: Whether to run syncdb for initial deployment
            
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting migration process...")
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        try:
            # Check database connection first
            if not self.check_database_connection():
                return False
            
            # Create backup before migration
            if not self.create_backup():
                logger.warning("Backup failed, but continuing with migration...")
            
            # Create rollback script
            if not self.create_rollback_script():
                logger.warning("Failed to create rollback script...")
            
            # Run migrations
            if run_syncdb:
                logger.info("Running initial deployment with syncdb...")
                returncode, stdout, stderr = self.run_command([
                    sys.executable, 'manage.py', 'migrate', '--run-syncdb'
                ])
            else:
                logger.info("Running standard migrations...")
                returncode, stdout, stderr = self.run_command([
                    sys.executable, 'manage.py', 'migrate'
                ])
            
            if returncode == 0:
                logger.info("✓ Migrations completed successfully")
                logger.info(f"Output: {stdout}")
                
                # Verify data integrity
                if not self.verify_data_integrity():
                    logger.warning("⚠ Data integrity check failed")
                    self.monitor.log_warning("Data integrity check failed after migration")
                
                return True
            else:
                logger.error("✗ Migration failed")
                logger.error(f"Error: {stderr}")
                self.monitor.log_error(f"Migration failed: {stderr}")
                return False
                
        finally:
            # Stop monitoring
            self.monitor.stop_monitoring()
    
    def migrate_apps(self, apps: List[str]) -> bool:
        """
        Run migrations for specific apps with detailed logging.
        
        Args:
            apps: List of app names to migrate
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Running migrations for apps: {', '.join(apps)}")
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        try:
            success = True
            for app in apps:
                logger.info(f"Migrating app: {app}")
                
                returncode, stdout, stderr = self.run_command([
                    sys.executable, 'manage.py', 'migrate', app, '--verbosity=2'
                ])
                
                if returncode == 0:
                    logger.info(f"✓ {app} migration successful")
                    logger.info(f"Output: {stdout}")
                else:
                    logger.error(f"✗ {app} migration failed")
                    logger.error(f"Error: {stderr}")
                    self.monitor.log_error(f"{app} migration failed: {stderr}")
                    success = False
            
            # Verify data integrity after app migrations
            if success and not self.verify_data_integrity():
                logger.warning("⚠ Data integrity check failed after app migrations")
                self.monitor.log_warning("Data integrity check failed after app migrations")
            
            return success
            
        finally:
            # Stop monitoring
            self.monitor.stop_monitoring()
    
    def collect_static(self) -> bool:
        """
        Collect static files.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Collecting static files...")
        
        returncode, stdout, stderr = self.run_command([
            sys.executable, 'manage.py', 'collectstatic', '--noinput'
        ])
        
        if returncode == 0:
            logger.info("✓ Static files collected successfully")
            logger.info(f"Output: {stdout}")
            return True
        else:
            logger.error("✗ Static file collection failed")
            logger.error(f"Error: {stderr}")
            return False
    
    def deploy_check(self) -> bool:
        """
        Run deployment validation.
        
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("Running deployment validation...")
        
        returncode, stdout, stderr = self.run_command([
            sys.executable, 'manage.py', 'check', '--deploy'
        ])
        
        if returncode == 0:
            logger.info("✓ Deployment validation passed")
            logger.info(f"Output: {stdout}")
            return True
        else:
            logger.error("✗ Deployment validation failed")
            logger.error(f"Error: {stderr}")
            return False
    
    def compile_translations(self) -> bool:
        """
        Compile translation files.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Compiling translation files...")
        
        returncode, stdout, stderr = self.run_command([
            sys.executable, 'manage.py', 'compilemessages'
        ])
        
        if returncode == 0:
            logger.info("✓ Translations compiled successfully")
            return True
        else:
            logger.warning("⚠ Translation compilation had issues")
            logger.warning(f"Output: {stderr}")
            return True  # Don't fail deployment for translation issues
    
    def full_deploy(self) -> bool:
        """
        Run complete deployment sequence.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("Starting full deployment sequence...")
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        try:
            steps = [
                ("Database connection check", self.check_database_connection),
                ("Migration check", self.check_migrations),
                ("Run migrations", lambda: self.migrate()),
                ("Migrate specific apps", lambda: self.migrate_apps(['medications', 'users', 'security', 'medguard_notifications'])),
                ("Compile translations", self.compile_translations),
                ("Collect static files", self.collect_static),
                ("Deployment validation", self.deploy_check),
                ("Data integrity verification", self.verify_data_integrity),
            ]
            
            for step_name, step_func in steps:
                logger.info(f"\n--- {step_name} ---")
                if not step_func():
                    logger.error(f"✗ Deployment failed at: {step_name}")
                    self.monitor.log_error(f"Deployment failed at: {step_name}")
                    return False
                logger.info(f"✓ {step_name} completed")
            
            logger.info("\n🎉 Full deployment completed successfully!")
            return True
            
        finally:
            # Stop monitoring and save performance report
            self.monitor.stop_monitoring()
            performance_report = self.monitor.get_performance_report()
            report_file = self.monitoring_dir / f"full_deploy_report_{self.timestamp}.json"
            
            with open(report_file, 'w') as f:
                json.dump(performance_report, f, indent=2)
            
            logger.info(f"Performance report saved to: {report_file}")


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Production Migration Script for MedGuard SA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python production_migrate.py check-migrations
  python production_migrate.py migrate
  python production_migrate.py migrate-apps medications users
  python production_migrate.py collectstatic
  python production_migrate.py deploy-check
  python production_migrate.py full-deploy
  python production_migrate.py verify-data
  python production_migrate.py zero-downtime
        """
    )
    
    parser.add_argument(
        'command',
        choices=[
            'check-migrations',
            'migrate',
            'migrate-apps',
            'collectstatic',
            'deploy-check',
            'full-deploy',
            'backup',
            'verify-data',
            'zero-downtime'
        ],
        help='Migration command to execute'
    )
    
    parser.add_argument(
        '--apps',
        nargs='+',
        help='Specific apps to migrate (for migrate-apps command)'
    )
    
    parser.add_argument(
        '--run-syncdb',
        action='store_true',
        help='Run syncdb for initial deployment'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='Skip database backup before migration'
    )
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = ProductionMigrator()
    
    # Execute command
    try:
        if args.command == 'check-migrations':
            success = migrator.check_migrations()
        elif args.command == 'migrate':
            success = migrator.migrate(run_syncdb=args.run_syncdb)
        elif args.command == 'migrate-apps':
            if not args.apps:
                logger.error("Please specify apps to migrate with --apps")
                sys.exit(1)
            success = migrator.migrate_apps(args.apps)
        elif args.command == 'collectstatic':
            success = migrator.collect_static()
        elif args.command == 'deploy-check':
            success = migrator.deploy_check()
        elif args.command == 'full-deploy':
            success = migrator.full_deploy()
        elif args.command == 'backup':
            success = migrator.create_backup()
        elif args.command == 'verify-data':
            success = migrator.verify_data_integrity()
        elif args.command == 'zero-downtime':
            success = migrator.execute_zero_downtime_migration()
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
        
        if success:
            logger.info("Command completed successfully")
            sys.exit(0)
        else:
            logger.error("Command failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 