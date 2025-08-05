/**
 * Enhanced API Configuration for MedGuard SA
 * 
 * This file manages API endpoints and configuration with comprehensive
 * prescription workflow support, security, and reliability features.
 */

import { environment } from './environment'

// Enhanced API Configuration Interface
export interface ApiConfig {
  baseURL: string
  backupURLs: string[]
  timeout: {
    default: number
    prescription: number
    ocr: number
    upload: number
    analytics: number
  }
  useMockData: boolean
  enableLogging: boolean
  retryAttempts: number
  retryDelay: number
  rateLimiting: {
    ocr: {
      requestsPerMinute: number
      burstLimit: number
    }
    prescription: {
      requestsPerMinute: number
      burstLimit: number
    }
    general: {
      requestsPerMinute: number
      burstLimit: number
    }
  }
  encryption: {
    enabled: boolean
    algorithm: string
    keyRotationInterval: number
  }
  caching: {
    enabled: boolean
    ttl: number
    maxSize: number
  }
  monitoring: {
    enabled: boolean
    endpoint: string
    sampleRate: number
  }
  authentication: {
    headerName: string
    tokenRefreshThreshold: number
    autoRefresh: boolean
  }
}

// Environment-based configuration
const getApiConfig = (): ApiConfig => {
  const isDevelopment = environment.IS_DEVELOPMENT
  const isProduction = environment.IS_PRODUCTION
  
  const forceRealApi = environment.FORCE_REAL_API
  const apiBaseUrl = environment.API_BASE_URL
  
  return {
    baseURL: apiBaseUrl,
    backupURLs: [
      'https://backup1.medguard-sa.com',
      'https://backup2.medguard-sa.com'
    ],
    timeout: {
      default: 30000, // 30 seconds
      prescription: 120000, // 2 minutes for prescription processing
      ocr: 60000, // 1 minute for OCR processing
      upload: 180000, // 3 minutes for file uploads
      analytics: 45000 // 45 seconds for analytics
    },
    useMockData: isDevelopment && !forceRealApi,
    enableLogging: environment.ENABLE_API_LOGGING,
    retryAttempts: 3,
    retryDelay: 1000,
    rateLimiting: {
      ocr: {
        requestsPerMinute: 10,
        burstLimit: 3
      },
      prescription: {
        requestsPerMinute: 30,
        burstLimit: 5
      },
      general: {
        requestsPerMinute: 100,
        burstLimit: 20
      }
    },
    encryption: {
      enabled: true,
      algorithm: 'AES-256-GCM',
      keyRotationInterval: 24 * 60 * 60 * 1000 // 24 hours
    },
    caching: {
      enabled: true,
      ttl: 5 * 60 * 1000, // 5 minutes
      maxSize: 100 // Maximum 100 cached items
    },
    monitoring: {
      enabled: true,
      endpoint: '/api/monitoring/analytics/',
      sampleRate: 0.1 // 10% of requests
    },
    authentication: {
      headerName: 'Authorization',
      tokenRefreshThreshold: 5 * 60 * 1000, // 5 minutes
      autoRefresh: true
    }
  }
}

export const apiConfig = getApiConfig()

