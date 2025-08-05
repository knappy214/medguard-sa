<template>
  <div class="ocr-prescription-processor">
    <!-- Header -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-2xl font-bold mb-4">
          <i class="fas fa-camera text-primary mr-2"></i>
          {{ $t('ocr.title', 'Prescription OCR Processor') }}
        </h2>
        
        <p class="text-base-content/70 mb-6">
          {{ $t('ocr.description', 'Upload a prescription image to automatically extract medication information using OCR technology.') }}
        </p>
      </div>
    </div>

    <!-- File Upload Section -->
    <div class="card bg-base-100 shadow-xl mt-6">
      <div class="card-body">
        <h3 class="text-lg font-semibold mb-4">
          {{ $t('ocr.upload.title', 'Upload Prescription') }}
        </h3>

        <!-- File Upload Area -->
        <div
          class="upload-area"
          :class="{
            'upload-area--dragover': isDragOver,
            'upload-area--processing': state.isProcessing
          }"
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragleave="handleDragLeave"
          @click="triggerFileInput"
        >
          <input
            ref="fileInput"
            type="file"
            accept="image/*"
            multiple
            class="hidden"
            @change="handleFileSelect"
          />
          
          <div class="upload-content">
            <i class="fas fa-cloud-upload-alt text-4xl text-primary mb-4"></i>
            <p class="text-lg font-medium mb-2">
              {{ $t('ocr.upload.dragDrop', 'Drag & drop prescription images here') }}
            </p>
            <p class="text-base-content/70 mb-4">
              {{ $t('ocr.upload.orClick', 'or click to browse files') }}
            </p>
            <p class="text-sm text-base-content/60">
              {{ $t('ocr.upload.supported', 'Supported formats: JPG, PNG, PDF (max 10MB each)') }}
            </p>
          </div>
        </div>

        <!-- Selected Files -->
        <div v-if="selectedFiles.length > 0" class="mt-4">
          <h4 class="font-medium mb-2">
            {{ $t('ocr.upload.selected', 'Selected Files') }} ({{ selectedFiles.length }})
          </h4>
          <div class="space-y-2">
            <div
              v-for="(file, index) in selectedFiles"
              :key="index"
              class="flex items-center justify-between p-3 bg-base-200 rounded-lg"
            >
              <div class="flex items-center space-x-3">
                <i class="fas fa-file-image text-primary"></i>
                <div>
                  <p class="font-medium">{{ file.name }}</p>
                  <p class="text-sm text-base-content/70">
                    {{ formatFileSize(file.size) }}
                  </p>
                </div>
              </div>
              <button
                @click="removeFile(index)"
                class="btn btn-sm btn-ghost text-error"
                :disabled="state.isProcessing"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Processing Controls -->
    <div v-if="selectedFiles.length > 0" class="card bg-base-100 shadow-xl mt-6">
      <div class="card-body">
        <h3 class="text-lg font-semibold mb-4">
          {{ $t('ocr.processing.title', 'Processing Options') }}
        </h3>

        <!-- Preprocessing Options -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('ocr.processing.contrast', 'Contrast') }}</span>
            </label>
            <input
              v-model.number="preprocessingOptions.contrast"
              type="range"
              min="0.5"
              max="2"
              step="0.1"
              class="range range-primary"
            />
            <div class="flex justify-between text-xs text-base-content/60">
              <span>0.5</span>
              <span>{{ preprocessingOptions.contrast }}</span>
              <span>2.0</span>
            </div>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('ocr.processing.brightness', 'Brightness') }}</span>
            </label>
            <input
              v-model.number="preprocessingOptions.brightness"
              type="range"
              min="-1"
              max="1"
              step="0.1"
              class="range range-primary"
            />
            <div class="flex justify-between text-xs text-base-content/60">
              <span>-1</span>
              <span>{{ preprocessingOptions.brightness }}</span>
              <span>1</span>
            </div>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('ocr.processing.threshold', 'Threshold') }}</span>
            </label>
            <input
              v-model.number="preprocessingOptions.threshold"
              type="range"
              min="0"
              max="255"
              step="1"
              class="range range-primary"
            />
            <div class="flex justify-between text-xs text-base-content/60">
              <span>0</span>
              <span>{{ preprocessingOptions.threshold }}</span>
              <span>255</span>
            </div>
          </div>
        </div>

        <!-- Processing Buttons -->
        <div class="flex flex-wrap gap-4">
          <button
            @click="processSelectedFiles"
            class="btn btn-primary"
            :disabled="state.isProcessing || selectedFiles.length === 0"
          >
            <i v-if="state.isProcessing" class="fas fa-spinner fa-spin mr-2"></i>
            <i v-else class="fas fa-play mr-2"></i>
            {{ $t('ocr.processing.start', 'Start Processing') }}
          </button>

          <button
            @click="clearAll"
            class="btn btn-outline"
            :disabled="state.isProcessing"
          >
            <i class="fas fa-times mr-2"></i>
            {{ $t('ocr.processing.clear', 'Clear All') }}
          </button>

          <button
            @click="resetOptions"
            class="btn btn-ghost"
            :disabled="state.isProcessing"
          >
            <i class="fas fa-undo mr-2"></i>
            {{ $t('ocr.processing.reset', 'Reset Options') }}
          </button>
        </div>

        <!-- Progress Bar -->
        <div v-if="state.isProcessing" class="mt-6">
          <div class="flex justify-between mb-2">
            <span class="text-sm font-medium">
              {{ $t('ocr.processing.progress', 'Processing...') }}
            </span>
            <span class="text-sm text-base-content/70">
              {{ Math.round(state.progress) }}%
            </span>
          </div>
          <progress
            class="progress progress-primary w-full"
            :value="state.progress"
            max="100"
          ></progress>
        </div>
      </div>
    </div>

    <!-- Results Section -->
    <div v-if="state.hasResult" class="card bg-base-100 shadow-xl mt-6">
      <div class="card-body">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold">
            {{ $t('ocr.results.title', 'Processing Results') }}
          </h3>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-base-content/70">
              {{ $t('ocr.results.confidence', 'Confidence') }}:
            </span>
            <div class="badge" :class="`badge-${confidenceColor}`">
              {{ Math.round(state.result!.confidence * 100) }}%
            </div>
          </div>
        </div>

        <!-- Validation Warnings -->
        <div v-if="state.validation && state.validation.suggestions.length > 0" class="alert alert-warning mb-6">
          <i class="fas fa-exclamation-triangle"></i>
          <div>
            <h4 class="font-medium">
              {{ $t('ocr.results.warnings', 'Processing Warnings') }}
            </h4>
            <ul class="mt-2 space-y-1">
              <li v-for="suggestion in state.validation.suggestions" :key="suggestion" class="text-sm">
                • {{ suggestion }}
              </li>
            </ul>
          </div>
        </div>

        <!-- Extracted Information -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Prescription Details -->
          <div class="space-y-4">
            <h4 class="font-semibold text-lg">
              {{ $t('ocr.results.prescription', 'Prescription Details') }}
            </h4>
            
            <div v-if="state.result!.prescriptionNumber" class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ $t('ocr.results.prescriptionNumber', 'Prescription Number') }}</div>
              <div class="stat-value text-lg">{{ state.result!.prescriptionNumber }}</div>
            </div>

            <div v-if="state.result!.doctorName" class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ $t('ocr.results.doctor', 'Prescribing Doctor') }}</div>
              <div class="stat-value text-lg">{{ state.result!.doctorName }}</div>
            </div>

            <div v-if="state.result!.icd10Codes.length > 0" class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ $t('ocr.results.icd10', 'ICD-10 Codes') }}</div>
              <div class="stat-value text-lg">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="code in state.result!.icd10Codes"
                    :key="code"
                    class="badge badge-outline"
                  >
                    {{ code }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Processing Stats -->
          <div class="space-y-4">
            <h4 class="font-semibold text-lg">
              {{ $t('ocr.results.stats', 'Processing Statistics') }}
            </h4>
            
            <div class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ $t('ocr.results.medications', 'Medications Found') }}</div>
              <div class="stat-value text-lg">{{ state.result!.medications.length }}</div>
            </div>

            <div class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ $t('ocr.results.processingTime', 'Processing Time') }}</div>
              <div class="stat-value text-lg">{{ state.result!.processingTime }}ms</div>
            </div>

            <div class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ $t('ocr.results.avgConfidence', 'Average Confidence') }}</div>
              <div class="stat-value text-lg">
                {{ state.result!.medications.length > 0 
                  ? Math.round(state.result!.medications.reduce((sum, med) => sum + med.confidence, 0) / state.result!.medications.length * 100)
                  : 0 }}%
              </div>
            </div>
          </div>
        </div>

        <!-- Extracted Medications -->
        <div v-if="state.result!.medications.length > 0" class="mt-8">
          <h4 class="font-semibold text-lg mb-4">
            {{ $t('ocr.results.medications', 'Extracted Medications') }}
          </h4>
          
          <div class="space-y-4">
            <div
              v-for="(medication, index) in state.result!.medications"
              :key="index"
              class="card bg-base-200 shadow-sm"
            >
              <div class="card-body">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center space-x-2 mb-2">
                      <h5 class="font-semibold text-lg">{{ medication.name }}</h5>
                      <div class="badge" :class="`badge-${getMedicationConfidenceColor(medication.confidence)}`">
                        {{ Math.round(medication.confidence * 100) }}%
                      </div>
                    </div>
                    
                    <div v-if="medication.genericName" class="text-sm text-base-content/70 mb-2">
                      <i class="fas fa-tag mr-1"></i>
                      {{ $t('ocr.results.generic', 'Generic') }}: {{ medication.genericName }}
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div v-if="medication.strength">
                        <span class="font-medium">{{ $t('ocr.results.strength', 'Strength') }}:</span>
                        {{ medication.strength }}
                      </div>
                      <div v-if="medication.dosage">
                        <span class="font-medium">{{ $t('ocr.results.dosage', 'Dosage') }}:</span>
                        {{ medication.dosage }}
                      </div>
                      <div v-if="medication.frequency">
                        <span class="font-medium">{{ $t('ocr.results.frequency', 'Frequency') }}:</span>
                        {{ medication.frequency }}
                      </div>
                      <div v-if="medication.manufacturer">
                        <span class="font-medium">{{ $t('ocr.results.manufacturer', 'Manufacturer') }}:</span>
                        {{ medication.manufacturer }}
                      </div>
                    </div>
                    
                    <div v-if="medication.instructions" class="mt-2 text-sm">
                      <span class="font-medium">{{ $t('ocr.results.instructions', 'Instructions') }}:</span>
                      {{ medication.instructions }}
                    </div>
                  </div>
                  
                  <div class="flex flex-col space-y-2 ml-4">
                    <button
                      @click="editMedication(index)"
                      class="btn btn-sm btn-outline"
                    >
                      <i class="fas fa-edit"></i>
                    </button>
                    <button
                      @click="removeMedication(index)"
                      class="btn btn-sm btn-outline btn-error"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex flex-wrap gap-4 mt-8">
          <button
            @click="addToMedications"
            class="btn btn-primary"
            :disabled="state.result!.medications.length === 0"
          >
            <i class="fas fa-plus mr-2"></i>
            {{ $t('ocr.results.addToMedications', 'Add to Medications') }}
          </button>

          <button
            @click="exportResults"
            class="btn btn-outline"
          >
            <i class="fas fa-download mr-2"></i>
            {{ $t('ocr.results.export', 'Export Results') }}
          </button>

          <button
            @click="retryProcessing"
            class="btn btn-ghost"
          >
            <i class="fas fa-redo mr-2"></i>
            {{ $t('ocr.results.retry', 'Retry with Different Options') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Error Display -->
    <div v-if="state.error" class="alert alert-error mt-6">
      <i class="fas fa-exclamation-circle"></i>
      <div>
        <h4 class="font-medium">{{ $t('ocr.error.title', 'Processing Error') }}</h4>
        <p>{{ state.error }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useOCR } from '../../composables/useOCR'
import type { PreprocessingOptions, ExtractedMedication } from '../../services/ocrService'
import type { BulkMedicationEntry } from '../../types/medication'

// Composables
const { t } = useI18n()
const {
  state,
  isReady,
  hasResult,
  confidenceLevel,
  confidenceColor,
  processImage,
  processMultipleImages,
  convertToBulkEntries,
  clearResult,
  initialize,
  terminate
} = useOCR()

// Component state
const fileInput = ref<HTMLInputElement>()
const selectedFiles = ref<File[]>([])
const isDragOver = ref(false)

// Preprocessing options
const preprocessingOptions = reactive<PreprocessingOptions>({
  contrast: 1.2,
  brightness: 0.1,
  sharpen: true,
  denoise: true,
  threshold: 128
})

// Methods
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    const files = Array.from(target.files)
    selectedFiles.value.push(...files.filter(file => file.type.startsWith('image/')))
  }
}

