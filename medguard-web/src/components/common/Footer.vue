<script setup lang="ts">
import Logo from './Logo.vue'

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
            Professional Healthcare Management System
          </p>
        </div>
        
        <!-- Quick Links -->
        <div class="flex flex-col items-center">
          <h3 class="font-semibold text-base-content mb-4">Quick Links</h3>
          <div class="flex flex-col space-y-2 text-sm">
            <a href="#" class="text-base-content/70 hover:text-primary transition-colors">
              Dashboard
            </a>
            <a href="#" class="text-base-content/70 hover:text-primary transition-colors">
              Medications
            </a>
            <a href="#" class="text-base-content/70 hover:text-primary transition-colors">
              Settings
            </a>
          </div>
        </div>
        
        <!-- Contact Info -->
        <div class="flex flex-col items-center md:items-end">
          <h3 class="font-semibold text-base-content mb-4">Contact</h3>
          <div class="text-sm text-base-content/70 text-center md:text-right">
            <p>MedGuard SA</p>
            <p>Professional Healthcare Solutions</p>
            <p class="mt-2">© {{ currentYear }} All rights reserved</p>
          </div>
        </div>
      </div>
      
      <!-- Bottom Bar -->
      <div class="border-t border-base-300 mt-8 pt-4 text-center">
        <p class="text-xs text-base-content/50">
          Built with ❤️ for South African Healthcare
        </p>
      </div>
    </div>
  </footer>
</template> 