// Comprehensive API Endpoints with Versioning
export const API_ENDPOINTS = {
  // Version 1 endpoints (current)
  v1: {
    // Authentication & User Management
    AUTH: {
      LOGIN: '/api/v1/auth/login/',
      LOGOUT: '/api/v1/auth/logout/',
      REFRESH: '/api/v1/auth/refresh/',
      VALIDATE: '/api/v1/auth/validate/',
      PROFILE: '/api/v1/users/profile/me/',
      CHANGE_PASSWORD: '/api/v1/auth/change-password/',
      RESET_PASSWORD: '/api/v1/auth/reset-password/',
      VERIFY_EMAIL: '/api/v1/auth/verify-email/',
    },
    
    // Comprehensive Prescription Workflow
    PRESCRIPTIONS: {
      // Core prescription operations
      CREATE: '/api/v1/prescriptions/',
      LIST: '/api/v1/prescriptions/',
      DETAIL: (id: string) => `/api/v1/prescriptions/${id}/`,
      UPDATE: (id: string) => `/api/v1/prescriptions/${id}/`,
      DELETE: (id: string) => `/api/v1/prescriptions/${id}/`,
      BULK_CREATE: '/api/v1/prescriptions/bulk/',
      BULK_UPDATE: '/api/v1/prescriptions/bulk/update/',
      BULK_DELETE: '/api/v1/prescriptions/bulk/delete/',
      
      // Prescription processing workflow
      PROCESS: (id: string) => `/api/v1/prescriptions/${id}/process/`,
      VALIDATE: (id: string) => `/api/v1/prescriptions/${id}/validate/`,
      APPROVE: (id: string) => `/api/v1/prescriptions/${id}/approve/`,
      REJECT: (id: string) => `/api/v1/prescriptions/${id}/reject/`,
      DISPENSE: (id: string) => `/api/v1/prescriptions/${id}/dispense/`,
      COMPLETE: (id: string) => `/api/v1/prescriptions/${id}/complete/`,
      
      // Prescription lifecycle management
      RENEWALS: '/api/v1/prescriptions/renewals/',
      RENEWAL_DETAIL: (id: string) => `/api/v1/prescriptions/renewals/${id}/`,
      RENEWAL_REQUEST: (id: string) => `/api/v1/prescriptions/${id}/renewal-request/`,
      RENEWAL_APPROVE: (id: string) => `/api/v1/prescriptions/renewals/${id}/approve/`,
      RENEWAL_REJECT: (id: string) => `/api/v1/prescriptions/renewals/${id}/reject/`,
      
      // Prescription history and tracking
      HISTORY: (id: string) => `/api/v1/prescriptions/${id}/history/`,
      AUDIT_TRAIL: (id: string) => `/api/v1/prescriptions/${id}/audit-trail/`,
      STATUS_CHANGES: (id: string) => `/api/v1/prescriptions/${id}/status-changes/`,
      
      // Prescription search and filtering
      SEARCH: '/api/v1/prescriptions/search/',
      FILTER: '/api/v1/prescriptions/filter/',
      EXPORT: '/api/v1/prescriptions/export/',
      
      // Prescription templates and favorites
      TEMPLATES: '/api/v1/prescriptions/templates/',
      TEMPLATE_DETAIL: (id: string) => `/api/v1/prescriptions/templates/${id}/`,
      FAVORITES: '/api/v1/prescriptions/favorites/',
      FAVORITE_TOGGLE: (id: string) => `/api/v1/prescriptions/${id}/favorite/`,
    },
    
    // OCR and Image Processing
    OCR: {
      PROCESS_IMAGE: '/api/v1/ocr/process/',
      PROCESS_BATCH: '/api/v1/ocr/process-batch/',
      VALIDATE_RESULT: '/api/v1/ocr/validate/',
      CORRECT_TEXT: '/api/v1/ocr/correct/',
      EXTRACT_MEDICATION: '/api/v1/ocr/extract-medication/',
      EXTRACT_DOSAGE: '/api/v1/ocr/extract-dosage/',
      EXTRACT_FREQUENCY: '/api/v1/ocr/extract-frequency/',
      EXTRACT_DURATION: '/api/v1/ocr/extract-duration/',
      EXTRACT_PRESCRIBER: '/api/v1/ocr/extract-prescriber/',
      EXTRACT_PATIENT: '/api/v1/ocr/extract-patient/',
      PROCESS_PRESCRIPTION_FORM: '/api/v1/ocr/prescription-form/',
      PROCESS_MEDICATION_LABEL: '/api/v1/ocr/medication-label/',
      PROCESS_DOCTOR_NOTE: '/api/v1/ocr/doctor-note/',
    },
    
    // Medication Management
    MEDICATIONS: {
      LIST: '/api/v1/medications/',
      DETAIL: (id: string) => `/api/v1/medications/${id}/`,
      CREATE: '/api/v1/medications/',
      UPDATE: (id: string) => `/api/v1/medications/${id}/`,
      DELETE: (id: string) => `/api/v1/medications/${id}/`,
      BULK_OPERATIONS: '/api/v1/medications/bulk/',
      
      // Medication scheduling and reminders
      SCHEDULE: '/api/v1/medications/schedules/',
      SCHEDULE_DETAIL: (id: string) => `/api/v1/medications/schedules/${id}/`,
      REMINDERS: '/api/v1/medications/reminders/',
      REMINDER_DETAIL: (id: string) => `/api/v1/medications/reminders/${id}/`,
      
      // Medication logs and tracking
      LOGS: '/api/v1/medications/logs/',
      LOG_DETAIL: (id: string) => `/api/v1/medications/logs/${id}/`,
      ALERTS: '/api/v1/medications/alerts/',
      ALERT_DETAIL: (id: string) => `/api/v1/medications/alerts/${id}/`,
      
      // Medication analytics and reporting
      ANALYTICS: (id: string) => `/api/v1/medications/${id}/analytics/`,
      REPORTS: '/api/v1/medications/reports/',
      STATISTICS: '/api/v1/medications/statistics/',
      
      // Medication validation and safety
      VALIDATION: {
        VALIDATE: '/api/v1/medications/validation/',
        DRUG_DATABASE: '/api/v1/medications/validation/drug-database/',
        INTERACTIONS: '/api/v1/medications/validation/interactions/',
        ALLERGIES: '/api/v1/medications/validation/allergies/',
        CONTRAINDICATIONS: '/api/v1/medications/validation/contraindications/',
        DOSAGE_CHECK: '/api/v1/medications/validation/dosage-check/',
        FREQUENCY_CHECK: '/api/v1/medications/validation/frequency-check/',
        DURATION_CHECK: '/api/v1/medications/validation/duration-check/',
      },
      
      // Medication enrichment and information
      ENRICHMENT: {
        PERPLEXITY: '/api/v1/medications/enrichment/perplexity/',
        DRUG_INFO: '/api/v1/medications/enrichment/drug-info/',
        COST_ANALYSIS: '/api/v1/medications/enrichment/cost-analysis/',
        AVAILABILITY: '/api/v1/medications/enrichment/availability/',
        ALTERNATIVES: '/api/v1/medications/enrichment/alternatives/',
        GENERIC_EQUIVALENTS: '/api/v1/medications/enrichment/generic-equivalents/',
        SIDE_EFFECTS: '/api/v1/medications/enrichment/side-effects/',
        INTERACTIONS_DETAILED: '/api/v1/medications/enrichment/interactions-detailed/',
      },
      
      // Batch operations
      BATCH: {
        CREATE: '/api/v1/medications/batch/create/',
        VALIDATE: '/api/v1/medications/batch/validate/',
        PROCESS: '/api/v1/medications/batch/process/',
        UPDATE: '/api/v1/medications/batch/update/',
        DELETE: '/api/v1/medications/batch/delete/',
        EXPORT: '/api/v1/medications/batch/export/',
        IMPORT: '/api/v1/medications/batch/import/',
      },
      
      // Image management
      IMAGES: {
        UPLOAD: '/api/v1/medications/images/upload/',
        LIST: (medicationId: string) => `/api/v1/medications/${medicationId}/images/`,
        DETAIL: (id: string) => `/api/v1/medications/images/${id}/`,
        DELETE: (id: string) => `/api/v1/medications/images/${id}/`,
        PROCESS: (id: string) => `/api/v1/medications/images/${id}/process/`,
        ANNOTATE: (id: string) => `/api/v1/medications/images/${id}/annotate/`,
      },
      
      // Adherence tracking
      ADHERENCE: {
        TRACKING: (medicationId: string) => `/api/v1/medications/${medicationId}/adherence/`,
        HISTORY: (medicationId: string) => `/api/v1/medications/${medicationId}/history/`,
        STATS: '/api/v1/medications/adherence/stats/',
        REPORTS: '/api/v1/medications/adherence/reports/',
        ALERTS: '/api/v1/medications/adherence/alerts/',
        GOALS: '/api/v1/medications/adherence/goals/',
      },
      
      // Storage and archiving
      STORAGE: {
        PRESCRIPTIONS: '/api/v1/medications/storage/prescriptions/',
        PRESCRIPTION_DETAIL: (id: string) => `/api/v1/medications/storage/prescriptions/${id}/`,
        ARCHIVE: (id: string) => `/api/v1/medications/storage/prescriptions/${id}/archive/`,
        RESTORE: (id: string) => `/api/v1/medications/storage/prescriptions/${id}/restore/`,
        BACKUP: '/api/v1/medications/storage/backup/',
        RESTORE_BACKUP: '/api/v1/medications/storage/restore-backup/',
      },
    },
    
    // Notifications and Communication
    NOTIFICATIONS: {
      LIST: '/api/v1/notifications/',
      DETAIL: (id: string) => `/api/v1/notifications/${id}/`,
      MARK_READ: (id: string) => `/api/v1/notifications/${id}/mark-read/`,
      MARK_ALL_READ: '/api/v1/notifications/mark-all-read/',
      DELETE: (id: string) => `/api/v1/notifications/${id}/`,
      DELETE_ALL: '/api/v1/notifications/delete-all/',
      PREFERENCES: '/api/v1/notifications/preferences/',
      TEST: '/api/v1/notifications/test/',
      BULK_OPERATIONS: '/api/v1/notifications/bulk/',
    },
    
    // Security and Compliance
    SECURITY: {
      EVENTS: '/api/v1/security/events/',
      SETTINGS: '/api/v1/security/settings/',
      AUDIT_LOG: '/api/v1/security/audit-log/',
      ACCESS_CONTROL: '/api/v1/security/access-control/',
      ENCRYPTION_KEYS: '/api/v1/security/encryption-keys/',
      COMPLIANCE_REPORT: '/api/v1/security/compliance-report/',
      DATA_BREACH: '/api/v1/security/data-breach/',
      PRIVACY_SETTINGS: '/api/v1/security/privacy-settings/',
    },
    
    // Monitoring and Analytics
    MONITORING: {
      ANALYTICS: '/api/v1/monitoring/analytics/',
      PERFORMANCE: '/api/v1/monitoring/performance/',
      ERRORS: '/api/v1/monitoring/errors/',
      USAGE: '/api/v1/monitoring/usage/',
      HEALTH: '/api/v1/monitoring/health/',
      METRICS: '/api/v1/monitoring/metrics/',
      ALERTS: '/api/v1/monitoring/alerts/',
      DASHBOARD: '/api/v1/monitoring/dashboard/',
    },
    
    // File Management
    FILES: {
      UPLOAD: '/api/v1/files/upload/',
      DOWNLOAD: (id: string) => `/api/v1/files/${id}/download/`,
      DELETE: (id: string) => `/api/v1/files/${id}/`,
      LIST: '/api/v1/files/',
      DETAIL: (id: string) => `/api/v1/files/${id}/`,
      SHARE: (id: string) => `/api/v1/files/${id}/share/`,
      UNSHARE: (id: string) => `/api/v1/files/${id}/unshare/`,
      VERSIONS: (id: string) => `/api/v1/files/${id}/versions/`,
    },
    
    // Backup and Recovery
    BACKUP: {
      CREATE: '/api/v1/backup/create/',
      RESTORE: '/api/v1/backup/restore/',
      LIST: '/api/v1/backup/',
      DETAIL: (id: string) => `/api/v1/backup/${id}/`,
      DELETE: (id: string) => `/api/v1/backup/${id}/`,
      SCHEDULE: '/api/v1/backup/schedule/',
      STATUS: '/api/v1/backup/status/',
    },
  },
  
  // Version 2 endpoints (future)
  v2: {
    // Future API version endpoints
    PRESCRIPTIONS: {
      CREATE: '/api/v2/prescriptions/',
      LIST: '/api/v2/prescriptions/',
      DETAIL: (id: string) => `/api/v2/prescriptions/${id}/`,
    },
  }
} as const

