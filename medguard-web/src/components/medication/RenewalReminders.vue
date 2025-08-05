<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { PrescriptionRenewal } from '@/types/medication'

const { t } = useI18n()

interface Props {
  renewals: PrescriptionRenewal[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
  renewal: [renewalId: string]
}>()

const currentTime = ref(new Date())
const selectedRenewal = ref<PrescriptionRenewal | null>(null)
const filterStatus = ref<'all' | 'active' | 'expired' | 'renewed'>('all')

let timer: NodeJS.Timeout | null = null

const updateTime = () => {
  currentTime.value = new Date()
}

const filteredRenewals = computed(() => {
  let filtered = props.renewals
  
  if (filterStatus.value !== 'all') {
    filtered = filtered.filter(renewal => renewal.status === filterStatus.value)
  }
  
  return filtered.sort((a, b) => new Date(a.expiryDate).getTime() - new Date(b.expiryDate).getTime())
})

const getDaysUntilExpiry = (expiryDate: string) => {
  const expiry = new Date(expiryDate)
  const diffTime = expiry.getTime() - currentTime.value.getTime()
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
  return diffDays
}

const getExpiryStatus = (expiryDate: string) => {
  const days = getDaysUntilExpiry(expiryDate)
  if (days < 0) return 'expired'
  if (days <= 7) return 'urgent'
  if (days <= 30) return 'warning'
  return 'safe'
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'badge-success'
    case 'expired': return 'badge-error'
    case 'renewed': return 'badge-info'
    default: return 'badge-neutral'
  }
}

const getExpiryColor = (status: string) => {
  switch (status) {
    case 'expired': return 'text-error'
    case 'urgent': return 'text-error'
    case 'warning': return 'text-warning'
    case 'safe': return 'text-success'
    default: return 'text-neutral'
  }
}

