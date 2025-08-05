<template>
  <div class="step6-stock-management">
    <h3 class="text-xl font-semibold mb-4">
      <i class="fas fa-boxes text-primary mr-2"></i>
      {{ $t('workflow.step6.title', 'Stock Management') }}
    </h3>

    <div class="space-y-6">
      <!-- Stock Summary -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step6.summary', 'Stock Summary') }}</h4>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step6.totalMedications', 'Total Medications') }}</div>
              <div class="font-medium text-lg">{{ medications.length }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step6.lowStock', 'Low Stock') }}</div>
              <div class="font-medium text-lg text-warning">{{ lowStockCount }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step6.outOfStock', 'Out of Stock') }}</div>
              <div class="font-medium text-lg text-error">{{ outOfStockCount }}</div>
            </div>
            <div>
              <div class="text-base-content/70">{{ $t('workflow.step6.wellStocked', 'Well Stocked') }}</div>
              <div class="font-medium text-lg text-success">{{ wellStockedCount }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stock Configuration -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step6.configuration', 'Stock Configuration') }}</h4>
          
          <div class="space-y-4">
            <div
              v-for="(medication, index) in medications"
              :key="index"
              class="card bg-base-100"
            >
              <div class="card-body p-4">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-3">
                      <h5 class="font-medium">{{ medication.name }}</h5>
                      <div class="badge badge-sm" :class="getStockBadgeClass(index)">
                        {{ getStockStatus(index) }}
                      </div>
                    </div>
                    
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div class="form-control">
                        <label class="label">
                          <span class="label-text text-sm">{{ $t('workflow.step6.currentStock', 'Current Stock') }}</span>
                        </label>
                        <input
                          v-model.number="stockLevels[index]"
                          type="number"
                          class="input input-bordered input-sm"
                          :class="getStockInputClass(index)"
                        />
                      </div>
                      
                      <div class="form-control">
                        <label class="label">
                          <span class="label-text text-sm">{{ $t('workflow.step6.minStock', 'Min Stock') }}</span>
                        </label>
                        <input
                          v-model.number="minStockLevels[index]"
                          type="number"
                          class="input input-bordered input-sm"
                        />
                      </div>
                      
                      <div class="form-control">
                        <label class="label">
                          <span class="label-text text-sm">{{ $t('workflow.step6.reorderPoint', 'Reorder Point') }}</span>
                        </label>
                        <input
                          v-model.number="reorderPoints[index]"
                          type="number"
                          class="input input-bordered input-sm"
                        />
                      </div>
                    </div>
                    
                    <!-- Stock progress bar -->
                    <div class="mt-3">
                      <div class="flex justify-between text-xs text-base-content/70 mb-1">
                        <span>{{ $t('workflow.step6.stockLevel', 'Stock Level') }}</span>
                        <span>{{ stockLevels[index] || 0 }} / {{ maxStockLevels[index] || 100 }}</span>
                      </div>
                      <div class="w-full bg-base-300 rounded-full h-2">
                        <div
                          class="h-2 rounded-full transition-all duration-300"
                          :class="getStockProgressClass(index)"
                          :style="{ width: `${getStockPercentage(index)}%` }"
                        ></div>
                      </div>
                    </div>
                    
                    <!-- Stock analytics -->
                    <div class="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                      <div>
                        <div class="text-base-content/70">{{ $t('workflow.step6.daysRemaining', 'Days Left') }}</div>
                        <div class="font-medium">{{ getDaysRemaining(index) }}</div>
                      </div>
                      <div>
                        <div class="text-base-content/70">{{ $t('workflow.step6.usageRate', 'Usage Rate') }}</div>
                        <div class="font-medium">{{ getUsageRate(index) }}/day</div>
                      </div>
                      <div>
                        <div class="text-base-content/70">{{ $t('workflow.step6.reorderQuantity', 'Reorder Qty') }}</div>
                        <div class="font-medium">{{ getReorderQuantity(index) }}</div>
                      </div>
                      <div>
                        <div class="text-base-content/70">{{ $t('workflow.step6.nextReorder', 'Next Reorder') }}</div>
                        <div class="font-medium">{{ getNextReorderDate(index) }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <div class="flex flex-col gap-2 ml-4">
                    <button
                      @click="autoCalculateStock(index)"
                      class="btn btn-circle btn-sm btn-primary"
                      :title="$t('workflow.step6.autoCalculate', 'Auto Calculate')"
                    >
                      <i class="fas fa-calculator"></i>
                    </button>
                    <button
                      @click="setDefaultStock(index)"
                      class="btn btn-circle btn-sm btn-ghost"
                      :title="$t('workflow.step6.setDefault', 'Set Default')"
                    >
                      <i class="fas fa-undo"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bulk Actions -->
      <div class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step6.bulkActions', 'Bulk Actions') }}</h4>
          
          <div class="flex gap-2 flex-wrap">
            <button
              @click="autoCalculateAll"
              class="btn btn-sm btn-primary"
            >
              <i class="fas fa-calculator mr-2"></i>
              {{ $t('workflow.step6.autoCalculateAll', 'Auto Calculate All') }}
            </button>
            <button
              @click="setDefaultAll"
              class="btn btn-sm btn-outline"
            >
              <i class="fas fa-undo mr-2"></i>
              {{ $t('workflow.step6.setDefaultAll', 'Set Default All') }}
            </button>
            <button
              @click="generateOrderList"
              class="btn btn-sm btn-outline"
            >
              <i class="fas fa-shopping-cart mr-2"></i>
              {{ $t('workflow.step6.generateOrder', 'Generate Order List') }}
            </button>
            <button
              @click="exportStockReport"
              class="btn btn-sm btn-outline"
            >
              <i class="fas fa-download mr-2"></i>
              {{ $t('workflow.step6.exportReport', 'Export Report') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Order List Preview -->
      <div v-if="orderList.length > 0" class="card bg-base-200">
        <div class="card-body">
          <h4 class="font-semibold mb-3">{{ $t('workflow.step6.orderList', 'Order List') }}</h4>
          
          <div class="overflow-x-auto">
            <table class="table table-zebra w-full">
              <thead>
                <tr>
                  <th>{{ $t('workflow.step6.medication', 'Medication') }}</th>
                  <th>{{ $t('workflow.step6.currentStock', 'Current') }}</th>
                  <th>{{ $t('workflow.step6.reorderQuantity', 'Order Qty') }}</th>
                  <th>{{ $t('workflow.step6.priority', 'Priority') }}</th>
                  <th>{{ $t('workflow.step6.estimatedCost', 'Est. Cost') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(item, index) in orderList"
                  :key="index"
                >
                  <td>{{ item.medication }}</td>
                  <td>{{ item.currentStock }}</td>
                  <td>{{ item.reorderQuantity }}</td>
                  <td>
                    <div class="badge badge-sm" :class="getPriorityBadgeClass(item.priority)">
                      {{ item.priority }}
                    </div>
                  </td>
                  <td>${{ item.estimatedCost.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { PrescriptionMedication } from '@/types/medication'

const { t } = useI18n()

// Props
interface Props {
  medications: PrescriptionMedication[]
  stockLevels: Record<string, number>
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'stock-configured': [levels: Record<string, number>]
}>()

// Reactive state
const minStockLevels = reactive<Record<number, number>>({})
const reorderPoints = reactive<Record<number, number>>({})
const maxStockLevels = reactive<Record<number, number>>({})
const orderList = ref<any[]>([])

// Computed properties
const lowStockCount = computed(() => {
  return Object.keys(stockLevels).filter(key => {
    const index = parseInt(key)
    const current = stockLevels[index] || 0
    const min = minStockLevels[index] || 10
    return current <= min && current > 0
  }).length
})

const outOfStockCount = computed(() => {
  return Object.keys(stockLevels).filter(key => {
    const index = parseInt(key)
    return (stockLevels[index] || 0) === 0
  }).length
})

const wellStockedCount = computed(() => {
  return props.medications.length - lowStockCount.value - outOfStockCount.value
})

// Methods
const getStockBadgeClass = (index: number) => {
  const current = stockLevels[index] || 0
  const min = minStockLevels[index] || 10
  
  if (current === 0) return 'badge-error'
  if (current <= min) return 'badge-warning'
  return 'badge-success'
}

const getStockStatus = (index: number) => {
  const current = stockLevels[index] || 0
  const min = minStockLevels[index] || 10
  
  if (current === 0) return t('workflow.step6.status.outOfStock', 'Out of Stock')
  if (current <= min) return t('workflow.step6.status.lowStock', 'Low Stock')
  return t('workflow.step6.status.wellStocked', 'Well Stocked')
}

const getStockInputClass = (index: number) => {
  const current = stockLevels[index] || 0
  const min = minStockLevels[index] || 10
  
  if (current === 0) return 'input-error'
  if (current <= min) return 'input-warning'
  return ''
}

const getStockProgressClass = (index: number) => {
  const current = stockLevels[index] || 0
  const min = minStockLevels[index] || 10
  const max = maxStockLevels[index] || 100
  
  const percentage = (current / max) * 100
  
  if (current === 0) return 'bg-error'
  if (percentage <= (min / max) * 100) return 'bg-warning'
  return 'bg-success'
}

const getStockPercentage = (index: number) => {
  const current = stockLevels[index] || 0
  const max = maxStockLevels[index] || 100
  return Math.min((current / max) * 100, 100)
}

const getDaysRemaining = (index: number) => {
  const current = stockLevels[index] || 0
  const usageRate = getUsageRate(index)
  return usageRate > 0 ? Math.floor(current / usageRate) : 0
}

const getUsageRate = (index: number) => {
  const medication = props.medications[index]
  if (!medication) return 0
  
  const frequency = medication.frequency.toLowerCase()
  if (frequency.includes('once daily')) return 1
  if (frequency.includes('twice daily')) return 2
  if (frequency.includes('three times daily')) return 3
  if (frequency.includes('every 6 hours')) return 4
  if (frequency.includes('every 8 hours')) return 3
  if (frequency.includes('every 12 hours')) return 2
  return 1
}

const getReorderQuantity = (index: number) => {
  const max = maxStockLevels[index] || 100
  const current = stockLevels[index] || 0
  return Math.max(max - current, 0)
}

const getNextReorderDate = (index: number) => {
  const daysRemaining = getDaysRemaining(index)
  if (daysRemaining === 0) return t('workflow.step6.now', 'Now')
  
  const date = new Date()
  date.setDate(date.getDate() + daysRemaining)
  return date.toLocaleDateString()
}

const autoCalculateStock = (index: number) => {
  const medication = props.medications[index]
  if (!medication) return
  
  const usageRate = getUsageRate(index)
  const daysOfSupply = 30 // 30 days of supply
  
  // Calculate recommended stock levels
  const recommendedMax = usageRate * daysOfSupply
  const recommendedMin = Math.ceil(recommendedMax * 0.2) // 20% of max
  const recommendedReorder = Math.ceil(recommendedMax * 0.3) // 30% of max
  
  maxStockLevels[index] = recommendedMax
  minStockLevels[index] = recommendedMin
  reorderPoints[index] = recommendedReorder
  
  // Set current stock if not set
  if (!stockLevels[index]) {
    stockLevels[index] = recommendedMax
  }
  
  emit('stock-configured', { ...stockLevels })
}

const setDefaultStock = (index: number) => {
  const medication = props.medications[index]
  if (!medication) return
  
  stockLevels[index] = medication.quantity || 30
  minStockLevels[index] = Math.ceil((medication.quantity || 30) * 0.2)
  reorderPoints[index] = Math.ceil((medication.quantity || 30) * 0.3)
  maxStockLevels[index] = medication.quantity || 30
  
  emit('stock-configured', { ...stockLevels })
}

const autoCalculateAll = () => {
  props.medications.forEach((_, index) => {
    autoCalculateStock(index)
  })
}

const setDefaultAll = () => {
  props.medications.forEach((_, index) => {
    setDefaultStock(index)
  })
}

const generateOrderList = () => {
  const orders: any[] = []
  
  Object.keys(stockLevels).forEach(key => {
    const index = parseInt(key)
    const current = stockLevels[index] || 0
    const min = minStockLevels[index] || 10
    const medication = props.medications[index]
    
    if (current <= min && medication) {
      const reorderQty = getReorderQuantity(index)
      const priority = current === 0 ? 'High' : 'Medium'
      const estimatedCost = reorderQty * 5 // Mock cost calculation
      
      orders.push({
        medication: medication.name,
        currentStock: current,
        reorderQuantity: reorderQty,
        priority,
        estimatedCost
      })
    }
  })
  
  // Sort by priority
  orderList.value = orders.sort((a, b) => {
    const priorityOrder = { 'High': 3, 'Medium': 2, 'Low': 1 }
    return priorityOrder[b.priority as keyof typeof priorityOrder] - priorityOrder[a.priority as keyof typeof priorityOrder]
  })
}

const getPriorityBadgeClass = (priority: string) => {
  switch (priority) {
    case 'High': return 'badge-error'
    case 'Medium': return 'badge-warning'
    case 'Low': return 'badge-info'
    default: return 'badge-neutral'
  }
}

const exportStockReport = () => {
  const report = {
    medications: props.medications,
    stockLevels,
    minStockLevels,
    reorderPoints,
    maxStockLevels,
    summary: {
      totalMedications: props.medications.length,
      lowStock: lowStockCount.value,
      outOfStock: outOfStockCount.value,
      wellStocked: wellStockedCount.value
    },
    orderList: orderList.value,
    generatedAt: new Date().toISOString()
  }
  
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'stock-management-report.json'
  a.click()
  URL.revokeObjectURL(url)
}

// Watch for changes
watch(() => stockLevels, (levels) => {
  emit('stock-configured', levels)
}, { deep: true })

// Initialize
props.medications.forEach((_, index) => {
  setDefaultStock(index)
})
</script>

<style scoped>
.table {
  @apply text-sm;
}

.table th {
  @apply font-medium;
}
</style> 