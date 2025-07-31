/**
 * Enhanced API Client
 * 
 * Provides a robust HTTP client with:
 * - Automatic retry logic
 * - Request/response interceptors
 * - Authentication token management
 * - Error handling and logging
 * - Development vs production optimizations
 */

import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios'
import { apiConfig, API_ENDPOINTS, shouldUseRealApi, devUtils } from '@/config/api'
import authService from './authService'

// Custom error types
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public data?: any
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NetworkError extends Error {
  constructor(message: string, public originalError?: any) {
    super(message)
    this.name = 'NetworkError'
  }
}

// Retry configuration
interface RetryConfig {
  attempts: number
  delay: number
  backoff: number
}

const defaultRetryConfig: RetryConfig = {
  attempts: apiConfig.retryAttempts,
  delay: apiConfig.retryDelay,
  backoff: 2
}

// Create axios instance
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: apiConfig.baseURL,
    timeout: apiConfig.timeout,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Request interceptor
  client.interceptors.request.use(
    async (config) => {
      try {
        // Add authentication token
        const token = await authService.getAccessToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        // Add HIPAA security headers
        config.headers['X-Security-Level'] = 'HIPAA'
        config.headers['X-Client-Version'] = '1.0.0'
        config.headers['X-Request-Timestamp'] = Date.now().toString()
        
        // Log request in development
        devUtils.logApiCall(config.method?.toUpperCase() || 'GET', config.url || '', config.data)
        
        return config
      } catch (error) {
        console.error('Request interceptor error:', error)
        return config
      }
    },
    (error) => {
      devUtils.logApiError('REQUEST', 'unknown', error)
      return Promise.reject(error)
    }
  )

  // Response interceptor
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Log response in development
      devUtils.logApiResponse(
        response.config.method?.toUpperCase() || 'GET',
        response.config.url || '',
        response.data
      )
      
      // Log successful API calls for audit trail
      authService.logSecurityEvent('API_SUCCESS', {
        endpoint: response.config.url,
        method: response.config.method,
        statusCode: response.status
      })
      
      return response
    },
    async (error: AxiosError) => {
      const config = error.config
      const status = error.response?.status
      const url = config?.url || 'unknown'
      const method = config?.method?.toUpperCase() || 'GET'
      
      // Log error in development
      devUtils.logApiError(method, url, error)
      
      // Log failed API calls for security monitoring
      authService.logSecurityEvent('API_ERROR', {
        endpoint: url,
        method: method,
        statusCode: status,
        error: error.message
      })
      
      // Handle authentication errors
      if (status === 401) {
        console.error('Authentication error - attempting token refresh')
        try {
          // Try to get a new access token (this will trigger refresh internally)
          const token = await authService.getAccessToken()
          if (token && config) {
            config.headers.Authorization = `Bearer ${token}`
            return client(config)
          }
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
          await authService.logout('Token refresh failed')
          window.location.href = '/login'
          return Promise.reject(new ApiError('Authentication failed', 401))
        }
      }
      
      // Handle other HTTP errors
      if (error.response) {
        const apiError = new ApiError(
          (error.response.data as any)?.message || error.message,
          error.response.status,
          (error.response.data as any)?.code,
          error.response.data
        )
        return Promise.reject(apiError)
      }
      
      // Handle network errors
      if (error.request) {
        const networkError = new NetworkError(
          'Network error - please check your connection',
          error
        )
        return Promise.reject(networkError)
      }
      
      return Promise.reject(error)
    }
  )

  return client
}

// Retry wrapper function
const withRetry = async <T>(
  fn: () => Promise<T>,
  retryConfig: Partial<RetryConfig> = {}
): Promise<T> => {
  const config = { ...defaultRetryConfig, ...retryConfig }
  let lastError: Error
  
  for (let attempt = 1; attempt <= config.attempts; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error
      
      // Don't retry on certain errors
      if (error instanceof ApiError) {
        if (error.status >= 400 && error.status < 500) {
          // Client errors (4xx) should not be retried
          throw error
        }
      }
      
      if (attempt === config.attempts) {
        throw lastError
      }
      
      // Wait before retrying with exponential backoff
      const delay = config.delay * Math.pow(config.backoff, attempt - 1)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  throw lastError!
}

// API client instance
const apiClient = createApiClient()

// Enhanced API methods
export const apiClientEnhanced = {
  // GET request with retry
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return withRetry(async () => {
      const response = await apiClient.get<T>(url, config)
      return response.data
    })
  },

  // POST request with retry
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return withRetry(async () => {
      const response = await apiClient.post<T>(url, data, config)
      return response.data
    })
  },

  // PUT request with retry
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return withRetry(async () => {
      const response = await apiClient.put<T>(url, data, config)
      return response.data
    })
  },

  // PATCH request with retry
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return withRetry(async () => {
      const response = await apiClient.patch<T>(url, data, config)
      return response.data
    })
  },

  // DELETE request with retry
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return withRetry(async () => {
      const response = await apiClient.delete<T>(url, config)
      return response.data
    })
  },

  // Raw axios instance for advanced usage
  raw: apiClient
}

// Utility functions
export const apiUtils = {
  // Check if we should use real API
  shouldUseRealApi,
  
  // Get API URL
  getApiUrl: (endpoint: string) => `${apiConfig.baseURL}${endpoint}`,
  
  // Create error message for user display
  createErrorMessage: (error: Error): string => {
    if (error instanceof ApiError) {
      return error.message || 'An error occurred while processing your request'
    }
    if (error instanceof NetworkError) {
      return 'Network error - please check your connection and try again'
    }
    return 'An unexpected error occurred'
  },
  
  // Check if error is retryable
  isRetryableError: (error: Error): boolean => {
    if (error instanceof ApiError) {
      // Retry on server errors (5xx) and some client errors
      return error.status >= 500 || error.status === 429 // Too Many Requests
    }
    if (error instanceof NetworkError) {
      return true // Network errors are always retryable
    }
    return false
  }
}

export default apiClientEnhanced 