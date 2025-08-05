# PrescriptionWorkflow Component

A comprehensive 7-step prescription processing workflow that handles the entire process from image capture to medication scheduling with automated OCR, validation, and progress saving capabilities.

## Features

### 🎯 Core Workflow Steps

1. **Image Capture** - Camera capture or file upload
2. **OCR Processing** - Automated text extraction with progress tracking
3. **Review & Edit** - Review and edit extracted medications
4. **Validation** - Validate medications against drug database
5. **Scheduling** - Create medication schedules
6. **Stock Management** - Set stock levels and reminders
7. **Save & Complete** - Confirm and save all medications

### 🔧 Advanced Features

- **Progress Saving** - Save and resume workflow progress
- **Error Handling** - Comprehensive error handling with rollback capabilities
- **Multi-language Support** - Full i18n support (English & Afrikaans)
- **Camera Integration** - Direct camera access for image capture
- **Drag & Drop** - File upload with drag and drop support
- **Validation** - Real-time medication validation against drug database
- **Responsive Design** - Mobile-first responsive design with DaisyUI

## Usage

### Basic Usage

```vue
<template>
  <PrescriptionWorkflow />
</template>

<script setup>
import PrescriptionWorkflow from '@/components/medication/PrescriptionWorkflow.vue'
</script>
```

### Demo Component

For a complete demo with instructions and tips:

```vue
<template>
  <PrescriptionWorkflowDemo />
</template>

<script setup>
import PrescriptionWorkflowDemo from '@/components/medication/PrescriptionWorkflowDemo.vue'
</script>
```

## Component Structure

### Template Structure

```vue
<template>
  <div class="prescription-workflow">
    <!-- Header with title and description -->
    <!-- Progress indicator with 7 steps -->
    <!-- Step content container -->
    <!-- Error and success modals -->
  </div>
</template>
```

### Script Structure

```typescript
// Imports
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import medicationApi from '@/services/medicationApi'

// Interfaces
interface WorkflowStep {
  title: string
  description: string
  icon: string
}

interface MedicationSchedule {
  timing: 'morning' | 'noon' | 'night' | 'custom'
  customTime: string
  dosageAmount: number
  instructions: string
  startDate: string
  duration: number
}

// Reactive state
const currentStep = ref(0)
const state = reactive<WorkflowState>({...})

// Methods
const nextStep = async () => {...}
const previousStep = () => {...}
const processOCR = async () => {...}
const validateMedications = async () => {...}
const saveProgress = async () => {...}
const completeWorkflow = async () => {...}
```

## API Integration

### Required Services

The component integrates with the following services:

- `medicationApi.validateMedication()` - Validate medications
- `medicationApi.createMedication()` - Create medication entries
- `medicationApi.createMedicationSchedules()` - Create schedules

### Data Flow

1. **Image Upload** → Base64 string
2. **OCR Processing** → ParsedPrescription object
3. **Validation** → MedicationValidation objects
4. **Scheduling** → MedicationSchedule objects
5. **Save** → Medication objects in database

## State Management

### Reactive State

```typescript
// Workflow state
const currentStep = ref(0)
const state = reactive({
  isProcessing: boolean
  isValidating: boolean
  isSaving: boolean
  isLoading: boolean
})

// Step-specific data
const prescriptionImage = ref<string | null>(null)
const ocrResult = ref<ParsedPrescription | null>(null)
const extractedMedications = ref<PrescriptionMedication[]>([])
const medicationValidation = ref<Record<number, MedicationValidation>>({})
const medicationSchedules = ref<MedicationSchedule[]>([])
const stockSettings = ref<StockSettings[]>([])
```

### Progress Persistence

The component automatically saves progress to localStorage and can resume from any step:

```typescript
const saveProgress = async () => {
  const progressData = {
    currentStep: currentStep.value,
    prescriptionImage: prescriptionImage.value,
    ocrResult: ocrResult.value,
    // ... other state
    timestamp: new Date().toISOString()
  }
  localStorage.setItem('prescriptionWorkflowProgress', JSON.stringify(progressData))
}
```

## Error Handling

### Error Types

- **Camera Access Errors** - When camera permission is denied
- **OCR Processing Errors** - When text extraction fails
- **Validation Errors** - When medication validation fails
- **Save Errors** - When saving to database fails

### Error Recovery

```typescript
const showError = (message: string) => {
  currentError.value = message
  showErrorModal.value = true
}

const closeErrorModal = () => {
  showErrorModal.value = false
  currentError.value = ''
}
```

## Internationalization

### Translation Keys

The component uses the following translation structure:

```json
{
  "workflow": {
    "title": "Prescription Workflow",
    "description": "Process your prescription step by step...",
    "steps": {
      "capture": "Capture",
      "ocr": "OCR",
      "review": "Review",
      "validate": "Validate",
      "schedule": "Schedule",
      "stock": "Stock",
      "save": "Save"
    },
    "step1": { /* Step 1 translations */ },
    "step2": { /* Step 2 translations */ },
    // ... other steps
    "success": { /* Success messages */ },
    "errors": { /* Error messages */ }
  }
}
```

