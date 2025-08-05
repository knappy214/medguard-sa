<template>
  <div class="mobile-camera-interface">
    <!-- Camera Viewport -->
    <div class="camera-viewport" :class="{ 'capturing': isCapturing }">
      <!-- Video Element -->
      <video
        ref="videoRef"
        class="camera-video"
        :class="{ 'mirrored': isFrontCamera }"
        autoplay
        playsinline
        muted
        @loadedmetadata="onVideoLoaded"
        @canplay="onVideoCanPlay"
      />
      
      <!-- Camera Overlay -->
      <div class="camera-overlay">
        <!-- Boundary Detection Guides -->
        <div class="boundary-guides" v-if="showBoundaryGuides">
          <div class="corner-guide top-left"></div>
          <div class="corner-guide top-right"></div>
          <div class="corner-guide bottom-left"></div>
          <div class="corner-guide bottom-right"></div>
          <div class="boundary-rectangle"></div>
        </div>
        
        <!-- Focus Indicator -->
        <div 
          v-if="showFocusIndicator" 
          class="focus-indicator"
          :style="{ left: focusPoint.x + '%', top: focusPoint.y + '%' }"
        >
          <div class="focus-ring"></div>
        </div>
        
        <!-- Image Quality Feedback -->
        <div v-if="imageQuality" class="quality-indicator" :class="qualityClass">
          <div class="quality-score">{{ imageQuality.overall }}%</div>
          <div class="quality-warnings" v-if="imageQuality.warnings.length">
            <div v-for="warning in imageQuality.warnings" :key="warning" class="warning-item">
              {{ warning }}
            </div>
          </div>
        </div>
        
        <!-- Capture Countdown -->
        <div v-if="captureCountdown > 0" class="capture-countdown">
          {{ captureCountdown }}
        </div>
        
        <!-- Multi-page Indicator -->
        <div v-if="prescriptionPages.length > 0" class="page-indicator">
          {{ t('mobileCamera.pageIndicator', { current: currentPageIndex + 1, total: prescriptionPages.length }) }}
        </div>
      </div>
    </div>
    
    <!-- Camera Controls -->
    <div class="camera-controls">
      <!-- Top Controls -->
      <div class="top-controls">
        <button 
          @click="closeCamera" 
          class="btn btn-circle btn-ghost"
          :title="t('mobileCamera.close')"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        <div class="camera-settings">
          <button 
            @click="toggleFlash" 
            class="btn btn-circle btn-ghost"
            :class="{ 'active': flashEnabled }"
            :title="t('mobileCamera.flash')"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </button>
          
          <button 
            @click="switchCamera" 
            class="btn btn-circle btn-ghost"
            :title="t('mobileCamera.switchCamera')"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Bottom Controls -->
      <div class="bottom-controls">
        <!-- Capture Button -->
        <button 
          @click="captureImage"
          class="capture-btn"
          :disabled="!isCameraReady || isCapturing"
          :class="{ 'capturing': isCapturing }"
        >
          <div class="capture-ring"></div>
        </button>
        
        <!-- Gallery Button -->
        <button 
          @click="openGallery"
          class="btn btn-circle btn-ghost gallery-btn"
          :title="t('mobileCamera.gallery')"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
    </div>
    
    <!-- Image Preview Modal -->
    <div v-if="showPreview" class="preview-modal modal modal-open">
      <div class="modal-box max-w-4xl">
        <div class="preview-header">
          <h3 class="text-lg font-bold">{{ t('mobileCamera.previewTitle') }}</h3>
          <button @click="closePreview" class="btn btn-sm btn-circle btn-ghost">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="preview-content">
          <div class="image-container">
            <img 
              :src="previewImage" 
              :style="{ transform: `rotate(${imageRotation}deg) scale(${imageZoom})` }"
              class="preview-image"
              @wheel="handleZoom"
              @mousedown="startPan"
              @mousemove="handlePan"
              @mouseup="stopPan"
              @touchstart="startPan"
              @touchmove="handlePan"
              @touchend="stopPan"
            />
          </div>
          
          <div class="preview-controls">
            <button @click="rotateImage" class="btn btn-sm">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ t('mobileCamera.rotate') }}
            </button>
            
            <button @click="resetZoom" class="btn btn-sm">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              {{ t('mobileCamera.resetZoom') }}
            </button>
            
            <button @click="cropImage" class="btn btn-sm">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              {{ t('mobileCamera.crop') }}
            </button>
          </div>
        </div>
        
        <div class="preview-actions">
          <button @click="retakePhoto" class="btn btn-outline">
            {{ t('mobileCamera.retake') }}
          </button>
          <button @click="confirmImage" class="btn btn-primary">
            {{ t('mobileCamera.confirm') }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Multi-page Review Modal -->
    <div v-if="showMultiPageReview" class="multi-page-modal modal modal-open">
      <div class="modal-box max-w-6xl">
        <div class="modal-header">
          <h3 class="text-lg font-bold">{{ t('mobileCamera.multiPageReview') }}</h3>
          <button @click="closeMultiPageReview" class="btn btn-sm btn-circle btn-ghost">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="pages-grid">
          <div 
            v-for="(page, index) in prescriptionPages" 
            :key="page.id"
            class="page-item"
            :class="{ 'selected': selectedPages.has(index) }"
            @click="togglePageSelection(index)"
          >
            <img :src="page.imageData" class="page-thumbnail" />
            <div class="page-info">
              <span class="page-number">{{ index + 1 }}</span>
              <span class="page-quality">{{ page.quality.overall }}%</span>
            </div>
            <button @click.stop="removePage(index)" class="remove-page-btn">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <div class="multi-page-actions">
          <button @click="addAnotherPage" class="btn btn-outline">
            {{ t('mobileCamera.addPage') }}
          </button>
          <button @click="processSelectedPages" class="btn btn-primary">
            {{ t('mobileCamera.processPages', { count: selectedPages.size }) }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Hidden Canvas for Image Processing -->
    <canvas ref="canvasRef" class="hidden" />
    
    <!-- Hidden File Input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      multiple
      capture="environment"
      class="hidden"
      @change="handleFileSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import type { 
  PrescriptionPage, 
  ImageQuality, 
  PrescriptionMetadata,
  CameraGuide,
  OCRConfidence
} from '@/types/medication'

interface Props {
  autoFocus?: boolean
  autoExposure?: boolean
  qualityThreshold?: number
  multiPage?: boolean
  autoCapture?: boolean
  captureDelay?: number
  enableHapticFeedback?: boolean
  enableBoundaryDetection?: boolean
  enableQualityAssessment?: boolean
  enableFlashControl?: boolean
  enableLowLightOptimization?: boolean
  maxPages?: number
  storageRetentionDays?: number
}

interface Emits {
  (e: 'close'): void
  (e: 'capture', imageData: string): void
  (e: 'multi-page-capture', pages: PrescriptionPage[]): void
  (e: 'error', error: string): void
  (e: 'quality-assessment', quality: ImageQuality): void
  (e: 'boundary-detected', boundaries: any): void
}

const props = withDefaults(defineProps<Props>(), {
  autoFocus: true,
  autoExposure: true,
  qualityThreshold: 70,
  multiPage: true,
  autoCapture: false,
  captureDelay: 3,
  enableHapticFeedback: true,
  enableBoundaryDetection: true,
  qualityAssessment: true,
  enableFlashControl: true,
  enableLowLightOptimization: true,
  maxPages: 10,
  storageRetentionDays: 7
})

const emit = defineEmits<Emits>()

const { t, locale } = useI18n()

// Camera state
const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const fileInputRef = ref<HTMLInputElement>()
const stream = ref<MediaStream | null>(null)
const isCameraReady = ref(false)
const isCapturing = ref(false)
const isFrontCamera = ref(false)
const flashEnabled = ref(false)
const showBoundaryGuides = ref(true)
const showFocusIndicator = ref(false)

// Image processing state
const capturedImage = ref<string | null>(null)
const previewImage = ref<string | null>(null)
const showPreview = ref(false)
const imageRotation = ref(0)
const imageZoom = ref(1)
const isPanning = ref(false)
const panStart = ref({ x: 0, y: 0 })

// Multi-page state
const prescriptionPages = ref<PrescriptionPage[]>([])
const currentPageIndex = ref(0)
const selectedPages = ref<Set<number>>(new Set())
const showMultiPageReview = ref(false)

// Quality assessment
const imageQuality = ref<ImageQuality | null>(null)
const qualityClass = computed(() => {
  if (!imageQuality.value) return ''
  const score = imageQuality.value.overall
  if (score >= 80) return 'quality-excellent'
  if (score >= 60) return 'quality-good'
  if (score >= 40) return 'quality-fair'
  return 'quality-poor'
})

// Focus and exposure
const focusPoint = ref({ x: 50, y: 50 })
const autoFocusTimer = ref<number | null>(null)
const autoExposureTimer = ref<number | null>(null)

// Capture countdown
const captureCountdown = ref(0)
const countdownTimer = ref<number | null>(null)

// Local storage management
const storageKey = 'medguard_camera_images'
const cleanupInterval = ref<number | null>(null)

// Methods
const initializeCamera = async () => {
  try {
    const constraints: MediaStreamConstraints = {
      video: {
        facingMode: 'environment',
        width: { ideal: 1920, min: 1280 },
        height: { ideal: 1080, min: 720 },
        frameRate: { ideal: 30, min: 15 }
      }
    }

    // Add advanced camera features if supported
    if (props.autoFocus || props.autoExposure) {
      constraints.video = {
        ...constraints.video,
        advanced: [
          {
            focusMode: props.autoFocus ? 'continuous' : 'manual',
            exposureMode: props.autoExposure ? 'continuous' : 'manual',
            whiteBalanceMode: 'continuous'
          }
        ]
      }
    }

    const mediaStream = await navigator.mediaDevices.getUserMedia(constraints)
    stream.value = mediaStream
    
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      await videoRef.value.play()
    }

    // Initialize advanced features
    if (props.enableBoundaryDetection) {
      initializeBoundaryDetection()
    }
    
    if (props.enableQualityAssessment) {
      startQualityAssessment()
    }

    // Setup local storage cleanup
    setupStorageCleanup()

  } catch (error) {
    console.error('Camera initialization error:', error)
    emit('error', t('mobileCamera.cameraError'))
  }
}

