<template>
  <div class="step2-ocr-processing">
    <h3 class="text-xl font-semibold mb-4">
      <i class="fas fa-search text-primary mr-2"></i>
      {{ $t('workflow.step2.title', 'OCR Processing') }}
    </h3>

    <!-- Processing Status -->
    <div v-if="ocrState.isProcessing" class="text-center py-8">
      <div class="space-y-6">
        <!-- Progress indicator -->
        <div class="loading loading-spinner loading-lg text-primary"></div>
        
        <div class="space-y-2">
          <p class="text-lg font-medium">
            {{ $t('workflow.step2.processing', 'Processing prescription image...') }}
          </p>
          <p class="text-sm text-base-content/70">
            {{ currentProcessingStep }}
          </p>
        </div>

        <!-- Progress bar -->
        <div class="w-full max-w-md mx-auto">
          <div class="w-full bg-base-300 rounded-full h-3">
            <div
              class="bg-primary h-3 rounded-full transition-all duration-300"
              :style="{ width: `${ocrState.progress}%` }"
            ></div>
          </div>
          <div class="flex justify-between text-xs text-base-content/70 mt-1">
            <span>{{ $t('workflow.step2.progress', { progress: Math.round(ocrState.progress) }, 'Progress: {progress}%') }}</span>
            <span>{{ estimatedTimeRemaining }}</span>
          </div>
        </div>

        <!-- Processing steps -->
        <div class="max-w-md mx-auto">
          <div class="space-y-2">
            <div
              v-for="(step, index) in processingSteps"
              :key="index"
              class="flex items-center gap-3 p-2 rounded"
              :class="getStepClass(step.status)"
            >
              <div class="w-4 h-4 rounded-full flex items-center justify-center">
                <i :class="getStepIcon(step.status)"></i>
              </div>
              <span class="text-sm">{{ step.label }}</span>
              <span v-if="step.duration" class="text-xs text-base-content/60 ml-auto">
                {{ step.duration }}ms
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- OCR Results -->
    <div v-else-if="ocrState.result && ocrState.result.success" class="space-y-6">
      <!-- Success message -->
      <div class="alert alert-success">
        <i class="fas fa-check-circle"></i>
        <div>
          <span class="font-medium">{{ $t('workflow.step2.success', 'OCR processing completed successfully!') }}</span>
          <div class="text-sm opacity-80">
            {{ $t('workflow.step2.confidence', { confidence: Math.round(ocrState.result.confidence * 100) }, 'Confidence: {confidence}%') }}
          </div>
        </div>
      </div>

      <!-- Confidence indicator -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step2.confidenceLevel', 'Confidence Level') }}</h4>
          <div class="flex items-center gap-3">
            <div class="flex gap-1">
              <div
                v-for="i in 5"
                :key="i"
                class="w-4 h-4 rounded-full"
                :class="getConfidenceClass(i)"
              ></div>
            </div>
            <span class="text-sm font-medium">{{ confidenceText }}</span>
          </div>
          <div class="text-xs text-base-content/70 mt-2">
            {{ confidenceDescription }}
          </div>
        </div>
      </div>

      <!-- Extracted Information -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step2.extracted', 'Extracted Information') }}</h4>
          
          <!-- Prescription metadata -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ $t('workflow.step2.patientName', 'Patient Name') }}</span>
              </label>
              <input
                v-model="extractedData.patientName"
                type="text"
                class="input input-bordered"
                :placeholder="$t('workflow.step2.enterPatientName', 'Enter patient name')"
              />
            </div>
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ $t('workflow.step2.doctor', 'Prescribing Doctor') }}</span>
              </label>
              <input
                v-model="extractedData.prescribingDoctor"
                type="text"
                class="input input-bordered"
                :placeholder="$t('workflow.step2.enterDoctor', 'Enter doctor name')"
              />
            </div>
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ $t('workflow.step2.prescriptionNumber', 'Prescription Number') }}</span>
              </label>
              <input
                v-model="extractedData.prescriptionNumber"
                type="text"
                class="input input-bordered"
                :placeholder="$t('workflow.step2.enterPrescriptionNumber', 'Enter prescription number')"
              />
            </div>
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ $t('workflow.step2.prescriptionDate', 'Prescription Date') }}</span>
              </label>
              <input
                v-model="extractedData.prescriptionDate"
                type="date"
                class="input input-bordered"
              />
            </div>
          </div>

          <!-- Medications list -->
          <div class="space-y-3">
            <h5 class="font-medium">{{ $t('workflow.step2.medications', 'Medications') }}</h5>
            <div
              v-for="(medication, index) in extractedData.medications"
              :key="index"
              class="card bg-base-100"
            >
              <div class="card-body p-4">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h6 class="font-medium">{{ medication.name }}</h6>
                    <div class="text-sm text-base-content/70 space-y-1 mt-1">
                      <div v-if="medication.strength">
                        <span class="font-medium">{{ $t('workflow.step2.strength', 'Strength') }}:</span> {{ medication.strength }}
                      </div>
                      <div v-if="medication.dosage">
                        <span class="font-medium">{{ $t('workflow.step2.dosage', 'Dosage') }}:</span> {{ medication.dosage }}
                      </div>
                      <div v-if="medication.frequency">
                        <span class="font-medium">{{ $t('workflow.step2.frequency', 'Frequency') }}:</span> {{ medication.frequency }}
                      </div>
                      <div v-if="medication.instructions">
                        <span class="font-medium">{{ $t('workflow.step2.instructions', 'Instructions') }}:</span> {{ medication.instructions }}
                      </div>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 ml-4">
                    <div class="badge badge-sm" :class="getMedicationConfidenceClass(medication.confidence)">
                      {{ Math.round(medication.confidence * 100) }}%
                    </div>
                    <button
                      @click="editMedication(index)"
                      class="btn btn-circle btn-sm btn-ghost"
                      :title="$t('workflow.step2.edit', 'Edit')"
                    >
                      <i class="fas fa-edit"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Processing statistics -->
          <div class="mt-4 p-3 bg-base-100 rounded-lg">
            <h5 class="font-medium mb-2">{{ $t('workflow.step2.statistics', 'Processing Statistics') }}</h5>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step2.processingTime', 'Processing Time') }}</div>
                <div class="font-medium">{{ formatTime(ocrState.result.processingTime) }}</div>
              </div>
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step2.medicationsFound', 'Medications Found') }}</div>
                <div class="font-medium">{{ extractedData.medications.length }}</div>
              </div>
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step2.averageConfidence', 'Avg Confidence') }}</div>
                <div class="font-medium">{{ averageConfidence }}%</div>
              </div>
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step2.textLength', 'Text Length') }}</div>
                <div class="font-medium">{{ ocrState.result.text.length }} chars</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="flex gap-2">
        <button
          @click="retryOCR"
          class="btn btn-outline"
        >
          <i class="fas fa-redo mr-2"></i>
          {{ $t('workflow.step2.retry', 'Retry OCR') }}
        </button>
        <button
          @click="adjustPreprocessing"
          class="btn btn-outline"
        >
          <i class="fas fa-sliders-h mr-2"></i>
          {{ $t('workflow.step2.adjustSettings', 'Adjust Settings') }}
        </button>
        <button
          @click="confirmResults"
          class="btn btn-primary"
        >
          <i class="fas fa-check mr-2"></i>
          {{ $t('workflow.step2.confirm', 'Confirm Results') }}
        </button>
      </div>
    </div>

    <!-- Error state -->
    <div v-else-if="ocrState.error" class="text-center py-8">
      <div class="alert alert-error max-w-md mx-auto">
        <i class="fas fa-exclamation-triangle"></i>
        <div>
          <span class="font-medium">{{ $t('workflow.step2.error', 'OCR processing failed') }}</span>
          <div class="text-sm opacity-80">{{ ocrState.error }}</div>
        </div>
      </div>
      
      <div class="mt-4 space-y-2">
        <button
          @click="retryOCR"
          class="btn btn-primary"
        >
          <i class="fas fa-redo mr-2"></i>
          {{ $t('workflow.step2.retry', 'Retry OCR') }}
        </button>
        <button
          @click="adjustPreprocessing"
          class="btn btn-outline"
        >
          <i class="fas fa-sliders-h mr-2"></i>
          {{ $t('workflow.step2.adjustSettings', 'Adjust Settings') }}
        </button>
      </div>
    </div>

    <!-- Preprocessing Settings Modal -->
    <div v-if="showPreprocessingModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">{{ $t('workflow.step2.preprocessingSettings', 'Preprocessing Settings') }}</h3>
        
        <div class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('workflow.step2.contrast', 'Contrast') }}</span>
              <span class="label-text-alt">{{ preprocessingOptions.contrast }}</span>
            </label>
            <input
              v-model="preprocessingOptions.contrast"
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              class="range range-primary"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('workflow.step2.brightness', 'Brightness') }}</span>
              <span class="label-text-alt">{{ preprocessingOptions.brightness }}</span>
            </label>
            <input
              v-model="preprocessingOptions.brightness"
              type="range"
              min="-0.5"
              max="0.5"
              step="0.1"
              class="range range-primary"
            />
          </div>
          
          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">{{ $t('workflow.step2.sharpen', 'Sharpen') }}</span>
              <input
                v-model="preprocessingOptions.sharpen"
                type="checkbox"
                class="checkbox checkbox-primary"
              />
            </label>
          </div>
          
          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">{{ $t('workflow.step2.denoise', 'Denoise') }}</span>
              <input
                v-model="preprocessingOptions.denoise"
                type="checkbox"
                class="checkbox checkbox-primary"
              />
            </label>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('workflow.step2.threshold', 'Threshold') }}</span>
              <span class="label-text-alt">{{ preprocessingOptions.threshold }}</span>
            </label>
            <input
              v-model="preprocessingOptions.threshold"
              type="range"
              min="0"
              max="255"
              step="1"
              class="range range-primary"
            />
          </div>
        </div>
        
        <div class="modal-action">
          <button
            @click="closePreprocessingModal"
            class="btn btn-ghost"
          >
            {{ $t('workflow.step2.cancel', 'Cancel') }}
          </button>
          <button
            @click="applyPreprocessingSettings"
            class="btn btn-primary"
          >
            {{ $t('workflow.step2.apply', 'Apply & Retry') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { OCRState, PreprocessingOptions } from '@/services/ocrService'
import type { PrescriptionMedication } from '@/types/medication'

const { t } = useI18n()

// Props
interface Props {
  image?: string | null
  ocrState: OCRState
  preprocessingOptions: PreprocessingOptions
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'ocr-complete': [result: any]
  'retry-ocr': []
}>()

// Reactive state
const showPreprocessingModal = ref(false)
const extractedData = reactive({
  patientName: '',
  prescribingDoctor: '',
  prescriptionNumber: '',
  prescriptionDate: '',
  medications: [] as PrescriptionMedication[]
})

// Processing steps simulation
const processingSteps = ref([
  { label: t('workflow.step2.step1', 'Loading image'), status: 'pending', duration: 0 },
  { label: t('workflow.step2.step2', 'Preprocessing image'), status: 'pending', duration: 0 },
  { label: t('workflow.step2.step3', 'Running OCR'), status: 'pending', duration: 0 },
  { label: t('workflow.step2.step4', 'Extracting text'), status: 'pending', duration: 0 },
  { label: t('workflow.step2.step5', 'Parsing medications'), status: 'pending', duration: 0 },
  { label: t('workflow.step2.step6', 'Validating results'), status: 'pending', duration: 0 }
])

// Computed properties
const currentProcessingStep = computed(() => {
  const currentStep = processingSteps.value.find(step => step.status === 'processing')
  return currentStep?.label || t('workflow.step2.processing', 'Processing...')
})

const estimatedTimeRemaining = computed(() => {
  if (props.ocrState.progress === 0) return ''
  const elapsed = Date.now() - (startTime.value || Date.now())
  const total = (elapsed / props.ocrState.progress) * 100
  const remaining = total - elapsed
  return t('workflow.step2.estimatedTime', { time: Math.round(remaining / 1000) }, '~{time}s remaining')
})

const averageConfidence = computed(() => {
  if (!extractedData.medications.length) return 0
  const total = extractedData.medications.reduce((sum, med) => sum + (med.confidence || 0), 0)
  return Math.round((total / extractedData.medications.length) * 100)
})

const confidenceText = computed(() => {
  const confidence = props.ocrState.result?.confidence || 0
  if (confidence >= 0.8) return t('workflow.step2.confidence.high', 'High')
  if (confidence >= 0.6) return t('workflow.step2.confidence.medium', 'Medium')
  if (confidence >= 0.4) return t('workflow.step2.confidence.low', 'Low')
  return t('workflow.step2.confidence.veryLow', 'Very Low')
})

const confidenceDescription = computed(() => {
  const confidence = props.ocrState.result?.confidence || 0
  if (confidence >= 0.8) return t('workflow.step2.confidence.highDesc', 'Excellent text recognition quality')
  if (confidence >= 0.6) return t('workflow.step2.confidence.mediumDesc', 'Good text recognition quality')
  if (confidence >= 0.4) return t('workflow.step2.confidence.lowDesc', 'Fair text recognition quality')
  return t('workflow.step2.confidence.veryLowDesc', 'Poor text recognition quality - manual review recommended')
})

// Local state
let startTime = ref<number | null>(null)

// Methods
const getStepClass = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-success/10 text-success'
    case 'processing': return 'bg-primary/10 text-primary'
    case 'error': return 'bg-error/10 text-error'
    default: return 'bg-base-200 text-base-content/70'
  }
}