// Error handling configurations
export const ERROR_CONFIG = {
  // HTTP status codes and their handling
  STATUS_CODES: {
    BAD_REQUEST: 400,
    UNAUTHORIZED: 401,
    FORBIDDEN: 403,
    NOT_FOUND: 404,
    METHOD_NOT_ALLOWED: 405,
    CONFLICT: 409,
    UNPROCESSABLE_ENTITY: 422,
    TOO_MANY_REQUESTS: 429,
    INTERNAL_SERVER_ERROR: 500,
    BAD_GATEWAY: 502,
    SERVICE_UNAVAILABLE: 503,
    GATEWAY_TIMEOUT: 504,
  },
  
  // Retry configurations for different error types
  RETRY_CONFIG: {
    NETWORK_ERRORS: {
      retry: true,
      maxAttempts: 3,
      backoffMultiplier: 2,
      initialDelay: 1000,
    },
    SERVER_ERRORS: {
      retry: true,
      maxAttempts: 2,
      backoffMultiplier: 1.5,
      initialDelay: 2000,
    },
    RATE_LIMIT_ERRORS: {
      retry: true,
      maxAttempts: 1,
      backoffMultiplier: 1,
      initialDelay: 5000,
    },
    AUTH_ERRORS: {
      retry: false,
      maxAttempts: 0,
      backoffMultiplier: 1,
      initialDelay: 0,
    },
  },
  
  // Error messages for different scenarios
  MESSAGES: {
    NETWORK_ERROR: 'Network connection error. Please check your internet connection.',
    TIMEOUT_ERROR: 'Request timed out. Please try again.',
    SERVER_ERROR: 'Server error occurred. Please try again later.',
    AUTH_ERROR: 'Authentication failed. Please log in again.',
    RATE_LIMIT_ERROR: 'Too many requests. Please wait before trying again.',
    VALIDATION_ERROR: 'Invalid data provided. Please check your input.',
    NOT_FOUND_ERROR: 'Resource not found.',
    PERMISSION_ERROR: 'You do not have permission to perform this action.',
    PRESCRIPTION_PROCESSING_ERROR: 'Error processing prescription. Please try again.',
    OCR_PROCESSING_ERROR: 'Error processing image. Please try again.',
    ENCRYPTION_ERROR: 'Error encrypting data. Please try again.',
    CACHE_ERROR: 'Cache error. Please try again.',
  },
} as const