const initializeBoundaryDetection = () => {
  // Use Canvas API for real-time boundary detection
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  
  if (!ctx || !videoRef.value) return

  const detectBoundaries = () => {
    if (!videoRef.value || !isCameraReady.value) return

    canvas.width = videoRef.value.videoWidth
    canvas.height = videoRef.value.videoHeight
    
    ctx.drawImage(videoRef.value, 0, 0)
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    
    // Simple edge detection for prescription boundaries
    const edges = detectEdges(imageData)
    const boundaries = findDocumentBoundaries(edges)
    
    if (boundaries) {
      emit('boundary-detected', boundaries)
      updateBoundaryGuides(boundaries)
    }
  }

  // Run boundary detection every 500ms
  setInterval(detectBoundaries, 500)
}

const detectEdges = (imageData: ImageData): Uint8ClampedArray => {
  const { data, width, height } = imageData
  const edges = new Uint8ClampedArray(data.length)
  
  // Simple Sobel edge detection
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = (y * width + x) * 4
      
      // Calculate gradients
      const gx = 
        -data[idx - 4] + data[idx + 4] +
        -2 * data[idx - 4 + width * 4] + 2 * data[idx + 4 + width * 4] +
        -data[idx - 4 + width * 8] + data[idx + 4 + width * 8]
      
      const gy = 
        -data[idx - width * 4] + data[idx + width * 4] +
        -2 * data[idx + 4 - width * 4] + 2 * data[idx + 4 + width * 4] +
        -data[idx + 8 - width * 4] + data[idx + 8 + width * 4]
      
      const magnitude = Math.sqrt(gx * gx + gy * gy)
      const edgeValue = Math.min(255, magnitude / 4)
      
      edges[idx] = edgeValue
      edges[idx + 1] = edgeValue
      edges[idx + 2] = edgeValue
      edges[idx + 3] = 255
    }
  }
  
  return edges
}

