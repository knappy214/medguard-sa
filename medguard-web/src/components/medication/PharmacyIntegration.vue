<template>
  <div class="pharmacy-integration">
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-primary">
          <i class="fas fa-hospital mr-2"></i>
          {{ t('medication.pharmacyIntegration.title') }}
        </h2>
        
        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-8">
          <span class="loading loading-spinner loading-lg text-primary"></span>
          <span class="ml-3">{{ t('common.loading') }}</span>
        </div>
        
        <!-- Integration Content -->
        <div v-else class="space-y-6">
          <!-- Active Integrations -->
          <div v-if="integrations.length > 0">
            <h3 class="text-lg font-semibold mb-4">{{ t('medication.pharmacyIntegration.activeIntegrations') }}</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div 
                v-for="integration in integrations" 
                :key="integration.id"
                class="bg-base-200 rounded-lg p-4 border-l-4"
                :class="getStatusBorderClass(integration.status)"
              >
                <div class="flex justify-between items-start mb-3">
                  <div>
                    <h4 class="font-semibold">{{ integration.name }}</h4>
                    <p class="text-sm opacity-70">{{ integration.pharmacy_name }}</p>
                  </div>
                  <div class="flex items-center gap-2">
                    <span 
                      class="badge badge-sm"
                      :class="getStatusBadgeClass(integration.status)"
                    >
                      {{ getStatusText(integration.status) }}
                    </span>
                    <button 
                      @click="toggleIntegration(integration)"
                      class="btn btn-xs"
                      :class="integration.status === 'active' ? 'btn-error' : 'btn-success'"
                    >
                      {{ integration.status === 'active' ? t('common.disable') : t('common.enable') }}
                    </button>
                  </div>
                </div>
                
                <div class="space-y-2 text-sm">
                  <div class="flex justify-between">
                    <span>{{ t('medication.pharmacyIntegration.type') }}</span>
                    <span class="font-semibold">{{ getIntegrationTypeText(integration.integration_type) }}</span>
                  </div>
                  <div class="flex justify-between">
                    <span>{{ t('medication.pharmacyIntegration.autoOrder') }}</span>
                    <span class="font-semibold">
                      <i 
                        class="fas"
                        :class="integration.auto_order_enabled ? 'fa-check text-success' : 'fa-times text-error'"
                      ></i>
                    </span>
                  </div>
                  <div class="flex justify-between">
                    <span>{{ t('medication.pharmacyIntegration.lastSync') }}</span>
                    <span class="font-semibold">{{ formatDate(integration.last_sync) }}</span>
                  </div>
                </div>
                
                <div class="mt-3 flex gap-2">
                  <button 
                    @click="testConnection(integration)"
                    class="btn btn-xs btn-outline"
                    :disabled="testing"
                  >
                    <i class="fas fa-plug mr-1"></i>
                    {{ t('medication.pharmacyIntegration.testConnection') }}
                  </button>
                  <button 
                    @click="editIntegration(integration)"
                    class="btn btn-xs btn-outline"
                  >
                    <i class="fas fa-edit mr-1"></i>
                    {{ t('common.edit') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- No Integrations -->
          <div v-else class="text-center py-8">
            <i class="fas fa-hospital text-4xl text-gray-400 mb-4"></i>
            <h3 class="text-lg font-semibold mb-2">{{ t('medication.pharmacyIntegration.noIntegrations') }}</h3>
            <p class="text-gray-600 mb-4">{{ t('medication.pharmacyIntegration.noIntegrationsDesc') }}</p>
            <button 
              @click="showAddModal = true"
              class="btn btn-primary"
            >
              <i class="fas fa-plus mr-2"></i>
              {{ t('medication.pharmacyIntegration.addIntegration') }}
            </button>
          </div>
          
          <!-- Add Integration Button -->
          <div v-if="integrations.length > 0" class="flex justify-center">
            <button 
              @click="showAddModal = true"
              class="btn btn-primary"
            >
              <i class="fas fa-plus mr-2"></i>
              {{ t('medication.pharmacyIntegration.addIntegration') }}
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add/Edit Integration Modal -->
    <div v-if="showAddModal" class="modal modal-open">
      <div class="modal-box">
        <h3 class="font-bold text-lg mb-4">
          {{ editingIntegration ? t('medication.pharmacyIntegration.editIntegration') : t('medication.pharmacyIntegration.addIntegration') }}
        </h3>
        
        <form @submit.prevent="saveIntegration" class="space-y-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('medication.pharmacyIntegration.name') }}</span>
            </label>
            <input 
              v-model="form.name"
              type="text"
              class="input input-bordered"
              :placeholder="t('medication.pharmacyIntegration.namePlaceholder')"
              required
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('medication.pharmacyIntegration.pharmacyName') }}</span>
            </label>
            <input 
              v-model="form.pharmacy_name"
              type="text"
              class="input input-bordered"
              :placeholder="t('medication.pharmacyIntegration.pharmacyNamePlaceholder')"
              required
            />
          </div>
          
          <div class="form-control">
            <label class="label">
              <span class="label-text">{{ t('medication.pharmacyIntegration.type') }}</span>
            </label>
            <select v-model="form.integration_type" class="select select-bordered" required>
              <option value="api">{{ t('medication.pharmacyIntegration.typeApi') }}</option>
              <option value="edi">{{ t('medication.pharmacyIntegration.typeEdi') }}</option>
              <option value="manual">{{ t('medication.pharmacyIntegration.typeManual') }}</option>
              <option value="webhook">{{ t('medication.pharmacyIntegration.typeWebhook') }}</option>
            </select>
          </div>
          
          <div v-if="form.integration_type === 'api'" class="space-y-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ t('medication.pharmacyIntegration.apiEndpoint') }}</span>
              </label>
              <input 
                v-model="form.api_endpoint"
                type="url"
                class="input input-bordered"
                :placeholder="t('medication.pharmacyIntegration.apiEndpointPlaceholder')"
              />
            </div>
            
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ t('medication.pharmacyIntegration.apiKey') }}</span>
              </label>
              <input 
                v-model="form.api_key"
                type="password"
                class="input input-bordered"
                :placeholder="t('medication.pharmacyIntegration.apiKeyPlaceholder')"
              />
            </div>
          </div>
          
          <div v-if="form.integration_type === 'webhook'" class="form-control">
            <label class="label">
              <span class="label-text">{{ t('medication.pharmacyIntegration.webhookUrl') }}</span>
            </label>
            <input 
              v-model="form.webhook_url"
              type="url"
              class="input input-bordered"
              :placeholder="t('medication.pharmacyIntegration.webhookUrlPlaceholder')"
            />
          </div>
          
          <div class="form-control">
            <label class="label cursor-pointer">
              <span class="label-text">{{ t('medication.pharmacyIntegration.autoOrder') }}</span>
              <input 
                v-model="form.auto_order_enabled"
                type="checkbox"
                class="checkbox checkbox-primary"
              />
            </label>
          </div>
          
          <div v-if="form.auto_order_enabled" class="grid grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ t('medication.pharmacyIntegration.orderThreshold') }}</span>
              </label>
              <input 
                v-model.number="form.order_threshold"
                type="number"
                class="input input-bordered"
                min="1"
              />
            </div>
            
            <div class="form-control">
              <label class="label">
                <span class="label-text">{{ t('medication.pharmacyIntegration.leadTime') }}</span>
              </label>
              <input 
                v-model.number="form.order_lead_time_days"
                type="number"
                class="input input-bordered"
                min="1"
              />
            </div>
          </div>
          
          <div class="modal-action">
            <button 
              type="button"
              @click="closeModal"
              class="btn"
            >
              {{ t('common.cancel') }}
            </button>
            <button 
              type="submit"
              class="btn btn-primary"
              :disabled="saving"
            >
              <i class="fas fa-save mr-2" :class="{ 'fa-spin': saving }"></i>
              {{ t('common.save') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

interface PharmacyIntegration {
  id: string
  name: string
  pharmacy_name: string
  integration_type: 'api' | 'edi' | 'manual' | 'webhook'
  status: 'active' | 'inactive' | 'testing' | 'error'
  api_endpoint?: string
  api_key?: string
  webhook_url?: string
  auto_order_enabled: boolean
  order_threshold: number
  order_lead_time_days: number
  last_sync?: string
}

const { t } = useI18n()

// Reactive state
const integrations = ref<PharmacyIntegration[]>([])
const loading = ref(true)
const testing = ref(false)
const saving = ref(false)
const showAddModal = ref(false)
const editingIntegration = ref<PharmacyIntegration | null>(null)

const form = ref({
  name: '',
  pharmacy_name: '',
  integration_type: 'api' as 'api' | 'edi' | 'manual' | 'webhook',
  api_endpoint: '',
  api_key: '',
  webhook_url: '',
  auto_order_enabled: false,
  order_threshold: 10,
  order_lead_time_days: 3
})

// Methods
const loadIntegrations = async () => {
  loading.value = true
  try {
    // Mock data for development
    if (import.meta.env.DEV) {
      integrations.value = [
        {
          id: '1',
          name: 'Clicks Pharmacy API',
          pharmacy_name: 'Clicks Pharmacy',
          integration_type: 'api',
          status: 'active',
          api_endpoint: 'https://api.clicks.co.za/v1',
          auto_order_enabled: true,
          order_threshold: 15,
          order_lead_time_days: 2,
          last_sync: new Date().toISOString()
        },
        {
          id: '2',
          name: 'Dis-Chem EDI',
          pharmacy_name: 'Dis-Chem Pharmacy',
          integration_type: 'edi',
          status: 'inactive',
          auto_order_enabled: false,
          order_threshold: 20,
          order_lead_time_days: 5
        }
      ]
    } else {
      // Real API call would go here
      console.log('Loading pharmacy integrations...')
    }
  } catch (error) {
    console.error('Failed to load pharmacy integrations:', error)
  } finally {
    loading.value = false
  }
}

const getStatusBorderClass = (status: string) => {
  switch (status) {
    case 'active': return 'border-success'
    case 'inactive': return 'border-gray-400'
    case 'testing': return 'border-warning'
    case 'error': return 'border-error'
    default: return 'border-gray-400'
  }
}

const getStatusBadgeClass = (status: string) => {
  switch (status) {
    case 'active': return 'badge-success'
    case 'inactive': return 'badge-ghost'
    case 'testing': return 'badge-warning'
    case 'error': return 'badge-error'
    default: return 'badge-ghost'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return t('medication.pharmacyIntegration.statusActive')
    case 'inactive': return t('medication.pharmacyIntegration.statusInactive')
    case 'testing': return t('medication.pharmacyIntegration.statusTesting')
    case 'error': return t('medication.pharmacyIntegration.statusError')
    default: return status
  }
}

const getIntegrationTypeText = (type: string) => {
  switch (type) {
    case 'api': return t('medication.pharmacyIntegration.typeApi')
    case 'edi': return t('medication.pharmacyIntegration.typeEdi')
    case 'manual': return t('medication.pharmacyIntegration.typeManual')
    case 'webhook': return t('medication.pharmacyIntegration.typeWebhook')
    default: return type
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return t('common.never')
  return new Date(dateString).toLocaleDateString()
}

const toggleIntegration = async (integration: PharmacyIntegration) => {
  try {
    const newStatus = integration.status === 'active' ? 'inactive' : 'active'
    // API call would go here
    integration.status = newStatus
  } catch (error) {
    console.error('Failed to toggle integration:', error)
  }
}

const testConnection = async (integration: PharmacyIntegration) => {
  testing.value = true
  try {
    // API call would go here
    await new Promise(resolve => setTimeout(resolve, 2000)) // Simulate API call
    console.log('Testing connection for:', integration.name)
  } catch (error) {
    console.error('Connection test failed:', error)
  } finally {
    testing.value = false
  }
}

const editIntegration = (integration: PharmacyIntegration) => {
  editingIntegration.value = integration
  form.value = {
    name: integration.name,
    pharmacy_name: integration.pharmacy_name,
    integration_type: integration.integration_type,
    api_endpoint: integration.api_endpoint || '',
    api_key: integration.api_key || '',
    webhook_url: integration.webhook_url || '',
    auto_order_enabled: integration.auto_order_enabled,
    order_threshold: integration.order_threshold,
    order_lead_time_days: integration.order_lead_time_days
  }
  showAddModal.value = true
}

const saveIntegration = async () => {
  saving.value = true
  try {
    if (editingIntegration.value) {
      // Update existing integration
      Object.assign(editingIntegration.value, form.value)
    } else {
      // Create new integration
      const newIntegration: PharmacyIntegration = {
        id: Date.now().toString(),
        ...form.value,
        status: 'inactive'
      }
      integrations.value.push(newIntegration)
    }
    closeModal()
  } catch (error) {
    console.error('Failed to save integration:', error)
  } finally {
    saving.value = false
  }
}

const closeModal = () => {
  showAddModal.value = false
  editingIntegration.value = null
  form.value = {
    name: '',
    pharmacy_name: '',
    integration_type: 'api',
    api_endpoint: '',
    api_key: '',
    webhook_url: '',
    auto_order_enabled: false,
    order_threshold: 10,
    order_lead_time_days: 3
  }
}

// Lifecycle
onMounted(() => {
  loadIntegrations()
})
</script>

<style scoped>
.pharmacy-card {
  width: 100%;
}
</style> 