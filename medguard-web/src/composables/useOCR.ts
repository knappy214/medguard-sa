import { ref, computed } from 'vue'
import { ocrService, type OCRResult, type PreprocessingOptions, type ExtractedMedication } from '../services/ocrService'
import { type BulkMedicationEntry } from '../types/medication'

/**
 * OCR Processing State
 */
export interface OCRState {
  isProcessing: boolean
  progress: number
  result: OCRResult | null
  error: string | null
  validation: {
    isValid: boolean
    suggestions: string[]
    requiresManualEntry: boolean
  } | null
}

/**
 * OCR Composable for Vue Components
 */
export function useOCR() {
  // Reactive state
  const state = ref<OCRState>({
    isProcessing: false,
    progress: 0,
    result: null,
    error: null,
    validation: null
  })

  // Computed properties
  const isReady = computed(() => !state.value.isProcessing && !state.value.error)
  const hasResult = computed(() => state.value.result !== null)
  const confidenceLevel = computed(() => {
    if (!state.value.result) return 'none'
    const conf = state.value.result.confidence
    if (conf >= 0.8) return 'high'
    if (conf >= 0.6) return 'medium'
    if (conf >= 0.4) return 'low'
    return 'very-low'
  })

  const confidenceColor = computed(() => {
    switch (confidenceLevel.value) {
      case 'high': return 'success'
      case 'medium': return 'warning'
      case 'low': return 'error'
      case 'very-low': return 'error'
      default: return 'neutral'
    }
  })

  /**
   * Process prescription image
   */
  const processImage = async (
    imageFile: File | string,
    options: PreprocessingOptions = {}
  ): Promise<OCRResult | null> => {
    try {
      // Reset state
      state.value.isProcessing = true
      state.value.progress = 0
      state.value.error = null
      state.value.result = null
      state.value.validation = null

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        if (state.value.progress < 90) {
          state.value.progress += Math.random() * 10
        }
      }, 200)

      // Process the image
      const result = await ocrService.processPrescription(imageFile, options)
      
      clearInterval(progressInterval)
      state.value.progress = 100

      // Update state
      state.value.result = result
      state.value.validation = ocrService.validateResult(result)

      if (!result.success) {
        state.value.error = result.errors?.join(', ') || 'OCR processing failed'
      }

      return result

    } catch (error) {
      state.value.error = error instanceof Error ? error.message : 'Unknown error occurred'
      return null
    } finally {
      state.value.isProcessing = false
    }
  }

  /**
   * Process multiple images
   */
  const processMultipleImages = async (
    imageFiles: (File | string)[],
    options: PreprocessingOptions = {}
  ): Promise<OCRResult[]> => {
    const results: OCRResult[] = []
    
    for (let i = 0; i < imageFiles.length; i++) {
      const file = imageFiles[i]
      state.value.progress = (i / imageFiles.length) * 100
      
      const result = await processImage(file, options)
      if (result) {
        results.push(result)
      }
    }
    
    state.value.progress = 100
    return results
  }

  /**
   * Convert extracted medications to bulk entries
   */
  const convertToBulkEntries = (medications: ExtractedMedication[]): BulkMedicationEntry[] => {
    return ocrService.convertToBulkEntries(medications)
  }

  /**
   * Get all medications from all results
   */
  const getAllMedications = (results: OCRResult[]): ExtractedMedication[] => {
    return results.flatMap(result => result.medications)
  }

  /**
   * Filter medications by confidence level
   */
  const filterMedicationsByConfidence = (
    medications: ExtractedMedication[],
    minConfidence: number = 0.5
  ): ExtractedMedication[] => {
    return medications.filter(med => med.confidence >= minConfidence)
  }

  /**
   * Merge duplicate medications
   */
  const mergeDuplicateMedications = (medications: ExtractedMedication[]): ExtractedMedication[] => {
    const merged = new Map<string, ExtractedMedication>()
    
    medications.forEach(med => {
      const key = med.name.toLowerCase()
      const existing = merged.get(key)
      
      if (!existing || med.confidence > existing.confidence) {
        merged.set(key, med)
      }
    })
    
    return Array.from(merged.values())
  }

  /**
   * Clear current result and error
   */
  const clearResult = () => {
    state.value.result = null
    state.value.error = null
    state.value.validation = null
    state.value.progress = 0
  }

  /**
   * Clear cache
   */
  const clearCache = () => {
    ocrService.clearCache()
  }

  /**
   * Get cache statistics
   */
  const getCacheStats = () => {
    return ocrService.getCacheStats()
  }

  /**
   * Initialize OCR service
   */
  const initialize = async (): Promise<void> => {
    try {
      state.value.isProcessing = true
      state.value.progress = 0
      await ocrService.initialize()
      state.value.progress = 100
    } catch (error) {
      state.value.error = error instanceof Error ? error.message : 'Initialization failed'
    } finally {
      state.value.isProcessing = false
    }
  }

  /**
   * Terminate OCR service
   */
  const terminate = async (): Promise<void> => {
    try {
      await ocrService.terminate()
      clearResult()
    } catch (error) {
      state.value.error = error instanceof Error ? error.message : 'Termination failed'
    }
  }

  /**
   * Retry processing with different options
   */
  const retryWithOptions = async (
    imageFile: File | string,
    options: PreprocessingOptions
  ): Promise<OCRResult | null> => {
    return processImage(imageFile, options)
  }

  /**
   * Get suggested preprocessing options based on image characteristics
   */
  const getSuggestedOptions = (imageFile: File | string): PreprocessingOptions => {
    // This would analyze the image and suggest optimal preprocessing options
    // For now, return default options
    return {
      contrast: 1.2,
      brightness: 0.1,
      sharpen: true,
      denoise: true,
      threshold: 128
    }
  }

  /**
   * Export result as JSON
   */
  const exportResult = (): string | null => {
    if (!state.value.result) return null
    return JSON.stringify(state.value.result, null, 2)
  }

  /**
   * Import result from JSON
   */
  const importResult = (jsonString: string): boolean => {
    try {
      const result = JSON.parse(jsonString) as OCRResult
      state.value.result = result
      state.value.validation = ocrService.validateResult(result)
      return true
    } catch (error) {
      state.value.error = 'Invalid JSON format'
      return false
    }
  }

  return {
    // State
    state: readonly(state),
    
    // Computed
    isReady,
    hasResult,
    confidenceLevel,
    confidenceColor,
    
    // Methods
    processImage,
    processMultipleImages,
    convertToBulkEntries,
    getAllMedications,
    filterMedicationsByConfidence,
    mergeDuplicateMedications,
    clearResult,
    clearCache,
    getCacheStats,
    initialize,
    terminate,
    retryWithOptions,
    getSuggestedOptions,
    exportResult,
    importResult
  }
} 