const findDocumentBoundaries = (edges: Uint8ClampedArray): any => {
  // Simplified document boundary detection
  // In a real implementation, this would use more sophisticated algorithms
  return {
    topLeft: { x: 10, y: 10 },
    topRight: { x: 90, y: 10 },
    bottomLeft: { x: 10, y: 90 },
    bottomRight: { x: 90, y: 90 }
  }
}

const updateBoundaryGuides = (boundaries: any) => {
  // Update the visual guides based on detected boundaries
  showBoundaryGuides.value = true
}

const startQualityAssessment = () => {
  const assessQuality = () => {
    if (!videoRef.value || !isCameraReady.value) return

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    
    if (!ctx) return

    canvas.width = videoRef.value.videoWidth
    canvas.height = videoRef.value.videoHeight
    ctx.drawImage(videoRef.value, 0, 0)
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
    const quality = calculateImageQuality(imageData)
    
    imageQuality.value = quality
    emit('quality-assessment', quality)
  }

  // Assess quality every second
  setInterval(assessQuality, 1000)
}

const calculateImageQuality = (imageData: ImageData): ImageQuality => {
  const { data, width, height } = imageData
  let brightness = 0
  let contrast = 0
  let sharpness = 0
  let noise = 0
  let blur = 0

  // Calculate brightness
  for (let i = 0; i < data.length; i += 4) {
    brightness += (data[i] + data[i + 1] + data[i + 2]) / 3
  }
  brightness = brightness / (data.length / 4)

  // Calculate contrast (simplified)
  let variance = 0
  for (let i = 0; i < data.length; i += 4) {
    const pixel = (data[i] + data[i + 1] + data[i + 2]) / 3
    variance += Math.pow(pixel - brightness, 2)
  }
  contrast = Math.sqrt(variance / (data.length / 4))

  // Calculate sharpness (simplified)
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = (y * width + x) * 4
      const current = (data[idx] + data[idx + 1] + data[idx + 2]) / 3
      const right = (data[idx + 4] + data[idx + 5] + data[idx + 6]) / 3
      const bottom = (data[idx + width * 4] + data[idx + width * 4 + 1] + data[idx + width * 4 + 2]) / 3
      
      sharpness += Math.abs(current - right) + Math.abs(current - bottom)
    }
  }
  sharpness = sharpness / ((width - 2) * (height - 2))

  // Normalize values
  brightness = Math.min(100, Math.max(0, (brightness / 255) * 100))
  contrast = Math.min(100, Math.max(0, (contrast / 255) * 100))
  sharpness = Math.min(100, Math.max(0, (sharpness / 255) * 100))

  // Calculate overall quality score
  const overall = (brightness * 0.2 + contrast * 0.3 + sharpness * 0.5)
  
  const warnings: string[] = []
  if (brightness < 30) warnings.push(t('mobileCamera.lowBrightness'))
  if (brightness > 80) warnings.push(t('mobileCamera.highBrightness'))
  if (contrast < 20) warnings.push(t('mobileCamera.lowContrast'))
  if (sharpness < 30) warnings.push(t('mobileCamera.blurry'))

  return {
    brightness,
    contrast,
    sharpness,
    noise,
    blur,
    overall,
    isValid: overall >= props.qualityThreshold,
    warnings
  }
}

