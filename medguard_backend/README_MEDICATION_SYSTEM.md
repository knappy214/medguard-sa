# MedGuard SA Medication Management System

A comprehensive Django-based medication management system designed for healthcare applications with robust tracking, scheduling, and alerting capabilities.

## 🏗️ System Architecture

### Models Overview

The system consists of five core models:

1. **User** - Extended AbstractUser with healthcare-specific fields
2. **Medication** - Medication inventory and information management
3. **MedicationSchedule** - Patient medication scheduling and timing
4. **MedicationLog** - Adherence tracking and history
5. **StockAlert** - Inventory monitoring and alerting system

## 👤 User Model

### Features
- **Custom User Types**: Patient, Caregiver, Healthcare Provider, Administrator
- **Medical Information**: Medical record numbers, healthcare provider details
- **Emergency Contacts**: Complete emergency contact information
- **Notification Preferences**: Email, SMS, and push notification settings
- **Accessibility**: Language preferences and timezone support

### Key Fields
```python
# User Types
PATIENT = 'patient'
CAREGIVER = 'caregiver'
HEALTHCARE_PROVIDER = 'healthcare_provider'
ADMIN = 'admin'

# Medical Information
medical_record_number = CharField(unique=True)
primary_healthcare_provider = CharField()
emergency_contact_name = CharField()
emergency_contact_phone = CharField()

# Preferences
preferred_language = CharField(choices=[('en', 'English'), ('af', 'Afrikaans')])
timezone = CharField(default='UTC')
email_notifications = BooleanField(default=True)
```

### Validation
- Medical record numbers automatically generated for patients (MRN-XXXXXXXX format)
- Emergency contact validation (name and phone must be provided together)
- Phone number format validation with international support

## 💊 Medication Model

### Features
- **Comprehensive Medication Types**: Tablets, capsules, liquids, injections, etc.
- **Stock Management**: Pill count tracking with low stock thresholds
- **Safety Information**: Side effects, contraindications, storage instructions
- **Expiration Tracking**: Automatic expiration date monitoring
- **Manufacturer Information**: Complete medication sourcing details

### Key Fields
```python
# Medication Types
TABLET = 'tablet'
CAPSULE = 'capsule'
LIQUID = 'liquid'
INJECTION = 'injection'
INHALER = 'inhaler'
# ... and more

# Stock Management
pill_count = PositiveIntegerField(default=0)
low_stock_threshold = PositiveIntegerField(default=10)
expiration_date = DateField()

# Safety Information
side_effects = TextField()
contraindications = TextField()
storage_instructions = TextField()
```

### Properties
- `is_low_stock`: Checks if medication is below threshold
- `is_expired`: Checks if medication has expired
- `is_expiring_soon`: Checks if medication expires within 30 days

## 📅 MedicationSchedule Model

### Features
- **Flexible Timing**: Morning, noon, night, or custom times
- **Weekly Scheduling**: Individual day selection for complex schedules
- **Dosage Tracking**: Precise dosage amounts with validation
- **Status Management**: Active, inactive, paused, completed states
- **Date Ranges**: Start and end dates for temporary medications

### Key Fields
```python
# Timing Options
MORNING = 'morning'
NOON = 'noon'
NIGHT = 'night'
CUSTOM = 'custom'

# Schedule Information
timing = CharField(choices=Timing.choices)
custom_time = TimeField()
dosage_amount = DecimalField()
frequency = CharField()

# Days of Week
monday = BooleanField(default=True)
tuesday = BooleanField(default=True)
# ... all days

# Status
ACTIVE = 'active'
INACTIVE = 'inactive'
PAUSED = 'paused'
COMPLETED = 'completed'
```

### Properties
- `is_active`: Checks if schedule is currently active
- `should_take_today`: Checks if medication should be taken today

## 📊 MedicationLog Model

### Features
- **Adherence Tracking**: Complete medication adherence history
- **Timing Analysis**: On-time vs. late medication tracking
- **Dosage Recording**: Actual vs. prescribed dosage tracking
- **Side Effect Monitoring**: Patient-reported side effects
- **Adherence Scoring**: Automatic adherence score calculation

### Key Fields
```python
# Status Options
TAKEN = 'taken'
MISSED = 'missed'
SKIPPED = 'skipped'
PARTIAL = 'partial'

# Timing Information
scheduled_time = DateTimeField()
actual_time = DateTimeField()
dosage_taken = DecimalField()

# Observations
notes = TextField()
side_effects = TextField()
```

### Properties
- `is_on_time`: Checks if medication was taken within 1 hour of scheduled time
- `adherence_score`: Calculates adherence percentage (100% for on-time, 80% for late, etc.)

## 🚨 StockAlert Model

