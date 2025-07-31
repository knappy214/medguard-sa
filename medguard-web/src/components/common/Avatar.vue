<template>
  <div class="avatar" :class="avatarClasses">
    <div :class="sizeClasses">
      <img 
        v-if="src" 
        :src="src" 
        :alt="alt"
        class="mask mask-circle object-cover"
      />
      <div 
        v-else 
        class="w-full h-full bg-primary text-primary-content flex items-center justify-center font-bold mask mask-circle"
        :class="textSizeClasses"
      >
        {{ initials }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'

interface Props {
  src?: string
  alt?: string
  name?: string
  email?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  status?: 'online' | 'offline'
  avatarClasses?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  alt: 'User avatar',
  avatarClasses: ''
})

// Debug logging
console.log('Avatar component props:', {
  src: props.src,
  name: props.name,
  email: props.email,
  size: props.size
})

// Watch for changes in props
watch(() => props.src, (newSrc) => {
  console.log('Avatar src changed:', newSrc)
})

const initials = computed(() => {
  if (props.name && props.name.trim()) {
    const nameParts = props.name.trim().split(' ')
    if (nameParts.length >= 2) {
      return `${nameParts[0][0]?.toUpperCase() || ''}${nameParts[nameParts.length - 1][0]?.toUpperCase() || ''}`
    } else {
      return nameParts[0][0]?.toUpperCase() || ''
    }
  } else if (props.email && props.email.trim()) {
    return props.email[0]?.toUpperCase() || 'U'
  } else {
    return 'U'
  }
})

const sizeClasses = computed(() => {
  const sizes = {
    xs: 'w-6 h-6',
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
    xl: 'w-20 h-20',
    '2xl': 'w-24 h-24'
  }
  return sizes[props.size]
})

const textSizeClasses = computed(() => {
  const sizes = {
    xs: 'text-xs',
    sm: 'text-sm',
    md: 'text-lg',
    lg: 'text-xl',
    xl: 'text-2xl',
    '2xl': 'text-3xl'
  }
  return sizes[props.size]
})
</script> 