const captureImage = async () => {
  if (!videoRef.value || !canvasRef.value || isCapturing.value) return

  isCapturing.value = true
  
  try {
    // Trigger haptic feedback
    if (props.enableHapticFeedback && 'vibrate' in navigator) {
      navigator.vibrate(100)
    }

    // Start countdown if auto-capture is enabled
    if (props.autoCapture) {
      await startCaptureCountdown()
    }

    const video = videoRef.value
    const canvas = canvasRef.value
    const ctx = canvas.getContext('2d')
    
    if (!ctx) throw new Error('Canvas context not available')

    // Set canvas size to match video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    
    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0)
    
    // Convert to base64 with high quality
    const imageData = canvas.toDataURL('image/jpeg', 0.95)
    capturedImage.value = imageData
    
    // Show preview
    previewImage.value = imageData
    showPreview.value = true
    
    // Add to multi-page collection if enabled
    if (props.multiPage && prescriptionPages.value.length < props.maxPages) {
      const page: PrescriptionPage = {
        id: `page_${Date.now()}_${Math.random()}`,
        imageData,
        pageNumber: prescriptionPages.value.length + 1,
        quality: imageQuality.value || {
          brightness: 0,
          contrast: 0,
          sharpness: 0,
          noise: 0,
          blur: 0,
          overall: 0,
          isValid: false,
          warnings: []
        },
        ocrText: '',
        extractedMedications: [],
        confidence: 0,
        processingStatus: 'pending'
      }
      
      prescriptionPages.value.push(page)
      selectedPages.value.add(prescriptionPages.value.length - 1)
    }

    emit('capture', imageData)

  } catch (error) {
    console.error('Capture error:', error)
    emit('error', t('mobileCamera.captureError'))
  } finally {
    isCapturing.value = false
  }
}

