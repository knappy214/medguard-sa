<template>
  <div class="prescription-medication-card card bg-base-100 shadow-lg hover:shadow-xl transition-all duration-300">
    <div class="card-body p-6">
      <!-- Header with Confidence Score and Status -->
      <div class="flex items-start justify-between mb-4">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-2">
            <h3 class="font-bold text-lg text-base-content">
              <span v-if="isEditing" class="flex items-center gap-2">
                <input 
                  v-model="editingMedication.name"
                  class="input input-bordered input-sm w-full"
                  :placeholder="$t('prescription.card.medicationName', 'Medication name')"
                />
              </span>
              <span v-else>{{ medication.name }}</span>
            </h3>
            <div class="flex items-center gap-1">
              <!-- Confidence Score Indicator -->
              <div class="tooltip" :data-tip="$t('prescription.card.confidenceScore', 'OCR Confidence Score')">
                <div class="flex items-center gap-1">
                  <div 
                    class="w-3 h-3 rounded-full"
                    :class="confidenceColorClass"
                  ></div>
                  <span class="text-xs font-medium">{{ confidenceScore }}%</span>
                </div>
              </div>
              
              <!-- Validation Status -->
              <div v-if="validation" class="tooltip" :data-tip="validationStatusText">
                <i 
                  :class="validationIconClass"
                  class="text-lg"
                ></i>
              </div>
            </div>
          </div>
          
          <div class="text-sm text-base-content/70">
            <span v-if="isEditing" class="flex items-center gap-2">
              <input 
                v-model="editingMedication.genericName"
                class="input input-bordered input-sm w-full"
                :placeholder="$t('prescription.card.genericName', 'Generic name')"
              />
            </span>
            <span v-else>{{ medication.genericName || $t('prescription.card.noGeneric', 'No generic name') }}</span>
          </div>
        </div>
        
        <!-- Action Buttons -->
        <div class="flex items-center gap-2">
          <button 
            v-if="!isEditing"
            @click="startEditing"
            class="btn btn-ghost btn-sm"
            :title="$t('prescription.card.edit', 'Edit medication')"
          >
            <i class="fas fa-edit"></i>
          </button>
          <div v-else class="flex items-center gap-1">
            <button 
              @click="saveChanges"
              class="btn btn-success btn-sm"
              :title="$t('prescription.card.save', 'Save changes')"
            >
              <i class="fas fa-check"></i>
            </button>
            <button 
              @click="cancelEditing"
              class="btn btn-error btn-sm"
              :title="$t('prescription.card.cancel', 'Cancel editing')"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
          
          <!-- Approval Status -->
          <div class="dropdown dropdown-end">
            <button class="btn btn-ghost btn-sm">
              <i class="fas fa-check-circle" :class="approvalIconClass"></i>
            </button>
            <ul class="dropdown-content menu bg-base-100 rounded-box shadow-lg border border-base-300 min-w-[150px] z-50">
              <li>
                <button @click="approveMedication" class="text-success">
                  <i class="fas fa-check"></i>
                  {{ $t('prescription.card.approve', 'Approve') }}
                </button>
              </li>
              <li>
                <button @click="rejectMedication" class="text-error">
                  <i class="fas fa-times"></i>
                  {{ $t('prescription.card.reject', 'Reject') }}
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Medication Details -->
      <div class="grid grid-cols-2 gap-4 mb-4">
        <div class="space-y-2">
          <label class="label">
            <span class="label-text font-medium">{{ $t('prescription.card.strength', 'Strength') }}</span>
          </label>
          <div v-if="isEditing">
            <input 
              v-model="editingMedication.strength"
              class="input input-bordered input-sm w-full"
              :placeholder="$t('prescription.card.strengthPlaceholder', 'e.g., 500mg')"
            />
          </div>
          <div v-else class="text-sm">{{ medication.strength }}</div>
        </div>
        
        <div class="space-y-2">
          <label class="label">
            <span class="label-text font-medium">{{ $t('prescription.card.dosage', 'Dosage') }}</span>
          </label>
          <div v-if="isEditing">
            <input 
              v-model="editingMedication.dosage"
              class="input input-bordered input-sm w-full"
              :placeholder="$t('prescription.card.dosagePlaceholder', 'e.g., 1 tablet')"
            />
          </div>
          <div v-else class="text-sm">{{ medication.dosage }}</div>
        </div>
        
        <div class="space-y-2">
          <label class="label">
            <span class="label-text font-medium">{{ $t('prescription.card.frequency', 'Frequency') }}</span>
          </label>
          <div v-if="isEditing">
            <input 
              v-model="editingMedication.frequency"
              class="input input-bordered input-sm w-full"
              :placeholder="$t('prescription.card.frequencyPlaceholder', 'e.g., Twice daily')"
            />
          </div>
          <div v-else class="text-sm">{{ medication.frequency }}</div>
        </div>
        
        <div class="space-y-2">
          <label class="label">
            <span class="label-text font-medium">{{ $t('prescription.card.quantity', 'Quantity') }}</span>
          </label>
          <div v-if="isEditing">
            <input 
              v-model.number="editingMedication.quantity"
              type="number"
              class="input input-bordered input-sm w-full"
              :placeholder="$t('prescription.card.quantityPlaceholder', 'Number of pills')"
            />
          </div>
          <div v-else class="text-sm">{{ medication.quantity }} {{ $t('prescription.card.pills', 'pills') }}</div>
        </div>
      </div>

      <!-- Instructions -->
      <div class="space-y-2 mb-4">
        <label class="label">
          <span class="label-text font-medium">{{ $t('prescription.card.instructions', 'Instructions') }}</span>
        </label>
        <div v-if="isEditing">
          <textarea 
            v-model="editingMedication.instructions"
            class="textarea textarea-bordered w-full text-sm"
            rows="2"
            :placeholder="$t('prescription.card.instructionsPlaceholder', 'Take with food, avoid alcohol...')"
          ></textarea>
        </div>
        <div v-else class="text-sm text-base-content/80">{{ medication.instructions }}</div>
      </div>

      <!-- Validation Errors and Warnings -->
      <div v-if="validation && (validation.errors?.length || validation.warnings?.length)" class="mb-4">
        <div v-if="validation.errors?.length" class="alert alert-error mb-2">
          <i class="fas fa-exclamation-triangle"></i>
          <div>
            <h4 class="font-bold">{{ $t('prescription.card.validationErrors', 'Validation Errors') }}</h4>
            <ul class="text-sm">
              <li v-for="error in validation.errors" :key="error">{{ error }}</li>
            </ul>
          </div>
        </div>
        
        <div v-if="validation.warnings?.length" class="alert alert-warning">
          <i class="fas fa-exclamation-circle"></i>
          <div>
            <h4 class="font-bold">{{ $t('prescription.card.validationWarnings', 'Validation Warnings') }}</h4>
            <ul class="text-sm">
              <li v-for="warning in validation.warnings" :key="warning">{{ warning }}</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Drug Interactions -->
      <div v-if="interactions?.length" class="mb-4">
        <div class="collapse collapse-arrow bg-base-200">
          <input type="checkbox" />
          <div class="collapse-title font-medium flex items-center gap-2">
            <i class="fas fa-exclamation-triangle text-warning"></i>
            {{ $t('prescription.card.drugInteractions', 'Drug Interactions') }}
            <span class="badge badge-warning badge-sm">{{ interactions.length }}</span>
          </div>
          <div class="collapse-content">
            <div v-for="interaction in interactions" :key="interaction.description" class="mb-3 p-3 bg-base-100 rounded-lg">
              <div class="flex items-center gap-2 mb-2">
                <span :class="`badge badge-${getSeverityColor(interaction.severity)} badge-sm`">
                  {{ interaction.severity.toUpperCase() }}
                </span>
                <span class="text-sm font-medium">{{ interaction.medications.join(', ') }}</span>
              </div>
              <p class="text-sm mb-2">{{ interaction.description }}</p>
              <div class="text-xs text-base-content/70">
                <p><strong>{{ $t('prescription.card.recommendations', 'Recommendations') }}:</strong> {{ interaction.recommendations }}</p>
                <p><strong>{{ $t('prescription.card.evidence', 'Evidence') }}:</strong> {{ interaction.evidence }}</p>
                <p><strong>{{ $t('prescription.card.source', 'Source') }}:</strong> {{ interaction.source }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Generic Alternatives -->
      <div v-if="alternatives?.length" class="mb-4">
        <div class="collapse collapse-arrow bg-base-200">
          <input type="checkbox" />
          <div class="collapse-title font-medium flex items-center gap-2">
            <i class="fas fa-tags text-info"></i>
            {{ $t('prescription.card.genericAlternatives', 'Generic Alternatives') }}
            <span class="badge badge-info badge-sm">{{ alternatives.length }}</span>
          </div>
          <div class="collapse-content">
            <div v-for="alternative in alternatives" :key="alternative.id" class="mb-3 p-3 bg-base-100 rounded-lg">
              <div class="flex items-center justify-between mb-2">
                <h5 class="font-medium">{{ alternative.name }}</h5>
                <span class="text-success font-bold">R{{ alternative.cost?.toFixed(2) }}</span>
              </div>
              <p class="text-sm text-base-content/70 mb-2">{{ alternative.description }}</p>
              <div class="flex items-center gap-2">
                <span class="badge badge-outline badge-sm">{{ alternative.strength }}</span>
                <span class="badge badge-outline badge-sm">{{ alternative.dosageForm }}</span>
                <span class="badge badge-outline badge-sm">{{ alternative.manufacturer }}</span>
              </div>
              <div class="mt-2">
                <button class="btn btn-primary btn-sm">
                  {{ $t('prescription.card.selectAlternative', 'Select Alternative') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stock Information -->
      <div v-if="stockInfo" class="mb-4">
        <div class="collapse collapse-arrow bg-base-200">
          <input type="checkbox" />
          <div class="collapse-title font-medium flex items-center gap-2">
            <i class="fas fa-boxes text-primary"></i>
            {{ $t('prescription.card.stockInformation', 'Stock Information') }}
          </div>
          <div class="collapse-content">
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p><strong>{{ $t('prescription.card.daysUntilStockout', 'Days until stockout') }}:</strong></p>
                <p class="text-warning font-medium">{{ stockInfo.days_until_stockout || 'N/A' }}</p>
              </div>
              <div>
                <p><strong>{{ $t('prescription.card.predictedStockout', 'Predicted stockout') }}:</strong></p>
                <p class="text-sm">{{ formatDate(stockInfo.predicted_stockout_date) }}</p>
              </div>
              <div>
                <p><strong>{{ $t('prescription.card.recommendedOrder', 'Recommended order') }}:</strong></p>
                <p class="text-info font-medium">{{ stockInfo.recommended_order_quantity }} {{ $t('prescription.card.pills', 'pills') }}</p>
              </div>
              <div>
                <p><strong>{{ $t('prescription.card.orderDate', 'Order date') }}:</strong></p>
                <p class="text-sm">{{ formatDate(stockInfo.recommended_order_date) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Compliance Information -->
      <div v-if="compliance" class="mb-4">
        <div class="collapse collapse-arrow bg-base-200">
          <input type="checkbox" />
          <div class="collapse-title font-medium flex items-center gap-2">
            <i class="fas fa-shield-alt" :class="compliance.isValid ? 'text-success' : 'text-error'"></i>
            {{ $t('prescription.card.compliance', 'SA Compliance') }}
            <span :class="`badge badge-${compliance.isValid ? 'success' : 'error'} badge-sm`">
              {{ compliance.isValid ? $t('prescription.card.compliant', 'Compliant') : $t('prescription.card.nonCompliant', 'Non-Compliant') }}
            </span>
          </div>
          <div class="collapse-content">
            <div class="space-y-2 text-sm">
              <div v-if="compliance.errors?.length" class="alert alert-error">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                  <h5 class="font-bold">{{ $t('prescription.card.complianceErrors', 'Compliance Errors') }}</h5>
                  <ul>
                    <li v-for="error in compliance.errors" :key="error">{{ error }}</li>
                  </ul>
                </div>
              </div>
              
              <div v-if="compliance.warnings?.length" class="alert alert-warning">
                <i class="fas fa-exclamation-circle"></i>
                <div>
                  <h5 class="font-bold">{{ $t('prescription.card.complianceWarnings', 'Compliance Warnings') }}</h5>
                  <ul>
                    <li v-for="warning in compliance.warnings" :key="warning">{{ warning }}</li>
                  </ul>
                </div>
              </div>
              
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <h6 class="font-medium">{{ $t('prescription.card.requiredFields', 'Required Fields') }}</h6>
                  <ul class="text-xs space-y-1">
                    <li v-for="(value, key) in compliance.requiredFields" :key="key" class="flex items-center gap-1">
                      <i :class="value ? 'fas fa-check text-success' : 'fas fa-times text-error'"></i>
                      {{ formatFieldName(key) }}
                    </li>
                  </ul>
                </div>
                <div>
                  <h6 class="font-medium">{{ $t('prescription.card.formatCompliance', 'Format Compliance') }}</h6>
                  <ul class="text-xs space-y-1">
                    <li v-for="(value, key) in compliance.formatCompliance" :key="key" class="flex items-center gap-1">
                      <i :class="value ? 'fas fa-check text-success' : 'fas fa-times text-error'"></i>
                      {{ formatFieldName(key) }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cost Information -->
      <div class="flex items-center justify-between text-sm">
        <div>
          <span class="font-medium">{{ $t('prescription.card.cost', 'Cost') }}:</span>
          <span class="text-primary font-bold">R{{ (medication.cost || 0).toFixed(2) }}</span>
        </div>
        <div>
          <span class="font-medium">{{ $t('prescription.card.refills', 'Refills') }}:</span>
          <span class="text-info font-medium">{{ medication.refills || 0 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { 
  PrescriptionMedication, 
  MedicationValidation, 
  MedicationInteraction,
  DrugDatabaseEntry,
  StockAnalytics,
  SouthAfricanPrescriptionValidation
} from '@/types/medication'

interface Props {
  medication: PrescriptionMedication
  validation?: MedicationValidation
  interactions?: MedicationInteraction[]
  alternatives?: DrugDatabaseEntry[]
  stockInfo?: StockAnalytics
  compliance?: SouthAfricanPrescriptionValidation
}

interface Emits {
  (e: 'update', medication: PrescriptionMedication): void
  (e: 'validate', medicationId: string): void
  (e: 'approve', medicationId: string, approved: boolean): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { t } = useI18n()

// Reactive state
const isEditing = ref(false)
const editingMedication = ref<PrescriptionMedication>({ ...props.medication })

// Computed properties
const confidenceScore = computed(() => {
  // Mock confidence score - in real app, this would come from OCR data
  return Math.floor(Math.random() * 40) + 60 // 60-100%
})

const confidenceColorClass = computed(() => {
  if (confidenceScore.value >= 90) return 'bg-success'
  if (confidenceScore.value >= 80) return 'bg-warning'
  return 'bg-error'
})

const validationIconClass = computed(() => {
  if (!props.validation) return 'fas fa-question-circle text-base-content/40'
  if (props.validation.errors?.length) return 'fas fa-times-circle text-error'
  if (props.validation.warnings?.length) return 'fas fa-exclamation-triangle text-warning'
  return 'fas fa-check-circle text-success'
})

const validationStatusText = computed(() => {
  if (!props.validation) return t('prescription.card.notValidated', 'Not validated')
  if (props.validation.errors?.length) return t('prescription.card.hasErrors', 'Has validation errors')
  if (props.validation.warnings?.length) return t('prescription.card.hasWarnings', 'Has validation warnings')
  return t('prescription.card.validated', 'Validated successfully')
})

const approvalIconClass = computed(() => {
  // This would be based on actual approval status
  return 'text-base-content/40'
})

// Helper functions
const getSeverityColor = (severity: string): string => {
  switch (severity) {
    case 'critical': return 'error'
    case 'high': return 'warning'
    case 'moderate': return 'info'
    case 'low': return 'success'
    default: return 'neutral'
  }
}

const formatDate = (dateString?: string): string => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

const formatFieldName = (fieldName: string): string => {
  return fieldName
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .replace('Is', '')
    .replace('Has', '')
}

// Event handlers
const startEditing = () => {
  editingMedication.value = { ...props.medication }
  isEditing.value = true
}

const saveChanges = () => {
  emit('update', editingMedication.value)
  isEditing.value = false
}

const cancelEditing = () => {
  editingMedication.value = { ...props.medication }
  isEditing.value = false
}

const approveMedication = () => {
  emit('approve', props.medication.id, true)
}

const rejectMedication = () => {
  emit('approve', props.medication.id, false)
}
</script>

<style scoped>
.prescription-medication-card {
  @apply transition-all duration-300;
}

.prescription-medication-card:hover {
  @apply transform scale-[1.02];
}

.collapse-content {
  @apply pt-2;
}

.alert {
  @apply text-sm;
}

.badge {
  @apply transition-all duration-200;
}

.tooltip {
  @apply cursor-help;
}
</style> 