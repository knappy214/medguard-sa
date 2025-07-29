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
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  expiresAt: number
}

export interface LoginCredentials {
  email: string
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
      
      // Check for existing session
      await this.restoreSession()
      
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
   * Login with HIPAA-compliant security measures
   */
  public async login(credentials: LoginCredentials): Promise<User> {
    try {
      this.isLoading.value = true
      
      // Validate input
      if (!credentials.email || !credentials.password) {
        throw new Error('Email and password are required')
      }
      
      // Prepare login payload with security metadata
      const loginPayload = {
        email: credentials.email,
        password: credentials.password,
        mfaCode: credentials.mfaCode,
        deviceId: this.deviceId,
        clientVersion: '1.0.0',
        timestamp: Date.now()
      }
      
      // Make login request
      const response = await axios.post('/api/auth/login/', loginPayload, {
        headers: {
          'Content-Type': 'application/json',
          'X-Device-ID': this.deviceId,
          'X-Security-Level': 'HIPAA'
        }
      })
      
      const { user, tokens } = response.data
      
      // Store tokens securely
      await this.storeTokens(tokens)
      
      // Set user and authentication state
      this.user.value = user
      this.isAuthenticated.value = true
      this.lastActivity.value = Date.now()
      
      // Setup API interceptors with new tokens
      this.setupApiInterceptors(tokens.accessToken)
      
      // Log security event
      this.logSecurityEvent('LOGIN_SUCCESS', { userId: user.id, deviceId: this.deviceId })
      
      return user
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
      this.logSecurityEvent('LOGIN_FAILURE', { 
        email: credentials.email, 
        deviceId: this.deviceId,
        error: errorMessage 
      })
      throw error
    } finally {
      this.isLoading.value = false
    }
  }

  /**
   * Logout with security cleanup
   */
  public async logout(reason: string = 'User initiated logout'): Promise<void> {
    try {
      // Log security event
      this.logSecurityEvent('LOGOUT', { 
        userId: this.user.value?.id, 
        deviceId: this.deviceId,
        reason 
      })
      
      // Call logout endpoint to invalidate tokens
      if (this.user.value) {
        await axios.post('/api/auth/logout/', {
          deviceId: this.deviceId
        }, {
          headers: {
            'Authorization': `Bearer ${await this.getAccessToken()}`
          }
        })
      }
    } catch (error) {
      console.error('Logout request failed:', error)
    } finally {
      this.clearSession()
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
    
    // Remove authorization header
    delete axios.defaults.headers.common['Authorization']
  }

  /**
   * Restore session from stored tokens
   */
  private async restoreSession(): Promise<void> {
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
      const response = await axios.get('/api/auth/validate/', {
        headers: {
          'Authorization': `Bearer ${tokens.accessToken}`,
          'X-Device-ID': this.deviceId
        }
      })
      
      this.user.value = response.data.user
      this.isAuthenticated.value = true
      this.setupApiInterceptors(tokens.accessToken)
      
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
      const response = await axios.post('/api/auth/refresh/', {
        refreshToken,
        deviceId: this.deviceId
      })
      
      const { tokens } = response.data
      await this.storeTokens(tokens)
      this.setupApiInterceptors(tokens.accessToken)
      
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
    // Set authorization header
    axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
    
    // Add response interceptor for token refresh
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
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
  }

  /**
   * Log security events for audit trail
   */
  public logSecurityEvent(eventType: string, data: any): void {
    const securityEvent = {
      eventType,
      timestamp: new Date().toISOString(),
      deviceId: this.deviceId,
      userId: this.user.value?.id,
      userAgent: navigator.userAgent,
      ipAddress: 'client-side', // Will be captured server-side
      data
    }
    
    // Send to security logging endpoint
    axios.post('/api/security/log/', securityEvent, {
      headers: {
        'Content-Type': 'application/json',
        'X-Device-ID': this.deviceId
      }
    }).catch(error => {
      console.error('Failed to log security event:', error)
    })
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