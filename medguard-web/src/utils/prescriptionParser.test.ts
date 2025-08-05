/**
 * Prescription Parser Tests
 * 
 * Comprehensive test suite for the prescription parser utility.
 * Tests various real-world prescription formats and edge cases.
 */

import { describe, it, expect, beforeEach } from 'vitest'
import {
  PrescriptionParser,
  parsePrescriptionText,
  prescriptionTextToFormData,
  validateMedicationName,
  extractICD10Codes,
  getMedicationType,
  MEDICATION_ABBREVIATIONS,
  ICD10_CODES,
  PRESCRIPTION_PATTERNS
} from './prescriptionParser'
import type { ParsedPrescription, ParsedMedication, ParsingOptions } from './prescriptionParser'

describe('PrescriptionParser', () => {
  let parser: PrescriptionParser

  beforeEach(() => {
    parser = new PrescriptionParser()
  })

  describe('Basic Parsing', () => {
    it('should parse a simple prescription', () => {
      const text = `
        METFORMIN 500mg tablets
        Take 1 tablet twice daily with meals
        Quantity: 60 tablets
        + 5 repeats
      `

      const result = parser.parsePrescription(text)

      expect(result.medications).toHaveLength(1)
      expect(result.medications[0].name).toBe('Metformin')
      expect(result.medications[0].strength).toBe('500mg')
      expect(result.medications[0].frequency).toBe('twice daily')
      expect(result.medications[0].quantity).toBe(60)
      expect(result.medications[0].repeats).toBe(5)
      expect(result.confidence).toBeGreaterThan(0.8)
    })

    it('should parse multiple medications', () => {
      const text = `
        LANTUS 100units/ml injection
        Inject 20 units once daily at night
        
        NOVORAPID 100units/ml injection
        Inject 10 units three times daily before meals
        Quantity: 2 pens each
      `

      const result = parser.parsePrescription(text)

      expect(result.medications).toHaveLength(2)
      expect(result.medications[0].name).toBe('Insulin glargine')
      expect(result.medications[1].name).toBe('Insulin aspart')
      expect(result.medications[0].frequency).toBe('daily')
      expect(result.medications[1].frequency).toBe('three times daily')
    })

    it('should handle medication abbreviations', () => {
      const text = 'LIPITOR 20mg tablets, take 1 daily'

      const result = parser.parsePrescription(text)

      expect(result.medications[0].name).toBe('Atorvastatin')
      expect(result.medications[0].strength).toBe('20mg')
    })
  })

  describe('Dosage and Frequency Parsing', () => {
    it('should parse various dosage formats', () => {
      const testCases = [
        { text: 'METFORMIN 500mg', expected: '500mg' },
        { text: 'INSULIN 100units/ml', expected: '100units/ml' },
        { text: 'ASPIRIN 81mg', expected: '81mg' },
        { text: 'VITAMIN D 1000iu', expected: '1000iu' }
      ]

      testCases.forEach(({ text, expected }) => {
        const result = parser.parsePrescription(text)
        expect(result.medications[0].strength).toBe(expected)
      })
    })

    it('should parse various frequency formats', () => {
      const testCases = [
        { text: 'Take once daily', expected: 'daily' },
        { text: 'Take twice daily', expected: 'twice daily' },
        { text: 'Take three times daily', expected: 'three times daily' },
        { text: 'Take every 8 hours', expected: 'every 8 hours' },
        { text: 'Take weekly', expected: 'weekly' }
      ]

      testCases.forEach(({ text, expected }) => {
        const result = parser.parsePrescription(text)
        expect(result.medications[0].frequency).toBe(expected)
      })
    })

    it('should parse timing instructions', () => {
      const testCases = [
        { text: 'Take in the morning', expected: 'morning' },
        { text: 'Take at night', expected: 'night' },
        { text: 'Take before meals', expected: 'before meals' },
        { text: 'Take with breakfast', expected: 'morning' }
      ]

      testCases.forEach(({ text, expected }) => {
        const result = parser.parsePrescription(text)
        expect(result.medications[0].timing).toBe(expected)
      })
    })
  })

  describe('Quantity and Repeats', () => {
    it('should parse quantity information', () => {
      const testCases = [
        { text: 'Quantity: 30 tablets', expected: 30 },
        { text: 'x 60 capsules', expected: 60 },
        { text: 'Pack of 90', expected: 90 },
        { text: 'Box of 120', expected: 120 }
      ]

      testCases.forEach(({ text, expected }) => {
        const result = parser.parsePrescription(text)
        expect(result.medications[0].quantity).toBe(expected)
      })
    })

    it('should parse repeat information', () => {
      const testCases = [
        { text: '+ 5 repeats', expected: 5 },
        { text: '3 refills', expected: 3 },
        { text: '2 renewals', expected: 2 },
        { text: '+ 10 times', expected: 10 }
      ]

      testCases.forEach(({ text, expected }) => {
        const result = parser.parsePrescription(text)
        expect(result.medications[0].repeats).toBe(expected)
      })
    })
  })

  describe('ICD-10 Code Extraction', () => {
    it('should extract ICD-10 codes', () => {
      const text = `
        Diagnosis: E11.9 (Type 2 diabetes)
        METFORMIN 500mg tablets
        Take 1 tablet twice daily
      `

      const result = parser.parsePrescription(text)

      expect(result.icd10Codes).toHaveLength(1)
      expect(result.icd10Codes[0].code).toBe('E11')
      expect(result.icd10Codes[0].description).toBe('Type 2 diabetes mellitus')
    })

    it('should handle multiple ICD-10 codes', () => {
      const text = `
        Diagnoses: E11.9, I10 (Type 2 diabetes, Hypertension)
        METFORMIN 500mg tablets
        LISINOPRIL 10mg tablets
      `

      const result = parser.parsePrescription(text)

      expect(result.icd10Codes).toHaveLength(2)
      expect(result.icd10Codes.some(code => code.code === 'E11')).toBe(true)
      expect(result.icd10Codes.some(code => code.code === 'I10')).toBe(true)
    })
  })

  describe('Prescription Metadata', () => {
    it('should extract prescription number', () => {
      const text = `
        Prescription #: RX123456
        METFORMIN 500mg tablets
        Take 1 tablet twice daily
      `

      const result = parser.parsePrescription(text)

      expect(result.prescriptionNumber).toBe('RX123456')
    })

    it('should extract doctor information', () => {
      const text = `
        Dr. John Smith
        METFORMIN 500mg tablets
        Take 1 tablet twice daily
      `

      const result = parser.parsePrescription(text)

      expect(result.prescribingDoctor).toBe('John Smith')
    })

    it('should extract dates', () => {
      const text = `
        Date: 15/12/2024
        Expires: 15/12/2025
        METFORMIN 500mg tablets
        Take 1 tablet twice daily
      `

      const result = parser.parsePrescription(text)

      expect(result.prescribedDate).toBe('15/12/2024')
      expect(result.expiryDate).toBe('15/12/2025')
    })
  })

  describe('Medication Type Identification', () => {
    it('should identify medication types', () => {
      const testCases = [
        { text: 'METFORMIN 500mg tablets', expected: 'tablet' },
        { text: 'OMEPRAZOLE 20mg capsules', expected: 'capsule' },
        { text: 'INSULIN injection', expected: 'injection' },
        { text: 'VENTOLIN inhaler', expected: 'inhaler' },
        { text: 'HYDROCORTISONE cream', expected: 'cream' }
      ]

      testCases.forEach(({ text, expected }) => {
        const result = parser.parsePrescription(text)
        expect(result.medications[0].medicationType).toBe(expected)
      })
    })
  })

  describe('Complex Prescriptions', () => {
    it('should parse a complex diabetes prescription', () => {
      const text = `
        Prescription #: DIAB001
        Dr. Sarah Johnson
        Date: 01/12/2024
        Expires: 01/12/2025
        
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
        
        ATORVASTATIN 20mg tablets
        Take 1 tablet once daily at night
        Quantity: 30 tablets
        + 3 repeats
      `

      const result = parser.parsePrescription(text)

      expect(result.medications).toHaveLength(4)
      expect(result.prescriptionNumber).toBe('DIAB001')
      expect(result.prescribingDoctor).toBe('Sarah Johnson')
      expect(result.icd10Codes).toHaveLength(1)
      expect(result.icd10Codes[0].code).toBe('E11')

      // Verify insulin medications
      const lantus = result.medications.find(m => m.name === 'Insulin glargine')
      expect(lantus?.frequency).toBe('daily')
      expect(lantus?.timing).toBe('night')

      const novorapid = result.medications.find(m => m.name === 'Insulin aspart')
      expect(novorapid?.frequency).toBe('three times daily')
      expect(novorapid?.timing).toBe('before meals')
    })

    it('should parse a cardiovascular prescription', () => {
      const text = `
        Prescription #: CARD001
        Dr. Michael Brown
        Date: 10/12/2024
        
        Diagnoses: I10 (Essential hypertension), E78.0 (Hypercholesterolemia)
        
        LISINOPRIL 10mg tablets
        Take 1 tablet once daily in the morning
        Quantity: 30 tablets
        + 3 repeats
        
        ATORVASTATIN 20mg tablets
        Take 1 tablet once daily at night
        Quantity: 30 tablets
        + 3 repeats
        
        ASPIRIN 81mg tablets
        Take 1 tablet once daily in the morning
        Quantity: 90 tablets
        + 2 repeats
      `

      const result = parser.parsePrescription(text)

      expect(result.medications).toHaveLength(3)
      expect(result.icd10Codes).toHaveLength(2)
      expect(result.confidence).toBeGreaterThan(0.9)
    })
  })

  describe('Error Handling', () => {
    it('should handle empty text', () => {
      const result = parser.parsePrescription('')

      expect(result.medications).toHaveLength(0)
      expect(result.confidence).toBe(0)
      expect(result.warnings).toContain('No medications found in prescription text')
    })

    it('should handle invalid text', () => {
      const result = parser.parsePrescription('This is not a prescription')

      expect(result.medications).toHaveLength(0)
      expect(result.confidence).toBeLessThan(1)
    })

    it('should handle malformed prescriptions', () => {
      const text = `
        METFORMIN tablets
        Take daily
        (Missing dosage information)
      `

      const result = parser.parsePrescription(text)

      expect(result.medications).toHaveLength(1)
      expect(result.medications[0].warnings).toContain('No dosage information found')
      expect(result.medications[0].confidence).toBeLessThan(1)
    })
  })

  describe('Form Data Conversion', () => {
    it('should convert to MedicationFormData', () => {
      const text = `
        METFORMIN 500mg tablets
        Take 1 tablet twice daily with meals
        Quantity: 60 tablets
      `

      const formData = prescriptionTextToFormData(text)

      expect(formData).toHaveLength(1)
      expect(formData[0].name).toBe('Metformin')
      expect(formData[0].dosage).toBe('500mg')
      expect(formData[0].frequency).toBe('twice daily')
      expect(formData[0].time).toBe('with meals')
      expect(formData[0].stock).toBe(60)
      expect(formData[0].minStock).toBe(12) // 20% of 60
      expect(formData[0].category).toBe('tablet')
    })
  })

  describe('Validation', () => {
    it('should validate medication names', () => {
      const validResult = validateMedicationName('LANTUS')
      expect(validResult.isValid).toBe(true)
      expect(validResult.expandedName).toBe('Insulin glargine')

      const invalidResult = validateMedicationName('UNKNOWN_MED')
      expect(invalidResult.isValid).toBe(false)
      expect(invalidResult.suggestions.length).toBeGreaterThan(0)
    })

    it('should validate medication data', async () => {
      const medications: ParsedMedication[] = [
        {
          name: 'Metformin',
          dosage: '500mg',
          frequency: 'twice daily',
          confidence: 0.9,
          warnings: []
        },
        {
          name: 'Invalid Med',
          confidence: 0.3,
          warnings: ['No dosage information found']
        }
      ]

      const validation = await parser.validateMedicationData(medications)

      expect(validation.valid).toHaveLength(1)
      expect(validation.invalid).toHaveLength(1)
      expect(Object.keys(validation.suggestions)).toHaveLength(1)
    })
  })

  describe('Utility Functions', () => {
    it('should extract ICD-10 codes from text', () => {
      const text = 'Diagnosis: E11.9, I10, F32.1'
      const codes = extractICD10Codes(text)

      expect(codes).toHaveLength(3)
      expect(codes.some(code => code.code === 'E11')).toBe(true)
      expect(codes.some(code => code.code === 'I10')).toBe(true)
      expect(codes.some(code => code.code === 'F32')).toBe(true)
    })

    it('should identify medication types', () => {
      expect(getMedicationType('tablets')).toBe('tablet')
      expect(getMedicationType('injection')).toBe('injection')
      expect(getMedicationType('inhaler')).toBe('inhaler')
      expect(getMedicationType('unknown')).toBeUndefined()
    })
  })

  describe('Configuration Options', () => {
    it('should respect parsing options', () => {
      const strictParser = new PrescriptionParser({
        expandAbbreviations: false,
        strictMode: true
      })

      const text = 'LANTUS 100units/ml injection'
      const result = strictParser.parsePrescription(text)

      expect(result.medications[0].name).toBe('LANTUS') // Not expanded
    })

    it('should handle different languages', () => {
      const afrikaansParser = new PrescriptionParser({
        language: 'af'
      })

      // Test with Afrikaans prescription text
      const text = `
        METFORMIN 500mg tablette
        Neem 1 tablet twee keer daagliks met maaltye
        Hoeveelheid: 60 tablette
      `

      const result = afrikaansParser.parsePrescription(text)
      expect(result.medications).toHaveLength(1)
    })
  })

  describe('Real-world Examples', () => {
    it('should parse a typical South African prescription', () => {
      const text = `
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

      const result = parser.parsePrescription(text)

      expect(result.medications).toHaveLength(3)
      expect(result.prescribingDoctor).toBe('Piet van der Merwe')
      expect(result.prescriptionNumber).toBe('SA001')
      expect(result.icd10Codes).toHaveLength(1)
    })

    it('should parse a complex multi-condition prescription', () => {
      const text = `
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

      const result = parser.parsePrescription(text)

      expect(result.medications).toHaveLength(6)
      expect(result.icd10Codes).toHaveLength(4)
      expect(result.confidence).toBeGreaterThan(0.9)

      // Verify all medication types are identified
      const types = result.medications.map(m => m.medicationType)
      expect(types).toContain('injection')
      expect(types).toContain('tablet')

      // Verify all have instructions
      const withInstructions = result.medications.filter(m => m.instructions)
      expect(withInstructions.length).toBeGreaterThan(0)
    })
  })
}) 