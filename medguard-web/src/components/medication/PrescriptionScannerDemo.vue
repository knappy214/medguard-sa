<template>
  <div class="p-6">
    <div class="max-w-4xl mx-auto">
      <h1 class="text-3xl font-bold mb-6">{{ t('prescriptionScanner.title') }}</h1>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <!-- Scanner Demo -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title">{{ t('prescriptionScanner.scanPrescription') }}</h2>
            <p class="text-base-content/70 mb-4">
              {{ t('prescriptionScanner.uploadHint') }}
            </p>
            
            <PrescriptionScanner
              mode="both"
              :allow-batch="true"
              :auto-process="false"
              @add="handleAddMedication"
              @bulk-add="handleBulkAdd"
              @error="handleError"
              @close="handleClose"
            />
          </div>
        </div>
        
        <!-- Instructions -->
        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title">How to Use</h2>
            <div class="space-y-3 text-sm">
              <div class="flex items-start gap-2">
                <span class="badge badge-primary">1</span>
                <p>Click the "Scan Prescription" button to open the scanner</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="badge badge-primary">2</span>
                <p>Use your camera or upload an image of your prescription</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="badge badge-primary">3</span>
                <p>Adjust image preprocessing options if needed</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="badge badge-primary">4</span>
                <p>Review and edit extracted medication information</p>
              </div>
              <div class="flex items-start gap-2">
                <span class="badge badge-primary">5</span>
                <p>Select medications and add them to your list</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Results -->
      <div v-if="addedMedications.length > 0" class="card bg-base-100 shadow-xl">
        <div class="card-body">
          <h2 class="card-title">Added Medications</h2>
          <div class="space-y-2">
            <div 
              v-for="(medication, index) in addedMedications"
              :key="index"
              class="card bg-base-200"
            >
              <div class="card-body p-4">
                <h3 class="font-medium">{{ medication.name }}</h3>
                <div class="text-sm text-base-content/70 space-y-1">
                  <p><strong>Dosage:</strong> {{ medication.dosage }}</p>
                  <p><strong>Frequency:</strong> {{ medication.frequency }}</p>
                  <p v-if="medication.instructions"><strong>Instructions:</strong> {{ medication.instructions }}</p>
                  <p v-if="medication.prescribingDoctor"><strong>Doctor:</strong> {{ medication.prescribingDoctor }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Error Display -->
      <div v-if="error" class="alert alert-error mt-4">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PrescriptionScanner from './PrescriptionScanner.vue'
import type { MedicationFormData, BulkMedicationEntry } from '@/types/medication'

const { t } = useI18n()

const addedMedications = ref<(MedicationFormData | BulkMedicationEntry)[]>([])
const error = ref('')

const handleAddMedication = (medication: MedicationFormData) => {
  addedMedications.value.push(medication)
  console.log('Added single medication:', medication)
}

const handleBulkAdd = (medications: BulkMedicationEntry[]) => {
  addedMedications.value.push(...medications)
  console.log('Added bulk medications:', medications)
}

const handleError = (errorMessage: string) => {
  error.value = errorMessage
  console.error('Scanner error:', errorMessage)
}

const handleClose = () => {
  console.log('Scanner closed')
}
</script> 