// Rate limiting configurations
export const RATE_LIMIT_CONFIG = {
  // Rate limit headers
  HEADERS: {
    REMAINING: 'X-RateLimit-Remaining',
    RESET: 'X-RateLimit-Reset',
    LIMIT: 'X-RateLimit-Limit',
  },
  
  // Rate limit strategies
  STRATEGIES: {
    TOKEN_BUCKET: 'token-bucket',
    LEAKY_BUCKET: 'leaky-bucket',
    FIXED_WINDOW: 'fixed-window',
    SLIDING_WINDOW: 'sliding-window',
  },
  
  // Default rate limits
  DEFAULTS: {
    WINDOW_SIZE: 60 * 1000, // 1 minute
    MAX_REQUESTS: 100,
    BURST_LIMIT: 20,
  },
} as const

// Caching configurations
export const CACHE_CONFIG = {
  // Cache strategies
  STRATEGIES: {
    MEMORY: 'memory',
    SESSION_STORAGE: 'session-storage',
    LOCAL_STORAGE: 'local-storage',
    INDEXED_DB: 'indexed-db',
  },
  
  // Cache keys
  KEYS: {
    PRESCRIPTIONS: 'prescriptions',
    MEDICATIONS: 'medications',
    USER_PROFILE: 'user-profile',
    OCR_RESULTS: 'ocr-results',
    DRUG_DATABASE: 'drug-database',
    INTERACTIONS: 'interactions',
  },
  
  // Default TTL values (in milliseconds)
  TTL: {
    PRESCRIPTIONS: 5 * 60 * 1000, // 5 minutes
    MEDICATIONS: 10 * 60 * 1000, // 10 minutes
    USER_PROFILE: 30 * 60 * 1000, // 30 minutes
    OCR_RESULTS: 2 * 60 * 1000, // 2 minutes
    DRUG_DATABASE: 24 * 60 * 60 * 1000, // 24 hours
    INTERACTIONS: 60 * 60 * 1000, // 1 hour
  },
} as const