const startCaptureCountdown = async () => {
  captureCountdown.value = props.captureDelay
  
  return new Promise<void>((resolve) => {
    countdownTimer.value = window.setInterval(() => {
      captureCountdown.value--
      
      if (captureCountdown.value <= 0) {
        clearInterval(countdownTimer.value!)
        countdownTimer.value = null
        resolve()
      }
    }, 1000)
  })
}

const toggleFlash = async () => {
  if (!props.enableFlashControl || !stream.value) return

  try {
    const videoTrack = stream.value.getVideoTracks()[0]
    if (!videoTrack) return

    const capabilities = videoTrack.getCapabilities()
    if (!capabilities.torch) return

    flashEnabled.value = !flashEnabled.value
    
    await videoTrack.applyConstraints({
      advanced: [{ torch: flashEnabled.value }]
    })

    // Trigger haptic feedback
    if (props.enableHapticFeedback && 'vibrate' in navigator) {
      navigator.vibrate(50)
    }

  } catch (error) {
    console.error('Flash toggle error:', error)
    flashEnabled.value = false
  }
}

const switchCamera = async () => {
  if (!stream.value) return

  try {
    // Stop current stream
    stream.value.getTracks().forEach(track => track.stop())
    
    // Switch camera
    isFrontCamera.value = !isFrontCamera.value
    
    // Initialize new camera
    await initializeCamera()

    // Trigger haptic feedback
    if (props.enableHapticFeedback && 'vibrate' in navigator) {
      navigator.vibrate(50)
    }

  } catch (error) {
    console.error('Camera switch error:', error)
    emit('error', t('mobileCamera.switchError'))
  }
}

const openGallery = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files
  
  if (!files || files.length === 0) return

  Array.from(files).forEach(file => {
    if (!file.type.startsWith('image/')) return

    const reader = new FileReader()
    reader.onload = (e) => {
      const imageData = e.target?.result as string
      
      if (props.multiPage && prescriptionPages.value.length < props.maxPages) {
        const page: PrescriptionPage = {
          id: `gallery_${Date.now()}_${Math.random()}`,
          imageData,
          pageNumber: prescriptionPages.value.length + 1,
          quality: {
            brightness: 0,
            contrast: 0,
            sharpness: 0,
            noise: 0,
            blur: 0,
            overall: 0,
            isValid: false,
            warnings: []
          },
          ocrText: '',
          extractedMedications: [],
          confidence: 0,
          processingStatus: 'pending'
        }
        
        prescriptionPages.value.push(page)
        selectedPages.value.add(prescriptionPages.value.length - 1)
      } else {
        previewImage.value = imageData
        showPreview.value = true
      }
    }
    reader.readAsDataURL(file)
  })
}

// Preview controls
const rotateImage = () => {
  imageRotation.value = (imageRotation.value + 90) % 360
}

const resetZoom = () => {
  imageZoom.value = 1
}

const cropImage = () => {
  // Implement image cropping functionality
  // This would involve creating a cropping interface
  console.log('Crop image functionality')
}

const handleZoom = (event: WheelEvent) => {
  event.preventDefault()
  const delta = event.deltaY > 0 ? 0.9 : 1.1
  imageZoom.value = Math.max(0.5, Math.min(3, imageZoom.value * delta))
}

const startPan = (event: MouseEvent | TouchEvent) => {
  isPanning.value = true
  if (event instanceof MouseEvent) {
    panStart.value = { x: event.clientX, y: event.clientY }
  } else if (event instanceof TouchEvent) {
    panStart.value = { x: event.touches[0].clientX, y: event.touches[0].clientY }
  }
}

const handlePan = (event: MouseEvent | TouchEvent) => {
  if (!isPanning.value) return
  
  // Implement panning logic
  console.log('Panning image')
}

const stopPan = () => {
  isPanning.value = false
}

const retakePhoto = () => {
  showPreview.value = false
  previewImage.value = null
  imageRotation.value = 0
  imageZoom.value = 1
}

const confirmImage = () => {
  if (previewImage.value) {
    emit('capture', previewImage.value)
  }
  showPreview.value = false
}

const closePreview = () => {
  showPreview.value = false
  previewImage.value = null
  imageRotation.value = 0
  imageZoom.value = 1
}

