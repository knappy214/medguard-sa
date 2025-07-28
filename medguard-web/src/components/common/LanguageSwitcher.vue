<script setup lang="ts">
interface Props {
  currentLocale: 'en-ZA' | 'af-ZA'
}

interface Emits {
  (e: 'switch-language', locale: 'en-ZA' | 'af-ZA'): void
}

defineProps<Props>()
defineEmits<Emits>()

const languages = [
  { code: 'en-ZA', name: 'English', flag: '🇿🇦' },
  { code: 'af-ZA', name: 'Afrikaans', flag: '🇿🇦' }
] as const
</script>

<template>
  <div class="dropdown dropdown-end">
    <div tabindex="0" role="button" class="btn btn-ghost btn-sm">
      <span class="text-lg">{{ currentLocale === 'en-ZA' ? '🇿🇦' : '🇿🇦' }}</span>
      <span class="ml-2 text-sm font-medium">
        {{ currentLocale === 'en-ZA' ? 'EN' : 'AF' }}
      </span>
      <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </div>
    <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box shadow-lg border border-base-300 min-w-[120px]">
      <li v-for="lang in languages" :key="lang.code">
        <button
          @click="$emit('switch-language', lang.code)"
          :class="[
            'flex items-center space-x-2 px-3 py-2 text-sm',
            currentLocale === lang.code ? 'bg-primary text-primary-content' : 'hover:bg-base-200'
          ]"
        >
          <span class="text-base">{{ lang.flag }}</span>
          <span>{{ lang.name }}</span>
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