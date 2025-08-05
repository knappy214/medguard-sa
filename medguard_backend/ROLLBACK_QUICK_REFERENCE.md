# Emergency Rollback Quick Reference

## 🚨 Emergency Commands

### Before Any Risky Migration
```bash
# 1. Create backup
python rollback_migrations.py create-backup

# 2. Export critical data
python rollback_migrations.py export-data medications

# 3. Verify current state
python rollback_migrations.py verify-state
```

### Migration Failed - Emergency Recovery
```bash
# Immediate emergency recovery
python rollback_migrations.py emergency-recovery

# If that fails, restore from latest backup
python rollback_migrations.py backup-restore backups/medguard_backup_*.sql
```

### Rollback Specific Migration
```bash
# Check dependencies first
python rollback_migrations.py check-dependencies medications 0018_remove_prescription_secondary_diagnoses

# Rollback the migration
python rollback_migrations.py rollback-migration medications 0018_remove_prescription_secondary_diagnoses
```

### Data Integrity & Notifications
```bash
# Verify data integrity
python rollback_migrations.py verify-integrity --export-path data_exports/data_export_20240101_120000.json

# Send notification
python rollback_migrations.py send-notification --notification-type migration_failed --notification-message "Migration failed" --severity error

# Gradual rollback (zero-downtime)
python rollback_migrations.py gradual-rollback medications 0017_merge_20250805_2014 --batch-size 50 --delay-seconds 3

# Resolve migration conflicts
python rollback_migrations.py resolve-conflicts medications

# Reconcile data after rollback
python rollback_migrations.py reconcile-data backups/backup_20240101_120000.sql --export-path data_exports/data_export_20240101_120000.json
```

## 📋 Common Scenarios

### Scenario 1: Migration Failed in Production
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

### Scenario 2: Data Corruption Suspected
```bash
# 1. Export current data
python rollback_migrations.py export-data

# 2. List all migrations
python rollback_migrations.py list-migrations

# 3. Validate schema
python rollback_migrations.py validate-schema

# 4. If issues found, restore from backup
python rollback_migrations.py backup-restore backups/medguard_backup_*.sql
```

### Scenario 3: Rollback to Previous Version
```bash
# 1. Create backup of current state
python rollback_migrations.py create-backup

# 2. Find target migration
python rollback_migrations.py list-migrations

# 3. Rollback to specific migration
python rollback_migrations.py rollback-migration medications 0017_merge_20250805_2014

# 4. Verify rollback
python rollback_migrations.py verify-state
```

### Scenario 4: Zero-Downtime Rollback
```bash
# 1. Create backup
python rollback_migrations.py create-backup

# 2. Export data
python rollback_migrations.py export-data medications

# 3. Perform gradual rollback
python rollback_migrations.py gradual-rollback medications 0017_merge_20250805_2014 --batch-size 50 --delay-seconds 3

# 4. Verify data integrity
python rollback_migrations.py verify-integrity --export-path data_exports/data_export_*.json

# 5. Send completion notification
python rollback_migrations.py send-notification --notification-type gradual_rollback_completed --notification-message "Gradual rollback completed successfully" --severity info
```

### Scenario 5: Migration Conflicts Detected
```bash
# 1. Check for conflicts in all apps
python rollback_migrations.py resolve-conflicts

# 2. Check specific app if needed
python rollback_migrations.py resolve-conflicts medications

# 3. Review conflict reports
ls conflict_reports/

# 4. Verify resolution
python rollback_migrations.py verify-state
```

### Scenario 6: Data Inconsistencies After Rollback
```bash
# 1. Reconcile data with backup
python rollback_migrations.py reconcile-data backups/backup_20240101_120000.sql

# 2. With export data for comparison
python rollback_migrations.py reconcile-data backups/backup_20240101_120000.sql --export-path data_exports/data_export_20240101_120000.json

# 3. Verify reconciliation
python rollback_migrations.py verify-integrity

# 4. Check final state
python rollback_migrations.py validate-schema
```

## 🔧 Verification Commands

