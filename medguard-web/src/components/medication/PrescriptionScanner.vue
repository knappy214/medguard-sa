<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import type { 
  MedicationFormData, 
  BulkMedicationEntry,
  PrescriptionPage,
  ImageQuality,
  PrescriptionMetadata,
  CameraGuide,
  OCRConfidence,
  MedicationInteraction,
  BatchProcessingResult,
  SouthAfricanPrescriptionValidation,
  FileUploadProgress,
  DragDropZone
} from '@/types/medication'

interface Props {
  mode?: 'camera' | 'upload' | 'both'
  allowBatch?: boolean
  autoProcess?: boolean
  multiPage?: boolean
  qualityThreshold?: number
  autoCapture?: boolean
  captureDelay?: number
}

interface Emits {
  (e: 'close'): void
  (e: 'add', data: MedicationFormData): void
  (e: 'bulk-add', data: BulkMedicationEntry[]): void
  (e: 'batch-result', result: BatchProcessingResult): void
  (e: 'error', error: string): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'both',
  allowBatch: true,
  autoProcess: false,
  multiPage: true,
  qualityThreshold: 70,
  autoCapture: false,
  captureDelay: 3
})

const emit = defineEmits<Emits>()

const { t, locale } = useI18n()

// Component state
const isOpen = ref(false)
const loading = ref(false)
const processing = ref(false)
const error = ref('')
const success = ref('')

// Camera and file handling
const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const fileInputRef = ref<HTMLInputElement>()
const stream = ref<MediaStream | null>(null)
const capturedImage = ref<string | null>(null)
const uploadedFile = ref<File | null>(null)

// Multi-page scanning
const prescriptionPages = ref<PrescriptionPage[]>([])
const currentPageIndex = ref(0)
const selectedPages = ref<Set<number>>(new Set())
const pageViewMode = ref<'grid' | 'list' | 'thumbnail'>('grid')
const sortBy = ref<'quality' | 'confidence' | 'pageNumber'>('pageNumber')
const filterStatus = ref<'all' | 'completed' | 'failed' | 'pending'>('all')

// Camera preview and guides
const cameraGuides = ref<CameraGuide[]>([
  {
    type: 'rectangle',
    position: { x: 50, y: 50, width: 80, height: 60 },
    color: '#00ff00',
    opacity: 0.7,
    message: t('prescriptionScanner.optimalPosition')
  }
])
const showGuides = ref(true)
const autoCaptureTimer = ref<number | null>(null)
const captureCountdown = ref(0)

// Image quality validation
const imageQuality = ref<ImageQuality | null>(null)
const qualityValidationEnabled = ref(true)
const qualityWarnings = ref<string[]>([])

// OCR and processing
const ocrText = ref('')
const extractedMedications = ref<BulkMedicationEntry[]>([])
const processingStep = ref<'capture' | 'preprocess' | 'ocr' | 'parse' | 'review'>('capture')
const ocrConfidence = ref<OCRConfidence[]>([])
const lowConfidenceResults = ref<OCRConfidence[]>([])

// Review interface
const selectedMedications = ref<Set<number>>(new Set())
const editingMedication = ref<BulkMedicationEntry | null>(null)
const showEditModal = ref(false)
const showManualCorrection = ref(false)

// Prescription metadata
const prescriptionMetadata = ref<PrescriptionMetadata>({})
const showMetadata = ref(false)

// Batch processing
const batchResult = ref<BatchProcessingResult | null>(null)
const duplicateMedications = ref<BulkMedicationEntry[]>([])
const interactions = ref<MedicationInteraction[]>([])
const showInteractions = ref(false)

// Drag and drop
const dragDropZone = ref<DragDropZone>({
  isActive: false,
  isDragOver: false,
  acceptedFiles: [],
  rejectedFiles: [],
  totalSize: 0
})
const uploadProgress = ref<FileUploadProgress[]>([])

// South African prescription validation
const saValidation = ref<SouthAfricanPrescriptionValidation | null>(null)
const validationEnabled = ref(true)

// Image preprocessing options
const preprocessingOptions = reactive({
  enhanceContrast: true,
  removeNoise: true,
  sharpen: true,
  rotate: 0,
  brightness: 1.0,
  contrast: 1.0,
  saturation: 1.0,
  gamma: 1.0,
  autoEnhance: true
})

// Export functionality
const exportFormat = ref<'json' | 'csv' | 'pdf' | 'xml'>('json')
const showExportModal = ref(false)

