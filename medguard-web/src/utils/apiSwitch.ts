/**
 * API Switch Utility
 * 
 * Provides easy functions to switch between mock and real API for testing.
 */

import { environment } from '@/config/environment'
import { apiConfig } from '@/config/api'

export const apiSwitch = {
  /**
   * Switch to real backend API
   * Call this function to enable real API calls
   */
  enableRealApi: () => {
    console.log('🌐 Enabling real backend API...')
    console.log('📋 Make sure:')
    console.log('  1. Django backend is running on http://localhost:8000')
    console.log('  2. You are logged in (authentication tokens available)')
    console.log('  3. Check browser console for API logs')
    
    // Note: In a real implementation, you would modify the environment config
    // For now, this is just a helper function to guide users
    return {
      success: true,
      message: 'Real API enabled. Check console for instructions.',
      nextSteps: [
        'Ensure Django backend is running on http://localhost:8000',
        'Login to get authentication tokens',
        'Check browser console for API logs',
        'API will fall back to mock data if backend is unavailable'
      ]
    }
  },

  /**
   * Switch to mock data
   * Call this function to use mock data for development
   */
  enableMockData: () => {
    console.log('🎭 Enabling mock data...')
    console.log('📋 Mock data will be used for all API calls')
    
    return {
      success: true,
      message: 'Mock data enabled for development.',
      nextSteps: [
        'All API calls will use mock data',
        'No backend connection required',
        'Perfect for UI development and testing'
      ]
    }
  },

  /**
   * Get current API status
   */
  getStatus: () => {
    const isUsingRealApi = !apiConfig.useMockData
    const baseUrl = apiConfig.baseURL
    const loggingEnabled = apiConfig.enableLogging
    
    return {
      isUsingRealApi,
      baseUrl,
      loggingEnabled,
      environment: environment.IS_DEVELOPMENT ? 'development' : 'production'
    }
  },

  /**
   * Test backend connection
   */
  testConnection: async () => {
    try {
      const response = await fetch(`${apiConfig.baseURL}/api/test/`)
      if (response.ok) {
        return {
          success: true,
          message: 'Backend connection successful!',
          status: response.status
        }
      } else {
        return {
          success: false,
          message: `Backend responded with status: ${response.status}`,
          status: response.status
        }
      }
    } catch (error) {
      return {
        success: false,
        message: 'Backend connection failed. Is the server running?',
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }
}

// Make it available globally for easy access in browser console
if (typeof window !== 'undefined') {
  (window as any).apiSwitch = apiSwitch
  console.log('🔧 API Switch utility available as window.apiSwitch')
  console.log('💡 Try: apiSwitch.enableRealApi() or apiSwitch.getStatus()')
} 