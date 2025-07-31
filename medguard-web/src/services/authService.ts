import axios from 'axios'
import { ref, computed } from 'vue'

// Types for authentication
export interface User {
  id: string
  email: string
  name: string
  userType: 'PATIENT' | 'CAREGIVER' | 'HEALTHCARE_PROVIDER'
  permissions: string[]
  lastLogin: string
  mfaEnabled: boolean
  avatarUrl?: string // Add avatar URL support
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresAt: number
}

export interface LoginCredentials {
  email: string  // Can be email or username
  password: string
  mfaCode?: string
}

// HIPAA Security Configuration
const SECURITY_CONFIG = {
  // Token expiration times (in milliseconds)
  ACCESS_TOKEN_EXPIRY: 15 * 60 * 1000, // 15 minutes
  REFRESH_TOKEN_EXPIRY: 7 * 24 * 60 * 60 * 1000, // 7 days
  
  // Session timeout (in milliseconds)
  SESSION_TIMEOUT: 30 * 60 * 1000, // 30 minutes of inactivity
  
  // Encryption key derivation
  PBKDF2_ITERATIONS: 100000,
  SALT_LENGTH: 32,
  
  // Secure storage keys
  STORAGE_KEYS: {
    ENCRYPTED_TOKENS: 'medguard_encrypted_tokens',
    SESSION_DATA: 'medguard_session_data',
    DEVICE_ID: 'medguard_device_id',
    SECURITY_SETTINGS: 'medguard_security_settings'
  }
}

class HIPAACompliantAuthService {
  private user = ref<User | null>(null)
  private isAuthenticated = ref(false)
  private isLoading = ref(false)
  private lastActivity = ref<number>(Date.now())
  private sessionTimer: number | null = null
  private deviceId: string | null = null
  private currentInterceptorId: number | null = null

  // Computed properties
  public readonly currentUser = computed(() => this.user.value)
  public readonly authenticated = computed(() => this.isAuthenticated.value)
  public readonly loading = computed(() => this.isLoading.value)

  constructor() {
    this.initializeSecurity()
    this.setupActivityMonitoring()
    this.setupSessionTimeout()
  }

  /**
   * Initialize security settings and device identification
   */
  private async initializeSecurity(): Promise<void> {
    try {
      // Generate or retrieve device ID
      this.deviceId = await this.getOrCreateDeviceId()
      
      // Check for existing session with a small delay to ensure Vite proxy is ready
      setTimeout(async () => {
        await this._restoreSession()
      }, 100)
      
      // Setup security headers
      this.setupSecurityHeaders()
    } catch (error) {
      console.error('Failed to initialize security:', error)
      this.clearSession()
    }
  }

  /**
   * Generate or retrieve device ID for security tracking
   */
  private async getOrCreateDeviceId(): Promise<string> {
    let deviceId = localStorage.getItem(SECURITY_CONFIG.STORAGE_KEYS.DEVICE_ID)
    
    if (!deviceId) {
      // Generate a unique device ID
      deviceId = this.generateDeviceId()
      localStorage.setItem(SECURITY_CONFIG.STORAGE_KEYS.DEVICE_ID, deviceId)
    }
    
    return deviceId
  }

  /**
   * Generate a unique device identifier
   */
  private generateDeviceId(): string {
    const timestamp = Date.now().toString(36)
    const random = Math.random().toString(36).substring(2)
    const userAgent = navigator.userAgent.substring(0, 10)
    const screenInfo = `${screen.width}x${screen.height}`
    
    return `${timestamp}-${random}-${userAgent}-${screenInfo}`
  }

  /**
   * Setup security headers for all API requests
   */
  private setupSecurityHeaders(): void {
    // Add security headers to axios defaults
    axios.defaults.headers.common['X-Device-ID'] = this.deviceId
    axios.defaults.headers.common['X-Client-Version'] = '1.0.0'
    axios.defaults.headers.common['X-Security-Level'] = 'HIPAA'
  }

