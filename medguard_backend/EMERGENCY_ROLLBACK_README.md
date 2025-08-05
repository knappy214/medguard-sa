# Emergency Rollback Procedures for MedGuard SA

This document provides comprehensive guidance for using the emergency rollback procedures implemented in `rollback_migrations.py`. These procedures are designed to handle critical migration failures and provide automated recovery capabilities.

## Overview

The emergency rollback system provides ten core features:

1. **Database Backup Restoration Procedures** - Automated backup creation and restoration
2. **Selective Migration Rollback Commands** - Rollback specific migrations safely
3. **Data Export Procedures** - Export data before risky migrations
4. **Migration State Verification Checks** - Validate migration consistency
5. **Automated Rollback Triggers** - Automatic recovery on migration failures
6. **Data Integrity Verification** - Comprehensive data integrity checks after rollbacks
7. **Notification Systems** - Multi-channel notifications for migration issues
8. **Gradual Rollback** - Zero-downtime rollback procedures
9. **Migration Conflict Resolution** - Detect and resolve migration conflicts
10. **Post-Rollback Data Reconciliation** - Reconcile data inconsistencies after rollbacks

## Quick Start

### Prerequisites

- PostgreSQL database (configured in Django settings)
- `pg_dump` and `pg_restore` tools installed
- Django environment properly configured
- Sufficient disk space for backups

### Basic Usage

```bash
# Create a backup before risky migration
python rollback_migrations.py create-backup

# Export data from specific app
python rollback_migrations.py export-data medications

# Rollback a specific migration
python rollback_migrations.py rollback-migration medications 0018_remove_prescription_secondary_diagnoses

# Verify migration state
python rollback_migrations.py verify-state

# Emergency recovery
python rollback_migrations.py emergency-recovery

# Verify data integrity
python rollback_migrations.py verify-integrity --export-path data_exports/data_export_20240101_120000.json

# Send notification
python rollback_migrations.py send-notification --notification-type migration_failed --notification-message "Migration failed" --severity error

# Gradual rollback
python rollback_migrations.py gradual-rollback medications 0017_merge_20250805_2014 --batch-size 50 --delay-seconds 3

# Resolve migration conflicts
python rollback_migrations.py resolve-conflicts medications

# Reconcile data after rollback
python rollback_migrations.py reconcile-data backups/backup_20240101_120000.sql --export-path data_exports/data_export_20240101_120000.json

## Detailed Commands

### 1. Database Backup Restoration

#### Create Backup
```bash
python rollback_migrations.py create-backup
```

**Features:**
- Creates PostgreSQL custom format backup
- Generates metadata with migration state
- Validates backup integrity
- Stores in `backups/` directory

**Output:**
```
2024-01-01 12:00:00 - INFO - Creating backup: backups/medguard_backup_20240101_120000.sql
2024-01-01 12:00:00 - INFO - ✓ Backup created successfully: backups/medguard_backup_20240101_120000.sql
```

#### Restore Backup
```bash
python rollback_migrations.py backup-restore backups/medguard_backup_20240101_120000.sql
```

**Features:**
- Drops and recreates database
- Restores from PostgreSQL backup
- Validates restoration
- Verifies migration state

### 2. Selective Migration Rollback

#### Rollback Specific Migration
```bash
python rollback_migrations.py rollback-migration <app_name> <migration_name>
```

**Example:**
```bash
python rollback_migrations.py rollback-migration medications 0018_remove_prescription_secondary_diagnoses
```

**Safety Features:**
- Creates backup before rollback
- Exports app data
- Automatic recovery on failure
- Verifies rollback success

#### Check Migration Dependencies
```bash
python rollback_migrations.py check-dependencies <app_name> <migration_name>
```

**Example:**
```bash
python rollback_migrations.py check-dependencies medications 0018_remove_prescription_secondary_diagnoses
```

**Output:**
```
Dependencies for medications.0018_remove_prescription_secondary_diagnoses:
  Applied: True
  Dependencies: [('medications', '0017_merge_20250805_2014')]
  Dependents: []
