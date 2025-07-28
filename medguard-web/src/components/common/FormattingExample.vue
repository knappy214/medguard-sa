<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t, n, d, locale } = useI18n()

// Example data
const medicationPrice = 125.50
const medicationQuantity = 30
const refillDate = new Date('2024-03-15')
const lastTaken = new Date()
</script>

<template>
  <div class="card bg-base-100 shadow-lg">
    <div class="card-body">
      <h3 class="card-title text-lg font-semibold">
        {{ $t('medication.name') }} - {{ $t('common.details') }}
      </h3>
      
      <div class="space-y-4">
        <!-- Price formatting -->
        <div class="flex justify-between items-center">
          <span class="text-base-content-secondary">{{ $t('medication.name') }} {{ $t('common.details') }}:</span>
          <span class="font-medium">{{ n(medicationPrice, 'currency') }}</span>
        </div>

        <!-- Quantity formatting -->
        <div class="flex justify-between items-center">
          <span class="text-base-content-secondary">{{ $t('medication.quantity') }}:</span>
          <span class="font-medium">{{ n(medicationQuantity, 'decimal') }} {{ $t('strengths.tablets') }}</span>
        </div>

        <!-- Date formatting -->
        <div class="flex justify-between items-center">
          <span class="text-base-content-secondary">{{ $t('medication.refillDate') }}:</span>
          <span class="font-medium">{{ d(refillDate, 'short') }}</span>
        </div>

        <div class="flex justify-between items-center">
          <span class="text-base-content-secondary">{{ $t('medication.lastTaken') }}:</span>
          <span class="font-medium">{{ d(lastTaken, 'time') }}</span>
        </div>

        <!-- Long date format -->
        <div class="flex justify-between items-center">
          <span class="text-base-content-secondary">{{ $t('schedule.startDate') }}:</span>
          <span class="font-medium">{{ d(refillDate, 'long') }}</span>
        </div>
      </div>

      <!-- Language indicator -->
      <div class="mt-4 pt-4 border-t border-base-300">
        <p class="text-sm text-base-content-secondary">
          {{ $t('common.details') }}: {{ locale === 'en-ZA' ? 'English (South Africa)' : 'Afrikaans (Suid-Afrika)' }}
        </p>
      </div>
    </div>
  </div>
</template> 