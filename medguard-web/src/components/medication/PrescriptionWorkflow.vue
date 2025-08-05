<template>
  <div class="prescription-workflow">
    <!-- Header -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <h2 class="card-title text-2xl font-bold">
          <i class="fas fa-prescription text-primary mr-2"></i>
          {{ $t('workflow.title', 'Prescription Workflow') }}
        </h2>
        <p class="text-base-content/70">
          {{ $t('workflow.description', 'Process your prescription step by step with automated OCR and validation.') }}
        </p>
      </div>
    </div>

    <!-- Progress Indicator -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="steps steps-horizontal w-full">
          <div
            v-for="(step, index) in workflowSteps"
            :key="index"
            class="step"
            :class="{
              'step-primary': currentStep >= index,
              'step-neutral': currentStep < index
            }"
          >
            <div class="step-icon">
              <i :class="step.icon"></i>
            </div>
            <div class="step-content">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-description">{{ step.description }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Step Content -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <!-- Step 1: Image Capture -->
        <div v-if="currentStep === 0" class="step-content">
          <h3 class="text-xl font-semibold mb-4">
            <i class="fas fa-camera text-primary mr-2"></i>
            {{ $t('workflow.step1.title', 'Capture Prescription Image') }}
          </h3>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Camera Capture -->
            <div class="card bg-base-200">
              <div class="card-body">
                <h4 class="font-semibold mb-3">
                  {{ $t('workflow.step1.camera', 'Camera Capture') }}
                </h4>
                <div class="camera-container">
                  <video
                    v-if="showCamera"
                    ref="videoElement"
                    class="w-full h-64 object-cover rounded-lg"
                    autoplay
                    muted
                  ></video>
                  <div
                    v-else
                    class="w-full h-64 bg-base-300 rounded-lg flex items-center justify-center"
                  >
                    <i class="fas fa-camera text-4xl text-base-content/50"></i>
                  </div>
                </div>
                <div class="flex gap-2 mt-4">
                  <button
                    @click="toggleCamera"
                    class="btn btn-primary"
                    :disabled="state.isProcessing"
                  >
                    <i class="fas fa-camera mr-2"></i>
                    {{ showCamera ? $t('workflow.step1.stopCamera', 'Stop Camera') : $t('workflow.step1.startCamera', 'Start Camera') }}
                  </button>
                  <button
                    v-if="showCamera"
                    @click="captureImage"
                    class="btn btn-secondary"
                    :disabled="state.isProcessing"
                  >
                    <i class="fas fa-camera-retro mr-2"></i>
                    {{ $t('workflow.step1.capture', 'Capture') }}
                  </button>
                </div>
              </div>
            </div>

            <!-- File Upload -->
            <div class="card bg-base-200">
              <div class="card-body">
                <h4 class="font-semibold mb-3">
                  {{ $t('workflow.step1.upload', 'Upload Image') }}
                </h4>
                <div
                  class="upload-area"
                  :class="{ 'upload-area--dragover': isDragOver }"
                  @drop="handleDrop"
                  @dragover="handleDragOver"
                  @dragleave="handleDragLeave"
                  @click="triggerFileInput"
                >
                  <input
                    ref="fileInput"
                    type="file"
                    accept="image/*"
                    class="hidden"
                    @change="handleFileSelect"
                  />
                  <div class="upload-content text-center">
                    <i class="fas fa-cloud-upload-alt text-4xl text-primary mb-4"></i>
                    <p class="text-lg font-medium mb-2">
                      {{ $t('workflow.step1.dragDrop', 'Drag & drop prescription image') }}
                    </p>
                    <p class="text-base-content/70">
                      {{ $t('workflow.step1.orClick', 'or click to browse') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Preview -->
          <div v-if="prescriptionImage" class="mt-6">
            <h4 class="font-semibold mb-3">
              {{ $t('workflow.step1.preview', 'Image Preview') }}
            </h4>
            <div class="relative">
              <img
                :src="prescriptionImage"
                alt="Prescription preview"
                class="w-full max-w-md rounded-lg shadow-lg"
              />
              <button
                @click="removeImage"
                class="btn btn-circle btn-sm btn-error absolute top-2 right-2"
              >
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>

          <!-- Navigation -->
          <div class="flex justify-between mt-6">
            <button
              @click="previousStep"
              class="btn btn-ghost"
              :disabled="currentStep === 0"
            >
              <i class="fas fa-arrow-left mr-2"></i>
              {{ $t('workflow.previous', 'Previous') }}
            </button>
            <button
              @click="nextStep"
              class="btn btn-primary"
              :disabled="!prescriptionImage || state.isProcessing"
            >
              {{ $t('workflow.next', 'Next') }}
              <i class="fas fa-arrow-right ml-2"></i>
            </button>
          </div>
        </div>

        <!-- Step 2: OCR Processing -->
        <div v-if="currentStep === 1" class="step-content">
          <h3 class="text-xl font-semibold mb-4">
            <i class="fas fa-search text-primary mr-2"></i>
            {{ $t('workflow.step2.title', 'OCR Processing') }}
          </h3>

          <div class="text-center py-8">
            <div v-if="state.isProcessing" class="space-y-4">
              <div class="loading loading-spinner loading-lg text-primary"></div>
              <p class="text-lg font-medium">
                {{ $t('workflow.step2.processing', 'Processing prescription image...') }}
              </p>
              <div class="w-full bg-base-300 rounded-full h-2">
                <div
                  class="bg-primary h-2 rounded-full transition-all duration-300"
                  :style="{ width: `${ocrProgress}%` }"
                ></div>
              </div>
              <p class="text-sm text-base-content/70">
                {{ $t('workflow.step2.progress', { progress: Math.round(ocrProgress) }, 'Progress: {progress}%') }}
              </p>
            </div>

            <div v-else-if="ocrResult" class="space-y-4">
              <div class="alert alert-success">
                <i class="fas fa-check-circle"></i>
                <span>{{ $t('workflow.step2.success', 'OCR processing completed successfully!') }}</span>
              </div>
              <div class="text-left">
                <h4 class="font-semibold mb-2">
                  {{ $t('workflow.step2.extracted', 'Extracted Information') }}
                </h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div class="form-control">
                    <label class="label">
                      <span class="label-text">{{ $t('workflow.step2.patientName', 'Patient Name') }}</span>
                    </label>
                    <input
                      v-model="ocrResult.patientName"
                      type="text"
                      class="input input-bordered"
                    />
                  </div>
                  <div class="form-control">
                    <label class="label">
                      <span class="label-text">{{ $t('workflow.step2.doctor', 'Prescribing Doctor') }}</span>
                    </label>
                    <input
                      v-model="ocrResult.prescribingDoctor"
                      type="text"
                      class="input input-bordered"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="ocrError" class="alert alert-error">
              <i class="fas fa-exclamation-triangle"></i>
              <span>{{ ocrError }}</span>
            </div>
          </div>

          <!-- Navigation -->
          <div class="flex justify-between mt-6">
            <button
              @click="previousStep"
              class="btn btn-ghost"
            >
              <i class="fas fa-arrow-left mr-2"></i>
              {{ $t('workflow.previous', 'Previous') }}
            </button>
            <button
              @click="nextStep"
              class="btn btn-primary"
              :disabled="!ocrResult || state.isProcessing"
            >
              {{ $t('workflow.next', 'Next') }}
              <i class="fas fa-arrow-right ml-2"></i>
            </button>
          </div>
        </div>

        <!-- Additional steps will be added here -->
        <div v-if="currentStep > 1" class="step-content">
          <h3 class="text-xl font-semibold mb-4">
            Step {{ currentStep + 1 }} - Coming Soon
          </h3>
          <p>This step is under development.</p>
          
          <!-- Navigation -->
          <div class="flex justify-between mt-6">
            <button
              @click="previousStep"
              class="btn btn-ghost"
            >
              <i class="fas fa-arrow-left mr-2"></i>
              {{ $t('workflow.previous', 'Previous') }}
            </button>
            <button
              @click="nextStep"
              class="btn btn-primary"
              :disabled="currentStep >= 6"
            >
              {{ $t('workflow.next', 'Next') }}
              <i class="fas fa-arrow-right ml-2"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Workflow steps configuration
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
    description: t('workflow.steps.validateDesc', 'Validate medications'),
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

// Reactive state
const currentStep = ref(0)
const state = reactive({
  isProcessing: false
})

// Step 1: Image capture
const prescriptionImage = ref<string | null>(null)
const showCamera = ref(false)
const isDragOver = ref(false)
const videoElement = ref<HTMLVideoElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
let stream: MediaStream | null = null

// Step 2: OCR processing
const ocrResult = ref<any>(null)
const ocrProgress = ref(0)
const ocrError = ref<string | null>(null)

// Methods
const toggleCamera = async () => {
  if (showCamera.value) {
    stopCamera()
  } else {
    await startCamera()
  }
}

const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { facingMode: 'environment' } 
    })
    if (videoElement.value) {
      videoElement.value.srcObject = stream
    }
    showCamera.value = true
  } catch (error) {
    console.error('Error accessing camera:', error)
  }
}

