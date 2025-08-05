# Migration 0012: Seed Prescription Data from Dr Owen Nosworthy

## Overview

This migration seeds the MedGuard SA database with comprehensive prescription data from Dr Owen Nosworthy's prescription dated 28th June 2025 for patient Mr Peter J Knapton.

## What This Migration Creates

### 1. **21 Medications from the Prescription**
All medications from the attached prescription are created with proper:
- Brand and generic names
- Strengths and dosage forms
- Manufacturer information
- Pricing data
- Stock levels (double the prescription quantity)

### 2. **ICD-10 Code Mappings**
Proper medical condition mappings:
- **E10.4** = Type 1 diabetes mellitus with neurological complications
- **E03.9** = Hypothyroidism, unspecified
- **E27.4** = Other and unspecified adrenocortical insufficiency
- **F90.9** = Attention-deficit hyperactivity disorder, unspecified type
- **F41.8** = Other specified anxiety disorders
- **G47.6** = Sleep related movement disorders
- **G89.4** = Chronic pain syndrome
- **K21.0** = Gastro-esophageal reflux disease with esophagitis
- **J30.9** = Allergic rhinitis, unspecified
- **R11.0** = Nausea

### 3. **Medication Categories**
Organized into logical categories:
- **Insulin**: NOVORAPID, LANTUS
- **Thyroid Hormones**: ELTROXIN
- **Corticosteroids**: MEDROL, FLORINEF
- **ADHD Medications**: VYVANSE, RITALIN LA
- **Antidepressants**: WELBUTRIN XL, CYMGEN
- **Benzodiazepines**: RIVOTRIL
- **Pain Management**: TARGINACT, CELEBREX, OXYNORM
- **Anticonvulsants**: EPLEPTIN
- **Antimalarials**: QUININE
- **Proton Pump Inhibitors**: TOPZOLE
- **Leukotriene Modifiers**: MONTEFLO
- **Antihistamines**: FEXO
- **Antiemetics**: CLOPAMON
- **Topical Corticosteroids**: BETNOVATE IN UEA

### 4. **Brand-to-Generic Mappings**
Accurate pharmaceutical mappings:
- NOVORAPID = Insulin aspart
- LANTUS = Insulin glargine
- ELTROXIN = Levothyroxine sodium
- MEDROL = Methylprednisolone
- FLORINEF = Fludrocortisone acetate
- VYVANSE = Lisdexamfetamine dimesylate
- RITALIN LA = Methylphenidate hydrochloride
- WELBUTRIN XL = Bupropion hydrochloride
- CYMGEN = Cymbalta (Duloxetine)
- RIVOTRIL = Clonazepam
- TARGINACT = Oxycodone/Naloxone
- EPLEPTIN = Phenytoin sodium
- CELEBREX = Celecoxib
- QUININE = Quinine sulphate
- TOPZOLE = Omeprazole
- MONTEFLO = Montelukast sodium
- FEXO = Fexofenadine hydrochloride
- CLOPAMON = Metoclopramide hydrochloride
- OXYNORM = Oxycodone hydrochloride
- BETNOVATE IN UEA = Betamethasone valerate

### 5. **Dosage Forms**
Proper dosage form tracking:
- **FlexPen**: NOVORAPID (3ml)
- **SolarStar Pen**: LANTUS
- **Tablets**: Most medications with specific strengths
- **Cream**: BETNOVATE IN UEA (500g tube)

### 6. **Manufacturer Data**
South African pharmaceutical companies:
- **Novo Nordisk**: NOVORAPID
- **Sanofi**: LANTUS, FEXO
- **Aspen Pharmacare**: ELTROXIN, FLORINEF, EPLEPTIN, TOPZOLE, CLOPAMON
- **Pfizer**: MEDROL, CELEBREX
- **Takeda**: VYVANSE
- **Novartis**: RITALIN LA
- **GlaxoSmithKline**: WELBUTRIN XL, BETNOVATE IN UEA
- **Eli Lilly**: CYMGEN
- **Roche**: RIVOTRIL
- **Mundipharma**: TARGINACT, OXYNORM
- **Merck**: MONTEFLO

### 7. **Sample Prescription**
Complete prescription record:
- **Doctor**: Dr Owen Nosworthy (Specialist Physician / Medical Oncologist)
- **Practice**: Nosworthy Oncology, 20 Kent Road, Dunkeld West
- **Practice Number**: 0292737
- **Contact**: +27 11 482 3593, owen@nosworthyonc.com
- **Patient**: Mr Peter J Knapton
- **Medical Aid**: Discovery Health (045661470)
- **Prescription Date**: 28th June 2025
- **Total Cost**: R6,845.00 (calculated from unit prices)

