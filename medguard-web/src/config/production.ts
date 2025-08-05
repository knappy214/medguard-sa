/**
 * Production Configuration for MedGuard SA
 * 
 * This file contains comprehensive production settings for:
 * - OCR processing with Google Cloud Vision and Azure Computer Vision
 * - Perplexity API integration with rate limiting and caching
 * - Secure image storage with encryption
 * - HIPAA-compliant logging and audit trails
 * - Medication database connections
 * - South African pharmacy API integrations
 * - Monitoring and alerting
 * - Backup and disaster recovery
 * - Performance monitoring and optimization
 */

import { OCRProviderConfig, BatchProcessingConfig } from '../services/ocrService'

// ============================================================================
// ENVIRONMENT VARIABLES VALIDATION
// ============================================================================

const requiredEnvVars = {
  // Google Cloud Vision
  GOOGLE_CLOUD_VISION_API_KEY: import.meta.env.VITE_GOOGLE_CLOUD_VISION_API_KEY,
  GOOGLE_CLOUD_PROJECT_ID: import.meta.env.VITE_GOOGLE_CLOUD_PROJECT_ID,
  GOOGLE_CLOUD_REGION: import.meta.env.VITE_GOOGLE_CLOUD_REGION,
  
  // Azure Computer Vision
  AZURE_COMPUTER_VISION_ENDPOINT: import.meta.env.VITE_AZURE_COMPUTER_VISION_ENDPOINT,
  AZURE_COMPUTER_VISION_API_KEY: import.meta.env.VITE_AZURE_COMPUTER_VISION_API_KEY,
  AZURE_REGION: import.meta.env.VITE_AZURE_REGION,
  
  // Perplexity API
  PERPLEXITY_API_KEY: import.meta.env.VITE_PERPLEXITY_API_KEY,
  
  // Storage and Encryption
  STORAGE_ENCRYPTION_KEY: import.meta.env.VITE_STORAGE_ENCRYPTION_KEY,
  STORAGE_BUCKET_NAME: import.meta.env.VITE_STORAGE_BUCKET_NAME,
  
  // Monitoring
  MONITORING_ENDPOINT: import.meta.env.VITE_MONITORING_ENDPOINT,
  ALERT_WEBHOOK_URL: import.meta.env.VITE_ALERT_WEBHOOK_URL,
  
  // Database Connections
  MEDICATION_DB_URL: import.meta.env.VITE_MEDICATION_DB_URL,
  PHARMACY_API_KEY: import.meta.env.VITE_PHARMACY_API_KEY,
  
  // Backup and Recovery
  BACKUP_ENDPOINT: import.meta.env.VITE_BACKUP_ENDPOINT,
  DISASTER_RECOVERY_ENDPOINT: import.meta.env.VITE_DISASTER_RECOVERY_ENDPOINT
}

// ============================================================================
// 1. GOOGLE CLOUD VISION API CONFIGURATION
// ============================================================================

export const googleCloudVisionConfig = {
  apiKey: requiredEnvVars.GOOGLE_CLOUD_VISION_API_KEY || '',
  projectId: requiredEnvVars.GOOGLE_CLOUD_PROJECT_ID || '',
  region: requiredEnvVars.GOOGLE_CLOUD_REGION || 'us-central1',
  
  // OCR-specific settings
  ocr: {
    languageHints: ['en-ZA', 'af-ZA'], // South African English and Afrikaans
    maxResults: 10,
    confidenceThreshold: 0.7,
    enableTextDetection: true,
    enableDocumentTextDetection: true
  },
  
  // Rate limiting and quotas
  rateLimiting: {
    requestsPerMinute: 1000,
    requestsPerSecond: 20,
    burstLimit: 50,
    quotaExceededRetryDelay: 60000 // 1 minute
  },
  
  // Error handling
  errorHandling: {
    maxRetries: 3,
    retryDelay: 2000,
    timeout: 30000,
    fallbackToAzure: true
  },
  
  // Performance optimization
  performance: {
    enableAsyncProcessing: true,
    batchSize: 10,
    concurrentRequests: 5,
    enableCaching: true,
    cacheTTL: 3600000 // 1 hour
  }
}

// ============================================================================
// 2. AZURE COMPUTER VISION BACKUP CONFIGURATION
// ============================================================================

