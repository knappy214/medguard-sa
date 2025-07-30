<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

interface Language {
  code: string
  name: string
  flag: string
  nativeName: string
}

const languages: Language[] = [
  { code: 'en', name: 'English', flag: '🇿🇦', nativeName: 'English' },
  { code: 'af', name: 'Afrikaans', flag: '🇿🇦', nativeName: 'Afrikaans' }
]

const currentLanguageCode = computed({
  get: () => {
    return locale.value || 'en'
  },
  set: (value: string) => {
    locale.value = value
  }
})

const currentLanguage = computed(() => {
  return languages.find(lang => lang.code === currentLanguageCode.value) || languages[0]
})

const changeLanguage = (): void => {
  // Language change is handled by the computed setter
}
</script>

<template>
  <div class="language-switcher">
    <select 
      v-model="currentLanguageCode"
      @change="changeLanguage"
      class="select select-bordered select-sm bg-base-100 text-high-contrast border-base-300 focus:border-primary"
    >
      <option 
        v-for="lang in languages" 
        :key="lang.code" 
        :value="lang.code"
        class="text-high-contrast"
      >
        {{ lang.flag }} {{ lang.nativeName }}
      </option>
    </select>
  </div>
</template>

<style scoped>
.language-switcher {
  position: relative;
}

.language-switcher select {
  min-width: 120px;
  font-weight: 500;
}

.language-switcher select:focus {
  outline: 2px solid hsl(var(--color-primary));
  outline-offset: 2px;
}
</style> 