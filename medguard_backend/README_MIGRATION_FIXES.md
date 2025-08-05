# MedGuard SA Migration Fix Script

This script handles common migration issues in the MedGuard SA backend, specifically designed to resolve:

1. **Circular dependency issues** between User and Medication models
2. **JSONField compatibility issues** across different Django versions (4.x and 5.x)
3. **ImageField upload_to path conflicts** that can cause file organization issues
4. **Timezone-aware datetime field migrations** for proper timezone handling
5. **Unique constraint violations** during data migration
6. **Foreign key constraint issues** with existing data
7. **Decimal field precision changes** for medication dosages
8. **Index naming conflicts** in complex models
9. **Migration dependency ordering issues** between apps
10. **Database engine-specific migrations** for PostgreSQL

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Django 4.x or 5.x
- PostgreSQL database
- MedGuard SA backend setup

### Basic Usage

```bash
# Preview all fixes without applying them
python fix_migrations.py --dry-run

# Apply all fixes
python fix_migrations.py

# Fix specific issues only
python fix_migrations.py --fix-circular
python fix_migrations.py --fix-json
python fix_migrations.py --fix-images
python fix_migrations.py --fix-timezone
python fix_migrations.py --fix-constraints
python fix_migrations.py --fix-foreign-keys
python fix_migrations.py --fix-decimal
python fix_migrations.py --fix-indexes
python fix_migrations.py --fix-dependencies
python fix_migrations.py --fix-postgresql
```

## 📋 What the Script Fixes

### 1. Circular Dependencies

**Problem**: Django migrations can fail when models reference each other in a circular manner.

**Examples in MedGuard**:
- `User` → `MedicationSchedule` → `User`
- `Medication` → `StockAlert` → `User`
- `User` → `PrescriptionRenewal` → `Medication`

**Solution**: Converts direct model references to string references in foreign keys.

**Before**:
```python
patient = models.ForeignKey(User, on_delete=models.CASCADE)
```

**After**:
```python
patient = models.ForeignKey('users.User', on_delete=models.CASCADE)
```

### 2. JSONField Compatibility

**Problem**: JSONField implementation differs between Django versions.

**Django 4.x**: Uses `django.contrib.postgres.fields.JSONField`
**Django 5.x**: Uses `django.db.models.JSONField`

**Solution**: Automatically detects Django version and applies appropriate imports and field definitions.

**Django 4.x**:
```python
from django.contrib.postgres.fields import JSONField
notification_preferences = JSONField(default=dict)
```

**Django 5.x**:
```python
notification_preferences = models.JSONField(default=dict)
```

### 3. ImageField Upload Paths

**Problem**: Image upload paths can conflict or become disorganized.

**Current Issues**:
- Avatar images: `avatars/%Y/%m/%d/` → `users/avatars/%Y/%m/%d/`
- Medication images: `medications/images/` → `medications/images/%Y/%m/%d/`

**Solution**: Organizes upload paths with proper date-based subdirectories and app-specific prefixes.

### 4. Timezone-Aware Datetime Fields

**Problem**: Django datetime fields may not be timezone-aware, causing issues with timezone handling.

**Examples in MedGuard**:
- `created_at` and `updated_at` fields without timezone awareness
- `scheduled_time` and `actual_time` in medication logs
- `last_login` timestamps

**Solution**: Adds proper timezone imports and ensures datetime fields use `timezone.now()` for defaults.

**Before**:
```python
created_at = models.DateTimeField(auto_now_add=True)
```

**After**:
```python
from django.utils import timezone
created_at = models.DateTimeField(auto_now_add=True, default=timezone.now)
```

### 5. Unique Constraint Violations

**Problem**: Data migration can fail due to unique constraint violations from duplicate data.

**Examples in MedGuard**:
- Duplicate email addresses in User model
- Duplicate medication names
- Duplicate prescription numbers

**Solution**: Automatically resolves duplicates by appending suffixes or generating new values.