### Features
- **Multiple Alert Types**: Low stock, out of stock, expiring soon, expired
- **Priority Levels**: Low, medium, high, critical priority system
- **Status Tracking**: Active, acknowledged, resolved, dismissed states
- **Resolution Tracking**: Complete alert resolution workflow
- **User Attribution**: Track who created and resolved alerts

### Key Fields
```python
# Alert Types
LOW_STOCK = 'low_stock'
OUT_OF_STOCK = 'out_of_stock'
EXPIRING_SOON = 'expiring_soon'
EXPIRED = 'expired'

# Priority Levels
LOW = 'low'
MEDIUM = 'medium'
HIGH = 'high'
CRITICAL = 'critical'

# Status
ACTIVE = 'active'
ACKNOWLEDGED = 'acknowledged'
RESOLVED = 'resolved'
DISMISSED = 'dismissed'
```

### Methods
- `acknowledge(user)`: Acknowledge alert with user attribution
- `resolve(notes)`: Resolve alert with resolution notes
- `dismiss()`: Dismiss alert without resolution

## 🔗 Relationships

### User Relationships
```python
# User -> MedicationSchedule (One-to-Many)
patient = ForeignKey(User, related_name='medication_schedules')

# User -> MedicationLog (One-to-Many)
patient = ForeignKey(User, related_name='medication_logs')

# User -> StockAlert (One-to-Many)
created_by = ForeignKey(User, related_name='created_alerts')
acknowledged_by = ForeignKey(User, related_name='acknowledged_alerts')
```

### Medication Relationships
```python
# Medication -> MedicationSchedule (One-to-Many)
medication = ForeignKey(Medication, related_name='schedules')

# Medication -> MedicationLog (One-to-Many)
medication = ForeignKey(Medication, related_name='logs')

# Medication -> StockAlert (One-to-Many)
medication = ForeignKey(Medication, related_name='stock_alerts')
```

### Schedule Relationships
```python
# MedicationSchedule -> MedicationLog (One-to-Many)
schedule = ForeignKey(MedicationSchedule, related_name='logs')
```

## 🛡️ Validation & Security

### Model Validation
- **Dosage Validation**: Positive decimal values with minimum thresholds
- **Date Validation**: Future dates for expiration, logical date ranges
- **Stock Validation**: Non-negative stock levels, positive thresholds
- **Time Validation**: Custom times required for custom timing
- **User Type Validation**: Patient-only restrictions for certain fields

### Data Integrity
- **Cascade Deletes**: Proper relationship cleanup
- **Unique Constraints**: Medical record numbers, medication names
- **Index Optimization**: Database indexes for performance
- **Audit Trails**: Created/updated timestamps on all models

## 🎛️ Admin Interface

### User Admin
- **Comprehensive User Management**: All user types and fields
- **Medical Information**: Dedicated sections for healthcare data
- **Contact Management**: Emergency contact and provider information
- **Preference Settings**: Notification and language preferences

### Medication Admin
- **Stock Monitoring**: Visual indicators for low stock and expiration
- **Bulk Actions**: Mark expired, update stock levels
- **Safety Information**: Side effects and contraindications management
- **Manufacturer Tracking**: Complete medication sourcing

### Schedule Admin
- **Schedule Management**: Activate/deactivate schedules
- **Timing Visualization**: Clear display of medication timing
- **Patient Tracking**: Patient-specific schedule management
- **Status Monitoring**: Active status and today's requirements

### Log Admin
- **Adherence Tracking**: Visual adherence scores and timing
- **Bulk Actions**: Mark taken/missed for multiple logs
- **Patient History**: Complete medication history
- **Side Effect Monitoring**: Patient-reported side effects

### Alert Admin
- **Alert Management**: Acknowledge, resolve, dismiss alerts
- **Priority Handling**: Critical alert identification
- **Resolution Tracking**: Complete alert workflow
- **Stock Monitoring**: Real-time stock level tracking

## 🚀 Usage Examples

### Creating a Patient
```python
from users.models import User

patient = User.objects.create_user(
    username='john.doe',
    email='john.doe@example.com',
    password='secure_password',
    first_name='John',
    last_name='Doe',
    user_type=User.UserType.PATIENT,
    phone_number='+27123456789',
    date_of_birth='1980-01-01'
)
# Medical record number automatically generated
```

### Adding a Medication
```python
from medications.models import Medication

medication = Medication.objects.create(
    name='Paracetamol',
    generic_name='Acetaminophen',
    strength='500mg',
    dosage_unit='mg',
    medication_type=Medication.MedicationType.TABLET,
    pill_count=100,
    low_stock_threshold=10,
    manufacturer='Generic Pharma Ltd',
    expiration_date='2025-12-31'
)
```

