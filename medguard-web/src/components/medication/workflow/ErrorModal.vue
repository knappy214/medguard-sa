<template>
  <div v-if="show" class="modal modal-open">
    <div class="modal-box max-w-2xl">
      <div class="flex items-center gap-2 mb-4">
        <i class="fas fa-exclamation-triangle text-error text-2xl"></i>
        <h3 class="font-bold text-lg">{{ $t('workflow.error.title', 'Workflow Error') }}</h3>
      </div>
      
      <div class="space-y-4">
        <!-- Error Details -->
        <div class="alert alert-error">
          <i class="fas fa-times-circle"></i>
          <div>
            <div class="font-medium">{{ error?.message || $t('workflow.error.unknown', 'An unknown error occurred') }}</div>
            <div v-if="error?.stack" class="text-xs mt-1 opacity-80">
              {{ error.stack }}
            </div>
          </div>
        </div>

        <!-- Step Information -->
        <div class="card bg-base-200">
          <div class="card-body p-4">
            <h4 class="font-medium mb-2">{{ $t('workflow.error.stepInfo', 'Error occurred at step {step}', { step: step + 1 }) }}</h4>
            <div class="text-sm text-base-content/70">
              {{ getStepDescription(step) }}
            </div>
          </div>
        </div>

        <!-- Recovery Options -->
        <div class="space-y-3">
          <h4 class="font-medium">{{ $t('workflow.error.recoveryOptions', 'Recovery Options') }}</h4>
          
          <div class="space-y-2">
            <button
              @click="retry"
              class="btn btn-primary w-full justify-start"
            >
              <i class="fas fa-redo mr-2"></i>
              {{ $t('workflow.error.retry', 'Retry this step') }}
            </button>
            
            <button
              @click="skip"
              class="btn btn-outline w-full justify-start"
            >
              <i class="fas fa-forward mr-2"></i>
              {{ $t('workflow.error.skip', 'Skip this step and continue') }}
            </button>
            
            <button
              @click="rollback"
              class="btn btn-outline w-full justify-start"
            >
              <i class="fas fa-undo mr-2"></i>
              {{ $t('workflow.error.rollback', 'Rollback to previous step') }}
            </button>
            
            <button
              @click="restart"
              class="btn btn-outline w-full justify-start"
            >
              <i class="fas fa-home mr-2"></i>
              {{ $t('workflow.error.restart', 'Restart workflow') }}
            </button>
          </div>
        </div>

        <!-- Error Context -->
        <div v-if="errorContext" class="card bg-base-200">
          <div class="card-body p-4">
            <h4 class="font-medium mb-2">{{ $t('workflow.error.context', 'Error Context') }}</h4>
            <div class="text-sm space-y-1">
              <div v-for="(value, key) in errorContext" :key="key">
                <span class="font-medium">{{ key }}:</span> {{ value }}
              </div>
            </div>
          </div>
        </div>

        <!-- Help Information -->
        <div class="alert alert-info">
          <i class="fas fa-info-circle"></i>
          <div>
            <div class="font-medium">{{ $t('workflow.error.help', 'Need Help?') }}</div>
            <div class="text-sm mt-1">
              {{ $t('workflow.error.helpText', 'If this error persists, please contact support with the error details above.') }}
            </div>
          </div>
        </div>
      </div>

      <div class="modal-action">
        <button
          @click="close"
          class="btn btn-ghost"
        >
          {{ $t('workflow.error.close', 'Close') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// Props
interface Props {
  show: boolean
  error: Error | null
  step: number
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'update:show': [value: boolean]
  'retry': []
  'skip': []
  'rollback': []
  'restart': []
}>()

// Computed properties
const errorContext = computed(() => {
  if (!props.error) return null
  
  return {
    'Error Type': props.error.name || 'Unknown',
    'Step': props.step + 1,
    'Timestamp': new Date().toLocaleString(),
    'User Agent': navigator.userAgent.substring(0, 100) + '...'
  }
})

// Methods
const getStepDescription = (step: number) => {
  const stepDescriptions = [
    t('workflow.error.step1', 'Image capture and upload'),
    t('workflow.error.step2', 'OCR processing and text extraction'),
    t('workflow.error.step3', 'Medication review and validation'),
    t('workflow.error.step4', 'Drug interaction checking'),
    t('workflow.error.step5', 'Schedule creation'),
    t('workflow.error.step6', 'Stock management configuration'),
    t('workflow.error.step7', 'Final confirmation and save')
  ]
  
  return stepDescriptions[step] || t('workflow.error.unknownStep', 'Unknown step')
}

const close = () => {
  emit('update:show', false)
}

const retry = () => {
  emit('retry')
  close()
}

const skip = () => {
  emit('skip')
  close()
}

const rollback = () => {
  emit('rollback')
  close()
}

const restart = () => {
  emit('restart')
  close()
}
</script>

<style scoped>
.modal {
  @apply z-50;
}
</style> 