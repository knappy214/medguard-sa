# MedGuard SA Database Initialization

This document describes the comprehensive database initialization script for the MedGuard SA project.

## Overview

The `initialize_database.py` script provides a complete database setup solution that:

1. **Drops and recreates the database** (development only)
2. **Runs all migrations** in the correct order
3. **Creates superuser account** for admin access
4. **Seeds the database** with prescription medications
5. **Creates sample patient data** for testing
6. **Initializes medication schedules and stock levels**
7. **Sets up OCR processing cache tables**
8. **Creates audit log entries for compliance**
9. **Initializes reporting and analytics tables**
10. **Verifies all data integrity constraints are met**

## Features

### 🔧 Database Management
- **Safe Environment Check**: Prevents dangerous operations in production
- **Database Drop/Recreate**: Clean slate setup for development
- **Migration Management**: Automatic migration detection and execution
- **Connection Verification**: Ensures database connectivity

### 👤 User Management
- **Superuser Creation**: Admin account with full privileges
- **Sample Patients**: Realistic patient data with medical records
- **Caregivers**: Family member and professional caregiver accounts
- **Healthcare Providers**: Doctor and pharmacist accounts
- **Multi-language Support**: English and Afrikaans users

### 💊 Medication System
- **Comprehensive Medication Data**: 24+ South African medications
- **Prescription Types**: Schedule 1-7, OTC, supplements
- **Medical Categories**: Diabetes, cardiovascular, respiratory, psychiatric
- **Stock Management**: Inventory tracking and alerts
- **Sample Schedules**: Medication timing and dosage schedules
- **Adherence Logs**: Medication intake tracking
- **Stock Transactions**: Purchase and dispensing records

### 📋 Sample Data
- **Patient Profiles**: Complete medical information
- **Emergency Contacts**: Family and healthcare contacts
- **Prescription Records**: Active prescriptions with renewals
- **Notification Preferences**: Email, SMS, and push settings
- **Geographic Data**: South African addresses and provinces

### 🔄 Medication Management
- **Medication Schedules**: Automated schedule creation with varied timing
- **Stock Management**: Stock level monitoring and low-stock alerts
- **Adherence Tracking**: Medication intake logging and compliance monitoring
- **Inventory Analytics**: Stock turnover and usage analytics

### 🔍 OCR Processing
- **Cache Tables**: Optimized OCR processing with image hash caching
- **Sample Data**: Pre-processed prescription images for testing
- **Performance Indexes**: Fast lookup and confidence score filtering
- **Processing Metrics**: Response time and accuracy tracking

### 📊 Analytics & Reporting
- **Adherence Analytics**: Patient medication compliance tracking
- **Stock Analytics**: Inventory turnover and forecasting
- **User Activity Analytics**: System usage and engagement metrics
- **Performance Indexes**: Optimized query performance

### 🔒 Security & Compliance
- **Audit Logging**: Comprehensive HIPAA-compliant audit trails
- **Security Events**: User activity and system access monitoring
- **Data Integrity**: Automated constraint validation and verification
- **Compliance Reporting**: Regulatory compliance data structures

## Usage

### Basic Initialization
```bash
cd medguard_backend
python initialize_database.py
```

### Advanced Options

#### Drop and Recreate Database
```bash
python initialize_database.py --drop-db
```
⚠️ **Warning**: This will delete all existing data!

#### Skip Medication Seeding
```bash
python initialize_database.py --skip-seed
```

#### Skip Patient Creation
```bash
python initialize_database.py --skip-patients
```

#### Combined Options
```bash
python initialize_database.py --drop-db --skip-patients
```

## Prerequisites

### Database Setup
1. **PostgreSQL Installation**: Ensure PostgreSQL is installed and running
2. **Database User**: Create the `medguard_user` with appropriate permissions
3. **Environment Variables**: Configure database connection in `.env` file

### Environment Configuration
```bash
# .env file
DB_NAME=medguard_sa
DB_USER=medguard_user
DB_PASSWORD=medguard123
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### Python Dependencies
```bash
pip install -r requirements.txt
```

## Output

### Console Output
The script provides detailed progress information:

```
🚀 Starting MedGuard SA Database Initialization
Timestamp: 2025-01-15 10:30:00

============================================================
 ENVIRONMENT CHECK
============================================================
Database: medguard_sa
Host: localhost
Port: 5432
User: medguard_user

============================================================
 RUNNING MIGRATIONS
============================================================
Running makemigrations...
Running migrate...
✅ Migrations completed successfully

============================================================
 CREATING SUPERUSER
============================================================
✅ Superuser created successfully
   Username: admin
   Email: admin@medguard-sa.com
   Password: admin123

============================================================
 SEEDING MEDICATIONS
============================================================
✅ Medication seeding completed

============================================================
 CREATING SAMPLE PATIENTS
