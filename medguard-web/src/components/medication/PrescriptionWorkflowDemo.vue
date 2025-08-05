<template>
  <div class="prescription-workflow-demo">
    <!-- Header -->
    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body">
        <h1 class="card-title text-3xl font-bold">
          <i class="fas fa-flask text-primary mr-2"></i>
          {{ $t('demo.title', 'Prescription Workflow Demo') }}
        </h1>
        <p class="text-base-content/70 text-lg">
          {{ $t('demo.description', 'Experience the complete prescription processing workflow with automated OCR, validation, and medication scheduling.') }}
        </p>
      </div>
    </div>

    <!-- Features Overview -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <div class="card bg-base-100 shadow-xl">
        <div class="card-body text-center">
          <i class="fas fa-camera text-4xl text-primary mb-4"></i>
          <h3 class="card-title justify-center">{{ $t('demo.features.capture.title', 'Image Capture') }}</h3>
          <p class="text-base-content/70">
            {{ $t('demo.features.capture.description', 'Capture prescription images using camera or upload from device') }}
          </p>
        </div>
      </div>

      <div class="card bg-base-100 shadow-xl">
        <div class="card-body text-center">
          <i class="fas fa-search text-4xl text-primary mb-4"></i>
          <h3 class="card-title justify-center">{{ $t('demo.features.ocr.title', 'OCR Processing') }}</h3>
          <p class="text-base-content/70">
            {{ $t('demo.features.ocr.description', 'Automated text extraction with progress tracking') }}
          </p>
        </div>
      </div>

      <div class="card bg-base-100 shadow-xl">
        <div class="card-body text-center">
          <i class="fas fa-check-circle text-4xl text-primary mb-4"></i>
          <h3 class="card-title justify-center">{{ $t('demo.features.validation.title', 'Validation') }}</h3>
          <p class="text-base-content/70">
            {{ $t('demo.features.validation.description', 'Validate medications against drug database') }}
          </p>
        </div>
      </div>

      <div class="card bg-base-100 shadow-xl">
        <div class="card-body text-center">
          <i class="fas fa-calendar-alt text-4xl text-primary mb-4"></i>
          <h3 class="card-title justify-center">{{ $t('demo.features.scheduling.title', 'Scheduling') }}</h3>
          <p class="text-base-content/70">
            {{ $t('demo.features.scheduling.description', 'Create medication schedules and reminders') }}
          </p>
        </div>
      </div>

      <div class="card bg-base-100 shadow-xl">
        <div class="card-body text-center">
          <i class="fas fa-boxes text-4xl text-primary mb-4"></i>
          <h3 class="card-title justify-center">{{ $t('demo.features.stock.title', 'Stock Management') }}</h3>
          <p class="text-base-content/70">
            {{ $t('demo.features.stock.description', 'Set stock levels and auto-refill alerts') }}
          </p>
        </div>
      </div>

      <div class="card bg-base-100 shadow-xl">
        <div class="card-body text-center">
          <i class="fas fa-save text-4xl text-primary mb-4"></i>
          <h3 class="card-title justify-center">{{ $t('demo.features.save.title', 'Progress Saving') }}</h3>
          <p class="text-base-content/70">
            {{ $t('demo.features.save.description', 'Save progress and resume later') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Workflow Component -->
    <div class="card bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-2xl font-bold mb-4">
          <i class="fas fa-play text-primary mr-2"></i>
          {{ $t('demo.workflow.title', 'Try the Workflow') }}
        </h2>
        
        <PrescriptionWorkflow />
      </div>
    </div>

    <!-- Usage Instructions -->
    <div class="card bg-base-100 shadow-xl mt-8">
      <div class="card-body">
        <h2 class="card-title text-2xl font-bold mb-4">
          <i class="fas fa-info-circle text-primary mr-2"></i>
          {{ $t('demo.instructions.title', 'How to Use') }}
        </h2>
        
        <div class="space-y-4">
          <div class="flex items-start gap-4">
            <div class="badge badge-primary badge-lg">1</div>
            <div>
              <h3 class="font-semibold">{{ $t('demo.instructions.step1.title', 'Capture Image') }}</h3>
              <p class="text-base-content/70">
                {{ $t('demo.instructions.step1.description', 'Use your device camera or upload a prescription image. Supported formats: JPG, PNG, PDF.') }}
              </p>
            </div>
          </div>

          <div class="flex items-start gap-4">
            <div class="badge badge-primary badge-lg">2</div>
            <div>
              <h3 class="font-semibold">{{ $t('demo.instructions.step2.title', 'OCR Processing') }}</h3>
              <p class="text-base-content/70">
                {{ $t('demo.instructions.step2.description', 'The system will automatically extract text and medication information from your prescription image.') }}
              </p>
            </div>
          </div>

          <div class="flex items-start gap-4">
            <div class="badge badge-primary badge-lg">3</div>
            <div>
              <h3 class="font-semibold">{{ $t('demo.instructions.step3.title', 'Review & Edit') }}</h3>
              <p class="text-base-content/70">
                {{ $t('demo.instructions.step3.description', 'Review the extracted medications and edit any information as needed. Add or remove medications.') }}
              </p>
            </div>
          </div>

          <div class="flex items-start gap-4">
            <div class="badge badge-primary badge-lg">4</div>
            <div>
              <h3 class="font-semibold">{{ $t('demo.instructions.step4.title', 'Validate') }}</h3>
              <p class="text-base-content/70">
                {{ $t('demo.instructions.step4.description', 'Each medication is validated against the drug database for accuracy and potential interactions.') }}
              </p>
            </div>
          </div>

          <div class="flex items-start gap-4">
            <div class="badge badge-primary badge-lg">5</div>
            <div>
              <h3 class="font-semibold">{{ $t('demo.instructions.step5.title', 'Create Schedules') }}</h3>
              <p class="text-base-content/70">
                {{ $t('demo.instructions.step5.description', 'Set up medication schedules with timing, dosage, and duration for each medication.') }}
              </p>
            </div>
          </div>

          <div class="flex items-start gap-4">
            <div class="badge badge-primary badge-lg">6</div>
            <div>
              <h3 class="font-semibold">{{ $t('demo.instructions.step6.title', 'Stock & Reminders') }}</h3>
              <p class="text-base-content/70">
                {{ $t('demo.instructions.step6.description', 'Configure stock levels, auto-refill settings, and notification preferences.') }}
              </p>
            </div>
          </div>

          <div class="flex items-start gap-4">
            <div class="badge badge-primary badge-lg">7</div>
            <div>
              <h3 class="font-semibold">{{ $t('demo.instructions.step7.title', 'Save & Complete') }}</h3>
              <p class="text-base-content/70">
                {{ $t('demo.instructions.step7.description', 'Review the summary and save your prescription. You can also save progress to continue later.') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tips and Best Practices -->
    <div class="card bg-base-100 shadow-xl mt-8">
      <div class="card-body">
        <h2 class="card-title text-2xl font-bold mb-4">
          <i class="fas fa-lightbulb text-primary mr-2"></i>
          {{ $t('demo.tips.title', 'Tips & Best Practices') }}
        </h2>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-3">
            <h3 class="font-semibold text-lg">{{ $t('demo.tips.image.title', 'Image Quality') }}</h3>
            <ul class="list-disc list-inside space-y-1 text-base-content/70">
              <li>{{ $t('demo.tips.image.goodLighting', 'Ensure good lighting when capturing images') }}</li>
              <li>{{ $t('demo.tips.image.steady', 'Keep the camera steady and avoid blur') }}</li>
              <li>{{ $t('demo.tips.image.angle', 'Capture from a straight angle for best results') }}</li>
              <li>{{ $t('demo.tips.image.resolution', 'Use high-resolution images when possible') }}</li>
            </ul>
          </div>

          <div class="space-y-3">
            <h3 class="font-semibold text-lg">{{ $t('demo.tips.workflow.title', 'Workflow Tips') }}</h3>
            <ul class="list-disc list-inside space-y-1 text-base-content/70">
              <li>{{ $t('demo.tips.workflow.save', 'Save your progress regularly for complex prescriptions') }}</li>
              <li>{{ $t('demo.tips.workflow.review', 'Always review extracted information before proceeding') }}</li>
              <li>{{ $t('demo.tips.workflow.validate', 'Pay attention to validation warnings and errors') }}</li>
              <li>{{ $t('demo.tips.workflow.schedule', 'Set realistic schedules that match your daily routine') }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import PrescriptionWorkflow from './PrescriptionWorkflow.vue'

const { t } = useI18n()
</script>

<style scoped>
.prescription-workflow-demo {
  @apply max-w-7xl mx-auto p-6;
}
</style> 