<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MedicationSchedule } from '@/types/medication'

const { t } = useI18n()

interface Props {
  schedule: MedicationSchedule[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const selectedDate = ref(new Date())
const viewMode = ref<'day' | 'week' | 'month'>('day')

const today = new Date()
const todayString = today.toDateString()

const getDateString = (date: Date) => {
  return date.toDateString()
}

const getTimeString = (timeString: string) => {
  return new Date(timeString).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'taken': return 'text-success'
    case 'missed': return 'text-error'
    case 'pending': return 'text-warning'
    default: return 'text-neutral'
  }
}

const getStatusBgColor = (status: string) => {
  switch (status) {
    case 'taken': return 'bg-success/10'
    case 'missed': return 'bg-error/10'
    case 'pending': return 'bg-warning/10'
    default: return 'bg-neutral/10'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'taken': return 'M5 13l4 4L19 7'
    case 'missed': return 'M6 18L18 6M6 6l12 12'
    case 'pending': return 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z'
    default: return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

const filteredSchedule = computed(() => {
  const dateString = getDateString(selectedDate.value)
  return props.schedule.filter(item => {
    const itemDate = new Date(item.scheduledTime).toDateString()
    return itemDate === dateString
  }).sort((a, b) => new Date(a.scheduledTime).getTime() - new Date(b.scheduledTime).getTime())
})

const scheduleStats = computed(() => {
  const stats = {
    taken: 0,
    missed: 0,
    pending: 0,
    total: filteredSchedule.value.length
  }
  
  filteredSchedule.value.forEach(item => {
    stats[item.status as keyof typeof stats]++
  })
  
  return stats
})

const getWeekDays = () => {
  const days = []
  const startOfWeek = new Date(selectedDate.value)
  startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay())
  
  for (let i = 0; i < 7; i++) {
    const day = new Date(startOfWeek)
    day.setDate(day.getDate() + i)
    days.push(day)
  }
  
  return days
}

const getScheduleForDate = (date: Date) => {
  const dateString = getDateString(date)
  return props.schedule.filter(item => {
    const itemDate = new Date(item.scheduledTime).toDateString()
    return itemDate === dateString
  })
}

const isToday = (date: Date) => {
  return getDateString(date) === todayString
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
}

const navigateDate = (direction: 'prev' | 'next') => {
  const newDate = new Date(selectedDate.value)
  
  switch (viewMode.value) {
    case 'day':
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 1 : -1))
      break
    case 'week':
      newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7))
      break
    case 'month':
      newDate.setMonth(newDate.getMonth() + (direction === 'next' ? 1 : -1))
      break
  }
  
  selectedDate.value = newDate
}

const goToToday = () => {
  selectedDate.value = new Date()
}
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-6xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {{ t('dashboard.scheduleOverview') }}
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Navigation Controls -->
      <div class="flex justify-between items-center mb-6">
        <div class="flex gap-2">
          <button 
            v-for="mode in ['day', 'week', 'month']" 
            :key="mode"
            @click="viewMode = mode"
            class="btn btn-sm"
            :class="viewMode === mode ? 'btn-primary' : 'btn-outline'"
          >
            {{ t(`dashboard.view.${mode}`) }}
          </button>
        </div>
        
        <div class="flex items-center gap-2">
          <button @click="navigateDate('prev')" class="btn btn-sm btn-circle btn-outline">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <button @click="goToToday" class="btn btn-sm btn-outline">
            {{ t('dashboard.today') }}
          </button>
          
          <button @click="navigateDate('next')" class="btn btn-sm btn-circle btn-outline">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Schedule Statistics -->
      <div class="stats shadow w-full mb-6">
        <div class="stat">
          <div class="stat-figure text-success">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.taken') }}</div>
          <div class="stat-value text-success">{{ scheduleStats.taken }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.doses') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.missed') }}</div>
          <div class="stat-value text-error">{{ scheduleStats.missed }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.doses') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-warning">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.pending') }}</div>
          <div class="stat-value text-warning">{{ scheduleStats.pending }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.doses') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-info">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.total') }}</div>
          <div class="stat-value text-info">{{ scheduleStats.total }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.doses') }}</div>
        </div>
      </div>

      <!-- Schedule Display -->
      <div v-if="viewMode === 'day'" class="space-y-4">
        <h4 class="font-semibold text-high-contrast">
          {{ formatDate(selectedDate) }}
          <span v-if="isToday(selectedDate)" class="badge badge-primary ml-2">{{ t('dashboard.today') }}</span>
        </h4>
        
        <div v-if="filteredSchedule.length === 0" class="text-center py-8">
          <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <p class="text-secondary-high-contrast">{{ t('dashboard.noScheduleForDate') }}</p>
        </div>
        
        <div v-else class="space-y-3">
          <div 
            v-for="item in filteredSchedule" 
            :key="item.id"
            class="card bg-base-200"
            :class="isToday(selectedDate) ? 'ring-2 ring-primary' : ''"
          >
            <div class="card-body p-4">
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getStatusIcon(item.status)" />
                    </svg>
                    <span :class="getStatusColor(item.status)" class="font-medium">
                      {{ t(`dashboard.status.${item.status}`) }}
                    </span>
                  </div>
                  <h5 class="font-medium text-high-contrast">{{ item.medication.name }}</h5>
                  <p class="text-sm text-secondary-high-contrast">{{ item.medication.dosage }}</p>
                  <p v-if="item.notes" class="text-sm text-secondary-high-contrast mt-1">{{ item.notes }}</p>
                </div>
                <div class="text-right">
                  <div class="text-lg font-bold text-high-contrast">{{ getTimeString(item.scheduledTime) }}</div>
                  <div v-if="item.takenAt" class="text-xs text-secondary-high-contrast">
                    {{ t('dashboard.takenAt') }}: {{ getTimeString(item.takenAt) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Week View -->
      <div v-else-if="viewMode === 'week'" class="space-y-4">
        <h4 class="font-semibold text-high-contrast">{{ t('dashboard.weekView') }}</h4>
        
        <div class="grid grid-cols-7 gap-4">
          <div 
            v-for="day in getWeekDays()" 
            :key="getDateString(day)"
            class="space-y-2"
          >
            <div class="text-center">
              <div class="font-medium text-high-contrast">{{ formatDate(day) }}</div>
              <div v-if="isToday(day)" class="badge badge-primary badge-xs">{{ t('dashboard.today') }}</div>
            </div>
            
            <div class="space-y-1">
              <div 
                v-for="item in getScheduleForDate(day)" 
                :key="item.id"
                class="p-2 bg-base-200 rounded text-xs"
                :class="getStatusBgColor(item.status)"
              >
                <div class="font-medium truncate">{{ item.medication.name }}</div>
                <div class="text-secondary-high-contrast">{{ getTimeString(item.scheduledTime) }}</div>
                <div :class="getStatusColor(item.status)" class="font-medium">
                  {{ t(`dashboard.status.${item.status}`) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Month View (simplified) -->
      <div v-else class="space-y-4">
        <h4 class="font-semibold text-high-contrast">{{ t('dashboard.monthView') }}</h4>
        <div class="text-center py-8">
          <p class="text-secondary-high-contrast">{{ t('dashboard.monthViewComingSoon') }}</p>
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

.truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style> 