export const azureComputerVisionConfig = {
  endpoint: requiredEnvVars.AZURE_COMPUTER_VISION_ENDPOINT || '',
  apiKey: requiredEnvVars.AZURE_COMPUTER_VISION_API_KEY || '',
  region: requiredEnvVars.AZURE_REGION || 'eastus',
  
  // OCR settings
  ocr: {
    language: 'en', // Azure supports English by default
    detectOrientation: true,
    modelVersion: 'latest',
    confidenceThreshold: 0.6
  },
  
  // Rate limiting
  rateLimiting: {
    requestsPerMinute: 500,
    requestsPerSecond: 10,
    burstLimit: 25
  },
  
  // Error handling
  errorHandling: {
    maxRetries: 2,
    retryDelay: 3000,
    timeout: 25000
  },
  
  // Performance settings
  performance: {
    enableAsyncProcessing: true,
    batchSize: 5,
    concurrentRequests: 3
  }
}

// ============================================================================
// 3. PERPLEXITY API CONFIGURATION WITH RATE LIMITING AND CACHING
// ============================================================================

export const perplexityApiConfig = {
  apiKey: requiredEnvVars.PERPLEXITY_API_KEY || '',
  baseUrl: 'https://api.perplexity.ai',
  
  // Rate limiting configuration
  rateLimiting: {
    requestsPerMinute: 50,
    requestsPerHour: 1000,
    requestsPerDay: 10000,
    burstLimit: 10,
    retryAfterHeader: 'X-RateLimit-Reset'
  },
  
  // Caching configuration
  caching: {
    enabled: true,
    ttl: 3600000, // 1 hour
    maxSize: 1000, // Maximum cache entries
    cacheKeyPrefix: 'perplexity:',
    enableCompression: true
  },
  
  // Request configuration
  request: {
    timeout: 30000,
    maxRetries: 3,
    retryDelay: 2000,
    userAgent: 'MedGuard-SA/1.0'
  },
  
  // Model configuration
  models: {
    default: 'llama-3.1-sonar-small-128k-online',
    fallback: 'llama-3.1-sonar-small-128k',
    maxTokens: 4096,
    temperature: 0.1
  },
  
  // Medication-specific prompts
  medicationPrompts: {
    drugInteraction: 'Analyze potential drug interactions between {drug1} and {drug2}',
    sideEffects: 'List common side effects for {medication}',
    dosage: 'Provide dosage information for {medication} for {condition}',
    contraindications: 'List contraindications for {medication}'
  }
}

// ============================================================================
// 4. SECURE IMAGE STORAGE WITH ENCRYPTION
// ============================================================================

export const secureImageStorageConfig = {
  // Encryption settings
  encryption: {
    enabled: true,
    algorithm: 'AES-256-GCM',
    key: requiredEnvVars.STORAGE_ENCRYPTION_KEY || '',
    keyRotationInterval: 2592000000, // 30 days
    enableKeyRotation: true
  },
  
  // Storage configuration
  storage: {
    bucketName: requiredEnvVars.STORAGE_BUCKET_NAME || 'medguard-prescriptions',
    region: 'eu-west-1', // European region for GDPR compliance
    enableVersioning: true,
    enableLifecycleManagement: true,
    retentionPeriod: 7776000000, // 90 days
    enableCompression: true
  },
  
  // Security settings
  security: {
    enableAccessLogging: true,
    enableServerSideEncryption: true,
    enableBucketPolicy: true,
    enableCORS: false, // Disable for security
    enablePublicAccess: false
  },
  
  // File handling
  fileHandling: {
    maxFileSize: 10485760, // 10MB
    allowedFormats: ['image/jpeg', 'image/png', 'image/webp'],
    enableVirusScanning: true,
    enableMetadataExtraction: true
  },
  
  // Backup configuration
  backup: {
    enabled: true,
    frequency: 'daily',
    retentionPeriod: 31536000000, // 1 year
    enableCrossRegionReplication: true
  }
}

// ============================================================================
// 5. HIPAA-COMPLIANT LOGGING AND AUDIT TRAILS
// ============================================================================