```

### 3. Data Export Procedures

#### Export All Data
```bash
python rollback_migrations.py export-data
```

#### Export Specific App Data
```bash
python rollback_migrations.py export-data medications
```

**Features:**
- Exports to JSON format
- Creates SHA256 checksums
- Handles datetime serialization
- Stores in `data_exports/` directory

**Output Structure:**
```json
{
  "medications": {
    "medications_prescription": {
      "count": 150,
      "data": [...]
    },
    "medications_medication": {
      "count": 75,
      "data": [...]
    }
  }
}
```

### 4. Migration State Verification

#### Verify Current State
```bash
python rollback_migrations.py verify-state
```

**Checks:**
- Database connection
- Django migration table
- Unapplied migrations
- Migration conflicts
- Django deployment checks

#### List All Migrations
```bash
python rollback_migrations.py list-migrations
```

**Output:**
```
Migration status:

medications:
  [✓] 0001_initial
  [✓] 0002_add_prescription_fields
  [ ] 0018_remove_prescription_secondary_diagnoses
```

#### Validate Schema
```bash
python rollback_migrations.py validate-schema
```

**Checks:**
- Missing tables
- Orphaned tables
- Django model consistency
- Deployment configuration

### 5. Emergency Recovery

#### Full Emergency Recovery
```bash
python rollback_migrations.py emergency-recovery
```

**Recovery Steps:**
1. Create emergency backup
2. Export critical data
3. Verify current state
4. Check schema consistency
5. Attempt to fix common issues
6. Final verification

### 6. Data Integrity Verification

#### Verify Data Integrity
```bash
python rollback_migrations.py verify-integrity --export-path data_exports/data_export_20240101_120000.json
```

**Verification Steps:**
1. Database connectivity check
2. Table record count validation
3. Foreign key constraint verification
4. Data consistency checks
5. Comparison with exported data
6. Business rule validation

**Output:**
```json
{
  "timestamp": "2024-01-01T12:00:00",
  "checks_passed": 5,
  "checks_failed": 0,
  "overall_status": "passed",
  "details": {
    "database_connection": "passed",
    "table_counts": {...},
    "foreign_key_issues": [],
    "consistency_issues": [],
    "data_comparison": {...},
    "business_rule_issues": []
  }
}
```

### 7. Notification Systems

#### Send Notifications
```bash
python rollback_migrations.py send-notification \
  --notification-type migration_failed \
  --notification-message "Migration failed due to constraint violation" \
  --severity error
```

**Supported Channels:**
- **Email**: Automatic email notifications to admin team
- **Slack**: Webhook-based Slack notifications
- **SMS**: Critical issue SMS alerts (configurable)

**Notification Types:**
- `migration_failed` - Migration failure alerts
- `rollback_completed` - Successful rollback notifications
- `data_integrity_issue` - Data integrity problems
- `gradual_rollback_progress` - Progress updates
- `emergency_recovery` - Emergency recovery events

**Severity Levels:**
- `info` - Informational messages
- `warning` - Warning conditions
- `error` - Error conditions
- `critical` - Critical system issues

### 8. Gradual Rollback

#### Zero-Downtime Rollback
```bash
python rollback_migrations.py gradual-rollback \
  medications 0017_merge_20250805_2014 \
  --batch-size 50 \
  --delay-seconds 3
```

**Features:**
- **Batch Processing**: Process data in configurable batches
- **Zero Downtime**: Maintain system availability during rollback
- **Progress Tracking**: Real-time progress monitoring
- **Automatic Recovery**: Automatic recovery on failures
- **Verification**: Step-by-step verification

**Rollback Steps:**
1. **Preparation**: Check dependencies and create backups
2. **Data Rollback**: Rollback data changes in batches
3. **Schema Rollback**: Rollback schema changes
4. **Verification**: Verify rollback completion

**Configuration Options:**
- `--batch-size`: Number of records per batch (default: 100)
- `--delay-seconds`: Delay between batches (default: 5)

## Advanced Usage

### Automated Rollback Triggers

The system can create automated rollback triggers for migration failures:

```python
from rollback_migrations import EmergencyRollbackProcedures

procedures = EmergencyRollbackProcedures()

# Create automated trigger for migration command
procedures.create_automated_rollback_trigger([
    'python', 'manage.py', 'migrate', 'medications'
])
```

This creates a shell script that automatically triggers rollback if the migration fails.

### Integration with CI/CD

Add to your deployment pipeline:

```bash
#!/bin/bash
set -e

# Create backup before deployment
python rollback_migrations.py create-backup

# Export critical data
python rollback_migrations.py export-data

