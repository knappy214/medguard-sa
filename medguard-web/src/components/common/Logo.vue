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
    <!-- Logo Icon -->
    <div :class="[sizeClasses[size], 'flex-shrink-0']">
      <svg 
        xmlns="http://www.w3.org/2000/svg" 
        viewBox="0 0 64 64" 
        :class="[variantClasses[variant], 'w-full h-full']"
        aria-label="MedGuard SA Logo"
      >
        <!-- Shield Background with Shadow -->
        <defs>
          <filter id="logo-shadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="1" dy="2" stdDeviation="2" flood-color="rgba(0,0,0,0.3)"/>
          </filter>
        </defs>
        
        <!-- Shield Shape -->
        <path 
          d="M32 8 L48 12 L48 28 C48 36 42 40 32 44 L24 42 C18 40 12 36 12 28 L12 12 Z" 
          fill="url(#shieldGradient)" 
          stroke="white" 
          stroke-width="1"
          filter="url(#logo-shadow)"
        />
        
        <!-- Gradient for Shield -->
        <defs>
          <linearGradient id="shieldGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#10B981;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#10B981;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#2563EB;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#2563EB;stop-opacity:1" />
          </linearGradient>
        </defs>
        
        <!-- Medical Cross (Left Side) -->
        <g transform="translate(20, 24)">
          <rect x="-4" y="-1" width="8" height="2" fill="white" rx="1"/>
          <rect x="-1" y="-4" width="2" height="8" fill="white" rx="1"/>
        </g>
        
        <!-- Pill/Capsule (Right Side) -->
        <g transform="translate(44, 26)">
          <!-- Left segment of capsule -->
          <ellipse cx="-4" cy="0" rx="6" ry="4" fill="#60A5FA"/>
          <ellipse cx="-4" cy="0" rx="5" ry="3" fill="#93C5FD"/>
          <!-- Curved line in left segment -->
          <path d="M-8 -1.5 Q-6 -0.5 -4 -1.5 Q-2 -2.5 0 -1.5" stroke="white" stroke-width="0.5" fill="none"/>
          
          <!-- Right segment of capsule -->
          <ellipse cx="4" cy="0" rx="6" ry="4" fill="white"/>
          <!-- Medical cross in right segment -->
          <g transform="translate(4, 0)">
            <rect x="-1.5" y="-0.5" width="3" height="1" fill="#60A5FA" rx="0.5"/>
            <rect x="-0.5" y="-1.5" width="1" height="3" fill="#60A5FA" rx="0.5"/>
          </g>
          
          <!-- Center line connecting segments -->
          <rect x="-1" y="-4" width="2" height="8" fill="#E5E7EB" rx="1"/>
        </g>
      </svg>
    </div>
    
    <!-- Brand Text -->
    <div v-if="showText" :class="['flex flex-col', textSizes[size]]">
      <span class="font-bold text-base-content leading-tight">MEDGUARD SA</span>
      <span class="text-base-content/70 text-xs leading-tight">PROFESSIONAL APP</span>
    </div>
  </div>
</template> 