// Multi-page controls
const togglePageSelection = (index: number) => {
  if (selectedPages.value.has(index)) {
    selectedPages.value.delete(index)
  } else {
    selectedPages.value.add(index)
  }
}

const removePage = (index: number) => {
  prescriptionPages.value.splice(index, 1)
  selectedPages.value.clear()
  
  // Reindex pages
  prescriptionPages.value.forEach((page, i) => {
    page.pageNumber = i + 1
  })
}

const addAnotherPage = () => {
  showMultiPageReview.value = false
  // Return to camera view
}

const processSelectedPages = () => {
  const selectedPageObjects = Array.from(selectedPages.value).map(index => 
    prescriptionPages.value[index]
  )
  
  emit('multi-page-capture', selectedPageObjects)
  showMultiPageReview.value = false
}

const closeMultiPageReview = () => {
  showMultiPageReview.value = false
}

// Local storage management
const setupStorageCleanup = () => {
  // Clean up old images every hour
  cleanupInterval.value = window.setInterval(() => {
    cleanupOldImages()
  }, 60 * 60 * 1000)
}

const cleanupOldImages = () => {
  try {
    const stored = localStorage.getItem(storageKey)
    if (!stored) return

    const images = JSON.parse(stored)
    const cutoff = Date.now() - (props.storageRetentionDays * 24 * 60 * 60 * 1000)
    
    const filtered = images.filter((img: any) => img.timestamp > cutoff)
    
    localStorage.setItem(storageKey, JSON.stringify(filtered))
  } catch (error) {
    console.error('Storage cleanup error:', error)
  }
}

const saveImageToStorage = (imageData: string) => {
  try {
    const stored = localStorage.getItem(storageKey) || '[]'
    const images = JSON.parse(stored)
    
    images.push({
      id: `img_${Date.now()}`,
      data: imageData,
      timestamp: Date.now()
    })
    
    // Keep only recent images
    const maxImages = 50
    if (images.length > maxImages) {
      images.splice(0, images.length - maxImages)
    }
    
    localStorage.setItem(storageKey, JSON.stringify(images))
  } catch (error) {
    console.error('Storage save error:', error)
  }
}

// Event handlers
const onVideoLoaded = () => {
  console.log('Video metadata loaded')
}

const onVideoCanPlay = () => {
  isCameraReady.value = true
}

const closeCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
  
  if (cleanupInterval.value) {
    clearInterval(cleanupInterval.value)
  }
  
  emit('close')
}

// Lifecycle
onMounted(async () => {
  await initializeCamera()
})

onUnmounted(() => {
  closeCamera()
})
</script>

<style scoped>
.mobile-camera-interface {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #000;
  z-index: 9999;
  display: flex;
  flex-direction: column;
}

/* Camera Viewport */
.camera-viewport {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: #000;
}

.camera-viewport.capturing {
  animation: capture-flash 0.3s ease-out;
}

@keyframes capture-flash {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scaleX(-1);
}

.camera-video.mirrored {
  transform: scaleX(1);
}

/* Camera Overlay */
.camera-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

/* Boundary Detection Guides */
.boundary-guides {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.corner-guide {
  position: absolute;
  width: 40px;
  height: 40px;
  border: 3px solid #00ff00;
  opacity: 0.8;
}

.corner-guide.top-left {
  top: 20%;
  left: 10%;
  border-right: none;
  border-bottom: none;
}

.corner-guide.top-right {
  top: 20%;
  right: 10%;
  border-left: none;
  border-bottom: none;
}

.corner-guide.bottom-left {
  bottom: 20%;
  left: 10%;
  border-right: none;
  border-top: none;
}

.corner-guide.bottom-right {
  bottom: 20%;
  right: 10%;
  border-left: none;
  border-top: none;
}

.boundary-rectangle {
  position: absolute;
  top: 20%;
  left: 10%;
  width: 80%;
  height: 60%;
  border: 2px dashed #00ff00;
  opacity: 0.6;
  pointer-events: none;
}

/* Focus Indicator */
.focus-indicator {
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.focus-ring {
  width: 60px;
  height: 60px;
  border: 2px solid #fff;
  border-radius: 50%;
  animation: focus-pulse 1s ease-in-out infinite;
}

@keyframes focus-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.7; }
}

/* Image Quality Feedback */
.quality-indicator {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 12px;
  pointer-events: none;
}

.quality-indicator.quality-excellent {
  border-left: 4px solid #10b981;
}

