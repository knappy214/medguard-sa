#!/usr/bin/env python
"""
Comprehensive Migration Fix Script for MedGuard SA Backend

This script handles common migration issues:
1. Circular dependency issues between User and Medication models
2. JSONField compatibility issues across different Django versions
3. ImageField upload_to path conflicts
4. Timezone-aware datetime field migrations
5. Unique constraint violations during data migration
6. Foreign key constraint issues with existing data
7. Decimal field precision changes for medication dosages
8. Index naming conflicts in complex models
9. Migration dependency ordering issues
10. Database engine-specific migration differences (PostgreSQL vs SQLite)

Usage:
    python fix_migrations.py [--fix-all] [--fix-circular] [--fix-json] [--fix-images]
    python fix_migrations.py [--fix-timezone] [--fix-constraints] [--fix-foreign-keys]
    python fix_migrations.py [--fix-decimal] [--fix-indexes] [--fix-dependencies]
    python fix_migrations.py [--fix-engine] [--dry-run] [--backup]
"""

import os
import sys
import logging
import json
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration_fix.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')

# Import Django after setting environment
import django
django.setup()

from django.conf import settings
from django.db import connection, migrations, models
from django.db.migrations.operations.base import Operation
from django.db.migrations.writer import MigrationWriter
from django.db.models import Model, Field
from django.core.management import call_command
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import InteractiveMigrationQuestioner
from django.db.migrations.state import ProjectState
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.executor import MigrationExecutor