// Prescription abbreviation mappings
const prescriptionAbbreviations = {
  en: {
    'po': 'by mouth',
    'pr': 'by rectum',
    'im': 'intramuscular',
    'iv': 'intravenous',
    'sc': 'subcutaneous',
    'qd': 'once daily',
    'bid': 'twice daily',
    'tid': 'three times daily',
    'qid': 'four times daily',
    'qod': 'every other day',
    'prn': 'as needed',
    'ac': 'before meals',
    'pc': 'after meals',
    'hs': 'at bedtime',
    'am': 'morning',
    'pm': 'evening',
    'mg': 'milligrams',
    'mcg': 'micrograms',
    'ml': 'milliliters',
    'tab': 'tablet',
    'cap': 'capsule',
    'tsp': 'teaspoon',
    'tbsp': 'tablespoon'
  },
  af: {
    'po': 'per mond',
    'pr': 'per rektum',
    'im': 'intramuskulêr',
    'iv': 'intraveneus',
    'sc': 'subkutaan',
    'qd': 'een keer daagliks',
    'bid': 'twee keer daagliks',
    'tid': 'drie keer daagliks',
    'qid': 'vier keer daagliks',
    'qod': 'elke tweede dag',
    'prn': 'soos benodig',
    'ac': 'voor maaltye',
    'pc': 'na maaltye',
    'hs': 'voor slaaptyd',
    'am': 'oggend',
    'pm': 'aand',
    'mg': 'milligram',
    'mcg': 'mikrogram',
    'ml': 'milliliter',
    'tab': 'tablet',
    'cap': 'kapsule',
    'tsp': 'teelepel',
    'tbsp': 'eetlepel'
  }
}

// Computed properties
const currentAbbreviations = computed(() => 
  prescriptionAbbreviations[locale.value as keyof typeof prescriptionAbbreviations] || prescriptionAbbreviations.en
)

const hasSelectedMedications = computed(() => selectedMedications.value.size > 0)
const hasSelectedPages = computed(() => selectedPages.value.size > 0)

const canProcess = computed(() => 
  capturedImage.value || uploadedFile.value || prescriptionPages.value.length > 0
)

const currentPage = computed(() => 
  prescriptionPages.value[currentPageIndex.value] || null
)

const filteredPages = computed(() => {
  let pages = prescriptionPages.value
  
  if (filterStatus.value !== 'all') {
    pages = pages.filter(page => page.processingStatus === filterStatus.value)
  }
  
  switch (sortBy.value) {
    case 'quality':
      return pages.sort((a, b) => b.quality.overall - a.quality.overall)
    case 'confidence':
      return pages.sort((a, b) => b.confidence - a.confidence)
    case 'pageNumber':
    default:
      return pages.sort((a, b) => a.pageNumber - b.pageNumber)
  }
})

const totalMedications = computed(() => 
  prescriptionPages.value.reduce((total, page) => total + page.extractedMedications.length, 0)
)

const duplicateCount = computed(() => duplicateMedications.value.length)
const interactionCount = computed(() => interactions.value.length)

// Methods
const openScanner = () => {
  isOpen.value = true
  resetState()
  if (props.mode === 'camera' || props.mode === 'both') {
    startCamera()
  }
}

const closeScanner = () => {
  stopCamera()
  clearAutoCaptureTimer()
  isOpen.value = false
  resetState()
  emit('close')
}

const resetState = () => {
  loading.value = false
  processing.value = false
  error.value = ''
  success.value = ''
  capturedImage.value = null
  uploadedFile.value = null
  ocrText.value = ''
  extractedMedications.value = []
  selectedMedications.value.clear()
  selectedPages.value.clear()
  prescriptionPages.value = []
  currentPageIndex.value = 0
  processingStep.value = 'capture'
  imageQuality.value = null
  qualityWarnings.value = []
  ocrConfidence.value = []
  lowConfidenceResults.value = []
  prescriptionMetadata.value = {}
  batchResult.value = null
  duplicateMedications.value = []
  interactions.value = []
  saValidation.value = null
  uploadProgress.value = []
  dragDropZone.value = {
    isActive: false,
    isDragOver: false,
    acceptedFiles: [],
    rejectedFiles: [],
    totalSize: 0
  }
}

// Camera handling
const startCamera = async () => {
  try {
    loading.value = true
    error.value = ''
    
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment',
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      }
    })
    
    stream.value = mediaStream
    if (videoRef.value) {
      videoRef.value.srcObject = mediaStream
      await videoRef.value.play()
    }
  } catch (err) {
    error.value = t('prescriptionScanner.cameraError')
    console.error('Camera error:', err)
  } finally {
    loading.value = false
  }
}

const stopCamera = () => {
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
}

const captureImage = () => {
  if (!videoRef.value || !canvasRef.value) return
  
  const video = videoRef.value
  const canvas = canvasRef.value
  const context = canvas.getContext('2d')
  
  if (!context) return
  
  // Set canvas size to match video
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  // Draw video frame to canvas
  context.drawImage(video, 0, 0)
  
  // Convert to base64
  capturedImage.value = canvas.toDataURL('image/jpeg', 0.8)
  processingStep.value = 'preprocess'
  
  if (props.autoProcess) {
    processImage()
  }
}

// File upload handling
const handleFileUpload = (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  
  if (!file) return
  
  if (!file.type.startsWith('image/')) {
    error.value = t('prescriptionScanner.invalidFileType')
    return
  }
  
  uploadedFile.value = file
  const reader = new FileReader()
  
  reader.onload = (e) => {
    capturedImage.value = e.target?.result as string
    processingStep.value = 'preprocess'
    
    if (props.autoProcess) {
      processImage()
    }
  }
  
  reader.readAsDataURL(file)
}

