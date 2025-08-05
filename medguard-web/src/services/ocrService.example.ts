/**
 * Enhanced OCR Service Usage Examples
 * 
 * This file demonstrates how to use the enhanced OCR service with all its features
 * including Google Cloud Vision, Azure Computer Vision, batch processing, and validation.
 */

import { OCRService, OCRResult, PreprocessingOptions } from './ocrService'
import { ocrConfig, getBatchConfig, validateOCRConfig } from '../config/ocrConfig'

/**
 * Example 1: Basic OCR Processing
 */
export async function basicOCRExample(imageFile: File): Promise<OCRResult> {
  // Get the OCR service instance
  const ocrService = OCRService.getInstance()
  
  // Initialize with configuration
  await ocrService.initialize(ocrConfig)
  
  // Process a single prescription
  const result = await ocrService.processPrescription(imageFile)
  
  console.log('OCR Result:', result)
  return result
}

/**
 * Example 2: OCR with Custom Preprocessing
 */
export async function ocrWithPreprocessingExample(imageFile: File): Promise<OCRResult> {
  const ocrService = OCRService.getInstance()
  await ocrService.initialize(ocrConfig)
  
  // Custom preprocessing options
  const preprocessingOptions: PreprocessingOptions = {
    contrast: 1.2,        // Enhance contrast
    brightness: 0.1,      // Slightly increase brightness
    sharpen: true,        // Apply sharpening
    denoise: true,        // Apply noise reduction
    deskew: true,         // Auto-deskew
    threshold: 140        // Custom threshold
  }
  
  const result = await ocrService.processPrescription(imageFile, preprocessingOptions)
  
  // Validate the result
  const validation = ocrService.validateResult(result)
  console.log('Validation:', validation)
  
  return result
}

/**
 * Example 3: Batch Processing Multiple Prescriptions
 */
export async function batchProcessingExample(imageFiles: File[]): Promise<OCRResult[]> {
  const ocrService = OCRService.getInstance()
  await ocrService.initialize(ocrConfig)
  
  // Configure batch processing
  const batchConfig = getBatchConfig()
  ocrService.configureBatchProcessing({
    maxConcurrent: 4,
    timeout: 45000,
    qualityThreshold: 0.65
  })
  
  // Process multiple prescriptions
  const results = await ocrService.processBatchPrescriptions(imageFiles)
  
  // Analyze results
  const successful = results.filter(r => r.success)
  const failed = results.filter(r => !r.success)
  const requiresReview = results.filter(r => r.requiresManualReview)
  
  console.log(`Batch Processing Complete:`)
  console.log(`- Successful: ${successful.length}`)
  console.log(`- Failed: ${failed.length}`)
  console.log(`- Require Review: ${requiresReview.length}`)
  
  return results
}

/**
 * Example 4: Advanced Validation and Quality Assessment
 */
