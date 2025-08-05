/**
 * Medication Enrichment Service Tests
 * 
 * Comprehensive test suite for the medication enrichment service
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import medicationEnrichmentService from '../medicationEnrichmentService'
import type {
  PerplexityEnrichmentRequest,
  PerplexityEnrichmentResponse,
  MedicationEnrichment,
  DrugDatabaseEntry,
  MedicationInteraction,
  DosageGuideline,
  CostAnalysis,
  AvailabilityInfo
} from '@/types/medication'

// Mock the apiClient
vi.mock('../apiClient', () => ({
  apiClient: {
    post: vi.fn()
  }
}))

// Import the mocked apiClient
import { apiClient } from '../apiClient'

describe('MedicationEnrichmentService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Clear cache before each test
    medicationEnrichmentService.clearCache()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('enrichMedication', () => {
    const mockRequest: PerplexityEnrichmentRequest = {
      medicationName: 'Paracetamol',
      genericName: 'Acetaminophen',
      strength: '500mg',
      includeInteractions: true,
      includeSideEffects: true,
      includeCost: true,
      includeAvailability: true
    }

    const mockDrugInfoResponse = {
      id: 'test-id',
      name: 'Paracetamol',
      genericName: 'Acetaminophen',
      brandNames: ['Panado', 'Calpol'],
      activeIngredients: ['Acetaminophen'],
      strength: '500mg',
      dosageForm: 'Tablet',
      manufacturer: 'Aspen Pharmacare',
      description: 'Pain reliever and fever reducer',
      sideEffects: ['Nausea', 'Stomach upset'],
      contraindications: ['Liver disease'],
      interactions: ['Warfarin'],
      pregnancyCategory: 'B',
      breastfeedingCategory: 'Safe',
      pediatricUse: 'Safe for children over 2 years',
      geriatricUse: 'No special precautions',
      renalDoseAdjustment: 'None required',
      hepaticDoseAdjustment: 'Avoid in severe liver disease',
      storageInstructions: 'Store at room temperature',
      disposalInstructions: 'Dispose of unused medication properly',
      cost: 25.50,
      availability: 'available' as const
    }

    const mockInteractionsResponse = [
      {
        severity: 'moderate' as const,
        description: 'May increase bleeding risk',
        medications: ['Warfarin'],
        recommendations: 'Monitor INR closely',
        evidence: 'Clinical studies',
        source: 'perplexity'
      }
    ]

    const mockSideEffectsResponse = [
      'Nausea',
      'Stomach upset',
      'Liver damage (rare)',
      'Allergic reactions'
    ]

    const mockContraindicationsResponse = [
      'Severe liver disease',
      'Known hypersensitivity',
      'Alcohol dependence'
    ]

    const mockDosageGuidelinesResponse = [
      {
        ageGroup: 'Adults',
        condition: 'Pain relief',
        dosage: '500-1000mg',
        frequency: 'Every 4-6 hours',
        duration: 'As needed',
        notes: 'Maximum 4g per day'
      }
    ]

    const mockCostAnalysisResponse = {
      averageCost: 25.50,
      costRange: { min: 20.00, max: 35.00 },
      genericAvailable: true,
      genericCost: 15.00,
      insuranceCoverage: 80,
      outOfPocketCost: 5.10,
      costPerDose: 0.25,
      monthlyCost: 45.00
    }

    const mockAvailabilityResponse = {
      isAvailable: true,
      stockStatus: 'in_stock' as const,
      pharmacies: [
        {
          name: 'Clicks Pharmacy',
          address: '123 Main St, Johannesburg',
          phone: '+27 11 123 4567',
          distance: 2.5,
          stock: 50,
          price: 25.50
        }
      ],
      onlineAvailability: true,
      prescriptionRequired: false
    }

    it('should enrich medication data successfully', async () => {
      // Mock successful API responses
      const mockApiResponse = {
        data: {
          response: JSON.stringify(mockDrugInfoResponse)
        }
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse)

      const result = await medicationEnrichmentService.enrichMedication(mockRequest)

      expect(result.success).toBe(true)
      expect(result.source).toBe('perplexity')
      expect(result.timestamp).toBeDefined()
      expect(result.data).toBeDefined()
      expect(result.data?.drugInfo).toBeDefined()
    })

    it('should return cached data for repeated requests', async () => {
      // Mock API response for first call
      const mockApiResponse = {
        data: {
          response: JSON.stringify(mockDrugInfoResponse)
        }
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse)

      // First call
      const result1 = await medicationEnrichmentService.enrichMedication(mockRequest)
      expect(result1.success).toBe(true)
      expect(apiClient.post).toHaveBeenCalledTimes(7) // 7 different enrichment calls

      // Second call should use cache
      const result2 = await medicationEnrichmentService.enrichMedication(mockRequest)
      expect(result2.success).toBe(true)
      expect(result2.data).toEqual(result1.data)
      // API should not be called again due to caching
      expect(apiClient.post).toHaveBeenCalledTimes(7)
    })

    it('should handle API errors gracefully', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('API Error'))

      const result = await medicationEnrichmentService.enrichMedication(mockRequest)

      expect(result.success).toBe(false)
      expect(result.error).toBe('API Error')
      expect(result.source).toBe('perplexity')
    })

    it('should handle malformed API responses', async () => {
      const mockApiResponse = {
        data: {
          response: 'invalid json'
        }
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse)

      const result = await medicationEnrichmentService.enrichMedication(mockRequest)

      expect(result.success).toBe(true)
      expect(result.data).toBeDefined()
      // Individual enrichment fields should be undefined due to parsing errors
      expect(result.data?.drugInfo).toBeUndefined()
    })

    it('should respect rate limiting', async () => {
      const mockApiResponse = {
        data: {
          response: JSON.stringify(mockDrugInfoResponse)
        }
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse)

      // Make multiple requests quickly
      const promises = Array.from({ length: 5 }, () =>
        medicationEnrichmentService.enrichMedication(mockRequest)
      )

      const results = await Promise.all(promises)

      // All should succeed, but rate limiting should be applied
      results.forEach(result => {
        expect(result.success).toBe(true)
      })
    })
  })

  describe('Cache Management', () => {
    it('should clear cache correctly', () => {
      const stats = medicationEnrichmentService.getCacheStats()
      expect(stats.size).toBe(0)

      // Add some test data to cache (using private method through reflection)
      const cache = (medicationEnrichmentService as any).cache
      cache.set('test-key', { data: 'test-data', timestamp: Date.now(), ttl: 3600000 })

      expect(cache.size).toBe(1)

      medicationEnrichmentService.clearCache()
      expect(cache.size).toBe(0)
    })

    it('should provide cache statistics', () => {
      const stats = medicationEnrichmentService.getCacheStats()
      expect(stats).toHaveProperty('size')
      expect(stats).toHaveProperty('maxSize')
      expect(typeof stats.size).toBe('number')
      expect(typeof stats.maxSize).toBe('number')
    })

    it('should handle cache expiration', async () => {
      const mockRequest: PerplexityEnrichmentRequest = {
        medicationName: 'Test Medication'
      }

      const mockApiResponse = {
        data: {
          response: JSON.stringify({ name: 'Test Medication' })
        }
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse)

      // First call
      await medicationEnrichmentService.enrichMedication(mockRequest)

      // Manually expire cache entry
      const cache = (medicationEnrichmentService as any).cache
      const cacheKey = (medicationEnrichmentService as any).generateCacheKey(mockRequest)
      const entry = cache.get(cacheKey)
      if (entry) {
        entry.timestamp = Date.now() - (24 * 60 * 60 * 1000 + 1000) // Expired
        cache.set(cacheKey, entry)
      }

      // Second call should make new API request
      await medicationEnrichmentService.enrichMedication(mockRequest)

      // API should be called twice (once for each request)
      expect(apiClient.post).toHaveBeenCalledTimes(14) // 7 calls per request
    })
  })

  describe('Rate Limiting', () => {
    it('should provide rate limit statistics', () => {
      const stats = medicationEnrichmentService.getRateLimitStats()
      expect(stats).toHaveProperty('maxRequests')
      expect(stats).toHaveProperty('windowMs')
      expect(stats).toHaveProperty('currentRequests')
      expect(stats).toHaveProperty('resetTime')
    })

    it('should handle rate limit exceeded', async () => {
      const mockRequest: PerplexityEnrichmentRequest = {
        medicationName: 'Test Medication'
      }

      const mockApiResponse = {
        data: {
          response: JSON.stringify({ name: 'Test Medication' })
        }
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse)

      // Make many requests to trigger rate limiting
      const promises = Array.from({ length: 60 }, () =>
        medicationEnrichmentService.enrichMedication(mockRequest)
      )

      const results = await Promise.all(promises)

      // All should eventually succeed
      results.forEach(result => {
        expect(result.success).toBe(true)
      })
    })
  })

  describe('Data Parsing', () => {
    it('should parse drug information correctly', () => {
      const service = medicationEnrichmentService as any
      const response = JSON.stringify({
        id: 'test-id',
        name: 'Test Drug',
        genericName: 'Test Generic',
        brandNames: ['Brand1', 'Brand2'],
        activeIngredients: ['Ingredient1'],
        strength: '100mg',
        dosageForm: 'Tablet',
        manufacturer: 'Test Manufacturer',
        description: 'Test description',
        sideEffects: ['Side effect 1'],
        contraindications: ['Contraindication 1'],
        interactions: ['Interaction 1'],
        pregnancyCategory: 'B',
        breastfeedingCategory: 'Safe',
        pediatricUse: 'Safe for children',
        geriatricUse: 'No special precautions',
        renalDoseAdjustment: 'None required',
        hepaticDoseAdjustment: 'None required',
        storageInstructions: 'Store at room temperature',
        disposalInstructions: 'Dispose properly',
        cost: 50.00,
        availability: 'available'
      })

      const result = service.parseDrugInfoResponse(response)

      expect(result).toBeDefined()
      expect(result.name).toBe('Test Drug')
      expect(result.genericName).toBe('Test Generic')
      expect(result.brandNames).toEqual(['Brand1', 'Brand2'])
      expect(result.cost).toBe(50.00)
    })

    it('should parse interactions correctly', () => {
      const service = medicationEnrichmentService as any
      const response = JSON.stringify([
        {
          severity: 'high',
          description: 'Test interaction',
          medications: ['Drug1', 'Drug2'],
          recommendations: 'Avoid combination',
          evidence: 'Clinical evidence',
          source: 'perplexity'
        }
      ])

      const result = service.parseInteractionsResponse(response)

      expect(result).toBeDefined()
      expect(Array.isArray(result)).toBe(true)
      expect(result[0].severity).toBe('high')
      expect(result[0].description).toBe('Test interaction')
    })

    it('should parse side effects correctly', () => {
      const service = medicationEnrichmentService as any
      const response = JSON.stringify(['Side effect 1', 'Side effect 2'])

      const result = service.parseSideEffectsResponse(response)

      expect(result).toBeDefined()
      expect(Array.isArray(result)).toBe(true)
      expect(result).toEqual(['Side effect 1', 'Side effect 2'])
    })

    it('should parse cost analysis correctly', () => {
      const service = medicationEnrichmentService as any
      const response = JSON.stringify({
        averageCost: 100.00,
        costRange: { min: 80.00, max: 120.00 },
        genericAvailable: true,
        genericCost: 60.00,
        insuranceCoverage: 70,
        outOfPocketCost: 30.00,
        costPerDose: 1.00,
        monthlyCost: 90.00
      })

      const result = service.parseCostAnalysisResponse(response)

      expect(result).toBeDefined()
      expect(result.averageCost).toBe(100.00)
      expect(result.costRange.min).toBe(80.00)
      expect(result.costRange.max).toBe(120.00)
      expect(result.genericAvailable).toBe(true)
    })

    it('should parse availability information correctly', () => {
      const service = medicationEnrichmentService as any
      const response = JSON.stringify({
        isAvailable: true,
        stockStatus: 'in_stock',
        pharmacies: [
          {
            name: 'Test Pharmacy',
            address: 'Test Address',
            phone: 'Test Phone',
            distance: 5.0,
            stock: 100,
            price: 50.00
          }
        ],
        onlineAvailability: true,
        prescriptionRequired: false
      })

      const result = service.parseAvailabilityResponse(response)

      expect(result).toBeDefined()
      expect(result.isAvailable).toBe(true)
      expect(result.stockStatus).toBe('in_stock')
      expect(result.pharmacies).toHaveLength(1)
      expect(result.pharmacies[0].name).toBe('Test Pharmacy')
    })
  })

  describe('Prompt Building', () => {
    it('should build drug info prompt correctly', () => {
      const service = medicationEnrichmentService as any
      const request: PerplexityEnrichmentRequest = {
        medicationName: 'Aspirin',
        genericName: 'Acetylsalicylic acid',
        strength: '100mg'
      }

      const prompt = service.buildDrugInfoPrompt(request)

      expect(prompt).toContain('Aspirin')
      expect(prompt).toContain('Acetylsalicylic acid')
      expect(prompt).toContain('100mg')
      expect(prompt).toContain('South Africa')
      expect(prompt).toContain('JSON format')
    })

    it('should build interactions prompt correctly', () => {
      const service = medicationEnrichmentService as any
      const request: PerplexityEnrichmentRequest = {
        medicationName: 'Warfarin'
      }

      const prompt = service.buildInteractionsPrompt(request)

      expect(prompt).toContain('Warfarin')
      expect(prompt).toContain('drug interaction')
      expect(prompt).toContain('severity levels')
      expect(prompt).toContain('South Africa')
    })

    it('should build cost analysis prompt correctly', () => {
      const service = medicationEnrichmentService as any
      const request: PerplexityEnrichmentRequest = {
        medicationName: 'Insulin'
      }

      const prompt = service.buildCostAnalysisPrompt(request)

      expect(prompt).toContain('Insulin')
      expect(prompt).toContain('cost analysis')
      expect(prompt).toContain('ZAR')
      expect(prompt).toContain('generic alternatives')
    })
  })

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'))

      const request: PerplexityEnrichmentRequest = {
        medicationName: 'Test Medication'
      }

      const result = await medicationEnrichmentService.enrichMedication(request)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Network error')
    })

    it('should handle timeout errors', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Request timeout'))

      const request: PerplexityEnrichmentRequest = {
        medicationName: 'Test Medication'
      }

      const result = await medicationEnrichmentService.enrichMedication(request)

      expect(result.success).toBe(false)
      expect(result.error).toBe('Request timeout')
    })

    it('should handle invalid JSON responses', async () => {
      const mockApiResponse = {
        data: {
          response: 'invalid json response'
        }
      }

      vi.mocked(apiClient.post).mockResolvedValue(mockApiResponse)

      const request: PerplexityEnrichmentRequest = {
        medicationName: 'Test Medication'
      }

      const result = await medicationEnrichmentService.enrichMedication(request)

      expect(result.success).toBe(true)
      // Individual enrichment fields should be undefined due to parsing errors
      expect(result.data?.drugInfo).toBeUndefined()
    })
  })

  describe('Resource Management', () => {
    it('should cleanup resources on destroy', () => {
      const service = new (medicationEnrichmentService.constructor as any)()
      
      // Add some test data
      const cache = (service as any).cache
      cache.set('test-key', { data: 'test-data', timestamp: Date.now(), ttl: 3600000 })
      
      expect(cache.size).toBe(1)
      
      service.destroy()
      
      expect(cache.size).toBe(0)
    })
  })
}) 