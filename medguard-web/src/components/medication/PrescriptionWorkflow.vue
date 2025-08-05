<template>
  <div class="prescription-workflow">
    <!-- Header with Progress -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="flex items-center justify-between mb-4">
          <h2 class="card-title text-2xl font-bold">
            <i class="fas fa-prescription text-primary mr-2"></i>
            {{ $t('workflow.title', 'Prescription Workflow') }}
          </h2>
          <div class="flex items-center gap-2">
            <div class="badge badge-primary">{{ currentStep + 1 }}/7</div>
            <div class="badge badge-outline">{{ workflowState.status }}</div>
            <div v-if="workflowState.totalMedications > 0" class="badge badge-info">
              {{ workflowState.totalMedications }} {{ $t('workflow.medications', 'medications') }}
            </div>
          </div>
        </div>
        
        <!-- Enhanced Progress Bar -->
        <div class="w-full bg-base-300 rounded-full h-3 mb-4">
          <div
            class="bg-primary h-3 rounded-full transition-all duration-500"
            :style="{ width: `${((currentStep + 1) / 7) * 100}%` }"
          ></div>
        </div>

        <!-- Auto-save indicator with enhanced status -->
        <div class="flex items-center justify-between">
          <div v-if="autoSaveStatus.isSaving" class="flex items-center gap-2 text-sm text-base-content/70">
            <div class="loading loading-spinner loading-xs"></div>
            {{ $t('workflow.autoSaving', 'Auto-saving...') }}
          </div>
          <div v-else-if="autoSaveStatus.lastSaved" class="flex items-center gap-2 text-sm text-success">
            <i class="fas fa-check-circle"></i>
            {{ $t('workflow.lastSaved', { time: formatTime(autoSaveStatus.lastSaved) }, 'Last saved: {time}') }}
          </div>
          
          <!-- Workflow statistics -->
          <div class="flex items-center gap-4 text-xs text-base-content/60">
            <span v-if="workflowState.processingTime > 0">
              <i class="fas fa-clock mr-1"></i>
              {{ formatDuration(workflowState.processingTime) }}
            </span>
            <span v-if="workflowState.totalMedications > 0">
              <i class="fas fa-pills mr-1"></i>
              {{ workflowState.totalMedications }} {{ $t('workflow.medications', 'medications') }}
            </span>
            <span v-if="workflowState.interactionsFound > 0">
              <i class="fas fa-exclamation-triangle mr-1"></i>
              {{ workflowState.interactionsFound }} {{ $t('workflow.interactions', 'interactions') }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced Step Indicator -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="steps steps-horizontal w-full">
          <div
            v-for="(step, index) in workflowSteps"
            :key="index"
            class="step cursor-pointer"
            :class="{
              'step-primary': currentStep >= index,
              'step-neutral': currentStep < index,
              'step-error': stepErrors[index],
              'step-success': stepCompleted[index]
            }"
            @click="goToStep(index)"
          >
            <div class="step-icon">
              <i :class="step.icon"></i>
            </div>
            <div class="step-content">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-description">{{ step.description }}</div>
              <div v-if="stepStats[index]" class="step-stats text-xs text-base-content/60">
                {{ stepStats[index] }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step Content -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <!-- Step 1: Enhanced Image Capture -->
        <div v-if="currentStep === 0" class="step-content">
          <Step1ImageCapture
            v-model:image="workflowState.prescriptionImage"
            v-model:showCamera="cameraState.showCamera"
            :isProcessing="workflowState.isProcessing"
            :cameraSettings="cameraSettings"
            :imageMetadata="workflowState.imageMetadata"
            @image-captured="handleImageCaptured"
            @image-uploaded="handleImageUploaded"
            @camera-settings-changed="handleCameraSettingsChanged"
          />
        </div>

        <!-- Step 2: Enhanced OCR Processing -->
        <div v-if="currentStep === 1" class="step-content">
          <Step2OCRProcessing
            :image="workflowState.prescriptionImage"
            :ocrState="ocrState"
            :preprocessingOptions="imagePreprocessing"
            :processingSteps="ocrProcessingSteps"
            @ocr-complete="handleOCRComplete"
            @retry-ocr="handleRetryOCR"
            @preprocessing-changed="handlePreprocessingChanged"
          />
        </div>

        <!-- Step 3: Enhanced Medication Review -->
        <div v-if="currentStep === 2" class="step-content">
          <Step3MedicationReview
            :medications="workflowState.extractedMedications"
            :validationResults="validationResults"
            :drugDatabase="drugDatabase"
            @medications-updated="handleMedicationsUpdated"
            @validation-complete="handleValidationComplete"
            @bulk-edit="handleBulkEdit"
          />
        </div>

        <!-- Step 4: Enhanced Drug Interactions -->
        <div v-if="currentStep === 3" class="step-content">
          <Step4DrugInteractions
            :medications="workflowState.extractedMedications"
            :interactions="drugInteractions"
            :validationResults="validationResults"
            :interactionSeverity="interactionSeverity"
            @interactions-checked="handleInteractionsChecked"
            @severity-updated="handleSeverityUpdated"
          />
        </div>

        <!-- Step 5: Enhanced Schedule Creation -->
        <div v-if="currentStep === 4" class="step-content">
          <Step5ScheduleCreation
            :medications="workflowState.extractedMedications"
            :scheduleConfig="scheduleConfig"
            :bulkScheduleOptions="bulkScheduleOptions"
            :conflictResolution="conflictResolution"
            @schedules-created="handleSchedulesCreated"
            @bulk-schedule-applied="handleBulkScheduleApplied"
          />
        </div>

        <!-- Step 6: Enhanced Stock Management -->
        <div v-if="currentStep === 5" class="step-content">
          <Step6StockManagement
            :medications="workflowState.extractedMedications"
            :stockLevels="stockLevels"
            :stockThresholds="stockThresholds"
            :stockAnalytics="stockAnalytics"
            @stock-configured="handleStockConfigured"
            @thresholds-updated="handleThresholdsUpdated"
          />
        </div>

        <!-- Step 7: Enhanced Confirmation -->
        <div v-if="currentStep === 6" class="step-content">
          <Step7Confirmation
            :workflowData="workflowState"
            :summary="workflowSummary"
            :prescriptionMetadata="workflowState.prescriptionMetadata"
            :imageMetadata="workflowState.imageMetadata"
            @workflow-complete="handleWorkflowComplete"
            @metadata-updated="handleMetadataUpdated"
          />
        </div>

        <!-- Enhanced Navigation -->
        <div class="flex justify-between mt-8 pt-6 border-t border-base-300">
          <div class="flex gap-2">
            <button
              @click="previousStep"
              class="btn btn-ghost"
              :disabled="currentStep === 0 || workflowState.isProcessing"
            >
              <i class="fas fa-arrow-left mr-2"></i>
              {{ $t('workflow.previous', 'Previous') }}
            </button>
            
            <button
              @click="resetWorkflow"
              class="btn btn-ghost btn-sm"
              :disabled="workflowState.isProcessing"
            >
              <i class="fas fa-redo mr-2"></i>
              {{ $t('workflow.reset', 'Reset') }}
            </button>
          </div>
          
          <div class="flex gap-2">
            <button
              v-if="currentStep < 6"
              @click="saveProgress"
              class="btn btn-outline"
              :disabled="workflowState.isProcessing"
            >
              <i class="fas fa-save mr-2"></i>
              {{ $t('workflow.saveProgress', 'Save Progress') }}
            </button>
            
            <button
              @click="nextStep"
              class="btn btn-primary"
              :disabled="!canProceedToNextStep || workflowState.isProcessing"
            >
              <span v-if="workflowState.isProcessing" class="loading loading-spinner loading-sm mr-2"></span>
              {{ currentStep === 6 ? $t('workflow.complete', 'Complete') : $t('workflow.next', 'Next') }}
              <i class="fas fa-arrow-right ml-2"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Enhanced Error Modal -->
    <ErrorModal
      v-model:show="errorModal.show"
      :error="errorModal.error"
      :step="errorModal.step"
      :rollbackData="errorModal.rollbackData"
      @retry="handleErrorRetry"
      @skip="handleErrorSkip"
      @rollback="handleErrorRollback"
    />

    <!-- Enhanced Success Modal -->
    <SuccessModal
      v-model:show="successModal.show"
      :summary="workflowSummary"
      :prescriptionData="workflowState"
      @view-medications="handleViewMedications"
      @start-new="handleStartNew"
      @download-summary="handleDownloadSummary"
    />

    <!-- Workflow Recovery Modal -->
    <div v-if="showRecoveryModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">
          <i class="fas fa-undo text-warning mr-2"></i>
          {{ $t('workflow.recovery.title', 'Recover Previous Session') }}
        </h3>
        <p class="mb-4">{{ $t('workflow.recovery.message', 'We found a previous prescription workflow session. Would you like to continue where you left off?') }}</p>
        <div class="modal-action">
          <button @click="loadProgress" class="btn btn-primary">
            {{ $t('workflow.recovery.continue', 'Continue Session') }}
          </button>
          <button @click="startNewWorkflow" class="btn btn-ghost">
            {{ $t('workflow.recovery.startNew', 'Start New') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useOCR } from '@/composables/useOCR'
import { medicationApi } from '@/services/medicationApi'
import type { 
  Medication, 
  ParsedPrescription, 
  PrescriptionMedication,
  MedicationValidation,
  MedicationInteraction,
  BatchMedicationResponse,
  StockAnalytics,
  MedicationImage
} from '@/types/medication'
import type { OCRResult, ExtractedMedication } from '@/services/ocrService'

// Import step components
import Step1ImageCapture from './workflow/Step1ImageCapture.vue'
import Step2OCRProcessing from './workflow/Step2OCRProcessing.vue'
import Step3MedicationReview from './workflow/Step3MedicationReview.vue'
import Step4DrugInteractions from './workflow/Step4DrugInteractions.vue'
import Step5ScheduleCreation from './workflow/Step5ScheduleCreation.vue'
import Step6StockManagement from './workflow/Step6StockManagement.vue'
import Step7Confirmation from './workflow/Step7Confirmation.vue'
import ErrorModal from './workflow/ErrorModal.vue'
import SuccessModal from './workflow/SuccessModal.vue'

const { t } = useI18n()
const { state: ocrState, processImage, clearResult } = useOCR()

// Enhanced workflow steps configuration
const workflowSteps = [
  {
    title: t('workflow.steps.capture', 'Capture'),
    description: t('workflow.steps.captureDesc', 'Upload prescription image'),
    icon: 'fas fa-camera'
  },
  {
    title: t('workflow.steps.ocr', 'OCR'),
    description: t('workflow.steps.ocrDesc', 'Process with OCR'),
    icon: 'fas fa-search'
  },
  {
    title: t('workflow.steps.review', 'Review'),
    description: t('workflow.steps.reviewDesc', 'Review medications'),
    icon: 'fas fa-pills'
  },
  {
    title: t('workflow.steps.validate', 'Validate'),
    description: t('workflow.steps.validateDesc', 'Check interactions'),
    icon: 'fas fa-check-circle'
  },
  {
    title: t('workflow.steps.schedule', 'Schedule'),
    description: t('workflow.steps.scheduleDesc', 'Create schedules'),
    icon: 'fas fa-calendar-alt'
  },
  {
    title: t('workflow.steps.stock', 'Stock'),
    description: t('workflow.steps.stockDesc', 'Set stock levels'),
    icon: 'fas fa-boxes'
  },
  {
    title: t('workflow.steps.save', 'Save'),
    description: t('workflow.steps.saveDesc', 'Confirm and save'),
    icon: 'fas fa-save'
  }
]

// Enhanced main workflow state
const workflowState = reactive({
  currentStep: 0,
  status: 'in-progress' as 'in-progress' | 'completed' | 'error' | 'paused',
  isProcessing: false,
  prescriptionImage: null as string | null,
  extractedMedications: [] as PrescriptionMedication[],
  validatedMedications: [] as Medication[],
  createdSchedules: [] as any[],
  stockLevels: {} as Record<string, number>,
  totalMedications: 0,
  interactionsFound: 0,
  processingTime: 0,
  startTime: Date.now(),
  prescriptionMetadata: {
    patientName: '',
    prescribingDoctor: '',
    prescriptionDate: '',
    prescriptionNumber: '',
    pharmacy: '',
    notes: '',
    insurance: '',
    totalCost: 0
  },
  imageMetadata: {
    uploadedAt: '',
    fileSize: 0,
    mimeType: '',
    dimensions: { width: 0, height: 0 },
    processingTime: 0,
    quality: 0
  },
  workflowVersion: '2.0.0',
  sessionId: generateSessionId()
})

// Enhanced camera state
const cameraState = reactive({
  showCamera: false,
  stream: null as MediaStream | null,
  isInitialized: false,
  hasPermission: false
})

// Enhanced camera settings
const cameraSettings = reactive({
  contrast: 1.2,
  brightness: 0.1,
  saturation: 1.0,
  sharpness: 1.1,
  autoFocus: true,
  flashMode: 'off' as 'off' | 'on' | 'auto',
  resolution: 'hd' as 'sd' | 'hd' | 'fullhd'
})

// Enhanced OCR and processing state
const imagePreprocessing = reactive({
  contrast: 1.2,
  brightness: 0.1,
  sharpen: true,
  denoise: true,
  threshold: 128,
  deskew: true,
  enhance: true
})

// Enhanced OCR processing steps
const ocrProcessingSteps = reactive([
  { label: 'Image preprocessing', status: 'pending', duration: 0 },
  { label: 'Text extraction', status: 'pending', duration: 0 },
  { label: 'Medication parsing', status: 'pending', duration: 0 },
  { label: 'Validation', status: 'pending', duration: 0 }
])

// Enhanced validation and interaction state
const validationResults = ref<Record<string, MedicationValidation>>({})
const drugInteractions = ref<MedicationInteraction[]>([])
const drugDatabase = ref<Record<string, any>>({})
const interactionSeverity = ref<'low' | 'moderate' | 'high' | 'contraindicated'>('low')

// Enhanced schedule configuration
const scheduleConfig = reactive({
  distributeEvenly: true,
  respectTiming: true,
  avoidConflicts: true,
  defaultTimes: ['08:00', '12:00', '20:00'],
  timeZone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  reminderSettings: {
    enabled: true,
    advanceMinutes: 15,
    repeatMinutes: 30
  }
})

// Enhanced bulk schedule options
const bulkScheduleOptions = reactive({
  applyToAll: false,
  selectedMedications: [] as string[],
  scheduleTemplate: 'standard' as 'standard' | 'morning' | 'evening' | 'custom',
  customTimes: [] as string[]
})

// Enhanced conflict resolution
const conflictResolution = reactive({
  autoResolve: true,
  resolutionStrategy: 'distribute' as 'distribute' | 'prioritize' | 'manual',
  priorityMedications: [] as string[]
})

// Enhanced stock management
const stockLevels = reactive<Record<string, number>>({})
const stockThresholds = reactive<Record<string, { min: number; warning: number; critical: number }>>({})
const stockAnalytics = reactive<Record<string, StockAnalytics>>({})

// Enhanced auto-save functionality
const autoSaveStatus = reactive({
  isSaving: false,
  lastSaved: null as Date | null,
  autoSaveInterval: null as number | null,
  saveAttempts: 0,
  lastError: null as Error | null
})

// Enhanced error handling
const stepErrors = ref<Record<number, string>>({})
const stepCompleted = ref<Record<number, boolean>>({})
const stepStats = ref<Record<number, string>>({})
const errorModal = reactive({
  show: false,
  error: null as Error | null,
  step: 0,
  rollbackData: null as any
})

// Enhanced success modal
const successModal = reactive({
  show: false
})

// Recovery modal
const showRecoveryModal = ref(false)

// Computed properties
const currentStep = computed(() => workflowState.currentStep)

const canProceedToNextStep = computed(() => {
  switch (currentStep.value) {
    case 0: return !!workflowState.prescriptionImage
    case 1: return ocrState.value.result && ocrState.value.result.success
    case 2: return workflowState.extractedMedications.length > 0
    case 3: return drugInteractions.value.length >= 0 // Always allow proceeding
    case 4: return workflowState.createdSchedules.length > 0
    case 5: return Object.keys(stockLevels.value).length > 0
    case 6: return true
    default: return false
  }
})

const workflowSummary = computed(() => ({
  totalMedications: workflowState.extractedMedications.length,
  totalSchedules: workflowState.createdSchedules.length,
  interactionsFound: drugInteractions.value.length,
  lowStockItems: Object.values(stockLevels.value).filter(level => level < 10).length,
  processingTime: workflowState.processingTime,
  confidence: ocrState.value.result?.confidence || 0,
  imageQuality: workflowState.imageMetadata.quality,
  sessionDuration: Date.now() - workflowState.startTime
}))

// Utility functions
function generateSessionId(): string {
  return `workflow_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString()
}

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  
  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  } else if (minutes > 0) {
    return `${minutes}m ${seconds % 60}s`
  } else {
    return `${seconds}s`
  }
}

// Enhanced event handlers
const handleImageCaptured = async (imageData: string) => {
  try {
    workflowState.isProcessing = true
    workflowState.prescriptionImage = imageData
    workflowState.imageMetadata.uploadedAt = new Date().toISOString()
    
    // Process image for quality assessment
    await assessImageQuality(imageData)
    
    saveProgress()
    stepCompleted.value[0] = true
    stepStats.value[0] = 'Image captured'
    
  } catch (error) {
    console.error('Image capture failed:', error)
    showError(error as Error, 0)
  } finally {
    workflowState.isProcessing = false
  }
}

const handleImageUploaded = async (file: File) => {
  try {
    workflowState.isProcessing = true
    
    const reader = new FileReader()
    reader.onload = async (e) => {
      const imageData = e.target?.result as string
      workflowState.prescriptionImage = imageData
      workflowState.imageMetadata = {
        uploadedAt: new Date().toISOString(),
        fileSize: file.size,
        mimeType: file.type,
        dimensions: { width: 0, height: 0 },
        processingTime: 0,
        quality: 0
      }
      
      // Assess image quality
      await assessImageQuality(imageData)
      
      saveProgress()
      stepCompleted.value[0] = true
      stepStats.value[0] = `${file.name} uploaded`
    }
    reader.readAsDataURL(file)
    
  } catch (error) {
    console.error('Image upload failed:', error)
    showError(error as Error, 0)
  } finally {
    workflowState.isProcessing = false
  }
}

const handleCameraSettingsChanged = (settings: any) => {
  Object.assign(cameraSettings, settings)
  saveProgress()
}

const handlePreprocessingChanged = (options: any) => {
  Object.assign(imagePreprocessing, options)
  saveProgress()
}

const handleOCRComplete = async (result: OCRResult) => {
  if (result.success) {
    workflowState.extractedMedications = result.medications.map(med => ({
      name: med.name,
      genericName: med.genericName,
      strength: med.strength || '',
      dosage: med.dosage,
      frequency: med.frequency,
      quantity: 30, // Default quantity
      refills: 0,
      instructions: med.instructions,
      drugDatabaseId: undefined,
      interactions: [],
      sideEffects: [],
      contraindications: []
    }))
    
    workflowState.totalMedications = result.medications.length
    
    // Extract prescription metadata
    if (result.prescriptionNumber) {
      workflowState.prescriptionMetadata.prescriptionNumber = result.prescriptionNumber
    }
    if (result.doctorName) {
      workflowState.prescriptionMetadata.prescribingDoctor = result.doctorName
    }
    
    stepCompleted.value[1] = true
    stepStats.value[1] = `${result.medications.length} medications found`
    
    saveProgress()
  }
}

const handleRetryOCR = async () => {
  if (workflowState.prescriptionImage) {
    clearResult()
    await processImage(workflowState.prescriptionImage, imagePreprocessing)
  }
}

const handleMedicationsUpdated = (medications: PrescriptionMedication[]) => {
  workflowState.extractedMedications = medications
  workflowState.totalMedications = medications.length
  saveProgress()
}

const handleBulkEdit = (updates: Record<string, any>) => {
  // Apply bulk updates to medications
  workflowState.extractedMedications = workflowState.extractedMedications.map(med => ({
    ...med,
    ...updates[med.name]
  }))
  saveProgress()
}

const handleValidationComplete = async (validations: Record<string, MedicationValidation>) => {
  validationResults.value = validations
  stepCompleted.value[2] = true
  stepStats.value[2] = `${Object.keys(validations).length} validated`
  saveProgress()
}

const handleInteractionsChecked = (interactions: MedicationInteraction[]) => {
  drugInteractions.value = interactions
  workflowState.interactionsFound = interactions.length
  stepCompleted.value[3] = true
  stepStats.value[3] = `${interactions.length} interactions found`
  saveProgress()
}

const handleSeverityUpdated = (severity: 'low' | 'moderate' | 'high' | 'contraindicated') => {
  interactionSeverity.value = severity
  saveProgress()
}

const handleSchedulesCreated = (schedules: any[]) => {
  workflowState.createdSchedules = schedules
  stepCompleted.value[4] = true
  stepStats.value[4] = `${schedules.length} schedules created`
  saveProgress()
}

const handleBulkScheduleApplied = (template: string, medications: string[]) => {
  // Apply bulk schedule template
  console.log('Bulk schedule applied:', template, medications)
  saveProgress()
}

const handleStockConfigured = (levels: Record<string, number>) => {
  Object.assign(stockLevels, levels)
  workflowState.stockLevels = { ...stockLevels }
  stepCompleted.value[5] = true
  stepStats.value[5] = `${Object.keys(levels).length} stock levels set`
  saveProgress()
}

const handleThresholdsUpdated = (thresholds: Record<string, any>) => {
  Object.assign(stockThresholds, thresholds)
  saveProgress()
}

const handleMetadataUpdated = (metadata: any) => {
  Object.assign(workflowState.prescriptionMetadata, metadata)
  saveProgress()
}

const handleWorkflowComplete = async () => {
  try {
    workflowState.isProcessing = true
    
    // Create medications from prescription
    const prescription: ParsedPrescription = {
      id: workflowState.prescriptionMetadata.prescriptionNumber || `prescription_${Date.now()}`,
      patientName: workflowState.prescriptionMetadata.patientName,
      prescribingDoctor: workflowState.prescriptionMetadata.prescribingDoctor,
      prescriptionDate: workflowState.prescriptionMetadata.prescriptionDate,
      medications: workflowState.extractedMedications,
      pharmacy: workflowState.prescriptionMetadata.pharmacy,
      notes: workflowState.prescriptionMetadata.notes,
      imageUrl: workflowState.prescriptionImage || undefined,
      status: 'active'
    }
    
    const createdMedications = await medicationApi.createMedicationsFromPrescription(prescription)
    
    // Store prescription image with enhanced metadata
    if (workflowState.prescriptionImage) {
      await storePrescriptionImage(workflowState.prescriptionImage, createdMedications)
    }
    
    // Create schedules
    await createMedicationSchedules(createdMedications)
    
    // Set stock levels
    await updateStockLevels(createdMedications)
    
    workflowState.status = 'completed'
    workflowState.processingTime = Date.now() - workflowState.startTime
    stepCompleted.value[6] = true
    stepStats.value[6] = 'Workflow completed'
    
    successModal.show = true
    
  } catch (error) {
    console.error('Workflow completion failed:', error)
    showError(error as Error, currentStep.value)
  } finally {
    workflowState.isProcessing = false
  }
}

// Enhanced step processing
const nextStep = async () => {
  if (currentStep.value < 6 && canProceedToNextStep.value) {
    try {
      workflowState.isProcessing = true
      
      // Process step-specific logic
      await processCurrentStep()
      
      // Move to next step
      workflowState.currentStep++
      saveProgress()
      
    } catch (error) {
      console.error('Step processing failed:', error)
      showError(error as Error, currentStep.value)
    } finally {
      workflowState.isProcessing = false
    }
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    workflowState.currentStep--
    saveProgress()
  }
}

const goToStep = (step: number) => {
  if (step >= 0 && step <= 6) {
    workflowState.currentStep = step
    saveProgress()
  }
}

const processCurrentStep = async () => {
  switch (currentStep.value) {
    case 1: // OCR Processing
      if (workflowState.prescriptionImage && !ocrState.value.result) {
        await processImage(workflowState.prescriptionImage, imagePreprocessing)
      }
      break
      
    case 2: // Medication Review
      // Validate each medication
      for (const medication of workflowState.extractedMedications) {
        const validation = await medicationApi.validateMedication({
          name: medication.name,
          strength: medication.strength,
          dosage: medication.dosage,
          frequency: medication.frequency,
          instructions: medication.instructions,
          stock: medication.quantity,
          minStock: Math.ceil(medication.quantity * 0.2),
          category: 'Prescription',
          time: '08:00'
        })
        validationResults.value[medication.name] = validation
      }
      break
      
    case 3: // Drug Interactions
      const medicationNames = workflowState.extractedMedications.map(med => med.name)
      drugInteractions.value = await medicationApi.checkMedicationInteractions(medicationNames)
      break
      
    case 4: // Schedule Creation
      // This will be handled by the Step5ScheduleCreation component
      break
      
    case 5: // Stock Management
      // This will be handled by the Step6StockManagement component
      break
  }
}

// Enhanced progress persistence
const saveProgress = async () => {
  try {
    autoSaveStatus.isSaving = true
    
    const progressData = {
      workflowState,
      currentStep: currentStep.value,
      timestamp: new Date().toISOString(),
      version: workflowState.workflowVersion,
      sessionId: workflowState.sessionId
    }
    
    localStorage.setItem('prescription-workflow-progress', JSON.stringify(progressData))
    autoSaveStatus.lastSaved = new Date()
    autoSaveStatus.saveAttempts++
    
  } catch (error) {
    console.error('Failed to save progress:', error)
    autoSaveStatus.lastError = error as Error
  } finally {
    autoSaveStatus.isSaving = false
  }
}

const loadProgress = () => {
  try {
    const saved = localStorage.getItem('prescription-workflow-progress')
    if (saved) {
      const progressData = JSON.parse(saved)
      const savedDate = new Date(progressData.timestamp)
      const hoursSinceSave = (Date.now() - savedDate.getTime()) / (1000 * 60 * 60)
      
      // Only load if saved within last 24 hours and version matches
      if (hoursSinceSave < 24 && progressData.version === workflowState.workflowVersion) {
        Object.assign(workflowState, progressData.workflowState)
        workflowState.currentStep = progressData.currentStep
        showRecoveryModal.value = false
        return true
      }
    }
  } catch (error) {
    console.error('Failed to load progress:', error)
  }
  return false
}

const clearProgress = () => {
  localStorage.removeItem('prescription-workflow-progress')
}

const startNewWorkflow = () => {
  showRecoveryModal.value = false
  resetWorkflow()
}

// Enhanced error handling
const showError = (error: Error, step: number) => {
  errorModal.error = error
  errorModal.step = step
  errorModal.rollbackData = getRollbackData(step)
  errorModal.show = true
  stepErrors.value[step] = error.message
}

const getRollbackData = (step: number) => {
  // Return data needed to rollback to previous step
  switch (step) {
    case 1: return { prescriptionImage: workflowState.prescriptionImage }
    case 2: return { extractedMedications: workflowState.extractedMedications }
    case 3: return { validationResults: validationResults.value }
    case 4: return { drugInteractions: drugInteractions.value }
    case 5: return { createdSchedules: workflowState.createdSchedules }
    case 6: return { stockLevels: workflowState.stockLevels }
    default: return null
  }
}

const handleErrorRetry = () => {
  errorModal.show = false
  // Retry current step
  processCurrentStep()
}

const handleErrorSkip = () => {
  errorModal.show = false
  // Skip to next step
  nextStep()
}

const handleErrorRollback = () => {
  errorModal.show = false
  // Rollback to previous step
  if (currentStep.value > 0) {
    workflowState.currentStep--
    // Restore rollback data if available
    if (errorModal.rollbackData) {
      Object.assign(workflowState, errorModal.rollbackData)
    }
  }
}

// Enhanced success handlers
const handleViewMedications = () => {
  // Navigate to medications list
  window.location.href = '/medications'
}

const handleStartNew = () => {
  // Reset workflow and start over
  resetWorkflow()
}

const handleDownloadSummary = () => {
  // Generate and download workflow summary
  const summary = {
    ...workflowSummary.value,
    prescription: workflowState.prescriptionMetadata,
    medications: workflowState.extractedMedications,
    schedules: workflowState.createdSchedules,
    interactions: drugInteractions.value,
    stockLevels: workflowState.stockLevels
  }
  
  const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `prescription-summary-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// Enhanced utility functions
const assessImageQuality = async (imageData: string): Promise<void> => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      workflowState.imageMetadata.dimensions = { width: img.width, height: img.height }
      
      // Calculate quality score based on resolution and aspect ratio
      const resolution = img.width * img.height
      const aspectRatio = img.width / img.height
      const quality = Math.min(100, (resolution / 1000000) * 50 + (aspectRatio > 0.5 && aspectRatio < 2 ? 50 : 0))
      
      workflowState.imageMetadata.quality = quality
      resolve()
    }
    img.src = imageData
  })
}

