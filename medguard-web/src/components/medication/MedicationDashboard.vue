<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { 
  Medication, 
  MedicationSchedule, 
  StockAlert, 
  ParsedPrescription,
  MedicationInteraction,
  AdherenceTracking,
  PrescriptionRenewal,
  BatchProcessingResult
} from '@/types/medication'
import { medicationApi } from '@/services/medicationApi'
import MedicationCard from './MedicationCard.vue'
import ScheduleCard from './ScheduleCard.vue'
import StockAlertsCard from './StockAlertsCard.vue'
import AddMedicationModal from './AddMedicationModal.vue'
import PrescriptionWorkflow from './PrescriptionWorkflow.vue'
import PrescriptionHistoryPanel from './PrescriptionHistoryPanel.vue'
import InteractionWarningsPanel from './InteractionWarningsPanel.vue'
import StockStatusOverview from './StockStatusOverview.vue'
import AdherenceTrackingDashboard from './AdherenceTrackingDashboard.vue'
import BarcodeScanner from './BarcodeScanner.vue'
import RenewalReminders from './RenewalReminders.vue'
import ScheduleOverview from './ScheduleOverview.vue'
import ExportModal from './ExportModal.vue'
import ShareModal from './ShareModal.vue'

const { t } = useI18n()

// Reactive state
const medications = ref<Medication[]>([])
const schedule = ref<MedicationSchedule[]>([])
const alerts = ref<StockAlert[]>([])
const loading = ref(true)
const showAddModal = ref(false)
const showEditModal = ref(false)
const editingMedication = ref<Medication | null>(null)

// New state for enhanced features
const showPrescriptionWorkflow = ref(false)
const showPrescriptionHistory = ref(false)
const showInteractionWarnings = ref(false)
const showStockStatus = ref(false)
const showAdherenceTracking = ref(false)
const showBarcodeScanner = ref(false)
const showRenewalReminders = ref(false)
const showScheduleOverview = ref(false)
const showExportModal = ref(false)
const showShareModal = ref(false)

// Enhanced data
const prescriptionHistory = ref<ParsedPrescription[]>([])
const interactions = ref<MedicationInteraction[]>([])
const adherenceData = ref<AdherenceTracking[]>([])
const renewalReminders = ref<PrescriptionRenewal[]>([])
const scannedMedication = ref<Medication | null>(null)
const prescriptionWorkflowProgress = ref(0)

// Computed properties
const pendingMedications = computed(() => 
  schedule.value.filter(item => item.status === 'pending')
)

const takenMedications = ref<MedicationSchedule[]>([])
const missedMedications = ref<MedicationSchedule[]>([])

const lowStockMedications = computed(() => 
  medications.value.filter(med => med.stock <= med.minStock)
)

const unreadAlerts = computed(() => 
  alerts.value.filter(alert => !alert.isRead)
)

const criticalInteractions = computed(() => 
  interactions.value.filter(interaction => 
    interaction.severity === 'high' || interaction.severity === 'contraindicated'
  )
)

const todaySchedule = computed(() => 
  schedule.value.filter(item => {
    const today = new Date().toDateString()
    const scheduledDate = new Date(item.scheduledTime).toDateString()
    return scheduledDate === today
  })
)

const upcomingRenewals = computed(() => 
  renewalReminders.value.filter(reminder => 
    new Date(reminder.expiryDate) > new Date() && 
    reminder.status === 'active'
  ).sort((a, b) => new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime())
)