export async function advancedValidationExample(imageFile: File): Promise<void> {
  const ocrService = OCRService.getInstance()
  await ocrService.initialize(ocrConfig)
  
  const result = await ocrService.processPrescription(imageFile)
  
  // Comprehensive validation
  const validation = ocrService.validateResult(result)
  
  console.log('=== OCR Result Analysis ===')
  console.log(`Success: ${result.success}`)
  console.log(`Confidence: ${(result.confidence * 100).toFixed(1)}%`)
  console.log(`Processing Time: ${result.processingTime}ms`)
  
  console.log('\n=== Image Quality Assessment ===')
  console.log(`Overall Score: ${(result.imageQuality.overallScore * 100).toFixed(1)}%`)
  console.log(`Resolution: ${(result.imageQuality.resolution * 100).toFixed(1)}%`)
  console.log(`Contrast: ${(result.imageQuality.contrast * 100).toFixed(1)}%`)
  console.log(`Brightness: ${(result.imageQuality.brightness * 100).toFixed(1)}%`)
  console.log(`Blur: ${(result.imageQuality.blur * 100).toFixed(1)}%`)
  console.log(`Noise: ${(result.imageQuality.noise * 100).toFixed(1)}%`)
  console.log(`Skew: ${(result.imageQuality.skew * 100).toFixed(1)}%`)
  
  if (result.imageQuality.recommendations.length > 0) {
    console.log('\nQuality Recommendations:')
    result.imageQuality.recommendations.forEach(rec => console.log(`- ${rec}`))
  }
  
  console.log('\n=== Prescription Format ===')
  console.log(`Type: ${result.prescriptionFormat.type}`)
  console.log(`Confidence: ${(result.prescriptionFormat.confidence * 100).toFixed(1)}%`)
  console.log(`Language: ${result.prescriptionFormat.language}`)
  console.log(`Features: ${result.prescriptionFormat.features.join(', ')}`)
  
  console.log('\n=== Extracted Data ===')
  console.log(`Medications Found: ${result.medications.length}`)
  console.log(`Prescription Number: ${result.prescriptionNumber || 'Not found'}`)
  console.log(`Doctor Name: ${result.doctorName || 'Not found'}`)
  console.log(`ICD-10 Codes: ${result.icd10Codes.join(', ') || 'None found'}`)
  
  console.log('\n=== Validation Results ===')
  console.log(`Is Valid: ${validation.isValid}`)
  console.log(`Requires Manual Entry: ${validation.requiresManualEntry}`)
  
  if (validation.suggestions.length > 0) {
    console.log('\nSuggestions:')
    validation.suggestions.forEach(suggestion => console.log(`- ${suggestion}`))
  }
  
  if (validation.qualityIssues.length > 0) {
    console.log('\nQuality Issues:')
    validation.qualityIssues.forEach(issue => console.log(`- ${issue}`))
  }
  
  if (validation.formatIssues.length > 0) {
    console.log('\nFormat Issues:')
    validation.formatIssues.forEach(issue => console.log(`- ${issue}`))
  }
  
  // Get detailed medication validation report
  const medicationReport = await ocrService.getMedicationValidationReport(result.medications)
  
  console.log('\n=== Medication Validation Report ===')
  console.log(`Validated: ${medicationReport.validated.length}`)
  console.log(`Unvalidated: ${medicationReport.unvalidated.length}`)
  
  if (medicationReport.warnings.length > 0) {
    console.log('\nWarnings:')
    medicationReport.warnings.forEach(warning => console.log(`- ${warning}`))
  }
  
  if (medicationReport.interactions.length > 0) {
    console.log('\nDrug Interactions:')
    medicationReport.interactions.forEach(interaction => console.log(`- ${interaction}`))
  }
}

/**
 * Example 5: Service Statistics and Monitoring
 */
export async function serviceStatisticsExample(): Promise<void> {
  const ocrService = OCRService.getInstance()
  
  // Get comprehensive service statistics
  const stats = ocrService.getServiceStats()
  
  console.log('=== OCR Service Statistics ===')
  console.log(`Cache Size: ${stats.cacheStats.size} entries`)
  console.log(`Batch Queue Size: ${stats.batchStats.queueSize}`)
  console.log(`Validated Medications: ${stats.validationStats.validated}`)
  console.log(`Unvalidated Medications: ${stats.validationStats.unvalidated}`)
  console.log(`Average Quality Score: ${(stats.qualityStats.averageScore * 100).toFixed(1)}%`)
  
  if (stats.qualityStats.recommendations.length > 0) {
    console.log('\nCommon Quality Recommendations:')
    stats.qualityStats.recommendations.forEach(rec => console.log(`- ${rec}`))
  }
  
  // Get batch configuration
  const batchStats = ocrService.getBatchStats()
  console.log('\n=== Batch Configuration ===')
  console.log(`Max Concurrent: ${batchStats.config.maxConcurrent}`)
  console.log(`Timeout: ${batchStats.config.timeout}ms`)
  console.log(`Retry Attempts: ${batchStats.config.retryAttempts}`)
  console.log(`Quality Threshold: ${(batchStats.config.qualityThreshold * 100).toFixed(1)}%`)
}

/**
 * Example 6: Configuration Validation
 */