============================================================
✅ Created patient: John Doe (john.doe)
✅ Created patient: Maria Smith (maria.smith)
✅ Created patient: Piet van der Merwe (piet.van.der.merwe)
✅ Created caregiver: Jane Caregiver (jane.caregiver)
✅ Created healthcare provider: Sarah Johnson (dr.johnson)
✅ Created 3 patients, 2 caregivers, 2 providers

============================================================
 VERIFICATION
============================================================
✅ Database connected: PostgreSQL 15.1
✅ Users: 8 total
   - Patients: 3
   - Caregivers: 2
   - Healthcare Providers: 3
   - Superusers: 1
✅ Medications: 24 total
   - Prescription: 18
   - Over-the-counter: 6
✅ Schedules: 15
✅ Logs: 5
✅ Transactions: 10
✅ Prescriptions: 6
✅ Stock Alerts: 3
✅ OCR Cache Entries: 2
✅ Adherence Analytics: 42
✅ Stock Analytics: 150
✅ Activity Analytics: 35
✅ Audit Logs: 15
✅ Security Events: 8

============================================================
 INITIALIZATION COMPLETE
============================================================
🎉 MedGuard SA Database Initialization Completed Successfully!

📋 Access Information:
   Admin URL: http://localhost:8000/admin/
   Username: admin
   Password: admin123

🔧 Next Steps:
   1. Start the development server: python manage.py runserver
   2. Access the admin interface
   3. Review and customize the seeded data
   4. Test the medication management features
```

### Log File
The script creates a detailed log file: `database_initialization.log`

## Created Data

### Superuser Account
- **Username**: `admin`
- **Email**: `admin@medguard-sa.com`
- **Password**: `admin123`
- **Type**: Healthcare Provider with full admin privileges

### Sample Patients

#### John Doe (English)
- **Username**: `john.doe`
- **Email**: `john.doe@example.com`
- **Password**: `patient123`
- **Age**: 45 years
- **Location**: Cape Town, Western Cape
- **Provider**: Dr. Sarah Johnson
- **Language**: English

#### Maria Smith (English)
- **Username**: `maria.smith`
- **Email**: `maria.smith@example.com`
- **Password**: `patient123`
- **Age**: 62 years
- **Location**: Johannesburg, Gauteng
- **Provider**: Dr. Michael Brown
- **Language**: English

#### Piet van der Merwe (Afrikaans)
- **Username**: `piet.van.der.merwe`
- **Email**: `piet.vandermerwe@example.com`
- **Password**: `patient123`
- **Age**: 38 years
- **Location**: Pretoria, Gauteng
- **Provider**: Dr. Anna van Wyk
- **Language**: Afrikaans

### Sample Caregivers
- **Jane Caregiver** (`jane.caregiver` / `caregiver123`) - English
- **Koos Versorger** (`koos.versorger` / `caregiver123`) - Afrikaans

### Sample Healthcare Providers
- **Dr. Sarah Johnson** (`dr.johnson` / `provider123`)
- **Dr. Michael Brown** (`dr.brown` / `provider123`)

### Medications (24 Total)

#### Diabetes Medications (3)
- NOVORAPID FlexPen (Insulin aspart)
- LANTUS SoloStar Pen (Insulin glargine)
- METFORMIN 500mg (Metformin hydrochloride)

#### Cardiovascular Medications (5)
- LIPITOR 20mg (Atorvastatin calcium)
- NORVASC 5mg (Amlodipine besylate)
- LISINOPRIL 10mg (Lisinopril)
- PLAVIX 75mg (Clopidogrel bisulfate)
- ASPIRIN 100mg (Acetylsalicylic acid)

#### Respiratory Medications (3)
- VENTOLIN Inhaler (Salbutamol sulfate)
- SERETIDE 250/25 Inhaler (Fluticasone + Salmeterol)
- SYMBICORT 160/4.5 Inhaler (Budesonide + Formoterol)

#### Psychiatric Medications (4)
- RITALIN 10mg (Methylphenidate hydrochloride)
- ZOLOFT 50mg (Sertraline hydrochloride)
- LEXAPRO 10mg (Escitalopram oxalate)
- SEROQUEL 25mg (Quetiapine fumarate)

#### Pain Management (3)
- PANADO 500mg (Paracetamol)
- BRUFEN 400mg (Ibuprofen)
- TRAMADOL 50mg (Tramadol hydrochloride)

#### Antibiotics (3)
- AMOXIL 500mg (Amoxicillin trihydrate)
- AUGMENTIN 625mg (Amoxicillin + Clavulanic acid)
- CIPRO 500mg (Ciprofloxacin hydrochloride)

#### Supplements/OTC (3)
- VITAMIN D3 1000IU (Cholecalciferol)
- OMEGA-3 1000mg (Fish Oil)
- PROBIOTIC 10 Billion CFU (Lactobacillus + Bifidobacterium)

### Analytics & Reporting Data

#### Medication Adherence Analytics (42 records)
- **7-day adherence tracking** for 3 patients × 2 medications
- **Compliance rates** ranging from 50% to 100%
- **Average delay metrics** for medication timing
- **Missed dose tracking** for intervention planning

#### Stock Analytics (150 records)
- **30-day inventory tracking** for 5 medications
- **Stock turnover rates** and usage patterns
- **Days of stock remaining** calculations
- **Restock scheduling** based on usage trends

#### User Activity Analytics (35 records)
- **7-day activity tracking** for 5 users
- **Login frequency** and session duration
- **Feature usage** (medication logs, prescriptions, alerts)
- **Engagement metrics** for user experience optimization

### Security & Compliance Data

#### Audit Logs (15 entries)
- **System initialization** audit trail
- **User creation** events for all accounts
- **Medication creation** audit records
- **HIPAA-compliant** event logging

#### Security Events (8 entries)
- **Login success** events for sample users
- **Data access** monitoring records
- **Medication dispensing** audit trails
- **Prescription renewal** security events

### OCR Processing Cache (2 entries)
- **Sample prescription images** with extracted text
- **Confidence scores** and processing times
- **JSON-structured** medication data
- **Performance metrics** for optimization

## Safety Features

### Environment Protection
- **Production Check**: Prevents dangerous operations in production
- **Debug Mode Requirement**: Database drop only allowed in DEBUG mode
- **Confirmation Prompts**: Clear warnings before destructive operations

### Data Integrity
- **Transaction Atomicity**: All operations wrapped in database transactions
- **Duplicate Prevention**: Checks for existing data before creation
- **Error Handling**: Graceful failure with detailed error messages
- **Rollback Support**: Automatic rollback on failure
- **Constraint Validation**: 15+ integrity checks for data quality
- **Referential Integrity**: Foreign key relationships validated
- **Business Rule Validation**: Medical and pharmaceutical compliance rules

### Logging
- **Comprehensive Logging**: All operations logged to file and console
- **Progress Tracking**: Clear section headers and progress indicators
- **Error Details**: Detailed error messages for troubleshooting
- **Verification**: Final verification of all created data

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Check database user permissions
psql -U postgres -c "SELECT usename, usesuper FROM pg_user;"

# Verify .env configuration
cat .env | grep DB_
```