const handleDrop = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
  
  if (event.dataTransfer?.files) {
    const files = Array.from(event.dataTransfer.files)
    selectedFiles.value.push(...files.filter(file => file.type.startsWith('image/')))
  }
}

const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (event: DragEvent) => {
  event.preventDefault()
  isDragOver.value = false
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const processSelectedFiles = async () => {
  if (selectedFiles.value.length === 0) return
  
  try {
    await processMultipleImages(selectedFiles.value, preprocessingOptions)
  } catch (error) {
    console.error('Failed to process files:', error)
  }
}

const clearAll = () => {
  selectedFiles.value = []
  clearResult()
}

const resetOptions = () => {
  Object.assign(preprocessingOptions, {
    contrast: 1.2,
    brightness: 0.1,
    sharpen: true,
    denoise: true,
    threshold: 128
  })
}

const getMedicationConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  return 'error'
}

const editMedication = (index: number) => {
  // TODO: Implement medication editing modal
  console.log('Edit medication:', index)
}

const removeMedication = (index: number) => {
  if (state.value.result) {
    state.value.result.medications.splice(index, 1)
  }
}

const addToMedications = () => {
  if (!state.value.result) return
  
  const bulkEntries = convertToBulkEntries(state.value.result.medications)
  // TODO: Emit event to parent component or use store to add medications
  console.log('Adding medications:', bulkEntries)
}

const exportResults = () => {
  if (!state.value.result) return
  
  const dataStr = JSON.stringify(state.value.result, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `prescription-ocr-results-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  
  URL.revokeObjectURL(url)
}

const retryProcessing = async () => {
  if (selectedFiles.value.length === 0) return
  
  // Reset and retry with current options
  clearResult()
  await processSelectedFiles()
}

// Lifecycle
onMounted(async () => {
  await initialize()
})

onUnmounted(async () => {
  await terminate()
})
</script>

<style scoped>
.upload-area {
  @apply border-2 border-dashed border-base-300 rounded-lg p-8 text-center cursor-pointer transition-all duration-200;
}

.upload-area:hover {
  @apply border-primary bg-base-200;
}

.upload-area--dragover {
  @apply border-primary bg-primary/10;
}

.upload-area--processing {
  @apply opacity-50 cursor-not-allowed;
}

.upload-content {
  @apply pointer-events-none;
}
</style> 