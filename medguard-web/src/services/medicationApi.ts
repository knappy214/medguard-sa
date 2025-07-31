import axios from 'axios'
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

// Configure axios to use Vite proxy (no base URL needed)
const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token and security headers
api.interceptors.request.use(async (config) => {
  try {
    // Get access token from auth service
    const token = await authService.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    // Add HIPAA security headers
    config.headers['X-Security-Level'] = 'HIPAA'
    config.headers['X-Client-Version'] = '1.0.0'
    
    // Add timestamp for request tracking
    config.headers['X-Request-Timestamp'] = Date.now().toString()
    
    return config
  } catch (error) {
    console.error('Failed to add authentication headers:', error)
    return config
  }
})

// Response interceptor for error handling and security logging
api.interceptors.response.use(
  (response) => {
    // Log successful API calls for audit trail
    authService.logSecurityEvent('API_SUCCESS', {
      endpoint: response.config.url,
      method: response.config.method,
      statusCode: response.status
    })
    return response
  },
  async (error) => {
    // Log failed API calls for security monitoring
    authService.logSecurityEvent('API_ERROR', {
      endpoint: error.config?.url,
      method: error.config?.method,
      statusCode: error.response?.status,
      error: error.message
    })
    
    // Handle authentication errors
    if (error.response?.status === 401) {
      console.error('Authentication error - redirecting to login')
      await authService.logout('Authentication failed')
      // Redirect to login page
      window.location.href = '/login'
    }
    
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const medicationApi = {
  // Get all medications
  async getMedications(): Promise<Medication[]> {
    try {
      const response = await api.get<ApiResponse<Medication[]>>('/api/medications/')
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch medications:', error)
      return []
    }
  },

  // Get medication by ID
  async getMedication(id: string): Promise<Medication | null> {
    try {
      const response = await api.get<ApiResponse<Medication>>(`/api/medications/${id}/`)
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch medication:', error)
      return null
    }
  },

  // Create new medication
  async createMedication(data: MedicationFormData): Promise<Medication | null> {
    try {
      const response = await api.post<ApiResponse<Medication>>('/api/medications/', data)
      return response.data.data
    } catch (error) {
      console.error('Failed to create medication:', error)
      return null
    }
  },

  // Update medication
  async updateMedication(id: string, data: Partial<MedicationFormData>): Promise<Medication | null> {
    try {
      const response = await api.put<ApiResponse<Medication>>(`/api/medications/${id}/`, data)
      return response.data.data
    } catch (error) {
      console.error('Failed to update medication:', error)
      return null
    }
  },

  // Delete medication
  async deleteMedication(id: string): Promise<boolean> {
    try {
      await api.delete(`/api/medications/${id}/`)
      return true
    } catch (error) {
      console.error('Failed to delete medication:', error)
      return false
    }
  },

  // Get today's schedule
  async getTodaySchedule(): Promise<MedicationSchedule[]> {
    try {
      const response = await api.get<ApiResponse<MedicationSchedule[]>>('/api/medications/schedule/today/')
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch today\'s schedule:', error)
      return []
    }
  },

  // Mark medication as taken
  async markAsTaken(scheduleId: string, notes?: string): Promise<boolean> {
    try {
      await api.post(`/api/medications/schedule/${scheduleId}/mark-taken/`, { notes })
      return true
    } catch (error) {
      console.error('Failed to mark medication as taken:', error)
      return false
    }
  },

  // Mark medication as missed
  async markAsMissed(scheduleId: string): Promise<boolean> {
    try {
      await api.post(`/api/medications/schedule/${scheduleId}/mark-missed/`)
      return true
    } catch (error) {
      console.error('Failed to mark medication as missed:', error)
      return false
    }
  },

  // Get stock alerts
  async getStockAlerts(): Promise<StockAlert[]> {
    try {
      const response = await api.get<ApiResponse<StockAlert[]>>('/api/medications/alerts/stock/')
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch stock alerts:', error)
      return []
    }
  },

  // Mark alert as read
  async markAlertAsRead(alertId: string): Promise<boolean> {
    try {
      await api.post(`/api/medications/alerts/${alertId}/mark-read/`)
      return true
    } catch (error) {
      console.error('Failed to mark alert as read:', error)
      return false
    }
  },

  // Update stock level
  async updateStock(medicationId: string, newStock: number): Promise<boolean> {
    try {
      await api.put(`/api/medications/${medicationId}/stock/`, { stock: newStock })
      return true
    } catch (error) {
      console.error('Failed to update stock:', error)
      return false
    }
  },

  // Get stock analytics
  async getStockAnalytics(medicationId: string): Promise<StockAnalytics> {
    try {
      const response = await api.get<ApiResponse<StockAnalytics>>(`/api/medications/${medicationId}/analytics/`)
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch stock analytics:', error)
      throw error
    }
  },

  // Get paginated medications
  async getMedicationsPaginated(page: number = 1, pageSize: number = 10): Promise<PaginatedResponse<Medication>> {
    try {
      const response = await api.get<ApiResponse<PaginatedResponse<Medication>>>('/api/medications/', {
        params: { page, page_size: pageSize }
      })
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch paginated medications:', error)
      throw error
    }
  },

  // Search medications
  async searchMedications(query: string): Promise<Medication[]> {
    try {
      const response = await api.get<ApiResponse<Medication[]>>('/api/medications/search/', {
        params: { q: query }
      })
      return response.data.data
    } catch (error) {
      console.error('Failed to search medications:', error)
      return []
    }
  },

  // Get medication history
  async getMedicationHistory(medicationId: string): Promise<any[]> {
    try {
      const response = await api.get<ApiResponse<any[]>>(`/api/medications/${medicationId}/history/`)
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch medication history:', error)
      return []
    }
  },

  // Export medication data
  async exportMedicationData(format: 'json' | 'csv' = 'json'): Promise<Blob> {
    try {
      const response = await api.get('/api/medications/export/', {
        params: { format },
        responseType: 'blob'
      })
      return response.data
    } catch (error) {
      console.error('Failed to export medication data:', error)
      throw error
    }
  },

  // Import medication data
  async importMedicationData(file: File): Promise<boolean> {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      await api.post('/api/medications/import/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return true
    } catch (error) {
      console.error('Failed to import medication data:', error)
      return false
    }
  },

  // Get medication statistics
  async getMedicationStats(): Promise<any> {
    try {
      const response = await api.get<ApiResponse<any>>('/api/medications/stats/')
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch medication statistics:', error)
      return {}
    }
  },

  // Get medication reminders
  async getMedicationReminders(): Promise<any[]> {
    try {
      const response = await api.get<ApiResponse<any[]>>('/api/medications/reminders/')
      return response.data.data
    } catch (error) {
      console.error('Failed to fetch medication reminders:', error)
      return []
    }
  },

  // Set medication reminder
  async setMedicationReminder(medicationId: string, reminderData: any): Promise<boolean> {
    try {
      await api.post(`/api/medications/${medicationId}/reminders/`, reminderData)
      return true
    } catch (error) {
      console.error('Failed to set medication reminder:', error)
      return false
    }
  },

  // Delete medication reminder
  async deleteMedicationReminder(reminderId: string): Promise<boolean> {
    try {
      await api.delete(`/api/medications/reminders/${reminderId}/`)
      return true
    } catch (error) {
      console.error('Failed to delete medication reminder:', error)
      return false
    }
  }
}

// Mock data for development/testing
export const mockMedications: Medication[] = [
  {
    id: '1',
    name: 'Paracetamol',
    dosage: '500mg',
    frequency: 'Every 6 hours',
    time: '08:00, 14:00, 20:00',
    stock: 45,
    pill_count: 45,
    minStock: 20,
    instructions: 'Take with food. Do not exceed 4 tablets per day.',
    category: 'Pain Relief',
    isActive: true,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    name: 'Amoxicillin',
    dosage: '250mg',
    frequency: 'Twice daily',
    time: '08:00, 20:00',
    stock: 12,
    pill_count: 12,
    minStock: 15,
    instructions: 'Take on an empty stomach. Complete the full course.',
    category: 'Antibiotic',
    isActive: true,
    createdAt: '2024-01-10T09:00:00Z',
    updatedAt: '2024-01-12T14:30:00Z'
  },
  {
    id: '3',
    name: 'Vitamin D',
    dosage: '1000 IU',
    frequency: 'Once daily',
    time: '08:00',
    stock: 30,
    pill_count: 30,
    minStock: 10,
    instructions: 'Take with breakfast for better absorption.',
    category: 'Vitamin',
    isActive: true,
    createdAt: '2024-01-05T11:00:00Z',
    updatedAt: '2024-01-05T11:00:00Z'
  },
  {
    id: '4',
    name: 'Ibuprofen',
    dosage: '400mg',
    frequency: 'Every 8 hours',
    time: '08:00, 16:00, 00:00',
    stock: 5,
    pill_count: 5,
    minStock: 20,
    instructions: 'Take with food. Do not take on empty stomach.',
    category: 'Pain Relief',
    isActive: true,
    createdAt: '2024-01-08T13:00:00Z',
    updatedAt: '2024-01-14T16:45:00Z'
  }
]

export const mockSchedule: MedicationSchedule[] = [
  {
    id: '1',
    medicationId: '1',
    medication: mockMedications[0],
    scheduledTime: '2024-01-15T08:00:00Z',
    status: 'taken',
    takenAt: '2024-01-15T08:05:00Z'
  },
  {
    id: '2',
    medicationId: '2',
    medication: mockMedications[1],
    scheduledTime: '2024-01-15T08:00:00Z',
    status: 'taken',
    takenAt: '2024-01-15T08:10:00Z'
  },
  {
    id: '3',
    medicationId: '3',
    medication: mockMedications[2],
    scheduledTime: '2024-01-15T08:00:00Z',
    status: 'taken',
    takenAt: '2024-01-15T08:15:00Z'
  },
  {
    id: '4',
    medicationId: '1',
    medication: mockMedications[0],
    scheduledTime: '2024-01-15T14:00:00Z',
    status: 'pending'
  },
  {
    id: '5',
    medicationId: '4',
    medication: mockMedications[3],
    scheduledTime: '2024-01-15T16:00:00Z',
    status: 'pending'
  }
]

export const mockAlerts: StockAlert[] = [
  {
    id: '1',
    medicationId: '2',
    medication: mockMedications[1],
    type: 'low_stock',
    message: 'Amoxicillin stock is running low. Only 12 tablets remaining.',
    severity: 'warning',
    createdAt: '2024-01-14T10:00:00Z',
    isRead: false
  },
  {
    id: '2',
    medicationId: '4',
    medication: mockMedications[3],
    type: 'low_stock',
    message: 'Ibuprofen stock is critically low. Only 5 tablets remaining.',
    severity: 'error',
    createdAt: '2024-01-15T09:00:00Z',
    isRead: false
  }
] 