export const hipaaLoggingConfig = {
  // Logging levels
  levels: {
    error: true,
    warn: true,
    info: true,
    debug: false, // Disable in production
    trace: false
  },
  
  // Audit trail configuration
  auditTrail: {
    enabled: true,
    logUserActions: true,
    logDataAccess: true,
    logDataModifications: true,
    logAuthenticationEvents: true,
    logAuthorizationEvents: true,
    retentionPeriod: 31536000000 // 7 years for HIPAA compliance
  },
  
  // Sensitive data handling
  sensitiveData: {
    maskPHI: true,
    maskCreditCards: true,
    maskSSNs: true,
    maskEmailAddresses: false, // Keep for audit purposes
    enableDataAnonymization: true
  },
  
  // Log storage
  storage: {
    type: 'structured', // JSON format
    destination: 'cloud-logging',
    enableCompression: true,
    enableEncryption: true,
    backupEnabled: true
  },
  
  // Compliance settings
  compliance: {
    hipaaCompliant: true,
    enableAccessLogs: true,
    enableChangeLogs: true,
    enableSecurityLogs: true,
    enablePerformanceLogs: true
  },
  
  // Alerting
  alerting: {
    enableSecurityAlerts: true,
    enablePerformanceAlerts: true,
    enableErrorAlerts: true,
    alertThresholds: {
      errorRate: 0.05, // 5%
      responseTime: 5000, // 5 seconds
      failedLogins: 5 // per minute
    }
  }
}

// ============================================================================
// 6. MEDICATION DATABASE CONNECTIONS
// ============================================================================

export const medicationDatabaseConfig = {
  // Primary medication database
  primary: {
    url: requiredEnvVars.MEDICATION_DB_URL || '',
    type: 'postgresql',
    connectionPool: {
      min: 5,
      max: 20,
      acquireTimeout: 60000,
      idleTimeout: 300000
    },
    ssl: {
      enabled: true,
      rejectUnauthorized: true
    }
  },
  
  // Drug interaction database
  interactions: {
    provider: 'drugbank',
    apiKey: import.meta.env.VITE_DRUGBANK_API_KEY || '',
    baseUrl: 'https://api.drugbank.com/v1',
    cacheEnabled: true,
    cacheTTL: 86400000 // 24 hours
  },
  
  // South African medication database
  saMedications: {
    provider: 'sahpra', // South African Health Products Regulatory Authority
    baseUrl: 'https://api.sahpra.org.za/v1',
    apiKey: import.meta.env.VITE_SAHPRA_API_KEY || '',
    cacheEnabled: true,
    cacheTTL: 3600000 // 1 hour
  },
  
  // Fallback databases
  fallbacks: [
    {
      name: 'openFDA',
      baseUrl: 'https://api.fda.gov',
      rateLimit: 1000, // requests per day
      cacheEnabled: true
    },
    {
      name: 'WHO-ATC',
      baseUrl: 'https://www.whocc.no/atc_ddd_index',
      cacheEnabled: true
    }
  ],
  
  // Validation settings
  validation: {
    enableRealTimeValidation: true,
    enableBatchValidation: true,
    validationTimeout: 10000,
    enableFuzzyMatching: true,
    confidenceThreshold: 0.8
  }
}

// ============================================================================
// 7. SOUTH AFRICAN PHARMACY API INTEGRATIONS
// ============================================================================

export const saPharmacyApiConfig = {
  // Primary pharmacy API
  primary: {
    provider: 'pharmacy-council-sa',
    baseUrl: 'https://api.pharmacycouncil.org.za/v1',
    apiKey: requiredEnvVars.PHARMACY_API_KEY || '',
    timeout: 15000
  },
  
  // Pharmacy verification
  verification: {
    enableLicenseVerification: true,
    enablePharmacyLookup: true,
    enablePrescriberVerification: true,
    cacheEnabled: true,
    cacheTTL: 86400000 // 24 hours
  },
  
  // Prescription validation
  prescriptionValidation: {
    enableDrugAvailability: true,
    enablePricing: true,
    enableSubstitution: true,
    enableGenericSubstitution: true
  },
  
  // Regional pharmacy networks
  regionalNetworks: {
    gauteng: {
      baseUrl: 'https://api.gauteng-pharmacy.org.za',
      apiKey: import.meta.env.VITE_GAUTENG_PHARMACY_API_KEY || ''
    },
    westernCape: {
      baseUrl: 'https://api.wc-pharmacy.org.za',
      apiKey: import.meta.env.VITE_WC_PHARMACY_API_KEY || ''
    },
    kwazuluNatal: {
      baseUrl: 'https://api.kzn-pharmacy.org.za',
      apiKey: import.meta.env.VITE_KZN_PHARMACY_API_KEY || ''
    }
  },
  
  // Compliance settings
  compliance: {
    enableSAHPRACompliance: true,
    enableNDOHCompliance: true, // National Department of Health
    enableBHFCompliance: true, // Board of Healthcare Funders
    enablePMSACompliance: true // Pharmaceutical Society of South Africa
  }
}

