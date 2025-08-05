import { z } from 'zod'

// ============================================================================
// CORE PRESCRIPTION INTERFACES
// ============================================================================

/**
 * Main prescription data interface containing all prescription information
 */
export interface PrescriptionData {
  id: string
  prescriptionNumber: string
  prescriptionDate: string
  expiryDate?: string
  doctor: DoctorInfo
  patient: PatientInfo
  medications: PrescriptionMedication[]
  pharmacy?: PharmacyInfo
  insurance?: InsuranceInfo
  totalCost?: number
  notes?: string
  status: 'active' | 'expired' | 'completed' | 'renewed' | 'cancelled'
  metadata: PrescriptionMetadata
  createdAt: string
  updatedAt: string
}

/**
 * Doctor information interface
 */
export interface DoctorInfo {
  name: string
  title?: string
  practiceNumber: string
  specialization?: string
  contactNumber?: string
  email?: string
  address?: Address
  signature?: string
}

/**
 * Patient information interface
 */
export interface PatientInfo {
  name: string
  dateOfBirth: string
  idNumber?: string
  contactNumber?: string
  email?: string
  address?: Address
  emergencyContact?: EmergencyContact
  allergies?: string[]
  medicalConditions?: string[]
  currentMedications?: string[]
}

/**
 * Prescription medication interface with parsed details
 */
export interface PrescriptionMedication {
  id: string
  name: string
  genericName?: string
  brandName?: string
  strength: string
  dosageForm: 'tablet' | 'capsule' | 'liquid' | 'injection' | 'cream' | 'ointment' | 'inhaler' | 'suppository' | 'drops' | 'other'
  dosage: DosageInstruction
  quantity: number
  refills: number
  refillsRemaining: number
  instructions: string
  schedule: ScheduleTiming
  cost?: number
  drugDatabaseId?: string
  icd10Codes?: ICD10Code[]
  interactions?: string[]
  sideEffects?: string[]
  contraindications?: string[]
  pregnancyCategory?: string
  breastfeedingCategory?: string
  storageInstructions?: string
  disposalInstructions?: string
  enrichedData?: MedicationEnrichment
}

/**
 * ICD-10 code interface with code and description mapping
 */
export interface ICD10Code {
  code: string
  description: string
  category: string
  isPrimary?: boolean
  severity?: 'mild' | 'moderate' | 'severe'
}

/**
 * Dosage instruction interface for structured dosage parsing
 */
export interface DosageInstruction {
  amount: number
  unit: string
  frequency: string
  route: 'oral' | 'topical' | 'injection' | 'inhalation' | 'rectal' | 'vaginal' | 'other'
  timing?: string
  duration?: string
  asNeeded?: boolean
  withFood?: boolean
  withWater?: boolean
  specialInstructions?: string[]
}

/**
 * Schedule timing interface for medication timing patterns
 */
export interface ScheduleTiming {
  type: 'fixed' | 'flexible' | 'as_needed' | 'custom'
  times: string[]
  daysOfWeek?: number[]
  interval?: number
  intervalUnit?: 'hours' | 'days' | 'weeks'
  startDate?: string
  endDate?: string
  timezone?: string
  reminders?: ReminderSettings
}

/**
 * Prescription metadata interface for OCR confidence and processing status
 */
export interface PrescriptionMetadata {
  ocrConfidence: number
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
  processingSteps: ProcessingStep[]
  imageQuality: ImageQuality
  validationResults: ValidationResult[]
  enrichmentStatus: 'pending' | 'enriched' | 'failed'
  lastProcessed: string
  version: string
}

/**
 * Medication mapping interface for brand name to generic name conversion
 */
export interface MedicationMapping {
  brandName: string
  genericName: string
  manufacturer: string
  strength: string
  dosageForm: string
  activeIngredients: string[]
  alternatives: string[]
  costComparison: CostComparison
  availability: AvailabilityStatus
  lastUpdated: string
}

// ============================================================================
// SUPPORTING INTERFACES
// ============================================================================

export interface Address {
  street: string
  city: string
  province: string
  postalCode: string
  country: string
}

export interface EmergencyContact {
  name: string
  relationship: string
  contactNumber: string
  email?: string
}

