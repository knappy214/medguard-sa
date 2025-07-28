<script setup lang="ts">
import { useLanguagePreference } from '@/composables/useLanguagePreference'

const { currentLocale, switchLanguage, availableLanguages } = useLanguagePreference()

// Get current language display info
const currentLanguage = availableLanguages.find(lang => lang.code === currentLocale.value) || availableLanguages[0]
</script>

<template>
  <div class="dropdown dropdown-end">
    <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
      <span class="text-lg">{{ currentLanguage.flag }}</span>
      <span class="ml-2 text-sm font-medium">
        {{ currentLanguage.code === 'en-ZA' ? 'EN' : 'AF' }}
      </span>
      <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>
    <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box shadow-lg border border-base-300 min-w-[140px]">
      <li v-for="lang in availableLanguages" :key="lang.code">
        <button
          @click="switchLanguage(lang.code)"
          :class="[
            'flex items-center space-x-2 px-3 py-2 text-sm',
            currentLocale === lang.code ? 'bg-primary text-primary-content' : 'hover:bg-base-200'
          ]"
        >
          <span class="text-base">{{ lang.flag }}</span>
          <div class="flex flex-col items-start">
            <span class="font-medium">{{ lang.name }}</span>
            <span class="text-xs opacity-70">{{ lang.nativeName }}</span>
          </div>
        </button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.dropdown-content {
  z-index: 1000;
}
</style> 