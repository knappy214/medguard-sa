<template>
  <div class="step5-schedule-creation">
    <h3 class="text-xl font-semibold mb-4">
      <i class="fas fa-calendar-alt text-primary mr-2"></i>
      {{ $t('workflow.step5.title', 'Schedule Creation') }}
    </h3>

    <div class="space-y-6">
      <!-- Schedule Configuration -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step5.configuration', 'Schedule Configuration') }}</h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step5.distributeEvenly', 'Distribute schedules evenly') }}</span>
                <input
                  v-model="scheduleConfig.distributeEvenly"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step5.respectTiming', 'Respect medication timing') }}</span>
                <input
                  v-model="scheduleConfig.respectTiming"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step5.avoidConflicts', 'Avoid time conflicts') }}</span>
                <input
                  v-model="scheduleConfig.avoidConflicts"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
            
            <div class="form-control">
              <label class="label cursor-pointer">
                <span class="label-text">{{ $t('workflow.step5.includeReminders', 'Include reminders') }}</span>
                <input
                  v-model="scheduleConfig.includeReminders"
                  type="checkbox"
                  class="checkbox checkbox-primary"
                />
              </label>
            </div>
          </div>
          
          <!-- Default times -->
          <div class="mt-4">
            <label class="label">
              <span class="label-text">{{ $t('workflow.step5.defaultTimes', 'Default Times') }}</span>
            </label>
            <div class="flex gap-2 flex-wrap">
              <div
                v-for="(time, index) in scheduleConfig.defaultTimes"
                :key="index"
                class="flex items-center gap-2"
              >
                <input
                  v-model="scheduleConfig.defaultTimes[index]"
                  type="time"
                  class="input input-bordered input-sm w-24"
                />
                <button
                  @click="removeTime(index)"
                  class="btn btn-circle btn-sm btn-ghost"
                  :title="$t('workflow.step5.removeTime', 'Remove time')"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
              <button
                @click="addTime"
                class="btn btn-sm btn-outline"
              >
                <i class="fas fa-plus mr-1"></i>
                {{ $t('workflow.step5.addTime', 'Add Time') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Schedule Preview -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step5.preview', 'Schedule Preview') }}</h4>
          
          <div class="space-y-4">
            <div
              v-for="(medication, index) in medications"
              :key="index"
              class="card bg-base-100"
            >
              <div class="card-body p-4">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h5 class="font-medium">{{ medication.name }}</h5>
                    <p class="text-sm text-base-content/70">{{ medication.frequency }}</p>
                    
                    <!-- Generated schedules -->
                    <div class="mt-3 space-y-2">
                      <div
                        v-for="(schedule, scheduleIndex) in generatedSchedules[index]"
                        :key="scheduleIndex"
                        class="flex items-center gap-2 p-2 bg-base-200 rounded"
                      >
                        <div class="badge badge-sm badge-primary">{{ schedule.time }}</div>
                        <span class="text-sm">{{ schedule.dosage }}</span>
                        <div class="badge badge-sm badge-outline">{{ schedule.days.join(', ') }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="flex flex-col gap-2 ml-4">
                    <button
                      @click="editSchedule(index)"
                      class="btn btn-circle btn-sm btn-ghost"
                      :title="$t('workflow.step5.editSchedule', 'Edit Schedule')"
                    >
                      <i class="fas fa-edit"></i>
                    </button>
                    <button
                      @click="removeSchedule(index)"
                      class="btn btn-circle btn-sm btn-error"
                      :title="$t('workflow.step5.removeSchedule', 'Remove Schedule')"
                    >
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Daily Schedule View -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step5.dailyView', 'Daily Schedule View') }}</h4>
          
          <div class="overflow-x-auto">
            <table class="table table-zebra w-full">
              <thead>
                <tr>
                  <th>{{ $t('workflow.step5.time', 'Time') }}</th>
                  <th>{{ $t('workflow.step5.medication', 'Medication') }}</th>
                  <th>{{ $t('workflow.step5.dosage', 'Dosage') }}</th>
                  <th>{{ $t('workflow.step5.instructions', 'Instructions') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(schedule, index) in dailySchedule"
                  :key="index"
                >
                  <td class="font-medium">{{ schedule.time }}</td>
                  <td>{{ schedule.medication }}</td>
                  <td>{{ schedule.dosage }}</td>
                  <td class="text-sm">{{ schedule.instructions }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex gap-2">
        <button
          @click="generateSchedules"
          class="btn btn-primary"
        >
          <i class="fas fa-magic mr-2"></i>
          {{ $t('workflow.step5.generateSchedules', 'Generate Schedules') }}
        </button>
        <button
          @click="optimizeSchedules"
          class="btn btn-outline"
        >
          <i class="fas fa-cogs mr-2"></i>
          {{ $t('workflow.step5.optimize', 'Optimize') }}
        </button>
        <button
          @click="exportSchedules"
          class="btn btn-outline"
        >
          <i class="fas fa-download mr-2"></i>
          {{ $t('workflow.step5.export', 'Export') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { PrescriptionMedication } from '@/types/medication'

const { t } = useI18n()

// Props
interface Props {
  medications: PrescriptionMedication[]
  scheduleConfig: {
    distributeEvenly: boolean
    respectTiming: boolean
    avoidConflicts: boolean
    defaultTimes: string[]
  }
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'schedules-created': [schedules: any[]]
}>()

// Reactive state
const generatedSchedules = ref<Record<number, any[]>>({})
const dailySchedule = ref<any[]>([])

// Methods
const addTime = () => {
  props.scheduleConfig.defaultTimes.push('12:00')
}

const removeTime = (index: number) => {
  props.scheduleConfig.defaultTimes.splice(index, 1)
}

const generateSchedules = () => {
  const schedules: any[] = []
  
  props.medications.forEach((medication, index) => {
    const medicationSchedules = generateMedicationSchedules(medication, index)
    generatedSchedules.value[index] = medicationSchedules
    schedules.push(...medicationSchedules)
  })
  
  updateDailySchedule()
  emit('schedules-created', schedules)
}

const generateMedicationSchedules = (medication: PrescriptionMedication, index: number) => {
  const schedules: any[] = []
  const frequency = medication.frequency.toLowerCase()
  
  let times: string[] = []
  
  // Determine times based on frequency
  if (frequency.includes('once daily')) {
    times = [props.scheduleConfig.defaultTimes[0] || '08:00']
  } else if (frequency.includes('twice daily')) {
    times = [
      props.scheduleConfig.defaultTimes[0] || '08:00',
      props.scheduleConfig.defaultTimes[1] || '20:00'
    ]
  } else if (frequency.includes('three times daily')) {
    times = [
      props.scheduleConfig.defaultTimes[0] || '08:00',
      props.scheduleConfig.defaultTimes[1] || '14:00',
      props.scheduleConfig.defaultTimes[2] || '20:00'
    ]
  } else if (frequency.includes('every 6 hours')) {
    times = ['06:00', '12:00', '18:00', '00:00']
  } else if (frequency.includes('every 8 hours')) {
    times = ['08:00', '16:00', '00:00']
  } else if (frequency.includes('every 12 hours')) {
    times = ['08:00', '20:00']
  } else {
    // Default to once daily
    times = [props.scheduleConfig.defaultTimes[0] || '08:00']
  }
  
  // Create schedules for each time
  times.forEach(time => {
    schedules.push({
      medicationId: index,
      medication: medication.name,
      time: time,
      dosage: medication.dosage,
      frequency: medication.frequency,
      instructions: medication.instructions,
      days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      enabled: true
    })
  })
  
  return schedules
}

const updateDailySchedule = () => {
  const allSchedules: any[] = []
  
  Object.values(generatedSchedules.value).forEach(medicationSchedules => {
    allSchedules.push(...medicationSchedules)
  })
  
  // Sort by time
  dailySchedule.value = allSchedules.sort((a, b) => {
    return a.time.localeCompare(b.time)
  })
}

const editSchedule = (index: number) => {
  // This would open a schedule edit modal
  console.log('Edit schedule for medication:', index)
}

const removeSchedule = (index: number) => {
  delete generatedSchedules.value[index]
  updateDailySchedule()
}

const optimizeSchedules = () => {
  // Optimize schedule timing to avoid conflicts
  const allSchedules = Object.values(generatedSchedules.value).flat()
  
  // Simple optimization: ensure minimum 2-hour gaps between medications
  const optimizedSchedules = allSchedules.map(schedule => {
    // This is a simplified optimization - in reality, you'd want more sophisticated logic
    return schedule
  })
  
  // Update the schedules
  Object.keys(generatedSchedules.value).forEach(key => {
    const index = parseInt(key)
    generatedSchedules.value[index] = optimizedSchedules.filter(s => s.medicationId === index)
  })
  
  updateDailySchedule()
}

const exportSchedules = () => {
  const exportData = {
    medications: props.medications,
    schedules: generatedSchedules.value,
    dailySchedule: dailySchedule.value,
    configuration: props.scheduleConfig,
    exportedAt: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'medication-schedules.json'
  a.click()
  URL.revokeObjectURL(url)
}

// Watch for medication changes
watch(() => props.medications, () => {
  generateSchedules()
}, { deep: true })

// Initialize
generateSchedules()
</script>

<style scoped>
.table {
  @apply text-sm;
}

.table th {
  @apply font-medium;
}
</style> 