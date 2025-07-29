export interface Medication {
  id: string
  name: string
  dosage: string
  frequency: string
  time: string
  stock: number
  pill_count: number // Added for backend compatibility
  minStock: number
  instructions: string
  category: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface MedicationSchedule {
  id: string
  medicationId: string
  medication: Medication
  scheduledTime: string
  status: 'pending' | 'taken' | 'missed'
  takenAt?: string
  notes?: string
}

export interface StockAlert {
  id: string
  medicationId: string
  medication: Medication
  type: 'low_stock' | 'out_of_stock' | 'expiring_soon'
  message: string
  severity: 'warning' | 'error' | 'info'
  createdAt: string
  isRead: boolean
}

export interface StockAnalytics {
  daily_usage_rate: number
  weekly_usage_rate: number
  monthly_usage_rate: number
  days_until_stockout: number | null
  predicted_stockout_date: string | null
  recommended_order_quantity: number
  recommended_order_date: string | null
  seasonal_factor: number
  usage_volatility: number
  stockout_confidence: number
  last_calculated: string | null
  calculation_window_days: number
}

export interface MedicationFormData {
  name: string
  dosage: string
  frequency: string
  time: string
  stock: number
  minStock: number
  instructions: string
  category: string
}

export interface ApiResponse<T> {
  data: T
  message: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  perPage: number
  totalPages: number
} 