# Production Migration Guide for MedGuard SA

This guide provides comprehensive instructions for safely deploying and migrating the MedGuard SA Django application in production environments.

## Overview

The production migration system consists of three main components:

1. **Python Script** (`production_migrate.py`) - Core migration logic with comprehensive error handling
2. **Shell Script** (`production_migrate.sh`) - Unix/Linux wrapper with additional safety checks
3. **Batch File** (`production_migrate.bat`) - Windows wrapper with additional safety checks

## Prerequisites

Before running production migrations, ensure you have:

- ✅ Python 3.8+ installed
- ✅ Django 4.x installed
- ✅ PostgreSQL database configured
- ✅ Environment variables set (see Environment Setup below)
- ✅ Virtual environment activated (recommended)
- ✅ Database connection tested

## Environment Setup

### Required Environment Variables

Set these environment variables in your production environment:

```bash
# Django Settings
export DJANGO_SETTINGS_MODULE="medguard_backend.settings.production"

# Database Configuration
export DB_NAME="medguard_sa"
export DB_USER="medguard_user"
export DB_PASSWORD="your_secure_password"
export DB_HOST="localhost"
export DB_PORT="5432"

# Optional: SSL/HTTPS Settings
export SECURE_SSL_REDIRECT="True"
export ALLOWED_HOSTS="your-domain.com,www.your-domain.com"

# Optional: Email Settings
export EMAIL_HOST="smtp.your-provider.com"
export EMAIL_PORT="587"
export EMAIL_USE_TLS="True"
export EMAIL_HOST_USER="your-email@domain.com"
export EMAIL_HOST_PASSWORD="your-email-password"
export DEFAULT_FROM_EMAIL="noreply@medguard-sa.com"

# Optional: Redis Cache
export REDIS_URL="redis://localhost:6379/1"
```

### Windows Environment Variables

For Windows, set environment variables using:

```cmd
set DJANGO_SETTINGS_MODULE=medguard_backend.settings.production
set DB_NAME=medguard_sa
set DB_USER=medguard_user
set DB_PASSWORD=your_secure_password
set DB_HOST=localhost
set DB_PORT=5432
```

## Migration Commands

### 1. Check for Pending Migrations

**Purpose**: Verify that no pending migrations exist before deployment.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh check-migrations

# Windows
production_migrate.bat check-migrations

# Direct Python
python production_migrate.py check-migrations
```

**What it does**:
- Runs `python manage.py makemigrations --check`
- Reports if any pending migrations are detected
- Does NOT apply any migrations
- Safe to run multiple times

**Expected Output**:
```
✓ No pending migrations found
```

### 2. Run Standard Migrations

**Purpose**: Apply all pending migrations safely.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh migrate

# Windows
production_migrate.bat migrate

# Direct Python
python production_migrate.py migrate
```

**What it does**:
- Creates database backup before migration
- Checks database connection
- Runs `python manage.py migrate`
- Provides detailed logging
- Handles errors gracefully

**Expected Output**:
```
✓ Migrations completed successfully
```

### 3. Initial Deployment with Syncdb

**Purpose**: For first-time deployments or when you need to sync database tables.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh migrate --run-syncdb

# Windows
production_migrate.bat migrate --run-syncdb

# Direct Python
python production_migrate.py migrate --run-syncdb
```

**What it does**:
- Creates database backup
- Runs `python manage.py migrate --run-syncdb`
- Creates tables for apps without migrations
- Applies all existing migrations

**⚠️ Warning**: Only use for initial deployments or when explicitly needed.

### 4. Migrate Specific Apps with Detailed Logging

**Purpose**: Apply migrations for specific apps with verbose output.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh migrate-apps --apps medications users security

# Windows
production_migrate.bat migrate-apps --apps medications users security

# Direct Python
python production_migrate.py migrate-apps --apps medications users security
```

**What it does**:
- Runs `python manage.py migrate [app] --verbosity=2` for each app
- Provides detailed logging for each migration step
- Useful for debugging migration issues
- Can target specific apps that need attention

**Available Apps**:
- `medications` - Medication management system
- `users` - User authentication and profiles
- `security` - Security and audit logging
- `medguard_notifications` - Notification system
- `home` - Homepage and CMS content
- `search` - Search functionality

### 5. Collect Static Files

**Purpose**: Collect and optimize static files for production.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh collectstatic

# Windows
production_migrate.bat collectstatic

# Direct Python
python production_migrate.py collectstatic
```

**What it does**:
- Runs `python manage.py collectstatic --noinput`
- Collects all static files to `STATIC_ROOT`
- Applies file optimization and compression
- Required for production deployment

### 6. Deployment Validation

**Purpose**: Validate production settings and configuration.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh deploy-check

# Windows
production_migrate.bat deploy-check

# Direct Python
python production_migrate.py deploy-check
```

