# MedGuard SA Healthcare Theme

A comprehensive healthcare-themed design system built with Vue 3, Tailwind CSS v4, and DaisyUI 5, specifically designed for medical applications.

## 🎨 Color Palette

### Primary Colors
- **Primary Blue**: `#2563EB` - Trust, professionalism, calm
- **Secondary Green**: `#10B981` - Health, healing, nature
- **Accent Pink**: `#D9488F` - Balance, clarity
- **Neutral Gray**: `#6B7280` - Modern, accessible text

### Status Colors
- **Success Green**: `#22C55E` - Medication taken successfully
- **Warning Orange**: `#F59E0B` - Low stock alerts
- **Error Red**: `#EF4444` - Missed doses, critical alerts
- **Info Blue**: `#3B82F6` - General information

### Background Colors
- **Base White**: `#FFFFFF` - Cleanliness, medical sterility
- **Light Gray**: `#F9FAFB` - Subtle backgrounds
- **Border Gray**: `#F3F4F6` - Subtle borders

## 🏗️ Architecture

### File Structure
```
src/
├── components/
│   └── healthcare/
│       ├── HealthcareCard.vue      # Reusable card component
│       ├── HealthcareButton.vue    # Healthcare-themed buttons
│       ├── HealthcareInput.vue     # Form inputs with validation
│       └── HealthcareDemo.vue      # Theme showcase
├── types/
│   └── healthcare.ts              # TypeScript definitions
└── style.css                      # Main theme configuration
```

### Technology Stack
- **Vue 3** with Composition API
- **TypeScript** for type safety
- **Tailwind CSS v4** with CSS-first approach
- **DaisyUI 5** for component library
- **Inter Font** for healthcare aesthetics

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Development
```bash
# Type checking
npm run type-check

# Format code
npm run format
```

## 🧩 Components

### HealthcareCard
A flexible card component with healthcare styling.

```vue
<HealthcareCard 
  title="Patient Information" 
  subtitle="Medical Records"
  icon="🏥"
  status="Active"
  statusType="success"
>
  <p>Card content goes here</p>
  
  <template #actions>
    <HealthcareButton variant="primary">View Details</HealthcareButton>
  </template>
</HealthcareCard>
```

**Props:**
- `title` (string, required): Card title
- `subtitle` (string, optional): Card subtitle
- `icon` (string, optional): Emoji or icon
- `status` (string, optional): Status badge text
- `statusType` (string, optional): Status type for badge styling

### HealthcareButton
Healthcare-themed button with multiple variants and states.

```vue
<HealthcareButton 
  variant="primary"
  size="md"
  :loading="isLoading"
  icon="💊"
  @click="handleClick"
>
  Administer Medication
</HealthcareButton>
```

**Props:**
- `variant`: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'ghost' | 'outline'
- `size`: 'xs' | 'sm' | 'md' | 'lg'
- `disabled`: boolean
- `loading`: boolean
- `icon`: string
- `type`: 'button' | 'submit' | 'reset'

### HealthcareInput
Form input with validation and healthcare styling.

```vue
<HealthcareInput
  v-model="patientName"
  label="Patient Name"
  placeholder="Enter patient name"
  icon="👤"
  required
  :errorMessage="nameError"
  helpText="Enter the patient's full name"
/>
```

**Props:**
- `modelValue`: string | number
- `label`: string
- `placeholder`: string
- `type`: input type
- `disabled`: boolean
- `required`: boolean
- `icon`: string
- `helpText`: string
- `errorMessage`: string

## 🎯 Usage Examples

