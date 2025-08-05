<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MedicationInteraction } from '@/types/medication'

const { t } = useI18n()

interface Props {
  interactions: MedicationInteraction[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const selectedInteraction = ref<MedicationInteraction | null>(null)
const filterSeverity = ref<'all' | 'low' | 'moderate' | 'high' | 'contraindicated'>('all')

const filteredInteractions = computed(() => {
  if (filterSeverity.value === 'all') return props.interactions
  return props.interactions.filter(interaction => interaction.severity === filterSeverity.value)
})

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'low': return 'badge-info'
    case 'moderate': return 'badge-warning'
    case 'high': return 'badge-error'
    case 'contraindicated': return 'badge-error badge-outline'
    default: return 'badge-neutral'
  }
}

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'low': return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'moderate': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'high': return 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'contraindicated': return 'M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728'
    default: return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

const getSeverityDescription = (severity: string) => {
  switch (severity) {
    case 'low': return t('dashboard.interactionSeverity.low')
    case 'moderate': return t('dashboard.interactionSeverity.moderate')
    case 'high': return t('dashboard.interactionSeverity.high')
    case 'contraindicated': return t('dashboard.interactionSeverity.contraindicated')
    default: return t('dashboard.interactionSeverity.unknown')
  }
}

const criticalInteractions = computed(() => 
  props.interactions.filter(interaction => 
    interaction.severity === 'high' || interaction.severity === 'contraindicated'
  )
)
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-4xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {{ t('dashboard.interactionWarnings') }}
          <span v-if="criticalInteractions.length > 0" 
                class="badge badge-error badge-sm ml-2">{{ criticalInteractions.length }}</span>
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Summary Stats -->
      <div class="stats shadow w-full mb-6">
        <div class="stat">
          <div class="stat-figure text-info">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.low') }}</div>
          <div class="stat-value text-info">{{ interactions.filter(i => i.severity === 'low').length }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-warning">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.moderate') }}</div>
          <div class="stat-value text-warning">{{ interactions.filter(i => i.severity === 'moderate').length }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.high') }}</div>
          <div class="stat-value text-error">{{ interactions.filter(i => i.severity === 'high').length }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.contraindicated') }}</div>
          <div class="stat-value text-error">{{ interactions.filter(i => i.severity === 'contraindicated').length }}</div>
        </div>
      </div>

      <!-- Filter Controls -->
      <div class="flex gap-2 mb-4">
        <button 
          v-for="severity in ['all', 'low', 'moderate', 'high', 'contraindicated']" 
          :key="severity"
          @click="filterSeverity = severity"
          class="btn btn-sm"
          :class="filterSeverity === severity ? 'btn-primary' : 'btn-outline'"
        >
          {{ t(`dashboard.severity.${severity}`) }}
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Interaction List -->
        <div class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.interactions') }} ({{ filteredInteractions.length }})</h4>
          
          <div v-if="filteredInteractions.length === 0" class="text-center py-8">
            <p class="text-secondary-high-contrast">{{ t('dashboard.noInteractions') }}</p>
          </div>
          
          <div v-else class="space-y-3 max-h-96 overflow-y-auto">
            <div 
              v-for="interaction in filteredInteractions" 
              :key="interaction.description"
              @click="selectedInteraction = interaction"
              class="card bg-base-200 cursor-pointer hover:bg-base-300 transition-colors"
              :class="selectedInteraction?.description === interaction.description ? 'ring-2 ring-primary' : ''"
            >
              <div class="card-body p-4">
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getSeverityIcon(interaction.severity)" />
                      </svg>
                      <span :class="getSeverityColor(interaction.severity)" class="badge">
                        {{ t(`dashboard.severity.${interaction.severity}`) }}
                      </span>
                    </div>
                    <p class="text-sm text-high-contrast line-clamp-2">{{ interaction.description }}</p>
                    <p class="text-xs text-secondary-high-contrast mt-1">
                      {{ interaction.medications.join(', ') }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Interaction Details -->
        <div v-if="selectedInteraction" class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.interactionDetails') }}</h4>
          
          <div class="card bg-base-100">
            <div class="card-body">
              <div class="space-y-4">
                <!-- Severity -->
                <div>
                  <div class="flex items-center gap-2 mb-2">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getSeverityIcon(selectedInteraction.severity)" />
                    </svg>
                    <span :class="getSeverityColor(selectedInteraction.severity)" class="badge badge-lg">
                      {{ t(`dashboard.severity.${selectedInteraction.severity}`) }}
                    </span>
                  </div>
                  <p class="text-sm text-secondary-high-contrast">
                    {{ getSeverityDescription(selectedInteraction.severity) }}
                  </p>
                </div>

                <!-- Description -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.description') }}</h5>
                  <p class="text-sm text-secondary-high-contrast bg-base-200 p-3 rounded-lg">
                    {{ selectedInteraction.description }}
                  </p>
                </div>

                <!-- Medications -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.medications') }}</h5>
                  <div class="flex flex-wrap gap-2">
                    <span 
                      v-for="medication in selectedInteraction.medications" 
                      :key="medication"
                      class="badge badge-outline"
                    >
                      {{ medication }}
                    </span>
                  </div>
                </div>

                <!-- Recommendations -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.recommendations') }}</h5>
                  <p class="text-sm text-secondary-high-contrast bg-base-200 p-3 rounded-lg">
                    {{ selectedInteraction.recommendations }}
                  </p>
                </div>

                <!-- Evidence -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.evidence') }}</h5>
                  <p class="text-sm text-secondary-high-contrast bg-base-200 p-3 rounded-lg">
                    {{ selectedInteraction.evidence }}
                  </p>
                </div>

                <!-- Source -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.source') }}</h5>
                  <p class="text-sm text-secondary-high-contrast">
                    {{ selectedInteraction.source }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- No Selection State -->
        <div v-else class="flex items-center justify-center h-64">
          <div class="text-center text-secondary-high-contrast">
            <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p>{{ t('dashboard.selectInteraction') }}</p>
          </div>
        </div>
      </div>

      <div class="modal-action">
        <button @click="emit('close')" class="btn">{{ t('common.close') }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-box {
  max-height: 90vh;
  overflow-y: auto;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style> 