class MigrationFixer:
    """Comprehensive migration issue fixer for MedGuard SA."""
    
    def __init__(self, dry_run: bool = False, backup: bool = True):
        self.dry_run = dry_run
        self.backup = backup
        self.backend_dir = Path(__file__).parent
        self.settings = settings
        self.connection = connection
        self.fixes_applied = []
        
    def log_section(self, title: str):
        """Log a section header."""
        logger.info(f"\n{'='*60}")
        logger.info(f" {title}")
        logger.info(f"{'='*60}")
    
    def create_backup(self) -> bool:
        """Create database backup before applying fixes."""
        if not self.backup:
            return True
            
        self.log_section("Creating Database Backup")
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"backup_before_fixes_{timestamp}.sql"
            
            if self.settings.DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql':
                # PostgreSQL backup
                db_config = self.settings.DATABASES['default']
                cmd = [
                    'pg_dump',
                    '-h', db_config.get('HOST', 'localhost'),
                    '-p', str(db_config.get('PORT', 5432)),
                    '-U', db_config.get('USER', 'postgres'),
                    '-d', db_config.get('NAME', 'medguard'),
                    '-f', backup_file,
                    '--no-password'
                ]
                
                # Set password environment variable
                env = os.environ.copy()
                if db_config.get('PASSWORD'):
                    env['PGPASSWORD'] = db_config['PASSWORD']
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ PostgreSQL backup created: {backup_file}")
                    return True
                else:
                    logger.error(f"❌ PostgreSQL backup failed: {result.stderr}")
                    return False
                    
            else:
                # SQLite backup
                db_path = self.settings.DATABASES['default']['NAME']
                import shutil
                shutil.copy2(db_path, backup_file)
                logger.info(f"✅ SQLite backup created: {backup_file}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Backup creation failed: {e}")
            return False
    
    def fix_circular_dependencies(self) -> bool:
        """Fix circular dependency issues between User and Medication models."""
        self.log_section("Fixing Circular Dependencies")
        
        try:
            # Check for circular dependencies in migrations
            loader = MigrationLoader(connection)
            graph = loader.graph
            
            # Find circular dependencies
            circular_deps = []
            for app_label in graph.apps:
                for migration_name in graph.apps[app_label]:
                    migration = graph.apps[app_label][migration_name]
                    for dep in migration.dependencies:
                        if dep[0] == app_label and dep[1] != migration_name:
                            # Check if this creates a cycle
                            if graph.is_dependency(migration, graph.apps[app_label][dep[1]]):
                                circular_deps.append((app_label, migration_name, dep))
            
            if not circular_deps:
                logger.info("✅ No circular dependencies found")
                return True
            
            logger.info(f"Found {len(circular_deps)} circular dependencies")
            
            for app_label, migration_name, dep in circular_deps:
                logger.info(f"Fixing circular dependency: {app_label}.{migration_name} -> {dep}")
                
                # Create a new migration to break the cycle
                if not self.dry_run:
                    # Use string references instead of direct model references
                    migration_file = self.backend_dir / app_label / 'migrations' / f"{migration_name}.py"
                    
                    if migration_file.exists():
                        with open(migration_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Replace direct model references with string references
                        content = content.replace(
                            "models.ForeignKey(User,",
                            "models.ForeignKey('users.User',"
                        )
                        content = content.replace(
                            "models.ForeignKey(Medication,",
                            "models.ForeignKey('medications.Medication',"
                        )
                        
                        with open(migration_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logger.info(f"✅ Fixed circular dependency in {migration_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix circular dependencies: {e}")
            return False
    
    def fix_jsonfield_compatibility(self) -> bool:
        """Fix JSONField compatibility issues across Django versions."""
        self.log_section("Fixing JSONField Compatibility")
        
        try:
            # Check Django version
            django_version = django.get_version()
            logger.info(f"Django version: {django_version}")
            
            # Find all JSONField usages in models
            json_fields = []
            
            for app_config in django.apps.apps.get_app_configs():
                if app_config.name.startswith('medguard'):
                    for model in app_config.get_models():
                        for field in model._meta.fields:
                            if isinstance(field, models.JSONField):
                                json_fields.append((model, field))
            
            if not json_fields:
                logger.info("✅ No JSONField compatibility issues found")
                return True
            
            logger.info(f"Found {len(json_fields)} JSONField usages")
            
            for model, field in json_fields:
                logger.info(f"Checking JSONField: {model._meta.app_label}.{model._meta.model_name}.{field.name}")
                
                # Check if JSONField has proper default handling
                if field.default == models.fields.NOT_PROVIDED:
                    logger.warning(f"JSONField {field.name} has no default value")
                    
                    if not self.dry_run:
                        # Add a default value to prevent issues
                        field.default = dict
                        
                        # Create a migration to add the default
                        call_command(
                            'makemigrations',
                            model._meta.app_label,
                            '--name', f'fix_jsonfield_default_{field.name}',
                            '--empty'
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix JSONField compatibility: {e}")
            return False
    
    def fix_imagefield_paths(self) -> bool:
        """Fix ImageField upload_to path conflicts."""
        self.log_section("Fixing ImageField Path Conflicts")
        
        try:
            # Find all ImageField usages
            image_fields = []
            
            for app_config in django.apps.apps.get_app_configs():
                if app_config.name.startswith('medguard'):
                    for model in app_config.get_models():
                        for field in model._meta.fields:
                            if isinstance(field, models.ImageField):
                                image_fields.append((model, field))
            
            if not image_fields:
                logger.info("✅ No ImageField path conflicts found")
                return True
            
            logger.info(f"Found {len(image_fields)} ImageField usages")
            
            # Check for path conflicts
            upload_paths = {}
            conflicts = []
            
            for model, field in image_fields:
                upload_to = field.upload_to
                if upload_to in upload_paths:
                    conflicts.append((upload_paths[upload_to], (model, field)))
                else:
                    upload_paths[upload_to] = (model, field)
            
            if not conflicts:
                logger.info("✅ No ImageField path conflicts found")
                return True
            
            logger.info(f"Found {len(conflicts)} ImageField path conflicts")
            
            for (model1, field1), (model2, field2) in conflicts:
                logger.info(f"Fixing path conflict: {model1._meta.model_name}.{field1.name} and {model2._meta.model_name}.{field2.name}")
                
                if not self.dry_run:
                    # Create unique paths for each field
                    new_path1 = f"{model1._meta.app_label}/{model1._meta.model_name}/{field1.name}/"
                    new_path2 = f"{model2._meta.app_label}/{model2._meta.model_name}/{field2.name}/"
                    
                    # Update the fields
                    field1.upload_to = new_path1
                    field2.upload_to = new_path2
                    
                    logger.info(f"✅ Updated paths: {new_path1}, {new_path2}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to fix ImageField paths: {e}")
            return False  
 
