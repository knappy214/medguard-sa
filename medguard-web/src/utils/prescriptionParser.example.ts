/**
 * Prescription Parser Usage Examples
 * 
 * This file demonstrates how to use the prescription parser utility
 * in various real-world scenarios for the MedGuard SA system.
 */

import {
  PrescriptionParser,
  parsePrescriptionText,
  prescriptionTextToFormData,
  validateMedicationName,
  extractICD10Codes,
  getMedicationType,
  createPrescriptionParser
} from './prescriptionParser'
import type { ParsingOptions, ParsedPrescription } from './prescriptionParser'

// ============================================================================
// BASIC USAGE EXAMPLES
// ============================================================================

/**
 * Example 1: Simple prescription parsing
 */
export function exampleBasicParsing() {
  console.log('=== Basic Prescription Parsing ===')
  
  const prescriptionText = `
    METFORMIN 500mg tablets
    Take 1 tablet twice daily with meals
    Quantity: 60 tablets
    + 5 repeats
  `

  const result = parsePrescriptionText(prescriptionText)
  
  console.log('Parsed medications:', result.medications.length)
  console.log('Confidence score:', result.confidence)
  console.log('Warnings:', result.warnings)
  
  if (result.medications.length > 0) {
    const med = result.medications[0]
    console.log('Medication:', med.name)
    console.log('Dosage:', med.dosage)
    console.log('Frequency:', med.frequency)
    console.log('Quantity:', med.quantity)
    console.log('Repeats:', med.repeats)
  }
}

/**
 * Example 2: Multiple medications with abbreviations
 */
export function exampleMultipleMedications() {
  console.log('\n=== Multiple Medications with Abbreviations ===')
  
  const prescriptionText = `
    LANTUS 100units/ml injection
    Inject 20 units once daily at night
    Quantity: 3 pens
    
    NOVORAPID 100units/ml injection
    Inject 10 units three times daily before meals
    Quantity: 3 pens
    
    LIPITOR 20mg tablets
    Take 1 tablet once daily at night
    Quantity: 30 tablets
    + 3 repeats
  `

  const result = parsePrescriptionText(prescriptionText)
  
  console.log('Total medications found:', result.medications.length)
  
  result.medications.forEach((med, index) => {
    console.log(`\nMedication ${index + 1}:`)
    console.log(`  Name: ${med.name}`)
    console.log(`  Type: ${med.medicationType}`)
    console.log(`  Dosage: ${med.dosage}`)
    console.log(`  Frequency: ${med.frequency}`)
    console.log(`  Timing: ${med.timing}`)
  })
}

// ============================================================================
// ADVANCED USAGE EXAMPLES
// ============================================================================

/**
 * Example 3: Custom parser configuration
 */
export function exampleCustomConfiguration() {
  console.log('\n=== Custom Parser Configuration ===')
  
  const options: ParsingOptions = {
    expandAbbreviations: true,
    validateAgainstDatabase: true,
    includeGenericNames: true,
    strictMode: false,
    language: 'en'
  }
  
  const parser = createPrescriptionParser(options)
  
  const prescriptionText = `
    Prescription #: RX123456
    Dr. John Smith
    Date: 15/12/2024
    Expires: 15/12/2025
    
    Diagnosis: E11.9 (Type 2 diabetes mellitus)
    
    METFORMIN 1000mg tablets
    Take 1 tablet twice daily with meals
    Quantity: 60 tablets
    + 5 repeats
    Instructions: Take with food to reduce stomach upset
  `

  const result = parser.parsePrescription(prescriptionText)
  
  console.log('Prescription number:', result.prescriptionNumber)
  console.log('Prescribing doctor:', result.prescribingDoctor)
  console.log('ICD-10 codes:', result.icd10Codes.map(code => code.code))
  console.log('Confidence:', result.confidence)
}

/**
 * Example 4: Converting to form data
 */
export function exampleFormDataConversion() {
  console.log('\n=== Converting to Form Data ===')
  
  const prescriptionText = `
    METFORMIN 500mg tablets
    Take 1 tablet twice daily with meals
    Quantity: 60 tablets
    + 5 repeats
  `

  const formData = prescriptionTextToFormData(prescriptionText)
  
  console.log('Form data for database insertion:')
  formData.forEach((med, index) => {
    console.log(`\nMedication ${index + 1}:`)
    console.log(`  Name: ${med.name}`)
    console.log(`  Dosage: ${med.dosage}`)
    console.log(`  Frequency: ${med.frequency}`)
    console.log(`  Time: ${med.time}`)
    console.log(`  Stock: ${med.stock}`)
    console.log(`  Min Stock: ${med.minStock}`)
    console.log(`  Category: ${med.category}`)
  })
}

// ============================================================================
// VALIDATION EXAMPLES
// ============================================================================

/**
 * Example 5: Medication name validation
 */