### Supported Languages

- **English** (`en.json`)
- **Afrikaans** (`af.json`)

## Styling

### CSS Classes

The component uses DaisyUI classes for styling:

```css
.prescription-workflow {
  @apply max-w-7xl mx-auto;
}

.upload-area {
  @apply border-2 border-dashed border-base-content/30 rounded-lg p-8 cursor-pointer transition-all duration-200;
}

.upload-area--dragover {
  @apply border-primary bg-primary/10;
}

.step-content {
  @apply space-y-6;
}
```

### Responsive Design

- **Mobile-first** approach
- **Grid layouts** that adapt to screen size
- **Flexible components** that work on all devices

## Browser Compatibility

### Required APIs

- **MediaDevices API** - For camera access
- **File API** - For file uploads
- **Canvas API** - For image processing
- **LocalStorage API** - For progress saving

### Browser Support

- **Chrome** 60+
- **Firefox** 55+
- **Safari** 11+
- **Edge** 79+

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading** - Components load only when needed
2. **Image Compression** - Automatic image compression before OCR
3. **Progress Caching** - Save progress to avoid data loss
4. **Error Boundaries** - Graceful error handling

### Memory Management

```typescript
onUnmounted(() => {
  stopCamera() // Clean up camera stream
})
```

## Testing

### Unit Tests

```typescript
// Test workflow progression
test('should advance to next step', () => {
  const wrapper = mount(PrescriptionWorkflow)
  wrapper.vm.nextStep()
  expect(wrapper.vm.currentStep).toBe(1)
})

// Test OCR processing
test('should process OCR successfully', async () => {
  const wrapper = mount(PrescriptionWorkflow)
  await wrapper.vm.processOCR()
  expect(wrapper.vm.ocrResult).toBeTruthy()
})
```

### Integration Tests

```typescript
// Test complete workflow
test('should complete full workflow', async () => {
  const wrapper = mount(PrescriptionWorkflow)
  // Simulate user interactions
  await wrapper.vm.completeWorkflow()
  expect(wrapper.emitted('completed')).toBeTruthy()
})
```

## Accessibility

### ARIA Labels

```vue
<button
  aria-label="Capture prescription image"
  @click="captureImage"
>
  <i class="fas fa-camera"></i>
</button>
```

### Keyboard Navigation

- **Tab** - Navigate between interactive elements
- **Enter/Space** - Activate buttons and controls
- **Arrow Keys** - Navigate between steps

### Screen Reader Support

- **Semantic HTML** - Proper heading structure
- **Alt Text** - Descriptive alt text for images
- **Status Messages** - Live regions for progress updates

## Security Considerations

### Data Protection

- **Local Storage** - Only stores non-sensitive progress data
- **Image Processing** - Images processed locally when possible
- **API Calls** - Secure API endpoints with authentication

### Privacy

- **Camera Access** - Explicit user permission required
- **File Upload** - User-initiated file selection only
- **Data Retention** - Progress data expires after 24 hours

## Future Enhancements

### Planned Features

1. **Batch Processing** - Process multiple prescriptions
2. **Advanced OCR** - Support for handwritten prescriptions
3. **AI Validation** - Machine learning-based validation
4. **Offline Support** - Work offline with sync when online
5. **Voice Commands** - Voice-activated workflow navigation

### API Extensions

```typescript
// Future API methods
interface PrescriptionWorkflowAPI {
  processBatch(prescriptions: File[]): Promise<BatchResult>
  validateWithAI(medication: Medication): Promise<AIValidation>
  syncOfflineData(): Promise<SyncResult>
}
```

## Troubleshooting

### Common Issues

1. **Camera Not Working**
   - Check browser permissions
   - Ensure HTTPS connection
   - Try different browser

2. **OCR Processing Fails**
   - Check image quality
   - Ensure good lighting
   - Try different image format

3. **Validation Errors**
   - Check medication names
   - Verify dosage information
   - Review drug database

### Debug Mode

Enable debug mode for detailed logging:

```typescript
const DEBUG = process.env.NODE_ENV === 'development'

if (DEBUG) {
  console.log('Workflow state:', {
    currentStep: currentStep.value,
    state,
    ocrResult: ocrResult.value
  })
}
```

## Contributing

### Development Setup

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Run Development Server**
   ```bash
   npm run dev
   ```

3. **Run Tests**
   ```bash
   npm run test
   ```

### Code Style

- **TypeScript** - Strict type checking
- **Vue 3 Composition API** - Modern Vue patterns
- **DaisyUI** - Consistent styling
- **ESLint** - Code quality enforcement

### Pull Request Process

1. **Fork** the repository
2. **Create** feature branch
3. **Implement** changes with tests
4. **Update** documentation
5. **Submit** pull request

## License

This component is part of the MedGuard SA project and follows the project's licensing terms. 