**Strategies**:
- **Update duplicates**: Modify existing records to resolve conflicts
- **Append suffix**: Add unique identifiers to duplicate values
- **Generate new number**: Create new unique identifiers for prescriptions

### 6. Foreign Key Constraint Issues

**Problem**: Foreign key relationships can have constraint violations with existing data.

**Examples in MedGuard**:
- Orphaned medication schedules referencing deleted users
- Orphaned medication logs with invalid patient references
- Stock alerts referencing deleted medications

**Solution**: Configures appropriate `on_delete` behaviors and cleans up orphaned records.

**Resolution Strategies**:
- **CASCADE**: Delete related records when parent is deleted
- **PROTECT**: Prevent deletion of parent if related records exist
- **SET_NULL**: Set foreign key to NULL when parent is deleted
- **SET_DEFAULT**: Set foreign key to default value when parent is deleted

### 7. Decimal Field Precision Changes

**Problem**: Medication dosage fields may need higher precision for accurate measurements.

**Examples in MedGuard**:
- `dosage_strength`: (5,2) → (8,3) for more precise measurements
- `price`: (8,2) → (10,2) for higher price ranges
- `quantity`: (5,0) → (8,2) for fractional quantities

**Solution**: Updates `DecimalField` precision and scale parameters.

**Before**:
```python
dosage_strength = models.DecimalField(max_digits=5, decimal_places=2)
```

**After**:
```python
dosage_strength = models.DecimalField(max_digits=8, decimal_places=3)
```

### 8. Index Naming Conflicts

**Problem**: Index names can conflict between different apps in complex Django projects.

**Examples in MedGuard**:
- `medication_name_idx` → `medications_medication_name_idx`
- `user_email_idx` → `users_user_email_idx`
- `schedule_patient_medication_idx` → `medications_schedule_patient_medication_idx`

**Solution**: Prefixes index names with app names to avoid conflicts.

**Before**:
```python
name = 'medication_name_idx'
```

**After**:
```python
name = 'medications_medication_name_idx'
```

### 9. Migration Dependency Ordering

**Problem**: Migrations may not have proper dependencies, causing ordering issues.

**Examples in MedGuard**:
- `medications` app depends on `users` app
- `security` app depends on `users` app
- `medguard_notifications` app depends on `users` app

**Solution**: Ensures proper migration dependencies are declared.

**Before**:
```python
dependencies = []
```

**After**:
```python
dependencies = [
    ('users', '0001_initial'),
]
```

### 10. PostgreSQL-Specific Migrations

**Problem**: Not leveraging PostgreSQL-specific features for better performance.

**Examples in MedGuard**:
- Using `JSON` instead of `JSONB` for better performance
- Missing GIN indexes for full-text search
- Missing partial indexes for active records
- Not using `ArrayField` for better data organization

**Solution**: Applies PostgreSQL-specific optimizations.

**JSONB Optimization**:
```python
# Before: JSON field
metadata = models.JSONField(default=dict)

# After: JSONB field with GIN index
metadata = models.JSONField(default=dict)

class Meta:
    indexes = [
        GinIndex(fields=['metadata'], name='medication_metadata_gin_idx')
    ]
```

**Partial Indexes**:
```python
class Meta:
    indexes = [
        models.Index(
            fields=['alert_type'], 
            condition=models.Q(is_active=True), 
            name='active_alerts_idx'
        )
    ]
```

## 🔧 Advanced Usage

### Command Line Options

```bash
python fix_migrations.py [OPTIONS]

Options:
  --dry-run              Preview fixes without applying them
  --fix-circular         Fix circular dependency issues only
  --fix-json            Fix JSONField compatibility issues only
  --fix-images          Fix ImageField upload path issues only
  --fix-timezone         Fix timezone-aware datetime field issues only
  --fix-constraints      Fix unique constraint violation issues only
  --fix-foreign-keys     Fix foreign key constraint issues only
  --fix-decimal          Fix decimal field precision changes only
  --fix-indexes          Fix index naming conflicts only
  --fix-dependencies     Fix migration dependency ordering only
  --fix-postgresql       Fix PostgreSQL-specific migrations only
  -h, --help            Show help message
```