// Image preprocessing
const preprocessImage = async (imageData: string): Promise<string> => {
  return new Promise((resolve) => {
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      
      if (!ctx) {
        resolve(imageData)
        return
      }
      
      canvas.width = img.width
      canvas.height = img.height
      
      // Apply preprocessing options
      if (preprocessingOptions.enhanceContrast) {
        ctx.filter = `contrast(${preprocessingOptions.contrast}) brightness(${preprocessingOptions.brightness})`
      }
      
      // Apply rotation
      if (preprocessingOptions.rotate !== 0) {
        ctx.save()
        ctx.translate(canvas.width / 2, canvas.height / 2)
        ctx.rotate((preprocessingOptions.rotate * Math.PI) / 180)
        ctx.drawImage(img, -img.width / 2, -img.height / 2)
        ctx.restore()
      } else {
        ctx.drawImage(img, 0, 0)
      }
      
      // Apply sharpening if enabled
      if (preprocessingOptions.sharpen) {
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
        const sharpened = sharpenImage(imageData)
        ctx.putImageData(sharpened, 0, 0)
      }
      
      resolve(canvas.toDataURL('image/jpeg', 0.9))
    }
    
    img.src = imageData
  })
}

const sharpenImage = (imageData: ImageData): ImageData => {
  const data = imageData.data
  const width = imageData.width
  const height = imageData.height
  const newData = new Uint8ClampedArray(data)
  
  const kernel = [
    0, -1, 0,
    -1, 5, -1,
    0, -1, 0
  ]
  
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      for (let c = 0; c < 3; c++) {
        let sum = 0
        for (let ky = -1; ky <= 1; ky++) {
          for (let kx = -1; kx <= 1; kx++) {
            const idx = ((y + ky) * width + (x + kx)) * 4 + c
            const kernelIdx = (ky + 1) * 3 + (kx + 1)
            sum += data[idx] * kernel[kernelIdx]
          }
        }
        const idx = (y * width + x) * 4 + c
        newData[idx] = Math.max(0, Math.min(255, sum))
      }
    }
  }
  
  return new ImageData(newData, width, height)
}

// OCR processing
const processOCR = async (imageData: string): Promise<string> => {
  // This is a placeholder for OCR service integration
  // In a real implementation, you would integrate with services like:
  // - Google Cloud Vision API
  // - Azure Computer Vision
  // - AWS Textract
  // - Tesseract.js (client-side)
  
  try {
    // Simulate OCR processing
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // For demo purposes, return sample prescription text
    const sampleText = locale.value === 'af' 
      ? `VOORSKRIF
      
Medikasie: Paracetamol 500mg
Dosis: 1-2 tablette
Frekvensie: 4-6 uur soos benodig
Instruksies: Neem met water
Dokter: Dr. Smith
Datum: 2024-01-15

Medikasie: Ibuprofen 400mg
Dosis: 1 tablet
Frekvensie: 8 uur
Instruksies: Neem met kos
Dokter: Dr. Smith
Datum: 2024-01-15`
      : `PRESCRIPTION
      
Medication: Paracetamol 500mg
Dosage: 1-2 tablets
Frequency: 4-6 hours as needed
Instructions: Take with water
Doctor: Dr. Smith
Date: 2024-01-15

Medication: Ibuprofen 400mg
Dosage: 1 tablet
Frequency: 8 hours
Instructions: Take with food
Doctor: Dr. Smith
Date: 2024-01-15`
    
    return sampleText
  } catch (err) {
    throw new Error(t('prescriptionScanner.ocrError'))
  }
}

// Prescription parsing
const parsePrescription = (text: string): BulkMedicationEntry[] => {
  const medications: BulkMedicationEntry[] = []
  const lines = text.split('\n').filter(line => line.trim())
  
  let currentMedication: Partial<BulkMedicationEntry> = {}
  
  for (const line of lines) {
    const lowerLine = line.toLowerCase()
    
    // Detect medication name
    if (lowerLine.includes('medication:') || lowerLine.includes('medikasie:')) {
      if (Object.keys(currentMedication).length > 0) {
        medications.push(currentMedication as BulkMedicationEntry)
      }
      currentMedication = {
        name: line.split(':')[1]?.trim() || '',
        strength: '',
        dosage: '',
        frequency: '',
        instructions: ''
      }
    }
    
    // Parse dosage
    else if (lowerLine.includes('dosage:') || lowerLine.includes('dosis:')) {
      currentMedication.dosage = line.split(':')[1]?.trim() || ''
    }
    
    // Parse frequency
    else if (lowerLine.includes('frequency:') || lowerLine.includes('frekvensie:')) {
      currentMedication.frequency = line.split(':')[1]?.trim() || ''
    }
    
    // Parse instructions
    else if (lowerLine.includes('instructions:') || lowerLine.includes('instruksies:')) {
      currentMedication.instructions = line.split(':')[1]?.trim() || ''
    }
    
    // Parse doctor
    else if (lowerLine.includes('doctor:') || lowerLine.includes('dokter:')) {
      currentMedication.prescribingDoctor = line.split(':')[1]?.trim() || ''
    }
    
    // Parse date
    else if (lowerLine.includes('date:') || lowerLine.includes('datum:')) {
      currentMedication.prescriptionNumber = line.split(':')[1]?.trim() || ''
    }
  }
  
  // Add the last medication
  if (Object.keys(currentMedication).length > 0) {
    medications.push(currentMedication as BulkMedicationEntry)
  }
  
  // Expand abbreviations
  return medications.map(med => expandAbbreviations(med))
}

