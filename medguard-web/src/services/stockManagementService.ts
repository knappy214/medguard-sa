import apiClientEnhanced, { ApiError, NetworkError } from './apiClient'
import { API_ENDPOINTS, shouldUseRealApi } from '@/config/api'
import authService from './authService'
import type { 
  Medication, 
  StockAnalytics, 
  StockAlert,
  MedicationHistory,
  AdherenceTracking,
  PrescriptionRenewal,
  CostAnalysis,
  AvailabilityInfo,
  PharmacyInfo
} from '@/types/medication'

// Enhanced types for stock management
export interface StockCalculation {
  currentStock: number
  dailyUsage: number
  weeklyUsage: number
  monthlyUsage: number
  daysUntilStockout: number | null
  predictedStockoutDate: string | null
  recommendedOrderQuantity: number
  recommendedOrderDate: string | null
  confidence: number
  lastCalculated: string
}

export interface InsulinPenCalculation {
  totalPens: number
  unitsPerPen: number
  totalUnits: number
  dailyUnits: number
  daysRemaining: number
  pensRemaining: number
  partialPenUnits: number
  refillDate: string | null
}

export interface LiquidMedicationCalculation {
  totalVolume: number
  volumeUnit: string
  dailyVolume: number
  daysRemaining: number
  remainingVolume: number
  refillDate: string | null
  concentration: number
  concentrationUnit: string
}

export interface WasteTracking {
  medicationId: string
  medication: Medication
  wastedAmount: number
  wasteReason: 'expired' | 'damaged' | 'discontinued' | 'allergic_reaction' | 'side_effects' | 'other'
  wasteDate: string
  cost: number
  notes: string
  reportedBy: string
}

export interface AdherencePattern {
  medicationId: string
  medication: Medication
  adherenceRate: number
  missedDoses: number
  takenDoses: number
  totalDoses: number
  streakDays: number
  lastTaken: string
  nextDose: string
  patternAnalysis: {
    timeOfDay: { [key: string]: number }
    dayOfWeek: { [key: string]: number }
    monthlyTrend: { [key: string]: number }
  }
}

export interface PharmacyComparison {
  medicationId: string
  medication: Medication
  pharmacies: PharmacyInfo[]
  bestPrice: number
  bestPharmacy: string
  averagePrice: number
  priceRange: { min: number; max: number }
  availability: 'in_stock' | 'low_stock' | 'out_of_stock'
  deliveryOptions: string[]
  prescriptionRequired: boolean
}

export interface PrescriptionRepeat {
  prescriptionId: string
  originalPrescription: any
  refillsRemaining: number
  totalRefills: number
  renewalDate: string
  expiryDate: string
  status: 'active' | 'expired' | 'renewed' | 'cancelled'
  reminderSent: boolean
  reminderDate?: string
  autoRenewal: boolean
}

export interface BatchExpiration {
  medicationId: string
  medication: Medication
  batchNumber: string
  expirationDate: string
  daysUntilExpiration: number
  quantity: number
  status: 'safe' | 'warning' | 'critical' | 'expired'
  actionRequired: boolean
  recommendedAction: string
}

export interface StockReport {
  reportId: string
  reportType: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual'
  generatedAt: string
  period: {
    start: string
    end: string
  }
  summary: {
    totalMedications: number
    lowStockItems: number
    outOfStockItems: number
    expiringItems: number
    totalValue: number
    wasteValue: number
  }
  details: {
    lowStock: Medication[]
    outOfStock: Medication[]
    expiring: BatchExpiration[]
    waste: WasteTracking[]
    adherence: AdherencePattern[]
  }
  recommendations: string[]
}

