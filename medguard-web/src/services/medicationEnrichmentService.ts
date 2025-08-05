/**
 * Medication Enrichment Service
 * 
 * Integrates with Perplexity API to enrich medication data with comprehensive information:
 * - Drug information (side effects, contraindications, interactions)
 * - South African-specific medication information and pricing
 * - Generic alternatives available in South Africa
 * - Dosage guidelines and administration instructions
 * - Drug interaction warnings and severity levels
 * - Storage requirements and expiration guidelines
 * - Manufacturer information and contact details
 * - Pregnancy/breastfeeding safety information
 * - Caching and rate limiting for API efficiency
 */

import { apiClient } from './apiClient'
import type {
  MedicationEnrichment,
  PerplexityEnrichmentRequest,
  PerplexityEnrichmentResponse,
  DrugDatabaseEntry,
  MedicationInteraction,
  DosageGuideline,
  CostAnalysis,
  AvailabilityInfo,
  PharmacyInfo
} from '@/types/medication'

// Cache configuration
interface CacheEntry<T> {
  data: T
  timestamp: number
  ttl: number
}

interface RateLimitConfig {
  maxRequests: number
  windowMs: number
  currentRequests: number
  resetTime: number
}

// Service configuration
const ENRICHMENT_CONFIG = {
  // Cache settings
  cache: {
    ttl: 24 * 60 * 60 * 1000, // 24 hours
    maxSize: 100, // Maximum cache entries
    cleanupInterval: 60 * 60 * 1000 // 1 hour
  },
  
  // Rate limiting
  rateLimit: {
    maxRequests: 50, // Max requests per window
    windowMs: 60 * 1000, // 1 minute window
    retryDelay: 2000 // 2 seconds
  },
  
  // Perplexity API settings
  perplexity: {
    baseURL: 'https://api.perplexity.ai',
    model: 'llama-3.1-sonar-large-128k-online',
    maxTokens: 4000,
    temperature: 0.1,
    timeout: 30000
  },
  
  // South African specific settings
  southAfrica: {
    currency: 'ZAR',
    language: 'en-ZA',
    timezone: 'Africa/Johannesburg',
    regulatoryBody: 'SAHPRA'
  }
}

class MedicationEnrichmentService {
  private cache = new Map<string, CacheEntry<any>>()
  private rateLimit: RateLimitConfig
  private cleanupTimer?: NodeJS.Timeout

  constructor() {
    this.rateLimit = {
      maxRequests: ENRICHMENT_CONFIG.rateLimit.maxRequests,
      windowMs: ENRICHMENT_CONFIG.rateLimit.windowMs,
      currentRequests: 0,
      resetTime: Date.now() + ENRICHMENT_CONFIG.rateLimit.windowMs
    }

    // Start cache cleanup
    this.startCacheCleanup()
  }

  /**
   * Enrich medication data using Perplexity API
   */
  async enrichMedication(
    request: PerplexityEnrichmentRequest
  ): Promise<PerplexityEnrichmentResponse> {
    try {
      // Check cache first
      const cacheKey = this.generateCacheKey(request)
      const cached = this.getFromCache<MedicationEnrichment>(cacheKey)
      if (cached) {
        return {
          success: true,
          data: cached,
          source: 'perplexity',
          timestamp: new Date().toISOString()
        }
      }

      // Check rate limit
      await this.checkRateLimit()

      // Enrich medication data
      const enrichment = await this.performEnrichment(request)

      // Cache the result
      this.setCache(cacheKey, enrichment)

      return {
        success: true,
        data: enrichment,
        source: 'perplexity',
        timestamp: new Date().toISOString()
      }
    } catch (error) {
      console.error('Medication enrichment failed:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        source: 'perplexity',
        timestamp: new Date().toISOString()
      }
    }
  }

