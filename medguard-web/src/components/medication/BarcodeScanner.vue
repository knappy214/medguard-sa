<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const emit = defineEmits<{
  close: []
  scan: [barcode: string]
}>()

const videoRef = ref<HTMLVideoElement>()
const canvasRef = ref<HTMLCanvasElement>()
const scanning = ref(false)
const scannedBarcode = ref('')
const error = ref('')
const manualBarcode = ref('')

// Mock barcode scanner - in real app, you'd use a library like QuaggaJS or ZXing
const startScanning = async () => {
  try {
    scanning.value = true
    error.value = ''
    
    // Check if camera is available
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error(t('dashboard.cameraNotSupported'))
    }
    
    const stream = await navigator.mediaDevices.getUserMedia({ 
      video: { 
        facingMode: 'environment',
        width: { ideal: 1280 },
        height: { ideal: 720 }
      } 
    })
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      videoRef.value.play()
    }
    
    // Simulate barcode detection (in real app, this would be actual barcode detection)
    setTimeout(() => {
      // Mock successful scan
      const mockBarcodes = ['1234567890123', '9876543210987', '4567891234567']
      const randomBarcode = mockBarcodes[Math.floor(Math.random() * mockBarcodes.length)]
      handleBarcodeDetected(randomBarcode)
    }, 3000)
    
  } catch (err) {
    error.value = (err as Error).message
    scanning.value = false
  }
}

const stopScanning = () => {
  scanning.value = false
  if (videoRef.value && videoRef.value.srcObject) {
    const stream = videoRef.value.srcObject as MediaStream
    stream.getTracks().forEach(track => track.stop())
    videoRef.value.srcObject = null
  }
}

const handleBarcodeDetected = (barcode: string) => {
  scannedBarcode.value = barcode
  stopScanning()
  
  // Auto-close after showing the result
  setTimeout(() => {
    emit('scan', barcode)
  }, 2000)
}

const handleManualSubmit = () => {
  if (manualBarcode.value.trim()) {
    emit('scan', manualBarcode.value.trim())
  }
}

const retryScanning = () => {
  scannedBarcode.value = ''
  error.value = ''
  startScanning()
}

onMounted(() => {
  startScanning()
})

onUnmounted(() => {
  stopScanning()
})
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-2xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V6a1 1 0 00-1-1H5a1 1 0 00-1 1v1a1 1 0 001 1zm12 0h2a1 1 0 001-1V6a1 1 0 00-1-1h-2a1 1 0 00-1 1v1a1 1 0 001 1zM5 20h2a1 1 0 001-1v-1a1 1 0 00-1-1H5a1 1 0 00-1 1v1a1 1 0 001 1z" />
          </svg>
          {{ t('dashboard.barcodeScanner') }}
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Scanner Interface -->
      <div class="space-y-6">
        <!-- Camera View -->
        <div class="relative">
          <div class="bg-black rounded-lg overflow-hidden aspect-video">
            <video 
              ref="videoRef"
              class="w-full h-full object-cover"
              autoplay
              muted
              playsinline
            ></video>
            
            <!-- Scanning Overlay -->
            <div v-if="scanning && !scannedBarcode" class="absolute inset-0 flex items-center justify-center">
              <div class="relative">
                <!-- Scanning Frame -->
                <div class="border-2 border-primary rounded-lg p-8">
                  <div class="w-64 h-32 border-2 border-dashed border-primary rounded"></div>
                </div>
                
                <!-- Scanning Animation -->
                <div class="absolute top-0 left-0 w-full h-1 bg-primary animate-pulse"></div>
                
                <!-- Instructions -->
                <div class="absolute -bottom-12 left-1/2 transform -translate-x-1/2 text-center">
                  <p class="text-white text-sm font-medium">{{ t('dashboard.positionBarcode') }}</p>
                  <p class="text-gray-300 text-xs">{{ t('dashboard.holdSteady') }}</p>
                </div>
              </div>
            </div>
            
            <!-- Success State -->
            <div v-if="scannedBarcode" class="absolute inset-0 flex items-center justify-center bg-black/50">
              <div class="text-center text-white">
                <svg class="w-16 h-16 mx-auto mb-4 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                <h3 class="text-xl font-bold mb-2">{{ t('dashboard.barcodeDetected') }}</h3>
                <p class="text-lg font-mono">{{ scannedBarcode }}</p>
                <p class="text-sm text-gray-300 mt-2">{{ t('dashboard.lookingUpMedication') }}</p>
              </div>
            </div>
          </div>
          
          <!-- Camera Controls -->
          <div class="flex justify-center mt-4 space-x-4">
            <button 
              v-if="!scanning && !scannedBarcode"
              @click="retryScanning"
              class="btn btn-primary gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              {{ t('dashboard.retryScan') }}
            </button>
            
            <button 
              v-if="scanning"
              @click="stopScanning"
              class="btn btn-outline gap-2"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              {{ t('dashboard.stopScan') }}
            </button>
          </div>
        </div>

        <!-- Error State -->
        <div v-if="error" class="alert alert-error">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="font-bold">{{ t('dashboard.scanError') }}</h3>
            <div class="text-sm">{{ error }}</div>
          </div>
        </div>

        <!-- Manual Entry -->
        <div class="card bg-base-200">
          <div class="card-body">
            <h4 class="card-title text-high-contrast">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              {{ t('dashboard.manualEntry') }}
            </h4>
            <p class="text-sm text-secondary-high-contrast mb-4">
              {{ t('dashboard.manualEntryDescription') }}
            </p>
            
            <div class="flex gap-2">
              <input 
                v-model="manualBarcode"
                type="text"
                :placeholder="t('dashboard.enterBarcode')"
                class="input input-bordered flex-1"
                @keyup.enter="handleManualSubmit"
              />
              <button 
                @click="handleManualSubmit"
                class="btn btn-primary"
                :disabled="!manualBarcode.trim()"
              >
                {{ t('dashboard.lookup') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Help Information -->
        <div class="alert alert-info">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="font-bold">{{ t('dashboard.scanningTips') }}</h3>
            <ul class="text-sm mt-2 space-y-1">
              <li>• {{ t('dashboard.tipGoodLighting') }}</li>
              <li>• {{ t('dashboard.tipHoldSteady') }}</li>
              <li>• {{ t('dashboard.tipCleanBarcode') }}</li>
              <li>• {{ t('dashboard.tipTryManualEntry') }}</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="modal-action">
        <button @click="emit('close')" class="btn">{{ t('common.cancel') }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-box {
  max-height: 90vh;
  overflow-y: auto;
}

/* Scanning animation */
@keyframes scan {
  0% { transform: translateY(0); }
  50% { transform: translateY(100%); }
  100% { transform: translateY(0); }
}

.animate-scan {
  animation: scan 2s ease-in-out infinite;
}

/* Video aspect ratio */
.aspect-video {
  aspect-ratio: 16 / 9;
}
</style> 