const stopCamera = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  showCamera.value = false
}

const captureImage = () => {
  if (!videoElement.value) return
  
  const canvas = document.createElement('canvas')
  canvas.width = videoElement.value.videoWidth
  canvas.height = videoElement.value.videoHeight
  
  const ctx = canvas.getContext('2d')
  if (ctx) {
    ctx.drawImage(videoElement.value, 0, 0)
    prescriptionImage.value = canvas.toDataURL('image/jpeg')
    stopCamera()
  }
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = false
}

const handleDrop = (e: DragEvent) => {
  e.preventDefault()
  isDragOver.value = false
  
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    handleFile(target.files[0])
  }
}

const handleFile = (file: File) => {
  if (!file.type.startsWith('image/')) {
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    prescriptionImage.value = e.target?.result as string
  }
  reader.readAsDataURL(file)
}

const removeImage = () => {
  prescriptionImage.value = null
}

const nextStep = async () => {
  if (currentStep.value < workflowSteps.length - 1) {
    if (currentStep.value === 1 && prescriptionImage.value) {
      await processOCR()
    }
    currentStep.value++
  }
}

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const processOCR = async () => {
  state.isProcessing = true
  ocrProgress.value = 0
  ocrError.value = null
  
  try {
    // Simulate OCR processing
    const progressInterval = setInterval(() => {
      ocrProgress.value += Math.random() * 20
      if (ocrProgress.value >= 100) {
        ocrProgress.value = 100
        clearInterval(progressInterval)
      }
    }, 200)
    
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    ocrResult.value = {
      patientName: 'John Doe',
      prescribingDoctor: 'Dr. Smith',
      prescriptionDate: new Date().toISOString().split('T')[0],
      medications: [
        {
          name: 'Aspirin',
          strength: '100mg',
          dosage: '1 tablet',
          frequency: 'Once daily',
          quantity: 30,
          instructions: 'Take with food'
        }
      ]
    }
    
  } catch (error) {
    ocrError.value = 'OCR processing failed'
  } finally {
    state.isProcessing = false
  }
}

// Lifecycle
onMounted(() => {
  // Component mounted
})

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.upload-area {
  @apply border-2 border-dashed border-base-content/30 rounded-lg p-8 cursor-pointer transition-all duration-200;
}

.upload-area:hover {
  @apply border-primary bg-primary/5;
}

.upload-area--dragover {
  @apply border-primary bg-primary/10;
}

.upload-content {
  @apply flex flex-col items-center justify-center;
}

.step-content {
  @apply space-y-6;
}
</style> 