  /**
   * Perform comprehensive medication enrichment
   */
  private async performEnrichment(
    request: PerplexityEnrichmentRequest
  ): Promise<MedicationEnrichment> {
    const enrichment: MedicationEnrichment = {
      enrichedAt: new Date().toISOString(),
      source: 'perplexity'
    }

    // Parallel enrichment for better performance
    const [
      drugInfo,
      interactions,
      sideEffects,
      contraindications,
      dosageGuidelines,
      costAnalysis,
      availability
    ] = await Promise.allSettled([
      this.getDrugInformation(request),
      this.getDrugInteractions(request),
      this.getSideEffects(request),
      this.getContraindications(request),
      this.getDosageGuidelines(request),
      this.getCostAnalysis(request),
      this.getAvailabilityInfo(request)
    ])

    // Assign results
    if (drugInfo.status === 'fulfilled') enrichment.drugInfo = drugInfo.value
    if (interactions.status === 'fulfilled') enrichment.interactions = interactions.value
    if (sideEffects.status === 'fulfilled') enrichment.sideEffects = sideEffects.value
    if (contraindications.status === 'fulfilled') enrichment.contraindications = contraindications.value
    if (dosageGuidelines.status === 'fulfilled') enrichment.dosageGuidelines = dosageGuidelines.value
    if (costAnalysis.status === 'fulfilled') enrichment.costAnalysis = costAnalysis.value
    if (availability.status === 'fulfilled') enrichment.availability = availability.value

    return enrichment
  }

  /**
   * Get comprehensive drug information
   */
  private async getDrugInformation(
    request: PerplexityEnrichmentRequest
  ): Promise<DrugDatabaseEntry | undefined> {
    const prompt = this.buildDrugInfoPrompt(request)
    const response = await this.queryPerplexity(prompt)
    
    if (!response) return undefined

    try {
      return this.parseDrugInfoResponse(response)
    } catch (error) {
      console.error('Failed to parse drug info response:', error)
      return undefined
    }
  }

  /**
   * Get drug interactions with severity levels
   */
  private async getDrugInteractions(
    request: PerplexityEnrichmentRequest
  ): Promise<MedicationInteraction[] | undefined> {
    const prompt = this.buildInteractionsPrompt(request)
    const response = await this.queryPerplexity(prompt)
    
    if (!response) return undefined

    try {
      return this.parseInteractionsResponse(response)
    } catch (error) {
      console.error('Failed to parse interactions response:', error)
      return undefined
    }
  }

  /**
   * Get side effects information
   */
  private async getSideEffects(
    request: PerplexityEnrichmentRequest
  ): Promise<string[] | undefined> {
    const prompt = this.buildSideEffectsPrompt(request)
    const response = await this.queryPerplexity(prompt)
    
    if (!response) return undefined

    try {
      return this.parseSideEffectsResponse(response)
    } catch (error) {
      console.error('Failed to parse side effects response:', error)
      return undefined
    }
  }

  /**
   * Get contraindications
   */
  private async getContraindications(
    request: PerplexityEnrichmentRequest
  ): Promise<string[] | undefined> {
    const prompt = this.buildContraindicationsPrompt(request)
    const response = await this.queryPerplexity(prompt)
    
    if (!response) return undefined

    try {
      return this.parseContraindicationsResponse(response)
    } catch (error) {
      console.error('Failed to parse contraindications response:', error)
      return undefined
    }
  }

  /**
   * Get dosage guidelines and administration instructions
   */
  private async getDosageGuidelines(
    request: PerplexityEnrichmentRequest
  ): Promise<DosageGuideline[] | undefined> {
    const prompt = this.buildDosageGuidelinesPrompt(request)
    const response = await this.queryPerplexity(prompt)
    
    if (!response) return undefined

    try {
      return this.parseDosageGuidelinesResponse(response)
    } catch (error) {
      console.error('Failed to parse dosage guidelines response:', error)
      return undefined
    }
  }

  /**
   * Get South African cost analysis
   */
  private async getCostAnalysis(
    request: PerplexityEnrichmentRequest
  ): Promise<CostAnalysis | undefined> {
    const prompt = this.buildCostAnalysisPrompt(request)
    const response = await this.queryPerplexity(prompt)
    
    if (!response) return undefined

    try {
      return this.parseCostAnalysisResponse(response)
    } catch (error) {
      console.error('Failed to parse cost analysis response:', error)
      return undefined
    }
  }