// Encryption configurations
export const ENCRYPTION_CONFIG = {
  // Encryption algorithms
  ALGORITHMS: {
    AES_256_GCM: 'AES-256-GCM',
    AES_256_CBC: 'AES-256-CBC',
    CHACHA20_POLY1305: 'ChaCha20-Poly1305',
  },
  
  // Key management
  KEY_MANAGEMENT: {
    ROTATION_INTERVAL: 24 * 60 * 60 * 1000, // 24 hours
    KEY_SIZE: 256,
    IV_SIZE: 12,
    TAG_SIZE: 16,
  },
  
  // Sensitive data fields
  SENSITIVE_FIELDS: [
    'patient_name',
    'patient_id',
    'prescriber_name',
    'prescriber_id',
    'medication_name',
    'dosage',
    'frequency',
    'duration',
    'notes',
    'diagnosis',
  ],
} as const

// Monitoring configurations
export const MONITORING_CONFIG = {
  // Metrics to track
  METRICS: {
    API_CALLS: 'api_calls',
    RESPONSE_TIME: 'response_time',
    ERROR_RATE: 'error_rate',
    CACHE_HIT_RATE: 'cache_hit_rate',
    RATE_LIMIT_HITS: 'rate_limit_hits',
    ENCRYPTION_OPERATIONS: 'encryption_operations',
    OCR_PROCESSING_TIME: 'ocr_processing_time',
    PRESCRIPTION_PROCESSING_TIME: 'prescription_processing_time',
  },
  
  // Alert thresholds
  ALERTS: {
    HIGH_ERROR_RATE: 0.05, // 5%
    HIGH_RESPONSE_TIME: 5000, // 5 seconds
    LOW_CACHE_HIT_RATE: 0.7, // 70%
    HIGH_RATE_LIMIT_HITS: 0.1, // 10%
  },
  
  // Sampling rates
  SAMPLING: {
    DEFAULT: 0.1, // 10%
    HIGH_TRAFFIC: 0.05, // 5%
    LOW_TRAFFIC: 0.2, // 20%
    CRITICAL: 1.0, // 100%
  },
} as const