export interface PharmacyInfo {
  name: string
  address: Address
  contactNumber: string
  email?: string
  operatingHours?: string
  services?: string[]
}

export interface InsuranceInfo {
  provider: string
  policyNumber: string
  groupNumber?: string
  coverageType: string
  copay?: number
  deductible?: number
  coveragePercentage?: number
}

export interface ProcessingStep {
  step: string
  status: 'pending' | 'completed' | 'failed'
  confidence?: number
  duration?: number
  error?: string
  timestamp: string
}

export interface ImageQuality {
  resolution: string
  brightness: number
  contrast: number
  sharpness: number
  noise: number
  overall: number
}

export interface ValidationResult {
  field: string
  isValid: boolean
  confidence: number
  suggestions: string[]
  warnings: string[]
  errors: string[]
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

export interface MedicationInteraction {
  severity: 'low' | 'moderate' | 'high' | 'contraindicated'
  description: string
  medications: string[]
  recommendations: string
  evidence: string
  source: string
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

export interface ReminderSettings {
  enabled: boolean
  method: 'push' | 'email' | 'sms' | 'all'
  advanceMinutes: number
  repeatCount: number
  repeatInterval: number
}

export interface CostComparison {
  brandCost: number
  genericCost: number
  savings: number
  savingsPercentage: number
  availability: boolean
}

export interface AvailabilityStatus {
  status: 'available' | 'limited' | 'unavailable' | 'discontinued'
  stockLevel: number
  estimatedRestock?: string
  alternativeSources: string[]
}

// ============================================================================
// VALIDATION SCHEMAS
// ============================================================================

export const DoctorInfoSchema = z.object({
  name: z.string().min(1, 'Doctor name is required'),
  title: z.string().optional(),
  practiceNumber: z.string().min(1, 'Practice number is required'),
  specialization: z.string().optional(),
  contactNumber: z.string().optional(),
  email: z.string().email().optional(),
  address: z.object({
    street: z.string(),
    city: z.string(),
    province: z.string(),
    postalCode: z.string(),
    country: z.string()
  }).optional(),
  signature: z.string().optional()
})

export const PatientInfoSchema = z.object({
  name: z.string().min(1, 'Patient name is required'),
  dateOfBirth: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format'),
  idNumber: z.string().optional(),
  contactNumber: z.string().optional(),
  email: z.string().email().optional(),
  address: z.object({
    street: z.string(),
    city: z.string(),
    province: z.string(),
    postalCode: z.string(),
    country: z.string()
  }).optional(),
  emergencyContact: z.object({
    name: z.string(),
    relationship: z.string(),
    contactNumber: z.string(),
    email: z.string().email().optional()
  }).optional(),
  allergies: z.array(z.string()).optional(),
  medicalConditions: z.array(z.string()).optional(),
  currentMedications: z.array(z.string()).optional()
})

export const ICD10CodeSchema = z.object({
  code: z.string().regex(/^[A-Z]\d{2}(\.\d{1,2})?$/, 'Invalid ICD-10 code format'),
  description: z.string().min(1, 'Description is required'),
  category: z.string(),
  isPrimary: z.boolean().optional(),
  severity: z.enum(['mild', 'moderate', 'severe']).optional()
})

export const DosageInstructionSchema = z.object({
  amount: z.number().positive('Amount must be positive'),
  unit: z.string().min(1, 'Unit is required'),
  frequency: z.string().min(1, 'Frequency is required'),
  route: z.enum(['oral', 'topical', 'injection', 'inhalation', 'rectal', 'vaginal', 'other']),
  timing: z.string().optional(),
  duration: z.string().optional(),
  asNeeded: z.boolean().optional(),
  withFood: z.boolean().optional(),
  withWater: z.boolean().optional(),
  specialInstructions: z.array(z.string()).optional()
})

export const ScheduleTimingSchema = z.object({
  type: z.enum(['fixed', 'flexible', 'as_needed', 'custom']),
  times: z.array(z.string().regex(/^\d{2}:\d{2}$/, 'Invalid time format')),
  daysOfWeek: z.array(z.number().min(0).max(6)).optional(),
  interval: z.number().positive().optional(),
  intervalUnit: z.enum(['hours', 'days', 'weeks']).optional(),
  startDate: z.string().optional(),
  endDate: z.string().optional(),
  timezone: z.string().optional(),
  reminders: z.object({
    enabled: z.boolean(),
    method: z.enum(['push', 'email', 'sms', 'all']),
    advanceMinutes: z.number().min(0),
    repeatCount: z.number().min(0),
    repeatInterval: z.number().min(0)
  }).optional()
})

export const PrescriptionMedicationSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, 'Medication name is required'),
  genericName: z.string().optional(),
  brandName: z.string().optional(),
  strength: z.string().min(1, 'Strength is required'),
  dosageForm: z.enum(['tablet', 'capsule', 'liquid', 'injection', 'cream', 'ointment', 'inhaler', 'suppository', 'drops', 'other']),
  dosage: DosageInstructionSchema,
  quantity: z.number().positive('Quantity must be positive'),
  refills: z.number().min(0, 'Refills cannot be negative'),
  refillsRemaining: z.number().min(0, 'Refills remaining cannot be negative'),
  instructions: z.string().min(1, 'Instructions are required'),
  schedule: ScheduleTimingSchema,
  cost: z.number().positive().optional(),
  drugDatabaseId: z.string().optional(),
  icd10Codes: z.array(ICD10CodeSchema).optional(),
  interactions: z.array(z.string()).optional(),
  sideEffects: z.array(z.string()).optional(),
  contraindications: z.array(z.string()).optional(),
  pregnancyCategory: z.string().optional(),
  breastfeedingCategory: z.string().optional(),
  storageInstructions: z.string().optional(),
  disposalInstructions: z.string().optional(),
  enrichedData: z.any().optional()
})