// ============================================================================
// 8. MONITORING AND ALERTING
// ============================================================================

export const monitoringConfig = {
  // Monitoring endpoint
  endpoint: requiredEnvVars.MONITORING_ENDPOINT || 'https://monitoring.medguard-sa.com',
  
  // Application performance monitoring
  apm: {
    enabled: true,
    sampleRate: 0.1, // 10% of requests
    enableRealUserMonitoring: true,
    enableErrorTracking: true,
    enablePerformanceTracking: true
  },
  
  // Health checks
  healthChecks: {
    enabled: true,
    interval: 30000, // 30 seconds
    timeout: 10000,
    endpoints: [
      '/api/health',
      '/api/ocr/health',
      '/api/prescriptions/health',
      '/api/medications/health'
    ]
  },
  
  // Metrics collection
  metrics: {
    enableSystemMetrics: true,
    enableApplicationMetrics: true,
    enableBusinessMetrics: true,
    collectionInterval: 60000 // 1 minute
  },
  
  // Alerting configuration
  alerting: {
    webhookUrl: requiredEnvVars.ALERT_WEBHOOK_URL || '',
    enableEmailAlerts: true,
    enableSMSAlerts: true,
    enableSlackAlerts: true,
    
    thresholds: {
      errorRate: 0.05, // 5%
      responseTime: 5000, // 5 seconds
      cpuUsage: 0.8, // 80%
      memoryUsage: 0.85, // 85%
      diskUsage: 0.9, // 90%
      failedPrescriptions: 10 // per hour
    },
    
    escalation: {
      level1: { delay: 300000 }, // 5 minutes
      level2: { delay: 900000 }, // 15 minutes
      level3: { delay: 3600000 } // 1 hour
    }
  },
  
  // Dashboard configuration
  dashboard: {
    enableRealTimeDashboard: true,
    enableHistoricalReports: true,
    enableCustomAlerts: true,
    retentionPeriod: 7776000000 // 90 days
  }
}

// ============================================================================
// 9. BACKUP AND DISASTER RECOVERY
// ============================================================================

export const backupRecoveryConfig = {
  // Backup configuration
  backup: {
    enabled: true,
    endpoint: requiredEnvVars.BACKUP_ENDPOINT || 'https://backup.medguard-sa.com',
    
    // Data backup
    data: {
      frequency: 'hourly',
      retentionPeriod: 31536000000, // 1 year
      enableIncremental: true,
      enableCompression: true,
      enableEncryption: true
    },
    
    // Configuration backup
    configuration: {
      frequency: 'daily',
      retentionPeriod: 31536000000, // 1 year
      includeSecrets: false,
      enableVersioning: true
    },
    
    // Database backup
    database: {
      frequency: 'daily',
      retentionPeriod: 7776000000, // 90 days
      enablePointInTimeRecovery: true,
      enableCrossRegionReplication: true
    }
  },
  
  // Disaster recovery
  disasterRecovery: {
    enabled: true,
    endpoint: requiredEnvVars.DISASTER_RECOVERY_ENDPOINT || 'https://dr.medguard-sa.com',
    
    // Recovery objectives
    objectives: {
      rto: 3600000, // 1 hour Recovery Time Objective
      rpo: 300000 // 5 minutes Recovery Point Objective
    },
    
    // Failover configuration
    failover: {
      automatic: true,
      manual: true,
      testing: {
        frequency: 'monthly',
        lastTest: null
      }
    },
    
    // Geographic redundancy
    geographicRedundancy: {
      primaryRegion: 'eu-west-1',
      secondaryRegion: 'eu-central-1',
      tertiaryRegion: 'us-east-1'
    }
  },
  
  // Business continuity
  businessContinuity: {
    enableOfflineMode: true,
    enableDataSync: true,
    enableGracefulDegradation: true,
    enableEmergencyProcedures: true
  }
}

// ============================================================================
// 10. PERFORMANCE MONITORING AND OPTIMIZATION
// ============================================================================

