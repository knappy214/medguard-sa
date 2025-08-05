# MedGuard SA Migration Execution Script

## Overview

The `migrate_all.py` script provides a comprehensive, production-ready migration workflow for the MedGuard SA Django backend. It handles all aspects of database migrations including connection verification, backups, execution, and integrity checks.

## Features

### 🔍 **Comprehensive Workflow**
- Database connection verification
- Automatic PostgreSQL backup creation
- Migration preview and dry-run capabilities
- SQL migration review
- Transaction-safe custom data migrations
- Table verification and integrity checks
- Deployment readiness validation

### 🛡️ **Safety Features**
- Automatic database backups before migration
- Dry-run mode for previewing changes
- Transaction rollback on errors
- Detailed logging and reporting
- Graceful error handling

### 📊 **Monitoring & Reporting**
- Real-time progress logging
- Comprehensive execution reports (JSON format)
- Success/failure tracking for each step
- Performance timing metrics

## Prerequisites

### System Requirements
- Python 3.8+
- PostgreSQL 12+
- `psycopg2` package installed
- `pg_dump` utility available in PATH

### Environment Setup
1. Ensure your virtual environment is activated
2. Verify PostgreSQL connection settings in `.env` file
3. Install required dependencies:
   ```bash
   pip install psycopg2-binary
   ```

## Usage

### Basic Usage

```bash
# Run complete migration workflow
python migrate_all.py

# Preview changes without executing (dry-run)
python migrate_all.py --dry-run

# Create database backup only
python migrate_all.py --backup-only

# Run verification checks only
python migrate_all.py --verify-only
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Preview all changes without executing migrations |
| `--backup-only` | Only create database backup |
| `--verify-only` | Only run verification and integrity checks |

## Workflow Steps

The script executes the following steps in sequence:

### 1. **Database Connection Check**
- Verifies PostgreSQL connection
- Displays database configuration
- Shows PostgreSQL version

### 2. **Database Backup**
- Creates timestamped backup using `pg_dump`
- Stores in `backups/` directory
- Uses `--clean --no-owner --no-privileges` flags

### 3. **Migration Preview**
- Runs `python manage.py makemigrations --dry-run`
- Shows pending migration changes
- No actual files created

### 4. **Create Migrations**
- Executes `python manage.py makemigrations medications`
- Creates new migration files if needed
- Verbose output for tracking

### 5. **SQL Migration Review**
- Runs `python manage.py sqlmigrate medications 0001`
- Shows actual SQL that will be executed
- Helps verify migration logic

### 6. **Fake Initial Migration**
- Runs `python manage.py migrate --fake-initial`
- Handles existing database scenarios
- Safe for both new and existing databases

### 7. **Execute Migrations**
- Runs general migrations first
- Then medications-specific migrations
- Verbose output with progress tracking

### 8. **Custom Data Migrations**
- Executes custom management commands:
  - `setup_notification_system`
  - `setup_notification_tasks`
  - `seed_medications`
- Uses transaction rollback on errors

### 9. **Table Verification**
- Verifies all expected tables exist
- Checks for core MedGuard tables
- Validates Django system tables

### 10. **Deployment Check**
- Runs `python manage.py check --deploy`
- Validates production readiness
- Checks security settings

### 11. **Data Integrity Checks**
- Checks for orphaned records
- Validates foreign key relationships
- Runs Django system checks

## Output Files

### Logs
- **Console Output**: Real-time progress and status
- **`migration_execution.log`**: Detailed execution log
- **`migration_report_YYYYMMDD_HHMMSS.json`**: Comprehensive report

### Backups
- **`backups/medguard_backup_YYYYMMDD_HHMMSS.sql`**: Database backup

## Expected Tables

The script verifies the following tables exist:

### Core MedGuard Tables
- `medications_medication`
- `medications_prescription`
- `medications_medicationlog`
- `medications_stocklevel`
- `medications_interaction`
- `medications_medicationimage`
- `medications_prescriptionrenewal`
- `medications_pharmacyintegration`
- `medications_medicationindexpage`
- `medications_medicationdetailpage`

### User & Security Tables
- `users_user`
- `security_securityevent`
- `security_auditlog`

### Notification Tables
- `medguard_notifications_notification`
- `medguard_notifications_notificationtemplate`

### Django System Tables
- `django_migrations`
- `django_content_type`
- `django_admin_log`
- `auth_group`
- `auth_permission`

## Error Handling

### Graceful Degradation
- Script continues on non-critical errors
- Detailed error logging for troubleshooting
- Transaction rollback for data migrations

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Verify connection settings
cat .env | grep DB_
```

#### Backup Creation Failed
```bash
# Check pg_dump availability
which pg_dump

# Verify PostgreSQL user permissions
psql -U medguard_user -d medguard_sa -c "SELECT current_user;"
```

#### Migration Conflicts
```bash
# Check migration status
python manage.py showmigrations

# Reset migrations if needed
python manage.py migrate --fake medications zero
```

## Best Practices

### Before Running
1. **Always test in development first**
2. **Review migration preview output**
3. **Ensure sufficient disk space for backups**
4. **Verify database user permissions**

### During Execution
1. **Monitor console output for errors**
2. **Check log files for detailed information**
3. **Don't interrupt the process**

### After Execution
1. **Review migration report**
2. **Verify application functionality**
3. **Test critical workflows**
4. **Keep backup files for recovery**

## Recovery Procedures

### Restore from Backup
```bash
# Restore database from backup
psql -U medguard_user -d medguard_sa < backups/medguard_backup_YYYYMMDD_HHMMSS.sql
```

### Rollback Migrations
```bash
# Rollback specific migration
python manage.py migrate medications 0010

# Fake rollback if needed
python manage.py migrate medications 0010 --fake
```

## Troubleshooting

### Permission Issues
```bash
# Grant necessary permissions
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE medguard_sa TO medguard_user;"
```

### Lock Issues
```bash
# Check for active connections
psql -U medguard_user -d medguard_sa -c "SELECT * FROM pg_stat_activity WHERE datname = 'medguard_sa';"

# Terminate connections if needed
psql -U medguard_user -d medguard_sa -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'medguard_sa' AND pid <> pg_backend_pid();"
```

### Memory Issues
```bash
# Increase PostgreSQL memory settings
# Edit postgresql.conf
shared_buffers = 256MB
work_mem = 4MB
maintenance_work_mem = 64MB
```

## Security Considerations

### HIPAA Compliance
- All operations logged for audit trails
- Database backups encrypted in transit
- No sensitive data in log files
- Secure credential handling

### Access Control
- Script requires database admin privileges
- Backup files stored securely
- Log files contain no sensitive information

## Performance Optimization

### Large Databases
- Consider running during low-traffic periods
- Monitor disk I/O during backup
- Use `--exclude-table-data` for large tables if needed

### Network Considerations
- Local database recommended for large migrations
- Consider network latency for remote databases
- Monitor connection timeouts

## Support

For issues or questions:
1. Check the log files for detailed error information
2. Review the migration report JSON file
3. Consult Django migration documentation
4. Contact the development team

---

**Note**: This script is designed for production use but should always be tested in a development environment first. Always maintain proper backups and have a rollback plan before running migrations in production. 