**What it does**:
- Runs `python manage.py check --deploy`
- Validates security settings
- Checks for common production issues
- Verifies database configuration
- Ensures static files are properly configured

### 7. Full Deployment Sequence

**Purpose**: Run complete deployment process in the correct order.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh full-deploy

# Windows
production_migrate.bat full-deploy

# Direct Python
python production_migrate.py full-deploy
```

**What it does** (in order):
1. Database connection check
2. Migration check (verify no pending migrations)
3. Run standard migrations
4. Migrate specific apps with detailed logging
5. Compile translation files
6. Collect static files
7. Deployment validation

**Expected Output**:
```
🎉 Full deployment completed successfully!
```

### 8. Database Backup

**Purpose**: Create a database backup before making changes.

**Command**:
```bash
# Unix/Linux
./production_migrate.sh backup

# Windows
production_migrate.bat backup

# Direct Python
python production_migrate.py backup
```

**What it does**:
- Creates timestamped PostgreSQL backup
- Stores backup in `backups/` directory
- Uses `pg_dump` for PostgreSQL databases
- Provides backup file location

## Production Deployment Workflow

### Standard Deployment

1. **Pre-deployment Check**:
   ```bash
   ./production_migrate.sh check-migrations
   ```

2. **Create Backup**:
   ```bash
   ./production_migrate.sh backup
   ```

3. **Run Full Deployment**:
   ```bash
   ./production_migrate.sh full-deploy
   ```

4. **Verify Deployment**:
   ```bash
   ./production_migrate.sh deploy-check
   ```

### Initial Deployment

1. **Set up environment variables**
2. **Create database and user**
3. **Run initial deployment**:
   ```bash
   ./production_migrate.sh migrate --run-syncdb
   ```
4. **Collect static files**:
   ```bash
   ./production_migrate.sh collectstatic
   ```
5. **Validate deployment**:
   ```bash
   ./production_migrate.sh deploy-check
   ```

### Emergency Rollback

If a migration fails, you can restore from backup:

```bash
# Restore from the most recent backup
psql -h localhost -U medguard_user -d medguard_sa < backups/medguard_backup_YYYYMMDD_HHMMSS.sql
```

## Safety Features

### Automatic Backup Creation

- Database backups are automatically created before migrations
- Backups are timestamped and stored in `backups/` directory
- Uses PostgreSQL `pg_dump` for reliable backups

### Error Handling

- Comprehensive error catching and reporting
- Graceful failure handling
- Detailed logging to `migration.log`
- Command timeouts to prevent hanging

### Pre-flight Checks

- Database connection verification
- Django installation check
- Environment variable validation
- Virtual environment detection

### Logging

All operations are logged to:
- Console output (with color coding)
- `migration.log` file
- Timestamped entries for audit trail

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check environment variables
   - Verify PostgreSQL is running
   - Test connection manually

2. **Migration Conflicts**
   - Check for pending migrations
   - Review migration files
   - Consider rolling back if needed

3. **Static Files Not Found**
   - Run `collectstatic` command
   - Check `STATIC_ROOT` setting
   - Verify file permissions

4. **Permission Denied**
   - Check file permissions on scripts
   - Ensure proper user permissions
   - Verify database user permissions

### Debug Mode

For troubleshooting, you can run commands with increased verbosity:

```bash
# Enable Django debug mode temporarily
export DJANGO_SETTINGS_MODULE="medguard_backend.settings.development"

# Run with detailed output
python production_migrate.py migrate-apps --apps medications --verbosity=3
```

### Log Analysis

Check the migration log for detailed information:

```bash
tail -f migration.log
```

## Security Considerations

### Environment Variables

- Never commit sensitive environment variables to version control
- Use secure methods to manage production secrets
- Rotate database passwords regularly

### Database Backups

- Store backups securely
- Encrypt backup files if containing sensitive data
- Test backup restoration procedures

### Access Control

- Limit access to production migration scripts
- Use dedicated database users with minimal privileges
- Monitor migration execution logs

## Best Practices

1. **Always test migrations in staging first**
2. **Create backups before any migration**
3. **Run migrations during low-traffic periods**
4. **Monitor application after migration**
5. **Keep migration scripts updated**
6. **Document any custom migration steps**
7. **Use version control for migration files**

## Support

For issues with the migration system:

1. Check the migration log file
2. Review this documentation
3. Test in development environment
4. Contact the development team

---

**Last Updated**: $(date)
**Version**: 1.0.0
**Compatible with**: Django 4.x, PostgreSQL 12+ 