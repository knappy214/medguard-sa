<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { 
  MedicationFormData, 
  Medication, 
  BulkMedicationEntry, 
  ICD10Code, 
  MedicationInteraction 
} from '@/types/medication'

interface Props {
  medication?: Medication | null
  mode?: 'add' | 'edit'
}

interface Emits {
  (e: 'close'): void
  (e: 'add', data: MedicationFormData): void
  (e: 'bulk-add', data: BulkMedicationEntry[]): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'add'
})

const emit = defineEmits<Emits>()

const { t } = useI18n()

// Enhanced form state
const form = reactive<MedicationFormData>({
  name: '',
  dosage: '',
  frequency: '',
  time: '',
  stock: 0,
  minStock: 10,
  instructions: '',
  category: '',
  // Schedule information
  scheduleTiming: 'morning',
  scheduleCustomTime: '',
  scheduleDosageAmount: 1.0,
  scheduleInstructions: '',
  // New enhanced fields
  strength: '',
  manufacturer: '',
  activeIngredients: '',
  sideEffects: '',
  icd10Code: '',
  prescriptionNumber: '',
  prescribingDoctor: '',
  expirationDate: '',
  medicationImage: null,
  interactions: [],
  // Bulk entry support
  isBulkEntry: false,
  bulkMedications: []
})

const errors = reactive<Record<string, string>>({})
const loading = ref(false)
const activeTab = ref('basic')
const showBulkEntry = ref(false)
const showInteractionWarnings = ref(false)
const interactions = ref<MedicationInteraction[]>([])
const icd10Codes = ref<ICD10Code[]>([])
const searchingICD10 = ref(false)
const icd10SearchQuery = ref('')

// Watch for medication prop changes to populate form in edit mode
watch(() => props.medication, (medication) => {
  if (medication && props.mode === 'edit') {
    Object.assign(form, {
      name: medication.name,
      dosage: medication.dosage,
      frequency: medication.frequency,
      time: medication.time,
      stock: medication.stock,
      minStock: medication.minStock,
      instructions: medication.instructions,
      category: medication.category,
      strength: medication.strength || '',
      manufacturer: medication.manufacturer || '',
      activeIngredients: medication.activeIngredients || '',
      sideEffects: medication.sideEffects || '',
      icd10Code: medication.icd10Code || '',
      prescriptionNumber: medication.prescriptionNumber || '',
      prescribingDoctor: medication.prescribingDoctor || '',
      expirationDate: medication.expirationDate || '',
      interactions: medication.interactions || []
    })
  }
}, { immediate: true })

