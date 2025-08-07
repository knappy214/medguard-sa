# MedGuard SA - Wagtail 7.0.2 Healthcare Maintenance Module

## Overview

This comprehensive maintenance module provides specialized tools for maintaining Wagtail 7.0.2 healthcare applications. It ensures optimal performance, security, and compliance with healthcare regulations including HIPAA, POPIA, and South African healthcare standards.

## Features

### 1. Healthcare Content Auditor
- **Medical accuracy validation** - Ensures healthcare content meets medical standards
- **Medical disclaimer checking** - Verifies required disclaimers are present
- **Content freshness auditing** - Identifies outdated medical information
- **Compliance verification** - Checks adherence to healthcare regulations

### 2. Medical Link Checker
- **Trusted medical domain validation** - Ensures links point to authoritative sources
- **Broken link detection** - Identifies and reports non-functional medical resource links
- **Security validation** - Checks for HTTPS usage on medical links
- **Authority compliance** - Validates links against trusted medical authorities

### 3. Medication Image Cleaner
- **Unused image detection** - Identifies orphaned medication images
- **Storage optimization** - Removes unused renditions and files
- **Space calculation** - Reports storage space that can be freed
- **Safe cleanup** - Preserves important medical imagery

### 4. Healthcare Search Index Manager
- **Medical terminology optimization** - Handles medical synonyms and drug variations
- **Multilingual support** - Optimizes for en-ZA and af-ZA locales
- **Index cleanup** - Removes stale search entries
- **Performance optimization** - Rebuilds indexes for healthcare content

### 5. Page Tree Optimizer
- **Structure analysis** - Analyzes page tree depth and organization
- **Orphaned page detection** - Identifies potentially unused pages
- **URL structure optimization** - Ensures consistent healthcare content organization
- **Performance recommendations** - Suggests improvements for better navigation

### 6. Healthcare Backup Verifier
- **Integrity checking** - Verifies backup file completeness
- **Compliance validation** - Ensures backup retention meets healthcare requirements
- **Frequency monitoring** - Checks backup schedule adherence
- **Restoration testing** - Validates backup restoration capabilities

### 7. Healthcare Log Rotator
- **Compliance-aware rotation** - Handles audit logs per healthcare requirements
- **Retention management** - Maintains logs for required periods (7 years for HIPAA)
- **Compression optimization** - Reduces storage usage while preserving accessibility
- **Archive management** - Organizes long-term log storage

### 8. Healthcare Cache Warmer
- **Medical content pre-loading** - Warms cache with frequently accessed medication data
- **Search result caching** - Pre-loads common healthcare search queries
- **API endpoint warming** - Ensures fast response times for critical endpoints
- **Performance optimization** - Reduces load times for healthcare users

### 9. Security Update Checker
- **Vulnerability scanning** - Checks for security issues in dependencies
- **Healthcare-specific monitoring** - Focuses on medical application security
- **Update notifications** - Alerts for critical security patches
- **Compliance reporting** - Generates security status reports

### 10. Healthcare Health Checker
- **System monitoring** - Comprehensive health checks for healthcare uptime
- **Database performance** - Monitors database health and performance
- **Compliance monitoring** - Ensures audit logging and backup availability
- **Resource utilization** - Tracks system resource usage
- **Uptime calculation** - Provides healthcare uptime percentages

## Installation

The maintenance module is already integrated into the MedGuard SA backend. No additional installation is required.

## Usage

### Command Line Interface

Run comprehensive maintenance:
```bash
python manage.py run_healthcare_maintenance
```

Run with dry-run (no changes made):
```bash
python manage.py run_healthcare_maintenance --dry-run
```

Run specific maintenance task:
```bash
python manage.py run_healthcare_maintenance --task content_audit
python manage.py run_healthcare_maintenance --task link_checker
python manage.py run_healthcare_maintenance --task image_cleaner
```

Save maintenance report:
```bash
python manage.py run_healthcare_maintenance --save-report
```

Get JSON output:
```bash
python manage.py run_healthcare_maintenance --output-format json
```

### Programmatic Usage

