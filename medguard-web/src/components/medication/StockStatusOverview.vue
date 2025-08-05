<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Medication } from '@/types/medication'

const { t } = useI18n()

interface Props {
  medications: Medication[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
  close: []
}>()

const filterStatus = ref<'all' | 'in_stock' | 'low_stock' | 'out_of_stock'>('all')
const sortBy = ref<'name' | 'stock' | 'status'>('status')

const getStockStatus = (medication: Medication) => {
  if (medication.stock === 0) return 'out_of_stock'
  if (medication.stock <= medication.minStock) return 'low_stock'
  return 'in_stock'
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'in_stock': return 'text-success'
    case 'low_stock': return 'text-warning'
    case 'out_of_stock': return 'text-error'
    default: return 'text-neutral'
  }
}

const getStatusBgColor = (status: string) => {
  switch (status) {
    case 'in_stock': return 'bg-success/10'
    case 'low_stock': return 'bg-warning/10'
    case 'out_of_stock': return 'bg-error/10'
    default: return 'bg-neutral/10'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'in_stock': return 'M5 13l4 4L19 7'
    case 'low_stock': return 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    case 'out_of_stock': return 'M6 18L18 6M6 6l12 12'
    default: return 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
  }
}

const filteredAndSortedMedications = computed(() => {
  let filtered = props.medications
  
  if (filterStatus.value !== 'all') {
    filtered = filtered.filter(med => getStockStatus(med) === filterStatus.value)
  }
  
  return filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'stock':
        return a.stock - b.stock
      case 'status':
        const statusA = getStockStatus(a)
        const statusB = getStockStatus(b)
        const statusOrder = { 'out_of_stock': 0, 'low_stock': 1, 'in_stock': 2 }
        return statusOrder[statusA as keyof typeof statusOrder] - statusOrder[statusB as keyof typeof statusOrder]
      default:
        return 0
    }
  })
})

const stockStats = computed(() => {
  const stats = {
    in_stock: 0,
    low_stock: 0,
    out_of_stock: 0,
    total: props.medications.length
  }
  
  props.medications.forEach(med => {
    const status = getStockStatus(med)
    stats[status as keyof typeof stats]++
  })
  
  return stats
})