// Enhanced form validation
const validateForm = (): boolean => {
  // Clear all errors
  Object.keys(errors).forEach(key => errors[key] = '')

  let isValid = true

  // Basic validation
  if (!form.name.trim()) {
    errors.name = t('validation.medicationNameRequired')
    isValid = false
  }

  if (!form.strength?.trim()) {
    errors.strength = t('validation.strengthRequired')
    isValid = false
  }

  if (!form.dosage.trim()) {
    errors.dosage = t('validation.dosageRequired')
    isValid = false
  }

  if (!form.frequency.trim()) {
    errors.frequency = t('validation.frequencyRequired')
    isValid = false
  }

  if (!form.time.trim()) {
    errors.time = t('validation.timeRequired')
    isValid = false
  }

  if (form.stock < 0) {
    errors.stock = t('validation.stockCannotBeNegative')
    isValid = false
  }

  if (form.minStock < 0) {
    errors.minStock = t('validation.minStockCannotBeNegative')
    isValid = false
  }

  if (!form.instructions.trim()) {
    errors.instructions = t('validation.instructionsRequired')
    isValid = false
  }

  if (!form.category.trim()) {
    errors.category = t('validation.categoryRequired')
    isValid = false
  }

  // Enhanced validation
  if (!form.manufacturer?.trim()) {
    errors.manufacturer = t('validation.manufacturerRequired')
    isValid = false
  }

  if (!form.activeIngredients?.trim()) {
    errors.activeIngredients = t('validation.activeIngredientsRequired')
    isValid = false
  }

  if (!form.sideEffects?.trim()) {
    errors.sideEffects = t('validation.sideEffectsRequired')
    isValid = false
  }

  if (!form.prescriptionNumber?.trim()) {
    errors.prescriptionNumber = t('validation.prescriptionNumberRequired')
    isValid = false
  }

  if (!form.prescribingDoctor?.trim()) {
    errors.prescribingDoctor = t('validation.prescribingDoctorRequired')
    isValid = false
  }

  if (!form.expirationDate) {
    errors.expirationDate = t('validation.expirationDateRequired')
    isValid = false
  } else if (new Date(form.expirationDate) <= new Date()) {
    errors.expirationDate = t('validation.expirationDateInvalid')
    isValid = false
  }

  if (!form.icd10Code?.trim()) {
    errors.icd10Code = t('validation.icd10CodeRequired')
    isValid = false
  }

  // Image validation
  if (form.medicationImage) {
    const maxSize = 5 * 1024 * 1024 // 5MB
    if (form.medicationImage.size > maxSize) {
      errors.medicationImage = t('validation.imageSizeLimit')
      isValid = false
    }

    const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
    if (!allowedTypes.includes(form.medicationImage.type)) {
      errors.medicationImage = t('validation.imageFormatInvalid')
      isValid = false
    }
  }

  // Validate schedule information
  if (form.scheduleTiming === 'custom' && !form.scheduleCustomTime) {
    errors.scheduleCustomTime = t('validation.customTimeRequired')
    isValid = false
  }

  if ((form.scheduleDosageAmount || 0) <= 0) {
    errors.scheduleDosageAmount = t('validation.dosageAmountMustBePositive')
    isValid = false
  }

  return isValid
}

// Smart frequency detection
const detectFrequency = (text: string): string => {
  const lowerText = text.toLowerCase()
  
  if (lowerText.includes('once daily') || lowerText.includes('daily') || lowerText.includes('1x')) {
    return 'Once daily'
  } else if (lowerText.includes('twice daily') || lowerText.includes('2x') || lowerText.includes('bid')) {
    return 'Twice daily'
  } else if (lowerText.includes('three times daily') || lowerText.includes('3x') || lowerText.includes('tid')) {
    return 'Three times daily'
  } else if (lowerText.includes('every 6 hours') || lowerText.includes('q6h')) {
    return 'Every 6 hours'
  } else if (lowerText.includes('every 8 hours') || lowerText.includes('q8h')) {
    return 'Every 8 hours'
  } else if (lowerText.includes('every 12 hours') || lowerText.includes('q12h')) {
    return 'Every 12 hours'
  } else if (lowerText.includes('as needed') || lowerText.includes('prn')) {
    return 'As needed'
  }
  
  return 'Once daily' // Default
}

// Handle image upload
const handleImageUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files && target.files[0]) {
    form.medicationImage = target.files[0]
  }
}

// Remove uploaded image
const removeImage = () => {
  form.medicationImage = null
}

// Search ICD-10 codes
const searchICD10Codes = async (query: string) => {
  if (query.length < 2) return
  
  searchingICD10.value = true
  try {
    // Mock ICD-10 codes - in real implementation, this would call an API
    const mockCodes: ICD10Code[] = [
      { code: 'E11.9', description: 'Type 2 diabetes mellitus without complications', category: 'Endocrine' },
      { code: 'I10', description: 'Essential (primary) hypertension', category: 'Cardiovascular' },
      { code: 'J45.909', description: 'Unspecified asthma with (acute) exacerbation', category: 'Respiratory' },
      { code: 'M79.3', description: 'Sciatica, unspecified side', category: 'Musculoskeletal' },
      { code: 'F41.1', description: 'Generalized anxiety disorder', category: 'Mental Health' }
    ]
    
    icd10Codes.value = mockCodes.filter(code => 
      code.code.toLowerCase().includes(query.toLowerCase()) ||
      code.description.toLowerCase().includes(query.toLowerCase())
    )
  } catch (error) {
    console.error('Failed to search ICD-10 codes:', error)
  } finally {
    searchingICD10.value = false
  }
}