export function exampleMedicationValidation() {
  console.log('\n=== Medication Name Validation ===')
  
  const testNames = ['LANTUS', 'METFORMIN', 'UNKNOWN_MED', 'LIPITOR']
  
  testNames.forEach(name => {
    const validation = validateMedicationName(name)
    
    console.log(`\nValidating: ${name}`)
    console.log(`  Is valid: ${validation.isValid}`)
    
    if (validation.expandedName) {
      console.log(`  Expanded name: ${validation.expandedName}`)
    }
    
    if (validation.suggestions.length > 0) {
      console.log(`  Suggestions: ${validation.suggestions.join(', ')}`)
    }
  })
}

/**
 * Example 6: ICD-10 code extraction
 */
export function exampleICD10Extraction() {
  console.log('\n=== ICD-10 Code Extraction ===')
  
  const text = `
    Diagnoses: 
    - E11.9 (Type 2 diabetes mellitus)
    - I10 (Essential hypertension)
    - E78.0 (Hypercholesterolemia)
    - F32.1 (Major depressive disorder, moderate)
  `

  const codes = extractICD10Codes(text)
  
  console.log('Extracted ICD-10 codes:')
  codes.forEach(code => {
    console.log(`  ${code.code}: ${code.description} (${code.category})`)
  })
}

// ============================================================================
// REAL-WORLD SCENARIOS
// ============================================================================

/**
 * Example 7: South African prescription format
 */
export function exampleSouthAfricanPrescription() {
  console.log('\n=== South African Prescription Format ===')
  
  const saPrescription = `
    MEDIESE PRAKTISYN: Dr. Piet van der Merwe
    PASIENT: Jan Smit
    DATUM: 15/12/2024
    VOORSKRYFING NR: SA001
    
    DIAGNOSE: E11.9 (Tipe 2 diabetes mellitus)
    
    METFORMIN 500mg tablette
    Neem 1 tablet twee keer daagliks met maaltye
    Hoeveelheid: 60 tablette
    + 5 herhalings
    
    LANTUS 100units/ml inspuiting
    Spuit 20 eenhede een keer daagliks voor slaap
    Hoeveelheid: 3 penne
    
    ATORVASTATIN 20mg tablette
    Neem 1 tablet een keer daagliks voor slaap
    Hoeveelheid: 30 tablette
    + 3 herhalings
  `

  const parser = createPrescriptionParser({ language: 'af' })
  const result = parser.parsePrescription(saPrescription)
  
  console.log('South African prescription parsed:')
  console.log('  Doctor:', result.prescribingDoctor)
  console.log('  Prescription number:', result.prescriptionNumber)
  console.log('  Medications found:', result.medications.length)
  console.log('  ICD-10 codes:', result.icd10Codes.map(c => c.code))
}

/**
 * Example 8: Complex multi-condition prescription
 */
export function exampleComplexPrescription() {
  console.log('\n=== Complex Multi-Condition Prescription ===')
  
  const complexPrescription = `
    Prescription #: COMPLEX001
    Dr. Dr. Maria Rodriguez
    Date: 20/12/2024
    Expires: 20/12/2025
    
    Diagnoses: 
    - E11.9 (Type 2 diabetes mellitus)
    - I10 (Essential hypertension)
    - E78.0 (Hypercholesterolemia)
    - F32.1 (Major depressive disorder, moderate)
    
    LANTUS 100units/ml injection
    Inject 30 units once daily at bedtime
    Quantity: 3 pens
    Instructions: Store in refrigerator, rotate injection sites
    
    NOVORAPID 100units/ml injection
    Inject 12 units three times daily before meals
    Quantity: 3 pens
    Instructions: Use within 28 days after opening
    
    METFORMIN 1000mg tablets
    Take 1 tablet twice daily with meals
    Quantity: 60 tablets
    + 5 repeats
    Instructions: Take with food to reduce stomach upset
    
    LISINOPRIL 10mg tablets
    Take 1 tablet once daily in the morning
    Quantity: 30 tablets
    + 3 repeats
    Instructions: Monitor blood pressure regularly
    
    ATORVASTATIN 20mg tablets
    Take 1 tablet once daily at night
    Quantity: 30 tablets
    + 3 repeats
    Instructions: Avoid grapefruit juice
    
    SERTRALINE 50mg tablets
    Take 1 tablet once daily in the morning
    Quantity: 30 tablets
    + 3 repeats
    Instructions: May take 2-4 weeks to see full effect
  `

  const result = parsePrescriptionText(complexPrescription)
  
  console.log('Complex prescription analysis:')
  console.log('  Total medications:', result.medications.length)
  console.log('  Confidence score:', result.confidence)
  console.log('  ICD-10 codes:', result.icd10Codes.map(c => c.code))
  
  // Group medications by type
  const byType = result.medications.reduce((acc, med) => {
    const type = med.medicationType || 'unknown'
    if (!acc[type]) acc[type] = []
    acc[type].push(med)
    return acc
  }, {} as Record<string, typeof result.medications>)
  
  console.log('\nMedications by type:')
  Object.entries(byType).forEach(([type, meds]) => {
    console.log(`  ${type}: ${meds.length} medications`)
  })
  
  // Check for medications with instructions
  const withInstructions = result.medications.filter(m => m.instructions)
  console.log(`\nMedications with special instructions: ${withInstructions.length}`)
}

// ============================================================================
// ERROR HANDLING EXAMPLES
// ============================================================================

