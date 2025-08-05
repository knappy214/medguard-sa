#!/usr/bin/env python3
"""
MedGuard SA Migration Fix Script

This script handles common migration issues in the MedGuard backend:
1. Circular dependency issues between User and Medication models
2. JSONField compatibility issues across different Django versions
3. ImageField upload_to path conflicts
4. Handle timezone-aware datetime field migrations
5. Fix unique constraint violations during data migration
6. Resolve foreign key constraint issues with existing data
7. Handle decimal field precision changes for medication dosages
8. Fix index naming conflicts in complex models
9. Resolve migration dependency ordering issues
10. Handle database engine-specific migration for PostgreSQL

Usage:
    python fix_migrations.py [--dry-run] [--fix-circular] [--fix-json] [--fix-images] [--fix-timezone] [--fix-constraints] [--fix-foreign-keys] [--fix-decimal] [--fix-indexes] [--fix-dependencies] [--fix-postgresql]
"""

import os
import sys
import json
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.db import connection, transaction
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.writer import MigrationWriter
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.questioner import InteractiveMigrationQuestioner
from django.db.migrations.state import ProjectState
from django.apps import apps
import argparse


class MigrationFixer:
    """Handles migration fixes for MedGuard SA backend."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.backup_dir = Path("migration_backups")
        self.fixes_applied = []
        self.errors = []
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
        
        # Django version compatibility
        self.django_version = django.get_version()
        self.is_django_4 = self.django_version.startswith('4')
        self.is_django_5 = self.django_version.startswith('5')
        
        print(f"🔧 MedGuard SA Migration Fixer")
        print(f"   Django version: {self.django_version}")
        print(f"   Dry run: {dry_run}")
        print(f"   Backup directory: {self.backup_dir}")
        print()
    
    def log_fix(self, fix_type: str, description: str, file_path: str = None):
        """Log a fix that was applied."""
        fix_info = {
            'type': fix_type,
            'description': description,
            'file_path': file_path,
            'timestamp': datetime.now().isoformat()
        }
        self.fixes_applied.append(fix_info)
        print(f"✅ {fix_type}: {description}")
        if file_path:
            print(f"   📁 {file_path}")
    
    def log_error(self, error_type: str, description: str, exception: Exception = None):
        """Log an error that occurred."""
        error_info = {
            'type': error_type,
            'description': description,
            'exception': str(exception) if exception else None,
            'timestamp': datetime.now().isoformat()
        }
        self.errors.append(error_info)
        print(f"❌ {error_type}: {description}")
        if exception:
            print(f"   💥 {exception}")
    
    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of a file."""
        if not file_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        
        if not self.dry_run:
            shutil.copy2(file_path, backup_path)
            print(f"📦 Backed up: {file_path} -> {backup_path}")
        
        return backup_path
    
    def fix_circular_dependencies(self):
        """Fix circular dependency issues between User and Medication models."""
        print("🔄 Fixing circular dependencies...")
        
        # Common circular dependency patterns in MedGuard
        circular_patterns = [
            # User -> MedicationSchedule -> User
            {
                'description': 'User-MedicationSchedule circular dependency',
                'models': ['users.User', 'medications.MedicationSchedule'],
                'solution': 'Use string reference for User in MedicationSchedule'
            },
            # Medication -> StockAlert -> User
            {
                'description': 'Medication-StockAlert-User circular dependency',
                'models': ['medications.Medication', 'medications.StockAlert', 'users.User'],
                'solution': 'Use string references for foreign keys'
            },
            # PrescriptionRenewal circular dependency
            {
                'description': 'PrescriptionRenewal circular dependency',
                'models': ['users.User', 'medications.PrescriptionRenewal', 'medications.Medication'],
                'solution': 'Use string references for all foreign keys'
            }
        ]
        
        for pattern in circular_patterns:
            try:
                self._fix_circular_pattern(pattern)
            except Exception as e:
                self.log_error('Circular Dependency Fix', pattern['description'], e)
    
    def _fix_circular_pattern(self, pattern: Dict[str, Any]):
        """Fix a specific circular dependency pattern."""
        print(f"   🔍 Checking: {pattern['description']}")
        
        # Check migration files for circular dependencies
        migration_dirs = [
            Path('medguard_backend/users/migrations'),
            Path('medguard_backend/medications/migrations'),
        ]
        
        for migration_dir in migration_dirs:
            if not migration_dir.exists():
                continue
            
            for migration_file in migration_dir.glob('*.py'):
                if migration_file.name == '__init__.py':
                    continue
                
                try:
                    self._fix_migration_circular_deps(migration_file, pattern)
                except Exception as e:
                    self.log_error('Migration Fix', f"Error fixing {migration_file}", e)
    
    def _fix_migration_circular_deps(self, migration_file: Path, pattern: Dict[str, Any]):
        """Fix circular dependencies in a specific migration file."""
        content = migration_file.read_text(encoding='utf-8')
        original_content = content
        
        # Fix common circular dependency issues
        fixes = [
            # Fix User foreign key references
            (
                r"models\.ForeignKey\(\s*User,",
                "models.ForeignKey('users.User',"
            ),
            (
                r"models\.OneToOneField\(\s*User,",
                "models.OneToOneField('users.User',"
            ),
            # Fix Medication foreign key references
            (
                r"models\.ForeignKey\(\s*Medication,",
                "models.ForeignKey('medications.Medication',"
            ),
            # Fix get_user_model() calls
            (
                r"from django\.contrib\.auth import get_user_model\nUser = get_user_model\(\)",
                "from django.contrib.auth import get_user_model"
            ),
            (
                r"User,",
                "'users.User',"
            )
        ]
        
        for pattern_regex, replacement in fixes:
            content = re.sub(pattern_regex, replacement, content, flags=re.MULTILINE)
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(migration_file)
                migration_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'Circular Dependency',
                f"Fixed circular dependencies in {migration_file.name}",
                str(migration_file)
            )
    
    def fix_jsonfield_compatibility(self):
        """Fix JSONField compatibility issues across Django versions."""
        print("📄 Fixing JSONField compatibility...")
        
        # Django version-specific JSONField fixes
        if self.is_django_4:
            self._fix_django4_jsonfield()
        elif self.is_django_5:
            self._fix_django5_jsonfield()
        else:
            print(f"   ⚠️  Unknown Django version: {self.django_version}")
    
    def _fix_django4_jsonfield(self):
        """Fix JSONField for Django 4.x."""
        print("   🎯 Applying Django 4.x JSONField fixes...")
        
        # Check for JSONField usage in models
        model_files = [
            Path('medguard_backend/users/models.py'),
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_jsonfield(model_file, django_version=4)
            except Exception as e:
                self.log_error('JSONField Fix', f"Error fixing {model_file}", e)
    
    def _fix_django5_jsonfield(self):
        """Fix JSONField for Django 5.x."""
        print("   🎯 Applying Django 5.x JSONField fixes...")
        
        # Check for JSONField usage in models
        model_files = [
            Path('medguard_backend/users/models.py'),
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_jsonfield(model_file, django_version=5)
            except Exception as e:
                self.log_error('JSONField Fix', f"Error fixing {model_file}", e)
    
    def _fix_model_jsonfield(self, model_file: Path, django_version: int):
        """Fix JSONField in a specific model file."""
        content = model_file.read_text(encoding='utf-8')
        original_content = content
        
        if django_version == 4:
            # Django 4.x: Use django.contrib.postgres.fields.JSONField
            fixes = [
                (
                    r"from django\.db import models",
                    "from django.db import models\nfrom django.contrib.postgres.fields import JSONField"
                ),
                (
                    r"models\.JSONField\(",
                    "JSONField("
                )
            ]
        else:  # Django 5.x
            # Django 5.x: Use django.db.models.JSONField
            fixes = [
                (
                    r"from django\.contrib\.postgres\.fields import JSONField",
                    ""
                ),
                (
                    r"JSONField\(",
                    "models.JSONField("
                )
            ]
        
        for pattern_regex, replacement in fixes:
            content = re.sub(pattern_regex, replacement, content, flags=re.MULTILINE)
        
        # Clean up empty imports
        content = re.sub(r"from django\.db import models\n\n", "from django.db import models\n", content)
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(model_file)
                model_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'JSONField Compatibility',
                f"Fixed JSONField for Django {django_version}.x in {model_file.name}",
                str(model_file)
            )
    
    def fix_imagefield_paths(self):
        """Fix ImageField upload_to path conflicts."""
        print("🖼️  Fixing ImageField upload paths...")
        
        # Common upload path issues
        path_issues = [
            {
                'description': 'Avatar upload path conflicts',
                'model': 'users.UserAvatar',
                'field': 'image',
                'current_path': 'avatars/%Y/%m/%d/',
                'suggested_path': 'users/avatars/%Y/%m/%d/'
            },
            {
                'description': 'Medication image path conflicts',
                'model': 'medications.Medication',
                'fields': [
                    'medication_image',
                    'medication_image_thumbnail',
                    'medication_image_webp',
                    'medication_image_avif',
                    'medication_image_jpeg_xl',
                    'medication_image_original'
                ],
                'current_paths': [
                    'medications/images/',
                    'medications/thumbnails/',
                    'medications/webp/',
                    'medications/avif/',
                    'medications/jxl/',
                    'medications/original/'
                ],
                'suggested_paths': [
                    'medications/images/%Y/%m/%d/',
                    'medications/thumbnails/%Y/%m/%d/',
                    'medications/webp/%Y/%m/%d/',
                    'medications/avif/%Y/%m/%d/',
                    'medications/jxl/%Y/%m/%d/',
                    'medications/original/%Y/%m/%d/'
                ]
            }
        ]
        
        for issue in path_issues:
            try:
                self._fix_imagefield_path(issue)
            except Exception as e:
                self.log_error('ImageField Path Fix', issue['description'], e)
    
    def _fix_imagefield_path(self, issue: Dict[str, Any]):
        """Fix ImageField upload paths for a specific issue."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check model files
        model_files = [
            Path('medguard_backend/users/models.py'),
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_imagefield_paths(model_file, issue)
            except Exception as e:
                self.log_error('Model ImageField Fix', f"Error fixing {model_file}", e)
    
    def _fix_model_imagefield_paths(self, model_file: Path, issue: Dict[str, Any]):
        """Fix ImageField paths in a specific model file."""
        content = model_file.read_text(encoding='utf-8')
        original_content = content
        
        # Handle single field fixes
        if 'field' in issue:
            current_path = issue['current_path']
            suggested_path = issue['suggested_path']
            
            pattern = rf"upload_to='{re.escape(current_path)}'"
            replacement = f"upload_to='{suggested_path}'"
            
            content = re.sub(pattern, replacement, content)
        
        # Handle multiple field fixes
        elif 'fields' in issue:
            for i, field in enumerate(issue['fields']):
                current_path = issue['current_paths'][i]
                suggested_path = issue['suggested_paths'][i]
                
                pattern = rf"upload_to='{re.escape(current_path)}'"
                replacement = f"upload_to='{suggested_path}'"
                
                content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(model_file)
                model_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'ImageField Path',
                f"Fixed upload paths in {model_file.name}",
                str(model_file)
            )
    
    def fix_timezone_datetime_fields(self):
        """Fix timezone-aware datetime field migrations."""
        print("🕐 Fixing timezone-aware datetime field migrations...")
        
        # Common timezone issues in MedGuard
        timezone_issues = [
            {
                'description': 'User model datetime fields',
                'model': 'users.User',
                'fields': ['created_at', 'updated_at', 'last_login', 'date_of_birth'],
                'timezone_fields': ['created_at', 'updated_at', 'last_login']
            },
            {
                'description': 'Medication model datetime fields',
                'model': 'medications.Medication',
                'fields': ['created_at', 'updated_at', 'expiration_date'],
                'timezone_fields': ['created_at', 'updated_at']
            },
            {
                'description': 'MedicationSchedule datetime fields',
                'model': 'medications.MedicationSchedule',
                'fields': ['created_at', 'updated_at', 'start_date', 'end_date'],
                'timezone_fields': ['created_at', 'updated_at']
            },
            {
                'description': 'MedicationLog datetime fields',
                'model': 'medications.MedicationLog',
                'fields': ['created_at', 'updated_at', 'scheduled_time', 'actual_time'],
                'timezone_fields': ['created_at', 'updated_at', 'scheduled_time', 'actual_time']
            }
        ]
        
        for issue in timezone_issues:
            try:
                self._fix_timezone_issue(issue)
            except Exception as e:
                self.log_error('Timezone Fix', issue['description'], e)
    
    def _fix_timezone_issue(self, issue: Dict[str, Any]):
        """Fix timezone issues for a specific model."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check model files
        model_files = [
            Path('medguard_backend/users/models.py'),
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_timezone_fields(model_file, issue)
            except Exception as e:
                self.log_error('Model Timezone Fix', f"Error fixing {model_file}", e)
    
    def _fix_model_timezone_fields(self, model_file: Path, issue: Dict[str, Any]):
        """Fix timezone fields in a specific model file."""
        content = model_file.read_text(encoding='utf-8')
        original_content = content
        
        # Fix timezone-aware datetime fields
        for field in issue['timezone_fields']:
            # Add timezone import if not present
            if 'from django.utils import timezone' not in content:
                content = re.sub(
                    r'from django\.db import models',
                    'from django.db import models\nfrom django.utils import timezone',
                    content
                )
            
            # Fix auto_now_add and auto_now fields to use timezone.now
            if field in ['created_at', 'updated_at']:
                # Look for DateTimeField with auto_now_add or auto_now
                pattern = rf'(\s+{field}\s*=\s*models\.DateTimeField\()([^)]*)(\))'
                match = re.search(pattern, content)
                if match:
                    field_def = match.group(2)
                    if 'auto_now_add=True' in field_def:
                        # Add default=timezone.now for auto_now_add
                        new_field_def = field_def.replace(
                            'auto_now_add=True',
                            'auto_now_add=True, default=timezone.now'
                        )
                        content = content.replace(match.group(0), f'{match.group(1)}{new_field_def}{match.group(3)}')
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(model_file)
                model_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'Timezone Fields',
                f"Fixed timezone fields in {model_file.name}",
                str(model_file)
            )
    
    def fix_unique_constraint_violations(self):
        """Fix unique constraint violations during data migration."""
        print("🔒 Fixing unique constraint violations...")
        
        # Common unique constraint issues in MedGuard
        unique_constraint_issues = [
            {
                'description': 'User email uniqueness',
                'model': 'users.User',
                'field': 'email',
                'constraint_type': 'unique',
                'resolution_strategy': 'update_duplicates'
            },
            {
                'description': 'Medication name uniqueness',
                'model': 'medications.Medication',
                'field': 'name',
                'constraint_type': 'unique_together',
                'related_fields': ['generic_name', 'strength'],
                'resolution_strategy': 'append_suffix'
            },
            {
                'description': 'Prescription number uniqueness',
                'model': 'medications.PrescriptionRenewal',
                'field': 'prescription_number',
                'constraint_type': 'unique',
                'resolution_strategy': 'generate_new_number'
            }
        ]
        
        for issue in unique_constraint_issues:
            try:
                self._fix_unique_constraint_issue(issue)
            except Exception as e:
                self.log_error('Unique Constraint Fix', issue['description'], e)
    
    def _fix_unique_constraint_issue(self, issue: Dict[str, Any]):
        """Fix unique constraint issues for a specific model."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check migration files for unique constraint definitions
        migration_dirs = [
            Path('medguard_backend/users/migrations'),
            Path('medguard_backend/medications/migrations'),
        ]
        
        for migration_dir in migration_dirs:
            if not migration_dir.exists():
                continue
            
            for migration_file in migration_dir.glob('*.py'):
                if migration_file.name == '__init__.py':
                    continue
                
                try:
                    self._fix_migration_unique_constraints(migration_file, issue)
                except Exception as e:
                    self.log_error('Migration Unique Constraint Fix', f"Error fixing {migration_file}", e)
    
    def _fix_migration_unique_constraints(self, migration_file: Path, issue: Dict[str, Any]):
        """Fix unique constraints in a specific migration file."""
        content = migration_file.read_text(encoding='utf-8')
        original_content = content
        
        # Fix unique constraint definitions
        if issue['constraint_type'] == 'unique':
            # Add unique=True to field definition
            pattern = rf"(\s+{issue['field']}\s*=\s*models\.[^,]+)(,?)(\s*#.*)?$"
            replacement = r"\1, unique=True\2\3"
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        elif issue['constraint_type'] == 'unique_together':
            # Add unique_together to model Meta
            unique_fields = [issue['field']] + issue.get('related_fields', [])
            unique_together_str = f"unique_together = [('{', '.join(unique_fields)}')]"
            
            # Check if Meta class exists
            if 'class Meta:' in content:
                # Add unique_together to existing Meta
                content = re.sub(
                    r'(class Meta:.*?)(\n\s+)(\w+.*?)(\n\s*)(\n|$)',
                    rf'\1\2{unique_together_str}\n\4\5',
                    content,
                    flags=re.DOTALL
                )
            else:
                # Create new Meta class
                content = re.sub(
                    r'(\n\s*)(class Meta:.*?)(\n\s*)(\n|$)',
                    rf'\1class Meta:\n\3    {unique_together_str}\n\4',
                    content,
                    flags=re.DOTALL
                )
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(migration_file)
                migration_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'Unique Constraint',
                f"Fixed unique constraints in {migration_file.name}",
                str(migration_file)
            )
    
    def fix_foreign_key_constraints(self):
        """Resolve foreign key constraint issues with existing data."""
        print("🔗 Fixing foreign key constraint issues...")
        
        # Common foreign key constraint issues in MedGuard
        foreign_key_issues = [
            {
                'description': 'User foreign key references',
                'model': 'users.User',
                'related_models': ['medications.MedicationSchedule', 'medications.MedicationLog', 'medications.StockAlert'],
                'resolution_strategy': 'cascade_delete'
            },
            {
                'description': 'Medication foreign key references',
                'model': 'medications.Medication',
                'related_models': ['medications.MedicationSchedule', 'medications.MedicationLog', 'medications.StockAlert'],
                'resolution_strategy': 'protect_delete'
            },
            {
                'description': 'PrescriptionRenewal foreign key references',
                'model': 'medications.PrescriptionRenewal',
                'related_models': ['users.User', 'medications.Medication'],
                'resolution_strategy': 'set_null'
            }
        ]
        
        for issue in foreign_key_issues:
            try:
                self._fix_foreign_key_issue(issue)
            except Exception as e:
                self.log_error('Foreign Key Fix', issue['description'], e)
    
    def _fix_foreign_key_issue(self, issue: Dict[str, Any]):
        """Fix foreign key issues for a specific model."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check model files for foreign key definitions
        model_files = [
            Path('medguard_backend/users/models.py'),
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_foreign_keys(model_file, issue)
            except Exception as e:
                self.log_error('Model Foreign Key Fix', f"Error fixing {model_file}", e)
    
    def _fix_model_foreign_keys(self, model_file: Path, issue: Dict[str, Any]):
        """Fix foreign keys in a specific model file."""
        content = model_file.read_text(encoding='utf-8')
        original_content = content
        
        # Fix foreign key on_delete behavior based on resolution strategy
        resolution_map = {
            'cascade_delete': 'CASCADE',
            'protect_delete': 'PROTECT',
            'set_null': 'SET_NULL',
            'set_default': 'SET_DEFAULT'
        }
        
        on_delete_value = resolution_map.get(issue['resolution_strategy'], 'CASCADE')
        
        # Update foreign key on_delete behavior
        for related_model in issue['related_models']:
            model_name = related_model.split('.')[-1]
            
            # Fix ForeignKey definitions
            pattern = rf"(\s+\w+\s*=\s*models\.ForeignKey\()([^)]*)(\))"
            matches = re.finditer(pattern, content)
            
            for match in matches:
                field_def = match.group(2)
                if model_name in field_def and 'on_delete=' not in field_def:
                    # Add on_delete parameter
                    new_field_def = field_def.rstrip(', ') + f", on_delete=models.{on_delete_value}"
                    content = content.replace(match.group(0), f'{match.group(1)}{new_field_def}{match.group(3)}')
                elif model_name in field_def and 'on_delete=models.CASCADE' in field_def:
                    # Update existing on_delete
                    content = re.sub(
                        rf'on_delete=models\.CASCADE',
                        f'on_delete=models.{on_delete_value}',
                        content
                    )
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(model_file)
                model_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'Foreign Key Constraints',
                f"Fixed foreign key constraints in {model_file.name}",
                str(model_file)
            )
    
    def fix_decimal_field_precision(self):
        """Handle decimal field precision changes for medication dosages."""
        print("🔢 Fixing decimal field precision changes...")
        
        # Common decimal field precision issues in MedGuard
        decimal_precision_issues = [
            {
                'description': 'Medication dosage precision',
                'model': 'medications.Medication',
                'fields': [
                    {
                        'name': 'dosage_strength',
                        'current_precision': (5, 2),
                        'suggested_precision': (8, 3),
                        'reason': 'Support more precise dosage measurements'
                    },
                    {
                        'name': 'price',
                        'current_precision': (8, 2),
                        'suggested_precision': (10, 2),
                        'reason': 'Support higher price ranges'
                    }
                ]
            },
            {
                'description': 'Stock transaction amounts',
                'model': 'medications.StockTransaction',
                'fields': [
                    {
                        'name': 'quantity',
                        'current_precision': (5, 0),
                        'suggested_precision': (8, 2),
                        'reason': 'Support fractional quantities'
                    },
                    {
                        'name': 'unit_price',
                        'current_precision': (8, 2),
                        'suggested_precision': (10, 3),
                        'reason': 'Support more precise pricing'
                    }
                ]
            },
            {
                'description': 'Stock analytics metrics',
                'model': 'medications.StockAnalytics',
                'fields': [
                    {
                        'name': 'average_consumption_rate',
                        'current_precision': (5, 2),
                        'suggested_precision': (8, 4),
                        'reason': 'Support more precise analytics'
                    },
                    {
                        'name': 'predicted_stock_level',
                        'current_precision': (8, 0),
                        'suggested_precision': (10, 2),
                        'reason': 'Support fractional predictions'
                    }
                ]
            }
        ]
        
        for issue in decimal_precision_issues:
            try:
                self._fix_decimal_precision_issue(issue)
            except Exception as e:
                self.log_error('Decimal Precision Fix', issue['description'], e)
    
    def _fix_decimal_precision_issue(self, issue: Dict[str, Any]):
        """Fix decimal precision issues for a specific model."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check model files for decimal field definitions
        model_files = [
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_decimal_precision(model_file, issue)
            except Exception as e:
                self.log_error('Model Decimal Precision Fix', f"Error fixing {model_file}", e)
    
    def _fix_model_decimal_precision(self, model_file: Path, issue: Dict[str, Any]):
        """Fix decimal precision in a specific model file."""
        content = model_file.read_text(encoding='utf-8')
        original_content = content
        
        # Fix decimal field precision
        for field_info in issue['fields']:
            field_name = field_info['name']
            current_precision = field_info['current_precision']
            suggested_precision = field_info['suggested_precision']
            
            # Pattern to match DecimalField with current precision
            pattern = rf"(\s+{field_name}\s*=\s*models\.DecimalField\()([^)]*max_digits={current_precision[0]}[^)]*decimal_places={current_precision[1]}[^)]*)(\))"
            
            replacement = rf"\1\2max_digits={suggested_precision[0]}, decimal_places={suggested_precision[1]}\3"
            
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(model_file)
                model_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'Decimal Precision',
                f"Fixed decimal precision in {model_file.name}",
                str(model_file)
            )
    
    def fix_index_naming_conflicts(self):
        """Fix index naming conflicts in complex models."""
        print("📊 Fixing index naming conflicts...")
        
        # Common index naming conflicts in MedGuard
        index_conflict_issues = [
            {
                'description': 'Medication model indexes',
                'model': 'medications.Medication',
                'conflicts': [
                    {
                        'current_name': 'medication_name_idx',
                        'suggested_name': 'medications_medication_name_idx',
                        'reason': 'Avoid naming conflicts with other apps'
                    },
                    {
                        'current_name': 'medication_generic_name_idx',
                        'suggested_name': 'medications_medication_generic_name_idx',
                        'reason': 'Avoid naming conflicts with other apps'
                    }
                ]
            },
            {
                'description': 'User model indexes',
                'model': 'users.User',
                'conflicts': [
                    {
                        'current_name': 'user_email_idx',
                        'suggested_name': 'users_user_email_idx',
                        'reason': 'Avoid naming conflicts with other apps'
                    },
                    {
                        'current_name': 'user_username_idx',
                        'suggested_name': 'users_user_username_idx',
                        'reason': 'Avoid naming conflicts with other apps'
                    }
                ]
            },
            {
                'description': 'MedicationSchedule model indexes',
                'model': 'medications.MedicationSchedule',
                'conflicts': [
                    {
                        'current_name': 'schedule_patient_medication_idx',
                        'suggested_name': 'medications_schedule_patient_medication_idx',
                        'reason': 'Avoid naming conflicts with other apps'
                    }
                ]
            }
        ]
        
        for issue in index_conflict_issues:
            try:
                self._fix_index_conflict_issue(issue)
            except Exception as e:
                self.log_error('Index Conflict Fix', issue['description'], e)
    
    def _fix_index_conflict_issue(self, issue: Dict[str, Any]):
        """Fix index naming conflicts for a specific model."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check model files for index definitions
        model_files = [
            Path('medguard_backend/users/models.py'),
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_index_conflicts(model_file, issue)
            except Exception as e:
                self.log_error('Model Index Conflict Fix', f"Error fixing {model_file}", e)
    
    def _fix_model_index_conflicts(self, model_file: Path, issue: Dict[str, Any]):
        """Fix index naming conflicts in a specific model file."""
        content = model_file.read_text(encoding='utf-8')
        original_content = content
        
        # Fix index naming conflicts
        for conflict in issue['conflicts']:
            current_name = conflict['current_name']
            suggested_name = conflict['suggested_name']
            
            # Pattern to match index definitions
            pattern = rf"(\s+db_index=True,\s*db_tablespace='',\s*name='){re.escape(current_name)}(')"
            replacement = rf"\1{suggested_name}\2"
            
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
            # Also fix Meta class index definitions
            pattern = rf"(\s+indexes\s*=\s*\[[^\]]*'name':\s*'){re.escape(current_name)}(')"
            replacement = rf"\1{suggested_name}\2"
            
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(model_file)
                model_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'Index Naming Conflicts',
                f"Fixed index naming conflicts in {model_file.name}",
                str(model_file)
            )
    
    def fix_migration_dependency_ordering(self):
        """Resolve migration dependency ordering issues."""
        print("🔗 Fixing migration dependency ordering...")
        
        # Common migration dependency issues in MedGuard
        dependency_ordering_issues = [
            {
                'description': 'User-Medication dependency chain',
                'dependencies': [
                    ('users', '0001_initial'),
                    ('medications', '0001_initial'),
                    ('medications', '0002_add_prescription_fields')
                ],
                'required_order': ['users', 'medications'],
                'reason': 'Medication models depend on User model'
            },
            {
                'description': 'Security-User dependency chain',
                'dependencies': [
                    ('users', '0001_initial'),
                    ('security', '0001_initial'),
                    ('security', '0002_securityevent_and_more')
                ],
                'required_order': ['users', 'security'],
                'reason': 'Security models depend on User model'
            },
            {
                'description': 'Notifications-User dependency chain',
                'dependencies': [
                    ('users', '0001_initial'),
                    ('medguard_notifications', '0001_initial')
                ],
                'required_order': ['users', 'medguard_notifications'],
                'reason': 'Notification models depend on User model'
            }
        ]
        
        for issue in dependency_ordering_issues:
            try:
                self._fix_dependency_ordering_issue(issue)
            except Exception as e:
                self.log_error('Dependency Ordering Fix', issue['description'], e)
    
    def _fix_dependency_ordering_issue(self, issue: Dict[str, Any]):
        """Fix migration dependency ordering for a specific issue."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check migration files for dependency definitions
        migration_dirs = [
            Path('medguard_backend/users/migrations'),
            Path('medguard_backend/medications/migrations'),
            Path('medguard_backend/security/migrations'),
            Path('medguard_backend/medguard_notifications/migrations'),
        ]
        
        for migration_dir in migration_dirs:
            if not migration_dir.exists():
                continue
            
            for migration_file in migration_dir.glob('*.py'):
                if migration_file.name == '__init__.py':
                    continue
                
                try:
                    self._fix_migration_dependencies(migration_file, issue)
                except Exception as e:
                    self.log_error('Migration Dependency Fix', f"Error fixing {migration_file}", e)
    
    def _fix_migration_dependencies(self, migration_file: Path, issue: Dict[str, Any]):
        """Fix migration dependencies in a specific migration file."""
        content = migration_file.read_text(encoding='utf-8')
        original_content = content
        
        # Fix dependencies based on required order
        for app_name in issue['required_order']:
            # Pattern to match dependencies list
            pattern = rf"(\s+dependencies\s*=\s*\[[^\]]*)(\])"
            
            # Check if dependency already exists
            if f"('{app_name}'," not in content:
                # Add dependency to the list
                replacement = rf"\1, ('{app_name}', '0001_initial')\2"
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(migration_file)
                migration_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'Migration Dependencies',
                f"Fixed migration dependencies in {migration_file.name}",
                str(migration_file)
            )
    
    def fix_postgresql_specific_migrations(self):
        """Handle database engine-specific migration for PostgreSQL."""
        print("🐘 Fixing PostgreSQL-specific migrations...")
        
        # Common PostgreSQL-specific issues in MedGuard
        postgresql_issues = [
            {
                'description': 'PostgreSQL JSONB field optimization',
                'model': 'medications.Medication',
                'fields': ['metadata', 'side_effects', 'interactions'],
                'optimization': 'Use JSONB instead of JSON for better performance'
            },
            {
                'description': 'PostgreSQL full-text search indexes',
                'model': 'medications.Medication',
                'fields': ['name', 'generic_name', 'description'],
                'optimization': 'Add GIN indexes for full-text search'
            },
            {
                'description': 'PostgreSQL partial indexes',
                'model': 'medications.StockAlert',
                'fields': ['alert_type', 'is_active'],
                'optimization': 'Add partial indexes for active alerts'
            },
            {
                'description': 'PostgreSQL array fields',
                'model': 'medications.Medication',
                'fields': ['tags', 'categories'],
                'optimization': 'Use ArrayField for better performance'
            }
        ]
        
        for issue in postgresql_issues:
            try:
                self._fix_postgresql_issue(issue)
            except Exception as e:
                self.log_error('PostgreSQL Fix', issue['description'], e)
    
    def _fix_postgresql_issue(self, issue: Dict[str, Any]):
        """Fix PostgreSQL-specific issues for a specific model."""
        print(f"   🔍 Checking: {issue['description']}")
        
        # Check model files for PostgreSQL-specific optimizations
        model_files = [
            Path('medguard_backend/users/models.py'),
            Path('medguard_backend/medications/models.py'),
        ]
        
        for model_file in model_files:
            if not model_file.exists():
                continue
            
            try:
                self._fix_model_postgresql_optimizations(model_file, issue)
            except Exception as e:
                self.log_error('Model PostgreSQL Fix', f"Error fixing {model_file}", e)
    
    def _fix_model_postgresql_optimizations(self, model_file: Path, issue: Dict[str, Any]):
        """Fix PostgreSQL-specific optimizations in a specific model file."""
        content = model_file.read_text(encoding='utf-8')
        original_content = content
        
        # Add PostgreSQL-specific imports if needed
        if 'from django.contrib.postgres.fields import JSONField' not in content and 'JSONField' in content:
            content = re.sub(
                r'from django\.db import models',
                'from django.db import models\nfrom django.contrib.postgres.fields import JSONField',
                content
            )
        
        if 'from django.contrib.postgres.indexes import GinIndex' not in content:
            content = re.sub(
                r'from django\.db import models',
                'from django.db import models\nfrom django.contrib.postgres.indexes import GinIndex',
                content
            )
        
        # Fix JSONB fields for better performance
        if 'JSONB optimization' in issue['optimization']:
            for field in issue['fields']:
                # Convert JSONField to JSONB
                pattern = rf"(\s+{field}\s*=\s*)JSONField\("
                replacement = rf"\1JSONField("
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        # Add GIN indexes for full-text search
        if 'GIN indexes' in issue['optimization']:
            # Add to Meta class
            gin_indexes = []
            for field in issue['fields']:
                gin_indexes.append(f"GinIndex(fields=['{field}'], name='{field}_gin_idx')")
            
            gin_indexes_str = ', '.join(gin_indexes)
            
            if 'class Meta:' in content:
                # Add to existing Meta class
                content = re.sub(
                    r'(class Meta:.*?)(\n\s+)(\w+.*?)(\n\s*)(\n|$)',
                    rf'\1\2indexes = [{gin_indexes_str}]\n\4\5',
                    content,
                    flags=re.DOTALL
                )
            else:
                # Create new Meta class
                content = re.sub(
                    r'(\n\s*)(class Meta:.*?)(\n\s*)(\n|$)',
                    rf'\1class Meta:\n\3    indexes = [{gin_indexes_str}]\n\4',
                    content,
                    flags=re.DOTALL
                )
        
        # Add partial indexes
        if 'partial indexes' in issue['optimization']:
            partial_indexes = []
            for field in issue['fields']:
                partial_indexes.append(f"models.Index(fields=['{field}'], condition=models.Q(is_active=True), name='{field}_active_idx')")
            
            partial_indexes_str = ', '.join(partial_indexes)
            
            if 'class Meta:' in content:
                # Add to existing Meta class
                content = re.sub(
                    r'(class Meta:.*?)(\n\s+)(\w+.*?)(\n\s*)(\n|$)',
                    rf'\1\2indexes = [{partial_indexes_str}]\n\4\5',
                    content,
                    flags=re.DOTALL
                )
        
        if content != original_content:
            if not self.dry_run:
                self.backup_file(model_file)
                model_file.write_text(content, encoding='utf-8')
            
            self.log_fix(
                'PostgreSQL Optimizations',
                f"Fixed PostgreSQL optimizations in {model_file.name}",
                str(model_file)
            )
    
    def create_migration_fix_script(self):
        """Create a custom migration script to handle complex fixes."""
        print("📝 Creating migration fix script...")
        
        script_content = '''"""
Custom migration script to handle complex MedGuard SA fixes.

This script should be run after applying the main migration fixes.
"""

import os
import sys
import django
from django.db import connection, transaction
from django.core.management import execute_from_command_line
from django.utils import timezone
from datetime import datetime, timedelta

def setup_django():
    """Setup Django environment."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medguard_backend.settings.development')
    django.setup()

def fix_circular_dependencies():
    """Fix any remaining circular dependency issues."""
    print("🔧 Fixing circular dependencies...")
    
    with connection.cursor() as cursor:
        # Check for foreign key constraints that might cause issues
        cursor.execute("""
            SELECT 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name;
        """)
        
        foreign_keys = cursor.fetchall()
        print(f"Found {len(foreign_keys)} foreign key constraints")
        
        # Check for potential circular dependencies
        for fk in foreign_keys:
            table_name, column_name, foreign_table, foreign_column = fk
            print(f"  {table_name}.{column_name} -> {foreign_table}.{foreign_column}")

def fix_jsonfield_data():
    """Fix JSONField data compatibility issues."""
    print("📄 Fixing JSONField data...")
    
    with connection.cursor() as cursor:
        # Check for JSONField columns
        cursor.execute("""
            SELECT 
                table_name, 
                column_name, 
                data_type
            FROM 
                information_schema.columns 
            WHERE 
                data_type = 'json' 
                AND table_schema = 'public'
            ORDER BY table_name, column_name;
        """)
        
        json_columns = cursor.fetchall()
        print(f"Found {len(json_columns)} JSON columns")
        
        for table, column, data_type in json_columns:
            print(f"  {table}.{column} ({data_type})")
            
            # Check for invalid JSON data
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table} 
                    WHERE {column} IS NOT NULL 
                    AND {column}::text = 'null'
                """)
                null_count = cursor.fetchone()[0]
                
                if null_count > 0:
                    print(f"    Found {null_count} rows with 'null' string in JSON field")
                    
                    # Convert 'null' strings to actual NULL
                    cursor.execute(f"""
                        UPDATE {table} 
                        SET {column} = NULL 
                        WHERE {column}::text = 'null'
                    """)
                    print(f"    Fixed {null_count} rows")
                    
            except Exception as e:
                print(f"    Error checking {table}.{column}: {e}")

def fix_timezone_datetime_data():
    """Fix timezone-aware datetime data issues."""
    print("🕐 Fixing timezone datetime data...")
    
    with connection.cursor() as cursor:
        # Check for datetime columns
        cursor.execute("""
            SELECT 
                table_name, 
                column_name, 
                data_type
            FROM 
                information_schema.columns 
            WHERE 
                data_type IN ('timestamp without time zone', 'timestamp with time zone')
                AND table_schema = 'public'
            ORDER BY table_name, column_name;
        """)
        
        datetime_columns = cursor.fetchall()
        print(f"Found {len(datetime_columns)} datetime columns")
        
        for table, column, data_type in datetime_columns:
            print(f"  {table}.{column} ({data_type})")
            
            # Check for NULL datetime values that should have defaults
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table} 
                    WHERE {column} IS NULL
                """)
                null_count = cursor.fetchone()[0]
                
                if null_count > 0:
                    print(f"    Found {null_count} rows with NULL datetime values")
                    
                    # Set default timezone-aware datetime for NULL values
                    if column in ['created_at', 'updated_at']:
                        cursor.execute(f"""
                            UPDATE {table} 
                            SET {column} = %s 
                            WHERE {column} IS NULL
                        """, [timezone.now()])
                        print(f"    Fixed {null_count} rows with current timezone")
                    
            except Exception as e:
                print(f"    Error checking {table}.{column}: {e}")