### Check System Health
```bash
# Verify migration state
python rollback_migrations.py verify-state

# Validate database schema
python rollback_migrations.py validate-schema

# List all migrations with status
python rollback_migrations.py list-migrations
```

### Check Migration Dependencies
```bash
# Check dependencies for specific migration
python rollback_migrations.py check-dependencies <app> <migration>

# Example
python rollback_migrations.py check-dependencies medications 0018_remove_prescription_secondary_diagnoses
```

## 📁 File Locations

### Backups
- **Location**: `backups/`
- **Files**: `medguard_backup_*.sql` (PostgreSQL backups)
- **Metadata**: `medguard_backup_*.json` (Backup information)

### Data Exports
- **Location**: `data_exports/`
- **Files**: `data_export_*.json` (Exported data)
- **Checksums**: `data_export_*.checksum` (Data integrity)

### Conflict Reports
- **Location**: `conflict_reports/`
- **Files**: `circular_dependency_*.md` (Circular dependency reports)

### Reconciliation Reports
- **Location**: `reconciliation_reports/`
- **Files**: `reconciliation_*.json` (Reconciliation results)

### Logs
- **File**: `rollback_migrations.log`
- **Console**: Real-time output during operations

## ⚠️ Important Notes

### Before Running Rollback
1. **Always create a backup first**
2. **Stop the application** if in production
3. **Verify disk space** for backups
4. **Check database connectivity**

### During Rollback
1. **Monitor the logs** for errors
2. **Don't interrupt** the process
3. **Have a backup plan** ready

### After Rollback
1. **Verify the restoration** worked
2. **Test application functionality**
3. **Check data integrity**
4. **Document what happened**

## 🆘 Troubleshooting

### Backup Creation Fails
```bash
# Check PostgreSQL connection
psql -h localhost -U medguard -d medguard_db -c "SELECT 1"

# Check disk space
df -h

# Check PostgreSQL service
sudo systemctl status postgresql
```

### Migration Rollback Fails
```bash
# Check migration state
python rollback_migrations.py verify-state

# Check dependencies
python rollback_migrations.py check-dependencies <app> <migration>

# Try emergency recovery
python rollback_migrations.py emergency-recovery
```

### Schema Validation Fails
```bash
# Check for missing tables
python rollback_migrations.py validate-schema

# Run Django checks
python manage.py check --deploy

# Check migration status
python manage.py showmigrations
```

## 📞 Emergency Contacts

### Development Team
- **Lead Developer**: [Contact Info]
- **Database Admin**: [Contact Info]
- **DevOps Engineer**: [Contact Info]

### Escalation Process
1. **Immediate**: Try emergency recovery
2. **15 minutes**: Contact lead developer
3. **30 minutes**: Escalate to database admin
4. **1 hour**: Full team notification

## 🔄 Recovery Checklist

### Pre-Recovery
- [ ] Stop application
- [ ] Create emergency backup
- [ ] Export critical data
- [ ] Document current state

### During Recovery
- [ ] Run emergency recovery
- [ ] Monitor logs
- [ ] Verify each step
- [ ] Document actions taken

### Post-Recovery
- [ ] Verify system health
- [ ] Test application
- [ ] Check data integrity
- [ ] Restart application
- [ ] Monitor for issues
- [ ] Document incident

## 📊 Monitoring

### Key Metrics to Watch
- **Backup success rate**: Should be 100%
- **Rollback frequency**: Should be low
- **Recovery time**: Should be under 30 minutes
- **Data loss incidents**: Should be 0

### Alerts to Set Up
- Migration failures
- Backup failures
- Schema validation errors
- Emergency recovery triggers

## 📚 Additional Resources

- **Full Documentation**: `EMERGENCY_ROLLBACK_README.md`
- **Test Script**: `test_rollback_procedures.py`
- **Django Migration Docs**: https://docs.djangoproject.com/en/stable/topics/migrations/
- **PostgreSQL Backup Docs**: https://www.postgresql.org/docs/current/app-pgdump.html

---

**Remember**: When in doubt, create a backup first and use emergency recovery. It's better to be safe than sorry! 