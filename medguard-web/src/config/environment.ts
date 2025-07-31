/**
 * Environment Configuration
 * 
 * This file provides easy configuration for switching between development and production modes.
 * You can modify these values to control API behavior.
 */

export const environment = {
  // Set to true to force using real backend API instead of mock data
  FORCE_REAL_API: true,
  
  // Backend API base URL
  API_BASE_URL: 'http://localhost:8000',
  
  // Enable detailed API logging
  ENABLE_API_LOGGING: true,
  
  // Development mode
  IS_DEVELOPMENT: import.meta.env.DEV,
  
  // Production mode
  IS_PRODUCTION: import.meta.env.PROD
}

// Instructions for switching to real API:
// 1. Set FORCE_REAL_API to true
// 2. Make sure your Django backend is running on http://localhost:8000
// 3. Ensure you're logged in to get authentication tokens
// 4. The API will automatically fall back to mock data if the backend is unavailable

export const switchToRealApi = () => {
  console.log('🌐 Switching to real backend API...')
  console.log('📋 Instructions:')
  console.log('1. Make sure Django backend is running on http://localhost:8000')
  console.log('2. Ensure you\'re logged in to get authentication tokens')
  console.log('3. Check browser console for API logs')
  console.log('4. API will fall back to mock data if backend is unavailable')
  
  // You can modify the environment object here or in the api.ts file
  // environment.FORCE_REAL_API = true
} 