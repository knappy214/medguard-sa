<script setup lang="ts">
interface Props {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showText?: boolean
  variant?: 'default' | 'white' | 'monochrome'
  className?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showText: true,
  variant: 'default',
  className: ''
})

const sizeClasses = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
  xl: 'w-24 h-24'
}

const textSizes = {
  sm: 'text-xs',
  md: 'text-sm',
  lg: 'text-base',
  xl: 'text-lg'
}

const variantClasses = {
  default: '',
  white: 'filter brightness-0 invert',
  monochrome: 'filter grayscale'
}
</script>

<template>
  <div :class="['flex items-center gap-2', className]">
    <!-- Logo Image -->
    <div :class="[sizeClasses[size], 'flex-shrink-0']">
      <img 
        src="/medguardLogo.png"
        alt="MedGuard SA Logo"
        :class="[variantClasses[variant], 'w-full h-full object-contain']"
        loading="lazy"
      />
    </div>
    
    <!-- Brand Text -->
    <div v-if="showText" :class="['flex flex-col', textSizes[size]]">
      <span class="font-bold text-base-content leading-tight">MEDGUARD SA</span>
      <span class="text-base-content/70 text-xs leading-tight">PROFESSIONAL APP</span>
    </div>
  </div>
</template> 