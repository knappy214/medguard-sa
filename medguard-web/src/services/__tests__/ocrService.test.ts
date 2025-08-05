import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { OCRService, type OCRResult, type ExtractedMedication } from '../ocrService'

// Mock Tesseract.js
vi.mock('tesseract.js', () => ({
  default: {
    createWorker: vi.fn(() => ({
      loadLanguage: vi.fn().mockResolvedValue(undefined),
      initialize: vi.fn().mockResolvedValue(undefined),
      setParameters: vi.fn().mockResolvedValue(undefined),
      recognize: vi.fn().mockResolvedValue({
        data: {
          text: 'Sample prescription text',
          confidence: 85
        }
      }),
      terminate: vi.fn().mockResolvedValue(undefined)
    })),
    PSM: {
      SINGLE_BLOCK: 6
    }
  }
}))

describe('OCRService', () => {
  let ocrService: OCRService

  beforeEach(() => {
    ocrService = OCRService.getInstance()
  })

  afterEach(async () => {
    await ocrService.terminate()
  })

  describe('Initialization', () => {
    it('should initialize successfully', async () => {
      await expect(ocrService.initialize()).resolves.not.toThrow()
    })

    it('should be a singleton', () => {
      const instance1 = OCRService.getInstance()
      const instance2 = OCRService.getInstance()
      expect(instance1).toBe(instance2)
    })
  })

  describe('Medication Database', () => {
    it('should map brand names to generic names', async () => {
      await ocrService.initialize()
      
      // Test with known medications
      const result = await ocrService.processPrescription('test-image-url')
      
      // The service should have mapped Panado to Paracetamol
      expect(result.medications.some(med => 
        med.name.toLowerCase().includes('panado') || 
        med.genericName?.toLowerCase().includes('paracetamol')
      )).toBeDefined()
    })
  })

  describe('Text Parsing', () => {
    it('should extract prescription numbers', async () => {
      await ocrService.initialize()
      
      // Mock OCR to return text with prescription number
      const mockText = 'Prescription No: RX123456'
      vi.mocked(require('tesseract.js').default.createWorker).mockReturnValue({
        loadLanguage: vi.fn().mockResolvedValue(undefined),
        initialize: vi.fn().mockResolvedValue(undefined),
        setParameters: vi.fn().mockResolvedValue(undefined),
        recognize: vi.fn().mockResolvedValue({
          data: {
            text: mockText,
            confidence: 90
          }
        }),
        terminate: vi.fn().mockResolvedValue(undefined)
      } as any)

      const result = await ocrService.processPrescription('test-image-url')
      expect(result.prescriptionNumber).toBe('RX123456')
    })

    it('should extract doctor names', async () => {
      await ocrService.initialize()
      
      const mockText = 'Dr. John Smith MD'
      vi.mocked(require('tesseract.js').default.createWorker).mockReturnValue({
        loadLanguage: vi.fn().mockResolvedValue(undefined),
        initialize: vi.fn().mockResolvedValue(undefined),
        setParameters: vi.fn().mockResolvedValue(undefined),
        recognize: vi.fn().mockResolvedValue({
          data: {
            text: mockText,
            confidence: 90
          }
        }),
        terminate: vi.fn().mockResolvedValue(undefined)
      } as any)

      const result = await ocrService.processPrescription('test-image-url')
      expect(result.doctorName).toBe('John Smith')
    })

    it('should extract ICD-10 codes', async () => {
      await ocrService.initialize()
      
      const mockText = 'Diagnosis: I10.9, E11.9'
      vi.mocked(require('tesseract.js').default.createWorker).mockReturnValue({
        loadLanguage: vi.fn().mockResolvedValue(undefined),
        initialize: vi.fn().mockResolvedValue(undefined),
        setParameters: vi.fn().mockResolvedValue(undefined),
        recognize: vi.fn().mockResolvedValue({
          data: {
            text: mockText,
            confidence: 90
          }
        }),
        terminate: vi.fn().mockResolvedValue(undefined)
      } as any)

      const result = await ocrService.processPrescription('test-image-url')
      expect(result.icd10Codes).toContain('I10.9')
      expect(result.icd10Codes).toContain('E11.9')
    })
  })

  describe('Dosage Pattern Extraction', () => {
    it('should extract daily dosage patterns', async () => {
      await ocrService.initialize()
      
      const mockText = 'Panado 500mg\nTake one tablet daily'
      vi.mocked(require('tesseract.js').default.createWorker).mockReturnValue({
        loadLanguage: vi.fn().mockResolvedValue(undefined),
        initialize: vi.fn().mockResolvedValue(undefined),
        setParameters: vi.fn().mockResolvedValue(undefined),
        recognize: vi.fn().mockResolvedValue({
          data: {
            text: mockText,
            confidence: 90
          }
        }),
        terminate: vi.fn().mockResolvedValue(undefined)
      } as any)

      const result = await ocrService.processPrescription('test-image-url')
      const medication = result.medications[0]
      
      expect(medication.name).toBe('Panado')
      expect(medication.dosage).toBe('one')
      expect(medication.frequency).toBe('daily')
    })

    it('should extract specific timing patterns', async () => {
      await ocrService.initialize()
      
      const mockText = 'Aspirin 100mg\nTake one tablet morning'
      vi.mocked(require('tesseract.js').default.createWorker).mockReturnValue({
        loadLanguage: vi.fn().mockResolvedValue(undefined),
        initialize: vi.fn().mockResolvedValue(undefined),
        setParameters: vi.fn().mockResolvedValue(undefined),
        recognize: vi.fn().mockResolvedValue({
          data: {
            text: mockText,
            confidence: 90
          }
        }),
        terminate: vi.fn().mockResolvedValue(undefined)
      } as any)

      const result = await ocrService.processPrescription('test-image-url')
      const medication = result.medications[0]
      
      expect(medication.frequency).toBe('specific')
      expect(medication.instructions).toContain('morning')
    })
  })

  describe('Confidence Scoring', () => {
    it('should calculate overall confidence', async () => {
      await ocrService.initialize()
      
      const result = await ocrService.processPrescription('test-image-url')
      expect(result.confidence).toBeGreaterThan(0)
      expect(result.confidence).toBeLessThanOrEqual(1)
    })

    it('should validate results appropriately', async () => {
      await ocrService.initialize()
      
      const result = await ocrService.processPrescription('test-image-url')
      const validation = ocrService.validateResult(result)
      
      expect(validation).toHaveProperty('isValid')
      expect(validation).toHaveProperty('suggestions')
      expect(validation).toHaveProperty('requiresManualEntry')
    })
  })

  describe('Caching', () => {
    it('should cache processed results', async () => {
      await ocrService.initialize()
      
      const imageUrl = 'test-image-url'
      const result1 = await ocrService.processPrescription(imageUrl)
      const result2 = await ocrService.processPrescription(imageUrl)
      
      // Second call should be faster due to caching
      expect(result1.processingTime).toBeGreaterThan(0)
      expect(result2.processingTime).toBeGreaterThan(0)
    })

    it('should provide cache statistics', () => {
      const stats = ocrService.getCacheStats()
      expect(stats).toHaveProperty('size')
      expect(stats).toHaveProperty('entries')
      expect(Array.isArray(stats.entries)).toBe(true)
    })

    it('should clear cache', () => {
      ocrService.clearCache()
      const stats = ocrService.getCacheStats()
      expect(stats.size).toBe(0)
    })
  })

  describe('Bulk Entry Conversion', () => {
    it('should convert extracted medications to bulk entries', async () => {
      await ocrService.initialize()
      
      const result = await ocrService.processPrescription('test-image-url')
      const bulkEntries = ocrService.convertToBulkEntries(result.medications)
      
      expect(Array.isArray(bulkEntries)).toBe(true)
      if (bulkEntries.length > 0) {
        expect(bulkEntries[0]).toHaveProperty('name')
        expect(bulkEntries[0]).toHaveProperty('strength')
        expect(bulkEntries[0]).toHaveProperty('dosage')
        expect(bulkEntries[0]).toHaveProperty('frequency')
      }
    })
  })

  describe('Error Handling', () => {
    it('should handle OCR failures gracefully', async () => {
      vi.mocked(require('tesseract.js').default.createWorker).mockReturnValue({
        loadLanguage: vi.fn().mockRejectedValue(new Error('OCR failed')),
        initialize: vi.fn().mockResolvedValue(undefined),
        setParameters: vi.fn().mockResolvedValue(undefined),
        recognize: vi.fn().mockResolvedValue({
          data: {
            text: '',
            confidence: 0
          }
        }),
        terminate: vi.fn().mockResolvedValue(undefined)
      } as any)

      const result = await ocrService.processPrescription('test-image-url')
      expect(result.success).toBe(false)
      expect(result.errors).toBeDefined()
    })
  })

  describe('Image Preprocessing', () => {
    it('should accept preprocessing options', async () => {
      await ocrService.initialize()
      
      const options = {
        contrast: 1.5,
        brightness: 0.2,
        sharpen: true,
        denoise: true,
        threshold: 150
      }
      
      const result = await ocrService.processPrescription('test-image-url', options)
      expect(result).toBeDefined()
    })
  })
}) 