export function configurationValidationExample(): void {
  console.log('=== OCR Configuration Validation ===')
  
  const configSummary = validateOCRConfig()
  
  console.log(`Configuration Valid: ${configSummary.isValid}`)
  
  if (configSummary.errors.length > 0) {
    console.log('\nErrors:')
    configSummary.errors.forEach(error => console.log(`- ${error}`))
  }
  
  if (configSummary.warnings.length > 0) {
    console.log('\nWarnings:')
    configSummary.warnings.forEach(warning => console.log(`- ${warning}`))
  }
  
  // Check available providers
  const { getAvailableOCRProviders } = require('../config/ocrConfig')
  const providers = getAvailableOCRProviders()
  
  console.log(`\nAvailable OCR Providers: ${providers.join(', ') || 'None'}`)
}

/**
 * Example 7: Error Handling and Recovery
 */
export async function errorHandlingExample(imageFile: File): Promise<void> {
  const ocrService = OCRService.getInstance()
  
  try {
    await ocrService.initialize(ocrConfig)
    
    const result = await ocrService.processPrescription(imageFile)
    
    if (!result.success) {
      console.error('OCR Processing Failed:')
      result.errors?.forEach(error => console.error(`- ${error}`))
      return
    }
    
    // Check if manual review is required
    if (result.requiresManualReview) {
      console.warn('Manual review required due to low confidence or quality issues')
      
      const validation = ocrService.validateResult(result)
      
      if (validation.requiresManualEntry) {
        console.warn('Manual entry recommended for better accuracy')
      }
    }
    
    console.log('OCR Processing completed successfully')
    
  } catch (error) {
    console.error('OCR Service Error:', error)
    
    // Try to recover by clearing caches
    ocrService.clearAllCaches()
    console.log('Caches cleared, please try again')
  }
}

/**
 * Example 8: Performance Optimization
 */
export async function performanceOptimizationExample(): Promise<void> {
  const ocrService = OCRService.getInstance()
  
  // Configure for performance
  ocrService.configureBatchProcessing({
    maxConcurrent: 6,
    timeout: 30000,
    retryAttempts: 1,
    qualityThreshold: 0.5
  })
  
  // Monitor performance
  const stats = ocrService.getServiceStats()
  console.log('Performance Configuration Applied')
  console.log(`Cache Hit Rate: ${stats.cacheStats.size > 0 ? 'Active' : 'Empty'}`)
  console.log(`Batch Processing: ${stats.batchStats.config.maxConcurrent} concurrent`)
  
  // Clear caches periodically for memory management
  if (stats.cacheStats.size > 100) {
    ocrService.clearAllCaches()
    console.log('Caches cleared for memory optimization')
  }
}

/**
 * Example 9: Integration with Vue Component
 */
export function vueComponentIntegrationExample() {
  return {
    data() {
      return {
        ocrService: OCRService.getInstance(),
        isProcessing: false,
        results: [] as OCRResult[],
        errors: [] as string[]
      }
    },
    
    async mounted() {
      // Initialize OCR service
      await this.ocrService.initialize(ocrConfig)
      
      // Validate configuration
      const configValidation = validateOCRConfig()
      if (!configValidation.isValid) {
        this.errors.push(...configValidation.errors)
      }
    },
    
    methods: {
      async processPrescription(file: File) {
        this.isProcessing = true
        this.errors = []
        
        try {
          const result = await this.ocrService.processPrescription(file)
          this.results.push(result)
          
          // Check if manual review is needed
          if (result.requiresManualReview) {
            this.$emit('manual-review-required', result)
          }
          
        } catch (error) {
          this.errors.push(error instanceof Error ? error.message : 'Unknown error')
        } finally {
          this.isProcessing = false
        }
      },
      
      async processBatch(files: File[]) {
        this.isProcessing = true
        this.errors = []
        
        try {
          const results = await this.ocrService.processBatchPrescriptions(files)
          this.results.push(...results)
          
          // Emit batch completion event
          this.$emit('batch-complete', results)
          
        } catch (error) {
          this.errors.push(error instanceof Error ? error.message : 'Unknown error')
        } finally {
          this.isProcessing = false
        }
      },
      
      getServiceStats() {
        return this.ocrService.getServiceStats()
      }
    }
  }
} 