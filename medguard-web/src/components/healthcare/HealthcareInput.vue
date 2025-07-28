<template>
  <div class="form-control w-full">
    <label v-if="label" :for="inputId" class="label">
      <span class="label-text font-medium text-base-content">{{ label }}</span>
      <span v-if="required" class="label-text-alt text-error">*</span>
    </label>
    
    <div class="relative">
      <input
        :id="inputId"
        :type="inputType"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :min="min"
        :max="max"
        :step="step"
        :pattern="pattern"
        :aria-describedby="ariaDescribedby"
        :aria-invalid="hasError"
        :class="inputClasses"
        @input="handleInput"
        @blur="handleBlur"
        @focus="handleFocus"
      />
      
      <div v-if="icon" class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
        <span class="text-base-content-secondary">{{ icon }}</span>
      </div>
      
      <div v-if="hasError" class="absolute inset-y-0 right-0 pr-3 flex items-center">
        <span class="text-error">⚠️</span>
      </div>
    </div>
    
    <label v-if="errorMessage" class="label">
      <span class="label-text-alt text-error">{{ errorMessage }}</span>
    </label>
    
    <label v-else-if="helpText" class="label">
      <span class="label-text-alt text-base-content-secondary">{{ helpText }}</span>
    </label>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  modelValue?: string | number
  label?: string
  placeholder?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'search' | 'date' | 'time' | 'datetime-local'
  disabled?: boolean
  required?: boolean
  icon?: string
  helpText?: string
  errorMessage?: string
  min?: string | number
  max?: string | number
  step?: string | number
  pattern?: string
  ariaDescribedby?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  disabled: false,
  required: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  blur: [event: FocusEvent]
  focus: [event: FocusEvent]
  input: [event: Event]
}>()

const inputId = ref(`healthcare-input-${Math.random().toString(36).substr(2, 9)}`)

const inputType = computed(() => {
  // Map Vue types to HTML input types
  const typeMap: Record<string, string> = {
    'datetime-local': 'datetime-local'
  }
  return typeMap[props.type] || props.type
})

const hasError = computed(() => !!props.errorMessage)

const inputClasses = computed(() => {
  const baseClasses = 'input input-bordered w-full transition-colors duration-200'
  const stateClasses = hasError.value ? 'input-error' : 'focus:input-primary'
  const iconClasses = props.icon ? 'pl-10' : ''
  const errorClasses = hasError.value ? 'pr-10' : ''
  
  return `${baseClasses} ${stateClasses} ${iconClasses} ${errorClasses}`
})

const handleInput = (event: Event) => {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
  emit('input', event)
}

const handleBlur = (event: FocusEvent) => {
  emit('blur', event)
}

const handleFocus = (event: FocusEvent) => {
  emit('focus', event)
}
</script>

<style scoped>
.input:focus {
  @apply ring-2 ring-primary ring-offset-2;
}

.input:disabled {
  @apply opacity-50 cursor-not-allowed;
}

/* Custom focus styles for better accessibility */
.input:focus-visible {
  @apply outline-none ring-2 ring-primary ring-offset-2;
}

/* Error state styling */
.input-error {
  @apply border-error focus:ring-error;
}

/* Success state when no error */
.input:not(.input-error):focus {
  @apply border-primary;
}
</style> 