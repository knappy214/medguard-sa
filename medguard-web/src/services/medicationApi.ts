import apiClientEnhanced, { ApiError, NetworkError } from './apiClient'
import { API_ENDPOINTS, shouldUseRealApi } from '@/config/api'
import authService from './authService'
import type { 
  Medication, 
  MedicationSchedule, 
  StockAlert, 
  MedicationFormData,
  StockAnalytics,
  ApiResponse,
  PaginatedResponse 
} from '@/types/medication'

// Import mock data
import { 
  mockMedications, 
  mockSchedule, 
  mockAlerts,
  mockStockAnalytics 
} from './mockData'

// Helper function to transform frontend data to backend format
const transformToBackendFormat = (data: MedicationFormData) => ({
  name: data.name,
  generic_name: data.name, // Use name as generic name for now
  brand_name: data.name, // Use name as brand name for now
  medication_type: 'tablet', // Default to tablet
  prescription_type: 'otc', // Default to over the counter
  strength: data.dosage,
  dosage_unit: 'mg', // Default unit
  pill_count: data.stock || 0,
  low_stock_threshold: data.minStock || 10,
  description: data.instructions || '',
  manufacturer: 'Unknown', // Default manufacturer
  active_ingredients: '',
  side_effects: '',
  contraindications: '',
  storage_instructions: '',
  expiration_date: null
})

// Helper function to transform backend data to frontend format
const transformToFrontendFormat = (backendData: any): Medication => ({
  id: String(backendData.id), // Ensure id is a string
  name: backendData.name,
  dosage: backendData.strength,
  frequency: 'Once daily', // Default frequency
  time: '08:00', // Default time
  stock: backendData.pill_count,
  pill_count: backendData.pill_count,
  minStock: backendData.low_stock_threshold,
  instructions: backendData.description || '',
  category: 'Other', // Default category
  isActive: true,
  createdAt: backendData.created_at,
  updatedAt: backendData.updated_at
})

// Helper function to transform backend schedule data to frontend format
const transformScheduleToFrontendFormat = (backendSchedule: any): MedicationSchedule => {
  // Create a proper time string based on timing and custom_time
  let scheduledTime: string
  if (backendSchedule.custom_time) {
    // Use custom time if available
    const today = new Date().toISOString().split('T')[0]
    scheduledTime = `${today}T${backendSchedule.custom_time}:00`
  } else {
    // Use timing to create a reasonable time
    const today = new Date().toISOString().split('T')[0]
    const timeMap = {
      'morning': '08:00',
      'noon': '12:00', 
      'night': '20:00'
    }
    const time = timeMap[backendSchedule.timing as keyof typeof timeMap] || '08:00'
    scheduledTime = `${today}T${time}:00`
  }

  // Transform medication data
  const medication: Medication = {
    id: String(backendSchedule.medication.id),
    name: backendSchedule.medication.name,
    dosage: backendSchedule.medication.strength || 'Unknown',
    frequency: backendSchedule.frequency || 'Once daily',
    time: scheduledTime.split('T')[1]?.split(':').slice(0, 2).join(':') || '08:00',
    stock: backendSchedule.medication.pill_count || 0,
    pill_count: backendSchedule.medication.pill_count || 0,
    minStock: backendSchedule.medication.low_stock_threshold || 10,
    instructions: backendSchedule.instructions || '',
    category: 'Other',
    isActive: true,
    createdAt: backendSchedule.created_at || new Date().toISOString(),
    updatedAt: backendSchedule.updated_at || new Date().toISOString()
  }

  // Determine frontend status based on today's log status
  let frontendStatus: 'pending' | 'taken' | 'missed'
  if (backendSchedule.today_log_status) {
    // Use today's log status if available
    if (backendSchedule.today_log_status === 'taken') {
      frontendStatus = 'taken'
    } else if (backendSchedule.today_log_status === 'missed') {
      frontendStatus = 'missed'
    } else {
      frontendStatus = 'pending'
    }
  } else {
    // Fallback to schedule status if no log exists
    if (backendSchedule.status === 'active') {
      frontendStatus = 'pending' // Active schedules should show as pending for user action
    } else if (backendSchedule.status === 'completed') {
      frontendStatus = 'taken'
    } else if (backendSchedule.status === 'missed') {
      frontendStatus = 'missed'
    } else {
      frontendStatus = 'pending'
    }
  }

  return {
    id: String(backendSchedule.id),
    medicationId: String(backendSchedule.medication.id),
    medication: medication,
    scheduledTime: scheduledTime,
    status: frontendStatus,
    notes: backendSchedule.instructions || ''
  }
}

