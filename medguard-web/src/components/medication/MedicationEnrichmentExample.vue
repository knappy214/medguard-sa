<template>
  <div class="medication-enrichment-example">
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-primary">
          <i class="fas fa-pills mr-2"></i>
          Medication Enrichment Example
        </h2>
        
        <!-- Input Form -->
        <div class="form-control w-full mb-6">
          <label class="label">
            <span class="label-text font-semibold">Medication Name</span>
          </label>
          <input
            v-model="medicationName"
            type="text"
            placeholder="e.g., Paracetamol, Aspirin, Insulin"
            class="input input-bordered w-full"
            :disabled="isLoading"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div class="form-control">
            <label class="label">
              <span class="label-text">Generic Name (Optional)</span>
            </label>
            <input
              v-model="genericName"
              type="text"
              placeholder="e.g., Acetaminophen"
              class="input input-bordered"
              :disabled="isLoading"
            />
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text">Strength (Optional)</span>
            </label>
            <input
              v-model="strength"
              type="text"
              placeholder="e.g., 500mg, 100mg"
              class="input input-bordered"
              :disabled="isLoading"
            />
          </div>
        </div>

        <!-- Enrichment Options -->
        <div class="form-control mb-6">
          <label class="label">
            <span class="label-text font-semibold">Enrichment Options</span>
          </label>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <label class="label cursor-pointer">
              <input
                v-model="enrichmentOptions.includeInteractions"
                type="checkbox"
                class="checkbox checkbox-primary"
                :disabled="isLoading"
              />
              <span class="label-text ml-2">Interactions</span>
            </label>
            <label class="label cursor-pointer">
              <input
                v-model="enrichmentOptions.includeSideEffects"
                type="checkbox"
                class="checkbox checkbox-primary"
                :disabled="isLoading"
              />
              <span class="label-text ml-2">Side Effects</span>
            </label>
            <label class="label cursor-pointer">
              <input
                v-model="enrichmentOptions.includeCost"
                type="checkbox"
                class="checkbox checkbox-primary"
                :disabled="isLoading"
              />
              <span class="label-text ml-2">Cost Analysis</span>
            </label>
            <label class="label cursor-pointer">
              <input
                v-model="enrichmentOptions.includeAvailability"
                type="checkbox"
                class="checkbox checkbox-primary"
                :disabled="isLoading"
              />
              <span class="label-text ml-2">Availability</span>
            </label>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-4 mb-6">
          <button
            @click="enrichMedication"
            class="btn btn-primary"
            :disabled="!medicationName || isLoading"
          >
            <span v-if="isLoading" class="loading loading-spinner loading-sm"></span>
            <i v-else class="fas fa-magic mr-2"></i>
            {{ isLoading ? 'Enriching...' : 'Enrich Medication' }}
          </button>

          <button
            @click="clearResults"
            class="btn btn-outline"
            :disabled="!enrichmentResult || isLoading"
          >
            <i class="fas fa-trash mr-2"></i>
            Clear Results
          </button>

          <button
            @click="showCacheStats"
            class="btn btn-ghost"
            :disabled="isLoading"
          >
            <i class="fas fa-chart-bar mr-2"></i>
            Cache Stats
          </button>
        </div>

        <!-- Loading State -->
        <div v-if="isLoading" class="text-center py-8">
          <div class="loading loading-spinner loading-lg text-primary"></div>
          <p class="mt-4 text-gray-600">Enriching medication data...</p>
          <p class="text-sm text-gray-500">This may take a few moments</p>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="alert alert-error mb-6">
          <i class="fas fa-exclamation-triangle"></i>
          <div>
            <h3 class="font-bold">Enrichment Failed</h3>
            <div class="text-sm">{{ error }}</div>
          </div>
        </div>

        <!-- Results -->
        <div v-else-if="enrichmentResult" class="space-y-6">
          <!-- Drug Information -->
          <div v-if="enrichmentResult.drugInfo" class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">
                <i class="fas fa-info-circle text-info mr-2"></i>
                Drug Information
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p><strong>Name:</strong> {{ enrichmentResult.drugInfo.name }}</p>
                  <p><strong>Generic:</strong> {{ enrichmentResult.drugInfo.genericName }}</p>
                  <p><strong>Strength:</strong> {{ enrichmentResult.drugInfo.strength }}</p>
                  <p><strong>Form:</strong> {{ enrichmentResult.drugInfo.dosageForm }}</p>
                  <p><strong>Manufacturer:</strong> {{ enrichmentResult.drugInfo.manufacturer }}</p>
                </div>
                <div>
                  <p><strong>Pregnancy Category:</strong> {{ enrichmentResult.drugInfo.pregnancyCategory }}</p>
                  <p><strong>Breastfeeding:</strong> {{ enrichmentResult.drugInfo.breastfeedingCategory }}</p>
                  <p><strong>Cost:</strong> R{{ enrichmentResult.drugInfo.cost?.toFixed(2) }}</p>
                  <p><strong>Availability:</strong> 
                    <span :class="getAvailabilityClass(enrichmentResult.drugInfo.availability)">
                      {{ enrichmentResult.drugInfo.availability }}
                    </span>
                  </p>
                </div>
              </div>
              <div class="mt-4">
                <p><strong>Description:</strong> {{ enrichmentResult.drugInfo.description }}</p>
              </div>
            </div>
          </div>

          <!-- Side Effects -->
          <div v-if="enrichmentResult.sideEffects?.length" class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">
                <i class="fas fa-exclamation-triangle text-warning mr-2"></i>
                Side Effects
              </h3>
              <ul class="list-disc list-inside space-y-1">
                <li v-for="effect in enrichmentResult.sideEffects" :key="effect" class="text-sm">
                  {{ effect }}
                </li>
              </ul>
            </div>
          </div>

          <!-- Interactions -->
          <div v-if="enrichmentResult.interactions?.length" class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">
                <i class="fas fa-exclamation-circle text-error mr-2"></i>
                Drug Interactions
              </h3>
              <div v-for="interaction in enrichmentResult.interactions" :key="interaction.description" class="mb-4 p-4 bg-base-300 rounded-lg">
                <div class="flex items-center mb-2">
                  <span :class="getSeverityClass(interaction.severity)" class="badge">
                    {{ interaction.severity.toUpperCase() }}
                  </span>
                </div>
                <p class="font-semibold">{{ interaction.description }}</p>
                <p class="text-sm text-gray-600">Medications: {{ interaction.medications.join(', ') }}</p>
                <p class="text-sm mt-2"><strong>Recommendation:</strong> {{ interaction.recommendations }}</p>
              </div>
            </div>
          </div>

          <!-- Cost Analysis -->
          <div v-if="enrichmentResult.costAnalysis" class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">
                <i class="fas fa-money-bill text-success mr-2"></i>
                Cost Analysis (ZAR)
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p><strong>Average Cost:</strong> R{{ enrichmentResult.costAnalysis.averageCost?.toFixed(2) }}</p>
                  <p><strong>Cost Range:</strong> R{{ enrichmentResult.costAnalysis.costRange?.min?.toFixed(2) }} - R{{ enrichmentResult.costAnalysis.costRange?.max?.toFixed(2) }}</p>
                  <p><strong>Cost per Dose:</strong> R{{ enrichmentResult.costAnalysis.costPerDose?.toFixed(2) }}</p>
                  <p><strong>Monthly Cost:</strong> R{{ enrichmentResult.costAnalysis.monthlyCost?.toFixed(2) }}</p>
                </div>
                <div>
                  <p><strong>Generic Available:</strong> 
                    <span :class="enrichmentResult.costAnalysis.genericAvailable ? 'text-success' : 'text-error'">
                      {{ enrichmentResult.costAnalysis.genericAvailable ? 'Yes' : 'No' }}
                    </span>
                  </p>
                  <p v-if="enrichmentResult.costAnalysis.genericCost">
                    <strong>Generic Cost:</strong> R{{ enrichmentResult.costAnalysis.genericCost.toFixed(2) }}
                  </p>
                  <p v-if="enrichmentResult.costAnalysis.insuranceCoverage">
                    <strong>Insurance Coverage:</strong> {{ enrichmentResult.costAnalysis.insuranceCoverage }}%
                  </p>
                  <p v-if="enrichmentResult.costAnalysis.outOfPocketCost">
                    <strong>Out of Pocket:</strong> R{{ enrichmentResult.costAnalysis.outOfPocketCost.toFixed(2) }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Availability -->
          <div v-if="enrichmentResult.availability" class="card bg-base-200">
            <div class="card-body">
              <h3 class="card-title text-lg">
                <i class="fas fa-store text-info mr-2"></i>
                Availability Information
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p><strong>Available:</strong> 
                    <span :class="enrichmentResult.availability.isAvailable ? 'text-success' : 'text-error'">
                      {{ enrichmentResult.availability.isAvailable ? 'Yes' : 'No' }}
                    </span>
                  </p>
                  <p><strong>Stock Status:</strong> 
                    <span :class="getStockStatusClass(enrichmentResult.availability.stockStatus)">
                      {{ enrichmentResult.availability.stockStatus.replace('_', ' ').toUpperCase() }}
                    </span>
                  </p>
                  <p><strong>Online Available:</strong> 
                    <span :class="enrichmentResult.availability.onlineAvailability ? 'text-success' : 'text-error'">
                      {{ enrichmentResult.availability.onlineAvailability ? 'Yes' : 'No' }}
                    </span>
                  </p>
                  <p><strong>Prescription Required:</strong> 
                    <span :class="enrichmentResult.availability.prescriptionRequired ? 'text-warning' : 'text-success'">
                      {{ enrichmentResult.availability.prescriptionRequired ? 'Yes' : 'No' }}
                    </span>
                  </p>
                </div>
                <div v-if="enrichmentResult.availability.pharmacies?.length">
                  <p class="font-semibold mb-2">Available at:</p>
                  <div v-for="pharmacy in enrichmentResult.availability.pharmacies.slice(0, 3)" :key="pharmacy.name" class="text-sm mb-2">
                    <p><strong>{{ pharmacy.name }}</strong></p>
                    <p class="text-gray-600">{{ pharmacy.address }}</p>
                    <p class="text-gray-600">R{{ pharmacy.price?.toFixed(2) }} ({{ pharmacy.stock }} in stock)</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Metadata -->
          <div class="text-sm text-gray-500 text-center">
            <p>Enriched at: {{ formatDate(enrichmentResult.enrichedAt) }}</p>
            <p>Source: {{ enrichmentResult.source }}</p>
          </div>
        </div>

        <!-- Cache Stats Modal -->
        <dialog ref="cacheStatsModal" class="modal">
          <div class="modal-box">
            <h3 class="font-bold text-lg mb-4">Cache Statistics</h3>
            <div class="space-y-4">
              <div class="stats shadow">
                <div class="stat">
                  <div class="stat-title">Cache Size</div>
                  <div class="stat-value text-primary">{{ cacheStats.size }}</div>
                  <div class="stat-desc">of {{ cacheStats.maxSize }} entries</div>
                </div>
                <div class="stat">
                  <div class="stat-title">Rate Limit</div>
                  <div class="stat-value text-secondary">{{ rateLimitStats.currentRequests }}</div>
                  <div class="stat-desc">of {{ rateLimitStats.maxRequests }} requests</div>
                </div>
              </div>
              <div class="text-sm text-gray-600">
                <p><strong>Cache TTL:</strong> 24 hours</p>
                <p><strong>Rate Limit Window:</strong> 1 minute</p>
                <p><strong>Cleanup Interval:</strong> 1 hour</p>
              </div>
            </div>
            <div class="modal-action">
              <button @click="closeCacheStats" class="btn">Close</button>
            </div>
          </div>
        </dialog>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import medicationEnrichmentService from '@/services/medicationEnrichmentService'
import type {
  PerplexityEnrichmentRequest,
  PerplexityEnrichmentResponse,
  MedicationEnrichment
} from '@/types/medication'

// Reactive data
const medicationName = ref('')
const genericName = ref('')
const strength = ref('')
const isLoading = ref(false)
const error = ref('')
const enrichmentResult = ref<MedicationEnrichment | null>(null)
const cacheStatsModal = ref<HTMLDialogElement>()

// Enrichment options
const enrichmentOptions = reactive({
  includeInteractions: true,
  includeSideEffects: true,
  includeCost: true,
  includeAvailability: true
})

// Cache and rate limit stats
const cacheStats = ref({ size: 0, maxSize: 100 })
const rateLimitStats = ref({ currentRequests: 0, maxRequests: 50 })

// Methods
const enrichMedication = async () => {
  if (!medicationName.value) {
    error.value = 'Please enter a medication name'
    return
  }

  isLoading.value = true
  error.value = ''
  enrichmentResult.value = null

  try {
    const request: PerplexityEnrichmentRequest = {
      medicationName: medicationName.value,
      genericName: genericName.value || undefined,
      strength: strength.value || undefined,
      ...enrichmentOptions
    }

    const result: PerplexityEnrichmentResponse = await medicationEnrichmentService.enrichMedication(request)

    if (result.success && result.data) {
      enrichmentResult.value = result.data
    } else {
      error.value = result.error || 'Enrichment failed'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'An unexpected error occurred'
  } finally {
    isLoading.value = false
  }
}

const clearResults = () => {
  enrichmentResult.value = null
  error.value = ''
}

const showCacheStats = () => {
  cacheStats.value = medicationEnrichmentService.getCacheStats()
  rateLimitStats.value = medicationEnrichmentService.getRateLimitStats()
  cacheStatsModal.value?.showModal()
}

const closeCacheStats = () => {
  cacheStatsModal.value?.close()
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('en-ZA', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const getAvailabilityClass = (availability: string) => {
  switch (availability) {
    case 'available':
      return 'text-success'
    case 'discontinued':
      return 'text-error'
    case 'restricted':
      return 'text-warning'
    default:
      return 'text-gray-600'
  }
}

const getSeverityClass = (severity: string) => {
  switch (severity) {
    case 'high':
    case 'contraindicated':
      return 'badge-error'
    case 'moderate':
      return 'badge-warning'
    case 'low':
      return 'badge-info'
    default:
      return 'badge-neutral'
  }
}

const getStockStatusClass = (status: string) => {
  switch (status) {
    case 'in_stock':
      return 'text-success'
    case 'low_stock':
      return 'text-warning'
    case 'out_of_stock':
      return 'text-error'
    case 'discontinued':
      return 'text-gray-600'
    default:
      return 'text-gray-600'
  }
}
</script>

<style scoped>
.medication-enrichment-example {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
}

.card {
  border-radius: 0.75rem;
}

.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style> 