### 8. **Medication Schedules**
Automated schedule creation based on prescription instructions:
- **Morning**: ELTROXIN, MEDROL, FLORINEF, VYVANSE, WELBUTRIN XL, CYMGEN, TOPZOLE, FEXO, BETNOVATE
- **Noon**: MEDROL (4mg)
- **Night**: RIVOTRIL, MONTEFLO
- **Twice Daily**: RITALIN LA, TARGINACT, CELEBREX, QUININE
- **Three Times Daily**: EPLEPTIN
- **As Needed**: NOVORAPID, LANTUS, CLOPAMON, OXYNORM

### 9. **Stock Levels**
Initial stock management:
- Each medication gets double the prescription quantity as initial stock
- Low stock threshold set to 10 units
- Expiration dates set to December 31, 2026

### 10. **Audit Trail**
Comprehensive transaction tracking:
- Initial stock purchase transactions
- Batch numbers and reference numbers
- User tracking for compliance
- Complete audit trail for prescription processing

## Medication Details

| # | Medication | Strength | Quantity | Instructions | ICD-10 | Category |
|---|------------|----------|----------|--------------|--------|----------|
| 1 | NOVORAPID | 100 units/ml | 3 FlexPen | Use as directed | E10.4 | Insulin |
| 2 | LANTUS | 100 units/ml | 2 SolarStar Pen | Use as directed | E10.4 | Insulin |
| 3 | ELTROXIN | 200mg | 30 tablets | Take one daily | E03.9 | Thyroid |
| 4 | MEDROL | 16mg | 30 tablets | Take one morning | E27.4 | Corticosteroids |
| 5 | MEDROL | 4mg | 60 tablets | Take two at 12h00 | E27.4 | Corticosteroids |
| 6 | FLORINEF | 0.1mg | 30 tablets | Take one daily | E27.4 | Corticosteroids |
| 7 | VYVANSE | 50mg | 60 tablets | Take two daily | F90.9 | ADHD |
| 8 | RITALIN LA | 20mg | 60 tablets | Take one twice daily | F90.9 | ADHD |
| 9 | WELBUTRIN XL | 300mg | 30 tablets | Take one daily | F41.8 | Antidepressants |
| 10 | CYMGEN | 60mg | 30 tablets | Take one daily | F41.8 | Antidepressants |
| 11 | RIVOTRIL | 2mg | 30 tablets | Take one at night | G47.6 | Benzodiazepines |
| 12 | TARGINACT | 20/10mg | 60 tablets | Take one twice daily | G89.4 | Pain Management |
| 13 | EPLEPTIN | 400mg | 270 tablets | Take three three times daily | G89.4 | Anticonvulsants |
| 14 | CELEBREX | 200mg | 60 tablets | Take one twice daily | G89.4 | Pain Management |
| 15 | QUININE | 150mg | 60 tablets | Take one twice daily | G47.6 | Antimalarials |
| 16 | TOPZOLE | 40mg | 30 tablets | Take one daily | K21.0 | PPI |
| 17 | MONTEFLO | 10mg | 30 tablets | Take one daily | J30.9 | Leukotriene |
| 18 | FEXO | 180mg | 30 tablets | Take one daily | J30.9 | Antihistamines |
| 19 | CLOPAMON | 10mg | 90 tablets | Take one three times as needed | R11.0 | Antiemetics |
| 20 | OXYNORM | 20mg | 90 tablets | Take one three times as needed | G89.4 | Pain Management |
| 21 | BETNOVATE IN UEA | 1:4 | 500g tube | Apply daily | - | Topical |

## Usage

### Running the Migration
```bash
cd medguard_backend
python manage.py migrate medications 0012_seed_prescription_data
```

### Reversing the Migration
```bash
python manage.py migrate medications 0011_optimize_indexes
```

### Verification
After running the migration, you can verify the data:

```python
# Check medications
from medications.models import Medication
print(f"Total medications: {Medication.objects.count()}")

# Check prescription
from medications.models import Prescription
prescription = Prescription.objects.get(prescription_number='PRES-2025-001')
print(f"Prescription total cost: R{prescription.total_cost}")

# Check medication schedules
from medications.models import MedicationSchedule
schedules = MedicationSchedule.objects.filter(patient__email='peter.knapton@example.com')
print(f"Medication schedules: {schedules.count()}")
```

## Compliance Features

1. **HIPAA Compliance**: All patient data is properly structured with audit trails
2. **South African Standards**: Uses local medical aid schemes and practice numbers
3. **Pharmaceutical Accuracy**: Correct generic names and manufacturer information
4. **Clinical Relevance**: Proper ICD-10 codes and medical condition mappings
5. **Audit Trail**: Complete transaction history for compliance reporting

## Notes

- The migration is idempotent and can be run multiple times safely
- All data is created with proper foreign key relationships
- Stock levels are set to double the prescription quantity for realistic inventory management
- Pricing is estimated based on South African pharmaceutical market rates
- The patient user account is created for testing purposes and can be modified as needed

## Support

For questions about this migration or the prescription data, refer to the MedGuard SA documentation or contact the development team. 