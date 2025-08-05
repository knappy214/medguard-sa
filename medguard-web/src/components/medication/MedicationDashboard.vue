<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Medication, MedicationSchedule, StockAlert } from '@/types/medication'
import { medicationApi } from '@/services/medicationApi'
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
const showEditModal = ref(false)
const editingMedication = ref<Medication | null>(null)

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
    console.log('🔄 Loading dashboard data...')
    // Use the enhanced API service which automatically handles mock vs real API
    const [meds, sched, alrts] = await Promise.all([
      medicationApi.getMedications(),
      medicationApi.getTodaySchedule(),
      medicationApi.getStockAlerts()
    ])
    console.log('📦 Received medications:', meds)
    console.log('📅 Received schedule:', sched)
    console.log('🚨 Received alerts:', alrts)
    
    medications.value = meds
    schedule.value = sched
    alerts.value = alrts
    
    console.log('✅ Updated reactive data:', {
      medicationsCount: medications.value.length,
      scheduleCount: schedule.value.length,
      alertsCount: alerts.value.length
    })
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    // Show user-friendly error message
    // You can add a toast notification here
  } finally {
    loading.value = false
  }
}

const handleMarkAsTaken = async (scheduleId: string) => {
  try {
    const result = await medicationApi.markAsTaken(scheduleId)
    
    if (result.success) {
      // Show success message with stock information
      console.log('✅ Medication marked as taken successfully')
      console.log(`📦 Stock deducted: ${result.stockDeducted}`)
      console.log(`📊 Remaining stock: ${result.remainingStock}`)
      
      if (result.lowStockAlert) {
        console.warn('⚠️ Low stock alert triggered')
        // You could show a toast notification here
      }
      
      await loadData() // Reload data
    } else {
      // Handle specific error cases
      if (result.error?.includes('Insufficient stock')) {
        console.error('❌ Insufficient stock:', result.error)
        // You could show a specific error message to the user
      } else {
        console.error('❌ Failed to mark medication as taken:', result.error)
      }
    }
  } catch (error) {
    console.error('Failed to mark medication as taken:', error)
    // Show user-friendly error message
  }
}

const handleMarkAsMissed = async (scheduleId: string) => {
  try {
    await medicationApi.markAsMissed(scheduleId)
    await loadData() // Reload data
  } catch (error) {
    console.error('Failed to mark medication as missed:', error)
    // Show user-friendly error message
  }
}

const handleAddMedication = async (medicationData: any) => {
  console.log('📝 handleAddMedication called with data:', medicationData)
  try {
    console.log('🔄 Calling medicationApi.createMedication...')
    const result = await medicationApi.createMedication(medicationData)
    console.log('✅ Medication created successfully:', result)
    await loadData() // Reload data
    showAddModal.value = false
  } catch (error) {
    console.error('❌ Failed to add medication:', error)
    console.error('🔍 Error in handleAddMedication:', {
      message: (error as any)?.message,
      status: (error as any)?.status,
      data: (error as any)?.data
    })
    // Show user-friendly error message
  }
}

const handleBulkAddMedications = async (medications: any[]) => {
  console.log('📝 handleBulkAddMedications called with data:', medications)
  try {
    console.log('🔄 Calling medicationApi.createBulkMedications...')
    const result = await medicationApi.createBulkMedications(medications)
    console.log('✅ Bulk medications created successfully:', result)
    await loadData() // Reload data
    showAddModal.value = false
  } catch (error) {
    console.error('❌ Failed to add bulk medications:', error)
    // Show user-friendly error message
  }
}

const handleDeleteMedication = async (medicationId: string) => {
  try {
    await medicationApi.deleteMedication(medicationId)
    await loadData() // Reload data
  } catch (error) {
    console.error('Failed to delete medication:', error)
    // Show user-friendly error message
  }
}

const handleEditMedication = (medication: Medication) => {
  editingMedication.value = medication
  showEditModal.value = true
}

const handleUpdateMedication = async (medicationData: any) => {
  try {
    await medicationApi.updateMedication(editingMedication.value!.id, medicationData)
    await loadData() // Reload data
    showEditModal.value = false
    editingMedication.value = null
  } catch (error) {
    console.error('Failed to update medication:', error)
    // Show user-friendly error message
  }
}

const handleMarkAlertAsRead = async (alertId: string) => {
  try {
    await medicationApi.markAlertAsRead(alertId)
    await loadData() // Reload data
  } catch (error) {
    console.error('Failed to mark alert as read:', error)
    // Show user-friendly error message
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
      <span class="ml-4 text-high-contrast">{{ t('common.loading') }}</span>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-6">
      <!-- Stats Overview -->
      <div class="stats shadow w-full bg-base-100">
        <div class="stat">
          <div class="stat-figure text-primary">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.medicationList') }}</div>
          <div class="stat-value text-primary">{{ medications.length }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.activePrescriptions') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-success">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.taken') }}</div>
          <div class="stat-value text-success">{{ takenMedications.length }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.today') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-warning">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.pending') }}</div>
          <div class="stat-value text-warning">{{ pendingMedications.length }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.remaining') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-error">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.alerts') }}</div>
          <div class="stat-value text-error">{{ unreadAlerts.length }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.unread') }}</div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex flex-wrap gap-4">
        <button 
          @click="showAddModal = true"
          class="btn btn-primary gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ t('dashboard.addMedication') }}
        </button>
        
        <button 
          @click="loadData"
          class="btn btn-outline gap-2"
          :disabled="loading"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          {{ t('common.refresh') }}
        </button>
      </div>

      <!-- Dashboard Cards -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ScheduleCard 
          :schedule="schedule"
          :pending-medications="pendingMedications"
          :taken-medications="takenMedications"
          :missed-medications="missedMedications"
          @mark-as-taken="handleMarkAsTaken"
          @mark-as-missed="handleMarkAsMissed"
        />
        
        <StockAlertsCard 
          :alerts="alerts"
          :unread-alerts="unreadAlerts"
          @mark-as-read="handleMarkAlertAsRead"
        />
      </div>

      <!-- Medication List -->
      <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
          <h2 class="card-title text-xl text-high-contrast">
            <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            {{ t('dashboard.medicationList') }}
          </h2>
          
          <div v-if="medications.length === 0" class="text-center py-8">
            <div class="text-secondary-high-contrast mb-4">
              <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <p class="text-lg font-medium text-high-contrast">{{ t('dashboard.noMedications') }}</p>
              <p class="text-secondary-high-contrast">{{ t('dashboard.addYourFirstMedication') }}</p>
            </div>
            <button 
              @click="showAddModal = true"
              class="btn btn-primary"
            >
              {{ t('dashboard.addMedication') }}
            </button>
          </div>
          
          <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            <MedicationCard 
              v-for="medication in medications" 
              :key="medication.id"
              :medication="medication"
              @delete="handleDeleteMedication"
              @edit="handleEditMedication"
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
      @bulk-add="handleBulkAddMedications"
    />

    <!-- Edit Medication Modal -->
    <AddMedicationModal 
      v-if="showEditModal"
      :medication="editingMedication"
      mode="edit"
      @close="showEditModal = false"
      @add="handleUpdateMedication"
    />
  </div>
</template>

<style scoped>
.medication-dashboard {
  min-height: 100vh;
}
</style> 