  /**
   * Get availability information in South Africa
   */
  private async getAvailabilityInfo(
    request: PerplexityEnrichmentRequest
  ): Promise<AvailabilityInfo | undefined> {
    const prompt = this.buildAvailabilityPrompt(request)
    const response = await this.queryPerplexity(prompt)
    
    if (!response) return undefined

    try {
      return this.parseAvailabilityResponse(response)
    } catch (error) {
      console.error('Failed to parse availability response:', error)
      return undefined
    }
  }

  /**
   * Query Perplexity API
   */
  private async queryPerplexity(prompt: string): Promise<string | null> {
    try {
      // Use backend proxy for Perplexity API calls
      const response = await apiClient.post('/api/medications/enrichment/perplexity/', {
        prompt,
        model: ENRICHMENT_CONFIG.perplexity.model,
        max_tokens: ENRICHMENT_CONFIG.perplexity.maxTokens,
        temperature: ENRICHMENT_CONFIG.perplexity.temperature
      })

      return response.data?.response || null
    } catch (error) {
      console.error('Perplexity API query failed:', error)
      return null
    }
  }

  /**
   * Build drug information prompt
   */
  private buildDrugInfoPrompt(request: PerplexityEnrichmentRequest): string {
    return `
    Provide comprehensive drug information for ${request.medicationName}${request.genericName ? ` (${request.genericName})` : ''}${request.strength ? ` ${request.strength}` : ''} in South Africa.

    Please provide the following information in JSON format:
    - Generic name and brand names available in South Africa
    - Active ingredients
    - Manufacturer information and contact details
    - Description and mechanism of action
    - Pregnancy and breastfeeding safety information
    - Pediatric and geriatric use considerations
    - Renal and hepatic dose adjustments
    - Storage instructions and requirements
    - Disposal instructions
    - Regulatory status in South Africa (SAHPRA approval)
    - Cost information in ZAR
    - Availability status

    Focus on South African market availability and regulatory compliance.
    `
  }

  /**
   * Build interactions prompt
   */
  private buildInteractionsPrompt(request: PerplexityEnrichmentRequest): string {
    return `
    Provide drug interaction information for ${request.medicationName} in South Africa.

    Please provide the following information in JSON format:
    - Common drug interactions with severity levels (low, moderate, high, contraindicated)
    - Food interactions
    - Alcohol interactions
    - Herbal supplement interactions
    - Specific recommendations for each interaction
    - Evidence level and sources
    - South African prescribing guidelines

    Focus on medications commonly prescribed in South Africa.
    `
  }

  /**
   * Build side effects prompt
   */
  private buildSideEffectsPrompt(request: PerplexityEnrichmentRequest): string {
    return `
    Provide side effects information for ${request.medicationName} in South Africa.

    Please provide the following information in JSON format:
    - Common side effects (frequency > 1%)
    - Serious side effects requiring immediate medical attention
    - Rare but severe side effects
    - Side effects specific to South African population
    - Management strategies for common side effects
    - When to contact healthcare provider

    Focus on side effects relevant to South African patients.
    `
  }

  /**
   * Build contraindications prompt
   */
  private buildContraindicationsPrompt(request: PerplexityEnrichmentRequest): string {
    return `
    Provide contraindications for ${request.medicationName} in South Africa.

    Please provide the following information in JSON format:
    - Absolute contraindications
    - Relative contraindications
    - Precautions and warnings
    - Specific contraindications for South African population
    - Age-related contraindications
    - Disease-specific contraindications

    Focus on South African prescribing guidelines and population considerations.
    `
  }

  /**
   * Build dosage guidelines prompt
   */
  private buildDosageGuidelinesPrompt(request: PerplexityEnrichmentRequest): string {
    return `
    Provide dosage guidelines for ${request.medicationName} in South Africa.

    Please provide the following information in JSON format:
    - Adult dosage guidelines
    - Pediatric dosage guidelines (by age/weight)
    - Geriatric dosage adjustments
    - Renal impairment adjustments
    - Hepatic impairment adjustments
    - Administration instructions
    - Timing considerations
    - Duration of therapy
    - Special instructions for South African patients

    Focus on South African prescribing practices and guidelines.
    `
  }