const expandAbbreviations = (medication: BulkMedicationEntry): BulkMedicationEntry => {
  const expanded = { ...medication }
  
  // Expand frequency abbreviations
  if (expanded.frequency) {
    Object.entries(currentAbbreviations.value).forEach(([abbr, full]) => {
      const regex = new RegExp(`\\b${abbr}\\b`, 'gi')
      expanded.frequency = expanded.frequency.replace(regex, full)
    })
  }
  
  // Expand instruction abbreviations
  if (expanded.instructions) {
    Object.entries(currentAbbreviations.value).forEach(([abbr, full]) => {
      const regex = new RegExp(`\\b${abbr}\\b`, 'gi')
      expanded.instructions = expanded.instructions.replace(regex, full)
    })
  }
  
  return expanded
}

// Main processing pipeline
const processImage = async () => {
  if (!capturedImage.value) return
  
  try {
    processing.value = true
    processingStep.value = 'preprocess'
    
    // Step 1: Preprocess image
    const preprocessedImage = await preprocessImage(capturedImage.value)
    
    // Step 2: OCR
    processingStep.value = 'ocr'
    ocrText.value = await processOCR(preprocessedImage)
    
    // Step 3: Parse prescription
    processingStep.value = 'parse'
    extractedMedications.value = parsePrescription(ocrText.value)
    
    // Step 4: Review
    processingStep.value = 'review'
    
    // Select all medications by default
    extractedMedications.value.forEach((_, index) => {
      selectedMedications.value.add(index)
    })
    
    success.value = t('prescriptionScanner.processingComplete', { count: extractedMedications.value.length })
    
  } catch (err) {
    error.value = err instanceof Error ? err.message : t('prescriptionScanner.processingError')
    console.error('Processing error:', err)
  } finally {
    processing.value = false
  }
}

// Review interface
const toggleMedicationSelection = (index: number) => {
  if (selectedMedications.value.has(index)) {
    selectedMedications.value.delete(index)
  } else {
    selectedMedications.value.add(index)
  }
}

const editMedication = (medication: BulkMedicationEntry, index: number) => {
  editingMedication.value = { ...medication }
  showEditModal.value = true
}

const saveEditedMedication = () => {
  if (editingMedication.value) {
    const index = extractedMedications.value.findIndex(med => 
      med.name === editingMedication.value?.name
    )
    if (index !== -1) {
      extractedMedications.value[index] = { ...editingMedication.value }
    }
  }
  showEditModal.value = false
  editingMedication.value = null
}

const addSelectedMedications = () => {
  const selected = Array.from(selectedMedications.value).map(index => 
    extractedMedications.value[index]
  )
  
  if (selected.length === 1) {
    // Single medication - emit as regular add
    const medication = selected[0]
    const formData: MedicationFormData = {
      name: medication.name,
      dosage: medication.dosage,
      frequency: medication.frequency,
      time: '08:00',
      stock: 0,
      minStock: 10,
      instructions: medication.instructions,
      category: '',
      prescribingDoctor: medication.prescribingDoctor,
      prescriptionNumber: medication.prescriptionNumber
    }
    emit('add', formData)
  } else {
    // Multiple medications - emit as bulk add
    emit('bulk-add', selected)
  }
  
  closeScanner()
}

// Multi-page scanning
const addPage = () => {
  const pageId = `page_${Date.now()}_${Math.random()}`
  const newPage: PrescriptionPage = {
    id: pageId,
    imageData: capturedImage.value || '',
    imageUrl: capturedImage.value || '',
    pageNumber: prescriptionPages.value.length + 1,
    ocrText: ocrText.value,
    extractedMedications: extractedMedications.value.map(med => ({
      ...med,
      quantity: 1,
      refills: 0
    })),
    processingStatus: 'pending',
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
    confidence: 0,
    lowConfidenceResults: [],
    metadata: {},
    interactions: [],
    saValidation: undefined
  }
  
  prescriptionPages.value.push(newPage)
  currentPageIndex.value = prescriptionPages.value.length - 1
  selectedPages.value.add(prescriptionPages.value.length - 1)
  success.value = t('prescriptionScanner.pageAdded')
}

const removePage = (index: number) => {
  if (prescriptionPages.value.length === 1) {
    error.value = t('prescriptionScanner.lastPageWarning')
    return
  }
  prescriptionPages.value.splice(index, 1)
  if (currentPageIndex.value === index) {
    currentPageIndex.value = 0
  } else if (currentPageIndex.value > index) {
    currentPageIndex.value--
  }
  selectedPages.value.delete(index)
  success.value = t('prescriptionScanner.pageRemoved')
}

const selectAllPages = () => {
  selectedPages.value.clear()
  for (let i = 0; i < prescriptionPages.value.length; i++) {
    selectedPages.value.add(i)
  }
}

const deselectAllPages = () => {
  selectedPages.value.clear()
}

const togglePageSelection = (index: number) => {
  if (selectedPages.value.has(index)) {
    selectedPages.value.delete(index)
  } else {
    selectedPages.value.add(index)
  }
}