  /**
   * Setup activity monitoring for session timeout
   */
  private setupActivityMonitoring(): void {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
    
    events.forEach(event => {
      document.addEventListener(event, () => {
        this.lastActivity.value = Date.now()
      }, true)
    })
  }

  /**
   * Setup session timeout monitoring
   */
  private setupSessionTimeout(): void {
    const checkSession = () => {
      const timeSinceLastActivity = Date.now() - this.lastActivity.value
      
      if (timeSinceLastActivity > SECURITY_CONFIG.SESSION_TIMEOUT) {
        this.handleSessionTimeout()
      }
    }

    // Check every minute
    this.sessionTimer = window.setInterval(checkSession, 60000)
  }

  /**
   * Handle session timeout
   */
  private handleSessionTimeout(): void {
    console.warn('Session timeout detected - logging out for security')
    this.logout('Session timeout due to inactivity')
  }

  /**
   * Encrypt sensitive data using Web Crypto API
   */
  private async encryptData(data: string): Promise<string> {
    try {
      const encoder = new TextEncoder()
      const dataBuffer = encoder.encode(data)
      
      // Generate a random key
      const key = await crypto.subtle.generateKey(
        {
          name: 'AES-GCM',
          length: 256
        },
        true,
        ['encrypt', 'decrypt']
      )
      
      // Generate random IV
      const iv = crypto.getRandomValues(new Uint8Array(12))
      
      // Encrypt the data
      const encryptedBuffer = await crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        dataBuffer
      )
      
      // Export the key
      const exportedKey = await crypto.subtle.exportKey('raw', key)
      
      // Combine IV, key, and encrypted data
      const combined = new Uint8Array(iv.length + exportedKey.byteLength + encryptedBuffer.byteLength)
      combined.set(iv, 0)
      combined.set(new Uint8Array(exportedKey), iv.length)
      combined.set(new Uint8Array(encryptedBuffer), iv.length + exportedKey.byteLength)
      
      return btoa(String.fromCharCode(...combined))
    } catch (error) {
      console.error('Encryption failed:', error)
      throw new Error('Failed to encrypt sensitive data')
    }
  }

  /**
   * Decrypt sensitive data using Web Crypto API
   */
  private async decryptData(encryptedData: string): Promise<string> {
    try {
      const combined = new Uint8Array(
        atob(encryptedData).split('').map(char => char.charCodeAt(0))
      )
      
      // Extract IV, key, and encrypted data
      const iv = combined.slice(0, 12)
      const keyData = combined.slice(12, 44) // 32 bytes for AES-256
      const encryptedBuffer = combined.slice(44)
      
      // Import the key
      const key = await crypto.subtle.importKey(
        'raw',
        keyData,
        {
          name: 'AES-GCM',
          length: 256
        },
        false,
        ['decrypt']
      )
      
      // Decrypt the data
      const decryptedBuffer = await crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv
        },
        key,
        encryptedBuffer
      )
      
      const decoder = new TextDecoder()
      return decoder.decode(decryptedBuffer)
    } catch (error) {
      console.error('Decryption failed:', error)
      throw new Error('Failed to decrypt sensitive data')
    }
  }

  /**
   * Securely store authentication tokens
   */
  private async storeTokens(tokens: AuthTokens): Promise<void> {
    try {
      const encryptedTokens = await this.encryptData(JSON.stringify(tokens))
      localStorage.setItem(SECURITY_CONFIG.STORAGE_KEYS.ENCRYPTED_TOKENS, encryptedTokens)
    } catch (error) {
      console.error('Failed to store tokens:', error)
      throw new Error('Failed to securely store authentication tokens')
    }
  }

  /**
   * Securely retrieve authentication tokens
   */
  private async getStoredTokens(): Promise<AuthTokens | null> {
    try {
      const encryptedTokens = localStorage.getItem(SECURITY_CONFIG.STORAGE_KEYS.ENCRYPTED_TOKENS)
      if (!encryptedTokens) return null
      
      const decryptedTokens = await this.decryptData(encryptedTokens)
      return JSON.parse(decryptedTokens)
    } catch (error) {
      console.error('Failed to retrieve tokens:', error)
      this.clearSession()
      return null
    }
  }

  /**
   * Fetch full user profile including avatar
   */
  public async fetchUserProfile(): Promise<User | null> {
    try {
      const accessToken = await this.getAccessToken()
      if (!accessToken) {
        console.log('fetchUserProfile: No access token available')
        return null
      }

      console.log('fetchUserProfile: Making request to /api/users/profile/me/')
      const response = await fetch('/api/users/profile/me/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      })

      console.log('fetchUserProfile: Response status:', response.status)
      if (!response.ok) {
        console.warn('Failed to fetch user profile:', response.status)
        return null
      }

      const profileData = await response.json()
      console.log('fetchUserProfile: Raw profile data:', profileData)
      console.log('fetchUserProfile: avatar_url field:', profileData.avatar_url)
      
      // Update user with full profile data including avatar
      const updatedUser: User = {
        id: profileData.id.toString(),
        email: profileData.email,
        name: `${profileData.first_name || ''} ${profileData.last_name || ''}`.trim() || profileData.username,
        userType: profileData.user_type,
        permissions: profileData.permissions || [],
        lastLogin: profileData.last_login || new Date().toISOString(),
        mfaEnabled: profileData.mfa_enabled || false,
        avatarUrl: profileData.avatar_url || undefined
      }

      console.log('fetchUserProfile: Updated user object:', updatedUser)
      console.log('fetchUserProfile: Final avatarUrl:', updatedUser.avatarUrl)

      this.user.value = updatedUser
      return updatedUser
    } catch (error) {
      console.error('Error fetching user profile:', error)
      return null
    }
  }

  /**
   * Refresh user profile (public method for components to call)
   */
  public async refreshUserProfile(): Promise<User | null> {
    return this.fetchUserProfile()
  }

  /**
   * Public method to restore session (for router guards)
   */
  public async restoreSession(): Promise<void> {
    return this._restoreSession()
  }

  /**
   * Login with security compliance
   */
  public async login(credentials: LoginCredentials): Promise<User> {
    try {
      this.isLoading.value = true
      
      // Validate input
      if (!credentials.email || !credentials.password) {
        throw new Error('Email/Username and password are required')
      }
      
      // Prepare login payload with security metadata
      const loginPayload = {
        email: credentials.email, // Send email field directly
        password: credentials.password,
        mfaCode: credentials.mfaCode,
        deviceId: this.deviceId,
        clientVersion: '1.0.0',
        timestamp: Date.now()
      }
      
      // Use native fetch API for login to completely avoid any axios-related issues
      // This ensures no global configurations, interceptors, or authentication headers interfere
      const response = await fetch('/api/users/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Device-ID': this.deviceId || 'unknown',
          'X-Security-Level': 'HIPAA'
        },
        body: JSON.stringify(loginPayload),
        // Explicitly disable credentials to prevent any authentication headers
        credentials: 'omit'
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error || `Login failed with status ${response.status}`)
      }
      
      const responseData = await response.json()
      console.log('Login response data:', responseData)
      
      const { user, access_token, refresh_token, expires_in } = responseData
      
      // Create tokens object in the expected format
      const tokens: AuthTokens = {
        accessToken: access_token,
        refreshToken: refresh_token,
        expiresAt: Date.now() + (expires_in * 1000) // Convert seconds to milliseconds
      }
      
      // Store tokens securely
      await this.storeTokens(tokens)
      
      // Set user and authentication state
      this.user.value = {
        id: user.id.toString(),
        email: user.email,
        name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username,
        userType: user.user_type,
        permissions: user.permissions || [],
        lastLogin: user.last_login || new Date().toISOString(),
        mfaEnabled: user.mfa_enabled || false,
        avatarUrl: user.avatar_url || undefined
      }
      
      console.log('Login: Initial user object set:', this.user.value)
      this.isAuthenticated.value = true
      this.lastActivity.value = Date.now()
      
      // Setup API interceptors with new tokens
      this.setupApiInterceptors(tokens.accessToken)
      
      // Fetch full user profile including avatar
      try {
        await this.fetchUserProfile()
      } catch (profileError) {
        console.warn('Failed to fetch full profile, using basic user data:', profileError)
      }
      
      // Log security event (don't let logging failures affect login)
      try {
        this.logSecurityEvent('LOGIN_SUCCESS', { 
          userId: user.id, 
          deviceId: this.deviceId,
          email: credentials.email,
          userAgent: navigator.userAgent
        })
      } catch (loggingError) {
        console.warn('Security logging failed, but login succeeded:', loggingError)
      }
      
      return this.user.value
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      // Log security event (don't let logging failures affect error handling)
      try {
        this.logSecurityEvent('LOGIN_FAILURE', { 
          email: credentials.email, 
          deviceId: this.deviceId,
          error: errorMessage 
        })
      } catch (loggingError) {
        console.warn('Security logging failed for login failure:', loggingError)
      }
      throw error
    } finally {
      this.isLoading.value = false
    }
  }

  /**
   * Logout with security cleanup
   */
  public async logout(reason: string = 'User initiated logout'): Promise<void> {
    // Store user info before clearing session
    const userId = this.user.value?.id
    const deviceId = this.deviceId
    
    try {
      // Try to call logout endpoint to invalidate tokens (optional)
      if (this.user.value) {
        try {
          const token = await this.getAccessToken()
          if (token) {
            await axios.post('/api/users/auth/logout/', {
              deviceId: this.deviceId
            }, {
              headers: {
                'Authorization': `Bearer ${token}`
              },
              timeout: 3000 // Short timeout for logout
            })
          }
        } catch (error) {
          // Log the error but don't fail the logout process
          console.warn('Logout endpoint call failed (this is normal if token is expired):', error)
        }
      }
      
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      this.clearSession()
      
      // Log security event AFTER clearing session to ensure no authentication interference
      try {
        this.logSecurityEvent('LOGOUT', { 
          userId: userId, 
          deviceId: deviceId,
          reason 
        })
      } catch (loggingError) {
        console.warn('Security logging failed during logout:', loggingError)
      }
    }
  }

  /**
   * Clear session and sensitive data
   */
  private clearSession(): void {
    this.user.value = null
    this.isAuthenticated.value = false
    this.lastActivity.value = 0
    
    // Clear stored tokens
    localStorage.removeItem(SECURITY_CONFIG.STORAGE_KEYS.ENCRYPTED_TOKENS)
    localStorage.removeItem(SECURITY_CONFIG.STORAGE_KEYS.SESSION_DATA)
    
    // Clear all axios global configurations and interceptors
    this.clearAxiosConfigurations()
    
    // Clear any cached data that might persist
    this.clearBrowserCache()
    
    // Force a complete reset of the authentication state
    this.forceAuthenticationReset()
  }

  /**
   * Force a complete reset of the authentication system
   */
  private forceAuthenticationReset(): void {
    try {
      // Clear any remaining authentication state
      this.currentInterceptorId = null
      
      // Force garbage collection if available (browser only)
      if (typeof window !== 'undefined' && 'gc' in window) {
        (window as any).gc()
      }
      
      // Reset any timers
      if (this.sessionTimer) {
        clearInterval(this.sessionTimer)
        this.sessionTimer = null
      }
      
      console.log('Authentication system completely reset')
    } catch (error) {
      console.warn('Error during authentication reset:', error)
    }
  }

  /**
   * Clear all axios configurations and interceptors
   */
  private clearAxiosConfigurations(): void {
    // Remove all authorization headers
    delete axios.defaults.headers.common['Authorization']
    delete axios.defaults.headers.common['X-CSRFToken']
    
    // Clear specific interceptor if it exists
    if (this.currentInterceptorId !== null && axios.interceptors.response) {
      axios.interceptors.response.eject(this.currentInterceptorId)
      this.currentInterceptorId = null
    }
    
    // Clear any request interceptors that might have been added
    if (axios.interceptors.request) {
      axios.interceptors.request.clear()
    }
    
    // Clear any response interceptors that might have been added
    if (axios.interceptors.response) {
      axios.interceptors.response.clear()
    }
    
    // Reset axios defaults to prevent persistence
    axios.defaults.headers.common = {}
    axios.defaults.headers.post = {}
    axios.defaults.headers.put = {}
    axios.defaults.headers.patch = {}
    axios.defaults.headers.delete = {}
    
    // Re-setup security headers (these are safe to keep)
    if (this.deviceId) {
      axios.defaults.headers.common['X-Device-ID'] = this.deviceId
      axios.defaults.headers.common['X-Client-Version'] = '1.0.0'
      axios.defaults.headers.common['X-Security-Level'] = 'HIPAA'
    }
    
    console.log('Axios configurations cleared successfully')
  }



  /**
   * Clear browser cache and storage that might persist authentication
   */
  private clearBrowserCache(): void {
    try {
      // Clear session storage
      sessionStorage.clear()
      
      // Clear any cached API responses
      if ('caches' in window) {
        caches.keys().then(cacheNames => {
          cacheNames.forEach(cacheName => {
            if (cacheName.includes('api') || cacheName.includes('auth')) {
              caches.delete(cacheName)
            }
          })
        })
      }
      
      // Clear any service worker caches
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(registrations => {
          registrations.forEach(registration => {
            registration.unregister()
          })
        })
      }
      
      // Clear any localStorage items that might contain auth data
      const keysToRemove = []
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && (key.includes('auth') || key.includes('token') || key.includes('session'))) {
          keysToRemove.push(key)
        }
      }
      keysToRemove.forEach(key => localStorage.removeItem(key))
      
      console.log('Browser cache and storage cleared successfully')
    } catch (error) {
      console.warn('Error clearing browser cache:', error)
    }
  }

  /**
   * Restore session from stored tokens
   */
  private async _restoreSession(): Promise<void> {
    try {
      const tokens = await this.getStoredTokens()
      if (!tokens) return
      
      // Check if tokens are expired
      if (Date.now() > tokens.expiresAt) {
        // Try to refresh tokens
        await this.refreshTokens(tokens.refreshToken)
        return
      }
      
      // Validate tokens with server
      const response = await fetch('/api/users/auth/validate/', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${tokens.accessToken}`,
          'X-Device-ID': this.deviceId || 'unknown'
        },
        credentials: 'omit'
      })
      
      if (!response.ok) {
        throw new Error(`Token validation failed with status ${response.status}`)
      }
      
      const responseData = await response.json()
      const user = responseData.user
      this.user.value = {
        id: user.id.toString(),
        email: user.email,
        name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.username,
        userType: user.user_type,
        permissions: user.permissions || [],
        lastLogin: user.last_login || new Date().toISOString(),
        mfaEnabled: user.mfa_enabled || false
      }
      this.isAuthenticated.value = true
      this.setupApiInterceptors(tokens.accessToken)
      
      // Fetch full user profile including avatar
      try {
        await this.fetchUserProfile()
      } catch (profileError) {
        console.warn('Failed to fetch full profile during session restore:', profileError)
      }
      
    } catch (error) {
      console.error('Failed to restore session:', error)
      this.clearSession()
    }
  }

  /**
   * Refresh authentication tokens
   */
  private async refreshTokens(refreshToken: string): Promise<void> {
    try {
      const response = await fetch('/api/users/auth/refresh/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Device-ID': this.deviceId || 'unknown'
        },
        body: JSON.stringify({
          refresh: refreshToken, // Django expects 'refresh' field
          deviceId: this.deviceId
        }),
        credentials: 'omit'
      })
      
      if (!response.ok) {
        throw new Error(`Token refresh failed with status ${response.status}`)
      }
      
      const responseData = await response.json()
      const { access } = responseData
      
      // Get current tokens to update access token
      const currentTokens = await this.getStoredTokens()
      if (currentTokens) {
        const updatedTokens: AuthTokens = {
          ...currentTokens,
          accessToken: access,
          expiresAt: Date.now() + (15 * 60 * 1000) // 15 minutes from now
        }
        await this.storeTokens(updatedTokens)
        this.setupApiInterceptors(access)
      }
      
    } catch (error) {
      console.error('Token refresh failed:', error)
      this.clearSession()
      throw new Error('Session expired. Please login again.')
    }
  }

  /**
   * Get current access token
   */
  public async getAccessToken(): Promise<string | null> {
    try {
      const tokens = await this.getStoredTokens()
      if (!tokens) return null
      
      // Check if token is expired
      if (Date.now() > tokens.expiresAt) {
        await this.refreshTokens(tokens.refreshToken)
        const newTokens = await this.getStoredTokens()
        return newTokens?.accessToken || null
      }
      
      return tokens.accessToken
    } catch (error) {
      console.error('Failed to get access token:', error)
      return null
    }
  }

  /**
   * Setup API interceptors for automatic token handling
   */
  private setupApiInterceptors(accessToken: string): void {
    // Clear any existing interceptors first to prevent duplicates
    if (axios.interceptors.response) {
      axios.interceptors.response.clear()
    }
    
    // Set authorization header
    axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
    
    // Add response interceptor for token refresh
    const interceptorId = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        // Only handle 401 errors if we're still authenticated
        if (error.response?.status === 401 && this.isAuthenticated.value) {
          try {
            const tokens = await this.getStoredTokens()
            if (tokens?.refreshToken) {
              await this.refreshTokens(tokens.refreshToken)
              // Retry the original request
              const newToken = await this.getAccessToken()
              if (newToken) {
                error.config.headers['Authorization'] = `Bearer ${newToken}`
                return axios.request(error.config)
              }
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError)
            this.clearSession()
          }
        }
        return Promise.reject(error)
      }
    )
    
    // Store the interceptor ID for potential cleanup
    this.currentInterceptorId = interceptorId
  }

  /**
   * Log security events for audit trail
   */
  public logSecurityEvent(eventType: string, data: any): void {
    try {
      const securityEvent = {
        eventType,
        timestamp: new Date().toISOString(),
        deviceId: this.deviceId,
        userId: this.user.value?.id,
        userAgent: navigator.userAgent,
        ipAddress: 'client-side', // Will be captured server-side
        data
      }
      
      // Always use public endpoint for security logging to avoid authentication issues
      const endpoint = '/api/security/log-public/'
      
      console.log(`Logging security event: ${eventType} to ${endpoint}`)
      
      // Use native fetch API instead of axios to completely avoid any axios-related issues
      // This ensures no global configurations, interceptors, or authentication headers interfere
      fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Device-ID': this.deviceId || 'unknown',
          'X-Client-Version': '1.0.0',
          'X-Security-Level': 'HIPAA'
        },
        body: JSON.stringify(securityEvent),
        // Explicitly disable credentials to prevent any authentication headers
        credentials: 'omit'
      })
      .then(response => {
        if (response.ok) {
          console.log(`Security event logged successfully: ${eventType}`)
        } else {
          console.warn(`Security logging returned status ${response.status}: ${response.statusText}`)
        }
      })
      .catch(error => {
        console.error(`Failed to log security event ${eventType}:`, error)
        // Don't throw the error to prevent login failures due to logging issues
      })
    } catch (error) {
      console.error('Error preparing security event:', error)
      // Don't throw the error to prevent login failures due to logging issues
    }
  }

  /**
   * Check if user has required permissions
   */
  public hasPermission(permission: string): boolean {
    return this.user.value?.permissions.includes(permission) || false
  }

  /**
   * Check if user is of specific type
   */
  public isUserType(userType: User['userType']): boolean {
    return this.user.value?.userType === userType
  }

  /**
   * Get security settings
   */
  public getSecuritySettings(): any {
    return {
      sessionTimeout: SECURITY_CONFIG.SESSION_TIMEOUT,
      deviceId: this.deviceId,
      lastActivity: this.lastActivity.value,
      isAuthenticated: this.isAuthenticated.value
    }
  }
}

// Create singleton instance
const authService = new HIPAACompliantAuthService()

export default authService 