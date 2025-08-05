/**
 * OCR Service Configuration
 * 
 * This file contains configuration for the enhanced OCR service including
 * API keys for Google Cloud Vision and Azure Computer Vision.
 */

import { OCRProviderConfig, BatchProcessingConfig } from '../services/ocrService'

/**
 * Environment-based OCR configuration
 */
export const ocrConfig: OCRProviderConfig = {
  // Google Cloud Vision API configuration
  googleCloudVision: {
    apiKey: import.meta.env.VITE_GOOGLE_CLOUD_VISION_API_KEY || '',
    projectId: import.meta.env.VITE_GOOGLE_CLOUD_PROJECT_ID || '',
    region: import.meta.env.VITE_GOOGLE_CLOUD_REGION || 'us-central1'
  },
  
  // Azure Computer Vision API configuration
  azureComputerVision: {
    endpoint: import.meta.env.VITE_AZURE_COMPUTER_VISION_ENDPOINT || '',
    apiKey: import.meta.env.VITE_AZURE_COMPUTER_VISION_API_KEY || '',
    region: import.meta.env.VITE_AZURE_REGION || 'eastus'
  },
  
  // Tesseract configuration
  tesseract: {
    enabled: true,
    languages: ['eng', 'afr'] // English and Afrikaans
  }
}

/**
 * Default batch processing configuration
 */
export const defaultBatchConfig: BatchProcessingConfig = {
  maxConcurrent: 3,
  timeout: 30000, // 30 seconds
  retryAttempts: 2,
  qualityThreshold: 0.6
}

/**
 * Production batch processing configuration
 */
export const productionBatchConfig: BatchProcessingConfig = {
  maxConcurrent: 5,
  timeout: 60000, // 60 seconds
  retryAttempts: 3,
  qualityThreshold: 0.7
}

/**
 * Development batch processing configuration
 */
export const developmentBatchConfig: BatchProcessingConfig = {
  maxConcurrent: 2,
  timeout: 15000, // 15 seconds
  retryAttempts: 1,
  qualityThreshold: 0.5
}

/**
 * Get appropriate batch configuration based on environment
 */
export function getBatchConfig(): BatchProcessingConfig {
  if (import.meta.env.PROD) {
    return productionBatchConfig
  } else if (import.meta.env.DEV) {
    return developmentBatchConfig
  } else {
    return defaultBatchConfig
  }
}

/**
 * Check if Google Cloud Vision is configured
 */
export function isGoogleCloudVisionConfigured(): boolean {
  return !!(ocrConfig.googleCloudVision?.apiKey && ocrConfig.googleCloudVision?.projectId)
}

/**
 * Check if Azure Computer Vision is configured
 */
export function isAzureComputerVisionConfigured(): boolean {
  return !!(ocrConfig.azureComputerVision?.apiKey && ocrConfig.azureComputerVision?.endpoint)
}

/**
 * Get available OCR providers
 */
export function getAvailableOCRProviders(): string[] {
  const providers: string[] = []
  
  if (isGoogleCloudVisionConfigured()) {
    providers.push('Google Cloud Vision')
  }
  
  if (isAzureComputerVisionConfigured()) {
    providers.push('Azure Computer Vision')
  }
  
  if (ocrConfig.tesseract?.enabled) {
    providers.push('Tesseract')
  }
  
  return providers
}

/**
 * Validate OCR configuration
 */
export function validateOCRConfig(): {
  isValid: boolean
  errors: string[]
  warnings: string[]
} {
  const errors: string[] = []
  const warnings: string[] = []
  
  // Check if at least one OCR provider is configured
  const availableProviders = getAvailableOCRProviders()
  
  if (availableProviders.length === 0) {
    errors.push('No OCR providers configured. At least one provider must be available.')
  }
  
  // Check Google Cloud Vision configuration
  if (ocrConfig.googleCloudVision?.apiKey && !ocrConfig.googleCloudVision?.projectId) {
    warnings.push('Google Cloud Vision API key provided but project ID is missing.')
  }
  
  if (ocrConfig.googleCloudVision?.projectId && !ocrConfig.googleCloudVision?.apiKey) {
    warnings.push('Google Cloud Vision project ID provided but API key is missing.')
  }
  
  // Check Azure Computer Vision configuration
  if (ocrConfig.azureComputerVision?.apiKey && !ocrConfig.azureComputerVision?.endpoint) {
    warnings.push('Azure Computer Vision API key provided but endpoint is missing.')
  }
  
  if (ocrConfig.azureComputerVision?.endpoint && !ocrConfig.azureComputerVision?.apiKey) {
    warnings.push('Azure Computer Vision endpoint provided but API key is missing.')
  }
  
  // Check Tesseract configuration
  if (!ocrConfig.tesseract?.enabled && availableProviders.length === 0) {
    warnings.push('Tesseract is disabled and no cloud providers configured. OCR will not work.')
  }
  
  return {
    isValid: errors.length === 0 && availableProviders.length > 0,
    errors,
    warnings
  }
}

/**
 * Get configuration summary for debugging
 */
export function getOCRConfigSummary(): {
  providers: string[]
  batchConfig: BatchProcessingConfig
  validation: { isValid: boolean; errors: string[]; warnings: string[] }
} {
  return {
    providers: getAvailableOCRProviders(),
    batchConfig: getBatchConfig(),
    validation: validateOCRConfig()
  }
} 