export interface EmergencyStockAlert {
  alertId: string
  medicationId: string
  medication: Medication
  alertType: 'critical_medication' | 'life_sustaining' | 'controlled_substance' | 'specialty_medication'
  severity: 'low' | 'medium' | 'high' | 'critical'
  message: string
  currentStock: number
  daysRemaining: number
  urgency: 'immediate' | 'within_24h' | 'within_48h' | 'within_week'
  actionRequired: string
  contactInfo: {
    pharmacy: string
    doctor: string
    emergency: string
  }
  createdAt: string
  acknowledged: boolean
  resolved: boolean
}

export interface ReorderAlert {
  alertId: string
  medicationId: string
  medication: Medication
  alertDate: string
  daysUntilStockout: number
  recommendedOrderQuantity: number
  recommendedOrderDate: string
  urgency: 'low' | 'medium' | 'high' | 'critical'
  status: 'pending' | 'ordered' | 'received' | 'cancelled'
  orderDetails?: {
    orderId: string
    orderDate: string
    expectedDelivery: string
    actualDelivery?: string
    quantity: number
    cost: number
    pharmacy: string
  }
}

// South African pharmacy chains for price comparison
const SA_PHARMACY_CHAINS = [
  'Clicks',
  'Dis-Chem',
  'Medirite',
  'Alpha Pharm',
  'Medplus',
  'Pharmacy Direct',
  'Netcare Pharmacy',
  'Life Pharmacy',
  'Medicross',
  'Mediclinic Pharmacy'
]

class StockManagementService {
  private readonly baseUrl: string
  private readonly useMockData: boolean

  constructor() {
    this.baseUrl = API_ENDPOINTS.MEDICATIONS.LIST
    this.useMockData = !shouldUseRealApi()
  }

