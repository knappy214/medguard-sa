<script setup lang="ts">
import HealthcareDemo from './components/healthcare/HealthcareDemo.vue'
</script>

<template>
  <div class="app">
    <HealthcareDemo />
  </div>
</template>

<style>
/* Global app styles */
.app {
  min-height: 100vh;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
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
</style>