// Helper functions
export const shouldUseRealApi = (): boolean => {
  return !apiConfig.useMockData
}

export const getApiUrl = (endpoint: string, version: 'v1' | 'v2' = 'v1'): string => {
  return `${apiConfig.baseURL}${endpoint}`
}

export const getBackupApiUrl = (endpoint: string, backupIndex: number = 0): string => {
  const backupUrl = apiConfig.backupURLs[backupIndex] || apiConfig.baseURL
  return `${backupUrl}${endpoint}`
}

export const getTimeout = (operation: keyof ApiConfig['timeout']): number => {
  return apiConfig.timeout[operation]
}

export const shouldRetry = (statusCode: number): boolean => {
  const retryableCodes = [
    ERROR_CONFIG.STATUS_CODES.INTERNAL_SERVER_ERROR,
    ERROR_CONFIG.STATUS_CODES.BAD_GATEWAY,
    ERROR_CONFIG.STATUS_CODES.SERVICE_UNAVAILABLE,
    ERROR_CONFIG.STATUS_CODES.GATEWAY_TIMEOUT,
  ]
  return retryableCodes.includes(statusCode as any)
}

export const getRetryConfig = (errorType: keyof typeof ERROR_CONFIG.RETRY_CONFIG) => {
  return ERROR_CONFIG.RETRY_CONFIG[errorType]
}