/**
 * Example 9: Error handling and validation
 */
export function exampleErrorHandling() {
  console.log('\n=== Error Handling and Validation ===')
  
  const testCases = [
    {
      name: 'Empty prescription',
      text: ''
    },
    {
      name: 'Invalid text',
      text: 'This is not a prescription at all'
    },
    {
      name: 'Missing dosage',
      text: 'METFORMIN tablets\nTake daily'
    },
    {
      name: 'Valid prescription',
      text: 'METFORMIN 500mg tablets\nTake 1 tablet twice daily'
    }
  ]
  
  testCases.forEach(testCase => {
    console.log(`\nTesting: ${testCase.name}`)
    
    try {
      const result = parsePrescriptionText(testCase.text)
      
      console.log(`  Medications found: ${result.medications.length}`)
      console.log(`  Confidence: ${result.confidence}`)
      console.log(`  Warnings: ${result.warnings.length}`)
      
      if (result.warnings.length > 0) {
        console.log(`  Warning details: ${result.warnings.join(', ')}`)
      }
    } catch (error) {
      console.log(`  Error: ${error}`)
    }
  })
}

// ============================================================================
// INTEGRATION EXAMPLES
// ============================================================================

/**
 * Example 10: Integration with medication form
 */
export function exampleFormIntegration() {
  console.log('\n=== Form Integration Example ===')
  
  // Simulate user input from a prescription form
  const userInput = `
    METFORMIN 500mg tablets
    Take 1 tablet twice daily with meals
    Quantity: 60 tablets
    + 5 repeats
  `

  // Parse the prescription
  const parsed = parsePrescriptionText(userInput)
  
  // Convert to form data
  const formData = prescriptionTextToFormData(parsed)
  
  // Simulate form validation
  const validation = {
    isValid: parsed.confidence > 0.7,
    errors: parsed.warnings,
    suggestions: [] as string[]
  }
  
  console.log('Form validation results:')
  console.log(`  Is valid: ${validation.isValid}`)
  console.log(`  Confidence: ${parsed.confidence}`)
  console.log(`  Errors: ${validation.errors.length}`)
  
  if (validation.errors.length > 0) {
    console.log(`  Error details: ${validation.errors.join(', ')}`)
  }
  
  // Simulate form submission
  if (validation.isValid) {
    console.log('\nForm data ready for submission:')
    formData.forEach((med, index) => {
      console.log(`  Medication ${index + 1}: ${med.name} - ${med.dosage}`)
    })
  }
}

/**
 * Example 11: Batch processing multiple prescriptions
 */
export function exampleBatchProcessing() {
  console.log('\n=== Batch Processing Example ===')
  
  const prescriptions = [
    {
      id: 'RX001',
      text: 'METFORMIN 500mg tablets\nTake 1 tablet twice daily'
    },
    {
      id: 'RX002',
      text: 'LANTUS 100units/ml injection\nInject 20 units daily'
    },
    {
      id: 'RX003',
      text: 'LIPITOR 20mg tablets\nTake 1 tablet daily'
    }
  ]
  
  const results = prescriptions.map(prescription => {
    const parsed = parsePrescriptionText(prescription.text)
    return {
      id: prescription.id,
      success: parsed.confidence > 0.7,
      medications: parsed.medications.length,
      confidence: parsed.confidence,
      warnings: parsed.warnings
    }
  })
  
  console.log('Batch processing results:')
  results.forEach(result => {
    console.log(`  ${result.id}: ${result.success ? 'SUCCESS' : 'FAILED'}`)
    console.log(`    Medications: ${result.medications}`)
    console.log(`    Confidence: ${result.confidence}`)
    if (result.warnings.length > 0) {
      console.log(`    Warnings: ${result.warnings.join(', ')}`)
    }
  })
  
  const successCount = results.filter(r => r.success).length
  console.log(`\nOverall success rate: ${(successCount / results.length * 100).toFixed(1)}%`)
}

// ============================================================================
// MAIN EXAMPLE RUNNER
// ============================================================================

/**
 * Run all examples
 */
export function runAllExamples() {
  console.log('🚀 Running Prescription Parser Examples\n')
  
  exampleBasicParsing()
  exampleMultipleMedications()
  exampleCustomConfiguration()
  exampleFormDataConversion()
  exampleMedicationValidation()
  exampleICD10Extraction()
  exampleSouthAfricanPrescription()
  exampleComplexPrescription()
  exampleErrorHandling()
  exampleFormIntegration()
  exampleBatchProcessing()
  
  console.log('\n✅ All examples completed!')
}

// Export individual examples for selective testing
export const examples = {
  basic: exampleBasicParsing,
  multiple: exampleMultipleMedications,
  custom: exampleCustomConfiguration,
  formData: exampleFormDataConversion,
  validation: exampleMedicationValidation,
  icd10: exampleICD10Extraction,
  saFormat: exampleSouthAfricanPrescription,
  complex: exampleComplexPrescription,
  errors: exampleErrorHandling,
  integration: exampleFormIntegration,
  batch: exampleBatchProcessing,
  all: runAllExamples
} 