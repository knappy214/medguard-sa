<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { AdherenceTracking } from '@/types/medication'

const { t } = useI18n()

interface Props {
  adherenceData: AdherenceTracking[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const selectedMedication = ref<AdherenceTracking | null>(null)
const filterAdherence = ref<'all' | 'excellent' | 'good' | 'poor'>('all')
const timeRange = ref<'7d' | '30d' | '90d'>('30d')

const getAdherenceLevel = (rate: number) => {
  if (rate >= 90) return 'excellent'
  if (rate >= 70) return 'good'
  return 'poor'
}

const getAdherenceColor = (rate: number) => {
  if (rate >= 90) return 'text-success'
  if (rate >= 70) return 'text-warning'
  return 'text-error'
}

const getAdherenceBgColor = (rate: number) => {
  if (rate >= 90) return 'bg-success/10'
  if (rate >= 70) return 'bg-warning/10'
  return 'bg-error/10'
}

const filteredAdherenceData = computed(() => {
  let filtered = props.adherenceData
  
  if (filterAdherence.value !== 'all') {
    filtered = filtered.filter(item => getAdherenceLevel(item.adherenceRate) === filterAdherence.value)
  }
  
  return filtered.sort((a, b) => b.adherenceRate - a.adherenceRate)
})

const overallAdherence = computed(() => {
  if (props.adherenceData.length === 0) return 0
  const total = props.adherenceData.reduce((sum, item) => sum + item.adherenceRate, 0)
  return Math.round(total / props.adherenceData.length)
})

const adherenceStats = computed(() => {
  const stats = {
    excellent: 0,
    good: 0,
    poor: 0,
    total: props.adherenceData.length
  }
  
  props.adherenceData.forEach(item => {
    const level = getAdherenceLevel(item.adherenceRate)
    stats[level as keyof typeof stats]++
  })
  
  return stats
})

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const getStreakColor = (streak: number) => {
  if (streak >= 30) return 'text-success'
  if (streak >= 7) return 'text-warning'
  return 'text-error'
}
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-6xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          {{ t('dashboard.adherenceTracking') }}
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Overall Adherence Summary -->
      <div class="stats shadow w-full mb-6">
        <div class="stat">
          <div class="stat-figure text-accent">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.overallAdherence') }}</div>
          <div class="stat-value" :class="getAdherenceColor(overallAdherence)">
            {{ overallAdherence }}%
          </div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.average') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-success">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.excellent') }}</div>
          <div class="stat-value text-success">{{ adherenceStats.excellent }}</div>
          <div class="stat-desc text-secondary-high-contrast">≥90%</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-warning">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.good') }}</div>
          <div class="stat-value text-warning">{{ adherenceStats.good }}</div>
          <div class="stat-desc text-secondary-high-contrast">70-89%</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.poor') }}</div>
          <div class="stat-value text-error">{{ adherenceStats.poor }}</div>
          <div class="stat-desc text-secondary-high-contrast">&lt;70%</div>
        </div>
      </div>

      <!-- Filter Controls -->
      <div class="flex flex-wrap gap-4 mb-6">
        <div class="form-control">
          <label class="label">
            <span class="label-text text-high-contrast">{{ t('dashboard.filterByAdherence') }}</span>
          </label>
          <select v-model="filterAdherence" class="select select-bordered select-sm">
            <option value="all">{{ t('dashboard.allLevels') }}</option>
            <option value="excellent">{{ t('dashboard.excellent') }} (≥90%)</option>
            <option value="good">{{ t('dashboard.good') }} (70-89%)</option>
            <option value="poor">{{ t('dashboard.poor') }} (&lt;70%)</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text text-high-contrast">{{ t('dashboard.timeRange') }}</span>
          </label>
          <select v-model="timeRange" class="select select-bordered select-sm">
            <option value="7d">{{ t('dashboard.last7Days') }}</option>
            <option value="30d">{{ t('dashboard.last30Days') }}</option>
            <option value="90d">{{ t('dashboard.last90Days') }}</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Adherence List -->
        <div class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.medicationAdherence') }} ({{ filteredAdherenceData.length }})</h4>
          
          <div v-if="filteredAdherenceData.length === 0" class="text-center py-8">
            <p class="text-secondary-high-contrast">{{ t('dashboard.noAdherenceData') }}</p>
          </div>
          
          <div v-else class="space-y-3 max-h-96 overflow-y-auto">
            <div 
              v-for="item in filteredAdherenceData" 
              :key="item.medicationId"
              @click="selectedMedication = item"
              class="card bg-base-200 cursor-pointer hover:bg-base-300 transition-colors"
              :class="selectedMedication?.medicationId === item.medicationId ? 'ring-2 ring-primary' : ''"
            >
              <div class="card-body p-4">
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <h5 class="font-medium text-high-contrast">{{ item.medication.name }}</h5>
                    <div class="flex items-center gap-4 mt-2">
                      <div class="flex items-center gap-2">
                        <div class="radial-progress" 
                             :style="{ '--value': item.adherenceRate, '--size': '2rem' }"
                             :class="getAdherenceColor(item.adherenceRate)">
                          {{ item.adherenceRate }}%
                        </div>
                        <span class="text-sm text-secondary-high-contrast">{{ t('dashboard.adherence') }}</span>
                      </div>
                      <div class="flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        <span :class="getStreakColor(item.streakDays)" class="text-sm font-medium">
                          {{ item.streakDays }} {{ t('dashboard.days') }}
                        </span>
                      </div>
                    </div>
                    <div class="flex gap-4 mt-2 text-xs text-secondary-high-contrast">
                      <span>{{ t('dashboard.taken') }}: {{ item.takenDoses }}/{{ item.totalDoses }}</span>
                      <span>{{ t('dashboard.missed') }}: {{ item.missedDoses }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Detailed Adherence View -->
        <div v-if="selectedMedication" class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.adherenceDetails') }}</h4>
          
          <div class="card bg-base-100">
            <div class="card-body">
              <div class="space-y-4">
                <!-- Medication Info -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ selectedMedication.medication.name }}</h5>
                  <p class="text-sm text-secondary-high-contrast">{{ selectedMedication.medication.dosage }}</p>
                </div>

                <!-- Adherence Progress -->
                <div>
                  <div class="flex justify-between items-center mb-2">
                    <span class="text-sm font-medium text-high-contrast">{{ t('dashboard.adherenceRate') }}</span>
                    <span :class="getAdherenceColor(selectedMedication.adherenceRate)" class="font-bold">
                      {{ selectedMedication.adherenceRate }}%
                    </span>
                  </div>
                  <progress 
                    class="progress w-full" 
                    :class="getAdherenceColor(selectedMedication.adherenceRate).replace('text-', 'progress-')"
                    :value="selectedMedication.adherenceRate" 
                    max="100"
                  ></progress>
                </div>

                <!-- Stats Grid -->
                <div class="grid grid-cols-2 gap-4">
                  <div class="text-center p-3 bg-base-200 rounded-lg">
                    <div class="text-2xl font-bold text-success">{{ selectedMedication.takenDoses }}</div>
                    <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.taken') }}</div>
                  </div>
                  <div class="text-center p-3 bg-base-200 rounded-lg">
                    <div class="text-2xl font-bold text-error">{{ selectedMedication.missedDoses }}</div>
                    <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.missed') }}</div>
                  </div>
                  <div class="text-center p-3 bg-base-200 rounded-lg">
                    <div class="text-2xl font-bold text-accent">{{ selectedMedication.streakDays }}</div>
                    <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.streakDays') }}</div>
                  </div>
                  <div class="text-center p-3 bg-base-200 rounded-lg">
                    <div class="text-2xl font-bold text-info">{{ selectedMedication.totalDoses }}</div>
                    <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.totalDoses') }}</div>
                  </div>
                </div>

                <!-- Recent History -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.recentHistory') }}</h5>
                  <div class="space-y-2 max-h-32 overflow-y-auto">
                    <div 
                      v-for="history in selectedMedication.history.slice(0, 5)" 
                      :key="history.id"
                      class="flex justify-between items-center p-2 bg-base-200 rounded text-sm"
                    >
                      <div class="flex items-center gap-2">
                        <span 
                          class="badge badge-xs"
                          :class="history.action === 'taken' ? 'badge-success' : history.action === 'missed' ? 'badge-error' : 'badge-warning'"
                        >
                          {{ t(`dashboard.action.${history.action}`) }}
                        </span>
                        <span class="text-secondary-high-contrast">{{ formatDate(history.timestamp) }}</span>
                      </div>
                      <span v-if="history.adherenceScore" class="text-xs text-secondary-high-contrast">
                        {{ history.adherenceScore }}%
                      </span>
                    </div>
                  </div>
                </div>

                <!-- Next Dose -->
                <div class="border-t pt-4">
                  <div class="flex justify-between items-center">
                    <span class="text-sm text-secondary-high-contrast">{{ t('dashboard.nextDose') }}:</span>
                    <span class="font-medium text-high-contrast">{{ formatDate(selectedMedication.nextDose) }}</span>
                  </div>
                  <div class="flex justify-between items-center mt-1">
                    <span class="text-sm text-secondary-high-contrast">{{ t('dashboard.lastTaken') }}:</span>
                    <span class="font-medium text-high-contrast">{{ formatDate(selectedMedication.lastTaken) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- No Selection State -->
        <div v-else class="flex items-center justify-center h-64">
          <div class="text-center text-secondary-high-contrast">
            <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <p>{{ t('dashboard.selectMedication') }}</p>
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

.radial-progress {
  @apply text-xs;
}
</style> 