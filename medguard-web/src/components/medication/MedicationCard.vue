<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Medication } from '@/types/medication'

interface Props {
  medication: Medication
}

interface Emits {
  (e: 'delete', id: string): void
  (e: 'edit', medication: Medication): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { t } = useI18n()

// Computed properties
const stockStatus = computed(() => {
  if (props.medication.stock === 0) {
    return { status: 'out-of-stock', color: 'error', text: t('dashboard.outOfStock') }
  } else if (props.medication.stock <= props.medication.minStock) {
    return { status: 'low-stock', color: 'warning', text: t('dashboard.lowStock') }
  } else {
    return { status: 'in-stock', color: 'success', text: 'In Stock' }
  }
})

const stockPercentage = computed(() => {
  const maxStock = Math.max(props.medication.stock, props.medication.minStock * 2)
  return Math.round((props.medication.stock / maxStock) * 100)
})

const handleDelete = () => {
  if (confirm('Are you sure you want to delete this medication?')) {
    emit('delete', props.medication.id)
  }
}

const handleEdit = () => {
  emit('edit', props.medication)
}
</script>

<template>
  <div class="card bg-base-100 shadow-sm hover:shadow-md transition-shadow duration-200">
    <div class="card-body p-4">
      <!-- Header with name and stock status -->
      <div class="flex justify-between items-start mb-3">
        <div class="flex-1">
          <h3 class="font-semibold text-base-content text-lg truncate">
            {{ medication.name }}
          </h3>
          <p class="text-base-content-secondary text-sm">
            {{ medication.dosage }} • {{ medication.frequency }}
          </p>
        </div>
        <div class="dropdown dropdown-end">
          <div tabindex="0" role="button" class="btn btn-ghost btn-xs">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
            </svg>
          </div>
          <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box shadow-lg border border-base-300 min-w-[120px] z-50">
            <li>
              <button @click="handleEdit" class="text-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                {{ t('common.edit') }}
              </button>
            </li>
            <li>
              <button @click="handleDelete" class="text-error text-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                {{ t('common.delete') }}
              </button>
            </li>
          </ul>
        </div>
      </div>

      <!-- Stock Information -->
      <div class="mb-3">
        <div class="flex justify-between items-center mb-2">
          <span class="text-sm font-medium text-base-content-secondary">
            {{ t('dashboard.status') }}
          </span>
          <span :class="`badge badge-${stockStatus.color} badge-sm`">
            {{ stockStatus.text }}
          </span>
        </div>
        
        <!-- Stock Progress Bar -->
        <div class="w-full bg-base-200 rounded-full h-2 mb-2">
          <div 
            :class="`h-2 rounded-full transition-all duration-300 ${
              stockStatus.color === 'error' ? 'bg-error' :
              stockStatus.color === 'warning' ? 'bg-warning' : 'bg-success'
            }`"
            :style="{ width: `${stockPercentage}%` }"
          ></div>
        </div>
        
        <div class="flex justify-between items-center text-xs text-base-content-secondary">
          <span>{{ medication.stock }} {{ t('dashboard.pillsRemaining') }}</span>
          <span>Min: {{ medication.minStock }}</span>
        </div>
      </div>

      <!-- Schedule Information -->
      <div class="mb-3">
        <div class="flex items-center text-sm text-base-content-secondary mb-1">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ t('dashboard.time') }}
        </div>
        <p class="text-sm text-base-content">{{ medication.time }}</p>
      </div>

      <!-- Instructions -->
      <div class="mb-3">
        <div class="flex items-center text-sm text-base-content-secondary mb-1">
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {{ t('dashboard.dosage') }}
        </div>
        <p class="text-sm text-base-content line-clamp-2">{{ medication.instructions }}</p>
      </div>

      <!-- Category Badge -->
      <div class="flex justify-between items-center">
        <span class="badge badge-outline badge-sm">{{ medication.category }}</span>
        <div class="text-xs text-base-content-secondary">
          {{ new Date(medication.updatedAt).toLocaleDateString() }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card {
  border-left: 4px solid;
  border-left-color: hsl(var(--color-primary));
}

.card:hover {
  border-left-color: hsl(var(--color-secondary));
}
</style> 