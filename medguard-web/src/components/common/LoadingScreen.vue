<script setup lang="ts">
import Logo from './Logo.vue'

interface Props {
  message?: string
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  message: 'Loading MedGuard SA...',
  size: 'lg'
})

const sizeClasses = {
  sm: 'w-16 h-16',
  md: 'w-24 h-24',
  lg: 'w-32 h-32'
}
</script>

<template>
  <div class="fixed inset-0 bg-base-100 flex items-center justify-center z-50">
    <div class="text-center">
      <!-- Animated Logo -->
      <div class="mb-8 flex justify-center">
        <div :class="[sizeClasses[size], 'animate-pulse']">
          <Logo :size="size" :show-text="false" />
        </div>
      </div>
      
      <!-- Loading Message -->
      <div class="text-base-content/70 text-lg font-medium mb-4">
        {{ message }}
      </div>
      
      <!-- Loading Spinner -->
      <div class="flex justify-center">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
      
      <!-- Brand Text -->
      <div class="mt-8">
        <Logo size="md" />
      </div>
    </div>
  </div>
</template> 