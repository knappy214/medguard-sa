<template>
  <div class="prescription-review-interface">
    <!-- Header with Summary -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="flex items-center justify-between mb-4">
          <h2 class="card-title text-2xl font-bold">
            <i class="fas fa-clipboard-check text-primary mr-2"></i>
            {{ $t('prescription.review.title', 'Prescription Review') }}
          </h2>
          <div class="flex items-center gap-2">
            <div class="badge badge-primary">{{ medications.length }}/21</div>
            <div class="badge badge-outline">{{ reviewStatus }}</div>
            <div v-if="validationStats.totalWarnings > 0" class="badge badge-warning">
              {{ validationStats.totalWarnings }} {{ $t('prescription.review.warnings', 'warnings') }}
            </div>
            <div v-if="validationStats.totalErrors > 0" class="badge badge-error">
              {{ validationStats.totalErrors }} {{ $t('prescription.review.errors', 'errors') }}
            </div>
          </div>
        </div>
        
        <!-- Progress and Stats -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div class="stat bg-base-200 rounded-lg p-4">
            <div class="stat-title">{{ $t('prescription.review.confidence', 'Avg Confidence') }}</div>
            <div class="stat-value text-primary">{{ averageConfidence }}%</div>
            <div class="stat-desc">{{ $t('prescription.review.ocrAccuracy', 'OCR Accuracy') }}</div>
          </div>
          <div class="stat bg-base-200 rounded-lg p-4">
            <div class="stat-title">{{ $t('prescription.review.interactions', 'Interactions') }}</div>
            <div class="stat-value text-warning">{{ interactionStats.total }}</div>
            <div class="stat-desc">{{ $t('prescription.review.critical', 'Critical') }}: {{ interactionStats.critical }}</div>
          </div>
          <div class="stat bg-base-200 rounded-lg p-4">
            <div class="stat-title">{{ $t('prescription.review.alternatives', 'Alternatives') }}</div>
            <div class="stat-value text-info">{{ alternativeStats.available }}</div>
            <div class="stat-desc">{{ $t('prescription.review.savings', 'Potential Savings') }}: R{{ alternativeStats.totalSavings }}</div>
          </div>
          <div class="stat bg-base-200 rounded-lg p-4">
            <div class="stat-title">{{ $t('prescription.review.compliance', 'Compliance') }}</div>
            <div class="stat-value text-success">{{ complianceScore }}%</div>
            <div class="stat-desc">{{ $t('prescription.review.saRegulations', 'SA Regulations') }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Filter and Search Controls -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <div class="flex flex-wrap gap-4 items-center">
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('prescription.review.filterBy', 'Filter by') }}</span>
            </label>
            <select v-model="filterBy" class="select select-bordered">
              <option value="all">{{ $t('prescription.review.all', 'All Medications') }}</option>
              <option value="high-confidence">{{ $t('prescription.review.highConfidence', 'High Confidence') }}</option>
              <option value="low-confidence">{{ $t('prescription.review.lowConfidence', 'Low Confidence') }}</option>
              <option value="errors">{{ $t('prescription.review.withErrors', 'With Errors') }}</option>
              <option value="warnings">{{ $t('prescription.review.withWarnings', 'With Warnings') }}</option>
              <option value="interactions">{{ $t('prescription.review.withInteractions', 'With Interactions') }}</option>
              <option value="alternatives">{{ $t('prescription.review.withAlternatives', 'With Alternatives') }}</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('prescription.review.search', 'Search') }}</span>
            </label>
            <input 
              v-model="searchQuery" 
              type="text" 
              :placeholder="$t('prescription.review.searchPlaceholder', 'Search medications...')"
              class="input input-bordered"
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('prescription.review.sortBy', 'Sort by') }}</span>
            </label>
            <select v-model="sortBy" class="select select-bordered">
              <option value="name">{{ $t('prescription.review.name', 'Name') }}</option>
              <option value="confidence">{{ $t('prescription.review.confidence', 'Confidence') }}</option>
              <option value="severity">{{ $t('prescription.review.severity', 'Severity') }}</option>
              <option value="cost">{{ $t('prescription.review.cost', 'Cost') }}</option>
            </select>
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('prescription.review.view', 'View') }}</span>
            </label>
            <select v-model="viewMode" class="select select-bordered">
              <option value="grid">{{ $t('prescription.review.grid', 'Grid') }}</option>
              <option value="list">{{ $t('prescription.review.list', 'List') }}</option>
              <option value="compact">{{ $t('prescription.review.compact', 'Compact') }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Medications Grid/List -->
    <div class="grid gap-6" :class="gridClasses">
      <PrescriptionMedicationCard
        v-for="medication in filteredAndSortedMedications"
        :key="medication.id"
        :medication="medication"
        :validation="medicationValidations[medication.id]"
        :interactions="medicationInteractions[medication.id]"
        :alternatives="medicationAlternatives[medication.id]"
        :stock-info="medicationStockInfo[medication.id]"
        :compliance="medicationCompliance[medication.id]"
        @update="handleMedicationUpdate"
        @validate="handleMedicationValidation"
        @approve="handleMedicationApproval"
      />
    </div>

    <!-- Approval Workflow -->
    <div class="card bg-base-100 shadow-xl mt-6">
      <div class="card-body">
        <h3 class="card-title text-xl mb-4">
          <i class="fas fa-signature text-primary mr-2"></i>
          {{ $t('prescription.review.approval', 'Prescription Approval') }}
        </h3>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <!-- Digital Signature -->
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ $t('prescription.review.digitalSignature', 'Digital Signature') }}</span>
            </label>
            <div class="border-2 border-dashed border-base-300 rounded-lg p-6 text-center">
              <div v-if="!digitalSignature" class="space-y-4">
                <i class="fas fa-signature text-4xl text-base-content/40"></i>
                <p class="text-base-content/60">{{ $t('prescription.review.signatureRequired', 'Digital signature required for approval') }}</p>
                <button @click="showSignatureModal = true" class="btn btn-primary">
                  {{ $t('prescription.review.addSignature', 'Add Signature') }}
                </button>
              </div>
              <div v-else class="space-y-2">
                <i class="fas fa-check-circle text-success text-2xl"></i>
                <p class="font-medium">{{ $t('prescription.review.signedBy', 'Signed by') }}: {{ digitalSignature.signerName }}</p>
                <p class="text-sm text-base-content/60">{{ formatDateTime(digitalSignature.timestamp) }}</p>
                <button @click="showSignatureModal = true" class="btn btn-ghost btn-sm">
                  {{ $t('prescription.review.changeSignature', 'Change') }}
                </button>
              </div>
            </div>
          </div>
          
          <!-- Approval Summary -->
          <div class="space-y-4">
            <h4 class="font-semibold">{{ $t('prescription.review.approvalSummary', 'Approval Summary') }}</h4>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span>{{ $t('prescription.review.totalMedications', 'Total Medications') }}:</span>
                <span class="font-medium">{{ medications.length }}</span>
              </div>
              <div class="flex justify-between">
                <span>{{ $t('prescription.review.validated', 'Validated') }}:</span>
                <span class="font-medium text-success">{{ validationStats.validated }}</span>
              </div>
              <div class="flex justify-between">
                <span>{{ $t('prescription.review.pending', 'Pending') }}:</span>
                <span class="font-medium text-warning">{{ validationStats.pending }}</span>
              </div>
              <div class="flex justify-between">
                <span>{{ $t('prescription.review.rejected', 'Rejected') }}:</span>
                <span class="font-medium text-error">{{ validationStats.rejected }}</span>
              </div>
              <div class="flex justify-between">
                <span>{{ $t('prescription.review.totalCost', 'Total Cost') }}:</span>
                <span class="font-medium">R{{ totalCost.toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="divider"></div>
            
            <div class="space-y-2">
              <button 
                @click="approveAllMedications"
                :disabled="!canApproveAll"
                class="btn btn-success w-full"
              >
                <i class="fas fa-check mr-2"></i>
                {{ $t('prescription.review.approveAll', 'Approve All Medications') }}
              </button>
              <button 
                @click="rejectAllMedications"
                class="btn btn-error w-full"
              >
                <i class="fas fa-times mr-2"></i>
                {{ $t('prescription.review.rejectAll', 'Reject All Medications') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Digital Signature Modal -->
    <DigitalSignatureModal
      v-if="showSignatureModal"
      @close="showSignatureModal = false"
      @sign="handleDigitalSignature"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { 
  PrescriptionMedication, 
  MedicationValidation, 
  MedicationInteraction,
  DrugDatabaseEntry,
  StockAnalytics,
  SouthAfricanPrescriptionValidation
} from '@/types/medication'
import PrescriptionMedicationCard from './PrescriptionMedicationCard.vue'
import DigitalSignatureModal from './DigitalSignatureModal.vue'

interface Props {
  medications: PrescriptionMedication[]
  prescriptionId?: string
}

interface Emits {
  (e: 'approve', medications: PrescriptionMedication[]): void
  (e: 'reject', medications: PrescriptionMedication[]): void
  (e: 'update', medications: PrescriptionMedication[]): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { t } = useI18n()

// Reactive state
const filterBy = ref('all')
const searchQuery = ref('')
const sortBy = ref('name')
const viewMode = ref('grid')
const showSignatureModal = ref(false)
const digitalSignature = ref<{
  signerName: string
  timestamp: string
  signature: string
} | null>(null)

// Validation and enrichment data
const medicationValidations = ref<Record<string, MedicationValidation>>({})
const medicationInteractions = ref<Record<string, MedicationInteraction[]>>({})
const medicationAlternatives = ref<Record<string, DrugDatabaseEntry[]>>({})
const medicationStockInfo = ref<Record<string, StockAnalytics>>({})
const medicationCompliance = ref<Record<string, SouthAfricanPrescriptionValidation>>({})

// Computed properties
const filteredAndSortedMedications = computed(() => {
  let filtered = props.medications

  // Apply search filter
  if (searchQuery.value) {
    filtered = filtered.filter(med => 
      med.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      med.genericName?.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // Apply type filter
  switch (filterBy.value) {
    case 'high-confidence':
      filtered = filtered.filter(med => getConfidenceScore(med) >= 80)
      break
    case 'low-confidence':
      filtered = filtered.filter(med => getConfidenceScore(med) < 80)
      break
    case 'errors':
      filtered = filtered.filter(med => 
        medicationValidations.value[med.id]?.errors?.length > 0
      )
      break
    case 'warnings':
      filtered = filtered.filter(med => 
        medicationValidations.value[med.id]?.warnings?.length > 0
      )
      break
    case 'interactions':
      filtered = filtered.filter(med => 
        medicationInteractions.value[med.id]?.length > 0
      )
      break
    case 'alternatives':
      filtered = filtered.filter(med => 
        medicationAlternatives.value[med.id]?.length > 0
      )
      break
  }

  // Apply sorting
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'confidence':
        return getConfidenceScore(b) - getConfidenceScore(a)
      case 'severity':
        return getSeverityScore(b) - getSeverityScore(a)
      case 'cost':
        return (b.cost || 0) - (a.cost || 0)
      default:
        return a.name.localeCompare(b.name)
    }
  })

  return filtered
})

const gridClasses = computed(() => {
  switch (viewMode.value) {
    case 'grid':
      return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
    case 'list':
      return 'grid-cols-1'
    case 'compact':
      return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4'
    default:
      return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
  }
})

const averageConfidence = computed(() => {
  if (props.medications.length === 0) return 0
  const total = props.medications.reduce((sum, med) => sum + getConfidenceScore(med), 0)
  return Math.round(total / props.medications.length)
})

const validationStats = computed(() => {
  const stats = {
    totalWarnings: 0,
    totalErrors: 0,
    validated: 0,
    pending: 0,
    rejected: 0
  }

  props.medications.forEach(med => {
    const validation = medicationValidations.value[med.id]
    if (validation) {
      stats.totalWarnings += validation.warnings?.length || 0
      stats.totalErrors += validation.errors?.length || 0
      
      if (validation.isValid && !validation.errors?.length) {
        stats.validated++
      } else if (validation.errors?.length) {
        stats.rejected++
      } else {
        stats.pending++
      }
    } else {
      stats.pending++
    }
  })

  return stats
})

const interactionStats = computed(() => {
  const stats = { total: 0, critical: 0, high: 0, moderate: 0, low: 0 }
  
  Object.values(medicationInteractions.value).forEach(interactions => {
    interactions.forEach(interaction => {
      stats.total++
      stats[interaction.severity]++
    })
  })
  
  return stats
})

const alternativeStats = computed(() => {
  const stats = { available: 0, totalSavings: 0 }
  
  Object.values(medicationAlternatives.value).forEach(alternatives => {
    stats.available += alternatives.length
    alternatives.forEach(alt => {
      // Calculate potential savings
      const originalCost = 0 // Get from original medication
      const alternativeCost = alt.cost || 0
      if (alternativeCost < originalCost) {
        stats.totalSavings += originalCost - alternativeCost
      }
    })
  })
  
  return stats
})

const complianceScore = computed(() => {
  if (props.medications.length === 0) return 0
  const total = props.medications.reduce((sum, med) => {
    const compliance = medicationCompliance.value[med.id]
    return sum + (compliance?.isValid ? 100 : 0)
  }, 0)
  return Math.round(total / props.medications.length)
})

const totalCost = computed(() => {
  return props.medications.reduce((sum, med) => sum + (med.cost || 0), 0)
})

const reviewStatus = computed(() => {
  if (validationStats.value.rejected > 0) return 'Needs Review'
  if (validationStats.value.pending > 0) return 'Pending Validation'
  if (validationStats.value.totalWarnings > 0) return 'Warnings Present'
  return 'Ready for Approval'
})

const canApproveAll = computed(() => {
  return validationStats.value.rejected === 0 && 
         validationStats.value.pending === 0 &&
         digitalSignature.value !== null
})

// Helper functions
const getConfidenceScore = (medication: PrescriptionMedication): number => {
  // This would come from OCR confidence data
  return Math.floor(Math.random() * 40) + 60 // Mock data: 60-100%
}

const getSeverityScore = (medication: PrescriptionMedication): number => {
  const validation = medicationValidations.value[medication.id]
  const interactions = medicationInteractions.value[medication.id]
  
  let score = 0
  if (validation?.errors?.length) score += 10
  if (validation?.warnings?.length) score += 5
  if (interactions?.some(i => i.severity === 'critical')) score += 8
  if (interactions?.some(i => i.severity === 'high')) score += 6
  if (interactions?.some(i => i.severity === 'moderate')) score += 4
  
  return score
}

const formatDateTime = (timestamp: string): string => {
  return new Date(timestamp).toLocaleString()
}

// Event handlers
const handleMedicationUpdate = (medication: PrescriptionMedication) => {
  // Update medication in the list
  const index = props.medications.findIndex(m => m.id === medication.id)
  if (index !== -1) {
    props.medications[index] = medication
  }
  emit('update', props.medications)
}

const handleMedicationValidation = async (medicationId: string) => {
  // Mock validation - in real app, this would call API
  medicationValidations.value[medicationId] = {
    isValid: Math.random() > 0.3,
    warnings: Math.random() > 0.7 ? ['Dosage may need adjustment'] : [],
    errors: Math.random() > 0.8 ? ['Invalid drug name'] : [],
    suggestions: ['Consider generic alternative']
  }
}

const handleMedicationApproval = (medicationId: string, approved: boolean) => {
  // Handle individual medication approval
  console.log(`Medication ${medicationId} ${approved ? 'approved' : 'rejected'}`)
}

const handleDigitalSignature = (signature: {
  signerName: string
  timestamp: string
  signature: string
}) => {
  digitalSignature.value = signature
  showSignatureModal.value = false
}

const approveAllMedications = () => {
  if (canApproveAll.value) {
    emit('approve', props.medications)
  }
}

const rejectAllMedications = () => {
  emit('reject', props.medications)
}

// Initialize data on mount
onMounted(async () => {
  // Initialize mock data for all medications
  props.medications.forEach(async (medication) => {
    // Mock validation data
    medicationValidations.value[medication.id] = {
      isValid: Math.random() > 0.3,
      warnings: Math.random() > 0.7 ? ['Dosage may need adjustment'] : [],
      errors: Math.random() > 0.8 ? ['Invalid drug name'] : [],
      suggestions: ['Consider generic alternative']
    }

    // Mock interaction data
    if (Math.random() > 0.6) {
      medicationInteractions.value[medication.id] = [{
        severity: ['low', 'moderate', 'high', 'critical'][Math.floor(Math.random() * 4)] as any,
        description: 'Potential interaction with other medications',
        medications: ['Aspirin', 'Warfarin'],
        recommendations: 'Monitor closely for bleeding',
        evidence: 'Clinical studies show increased bleeding risk',
        source: 'DrugBank Database'
      }]
    }

    // Mock alternatives data
    if (Math.random() > 0.5) {
      medicationAlternatives.value[medication.id] = [{
        id: 'alt-1',
        name: 'Generic Alternative',
        genericName: 'Generic Name',
        brandNames: ['Brand 1', 'Brand 2'],
        activeIngredients: ['Active Ingredient'],
        strength: '500mg',
        dosageForm: 'Tablet',
        manufacturer: 'Generic Pharma',
        description: 'Generic alternative with same efficacy',
        sideEffects: ['Nausea', 'Headache'],
        contraindications: ['Allergy to ingredient'],
        interactions: ['May interact with blood thinners'],
        pregnancyCategory: 'C',
        breastfeedingCategory: 'L2',
        pediatricUse: 'Not recommended under 12',
        geriatricUse: 'Use with caution',
        renalDoseAdjustment: 'Reduce dose in renal impairment',
        hepaticDoseAdjustment: 'No adjustment needed',
        storageInstructions: 'Store at room temperature',
        disposalInstructions: 'Dispose properly',
        cost: Math.floor(Math.random() * 100) + 20,
        availability: 'available'
      }]
    }

    // Mock stock info
    medicationStockInfo.value[medication.id] = {
      daily_usage_rate: Math.random() * 2,
      weekly_usage_rate: Math.random() * 14,
      monthly_usage_rate: Math.random() * 60,
      days_until_stockout: Math.floor(Math.random() * 30) + 1,
      predicted_stockout_date: new Date(Date.now() + Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
      recommended_order_quantity: Math.floor(Math.random() * 100) + 30,
      recommended_order_date: new Date(Date.now() + Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString(),
      seasonal_factor: Math.random() * 0.5 + 0.75,
      usage_volatility: Math.random() * 0.3,
      stockout_confidence: Math.random() * 0.2 + 0.8,
      last_calculated: new Date().toISOString(),
      calculation_window_days: 30
    }

    // Mock compliance data
    medicationCompliance.value[medication.id] = {
      isValid: Math.random() > 0.2,
      errors: Math.random() > 0.8 ? ['Missing doctor signature'] : [],
      warnings: Math.random() > 0.6 ? ['Dosage format non-standard'] : [],
      requiredFields: {
        doctorName: Math.random() > 0.1,
        doctorLicense: Math.random() > 0.1,
        prescriptionDate: Math.random() > 0.1,
        patientName: Math.random() > 0.1,
        medicationDetails: Math.random() > 0.1
      },
      formatCompliance: {
        isStandardFormat: Math.random() > 0.3,
        hasRequiredSections: Math.random() > 0.2,
        hasProperDosage: Math.random() > 0.2,
        hasFrequency: Math.random() > 0.2
      }
    }
  })
})
</script>

<style scoped>
.prescription-review-interface {
  @apply space-y-6;
}

.stat {
  @apply transition-all duration-200 hover:shadow-md;
}

.badge {
  @apply transition-all duration-200;
}
</style> 