<template>
  <div class="step1-image-capture">
    <h3 class="text-xl font-semibold mb-4">
      <i class="fas fa-camera text-primary mr-2"></i>
      {{ $t('workflow.step1.title', 'Capture Prescription Image') }}
    </h3>
    
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Camera Capture -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">
            <i class="fas fa-camera mr-2"></i>
            {{ $t('workflow.step1.camera', 'Camera Capture') }}
          </h4>
          
          <div class="camera-container relative">
            <video
              v-if="showCamera"
              ref="videoElement"
              class="w-full h-64 object-cover rounded-lg"
              autoplay
              muted
              playsinline
            ></video>
            <div
              v-else
              class="w-full h-64 bg-base-300 rounded-lg flex items-center justify-center"
            >
              <i class="fas fa-camera text-4xl text-base-content/50"></i>
            </div>
            
            <!-- Camera overlay with guide -->
            <div v-if="showCamera" class="absolute inset-0 pointer-events-none">
              <div class="absolute inset-4 border-2 border-primary border-dashed rounded-lg opacity-50"></div>
              <div class="absolute top-2 left-2 bg-base-100 px-2 py-1 rounded text-xs">
                {{ $t('workflow.step1.alignPrescription', 'Align prescription within frame') }}
              </div>
            </div>
          </div>
          
          <div class="flex gap-2 mt-4">
            <button
              @click="toggleCamera"
              class="btn btn-primary"
              :disabled="isProcessing"
            >
              <i class="fas fa-camera mr-2"></i>
              {{ showCamera ? $t('workflow.step1.stopCamera', 'Stop Camera') : $t('workflow.step1.startCamera', 'Start Camera') }}
            </button>
            <button
              v-if="showCamera"
              @click="captureImage"
              class="btn btn-secondary"
              :disabled="isProcessing"
            >
              <i class="fas fa-camera-retro mr-2"></i>
              {{ $t('workflow.step1.capture', 'Capture') }}
            </button>
          </div>
          
          <!-- Camera settings -->
          <div v-if="showCamera" class="mt-4 p-3 bg-base-100 rounded-lg">
            <h5 class="font-medium mb-2">{{ $t('workflow.step1.cameraSettings', 'Camera Settings') }}</h5>
            <div class="grid grid-cols-2 gap-3">
              <div class="form-control">
                <label class="label">
                  <span class="label-text text-xs">{{ $t('workflow.step1.contrast', 'Contrast') }}</span>
                </label>
                <input
                  v-model="cameraSettings.contrast"
                  type="range"
                  min="0.5"
                  max="2"
                  step="0.1"
                  class="range range-xs range-primary"
                />
              </div>
              <div class="form-control">
                <label class="label">
                  <span class="label-text text-xs">{{ $t('workflow.step1.brightness', 'Brightness') }}</span>
                </label>
                <input
                  v-model="cameraSettings.brightness"
                  type="range"
                  min="-0.5"
                  max="0.5"
                  step="0.1"
                  class="range range-xs range-primary"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- File Upload -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">
            <i class="fas fa-cloud-upload-alt mr-2"></i>
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
              <p class="text-base-content/70 mb-4">
                {{ $t('workflow.step1.orClick', 'or click to browse') }}
              </p>
              <div class="text-xs text-base-content/60">
                <p>{{ $t('workflow.step1.supportedFormats', 'Supported: JPG, PNG, PDF') }}</p>
                <p>{{ $t('workflow.step1.maxSize', 'Max size: 10MB') }}</p>
              </div>
            </div>
          </div>
          
          <!-- Image preprocessing options -->
          <div class="mt-4 p-3 bg-base-100 rounded-lg">
            <h5 class="font-medium mb-2">{{ $t('workflow.step1.preprocessing', 'Image Preprocessing') }}</h5>
            <div class="space-y-3">
              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text text-sm">{{ $t('workflow.step1.autoEnhance', 'Auto-enhance image') }}</span>
                  <input
                    v-model="preprocessingOptions.autoEnhance"
                    type="checkbox"
                    class="checkbox checkbox-primary checkbox-sm"
                  />
                </label>
              </div>
              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text text-sm">{{ $t('workflow.step1.autoRotate', 'Auto-rotate') }}</span>
                  <input
                    v-model="preprocessingOptions.autoRotate"
                    type="checkbox"
                    class="checkbox checkbox-primary checkbox-sm"
                  />
                </label>
              </div>
              <div class="form-control">
                <label class="label cursor-pointer">
                  <span class="label-text text-sm">{{ $t('workflow.step1.denoise', 'Remove noise') }}</span>
                  <input
                    v-model="preprocessingOptions.denoise"
                    type="checkbox"
                    class="checkbox checkbox-primary checkbox-sm"
                  />
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Image Preview -->
    <div v-if="image" class="mt-6">
      <h4 class="font-semibold mb-3">
        <i class="fas fa-eye mr-2"></i>
        {{ $t('workflow.step1.preview', 'Image Preview') }}
      </h4>
      
      <div class="relative inline-block">
        <img
          :src="image"
          alt="Prescription preview"
          class="max-w-md rounded-lg shadow-lg"
          @load="handleImageLoad"
        />
        
        <!-- Image info overlay -->
        <div class="absolute top-2 left-2 bg-base-100/90 px-2 py-1 rounded text-xs">
          <div>{{ imageInfo.dimensions.width }} × {{ imageInfo.dimensions.height }}</div>
          <div>{{ formatFileSize(imageInfo.fileSize) }}</div>
        </div>
        
        <!-- Action buttons -->
        <div class="absolute top-2 right-2 flex gap-1">
          <button
            @click="enhanceImage"
            class="btn btn-circle btn-sm btn-primary"
            :disabled="isProcessing"
            :title="$t('workflow.step1.enhance', 'Enhance image')"
          >
            <i class="fas fa-magic"></i>
          </button>
          <button
            @click="rotateImage"
            class="btn btn-circle btn-sm btn-secondary"
            :disabled="isProcessing"
            :title="$t('workflow.step1.rotate', 'Rotate image')"
          >
            <i class="fas fa-redo"></i>
          </button>
          <button
            @click="removeImage"
            class="btn btn-circle btn-sm btn-error"
            :title="$t('workflow.step1.remove', 'Remove image')"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
      
      <!-- Image quality indicator -->
      <div class="mt-3 flex items-center gap-2">
        <div class="flex items-center gap-1">
          <i class="fas fa-chart-line text-sm"></i>
          <span class="text-sm">{{ $t('workflow.step1.quality', 'Quality') }}:</span>
        </div>
        <div class="flex gap-1">
          <div
            v-for="i in 5"
            :key="i"
            class="w-2 h-2 rounded-full"
            :class="i <= imageQuality ? 'bg-success' : 'bg-base-300'"
          ></div>
        </div>
        <span class="text-xs text-base-content/70">{{ imageQualityText }}</span>
      </div>
    </div>

    <!-- Processing indicator -->
    <div v-if="isProcessing" class="mt-4">
      <div class="alert alert-info">
        <div class="loading loading-spinner loading-sm"></div>
        <span>{{ $t('workflow.step1.processing', 'Processing image...') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Props
interface Props {
  image?: string | null
  showCamera?: boolean
  isProcessing?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  image: null,
  showCamera: false,
  isProcessing: false
})

// Emits
const emit = defineEmits<{
  'update:image': [value: string | null]
  'update:showCamera': [value: boolean]
  'image-captured': [imageData: string]
  'image-uploaded': [file: File]
}>()

// Reactive state
const isDragOver = ref(false)
const videoElement = ref<HTMLVideoElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
let stream: MediaStream | null = null

// Camera settings
const cameraSettings = reactive({
  contrast: 1.2,
  brightness: 0.1
})

// Image preprocessing options
const preprocessingOptions = reactive({
  autoEnhance: true,
  autoRotate: true,
  denoise: true
})

// Image info
const imageInfo = reactive({
  dimensions: { width: 0, height: 0 },
  fileSize: 0
})

// Computed properties
const imageQuality = computed(() => {
  if (!props.image) return 0
  
  // Simple quality assessment based on dimensions and file size
  const { width, height } = imageInfo.dimensions
  const megapixels = (width * height) / 1000000
  
  if (megapixels > 8) return 5
  if (megapixels > 4) return 4
  if (megapixels > 2) return 3
  if (megapixels > 1) return 2
  return 1
})

const imageQualityText = computed(() => {
  switch (imageQuality.value) {
    case 5: return t('workflow.step1.quality.excellent', 'Excellent')
    case 4: return t('workflow.step1.quality.good', 'Good')
    case 3: return t('workflow.step1.quality.fair', 'Fair')
    case 2: return t('workflow.step1.quality.poor', 'Poor')
    case 1: return t('workflow.step1.quality.veryPoor', 'Very Poor')
    default: return t('workflow.step1.quality.unknown', 'Unknown')
  }
})

// Methods
const toggleCamera = async () => {
  if (props.showCamera) {
    stopCamera()
  } else {
    await startCamera()
  }
}

const startCamera = async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        facingMode: 'environment',
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      } 
    })
    
    if (videoElement.value) {
      videoElement.value.srcObject = stream
    }
    
    emit('update:showCamera', true)
  } catch (error) {
    console.error('Error accessing camera:', error)
    // Fallback to any available camera
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true })
      if (videoElement.value) {
        videoElement.value.srcObject = stream
      }
      emit('update:showCamera', true)
    } catch (fallbackError) {
      console.error('Camera access failed:', fallbackError)
    }
  }
}

