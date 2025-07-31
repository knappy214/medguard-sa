import './style.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import router from './router'
import App from './App.vue'

// Import locale messages
import en from './locales/en.json'
import af from './locales/af.json'

// Import API switch utility for development
import '@/utils/apiSwitch'

// Create Pinia instance
const pinia = createPinia()

// Composition API i18n setup with external locale files
const i18n = createI18n({
  legacy: false, // Use Composition API mode for script setup
  globalInjection: true, // This enables $i18n global property
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en,
    af
  },
  silentTranslationWarn: true,
  silentFallbackWarn: true
})

const app = createApp(App)
app.use(pinia)
app.use(i18n)
app.use(router)
app.mount('#app')