// Methods
const loadData = async () => {
  loading.value = true
  try {
    console.log('🔄 Loading enhanced dashboard data...')
    const [
      meds, 
      sched, 
      alrts, 
      history, 
      interactionsData, 
      adherence, 
      renewals
    ] = await Promise.all([
      medicationApi.getMedications(),
      medicationApi.getTodaySchedule(),
      medicationApi.getStockAlerts(),
      medicationApi.getPrescriptionHistory(),
      medicationApi.getMedicationInteractions(),
      medicationApi.getAdherenceTracking(),
      medicationApi.getRenewalReminders()
    ])
    
    medications.value = meds
    schedule.value = sched
    alerts.value = alrts
    prescriptionHistory.value = history
    interactions.value = interactionsData
    adherenceData.value = adherence
    renewalReminders.value = renewals
    
    console.log('✅ Updated enhanced reactive data:', {
      medicationsCount: medications.value.length,
      scheduleCount: schedule.value.length,
      alertsCount: alerts.value.length,
      historyCount: prescriptionHistory.value.length,
      interactionsCount: interactions.value.length,
      adherenceCount: adherenceData.value.length,
      renewalsCount: renewalReminders.value.length
    })
  } catch (error) {
    console.error('Failed to load enhanced dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const handleMarkAsTaken = async (scheduleId: string) => {
  try {
    const result = await medicationApi.markAsTaken(scheduleId)
    
    if (result.success) {
      console.log('✅ Medication marked as taken successfully')
      console.log(`📦 Stock deducted: ${result.stockDeducted}`)
      console.log(`📊 Remaining stock: ${result.remainingStock}`)
      
      if (result.lowStockAlert) {
        console.warn('⚠️ Low stock alert triggered')
      }
      
      await loadData()
    } else {
      if (result.error?.includes('Insufficient stock')) {
        console.error('❌ Insufficient stock:', result.error)
      } else {
        console.error('❌ Failed to mark medication as taken:', result.error)
      }
    }
  } catch (error) {
    console.error('Failed to mark medication as taken:', error)
  }
}

const handleMarkAsMissed = async (scheduleId: string) => {
  try {
    await medicationApi.markAsMissed(scheduleId)
    await loadData()
  } catch (error) {
    console.error('Failed to mark medication as missed:', error)
  }
}

const handleAddMedication = async (medicationData: any) => {
  console.log('📝 handleAddMedication called with data:', medicationData)
  try {
    console.log('🔄 Calling medicationApi.createMedication...')
    const result = await medicationApi.createMedication(medicationData)
    console.log('✅ Medication created successfully:', result)
    await loadData()
    showAddModal.value = false
  } catch (error) {
    console.error('❌ Failed to add medication:', error)
    console.error('🔍 Error in handleAddMedication:', {
      message: (error as any)?.message,
      status: (error as any)?.status,
      data: (error as any)?.data
    })
  }
}

const handleBulkAddMedications = async (medications: any[]) => {
  console.log('📝 handleBulkAddMedications called with data:', medications)
  try {
    console.log('🔄 Calling medicationApi.createBulkMedications...')
    const result = await medicationApi.createBulkMedications(medications)
    console.log('✅ Bulk medications created successfully:', result)
    await loadData()
    showAddModal.value = false
  } catch (error) {
    console.error('❌ Failed to add bulk medications:', error)
  }
}

const handleDeleteMedication = async (medicationId: string) => {
  try {
    await medicationApi.deleteMedication(medicationId)
    await loadData()
  } catch (error) {
    console.error('Failed to delete medication:', error)
  }
}

const handleEditMedication = (medication: Medication) => {
  editingMedication.value = medication
  showEditModal.value = true
}

const handleUpdateMedication = async (medicationData: any) => {
  try {
    await medicationApi.updateMedication(editingMedication.value!.id, medicationData)
    await loadData()
    showEditModal.value = false
    editingMedication.value = null
  } catch (error) {
    console.error('Failed to update medication:', error)
  }
}

const handleMarkAlertAsRead = async (alertId: string) => {
  try {
    await medicationApi.markAlertAsRead(alertId)
    await loadData()
  } catch (error) {
    console.error('Failed to mark alert as read:', error)
  }
}

// New enhanced methods
const handlePrescriptionWorkflowComplete = async (result: BatchProcessingResult) => {
  console.log('✅ Prescription workflow completed:', result)
  prescriptionWorkflowProgress.value = 100
  await loadData()
  showPrescriptionWorkflow.value = false
  
  // Show success message with summary
  const summary = {
    totalMedications: result.totalMedications,
    successfulPages: result.successfulPages,
    interactions: result.interactions.length,
    processingTime: result.processingTime
  }
  console.log('📊 Workflow Summary:', summary)
}

const handleBarcodeScan = async (barcode: string) => {
  try {
    console.log('📱 Barcode scanned:', barcode)
    const medication = await medicationApi.lookupMedicationByBarcode(barcode)
    scannedMedication.value = medication
    showBarcodeScanner.value = false
    
    if (medication) {
      console.log('✅ Medication found:', medication.name)
      // Optionally auto-add the medication
      // await handleAddMedication(medication)
    } else {
      console.log('❌ Medication not found for barcode:', barcode)
    }
  } catch (error) {
    console.error('Failed to lookup medication by barcode:', error)
  }
}

const handleExportData = async (format: string, dataType: string) => {
  try {
    console.log('📤 Exporting data:', { format, dataType })
    const exportData = await medicationApi.exportMedicationData(format, dataType)
    console.log('✅ Export completed:', exportData)
    showExportModal.value = false
  } catch (error) {
    console.error('Failed to export data:', error)
  }
}

const handleShareWithProvider = async (providerData: any) => {
  try {
    console.log('📤 Sharing with healthcare provider:', providerData)
    const result = await medicationApi.shareWithHealthcareProvider(providerData)
    console.log('✅ Sharing completed:', result)
    showShareModal.value = false
  } catch (error) {
    console.error('Failed to share with provider:', error)
  }
}

const handleRenewalReminder = async (renewalId: string) => {
  try {
    console.log('🔄 Processing renewal reminder:', renewalId)
    await medicationApi.processRenewalReminder(renewalId)
    await loadData()
  } catch (error) {
    console.error('Failed to process renewal reminder:', error)
  }
}

// Lifecycle
onMounted(() => {
  loadData()
})

// Watch for schedule changes to update computed properties
watch(schedule, (newSchedule) => {
  takenMedications.value = newSchedule.filter(item => item.status === 'taken')
  missedMedications.value = newSchedule.filter(item => item.status === 'missed')
}, { immediate: true })
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
      <!-- Enhanced Stats Overview -->
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

        <!-- New enhanced stats -->
        <div class="stat">
          <div class="stat-figure text-info">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.prescriptions') }}</div>
          <div class="stat-value text-info">{{ prescriptionHistory.length }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.processed') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-accent">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.adherence') }}</div>
          <div class="stat-value text-accent">{{ adherenceData.length > 0 ? Math.round(adherenceData.reduce((acc, item) => acc + item.adherenceRate, 0) / adherenceData.length) : 0 }}%</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.average') }}</div>
        </div>
      </div>

      <!-- Enhanced Action Buttons -->
      <div class="flex flex-wrap gap-4">
        <!-- Prescription Workflow Button -->
        <button 
          @click="showPrescriptionWorkflow = true"
          class="btn btn-primary gap-2"
          :disabled="prescriptionWorkflowProgress > 0 && prescriptionWorkflowProgress < 100"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ t('dashboard.prescriptionWorkflow') }}
          <div v-if="prescriptionWorkflowProgress > 0 && prescriptionWorkflowProgress < 100" 
               class="loading loading-spinner loading-xs"></div>
        </button>

        <!-- Barcode Scanner Button -->
        <button 
          @click="showBarcodeScanner = true"
          class="btn btn-secondary gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V6a1 1 0 00-1-1H5a1 1 0 00-1 1v1a1 1 0 001 1zm12 0h2a1 1 0 001-1V6a1 1 0 00-1-1h-2a1 1 0 00-1 1v1a1 1 0 001 1zM5 20h2a1 1 0 001-1v-1a1 1 0 00-1-1H5a1 1 0 00-1 1v1a1 1 0 001 1z" />
          </svg>
          {{ t('dashboard.scanBarcode') }}
        </button>

        <!-- Add Medication Button -->
        <button 
          @click="showAddModal = true"
          class="btn btn-accent gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ t('dashboard.addMedication') }}
        </button>

        <!-- Export Button -->
        <button 
          @click="showExportModal = true"
          class="btn btn-outline gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ t('dashboard.export') }}
        </button>

        <!-- Share Button -->
        <button 
          @click="showShareModal = true"
          class="btn btn-outline gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
          </svg>
          {{ t('dashboard.share') }}
        </button>
        
        <!-- Refresh Button -->
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

      <!-- Enhanced Dashboard Grid -->
      <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        <!-- Schedule Card -->
        <ScheduleCard 
          :schedule="schedule"
          :pending-medications="pendingMedications"
          :taken-medications="takenMedications"
          :missed-medications="missedMedications"
          @mark-as-taken="handleMarkAsTaken"
          @mark-as-missed="handleMarkAsMissed"
        />
        
        <!-- Stock Alerts Card -->
        <StockAlertsCard 
          :alerts="alerts"
          :unread-alerts="unreadAlerts"
          @mark-as-read="handleMarkAlertAsRead"
        />

        <!-- Interaction Warnings Panel -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title text-xl text-high-contrast">
              <svg class="w-6 h-6 mr-2 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {{ t('dashboard.interactions') }}
              <span v-if="criticalInteractions.length > 0" 
                    class="badge badge-error badge-sm">{{ criticalInteractions.length }}</span>
            </h2>
            
            <div v-if="interactions.length === 0" class="text-center py-4">
              <p class="text-secondary-high-contrast">{{ t('dashboard.noInteractions') }}</p>
            </div>
            
            <div v-else class="space-y-2">
              <div v-for="interaction in criticalInteractions.slice(0, 3)" 
                   :key="interaction.description"
                   class="alert alert-warning">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <h3 class="font-bold">{{ interaction.severity.toUpperCase() }}</h3>
                  <div class="text-xs">{{ interaction.description }}</div>
                </div>
              </div>
              
              <button v-if="interactions.length > 3" 
                      @click="showInteractionWarnings = true"
                      class="btn btn-sm btn-outline w-full">
                {{ t('dashboard.viewAllInteractions') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Stock Status Overview -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title text-xl text-high-contrast">
              <svg class="w-6 h-6 mr-2 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
              {{ t('dashboard.stockStatus') }}
            </h2>
            
            <div class="space-y-2">
              <div v-for="medication in lowStockMedications.slice(0, 5)" 
                   :key="medication.id"
                   class="flex justify-between items-center p-2 rounded-lg"
                   :class="medication.stock === 0 ? 'bg-error/10' : 'bg-warning/10'">
                <span class="font-medium">{{ medication.name }}</span>
                <span class="badge" 
                      :class="medication.stock === 0 ? 'badge-error' : 'badge-warning'">
                  {{ medication.stock }} {{ t('dashboard.pillsRemaining') }}
                </span>
              </div>
              
              <button v-if="lowStockMedications.length > 5" 
                      @click="showStockStatus = true"
                      class="btn btn-sm btn-outline w-full">
                {{ t('dashboard.viewAllStock') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Renewal Reminders -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title text-xl text-high-contrast">
              <svg class="w-6 h-6 mr-2 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ t('dashboard.renewals') }}
              <span v-if="upcomingRenewals.length > 0" 
                    class="badge badge-accent badge-sm">{{ upcomingRenewals.length }}</span>
            </h2>
            
            <div v-if="upcomingRenewals.length === 0" class="text-center py-4">
              <p class="text-secondary-high-contrast">{{ t('dashboard.noRenewals') }}</p>
            </div>
            
            <div v-else class="space-y-2">
              <div v-for="renewal in upcomingRenewals.slice(0, 3)" 
                   :key="renewal.id"
                   class="alert alert-info">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div>
                  <h3 class="font-bold">{{ renewal.originalPrescription.patientName }}</h3>
                  <div class="text-xs">{{ t('dashboard.expires') }}: {{ new Date(renewal.expiryDate).toLocaleDateString() }}</div>
                </div>
              </div>
              
              <button v-if="upcomingRenewals.length > 3" 
                      @click="showRenewalReminders = true"
                      class="btn btn-sm btn-outline w-full">
                {{ t('dashboard.viewAllRenewals') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Schedule Overview -->
        <div class="card bg-base-100 shadow-sm">
          <div class="card-body">
            <h2 class="card-title text-xl text-high-contrast">
              <svg class="w-6 h-6 mr-2 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {{ t('dashboard.todaySchedule') }}
            </h2>
            
            <div v-if="todaySchedule.length === 0" class="text-center py-4">
              <p class="text-secondary-high-contrast">{{ t('dashboard.noScheduleToday') }}</p>
            </div>
            
            <div v-else class="space-y-2">
              <div v-for="item in todaySchedule.slice(0, 5)" 
                   :key="item.id"
                   class="flex justify-between items-center p-2 rounded-lg"
                   :class="item.status === 'taken' ? 'bg-success/10' : item.status === 'missed' ? 'bg-error/10' : 'bg-warning/10'">
                <div>
                  <span class="font-medium">{{ item.medication.name }}</span>
                  <div class="text-xs text-secondary-high-contrast">{{ item.medication.dosage }}</div>
                </div>
                <div class="text-right">
                  <div class="text-sm font-medium">{{ new Date(item.scheduledTime).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) }}</div>
                  <span class="badge badge-sm" 
                        :class="item.status === 'taken' ? 'badge-success' : item.status === 'missed' ? 'badge-error' : 'badge-warning'">
                    {{ item.status }}
                  </span>
                </div>
              </div>
              
              <button v-if="todaySchedule.length > 5" 
                      @click="showScheduleOverview = true"
                      class="btn btn-sm btn-outline w-full">
                {{ t('dashboard.viewFullSchedule') }}
              </button>
            </div>
          </div>
        </div>
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

    <!-- Modals -->
    <AddMedicationModal 
      v-if="showAddModal"
      @close="showAddModal = false"
      @add="handleAddMedication"
      @bulk-add="handleBulkAddMedications"
    />

    <AddMedicationModal 
      v-if="showEditModal"
      :medication="editingMedication"
      mode="edit"
      @close="showEditModal = false"
      @add="handleUpdateMedication"
    />

    <!-- Enhanced Modals -->
    <PrescriptionWorkflow 
      v-if="showPrescriptionWorkflow"
      @close="showPrescriptionWorkflow = false"
      @complete="handlePrescriptionWorkflowComplete"
    />

    <PrescriptionHistoryPanel 
      v-if="showPrescriptionHistory"
      :history="prescriptionHistory"
      @close="showPrescriptionHistory = false"
    />

    <InteractionWarningsPanel 
      v-if="showInteractionWarnings"
      :interactions="interactions"
      @close="showInteractionWarnings = false"
    />

    <StockStatusOverview 
      v-if="showStockStatus"
      :medications="medications"
      @close="showStockStatus = false"
    />

    <AdherenceTrackingDashboard 
      v-if="showAdherenceTracking"
      :adherence-data="adherenceData"
      @close="showAdherenceTracking = false"
    />

    <BarcodeScanner 
      v-if="showBarcodeScanner"
      @close="showBarcodeScanner = false"
      @scan="handleBarcodeScan"
    />

    <RenewalReminders 
      v-if="showRenewalReminders"
      :renewals="renewalReminders"
      @close="showRenewalReminders = false"
      @renewal="handleRenewalReminder"
    />

    <ScheduleOverview 
      v-if="showScheduleOverview"
      :schedule="schedule"
      @close="showScheduleOverview = false"
    />

    <ExportModal 
      v-if="showExportModal"
      @close="showExportModal = false"
      @export="handleExportData"
    />

    <ShareModal 
      v-if="showShareModal"
      :medications="medications"
      @close="showShareModal = false"
      @share="handleShareWithProvider"
    />
  </div>
</template>

<style scoped>
.medication-dashboard {
  min-height: 100vh;
}

/* Enhanced styling for better visual hierarchy */
.stats .stat {
  @apply transition-all duration-200 hover:shadow-md;
}

.card {
  @apply transition-all duration-200 hover:shadow-lg;
}

.btn {
  @apply transition-all duration-200;
}

/* Progress indicator styling */
.loading-spinner {
  @apply animate-spin;
}

/* Alert styling for better contrast */
.alert {
  @apply border-l-4;
}

.alert-warning {
  @apply bg-warning/10 border-warning text-warning-content;
}

.alert-error {
  @apply bg-error/10 border-error text-error-content;
}

.alert-info {
  @apply bg-info/10 border-info text-info-content;
}

.alert-success {
  @apply bg-success/10 border-success text-success-content;
}
</style> 