const storePrescriptionImage = async (imageData: string, medications: Medication[]): Promise<void> => {
  try {
    // Convert base64 to file for upload
    const response = await fetch(imageData)
    const blob = await response.blob()
    const file = new File([blob], 'prescription.jpg', { type: 'image/jpeg' })
    
    // Upload image for each medication
    for (const medication of medications) {
      await medicationApi.uploadMedicationImage(medication.id, file, 'Prescription image')
    }
  } catch (error) {
    console.error('Failed to store prescription image:', error)
  }
}

const createMedicationSchedules = async (medications: Medication[]): Promise<void> => {
  try {
    // Create schedules for each medication
    for (const schedule of workflowState.createdSchedules) {
      await medicationApi.createMedicationSchedules(schedule.medicationId, schedule)
    }
  } catch (error) {
    console.error('Failed to create medication schedules:', error)
  }
}

const updateStockLevels = async (medications: Medication[]): Promise<void> => {
  try {
    // Update stock levels for each medication
    for (const medication of medications) {
      const stockLevel = stockLevels[medication.name] || 0
      await medicationApi.updateStock(medication.id, stockLevel)
    }
  } catch (error) {
    console.error('Failed to update stock levels:', error)
  }
}

const resetWorkflow = () => {
  // Reset all state
  Object.assign(workflowState, {
    currentStep: 0,
    status: 'in-progress',
    isProcessing: false,
    prescriptionImage: null,
    extractedMedications: [],
    validatedMedications: [],
    createdSchedules: [],
    stockLevels: {},
    totalMedications: 0,
    interactionsFound: 0,
    processingTime: 0,
    startTime: Date.now(),
    prescriptionMetadata: {
      patientName: '',
      prescribingDoctor: '',
      prescriptionDate: '',
      prescriptionNumber: '',
      pharmacy: '',
      notes: '',
      insurance: '',
      totalCost: 0
    },
    imageMetadata: {
      uploadedAt: '',
      fileSize: 0,
      mimeType: '',
      dimensions: { width: 0, height: 0 },
      processingTime: 0,
      quality: 0
    },
    sessionId: generateSessionId()
  })
  
  // Clear other state
  validationResults.value = {}
  drugInteractions.value = []
  stepErrors.value = {}
  stepCompleted.value = {}
  stepStats.value = {}
  clearResult()
  clearProgress()
}

