<template>
  <div class="stock-analytics">
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-primary">
          <i class="fas fa-chart-line mr-2"></i>
          {{ t('medication.stockAnalytics.title') }}
        </h2>
        
        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-8">
          <span class="loading loading-spinner loading-lg text-primary"></span>
          <span class="ml-3">{{ t('common.loading') }}</span>
        </div>
        
        <!-- Analytics Content -->
        <div v-else class="space-y-6">
          <!-- Stock Overview -->
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ t('medication.stockAnalytics.currentStock') }}</div>
              <div class="stat-value text-primary">{{ medication.pill_count }}</div>
              <div class="stat-desc">{{ t('medication.stockAnalytics.units') }}</div>
            </div>
            
            <div class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ t('medication.stockAnalytics.daysUntilStockout') }}</div>
              <div class="stat-value" :class="stockoutClass">
                {{ analytics.days_until_stockout || 'N/A' }}
              </div>
              <div class="stat-desc">{{ t('medication.stockAnalytics.days') }}</div>
            </div>
            
            <div class="stat bg-base-200 rounded-lg">
              <div class="stat-title">{{ t('medication.stockAnalytics.dailyUsage') }}</div>
              <div class="stat-value text-secondary">{{ analytics.daily_usage_rate?.toFixed(1) || '0.0' }}</div>
              <div class="stat-desc">{{ t('medication.stockAnalytics.unitsPerDay') }}</div>
            </div>
          </div>
          
          <!-- Stock Prediction Chart -->
          <div class="bg-base-200 rounded-lg p-4">
            <h3 class="text-lg font-semibold mb-4">{{ t('medication.stockAnalytics.stockPrediction') }}</h3>
            <div class="h-64 flex items-center justify-center">
              <!-- Chart placeholder - would integrate with Chart.js or similar -->
              <div class="text-center text-gray-500">
                <i class="fas fa-chart-area text-4xl mb-2"></i>
                <p>{{ t('medication.stockAnalytics.chartPlaceholder') }}</p>
              </div>
            </div>
          </div>
          
          <!-- Usage Patterns -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-base-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold mb-3">{{ t('medication.stockAnalytics.usagePatterns') }}</h3>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span>{{ t('medication.stockAnalytics.weeklyUsage') }}</span>
                  <span class="font-semibold">{{ analytics.weekly_usage_rate?.toFixed(1) || '0.0' }}</span>
                </div>
                <div class="flex justify-between">
                  <span>{{ t('medication.stockAnalytics.monthlyUsage') }}</span>
                  <span class="font-semibold">{{ analytics.monthly_usage_rate?.toFixed(1) || '0.0' }}</span>
                </div>
                <div class="flex justify-between">
                  <span>{{ t('medication.stockAnalytics.volatility') }}</span>
                  <span class="font-semibold">{{ analytics.usage_volatility?.toFixed(2) || '0.00' }}</span>
                </div>
              </div>
            </div>
            
            <div class="bg-base-200 rounded-lg p-4">
              <h3 class="text-lg font-semibold mb-3">{{ t('medication.stockAnalytics.recommendations') }}</h3>
              <div class="space-y-2">
                <div class="flex justify-between">
                  <span>{{ t('medication.stockAnalytics.recommendedOrder') }}</span>
                  <span class="font-semibold text-primary">{{ analytics.recommended_order_quantity || 0 }}</span>
                </div>
                <div class="flex justify-between">
                  <span>{{ t('medication.stockAnalytics.orderDate') }}</span>
                  <span class="font-semibold">{{ formatDate(analytics.recommended_order_date) }}</span>
                </div>
                <div class="flex justify-between">
                  <span>{{ t('medication.stockAnalytics.confidence') }}</span>
                  <span class="font-semibold">{{ (analytics.stockout_confidence * 100)?.toFixed(0) || 0 }}%</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Alerts and Warnings -->
          <div v-if="hasWarnings" class="bg-warning/10 border border-warning rounded-lg p-4">
            <h3 class="text-lg font-semibold text-warning mb-3">
              <i class="fas fa-exclamation-triangle mr-2"></i>
              {{ t('medication.stockAnalytics.warnings') }}
            </h3>
            <ul class="space-y-2">
              <li v-if="analytics.days_until_stockout && analytics.days_until_stockout <= 7" class="flex items-center">
                <i class="fas fa-clock text-warning mr-2"></i>
                {{ t('medication.stockAnalytics.stockoutWarning', { days: analytics.days_until_stockout }) }}
              </li>
              <li v-if="analytics.stockout_confidence && analytics.stockout_confidence < 0.7" class="flex items-center">
                <i class="fas fa-chart-line text-warning mr-2"></i>
                {{ t('medication.stockAnalytics.lowConfidenceWarning') }}
              </li>
            </ul>
          </div>
          
          <!-- Actions -->
          <div class="flex flex-wrap gap-2">
            <button 
              @click="refreshAnalytics" 
              class="btn btn-primary btn-sm"
              :disabled="refreshing"
            >
              <i class="fas fa-sync-alt mr-2" :class="{ 'fa-spin': refreshing }"></i>
              {{ t('medication.stockAnalytics.refresh') }}
            </button>
            
            <button 
              @click="generateReport" 
              class="btn btn-secondary btn-sm"
              :disabled="generating"
            >
              <i class="fas fa-file-pdf mr-2" :class="{ 'fa-spin': generating }"></i>
              {{ t('medication.stockAnalytics.generateReport') }}
            </button>
            
            <button 
              v-if="analytics.recommended_order_quantity > 0"
              @click="placeOrder" 
              class="btn btn-accent btn-sm"
            >
              <i class="fas fa-shopping-cart mr-2"></i>
              {{ t('medication.stockAnalytics.placeOrder') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Medication, StockAnalytics } from '@/types/medication'
import { medicationApi } from '@/services/medicationApi'

interface Props {
  medication: Medication
}

const props = defineProps<Props>()

const { t } = useI18n()

// Reactive state
const analytics = ref<StockAnalytics>({
  daily_usage_rate: 0,
  weekly_usage_rate: 0,
  monthly_usage_rate: 0,
  days_until_stockout: null,
  predicted_stockout_date: null,
  recommended_order_quantity: 0,
  recommended_order_date: null,
  seasonal_factor: 1.0,
  usage_volatility: 0,
  stockout_confidence: 0,
  last_calculated: null,
  calculation_window_days: 90
})

const loading = ref(true)
const refreshing = ref(false)
const generating = ref(false)

// Computed properties
const stockoutClass = computed(() => {
  const days = analytics.value.days_until_stockout
  if (!days) return 'text-gray-500'
  if (days <= 7) return 'text-error'
  if (days <= 14) return 'text-warning'
  return 'text-success'
})

const hasWarnings = computed(() => {
  return (
    (analytics.value.days_until_stockout && analytics.value.days_until_stockout <= 7) ||
    (analytics.value.stockout_confidence && analytics.value.stockout_confidence < 0.7)
  )
})

// Methods
const loadAnalytics = async () => {
  loading.value = true
  try {
    if (import.meta.env.DEV) {
      // Mock analytics data
      analytics.value = {
        daily_usage_rate: 2.5,
        weekly_usage_rate: 17.5,
        monthly_usage_rate: 75.0,
        days_until_stockout: 12,
        predicted_stockout_date: new Date(Date.now() + 12 * 24 * 60 * 60 * 1000).toISOString(),
        recommended_order_quantity: 50,
        recommended_order_date: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
        seasonal_factor: 1.1,
        usage_volatility: 0.8,
        stockout_confidence: 0.85,
        last_calculated: new Date().toISOString(),
        calculation_window_days: 90
      }
    } else {
      const data = await medicationApi.getStockAnalytics(props.medication.id)
      analytics.value = data
    }
  } catch (error) {
    console.error('Failed to load stock analytics:', error)
  } finally {
    loading.value = false
  }
}

const refreshAnalytics = async () => {
  refreshing.value = true
  try {
    await loadAnalytics()
  } finally {
    refreshing.value = false
  }
}

const generateReport = async () => {
  generating.value = true
  try {
    // Implementation for generating PDF report
    console.log('Generating stock analytics report...')
  } finally {
    generating.value = false
  }
}

const placeOrder = async () => {
  try {
    // Implementation for placing automatic order
    console.log('Placing order for medication:', props.medication.id)
  } catch (error) {
    console.error('Failed to place order:', error)
  }
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString()
}

// Lifecycle
onMounted(() => {
  loadAnalytics()
})
</script>

<style scoped>
.stock-analytics {
  width: 100%;
}

.analytics-card {
  width: 100%;
}

.analytics-title {
  text-align: center;
}

.analytics-value {
  font-size: 1.5rem;
  font-weight: 700;
}

.analytics-label {
  font-size: 0.875rem;
  opacity: 0.7;
}
</style> 