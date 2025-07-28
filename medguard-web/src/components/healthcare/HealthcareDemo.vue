<template>
  <div class="min-h-screen bg-base-200 p-6">
    <div class="max-w-7xl mx-auto space-y-8">
      <!-- Header -->
      <div class="text-center space-y-4">
        <h1 class="text-4xl font-bold text-base-content">MedGuard SA</h1>
        <p class="text-xl text-base-content-secondary">Healthcare Management System</p>
        <div class="badge badge-primary badge-lg">Healthcare Theme Demo</div>
      </div>

      <!-- Color Palette Showcase -->
      <HealthcareCard title="Healthcare Color Palette" icon="🎨" status="Design System">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-primary rounded-lg mx-auto flex items-center justify-center text-primary-content font-bold">P</div>
            <p class="text-sm font-medium">Primary</p>
            <p class="text-xs text-base-content-secondary">#2563EB</p>
          </div>
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-secondary rounded-lg mx-auto flex items-center justify-center text-secondary-content font-bold">S</div>
            <p class="text-sm font-medium">Secondary</p>
            <p class="text-xs text-base-content-secondary">#10B981</p>
          </div>
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-accent rounded-lg mx-auto flex items-center justify-center text-accent-content font-bold">A</div>
            <p class="text-sm font-medium">Accent</p>
            <p class="text-xs text-base-content-secondary">#D9488F</p>
          </div>
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-neutral rounded-lg mx-auto flex items-center justify-center text-neutral-content font-bold">N</div>
            <p class="text-sm font-medium">Neutral</p>
            <p class="text-xs text-base-content-secondary">#6B7280</p>
          </div>
        </div>
      </HealthcareCard>

      <!-- Status Colors -->
      <HealthcareCard title="Status Colors" icon="🔔" status="System Alerts">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-success rounded-lg mx-auto flex items-center justify-center text-success-content font-bold">✓</div>
            <p class="text-sm font-medium">Success</p>
            <p class="text-xs text-base-content-secondary">Medication taken</p>
          </div>
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-warning rounded-lg mx-auto flex items-center justify-center text-warning-content font-bold">⚠</div>
            <p class="text-sm font-medium">Warning</p>
            <p class="text-xs text-base-content-secondary">Low stock alert</p>
          </div>
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-error rounded-lg mx-auto flex items-center justify-center text-error-content font-bold">✗</div>
            <p class="text-sm font-medium">Error</p>
            <p class="text-xs text-base-content-secondary">Missed dose</p>
          </div>
          <div class="text-center space-y-2">
            <div class="w-16 h-16 bg-info rounded-lg mx-auto flex items-center justify-center text-info-content font-bold">ℹ</div>
            <p class="text-sm font-medium">Info</p>
            <p class="text-xs text-base-content-secondary">General info</p>
          </div>
        </div>
      </HealthcareCard>

      <!-- Button Showcase -->
      <HealthcareCard title="Healthcare Buttons" icon="🔘" status="Interactive Elements">
        <div class="space-y-4">
          <div class="flex flex-wrap gap-2">
            <HealthcareButton variant="primary" icon="💊">Primary Action</HealthcareButton>
            <HealthcareButton variant="secondary" icon="🏥">Secondary Action</HealthcareButton>
            <HealthcareButton variant="success" icon="✓">Success Action</HealthcareButton>
            <HealthcareButton variant="warning" icon="⚠">Warning Action</HealthcareButton>
            <HealthcareButton variant="error" icon="✗">Error Action</HealthcareButton>
          </div>
          
          <div class="flex flex-wrap gap-2">
            <HealthcareButton variant="primary" size="sm">Small</HealthcareButton>
            <HealthcareButton variant="primary" size="md">Medium</HealthcareButton>
            <HealthcareButton variant="primary" size="lg">Large</HealthcareButton>
          </div>
          
          <div class="flex flex-wrap gap-2">
            <HealthcareButton variant="primary" :loading="true">Loading</HealthcareButton>
            <HealthcareButton variant="primary" disabled>Disabled</HealthcareButton>
            <HealthcareButton variant="ghost">Ghost</HealthcareButton>
            <HealthcareButton variant="outline">Outline</HealthcareButton>
          </div>
        </div>
      </HealthcareCard>

      <!-- Form Inputs -->
      <HealthcareCard title="Healthcare Form Inputs" icon="📝" status="Data Entry">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <HealthcareInput
            v-model="formData.patientName"
            label="Patient Name"
            placeholder="Enter patient name"
            icon="👤"
            required
          />
          
          <HealthcareInput
            v-model="formData.medication"
            label="Medication"
            placeholder="Enter medication name"
            icon="💊"
            required
          />
          
          <HealthcareInput
            v-model="formData.dosage"
            label="Dosage"
            type="number"
            placeholder="Enter dosage"
            icon="⚖️"
            min="0"
            step="0.1"
          />
          
          <HealthcareInput
            v-model="formData.schedule"
            label="Schedule"
            type="time"
            icon="⏰"
          />
          
          <HealthcareInput
            v-model="formData.email"
            label="Email"
            type="email"
            placeholder="patient@example.com"
            icon="📧"
            :errorMessage="emailError"
          />
          
          <HealthcareInput
            v-model="formData.phone"
            label="Phone"
            type="tel"
            placeholder="+27 12 345 6789"
            icon="📞"
          />
        </div>
      </HealthcareCard>

      <!-- Alert Messages -->
      <HealthcareCard title="Alert Messages" icon="📢" status="Notifications">
        <div class="space-y-4">
          <div class="alert alert-success">
            <span>✅ Medication successfully administered to Patient #12345</span>
          </div>
          
          <div class="alert alert-warning">
            <span>⚠️ Low stock alert: Paracetamol 500mg - Only 15 tablets remaining</span>
          </div>
          
          <div class="alert alert-error">
            <span>❌ Missed dose alert: Patient #12345 missed their 2:00 PM medication</span>
          </div>
          
          <div class="alert alert-info">
            <span>ℹ️ New patient registration: John Doe added to the system</span>
          </div>
        </div>
      </HealthcareCard>

      <!-- Data Tables -->
      <HealthcareCard title="Patient Records" icon="📋" status="Active">
        <div class="overflow-x-auto">
          <table class="table table-zebra">
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Name</th>
                <th>Medication</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>#12345</td>
                <td>John Doe</td>
                <td>Paracetamol 500mg</td>
                <td><span class="badge badge-success">Active</span></td>
                <td>
                  <HealthcareButton variant="primary" size="sm">View</HealthcareButton>
                </td>
              </tr>
              <tr>
                <td>#12346</td>
                <td>Jane Smith</td>
                <td>Ibuprofen 400mg</td>
                <td><span class="badge badge-warning">Pending</span></td>
                <td>
                  <HealthcareButton variant="secondary" size="sm">Edit</HealthcareButton>
                </td>
              </tr>
              <tr>
                <td>#12347</td>
                <td>Bob Johnson</td>
                <td>Aspirin 100mg</td>
                <td><span class="badge badge-error">Overdue</span></td>
                <td>
                  <HealthcareButton variant="error" size="sm">Alert</HealthcareButton>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </HealthcareCard>

      <!-- Accessibility Features -->
      <HealthcareCard title="Accessibility Features" icon="♿" status="WCAG 2.2 AA Compliant">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="space-y-4">
            <h4 class="font-semibold text-base-content">High Contrast Support</h4>
            <p class="text-sm text-base-content-secondary">
              All color combinations meet WCAG AA/AAA standards with high contrast ratios.
            </p>
            
            <h4 class="font-semibold text-base-content">Keyboard Navigation</h4>
            <p class="text-sm text-base-content-secondary">
              All interactive elements are fully accessible via keyboard navigation.
            </p>
            
            <h4 class="font-semibold text-base-content">Screen Reader Support</h4>
            <p class="text-sm text-base-content-secondary">
              Proper ARIA labels and semantic HTML structure for screen readers.
            </p>
          </div>
          
          <div class="space-y-4">
            <h4 class="font-semibold text-base-content">Reduced Motion</h4>
            <p class="text-sm text-base-content-secondary">
              Respects user preferences for reduced motion and animations.
            </p>
            
            <h4 class="font-semibold text-base-content">Focus Indicators</h4>
            <p class="text-sm text-base-content-secondary">
              Clear focus indicators for all interactive elements.
            </p>
            
            <h4 class="font-semibold text-base-content">Print Optimization</h4>
            <p class="text-sm text-base-content-secondary">
              Optimized styles for printing medical records and reports.
            </p>
          </div>
        </div>
      </HealthcareCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import HealthcareCard from './HealthcareCard.vue'
import HealthcareButton from './HealthcareButton.vue'
import HealthcareInput from './HealthcareInput.vue'

const formData = ref({
  patientName: '',
  medication: '',
  dosage: '',
  schedule: '',
  email: '',
  phone: ''
})

const emailError = computed(() => {
  if (formData.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.value.email)) {
    return 'Please enter a valid email address'
  }
  return ''
})
</script>

<style scoped>
/* Additional demo-specific styles */
.alert {
  @apply shadow-sm;
}

.table th {
  @apply font-semibold text-base-content;
}

.table td {
  @apply text-base-content-secondary;
}

/* Smooth transitions for demo interactions */
* {
  transition: all 0.2s ease-in-out;
}
</style> 