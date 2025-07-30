<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MedicationSchedule } from '@/types/medication'

interface Props {
  schedule: MedicationSchedule[]
  pendingMedications: MedicationSchedule[]
  takenMedications: MedicationSchedule[]
  missedMedications: MedicationSchedule[]
}

interface Emits {
  (e: 'mark-as-taken', scheduleId: string): void
  (e: 'mark-as-missed', scheduleId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { t } = useI18n()

// Computed properties
const sortedSchedule = computed(() => {
  return [...props.schedule].sort((a, b) => 
    new Date(a.scheduledTime).getTime() - new Date(b.scheduledTime).getTime()
  )
})

const formatTime = (dateString: string) => {
  return new Date(dateString).toLocaleTimeString('en', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  })
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'taken':
      return '✅'
    case 'missed':
      return '❌'
    case 'pending':
      return '⏰'
    default:
      return '⏰'
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'taken':
      return 'text-success'
    case 'missed':
      return 'text-error'
    case 'pending':
      return 'text-warning'
    default:
      return 'text-base-content-secondary'
  }
}

const handleMarkAsTaken = (scheduleId: string) => {
  emit('mark-as-taken', scheduleId)
}

const handleMarkAsMissed = (scheduleId: string) => {
  emit('mark-as-missed', scheduleId)
}

const isOverdue = (scheduledTime: string) => {
  const now = new Date()
  const scheduled = new Date(scheduledTime)
  return now > scheduled && now.getDate() === scheduled.getDate()
}
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <h2 class="card-title text-xl mb-4 text-base-content">
        <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        {{ t('dashboard.todaySchedule') }}
      </h2>

      <!-- Schedule Summary -->
      <div class="flex flex-wrap gap-2 mb-4">
        <div class="badge badge-success gap-1">
          <span>✅</span>
          {{ takenMedications.length }} {{ t('dashboard.taken') }}
        </div>
        <div class="badge badge-warning gap-1">
          <span>⏰</span>
          {{ pendingMedications.length }} {{ t('dashboard.upcoming') }}
        </div>
        <div class="badge badge-error gap-1">
          <span>❌</span>
          {{ missedMedications.length }} {{ t('dashboard.missed') }}
        </div>
      </div>

      <!-- Schedule List -->
      <div v-if="sortedSchedule.length === 0" class="text-center py-8">
        <div class="text-4xl mb-4">📅</div>
        <p class="text-base-content/70">{{ t('dashboard.noMedications') }}</p>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="item in sortedSchedule"
          :key="item.id"
          :class="[
            'flex items-center justify-between p-3 rounded-lg border transition-all duration-200',
            item.status === 'taken' ? 'bg-success/10 border-success/20' :
            item.status === 'missed' ? 'bg-error/10 border-error/20' :
            isOverdue(item.scheduledTime) ? 'bg-warning/10 border-warning/20' :
            'bg-base-200/50 border-base-300'
          ]"
        >
          <!-- Medication Info -->
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-lg">{{ getStatusIcon(item.status) }}</span>
              <h3 class="font-semibold text-base-content">
                {{ item.medication.name }}
              </h3>
              <span :class="`badge badge-sm ${getStatusColor(item.status)}`">
                {{ item.status }}
              </span>
            </div>
            
            <div class="text-sm text-base-content/70 space-y-1">
              <p>{{ item.medication.dosage }} • {{ item.medication.frequency }}</p>
              <p class="flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {{ formatTime(item.scheduledTime) }}
                <span v-if="item.takenAt" class="text-success">
                  (Taken at {{ formatTime(item.takenAt) }})
                </span>
              </p>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex items-center gap-2 ml-4">
            <button
              v-if="item.status === 'pending'"
              @click="handleMarkAsTaken(item.id)"
              class="btn btn-success btn-sm"
              :title="t('dashboard.markAsTaken')"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              {{ t('dashboard.markAsTaken') }}
            </button>
            
            <button
              v-if="item.status === 'pending'"
              @click="handleMarkAsMissed(item.id)"
              class="btn btn-error btn-sm"
              :title="t('dashboard.markAsMissed')"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              {{ t('dashboard.markAsMissed') }}
            </button>

            <div
              v-if="item.status === 'taken'"
              class="text-success text-sm font-medium"
            >
              {{ t('dashboard.taken') }}
            </div>

            <div
              v-if="item.status === 'missed'"
              class="text-error text-sm font-medium"
            >
              {{ t('dashboard.missed') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Instructions -->
      <div class="mt-4 p-3 bg-info/10 border border-info/20 rounded-lg">
        <p class="text-sm text-base-content/80">
          <strong>Tip:</strong> Click the buttons to mark medications as taken or missed. This helps track your medication adherence.
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  border-left: 4px solid;
  border-left-color: hsl(var(--color-secondary));
}
</style> 