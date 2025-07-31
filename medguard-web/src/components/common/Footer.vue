<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import Logo from './Logo.vue'

const { t } = useI18n()
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="bg-base-200 border-t border-base-300 mt-auto">
    <div class="container mx-auto px-4 py-8">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 items-center">
        <!-- Logo and Brand -->
        <div class="flex flex-col items-center md:items-start">
          <Logo size="lg" />
          <p class="text-base-content/70 text-sm mt-2 text-center md:text-left">
            {{ t('footer.tagline') }}
          </p>
        </div>
        
        <!-- Quick Links -->
        <div class="flex flex-col items-center">
          <h3 class="font-semibold text-base-content mb-4">{{ t('footer.quickLinks') }}</h3>
          <div class="flex flex-col space-y-2 text-sm">
            <a href="#" class="text-base-content/70 hover:text-primary transition-colors">
              {{ t('footer.dashboard') }}
            </a>
            <a href="#" class="text-base-content/70 hover:text-primary transition-colors">
              {{ t('footer.medications') }}
            </a>
            <a href="#" class="text-base-content/70 hover:text-primary transition-colors">
              {{ t('footer.settings') }}
            </a>
          </div>
        </div>
        
        <!-- Contact Info -->
        <div class="flex flex-col items-center md:items-end">
          <h3 class="font-semibold text-base-content mb-4">{{ t('footer.contact') }}</h3>
          <div class="text-sm text-base-content/70 text-center md:text-right">
            <p>{{ t('footer.companyName') }}</p>
            <p>{{ t('footer.companyDescription') }}</p>
            <p class="mt-2">{{ t('footer.copyright', { year: currentYear }) }}</p>
          </div>
        </div>
      </div>
      
      <!-- Bottom Bar -->
      <div class="border-t border-base-300 mt-8 pt-4 text-center">
        <p class="text-xs text-base-content/50">
          {{ t('footer.builtWith') }}
        </p>
      </div>
    </div>
  </footer>
</template> 