.quality-indicator.quality-good {
  border-left: 4px solid #f59e0b;
}

.quality-indicator.quality-fair {
  border-left: 4px solid #f97316;
}

.quality-indicator.quality-poor {
  border-left: 4px solid #ef4444;
}

.quality-score {
  font-weight: bold;
  font-size: 14px;
}

.quality-warnings {
  margin-top: 4px;
}

.warning-item {
  color: #fbbf24;
  font-size: 10px;
  margin-top: 2px;
}

/* Capture Countdown */
.capture-countdown {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 120px;
  font-weight: bold;
  color: white;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
  animation: countdown-pulse 1s ease-in-out infinite;
}

@keyframes countdown-pulse {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.1); }
}

/* Page Indicator */
.page-indicator {
  position: absolute;
  bottom: 120px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  pointer-events: none;
}

/* Camera Controls */
.camera-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  padding: 20px;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.8));
  pointer-events: auto;
}

.top-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.camera-settings {
  display: flex;
  gap: 16px;
}

.bottom-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
}

/* Capture Button */
.capture-btn {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: white;
  border: 4px solid #e5e7eb;
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.capture-btn:hover {
  transform: scale(1.05);
  border-color: #d1d5db;
}

.capture-btn:active {
  transform: scale(0.95);
}

.capture-btn.capturing {
  animation: capture-pulse 0.5s ease-in-out infinite;
}

@keyframes capture-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(0.9); }
}

.capture-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.capture-ring {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: white;
  border: 2px solid #e5e7eb;
}

.gallery-btn {
  width: 50px;
  height: 50px;
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
}

.gallery-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

/* Preview Modal */
.preview-modal {
  z-index: 10000;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.preview-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-container {
  position: relative;
  width: 100%;
  height: 400px;
  overflow: hidden;
  border-radius: 8px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: transform 0.2s ease;
  cursor: grab;
}

.preview-image:active {
  cursor: grabbing;
}

.preview-controls {
  display: flex;
  gap: 8px;
  justify-content: center;
}

.preview-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 16px;
}

/* Multi-page Modal */
.multi-page-modal {
  z-index: 10000;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.page-item {
  position: relative;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-item:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
}

.page-item.selected {
  border-color: #10b981;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.page-thumbnail {
  width: 100%;
  height: 120px;
  object-fit: cover;
}

.page-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  font-size: 12px;
  display: flex;
  justify-content: space-between;
}

.remove-page-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 24px;
  height: 24px;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}

.remove-page-btn:hover {
  background: rgba(239, 68, 68, 1);
}

.multi-page-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* Utility Classes */
.hidden {
  display: none !important;
}

/* Responsive Design */
@media (max-width: 768px) {
  .camera-controls {
    padding: 16px;
  }
  
  .capture-btn {
    width: 70px;
    height: 70px;
  }
  
  .capture-ring {
    width: 50px;
    height: 50px;
  }
  
  .gallery-btn {
    width: 45px;
    height: 45px;
  }
  
  .pages-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
  
  .page-thumbnail {
    height: 100px;
  }
}

@media (max-width: 480px) {
  .top-controls {
    margin-bottom: 16px;
  }
  
  .camera-settings {
    gap: 12px;
  }
  
  .bottom-controls {
    gap: 30px;
  }
  
  .capture-btn {
    width: 65px;
    height: 65px;
  }
  
  .capture-ring {
    width: 45px;
    height: 45px;
  }
  
  .pages-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }
  
  .page-thumbnail {
    height: 80px;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .preview-modal .modal-box,
  .multi-page-modal .modal-box {
    background: #1f2937;
    color: white;
  }
  
  .image-container {
    background: #374151;
  }
  
  .page-item {
    border-color: #4b5563;
  }
  
  .page-item:hover {
    border-color: #60a5fa;
  }
  
  .page-item.selected {
    border-color: #34d399;
    box-shadow: 0 4px 12px rgba(52, 211, 153, 0.3);
  }
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .capture-btn,
  .focus-ring,
  .capture-countdown,
  .page-item {
    animation: none;
    transition: none;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .boundary-rectangle {
    border-color: #ffffff;
    border-width: 3px;
  }
  
  .corner-guide {
    border-color: #ffffff;
    border-width: 4px;
  }
  
  .quality-indicator {
    background: #000000;
    border: 2px solid #ffffff;
  }
}
</style>