export const isSensitiveField = (fieldName: string): boolean => {
  return ENCRYPTION_CONFIG.SENSITIVE_FIELDS.includes(fieldName as any)
}

export const getCacheKey = (baseKey: string, params?: Record<string, any>): string => {
  if (!params) return baseKey
  const paramString = Object.entries(params)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([key, value]) => `${key}:${value}`)
    .join('|')
  return `${baseKey}:${paramString}`
}

export const getCacheTTL = (cacheType: keyof typeof CACHE_CONFIG.TTL): number => {
  return CACHE_CONFIG.TTL[cacheType]
}

// Development utilities
export const devUtils = {
  // Log API calls in development
  logApiCall: (method: string, url: string, data?: any, headers?: Record<string, string>) => {
    if (apiConfig.enableLogging) {
      console.group(`🌐 API Call: ${method} ${url}`)
      if (headers) console.log('Headers:', headers)
      if (data) console.log('Data:', data)
      console.groupEnd()
    }
  },
  
  // Log API responses in development
  logApiResponse: (method: string, url: string, response: any, duration: number) => {
    if (apiConfig.enableLogging) {
      console.group(`✅ API Response: ${method} ${url} (${duration}ms)`)
      console.log('Response:', response)
      console.groupEnd()
    }
  },
  
  // Log API errors in development
  logApiError: (method: string, url: string, error: any, retryAttempt?: number) => {
    if (apiConfig.enableLogging) {
      console.group(`❌ API Error: ${method} ${url}${retryAttempt ? ` (Attempt ${retryAttempt})` : ''}`)
      console.error('Error:', error)
      console.groupEnd()
    }
  },
  
  // Log cache operations
  logCacheOperation: (operation: 'get' | 'set' | 'delete', key: string, hit?: boolean) => {
    if (apiConfig.enableLogging) {
      const icon = operation === 'get' ? (hit ? '🎯' : '💾') : operation === 'set' ? '💾' : '🗑️'
      console.log(`${icon} Cache ${operation}: ${key}${hit !== undefined ? ` (${hit ? 'HIT' : 'MISS'})` : ''}`)
    }
  },
  
  // Log encryption operations
  logEncryptionOperation: (operation: 'encrypt' | 'decrypt', field: string, success: boolean) => {
    if (apiConfig.enableLogging) {
      const icon = success ? '🔐' : '⚠️'
      console.log(`${icon} Encryption ${operation}: ${field} (${success ? 'SUCCESS' : 'FAILED'})`)
    }
  },
  
  // Log rate limiting
  logRateLimit: (endpoint: string, remaining: number, reset: number) => {
    if (apiConfig.enableLogging) {
      console.log(`⏱️ Rate Limit: ${endpoint} - ${remaining} requests remaining, resets at ${new Date(reset).toISOString()}`)
    }
  },
  
  // Log monitoring metrics
  logMetric: (metric: string, value: number, tags?: Record<string, string>) => {
    if (apiConfig.enableLogging) {
      const tagString = tags ? ` [${Object.entries(tags).map(([k, v]) => `${k}=${v}`).join(', ')}]` : ''
      console.log(`📊 Metric: ${metric} = ${value}${tagString}`)
    }
  },
}

// Export all configurations for use in other modules
export default {
  apiConfig,
  API_ENDPOINTS,
  ERROR_CONFIG,
  RATE_LIMIT_CONFIG,
  CACHE_CONFIG,
  ENCRYPTION_CONFIG,
  MONITORING_CONFIG,
  shouldUseRealApi,
  getApiUrl,
  getBackupApiUrl,
  getTimeout,
  shouldRetry,
  getRetryConfig,
  isSensitiveField,
  getCacheKey,
  getCacheTTL,
  devUtils,
} 