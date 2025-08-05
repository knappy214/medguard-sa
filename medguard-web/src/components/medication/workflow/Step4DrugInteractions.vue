<template>
  <div class="step4-drug-interactions">
    <h3 class="text-xl font-semibold mb-4">
      <i class="fas fa-check-circle text-primary mr-2"></i>
      {{ $t('workflow.step4.title', 'Drug Interactions') }}
    </h3>

    <div class="space-y-6">
      <!-- Interaction Check Status -->
      <div v-if="isChecking" class="text-center py-8">
        <div class="loading loading-spinner loading-lg text-primary mb-4"></div>
        <p class="text-lg font-medium">{{ $t('workflow.step4.checking', 'Checking drug interactions...') }}</p>
        <p class="text-sm text-base-content/70">{{ currentCheckStep }}</p>
      </div>

      <!-- Interaction Results -->
      <div v-else class="space-y-6">
        <!-- Summary -->
        <div class="card bg-base-200">
          <div class="card-body">
            <h4 class="font-semibold mb-3">{{ $t('workflow.step4.summary', 'Interaction Summary') }}</h4>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step4.totalMedications', 'Total Medications') }}</div>
                <div class="font-medium text-lg">{{ medications.length }}</div>
              </div>
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step4.interactionsFound', 'Interactions Found') }}</div>
                <div class="font-medium text-lg" :class="interactions.length > 0 ? 'text-warning' : 'text-success'">
                  {{ interactions.length }}
                </div>
              </div>
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step4.highRisk', 'High Risk') }}</div>
                <div class="font-medium text-lg text-error">{{ highRiskCount }}</div>
              </div>
              <div>
                <div class="text-base-content/70">{{ $t('workflow.step4.safe', 'Safe') }}</div>
                <div class="font-medium text-lg text-success">{{ safeCount }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Interactions List -->
        <div v-if="interactions.length > 0" class="space-y-4">
          <h4 class="font-semibold">{{ $t('workflow.step4.interactions', 'Drug Interactions') }}</h4>
          
          <div
            v-for="(interaction, index) in interactions"
            :key="index"
            class="card"
            :class="getInteractionCardClass(interaction.severity)"
          >
            <div class="card-body">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <div class="badge" :class="getSeverityBadgeClass(interaction.severity)">
                      {{ getSeverityText(interaction.severity) }}
                    </div>
                    <h5 class="font-medium">{{ interaction.description }}</h5>
                  </div>
                  
                  <div class="text-sm space-y-2">
                    <div>
                      <span class="font-medium">{{ $t('workflow.step4.medications', 'Medications') }}:</span>
                      {{ interaction.medications.join(', ') }}
                    </div>
                    <div>
                      <span class="font-medium">{{ $t('workflow.step4.recommendations', 'Recommendations') }}:</span>
                      {{ interaction.recommendations }}
                    </div>
                    <div v-if="interaction.evidence" class="text-xs text-base-content/60">
                      {{ $t('workflow.step4.evidence', 'Evidence') }}: {{ interaction.evidence }}
                    </div>
                  </div>
                </div>
                
                <div class="flex flex-col gap-2 ml-4">
                  <button
                    @click="viewDetails(interaction)"
                    class="btn btn-circle btn-sm btn-ghost"
                    :title="$t('workflow.step4.viewDetails', 'View Details')"
                  >
                    <i class="fas fa-info-circle"></i>
                  </button>
                  <button
                    @click="dismissInteraction(index)"
                    class="btn btn-circle btn-sm btn-ghost"
                    :title="$t('workflow.step4.dismiss', 'Dismiss')"
                  >
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- No Interactions -->
        <div v-else class="alert alert-success">
          <i class="fas fa-check-circle"></i>
          <span>{{ $t('workflow.step4.noInteractions', 'No drug interactions found. Your medication combination appears to be safe.') }}</span>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2">
          <button
            @click="checkInteractions"
            class="btn btn-primary"
          >
            <i class="fas fa-search mr-2"></i>
            {{ $t('workflow.step4.recheck', 'Re-check Interactions') }}
          </button>
          <button
            @click="exportReport"
            class="btn btn-outline"
          >
            <i class="fas fa-download mr-2"></i>
            {{ $t('workflow.step4.exportReport', 'Export Report') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { medicationApi } from '@/services/medicationApi'
import type { PrescriptionMedication, MedicationInteraction, MedicationValidation } from '@/types/medication'

const { t } = useI18n()

// Props
interface Props {
  medications: PrescriptionMedication[]
  interactions: MedicationInteraction[]
  validationResults: Record<string, MedicationValidation>
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'interactions-checked': [interactions: MedicationInteraction[]]
}>()

// Reactive state
const isChecking = ref(false)
const currentCheckStep = ref('')

// Computed properties
const highRiskCount = computed(() => {
  return props.interactions.filter(i => i.severity === 'high' || i.severity === 'contraindicated').length
})

const safeCount = computed(() => {
  return props.medications.length - props.interactions.length
})

// Methods
const getInteractionCardClass = (severity: string) => {
  switch (severity) {
    case 'contraindicated': return 'bg-error/10 border-error'
    case 'high': return 'bg-error/5 border-error/50'
    case 'moderate': return 'bg-warning/10 border-warning'
    case 'low': return 'bg-info/10 border-info'
    default: return 'bg-base-100'
  }
}

const getSeverityBadgeClass = (severity: string) => {
  switch (severity) {
    case 'contraindicated': return 'badge-error'
    case 'high': return 'badge-error'
    case 'moderate': return 'badge-warning'
    case 'low': return 'badge-info'
    default: return 'badge-neutral'
  }
}

const getSeverityText = (severity: string) => {
  switch (severity) {
    case 'contraindicated': return t('workflow.step4.severity.contraindicated', 'Contraindicated')
    case 'high': return t('workflow.step4.severity.high', 'High Risk')
    case 'moderate': return t('workflow.step4.severity.moderate', 'Moderate')
    case 'low': return t('workflow.step4.severity.low', 'Low Risk')
    default: return t('workflow.step4.severity.unknown', 'Unknown')
  }
}

const checkInteractions = async () => {
  if (props.medications.length < 2) {
    emit('interactions-checked', [])
    return
  }

  isChecking.value = true
  currentCheckStep.value = t('workflow.step4.step1', 'Analyzing medication combinations...')

  try {
    const medicationNames = props.medications.map(med => med.name)
    const interactions = await medicationApi.checkMedicationInteractions(medicationNames)
    
    // Simulate processing steps
    await new Promise(resolve => setTimeout(resolve, 1000))
    currentCheckStep.value = t('workflow.step4.step2', 'Checking drug databases...')
    await new Promise(resolve => setTimeout(resolve, 1000))
    currentCheckStep.value = t('workflow.step4.step3', 'Generating recommendations...')
    await new Promise(resolve => setTimeout(resolve, 500))
    
    emit('interactions-checked', interactions)
  } catch (error) {
    console.error('Failed to check interactions:', error)
    emit('interactions-checked', [])
  } finally {
    isChecking.value = false
  }
}

const viewDetails = (interaction: MedicationInteraction) => {
  // This would open a detailed interaction modal
  console.log('View interaction details:', interaction)
}

const dismissInteraction = (index: number) => {
  const updatedInteractions = props.interactions.filter((_, i) => i !== index)
  emit('interactions-checked', updatedInteractions)
}

const exportReport = () => {
  const report = {
    medications: props.medications,
    interactions: props.interactions,
    summary: {
      totalMedications: props.medications.length,
      interactionsFound: props.interactions.length,
      highRisk: highRiskCount.value,
      safe: safeCount.value
    },
    generatedAt: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'drug-interactions-report.json'
  a.click()
  URL.revokeObjectURL(url)
}

// Lifecycle
onMounted(() => {
  // Auto-check interactions on mount
  checkInteractions()
})
</script>

<style scoped>
.card {
  @apply border;
}
</style> 