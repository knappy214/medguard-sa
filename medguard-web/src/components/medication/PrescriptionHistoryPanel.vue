<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ParsedPrescription } from '@/types/medication'

const { t } = useI18n()

interface Props {
  history: ParsedPrescription[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const selectedPrescription = ref<ParsedPrescription | null>(null)
const filterStatus = ref<'all' | 'active' | 'expired' | 'completed' | 'renewed'>('all')

const filteredHistory = computed(() => {
  if (filterStatus.value === 'all') return props.history
  return props.history.filter(prescription => prescription.status === filterStatus.value)
})

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active': return 'badge-success'
    case 'expired': return 'badge-error'
    case 'completed': return 'badge-info'
    case 'renewed': return 'badge-warning'
    default: return 'badge-neutral'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const getTotalCost = (prescription: ParsedPrescription) => {
  return prescription.medications.reduce((total, med) => total + (med.cost || 0), 0)
}
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-4xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {{ t('dashboard.prescriptionHistory') }}
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Filter Controls -->
      <div class="flex gap-2 mb-4">
        <button 
          v-for="status in ['all', 'active', 'expired', 'completed', 'renewed']" 
          :key="status"
          @click="filterStatus = status"
          class="btn btn-sm"
          :class="filterStatus === status ? 'btn-primary' : 'btn-outline'"
        >
          {{ t(`dashboard.status.${status}`) }}
        </button>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Prescription List -->
        <div class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.prescriptions') }} ({{ filteredHistory.length }})</h4>
          
          <div v-if="filteredHistory.length === 0" class="text-center py-8">
            <p class="text-secondary-high-contrast">{{ t('dashboard.noPrescriptions') }}</p>
          </div>
          
          <div v-else class="space-y-3 max-h-96 overflow-y-auto">
            <div 
              v-for="prescription in filteredHistory" 
              :key="prescription.id"
              @click="selectedPrescription = prescription"
              class="card bg-base-200 cursor-pointer hover:bg-base-300 transition-colors"
              :class="selectedPrescription?.id === prescription.id ? 'ring-2 ring-primary' : ''"
            >
              <div class="card-body p-4">
                <div class="flex justify-between items-start">
                  <div>
                    <h5 class="font-medium text-high-contrast">{{ prescription.patientName }}</h5>
                    <p class="text-sm text-secondary-high-contrast">{{ prescription.prescribingDoctor }}</p>
                    <p class="text-xs text-secondary-high-contrast">{{ formatDate(prescription.prescriptionDate) }}</p>
                  </div>
                  <div class="text-right">
                    <span :class="getStatusColor(prescription.status)" class="badge">
                      {{ t(`dashboard.status.${prescription.status}`) }}
                    </span>
                    <div class="text-sm text-secondary-high-contrast mt-1">
                      {{ prescription.medications.length }} {{ t('dashboard.medications') }}
                    </div>
                    <div v-if="prescription.totalCost" class="text-sm font-medium">
                      R{{ prescription.totalCost.toFixed(2) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Prescription Details -->
        <div v-if="selectedPrescription" class="space-y-4">
          <h4 class="font-semibold text-high-contrast">{{ t('dashboard.prescriptionDetails') }}</h4>
          
          <div class="card bg-base-100">
            <div class="card-body">
              <div class="space-y-4">
                <!-- Patient Info -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.patientInfo') }}</h5>
                  <div class="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span class="text-secondary-high-contrast">{{ t('dashboard.patientName') }}:</span>
                      <span class="ml-2">{{ selectedPrescription.patientName }}</span>
                    </div>
                    <div>
                      <span class="text-secondary-high-contrast">{{ t('dashboard.prescribingDoctor') }}:</span>
                      <span class="ml-2">{{ selectedPrescription.prescribingDoctor }}</span>
                    </div>
                    <div>
                      <span class="text-secondary-high-contrast">{{ t('dashboard.prescriptionDate') }}:</span>
                      <span class="ml-2">{{ formatDate(selectedPrescription.prescriptionDate) }}</span>
                    </div>
                    <div v-if="selectedPrescription.pharmacy">
                      <span class="text-secondary-high-contrast">{{ t('dashboard.pharmacy') }}:</span>
                      <span class="ml-2">{{ selectedPrescription.pharmacy }}</span>
                    </div>
                  </div>
                </div>

                <!-- Medications -->
                <div>
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.medications') }}</h5>
                  <div class="space-y-2">
                    <div 
                      v-for="medication in selectedPrescription.medications" 
                      :key="medication.name"
                      class="p-3 bg-base-200 rounded-lg"
                    >
                      <div class="flex justify-between items-start">
                        <div>
                          <div class="font-medium">{{ medication.name }}</div>
                          <div class="text-sm text-secondary-high-contrast">
                            {{ medication.strength }} - {{ medication.dosage }}
                          </div>
                          <div class="text-sm text-secondary-high-contrast">
                            {{ medication.frequency }} - {{ medication.quantity }} {{ t('dashboard.pills') }}
                          </div>
                          <div class="text-sm text-secondary-high-contrast">
                            {{ medication.instructions }}
                          </div>
                        </div>
                        <div class="text-right">
                          <div v-if="medication.cost" class="font-medium">
                            R{{ medication.cost.toFixed(2) }}
                          </div>
                          <div class="text-sm text-secondary-high-contrast">
                            {{ medication.refills }} {{ t('dashboard.refills') }}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Summary -->
                <div class="border-t pt-4">
                  <div class="flex justify-between items-center">
                    <span class="font-medium">{{ t('dashboard.totalCost') }}:</span>
                    <span class="font-bold text-lg">R{{ getTotalCost(selectedPrescription).toFixed(2) }}</span>
                  </div>
                  <div class="flex justify-between items-center mt-2">
                    <span class="text-secondary-high-contrast">{{ t('dashboard.totalMedications') }}:</span>
                    <span>{{ selectedPrescription.medications.length }}</span>
                  </div>
                </div>

                <!-- Notes -->
                <div v-if="selectedPrescription.notes">
                  <h5 class="font-medium text-high-contrast mb-2">{{ t('dashboard.notes') }}</h5>
                  <p class="text-sm text-secondary-high-contrast bg-base-200 p-3 rounded-lg">
                    {{ selectedPrescription.notes }}
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
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p>{{ t('dashboard.selectPrescription') }}</p>
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