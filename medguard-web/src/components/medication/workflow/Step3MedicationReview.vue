<template>
  <div class="step3-medication-review">
    <h3 class="text-xl font-semibold mb-4">
      <i class="fas fa-pills text-primary mr-2"></i>
      {{ $t('workflow.step3.title', 'Review Medications') }}
    </h3>

    <div class="space-y-6">
      <!-- Summary -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step3.summary', 'Summary') }}</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step3.totalMedications', 'Total Medications') }}</div>
              <div class="font-medium text-lg">{{ medications.length }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step3.validated', 'Validated') }}</div>
              <div class="font-medium text-lg text-success">{{ validatedCount }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step3.warnings', 'Warnings') }}</div>
              <div class="font-medium text-lg text-warning">{{ warningCount }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step3.errors', 'Errors') }}</div>
              <div class="font-medium text-lg text-error">{{ errorCount }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Medications List -->
      <div class="space-y-4">
        <div
          v-for="(medication, index) in medications"
          :key="index"
          class="card bg-base-100"
        >
          <div class="card-body">
            <div class="flex items-start justify-between mb-4">
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-2">
                  <h5 class="font-medium">{{ medication.name }}</h5>
                  <div class="badge badge-sm" :class="getValidationBadgeClass(index)">
                    {{ getValidationStatus(index) }}
                  </div>
                </div>
                
                <!-- Medication details -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div class="form-control">
                    <label class="label">
                      <span class="label-text text-sm">{{ $t('workflow.step3.strength', 'Strength') }}</span>
                    </label>
                    <input
                      v-model="medication.strength"
                      type="text"
                      class="input input-bordered input-sm"
                      :class="getFieldClass(index, 'strength')"
                    />
                  </div>
                  <div class="form-control">
                    <label class="label">
                      <span class="label-text text-sm">{{ $t('workflow.step3.dosage', 'Dosage') }}</span>
                    </label>
                    <input
                      v-model="medication.dosage"
                      type="text"
                      class="input input-bordered input-sm"
                      :class="getFieldClass(index, 'dosage')"
                    />
                  </div>
                  <div class="form-control">
                    <label class="label">
                      <span class="label-text text-sm">{{ $t('workflow.step3.frequency', 'Frequency') }}</span>
                    </label>
                    <select
                      v-model="medication.frequency"
                      class="select select-bordered select-sm"
                      :class="getFieldClass(index, 'frequency')"
                    >
                      <option value="Once daily">{{ $t('workflow.step3.onceDaily', 'Once daily') }}</option>
                      <option value="Twice daily">{{ $t('workflow.step3.twiceDaily', 'Twice daily') }}</option>
                      <option value="Three times daily">{{ $t('workflow.step3.threeTimesDaily', 'Three times daily') }}</option>
                      <option value="Every 6 hours">{{ $t('workflow.step3.every6Hours', 'Every 6 hours') }}</option>
                      <option value="Every 8 hours">{{ $t('workflow.step3.every8Hours', 'Every 8 hours') }}</option>
                      <option value="Every 12 hours">{{ $t('workflow.step3.every12Hours', 'Every 12 hours') }}</option>
                      <option value="As needed">{{ $t('workflow.step3.asNeeded', 'As needed') }}</option>
                    </select>
                  </div>
                  <div class="form-control">
                    <label class="label">
                      <span class="label-text text-sm">{{ $t('workflow.step3.quantity', 'Quantity') }}</span>
                    </label>
                    <input
                      v-model.number="medication.quantity"
                      type="number"
                      class="input input-bordered input-sm"
                      :class="getFieldClass(index, 'quantity')"
                    />
                  </div>
                </div>
                
                <div class="form-control mt-3">
                  <label class="label">
                    <span class="label-text text-sm">{{ $t('workflow.step3.instructions', 'Instructions') }}</span>
                  </label>
                  <textarea
                    v-model="medication.instructions"
                    class="textarea textarea-bordered textarea-sm"
                    :class="getFieldClass(index, 'instructions')"
                    rows="2"
                  ></textarea>
                </div>
              </div>
              
              <!-- Action buttons -->
              <div class="flex flex-col gap-2 ml-4">
                <button
                  @click="validateMedication(index)"
                  class="btn btn-circle btn-sm btn-primary"
                  :title="$t('workflow.step3.validate', 'Validate')"
                >
                  <i class="fas fa-check"></i>
                </button>
                <button
                  @click="removeMedication(index)"
                  class="btn btn-circle btn-sm btn-error"
                  :title="$t('workflow.step3.remove', 'Remove')"
                >
                  <i class="fas fa-trash"></i>
                </button>
              </div>
            </div>
            
            <!-- Validation messages -->
            <div v-if="validationResults[index]" class="mt-3">
              <div v-if="validationResults[index].warnings.length > 0" class="alert alert-warning alert-sm">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                  <div class="font-medium">{{ $t('workflow.step3.warnings', 'Warnings') }}</div>
                  <ul class="text-sm mt-1">
                    <li v-for="warning in validationResults[index].warnings" :key="warning">{{ warning }}</li>
                  </ul>
                </div>
              </div>
              
              <div v-if="validationResults[index].errors.length > 0" class="alert alert-error alert-sm">
                <i class="fas fa-times-circle"></i>
                <div>
                  <div class="font-medium">{{ $t('workflow.step3.errors', 'Errors') }}</div>
                  <ul class="text-sm mt-1">
                    <li v-for="error in validationResults[index].errors" :key="error">{{ error }}</li>
                  </ul>
                </div>
              </div>
              
              <div v-if="validationResults[index].suggestions.length > 0" class="alert alert-info alert-sm">
                <i class="fas fa-lightbulb"></i>
                <div>
                  <div class="font-medium">{{ $t('workflow.step3.suggestions', 'Suggestions') }}</div>
                  <ul class="text-sm mt-1">
                    <li v-for="suggestion in validationResults[index].suggestions" :key="suggestion">{{ suggestion }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Add medication button -->
      <div class="text-center">
        <button
          @click="addMedication"
          class="btn btn-outline btn-primary"
        >
          <i class="fas fa-plus mr-2"></i>
          {{ $t('workflow.step3.addMedication', 'Add Medication') }}
        </button>
      </div>

      <!-- Bulk actions -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step3.bulkActions', 'Bulk Actions') }}</h4>
          <div class="flex gap-2 flex-wrap">
            <button
              @click="validateAll"
              class="btn btn-sm btn-primary"
            >
              <i class="fas fa-check-double mr-2"></i>
              {{ $t('workflow.step3.validateAll', 'Validate All') }}
            </button>
            <button
              @click="clearAll"
              class="btn btn-sm btn-outline"
            >
              <i class="fas fa-eraser mr-2"></i>
              {{ $t('workflow.step3.clearAll', 'Clear All') }}
            </button>
            <button
              @click="exportMedications"
              class="btn btn-sm btn-outline"
            >
              <i class="fas fa-download mr-2"></i>
              {{ $t('workflow.step3.export', 'Export') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { medicationApi } from '@/services/medicationApi'
import type { PrescriptionMedication, MedicationValidation } from '@/types/medication'

const { t } = useI18n()

// Props
interface Props {
  medications: PrescriptionMedication[]
  validationResults: Record<string, MedicationValidation>
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'medications-updated': [medications: PrescriptionMedication[]]
  'validation-complete': [validations: Record<string, MedicationValidation>]
}>()

// Computed properties
const validatedCount = computed(() => {
  return Object.values(props.validationResults).filter(v => v.isValid).length
})

const warningCount = computed(() => {
  return Object.values(props.validationResults).reduce((sum, v) => sum + v.warnings.length, 0)
})

const errorCount = computed(() => {
  return Object.values(props.validationResults).reduce((sum, v) => sum + v.errors.length, 0)
})

// Methods
const getValidationBadgeClass = (index: number) => {
  const validation = props.validationResults[index]
  if (!validation) return 'badge-neutral'
  if (validation.isValid) return 'badge-success'
  if (validation.errors.length > 0) return 'badge-error'
  return 'badge-warning'
}

const getValidationStatus = (index: number) => {
  const validation = props.validationResults[index]
  if (!validation) return t('workflow.step3.notValidated', 'Not Validated')
  if (validation.isValid) return t('workflow.step3.valid', 'Valid')
  if (validation.errors.length > 0) return t('workflow.step3.invalid', 'Invalid')
  return t('workflow.step3.warnings', 'Warnings')
}

const getFieldClass = (index: number, field: string) => {
  const validation = props.validationResults[index]
  if (!validation) return ''
  
  // Check if field has errors
  const hasErrors = validation.errors.some(error => 
    error.toLowerCase().includes(field.toLowerCase())
  )
  
  return hasErrors ? 'input-error' : ''
}

const validateMedication = async (index: number) => {
  const medication = props.medications[index]
  if (!medication) return
  
  try {
    const validation = await medicationApi.validateMedication({
      name: medication.name,
      strength: medication.strength,
      dosage: medication.dosage,
      frequency: medication.frequency,
      instructions: medication.instructions,
      stock: medication.quantity,
      minStock: Math.ceil(medication.quantity * 0.2),
      category: 'Prescription',
      time: '08:00'
    })
    
    emit('validation-complete', {
      ...props.validationResults,
      [index]: validation
    })
  } catch (error) {
    console.error('Validation failed:', error)
  }
}

const validateAll = async () => {
  for (let i = 0; i < props.medications.length; i++) {
    await validateMedication(i)
  }
}

const addMedication = () => {
  const newMedication: PrescriptionMedication = {
    name: '',
    strength: '',
    dosage: '',
    frequency: 'Once daily',
    quantity: 30,
    refills: 0,
    instructions: '',
    drugDatabaseId: undefined,
    interactions: [],
    sideEffects: [],
    contraindications: []
  }
  
  emit('medications-updated', [...props.medications, newMedication])
}

const removeMedication = (index: number) => {
  const updatedMedications = props.medications.filter((_, i) => i !== index)
  emit('medications-updated', updatedMedications)
}

const clearAll = () => {
  emit('medications-updated', [])
}

const exportMedications = () => {
  const data = {
    medications: props.medications,
    validationResults: props.validationResults,
    exportDate: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'medications-export.json'
  a.click()
  URL.revokeObjectURL(url)
}

// Watch for changes and emit updates
watch(() => props.medications, (medications) => {
  emit('medications-updated', medications)
}, { deep: true })
</script>

<style scoped>
.alert-sm {
  @apply p-2 text-sm;
}

.alert-sm .alert-icon {
  @apply w-4 h-4;
}
</style> 