export const PrescriptionMetadataSchema = z.object({
  ocrConfidence: z.number().min(0).max(1),
  processingStatus: z.enum(['pending', 'processing', 'completed', 'failed']),
  processingSteps: z.array(z.object({
    step: z.string(),
    status: z.enum(['pending', 'completed', 'failed']),
    confidence: z.number().optional(),
    duration: z.number().optional(),
    error: z.string().optional(),
    timestamp: z.string()
  })),
  imageQuality: z.object({
    resolution: z.string(),
    brightness: z.number().min(0).max(1),
    contrast: z.number().min(0).max(1),
    sharpness: z.number().min(0).max(1),
    noise: z.number().min(0).max(1),
    overall: z.number().min(0).max(1)
  }),
  validationResults: z.array(z.object({
    field: z.string(),
    isValid: z.boolean(),
    confidence: z.number().min(0).max(1),
    suggestions: z.array(z.string()),
    warnings: z.array(z.string()),
    errors: z.array(z.string())
  })),
  enrichmentStatus: z.enum(['pending', 'enriched', 'failed']),
  lastProcessed: z.string(),
  version: z.string()
})

export const PrescriptionDataSchema = z.object({
  id: z.string().uuid(),
  prescriptionNumber: z.string().min(1, 'Prescription number is required'),
  prescriptionDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format'),
  expiryDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Invalid date format').optional(),
  doctor: DoctorInfoSchema,
  patient: PatientInfoSchema,
  medications: z.array(PrescriptionMedicationSchema).min(1, 'At least one medication is required'),
  pharmacy: z.object({
    name: z.string(),
    address: z.object({
      street: z.string(),
      city: z.string(),
      province: z.string(),
      postalCode: z.string(),
      country: z.string()
    }),
    contactNumber: z.string(),
    email: z.string().email().optional(),
    operatingHours: z.string().optional(),
    services: z.array(z.string()).optional()
  }).optional(),
  insurance: z.object({
    provider: z.string(),
    policyNumber: z.string(),
    groupNumber: z.string().optional(),
    coverageType: z.string(),
    copay: z.number().positive().optional(),
    deductible: z.number().positive().optional(),
    coveragePercentage: z.number().min(0).max(100).optional()
  }).optional(),
  totalCost: z.number().positive().optional(),
  notes: z.string().optional(),
  status: z.enum(['active', 'expired', 'completed', 'renewed', 'cancelled']),
  metadata: PrescriptionMetadataSchema,
  createdAt: z.string(),
  updatedAt: z.string()
})