const getExpiryIcon = (status: string) => {
  switch (status) {
    case 'expired': return 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    case 'urgent': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'warning': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'safe': return 'M5 13l4 4L19 7'
    default: return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const formatCountdown = (expiryDate: string) => {
  const days = getDaysUntilExpiry(expiryDate)
  if (days < 0) {
    return `${Math.abs(days)} ${t('dashboard.daysOverdue')}`
  } else if (days === 0) {
    return t('dashboard.expiresToday')
  } else if (days === 1) {
    return t('dashboard.expiresTomorrow')
  } else {
    return `${days} ${t('dashboard.days')}`
  }
}

const urgentRenewals = computed(() => 
  props.renewals.filter(renewal => 
    renewal.status === 'active' && getDaysUntilExpiry(renewal.expiryDate) <= 7
  )
)

const expiredRenewals = computed(() => 
  props.renewals.filter(renewal => 
    renewal.status === 'active' && getDaysUntilExpiry(renewal.expiryDate) < 0
  )
)

const handleRenewal = (renewalId: string) => {
  emit('renewal', renewalId)
}

onMounted(() => {
  timer = setInterval(updateTime, 60000) // Update every minute
})

onUnmounted(() => {
  if (timer) {
    clearInterval(timer)
  }
})
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-6xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ t('dashboard.renewalReminders') }}
          <span v-if="urgentRenewals.length > 0" 
                class="badge badge-error badge-sm ml-2">{{ urgentRenewals.length }}</span>
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Critical Alerts -->
      <div v-if="expiredRenewals.length > 0 || urgentRenewals.length > 0" class="mb-6">
        <h4 class="font-semibold text-high-contrast mb-4">{{ t('dashboard.criticalRenewals') }}</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-if="expiredRenewals.length > 0" class="alert alert-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <h3 class="font-bold">{{ t('dashboard.expiredPrescriptions') }}</h3>
              <div class="text-sm">{{ expiredRenewals.length }} {{ t('dashboard.prescriptionsExpired') }}</div>
            </div>
          </div>
          
          <div v-if="urgentRenewals.length > 0" class="alert alert-warning">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h3 class="font-bold">{{ t('dashboard.urgentRenewals') }}</h3>
              <div class="text-sm">{{ urgentRenewals.length }} {{ t('dashboard.prescriptionsExpiringSoon') }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Filter Controls -->
      <div class="flex gap-2 mb-4">
        <button 
          v-for="status in ['all', 'active', 'expired', 'renewed']" 
          :key="status"
          @click="filterStatus = status"
          class="btn btn-sm"
          :class="filterStatus === status ? 'btn-primary' : 'btn-outline'"
        >
          {{ t(`dashboard.status.${status}`) }}
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Renewal List -->
        <div class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.renewals') }} ({{ filteredRenewals.length }})</h4>
          
          <div v-if="filteredRenewals.length === 0" class="text-center py-8">
            <p class="text-secondary-high-contrast">{{ t('dashboard.noRenewals') }}</p>
          </div>
          
          <div v-else class="space-y-3 max-h-96 overflow-y-auto">
            <div 
              v-for="renewal in filteredRenewals" 
              :key="renewal.id"
              @click="selectedRenewal = renewal"
              class="card bg-base-200 cursor-pointer hover:bg-base-300 transition-colors"
              :class="selectedRenewal?.id === renewal.id ? 'ring-2 ring-primary' : ''"
            >
              <div class="card-body p-4">
                <div class="flex justify-between items-start">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getExpiryIcon(getExpiryStatus(renewal.expiryDate))" />
                      </svg>
                      <span :class="getStatusColor(renewal.status)" class="badge">
                        {{ t(`dashboard.status.${renewal.status}`) }}
                      </span>
                    </div>
                    <h5 class="font-medium text-high-contrast">{{ renewal.originalPrescription.patientName }}</h5>
                    <p class="text-sm text-secondary-high-contrast">{{ renewal.originalPrescription.prescribingDoctor }}</p>
                    <div class="flex items-center gap-4 mt-2">
                      <span :class="getExpiryColor(getExpiryStatus(renewal.expiryDate))" class="text-sm font-medium">
                        {{ formatCountdown(renewal.expiryDate) }}
                      </span>
                      <span class="text-xs text-secondary-high-contrast">
                        {{ formatDate(renewal.expiryDate) }}
                      </span>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-sm text-secondary-high-contrast">
                      {{ renewal.refillsRemaining }}/{{ renewal.totalRefills }} {{ t('dashboard.refills') }}
                    </div>
                    <button 
                      v-if="renewal.status === 'active'"
                      @click.stop="handleRenewal(renewal.id)"
                      class="btn btn-xs btn-primary mt-2"
                    >
                      {{ t('dashboard.renew') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Renewal Details -->
        <div v-if="selectedRenewal" class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.renewalDetails') }}</h4>
          
          <div class="card bg-base-100">
            <div class="card-body">
              <div class="space-y-4">
                <!-- Patient Info -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.patientInfo') }}</h5>
                  <div class="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span class="text-secondary-high-contrast">{{ t('dashboard.patientName') }}:</span>
                      <span class="ml-2">{{ selectedRenewal.originalPrescription.patientName }}</span>
                    </div>
                    <div>
                      <span class="text-secondary-high-contrast">{{ t('dashboard.prescribingDoctor') }}:</span>
                      <span class="ml-2">{{ selectedRenewal.originalPrescription.prescribingDoctor }}</span>
                    </div>
                  </div>
                </div>

                <!-- Expiry Information -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.expiryInformation') }}</h5>
                  <div class="grid grid-cols-2 gap-4">
                    <div class="text-center p-3 bg-base-200 rounded-lg">
                      <div class="text-2xl font-bold" :class="getExpiryColor(getExpiryStatus(selectedRenewal.expiryDate))">
                        {{ formatCountdown(selectedRenewal.expiryDate) }}
                      </div>
                      <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.timeRemaining') }}</div>
                    </div>
                    <div class="text-center p-3 bg-base-200 rounded-lg">
                      <div class="text-2xl font-bold text-info">{{ formatDate(selectedRenewal.expiryDate) }}</div>
                      <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.expiryDate') }}</div>
                    </div>
                  </div>
                </div>

                <!-- Refill Information -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.refillInformation') }}</h5>
                  <div class="grid grid-cols-2 gap-4">
                    <div class="text-center p-3 bg-base-200 rounded-lg">
                      <div class="text-2xl font-bold text-warning">{{ selectedRenewal.refillsRemaining }}</div>
                      <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.refillsRemaining') }}</div>
                    </div>
                    <div class="text-center p-3 bg-base-200 rounded-lg">
                      <div class="text-2xl font-bold text-info">{{ selectedRenewal.totalRefills }}</div>
                      <div class="text-sm text-secondary-high-contrast">{{ t('dashboard.totalRefills') }}</div>
                    </div>
                  </div>
                </div>

                <!-- Medications -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.medications') }}</h5>
                  <div class="space-y-2">
                    <div 
                      v-for="medication in selectedRenewal.originalPrescription.medications" 
                      :key="medication.name"
                      class="p-3 bg-base-200 rounded-lg"
                    >
                      <div class="font-medium">{{ medication.name }}</div>
                      <div class="text-sm text-secondary-high-contrast">
                        {{ medication.strength }} - {{ medication.dosage }}
                      </div>
                      <div class="text-sm text-secondary-high-contrast">
                        {{ medication.frequency }} - {{ medication.quantity }} {{ t('dashboard.pills') }}
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Notes -->
                <div v-if="selectedRenewal.notes">
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.notes') }}</h5>
                  <p class="text-sm text-secondary-high-contrast bg-base-200 p-3 rounded-lg">
                    {{ selectedRenewal.notes }}
                  </p>
                </div>

                <!-- Action Buttons -->
                <div v-if="selectedRenewal.status === 'active'" class="border-t pt-4">
                  <div class="flex gap-2">
                    <button 
                      @click="handleRenewal(selectedRenewal.id)"
                      class="btn btn-primary flex-1"
                      :disabled="getDaysUntilExpiry(selectedRenewal.expiryDate) < 0"
                    >
                      <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      {{ t('dashboard.renewPrescription') }}
                    </button>
                    <button class="btn btn-outline">
                      {{ t('dashboard.contactDoctor') }}
                    </button>
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
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p>{{ t('dashboard.selectRenewal') }}</p>
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
</style> 