const getDaysUntilStockout = (medication: Medication) => {
  // Simple calculation - in real app, this would use usage analytics
  const dailyUsage = 1 // Assume 1 pill per day
  return Math.floor(medication.stock / dailyUsage)
}
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-6xl">
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-high-contrast">
          <svg class="w-6 h-6 mr-2 inline text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
          {{ t('dashboard.stockStatusOverview') }}
        </h3>
        <button @click="emit('close')" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Stock Statistics -->
      <div class="stats shadow w-full mb-6">
        <div class="stat">
          <div class="stat-figure text-success">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.inStock') }}</div>
          <div class="stat-value text-success">{{ stockStats.in_stock }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.medications') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-warning">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.lowStock') }}</div>
          <div class="stat-value text-warning">{{ stockStats.low_stock }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.medications') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.outOfStock') }}</div>
          <div class="stat-value text-error">{{ stockStats.out_of_stock }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.medications') }}</div>
        </div>

        <div class="stat">
          <div class="stat-figure text-info">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div class="stat-title text-high-contrast">{{ t('dashboard.total') }}</div>
          <div class="stat-value text-info">{{ stockStats.total }}</div>
          <div class="stat-desc text-secondary-high-contrast">{{ t('dashboard.medications') }}</div>
        </div>
      </div>

      <!-- Filter and Sort Controls -->
      <div class="flex flex-wrap gap-4 mb-6">
        <div class="form-control">
          <label class="label">
            <span class="label-text text-high-contrast">{{ t('dashboard.filterByStatus') }}</span>
          </label>
          <select v-model="filterStatus" class="select select-bordered select-sm">
            <option value="all">{{ t('dashboard.allStatuses') }}</option>
            <option value="in_stock">{{ t('dashboard.inStock') }}</option>
            <option value="low_stock">{{ t('dashboard.lowStock') }}</option>
            <option value="out_of_stock">{{ t('dashboard.outOfStock') }}</option>
          </select>
        </div>

        <div class="form-control">
          <label class="label">
            <span class="label-text text-high-contrast">{{ t('dashboard.sortBy') }}</span>
          </label>
          <select v-model="sortBy" class="select select-bordered select-sm">
            <option value="status">{{ t('dashboard.status') }}</option>
            <option value="name">{{ t('dashboard.name') }}</option>
            <option value="stock">{{ t('dashboard.stock') }}</option>
          </select>
        </div>
      </div>

      <!-- Stock Status Table -->
      <div class="overflow-x-auto">
        <table class="table table-zebra w-full">
          <thead>
            <tr>
              <th class="text-high-contrast">{{ t('dashboard.medication') }}</th>
              <th class="text-high-contrast">{{ t('dashboard.stock') }}</th>
              <th class="text-high-contrast">{{ t('dashboard.minStock') }}</th>
              <th class="text-high-contrast">{{ t('dashboard.status') }}</th>
              <th class="text-high-contrast">{{ t('dashboard.daysUntilStockout') }}</th>
              <th class="text-high-contrast">{{ t('dashboard.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="medication in filteredAndSortedMedications" :key="medication.id">
              <td>
                <div class="flex items-center space-x-3">
                  <div class="avatar placeholder">
                    <div class="bg-neutral text-neutral-content rounded-full w-8">
                      <span class="text-xs">{{ medication.name.charAt(0) }}</span>
                    </div>
                  </div>
                  <div>
                    <div class="font-bold text-high-contrast">{{ medication.name }}</div>
                    <div class="text-sm opacity-50 text-secondary-high-contrast">{{ medication.dosage }}</div>
                  </div>
                </div>
              </td>
              <td>
                <span class="font-mono text-high-contrast">{{ medication.stock }}</span>
                <span class="text-sm text-secondary-high-contrast ml-1">{{ t('dashboard.pills') }}</span>
              </td>
              <td>
                <span class="font-mono text-secondary-high-contrast">{{ medication.minStock }}</span>
                <span class="text-sm text-secondary-high-contrast ml-1">{{ t('dashboard.pills') }}</span>
              </td>
              <td>
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="getStatusIcon(getStockStatus(medication))" />
                  </svg>
                  <span :class="getStatusColor(getStockStatus(medication))" class="font-medium">
                    {{ t(`dashboard.status.${getStockStatus(medication)}`) }}
                  </span>
                </div>
              </td>
              <td>
                <span v-if="getStockStatus(medication) !== 'out_of_stock'" 
                      class="font-mono"
                      :class="getDaysUntilStockout(medication) <= 7 ? 'text-warning' : 'text-secondary-high-contrast'">
                  {{ getDaysUntilStockout(medication) }}
                </span>
                <span v-else class="text-error font-medium">
                  {{ t('dashboard.outOfStock') }}
                </span>
              </td>
              <td>
                <div class="flex gap-2">
                  <button class="btn btn-xs btn-outline">
                    {{ t('dashboard.order') }}
                  </button>
                  <button class="btn btn-xs btn-outline">
                    {{ t('dashboard.edit') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty State -->
      <div v-if="filteredAndSortedMedications.length === 0" class="text-center py-12">
        <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
        <p class="text-secondary-high-contrast">{{ t('dashboard.noMedicationsMatchFilter') }}</p>
      </div>

      <!-- Critical Alerts Summary -->
      <div v-if="stockStats.low_stock > 0 || stockStats.out_of_stock > 0" class="mt-6">
        <h4 class="font-semibold text-high-contrast mb-4">{{ t('dashboard.criticalAlerts') }}</h4>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div v-if="stockStats.out_of_stock > 0" class="alert alert-error">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <div>
              <h3 class="font-bold">{{ t('dashboard.outOfStockAlert') }}</h3>
              <div class="text-sm">{{ stockStats.out_of_stock }} {{ t('dashboard.medicationsOutOfStock') }}</div>
            </div>
          </div>
          
          <div v-if="stockStats.low_stock > 0" class="alert alert-warning">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h3 class="font-bold">{{ t('dashboard.lowStockAlert') }}</h3>
              <div class="text-sm">{{ stockStats.low_stock }} {{ t('dashboard.medicationsLowStock') }}</div>
            </div>
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

.table th {
  @apply bg-base-200;
}

.table td {
  @apply align-middle;
}
</style> 