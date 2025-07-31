<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { MedicationFormData, Medication } from '@/types/medication'

interface Props {
  medication?: Medication | null
  mode?: 'add' | 'edit'
}

interface Emits {
  (e: 'close'): void
  (e: 'add', data: MedicationFormData): void
}

const props = withDefaults(defineProps<Props>(), {
  mode: 'add'
})

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
  category: '',
  // Schedule information
  scheduleTiming: 'morning',
  scheduleCustomTime: '',
  scheduleDosageAmount: 1.0,
  scheduleInstructions: ''
})

const errors = reactive<Record<string, string>>({})
const loading = ref(false)

// Watch for medication prop changes to populate form in edit mode
watch(() => props.medication, (medication) => {
  if (medication && props.mode === 'edit') {
    Object.assign(form, {
      name: medication.name,
      dosage: medication.dosage,
      frequency: medication.frequency,
      time: medication.time,
      stock: medication.stock,
      minStock: medication.minStock,
      instructions: medication.instructions,
      category: medication.category
    })
  }
}, { immediate: true })

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
    errors.name = t('validation.medicationNameRequired')
    isValid = false
  }

  if (!form.dosage.trim()) {
    errors.dosage = t('validation.dosageRequired')
    isValid = false
  }

  if (!form.frequency.trim()) {
    errors.frequency = t('validation.frequencyRequired')
    isValid = false
  }

  if (!form.time.trim()) {
    errors.time = t('validation.timeRequired')
    isValid = false
  }

  if (form.stock < 0) {
    errors.stock = t('validation.stockCannotBeNegative')
    isValid = false
  }

  if (form.minStock < 0) {
    errors.minStock = t('validation.minStockCannotBeNegative')
    isValid = false
  }

  if (!form.instructions.trim()) {
    errors.instructions = t('validation.instructionsRequired')
    isValid = false
  }

  if (!form.category.trim()) {
    errors.category = t('validation.categoryRequired')
    isValid = false
  }

  // Validate schedule information
  if (form.scheduleTiming === 'custom' && !form.scheduleCustomTime) {
    errors.scheduleCustomTime = t('validation.customTimeRequired')
    isValid = false
  }

  if ((form.scheduleDosageAmount || 0) <= 0) {
    errors.scheduleDosageAmount = t('validation.dosageAmountMustBePositive')
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
          {{ props.mode === 'edit' ? t('dashboard.editMedication') : t('dashboard.addMedication') }}
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
              <span class="label-text font-medium">{{ t('form.medicationName') }} *</span>
            </label>
            <input
              v-model="form.name"
              type="text"
              :placeholder="t('form.medicationName')"
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
              <span class="label-text font-medium">{{ t('form.category') }} *</span>
            </label>
            <select
              v-model="form.category"
              :class="[
                'select select-bordered w-full',
                errors.category ? 'select-error' : ''
              ]"
            >
              <option value="">{{ t('form.selectFrequency') }}</option>
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
              <span class="label-text font-medium">{{ t('form.dosage') }} *</span>
            </label>
            <input
              v-model="form.dosage"
              type="text"
              :placeholder="t('form.dosagePlaceholder')"
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
              <span class="label-text font-medium">{{ t('form.frequency') }} *</span>
            </label>
            <select
              v-model="form.frequency"
              :class="[
                'select select-bordered w-full',
                errors.frequency ? 'select-error' : ''
              ]"
            >
              <option value="">{{ t('form.selectFrequency') }}</option>
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
              <span class="label-text font-medium">{{ t('form.time') }} *</span>
            </label>
            <input
              v-model="form.time"
              type="text"
              :placeholder="t('form.timePlaceholder')"
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
              <span class="label-text font-medium">{{ t('form.currentStock') }}</span>
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
              <span class="label-text font-medium">{{ t('form.minimumStock') }}</span>
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

        <!-- Schedule Information -->
        <div class="card bg-base-200 p-4 mb-4">
          <h4 class="font-semibold text-base-content mb-3">
            <svg class="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {{ t('form.scheduleInformation') }}
          </h4>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.scheduleTiming') }}</span>
              </label>
              <select
                v-model="form.scheduleTiming"
                class="select select-bordered w-full"
              >
                <option value="morning">{{ t('form.morning') }}</option>
                <option value="noon">{{ t('form.noon') }}</option>
                <option value="night">{{ t('form.night') }}</option>
                <option value="custom">{{ t('form.customTime') }}</option>
              </select>
            </div>

            <div class="form-control" v-if="form.scheduleTiming === 'custom'">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.customTime') }}</span>
              </label>
              <input
                v-model="form.scheduleCustomTime"
                type="time"
                :class="[
                  'input input-bordered w-full',
                  errors.scheduleCustomTime ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.scheduleCustomTime" class="label">
                <span class="label-text-alt text-error">{{ errors.scheduleCustomTime }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.dosageAmount') }}</span>
              </label>
              <input
                v-model.number="form.scheduleDosageAmount"
                type="number"
                min="0.1"
                step="0.1"
                placeholder="1.0"
                :class="[
                  'input input-bordered w-full',
                  errors.scheduleDosageAmount ? 'input-error' : ''
                ]"
              />
              <label v-if="errors.scheduleDosageAmount" class="label">
                <span class="label-text-alt text-error">{{ errors.scheduleDosageAmount }}</span>
              </label>
            </div>

            <div class="form-control">
              <label class="label">
                <span class="label-text font-medium">{{ t('form.scheduleInstructions') }}</span>
              </label>
              <textarea
                v-model="form.scheduleInstructions"
                :placeholder="t('form.scheduleInstructionsPlaceholder')"
                class="textarea textarea-bordered h-20"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Instructions -->
        <div class="form-control">
          <label class="label">
            <span class="label-text font-medium">{{ t('form.instructions') }} *</span>
          </label>
          <textarea
            v-model="form.instructions"
            :placeholder="t('form.instructionsPlaceholder')"
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
            {{ loading ? t('common.loading') : (props.mode === 'edit' ? t('common.update') : t('common.save')) }}
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
  background-color: hsl(var(--color-base-content) / 0.2);
}

.form-control {
  width: 100%;
}

/* Custom styling for form elements */
.input:focus,
.select:focus,
.textarea:focus {
  border-color: hsl(var(--color-primary));
  box-shadow: 0 0 0 2px hsl(var(--color-primary) / 0.2);
}

.input-error:focus,
.select-error:focus,
.textarea-error:focus {
  border-color: hsl(var(--color-error));
  box-shadow: 0 0 0 2px hsl(var(--color-error) / 0.2);
}
</style> 