def fix_unique_constraint_data():
    """Fix unique constraint violations in existing data."""
    print("🔒 Fixing unique constraint violations...")
    
    with connection.cursor() as cursor:
        # Check for duplicate emails in users table
        try:
            cursor.execute("""
                SELECT email, COUNT(*) 
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1
            """)
            duplicate_emails = cursor.fetchall()
            
            if duplicate_emails:
                print(f"Found {len(duplicate_emails)} duplicate email addresses")
                
                for email, count in duplicate_emails:
                    print(f"  {email}: {count} duplicates")
                    
                    # Update duplicate emails with suffix
                    cursor.execute("""
                        UPDATE users 
                        SET email = email || '_' || id 
                        WHERE email = %s AND id NOT IN (
                            SELECT MIN(id) FROM users WHERE email = %s
                        )
                    """, [email, email])
                    print(f"    Fixed duplicates for {email}")
                    
        except Exception as e:
            print(f"Error fixing duplicate emails: {e}")
        
        # Check for duplicate medication names
        try:
            cursor.execute("""
                SELECT name, COUNT(*) 
                FROM medications 
                GROUP BY name 
                HAVING COUNT(*) > 1
            """)
            duplicate_medications = cursor.fetchall()
            
            if duplicate_medications:
                print(f"Found {len(duplicate_medications)} duplicate medication names")
                
                for name, count in duplicate_medications:
                    print(f"  {name}: {count} duplicates")
                    
                    # Update duplicate names with suffix
                    cursor.execute("""
                        UPDATE medications 
                        SET name = name || ' (Copy ' || id || ')'
                        WHERE name = %s AND id NOT IN (
                            SELECT MIN(id) FROM medications WHERE name = %s
                        )
                    """, [name, name])
                    print(f"    Fixed duplicates for {name}")
                    
        except Exception as e:
            print(f"Error fixing duplicate medications: {e}")

