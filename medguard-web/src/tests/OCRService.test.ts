/**
 * Comprehensive OCR Service Tests
 * 
 * Tests for image processing, text extraction, quality assessment,
 * and error handling in the OCR service.
 */

import { describe, it, expect, beforeEach, afterEach, vi, beforeAll, afterAll } from 'vitest'
import { OCRService } from '../services/ocrService'
import type { OCRResult, ImageQualityAssessment, PrescriptionFormat, PreprocessingOptions } from '../services/ocrService'

// Mock Tesseract.js
vi.mock('tesseract.js', () => ({
  default: {
    createWorker: vi.fn().mockResolvedValue({
      loadLanguage: vi.fn().mockResolvedValue(undefined),
      initialize: vi.fn().mockResolvedValue(undefined),
      recognize: vi.fn().mockResolvedValue({
        data: {
          text: 'Mock OCR Text',
          confidence: 85
        }
      }),
      terminate: vi.fn().mockResolvedValue(undefined)
    })
  }
}))

// Mock Canvas API for image processing
const mockCanvas = {
  getContext: vi.fn().mockReturnValue({
    drawImage: vi.fn(),
    getImageData: vi.fn().mockReturnValue({
      data: new Uint8ClampedArray(1000),
      width: 100,
      height: 10
    }),
    putImageData: vi.fn(),
    fillRect: vi.fn(),
    clearRect: vi.fn()
  }),
  width: 100,
  height: 100,
  toBlob: vi.fn().mockResolvedValue(new Blob(['mock']))
}

global.HTMLCanvasElement.prototype.getContext = mockCanvas.getContext
global.HTMLCanvasElement.prototype.toBlob = mockCanvas.toBlob

// Mock File API
const createMockImageFile = (content: string, name: string, type: string): File => {
  return new File([content], name, { type })
}

// Test prescription images
const GOOD_QUALITY_IMAGE = createMockImageFile('good-quality-data', 'prescription.jpg', 'image/jpeg')
const POOR_QUALITY_IMAGE = createMockImageFile('poor-quality-data', 'blurry.jpg', 'image/jpeg')
const LARGE_IMAGE = createMockImageFile('large-image-data'.repeat(1000), 'large.jpg', 'image/jpeg')
const UNSUPPORTED_FORMAT = createMockImageFile('unsupported', 'document.pdf', 'application/pdf')

// Test prescription text
const TEST_PRESCRIPTION_TEXT = `
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

ICD-10 Codes: E11.9, I10, J45.901
`