#### Migration Errors
```bash
# Check migration status
python manage.py showmigrations

# Reset migrations (if needed)
python manage.py migrate --fake-initial

# Create fresh migrations
python manage.py makemigrations --empty
```

#### Permission Denied
```bash
# Check file permissions
chmod +x initialize_database.py

# Check database user permissions
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE medguard_sa TO medguard_user;"
```

#### Import Errors
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check Django settings
python manage.py check

# Verify virtual environment
source venv/bin/activate  # or your virtual environment
```

### Recovery Options

#### Reset Everything
```bash
python initialize_database.py --drop-db
```

#### Skip Problematic Steps
```bash
python initialize_database.py --skip-seed --skip-patients
```

#### Manual Recovery
```bash
# Drop database manually
dropdb medguard_sa

# Recreate database
createdb medguard_sa

# Run migrations only
python manage.py migrate

# Create superuser manually
python manage.py createsuperuser
```

## Development Workflow

### First-Time Setup
1. **Clone Repository**: `git clone <repository-url>`
2. **Install Dependencies**: `pip install -r requirements.txt`
3. **Configure Environment**: Set up `.env` file
4. **Initialize Database**: `python initialize_database.py --drop-db`
5. **Start Development Server**: `python manage.py runserver`

### Regular Development
```bash
# Make model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Re-seed medications (if needed)
python manage.py seed_medications --clear

# Add sample data
python initialize_database.py --skip-seed
```

### Testing
```bash
# Run tests
python manage.py test

# Test with fresh data
python initialize_database.py --drop-db
python manage.py test
```

## Production Considerations

### Security
- **Change Default Passwords**: Update all default passwords
- **Environment Variables**: Use secure secret keys
- **Database Permissions**: Restrict database user privileges
- **SSL Connection**: Enable SSL for database connections

### Data Management
- **Backup Strategy**: Implement regular database backups
- **Migration Strategy**: Test migrations in staging environment
- **Data Validation**: Validate all seeded data
- **Monitoring**: Monitor database performance and health

### Compliance
- **HIPAA Compliance**: Ensure all data handling meets HIPAA requirements
- **Audit Logging**: Maintain comprehensive audit trails
- **Data Retention**: Implement appropriate data retention policies
- **Access Controls**: Enforce role-based access controls

## Support

For issues or questions:

1. **Check Logs**: Review `database_initialization.log`
2. **Verify Environment**: Ensure all prerequisites are met
3. **Test Incrementally**: Use skip options to isolate issues
4. **Consult Documentation**: Review Django and PostgreSQL documentation

## Contributing

When modifying the initialization script:

1. **Test Thoroughly**: Test all scenarios and edge cases
2. **Update Documentation**: Keep this README current
3. **Follow Patterns**: Maintain consistent logging and error handling
4. **Version Control**: Commit changes with descriptive messages 