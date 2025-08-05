<template>
  <div v-if="show" class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <div class="text-center mb-6">
        <div class="w-16 h-16 bg-success/20 rounded-full flex items-center justify-center mx-auto mb-4">
          <i class="fas fa-check text-success text-2xl"></i>
        </div>
        <h3 class="font-bold text-2xl mb-2">{{ $t('workflow.success.title', 'Workflow Completed!') }}</h3>
        <p class="text-base-content/70">{{ $t('workflow.success.subtitle', 'Your prescription has been successfully processed and saved.') }}</p>
      </div>
      
      <div class="space-y-6">
        <!-- Success Summary -->
        <div class="card bg-success/10 border-success/20">
          <div class="card-body p-4">
            <h4 class="font-semibold mb-3 text-success">{{ $t('workflow.success.summary', 'Processing Summary') }}</h4>
            
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div class="flex items-center gap-2">
                <i class="fas fa-pills text-success"></i>
                <div>
                  <div class="text-base-content/70">{{ $t('workflow.success.medications', 'Medications') }}</div>
                  <div class="font-medium">{{ summary.totalMedications }}</div>
                </div>
              </div>
              
              <div class="flex items-center gap-2">
                <i class="fas fa-calendar-alt text-success"></i>
                <div>
                  <div class="text-base-content/70">{{ $t('workflow.success.schedules', 'Schedules') }}</div>
                  <div class="font-medium">{{ summary.totalSchedules }}</div>
                </div>
              </div>
              
              <div class="flex items-center gap-2">
                <i class="fas fa-clock text-success"></i>
                <div>
                  <div class="text-base-content/70">{{ $t('workflow.success.processingTime', 'Processing Time') }}</div>
                  <div class="font-medium">{{ formatTime(summary.processingTime) }}</div>
                </div>
              </div>
              
              <div class="flex items-center gap-2">
                <i class="fas fa-shield-alt text-success"></i>
                <div>
                  <div class="text-base-content/70">{{ $t('workflow.success.interactions', 'Interactions') }}</div>
                  <div class="font-medium">{{ summary.interactionsFound }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- What's Next -->
        <div class="card bg-base-200">
          <div class="card-body p-4">
            <h4 class="font-semibold mb-3">{{ $t('workflow.success.whatsNext', 'What\'s Next?') }}</h4>
            
            <div class="space-y-3">
              <div class="flex items-start gap-3">
                <div class="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span class="text-primary text-xs font-bold">1</span>
                </div>
                <div>
                  <div class="font-medium">{{ $t('workflow.success.step1.title', 'Review Your Medications') }}</div>
                  <div class="text-sm text-base-content/70">{{ $t('workflow.success.step1.description', 'Check your medication list and schedules in the dashboard.') }}</div>
                </div>
              </div>
              
              <div class="flex items-start gap-3">
                <div class="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span class="text-primary text-xs font-bold">2</span>
                </div>
                <div>
                  <div class="font-medium">{{ $t('workflow.success.step2.title', 'Set Up Reminders') }}</div>
                  <div class="text-sm text-base-content/70">{{ $t('workflow.success.step2.description', 'Configure notification preferences for medication reminders.') }}</div>
                </div>
              </div>
              
              <div class="flex items-start gap-3">
                <div class="w-6 h-6 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <span class="text-primary text-xs font-bold">3</span>
                </div>
                <div>
                  <div class="font-medium">{{ $t('workflow.success.step3.title', 'Monitor Stock Levels') }}</div>
                  <div class="text-sm text-base-content/70">{{ $t('workflow.success.step3.description', 'Keep track of your medication supply and reorder when needed.') }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="space-y-3">
          <h4 class="font-semibold">{{ $t('workflow.success.quickActions', 'Quick Actions') }}</h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <button
              @click="viewMedications"
              class="btn btn-primary w-full justify-start"
            >
              <i class="fas fa-pills mr-2"></i>
              {{ $t('workflow.success.viewMedications', 'View Medications') }}
            </button>
            
            <button
              @click="viewSchedules"
              class="btn btn-outline w-full justify-start"
            >
              <i class="fas fa-calendar-alt mr-2"></i>
              {{ $t('workflow.success.viewSchedules', 'View Schedules') }}
            </button>
            
            <button
              @click="exportData"
              class="btn btn-outline w-full justify-start"
            >
              <i class="fas fa-download mr-2"></i>
              {{ $t('workflow.success.exportData', 'Export Data') }}
            </button>
            
            <button
              @click="startNew"
              class="btn btn-outline w-full justify-start"
            >
              <i class="fas fa-plus mr-2"></i>
              {{ $t('workflow.success.startNew', 'Start New Workflow') }}
            </button>
          </div>
        </div>

        <!-- Tips -->
        <div class="alert alert-info">
          <i class="fas fa-lightbulb"></i>
          <div>
            <div class="font-medium">{{ $t('workflow.success.tip.title', 'Pro Tip') }}</div>
            <div class="text-sm mt-1">
              {{ $t('workflow.success.tip.description', 'You can always come back to modify your medications, schedules, or stock levels from the dashboard.') }}
            </div>
          </div>
        </div>
      </div>

      <div class="modal-action">
        <button
          @click="close"
          class="btn btn-ghost"
        >
          {{ $t('workflow.success.close', 'Close') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Props
interface Props {
  show: boolean
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
  'update:show': [value: boolean]
  'view-medications': []
  'start-new': []
}>()

// Methods
const formatTime = (ms: number) => {
  if (ms < 1000) return `${ms}ms`
  const seconds = Math.floor(ms / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  return `${minutes}m ${seconds % 60}s`
}

const close = () => {
  emit('update:show', false)
}

const viewMedications = () => {
  emit('view-medications')
  close()
}

const viewSchedules = () => {
  // Navigate to schedules page
  window.location.href = '/schedules'
}

const exportData = () => {
  const exportData = {
    summary: props.summary,
    exportedAt: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'workflow-completion-summary.json'
  a.click()
  URL.revokeObjectURL(url)
}

const startNew = () => {
  emit('start-new')
  close()
}
</script>

<style scoped>
.modal {
  @apply z-50;
}
</style> 