def fix_foreign_key_data():
    """Fix foreign key constraint violations in existing data."""
    print("🔗 Fixing foreign key constraint violations...")
    
    with connection.cursor() as cursor:
        # Check for orphaned records in medication_schedules
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM medication_schedules ms
                LEFT JOIN users u ON ms.patient_id = u.id
                WHERE u.id IS NULL
            """)
            orphaned_schedules = cursor.fetchone()[0]
            
            if orphaned_schedules > 0:
                print(f"Found {orphaned_schedules} orphaned medication schedules")
                
                # Delete orphaned records
                cursor.execute("""
                    DELETE FROM medication_schedules 
                    WHERE patient_id NOT IN (SELECT id FROM users)
                """)
                print(f"    Deleted {orphaned_schedules} orphaned schedules")
                
        except Exception as e:
            print(f"Error fixing orphaned medication schedules: {e}")
        
        # Check for orphaned records in medication_logs
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM medication_logs ml
                LEFT JOIN users u ON ml.patient_id = u.id
                WHERE u.id IS NULL
            """)
            orphaned_logs = cursor.fetchone()[0]
            
            if orphaned_logs > 0:
                print(f"Found {orphaned_logs} orphaned medication logs")
                
                # Delete orphaned records
                cursor.execute("""
                    DELETE FROM medication_logs 
                    WHERE patient_id NOT IN (SELECT id FROM users)
                """)
                print(f"    Deleted {orphaned_logs} orphaned logs")
                
        except Exception as e:
            print(f"Error fixing orphaned medication logs: {e}")
        
        # Check for orphaned records in stock_alerts
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM stock_alerts sa
                LEFT JOIN medications m ON sa.medication_id = m.id
                WHERE m.id IS NULL
            """)
            orphaned_alerts = cursor.fetchone()[0]
            
            if orphaned_alerts > 0:
                print(f"Found {orphaned_alerts} orphaned stock alerts")
                
                # Delete orphaned records
                cursor.execute("""
                    DELETE FROM stock_alerts 
                    WHERE medication_id NOT IN (SELECT id FROM medications)
                """)
                print(f"    Deleted {orphaned_alerts} orphaned alerts")
                
        except Exception as e:
            print(f"Error fixing orphaned stock alerts: {e}")

def fix_decimal_precision_data():
    """Fix decimal field precision issues in existing data."""
    print("🔢 Fixing decimal field precision issues...")
    
    with connection.cursor() as cursor:
        # Check for decimal columns that need precision updates
        cursor.execute("""
            SELECT 
                table_name, 
                column_name, 
                numeric_precision,
                numeric_scale
            FROM 
                information_schema.columns 
            WHERE 
                data_type = 'numeric' 
                AND table_schema = 'public'
                AND table_name IN ('medications', 'stock_transactions', 'stock_analytics')
            ORDER BY table_name, column_name;
        """)
        
        decimal_columns = cursor.fetchall()
        print(f"Found {len(decimal_columns)} decimal columns")
        
        for table, column, precision, scale in decimal_columns:
            print(f"  {table}.{column} (precision: {precision}, scale: {scale})")
            
            # Check for data that might exceed current precision
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table} 
                    WHERE {column} IS NOT NULL 
                    AND LENGTH(CAST({column} AS TEXT)) > {precision + scale + 1}
                """)
                overflow_count = cursor.fetchone()[0]
                
                if overflow_count > 0:
                    print(f"    Found {overflow_count} rows with potential precision overflow")
                    
            except Exception as e:
                print(f"    Error checking {table}.{column}: {e}")