  /**
   * 1. Calculates precise stock levels based on prescription quantities and frequencies
   */
  async calculateStockLevels(medicationId: string): Promise<StockCalculation> {
    try {
      if (this.useMockData) {
        return this.getMockStockCalculation(medicationId)
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ANALYTICS(medicationId)}stock-calculation/`
      )

      return response.data
    } catch (error) {
      console.error('Error calculating stock levels:', error)
      throw new Error('Failed to calculate stock levels')
    }
  }

  /**
   * 2. Implements predictive analytics for medication refill dates
   */
  async getPredictiveRefillDates(medicationId: string): Promise<{
    predictedRefillDate: string
    confidence: number
    factors: string[]
    alternativeDates: string[]
  }> {
    try {
      if (this.useMockData) {
        return this.getMockPredictiveRefill(medicationId)
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ANALYTICS(medicationId)}predictive-refill/`
      )

      return response.data
    } catch (error) {
      console.error('Error getting predictive refill dates:', error)
      throw new Error('Failed to get predictive refill dates')
    }
  }

  /**
   * 3. Handles complex calculations for insulin pens and liquid medications
   */
  async calculateInsulinPenStock(medicationId: string): Promise<InsulinPenCalculation> {
    try {
      if (this.useMockData) {
        return this.getMockInsulinPenCalculation(medicationId)
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ANALYTICS(medicationId)}insulin-pen-calculation/`
      )

      return response.data
    } catch (error) {
      console.error('Error calculating insulin pen stock:', error)
      throw new Error('Failed to calculate insulin pen stock')
    }
  }

  async calculateLiquidMedicationStock(medicationId: string): Promise<LiquidMedicationCalculation> {
    try {
      if (this.useMockData) {
        return this.getMockLiquidMedicationCalculation(medicationId)
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ANALYTICS(medicationId)}liquid-medication-calculation/`
      )

      return response.data
    } catch (error) {
      console.error('Error calculating liquid medication stock:', error)
      throw new Error('Failed to calculate liquid medication stock')
    }
  }

  /**
   * 4. Creates automatic reorder alerts 5 working days before stock depletion
   */
  async createReorderAlerts(): Promise<ReorderAlert[]> {
    try {
      if (this.useMockData) {
        return this.getMockReorderAlerts()
      }

      const response = await apiClientEnhanced.post(
        `${API_ENDPOINTS.MEDICATIONS.ALERTS}reorder-alerts/`
      )

      return response.data
    } catch (error) {
      console.error('Error creating reorder alerts:', error)
      throw new Error('Failed to create reorder alerts')
    }
  }

  async getReorderAlerts(): Promise<ReorderAlert[]> {
    try {
      if (this.useMockData) {
        return this.getMockReorderAlerts()
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ALERTS}reorder-alerts/`
      )

      return response.data
    } catch (error) {
      console.error('Error getting reorder alerts:', error)
      throw new Error('Failed to get reorder alerts')
    }
  }

  /**
   * 5. Tracks medication waste and adherence patterns
   */
  async trackWaste(wasteData: Omit<WasteTracking, 'wasteDate' | 'reportedBy'>): Promise<WasteTracking> {
    try {
      if (this.useMockData) {
        return this.getMockWasteTracking(wasteData)
      }

      const response = await apiClientEnhanced.post(
        `${API_ENDPOINTS.MEDICATIONS.LOGS}waste-tracking/`,
        {
          ...wasteData,
          wasteDate: new Date().toISOString(),
          reportedBy: await this.getCurrentUserId()
        }
      )

      return response.data
    } catch (error) {
      console.error('Error tracking waste:', error)
      throw new Error('Failed to track waste')
    }
  }

  async getWasteHistory(medicationId?: string): Promise<WasteTracking[]> {
    try {
      if (this.useMockData) {
        return this.getMockWasteHistory(medicationId)
      }

      const url = medicationId 
        ? `${API_ENDPOINTS.MEDICATIONS.LOGS}waste-tracking/?medication_id=${medicationId}`
        : `${API_ENDPOINTS.MEDICATIONS.LOGS}waste-tracking/`

      const response = await apiClientEnhanced.get(url)
      return response.data
    } catch (error) {
      console.error('Error getting waste history:', error)
      throw new Error('Failed to get waste history')
    }
  }

  async getAdherencePatterns(medicationId?: string): Promise<AdherencePattern[]> {
    try {
      if (this.useMockData) {
        return this.getMockAdherencePatterns(medicationId)
      }

      const url = medicationId 
        ? `${API_ENDPOINTS.MEDICATIONS.ADHERENCE.STATS}?medication_id=${medicationId}`
        : API_ENDPOINTS.MEDICATIONS.ADHERENCE.STATS

      const response = await apiClientEnhanced.get(url)
      return response.data
    } catch (error) {
      console.error('Error getting adherence patterns:', error)
      throw new Error('Failed to get adherence patterns')
    }
  }

  /**
   * 6. Integrates with South African pharmacy chains for price comparison
   */
  async getPharmacyPriceComparison(medicationId: string): Promise<PharmacyComparison> {
    try {
      if (this.useMockData) {
        return this.getMockPharmacyComparison(medicationId)
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ENRICHMENT.AVAILABILITY}?medication_id=${medicationId}&country=ZA`
      )

      return response.data
    } catch (error) {
      console.error('Error getting pharmacy price comparison:', error)
      throw new Error('Failed to get pharmacy price comparison')
    }
  }

  async searchPharmacies(medicationName: string, location?: string): Promise<PharmacyInfo[]> {
    try {
      if (this.useMockData) {
        return this.getMockPharmacySearch(medicationName, location)
      }

      const params = new URLSearchParams({ medication_name: medicationName })
      if (location) params.append('location', location)

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ENRICHMENT.AVAILABILITY}search-pharmacies/?${params}`
      )

      return response.data
    } catch (error) {
      console.error('Error searching pharmacies:', error)
      throw new Error('Failed to search pharmacies')
    }
  }

  /**
   * 7. Handles prescription repeats and renewal tracking
   */
  async getPrescriptionRepeats(): Promise<PrescriptionRepeat[]> {
    try {
      if (this.useMockData) {
        return this.getMockPrescriptionRepeats()
      }

      const response = await apiClientEnhanced.get(
        API_ENDPOINTS.MEDICATIONS.PRESCRIPTIONS.RENEWALS
      )

      return response.data
    } catch (error) {
      console.error('Error getting prescription repeats:', error)
      throw new Error('Failed to get prescription repeats')
    }
  }

  async createPrescriptionRenewal(prescriptionId: string, renewalData: Partial<PrescriptionRepeat>): Promise<PrescriptionRepeat> {
    try {
      if (this.useMockData) {
        return this.getMockPrescriptionRenewal(prescriptionId, renewalData)
      }

      const response = await apiClientEnhanced.post(
        API_ENDPOINTS.MEDICATIONS.PRESCRIPTIONS.RENEWALS,
        { prescription_id: prescriptionId, ...renewalData }
      )

      return response.data
    } catch (error) {
      console.error('Error creating prescription renewal:', error)
      throw new Error('Failed to create prescription renewal')
    }
  }

  async setAutoRenewal(prescriptionId: string, enabled: boolean): Promise<boolean> {
    try {
      if (this.useMockData) {
        return true
      }

      const response = await apiClientEnhanced.patch(
        `${API_ENDPOINTS.MEDICATIONS.PRESCRIPTIONS.RENEWAL_DETAIL(prescriptionId)}`,
        { auto_renewal: enabled }
      )

      return response.data.success
    } catch (error) {
      console.error('Error setting auto renewal:', error)
      throw new Error('Failed to set auto renewal')
    }
  }

  /**
   * 8. Implements batch expiration date monitoring
   */
  async getBatchExpirations(medicationId?: string): Promise<BatchExpiration[]> {
    try {
      if (this.useMockData) {
        return this.getMockBatchExpirations(medicationId)
      }

      const url = medicationId 
        ? `${API_ENDPOINTS.MEDICATIONS.ALERTS}batch-expirations/?medication_id=${medicationId}`
        : `${API_ENDPOINTS.MEDICATIONS.ALERTS}batch-expirations/`

      const response = await apiClientEnhanced.get(url)
      return response.data
    } catch (error) {
      console.error('Error getting batch expirations:', error)
      throw new Error('Failed to get batch expirations')
    }
  }

  async setExpirationAlert(medicationId: string, daysBeforeExpiration: number): Promise<boolean> {
    try {
      if (this.useMockData) {
        return true
      }

      const response = await apiClientEnhanced.post(
        `${API_ENDPOINTS.MEDICATIONS.ALERTS}expiration-alerts/`,
        {
          medication_id: medicationId,
          days_before_expiration: daysBeforeExpiration
        }
      )

      return response.data.success
    } catch (error) {
      console.error('Error setting expiration alert:', error)
      throw new Error('Failed to set expiration alert')
    }
  }

  /**
   * 9. Creates stock reports for healthcare providers
   */
  async generateStockReport(
    reportType: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual',
    startDate?: string,
    endDate?: string
  ): Promise<StockReport> {
    try {
      if (this.useMockData) {
        return this.getMockStockReport(reportType, startDate, endDate)
      }

      const response = await apiClientEnhanced.post(
        `${API_ENDPOINTS.MEDICATIONS.ANALYTICS('')}generate-report/`,
        {
          report_type: reportType,
          start_date: startDate,
          end_date: endDate
        }
      )

      return response.data
    } catch (error) {
      console.error('Error generating stock report:', error)
      throw new Error('Failed to generate stock report')
    }
  }

  async exportStockReport(reportId: string, format: 'pdf' | 'csv' | 'excel'): Promise<Blob> {
    try {
      if (this.useMockData) {
        return new Blob(['Mock report data'], { type: 'application/pdf' })
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ANALYTICS('')}export-report/${reportId}/?format=${format}`,
        { responseType: 'blob' }
      )

      return response.data
    } catch (error) {
      console.error('Error exporting stock report:', error)
      throw new Error('Failed to export stock report')
    }
  }

  /**
   * 10. Includes emergency stock notifications for critical medications
   */
  async getEmergencyStockAlerts(): Promise<EmergencyStockAlert[]> {
    try {
      if (this.useMockData) {
        return this.getMockEmergencyStockAlerts()
      }

      const response = await apiClientEnhanced.get(
        `${API_ENDPOINTS.MEDICATIONS.ALERTS}emergency-alerts/`
      )

      return response.data
    } catch (error) {
      console.error('Error getting emergency stock alerts:', error)
      throw new Error('Failed to get emergency stock alerts')
    }
  }

  async acknowledgeEmergencyAlert(alertId: string): Promise<boolean> {
    try {
      if (this.useMockData) {
        return true
      }

      const response = await apiClientEnhanced.patch(
        `${API_ENDPOINTS.MEDICATIONS.ALERTS}emergency-alerts/${alertId}/acknowledge/`
      )

      return response.data.success
    } catch (error) {
      console.error('Error acknowledging emergency alert:', error)
      throw new Error('Failed to acknowledge emergency alert')
    }
  }

  async resolveEmergencyAlert(alertId: string, resolution: string): Promise<boolean> {
    try {
      if (this.useMockData) {
        return true
      }

      const response = await apiClientEnhanced.patch(
        `${API_ENDPOINTS.MEDICATIONS.ALERTS}emergency-alerts/${alertId}/resolve/`,
        { resolution }
      )

      return response.data.success
    } catch (error) {
      console.error('Error resolving emergency alert:', error)
      throw new Error('Failed to resolve emergency alert')
    }
  }

  // Utility methods
  private async getCurrentUserId(): Promise<string> {
    try {
      const profile = await authService.getProfile()
      return profile?.id || 'unknown'
    } catch (error) {
      return 'unknown'
    }
  }

  // Mock data methods for development
  private getMockStockCalculation(medicationId: string): StockCalculation {
    return {
      currentStock: 30,
      dailyUsage: 2,
      weeklyUsage: 14,
      monthlyUsage: 60,
      daysUntilStockout: 15,
      predictedStockoutDate: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
      recommendedOrderQuantity: 60,
      recommendedOrderDate: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(),
      confidence: 0.85,
      lastCalculated: new Date().toISOString()
    }
  }

  private getMockPredictiveRefill(medicationId: string) {
    return {
      predictedRefillDate: new Date(Date.now() + 20 * 24 * 60 * 60 * 1000).toISOString(),
      confidence: 0.78,
      factors: ['Historical usage patterns', 'Adherence rate', 'Seasonal variations'],
      alternativeDates: [
        new Date(Date.now() + 18 * 24 * 60 * 60 * 1000).toISOString(),
        new Date(Date.now() + 22 * 24 * 60 * 60 * 1000).toISOString()
      ]
    }
  }

  private getMockInsulinPenCalculation(medicationId: string): InsulinPenCalculation {
    return {
      totalPens: 5,
      unitsPerPen: 300,
      totalUnits: 1500,
      dailyUnits: 50,
      daysRemaining: 30,
      pensRemaining: 5,
      partialPenUnits: 0,
      refillDate: new Date(Date.now() + 25 * 24 * 60 * 60 * 1000).toISOString()
    }
  }

  private getMockLiquidMedicationCalculation(medicationId: string): LiquidMedicationCalculation {
    return {
      totalVolume: 100,
      volumeUnit: 'ml',
      dailyVolume: 5,
      daysRemaining: 20,
      remainingVolume: 100,
      refillDate: new Date(Date.now() + 15 * 24 * 60 * 60 * 1000).toISOString(),
      concentration: 10,
      concentrationUnit: 'mg/ml'
    }
  }

  private getMockReorderAlerts(): ReorderAlert[] {
    return [
      {
        alertId: '1',
        medicationId: '1',
        medication: { id: '1', name: 'Aspirin', dosage: '100mg', frequency: 'Once daily', time: '08:00', stock: 5, pill_count: 5, minStock: 10, instructions: 'Take with food', category: 'Pain Relief', isActive: true, createdAt: '', updatedAt: '' },
        alertDate: new Date().toISOString(),
        daysUntilStockout: 3,
        recommendedOrderQuantity: 30,
        recommendedOrderDate: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
        urgency: 'high',
        status: 'pending'
      }
    ]
  }

  private getMockWasteTracking(wasteData: any): WasteTracking {
    return {
      ...wasteData,
      wasteDate: new Date().toISOString(),
      reportedBy: 'current-user'
    }
  }

  private getMockWasteHistory(medicationId?: string): WasteTracking[] {
    return [
      {
        medicationId: '1',
        medication: { id: '1', name: 'Aspirin', dosage: '100mg', frequency: 'Once daily', time: '08:00', stock: 5, pill_count: 5, minStock: 10, instructions: 'Take with food', category: 'Pain Relief', isActive: true, createdAt: '', updatedAt: '' },
        wastedAmount: 10,
        wasteReason: 'expired',
        wasteDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        cost: 25.50,
        notes: 'Expired medication disposed of safely',
        reportedBy: 'user-1'
      }
    ]
  }

  private getMockAdherencePatterns(medicationId?: string): AdherencePattern[] {
    return [
      {
        medicationId: '1',
        medication: { id: '1', name: 'Aspirin', dosage: '100mg', frequency: 'Once daily', time: '08:00', stock: 5, pill_count: 5, minStock: 10, instructions: 'Take with food', category: 'Pain Relief', isActive: true, createdAt: '', updatedAt: '' },
        adherenceRate: 0.85,
        missedDoses: 3,
        takenDoses: 17,
        totalDoses: 20,
        streakDays: 5,
        lastTaken: new Date().toISOString(),
        nextDose: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
        patternAnalysis: {
          timeOfDay: { '08:00': 15, '09:00': 2 },
          dayOfWeek: { 'Monday': 3, 'Tuesday': 3, 'Wednesday': 3, 'Thursday': 3, 'Friday': 3, 'Saturday': 1, 'Sunday': 1 },
          monthlyTrend: { 'January': 30, 'February': 28 }
        }
      }
    ]
  }

  private getMockPharmacyComparison(medicationId: string): PharmacyComparison {
    return {
      medicationId,
      medication: { id: medicationId, name: 'Aspirin', dosage: '100mg', frequency: 'Once daily', time: '08:00', stock: 5, pill_count: 5, minStock: 10, instructions: 'Take with food', category: 'Pain Relief', isActive: true, createdAt: '', updatedAt: '' },
      pharmacies: [
        { name: 'Clicks', address: '123 Main St, Cape Town', phone: '+27 21 123 4567', distance: 2.5, stock: 50, price: 45.99 },
        { name: 'Dis-Chem', address: '456 Oak Ave, Cape Town', phone: '+27 21 987 6543', distance: 3.2, stock: 30, price: 42.50 },
        { name: 'Medirite', address: '789 Pine Rd, Cape Town', phone: '+27 21 555 1234', distance: 1.8, stock: 25, price: 48.75 }
      ],
      bestPrice: 42.50,
      bestPharmacy: 'Dis-Chem',
      averagePrice: 45.75,
      priceRange: { min: 42.50, max: 48.75 },
      availability: 'in_stock',
      deliveryOptions: ['Same day delivery', 'Next day delivery', 'Store pickup'],
      prescriptionRequired: false
    }
  }

  private getMockPharmacySearch(medicationName: string, location?: string): PharmacyInfo[] {
    return [
      { name: 'Clicks', address: '123 Main St, Cape Town', phone: '+27 21 123 4567', distance: 2.5, stock: 50, price: 45.99 },
      { name: 'Dis-Chem', address: '456 Oak Ave, Cape Town', phone: '+27 21 987 6543', distance: 3.2, stock: 30, price: 42.50 },
      { name: 'Medirite', address: '789 Pine Rd, Cape Town', phone: '+27 21 555 1234', distance: 1.8, stock: 25, price: 48.75 }
    ]
  }

  private getMockPrescriptionRepeats(): PrescriptionRepeat[] {
    return [
      {
        prescriptionId: '1',
        originalPrescription: { id: '1', patientName: 'John Doe', prescribingDoctor: 'Dr. Smith', prescriptionDate: '2024-01-01', medications: [], status: 'active' },
        refillsRemaining: 2,
        totalRefills: 5,
        renewalDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        expiryDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
        status: 'active',
        reminderSent: false,
        autoRenewal: true
      }
    ]
  }

  private getMockPrescriptionRenewal(prescriptionId: string, renewalData: any): PrescriptionRepeat {
    return {
      prescriptionId,
      originalPrescription: { id: prescriptionId, patientName: 'John Doe', prescribingDoctor: 'Dr. Smith', prescriptionDate: '2024-01-01', medications: [], status: 'active' },
      refillsRemaining: 5,
      totalRefills: 5,
      renewalDate: new Date().toISOString(),
      expiryDate: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'active',
      reminderSent: false,
      autoRenewal: true,
      ...renewalData
    }
  }

  private getMockBatchExpirations(medicationId?: string): BatchExpiration[] {
    return [
      {
        medicationId: '1',
        medication: { id: '1', name: 'Aspirin', dosage: '100mg', frequency: 'Once daily', time: '08:00', stock: 5, pill_count: 5, minStock: 10, instructions: 'Take with food', category: 'Pain Relief', isActive: true, createdAt: '', updatedAt: '' },
        batchNumber: 'BATCH001',
        expirationDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        daysUntilExpiration: 30,
        quantity: 50,
        status: 'warning',
        actionRequired: true,
        recommendedAction: 'Use this batch first to minimize waste'
      }
    ]
  }

  private getMockStockReport(reportType: string, startDate?: string, endDate?: string): StockReport {
    return {
      reportId: '1',
      reportType: reportType as any,
      generatedAt: new Date().toISOString(),
      period: {
        start: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        end: endDate || new Date().toISOString()
      },
      summary: {
        totalMedications: 15,
        lowStockItems: 3,
        outOfStockItems: 1,
        expiringItems: 2,
        totalValue: 1250.75,
        wasteValue: 45.50
      },
      details: {
        lowStock: [],
        outOfStock: [],
        expiring: [],
        waste: [],
        adherence: []
      },
      recommendations: [
        'Order refills for low stock medications',
        'Dispose of expired medications safely',
        'Review adherence patterns for improvement'
      ]
    }
  }

  private getMockEmergencyStockAlerts(): EmergencyStockAlert[] {
    return [
      {
        alertId: '1',
        medicationId: '1',
        medication: { id: '1', name: 'Insulin', dosage: '10 units', frequency: 'Twice daily', time: '08:00', stock: 2, pill_count: 2, minStock: 5, instructions: 'Inject as prescribed', category: 'Diabetes', isActive: true, createdAt: '', updatedAt: '' },
        alertType: 'critical_medication',
        severity: 'critical',
        message: 'Critical medication running low - immediate action required',
        currentStock: 2,
        daysRemaining: 1,
        urgency: 'immediate',
        actionRequired: 'Contact pharmacy immediately for emergency refill',
        contactInfo: {
          pharmacy: '+27 21 123 4567',
          doctor: '+27 21 987 6543',
          emergency: '112'
        },
        createdAt: new Date().toISOString(),
        acknowledged: false,
        resolved: false
      }
    ]
  }
}

// Export singleton instance
const stockManagementService = new StockManagementService()
export default stockManagementService 