const getStepIcon = (status: string) => {
  switch (status) {
    case 'completed': return 'fas fa-check text-success'
    case 'processing': return 'fas fa-spinner fa-spin text-primary'
    case 'error': return 'fas fa-times text-error'
    default: return 'fas fa-circle text-base-content/30'
  }
}

const getConfidenceClass = (level: number) => {
  const confidence = props.ocrState.result?.confidence || 0
  const confidenceLevel = Math.ceil(confidence * 5)
  return level <= confidenceLevel ? 'bg-success' : 'bg-base-300'
}

const getMedicationConfidenceClass = (confidence: number) => {
  if (confidence >= 0.8) return 'badge-success'
  if (confidence >= 0.6) return 'badge-warning'
  return 'badge-error'
}

const formatTime = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const retryOCR = () => {
  emit('retry-ocr')
}

const adjustPreprocessing = () => {
  showPreprocessingModal.value = true
}

const closePreprocessingModal = () => {
  showPreprocessingModal.value = false
}

const applyPreprocessingSettings = () => {
  closePreprocessingModal()
  retryOCR()
}

const editMedication = (index: number) => {
  // This would open a medication edit modal
  console.log('Edit medication:', index)
}

const confirmResults = () => {
  emit('ocr-complete', {
    ...props.ocrState.result,
    extractedData
  })
}