const processSelectedPages = async () => {
  if (selectedPages.value.size === 0) {
    error.value = t('prescriptionScanner.selectPagesWarning')
    return
  }

  processing.value = true
  const selectedPageNumbers = Array.from(selectedPages.value).map(i => i + 1)
  const selectedPageImages = selectedPageNumbers.map(i => prescriptionPages.value[i - 1].imageUrl)

  try {
    const result = await Promise.all(selectedPageImages.map(async (imageUrl, index) => {
      const page = prescriptionPages.value[selectedPageNumbers[index] - 1]
      if (!imageUrl) throw new Error('No image URL found')
      
      const imageData = await fetch(imageUrl).then(res => res.blob()).then(blob => URL.createObjectURL(blob))
      const preprocessedImage = await preprocessImage(imageData)
      const ocrText = await processOCR(preprocessedImage)
      const parsedMedications = parsePrescription(ocrText)

      // Simulate quality and confidence
      const quality = {
        brightness: 85,
        contrast: 90,
        sharpness: 80,
        noise: 75,
        blur: 95,
        overall: 85,
        isValid: true,
        warnings: []
      }
      const confidence = 92
      const lowConfidenceResults: OCRConfidence[] = [] // Placeholder

      return {
        id: page.id,
        imageData: page.imageData,
        imageUrl: page.imageUrl,
        pageNumber: page.pageNumber,
        ocrText: ocrText,
        extractedMedications: parsedMedications.map(med => ({
          ...med,
          quantity: 1,
          refills: 0
        })),
        processingStatus: 'completed' as const,
        quality: quality,
        confidence: confidence,
        lowConfidenceResults: lowConfidenceResults,
        metadata: {},
        interactions: [],
        saValidation: undefined
      }
    }))

    prescriptionPages.value = result
    batchResult.value = {
      totalPages: selectedPages.value.size,
      successfulPages: selectedPages.value.size,
      failedPages: 0,
      totalMedications: totalMedications.value,
      duplicateMedications: duplicateMedications.value,
      interactions: interactions.value,
      processingTime: 0,
      pages: result,
      metadata: prescriptionMetadata.value,
      exportData: {
        format: 'json',
        data: result,
        filename: `prescription_${Date.now()}.json`,
        timestamp: new Date().toISOString()
      },
      saValidation: saValidation.value || undefined
    }
    success.value = t('prescriptionScanner.batchProcessingComplete', { count: totalMedications.value })
    emit('batch-result', batchResult.value)

  } catch (err) {
    error.value = err instanceof Error ? err.message : t('prescriptionScanner.batchProcessingError')
    console.error('Batch processing error:', err)
  } finally {
    processing.value = false
  }
}

// Auto-capture
const startAutoCapture = () => {
  if (autoCaptureTimer.value) {
    clearAutoCaptureTimer()
    return
  }
  captureCountdown.value = props.captureDelay
  autoCaptureTimer.value = window.setInterval(() => {
    if (captureCountdown.value > 0) {
      captureCountdown.value--
    } else {
      captureImage()
      captureCountdown.value = props.captureDelay
    }
  }, 1000)
}

const clearAutoCaptureTimer = () => {
  if (autoCaptureTimer.value) {
    window.clearInterval(autoCaptureTimer.value)
    autoCaptureTimer.value = null
  }
}

// South African prescription validation
const validateSA = async () => {
  if (!saValidation.value) {
    error.value = t('prescriptionScanner.saValidationError')
    return
  }

  processing.value = true
  try {
    const result = await Promise.all(prescriptionPages.value.map(async page => {
      if (!page.imageUrl) throw new Error('No image URL found')
      
      const imageData = await fetch(page.imageUrl).then(res => res.blob()).then(blob => URL.createObjectURL(blob))
      const preprocessedImage = await preprocessImage(imageData)
      const ocrText = await processOCR(preprocessedImage)
      const parsedMedications = parsePrescription(ocrText)

      const saValidationResult = await new Promise<SouthAfricanPrescriptionValidation>(resolve => {
        // Simulate SA validation
        setTimeout(() => {
          const warnings: string[] = []
          if (parsedMedications.some(med => med.name.toLowerCase().includes('paracetamol'))) {
            warnings.push(t('prescriptionScanner.saWarningParacetamol'))
          }
          if (parsedMedications.some(med => med.name.toLowerCase().includes('ibuprofen'))) {
            warnings.push(t('prescriptionScanner.saWarningIbuprofen'))
          }
          resolve({
            isValid: warnings.length === 0,
            errors: [],
            warnings: warnings,
            requiredFields: {
              doctorName: true,
              doctorLicense: true,
              prescriptionDate: true,
              patientName: true,
              medicationDetails: true
            },
            formatCompliance: {
              isStandardFormat: true,
              hasRequiredSections: true,
              hasProperDosage: true,
              hasFrequency: true
            },
            details: {
              totalMedications: parsedMedications.length,
              warnings: warnings.length,
              specificWarnings: warnings.map(w => ({
                name: 'SA Warning',
                message: w
              }))
            }
          })
        }, 1000)
      })

      return {
        id: page.id,
        imageData: page.imageData,
        imageUrl: page.imageUrl,
        pageNumber: page.pageNumber,
        ocrText: ocrText,
        extractedMedications: parsedMedications.map(med => ({
          ...med,
          quantity: 1,
          refills: 0
        })),
        processingStatus: 'completed' as const,
        quality: page.quality,
        confidence: page.confidence,
        lowConfidenceResults: page.lowConfidenceResults || [],
        metadata: page.metadata || {},
        interactions: page.interactions || [],
        saValidation: saValidationResult
      }
    }))

    prescriptionPages.value = result
    saValidation.value = {
      isValid: true,
      errors: [],
      warnings: [],
      requiredFields: {
        doctorName: true,
        doctorLicense: true,
        prescriptionDate: true,
        patientName: true,
        medicationDetails: true
      },
      formatCompliance: {
        isStandardFormat: true,
        hasRequiredSections: true,
        hasProperDosage: true,
        hasFrequency: true
      },
      details: {
        totalMedications: totalMedications.value,
        warnings: 0,
        specificWarnings: []
      }
    }
    success.value = t('prescriptionScanner.saValidationComplete')
    emit('batch-result', {
      totalPages: prescriptionPages.value.length,
      successfulPages: prescriptionPages.value.length,
      failedPages: 0,
      totalMedications: totalMedications.value,
      duplicateMedications: duplicateMedications.value,
      interactions: interactions.value,
      processingTime: 0,
      pages: result,
      metadata: prescriptionMetadata.value,
      exportData: {
        format: 'json',
        data: result,
        filename: `prescription_${Date.now()}.json`,
        timestamp: new Date().toISOString()
      },
      saValidation: saValidation.value
    })

  } catch (err) {
    error.value = err instanceof Error ? err.message : t('prescriptionScanner.saValidationError')
    console.error('SA validation error:', err)
  } finally {
    processing.value = false
  }
}