export const MedicationMappingSchema = z.object({
  brandName: z.string().min(1, 'Brand name is required'),
  genericName: z.string().min(1, 'Generic name is required'),
  manufacturer: z.string().min(1, 'Manufacturer is required'),
  strength: z.string().min(1, 'Strength is required'),
  dosageForm: z.string().min(1, 'Dosage form is required'),
  activeIngredients: z.array(z.string()).min(1, 'At least one active ingredient is required'),
  alternatives: z.array(z.string()),
  costComparison: z.object({
    brandCost: z.number().positive(),
    genericCost: z.number().positive(),
    savings: z.number(),
    savingsPercentage: z.number().min(0).max(100),
    availability: z.boolean()
  }),
  availability: z.object({
    status: z.enum(['available', 'limited', 'unavailable', 'discontinued']),
    stockLevel: z.number().min(0),
    estimatedRestock: z.string().optional(),
    alternativeSources: z.array(z.string())
  }),
  lastUpdated: z.string()
})

// ============================================================================
// EXAMPLE DATA - 21 MEDICATIONS FROM PRESCRIPTION
// ============================================================================

export const EXAMPLE_MEDICATIONS: PrescriptionMedication[] = [
  {
    id: '1',
    name: 'Paracetamol',
    genericName: 'Acetaminophen',
    brandName: 'Panado',
    strength: '500mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'every 4-6 hours',
      route: 'oral',
      asNeeded: true,
      withWater: true
    },
    quantity: 30,
    refills: 2,
    refillsRemaining: 2,
    instructions: 'Take with water. Do not exceed 8 tablets in 24 hours.',
    schedule: {
      type: 'as_needed',
      times: ['08:00', '12:00', '16:00', '20:00']
    }
  },
  {
    id: '2',
    name: 'Ibuprofen',
    genericName: 'Ibuprofen',
    brandName: 'Brufen',
    strength: '400mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'every 8 hours',
      route: 'oral',
      withFood: true,
      withWater: true
    },
    quantity: 21,
    refills: 1,
    refillsRemaining: 1,
    instructions: 'Take with food to prevent stomach upset.',
    schedule: {
      type: 'fixed',
      times: ['08:00', '16:00', '00:00']
    }
  },
  {
    id: '3',
    name: 'Amoxicillin',
    genericName: 'Amoxicillin',
    brandName: 'Amoxil',
    strength: '500mg',
    dosageForm: 'capsule',
    dosage: {
      amount: 1,
      unit: 'capsule',
      frequency: 'three times daily',
      route: 'oral',
      withWater: true
    },
    quantity: 21,
    refills: 0,
    refillsRemaining: 0,
    instructions: 'Take on an empty stomach. Complete the full course.',
    schedule: {
      type: 'fixed',
      times: ['08:00', '14:00', '20:00']
    }
  },
  {
    id: '4',
    name: 'Omeprazole',
    genericName: 'Omeprazole',
    brandName: 'Losec',
    strength: '20mg',
    dosageForm: 'capsule',
    dosage: {
      amount: 1,
      unit: 'capsule',
      frequency: 'once daily',
      route: 'oral',
      timing: 'before breakfast'
    },
    quantity: 30,
    refills: 3,
    refillsRemaining: 3,
    instructions: 'Take 30 minutes before breakfast.',
    schedule: {
      type: 'fixed',
      times: ['07:00']
    }
  },
  {
    id: '5',
    name: 'Metformin',
    genericName: 'Metformin',
    brandName: 'Glucophage',
    strength: '500mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'twice daily',
      route: 'oral',
      withFood: true
    },
    quantity: 60,
    refills: 5,
    refillsRemaining: 5,
    instructions: 'Take with meals to reduce stomach upset.',
    schedule: {
      type: 'fixed',
      times: ['08:00', '20:00']
    }
  },
  {
    id: '6',
    name: 'Atorvastatin',
    genericName: 'Atorvastatin',
    brandName: 'Lipitor',
    strength: '10mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral',
      timing: 'at bedtime'
    },
    quantity: 30,
    refills: 5,
    refillsRemaining: 5,
    instructions: 'Take at bedtime for best effect.',
    schedule: {
      type: 'fixed',
      times: ['22:00']
    }
  },
  {
    id: '7',
    name: 'Lisinopril',
    genericName: 'Lisinopril',
    brandName: 'Zestril',
    strength: '5mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral',
      timing: 'in the morning'
    },
    quantity: 30,
    refills: 5,
    refillsRemaining: 5,
    instructions: 'Take in the morning. Monitor blood pressure.',
    schedule: {
      type: 'fixed',
      times: ['08:00']
    }
  },
  {
    id: '8',
    name: 'Amlodipine',
    genericName: 'Amlodipine',
    brandName: 'Norvasc',
    strength: '5mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral'
    },
    quantity: 30,
    refills: 5,
    refillsRemaining: 5,
    instructions: 'Take at the same time each day.',
    schedule: {
      type: 'fixed',
      times: ['08:00']
    }
  },
  {
    id: '9',
    name: 'Simvastatin',
    genericName: 'Simvastatin',
    brandName: 'Zocor',
    strength: '20mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral',
      timing: 'at bedtime'
    },
    quantity: 30,
    refills: 5,
    refillsRemaining: 5,
    instructions: 'Take at bedtime for best effect.',
    schedule: {
      type: 'fixed',
      times: ['22:00']
    }
  },
  {
    id: '10',
    name: 'Losartan',
    genericName: 'Losartan',
    brandName: 'Cozaar',
    strength: '50mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral'
    },
    quantity: 30,
    refills: 5,
    refillsRemaining: 5,
    instructions: 'Take at the same time each day.',
    schedule: {
      type: 'fixed',
      times: ['08:00']
    }
  },
  {
    id: '11',
    name: 'Hydrochlorothiazide',
    genericName: 'Hydrochlorothiazide',
    brandName: 'Microzide',
    strength: '12.5mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral',
      timing: 'in the morning'
    },
    quantity: 30,
    refills: 5,
    refillsRemaining: 5,
    instructions: 'Take in the morning to avoid nighttime urination.',
    schedule: {
      type: 'fixed',
      times: ['08:00']
    }
  },
  {
    id: '12',
    name: 'Pantoprazole',
    genericName: 'Pantoprazole',
    brandName: 'Protonix',
    strength: '40mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral',
      timing: 'before breakfast'
    },
    quantity: 30,
    refills: 3,
    refillsRemaining: 3,
    instructions: 'Take 30 minutes before breakfast.',
    schedule: {
      type: 'fixed',
      times: ['07:00']
    }
  },
  {
    id: '13',
    name: 'Cetirizine',
    genericName: 'Cetirizine',
    brandName: 'Zyrtec',
    strength: '10mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral'
    },
    quantity: 30,
    refills: 2,
    refillsRemaining: 2,
    instructions: 'Take as needed for allergy symptoms.',
    schedule: {
      type: 'as_needed',
      times: ['08:00']
    }
  },
  {
    id: '14',
    name: 'Loratadine',
    genericName: 'Loratadine',
    brandName: 'Claritin',
    strength: '10mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral'
    },
    quantity: 30,
    refills: 2,
    refillsRemaining: 2,
    instructions: 'Take as needed for allergy symptoms.',
    schedule: {
      type: 'as_needed',
      times: ['08:00']
    }
  },
  {
    id: '15',
    name: 'Diclofenac',
    genericName: 'Diclofenac',
    brandName: 'Voltaren',
    strength: '50mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'three times daily',
      route: 'oral',
      withFood: true
    },
    quantity: 21,
    refills: 1,
    refillsRemaining: 1,
    instructions: 'Take with food to prevent stomach upset.',
    schedule: {
      type: 'fixed',
      times: ['08:00', '14:00', '20:00']
    }
  },
  {
    id: '16',
    name: 'Tramadol',
    genericName: 'Tramadol',
    brandName: 'Ultram',
    strength: '50mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'every 4-6 hours',
      route: 'oral',
      asNeeded: true
    },
    quantity: 30,
    refills: 0,
    refillsRemaining: 0,
    instructions: 'Take as needed for moderate pain. Do not exceed 8 tablets in 24 hours.',
    schedule: {
      type: 'as_needed',
      times: ['08:00', '12:00', '16:00', '20:00', '00:00', '04:00']
    }
  },
  {
    id: '17',
    name: 'Codeine',
    genericName: 'Codeine',
    brandName: 'Codeine Phosphate',
    strength: '30mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'every 4-6 hours',
      route: 'oral',
      asNeeded: true
    },
    quantity: 20,
    refills: 0,
    refillsRemaining: 0,
    instructions: 'Take as needed for severe pain. May cause drowsiness.',
    schedule: {
      type: 'as_needed',
      times: ['08:00', '12:00', '16:00', '20:00', '00:00', '04:00']
    }
  },
  {
    id: '18',
    name: 'Morphine',
    genericName: 'Morphine',
    brandName: 'MST Continus',
    strength: '10mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'twice daily',
      route: 'oral'
    },
    quantity: 14,
    refills: 0,
    refillsRemaining: 0,
    instructions: 'Take exactly as prescribed. Do not crush or break tablets.',
    schedule: {
      type: 'fixed',
      times: ['08:00', '20:00']
    }
  },
  {
    id: '19',
    name: 'Oxycodone',
    genericName: 'Oxycodone',
    brandName: 'OxyContin',
    strength: '5mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'every 12 hours',
      route: 'oral'
    },
    quantity: 14,
    refills: 0,
    refillsRemaining: 0,
    instructions: 'Take exactly as prescribed. Do not crush or break tablets.',
    schedule: {
      type: 'fixed',
      times: ['08:00', '20:00']
    }
  },
  {
    id: '20',
    name: 'Fentanyl',
    genericName: 'Fentanyl',
    brandName: 'Duragesic',
    strength: '25mcg',
    dosageForm: 'patch',
    dosage: {
      amount: 1,
      unit: 'patch',
      frequency: 'every 72 hours',
      route: 'topical'
    },
    quantity: 4,
    refills: 0,
    refillsRemaining: 0,
    instructions: 'Apply to clean, dry skin. Change every 72 hours.',
    schedule: {
      type: 'fixed',
      times: ['08:00'],
      interval: 72,
      intervalUnit: 'hours'
    }
  },
  {
    id: '21',
    name: 'Methadone',
    genericName: 'Methadone',
    brandName: 'Methadone',
    strength: '5mg',
    dosageForm: 'tablet',
    dosage: {
      amount: 1,
      unit: 'tablet',
      frequency: 'once daily',
      route: 'oral'
    },
    quantity: 7,
    refills: 0,
    refillsRemaining: 0,
    instructions: 'Take exactly as prescribed. Do not share with others.',
    schedule: {
      type: 'fixed',
      times: ['08:00']
    }
  }
]

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Validate prescription data using Zod schemas
 */
