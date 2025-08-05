# Prescription Parser Utility

A comprehensive utility for parsing prescription text and converting it into structured medication data for the MedGuard SA system.

## Features

### 🔍 **Regex Pattern Matching**
- **Medication Names**: Extracts brand names, generic names, and medication types
- **Dosage Information**: Parses strength, units, and dosage amounts
- **Frequency Patterns**: Recognizes daily, twice daily, three times daily, etc.
- **Timing Instructions**: Identifies morning, night, before/after meals
- **Quantity & Repeats**: Extracts pack sizes and refill information
- **ICD-10 Codes**: Recognizes and maps diagnostic codes
- **Prescription Metadata**: Extracts doctor, dates, prescription numbers

### 💊 **Medication Abbreviation Mapping**
Comprehensive mapping of common medication abbreviations to full names:

```typescript
// Insulin types
'NOVORAPID' → 'Insulin aspart'
'LANTUS' → 'Insulin glargine'
'TRESIBA' → 'Insulin degludec'

// Diabetes medications
'METFORMIN' → 'Metformin'
'JANUVIA' → 'Sitagliptin'
'GLIPIZIDE' → 'Glipizide'

// Blood pressure medications
'LISINOPRIL' → 'Lisinopril'
'AMLODIPINE' → 'Amlodipine'
'LOSARTAN' → 'Losartan'

// And many more...
```

### 🏥 **ICD-10 Code Mapping**
Maps ICD-10 codes to condition descriptions:

```typescript
'E11' → 'Type 2 diabetes mellitus'
'I10' → 'Essential (primary) hypertension'
'E78' → 'Disorders of lipoprotein metabolism'
'F32' → 'Major depressive disorder, single episode'
```

### 📊 **Medication Type Identification**
Automatically identifies medication types from text:
- **tablet** - tablets, pills, oral
- **capsule** - capsules, caps
- **injection** - injection, injectable, subcutaneous
- **inhaler** - inhaler, puffs, nebulizer
- **liquid** - suspension, syrup, drops
- **cream** - cream, ointment, gel
- **patch** - patch, transdermal

### ✅ **Data Validation**
- Validates parsed data against known medication databases
- Provides confidence scores for parsing accuracy
- Generates warnings for missing or unclear information
- Suggests corrections for unrecognized medications

### 🌍 **Multi-language Support**
- English and Afrikaans support
- South African prescription format recognition
- Localized medication terminology

## Installation

The prescription parser is included in the MedGuard SA frontend project. No additional installation required.

## Quick Start

### Basic Usage

```typescript
import { parsePrescriptionText } from '@/utils/prescriptionParser'

const prescriptionText = `
  METFORMIN 500mg tablets
  Take 1 tablet twice daily with meals
  Quantity: 60 tablets
  + 5 repeats
`

const result = parsePrescriptionText(prescriptionText)

console.log('Medications found:', result.medications.length)
console.log('Confidence:', result.confidence)
console.log('Warnings:', result.warnings)
```

### Advanced Usage

```typescript
import { createPrescriptionParser } from '@/utils/prescriptionParser'

const parser = createPrescriptionParser({
  expandAbbreviations: true,
  validateAgainstDatabase: true,
  strictMode: false,
  language: 'en'
})

const result = parser.parsePrescription(prescriptionText)
```

### Converting to Form Data

```typescript
import { prescriptionTextToFormData } from '@/utils/prescriptionParser'

const formData = prescriptionTextToFormData(prescriptionText)

// formData is ready for database insertion
formData.forEach(medication => {
  console.log(`${medication.name} - ${medication.dosage}`)
})
```

## API Reference

### Core Functions

#### `parsePrescriptionText(text: string, options?: ParsingOptions): ParsedPrescription`

Quick parse function for simple use cases.

**Parameters:**
- `text` - Prescription text to parse
- `options` - Optional parsing configuration

**Returns:** `ParsedPrescription` object

#### `createPrescriptionParser(options?: ParsingOptions): PrescriptionParser`

Creates a configured parser instance.

**Parameters:**
- `options` - Parsing configuration options

**Returns:** `PrescriptionParser` instance

#### `prescriptionTextToFormData(text: string, options?: ParsingOptions): MedicationFormData[]`

Converts prescription text directly to medication form data.

**Parameters:**
- `text` - Prescription text to parse
- `options` - Optional parsing configuration

**Returns:** Array of `MedicationFormData` objects

### Utility Functions

#### `validateMedicationName(name: string): ValidationResult`

Validates a medication name against known abbreviations.

#### `extractICD10Codes(text: string): ICD10Code[]`

Extracts ICD-10 codes from text.

#### `getMedicationType(text: string): string | undefined`

Identifies medication type from text.

### Interfaces

#### `ParsedPrescription`

```typescript
interface ParsedPrescription {
  medications: ParsedMedication[]
  prescriptionNumber?: string
  prescribingDoctor?: string
  prescribedDate?: string
  expiryDate?: string
  icd10Codes: ICD10Code[]
  rawText: string
  confidence: number
  warnings: string[]
}
```

#### `ParsedMedication`

```typescript
interface ParsedMedication {
  name: string
  genericName?: string
  strength?: string
  dosage?: string
  frequency?: string
  timing?: string
  quantity?: number
  repeats?: number
  instructions?: string
  medicationType?: string
  category?: string
  confidence: number
  warnings: string[]
}
```

#### `ParsingOptions`

```typescript
interface ParsingOptions {
  expandAbbreviations?: boolean
  validateAgainstDatabase?: boolean
  includeGenericNames?: boolean
  strictMode?: boolean
  language?: 'en' | 'af'
}
```

## Examples

### Example 1: Simple Prescription