  /**
   * Build cost analysis prompt
   */
  private buildCostAnalysisPrompt(request: PerplexityEnrichmentRequest): string {
    return `
    Provide cost analysis for ${request.medicationName} in South Africa.

    Please provide the following information in JSON format:
    - Average cost in ZAR
    - Cost range (minimum to maximum)
    - Generic alternatives and their costs
    - Insurance coverage information
    - Out-of-pocket costs
    - Cost per dose
    - Monthly cost estimates
    - Cost comparison with similar medications
    - Availability of generic versions in South Africa

    Focus on current South African pricing and availability.
    `
  }

  /**
   * Build availability prompt
   */
  private buildAvailabilityPrompt(request: PerplexityEnrichmentRequest): string {
    return `
    Provide availability information for ${request.medicationName} in South Africa.

    Please provide the following information in JSON format:
    - Current availability status
    - Stock status in major pharmacies
    - Online availability
    - Prescription requirements
    - Major pharmacy chains carrying the medication
    - Alternative sources
    - Import requirements if not locally available
    - Regulatory restrictions

    Focus on South African market availability and access.
    `
  }

  /**
   * Parse drug information response
   */
  private parseDrugInfoResponse(response: string): DrugDatabaseEntry | undefined {
    try {
      const data = JSON.parse(response)
      return {
        id: data.id || crypto.randomUUID(),
        name: data.name || '',
        genericName: data.genericName || '',
        brandNames: data.brandNames || [],
        activeIngredients: data.activeIngredients || [],
        strength: data.strength || '',
        dosageForm: data.dosageForm || '',
        manufacturer: data.manufacturer || '',
        description: data.description || '',
        sideEffects: data.sideEffects || [],
        contraindications: data.contraindications || [],
        interactions: data.interactions || [],
        pregnancyCategory: data.pregnancyCategory || '',
        breastfeedingCategory: data.breastfeedingCategory || '',
        pediatricUse: data.pediatricUse || '',
        geriatricUse: data.geriatricUse || '',
        renalDoseAdjustment: data.renalDoseAdjustment || '',
        hepaticDoseAdjustment: data.hepaticDoseAdjustment || '',
        storageInstructions: data.storageInstructions || '',
        disposalInstructions: data.disposalInstructions || '',
        cost: data.cost || 0,
        availability: data.availability || 'available'
      }
    } catch (error) {
      console.error('Failed to parse drug info response:', error)
      return undefined
    }
  }

  /**
   * Parse interactions response
   */
  private parseInteractionsResponse(response: string): MedicationInteraction[] | undefined {
    try {
      const data = JSON.parse(response)
      return Array.isArray(data) ? data.map(interaction => ({
        severity: interaction.severity || 'moderate',
        description: interaction.description || '',
        medications: interaction.medications || [],
        recommendations: interaction.recommendations || '',
        evidence: interaction.evidence || '',
        source: interaction.source || 'perplexity'
      })) : undefined
    } catch (error) {
      console.error('Failed to parse interactions response:', error)
      return undefined
    }
  }

  /**
   * Parse side effects response
   */
  private parseSideEffectsResponse(response: string): string[] | undefined {
    try {
      const data = JSON.parse(response)
      return Array.isArray(data) ? data : undefined
    } catch (error) {
      console.error('Failed to parse side effects response:', error)
      return undefined
    }
  }

  /**
   * Parse contraindications response
   */
  private parseContraindicationsResponse(response: string): string[] | undefined {
    try {
      const data = JSON.parse(response)
      return Array.isArray(data) ? data : undefined
    } catch (error) {
      console.error('Failed to parse contraindications response:', error)
      return undefined
    }
  }

  /**
   * Parse dosage guidelines response
   */
  private parseDosageGuidelinesResponse(response: string): DosageGuideline[] | undefined {
    try {
      const data = JSON.parse(response)
      return Array.isArray(data) ? data.map(guideline => ({
        ageGroup: guideline.ageGroup || '',
        condition: guideline.condition || '',
        dosage: guideline.dosage || '',
        frequency: guideline.frequency || '',
        duration: guideline.duration || '',
        notes: guideline.notes || ''
      })) : undefined
    } catch (error) {
      console.error('Failed to parse dosage guidelines response:', error)
      return undefined
    }
  }

