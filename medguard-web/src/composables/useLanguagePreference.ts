import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const STORAGE_KEY = 'medguard-locale'

export function useLanguagePreference() {
  const { locale } = useI18n()
  const currentLocale = ref<'en-ZA' | 'af-ZA'>('en-ZA')

  // Initialize from localStorage
  const initializeLocale = () => {
    const savedLocale = localStorage.getItem(STORAGE_KEY)
    if (savedLocale && (savedLocale === 'en-ZA' || savedLocale === 'af-ZA')) {
      currentLocale.value = savedLocale as 'en-ZA' | 'af-ZA'
      locale.value = savedLocale as 'en-ZA' | 'af-ZA'
    } else {
      // Set default based on browser language
      const browserLang = navigator.language
      if (browserLang.startsWith('af')) {
        currentLocale.value = 'af-ZA'
        locale.value = 'af-ZA'
      } else {
        currentLocale.value = 'en-ZA'
        locale.value = 'en-ZA'
      }
    }
  }

  // Switch language
  const switchLanguage = (newLocale: 'en-ZA' | 'af-ZA') => {
    currentLocale.value = newLocale
    locale.value = newLocale
    localStorage.setItem(STORAGE_KEY, newLocale)
  }

  // Watch for locale changes and persist
  watch(locale, (newLocale) => {
    if (newLocale === 'en-ZA' || newLocale === 'af-ZA') {
      currentLocale.value = newLocale as 'en-ZA' | 'af-ZA'
      localStorage.setItem(STORAGE_KEY, newLocale)
    }
  })

  // Get available languages
  const availableLanguages = [
    { code: 'en-ZA', name: 'English', flag: '🇿🇦', nativeName: 'English' },
    { code: 'af-ZA', name: 'Afrikaans', flag: '🇿🇦', nativeName: 'Afrikaans' }
  ] as const

  return {
    currentLocale,
    switchLanguage,
    initializeLocale,
    availableLanguages
  }
} 