// Enhanced medication API service with real backend integration
export const medicationApi = {
  // Get all medications
  async getMedications(): Promise<Medication[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<any>(API_ENDPOINTS.MEDICATIONS.LIST)
        console.log('📦 Raw API response:', response)
        
        // Handle Django REST Framework pagination format
        if (response.results) {
          // Django REST Framework pagination format: {count, next, previous, results}
          console.log('✅ Found results array with', response.results.length, 'medications')
          const transformedMedications = response.results.map((med: any) => transformToFrontendFormat(med))
          console.log('🔄 Transformed medications:', transformedMedications)
          return transformedMedications
        } else if (Array.isArray(response)) {
          // Direct array response
          console.log('✅ Found direct array with', response.length, 'medications')
          const transformedMedications = response.map((med: any) => transformToFrontendFormat(med))
          console.log('🔄 Transformed medications:', transformedMedications)
          return transformedMedications
        } else if (response.data) {
          // Custom pagination format
          console.log('✅ Found data array with', response.data.length, 'medications')
          const transformedMedications = response.data.map((med: any) => transformToFrontendFormat(med))
          console.log('🔄 Transformed medications:', transformedMedications)
          return transformedMedications
        } else {
          console.warn('⚠️ Unexpected response format:', response)
          return []
        }
      } else {
        // Fallback to mock data
        return mockMedications
      }
    } catch (error) {
      console.error('Failed to fetch medications:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return []
    }
  },

  // Get medication by ID
  async getMedication(id: string): Promise<Medication | null> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<ApiResponse<Medication>>(API_ENDPOINTS.MEDICATIONS.DETAIL(id))
        return response.data || null
      } else {
        // Fallback to mock data
        return mockMedications.find(med => med.id === id) || null
      }
    } catch (error) {
      console.error('Failed to fetch medication:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return null
    }
  },



  // Create medication schedules based on frequency
  async createMedicationSchedules(medicationId: string, data: MedicationFormData): Promise<MedicationSchedule[]> {
    try {
      console.log('📅 Creating medication schedules for medication:', medicationId)
      console.log('📅 Schedule data:', data)
      
      if (shouldUseRealApi()) {
        const schedules: MedicationSchedule[] = []
        
        // Determine how many schedules to create based on frequency
        const frequencyMap = {
          'Once daily': 1,
          'Twice daily': 2,
          'Three times daily': 3,
          'Every 6 hours': 4,
          'Every 8 hours': 3,
          'Every 12 hours': 2,
          'As needed': 1,
          'Other': 1
        }
        
        const numSchedules = frequencyMap[data.frequency as keyof typeof frequencyMap] || 1
        console.log(`🔄 Creating ${numSchedules} schedules for frequency: ${data.frequency}`)
        
        // Create schedules based on frequency
        for (let i = 0; i < numSchedules; i++) {
          let timing: string
          let customTime: string | null = null
          
          if (data.scheduleTiming === 'custom' && data.scheduleCustomTime) {
            // Use custom time for all schedules (same time each day)
            timing = 'custom'
            customTime = data.scheduleCustomTime
          } else {
            // Distribute schedules across day
            if (numSchedules === 1) {
              timing = data.scheduleTiming || 'morning'
            } else if (numSchedules === 2) {
              timing = i === 0 ? 'morning' : 'night'
            } else if (numSchedules === 3) {
              timing = i === 0 ? 'morning' : i === 1 ? 'noon' : 'night'
            } else {
              // For 4+ schedules, use custom times
              timing = 'custom'
              const hour = 6 + (i * 6) // 6am, 12pm, 6pm, 12am
              customTime = `${hour.toString().padStart(2, '0')}:00`
            }
          }
          
          const scheduleData = {
            medication_id: medicationId, // Correct field name
            timing: timing,
            custom_time: customTime,
            dosage_amount: data.scheduleDosageAmount || 1.0,
            frequency: data.frequency || 'daily',
            instructions: data.scheduleInstructions || data.instructions || '',
            start_date: new Date().toISOString().split('T')[0], // Today's date
            status: 'active',
            // Set all days of the week to True for daily medications
            monday: true,
            tuesday: true,
            wednesday: true,
            thursday: true,
            friday: true,
            saturday: true,
            sunday: true
          }
          
          console.log(`📅 Creating schedule ${i + 1}/${numSchedules}:`, scheduleData)
          
          try {
            const response = await apiClientEnhanced.post<any>(API_ENDPOINTS.MEDICATIONS.SCHEDULE, scheduleData)
            console.log(`✅ Schedule ${i + 1} created successfully:`, response)
            schedules.push(response)
          } catch (error) {
            console.error(`❌ Failed to create schedule ${i + 1}:`, error)
            // Continue with other schedules even if one fails
          }
        }
        
        console.log(`✅ Created ${schedules.length} schedules successfully`)
        return schedules
      } else {
        // Fallback to mock data
        const newSchedule: MedicationSchedule = {
          id: Date.now().toString(),
          medicationId: medicationId,
          medication: mockMedications.find(med => med.id === medicationId) || mockMedications[0],
          scheduledTime: new Date().toISOString(),
          status: 'pending',
          notes: data.scheduleInstructions || data.instructions || ''
        }
        mockSchedule.push(newSchedule)
        console.log('✅ Mock schedule created:', newSchedule)
        return [newSchedule]
      }
    } catch (error) {
      console.error('❌ Failed to create medication schedules:', error)
      throw error
    }
  },

  // Create new medication
  async createMedication(data: MedicationFormData): Promise<Medication | null> {
    try {
      console.log('🌐 Creating medication with data:', data)
      console.log('🔧 Using real API:', shouldUseRealApi())
      
      if (shouldUseRealApi()) {
        // Check authentication status
        const isAuthenticated = authService.authenticated.value
        console.log('🔐 Authentication status:', isAuthenticated)
        
        if (!isAuthenticated) {
          console.error('❌ User not authenticated')
          throw new Error('User not authenticated. Please log in first.')
        }
        
        // Transform frontend data to backend format
        const backendData = transformToBackendFormat(data)
        
        console.log('🔄 Transformed data for backend:', backendData)
        console.log('📡 Making API call to:', API_ENDPOINTS.MEDICATIONS.CREATE)
        const response = await apiClientEnhanced.post<any>(API_ENDPOINTS.MEDICATIONS.CREATE, backendData)
        console.log('✅ API response:', response)
        
        // Create medication schedules if medication was created successfully
        if (response && (response.id || response.data?.id)) {
          const medicationId = response.id || response.data?.id
          console.log('📅 Creating schedules for new medication:', medicationId)
          try {
            await this.createMedicationSchedules(medicationId, data)
            console.log('✅ Medication schedules created successfully')
          } catch (scheduleError) {
            console.error('⚠️ Failed to create medication schedules:', scheduleError)
            // Don't fail the medication creation if schedule creation fails
          }
        }
        
        return response.data || response || null
      } else {
        console.log('🎭 Using mock data fallback')
        // Fallback to mock data
        const newMedication: Medication = {
          id: Date.now().toString(),
          ...data,
          pill_count: data.stock || 0,
          isActive: true,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
        mockMedications.push(newMedication)
        console.log('✅ Mock medication created:', newMedication)
        
        // Create mock schedules
        try {
          await this.createMedicationSchedules(newMedication.id, data)
        } catch (scheduleError) {
          console.error('⚠️ Failed to create mock medication schedules:', scheduleError)
        }
        
        return newMedication
      }
    } catch (error) {
      console.error('❌ Failed to create medication:', error)
      console.error('🔍 Error details:', {
        message: (error as any)?.message,
        status: (error as any)?.status,
        data: (error as any)?.data,
        stack: (error as any)?.stack
      })
      throw error
    }
  },

  // Update medication
  async updateMedication(id: string, data: Partial<MedicationFormData>): Promise<Medication | null> {
    try {
      if (shouldUseRealApi()) {
        // Transform frontend data to backend format (handle partial data)
        const backendData = {
          ...(data.name && { name: data.name }),
          ...(data.name && { generic_name: data.name }),
          ...(data.name && { brand_name: data.name }),
          ...(data.dosage && { strength: data.dosage }),
          ...(data.stock !== undefined && { pill_count: data.stock }),
          ...(data.minStock !== undefined && { low_stock_threshold: data.minStock }),
          ...(data.instructions && { description: data.instructions }),
        }
        
        console.log('🔄 Updating medication with transformed data:', backendData)
        const response = await apiClientEnhanced.patch<ApiResponse<Medication>>(API_ENDPOINTS.MEDICATIONS.UPDATE(id), backendData)
        return response.data || null
      } else {
        // Fallback to mock data
        const index = mockMedications.findIndex(med => med.id === id)
        if (index !== -1) {
          mockMedications[index] = {
            ...mockMedications[index],
            ...data,
            updatedAt: new Date().toISOString()
          }
          return mockMedications[index]
        }
        return null
      }
    } catch (error) {
      console.error('Failed to update medication:', error)
      throw error
    }
  },

  // Delete medication
  async deleteMedication(id: string): Promise<boolean> {
    try {
      if (shouldUseRealApi()) {
        await apiClientEnhanced.delete(API_ENDPOINTS.MEDICATIONS.DELETE(id))
        return true
      } else {
        // Fallback to mock data
        const index = mockMedications.findIndex(med => med.id === id)
        if (index !== -1) {
          mockMedications.splice(index, 1)
          return true
        }
        return false
      }
    } catch (error) {
      console.error('Failed to delete medication:', error)
      throw error
    }
  },

  // Get today's schedule
  async getTodaySchedule(): Promise<MedicationSchedule[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<any>(API_ENDPOINTS.MEDICATIONS.SCHEDULE + 'today/')
        console.log('📅 Raw schedule response:', response)
        
        // Handle different response formats and transform data
        let scheduleData: any[] = []
        if (Array.isArray(response)) {
          // Direct array response
          console.log('✅ Found direct array with', response.length, 'schedules')
          scheduleData = response
        } else if (response.data && Array.isArray(response.data)) {
          // Wrapped in data property
          console.log('✅ Found data array with', response.data.length, 'schedules')
          scheduleData = response.data
        } else if (response.results && Array.isArray(response.results)) {
          // Django REST Framework pagination format
          console.log('✅ Found results array with', response.results.length, 'schedules')
          scheduleData = response.results
        } else {
          console.warn('⚠️ Unexpected schedule response format:', response)
          return []
        }

        // Transform each schedule to frontend format
        const transformedSchedules = scheduleData.map(transformScheduleToFrontendFormat)
        console.log('🔄 Transformed schedules:', transformedSchedules)
        return transformedSchedules
      } else {
        // Fallback to mock data
        return mockSchedule
      }
    } catch (error) {
      console.error('Failed to fetch today\'s schedule:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return []
    }
  },

  // Mark medication as taken
  async markAsTaken(scheduleId: string, notes?: string): Promise<{ success: boolean; stockDeducted?: number; remainingStock?: number; lowStockAlert?: boolean; error?: string }> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.post(`${API_ENDPOINTS.MEDICATIONS.SCHEDULE}${scheduleId}/mark_taken/`, { notes })
        console.log('✅ Medication marked as taken:', response)
        
        return {
          success: true,
          stockDeducted: response.stock_deducted,
          remainingStock: response.remaining_stock,
          lowStockAlert: response.low_stock_alert
        }
      } else {
        // Fallback to mock data
        const scheduleItem = mockSchedule.find(item => item.id === scheduleId)
        if (scheduleItem) {
          scheduleItem.status = 'taken'
          scheduleItem.takenAt = new Date().toISOString()
          return { success: true }
        }
        return { success: false, error: 'Schedule not found' }
      }
    } catch (error: any) {
      console.error('Failed to mark medication as taken:', error)
      
      // Handle specific error cases
      if (error.response?.status === 400 && error.response?.data?.error === 'Insufficient stock') {
        return {
          success: false,
          error: error.response.data.message,
          remainingStock: error.response.data.current_stock
        }
      }
      
      throw error
    }
  },

  // Mark medication as missed
  async markAsMissed(scheduleId: string): Promise<boolean> {
    try {
      if (shouldUseRealApi()) {
        await apiClientEnhanced.post(`${API_ENDPOINTS.MEDICATIONS.SCHEDULE}${scheduleId}/mark_missed/`)
        return true
      } else {
        // Fallback to mock data
        const scheduleItem = mockSchedule.find(item => item.id === scheduleId)
        if (scheduleItem) {
          scheduleItem.status = 'missed'
          return true
        }
        return false
      }
    } catch (error) {
      console.error('Failed to mark medication as missed:', error)
      throw error
    }
  },

  // Get stock alerts
  async getStockAlerts(): Promise<StockAlert[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<ApiResponse<StockAlert[]>>(API_ENDPOINTS.MEDICATIONS.ALERTS)
        return response.data || []
      } else {
        // Fallback to mock data
        return mockAlerts
      }
    } catch (error) {
      console.error('Failed to fetch stock alerts:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return []
    }
  },

  // Mark alert as read
  async markAlertAsRead(alertId: string): Promise<boolean> {
    try {
      if (shouldUseRealApi()) {
        await apiClientEnhanced.post(API_ENDPOINTS.MEDICATIONS.ALERTS + `${alertId}/mark-read/`)
        return true
      } else {
        // Fallback to mock data
        const alert = mockAlerts.find(a => a.id === alertId)
        if (alert) {
          alert.isRead = true
          return true
        }
        return false
      }
    } catch (error) {
      console.error('Failed to mark alert as read:', error)
      throw error
    }
  },

  // Update stock
  async updateStock(medicationId: string, newStock: number): Promise<boolean> {
    try {
      if (shouldUseRealApi()) {
        await apiClientEnhanced.patch(API_ENDPOINTS.MEDICATIONS.UPDATE(medicationId), { stock: newStock })
        return true
      } else {
        // Fallback to mock data
        const medication = mockMedications.find(med => med.id === medicationId)
        if (medication) {
          medication.stock = newStock
          medication.updatedAt = new Date().toISOString()
          return true
        }
        return false
      }
    } catch (error) {
      console.error('Failed to update stock:', error)
      throw error
    }
  },

  // Get stock analytics
  async getStockAnalytics(medicationId: string): Promise<StockAnalytics> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<ApiResponse<StockAnalytics>>(API_ENDPOINTS.MEDICATIONS.ANALYTICS(medicationId))
        return response.data || mockStockAnalytics
      } else {
        // Fallback to mock data
        return mockStockAnalytics
      }
    } catch (error) {
      console.error('Failed to fetch stock analytics:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return mockStockAnalytics
    }
  },

  // Get medications with pagination
  async getMedicationsPaginated(page: number = 1, pageSize: number = 10): Promise<PaginatedResponse<Medication>> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<PaginatedResponse<Medication>>(
          `${API_ENDPOINTS.MEDICATIONS.LIST}?page=${page}&page_size=${pageSize}`
        )
        return response
      } else {
        // Fallback to mock data with pagination
        const start = (page - 1) * pageSize
        const end = start + pageSize
        const items = mockMedications.slice(start, end)
        
        return {
          data: items,
          total: mockMedications.length,
          page: page,
          perPage: pageSize,
          totalPages: Math.ceil(mockMedications.length / pageSize)
        }
      }
    } catch (error) {
      console.error('Failed to fetch paginated medications:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return {
        data: [],
        total: 0,
        page: 1,
        perPage: pageSize,
        totalPages: 0
      }
    }
  },

  // Search medications
  async searchMedications(query: string): Promise<Medication[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<ApiResponse<Medication[]>>(
          `${API_ENDPOINTS.MEDICATIONS.LIST}?search=${encodeURIComponent(query)}`
        )
        return response.data || []
      } else {
        // Fallback to mock data with search
        return mockMedications.filter(med => 
          med.name.toLowerCase().includes(query.toLowerCase()) ||
          med.category.toLowerCase().includes(query.toLowerCase())
        )
      }
    } catch (error) {
      console.error('Failed to search medications:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return []
    }
  },

  // Get medication history
  async getMedicationHistory(medicationId: string): Promise<any[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<ApiResponse<any[]>>(
          `${API_ENDPOINTS.MEDICATIONS.LOGS}?medication=${medicationId}`
        )
        return response.data || []
      } else {
        // Fallback to mock data
        return []
      }
    } catch (error) {
      console.error('Failed to fetch medication history:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return []
    }
  },

  // Export medication data
  async exportMedicationData(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.raw.get(
          `${API_ENDPOINTS.MEDICATIONS.LIST}export/?format=${format}`,
          { responseType: 'blob' }
        )
        return response.data
      } else {
        // Fallback to mock data export
        const data = format === 'json' 
          ? JSON.stringify(mockMedications, null, 2)
          : mockMedications.map(med => `${med.name},${med.dosage},${med.frequency}`).join('\n')
        
        return new Blob([data], { 
          type: format === 'json' ? 'application/json' : 'text/csv' 
        })
      }
    } catch (error) {
      console.error('Failed to export medication data:', error)
      throw error
    }
  },

  // Import medication data
  async importMedicationData(file: File): Promise<boolean> {
    try {
      if (shouldUseRealApi()) {
        const formData = new FormData()
        formData.append('file', file)
        
        await apiClientEnhanced.raw.post(
          `${API_ENDPOINTS.MEDICATIONS.LIST}import/`,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )
        return true
      } else {
        // Fallback to mock data import
        console.log('Mock import:', file.name)
        return true
      }
    } catch (error) {
      console.error('Failed to import medication data:', error)
      throw error
    }
  },

  // Get medication statistics
  async getMedicationStats(): Promise<any> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<ApiResponse<any>>(
          `${API_ENDPOINTS.MEDICATIONS.LIST}stats/`
        )
        return response.data || {}
      } else {
        // Fallback to mock data
        return {
          total: mockMedications.length,
          active: mockMedications.filter(med => med.isActive).length,
          lowStock: mockMedications.filter(med => med.stock <= med.minStock).length
        }
      }
    } catch (error) {
      console.error('Failed to fetch medication stats:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return {}
    }
  },

  // Get medication reminders
  async getMedicationReminders(): Promise<any[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<ApiResponse<any[]>>(
          `${API_ENDPOINTS.MEDICATIONS.LIST}reminders/`
        )
        return response.data || []
      } else {
        // Fallback to mock data
        return []
      }
    } catch (error) {
      console.error('Failed to fetch medication reminders:', error)
      if (shouldUseRealApi()) {
        throw error
      }
      return []
    }
  },

  // Set medication reminder
  async setMedicationReminder(medicationId: string, reminderData: any): Promise<boolean> {
    try {
      if (shouldUseRealApi()) {
        await apiClientEnhanced.post(
          `${API_ENDPOINTS.MEDICATIONS.LIST}${medicationId}/reminders/`,
          reminderData
        )
        return true
      } else {
        // Fallback to mock data
        console.log('Mock reminder set:', medicationId, reminderData)
        return true
      }
    } catch (error) {
      console.error('Failed to set medication reminder:', error)
      throw error
    }
  },

  // Delete medication reminder
  async deleteMedicationReminder(reminderId: string): Promise<boolean> {
    try {
      if (shouldUseRealApi()) {
        await apiClientEnhanced.delete(
          `${API_ENDPOINTS.MEDICATIONS.LIST}reminders/${reminderId}/`
        )
        return true
      } else {
        // Fallback to mock data
        console.log('Mock reminder deleted:', reminderId)
        return true
      }
    } catch (error) {
      console.error('Failed to delete medication reminder:', error)
      throw error
    }
  }
}