### Patient Management Form
```vue
<template>
  <HealthcareCard title="Patient Registration" icon="📋">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <HealthcareInput
        v-model="form.patientName"
        label="Full Name"
        placeholder="Enter patient's full name"
        icon="👤"
        required
      />
      
      <HealthcareInput
        v-model="form.medicalRecordNumber"
        label="Medical Record Number"
        placeholder="MRN-12345"
        icon="🏥"
        required
      />
      
      <HealthcareInput
        v-model="form.email"
        label="Email"
        type="email"
        placeholder="patient@example.com"
        icon="📧"
      />
      
      <HealthcareInput
        v-model="form.phone"
        label="Phone"
        type="tel"
        placeholder="+27 12 345 6789"
        icon="📞"
      />
    </div>
    
    <template #actions>
      <HealthcareButton variant="secondary" @click="resetForm">
        Cancel
      </HealthcareButton>
      <HealthcareButton 
        variant="primary" 
        :loading="isSubmitting"
        @click="submitForm"
      >
        Register Patient
      </HealthcareButton>
    </template>
  </HealthcareCard>
</template>
```

### Medication Alert System
```vue
<template>
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
  </div>
</template>
```

## ♿ Accessibility Features

### WCAG 2.2 AA Compliance
- **High Contrast**: All color combinations meet AA/AAA standards
- **Keyboard Navigation**: Full keyboard accessibility
- **Screen Reader Support**: Proper ARIA labels and semantic HTML
- **Focus Indicators**: Clear focus states for all interactive elements
- **Reduced Motion**: Respects user motion preferences
- **Print Optimization**: Optimized styles for medical record printing

### Accessibility Classes
```css
/* High contrast mode support */
@media (prefers-contrast: high) {
  .btn { @apply border-2; }
  .card { @apply border-2 border-base-content; }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 🎨 Customization

### Theme Variables
All colors are defined as CSS custom properties in `src/style.css`:

```css
@theme {
  --color-primary: 37 99 235;      /* #2563EB */
  --color-secondary: 16 185 129;   /* #10B981 */
  --color-accent: 217 72 136;      /* #D9488F */
  --color-success: 34 197 94;      /* #22C55E */
  --color-warning: 245 158 11;     /* #F59E0B */
  --color-error: 239 68 68;        /* #EF4444 */
  --color-info: 59 130 246;        /* #3B82F6 */
}
```

### Custom Components
Create custom healthcare components by extending the base classes:

```vue
<template>
  <div class="healthcare-card custom-medication-card">
    <!-- Custom content -->
  </div>
</template>

<style scoped>
.custom-medication-card {
  @apply border-l-4 border-l-primary;
}
</style>
```

## 📱 Responsive Design

The theme is fully responsive with mobile-first design:

```css
/* Mobile-first breakpoints */
.grid-cols-1 md:grid-cols-2 lg:grid-cols-3
```

### Breakpoints
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

## 🔧 Development Guidelines

### Component Structure
1. Use Composition API with `<script setup>`
2. Include TypeScript interfaces for props
3. Implement proper accessibility attributes
4. Add comprehensive error handling
5. Include loading states where appropriate

### Styling Guidelines
1. Use Tailwind utility classes
2. Leverage DaisyUI components
3. Follow healthcare color semantics
4. Ensure WCAG compliance
5. Test with screen readers

### TypeScript Usage
```typescript
import type { Patient, Medication, HealthcareFormData } from '@/types/healthcare'

// Use typed interfaces for better development experience
const patient: Patient = {
  id: '12345',
  name: 'John Doe',
  medicalRecordNumber: 'MRN-12345',
  status: 'active',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString()
}
```

## 🧪 Testing

### Component Testing
```bash
# Run tests
npm run test

# Run tests with coverage
npm run test:coverage
```

### Accessibility Testing
- Use axe-core for automated testing
- Test with screen readers (NVDA, JAWS, VoiceOver)
- Verify keyboard navigation
- Check color contrast ratios

## 📚 Resources

- [DaisyUI Documentation](https://daisyui.com/)
- [Tailwind CSS v4 Documentation](https://tailwindcss.com/)
- [Vue 3 Documentation](https://vuejs.org/)
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [Healthcare Design Patterns](https://www.nngroup.com/articles/healthcare-ux/)

## 🤝 Contributing

1. Follow the established component patterns
2. Ensure accessibility compliance
3. Add TypeScript types for new components
4. Update documentation
5. Test across different devices and browsers

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 