# Migration Quick Reference

## 🚀 Production Deployment Commands

### Basic Commands
```bash
# Check for pending migrations (safe to run anytime)
./production_migrate.sh check-migrations

# Run all migrations safely
./production_migrate.sh migrate

# Initial deployment (first time only)
./production_migrate.sh migrate --run-syncdb

# Migrate specific apps with detailed logging
./production_migrate.sh migrate-apps --apps medications users security

# Collect static files
./production_migrate.sh collectstatic

# Validate production settings
./production_migrate.sh deploy-check

# Full deployment sequence (recommended)
./production_migrate.sh full-deploy

# Create database backup
./production_migrate.sh backup
```

### Advanced Safety Commands
```bash
# Verify data integrity after migration
./production_migrate.sh verify-data

# Execute zero-downtime migration strategy
./production_migrate.sh zero-downtime

# Enhanced backup with compression
./production_migrate_enhanced.sh backup

# Monitor migration performance
./production_migrate_enhanced.sh migrate --monitor
```

### Windows Commands
```cmd
# Same commands, use .bat extension
production_migrate.bat check-migrations
production_migrate.bat migrate
production_migrate.bat full-deploy
```

### Direct Python Commands
```bash
# Direct execution without wrapper
python production_migrate.py check-migrations
python production_migrate.py migrate
python production_migrate.py full-deploy
```

## 📋 Standard Deployment Workflow

1. **Pre-deployment Check**
   ```bash
   ./production_migrate.sh check-migrations
   ```

2. **Full Deployment**
   ```bash
   ./production_migrate.sh full-deploy
   ```

3. **Verify Success**
   ```bash
   ./production_migrate.sh deploy-check
   ```

## 🔧 Troubleshooting Commands

```bash
# Check database connection
python manage.py dbshell

# View migration status
python manage.py showmigrations

# Check Django settings
python manage.py check --deploy

# View logs
tail -f migration.log
```

## ⚠️ Emergency Commands

```bash
# Create backup before any changes
./production_migrate.sh backup

# List available backups
python rollback_manager.py list-backups

# Emergency rollback to most recent backup
python rollback_manager.py emergency-rollback

# Rollback to specific backup
python rollback_manager.py rollback medguard_backup_20240101_120000.sql

# Validate backup integrity
python rollback_manager.py validate-backup backups/medguard_backup_20240101_120000.sql

# Clean up old backups (keep last 7 days)
python rollback_manager.py cleanup-backups --keep-days 7
```

## 📝 Environment Variables (Required)

```bash
export DJANGO_SETTINGS_MODULE="medguard_backend.settings.production"
export DB_NAME="medguard_sa"
export DB_USER="medguard_user"
export DB_PASSWORD="your_password"
export DB_HOST="localhost"
export DB_PORT="5432"
```

## 🎯 Most Common Use Cases

### Daily Deployment
```bash
./production_migrate.sh full-deploy
```

### Check Migration Status
```bash
./production_migrate.sh check-migrations
```

### Update Specific App
```bash
./production_migrate.sh migrate-apps --apps medications
```

### Static Files Update
```bash
./production_migrate.sh collectstatic
```

### Zero-Downtime Production Update
```bash
./production_migrate.sh zero-downtime
```

### Data Integrity Verification
```bash
./production_migrate.sh verify-data
```

### Performance Monitoring
```bash
./production_migrate_enhanced.sh migrate --monitor
```

---

**💡 Tip**: Always run `check-migrations` first to verify no pending migrations exist before deployment. 