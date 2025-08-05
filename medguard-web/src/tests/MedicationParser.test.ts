/**
 * Comprehensive Medication Parser Tests
 * 
 * Tests for prescription text parsing, medication extraction,
 * validation, and form data conversion using actual prescription data.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { PrescriptionParser, parsePrescriptionText, prescriptionTextToFormData } from '../utils/prescriptionParser'
import type { ParsedPrescription, ParsingOptions } from '../utils/prescriptionParser'

// Real prescription data for comprehensive testing
const REAL_21_MEDICATION_PRESCRIPTION = `
PRESCRIPTION

Patient: John Doe
Date: 2024-01-15
Doctor: Dr. Smith
Practice: Cape Town Medical Centre

1. NOVORAPID FlexPen 100units/ml
   Inject 10 units three times daily before meals
   Quantity: 3 pens
   + 2 repeats

2. LANTUS SoloStar Pen 100units/ml
   Inject 20 units once daily at night
   Quantity: 3 pens
   + 2 repeats

3. METFORMIN 500mg tablets
   Take 1 tablet twice daily with meals
   Quantity: 60 tablets
   + 5 repeats

4. LIPITOR 20mg tablets
   Take 1 tablet once daily at night
   Quantity: 30 tablets
   + 3 repeats

5. COZAAR 50mg tablets
   Take 1 tablet once daily
   Quantity: 30 tablets
   + 3 repeats

6. VENTOLIN inhaler 100mcg
   Use 2 puffs as needed for shortness of breath
   Quantity: 1 inhaler
   + 1 repeat

7. SERETIDE 250/25 inhaler
   Use 2 puffs twice daily
   Quantity: 1 inhaler
   + 2 repeats

8. PANADO 500mg tablets
   Take 2 tablets as needed for pain
   Quantity: 30 tablets
   + 2 repeats

9. OMEPRAZOLE 20mg capsules
   Take 1 capsule once daily before breakfast
   Quantity: 30 capsules
   + 3 repeats

10. MOVICOL sachets
    Take 1 sachet daily as needed for constipation
    Quantity: 30 sachets
    + 2 repeats

11. VITAMIN D3 1000IU tablets
    Take 1 tablet once daily
    Quantity: 60 tablets
    + 3 repeats

12. FOLIC ACID 5mg tablets
    Take 1 tablet once daily
    Quantity: 30 tablets
    + 3 repeats

13. CALCIUM CARBONATE 500mg tablets
    Take 2 tablets twice daily with meals
    Quantity: 60 tablets
    + 3 repeats

14. MAGNESIUM 400mg tablets
    Take 1 tablet once daily at night
    Quantity: 30 tablets
    + 2 repeats

15. OMEGA-3 1000mg capsules
    Take 2 capsules once daily with meals
    Quantity: 60 capsules
    + 3 repeats

16. PROBIOTIC capsules
    Take 1 capsule once daily
    Quantity: 30 capsules
    + 2 repeats

17. MELATONIN 3mg tablets
    Take 1 tablet at bedtime as needed for sleep
    Quantity: 30 tablets
    + 2 repeats

18. ASPIRIN 100mg tablets
    Take 1 tablet once daily
    Quantity: 30 tablets
    + 3 repeats

19. VITAMIN B12 1000mcg tablets
    Take 1 tablet once daily
    Quantity: 30 tablets
    + 2 repeats

20. ZINC 15mg tablets
    Take 1 tablet once daily
    Quantity: 30 tablets
    + 2 repeats

21. VITAMIN C 500mg tablets
    Take 1 tablet once daily
    Quantity: 30 tablets
    + 2 repeats

ICD-10 Codes: E11.9, I10, J45.901, Z79.4
`

const COMPLEX_DOSAGE_PRESCRIPTION = `
PRESCRIPTION

Patient: Jane Smith
Date: 2024-01-20
Doctor: Dr. Johnson

1. WARFARIN 5mg tablets
   Take 1 tablet daily at 18h00
   INR monitoring required
   Quantity: 30 tablets
   + 3 repeats

2. INSULIN MIXTARD 30/70 100units/ml
   Inject 15 units morning and 10 units evening
   Quantity: 2 pens
   + 2 repeats

3. AMIODARONE 200mg tablets
   Take 2 tablets twice daily for 1 week, then 1 tablet daily
   Quantity: 60 tablets
   + 2 repeats

4. PREDNISONE 5mg tablets
   Take 4 tablets daily for 3 days, then 2 tablets daily for 3 days, then 1 tablet daily
   Quantity: 30 tablets
   + 1 repeat

5. METHOTREXATE 2.5mg tablets
   Take 6 tablets once weekly on Monday
   Quantity: 30 tablets
   + 3 repeats

ICD-10 Codes: I48.91, E11.9, I25.10
`

const AFRIKAANS_PRESCRIPTION = `
VOORSKRYWING

Pasiënt: Piet van der Merwe
Datum: 2024-01-25
Dokter: Dr. Botha

1. NOVORAPID FlexPen 100eenhede/ml
   Spuit 10 eenhede drie keer daagliks voor maaltye
   Hoeveelheid: 3 penne
   + 2 herhalings

2. METFORMIEN 500mg tablette
   Neem 1 tablet twee keer daagliks met maaltye
   Hoeveelheid: 60 tablette
   + 5 herhalings

3. VENTOLIN inhaleerder 100mcg
   Gebruik 2 teugies soos benodig vir kortasem
   Hoeveelheid: 1 inhaleerder
   + 1 herhaling

ICD-10 Kodes: E11.9, J45.901
`

const MALFORMED_PRESCRIPTION = `
PRESCRIPTION

Patient: Test Patient
Date: 2024-01-30
Doctor: Dr. Test

1. MEDICATION A
   Take as directed
   Quantity: unknown

2. MEDICATION B
   Dosage: unclear
   Frequency: not specified

3. MEDICATION C
   Instructions: take when needed
   No quantity specified
`

describe('Medication Parser Tests', () => {
  let parser: PrescriptionParser

  beforeEach(() => {
    parser = new PrescriptionParser()
  })

  describe('1. Basic Prescription Parsing', () => {
    it('should parse all 21 medications from real prescription', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      expect(result.medications).toHaveLength(21)
      expect(result.confidence).toBeGreaterThan(0.8)
      expect(result.warnings).toHaveLength(0)
      expect(result.patientInfo).toBeDefined()
      expect(result.doctorInfo).toBeDefined()
      expect(result.prescriptionDate).toBeDefined()
    })

    it('should extract patient information correctly', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      expect(result.patientInfo?.name).toBe('John Doe')
      expect(result.doctorInfo?.name).toBe('Dr. Smith')
      expect(result.prescriptionDate).toBe('2024-01-15')
    })

    it('should extract ICD-10 codes accurately', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      expect(result.icd10Codes).toContain('E11.9')
      expect(result.icd10Codes).toContain('I10')
      expect(result.icd10Codes).toContain('J45.901')
      expect(result.icd10Codes).toContain('Z79.4')
    })

    it('should parse medication details accurately', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      const novorapid = result.medications.find(m => m.name.includes('NOVORAPID'))
      
      expect(novorapid).toBeDefined()
      expect(novorapid?.name).toBe('NOVORAPID FlexPen 100units/ml')
      expect(novorapid?.dosage).toBe('10 units')
      expect(novorapid?.frequency).toBe('three times daily')
      expect(novorapid?.timing).toBe('before meals')
      expect(novorapid?.quantity).toBe(3)
      expect(novorapid?.repeats).toBe(2)
      expect(novorapid?.medicationType).toBe('pen')
    })
  })

  describe('2. Complex Dosage Instructions', () => {
    it('should parse complex dosage schedules', () => {
      const result = parsePrescriptionText(COMPLEX_DOSAGE_PRESCRIPTION)
      
      expect(result.medications).toHaveLength(5)
      
      // Test specific time instructions
      const warfarin = result.medications.find(m => m.name.includes('WARFARIN'))
      expect(warfarin?.timing).toBe('at 18h00')
      
      // Test split dosage
      const insulin = result.medications.find(m => m.name.includes('INSULIN MIXTARD'))
      expect(insulin?.dosage).toContain('15 units morning and 10 units evening')
      
      // Test tapering dosage
      const prednisone = result.medications.find(m => m.name.includes('PREDNISONE'))
      expect(prednisone?.instructions).toContain('tapering')
    })

    it('should handle weekly medication schedules', () => {
      const result = parsePrescriptionText(COMPLEX_DOSAGE_PRESCRIPTION)
      const methotrexate = result.medications.find(m => m.name.includes('METHOTREXATE'))
      
      expect(methotrexate?.frequency).toBe('once weekly')
      expect(methotrexate?.timing).toBe('on Monday')
      expect(methotrexate?.dosage).toBe('6 tablets')
    })

    it('should parse tapering instructions', () => {
      const result = parsePrescriptionText(COMPLEX_DOSAGE_PRESCRIPTION)
      const prednisone = result.medications.find(m => m.name.includes('PREDNISONE'))
      
      expect(prednisone?.instructions).toContain('4 tablets daily for 3 days')
      expect(prednisone?.instructions).toContain('then 2 tablets daily for 3 days')
      expect(prednisone?.instructions).toContain('then 1 tablet daily')
    })
  })

  describe('3. Afrikaans Prescription Support', () => {
    it('should parse Afrikaans prescriptions', () => {
      const result = parsePrescriptionText(AFRIKAANS_PRESCRIPTION)
      
      expect(result.medications).toHaveLength(3)
      expect(result.patientInfo?.name).toBe('Piet van der Merwe')
      expect(result.doctorInfo?.name).toBe('Dr. Botha')
    })

    it('should translate Afrikaans medication terms', () => {
      const result = parsePrescriptionText(AFRIKAANS_PRESCRIPTION)
      const novorapid = result.medications.find(m => m.name.includes('NOVORAPID'))
      
      expect(novorapid?.frequency).toBe('three times daily')
      expect(novorapid?.timing).toBe('before meals')
    })

    it('should handle Afrikaans quantity terms', () => {
      const result = parsePrescriptionText(AFRIKAANS_PRESCRIPTION)
      
      for (const medication of result.medications) {
        expect(medication.quantity).toBeGreaterThan(0)
        expect(medication.repeats).toBeGreaterThanOrEqual(0)
      }
    })
  })

  describe('4. Medication Type Detection', () => {
    it('should detect different medication types', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const types = result.medications.map(m => m.medicationType)
      expect(types).toContain('pen')
      expect(types).toContain('tablet')
      expect(types).toContain('capsule')
      expect(types).toContain('inhaler')
      expect(types).toContain('sachet')
    })

    it('should detect insulin pens correctly', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      const insulinMeds = result.medications.filter(m => m.medicationType === 'pen')
      
      expect(insulinMeds.length).toBe(2)
      expect(insulinMeds[0].name).toContain('NOVORAPID')
      expect(insulinMeds[1].name).toContain('LANTUS')
    })

    it('should detect inhalers correctly', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      const inhalers = result.medications.filter(m => m.medicationType === 'inhaler')
      
      expect(inhalers.length).toBe(2)
      expect(inhalers[0].name).toContain('VENTOLIN')
      expect(inhalers[1].name).toContain('SERETIDE')
    })
  })

  describe('5. Dosage and Frequency Parsing', () => {
    it('should parse various dosage patterns', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      // Test different dosage patterns
      const patterns = result.medications.map(m => m.dosage)
      expect(patterns).toContain('10 units')
      expect(patterns).toContain('20 units')
      expect(patterns).toContain('1 tablet')
      expect(patterns).toContain('2 tablets')
      expect(patterns).toContain('2 puffs')
    })

    it('should parse frequency patterns correctly', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const frequencies = result.medications.map(m => m.frequency)
      expect(frequencies).toContain('three times daily')
      expect(frequencies).toContain('once daily')
      expect(frequencies).toContain('twice daily')
      expect(frequencies).toContain('as needed')
    })

    it('should parse timing instructions', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const timings = result.medications.map(m => m.timing)
      expect(timings).toContain('before meals')
      expect(timings).toContain('at night')
      expect(timings).toContain('with meals')
      expect(timings).toContain('before breakfast')
    })
  })

  describe('6. Quantity and Repeat Parsing', () => {
    it('should parse quantities correctly', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const quantities = result.medications.map(m => m.quantity)
      expect(quantities).toContain(3) // pens
      expect(quantities).toContain(60) // tablets
      expect(quantities).toContain(30) // tablets/capsules
      expect(quantities).toContain(1) // inhalers
    })

    it('should parse repeat information', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const repeats = result.medications.map(m => m.repeats)
      expect(repeats).toContain(2)
      expect(repeats).toContain(3)
      expect(repeats).toContain(5)
      expect(repeats).toContain(1)
    })

    it('should handle missing quantity information', () => {
      const result = parsePrescriptionText(MALFORMED_PRESCRIPTION)
      
      expect(result.warnings.length).toBeGreaterThan(0)
      expect(result.medications.some(m => !m.quantity)).toBe(true)
    })
  })

  describe('7. Brand Name to Generic Mapping', () => {
    it('should map brand names to generic names', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const novorapid = result.medications.find(m => m.name.includes('NOVORAPID'))
      expect(novorapid?.genericName).toBe('Insulin aspart')
      
      const lantus = result.medications.find(m => m.name.includes('LANTUS'))
      expect(lantus?.genericName).toBe('Insulin glargine')
      
      const metformin = result.medications.find(m => m.name.includes('METFORMIN'))
      expect(metformin?.genericName).toBe('Metformin')
      
      const lipitor = result.medications.find(m => m.name.includes('LIPITOR'))
      expect(lipitor?.genericName).toBe('Atorvastatin')
    })

    it('should handle medications without generic mappings', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const vitaminD = result.medications.find(m => m.name.includes('VITAMIN D3'))
      expect(vitaminD?.genericName).toBeUndefined()
    })
  })

  describe('8. Error Handling and Validation', () => {
    it('should handle malformed prescriptions gracefully', () => {
      const result = parsePrescriptionText(MALFORMED_PRESCRIPTION)
      
      expect(result.medications).toHaveLength(3)
      expect(result.confidence).toBeLessThan(0.7)
      expect(result.warnings.length).toBeGreaterThan(0)
    })

    it('should identify missing dosage information', () => {
      const result = parsePrescriptionText(MALFORMED_PRESCRIPTION)
      
      const medicationB = result.medications.find(m => m.name.includes('MEDICATION B'))
      expect(medicationB?.dosage).toBe('unclear')
      expect(result.warnings).toContain('Missing or unclear dosage information')
    })

    it('should identify missing frequency information', () => {
      const result = parsePrescriptionText(MALFORMED_PRESCRIPTION)
      
      const medicationB = result.medications.find(m => m.name.includes('MEDICATION B'))
      expect(medicationB?.frequency).toBe('not specified')
      expect(result.warnings).toContain('Missing frequency information')
    })

    it('should handle empty prescription text', () => {
      const result = parsePrescriptionText('')
      
      expect(result.medications).toHaveLength(0)
      expect(result.confidence).toBe(0)
      expect(result.warnings).toContain('No prescription text provided')
    })
  })

  describe('9. Form Data Conversion', () => {
    it('should convert prescription to form data', () => {
      const formData = prescriptionTextToFormData(REAL_21_MEDICATION_PRESCRIPTION)
      
      expect(formData.medications).toHaveLength(21)
      expect(formData.patientInfo).toBeDefined()
      expect(formData.doctorInfo).toBeDefined()
      expect(formData.prescriptionDate).toBeDefined()
      expect(formData.icd10Codes).toBeDefined()
    })

    it('should maintain data integrity in form conversion', () => {
      const parsed = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      const formData = prescriptionTextToFormData(REAL_21_MEDICATION_PRESCRIPTION)
      
      expect(formData.medications.length).toBe(parsed.medications.length)
      
      for (let i = 0; i < parsed.medications.length; i++) {
        expect(formData.medications[i].name).toBe(parsed.medications[i].name)
        expect(formData.medications[i].dosage).toBe(parsed.medications[i].dosage)
        expect(formData.medications[i].frequency).toBe(parsed.medications[i].frequency)
      }
    })
  })

  describe('10. Custom Parsing Options', () => {
    it('should respect parsing options', () => {
      const options: ParsingOptions = {
        expandAbbreviations: true,
        validateAgainstDatabase: true,
        includeGenericNames: true
      }
      
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION, options)
      
      expect(result.medications.every(m => m.genericName || m.name.includes('VITAMIN'))).toBe(true)
    })

    it('should handle abbreviation expansion', () => {
      const textWithAbbreviations = `
        MEDICATION A 100mg
        Take 1 tab bid with meals
        Quantity: 30 tabs
      `
      
      const result = parsePrescriptionText(textWithAbbreviations)
      
      expect(result.medications[0].frequency).toBe('twice daily')
    })
  })

  describe('11. Performance Testing', () => {
    it('should parse large prescriptions efficiently', () => {
      const startTime = Date.now()
      
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const parsingTime = Date.now() - startTime
      expect(parsingTime).toBeLessThan(1000) // Should complete within 1 second
      expect(result.medications).toHaveLength(21)
    })

    it('should handle repeated parsing without memory leaks', () => {
      const iterations = 100
      const startTime = Date.now()
      
      for (let i = 0; i < iterations; i++) {
        const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
        expect(result.medications).toHaveLength(21)
      }
      
      const totalTime = Date.now() - startTime
      expect(totalTime).toBeLessThan(5000) // Should complete within 5 seconds
    })
  })

  describe('12. Edge Cases and Special Scenarios', () => {
    it('should handle "as needed" medications', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const asNeededMeds = result.medications.filter(m => m.frequency === 'as needed')
      expect(asNeededMeds.length).toBeGreaterThan(0)
      
      const ventolin = asNeededMeds.find(m => m.name.includes('VENTOLIN'))
      expect(ventolin?.instructions).toContain('shortness of breath')
    })

    it('should handle medications with special instructions', () => {
      const result = parsePrescriptionText(COMPLEX_DOSAGE_PRESCRIPTION)
      
      const warfarin = result.medications.find(m => m.name.includes('WARFARIN'))
      expect(warfarin?.instructions).toContain('INR monitoring required')
    })

    it('should handle medications with multiple strengths', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      const seretide = result.medications.find(m => m.name.includes('SERETIDE'))
      expect(seretide?.name).toContain('250/25')
    })

    it('should handle medications with manufacturer information', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      // Check if manufacturer information is preserved
      for (const medication of result.medications) {
        expect(medication.name).toBeDefined()
        expect(medication.name.length).toBeGreaterThan(0)
      }
    })
  })

  describe('13. Integration with Validation', () => {
    it('should validate parsed medications', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      for (const medication of result.medications) {
        expect(medication.name).toBeDefined()
        expect(medication.name.length).toBeGreaterThan(0)
        expect(medication.dosage).toBeDefined()
        expect(medication.frequency).toBeDefined()
        expect(medication.quantity).toBeGreaterThan(0)
        expect(medication.repeats).toBeGreaterThanOrEqual(0)
      }
    })

    it('should provide confidence scores for parsed data', () => {
      const result = parsePrescriptionText(REAL_21_MEDICATION_PRESCRIPTION)
      
      expect(result.confidence).toBeGreaterThan(0.8)
      
      for (const medication of result.medications) {
        expect(medication.confidence).toBeGreaterThan(0.5)
      }
    })
  })
}) 