# Run migrations
python manage.py migrate

# Verify deployment
python rollback_migrations.py verify-state

# If verification fails, trigger emergency recovery
if [ $? -ne 0 ]; then
    python rollback_migrations.py emergency-recovery
    exit 1
fi
```

### Monitoring and Logging

The system provides comprehensive logging:

- **File Logging**: `rollback_migrations.log`
- **Console Output**: Real-time status updates
- **Error Tracking**: Detailed error messages and stack traces

## Best Practices

### Before Risky Migrations

1. **Always create a backup:**
   ```bash
   python rollback_migrations.py create-backup
   ```

2. **Export critical data:**
   ```bash
   python rollback_migrations.py export-data medications
   ```

3. **Verify current state:**
   ```bash
   python rollback_migrations.py verify-state
   ```

4. **Check dependencies:**
   ```bash
   python rollback_migrations.py check-dependencies medications <migration_name>
   ```

### During Migration Failures

1. **Immediate assessment:**
   ```bash
   python rollback_migrations.py verify-state
   ```

2. **Emergency recovery if needed:**
   ```bash
   python rollback_migrations.py emergency-recovery
   ```

3. **Manual rollback if automatic fails:**
   ```bash
   python rollback_migrations.py rollback-migration <app> <migration>
   ```

### After Recovery

1. **Verify restoration:**
   ```bash
   python rollback_migrations.py verify-state
   python rollback_migrations.py validate-schema
   ```

2. **Check data integrity:**
   - Compare exported data with current state
   - Verify critical business data
   - Test application functionality

## Troubleshooting

### Common Issues

#### Backup Creation Fails
```
ERROR: Backup creation failed: pg_dump: error: connection to database failed
```

**Solutions:**
- Check PostgreSQL connection settings
- Verify database credentials
- Ensure PostgreSQL service is running
- Check disk space

#### Migration Rollback Fails
```
ERROR: Migration rollback failed: django.db.utils.OperationalError
```

**Solutions:**
- Check migration dependencies
- Verify database state
- Use emergency recovery
- Manual intervention may be required

#### Schema Validation Fails
```
ERROR: Missing tables: ['medications_prescription']
```

**Solutions:**
- Check if migrations are applied
- Verify Django model definitions
- Run emergency recovery
- Restore from backup

### Recovery Procedures

#### Complete System Recovery
```bash
# 1. Stop application
sudo systemctl stop medguard-backend

# 2. Emergency recovery
python rollback_migrations.py emergency-recovery

# 3. Verify recovery
python rollback_migrations.py verify-state
python rollback_migrations.py validate-schema

# 4. Restart application
sudo systemctl start medguard-backend
```

#### Data Recovery from Export
```python
import json
from django.core.management import execute_from_command_line

# Load exported data
with open('data_exports/data_export_20240101_120000_medications.json', 'r') as f:
    data = json.load(f)

# Restore data (implement based on your needs)
# This is a simplified example
for table_name, table_data in data['medications'].items():
    if 'data' in table_data:
        # Restore records
        pass
```

### 9. Migration Conflict Resolution

#### Resolve Migration Conflicts
```bash
python rollback_migrations.py resolve-conflicts [app_name]
```

**Example:**
```bash
# Resolve conflicts in all apps
python rollback_migrations.py resolve-conflicts