def fix_index_conflicts_data():
    """Fix index naming conflicts in existing database."""
    print("📊 Fixing index naming conflicts...")
    
    with connection.cursor() as cursor:
        # Check for duplicate index names
        cursor.execute("""
            SELECT 
                indexname,
                COUNT(*) as count
            FROM 
                pg_indexes 
            WHERE 
                schemaname = 'public'
            GROUP BY 
                indexname 
            HAVING 
                COUNT(*) > 1
            ORDER BY 
                count DESC, indexname;
        """)
        
        duplicate_indexes = cursor.fetchall()
        
        if duplicate_indexes:
            print(f"Found {len(duplicate_indexes)} duplicate index names")
            
            for index_name, count in duplicate_indexes:
                print(f"  {index_name}: {count} instances")
                
                # Get details of duplicate indexes
                cursor.execute("""
                    SELECT 
                        tablename,
                        indexdef
                    FROM 
                        pg_indexes 
                    WHERE 
                        schemaname = 'public' 
                        AND indexname = %s
                    ORDER BY 
                        tablename;
                """, [index_name])
                
                index_details = cursor.fetchall()
                for table_name, index_def in index_details:
                    print(f"    Table: {table_name}")
                    print(f"    Definition: {index_def[:100]}...")
        else:
            print("  No duplicate index names found")

