<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Medication, MedicationSchedule, StockAlert } from '@/types/medication'
import { medicationApi, mockMedications, mockSchedule, mockAlerts } from '@/services/medicationApi'
import MedicationCard from './MedicationCard.vue'
import ScheduleCard from './ScheduleCard.vue'
import StockAlertsCard from './StockAlertsCard.vue'
import AddMedicationModal from './AddMedicationModal.vue'

const { t } = useI18n()

// Reactive state
const medications = ref<Medication[]>([])
const schedule = ref<MedicationSchedule[]>([])
const alerts = ref<StockAlert[]>([])
const loading = ref(true)
const showAddModal = ref(false)

// Computed properties
const pendingMedications = computed(() => 
  schedule.value.filter(item => item.status === 'pending')
)

const takenMedications = computed(() => 
  schedule.value.filter(item => item.status === 'taken')
)

const missedMedications = computed(() => 
  schedule.value.filter(item => item.status === 'missed')
)

const lowStockMedications = computed(() => 
  medications.value.filter(med => med.stock <= med.minStock)
)

const unreadAlerts = computed(() => 
  alerts.value.filter(alert => !alert.isRead)
)

// Methods
const loadData = async () => {
  loading.value = true
  try {
    // In development, use mock data
    if (import.meta.env.DEV) {
      medications.value = mockMedications
      schedule.value = mockSchedule
      alerts.value = mockAlerts
    } else {
      // In production, use real API
      const [meds, sched, alrts] = await Promise.all([
        medicationApi.getMedications(),
        medicationApi.getTodaySchedule(),
        medicationApi.getStockAlerts()
      ])
      medications.value = meds
      schedule.value = sched
      alerts.value = alrts
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const handleMarkAsTaken = async (scheduleId: string) => {
  try {
    if (import.meta.env.DEV) {
      // Update mock data
      const scheduleItem = schedule.value.find(item => item.id === scheduleId)
      if (scheduleItem) {
        scheduleItem.status = 'taken'
        scheduleItem.takenAt = new Date().toISOString()
      }
    } else {
      await medicationApi.markAsTaken(scheduleId)
      await loadData() // Reload data
    }
  } catch (error) {
    console.error('Failed to mark medication as taken:', error)
  }
}

const handleMarkAsMissed = async (scheduleId: string) => {
  try {
    if (import.meta.env.DEV) {
      // Update mock data
      const scheduleItem = schedule.value.find(item => item.id === scheduleId)
      if (scheduleItem) {
        scheduleItem.status = 'missed'
      }
    } else {
      await medicationApi.markAsMissed(scheduleId)
      await loadData() // Reload data
    }
  } catch (error) {
    console.error('Failed to mark medication as missed:', error)
  }
}

const handleAddMedication = async (medicationData: any) => {
  try {
    if (import.meta.env.DEV) {
      // Add to mock data
      const newMedication: Medication = {
        id: Date.now().toString(),
        ...medicationData,
        isActive: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
      medications.value.push(newMedication)
    } else {
      await medicationApi.createMedication(medicationData)
      await loadData() // Reload data
    }
    showAddModal.value = false
  } catch (error) {
    console.error('Failed to add medication:', error)
  }
}

const handleDeleteMedication = async (medicationId: string) => {
  try {
    if (import.meta.env.DEV) {
      // Remove from mock data
      medications.value = medications.value.filter(med => med.id !== medicationId)
    } else {
      await medicationApi.deleteMedication(medicationId)
      await loadData() // Reload data
    }
  } catch (error) {
    console.error('Failed to delete medication:', error)
  }
}

const handleMarkAlertAsRead = async (alertId: string) => {
  try {
    if (import.meta.env.DEV) {
      // Update mock data
      const alert = alerts.value.find(a => a.id === alertId)
      if (alert) {
        alert.isRead = true
      }
    } else {
      await medicationApi.markAlertAsRead(alertId)
      await loadData() // Reload data
    }
  } catch (error) {
    console.error('Failed to mark alert as read:', error)
  }
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="medication-dashboard">
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-12">
      <div class="loading loading-spinner loading-lg text-primary"></div>
      <span class="ml-4 text-base-content-secondary">{{ t('common.loading') }}</span>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-6">
      <!-- Stats Overview -->
      <div class="stats stats-vertical lg:stats-horizontal shadow w-full">
        <div class="stat">
          <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title">{{ t('dashboard.taken') }}</div>
          <div class="stat-value text-primary">{{ takenMedications.length }}</div>
          <div class="stat-desc">{{ t('dashboard.todaySchedule') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-warning">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title">{{ t('dashboard.upcoming') }}</div>
          <div class="stat-value text-warning">{{ pendingMedications.length }}</div>
          <div class="stat-desc">{{ t('dashboard.todaySchedule') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-error">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title">{{ t('dashboard.missed') }}</div>
          <div class="stat-value text-error">{{ missedMedications.length }}</div>
          <div class="stat-desc">{{ t('dashboard.todaySchedule') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-info">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="stat-title">{{ t('dashboard.stockAlerts') }}</div>
          <div class="stat-value text-info">{{ unreadAlerts.length }}</div>
          <div class="stat-desc">{{ t('dashboard.lowStock') }}</div>
        </div>
      </div>

      <!-- Main Content Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- Today's Schedule -->
        <div class="lg:col-span-2">
          <ScheduleCard
            :schedule="schedule"
            :pending-medications="pendingMedications"
            :taken-medications="takenMedications"
            :missed-medications="missedMedications"
            @mark-as-taken="handleMarkAsTaken"
            @mark-as-missed="handleMarkAsMissed"
          />
        </div>

        <!-- Stock Alerts -->
        <div class="lg:col-span-1">
          <StockAlertsCard
            :alerts="alerts"
            :unread-alerts="unreadAlerts"
            @mark-as-read="handleMarkAlertAsRead"
          />
        </div>
      </div>

      <!-- Medication List -->
      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <div class="flex justify-between items-center mb-4">
            <h2 class="card-title text-xl">
              <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              {{ t('dashboard.medicationList') }}
            </h2>
            <button 
              @click="showAddModal = true"
              class="btn btn-primary btn-sm"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              {{ t('dashboard.addMedication') }}
            </button>
          </div>

          <div v-if="medications.length === 0" class="text-center py-8">
            <div class="text-6xl mb-4">💊</div>
            <p class="text-base-content-secondary">{{ t('dashboard.noMedications') }}</p>
          </div>

          <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <MedicationCard
              v-for="medication in medications"
              :key="medication.id"
              :medication="medication"
              @delete="handleDeleteMedication"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Add Medication Modal -->
    <AddMedicationModal
      v-if="showAddModal"
      @close="showAddModal = false"
      @add="handleAddMedication"
    />
  </div>
</template>

<style scoped>
.medication-dashboard {
  min-height: 100vh;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .stats {
    @apply stats-vertical;
  }
}
</style> 