### Examples

```bash
# Preview circular dependency fixes
python fix_migrations.py --dry-run --fix-circular

# Fix JSON and image issues only
python fix_migrations.py --fix-json --fix-images

# Fix timezone and constraint issues
python fix_migrations.py --fix-timezone --fix-constraints

# Fix foreign key issues only
python fix_migrations.py --fix-foreign-keys

# Fix decimal precision and index issues
python fix_migrations.py --fix-decimal --fix-indexes

# Fix dependency and PostgreSQL issues
python fix_migrations.py --fix-dependencies --fix-postgresql

# Apply all fixes with backup
python fix_migrations.py
```

## 📁 Backup and Safety

### Automatic Backups

The script automatically creates backups before making changes:

- **Backup Location**: `migration_backups/`
- **Backup Format**: `filename_YYYYMMDD_HHMMSS.ext`
- **Backup Contents**: Original files before modification

### Dry Run Mode

Always use `--dry-run` first to preview changes:

```bash
python fix_migrations.py --dry-run
```

This shows what would be changed without actually modifying files.

## 📊 Reports and Logging

### Fix Report

After running the script, a detailed report is generated:

```json
{
  "timestamp": "2025-01-08T10:30:00",
  "django_version": "5.2.4",
  "dry_run": false,
  "fixes_applied": [
    {
      "type": "Circular Dependency",
      "description": "Fixed circular dependencies in 0001_initial.py",
      "file_path": "medguard_backend/medications/migrations/0001_initial.py",
      "timestamp": "2025-01-08T10:30:15"
    }
  ],
  "errors": [],
  "summary": {
    "total_fixes": 5,
    "total_errors": 0,
    "fix_types": {
      "Circular Dependency": 2,
      "JSONField Compatibility": 2,
      "ImageField Path": 1,
      "Timezone Fields": 1,
      "Unique Constraint": 1,
      "Foreign Key Constraints": 1
    }
  }
}
```

### Console Output

The script provides real-time feedback:

```
🔧 MedGuard SA Migration Fixer
   Django version: 5.2.4
   Dry run: False
   Backup directory: migration_backups

🔄 Fixing circular dependencies...
   🔍 Checking: User-MedicationSchedule circular dependency
✅ Circular Dependency: Fixed circular dependencies in 0001_initial.py
   📁 medguard_backend/medications/migrations/0001_initial.py

📄 Fixing JSONField compatibility...
   🎯 Applying Django 5.x JSONField fixes...
✅ JSONField Compatibility: Fixed JSONField for Django 5.x in users/models.py
   📁 medguard_backend/users/models.py

🖼️  Fixing ImageField upload paths...
   🔍 Checking: Avatar upload path conflicts
✅ ImageField Path: Fixed upload paths in users/models.py
   📁 medguard_backend/users/models.py

🕐 Fixing timezone-aware datetime field migrations...
   🔍 Checking: User model datetime fields
✅ Timezone Fields: Fixed timezone fields in users/models.py
   📁 medguard_backend/users/models.py

🔒 Fixing unique constraint violations...
   🔍 Checking: User email uniqueness
✅ Unique Constraint: Fixed unique constraints in 0001_initial.py
   📁 medguard_backend/users/migrations/0001_initial.py

🔗 Fixing foreign key constraint issues...
   🔍 Checking: User foreign key references
✅ Foreign Key Constraints: Fixed foreign key constraints in medications/models.py
   📁 medguard_backend/medications/models.py

📝 Creating migration fix script...
✅ Migration Script: Created custom migration fix script
   📁 medguard_backend/custom_migration_fixes.py

📊 Generating fix report...
📋 Fix Report Summary:
   Total fixes applied: 12
   Total errors: 0
   Fix types: {'Circular Dependency': 2, 'JSONField Compatibility': 2, 'ImageField Path': 1, 'Timezone Fields': 1, 'Unique Constraint': 1, 'Foreign Key Constraints': 1, 'Decimal Precision': 2, 'Index Naming Conflicts': 1, 'Migration Dependencies': 1, 'PostgreSQL Optimizations': 1}
   Report saved to: migration_backups/migration_fix_report_20250108_103000.json

✅ Migration fixes completed!
   All fixes have been applied.
   Check the backup directory for original files.
   Run the custom migration script if needed.
```