// Drag and drop
const handleDragOver = (event: DragEvent) => {
  event.preventDefault()
  dragDropZone.value.isDragOver = true
}

const handleDragLeave = () => {
  dragDropZone.value.isDragOver = false
}

const handleDrop = async (event: DragEvent) => {
  event.preventDefault()
  dragDropZone.value.isDragOver = false

  const files = Array.from(event.dataTransfer?.files || [])
  if (files.length === 0) return

  dragDropZone.value.acceptedFiles = files
  dragDropZone.value.rejectedFiles = []
  dragDropZone.value.totalSize = files.reduce((sum, file) => sum + file.size, 0)

  if (uploadedFile.value) {
    // If a file is already uploaded, clear it
    uploadedFile.value = null
    success.value = t('prescriptionScanner.fileCleared')
  }

  if (prescriptionPages.value.length === 0) {
    // If no pages, start processing
    await processImage()
  } else {
    // If pages exist, add them
    files.forEach(file => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const imageUrl = e.target?.result as string
        prescriptionPages.value.push({
          id: `page_${Date.now()}_${Math.random()}`,
          imageData: imageUrl,
          imageUrl: imageUrl,
          pageNumber: prescriptionPages.value.length + 1,
          ocrText: '',
          extractedMedications: [], // Will be populated by OCR
          processingStatus: 'pending',
          quality: { brightness: 0, contrast: 0, sharpness: 0, noise: 0, blur: 0, overall: 0, isValid: false, warnings: [] },
          confidence: 0,
          lowConfidenceResults: [],
          metadata: {},
          interactions: [],
          saValidation: undefined
        })
        currentPageIndex.value = prescriptionPages.value.length - 1
        selectedPages.value.add(prescriptionPages.value.length - 1)
      }
      reader.readAsDataURL(file)
    })
    success.value = t('prescriptionScanner.filesAdded', { count: files.length })
  }
}

const handleFileRejection = (file: File) => {
  dragDropZone.value.rejectedFiles.push(file)
  error.value = t('prescriptionScanner.fileRejected', { name: file.name })
}

// Lifecycle
onMounted(() => {
  // Component mounted
})

onUnmounted(() => {
  stopCamera()
  clearAutoCaptureTimer()
})
</script>

