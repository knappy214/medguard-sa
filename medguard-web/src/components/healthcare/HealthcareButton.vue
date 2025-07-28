<template>
  <button
    :class="buttonClasses"
    :disabled="disabled || loading"
    :type="type"
    @click="handleClick"
    :aria-label="ariaLabel"
    :aria-describedby="ariaDescribedby"
  >
    <div v-if="loading" class="loading loading-spinner loading-sm"></div>
    <span v-if="icon && !loading" class="mr-2">{{ icon }}</span>
    <slot />
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'ghost' | 'outline'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  icon?: string
  type?: 'button' | 'submit' | 'reset'
  ariaLabel?: string
  ariaDescribedby?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  type: 'button'
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClasses = computed(() => {
  const baseClasses = 'btn font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2'
  
  // Size classes
  const sizeClasses = {
    xs: 'btn-xs',
    sm: 'btn-sm',
    md: 'btn-md',
    lg: 'btn-lg'
  }
  
  // Variant classes
  const variantClasses = {
    primary: 'healthcare-button-primary',
    secondary: 'healthcare-button-secondary',
    success: 'healthcare-button-success',
    warning: 'healthcare-button-warning',
    error: 'healthcare-button-error',
    info: 'btn-info',
    ghost: 'btn-ghost',
    outline: 'btn-outline'
  }
  
  const disabledClasses = props.disabled || props.loading ? 'opacity-50 cursor-not-allowed' : ''
  
  return `${baseClasses} ${sizeClasses[props.size]} ${variantClasses[props.variant]} ${disabledClasses}`
})

const handleClick = (event: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', event)
  }
}
</script>

<style scoped>
.btn:focus-visible {
  @apply ring-2 ring-primary ring-offset-2;
}

.btn:active:not(:disabled) {
  transform: scale(0.98);
}

/* Loading state animation */
.loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style> 