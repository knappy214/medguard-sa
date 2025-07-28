<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import MedicationDashboard from './components/medication/MedicationDashboard.vue'
import LanguageSwitcher from './components/common/LanguageSwitcher.vue'

const { locale } = useI18n()
const currentLocale = ref('en-ZA')

const switchLanguage = (newLocale: 'en-ZA' | 'af-ZA') => {
  currentLocale.value = newLocale
  locale.value = newLocale
  localStorage.setItem('medguard-locale', newLocale)
}

onMounted(() => {
  const savedLocale = localStorage.getItem('medguard-locale')
  if (savedLocale && (savedLocale === 'en-ZA' || savedLocale === 'af-ZA')) {
    switchLanguage(savedLocale as 'en-ZA' | 'af-ZA')
  }
})
</script>

<template>
  <div class="app">
    <!-- Header with Language Switcher -->
    <header class="bg-base-100 border-b border-base-300 shadow-sm">
      <div class="container mx-auto px-4 py-4">
        <div class="flex justify-between items-center">
          <div class="flex items-center space-x-4">
            <div class="text-2xl">💊</div>
            <div>
              <h1 class="text-2xl font-bold text-base-content">
                {{ $t('dashboard.title') }}
              </h1>
              <p class="text-base-content-secondary text-sm">
                {{ $t('dashboard.subtitle') }}
              </p>
            </div>
          </div>
          <LanguageSwitcher 
            :current-locale="currentLocale"
            @switch-language="switchLanguage"
          />
        </div>
      </div>
    </header>

    <!-- Main Dashboard -->
    <main class="container mx-auto px-4 py-8">
      <MedicationDashboard />
    </main>
  </div>
</template>

<style>
/* Global app styles */
.app {
  min-height: 100vh;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background-color: hsl(var(--color-base-200));
}

/* Ensure proper color inheritance */
* {
  box-sizing: border-box;
}

/* Smooth scrolling */
html {
  scroll-behavior: smooth;
}

/* Better focus management */
:focus-visible {
  outline: 2px solid hsl(var(--color-primary));
  outline-offset: 2px;
}

/* Print styles */
@media print {
  .no-print {
    display: none !important;
  }
}

/* Responsive container */
.container {
  max-width: 1200px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .container {
    padding-left: 1rem;
    padding-right: 1rem;
  }
}
</style>