// Check for drug interactions
const checkInteractions = async () => {
  if (!form.name.trim()) return
  
  showInteractionWarnings.value = true
  loading.value = true
  
  try {
    // Mock interaction check - in real implementation, this would call an API
    const mockInteractions: MedicationInteraction[] = [
      {
        severity: 'moderate',
        description: 'May increase risk of bleeding',
        medications: ['Aspirin', 'Warfarin'],
        recommendations: 'Monitor closely for signs of bleeding'
      }
    ]
    
    interactions.value = mockInteractions
  } catch (error) {
    console.error('Failed to check interactions:', error)
  } finally {
    loading.value = false
  }
}

// Bulk entry functions
const addBulkMedication = () => {
  if (!form.bulkMedications) form.bulkMedications = []
  form.bulkMedications.push({
    name: '',
    strength: '',
    dosage: '',
    frequency: '',
    instructions: '',
    manufacturer: '',
    prescriptionNumber: '',
    prescribingDoctor: ''
  })
}

const removeBulkMedication = (index: number) => {
  if (form.bulkMedications) {
    form.bulkMedications.splice(index, 1)
  }
}

const saveBulkMedications = async () => {
  if (!form.bulkMedications || form.bulkMedications.length === 0) return
  
  loading.value = true
  try {
    await emit('bulk-add', form.bulkMedications)
    form.bulkMedications = []
    showBulkEntry.value = false
  } catch (error) {
    console.error('Failed to save bulk medications:', error)
  } finally {
    loading.value = false
  }
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  try {
    await emit('add', { ...form })
    // Reset form
    Object.assign(form, {
      name: '',
      dosage: '',
      frequency: '',
      time: '',
      stock: 0,
      minStock: 10,
      instructions: '',
      category: '',
      strength: '',
      manufacturer: '',
      activeIngredients: '',
      sideEffects: '',
      icd10Code: '',
      prescriptionNumber: '',
      prescribingDoctor: '',
      expirationDate: '',
      medicationImage: null,
      interactions: [],
      isBulkEntry: false,
      bulkMedications: []
    })
  } catch (error) {
    console.error('Failed to add medication:', error)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  emit('close')
}

// Predefined categories
const categories = [
  'Pain Relief',
  'Antibiotic',
  'Vitamin',
  'Blood Pressure',
  'Diabetes',
  'Heart Medication',
  'Mental Health',
  'Other'
]

// Predefined frequencies
const frequencies = [
  'Once daily',
  'Twice daily',
  'Three times daily',
  'Every 6 hours',
  'Every 8 hours',
  'Every 12 hours',
  'As needed',
  'Other'
]

// Computed properties
const imagePreview = computed(() => {
  if (form.medicationImage) {
    return URL.createObjectURL(form.medicationImage)
  }
  return null
})

const hasInteractions = computed(() => interactions.value.length > 0)

const bulkMedicationCount = computed(() => form.bulkMedications?.length || 0)
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-4xl max-h-[90vh] overflow-y-auto">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-base-content">
          <svg class="w-6 h-6 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ props.mode === 'edit' ? t('dashboard.editMedication') : t('dashboard.addMedication') }}
        </h3>
        <button @click="handleClose" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Tab Navigation -->
      <div class="tabs tabs-boxed mb-6">
        <button 
          @click="activeTab = 'basic'" 
          :class="['tab', activeTab === 'basic' ? 'tab-active' : '']"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ t('form.basicInfo') }}
        </button>
        <button 
          @click="activeTab = 'details'" 
          :class="['tab', activeTab === 'details' ? 'tab-active' : '']"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ t('form.details') }}
        </button>
        <button 
          @click="activeTab = 'prescription'" 
          :class="['tab', activeTab === 'prescription' ? 'tab-active' : '']"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ t('form.prescriptionDetails') }}
        </button>
        <button 
          @click="activeTab = 'bulk'" 
          :class="['tab', activeTab === 'bulk' ? 'tab-active' : '']"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          {{ t('form.bulkEntry') }}
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Basic Information Tab -->
        <div v-if="activeTab === 'basic'" class="space-y-6">
          <!-- Basic Information -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.medicationName') }} *</span>
              </label>
              <input
                v-model="form.name"
                type="text"
                :placeholder="t('form.medicationName')"
                :class="[
                  'input input-bordered w-full',
                  errors.name ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.name" class="label">
                <span class="label-text-alt text-error">{{ errors.name }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.category') }} *</span>
              </label>
              <select
                v-model="form.category"
                :class="[
                  'select select-bordered w-full',
                  errors.category ? 'select-error' : ''
                ]"
              >
                <option value="">{{ t('form.selectFrequency') }}</option>
                <option v-for="category in categories" :key="category" :value="category">
                  {{ category }}
                </option>
              </select>
              <label v-if="errors.category" class="label">
                <span class="label-text-alt text-error">{{ errors.category }}</span>
              </label>
            </div>
          </div>

          <!-- Strength and Dosage -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.strength') }} *</span>
              </label>
              <input
                v-model="form.strength"
                type="text"
                :placeholder="t('form.strengthPlaceholder')"
                :class="[
                  'input input-bordered w-full',
                  errors.strength ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.strength" class="label">
                <span class="label-text-alt text-error">{{ errors.strength }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.dosage') }} *</span>
              </label>
              <input
                v-model="form.dosage"
                type="text"
                :placeholder="t('form.dosagePlaceholder')"
                :class="[
                  'input input-bordered w-full',
                  errors.dosage ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.dosage" class="label">
                <span class="label-text-alt text-error">{{ errors.dosage }}</span>
              </label>
            </div>
          </div>

                  <!-- Frequency and Time -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.frequency') }} *</span>
              </label>
              <select
                v-model="form.frequency"
                :class="[
                  'select select-bordered w-full',
                  errors.frequency ? 'select-error' : ''
                ]"
              >
                <option value="">{{ t('form.selectFrequency') }}</option>
                <option v-for="frequency in frequencies" :key="frequency" :value="frequency">
                  {{ frequency }}
                </option>
              </select>
              <label v-if="errors.frequency" class="label">
                <span class="label-text-alt text-error">{{ errors.frequency }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.time') }} *</span>
              </label>
              <input
                v-model="form.time"
                type="text"
                :placeholder="t('form.timePlaceholder')"
                :class="[
                  'input input-bordered w-full',
                  errors.time ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.time" class="label">
                <span class="label-text-alt text-error">{{ errors.time }}</span>
              </label>
            </div>
          </div>

          <!-- Stock Information -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.currentStock') }}</span>
              </label>
              <input
                v-model.number="form.stock"
                type="number"
                min="0"
                placeholder="0"
                :class="[
                  'input input-bordered w-full',
                  errors.stock ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.stock" class="label">
                <span class="label-text-alt text-error">{{ errors.stock }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.minimumStock') }}</span>
              </label>
              <input
                v-model.number="form.minStock"
                type="number"
                min="0"
                placeholder="10"
                :class="[
                  'input input-bordered w-full',
                  errors.minStock ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.minStock" class="label">
                <span class="label-text-alt text-error">{{ errors.minStock }}</span>
              </label>
            </div>
          </div>

        <!-- Schedule Information -->
        <div class="card bg-base-200 p-4 mb-4">
          <h4 class="font-semibold text-base-content mb-3">
            <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ t('form.scheduleInformation') }}
          </h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.scheduleTiming') }}</span>
              </label>
              <select
                v-model="form.scheduleTiming"
                class="select select-bordered w-full"
              >
                <option value="morning">{{ t('form.morning') }}</option>
                <option value="noon">{{ t('form.noon') }}</option>
                <option value="night">{{ t('form.night') }}</option>
                <option value="custom">{{ t('form.customTime') }}</option>
              </select>
            </div>

            <div class="form-control" v-if="form.scheduleTiming === 'custom'">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.customTime') }}</span>
              </label>
              <input
                v-model="form.scheduleCustomTime"
                type="time"
                :class="[
                  'input input-bordered w-full',
                  errors.scheduleCustomTime ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.scheduleCustomTime" class="label">
                <span class="label-text-alt text-error">{{ errors.scheduleCustomTime }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.dosageAmount') }}</span>
              </label>
              <input
                v-model.number="form.scheduleDosageAmount"
                type="number"
                min="0.1"
                step="0.1"
                placeholder="1.0"
                :class="[
                  'input input-bordered w-full',
                  errors.scheduleDosageAmount ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.scheduleDosageAmount" class="label">
                <span class="label-text-alt text-error">{{ errors.scheduleDosageAmount }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.scheduleInstructions') }}</span>
              </label>
              <textarea
                v-model="form.scheduleInstructions"
                :placeholder="t('form.scheduleInstructionsPlaceholder')"
                class="textarea textarea-bordered h-20"
              ></textarea>
            </div>
          </div>
        </div>

          <!-- Instructions -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">{{ t('form.instructions') }} *</span>
            </label>
            <textarea
              v-model="form.instructions"
              :placeholder="t('form.instructionsPlaceholder')"
              :class="[
                'textarea textarea-bordered h-24',
                errors.instructions ? 'textarea-error' : ''
              ]"
            ></textarea>
            <label v-if="errors.instructions" class="label">
              <span class="label-text-alt text-error">{{ errors.instructions }}</span>
            </label>
          </div>
        </div>

        <!-- Details Tab -->
        <div v-if="activeTab === 'details'" class="space-y-6">
          <!-- Manufacturer and Active Ingredients -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.manufacturer') }} *</span>
              </label>
              <input
                v-model="form.manufacturer"
                type="text"
                :placeholder="t('form.manufacturerPlaceholder')"
                :class="[
                  'input input-bordered w-full',
                  errors.manufacturer ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.manufacturer" class="label">
                <span class="label-text-alt text-error">{{ errors.manufacturer }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.activeIngredients') }} *</span>
              </label>
              <textarea
                v-model="form.activeIngredients"
                :placeholder="t('form.activeIngredientsPlaceholder')"
                :class="[
                  'textarea textarea-bordered h-20',
                  errors.activeIngredients ? 'textarea-error' : ''
                ]"
              ></textarea>
              <label v-if="errors.activeIngredients" class="label">
                <span class="label-text-alt text-error">{{ errors.activeIngredients }}</span>
              </label>
            </div>
          </div>

          <!-- Side Effects -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">{{ t('form.sideEffects') }} *</span>
            </label>
            <textarea
              v-model="form.sideEffects"
              :placeholder="t('form.sideEffectsPlaceholder')"
              :class="[
                'textarea textarea-bordered h-24',
                errors.sideEffects ? 'textarea-error' : ''
              ]"
            ></textarea>
            <label v-if="errors.sideEffects" class="label">
              <span class="label-text-alt text-error">{{ errors.sideEffects }}</span>
            </label>
          </div>

          <!-- ICD-10 Code Selection -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">{{ t('form.icd10Code') }} *</span>
            </label>
            <div class="relative">
              <input
                v-model="icd10SearchQuery"
                type="text"
                :placeholder="t('icd10.searchPlaceholder')"
                class="input input-bordered w-full pr-10"
                @input="searchICD10Codes(icd10SearchQuery)"
              />
              <button
                v-if="searchingICD10"
                class="absolute right-3 top-3 loading loading-spinner loading-sm"
              ></button>
            </div>
            <div v-if="icd10Codes.length > 0" class="mt-2 max-h-40 overflow-y-auto border rounded-lg">
              <div
                v-for="code in icd10Codes"
                :key="code.code"
                @click="form.icd10Code = code.code; icd10SearchQuery = code.code; icd10Codes = []"
                class="p-3 hover:bg-base-200 cursor-pointer border-b last:border-b-0"
              >
                <div class="font-medium">{{ code.code }}</div>
                <div class="text-sm text-base-content/70">{{ code.description }}</div>
                <div class="text-xs text-base-content/50">{{ code.category }}</div>
              </div>
            </div>
            <label v-if="errors.icd10Code" class="label">
              <span class="label-text-alt text-error">{{ errors.icd10Code }}</span>
            </label>
          </div>

          <!-- Image Upload -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">{{ t('form.medicationImage') }}</span>
            </label>
            <div class="flex items-center space-x-4">
              <input
                type="file"
                accept="image/*"
                @change="handleImageUpload"
                class="file-input file-input-bordered w-full max-w-xs"
              />
              <button
                v-if="form.medicationImage"
                @click="removeImage"
                type="button"
                class="btn btn-sm btn-error"
              >
                {{ t('common.remove') }}
              </button>
            </div>
            <div v-if="imagePreview" class="mt-4">
              <img :src="imagePreview" alt="Medication preview" class="max-w-xs rounded-lg border" />
            </div>
            <label v-if="errors.medicationImage" class="label">
              <span class="label-text-alt text-error">{{ errors.medicationImage }}</span>
            </label>
          </div>

          <!-- Interaction Warnings -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">{{ t('form.interactionWarnings') }}</span>
            </label>
            <button
              @click="checkInteractions"
              type="button"
              class="btn btn-outline btn-sm"
              :disabled="!form.name.trim() || loading"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              {{ t('interactions.title') }}
            </button>
            
            <div v-if="showInteractionWarnings && hasInteractions" class="mt-4 alert alert-warning">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <div>
                <h3 class="font-bold">{{ t('interactions.interactionsFound', { count: interactions.length }) }}</h3>
                <div class="text-sm">
                  <div v-for="interaction in interactions" :key="interaction.description" class="mt-2">
                    <div class="font-medium">{{ interaction.description }}</div>
                    <div class="text-xs opacity-70">{{ t('interactions.severity.' + interaction.severity) }}</div>
                    <div class="text-xs">{{ interaction.recommendations }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Prescription Tab -->
        <div v-if="activeTab === 'prescription'" class="space-y-6">
          <!-- Prescription Details -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.prescriptionNumber') }} *</span>
              </label>
              <input
                v-model="form.prescriptionNumber"
                type="text"
                :placeholder="t('form.prescriptionNumberPlaceholder')"
                :class="[
                  'input input-bordered w-full',
                  errors.prescriptionNumber ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.prescriptionNumber" class="label">
                <span class="label-text-alt text-error">{{ errors.prescriptionNumber }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.prescribingDoctor') }} *</span>
              </label>
              <input
                v-model="form.prescribingDoctor"
                type="text"
                :placeholder="t('form.prescribingDoctorPlaceholder')"
                :class="[
                  'input input-bordered w-full',
                  errors.prescribingDoctor ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.prescribingDoctor" class="label">
                <span class="label-text-alt text-error">{{ errors.prescribingDoctor }}</span>
              </label>
            </div>
          </div>

          <!-- Expiration Date -->
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">{{ t('form.expirationDate') }} *</span>
            </label>
            <input
              v-model="form.expirationDate"
              type="date"
              :min="new Date().toISOString().split('T')[0]"
              :class="[
                'input input-bordered w-full',
                errors.expirationDate ? 'input-error' : ''
              ]"
            />
            <label v-if="errors.expirationDate" class="label">
              <span class="label-text-alt text-error">{{ errors.expirationDate }}</span>
            </label>
          </div>
        </div>

        <!-- Bulk Entry Tab -->
        <div v-if="activeTab === 'bulk'" class="space-y-6">
          <div class="alert alert-info">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 class="font-bold">{{ t('bulk.title') }}</h3>
              <div class="text-sm">{{ t('bulk.description') }}</div>
            </div>
          </div>

          <div class="flex justify-between items-center">
            <h4 class="font-semibold">{{ t('bulk.medicationCount', { count: bulkMedicationCount }) }}</h4>
            <button
              @click="addBulkMedication"
              type="button"
              class="btn btn-primary btn-sm"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              {{ t('bulk.addRow') }}
            </button>
          </div>

          <div v-if="form.bulkMedications && form.bulkMedications.length > 0" class="space-y-4">
            <div
              v-for="(medication, index) in form.bulkMedications"
              :key="index"
              class="card bg-base-200 p-4"
            >
              <div class="flex justify-between items-start mb-4">
                <h5 class="font-medium">Medication {{ index + 1 }}</h5>
                <button
                  @click="removeBulkMedication(index)"
                  type="button"
                  class="btn btn-sm btn-error"
                >
                  {{ t('bulk.removeRow') }}
                </button>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="form-control">
                  <label class="label">
                    <span class="label-text font-medium">{{ t('form.medicationName') }} *</span>
                  </label>
                  <input
                    v-model="medication.name"
                    type="text"
                    :placeholder="t('form.medicationName')"
                    class="input input-bordered w-full"
                  />
                </div>

                <div class="form-control">
                  <label class="label">
                    <span class="label-text font-medium">{{ t('form.strength') }} *</span>
                  </label>
                  <input
                    v-model="medication.strength"
                    type="text"
                    :placeholder="t('form.strengthPlaceholder')"
                    class="input input-bordered w-full"
                  />
                </div>

                <div class="form-control">
                  <label class="label">
                    <span class="label-text font-medium">{{ t('form.dosage') }} *</span>
                  </label>
                  <input
                    v-model="medication.dosage"
                    type="text"
                    :placeholder="t('form.dosagePlaceholder')"
                    class="input input-bordered w-full"
                  />
                </div>

                <div class="form-control">
                  <label class="label">
                    <span class="label-text font-medium">{{ t('form.frequency') }} *</span>
                  </label>
                  <select v-model="medication.frequency" class="select select-bordered w-full">
                    <option value="">{{ t('form.selectFrequency') }}</option>
                    <option v-for="frequency in frequencies" :key="frequency" :value="frequency">
                      {{ frequency }}
                    </option>
                  </select>
                </div>

                <div class="form-control md:col-span-2">
                  <label class="label">
                    <span class="label-text font-medium">{{ t('form.instructions') }}</span>
                  </label>
                  <textarea
                    v-model="medication.instructions"
                    :placeholder="t('form.instructionsPlaceholder')"
                    class="textarea textarea-bordered h-20"
                  ></textarea>
                </div>
              </div>
            </div>

            <div class="flex justify-end space-x-2">
              <button
                @click="saveBulkMedications"
                type="button"
                class="btn btn-primary"
                :disabled="loading || bulkMedicationCount === 0"
              >
                <span v-if="loading" class="loading loading-spinner loading-sm"></span>
                {{ t('bulk.saveAll') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Form Actions -->
        <div class="modal-action">
          <button
            type="button"
            @click="handleClose"
            class="btn btn-ghost"
            :disabled="loading"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            v-if="activeTab !== 'bulk'"
            type="submit"
            class="btn btn-primary"
            :disabled="loading"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            {{ loading ? t('common.loading') : (props.mode === 'edit' ? t('common.update') : t('common.save')) }}
          </button>
        </div>
      </form>
    </div>

    <!-- Backdrop -->
    <div class="modal-backdrop" @click="handleClose"></div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  background-color: hsl(var(--color-base-content) / 0.2);
}

.form-control {
  width: 100%;
}

/* Custom styling for form elements */
.input:focus,
.select:focus,
.textarea:focus {
  border-color: hsl(var(--color-primary));
  box-shadow: 0 0 0 2px hsl(var(--color-primary) / 0.2);
}

.input-error:focus,
.select-error:focus,
.textarea-error:focus {
  border-color: hsl(var(--color-error));
  box-shadow: 0 0 0 2px hsl(var(--color-error) / 0.2);
}
</style> 