<template>
  <div>
    <!-- Scanner Button -->
    <button 
      @click="openScanner"
      class="btn btn-primary gap-2"
      :disabled="loading"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V6a1 1 0 00-1-1H5a1 1 0 00-1 1v1a1 1 0 001 1zm12 0h2a1 1 0 001-1V6a1 1 0 00-1-1h-2a1 1 0 00-1 1v1a1 1 0 001 1zM5 20h2a1 1 0 001-1v-1a1 1 0 00-1-1H5a1 1 0 00-1 1v1a1 1 0 001 1z"></path>
      </svg>
      {{ t('prescriptionScanner.scanPrescription') }}
    </button>

    <!-- Scanner Modal -->
    <div v-if="isOpen" class="modal modal-open">
      <div class="modal-box w-11/12 max-w-4xl">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-bold text-lg">
            {{ t('prescriptionScanner.title') }}
          </h3>
          <button @click="closeScanner" class="btn btn-sm btn-circle btn-ghost">
            ✕
          </button>
        </div>

        <!-- Progress Steps -->
        <div class="steps steps-horizontal mb-6">
          <div 
            class="step" 
            :class="{ 'step-primary': processingStep === 'capture' || processingStep === 'preprocess' || processingStep === 'ocr' || processingStep === 'parse' || processingStep === 'review' }"
          >
            {{ t('prescriptionScanner.stepCapture') }}
          </div>
          <div 
            class="step" 
            :class="{ 'step-primary': processingStep === 'preprocess' || processingStep === 'ocr' || processingStep === 'parse' || processingStep === 'review' }"
          >
            {{ t('prescriptionScanner.stepProcess') }}
          </div>
          <div 
            class="step" 
            :class="{ 'step-primary': processingStep === 'ocr' || processingStep === 'parse' || processingStep === 'review' }"
          >
            {{ t('prescriptionScanner.stepExtract') }}
          </div>
          <div 
            class="step" 
            :class="{ 'step-primary': processingStep === 'parse' || processingStep === 'review' }"
          >
            {{ t('prescriptionScanner.stepParse') }}
          </div>
          <div 
            class="step" 
            :class="{ 'step-primary': processingStep === 'review' }"
          >
            {{ t('prescriptionScanner.stepReview') }}
          </div>
        </div>

        <!-- Error/Success Messages -->
        <div v-if="error" class="alert alert-error mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span>{{ error }}</span>
        </div>

        <div v-if="success" class="alert alert-success mb-4">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
          </svg>
          <span>{{ success }}</span>
        </div>

        <!-- Capture Section -->
        <div v-if="processingStep === 'capture'" class="space-y-4">
          <!-- Camera Mode -->
          <div v-if="mode === 'camera' || mode === 'both'" class="card bg-base-200">
            <div class="card-body">
              <h4 class="card-title">{{ t('prescriptionScanner.cameraMode') }}</h4>
              
              <div class="relative">
                <video 
                  ref="videoRef"
                  class="w-full max-h-96 object-cover rounded-lg"
                  autoplay
                  muted
                  playsinline
                ></video>
                
                <canvas ref="canvasRef" class="hidden"></canvas>
                
                <div v-if="loading" class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 rounded-lg">
                  <span class="loading loading-spinner loading-lg"></span>
                </div>
              </div>
              
              <div class="flex gap-2 mt-4">
                <button 
                  @click="captureImage"
                  class="btn btn-primary"
                  :disabled="loading || !stream"
                >
                  {{ t('prescriptionScanner.capture') }}
                </button>
                <button 
                  @click="startCamera"
                  class="btn btn-outline"
                  :disabled="loading"
                >
                  {{ t('prescriptionScanner.retryCamera') }}
                </button>
              </div>
            </div>
          </div>

          <!-- File Upload Mode -->
          <div v-if="mode === 'upload' || mode === 'both'" class="card bg-base-200">
            <div class="card-body">
              <h4 class="card-title">{{ t('prescriptionScanner.uploadMode') }}</h4>
              
              <input
                ref="fileInputRef"
                type="file"
                accept="image/*"
                @change="handleFileUpload"
                class="file-input file-input-bordered w-full"
              />
              
              <p class="text-sm text-base-content/70 mt-2">
                {{ t('prescriptionScanner.uploadHint') }}
              </p>
            </div>
          </div>
        </div>

        <!-- Preprocessing Section -->
        <div v-if="processingStep === 'preprocess'" class="space-y-4">
          <div class="card bg-base-200">
            <div class="card-body">
              <h4 class="card-title">{{ t('prescriptionScanner.preprocessing') }}</h4>
              
              <div class="grid grid-cols-2 gap-4">
                <div class="form-control">
                  <label class="label cursor-pointer">
                    <span class="label-text">{{ t('prescriptionScanner.enhanceContrast') }}</span>
                    <input 
                      v-model="preprocessingOptions.enhanceContrast"
                      type="checkbox" 
                      class="checkbox"
                    />
                  </label>
                </div>
                
                <div class="form-control">
                  <label class="label cursor-pointer">
                    <span class="label-text">{{ t('prescriptionScanner.removeNoise') }}</span>
                    <input 
                      v-model="preprocessingOptions.removeNoise"
                      type="checkbox" 
                      class="checkbox"
                    />
                  </label>
                </div>
                
                <div class="form-control">
                  <label class="label cursor-pointer">
                    <span class="label-text">{{ t('prescriptionScanner.sharpen') }}</span>
                    <input 
                      v-model="preprocessingOptions.sharpen"
                      type="checkbox" 
                      class="checkbox"
                    />
                  </label>
                </div>
                
                <div class="form-control">
                  <label class="label-text">{{ t('prescriptionScanner.rotate') }}</label>
                  <select v-model="preprocessingOptions.rotate" class="select select-bordered">
                    <option value="0">0°</option>
                    <option value="90">90°</option>
                    <option value="180">180°</option>
                    <option value="270">270°</option>
                  </select>
                </div>
              </div>
              
              <div class="flex gap-2 mt-4">
                <button 
                  @click="processImage"
                  class="btn btn-primary"
                  :disabled="processing"
                >
                  {{ t('prescriptionScanner.processImage') }}
                </button>
                <button 
                  @click="processingStep = 'capture'"
                  class="btn btn-outline"
                >
                  {{ t('prescriptionScanner.back') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- OCR Processing Section -->
        <div v-if="processingStep === 'ocr'" class="text-center py-8">
          <span class="loading loading-spinner loading-lg"></span>
          <p class="mt-4">{{ t('prescriptionScanner.extractingText') }}</p>
        </div>

        <!-- Parsing Section -->
        <div v-if="processingStep === 'parse'" class="text-center py-8">
          <span class="loading loading-spinner loading-lg"></span>
          <p class="mt-4">{{ t('prescriptionScanner.parsingMedications') }}</p>
        </div>

        <!-- Review Section -->
        <div v-if="processingStep === 'review'" class="space-y-4">
          <div class="card bg-base-200">
            <div class="card-body">
              <h4 class="card-title">{{ t('prescriptionScanner.reviewTitle') }}</h4>
              
              <div v-if="extractedMedications.length === 0" class="text-center py-8">
                <p class="text-base-content/70">{{ t('prescriptionScanner.noMedicationsFound') }}</p>
                <button 
                  @click="processingStep = 'capture'"
                  class="btn btn-outline mt-4"
                >
                  {{ t('prescriptionScanner.tryAgain') }}
                </button>
              </div>
              
              <div v-else class="space-y-4">
                <!-- OCR Text Preview -->
                <div class="collapse collapse-arrow bg-base-100">
                  <input type="checkbox" />
                  <div class="collapse-title font-medium">
                    {{ t('prescriptionScanner.ocrTextPreview') }}
                  </div>
                  <div class="collapse-content">
                    <pre class="text-sm whitespace-pre-wrap">{{ ocrText }}</pre>
                  </div>
                </div>
                
                <!-- Extracted Medications -->
                <div class="space-y-2">
                  <div class="flex justify-between items-center">
                    <h5 class="font-medium">{{ t('prescriptionScanner.extractedMedications') }}</h5>
                    <div class="flex gap-2">
                      <button 
                        @click="selectedMedications.clear()"
                        class="btn btn-sm btn-outline"
                      >
                        {{ t('prescriptionScanner.deselectAll') }}
                      </button>
                      <button 
                        @click="extractedMedications.forEach((_, index) => selectedMedications.add(index))"
                        class="btn btn-sm btn-outline"
                      >
                        {{ t('prescriptionScanner.selectAll') }}
                      </button>
                    </div>
                  </div>
                  
                  <div class="space-y-2 max-h-96 overflow-y-auto">
                    <div 
                      v-for="(medication, index) in extractedMedications"
                      :key="index"
                      class="card bg-base-100 border-2"
                      :class="{ 'border-primary': selectedMedications.has(index) }"
                    >
                      <div class="card-body p-4">
                        <div class="flex items-start gap-3">
                          <input 
                            type="checkbox"
                            :checked="selectedMedications.has(index)"
                            @change="toggleMedicationSelection(index)"
                            class="checkbox checkbox-primary mt-1"
                          />
                          
                          <div class="flex-1">
                            <h6 class="font-medium">{{ medication.name }}</h6>
                            <div class="text-sm text-base-content/70 space-y-1">
                              <p><strong>{{ t('medication.dosage') }}:</strong> {{ medication.dosage }}</p>
                              <p><strong>{{ t('prescriptionScanner.frequency') }}:</strong> {{ medication.frequency }}</p>
                              <p v-if="medication.instructions"><strong>{{ t('prescriptionScanner.instructions') }}:</strong> {{ medication.instructions }}</p>
                              <p v-if="medication.prescribingDoctor"><strong>{{ t('prescriptionScanner.doctor') }}:</strong> {{ medication.prescribingDoctor }}</p>
                            </div>
                          </div>
                          
                          <button 
                            @click="editMedication(medication, index)"
                            class="btn btn-sm btn-outline"
                          >
                            {{ t('prescriptionScanner.edit') }}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- Action Buttons -->
                <div class="flex gap-2 justify-end">
                  <button 
                    @click="processingStep = 'capture'"
                    class="btn btn-outline"
                  >
                    {{ t('prescriptionScanner.scanAnother') }}
                  </button>
                  <button 
                    @click="addSelectedMedications"
                    class="btn btn-primary"
                    :disabled="!hasSelectedMedications"
                  >
                    {{ t('prescriptionScanner.addSelected', { count: selectedMedications.size }) }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Medication Modal -->
    <div v-if="showEditModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">{{ t('prescriptionScanner.editMedication') }}</h3>
        
        <div v-if="editingMedication" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('medication.name') }}</span>
            </label>
            <input 
              v-model="editingMedication.name"
              type="text" 
              class="input input-bordered"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('medication.dosage') }}</span>
            </label>
            <input 
              v-model="editingMedication.dosage"
              type="text" 
              class="input input-bordered"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('prescriptionScanner.frequency') }}</span>
            </label>
            <input 
              v-model="editingMedication.frequency"
              type="text" 
              class="input input-bordered"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('prescriptionScanner.instructions') }}</span>
            </label>
            <textarea 
              v-model="editingMedication.instructions"
              class="textarea textarea-bordered"
              rows="3"
            ></textarea>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('prescriptionScanner.doctor') }}</span>
            </label>
            <input 
              v-model="editingMedication.prescribingDoctor"
              type="text" 
              class="input input-bordered"
            />
          </div>
        </div>
        
        <div class="modal-action">
          <button @click="showEditModal = false" class="btn btn-outline">
            {{ t('prescriptionScanner.cancel') }}
          </button>
          <button @click="saveEditedMedication" class="btn btn-primary">
            {{ t('prescriptionScanner.save') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal {
  z-index: 1000;
}

.steps .step {
  @apply text-sm;
}

.steps .step-primary {
  @apply text-primary;
}

/* Custom scrollbar for medication list */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: hsl(var(--b2));
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: hsl(var(--bc) / 0.3);
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--bc) / 0.5);
}
</style>