# Resolve conflicts in specific app
python rollback_migrations.py resolve-conflicts medications
```

**Features:**
- Detects missing migration files
- Identifies unapplied migration files
- Checks dependency conflicts
- Detects circular dependencies
- Automatically resolves simple conflicts
- Creates reports for manual intervention

**Conflict Types Handled:**
- **Missing File Conflicts**: Migration applied but file missing
- **Unapplied File Conflicts**: Migration file exists but not applied
- **Dependency Conflicts**: Missing dependencies for applied migrations
- **Circular Dependencies**: Circular dependency chains

**Output:**
```
2024-01-01 12:00:00 - INFO - Starting migration conflict resolution...
2024-01-01 12:00:00 - INFO - ✓ Migration conflict resolution completed successfully
2024-01-01 12:00:00 - INFO - Resolved 2 conflicts
```

#### Conflict Resolution Process
1. **Detection**: Scan all apps for migration inconsistencies
2. **Analysis**: Identify conflict types and dependencies
3. **Resolution**: Attempt automatic resolution where possible
4. **Reporting**: Create detailed reports for manual intervention
5. **Verification**: Verify resolution success

### 10. Post-Rollback Data Reconciliation

#### Reconcile Data After Rollback
```bash
python rollback_migrations.py reconcile-data <backup_path> [--export-path <export_path>]
```

**Example:**
```bash
python rollback_migrations.py reconcile-data backups/backup_20240101_120000.sql --export-path data_exports/data_export_20240101_120000.json
```

**Features:**
- Verifies backup integrity
- Compares current data with backup
- Identifies data inconsistencies
- Reconciles foreign key relationships
- Restores missing data from exports
- Performs final integrity checks

**Reconciliation Steps:**
1. **Backup Verification**: Validate backup file integrity
2. **Data Comparison**: Compare current database with backup
3. **Issue Resolution**: Resolve data inconsistencies
4. **Foreign Key Reconciliation**: Verify and fix relationships
5. **Export Restoration**: Restore missing data from exports
6. **Final Verification**: Comprehensive integrity check

**Data Issues Handled:**
- Missing tables
- Row count mismatches
- Missing data records
- Foreign key violations
- Data corruption

**Output:**
```
2024-01-01 12:00:00 - INFO - Starting post-rollback data reconciliation...
2024-01-01 12:00:00 - INFO - Step 1: Verifying backup integrity...
2024-01-01 12:00:00 - INFO - Step 2: Comparing current data with backup...
2024-01-01 12:00:00 - INFO - Step 3: Reconciling data inconsistencies...
2024-01-01 12:00:00 - INFO - ✓ Post-rollback reconciliation completed: 3 resolved, 0 failed
```

#### Reconciliation Configuration
```bash
# Basic reconciliation
python rollback_migrations.py reconcile-data backups/backup.sql

# With export data for comparison
python rollback_migrations.py reconcile-data backups/backup.sql --export-path exports/data.json

# Verbose output for debugging
python rollback_migrations.py reconcile-data backups/backup.sql --verbose
```

## File Structure

```
medguard_backend/
├── rollback_migrations.py          # Main rollback procedures
├── backups/                        # Database backups
│   ├── medguard_backup_*.sql      # PostgreSQL backups
│   └── medguard_backup_*.json     # Backup metadata
├── data_exports/                   # Exported data
│   ├── data_export_*.json         # JSON data exports
│   └── data_export_*.checksum     # Data integrity checksums
├── rollback_scripts/               # Generated rollback scripts
│   └── automated_rollback_trigger.sh
├── conflict_reports/               # Migration conflict reports
│   └── circular_dependency_*.md   # Circular dependency reports
├── reconciliation_reports/         # Data reconciliation reports
│   └── reconciliation_*.json      # Reconciliation results
└── rollback_migrations.log         # Rollback operation logs
```

## Security Considerations

### Data Protection
- Backups contain sensitive patient data
- Ensure proper access controls
- Encrypt backup files in transit and at rest
- Regular backup rotation and cleanup

### Access Control
- Limit access to rollback procedures
- Use dedicated service accounts
- Audit all rollback operations
- Implement approval workflows for production

### Compliance
- Maintain audit trails
- Document all rollback operations
- Ensure HIPAA compliance for patient data
- Regular security assessments

## Performance Considerations

### Backup Performance
- Use PostgreSQL custom format for faster backups
- Consider incremental backups for large databases
- Schedule backups during low-traffic periods
- Monitor backup duration and size

### Rollback Performance
- Large databases may take significant time to restore
- Consider staging environment for testing
- Monitor system resources during rollback
- Plan for downtime during critical operations

## Support and Maintenance

### Regular Maintenance
- Clean up old backups (older than 30 days)
- Verify backup integrity regularly
- Test rollback procedures in staging
- Update procedures as system evolves

### Monitoring
- Monitor backup success/failure
- Track rollback operation frequency
- Alert on migration failures
- Regular health checks

### Documentation
- Keep this documentation updated
- Document any custom procedures
- Maintain runbooks for common scenarios
- Regular team training on procedures

## Conclusion

The emergency rollback procedures provide a comprehensive safety net for critical migration operations. By following the best practices outlined in this document, you can ensure reliable recovery from migration failures while maintaining data integrity and system stability.

For additional support or questions, refer to the Django migration documentation or contact the development team. 