const stopCamera = () => {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
  emit('update:showCamera', false)
}

const captureImage = () => {
  if (!videoElement.value) return
  
  const canvas = document.createElement('canvas')
  canvas.width = videoElement.value.videoWidth
  canvas.height = videoElement.value.videoHeight
  
  const ctx = canvas.getContext('2d')
  if (ctx) {
    // Apply camera settings
    ctx.filter = `contrast(${cameraSettings.contrast}) brightness(${1 + cameraSettings.brightness})`
    ctx.drawImage(videoElement.value, 0, 0)
    
    const imageData = canvas.toDataURL('image/jpeg', 0.9)
    emit('image-captured', imageData)
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
    console.error('Invalid file type')
    return
  }
  
  if (file.size > 10 * 1024 * 1024) { // 10MB limit
    console.error('File too large')
    return
  }
  
  const reader = new FileReader()
  reader.onload = (e) => {
    const imageData = e.target?.result as string
    emit('update:image', imageData)
    emit('image-uploaded', file)
    
    // Set file info
    imageInfo.fileSize = file.size
  }
  reader.readAsDataURL(file)
}

const handleImageLoad = (e: Event) => {
  const img = e.target as HTMLImageElement
  imageInfo.dimensions = {
    width: img.naturalWidth,
    height: img.naturalHeight
  }
}

