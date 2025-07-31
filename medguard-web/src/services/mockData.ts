import type { 
  Medication, 
  MedicationSchedule, 
  StockAlert, 
  StockAnalytics 
} from '@/types/medication'

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

export const mockStockAnalytics: StockAnalytics = {
  daily_usage_rate: 3,
  weekly_usage_rate: 21,
  monthly_usage_rate: 90,
  days_until_stockout: 15,
  predicted_stockout_date: '2024-01-30T10:00:00Z',
  recommended_order_quantity: 50,
  recommended_order_date: '2024-01-25T10:00:00Z',
  seasonal_factor: 1.0,
  usage_volatility: 0.2,
  stockout_confidence: 0.85,
  last_calculated: '2024-01-15T10:00:00Z',
  calculation_window_days: 30
} 