## 🛠️ Custom Migration Script

The script also generates `custom_migration_fixes.py` for complex database-level fixes:

```bash
# Run the custom migration script
python medguard_backend/custom_migration_fixes.py
```

This script handles:
- Database-level circular dependency checks
- JSONField data validation and cleanup
- Timezone datetime data validation and fixes
- Unique constraint violation resolution
- Foreign key constraint violation cleanup
- ImageField path verification

## 🔍 Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Ensure write permissions
   chmod +w medguard_backend/
   ```

2. **Django Not Found**
   ```bash
   # Set Django settings
   export DJANGO_SETTINGS_MODULE=medguard_backend.settings.development
   ```

3. **Backup Directory Issues**
   ```bash
   # Create backup directory manually
   mkdir -p migration_backups
   ```

### Error Recovery

If something goes wrong:

1. **Restore from Backup**:
   ```bash
   # Find backup files
   ls migration_backups/
   
   # Restore specific file
   cp migration_backups/filename_20250108_103000.py original_location/
   ```

2. **Check Fix Report**:
   ```bash
   # Review what was changed
   cat migration_backups/migration_fix_report_*.json
   ```

3. **Re-run with Dry Run**:
   ```bash
   # Verify current state
   python fix_migrations.py --dry-run
   ```

## 📝 Migration Best Practices

### Before Running Fixes

1. **Backup Database**:
   ```bash
   pg_dump medguard_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Check Current State**:
   ```bash
   python manage.py showmigrations
   ```

3. **Test in Development**:
   ```bash
   # Always test in development first
   python fix_migrations.py --dry-run
   ```

### After Running Fixes

1. **Verify Changes**:
   ```bash
   python manage.py check
   python manage.py makemigrations --dry-run
   ```

2. **Test Migrations**:
   ```bash
   python manage.py migrate --plan
   ```

3. **Run Tests**:
   ```bash
   python manage.py test
   ```

## 🔄 Integration with CI/CD

### GitHub Actions Example

```yaml
name: Migration Fixes
on:
  pull_request:
    paths:
      - 'medguard_backend/**'

jobs:
  migration-fixes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run migration fixes (dry run)
        run: |
          cd medguard_backend
          python fix_migrations.py --dry-run
      
      - name: Check for issues
        run: |
          python manage.py check
          python manage.py makemigrations --dry-run
```

## 📚 Related Documentation

- [Django Migrations Documentation](https://docs.djangoproject.com/en/stable/topics/migrations/)
- [Django JSONField Documentation](https://docs.djangoproject.com/en/stable/ref/models/fields/#jsonfield)
- [Django ImageField Documentation](https://docs.djangoproject.com/en/stable/ref/models/fields/#imagefield)

## 🤝 Contributing

To contribute to the migration fix script:

1. **Fork the repository**
2. **Create a feature branch**
3. **Add tests for new fixes**
4. **Update documentation**
5. **Submit a pull request**

### Adding New Fix Types

To add support for new migration issues:

1. **Add fix method** to `MigrationFixer` class
2. **Update command line arguments** in `main()`
3. **Add documentation** to this README
4. **Include test cases**

## 📄 License

This script is part of the MedGuard SA project and follows the same license terms.

## 🆘 Support

For issues or questions:

1. **Check the troubleshooting section**
2. **Review the fix report**
3. **Create an issue** with detailed error information
4. **Include Django version and error logs**

---

**Note**: Always test migration fixes in a development environment before applying to production. 