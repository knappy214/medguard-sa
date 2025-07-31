import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import authService, { type User, type LoginCredentials } from '@/services/authService'

export function useAuth() {
  const router = useRouter()
  
  // Reactive state
  const user = computed(() => authService.currentUser.value)
  const isAuthenticated = computed(() => authService.authenticated.value)
  const isLoading = computed(() => authService.loading.value)
  
  // Login function
  const login = async (credentials: LoginCredentials) => {
    try {
      const user = await authService.login(credentials)
      router.push('/dashboard')
      return user
    } catch (error) {
      throw error
    }
  }
  
  // Logout function
  const logout = async (reason?: string) => {
    try {
      await authService.logout(reason)
      router.push('/login')
    } catch (error) {
      console.error('Logout error:', error)
      // Force redirect even if logout fails
      router.push('/login')
    }
  }
  
  // Check permissions
  const hasPermission = (permission: string) => {
    return authService.hasPermission(permission)
  }
  
  // Check user type
  const isUserType = (userType: User['userType']) => {
    return authService.isUserType(userType)
  }
  
  // Get security settings
  const getSecuritySettings = () => {
    return authService.getSecuritySettings()
  }
  
  // Check if user is admin
  const isAdmin = computed(() => {
    return user.value?.userType === 'HEALTHCARE_PROVIDER' && 
           hasPermission('admin_access')
  })
  
  // Check if user is patient
  const isPatient = computed(() => {
    return user.value?.userType === 'PATIENT'
  })
  
  // Check if user is caregiver
  const isCaregiver = computed(() => {
    return user.value?.userType === 'CAREGIVER'
  })
  
  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    
    // Computed
    isAdmin,
    isPatient,
    isCaregiver,
    
    // Methods
    login,
    logout,
    hasPermission,
    isUserType,
    getSecuritySettings
  }
} 