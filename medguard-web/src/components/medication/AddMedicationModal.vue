<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MedicationFormData } from '@/types/medication'

interface Emits {
  (e: 'close'): void
  (e: 'add', data: MedicationFormData): void
}

const emit = defineEmits<Emits>()

const { t } = useI18n()

// Form state
const form = reactive<MedicationFormData>({
  name: '',
  dosage: '',
  frequency: '',
  time: '',
  stock: 0,
  minStock: 10,
  instructions: '',
  category: ''
})

const errors = reactive<Record<string, string>>({})
const loading = ref(false)

// Form validation
const validateForm = (): boolean => {
  errors.name = ''
  errors.dosage = ''
  errors.frequency = ''
  errors.time = ''
  errors.stock = ''
  errors.minStock = ''
  errors.instructions = ''
  errors.category = ''

  let isValid = true

  if (!form.name.trim()) {
    errors.name = 'Medication name is required'
    isValid = false
  }

  if (!form.dosage.trim()) {
    errors.dosage = 'Dosage is required'
    isValid = false
  }

  if (!form.frequency.trim()) {
    errors.frequency = 'Frequency is required'
    isValid = false
  }

  if (!form.time.trim()) {
    errors.time = 'Time is required'
    isValid = false
  }

  if (form.stock < 0) {
    errors.stock = 'Stock cannot be negative'
    isValid = false
  }

  if (form.minStock < 0) {
    errors.minStock = 'Minimum stock cannot be negative'
    isValid = false
  }

  if (!form.instructions.trim()) {
    errors.instructions = 'Instructions are required'
    isValid = false
  }

  if (!form.category.trim()) {
    errors.category = 'Category is required'
    isValid = false
  }

  return isValid
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true
  try {
    await emit('add', { ...form })
    // Reset form
    Object.assign(form, {
      name: '',
      dosage: '',
      frequency: '',
      time: '',
      stock: 0,
      minStock: 10,
      instructions: '',
      category: ''
    })
  } catch (error) {
    console.error('Failed to add medication:', error)
  } finally {
    loading.value = false
  }
}

const handleClose = () => {
  emit('close')
}

// Predefined categories
const categories = [
  'Pain Relief',
  'Antibiotic',
  'Vitamin',
  'Blood Pressure',
  'Diabetes',
  'Heart Medication',
  'Mental Health',
  'Other'
]

// Predefined frequencies
const frequencies = [
  'Once daily',
  'Twice daily',
  'Three times daily',
  'Every 6 hours',
  'Every 8 hours',
  'Every 12 hours',
  'As needed',
  'Other'
]
</script>

<template>
  <div class="modal modal-open">
    <div class="modal-box w-11/12 max-w-2xl">
      <!-- Header -->
      <div class="flex justify-between items-center mb-6">
        <h3 class="font-bold text-lg text-base-content">
          <svg class="w-6 h-6 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          {{ t('dashboard.addMedication') }}
        </h3>
        <button @click="handleClose" class="btn btn-sm btn-circle btn-ghost">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <!-- Basic Information -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">Medication Name *</span>
            </label>
            <input
              v-model="form.name"
              type="text"
              placeholder="e.g., Paracetamol"
              :class="[
                'input input-bordered w-full',
                errors.name ? 'input-error' : ''
              ]"
            />
            <label v-if="errors.name" class="label">
              <span class="label-text-alt text-error">{{ errors.name }}</span>
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">Category *</span>
            </label>
            <select
              v-model="form.category"
              :class="[
                'select select-bordered w-full',
                errors.category ? 'select-error' : ''
              ]"
            >
              <option value="">Select category</option>
              <option v-for="category in categories" :key="category" :value="category">
                {{ category }}
              </option>
            </select>
            <label v-if="errors.category" class="label">
              <span class="label-text-alt text-error">{{ errors.category }}</span>
            </label>
          </div>
        </div>

        <!-- Dosage and Frequency -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">Dosage *</span>
            </label>
            <input
              v-model="form.dosage"
              type="text"
              placeholder="e.g., 500mg"
              :class="[
                'input input-bordered w-full',
                errors.dosage ? 'input-error' : ''
              ]"
            />
            <label v-if="errors.dosage" class="label">
              <span class="label-text-alt text-error">{{ errors.dosage }}</span>
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">Frequency *</span>
            </label>
            <select
              v-model="form.frequency"
              :class="[
                'select select-bordered w-full',
                errors.frequency ? 'select-error' : ''
              ]"
            >
              <option value="">Select frequency</option>
              <option v-for="frequency in frequencies" :key="frequency" :value="frequency">
                {{ frequency }}
              </option>
            </select>
            <label v-if="errors.frequency" class="label">
              <span class="label-text-alt text-error">{{ errors.frequency }}</span>
            </label>
          </div>
        </div>

        <!-- Time and Stock -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">Time *</span>
            </label>
            <input
              v-model="form.time"
              type="text"
              placeholder="e.g., 08:00, 14:00, 20:00"
              :class="[
                'input input-bordered w-full',
                errors.time ? 'input-error' : ''
              ]"
            />
            <label v-if="errors.time" class="label">
              <span class="label-text-alt text-error">{{ errors.time }}</span>
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">Current Stock</span>
            </label>
            <input
              v-model.number="form.stock"
              type="number"
              min="0"
              placeholder="0"
              :class="[
                'input input-bordered w-full',
                errors.stock ? 'input-error' : ''
              ]"
            />
            <label v-if="errors.stock" class="label">
              <span class="label-text-alt text-error">{{ errors.stock }}</span>
            </label>
          </div>

          <div class="form-control">
            <label class="label">
              <span class="label-text font-medium">Minimum Stock</span>
            </label>
            <input
              v-model.number="form.minStock"
              type="number"
              min="0"
              placeholder="10"
              :class="[
                'input input-bordered w-full',
                errors.minStock ? 'input-error' : ''
              ]"
            />
            <label v-if="errors.minStock" class="label">
              <span class="label-text-alt text-error">{{ errors.minStock }}</span>
            </label>
          </div>
        </div>

        <!-- Instructions -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">Instructions *</span>
          </label>
          <textarea
            v-model="form.instructions"
            placeholder="e.g., Take with food. Do not exceed 4 tablets per day."
            :class="[
              'textarea textarea-bordered h-24',
              errors.instructions ? 'textarea-error' : ''
            ]"
          ></textarea>
          <label v-if="errors.instructions" class="label">
            <span class="label-text-alt text-error">{{ errors.instructions }}</span>
          </label>
        </div>

        <!-- Form Actions -->
        <div class="modal-action">
          <button
            type="button"
            @click="handleClose"
            class="btn btn-ghost"
            :disabled="loading"
          >
            {{ t('common.cancel') }}
          </button>
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="loading"
          >
            <span v-if="loading" class="loading loading-spinner loading-sm"></span>
            {{ loading ? t('common.loading') : t('common.save') }}
          </button>
        </div>
      </form>
    </div>

    <!-- Backdrop -->
    <div class="modal-backdrop" @click="handleClose"></div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  @apply bg-base-content/20;
}

.form-control {
  @apply w-full;
}

/* Custom styling for form elements */
.input:focus,
.select:focus,
.textarea:focus {
  @apply border-primary;
  @apply ring-2 ring-primary/20;
}

.input-error:focus,
.select-error:focus,
.textarea-error:focus {
  @apply border-error;
  @apply ring-2 ring-error/20;
}
</style> 