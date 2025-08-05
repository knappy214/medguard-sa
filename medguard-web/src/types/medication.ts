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
  // New fields for enhanced medication management
  strength?: string
  manufacturer?: string
  activeIngredients?: string
  sideEffects?: string
  icd10Code?: string
  prescriptionNumber?: string
  prescribingDoctor?: string
  expirationDate?: string
  medicationImage?: string
  interactions?: string[]
  // New fields for prescription processing
  prescriptionId?: string
  isPrescription?: boolean
  renewalDate?: string
  refillsRemaining?: number
  totalRefills?: number
  adherenceRate?: number
  lastTaken?: string
  nextDose?: string
  drugDatabaseId?: string
  enrichedData?: MedicationEnrichment
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
  // Schedule information
  scheduleTiming?: 'morning' | 'noon' | 'night' | 'custom'
  scheduleCustomTime?: string
  scheduleDosageAmount?: number
  scheduleInstructions?: string
  // New enhanced fields
  strength?: string
  manufacturer?: string
  activeIngredients?: string
  sideEffects?: string
  icd10Code?: string
  prescriptionNumber?: string
  prescribingDoctor?: string
  expirationDate?: string
  medicationImage?: File | null
  interactions?: string[]
  // Bulk entry support
  isBulkEntry?: boolean
  bulkMedications?: BulkMedicationEntry[]
}

export interface BulkMedicationEntry {
  name: string
  strength: string
  dosage: string
  frequency: string
  instructions: string
  manufacturer?: string
  prescriptionNumber?: string
  prescribingDoctor?: string
}

export interface ICD10Code {
  code: string
  description: string
  category: string
}