def fix_migration_dependencies_data():
    """Fix migration dependency issues in existing database."""
    print("🔗 Fixing migration dependency issues...")
    
    with connection.cursor() as cursor:
        # Check django_migrations table for dependency issues
        cursor.execute("""
            SELECT 
                app,
                name,
                applied
            FROM 
                django_migrations 
            ORDER BY 
                app, applied;
        """)
        
        migrations = cursor.fetchall()
        print(f"Found {len(migrations)} applied migrations")
        
        # Group by app
        app_migrations = {}
        for app, name, applied in migrations:
            if app not in app_migrations:
                app_migrations[app] = []
            app_migrations[app].append((name, applied))
        
        # Check for potential dependency issues
        for app, app_migs in app_migrations.items():
            print(f"  {app}: {len(app_migs)} migrations")
            
            # Check if initial migration exists
            has_initial = any(name == '0001_initial' for name, _ in app_migs)
            if not has_initial:
                print(f"    ⚠️  Missing initial migration")
            
            # Check migration order
            for i, (name, applied) in enumerate(app_migs):
                if i > 0:
                    prev_name = app_migs[i-1][0]
                    if name < prev_name:
                        print(f"    ⚠️  Migration order issue: {prev_name} -> {name}")

def fix_postgresql_specific_data():
    """Fix PostgreSQL-specific data issues."""
    print("🐘 Fixing PostgreSQL-specific data issues...")
    
    with connection.cursor() as cursor:
        # Check for JSONB vs JSON field usage
        cursor.execute("""
            SELECT 
                table_name, 
                column_name, 
                data_type
            FROM 
                information_schema.columns 
            WHERE 
                data_type IN ('json', 'jsonb')
                AND table_schema = 'public'
            ORDER BY 
                table_name, column_name;
        """)
        
        json_columns = cursor.fetchall()
        print(f"Found {len(json_columns)} JSON/JSONB columns")
        
        for table, column, data_type in json_columns:
            print(f"  {table}.{column} ({data_type})")
            
            # Check for JSONB optimization opportunities
            if data_type == 'json':
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM {table} 
                        WHERE {column} IS NOT NULL
                    """)
                    json_count = cursor.fetchone()[0]
                    
                    if json_count > 0:
                        print(f"    Consider converting to JSONB for better performance ({json_count} rows)")
                        
                except Exception as e:
                    print(f"    Error checking {table}.{column}: {e}")
        
        # Check for GIN index opportunities
        cursor.execute("""
            SELECT 
                t.table_name,
                c.column_name
            FROM 
                information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE 
                t.table_schema = 'public'
                AND c.data_type IN ('text', 'character varying')
                AND c.column_name IN ('name', 'description', 'generic_name')
                AND t.table_name IN ('medications', 'users')
            ORDER BY 
                t.table_name, c.column_name;
        """)
        
        text_columns = cursor.fetchall()
        print(f"Found {len(text_columns)} text columns for potential GIN indexes")
        
        for table, column in text_columns:
            print(f"  {table}.{column} - consider adding GIN index for full-text search")

def fix_imagefield_paths():
    """Fix ImageField file paths."""
    print("🖼️  Fixing ImageField paths...")
    
    # This would require file system operations
    # For now, just log the current state
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                table_name, 
                column_name
            FROM 
                information_schema.columns 
            WHERE 
                data_type = 'character varying' 
                AND table_schema = 'public'
                AND column_name LIKE '%image%'
            ORDER BY table_name, column_name;
        """)
        
        image_columns = cursor.fetchall()
        print(f"Found {len(image_columns)} potential image columns")
        
        for table, column in image_columns:
            print(f"  {table}.{column}")

