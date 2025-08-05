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
  PaginatedResponse,
  BulkMedicationEntry,
  // New types for enhanced features
  ParsedPrescription,
  PrescriptionMedication,
  MedicationValidation,
  DrugDatabaseEntry,
  MedicationEnrichment,
  PrescriptionStorage,
  BatchMedicationResponse,
  BatchMedicationResult,
  MedicationHistory,
  AdherenceTracking,
  PrescriptionRenewal,
  MedicationImage,
  PerplexityEnrichmentRequest,
  PerplexityEnrichmentResponse,
  MedicationInteraction,
  CostAnalysis,
  AvailabilityInfo
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
  strength: data.strength || data.dosage,
  dosage_unit: 'mg', // Default unit
  pill_count: data.stock || 0,
  low_stock_threshold: data.minStock || 10,
  description: data.instructions || '',
  manufacturer: data.manufacturer || 'Unknown',
  active_ingredients: data.activeIngredients || '',
  side_effects: data.sideEffects || '',
  contraindications: '',
  storage_instructions: '',
  expiration_date: data.expirationDate || null,
  // Additional fields for enhanced medication management
  icd10_code: data.icd10Code || '',
  prescription_number: data.prescriptionNumber || '',
  prescribing_doctor: data.prescribingDoctor || '',
  // Image handling would be done separately via FormData
  interactions: data.interactions || [],
  // Handle medicationImage properly - convert File to string URL or undefined
  medication_image: data.medicationImage instanceof File ? undefined : data.medicationImage || undefined
})

