/**
 * API Configuration
 * 
 * This file manages API endpoints and configuration based on environment.
 * Provides a clean way to switch between development (mock) and production (real) APIs.
 */

import { environment } from './environment'

export interface ApiConfig {
  baseURL: string
  timeout: number
  useMockData: boolean
  enableLogging: boolean
  retryAttempts: number
  retryDelay: number
}

// Environment-based configuration
const getApiConfig = (): ApiConfig => {
  const isDevelopment = environment.IS_DEVELOPMENT
  const isProduction = environment.IS_PRODUCTION
  
  // You can override this with environment variables or the environment config
  const forceRealApi = environment.FORCE_REAL_API
  const apiBaseUrl = environment.API_BASE_URL
  
  return {
    baseURL: apiBaseUrl,
    timeout: 30000, // 30 seconds
    useMockData: isDevelopment && !forceRealApi, // Use mock data in development unless forced
    enableLogging: environment.ENABLE_API_LOGGING,
    retryAttempts: 3,
    retryDelay: 1000 // 1 second
  }
}

export const apiConfig = getApiConfig()

// API Endpoints
export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: '/api/users/auth/login/',
    LOGOUT: '/api/users/auth/logout/',
    REFRESH: '/api/users/auth/refresh/',
    VALIDATE: '/api/users/auth/validate/',
    PROFILE: '/api/users/profile/me/',
  },
  
  // Medications
  MEDICATIONS: {
    LIST: '/api/medications/',
    DETAIL: (id: string) => `/api/medications/${id}/`,
    CREATE: '/api/medications/',
    UPDATE: (id: string) => `/api/medications/${id}/`,
    DELETE: (id: string) => `/api/medications/${id}/`,
    SCHEDULE: '/api/medications/schedules/',
    LOGS: '/api/medications/logs/',
    ALERTS: '/api/medications/alerts/',
    ANALYTICS: (id: string) => `/api/medications/${id}/analytics/`,
  },
  
  // Notifications
  NOTIFICATIONS: {
    LIST: '/api/notifications/',
    MARK_READ: (id: string) => `/api/notifications/${id}/mark-read/`,
  },
  
  // Security
  SECURITY: {
    EVENTS: '/api/security/events/',
    SETTINGS: '/api/security/settings/',
  }
} as const

// Helper function to check if we should use real API
export const shouldUseRealApi = (): boolean => {
  return !apiConfig.useMockData
}

// Helper function to get full API URL
export const getApiUrl = (endpoint: string): string => {
  return `${apiConfig.baseURL}${endpoint}`
}

// Development utilities
export const devUtils = {
  // Log API calls in development
  logApiCall: (method: string, url: string, data?: any) => {
    if (apiConfig.enableLogging) {
      console.group(`🌐 API Call: ${method} ${url}`)
      if (data) console.log('Data:', data)
      console.groupEnd()
    }
  },
  
  // Log API responses in development
  logApiResponse: (method: string, url: string, response: any) => {
    if (apiConfig.enableLogging) {
      console.group(`✅ API Response: ${method} ${url}`)
      console.log('Response:', response)
      console.groupEnd()
    }
  },
  
  // Log API errors in development
  logApiError: (method: string, url: string, error: any) => {
    if (apiConfig.enableLogging) {
      console.group(`❌ API Error: ${method} ${url}`)
      console.error('Error:', error)
      console.groupEnd()
    }
  }
} 