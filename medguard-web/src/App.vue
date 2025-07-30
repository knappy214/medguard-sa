<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useThemeStore } from '@/stores/theme'
import MedicationDashboard from './components/medication/MedicationDashboard.vue'
import LanguageSwitcher from './components/common/LanguageSwitcher.vue'
import ThemeToggle from './components/common/ThemeToggle.vue'
import Logo from './components/common/Logo.vue'
import Footer from './components/common/Footer.vue'

const { t } = useI18n()
const themeStore = useThemeStore()

// Initialize theme on app mount
onMounted(() => {
  themeStore.initializeTheme()
})
</script>

<template>
  <div class="app min-h-screen bg-base-100 flex flex-col">
    <!-- Header with Logo, Language Switcher and Theme Toggle -->
    <header class="bg-base-100 border-b border-base-300 shadow-sm sticky top-0 z-50">
      <div class="container mx-auto px-4 py-4">
        <div class="flex justify-between items-center">
          <div class="flex items-center space-x-4">
            <Logo size="lg" :show-text="false" />
            <div>
              <h1 class="text-2xl font-bold text-base-content">
                {{ t('dashboard.title') }}
              </h1>
              <p class="text-base-content/70 text-sm">
                {{ t('dashboard.subtitle') }}
              </p>
            </div>
          </div>
          
          <!-- Right side controls -->
          <div class="flex items-center space-x-3">
            <LanguageSwitcher />
            <ThemeToggle />
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="container mx-auto px-4 py-8 flex-1">
      <MedicationDashboard />
    </main>

    <!-- Footer -->
    <Footer />
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
}

/* Ensure smooth transitions for theme changes */
* {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
</style>
