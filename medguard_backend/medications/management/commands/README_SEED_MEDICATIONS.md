# Medication Database Seeder

## Overview

The `seed_medications` command is a comprehensive Django management command that populates the MedGuard SA medication database with South African medications, including proper ICD-10 mappings, dosage forms, brand names, manufacturers, and prescription types.

## Features

### 1. South African Medications
- **Diabetes Medications**: Insulin (NOVORAPID, LANTUS), Metformin
- **Cardiovascular Medications**: Statins (LIPITOR), ACE inhibitors (LISINOPRIL), antiplatelets (PLAVIX, ASPIRIN)
- **Respiratory Medications**: Inhalers (VENTOLIN, SERETIDE, SYMBICORT)
- **Psychiatric Medications**: ADHD (RITALIN), antidepressants (ZOLOFT, LEXAPRO), antipsychotics (SEROQUEL)
- **Pain Management**: OTC (PANADO, BRUFEN), prescription (TRAMADOL)
- **Antibiotics**: Penicillins (AMOXIL, AUGMENTIN), fluoroquinolones (CIPRO)
- **Supplements**: Vitamins (VITAMIN D3), omega-3, probiotics

### 2. Proper ICD-10 Mappings
- **E10.4, E11.4, E13.4**: Diabetes with complications
- **F90.9, F90.0, F90.1**: ADHD
- **F32.9, F41.9, F33.9**: Depression and anxiety
- **I10, I11.9, I12.9**: Hypertension
- **J45.901, J44.9, J45.909**: Asthma and COPD
- **M79.3, R52.9**: Pain syndromes
- **N39.0, A09.9**: Infections

### 3. Medication Categories and Types
- **Tablets**: Oral medications (METFORMIN, LIPITOR, PANADO)
- **Capsules**: Encapsulated medications (AMOXIL, OMEGA-3)
- **Injections**: Insulin pens (NOVORAPID FlexPen, LANTUS SoloStar)
- **Inhalers**: Respiratory medications (VENTOLIN, SERETIDE)
- **Supplements**: Vitamins and nutritional supplements

### 4. Brand Names to Generic Names
- **NOVORAPID** = Insulin aspart
- **LANTUS** = Insulin glargine
- **LIPITOR** = Atorvastatin calcium
- **VENTOLIN** = Salbutamol sulfate
- **RITALIN** = Methylphenidate hydrochloride
- **PANADO** = Paracetamol
- **BRUFEN** = Ibuprofen

### 5. Strength Units
- **mg**: Milligrams (500mg, 20mg, 10mg)
- **mcg**: Micrograms (100mcg, 250/25mcg)
- **units/ml**: Insulin units (100 units/ml)
- **IU**: International units (1000IU)
- **billion CFU**: Probiotic colony forming units

### 6. South African Manufacturers
- **Novo Nordisk**: Insulin products
- **Sanofi-Aventis**: LANTUS, PLAVIX
- **Pfizer**: LIPITOR, NORVASC, ZOLOFT
- **GlaxoSmithKline**: VENTOLIN, SERETIDE, PANADO, AMOXIL
- **Aspen Pharmacare**: METFORMIN, LISINOPRIL, TRAMADOL
- **AstraZeneca**: SYMBICORT, SEROQUEL
- **Bayer**: ASPIRIN, CIPRO
- **Dis-Chem**: VITAMIN D3
- **Clicks**: OMEGA-3, PROBIOTIC

### 7. Prescription Types
- **Prescription**: Requires doctor's prescription (insulin, statins, antibiotics)
- **OTC**: Over-the-counter (PANADO, BRUFEN, ASPIRIN)
- **Supplement**: Nutritional supplements (VITAMIN D3, OMEGA-3)

### 8. Storage Instructions
- **Refrigerated**: Insulin, omega-3, probiotics (2-8°C)
- **Room temperature**: Most tablets and capsules (15-30°C)
- **Special handling**: Inhalers (away from heat and direct sunlight)

### 9. Contraindications and Side Effects
- **Diabetes medications**: Hypoglycemia, kidney disease
- **Cardiovascular**: Liver disease, pregnancy, bleeding disorders
- **Psychiatric**: MAOI interactions, bipolar disorder
- **Pain medications**: Liver disease, peptic ulcers
- **Antibiotics**: Penicillin allergy, pregnancy

### 10. Sample Data Creation
- **Medication Schedules**: Daily dosing schedules for patients
- **Medication Logs**: Adherence tracking with timestamps
- **Stock Transactions**: Purchase and inventory management

## Usage

### Basic Seeding
```bash
python manage.py seed_medications
```

### Clear Existing Data
```bash
python manage.py seed_medications --clear
```

### Create Sample Data
```bash
python manage.py seed_medications --create-sample-schedules --create-sample-logs --create-sample-transactions
```

### Full Setup
```bash
python manage.py seed_medications --clear --create-sample-schedules --create-sample-logs --create-sample-transactions
```

## Command Options

| Option | Description |
|--------|-------------|
| `--clear` | Clear existing medications before seeding |
| `--create-sample-schedules` | Create sample medication schedules for testing |
| `--create-sample-logs` | Create sample medication logs for testing |
| `--create-sample-transactions` | Create sample stock transactions for testing |

## Output Summary

The command provides a detailed summary of created data:

```
Medication Database Seeding Completed Successfully!
• Diabetes Medications: 3 created
• Cardiovascular Medications: 5 created
• Respiratory Medications: 3 created
• Psychiatric Medications: 4 created
• Pain Management: 3 created
• Antibiotics: 3 created
• Supplements/OTC: 3 created
• Total Medications: 24
• Sample Schedules: 5 created
• Sample Logs: 5 created
• Sample Transactions: 10 created
```

## Database Schema Integration

The seeder integrates with the existing MedGuard SA database schema:

- **Medication Model**: Core medication information
- **MedicationSchedule Model**: Patient dosing schedules
- **MedicationLog Model**: Adherence tracking
- **StockTransaction Model**: Inventory management
- **User Model**: Patient and pharmacist accounts

## Safety Features

- **Transaction Atomicity**: All operations wrapped in database transactions
- **Error Handling**: Graceful failure with detailed error messages
- **Data Validation**: Proper data types and constraints
- **Duplicate Prevention**: Clear existing data option
- **User Creation**: Automatic test user creation for sample data

## Testing

The seeder creates realistic test data for:
- **Unit Testing**: Medication model validation
- **Integration Testing**: Schedule and log workflows
- **UI Testing**: Frontend medication displays
- **API Testing**: REST endpoint functionality

## Maintenance

### Adding New Medications
1. Add medication data to appropriate category method
2. Include proper ICD-10 codes
3. Add manufacturer information
4. Specify storage requirements
5. Document contraindications

### Updating Existing Data
1. Use `--clear` flag to remove existing data
2. Modify medication data in seeder methods
3. Re-run command with updated data

### Extending Categories
1. Create new category method (e.g., `_create_oncology_medications`)
2. Add category to main `handle` method
3. Include in summary statistics

## Compliance

The seeder follows MedGuard SA compliance requirements:
- **HIPAA**: No real patient data
- **ICD-10**: Standard diagnosis codes
- **South African Regulations**: Local medication names and manufacturers
- **Data Privacy**: Test data only, no PHI

## Future Enhancements

Potential improvements for the seeder:
- **ICD-10 Validation**: Real-time code validation
- **Drug Interactions**: Interaction database integration
- **Pricing Data**: South African medication pricing
- **Image Assets**: Medication packaging images
- **Multi-language**: Afrikaans medication names
- **Batch Processing**: Large dataset handling
- **API Integration**: External medication databases 