export interface MedicationInteraction {
  severity: 'low' | 'moderate' | 'high' | 'contraindicated'
  description: string
  medications: string[]
  recommendations: string
  evidence: string
  source: string
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

// New interfaces for prescription processing
export interface ParsedPrescription {
  id: string
  patientName: string
  prescribingDoctor: string
  prescriptionDate: string
  medications: PrescriptionMedication[]
  pharmacy?: string
  totalCost?: number
  insurance?: string
  notes?: string
  imageUrl?: string
  status: 'active' | 'expired' | 'completed' | 'renewed'
}

export interface PrescriptionMedication {
  name: string
  genericName?: string
  strength: string
  dosage: string
  frequency: string
  quantity: number
  refills: number
  instructions: string
  cost?: number
  drugDatabaseId?: string
  interactions?: string[]
  sideEffects?: string[]
  contraindications?: string[]
}

export interface MedicationValidation {
  isValid: boolean
  warnings: string[]
  errors: string[]
  suggestions: string[]
  drugDatabaseMatch?: DrugDatabaseEntry
  alternatives?: DrugDatabaseEntry[]
}

export interface DrugDatabaseEntry {
  id: string
  name: string
  genericName: string
  brandNames: string[]
  activeIngredients: string[]
  strength: string
  dosageForm: string
  manufacturer: string
  description: string
  sideEffects: string[]
  contraindications: string[]
  interactions: string[]
  pregnancyCategory: string
  breastfeedingCategory: string
  pediatricUse: string
  geriatricUse: string
  renalDoseAdjustment: string
  hepaticDoseAdjustment: string
  storageInstructions: string
  disposalInstructions: string
  cost: number
  availability: 'available' | 'discontinued' | 'restricted'
}

export interface MedicationEnrichment {
  drugInfo?: DrugDatabaseEntry
  interactions?: MedicationInteraction[]
  sideEffects?: string[]
  contraindications?: string[]
  dosageGuidelines?: DosageGuideline[]
  costAnalysis?: CostAnalysis
  availability?: AvailabilityInfo
  enrichedAt: string
  source: 'perplexity' | 'drug_database' | 'manual'
}

export interface DosageGuideline {
  ageGroup: string
  condition: string
  dosage: string
  frequency: string
  duration: string
  notes: string
}

export interface CostAnalysis {
  averageCost: number
  costRange: {
    min: number
    max: number
  }
  genericAvailable: boolean
  genericCost?: number
  insuranceCoverage?: number
  outOfPocketCost?: number
  costPerDose?: number
  monthlyCost?: number
}

export interface AvailabilityInfo {
  isAvailable: boolean
  stockStatus: 'in_stock' | 'low_stock' | 'out_of_stock' | 'discontinued'
  pharmacies: PharmacyInfo[]
  onlineAvailability: boolean
  prescriptionRequired: boolean
}

export interface PharmacyInfo {
  name: string
  address: string
  phone: string
  distance: number
  stock: number
  price: number
}

export interface PrescriptionStorage {
  id: string
  prescriptionId: string
  prescription: ParsedPrescription
  medications: Medication[]
  createdAt: string
  updatedAt: string
  status: 'active' | 'archived' | 'deleted'
  tags: string[]
  notes: string
}

export interface BatchMedicationResult {
  success: boolean
  medication?: Medication
  error?: string
  warnings?: string[]
  validation?: MedicationValidation
}

export interface BatchMedicationResponse {
  total: number
  successful: number
  failed: number
  results: BatchMedicationResult[]
  errors: string[]
  warnings: string[]
}

export interface MedicationHistory {
  id: string
  medicationId: string
  action: 'taken' | 'missed' | 'skipped' | 'dose_adjusted' | 'stock_updated'
  timestamp: string
  notes?: string
  doseAmount?: number
  stockBefore?: number
  stockAfter?: number
  adherenceScore?: number
}

export interface AdherenceTracking {
  medicationId: string
  medication: Medication
  totalDoses: number
  takenDoses: number
  missedDoses: number
  adherenceRate: number
  streakDays: number
  lastTaken: string
  nextDose: string
  history: MedicationHistory[]
}

export interface PrescriptionRenewal {
  id: string
  prescriptionId: string
  originalPrescription: ParsedPrescription
  renewalDate: string
  expiryDate: string
  refillsRemaining: number
  totalRefills: number
  status: 'active' | 'expired' | 'renewed' | 'cancelled'
  reminderSent: boolean
  reminderDate?: string
  notes: string
}

export interface MedicationImage {
  id: string
  medicationId: string
  imageUrl: string
  thumbnailUrl: string
  uploadedAt: string
  fileSize: number
  mimeType: string
  description?: string
  isPrimary: boolean
}

export interface PerplexityEnrichmentRequest {
  medicationName: string
  genericName?: string
  strength?: string
  manufacturer?: string
  includeInteractions?: boolean
  includeSideEffects?: boolean
  includeCost?: boolean
  includeAvailability?: boolean
}

export interface PerplexityEnrichmentResponse {
  success: boolean
  data?: MedicationEnrichment
  error?: string
  source: 'perplexity'
  timestamp: string
}

// Enhanced prescription scanner interfaces
export interface PrescriptionPage {
  id: string
  imageData: string
  imageUrl?: string
  pageNumber: number
  quality: ImageQuality
  ocrText: string
  extractedMedications: PrescriptionMedication[]
  confidence: number
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
  error?: string
  lowConfidenceResults?: OCRConfidence[]
  metadata?: PrescriptionMetadata
  interactions?: MedicationInteraction[]
  saValidation?: SouthAfricanPrescriptionValidation
}

export interface ImageQuality {
  brightness: number
  contrast: number
  sharpness: number
  noise: number
  blur: number
  overall: number
  isValid: boolean
  warnings: string[]
}

export interface PrescriptionMetadata {
  patientName?: string
  patientId?: string
  prescribingDoctor?: string
  doctorLicense?: string
  prescriptionDate?: string
  expiryDate?: string
  prescriptionNumber?: string
  pharmacy?: string
  diagnosis?: string
  allergies?: string[]
  totalCost?: number
  insurance?: string
  refills?: number
  notes?: string
}

export interface CameraGuide {
  type: 'rectangle' | 'corner' | 'crosshair'
  position: { x: number; y: number; width: number; height: number }
  color: string
  opacity: number
  message: string
}

export interface OCRConfidence {
  text: string
  confidence: number
  boundingBox: { x: number; y: number; width: number; height: number }
  suggestions: string[]
}

export interface MedicationInteraction {
  severity: 'low' | 'moderate' | 'high' | 'contraindicated'
  description: string
  medications: string[]
  recommendations: string
  evidence: string
  source: string
}

export interface BatchProcessingResult {
  totalPages: number
  successfulPages: number
  failedPages: number
  totalMedications: number
  duplicateMedications: BulkMedicationEntry[]
  interactions: MedicationInteraction[]
  processingTime: number
  pages: PrescriptionPage[]
  metadata: PrescriptionMetadata
  exportData: PrescriptionExportData
  saValidation?: SouthAfricanPrescriptionValidation
}

export interface PrescriptionExportData {
  format: 'json' | 'csv' | 'pdf' | 'xml'
  data: any
  filename: string
  timestamp: string
}

export interface SouthAfricanPrescriptionValidation {
  isValid: boolean
  errors: string[]
  warnings: string[]
  requiredFields: {
    doctorName: boolean
    doctorLicense: boolean
    prescriptionDate: boolean
    patientName: boolean
    medicationDetails: boolean
  }
  formatCompliance: {
    isStandardFormat: boolean
    hasRequiredSections: boolean
    hasProperDosage: boolean
    hasFrequency: boolean
  }
  details?: {
    totalMedications: number
    warnings: number
    specificWarnings: Array<{
      name: string
      message: string
    }>
  }
}

export interface FileUploadProgress {
  fileId: string
  filename: string
  progress: number
  status: 'uploading' | 'processing' | 'completed' | 'failed'
  error?: string
  result?: PrescriptionPage
}

export interface DragDropZone {
  isActive: boolean
  isDragOver: boolean
  acceptedFiles: File[]
  rejectedFiles: File[]
  totalSize: number
} 