export function validatePrescriptionData(data: PrescriptionData): {
  isValid: boolean
  errors: string[]
  warnings: string[]
} {
  try {
    PrescriptionDataSchema.parse(data)
    return { isValid: true, errors: [], warnings: [] }
  } catch (error) {
    if (error instanceof z.ZodError) {
      const errors = error.errors.map(err => `${err.path.join('.')}: ${err.message}`)
      return { isValid: false, errors, warnings: [] }
    }
    return { isValid: false, errors: ['Unknown validation error'], warnings: [] }
  }
}

/**
 * Transform raw OCR text to structured prescription data
 */
export function transformOCRToPrescriptionData(
  ocrText: string,
  metadata: Partial<PrescriptionMetadata>
): PrescriptionData {
  // This is a simplified transformation - in practice, you'd use more sophisticated NLP
  const lines = ocrText.split('\n').filter(line => line.trim())
  
  const prescriptionData: PrescriptionData = {
    id: crypto.randomUUID(),
    prescriptionNumber: generatePrescriptionNumber(),
    prescriptionDate: new Date().toISOString().split('T')[0],
    doctor: extractDoctorInfo(lines),
    patient: extractPatientInfo(lines),
    medications: extractMedications(lines),
    status: 'active',
    metadata: {
      ocrConfidence: metadata.ocrConfidence || 0.8,
      processingStatus: 'completed',
      processingSteps: [
        {
          step: 'ocr_extraction',
          status: 'completed',
          confidence: metadata.ocrConfidence || 0.8,
          duration: 2000,
          timestamp: new Date().toISOString()
        }
      ],
      imageQuality: {
        resolution: '1920x1080',
        brightness: 0.7,
        contrast: 0.8,
        sharpness: 0.9,
        noise: 0.2,
        overall: 0.8
      },
      validationResults: [],
      enrichmentStatus: 'pending',
      lastProcessed: new Date().toISOString(),
      version: '1.0.0'
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
  
  return prescriptionData
}

/**
 * Convert brand name to generic name using medication mapping
 */
export function convertBrandToGeneric(
  brandName: string,
  mappings: MedicationMapping[]
): string | null {
  const mapping = mappings.find(m => 
    m.brandName.toLowerCase() === brandName.toLowerCase()
  )
  return mapping?.genericName || null
}

/**
 * Calculate prescription cost including generics
 */
export function calculatePrescriptionCost(
  medications: PrescriptionMedication[],
  mappings: MedicationMapping[]
): {
  totalCost: number
  brandCost: number
  genericCost: number
  savings: number
  savingsPercentage: number
} {
  let brandCost = 0
  let genericCost = 0
  
  medications.forEach(med => {
    const mapping = mappings.find(m => 
      m.brandName.toLowerCase() === med.brandName?.toLowerCase()
    )
    
    if (mapping) {
      brandCost += (med.cost || 0)
      genericCost += mapping.costComparison.genericCost
    } else {
      brandCost += (med.cost || 0)
      genericCost += (med.cost || 0)
    }
  })
  
  const savings = brandCost - genericCost
  const savingsPercentage = brandCost > 0 ? (savings / brandCost) * 100 : 0
  
  return {
    totalCost: genericCost,
    brandCost,
    genericCost,
    savings,
    savingsPercentage
  }
}

/**
 * Generate medication schedule from prescription data
 */
export function generateMedicationSchedule(
  medications: PrescriptionMedication[]
): Array<{
  medicationId: string
  medicationName: string
  time: string
  dosage: string
  instructions: string
}> {
  const schedule: Array<{
    medicationId: string
    medicationName: string
    time: string
    dosage: string
    instructions: string
  }> = []
  
  medications.forEach(med => {
    med.schedule.times.forEach(time => {
      schedule.push({
        medicationId: med.id,
        medicationName: med.name,
        time,
        dosage: `${med.dosage.amount} ${med.dosage.unit}`,
        instructions: med.instructions
      })
    })
  })
  
  return schedule.sort((a, b) => a.time.localeCompare(b.time))
}

/**
 * Check for drug interactions between medications
 */
export function checkDrugInteractions(
  medications: PrescriptionMedication[]
): Array<{
  severity: 'low' | 'moderate' | 'high' | 'contraindicated'
  description: string
  medications: string[]
  recommendations: string
}> {
  const interactions: Array<{
    severity: 'low' | 'moderate' | 'high' | 'contraindicated'
    description: string
    medications: string[]
    recommendations: string
  }> = []
  
  // This is a simplified check - in practice, you'd use a drug interaction database
  const medicationNames = medications.map(m => m.name.toLowerCase())
  
  // Example interaction checks
  if (medicationNames.includes('warfarin') && medicationNames.includes('aspirin')) {
    interactions.push({
      severity: 'high',
      description: 'Increased risk of bleeding when combining anticoagulants',
      medications: ['Warfarin', 'Aspirin'],
      recommendations: 'Monitor INR closely and watch for signs of bleeding'
    })
  }
  
  if (medicationNames.includes('simvastatin') && medicationNames.includes('amiodarone')) {
    interactions.push({
      severity: 'moderate',
      description: 'Increased risk of muscle damage when combining statins with amiodarone',
      medications: ['Simvastatin', 'Amiodarone'],
      recommendations: 'Monitor for muscle pain and consider alternative statin'
    })
  }
  
  return interactions
}

/**
 * Validate dosage instructions for safety
 */
export function validateDosageSafety(
  dosage: DosageInstruction,
  medicationName: string
): {
  isValid: boolean
  warnings: string[]
  errors: string[]
} {
  const warnings: string[] = []
  const errors: string[] = []
  
  // Check for excessive frequency
  if (dosage.frequency.includes('every hour') || dosage.frequency.includes('hourly')) {
    warnings.push('Very frequent dosing may lead to side effects')
  }
  
  // Check for high doses
  if (dosage.amount > 1000 && dosage.unit === 'mg') {
    warnings.push('High dose detected - verify with healthcare provider')
  }
  
  // Check for specific medication warnings
  if (medicationName.toLowerCase().includes('paracetamol') && dosage.amount > 500) {
    warnings.push('High paracetamol dose - do not exceed 4g daily')
  }
  
  return {
    isValid: errors.length === 0,
    warnings,
    errors
  }
}

/**
 * Generate prescription summary for patient
 */
export function generatePrescriptionSummary(
  prescription: PrescriptionData
): {
  summary: string
  keyInstructions: string[]
  warnings: string[]
  nextRefillDate?: string
} {
  const keyInstructions: string[] = []
  const warnings: string[] = []
  
  prescription.medications.forEach(med => {
    keyInstructions.push(`${med.name}: ${med.dosage.amount} ${med.dosage.unit} ${med.dosage.frequency}`)
    
    if (med.refillsRemaining === 0) {
      warnings.push(`${med.name} has no refills remaining`)
    }
    
    if (med.dosage.withFood) {
      keyInstructions.push(`Take ${med.name} with food`)
    }
  })
  
  const summary = `Prescription for ${prescription.patient.name} with ${prescription.medications.length} medications`
  
  return {
    summary,
    keyInstructions,
    warnings,
    nextRefillDate: prescription.medications.find(m => m.refillsRemaining > 0)?.schedule.startDate
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function generatePrescriptionNumber(): string {
  return `RX${Date.now().toString().slice(-8)}`
}

function extractDoctorInfo(lines: string[]): DoctorInfo {
  // Simplified extraction - in practice, use NLP
  const doctorLine = lines.find(line => 
    line.toLowerCase().includes('dr.') || line.toLowerCase().includes('doctor')
  )
  
  return {
    name: doctorLine?.replace(/dr\.?\s*/i, '').trim() || 'Unknown Doctor',
    practiceNumber: 'PR123456',
    title: 'Dr.'
  }
}

function extractPatientInfo(lines: string[]): PatientInfo {
  // Simplified extraction - in practice, use NLP
  const patientLine = lines.find(line => 
    line.toLowerCase().includes('patient') || line.toLowerCase().includes('name')
  )
  
  return {
    name: patientLine?.replace(/patient\s*name\s*:\s*/i, '').trim() || 'Unknown Patient',
    dateOfBirth: '1990-01-01'
  }
}

function extractMedications(lines: string[]): PrescriptionMedication[] {
  // Simplified extraction - in practice, use NLP
  const medications: PrescriptionMedication[] = []
  
  // This is a placeholder - in practice, you'd parse the actual OCR text
  // and extract medication information using NLP techniques
  
  return medications
}

// ============================================================================
// EXPORTS
// ============================================================================

export type {
  PrescriptionData,
  DoctorInfo,
  PatientInfo,
  PrescriptionMedication,
  ICD10Code,
  DosageInstruction,
  ScheduleTiming,
  PrescriptionMetadata,
  MedicationMapping,
  Address,
  EmergencyContact,
  PharmacyInfo,
  InsuranceInfo,
  ProcessingStep,
  ImageQuality,
  ValidationResult,
  MedicationEnrichment,
  DrugDatabaseEntry,
  MedicationInteraction,
  DosageGuideline,
  CostAnalysis,
  AvailabilityInfo,
  ReminderSettings,
  CostComparison,
  AvailabilityStatus
}

export {
  // Schemas
  PrescriptionDataSchema,
  DoctorInfoSchema,
  PatientInfoSchema,
  PrescriptionMedicationSchema,
  ICD10CodeSchema,
  DosageInstructionSchema,
  ScheduleTimingSchema,
  PrescriptionMetadataSchema,
  MedicationMappingSchema,
  
  // Example data
  EXAMPLE_MEDICATIONS,
  
  // Utility functions
  validatePrescriptionData,
  transformOCRToPrescriptionData,
  convertBrandToGeneric,
  calculatePrescriptionCost,
  generateMedicationSchedule,
  checkDrugInteractions,
  validateDosageSafety,
  generatePrescriptionSummary
} 