// Enhanced auto-save setup
const setupAutoSave = () => {
  autoSaveStatus.autoSaveInterval = window.setInterval(() => {
    if (workflowState.prescriptionImage && !workflowState.isProcessing) {
      saveProgress()
    }
  }, 30000) // Auto-save every 30 seconds
}

// Lifecycle
onMounted(() => {
  // Check for existing progress
  if (loadProgress()) {
    showRecoveryModal.value = true
  } else {
    // Initialize new workflow
    workflowState.prescriptionMetadata.prescriptionDate = new Date().toISOString().split('T')[0]
  }
  
  // Setup auto-save
  setupAutoSave()
})

onUnmounted(() => {
  // Cleanup
  if (autoSaveStatus.autoSaveInterval) {
    clearInterval(autoSaveStatus.autoSaveInterval)
  }
  
  if (cameraState.stream) {
    cameraState.stream.getTracks().forEach(track => track.stop())
  }
})

// Watch for workflow completion
watch(() => workflowState.status, (newStatus) => {
  if (newStatus === 'completed') {
    clearProgress()
  }
})

// Watch for step completion
watch(() => currentStep.value, (newStep) => {
  workflowState.processingTime = Date.now() - workflowState.startTime
})
</script>

<style scoped>
.step-content {
  @apply space-y-6;
}

.step {
  @apply transition-all duration-200;
}

.step:hover {
  @apply transform scale-105;
}

.step-error {
  @apply text-error;
}

.step-success {
  @apply text-success;
}

.step-stats {
  @apply mt-1;
}

.modal {
  @apply z-50;
}
</style> 