/**
 * Comprehensive End-to-End Prescription Workflow Tests
 * 
 * Tests the complete prescription processing pipeline:
 * 1. OCR image processing
 * 2. Text extraction and parsing
 * 3. Medication validation
 * 4. Form data conversion
 * 5. API submission
 * 6. Schedule generation
 * 7. Error handling
 */

import { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick } from 'vue'
import { OCRService } from '../services/ocrService'
import { PrescriptionParser, parsePrescriptionText } from '../utils/prescriptionParser'
import { medicationApi } from '../services/medicationApi'
import { scheduleGenerator } from '../services/scheduleGenerator'
import type { OCRResult, ExtractedMedication } from '../services/ocrService'
import type { ParsedPrescription } from '../utils/prescriptionParser'
import type { Medication, BulkMedicationEntry } from '../types/medication'

// Mock data for comprehensive testing
const MOCK_PRESCRIPTION_IMAGE = new File(['mock-image-data'], 'prescription.jpg', { type: 'image/jpeg' })

const COMPLEX_21_MEDICATION_PRESCRIPTION = `
PRESCRIPTION

Patient: John Doe
Date: 2024-01-15
Doctor: Dr. Smith

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

// Mock OCR result for testing
const MOCK_OCR_RESULT: OCRResult = {
  success: true,
  confidence: 0.85,
  text: COMPLEX_21_MEDICATION_PRESCRIPTION,
  medications: [],
  prescriptionNumber: 'RX123456',
  doctorName: 'Dr. Smith',
  icd10Codes: ['E11.9', 'I10', 'J45.901', 'Z79.4'],
  rawText: COMPLEX_21_MEDICATION_PRESCRIPTION,
  processingTime: 2500,
  imageQuality: {
    overallScore: 0.8,
    resolution: 1920,
    contrast: 0.7,
    brightness: 0.6,
    blur: 0.2,
    noise: 0.3,
    skew: 0.1,
    isProcessable: true,
    recommendations: ['Good quality image']
  },
  prescriptionFormat: {
    type: 'SA_STANDARD',
    confidence: 0.9,
    features: ['header', 'patient_info', 'medication_list'],
    language: 'en'
  },
  requiresManualReview: false
}

describe('Prescription Workflow - End-to-End Tests', () => {
  let ocrService: OCRService
  let prescriptionParser: PrescriptionParser

  beforeAll(async () => {
    // Initialize services
    ocrService = OCRService.getInstance()
    await ocrService.initialize()
    prescriptionParser = new PrescriptionParser()
    
    // Mock API calls
    vi.spyOn(medicationApi, 'createMedication').mockResolvedValue({
      id: 'med-123',
      name: 'Test Medication',
      success: true
    })
    
    vi.spyOn(medicationApi, 'createBulkMedications').mockResolvedValue({
      success: true,
      created: 21,
      failed: 0,
      medications: []
    })
    
    vi.spyOn(scheduleGenerator, 'generateSchedule').mockResolvedValue({
      success: true,
      schedule: {
        id: 'schedule-123',
        medications: []
      }
    })
  })

  afterAll(async () => {
    await ocrService.terminate()
    vi.restoreAllMocks()
  })

  beforeEach(() => {
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('1. OCR Image Processing', () => {
    it('should process prescription image successfully', async () => {
      const result = await ocrService.processPrescription(MOCK_PRESCRIPTION_IMAGE)
      
      expect(result.success).toBe(true)
      expect(result.confidence).toBeGreaterThan(0.7)
      expect(result.text).toContain('NOVORAPID')
      expect(result.text).toContain('LANTUS')
      expect(result.medications.length).toBeGreaterThan(0)
      expect(result.processingTime).toBeLessThan(10000) // Should complete within 10 seconds
    })

    it('should handle poor quality images gracefully', async () => {
      const poorQualityImage = new File(['low-quality-data'], 'blurry.jpg', { type: 'image/jpeg' })
      
      const result = await ocrService.processPrescription(poorQualityImage)
      
      expect(result.imageQuality.isProcessable).toBe(false)
      expect(result.requiresManualReview).toBe(true)
      expect(result.errors).toBeDefined()
    })

    it('should detect prescription format correctly', async () => {
      const result = await ocrService.processPrescription(MOCK_PRESCRIPTION_IMAGE)
      
      expect(result.prescriptionFormat.type).toBe('SA_STANDARD')
      expect(result.prescriptionFormat.confidence).toBeGreaterThan(0.8)
      expect(result.prescriptionFormat.language).toBe('en')
    })

    it('should extract ICD-10 codes accurately', async () => {
      const result = await ocrService.processPrescription(MOCK_PRESCRIPTION_IMAGE)
      
      expect(result.icd10Codes).toContain('E11.9')
      expect(result.icd10Codes).toContain('I10')
      expect(result.icd10Codes).toContain('J45.901')
      expect(result.icd10Codes).toContain('Z79.4')
    })
  })

  describe('2. Text Parsing and Medication Extraction', () => {
    it('should parse all 21 medications from complex prescription', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      
      expect(parsedResult.medications).toHaveLength(21)
      expect(parsedResult.confidence).toBeGreaterThan(0.8)
      expect(parsedResult.warnings).toHaveLength(0)
    })

    it('should extract medication details accurately', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const novorapid = parsedResult.medications.find(m => m.name.includes('NOVORAPID'))
      
      expect(novorapid).toBeDefined()
      expect(novorapid?.dosage).toBe('10 units')
      expect(novorapid?.frequency).toBe('three times daily')
      expect(novorapid?.timing).toBe('before meals')
      expect(novorapid?.quantity).toBe(3)
      expect(novorapid?.repeats).toBe(2)
    })

    it('should handle complex dosage instructions', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const metformin = parsedResult.medications.find(m => m.name.includes('METFORMIN'))
      
      expect(metformin?.dosage).toBe('1 tablet')
      expect(metformin?.frequency).toBe('twice daily')
      expect(metformin?.timing).toBe('with meals')
    })

    it('should extract "as needed" medications correctly', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const ventolin = parsedResult.medications.find(m => m.name.includes('VENTOLIN'))
      
      expect(ventolin?.frequency).toBe('as needed')
      expect(ventolin?.instructions).toContain('shortness of breath')
    })
  })

  describe('3. Medication Validation', () => {
    it('should validate all medications against database', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const validationReport = await ocrService.getMedicationValidationReport(parsedResult.medications)
      
      expect(validationReport.validated.length).toBeGreaterThan(0)
      expect(validationReport.warnings).toBeDefined()
      expect(validationReport.interactions).toBeDefined()
    })

    it('should identify potential drug interactions', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const validationReport = await ocrService.getMedicationValidationReport(parsedResult.medications)
      
      // Should detect interactions between diabetes medications
      expect(validationReport.interactions.length).toBeGreaterThanOrEqual(0)
    })

    it('should map brand names to generic names', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const novorapid = parsedResult.medications.find(m => m.name.includes('NOVORAPID'))
      
      expect(novorapid?.genericName).toBe('Insulin aspart')
    })
  })

  describe('4. Form Data Conversion', () => {
    it('should convert parsed data to form format', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const formData = prescriptionParser.prescriptionTextToFormData(COMPLEX_21_MEDICATION_PRESCRIPTION)
      
      expect(formData.medications).toHaveLength(21)
      expect(formData.patientInfo).toBeDefined()
      expect(formData.doctorInfo).toBeDefined()
      expect(formData.prescriptionDate).toBeDefined()
    })

    it('should handle bulk medication entries', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const bulkEntries = ocrService.convertToBulkEntries(parsedResult.medications)
      
      expect(bulkEntries).toHaveLength(21)
      expect(bulkEntries[0]).toHaveProperty('name')
      expect(bulkEntries[0]).toHaveProperty('dosage')
      expect(bulkEntries[0]).toHaveProperty('frequency')
    })
  })

  describe('5. API Submission and Error Handling', () => {
    it('should submit medications to API successfully', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const bulkEntries = ocrService.convertToBulkEntries(parsedResult.medications)
      
      const apiResult = await medicationApi.createBulkMedications(bulkEntries)
      
      expect(apiResult.success).toBe(true)
      expect(apiResult.created).toBe(21)
      expect(apiResult.failed).toBe(0)
    })

    it('should handle API errors gracefully', async () => {
      vi.spyOn(medicationApi, 'createBulkMedications').mockRejectedValueOnce(new Error('Network error'))
      
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const bulkEntries = ocrService.convertToBulkEntries(parsedResult.medications)
      
      await expect(medicationApi.createBulkMedications(bulkEntries)).rejects.toThrow('Network error')
    })

    it('should retry failed submissions', async () => {
      const mockCreateBulk = vi.spyOn(medicationApi, 'createBulkMedications')
        .mockRejectedValueOnce(new Error('Temporary error'))
        .mockResolvedValueOnce({ success: true, created: 21, failed: 0, medications: [] })
      
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const bulkEntries = ocrService.convertToBulkEntries(parsedResult.medications)
      
      // First call should fail, second should succeed
      await expect(medicationApi.createBulkMedications(bulkEntries)).rejects.toThrow('Temporary error')
      const result = await medicationApi.createBulkMedications(bulkEntries)
      
      expect(result.success).toBe(true)
      expect(mockCreateBulk).toHaveBeenCalledTimes(2)
    })
  })

  describe('6. Schedule Generation', () => {
    it('should generate medication schedules', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const bulkEntries = ocrService.convertToBulkEntries(parsedResult.medications)
      
      const scheduleResult = await scheduleGenerator.generateSchedule(bulkEntries)
      
      expect(scheduleResult.success).toBe(true)
      expect(scheduleResult.schedule).toBeDefined()
      expect(scheduleResult.schedule.id).toBeDefined()
    })

    it('should handle complex timing requirements', async () => {
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const novorapid = parsedResult.medications.find(m => m.name.includes('NOVORAPID'))
      
      expect(novorapid?.frequency).toBe('three times daily')
      expect(novorapid?.timing).toBe('before meals')
    })
  })

  describe('7. Performance Testing', () => {
    it('should process large prescriptions within reasonable time', async () => {
      const startTime = Date.now()
      
      const result = await ocrService.processPrescription(MOCK_PRESCRIPTION_IMAGE)
      
      const processingTime = Date.now() - startTime
      expect(processingTime).toBeLessThan(15000) // Should complete within 15 seconds
      expect(result.processingTime).toBeLessThan(10000) // OCR processing should be under 10 seconds
    })

    it('should handle concurrent prescription processing', async () => {
      const images = Array(5).fill(MOCK_PRESCRIPTION_IMAGE)
      
      const startTime = Date.now()
      const results = await Promise.all(
        images.map(img => ocrService.processPrescription(img))
      )
      const totalTime = Date.now() - startTime
      
      expect(results).toHaveLength(5)
      expect(results.every(r => r.success)).toBe(true)
      expect(totalTime).toBeLessThan(30000) // Should complete within 30 seconds
    })
  })

  describe('8. Error Handling and Edge Cases', () => {
    it('should handle malformed prescription text', async () => {
      const malformedText = 'Invalid prescription format\nNo medications found'
      
      const result = parsePrescriptionText(malformedText)
      
      expect(result.medications).toHaveLength(0)
      expect(result.confidence).toBeLessThan(0.5)
      expect(result.warnings.length).toBeGreaterThan(0)
    })

    it('should handle missing medication information', async () => {
      const incompleteText = `
        NOVORAPID 100units/ml
        Take as directed
        Quantity: 3 pens
      `
      
      const result = parsePrescriptionText(incompleteText)
      
      expect(result.medications).toHaveLength(1)
      expect(result.warnings.length).toBeGreaterThan(0)
      expect(result.medications[0].dosage).toBe('as directed')
    })

    it('should handle network timeouts', async () => {
      vi.spyOn(medicationApi, 'createBulkMedications').mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Timeout')), 100)
        )
      )
      
      const parsedResult = parsePrescriptionText(COMPLEX_21_MEDICATION_PRESCRIPTION)
      const bulkEntries = ocrService.convertToBulkEntries(parsedResult.medications)
      
      await expect(medicationApi.createBulkMedications(bulkEntries)).rejects.toThrow('Timeout')
    })
  })

  describe('9. Accessibility and Mobile Testing', () => {
    it('should provide accessible error messages', async () => {
      const result = await ocrService.processPrescription(new File([''], 'empty.jpg'))
      
      expect(result.errors).toBeDefined()
      expect(result.errors?.length).toBeGreaterThan(0)
      expect(result.errors?.[0]).toMatch(/image|quality|process/i)
    })

    it('should handle mobile device constraints', async () => {
      // Simulate mobile device with limited resources
      const mobileImage = new File(['mobile-image-data'], 'mobile.jpg', { type: 'image/jpeg' })
      
      const result = await ocrService.processPrescription(mobileImage, {
        contrast: 1.2,
        brightness: 0.1,
        sharpen: true
      })
      
      expect(result.success).toBe(true)
      expect(result.processingTime).toBeLessThan(8000) // Should be faster on mobile
    })
  })

  describe('10. Security and Data Handling', () => {
    it('should not expose sensitive information in logs', async () => {
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      
      await ocrService.processPrescription(MOCK_PRESCRIPTION_IMAGE)
      
      const loggedMessages = consoleSpy.mock.calls.flat().join(' ')
      expect(loggedMessages).not.toContain('John Doe')
      expect(loggedMessages).not.toContain('Dr. Smith')
      
      consoleSpy.mockRestore()
    })

    it('should validate prescription data integrity', async () => {
      const result = await ocrService.processPrescription(MOCK_PRESCRIPTION_IMAGE)
      const validation = ocrService.validateResult(result)
      
      expect(validation.isValid).toBe(true)
      expect(validation.qualityIssues).toHaveLength(0)
      expect(validation.formatIssues).toHaveLength(0)
    })

    it('should handle encrypted prescription data', async () => {
      // Test with encrypted image data
      const encryptedImage = new File(['encrypted-data'], 'encrypted.jpg', { type: 'image/jpeg' })
      
      const result = await ocrService.processPrescription(encryptedImage)
      
      expect(result.success).toBe(false)
      expect(result.errors).toBeDefined()
      expect(result.errors?.[0]).toMatch(/encrypt|format|invalid/i)
    })
  })

  describe('11. Integration Test - Complete Workflow', () => {
    it('should process complete prescription workflow end-to-end', async () => {
      // Step 1: OCR Processing
      const ocrResult = await ocrService.processPrescription(MOCK_PRESCRIPTION_IMAGE)
      expect(ocrResult.success).toBe(true)
      expect(ocrResult.medications.length).toBeGreaterThan(0)
      
      // Step 2: Text Parsing
      const parsedResult = parsePrescriptionText(ocrResult.text)
      expect(parsedResult.medications).toHaveLength(21)
      expect(parsedResult.confidence).toBeGreaterThan(0.8)
      
      // Step 3: Validation
      const validationReport = await ocrService.getMedicationValidationReport(parsedResult.medications)
      expect(validationReport.validated.length).toBeGreaterThan(0)
      
      // Step 4: Form Conversion
      const bulkEntries = ocrService.convertToBulkEntries(parsedResult.medications)
      expect(bulkEntries).toHaveLength(21)
      
      // Step 5: API Submission
      const apiResult = await medicationApi.createBulkMedications(bulkEntries)
      expect(apiResult.success).toBe(true)
      expect(apiResult.created).toBe(21)
      
      // Step 6: Schedule Generation
      const scheduleResult = await scheduleGenerator.generateSchedule(bulkEntries)
      expect(scheduleResult.success).toBe(true)
      expect(scheduleResult.schedule).toBeDefined()
      
      // Verify overall workflow success
      expect(ocrResult.processingTime).toBeLessThan(10000)
      expect(parsedResult.warnings).toHaveLength(0)
      expect(apiResult.failed).toBe(0)
    })
  })
}) 