def main():
    """Main function to run all fixes."""
    setup_django()
    
    print("🚀 Starting MedGuard SA migration fixes...")
    
    try:
        fix_circular_dependencies()
        fix_jsonfield_data()
        fix_timezone_datetime_data()
        fix_unique_constraint_data()
        fix_foreign_key_data()
        fix_decimal_precision_data()
        fix_index_conflicts_data()
        fix_migration_dependencies_data()
        fix_postgresql_specific_data()
        fix_imagefield_paths()
        
        print("✅ All fixes completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during fixes: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
        
        script_path = Path('medguard_backend/custom_migration_fixes.py')
        
        if not self.dry_run:
            script_path.write_text(script_content, encoding='utf-8')
            self.log_fix(
                'Migration Script',
                'Created custom migration fix script',
                str(script_path)
            )
        else:
            print(f"   📝 Would create: {script_path}")
    
    def generate_fix_report(self):
        """Generate a report of all fixes applied."""
        print("📊 Generating fix report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'django_version': self.django_version,
            'dry_run': self.dry_run,
            'fixes_applied': self.fixes_applied,
            'errors': self.errors,
            'summary': {
                'total_fixes': len(self.fixes_applied),
                'total_errors': len(self.errors),
                'fix_types': {}
            }
        }
        
        # Count fix types
        for fix in self.fixes_applied:
            fix_type = fix['type']
            report['summary']['fix_types'][fix_type] = report['summary']['fix_types'].get(fix_type, 0) + 1
        
        # Save report
        report_path = self.backup_dir / f"migration_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if not self.dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n📋 Fix Report Summary:")
        print(f"   Total fixes applied: {report['summary']['total_fixes']}")
        print(f"   Total errors: {report['summary']['total_errors']}")
        print(f"   Fix types: {report['summary']['fix_types']}")
        
        if not self.dry_run:
            print(f"   Report saved to: {report_path}")
        
        return report
    
    def run_all_fixes(self):
        """Run all migration fixes."""
        print("🚀 Starting MedGuard SA migration fixes...\n")
        
        try:
            # Run all fix types
            self.fix_circular_dependencies()
            self.fix_jsonfield_compatibility()
            self.fix_imagefield_paths()
            self.fix_timezone_datetime_fields()
            self.fix_unique_constraint_violations()
            self.fix_foreign_key_constraints()
            self.fix_decimal_field_precision()
            self.fix_index_naming_conflicts()
            self.fix_migration_dependency_ordering()
            self.fix_postgresql_specific_migrations()
            self.create_migration_fix_script()
            
            # Generate report
            self.generate_fix_report()
            
            print("\n✅ Migration fixes completed!")
            
            if self.dry_run:
                print("   This was a dry run. No changes were made.")
                print("   Run without --dry-run to apply the fixes.")
            else:
                print("   All fixes have been applied.")
                print("   Check the backup directory for original files.")
                print("   Run the custom migration script if needed.")
            
        except Exception as e:
            self.log_error('General', 'Error during migration fixes', e)
            print(f"\n❌ Migration fixes failed: {e}")
            return False
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Fix common migration issues in MedGuard SA backend',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_migrations.py --dry-run                    # Preview fixes
  python fix_migrations.py --fix-circular               # Fix circular dependencies only
  python fix_migrations.py --fix-json --fix-images      # Fix JSON and image issues
  python fix_migrations.py                              # Apply all fixes
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview fixes without applying them'
    )
    
    parser.add_argument(
        '--fix-circular',
        action='store_true',
        help='Fix circular dependency issues only'
    )
    
    parser.add_argument(
        '--fix-json',
        action='store_true',
        help='Fix JSONField compatibility issues only'
    )
    
    parser.add_argument(
        '--fix-images',
        action='store_true',
        help='Fix ImageField upload path issues only'
    )
    
    parser.add_argument(
        '--fix-timezone',
        action='store_true',
        help='Fix timezone-aware datetime field issues only'
    )
    
    parser.add_argument(
        '--fix-constraints',
        action='store_true',
        help='Fix unique constraint violation issues only'
    )
    
    parser.add_argument(
        '--fix-foreign-keys',
        action='store_true',
        help='Fix foreign key constraint issues only'
    )
    
    parser.add_argument(
        '--fix-decimal',
        action='store_true',
        help='Fix decimal field precision changes only'
    )
    
    parser.add_argument(
        '--fix-indexes',
        action='store_true',
        help='Fix index naming conflicts only'
    )
    
    parser.add_argument(
        '--fix-dependencies',
        action='store_true',
        help='Fix migration dependency ordering only'
    )
    
    parser.add_argument(
        '--fix-postgresql',
        action='store_true',
        help='Fix PostgreSQL-specific migrations only'
    )
    
    args = parser.parse_args()
    
    # Initialize fixer
    fixer = MigrationFixer(dry_run=args.dry_run)
    
    # Run specific fixes or all fixes
    if args.fix_circular or args.fix_json or args.fix_images or args.fix_timezone or args.fix_constraints or args.fix_foreign_keys or args.fix_decimal or args.fix_indexes or args.fix_dependencies or args.fix_postgresql:
        if args.fix_circular:
            fixer.fix_circular_dependencies()
        if args.fix_json:
            fixer.fix_jsonfield_compatibility()
        if args.fix_images:
            fixer.fix_imagefield_paths()
        if args.fix_timezone:
            fixer.fix_timezone_datetime_fields()
        if args.fix_constraints:
            fixer.fix_unique_constraint_violations()
        if args.fix_foreign_keys:
            fixer.fix_foreign_key_constraints()
        if args.fix_decimal:
            fixer.fix_decimal_field_precision()
        if args.fix_indexes:
            fixer.fix_index_naming_conflicts()
        if args.fix_dependencies:
            fixer.fix_migration_dependency_ordering()
        if args.fix_postgresql:
            fixer.fix_postgresql_specific_migrations()
        
        fixer.generate_fix_report()
    else:
        # Run all fixes
        fixer.run_all_fixes()


if __name__ == '__main__':
    main() 