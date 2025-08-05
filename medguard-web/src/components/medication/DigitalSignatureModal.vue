<template>
  <div class="modal modal-open">
    <div class="modal-box max-w-md">
      <h3 class="font-bold text-lg mb-4">
        <i class="fas fa-signature text-primary mr-2"></i>
        {{ $t('signature.title', 'Digital Signature') }}
      </h3>
      
      <div class="space-y-4">
        <!-- Signer Information -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">{{ $t('signature.signerName', 'Full Name') }}</span>
          </label>
          <input 
            v-model="signerName"
            type="text"
            class="input input-bordered"
            :placeholder="$t('signature.signerNamePlaceholder', 'Enter your full name')"
            required
          />
        </div>
        
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">{{ $t('signature.credentials', 'Professional Credentials') }}</span>
          </label>
          <input 
            v-model="credentials"
            type="text"
            class="input input-bordered"
            :placeholder="$t('signature.credentialsPlaceholder', 'e.g., MD, RN, PharmD')"
          />
        </div>
        
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">{{ $t('signature.license', 'License Number') }}</span>
          </label>
          <input 
            v-model="licenseNumber"
            type="text"
            class="input input-bordered"
            :placeholder="$t('signature.licensePlaceholder', 'Professional license number')"
          />
        </div>
        
        <!-- Signature Canvas -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">{{ $t('signature.signature', 'Digital Signature') }}</span>
          </label>
          <div class="border-2 border-dashed border-base-300 rounded-lg p-4">
            <canvas
              ref="signatureCanvas"
              class="w-full h-32 bg-base-100 border border-base-300 rounded cursor-crosshair"
              @mousedown="startDrawing"
              @mousemove="draw"
              @mouseup="stopDrawing"
              @mouseleave="stopDrawing"
              @touchstart="startDrawingTouch"
              @touchmove="drawTouch"
              @touchend="stopDrawing"
            ></canvas>
            <div class="flex justify-between items-center mt-2">
              <button 
                @click="clearSignature"
                class="btn btn-ghost btn-sm"
                :disabled="!hasSignature"
              >
                <i class="fas fa-eraser mr-1"></i>
                {{ $t('signature.clear', 'Clear') }}
              </button>
              <span class="text-xs text-base-content/60">
                {{ $t('signature.signatureHint', 'Sign above to approve prescription') }}
              </span>
            </div>
          </div>
        </div>
        
        <!-- Terms and Conditions -->
        <div class="form-control">
          <label class="label cursor-pointer">
            <span class="label-text">
              {{ $t('signature.agreeTerms', 'I agree to the terms and conditions') }}
            </span>
            <input 
              v-model="agreeToTerms"
              type="checkbox" 
              class="checkbox checkbox-primary"
              required
            />
          </label>
        </div>
        
        <!-- Compliance Statement -->
        <div class="alert alert-info">
          <i class="fas fa-info-circle"></i>
          <div>
            <h4 class="font-bold">{{ $t('signature.complianceTitle', 'Compliance Statement') }}</h4>
            <p class="text-sm">
              {{ $t('signature.complianceText', 'By signing this prescription, I confirm that I have reviewed all medications, interactions, and compliance requirements in accordance with South African healthcare regulations.') }}
            </p>
          </div>
        </div>
      </div>
      
      <!-- Action Buttons -->
      <div class="modal-action">
        <button 
          @click="handleClose"
          class="btn btn-ghost"
        >
          {{ $t('signature.cancel', 'Cancel') }}
        </button>
        <button 
          @click="handleSign"
          class="btn btn-primary"
          :disabled="!canSign"
        >
          <i class="fas fa-signature mr-2"></i>
          {{ $t('signature.sign', 'Sign & Approve') }}
        </button>
      </div>
    </div>
    
    <!-- Backdrop -->
    <div class="modal-backdrop" @click="handleClose"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'

interface Emits {
  (e: 'close'): void
  (e: 'sign', signature: {
    signerName: string
    credentials: string
    licenseNumber: string
    timestamp: string
    signature: string
  }): void
}

const emit = defineEmits<Emits>()

const { t } = useI18n()

// Reactive state
const signerName = ref('')
const credentials = ref('')
const licenseNumber = ref('')
const agreeToTerms = ref(false)
const hasSignature = ref(false)

// Canvas drawing state
const signatureCanvas = ref<HTMLCanvasElement>()
const isDrawing = ref(false)
const lastX = ref(0)
const lastY = ref(0)

// Computed properties
const canSign = computed(() => {
  return signerName.value.trim() && 
         agreeToTerms.value && 
         hasSignature.value
})

// Canvas drawing functions
const startDrawing = (event: MouseEvent) => {
  isDrawing.value = true
  const rect = signatureCanvas.value!.getBoundingClientRect()
  lastX.value = event.clientX - rect.left
  lastY.value = event.clientY - rect.top
}

const draw = (event: MouseEvent) => {
  if (!isDrawing.value) return
  
  const canvas = signatureCanvas.value!
  const ctx = canvas.getContext('2d')!
  const rect = canvas.getBoundingClientRect()
  const currentX = event.clientX - rect.left
  const currentY = event.clientY - rect.top
  
  ctx.beginPath()
  ctx.moveTo(lastX.value, lastY.value)
  ctx.lineTo(currentX, currentY)
  ctx.stroke()
  
  lastX.value = currentX
  lastY.value = currentY
  hasSignature.value = true
}

const stopDrawing = () => {
  isDrawing.value = false
}

// Touch support for mobile devices
const startDrawingTouch = (event: TouchEvent) => {
  event.preventDefault()
  const touch = event.touches[0]
  const mouseEvent = new MouseEvent('mousedown', {
    clientX: touch.clientX,
    clientY: touch.clientY
  })
  startDrawing(mouseEvent)
}

const drawTouch = (event: TouchEvent) => {
  event.preventDefault()
  const touch = event.touches[0]
  const mouseEvent = new MouseEvent('mousemove', {
    clientX: touch.clientX,
    clientY: touch.clientY
  })
  draw(mouseEvent)
}

const clearSignature = () => {
  const canvas = signatureCanvas.value!
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  hasSignature.value = false
}

// Initialize canvas
onMounted(async () => {
  await nextTick()
  if (signatureCanvas.value) {
    const canvas = signatureCanvas.value
    const ctx = canvas.getContext('2d')!
    
    // Set canvas size
    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight
    
    // Configure drawing style
    ctx.strokeStyle = '#2563EB' // Primary blue color
    ctx.lineWidth = 2
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
  }
})

// Event handlers
const handleClose = () => {
  emit('close')
}

const handleSign = () => {
  if (!canSign.value) return
  
  const canvas = signatureCanvas.value!
  const signatureData = canvas.toDataURL('image/png')
  
  const signature = {
    signerName: signerName.value,
    credentials: credentials.value,
    licenseNumber: licenseNumber.value,
    timestamp: new Date().toISOString(),
    signature: signatureData
  }
  
  emit('sign', signature)
}
</script>

<style scoped>
.modal-backdrop {
  @apply fixed inset-0 bg-black bg-opacity-50;
}

canvas {
  touch-action: none;
}

.checkbox {
  @apply transition-all duration-200;
}

.btn:disabled {
  @apply opacity-50 cursor-not-allowed;
}
</style> 