```typescript
const text = `
  METFORMIN 500mg tablets
  Take 1 tablet twice daily with meals
  Quantity: 60 tablets
  + 5 repeats
`

const result = parsePrescriptionText(text)
// Result: 1 medication, confidence > 0.9
```

### Example 2: Complex Diabetes Prescription

```typescript
const text = `
  Prescription #: DIAB001
  Dr. Sarah Johnson
  Date: 01/12/2024
  
  Diagnosis: E11.9 (Type 2 diabetes mellitus)
  
  LANTUS 100units/ml injection
  Inject 25 units once daily at bedtime
  Quantity: 3 pens
  
  NOVORAPID 100units/ml injection
  Inject 8 units three times daily before meals
  Quantity: 3 pens
  
  METFORMIN 1000mg tablets
  Take 1 tablet twice daily with meals
  Quantity: 60 tablets
  + 5 repeats
`

const result = parsePrescriptionText(text)
// Result: 3 medications, 1 ICD-10 code, confidence > 0.9
```

### Example 3: South African Format

```typescript
const text = `
  MEDIESE PRAKTISYN: Dr. Piet van der Merwe
  VOORSKRYFING NR: SA001
  DIAGNOSE: E11.9 (Tipe 2 diabetes mellitus)
  
  METFORMIN 500mg tablette
  Neem 1 tablet twee keer daagliks met maaltye
  Hoeveelheid: 60 tablette
  + 5 herhalings
`

const parser = createPrescriptionParser({ language: 'af' })
const result = parser.parsePrescription(text)
// Result: 1 medication, Afrikaans format recognized
```

## Integration with MedGuard SA

### Frontend Integration

```typescript
// In a Vue component
import { prescriptionTextToFormData } from '@/utils/prescriptionParser'

export default {
  data() {
    return {
      prescriptionText: '',
      parsedMedications: []
    }
  },
  methods: {
    parsePrescription() {
      try {
        this.parsedMedications = prescriptionTextToFormData(this.prescriptionText)
        this.$emit('medications-parsed', this.parsedMedications)
      } catch (error) {
        console.error('Failed to parse prescription:', error)
      }
    }
  }
}
```

### Form Validation

```typescript
import { parsePrescriptionText } from '@/utils/prescriptionParser'

function validatePrescriptionForm(text: string) {
  const result = parsePrescriptionText(text)
  
  return {
    isValid: result.confidence > 0.7,
    errors: result.warnings,
    medications: result.medications,
    confidence: result.confidence
  }
}
```

### Database Integration

```typescript
import { prescriptionTextToFormData } from '@/utils/prescriptionParser'
import { medicationApi } from '@/services/medicationApi'

async function savePrescription(prescriptionText: string) {
  const formData = prescriptionTextToFormData(prescriptionText)
  
  const savedMedications = []
  for (const medication of formData) {
    const saved = await medicationApi.createMedication(medication)
    savedMedications.push(saved)
  }
  
  return savedMedications
}
```

## Testing

Run the test suite:

```bash
npm run test prescriptionParser.test.ts
```

Run specific examples:

```typescript
import { examples } from '@/utils/prescriptionParser.example'

// Run all examples
examples.all()

// Run specific example
examples.basic()
examples.complex()
```

## Configuration

### Parsing Options

```typescript
const options: ParsingOptions = {
  expandAbbreviations: true,    // Expand medication abbreviations
  validateAgainstDatabase: true, // Validate against known medications
  includeGenericNames: true,     // Include generic names
  strictMode: false,            // Strict parsing mode
  language: 'en'                // Language preference
}
```

### Adding New Medications

To add new medication abbreviations, update the `MEDICATION_ABBREVIATIONS` object:

```typescript
export const MEDICATION_ABBREVIATIONS: Record<string, string> = {
  // ... existing mappings
  'NEW_MED': 'New Medication Name',
  'BRAND_NAME': 'Generic Name'
}
```

### Adding New ICD-10 Codes

To add new ICD-10 codes, update the `ICD10_CODES` object:

```typescript
export const ICD10_CODES: Record<string, ICD10Code> = {
  // ... existing codes
  'NEW_CODE': {
    code: 'NEW_CODE',
    description: 'New Condition Description',
    category: 'Category Name'
  }
}
```

## Error Handling

The parser includes comprehensive error handling:

```typescript
try {
  const result = parsePrescriptionText(text)
  
  if (result.confidence < 0.7) {
    console.warn('Low confidence parsing:', result.warnings)
  }
  
  if (result.medications.length === 0) {
    throw new Error('No medications found in prescription')
  }
  
} catch (error) {
  console.error('Parsing failed:', error)
  // Handle error appropriately
}
```

## Performance

- **Fast parsing**: Optimized regex patterns for quick text processing
- **Memory efficient**: Minimal memory footprint for large prescriptions
- **Scalable**: Handles multiple medications and complex prescriptions
- **Caching**: Consider caching parsed results for repeated use

## Security

- **Input validation**: All input is validated and sanitized
- **No external dependencies**: Self-contained utility
- **Type safety**: Full TypeScript support with strict typing
- **Error isolation**: Errors don't expose internal implementation details

## Contributing

When contributing to the prescription parser:

1. **Add tests** for new features
2. **Update documentation** for new patterns
3. **Follow TypeScript conventions**
4. **Test with real prescription examples**
5. **Consider edge cases** and error scenarios

## License

Part of the MedGuard SA project. See project license for details.

## Support

For issues or questions about the prescription parser:

1. Check the test examples for usage patterns
2. Review the API documentation
3. Test with the provided example functions
4. Create an issue with sample prescription text

---

**Note**: This utility is designed specifically for the MedGuard SA healthcare system and follows South African medical practices and terminology. 