export const performanceConfig = {
  // Performance monitoring
  monitoring: {
    enableRealTimeMonitoring: true,
    enableHistoricalAnalysis: true,
    enablePredictiveAnalysis: true,
    enableResourceTracking: true
  },
  
  // Caching strategy
  caching: {
    // Browser caching
    browser: {
      enabled: true,
      maxAge: 3600, // 1 hour
      enableETags: true,
      enableCompression: true
    },
    
    // Application caching
    application: {
      enabled: true,
      maxSize: 100, // MB
      ttl: 1800000, // 30 minutes
      enableLRU: true
    },
    
    // CDN caching
    cdn: {
      enabled: true,
      ttl: 3600, // 1 hour
      enablePurge: true,
      enableCompression: true
    }
  },
  
  // Database optimization
  database: {
    enableConnectionPooling: true,
    enableQueryOptimization: true,
    enableIndexing: true,
    enableReadReplicas: true,
    enableSharding: false // For future scaling
  },
  
  // Image optimization
  imageOptimization: {
    enableCompression: true,
    enableWebP: true,
    enableResponsiveImages: true,
    enableLazyLoading: true,
    maxWidth: 1920,
    quality: 0.8
  },
  
  // Code splitting and bundling
  bundling: {
    enableCodeSplitting: true,
    enableTreeShaking: true,
    enableMinification: true,
    enableGzip: true,
    enableBrotli: true
  },
  
  // API optimization
  api: {
    enableGraphQL: false, // For future consideration
    enableBatching: true,
    enablePagination: true,
    enableFiltering: true,
    enableSorting: true
  }
}

// ============================================================================
// CONFIGURATION VALIDATION AND EXPORTS
// ============================================================================

/**
 * Validate production configuration
 */
export function validateProductionConfig(): {
  isValid: boolean
  errors: string[]
  warnings: string[]
} {
  const errors: string[] = []
  const warnings: string[] = []
  
  // Check required environment variables
  Object.entries(requiredEnvVars).forEach(([key, value]) => {
    if (!value) {
      errors.push(`Missing required environment variable: ${key}`)
    }
  })
  
  // Validate Google Cloud Vision configuration
  if (!googleCloudVisionConfig.apiKey || !googleCloudVisionConfig.projectId) {
    warnings.push('Google Cloud Vision API not fully configured')
  }
  
  // Validate Azure Computer Vision configuration
  if (!azureComputerVisionConfig.apiKey || !azureComputerVisionConfig.endpoint) {
    warnings.push('Azure Computer Vision API not fully configured')
  }
  
  // Validate Perplexity API configuration
  if (!perplexityApiConfig.apiKey) {
    warnings.push('Perplexity API not configured')
  }
  
  // Validate storage configuration
  if (!secureImageStorageConfig.encryption.key) {
    errors.push('Storage encryption key is required')
  }
  
  // Validate monitoring configuration
  if (!monitoringConfig.endpoint) {
    warnings.push('Monitoring endpoint not configured')
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

/**
 * Get production configuration summary
 */
export function getProductionConfigSummary(): {
  services: {
    googleCloudVision: boolean
    azureComputerVision: boolean
    perplexityApi: boolean
    secureStorage: boolean
    monitoring: boolean
    backup: boolean
  }
  validation: {
    isValid: boolean
    errors: string[]
    warnings: string[]
  }
} {
  return {
    services: {
      googleCloudVision: !!(googleCloudVisionConfig.apiKey && googleCloudVisionConfig.projectId),
      azureComputerVision: !!(azureComputerVisionConfig.apiKey && azureComputerVisionConfig.endpoint),
      perplexityApi: !!perplexityApiConfig.apiKey,
      secureStorage: !!secureImageStorageConfig.encryption.key,
      monitoring: !!monitoringConfig.endpoint,
      backup: !!backupRecoveryConfig.backup.endpoint
    },
    validation: validateProductionConfig()
  }
}

// Export all configurations
export {
  googleCloudVisionConfig,
  azureComputerVisionConfig,
  perplexityApiConfig,
  secureImageStorageConfig,
  hipaaLoggingConfig,
  medicationDatabaseConfig,
  saPharmacyApiConfig,
  monitoringConfig,
  backupRecoveryConfig,
  performanceConfig
}

// Default export for easy importing
export default {
  googleCloudVision: googleCloudVisionConfig,
  azureComputerVision: azureComputerVisionConfig,
  perplexityApi: perplexityApiConfig,
  secureImageStorage: secureImageStorageConfig,
  hipaaLogging: hipaaLoggingConfig,
  medicationDatabase: medicationDatabaseConfig,
  saPharmacyApi: saPharmacyApiConfig,
  monitoring: monitoringConfig,
  backupRecovery: backupRecoveryConfig,
  performance: performanceConfig,
  validate: validateProductionConfig,
  getSummary: getProductionConfigSummary
} 