### Creating a Schedule
```python
from medications.models import MedicationSchedule

schedule = MedicationSchedule.objects.create(
    patient=patient,
    medication=medication,
    timing=MedicationSchedule.Timing.MORNING,
    dosage_amount=1.0,
    frequency='daily',
    start_date='2024-01-01',
    instructions='Take with food'
)
```

### Logging Medication Taken
```python
from medications.models import MedicationLog
from django.utils import timezone

log = MedicationLog.objects.create(
    patient=patient,
    medication=medication,
    schedule=schedule,
    scheduled_time=timezone.now(),
    actual_time=timezone.now(),
    status=MedicationLog.Status.TAKEN,
    dosage_taken=1.0
)
```

### Creating Stock Alert
```python
from medications.models import StockAlert

alert = StockAlert.objects.create(
    medication=medication,
    created_by=admin_user,
    alert_type=StockAlert.AlertType.LOW_STOCK,
    priority=StockAlert.Priority.HIGH,
    title='Low Stock Alert',
    message=f'{medication.name} is running low. Current stock: {medication.pill_count}',
    current_stock=medication.pill_count,
    threshold_level=medication.low_stock_threshold
)
```

## 📊 Query Examples

### Patient Adherence Analysis
```python
# Get adherence statistics for a patient
patient_logs = MedicationLog.objects.filter(patient=patient)
total_doses = patient_logs.count()
taken_doses = patient_logs.filter(status=MedicationLog.Status.TAKEN).count()
adherence_rate = (taken_doses / total_doses) * 100 if total_doses > 0 else 0
```

### Low Stock Medications
```python
# Find all medications with low stock
low_stock_medications = Medication.objects.filter(
    pill_count__lte=models.F('low_stock_threshold')
)
```

### Active Schedules for Today
```python
# Get all active schedules for today
from datetime import date
today = date.today()
active_schedules = MedicationSchedule.objects.filter(
    status=MedicationSchedule.Status.ACTIVE,
    start_date__lte=today,
    end_date__isnull=True | models.Q(end_date__gte=today)
)
```

### Expiring Medications
```python
# Find medications expiring within 30 days
from datetime import timedelta
expiring_soon = Medication.objects.filter(
    expiration_date__lte=date.today() + timedelta(days=30),
    expiration_date__gt=date.today()
)
```

## 🔧 Customization

### Adding New Medication Types
```python
class MedicationType(models.TextChoices):
    TABLET = 'tablet', _('Tablet')
    CAPSULE = 'capsule', _('Capsule')
    # Add new types here
    SUPPOSITORY = 'suppository', _('Suppository')
```

### Custom Validation Rules
```python
def clean(self):
    """Add custom validation logic."""
    if self.dosage_amount > 10:
        raise ValidationError('Dosage amount cannot exceed 10 units')
```

### Custom Properties
```python
@property
def days_until_expiry(self):
    """Calculate days until medication expires."""
    if self.expiration_date:
        return (self.expiration_date - date.today()).days
    return None
```

## 🧪 Testing

### Model Testing
```python
from django.test import TestCase
from users.models import User
from medications.models import Medication, MedicationSchedule

class MedicationModelTest(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username='test_patient',
            user_type=User.UserType.PATIENT
        )
        self.medication = Medication.objects.create(
            name='Test Medication',
            strength='100mg'
        )
    
    def test_medication_creation(self):
        self.assertEqual(self.medication.name, 'Test Medication')
        self.assertTrue(self.medication.is_low_stock)
```

## 📚 API Integration

The models are designed to work seamlessly with Django REST Framework:

```python
from rest_framework import serializers

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'

class MedicationScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationSchedule
        fields = '__all__'
```

## 🔒 Security Considerations

- **User Type Restrictions**: Proper user type validation
- **Data Privacy**: Sensitive medical information protection
- **Audit Logging**: Complete change tracking
- **Access Control**: Role-based permissions
- **Data Validation**: Comprehensive input validation

## 🚀 Deployment

### Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Load Sample Data
```bash
python manage.py loaddata sample_medications
```

## 📈 Performance Optimization

- **Database Indexes**: Optimized for common queries
- **Select Related**: Efficient relationship loading
- **Bulk Operations**: Efficient batch processing
- **Caching**: Redis integration for frequently accessed data

## 🔄 Future Enhancements

- **Real-time Notifications**: WebSocket integration
- **Mobile App Support**: API endpoints for mobile applications
- **Advanced Analytics**: Detailed adherence analytics
- **Integration APIs**: Pharmacy and healthcare provider integrations
- **Machine Learning**: Predictive adherence modeling

This medication management system provides a robust foundation for healthcare applications with comprehensive tracking, scheduling, and alerting capabilities while maintaining data integrity and security standards. 