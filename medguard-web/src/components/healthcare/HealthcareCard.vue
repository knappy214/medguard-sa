<template>
  <div class="healthcare-card p-6">
    <div class="flex items-start justify-between mb-4">
      <div class="flex items-center space-x-3">
        <div class="avatar placeholder">
          <div class="bg-primary text-primary-content rounded-full w-12 h-12 flex items-center justify-center">
            <span class="text-lg font-semibold">{{ icon }}</span>
          </div>
        </div>
        <div>
          <h3 class="text-lg font-semibold text-base-content">{{ title }}</h3>
          <p v-if="subtitle" class="text-sm text-base-content-secondary">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="status" class="badge" :class="statusClass">
        {{ status }}
      </div>
    </div>
    
    <div class="space-y-3">
      <slot />
    </div>
    
    <div v-if="$slots.actions" class="flex justify-end space-x-2 mt-4 pt-4 border-t border-base-300">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  title: string
  subtitle?: string
  icon?: string
  status?: string
  statusType?: 'success' | 'warning' | 'error' | 'info' | 'neutral'
}

const props = withDefaults(defineProps<Props>(), {
  icon: '🏥',
  statusType: 'neutral'
})

const statusClass = computed(() => {
  const baseClass = 'badge'
  switch (props.statusType) {
    case 'success':
      return `${baseClass} badge-success`
    case 'warning':
      return `${baseClass} badge-warning`
    case 'error':
      return `${baseClass} badge-error`
    case 'info':
      return `${baseClass} badge-info`
    default:
      return `${baseClass} badge-neutral`
  }
})
</script>

<style scoped>
.healthcare-card {
  transition: all 0.2s ease-in-out;
}

.healthcare-card:hover {
  transform: translateY(-1px);
}
</style> 