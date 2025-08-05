<template>
  <div class="mobile-camera-demo">
    <div class="demo-header">
      <h2 class="text-2xl font-bold mb-4">{{ t('mobileCameraDemo.title') }}</h2>
      <p class="text-gray-600 mb-6">{{ t('mobileCameraDemo.description') }}</p>
    </div>

    <!-- Feature Overview -->
    <div class="features-grid mb-8">
      <div 
        v-for="feature in features" 
        :key="feature.id"
        class="feature-card"
        :class="{ 'active': activeFeature === feature.id }"
        @click="activeFeature = feature.id"
      >
        <div class="feature-icon">
          <component :is="feature.icon" class="w-6 h-6" />
        </div>
        <h3 class="feature-title">{{ feature.title }}</h3>
        <p class="feature-description">{{ feature.description }}</p>
      </div>
    </div>

    <!-- Camera Interface Demo -->
    <div class="demo-section">
      <div class="demo-controls mb-4">
        <button 
          @click="showCamera = true"
          class="btn btn-primary"
          :disabled="showCamera"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {{ t('mobileCameraDemo.openCamera') }}
        </button>

        <button 
          @click="showSettings = true"
          class="btn btn-outline"
        >
          <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          {{ t('mobileCameraDemo.settings') }}
        </button>
      </div>

      <!-- Demo Results -->
      <div v-if="capturedImages.length > 0" class="demo-results">
        <h3 class="text-lg font-semibold mb-4">{{ t('mobileCameraDemo.capturedImages') }}</h3>
        <div class="images-grid">
          <div 
            v-for="(image, index) in capturedImages" 
            :key="index"
            class="image-item"
          >
            <img :src="image.data" :alt="`Captured image ${index + 1}`" class="image-preview" />
            <div class="image-info">
              <span class="image-quality">{{ image.quality }}%</span>
              <button @click="removeImage(index)" class="remove-btn">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Quality Assessment Results -->
      <div v-if="qualityAssessments.length > 0" class="quality-results mt-6">
        <h3 class="text-lg font-semibold mb-4">{{ t('mobileCameraDemo.qualityAssessment') }}</h3>
        <div class="quality-grid">
          <div 
            v-for="(assessment, index) in qualityAssessments" 
            :key="index"
            class="quality-item"
            :class="getQualityClass(assessment.overall)"
          >
            <div class="quality-header">
              <span class="quality-score">{{ assessment.overall }}%</span>
              <span class="quality-status">{{ getQualityStatus(assessment.overall) }}</span>
            </div>
            <div class="quality-details">
              <div class="quality-metric">
                <span class="metric-label">{{ t('mobileCameraDemo.brightness') }}:</span>
                <span class="metric-value">{{ assessment.brightness.toFixed(1) }}%</span>
              </div>
              <div class="quality-metric">
                <span class="metric-label">{{ t('mobileCameraDemo.contrast') }}:</span>
                <span class="metric-value">{{ assessment.contrast.toFixed(1) }}%</span>
              </div>
              <div class="quality-metric">
                <span class="metric-label">{{ t('mobileCameraDemo.sharpness') }}:</span>
                <span class="metric-value">{{ assessment.sharpness.toFixed(1) }}%</span>
              </div>
            </div>
            <div v-if="assessment.warnings.length > 0" class="quality-warnings">
              <div v-for="warning in assessment.warnings" :key="warning" class="warning-item">
                {{ warning }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile Camera Interface -->
    <MobileCameraInterface
      v-if="showCamera"
      :auto-focus="cameraSettings.autoFocus"
      :auto-exposure="cameraSettings.autoExposure"
      :quality-threshold="cameraSettings.qualityThreshold"
      :multi-page="cameraSettings.multiPage"
      :auto-capture="cameraSettings.autoCapture"
      :capture-delay="cameraSettings.captureDelay"
      :enable-haptic-feedback="cameraSettings.enableHapticFeedback"
      :enable-boundary-detection="cameraSettings.enableBoundaryDetection"
      :enable-quality-assessment="cameraSettings.enableQualityAssessment"
      :enable-flash-control="cameraSettings.enableFlashControl"
      :enable-low-light-optimization="cameraSettings.enableLowLightOptimization"
      :max-pages="cameraSettings.maxPages"
      :storage-retention-days="cameraSettings.storageRetentionDays"
      @close="showCamera = false"
      @capture="handleImageCapture"
      @multi-page-capture="handleMultiPageCapture"
      @error="handleCameraError"
      @quality-assessment="handleQualityAssessment"
      @boundary-detected="handleBoundaryDetection"
    />

    <!-- Settings Modal -->
    <div v-if="showSettings" class="modal modal-open">
      <div class="modal-box max-w-2xl">
        <div class="modal-header">
          <h3 class="text-lg font-bold">{{ t('mobileCameraDemo.cameraSettings') }}</h3>
          <button @click="showSettings = false" class="btn btn-sm btn-circle btn-ghost">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="settings-grid">
          <div class="setting-group">
            <h4 class="setting-title">{{ t('mobileCameraDemo.cameraFeatures') }}</h4>
            
            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.autoFocus" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.autoFocus') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.autoFocusDesc') }}</p>
            </div>

            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.autoExposure" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.autoExposure') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.autoExposureDesc') }}</p>
            </div>

            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.enableBoundaryDetection" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.boundaryDetection') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.boundaryDetectionDesc') }}</p>
            </div>

            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.enableQualityAssessment" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.qualityAssessment') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.qualityAssessmentDesc') }}</p>
            </div>

            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.enableFlashControl" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.flashControl') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.flashControlDesc') }}</p>
            </div>

            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.enableHapticFeedback" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.hapticFeedback') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.hapticFeedbackDesc') }}</p>
            </div>
          </div>

          <div class="setting-group">
            <h4 class="setting-title">{{ t('mobileCameraDemo.captureSettings') }}</h4>
            
            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.autoCapture" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.autoCapture') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.autoCaptureDesc') }}</p>
            </div>

            <div class="setting-item">
              <label class="setting-label">{{ t('mobileCameraDemo.captureDelay') }}</label>
              <input 
                v-model.number="cameraSettings.captureDelay" 
                type="range" 
                min="1" 
                max="10" 
                class="range range-sm"
              />
              <span class="setting-value">{{ cameraSettings.captureDelay }}s</span>
            </div>

            <div class="setting-item">
              <label class="setting-label">{{ t('mobileCameraDemo.qualityThreshold') }}</label>
              <input 
                v-model.number="cameraSettings.qualityThreshold" 
                type="range" 
                min="50" 
                max="95" 
                step="5"
                class="range range-sm"
              />
              <span class="setting-value">{{ cameraSettings.qualityThreshold }}%</span>
            </div>

            <div class="setting-item">
              <label class="setting-label">
                <input 
                  v-model="cameraSettings.multiPage" 
                  type="checkbox" 
                  class="checkbox"
                />
                {{ t('mobileCameraDemo.multiPage') }}
              </label>
              <p class="setting-description">{{ t('mobileCameraDemo.multiPageDesc') }}</p>
            </div>

            <div class="setting-item">
              <label class="setting-label">{{ t('mobileCameraDemo.maxPages') }}</label>
              <input 
                v-model.number="cameraSettings.maxPages" 
                type="number" 
                min="1" 
                max="20" 
                class="input input-sm w-20"
              />
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="resetSettings" class="btn btn-outline">
            {{ t('mobileCameraDemo.resetSettings') }}
          </button>
          <button @click="showSettings = false" class="btn btn-primary">
            {{ t('mobileCameraDemo.saveSettings') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import MobileCameraInterface from './MobileCameraInterface.vue'
import type { ImageQuality } from '@/types/medication'

const { t } = useI18n()

// Demo state
const showCamera = ref(false)
const showSettings = ref(false)
const activeFeature = ref('camera')

// Captured data
const capturedImages = ref<Array<{ data: string; quality: number }>>([])
const qualityAssessments = ref<ImageQuality[]>([])
const boundaryDetections = ref<any[]>([])

// Camera settings
const cameraSettings = reactive({
  autoFocus: true,
  autoExposure: true,
  qualityThreshold: 70,
  multiPage: true,
  autoCapture: false,
  captureDelay: 3,
  enableHapticFeedback: true,
  enableBoundaryDetection: true,
  enableQualityAssessment: true,
  enableFlashControl: true,
  enableLowLightOptimization: true,
  maxPages: 10,
  storageRetentionDays: 7
})

// Feature definitions
const features = [
  {
    id: 'camera',
    title: t('mobileCameraDemo.features.camera.title'),
    description: t('mobileCameraDemo.features.camera.description'),
    icon: 'CameraIcon'
  },
  {
    id: 'quality',
    title: t('mobileCameraDemo.features.quality.title'),
    description: t('mobileCameraDemo.features.quality.description'),
    icon: 'QualityIcon'
  },
  {
    id: 'boundary',
    title: t('mobileCameraDemo.features.boundary.title'),
    description: t('mobileCameraDemo.features.boundary.description'),
    icon: 'BoundaryIcon'
  },
  {
    id: 'multiPage',
    title: t('mobileCameraDemo.features.multiPage.title'),
    description: t('mobileCameraDemo.features.multiPage.description'),
    icon: 'MultiPageIcon'
  },
  {
    id: 'preview',
    title: t('mobileCameraDemo.features.preview.title'),
    description: t('mobileCameraDemo.features.preview.description'),
    icon: 'PreviewIcon'
  },
  {
    id: 'storage',
    title: t('mobileCameraDemo.features.storage.title'),
    description: t('mobileCameraDemo.features.storage.description'),
    icon: 'StorageIcon'
  }
]

// Event handlers
const handleImageCapture = (imageData: string) => {
  capturedImages.value.push({
    data: imageData,
    quality: Math.floor(Math.random() * 30) + 70 // Simulate quality score
  })
}

const handleMultiPageCapture = (pages: any[]) => {
  pages.forEach(page => {
    capturedImages.value.push({
      data: page.imageData,
      quality: page.quality.overall
    })
  })
}

const handleCameraError = (error: string) => {
  console.error('Camera error:', error)
  // You could show a toast notification here
}

const handleQualityAssessment = (quality: ImageQuality) => {
  qualityAssessments.value.push(quality)
}

const handleBoundaryDetection = (boundaries: any) => {
  boundaryDetections.value.push(boundaries)
}

// Utility functions
const removeImage = (index: number) => {
  capturedImages.value.splice(index, 1)
}

const getQualityClass = (score: number) => {
  if (score >= 80) return 'quality-excellent'
  if (score >= 60) return 'quality-good'
  if (score >= 40) return 'quality-fair'
  return 'quality-poor'
}

const getQualityStatus = (score: number) => {
  if (score >= 80) return t('mobileCameraDemo.excellent')
  if (score >= 60) return t('mobileCameraDemo.good')
  if (score >= 40) return t('mobileCameraDemo.fair')
  return t('mobileCameraDemo.poor')
}

const resetSettings = () => {
  Object.assign(cameraSettings, {
    autoFocus: true,
    autoExposure: true,
    qualityThreshold: 70,
    multiPage: true,
    autoCapture: false,
    captureDelay: 3,
    enableHapticFeedback: true,
    enableBoundaryDetection: true,
    enableQualityAssessment: true,
    enableFlashControl: true,
    enableLowLightOptimization: true,
    maxPages: 10,
    storageRetentionDays: 7
  })
}

// Icon components (simplified)
const CameraIcon = { template: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" /></svg>' }
const QualityIcon = { template: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>' }
const BoundaryIcon = { template: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>' }
const MultiPageIcon = { template: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>' }
const PreviewIcon = { template: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>' }
const StorageIcon = { template: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" /></svg>' }
</script>

<style scoped>
.mobile-camera-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.demo-header {
  text-align: center;
  margin-bottom: 3rem;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.feature-card {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.feature-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.feature-card.active {
  border-color: #10b981;
  background: #f0fdf4;
}

.feature-icon {
  width: 48px;
  height: 48px;
  background: #f3f4f6;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
  color: #6b7280;
}

.feature-card.active .feature-icon {
  background: #dcfce7;
  color: #10b981;
}

.feature-title {
  font-size: 1.125rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #1f2937;
}

.feature-description {
  color: #6b7280;
  font-size: 0.875rem;
  line-height: 1.5;
}

.demo-section {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.demo-controls {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.demo-results {
  margin-top: 2rem;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.image-item {
  position: relative;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.image-preview {
  width: 100%;
  height: 150px;
  object-fit: cover;
}

.image-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.image-quality {
  font-size: 0.875rem;
  font-weight: 500;
}

.remove-btn {
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
}

.remove-btn:hover {
  background: rgba(239, 68, 68, 1);
}

.quality-results {
  margin-top: 2rem;
}

.quality-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.quality-item {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
}

.quality-item.quality-excellent {
  border-color: #10b981;
  background: #f0fdf4;
}

.quality-item.quality-good {
  border-color: #f59e0b;
  background: #fffbeb;
}

.quality-item.quality-fair {
  border-color: #f97316;
  background: #fff7ed;
}

.quality-item.quality-poor {
  border-color: #ef4444;
  background: #fef2f2;
}

.quality-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.quality-score {
  font-size: 1.25rem;
  font-weight: 700;
}

.quality-status {
  font-size: 0.875rem;
  font-weight: 500;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.1);
}

.quality-details {
  margin-bottom: 0.75rem;
}

.quality-metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.25rem;
  font-size: 0.875rem;
}

.metric-label {
  color: #6b7280;
}

.metric-value {
  font-weight: 500;
}

.quality-warnings {
  border-top: 1px solid #e5e7eb;
  padding-top: 0.75rem;
}

.warning-item {
  color: #f59e0b;
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}

/* Settings Modal */
.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 1.5rem;
}

.setting-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.setting-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.setting-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin-left: 1.5rem;
}

.setting-value {
  font-size: 0.875rem;
  font-weight: 500;
  color: #3b82f6;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .mobile-camera-demo {
    padding: 1rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .settings-grid {
    grid-template-columns: 1fr;
  }
  
  .demo-controls {
    flex-direction: column;
  }
  
  .images-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  }
  
  .quality-grid {
    grid-template-columns: 1fr;
  }
}

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .feature-card,
  .demo-section,
  .quality-item {
    background: #1f2937;
    border-color: #4b5563;
    color: white;
  }
  
  .feature-card:hover {
    border-color: #60a5fa;
  }
  
  .feature-card.active {
    background: #064e3b;
    border-color: #34d399;
  }
  
  .feature-icon {
    background: #374151;
    color: #9ca3af;
  }
  
  .feature-card.active .feature-icon {
    background: #065f46;
    color: #34d399;
  }
  
  .feature-title {
    color: #f9fafb;
  }
  
  .feature-description {
    color: #9ca3af;
  }
  
  .setting-title {
    color: #f9fafb;
  }
  
  .setting-label {
    color: #d1d5db;
  }
  
  .setting-description {
    color: #9ca3af;
  }
}
</style> 