  /**
   * Parse cost analysis response
   */
  private parseCostAnalysisResponse(response: string): CostAnalysis | undefined {
    try {
      const data = JSON.parse(response)
      return {
        averageCost: data.averageCost || 0,
        costRange: {
          min: data.costRange?.min || 0,
          max: data.costRange?.max || 0
        },
        genericAvailable: data.genericAvailable || false,
        genericCost: data.genericCost,
        insuranceCoverage: data.insuranceCoverage,
        outOfPocketCost: data.outOfPocketCost,
        costPerDose: data.costPerDose,
        monthlyCost: data.monthlyCost
      }
    } catch (error) {
      console.error('Failed to parse cost analysis response:', error)
      return undefined
    }
  }

  /**
   * Parse availability response
   */
  private parseAvailabilityResponse(response: string): AvailabilityInfo | undefined {
    try {
      const data = JSON.parse(response)
      return {
        isAvailable: data.isAvailable || false,
        stockStatus: data.stockStatus || 'out_of_stock',
        pharmacies: Array.isArray(data.pharmacies) ? data.pharmacies.map(pharmacy => ({
          name: pharmacy.name || '',
          address: pharmacy.address || '',
          phone: pharmacy.phone || '',
          distance: pharmacy.distance || 0,
          stock: pharmacy.stock || 0,
          price: pharmacy.price || 0
        })) : [],
        onlineAvailability: data.onlineAvailability || false,
        prescriptionRequired: data.prescriptionRequired || true
      }
    } catch (error) {
      console.error('Failed to parse availability response:', error)
      return undefined
    }
  }

  /**
   * Generate cache key
   */
  private generateCacheKey(request: PerplexityEnrichmentRequest): string {
    return `enrichment:${request.medicationName}:${request.genericName || ''}:${request.strength || ''}`
  }

  /**
   * Get data from cache
   */
  private getFromCache<T>(key: string): T | null {
    const entry = this.cache.get(key)
    if (!entry) return null

    if (Date.now() - entry.timestamp > entry.ttl) {
      this.cache.delete(key)
      return null
    }

    return entry.data
  }

  /**
   * Set data in cache
   */
  private setCache<T>(key: string, data: T): void {
    // Implement LRU cache eviction
    if (this.cache.size >= ENRICHMENT_CONFIG.cache.maxSize) {
      const firstKey = this.cache.keys().next().value
      this.cache.delete(firstKey)
    }

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl: ENRICHMENT_CONFIG.cache.ttl
    })
  }

  /**
   * Check rate limit
   */
  private async checkRateLimit(): Promise<void> {
    const now = Date.now()

    // Reset rate limit if window has passed
    if (now > this.rateLimit.resetTime) {
      this.rateLimit.currentRequests = 0
      this.rateLimit.resetTime = now + this.rateLimit.windowMs
    }

    // Check if rate limit exceeded
    if (this.rateLimit.currentRequests >= this.rateLimit.maxRequests) {
      const waitTime = this.rateLimit.resetTime - now
      await new Promise(resolve => setTimeout(resolve, waitTime))
      this.rateLimit.currentRequests = 0
      this.rateLimit.resetTime = Date.now() + this.rateLimit.windowMs
    }

    this.rateLimit.currentRequests++
  }

  /**
   * Start cache cleanup timer
   */
  private startCacheCleanup(): void {
    this.cleanupTimer = setInterval(() => {
      const now = Date.now()
      for (const [key, entry] of this.cache.entries()) {
        if (now - entry.timestamp > entry.ttl) {
          this.cache.delete(key)
        }
      }
    }, ENRICHMENT_CONFIG.cache.cleanupInterval)
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.cache.clear()
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): { size: number; maxSize: number } {
    return {
      size: this.cache.size,
      maxSize: ENRICHMENT_CONFIG.cache.maxSize
    }
  }

  /**
   * Get rate limit statistics
   */
  getRateLimitStats(): RateLimitConfig {
    return { ...this.rateLimit }
  }

  /**
   * Cleanup resources
   */
  destroy(): void {
    if (this.cleanupTimer) {
      clearInterval(this.cleanupTimer)
    }
    this.cache.clear()
  }
}

// Export singleton instance
const medicationEnrichmentService = new MedicationEnrichmentService()

export default medicationEnrichmentService 