```python
from maintenance import MaintenanceTaskRunner

# Run all maintenance tasks
runner = MaintenanceTaskRunner()
results = runner.run_all_maintenance(dry_run=True)

# Run specific components
from maintenance import HealthcareContentAuditor, MedicalLinkChecker

auditor = HealthcareContentAuditor()
audit_results = auditor.audit_healthcare_content()

link_checker = MedicalLinkChecker()
link_results = link_checker.check_medical_links()
```

### Scheduled Maintenance

Add to your crontab for automated maintenance:

```bash
# Daily health check at 2 AM
0 2 * * * cd /path/to/medguard && python manage.py run_healthcare_maintenance --task health_checker

# Weekly comprehensive maintenance on Sundays at 3 AM
0 3 * * 0 cd /path/to/medguard && python manage.py run_healthcare_maintenance --save-report

# Monthly security update check on 1st of each month at 4 AM
0 4 1 * * cd /path/to/medguard && python manage.py run_healthcare_maintenance --task security_checker
```

## Configuration

### Trusted Medical Domains

The link checker validates against these trusted medical authorities:
- World Health Organization (who.int)
- Centers for Disease Control (cdc.gov)
- National Institutes of Health (nih.gov)
- PubMed (pubmed.ncbi.nlm.nih.gov)
- South African Health Products Regulatory Authority (sahpra.org.za)
- SA Department of Health (health.gov.za)
- Health Professions Council of SA (hpcsa.co.za)
- Pharmacy Council of SA (pharmcouncil.co.za)

### Log Retention Policies

- **Application logs**: 90 days
- **Security logs**: 7 years (HIPAA compliance)
- **Audit logs**: 7 years (HIPAA compliance)
- **Access logs**: 1 year

### Backup Requirements

- **Frequency**: Daily backups required for healthcare data
- **Retention**: Minimum 7 days of recent backups
- **Verification**: Automated integrity checking
- **Encryption**: Required for PHI/PII data

## Healthcare Compliance Features

### HIPAA Compliance
- 7-year audit log retention
- Automated backup verification
- Security event monitoring
- Access logging and monitoring

### POPIA Compliance
- Data access logging
- Automated cleanup of unused personal data
- Security monitoring and alerting
- Regular compliance health checks

### South African Healthcare Standards
- Integration with local healthcare authorities
- Validation against SA medical guidelines
- Support for local medical terminology
- Compliance with DOH requirements

## Monitoring and Alerting

### Critical Issues
The system identifies and reports:
- Missing medical disclaimers
- Broken medical resource links
- Failed backup integrity checks
- Security vulnerabilities
- System performance issues

### Warning Conditions
- Outdated medical content (>6 months)
- Untrusted medical sources
- Low disk space
- High resource utilization
- Missing audit logs

### Recommendations
Each maintenance run provides:
- Prioritized action items
- Performance optimization suggestions
- Security improvement recommendations
- Compliance enhancement guidance

## Integration with Wagtail 7.0.2

This module leverages Wagtail 7.0.2 features:
- **Universal Listings** for medication catalogs
- **Enhanced search capabilities** for medical terminology
- **Improved admin interface** for healthcare content management
- **Advanced caching** for better performance
- **Comprehensive API** for mobile integration

## Security Considerations

- All maintenance operations are logged
- Sensitive data is handled securely
- Access controls are enforced
- Security updates are monitored
- Compliance requirements are maintained

## Performance Impact

- Maintenance tasks are designed to run during low-traffic periods
- Dry-run mode allows testing without system impact
- Individual tasks can be run separately to minimize load
- Caching strategies optimize performance during maintenance

## Troubleshooting

### Common Issues

1. **Database connection errors**
   - Check PostgreSQL service status
   - Verify connection settings in .env file
   - Ensure database user has required permissions

2. **Cache connection errors**
   - Verify Redis service is running
   - Check cache configuration in settings
   - Test cache connectivity manually

3. **File permission errors**
   - Ensure proper ownership of media/static directories
   - Check write permissions for log directories
   - Verify backup directory accessibility

4. **Memory issues during maintenance**
   - Run individual tasks instead of comprehensive maintenance
   - Increase available memory for large operations
   - Schedule maintenance during low-traffic periods

### Support

For technical support or questions about the maintenance module:
- Check the Django logs for detailed error information
- Review the maintenance report for specific recommendations
- Contact the MedGuard SA development team for assistance

## License

This maintenance module is proprietary software developed for MedGuard SA healthcare platform. All rights reserved.
