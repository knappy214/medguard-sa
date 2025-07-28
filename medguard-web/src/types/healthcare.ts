// Healthcare-specific type definitions

export interface Patient {
  id: string
  name: string
  email?: string
  phone?: string
  dateOfBirth?: string
  medicalRecordNumber: string
  status: 'active' | 'inactive' | 'pending'
  createdAt: string
  updatedAt: string
}

export interface Medication {
  id: string
  name: string
  dosage: string
  frequency: string
  instructions?: string
  patientId: string
  status: 'active' | 'discontinued' | 'pending'
  startDate: string
  endDate?: string
  createdAt: string
  updatedAt: string
}

export interface MedicationSchedule {
  id: string
  medicationId: string
  patientId: string
  time: string
  dayOfWeek?: number // 0-6, where 0 is Sunday
  isActive: boolean
  lastTaken?: string
  nextDue: string
  status: 'scheduled' | 'taken' | 'missed' | 'overdue'
}

export interface Alert {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
  patientId?: string
  medicationId?: string
  isRead: boolean
  createdAt: string
  expiresAt?: string
}

export interface HealthcareFormData {
  patientName: string
  medication: string
  dosage: string
  schedule: string
  email: string
  phone: string
}

// Component prop types
export interface HealthcareCardProps {
  title: string
  subtitle?: string
  icon?: string
  status?: string
  statusType?: 'success' | 'warning' | 'error' | 'info' | 'neutral'
}

export interface HealthcareButtonProps {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'ghost' | 'outline'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  icon?: string
  type?: 'button' | 'submit' | 'reset'
  ariaLabel?: string
  ariaDescribedby?: string
}

export interface HealthcareInputProps {
  modelValue?: string | number
  label?: string
  placeholder?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search' | 'date' | 'time' | 'datetime-local'
  disabled?: boolean
  required?: boolean
  icon?: string
  helpText?: string
  errorMessage?: string
  min?: string | number
  max?: string | number
  step?: string | number
  pattern?: string
  ariaDescribedby?: string
}

// API response types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  errors?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  data: T[]
  pagination: {
    page: number
    perPage: number
    total: number
    totalPages: number
  }
}

// Form validation types
export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: any) => boolean | string
}

export interface ValidationRules {
  [key: string]: ValidationRule
}

// Theme configuration
export interface HealthcareTheme {
  primary: string
  secondary: string
  accent: string
  neutral: string
  success: string
  warning: string
  error: string
  info: string
}

// Accessibility configuration
export interface AccessibilityConfig {
  highContrast: boolean
  reducedMotion: boolean
  fontSize: 'small' | 'medium' | 'large'
  screenReader: boolean
} 