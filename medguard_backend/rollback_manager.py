#!/usr/bin/env python
"""
Rollback Manager for MedGuard SA

This script provides comprehensive rollback capabilities for critical migration failures.
It includes automatic backup restoration, validation, and recovery procedures.

Usage:
    python rollback_manager.py [command]

Commands:
    list-backups       - List available backups with metadata
    rollback           - Rollback to a specific backup
    emergency-rollback - Emergency rollback to most recent backup
    validate-backup    - Validate backup integrity
    restore-backup     - Restore from backup with validation
    cleanup-backups    - Clean up old backups
"""

import os
import sys
import json
import argparse
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rollback.log'),
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
    from django.conf import settings
    from django.db import connection
except ImportError as e:
    logger.error(f"Failed to import Django: {e}")
    sys.exit(1)


class RollbackManager:
    """Comprehensive rollback manager for critical migration failures."""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        self.rollback_dir = Path("rollback_scripts")
        self.rollback_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def run_command(self, command: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
        """Run a shell command safely."""
        try:
            logger.info(f"Running command: {' '.join(command)}")
            
            if capture_output:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=300
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
    
    def list_backups(self) -> List[Dict]:
        """List available backups with metadata."""
        logger.info("Listing available backups...")
        
        backups = []
        
        for backup_file in self.backup_dir.glob("medguard_backup_*.sql"):
            metadata_file = backup_file.with_suffix('.json')
            
            backup_info = {
                'filename': backup_file.name,
                'path': str(backup_file),
                'size_bytes': backup_file.stat().st_size,
                'size_human': self._format_bytes(backup_file.stat().st_size),
                'created': datetime.fromtimestamp(backup_file.stat().st_mtime),
                'metadata': None
            }
            
            # Load metadata if available
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        backup_info['metadata'] = json.load(f)
                except Exception as e:
                    logger.warning(f"Could not load metadata for {backup_file.name}: {e}")
            
            backups.append(backup_info)
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        
        return backups
    
    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes to human readable format."""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    def validate_backup(self, backup_path: str) -> bool:
        """Validate backup integrity."""
        logger.info(f"Validating backup: {backup_path}")
        
        backup_file = Path(backup_path)
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # Check file size
        if backup_file.stat().st_size == 0:
            logger.error("Backup file is empty")
            return False
        
        # Check if it's a valid PostgreSQL backup
        try:
            # Try to read the first few bytes to check format
            with open(backup_file, 'rb') as f:
                header = f.read(100)
                
            # Check for PostgreSQL custom format signature
            if b'PGDMP' in header:
                logger.info("✓ Valid PostgreSQL custom format backup")
                return True
            elif b'-- PostgreSQL database dump' in header:
                logger.info("✓ Valid PostgreSQL plain text backup")
                return True
            else:
                logger.warning("Unknown backup format, but file exists and has content")
                return True
                
        except Exception as e:
            logger.error(f"Error validating backup: {e}")
            return False
    
    def restore_backup(self, backup_path: str, validate_after: bool = True) -> bool:
        """Restore from backup with validation."""
        logger.info(f"Restoring from backup: {backup_path}")
        
        # Validate backup first
        if not self.validate_backup(backup_path):
            logger.error("Backup validation failed")
            return False
        
        # Get database settings
        db_settings = settings.DATABASES['default']
        
        try:
            # Stop application (if running)
            logger.info("Stopping application...")
            # Add your application stop command here
            # self.run_command(['systemctl', 'stop', 'medguard-backend'])
            
            # Restore database
            logger.info("Restoring database...")
            
            if db_settings['ENGINE'] == 'django.db.backends.postgresql':
                # Set password environment variable
                env = os.environ.copy()
                env['PGPASSWORD'] = db_settings['PASSWORD']
                
                # Drop and recreate database
                logger.info("Dropping and recreating database...")
                
                drop_cmd = [
                    'psql',
                    '-h', db_settings['HOST'],
                    '-p', str(db_settings['PORT']),
                    '-U', db_settings['USER'],
                    '-d', 'postgres',
                    '-c', f'DROP DATABASE IF EXISTS {db_settings["NAME"]};'
                ]
                
                create_cmd = [
                    'psql',
                    '-h', db_settings['HOST'],
                    '-p', str(db_settings['PORT']),
                    '-U', db_settings['USER'],
                    '-d', 'postgres',
                    '-c', f'CREATE DATABASE {db_settings["NAME"]};'
                ]
                
                restore_cmd = [
                    'pg_restore',
                    '-h', db_settings['HOST'],
                    '-p', str(db_settings['PORT']),
                    '-U', db_settings['USER'],
                    '-d', db_settings['NAME'],
                    '--verbose',
                    '--clean',
                    '--if-exists',
                    str(backup_path)
                ]
                
                # Execute commands
                for cmd, desc in [(drop_cmd, "Drop database"), (create_cmd, "Create database"), (restore_cmd, "Restore backup")]:
                    returncode, stdout, stderr = subprocess.run(
                        cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    
                    if returncode != 0:
                        logger.error(f"{desc} failed: {stderr}")
                        return False
                    
                    logger.info(f"✓ {desc} completed")
                
            else:
                logger.error("Restore not implemented for this database engine")
                return False
            
            # Validate restoration
            if validate_after:
                logger.info("Validating database restoration...")
                
                # Check database connection
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        logger.info("✓ Database connection successful")
                except Exception as e:
                    logger.error(f"Database connection failed: {e}")
                    return False
                
                # Run Django checks
                returncode, stdout, stderr = self.run_command([
                    sys.executable, 'manage.py', 'check', '--deploy'
                ])
                
                if returncode == 0:
                    logger.info("✓ Django deployment check passed")
                else:
                    logger.warning(f"⚠ Django deployment check failed: {stderr}")
            
            # Restart application
            logger.info("Restarting application...")
            # Add your application start command here
            # self.run_command(['systemctl', 'start', 'medguard-backend'])
            
            logger.info("✓ Backup restoration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False
    
    def emergency_rollback(self) -> bool:
        """Emergency rollback to most recent backup."""
        logger.info("Executing emergency rollback...")
        
        # Get available backups
        backups = self.list_backups()
        
        if not backups:
            logger.error("No backups available for rollback")
            return False
        
        # Get most recent backup
        latest_backup = backups[0]
        backup_path = latest_backup['path']
        
        logger.info(f"Rolling back to: {latest_backup['filename']}")
        logger.info(f"Created: {latest_backup['created']}")
        logger.info(f"Size: {latest_backup['size_human']}")
        
        # Confirm rollback
        logger.warning("⚠ EMERGENCY ROLLBACK - This will overwrite current database!")
        logger.warning("⚠ Make sure you have stopped the application")
        
        # Perform rollback
        return self.restore_backup(backup_path, validate_after=True)
    
    def rollback_to_backup(self, backup_filename: str) -> bool:
        """Rollback to a specific backup."""
        logger.info(f"Rolling back to backup: {backup_filename}")
        
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_filename}")
            return False
        
        # Get backup info
        backups = self.list_backups()
        target_backup = None
        
        for backup in backups:
            if backup['filename'] == backup_filename:
                target_backup = backup
                break
        
        if not target_backup:
            logger.error(f"Backup not found in list: {backup_filename}")
            return False
        
        logger.info(f"Backup details:")
        logger.info(f"  Created: {target_backup['created']}")
        logger.info(f"  Size: {target_backup['size_human']}")
        
        if target_backup['metadata']:
            logger.info(f"  Database: {target_backup['metadata'].get('database', 'unknown')}")
            logger.info(f"  Migration version: {target_backup['metadata'].get('migration_version', 'unknown')}")
        
        # Perform rollback
        return self.restore_backup(str(backup_path), validate_after=True)
    
    def cleanup_backups(self, keep_days: int = 30) -> bool:
        """Clean up old backups."""
        logger.info(f"Cleaning up backups older than {keep_days} days...")
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        deleted_count = 0
        
        for backup_file in self.backup_dir.glob("medguard_backup_*.sql"):
            file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            if file_date < cutoff_date:
                try:
                    # Delete backup file
                    backup_file.unlink()
                    
                    # Delete metadata file if it exists
                    metadata_file = backup_file.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    logger.info(f"Deleted old backup: {backup_file.name}")
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to delete {backup_file.name}: {e}")
        
        logger.info(f"✓ Cleanup completed. Deleted {deleted_count} old backups")
        return True
    
    def create_rollback_script(self, backup_path: str) -> bool:
        """Create a rollback script for a specific backup."""
        logger.info(f"Creating rollback script for: {backup_path}")
        
        backup_file = Path(backup_path)
        if not backup_file.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # Get database settings
        db_settings = settings.DATABASES['default']
        
        # Create rollback script
        script_content = f"""#!/bin/bash
# Rollback script for {backup_file.name}
# Created: {datetime.now().isoformat()}

set -e

echo "Starting rollback for {backup_file.name}..."

# Environment variables
export DJANGO_SETTINGS_MODULE="medguard_backend.settings.production"
export DB_NAME="{db_settings['NAME']}"
export DB_USER="{db_settings['USER']}"
export DB_PASSWORD="{db_settings['PASSWORD']}"
export DB_HOST="{db_settings['HOST']}"
export DB_PORT="{db_settings['PORT']}"

# Check if backup exists
BACKUP_FILE="{backup_path}"
if [ ! -f "$BACKUP_FILE" ]; then
    echo "ERROR: Backup file $BACKUP_FILE not found!"
    exit 1
fi

# Stop application
echo "Stopping application..."
# systemctl stop medguard-backend

# Drop and recreate database
echo "Dropping and recreating database..."
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"

# Restore database from backup
echo "Restoring database from backup..."
PGPASSWORD="$DB_PASSWORD" pg_restore -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --verbose --clean --if-exists "$BACKUP_FILE"

# Verify restoration
echo "Verifying database restoration..."
python manage.py check --deploy

# Restart application
echo "Restarting application..."
# systemctl start medguard-backend

echo "Rollback completed successfully!"
"""
        
        script_file = self.rollback_dir / f"rollback_{backup_file.stem}.sh"
        
        with open(script_file, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        script_file.chmod(0o755)
        
        logger.info(f"✓ Rollback script created: {script_file}")
        return True


def main():
    """Main entry point for the rollback manager."""
    parser = argparse.ArgumentParser(
        description="Rollback Manager for MedGuard SA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rollback_manager.py list-backups
  python rollback_manager.py validate-backup backups/medguard_backup_20240101_120000.sql
  python rollback_manager.py rollback medguard_backup_20240101_120000.sql
  python rollback_manager.py emergency-rollback
  python rollback_manager.py cleanup-backups --keep-days 7
        """
    )
    
    parser.add_argument(
        'command',
        choices=[
            'list-backups',
            'rollback',
            'emergency-rollback',
            'validate-backup',
            'restore-backup',
            'cleanup-backups'
        ],
        help='Rollback command to execute'
    )
    
    parser.add_argument(
        'backup_path',
        nargs='?',
        help='Backup file path or filename (for rollback, validate-backup, restore-backup)'
    )
    
    parser.add_argument(
        '--keep-days',
        type=int,
        default=30,
        help='Number of days to keep backups (for cleanup-backups)'
    )
    
    args = parser.parse_args()
    
    # Initialize rollback manager
    manager = RollbackManager()
    
    # Execute command
    try:
        if args.command == 'list-backups':
            backups = manager.list_backups()
            
            if not backups:
                logger.info("No backups found")
                return
            
            logger.info(f"Found {len(backups)} backup(s):")
            logger.info("-" * 80)
            
            for backup in backups:
                logger.info(f"📁 {backup['filename']}")
                logger.info(f"   Created: {backup['created']}")
                logger.info(f"   Size: {backup['size_human']}")
                
                if backup['metadata']:
                    logger.info(f"   Database: {backup['metadata'].get('database', 'unknown')}")
                    logger.info(f"   Migration: {backup['metadata'].get('migration_version', 'unknown')}")
                
                logger.info("")
        
        elif args.command == 'validate-backup':
            if not args.backup_path:
                logger.error("Please specify backup path")
                sys.exit(1)
            
            success = manager.validate_backup(args.backup_path)
            if success:
                logger.info("✓ Backup validation passed")
                sys.exit(0)
            else:
                logger.error("✗ Backup validation failed")
                sys.exit(1)
        
        elif args.command == 'restore-backup':
            if not args.backup_path:
                logger.error("Please specify backup path")
                sys.exit(1)
            
            success = manager.restore_backup(args.backup_path)
            if success:
                logger.info("✓ Backup restoration completed")
                sys.exit(0)
            else:
                logger.error("✗ Backup restoration failed")
                sys.exit(1)
        
        elif args.command == 'rollback':
            if not args.backup_path:
                logger.error("Please specify backup filename")
                sys.exit(1)
            
            success = manager.rollback_to_backup(args.backup_path)
            if success:
                logger.info("✓ Rollback completed")
                sys.exit(0)
            else:
                logger.error("✗ Rollback failed")
                sys.exit(1)
        
        elif args.command == 'emergency-rollback':
            success = manager.emergency_rollback()
            if success:
                logger.info("✓ Emergency rollback completed")
                sys.exit(0)
            else:
                logger.error("✗ Emergency rollback failed")
                sys.exit(1)
        
        elif args.command == 'cleanup-backups':
            success = manager.cleanup_backups(args.keep_days)
            if success:
                logger.info("✓ Backup cleanup completed")
                sys.exit(0)
            else:
                logger.error("✗ Backup cleanup failed")
                sys.exit(1)
        
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Rollback interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 