const removeImage = () => {
  emit('update:image', null)
  imageInfo.dimensions = { width: 0, height: 0 }
  imageInfo.fileSize = 0
}

const enhanceImage = async () => {
  if (!props.image) return
  
  try {
    // Apply image enhancement
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    
    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      
      if (ctx) {
        // Apply enhancement filters
        ctx.filter = 'contrast(1.2) brightness(1.1) saturate(1.1)'
        ctx.drawImage(img, 0, 0)
        
        const enhancedImage = canvas.toDataURL('image/jpeg', 0.9)
        emit('update:image', enhancedImage)
      }
    }
    
    img.src = props.image
  } catch (error) {
    console.error('Image enhancement failed:', error)
  }
}

const rotateImage = async () => {
  if (!props.image) return
  
  try {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    
    img.onload = () => {
      // Rotate 90 degrees clockwise
      canvas.width = img.height
      canvas.height = img.width
      
      if (ctx) {
        ctx.translate(canvas.width, 0)
        ctx.rotate(Math.PI / 2)
        ctx.drawImage(img, 0, 0)
        
        const rotatedImage = canvas.toDataURL('image/jpeg', 0.9)
        emit('update:image', rotatedImage)
        
        // Update dimensions
        imageInfo.dimensions = {
          width: img.height,
          height: img.width
        }
      }
    }
    
    img.src = props.image
  } catch (error) {
    console.error('Image rotation failed:', error)
  }
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Lifecycle
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

.camera-container {
  @apply relative overflow-hidden;
}

.range {
  @apply w-full;
}
</style> 