// Helper function to transform backend data to frontend format
const transformToFrontendFormat = (backendData: any): Medication => ({
  id: String(backendData.id), // Ensure id is a string
  name: backendData.name,
  dosage: backendData.dosage_instructions || 'Take as prescribed', // Default dosage instructions
  frequency: 'Once daily', // Default frequency
  time: '08:00', // Default time
  stock: backendData.pill_count,
  pill_count: backendData.pill_count,
  minStock: backendData.low_stock_threshold,
  instructions: backendData.description || '',
  category: 'Other', // Default category
  isActive: true,
  createdAt: backendData.created_at,
  updatedAt: backendData.updated_at,
  // Enhanced fields
  strength: backendData.strength || '',
  manufacturer: backendData.manufacturer || '',
  activeIngredients: backendData.active_ingredients || '',
  sideEffects: backendData.side_effects || '',
  icd10Code: backendData.icd10_code || '',
  prescriptionNumber: backendData.prescription_number || '',
  prescribingDoctor: backendData.prescribing_doctor || '',
  expirationDate: backendData.expiration_date || '',
  medicationImage: backendData.medication_image || undefined,
  interactions: backendData.interactions || []
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
          // Handle medicationImage type conversion
          const updatedData = { ...data }
          if (updatedData.medicationImage !== undefined) {
            updatedData.medicationImage = updatedData.medicationImage instanceof File ? undefined : (updatedData.medicationImage as string | undefined)
          }
          
          mockMedications[index] = {
            ...mockMedications[index],
            ...updatedData,
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

  // 1. Create medications from prescription data
  async createMedicationsFromPrescription(prescription: ParsedPrescription): Promise<Medication[]> {
    try {
      console.log('📋 Creating medications from prescription:', prescription)
      
      if (shouldUseRealApi()) {
        const createdMedications: Medication[] = []
        
        for (const prescriptionMed of prescription.medications) {
          try {
            // Transform prescription medication to form data
            const formData: MedicationFormData = {
              name: prescriptionMed.name,
              strength: prescriptionMed.strength,
              dosage: prescriptionMed.dosage,
              frequency: prescriptionMed.frequency,
              time: '08:00', // Default time
              stock: prescriptionMed.quantity,
              minStock: Math.ceil(prescriptionMed.quantity * 0.2), // 20% of quantity
              instructions: prescriptionMed.instructions,
              category: 'Prescription',
              manufacturer: '',
              prescriptionNumber: prescription.id,
              prescribingDoctor: prescription.prescribingDoctor,
                           activeIngredients: '',
             sideEffects: prescriptionMed.sideEffects?.join(', ') || '',
             icd10Code: '',
             expirationDate: '',
             medicationImage: undefined,
             interactions: prescriptionMed.interactions || [],
             isBulkEntry: false,
             bulkMedications: []
            }
            
            // Validate medication before creating
            const validation = await this.validateMedication(formData)
            if (!validation.isValid) {
              console.warn(`⚠️ Validation failed for ${prescriptionMed.name}:`, validation.errors)
            }
            
            const createdMedication = await this.createMedication(formData)
            if (createdMedication) {
              // Enrich with drug database information
              try {
                await this.enrichMedicationWithPerplexity(createdMedication.id, {
                  medicationName: prescriptionMed.name,
                  genericName: prescriptionMed.genericName,
                  strength: prescriptionMed.strength,
                  includeInteractions: true,
                  includeSideEffects: true,
                  includeCost: true,
                  includeAvailability: true
                })
              } catch (enrichmentError) {
                console.warn(`⚠️ Failed to enrich ${prescriptionMed.name}:`, enrichmentError)
              }
              
              createdMedications.push(createdMedication)
            }
          } catch (error) {
            console.error(`❌ Failed to create medication ${prescriptionMed.name}:`, error)
            // Continue with other medications even if one fails
          }
        }
        
        // Store prescription for future reference
        await this.storePrescription(prescription, createdMedications)
        
        return createdMedications
      } else {
        // Fallback to mock data
        const createdMedications: Medication[] = []
        
        for (const prescriptionMed of prescription.medications) {
          const newMedication: Medication = {
            id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
            name: prescriptionMed.name,
            strength: prescriptionMed.strength,
            dosage: prescriptionMed.dosage,
            frequency: prescriptionMed.frequency,
            time: '08:00',
            stock: prescriptionMed.quantity,
            pill_count: prescriptionMed.quantity,
            minStock: Math.ceil(prescriptionMed.quantity * 0.2),
            instructions: prescriptionMed.instructions,
            category: 'Prescription',
            isActive: true,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
            manufacturer: '',
            prescriptionNumber: prescription.id,
            prescribingDoctor: prescription.prescribingDoctor,
            activeIngredients: '',
            sideEffects: prescriptionMed.sideEffects?.join(', ') || '',
            icd10Code: '',
            expirationDate: '',
            medicationImage: undefined,
            interactions: prescriptionMed.interactions || [],
            prescriptionId: prescription.id,
            isPrescription: true,
            refillsRemaining: prescriptionMed.refills,
            totalRefills: prescriptionMed.refills
          }
          
          mockMedications.push(newMedication)
          createdMedications.push(newMedication)
        }
        
        return createdMedications
      }
    } catch (error) {
      console.error('❌ Failed to create medications from prescription:', error)
      throw error
    }
  },

  // 2. Validate medication against drug databases
  async validateMedication(medicationData: MedicationFormData): Promise<MedicationValidation> {
    try {
      console.log('🔍 Validating medication:', medicationData.name)
      
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.post<MedicationValidation>(
          API_ENDPOINTS.MEDICATIONS.VALIDATION.VALIDATE,
          {
            name: medicationData.name,
            strength: medicationData.strength,
            dosage: medicationData.dosage,
            frequency: medicationData.frequency,
            instructions: medicationData.instructions
          }
        )
        
        return response
      } else {
        // Mock validation
        const warnings: string[] = []
        const errors: string[] = []
        const suggestions: string[] = []
        
        // Basic validation rules
        if (!medicationData.name) {
          errors.push('Medication name is required')
        }
        
        if (!medicationData.dosage) {
          errors.push('Dosage information is required')
        }
        
        if (!medicationData.frequency) {
          errors.push('Frequency is required')
        }
        
        if (medicationData.stock < 0) {
          errors.push('Stock cannot be negative')
        }
        
        if (medicationData.minStock > medicationData.stock) {
          warnings.push('Minimum stock is higher than current stock')
        }
        
        // Mock drug database match
        const mockDrugMatch: DrugDatabaseEntry = {
          id: 'mock-drug-1',
          name: medicationData.name,
          genericName: medicationData.name,
          brandNames: [medicationData.name],
          activeIngredients: ['Active ingredient'],
          strength: medicationData.strength || 'Unknown',
          dosageForm: 'tablet',
          manufacturer: medicationData.manufacturer || 'Unknown',
          description: 'Mock drug description',
          sideEffects: ['Nausea', 'Headache'],
          contraindications: ['Allergy to active ingredient'],
          interactions: [],
          pregnancyCategory: 'C',
          breastfeedingCategory: 'Unknown',
          pediatricUse: 'Consult healthcare provider',
          geriatricUse: 'Consult healthcare provider',
          renalDoseAdjustment: 'May require adjustment',
          hepaticDoseAdjustment: 'May require adjustment',
          storageInstructions: 'Store at room temperature',
          disposalInstructions: 'Dispose of properly',
          cost: 25.00,
          availability: 'available'
        }
        
        return {
          isValid: errors.length === 0,
          warnings,
          errors,
          suggestions,
          drugDatabaseMatch: mockDrugMatch,
          alternatives: []
        }
      }
    } catch (error) {
      console.error('❌ Failed to validate medication:', error)
      return {
        isValid: false,
        warnings: [],
        errors: ['Validation service unavailable'],
        suggestions: []
      }
    }
  },

  // 3. Store and retrieve prescriptions
  async storePrescription(prescription: ParsedPrescription, medications: Medication[]): Promise<PrescriptionStorage> {
    try {
      console.log('💾 Storing prescription:', prescription.id)
      
      if (shouldUseRealApi()) {
        const storageData = {
          prescription: prescription,
          medications: medications.map(med => med.id),
          tags: ['prescription', 'imported'],
          notes: `Imported from prescription ${prescription.id}`
        }
        
        const response = await apiClientEnhanced.post<PrescriptionStorage>(
          API_ENDPOINTS.MEDICATIONS.STORAGE.PRESCRIPTIONS,
          storageData
        )
        
        return response
      } else {
        // Mock storage
        const storage: PrescriptionStorage = {
          id: Date.now().toString(),
          prescriptionId: prescription.id,
          prescription,
          medications,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          status: 'active',
          tags: ['prescription', 'imported'],
          notes: `Imported from prescription ${prescription.id}`
        }
        
        return storage
      }
    } catch (error) {
      console.error('❌ Failed to store prescription:', error)
      throw error
    }
  },

  async getStoredPrescriptions(): Promise<PrescriptionStorage[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<PrescriptionStorage[]>(
          API_ENDPOINTS.MEDICATIONS.STORAGE.PRESCRIPTIONS
        )
        return response
      } else {
        // Mock data
        return []
      }
    } catch (error) {
      console.error('❌ Failed to get stored prescriptions:', error)
      return []
    }
  },

  // 4. Medication enrichment using Perplexity API
  async enrichMedicationWithPerplexity(
    medicationId: string, 
    request: PerplexityEnrichmentRequest
  ): Promise<PerplexityEnrichmentResponse> {
    try {
      console.log('🧠 Enriching medication with Perplexity:', medicationId)
      
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.post<PerplexityEnrichmentResponse>(
          API_ENDPOINTS.MEDICATIONS.ENRICHMENT.PERPLEXITY,
          {
            medication_id: medicationId,
            ...request
          }
        )
        
        return response
      } else {
        // Mock enrichment
        const mockEnrichment: MedicationEnrichment = {
          drugInfo: {
            id: 'mock-drug-1',
            name: request.medicationName,
            genericName: request.genericName || request.medicationName,
            brandNames: [request.medicationName],
            activeIngredients: ['Active ingredient'],
            strength: request.strength || 'Unknown',
            dosageForm: 'tablet',
            manufacturer: request.manufacturer || 'Unknown',
            description: 'Mock drug information from Perplexity',
            sideEffects: ['Nausea', 'Headache', 'Dizziness'],
            contraindications: ['Allergy to active ingredient'],
            interactions: ['Drug A', 'Drug B'],
            pregnancyCategory: 'C',
            breastfeedingCategory: 'Unknown',
            pediatricUse: 'Consult healthcare provider',
            geriatricUse: 'Consult healthcare provider',
            renalDoseAdjustment: 'May require adjustment',
            hepaticDoseAdjustment: 'May require adjustment',
            storageInstructions: 'Store at room temperature',
            disposalInstructions: 'Dispose of properly',
            cost: 25.00,
            availability: 'available'
          },
          interactions: [
            {
              severity: 'moderate',
              description: 'May interact with other medications',
              medications: ['Drug A', 'Drug B'],
              recommendations: 'Monitor for side effects',
              evidence: 'Clinical studies',
              source: 'Perplexity API'
            }
          ],
          sideEffects: ['Nausea', 'Headache', 'Dizziness'],
          contraindications: ['Allergy to active ingredient'],
          dosageGuidelines: [
            {
              ageGroup: 'Adults',
              condition: 'General',
              dosage: '1 tablet',
              frequency: 'Once daily',
              duration: 'As prescribed',
              notes: 'Take with food'
            }
          ],
          costAnalysis: {
            averageCost: 25.00,
            costRange: { min: 20.00, max: 30.00 },
            genericAvailable: true,
            genericCost: 15.00,
            insuranceCoverage: 80,
            outOfPocketCost: 5.00,
            costPerDose: 0.83,
            monthlyCost: 25.00
          },
          availability: {
            isAvailable: true,
            stockStatus: 'in_stock',
            pharmacies: [
              {
                name: 'Local Pharmacy',
                address: '123 Main St',
                phone: '555-1234',
                distance: 2.5,
                stock: 50,
                price: 25.00
              }
            ],
            onlineAvailability: true,
            prescriptionRequired: true
          },
          enrichedAt: new Date().toISOString(),
          source: 'perplexity'
        }
        
        return {
          success: true,
          data: mockEnrichment,
          source: 'perplexity',
          timestamp: new Date().toISOString()
        }
      }
    } catch (error) {
      console.error('❌ Failed to enrich medication with Perplexity:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        source: 'perplexity',
        timestamp: new Date().toISOString()
      }
    }
  },

  // 5. Batch medication creation with proper error handling
  async createBatchMedications(medications: MedicationFormData[]): Promise<BatchMedicationResponse> {
    try {
      console.log('📦 Creating batch medications:', medications.length)
      
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.post<BatchMedicationResponse>(
          API_ENDPOINTS.MEDICATIONS.BATCH.CREATE,
          { medications }
        )
        
        return response
      } else {
        // Mock batch creation
        const results: BatchMedicationResult[] = []
        let successful = 0
        let failed = 0
        const errors: string[] = []
        const warnings: string[] = []
        
        for (const medicationData of medications) {
          try {
            // Validate first
            const validation = await this.validateMedication(medicationData)
            
            if (!validation.isValid) {
              results.push({
                success: false,
                error: validation.errors.join(', '),
                warnings: validation.warnings,
                validation
              })
              failed++
              errors.push(`Validation failed for ${medicationData.name}: ${validation.errors.join(', ')}`)
            } else {
                             // Create medication
               const newMedication: Medication = {
                 id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
                 name: medicationData.name,
                 strength: medicationData.strength || '',
                 dosage: medicationData.dosage,
                 frequency: medicationData.frequency,
                 time: medicationData.time,
                 stock: medicationData.stock,
                 pill_count: medicationData.stock,
                 minStock: medicationData.minStock,
                 instructions: medicationData.instructions,
                 category: medicationData.category,
                 isActive: true,
                 createdAt: new Date().toISOString(),
                 updatedAt: new Date().toISOString(),
                 manufacturer: medicationData.manufacturer || '',
                 prescriptionNumber: medicationData.prescriptionNumber || '',
                 prescribingDoctor: medicationData.prescribingDoctor || '',
                 activeIngredients: medicationData.activeIngredients || '',
                 sideEffects: medicationData.sideEffects || '',
                 icd10Code: medicationData.icd10Code || '',
                 expirationDate: medicationData.expirationDate || '',
                 medicationImage: medicationData.medicationImage instanceof File ? undefined : (medicationData.medicationImage as string | undefined),
                 interactions: medicationData.interactions || []
               }
              
              mockMedications.push(newMedication)
              
              results.push({
                success: true,
                medication: newMedication,
                warnings: validation.warnings,
                validation
              })
              successful++
              
              if (validation.warnings.length > 0) {
                warnings.push(`Warnings for ${medicationData.name}: ${validation.warnings.join(', ')}`)
              }
            }
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error'
            results.push({
              success: false,
              error: errorMessage
            })
            failed++
            errors.push(`Failed to create ${medicationData.name}: ${errorMessage}`)
          }
        }
        
        return {
          total: medications.length,
          successful,
          failed,
          results,
          errors,
          warnings
        }
      }
    } catch (error) {
      console.error('❌ Failed to create batch medications:', error)
      throw error
    }
  },

  // 6. Medication interaction checking
  async checkMedicationInteractions(medicationIds: string[]): Promise<MedicationInteraction[]> {
    try {
      console.log('🔍 Checking medication interactions for:', medicationIds)
      
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.post<MedicationInteraction[]>(
          API_ENDPOINTS.MEDICATIONS.VALIDATION.INTERACTIONS,
          { medication_ids: medicationIds }
        )
        
        return response
      } else {
        // Mock interactions
        const mockInteractions: MedicationInteraction[] = []
        
        if (medicationIds.length > 1) {
          mockInteractions.push({
            severity: 'moderate',
            description: 'May increase risk of side effects',
            medications: medicationIds,
            recommendations: 'Monitor for adverse effects and consult healthcare provider',
            evidence: 'Drug interaction database',
            source: 'Mock API'
          })
        }
        
        return mockInteractions
      }
    } catch (error) {
      console.error('❌ Failed to check medication interactions:', error)
      return []
    }
  },

  // 7. Prescription renewal tracking and reminders
  async createPrescriptionRenewal(prescriptionId: string, renewalData: Partial<PrescriptionRenewal>): Promise<PrescriptionRenewal> {
    try {
      console.log('🔄 Creating prescription renewal for:', prescriptionId)
      
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.post<PrescriptionRenewal>(
          API_ENDPOINTS.MEDICATIONS.PRESCRIPTIONS.RENEWALS,
          {
            prescription_id: prescriptionId,
            ...renewalData
          }
        )
        
        return response
      } else {
        // Mock renewal
        const renewal: PrescriptionRenewal = {
          id: Date.now().toString(),
          prescriptionId,
          originalPrescription: {
            id: prescriptionId,
            patientName: 'Mock Patient',
            prescribingDoctor: 'Dr. Smith',
            prescriptionDate: new Date().toISOString(),
            medications: [],
            status: 'active'
          },
          renewalDate: new Date().toISOString(),
          expiryDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days
          refillsRemaining: 2,
          totalRefills: 3,
          status: 'active',
          reminderSent: false,
          notes: renewalData.notes || 'Prescription renewal'
        }
        
        return renewal
      }
    } catch (error) {
      console.error('❌ Failed to create prescription renewal:', error)
      throw error
    }
  },

  async getPrescriptionRenewals(): Promise<PrescriptionRenewal[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<PrescriptionRenewal[]>(
          API_ENDPOINTS.MEDICATIONS.PRESCRIPTIONS.RENEWALS
        )
        return response
      } else {
        // Mock data
        return []
      }
    } catch (error) {
      console.error('❌ Failed to get prescription renewals:', error)
      return []
    }
  },

  // 8. Medication image storage and retrieval
  async uploadMedicationImage(medicationId: string, file: File, description?: string): Promise<MedicationImage> {
    try {
      console.log('📸 Uploading medication image for:', medicationId)
      
      if (shouldUseRealApi()) {
        const formData = new FormData()
        formData.append('medication_id', medicationId)
        formData.append('image', file)
        if (description) {
          formData.append('description', description)
        }
        
        const response = await apiClientEnhanced.raw.post<MedicationImage>(
          API_ENDPOINTS.MEDICATIONS.IMAGES.UPLOAD,
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )
        
        return response.data
      } else {
        // Mock image upload
        const image: MedicationImage = {
          id: Date.now().toString(),
          medicationId,
          imageUrl: URL.createObjectURL(file),
          thumbnailUrl: URL.createObjectURL(file),
          uploadedAt: new Date().toISOString(),
          fileSize: file.size,
          mimeType: file.type,
          description: description || '',
          isPrimary: true
        }
        
        return image
      }
    } catch (error) {
      console.error('❌ Failed to upload medication image:', error)
      throw error
    }
  },

  async getMedicationImages(medicationId: string): Promise<MedicationImage[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<MedicationImage[]>(
          API_ENDPOINTS.MEDICATIONS.IMAGES.LIST(medicationId)
        )
        return response
      } else {
        // Mock data
        return []
      }
    } catch (error) {
      console.error('❌ Failed to get medication images:', error)
      return []
    }
  },

  // 9. Medication history and adherence tracking
  async getMedicationHistory(medicationId: string): Promise<MedicationHistory[]> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<MedicationHistory[]>(
          API_ENDPOINTS.MEDICATIONS.ADHERENCE.HISTORY(medicationId)
        )
        return response
      } else {
        // Mock history
        const history: MedicationHistory[] = [
          {
            id: '1',
            medicationId,
            action: 'taken',
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // Yesterday
            notes: 'Taken as prescribed',
            doseAmount: 1,
            stockBefore: 10,
            stockAfter: 9,
            adherenceScore: 100
          },
          {
            id: '2',
            medicationId,
            action: 'taken',
            timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), // 2 days ago
            notes: 'Taken as prescribed',
            doseAmount: 1,
            stockBefore: 11,
            stockAfter: 10,
            adherenceScore: 100
          }
        ]
        
        return history
      }
    } catch (error) {
      console.error('❌ Failed to get medication history:', error)
      return []
    }
  },

  async getAdherenceTracking(medicationId: string): Promise<AdherenceTracking | null> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<AdherenceTracking>(
          API_ENDPOINTS.MEDICATIONS.ADHERENCE.TRACKING(medicationId)
        )
        return response
      } else {
        // Mock adherence tracking
        const medication = mockMedications.find(med => med.id === medicationId)
        if (!medication) return null
        
        const history = await this.getMedicationHistory(medicationId)
        const takenDoses = history.filter(h => h.action === 'taken').length
        const missedDoses = history.filter(h => h.action === 'missed').length
        const totalDoses = takenDoses + missedDoses
        const adherenceRate = totalDoses > 0 ? (takenDoses / totalDoses) * 100 : 0
        
        return {
          medicationId,
          medication,
          totalDoses,
          takenDoses,
          missedDoses,
          adherenceRate,
          streakDays: 5, // Mock streak
          lastTaken: history[0]?.timestamp || '',
          nextDose: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(), // Tomorrow
          history
        }
      }
    } catch (error) {
      console.error('❌ Failed to get adherence tracking:', error)
      return null
    }
  },

  // 10. Proper error handling for failed batch operations
  async processBatchWithRetry(
    medications: MedicationFormData[], 
    maxRetries: number = 3
  ): Promise<BatchMedicationResponse> {
    try {
      console.log('🔄 Processing batch with retry logic:', medications.length)
      
      let lastError: Error | null = null
      
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          console.log(`📦 Batch attempt ${attempt}/${maxRetries}`)
          
          // Validate all medications first
          const validationPromises = medications.map(med => this.validateMedication(med))
          const validations = await Promise.all(validationPromises)
          
          const invalidMedications = validations.filter(v => !v.isValid)
          if (invalidMedications.length > 0) {
            console.warn(`⚠️ ${invalidMedications.length} medications failed validation`)
          }
          
          // Create batch
          const result = await this.createBatchMedications(medications)
          
          // Check if we need to retry
          if (result.failed === 0 || result.successful > result.failed) {
            console.log(`✅ Batch completed successfully: ${result.successful}/${result.total}`)
            return result
          } else {
            console.warn(`⚠️ Batch partially failed: ${result.successful}/${result.total}`)
            // If more than 50% succeeded, don't retry
            if (result.successful / result.total > 0.5) {
              return result
            }
            throw new Error(`Batch failed: ${result.failed} medications failed`)
          }
        } catch (error) {
          lastError = error instanceof Error ? error : new Error('Unknown error')
          console.error(`❌ Batch attempt ${attempt} failed:`, lastError.message)
          
          if (attempt < maxRetries) {
            // Wait before retrying (exponential backoff)
            const delay = Math.pow(2, attempt) * 1000
            console.log(`⏳ Waiting ${delay}ms before retry...`)
            await new Promise(resolve => setTimeout(resolve, delay))
          }
        }
      }
      
      // All retries failed
      throw lastError || new Error('All batch attempts failed')
    } catch (error) {
      console.error('❌ All batch processing attempts failed:', error)
      
      // Return a response with all failures
      return {
        total: medications.length,
        successful: 0,
        failed: medications.length,
        results: medications.map(med => ({
          success: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        })),
        errors: [error instanceof Error ? error.message : 'Unknown error'],
        warnings: []
      }
    }
  },

  // Additional utility methods

  // Get drug database information
  async getDrugDatabaseInfo(medicationName: string): Promise<DrugDatabaseEntry | null> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<DrugDatabaseEntry>(
          `${API_ENDPOINTS.MEDICATIONS.VALIDATION.DRUG_DATABASE}?name=${encodeURIComponent(medicationName)}`
        )
        return response
      } else {
        // Mock drug database info
        return {
          id: 'mock-drug-1',
          name: medicationName,
          genericName: medicationName,
          brandNames: [medicationName],
          activeIngredients: ['Active ingredient'],
          strength: 'Unknown',
          dosageForm: 'tablet',
          manufacturer: 'Unknown',
          description: 'Mock drug description',
          sideEffects: ['Nausea', 'Headache'],
          contraindications: ['Allergy to active ingredient'],
          interactions: [],
          pregnancyCategory: 'C',
          breastfeedingCategory: 'Unknown',
          pediatricUse: 'Consult healthcare provider',
          geriatricUse: 'Consult healthcare provider',
          renalDoseAdjustment: 'May require adjustment',
          hepaticDoseAdjustment: 'May require adjustment',
          storageInstructions: 'Store at room temperature',
          disposalInstructions: 'Dispose of properly',
          cost: 25.00,
          availability: 'available'
        }
      }
    } catch (error) {
      console.error('❌ Failed to get drug database info:', error)
      return null
    }
  },

  // Get cost analysis
  async getCostAnalysis(medicationName: string): Promise<CostAnalysis | null> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<CostAnalysis>(
          `${API_ENDPOINTS.MEDICATIONS.ENRICHMENT.COST_ANALYSIS}?name=${encodeURIComponent(medicationName)}`
        )
        return response
      } else {
        // Mock cost analysis
        return {
          averageCost: 25.00,
          costRange: { min: 20.00, max: 30.00 },
          genericAvailable: true,
          genericCost: 15.00,
          insuranceCoverage: 80,
          outOfPocketCost: 5.00,
          costPerDose: 0.83,
          monthlyCost: 25.00
        }
      }
    } catch (error) {
      console.error('❌ Failed to get cost analysis:', error)
      return null
    }
  },

  // Get availability information
  async getAvailabilityInfo(medicationName: string): Promise<AvailabilityInfo | null> {
    try {
      if (shouldUseRealApi()) {
        const response = await apiClientEnhanced.get<AvailabilityInfo>(
          `${API_ENDPOINTS.MEDICATIONS.ENRICHMENT.AVAILABILITY}?name=${encodeURIComponent(medicationName)}`
        )
        return response
      } else {
        // Mock availability info
        return {
          isAvailable: true,
          stockStatus: 'in_stock',
          pharmacies: [
            {
              name: 'Local Pharmacy',
              address: '123 Main St',
              phone: '555-1234',
              distance: 2.5,
              stock: 50,
              price: 25.00
            }
          ],
          onlineAvailability: true,
          prescriptionRequired: true
        }
      }
    } catch (error) {
      console.error('❌ Failed to get availability info:', error)
      return null
    }
  }
}