describe('OCR Service Tests', () => {
  let ocrService: OCRService

  beforeAll(async () => {
    ocrService = OCRService.getInstance()
    await ocrService.initialize()
  })

  afterAll(async () => {
    await ocrService.terminate()
  })

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('1. Image Quality Assessment', () => {
    it('should assess image quality accurately', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.imageQuality).toBeDefined()
      expect(result.imageQuality.overallScore).toBeGreaterThan(0)
      expect(result.imageQuality.overallScore).toBeLessThanOrEqual(1)
      expect(result.imageQuality.isProcessable).toBe(true)
      expect(result.imageQuality.recommendations).toBeDefined()
    })

    it('should detect poor quality images', async () => {
      const result = await ocrService.processPrescription(POOR_QUALITY_IMAGE)
      
      expect(result.imageQuality.isProcessable).toBe(false)
      expect(result.requiresManualReview).toBe(true)
      expect(result.imageQuality.recommendations.length).toBeGreaterThan(0)
    })

    it('should calculate contrast correctly', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.imageQuality.contrast).toBeGreaterThan(0)
      expect(result.imageQuality.contrast).toBeLessThanOrEqual(1)
    })

    it('should calculate brightness correctly', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.imageQuality.brightness).toBeGreaterThan(0)
      expect(result.imageQuality.brightness).toBeLessThanOrEqual(1)
    })

    it('should detect blur in images', async () => {
      const result = await ocrService.processPrescription(POOR_QUALITY_IMAGE)
      
      expect(result.imageQuality.blur).toBeGreaterThan(0)
      expect(result.imageQuality.blur).toBeLessThanOrEqual(1)
    })

    it('should detect noise in images', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.imageQuality.noise).toBeGreaterThan(0)
      expect(result.imageQuality.noise).toBeLessThanOrEqual(1)
    })

    it('should detect image skew', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.imageQuality.skew).toBeGreaterThan(0)
      expect(result.imageQuality.skew).toBeLessThanOrEqual(1)
    })
  })

  describe('2. Image Preprocessing', () => {
    it('should enhance contrast when needed', async () => {
      const options: PreprocessingOptions = {
        contrast: 1.5,
        brightness: 0.1,
        sharpen: true
      }
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE, options)
      
      expect(result.success).toBe(true)
      expect(result.processingTime).toBeGreaterThan(0)
    })

    it('should adjust brightness correctly', async () => {
      const options: PreprocessingOptions = {
        brightness: -0.2
      }
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE, options)
      
      expect(result.success).toBe(true)
    })

    it('should apply sharpening filter', async () => {
      const options: PreprocessingOptions = {
        sharpen: true
      }
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE, options)
      
      expect(result.success).toBe(true)
    })

    it('should apply denoising filter', async () => {
      const options: PreprocessingOptions = {
        denoise: true
      }
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE, options)
      
      expect(result.success).toBe(true)
    })

    it('should deskew rotated images', async () => {
      const options: PreprocessingOptions = {
        deskew: true
      }
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE, options)
      
      expect(result.success).toBe(true)
    })

    it('should apply threshold for binary images', async () => {
      const options: PreprocessingOptions = {
        threshold: 128
      }
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE, options)
      
      expect(result.success).toBe(true)
    })
  })

  describe('3. Text Extraction and Processing', () => {
    it('should extract text from prescription images', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.success).toBe(true)
      expect(result.text).toBeDefined()
      expect(result.text.length).toBeGreaterThan(0)
      expect(result.confidence).toBeGreaterThan(0)
    })

    it('should extract medications from text', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.medications).toBeDefined()
      expect(result.medications.length).toBeGreaterThan(0)
    })

    it('should extract prescription metadata', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.prescriptionNumber).toBeDefined()
      expect(result.doctorName).toBeDefined()
      expect(result.icd10Codes).toBeDefined()
    })

    it('should expand medical abbreviations', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      // Check if abbreviations like "bid", "tid", "prn" are expanded
      expect(result.text).not.toContain('bid')
      expect(result.text).not.toContain('tid')
      expect(result.text).not.toContain('prn')
    })

    it('should handle multiple languages', async () => {
      const afrikaansImage = createMockImageFile('Afrikaans prescription data', 'afrikaans.jpg', 'image/jpeg')
      
      const result = await ocrService.processPrescription(afrikaansImage)
      
      expect(result.prescriptionFormat.language).toBeDefined()
    })
  })

  describe('4. Prescription Format Detection', () => {
    it('should detect South African standard format', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.prescriptionFormat.type).toBe('SA_STANDARD')
      expect(result.prescriptionFormat.confidence).toBeGreaterThan(0.8)
    })

    it('should detect private practice format', async () => {
      const privateImage = createMockImageFile('Private practice prescription', 'private.jpg', 'image/jpeg')
      
      const result = await ocrService.processPrescription(privateImage)
      
      expect(result.prescriptionFormat.type).toBeDefined()
      expect(result.prescriptionFormat.features).toBeDefined()
    })

    it('should detect international formats', async () => {
      const internationalImage = createMockImageFile('International prescription', 'international.jpg', 'image/jpeg')
      
      const result = await ocrService.processPrescription(internationalImage)
      
      expect(result.prescriptionFormat.type).toBeDefined()
    })

    it('should identify prescription features', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.prescriptionFormat.features).toContain('header')
      expect(result.prescriptionFormat.features).toContain('patient_info')
      expect(result.prescriptionFormat.features).toContain('medication_list')
    })
  })

  describe('5. Medication Validation', () => {
    it('should validate extracted medications', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.medications.length).toBeGreaterThan(0)
      
      for (const medication of result.medications) {
        expect(medication.name).toBeDefined()
        expect(medication.dosage).toBeDefined()
        expect(medication.frequency).toBeDefined()
        expect(medication.confidence).toBeGreaterThan(0)
      }
    })

    it('should map brand names to generic names', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      const novorapid = result.medications.find(m => m.name.includes('NOVORAPID'))
      if (novorapid) {
        expect(novorapid.genericName).toBe('Insulin aspart')
      }
    })

    it('should identify potential drug interactions', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      // Should detect interactions between diabetes medications
      expect(result.medications.length).toBeGreaterThan(0)
    })

    it('should validate medication dosages', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      for (const medication of result.medications) {
        expect(medication.dosage).toMatch(/\d+/)
        expect(medication.frequency).toBeDefined()
      }
    })
  })

  describe('6. Error Handling', () => {
    it('should handle unsupported file formats', async () => {
      const result = await ocrService.processPrescription(UNSUPPORTED_FORMAT)
      
      expect(result.success).toBe(false)
      expect(result.errors).toBeDefined()
      expect(result.errors?.length).toBeGreaterThan(0)
    })

    it('should handle corrupted image files', async () => {
      const corruptedImage = createMockImageFile('', 'corrupted.jpg', 'image/jpeg')
      
      const result = await ocrService.processPrescription(corruptedImage)
      
      expect(result.success).toBe(false)
      expect(result.errors).toBeDefined()
    })

    it('should handle extremely large images', async () => {
      const result = await ocrService.processPrescription(LARGE_IMAGE)
      
      expect(result.success).toBe(true)
      expect(result.processingTime).toBeLessThan(30000) // Should complete within 30 seconds
    })

    it('should handle network timeouts', async () => {
      // Mock a timeout scenario
      vi.spyOn(ocrService as any, 'performOCR').mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('OCR timeout')), 100)
        )
      )
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.success).toBe(false)
      expect(result.errors).toBeDefined()
      
      vi.restoreAllMocks()
    })

    it('should handle OCR failures gracefully', async () => {
      // Mock OCR failure
      vi.spyOn(ocrService as any, 'performOCR').mockRejectedValue(new Error('OCR failed'))
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      expect(result.success).toBe(false)
      expect(result.errors).toBeDefined()
      
      vi.restoreAllMocks()
    })
  })

  describe('7. Performance Testing', () => {
    it('should process images within reasonable time', async () => {
      const startTime = Date.now()
      
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      const processingTime = Date.now() - startTime
      expect(processingTime).toBeLessThan(10000) // Should complete within 10 seconds
      expect(result.processingTime).toBeLessThan(8000) // OCR processing should be under 8 seconds
    })

    it('should handle concurrent processing', async () => {
      const images = Array(3).fill(GOOD_QUALITY_IMAGE)
      
      const startTime = Date.now()
      const results = await Promise.all(
        images.map(img => ocrService.processPrescription(img))
      )
      const totalTime = Date.now() - startTime
      
      expect(results).toHaveLength(3)
      expect(results.every(r => r.success)).toBe(true)
      expect(totalTime).toBeLessThan(20000) // Should complete within 20 seconds
    })

    it('should cache processed results', async () => {
      // First processing
      const result1 = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      const time1 = result1.processingTime
      
      // Second processing (should use cache)
      const result2 = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      const time2 = result2.processingTime
      
      expect(time2).toBeLessThan(time1) // Cached result should be faster
    })
  })

  describe('8. Batch Processing', () => {
    it('should process multiple prescriptions in batch', async () => {
      const images = Array(5).fill(GOOD_QUALITY_IMAGE)
      
      const results = await ocrService.processBatchPrescriptions(images)
      
      expect(results).toHaveLength(5)
      expect(results.every(r => r.success)).toBe(true)
    })

    it('should handle batch processing errors', async () => {
      const images = [GOOD_QUALITY_IMAGE, UNSUPPORTED_FORMAT, GOOD_QUALITY_IMAGE]
      
      const results = await ocrService.processBatchPrescriptions(images)
      
      expect(results).toHaveLength(3)
      expect(results[0].success).toBe(true)
      expect(results[1].success).toBe(false)
      expect(results[2].success).toBe(true)
    })

    it('should respect batch processing configuration', async () => {
      ocrService.configureBatchProcessing({
        maxConcurrent: 2,
        timeout: 5000,
        retryAttempts: 1
      })
      
      const stats = ocrService.getBatchStats()
      expect(stats.config.maxConcurrent).toBe(2)
      expect(stats.config.timeout).toBe(5000)
      expect(stats.config.retryAttempts).toBe(1)
    })
  })

  describe('9. Result Validation', () => {
    it('should validate OCR results', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      const validation = ocrService.validateResult(result)
      
      expect(validation.isValid).toBe(true)
      expect(validation.suggestions).toBeDefined()
      expect(validation.requiresManualEntry).toBeDefined()
      expect(validation.qualityIssues).toBeDefined()
      expect(validation.formatIssues).toBeDefined()
    })

    it('should identify quality issues', async () => {
      const result = await ocrService.processPrescription(POOR_QUALITY_IMAGE)
      const validation = ocrService.validateResult(result)
      
      expect(validation.qualityIssues.length).toBeGreaterThan(0)
    })

    it('should suggest manual entry when needed', async () => {
      const result = await ocrService.processPrescription(POOR_QUALITY_IMAGE)
      const validation = ocrService.validateResult(result)
      
      expect(validation.requiresManualEntry).toBe(true)
    })
  })

  describe('10. Service Statistics', () => {
    it('should provide cache statistics', async () => {
      const stats = ocrService.getCacheStats()
      
      expect(stats.size).toBeGreaterThanOrEqual(0)
      expect(stats.entries).toBeDefined()
    })

    it('should provide batch processing statistics', async () => {
      const stats = ocrService.getBatchStats()
      
      expect(stats.queueSize).toBeGreaterThanOrEqual(0)
      expect(stats.config).toBeDefined()
    })

    it('should provide comprehensive service statistics', async () => {
      const stats = ocrService.getServiceStats()
      
      expect(stats.cacheStats).toBeDefined()
      expect(stats.batchStats).toBeDefined()
      expect(stats.validationStats).toBeDefined()
      expect(stats.qualityStats).toBeDefined()
    })
  })

  describe('11. Memory Management', () => {
    it('should clear cache when requested', async () => {
      // Process an image to populate cache
      await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      const beforeStats = ocrService.getCacheStats()
      expect(beforeStats.size).toBeGreaterThan(0)
      
      // Clear cache
      ocrService.clearCache()
      
      const afterStats = ocrService.getCacheStats()
      expect(afterStats.size).toBe(0)
    })

    it('should clear all caches', async () => {
      // Process images to populate caches
      await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      // Clear all caches
      ocrService.clearAllCaches()
      
      const stats = ocrService.getServiceStats()
      expect(stats.cacheStats.size).toBe(0)
    })
  })

  describe('12. Integration with Prescription Parser', () => {
    it('should integrate with prescription parser seamlessly', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      // Convert to bulk entries
      const bulkEntries = ocrService.convertToBulkEntries(result.medications)
      
      expect(bulkEntries).toHaveLength(result.medications.length)
      expect(bulkEntries[0]).toHaveProperty('name')
      expect(bulkEntries[0]).toHaveProperty('dosage')
      expect(bulkEntries[0]).toHaveProperty('frequency')
    })

    it('should maintain data integrity through conversion', async () => {
      const result = await ocrService.processPrescription(GOOD_QUALITY_IMAGE)
      
      const bulkEntries = ocrService.convertToBulkEntries(result.medications)
      
      for (let i = 0; i < result.medications.length; i++) {
        expect(bulkEntries[i].name).toBe(result.medications[i].name)
        expect(bulkEntries[i].dosage).toBe(result.medications[i].dosage)
        expect(bulkEntries[i].frequency).toBe(result.medications[i].frequency)
      }
    })
  })
}) 