// Simulate processing steps
const simulateProcessingSteps = () => {
  if (!props.ocrState.isProcessing) return
  
  let currentStepIndex = 0
  
  const processStep = () => {
    if (currentStepIndex < processingSteps.value.length) {
      const step = processingSteps.value[currentStepIndex]
      step.status = 'processing'
      
      setTimeout(() => {
        step.status = 'completed'
        step.duration = Math.random() * 1000 + 500
        currentStepIndex++
        
        if (currentStepIndex < processingSteps.value.length) {
          processStep()
        }
      }, Math.random() * 2000 + 1000)
    }
  }
  
  processStep()
}

// Watch for OCR state changes
watch(() => props.ocrState.isProcessing, (isProcessing) => {
  if (isProcessing) {
    startTime.value = Date.now()
    // Reset processing steps
    processingSteps.value.forEach(step => {
      step.status = 'pending'
      step.duration = 0
    })
    simulateProcessingSteps()
  }
})

watch(() => props.ocrState.result, (result) => {
  if (result && result.success) {
    // Extract data from OCR result
    extractedData.medications = result.medications.map(med => ({
      name: med.name,
      genericName: med.genericName,
      strength: med.strength || '',
      dosage: med.dosage,
      frequency: med.frequency,
      quantity: 30,
      refills: 0,
      instructions: med.instructions,
      drugDatabaseId: undefined,
      interactions: [],
      sideEffects: [],
      contraindications: [],
      confidence: med.confidence
    }))
    
    // Extract prescription metadata
    if (result.prescriptionNumber) {
      extractedData.prescriptionNumber = result.prescriptionNumber
    }
    if (result.doctorName) {
      extractedData.prescribingDoctor = result.doctorName
    }
  }
})

// Lifecycle
onMounted(() => {
  // Set default prescription date
  extractedData.prescriptionDate = new Date().toISOString().split('T')[0]
})
</script>

<style scoped>
.range {
  @apply w-full;
}

.modal {
  @apply z-50;
}
</style> 