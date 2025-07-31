<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { StockAlert } from '@/types/medication'

interface Props {
  alerts: StockAlert[]
  unreadAlerts: StockAlert[]
}

interface Emits {
  (e: 'mark-as-read', alertId: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { t } = useI18n()

// Computed properties
const sortedAlerts = computed(() => {
  return [...props.alerts].sort((a, b) => 
    new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  )
})

const getAlertIcon = (type: string) => {
  switch (type) {
    case 'low_stock':
      return '⚠️'
    case 'out_of_stock':
      return '🚨'
    case 'expiring_soon':
      return '⏰'
    default:
      return 'ℹ️'
  }
}

const getAlertColor = (severity: string) => {
  switch (severity) {
    case 'error':
      return 'alert-error'
    case 'warning':
      return 'alert-warning'
    case 'info':
      return 'alert-info'
    default:
      return 'alert-info'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleMarkAsRead = (alertId: string) => {
  emit('mark-as-read', alertId)
}

// Function to get localized alert message
const getLocalizedMessage = (alert: StockAlert) => {
  if (alert.type === 'low_stock') {
    const stock = alert.medication.stock
    if (alert.severity === 'error') {
      return t('dashboard.stockCriticalMessage', { 
        medication: alert.medication.name, 
        count: stock 
      })
    } else {
      return t('dashboard.stockLowMessage', { 
        medication: alert.medication.name, 
        count: stock 
      })
    }
  }
  return alert.message
}
</script>

<template>
  <div class="card bg-base-100 shadow-sm">
    <div class="card-body">
      <h2 class="card-title text-xl mb-4 text-base-content">
        <svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        {{ t('dashboard.stockAlerts') }}
        <span v-if="unreadAlerts.length > 0" class="badge badge-error badge-sm">
          {{ unreadAlerts.length }}
        </span>
      </h2>

      <!-- Alerts Summary -->
      <div class="flex flex-wrap gap-2 mb-4">
        <div class="badge badge-error gap-1">
          <span>🚨</span>
          {{ alerts.filter((a: StockAlert) => a.severity === 'error').length }} {{ t('dashboard.critical') }}
        </div>
        <div class="badge badge-warning gap-1">
          <span>⚠️</span>
          {{ alerts.filter((a: StockAlert) => a.severity === 'warning').length }} {{ t('dashboard.warning') }}
        </div>
        <div class="badge badge-info gap-1">
          <span>ℹ️</span>
          {{ alerts.filter((a: StockAlert) => a.severity === 'info').length }} {{ t('dashboard.info') }}
        </div>
      </div>

      <!-- Alerts List -->
      <div v-if="sortedAlerts.length === 0" class="text-center py-8">
        <div class="text-4xl mb-4">✅</div>
        <p class="text-base-content/70">{{ t('dashboard.noAlerts') }}</p>
      </div>

      <div v-else class="space-y-3 max-h-96 overflow-y-auto">
        <div
          v-for="alert in sortedAlerts"
          :key="alert.id"
          :class="[
            'alert transition-all duration-200',
            getAlertColor(alert.severity),
            !alert.isRead ? 'border-2' : ''
          ]"
        >
          <div class="flex-1">
            <div class="flex items-start justify-between mb-2">
              <div class="flex items-center gap-2">
                <span class="text-lg">{{ getAlertIcon(alert.type) }}</span>
                <h3 class="font-semibold text-base-content">
                  {{ alert.medication.name }}
                </h3>
                <span v-if="!alert.isRead" class="badge badge-primary badge-xs">
                  {{ t('dashboard.new') }}
                </span>
              </div>
              <button
                v-if="!alert.isRead"
                @click="handleMarkAsRead(alert.id)"
                class="btn btn-ghost btn-xs"
                :title="t('dashboard.markAsRead')"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </button>
            </div>
            
            <p class="text-sm text-base-content mb-2">
              {{ getLocalizedMessage(alert) }}
            </p>
            
            <div class="flex items-center justify-between text-xs text-base-content/60">
              <span>{{ formatDate(alert.createdAt) }}</span>
              <span class="capitalize">{{ alert.type.replace('_', ' ') }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-4 space-y-2">
        <button
          v-if="unreadAlerts.length > 0"
          @click="unreadAlerts.forEach((alert: StockAlert) => handleMarkAsRead(alert.id))"
          class="btn btn-outline btn-sm btn-block"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          {{ t('dashboard.markAllAsRead') }}
        </button>
        
        <button class="btn btn-primary btn-sm btn-block">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ t('dashboard.refillReminder') }}
        </button>
      </div>

      <!-- Alert Legend -->
      <div class="mt-4 p-3 bg-base-200/50 border border-base-300 rounded-lg">
        <p class="text-sm text-base-content/80">
          <strong>{{ t('dashboard.legend') }}:</strong> {{ t('dashboard.legendText') }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.card {
  border-left: 4px solid;
  border-left-color: hsl(var(--color-warning));
}

/* Custom scrollbar for alerts list */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background-color: hsl(var(--color-base-200));
  border-radius: 9999px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: hsl(var(--color-base-content) / 0.2);
  border-radius: 9999px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background-color: hsl(var(--color-base-content) / 0.3);
}
</style> 