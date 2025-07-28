import './style.css'

import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'

// Import translation files
import en from './locales/en.json'
import af from './locales/af.json'

// South African locale formatting
const dateTimeFormats = {
  'en-ZA': {
    short: {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    },
    long: {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    },
    time: {
      hour: '2-digit',
      minute: '2-digit'
    }
  },
  'af-ZA': {
    short: {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    },
    long: {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      weekday: 'long'
    },
    time: {
      hour: '2-digit',
      minute: '2-digit'
    }
  }
}

const numberFormats = {
  'en-ZA': {
    currency: {
      style: 'currency' as const,
      currency: 'ZAR',
      currencyDisplay: 'symbol' as const
    },
    decimal: {
      style: 'decimal' as const,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    },
    percent: {
      style: 'percent' as const,
      minimumFractionDigits: 2
    }
  },
  'af-ZA': {
    currency: {
      style: 'currency' as const,
      currency: 'ZAR',
      currencyDisplay: 'symbol' as const
    },
    decimal: {
      style: 'decimal' as const,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    },
    percent: {
      style: 'percent' as const,
      minimumFractionDigits: 2
    }
  }
}

// i18n setup
const i18n = createI18n({
  legacy: false,
  locale: 'en-ZA',
  fallbackLocale: 'en-ZA',
  messages: {
    'en-ZA': en,
    'af-ZA': af
  },
  dateTimeFormats,
  numberFormats,
  missingWarn: false,
  fallbackWarn: false
})

const app = createApp(App)
app.use(i18n)
app.mount('#app')
