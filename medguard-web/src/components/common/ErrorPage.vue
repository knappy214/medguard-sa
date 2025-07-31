<script setup lang="ts">
import { useRouter } from 'vue-router'
import Logo from './Logo.vue'

interface Props {
  code?: string
  title?: string
  message?: string
  showHomeButton?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  code: '404',
  title: 'Page Not Found',
  message: 'Sorry, the page you are looking for could not be found.',
  showHomeButton: true
})

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.go(-1)
}
</script>

<template>
  <div class="min-h-screen bg-base-100 flex items-center justify-center p-4">
    <div class="card w-full max-w-md bg-base-100 shadow-xl">
      <div class="card-body text-center">
        <!-- Logo -->
        <div class="flex justify-center mb-6">
          <Logo size="xl" :show-text="false" />
        </div>
        
        <!-- Error Code -->
        <div class="text-8xl font-bold text-primary mb-4">{{ code }}</div>
        
        <!-- Error Title -->
        <h1 class="text-2xl font-bold text-base-content mb-4">{{ title }}</h1>
        
        <!-- Error Message -->
        <p class="text-base-content/70 mb-8">{{ message }}</p>
        
        <!-- Action Buttons -->
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button @click="goBack" class="btn btn-outline">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Go Back
          </button>
          
          <button v-if="showHomeButton" @click="goHome" class="btn btn-primary">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Go to Dashboard
          </button>
        </div>
        
        <!-- Brand Footer -->
        <div class="mt-8 pt-6 border-t border-base-300">
          <Logo size="md" />
        </div>
      </div>
    </div>
  </div>
</template> 