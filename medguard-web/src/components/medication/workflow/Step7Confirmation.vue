<template>
  <div class="step7-confirmation">
    <h3 class="text-xl font-semibold mb-4">
      <i class="fas fa-save text-primary mr-2"></i>
      {{ $t('workflow.step7.title', 'Confirm & Save') }}
    </h3>

    <div class="space-y-6">
      <!-- Summary -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step7.summary', 'Workflow Summary') }}</h4>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step7.medications', 'Medications') }}</div>
              <div class="font-medium text-lg">{{ summary.totalMedications }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step7.schedules', 'Schedules') }}</div>
              <div class="font-medium text-lg">{{ summary.totalSchedules }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step7.interactions', 'Interactions') }}</div>
              <div class="font-medium text-lg">{{ summary.interactionsFound }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step7.processingTime', 'Processing Time') }}</div>
              <div class="font-medium text-lg">{{ formatTime(summary.processingTime) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Final Review -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step7.finalReview', 'Final Review') }}</h4>
          
          <div class="space-y-4">
            <!-- Prescription Information -->
            <div class="card bg-base-100">
              <div class="card-body p-4">
                <h5 class="font-medium mb-2">{{ $t('workflow.step7.prescriptionInfo', 'Prescription Information') }}</h5>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div>
                    <span class="font-medium">{{ $t('workflow.step7.patientName', 'Patient') }}:</span>
                    {{ workflowData.prescriptionMetadata.patientName || 'Not specified' }}
                  </div>
                  <div>
                    <span class="font-medium">{{ $t('workflow.step7.doctor', 'Doctor') }}:</span>
                    {{ workflowData.prescriptionMetadata.prescribingDoctor || 'Not specified' }}
                  </div>
                  <div>
                    <span class="font-medium">{{ $t('workflow.step7.prescriptionDate', 'Date') }}:</span>
                    {{ workflowData.prescriptionMetadata.prescriptionDate || 'Not specified' }}
                  </div>
                  <div>
                    <span class="font-medium">{{ $t('workflow.step7.prescriptionNumber', 'Number') }}:</span>
                    {{ workflowData.prescriptionMetadata.prescriptionNumber || 'Not specified' }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Medications List -->
            <div class="card bg-base-100">
              <div class="card-body p-4">
                <h5 class="font-medium mb-2">{{ $t('workflow.step7.medications', 'Medications') }}</h5>
                <div class="space-y-2">
                  <div
                    v-for="(medication, index) in workflowData.extractedMedications"
                    :key="index"
                    class="flex items-center justify-between p-2 bg-base-200 rounded"
                  >
                    <div>
                      <div class="font-medium">{{ medication.name }}</div>
                      <div class="text-sm text-base-content/70">
                        {{ medication.strength }} - {{ medication.dosage }} - {{ medication.frequency }}
                      </div>
                    </div>
                    <div class="text-sm text-base-content/70">
                      Qty: {{ medication.quantity }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Stock Levels -->
            <div class="card bg-base-100">
              <div class="card-body p-4">
                <h5 class="font-medium mb-2">{{ $t('workflow.step7.stockLevels', 'Stock Levels') }}</h5>
                <div class="space-y-2">
                  <div
                    v-for="(level, medicationName) in workflowData.stockLevels"
                    :key="medicationName"
                    class="flex items-center justify-between p-2 bg-base-200 rounded"
                  >
                    <span class="font-medium">{{ medicationName }}</span>
                    <span class="text-sm">{{ level }} units</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Confirmation Options -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step7.confirmation', 'Confirmation Options') }}</h4>
          
          <div class="space-y-4">
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step7.createSchedules', 'Create medication schedules') }}</span>
                <input
                  v-model="confirmationOptions.createSchedules"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step7.setReminders', 'Set up reminders') }}</span>
                <input
                  v-model="confirmationOptions.setReminders"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step7.enableNotifications', 'Enable notifications') }}</span>
                <input
                  v-model="confirmationOptions.enableNotifications"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step7.shareWithCaregiver', 'Share with caregiver') }}</span>
                <input
                  v-model="confirmationOptions.shareWithCaregiver"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-2">
        <button
          @click="exportWorkflow"
          class="btn btn-outline"
        >
          <i class="fas fa-download mr-2"></i>
          {{ $t('workflow.step7.export', 'Export Data') }}
        </button>
        <button
          @click="completeWorkflow"
          class="btn btn-primary"
          :disabled="isProcessing"
        >
          <i class="fas fa-check mr-2"></i>
          {{ $t('workflow.step7.complete', 'Complete Workflow') }}
        </button>
      </div>

      <!-- Processing indicator -->
      <div v-if="isProcessing" class="text-center py-4">
        <div class="loading loading-spinner loading-lg text-primary mb-4"></div>
        <p class="text-lg font-medium">{{ $t('workflow.step7.processing', 'Processing...') }}</p>
        <p class="text-sm text-base-content/70">{{ currentProcessingStep }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Props
interface Props {
  workflowData: any
  summary: {
    totalMedications: number
    totalSchedules: number
    interactionsFound: number
    lowStockItems: number
    processingTime: number
  }
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'workflow-complete': []
}>()

// Reactive state
const isProcessing = ref(false)
const currentProcessingStep = ref('')
const confirmationOptions = reactive({
  createSchedules: true,
  setReminders: true,
  enableNotifications: true,
  shareWithCaregiver: false
})

// Methods
const formatTime = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  return `${minutes}m ${seconds % 60}s`
}

const exportWorkflow = () => {
  const exportData = {
    workflowData: props.workflowData,
    summary: props.summary,
    confirmationOptions,
    exportedAt: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'prescription-workflow-export.json'
  a.click()
  URL.revokeObjectURL(url)
}

const completeWorkflow = async () => {
  isProcessing.value = true
  
  try {
    // Simulate processing steps
    const steps = [
      t('workflow.step7.step1', 'Validating data...'),
      t('workflow.step7.step2', 'Creating medications...'),
      t('workflow.step7.step3', 'Setting up schedules...'),
      t('workflow.step7.step4', 'Configuring notifications...'),
      t('workflow.step7.step5', 'Finalizing...')
    ]
    
    for (let i = 0; i < steps.length; i++) {
      currentProcessingStep.value = steps[i]
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    // Emit completion
    emit('workflow-complete')
    
  } catch (error) {
    console.error('Workflow completion failed:', error)
  } finally {
    isProcessing.value = false
  }
}
</script>

<style scoped>
.card {
  @apply border-0;
}
</style> 