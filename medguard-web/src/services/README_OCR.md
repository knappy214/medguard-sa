# OCR Service for Prescription Processing

## Overview

The OCR (Optical Character Recognition) service provides comprehensive prescription processing capabilities for the MedGuard SA application. It integrates with Tesseract.js to extract medication information from prescription images and converts them into structured data.

## Features

### 🔍 **Core OCR Processing**
- **Tesseract.js Integration**: Client-side OCR processing using Tesseract.js
- **Image Preprocessing**: Advanced image enhancement for better text recognition
- **Multi-format Support**: Handles JPG, PNG, and other image formats
- **Batch Processing**: Process multiple prescription images simultaneously

### 🏥 **Prescription Data Extraction**
- **Medication Names**: Extract brand and generic medication names
- **Dosage Information**: Parse dosage amounts and frequency patterns
- **Instructions**: Extract medication instructions and special notes
- **Prescription Numbers**: Identify prescription reference numbers
- **Doctor Information**: Extract prescribing doctor names
- **ICD-10 Codes**: Detect and extract medical diagnosis codes

### 🧠 **Intelligent Processing**
- **Medication Mapping**: Map brand names to generic equivalents
- **Dosage Pattern Recognition**: Understand various dosage instructions
- **Confidence Scoring**: Provide accuracy metrics for extracted data
- **Validation**: Suggest manual entry for low-confidence extractions
- **Caching**: Cache processed results for improved performance

### 🎛️ **Image Enhancement**
- **Contrast Adjustment**: Optimize text contrast for better recognition
- **Brightness Control**: Adjust image brightness levels
- **Sharpening**: Apply sharpening filters for clearer text
- **Noise Reduction**: Remove image noise and artifacts
- **Threshold Processing**: Convert to binary for better OCR

## Architecture

### Service Structure

```
OCRService (Singleton)
├── TesseractWorker
├── MedicationDatabase
├── ImagePreprocessor
├── TextParser
├── ResultValidator
└── CacheManager
```

### Key Components

1. **OCRService**: Main service class implementing singleton pattern
2. **useOCR**: Vue composable for reactive OCR functionality
3. **OCRPrescriptionProcessor**: Vue component for user interface
4. **Image Preprocessing**: Canvas-based image enhancement
5. **Text Parser**: Regex-based prescription text analysis
6. **Medication Database**: Brand-to-generic name mapping

## Usage

### Basic Usage

```typescript
import { ocrService } from '@/services/ocrService'

// Initialize the service
await ocrService.initialize()

// Process a prescription image
const result = await ocrService.processPrescription(imageFile)

// Check results
if (result.success) {
  console.log('Medications found:', result.medications.length)
  console.log('Confidence:', result.confidence)
  console.log('Prescription number:', result.prescriptionNumber)
}
```

### Vue Composable Usage

```vue
<script setup>
import { useOCR } from '@/composables/useOCR'

const {
  state,
  processImage,
  convertToBulkEntries,
  clearResult
} = useOCR()

// Process image with preprocessing options
const options = {
  contrast: 1.2,
  brightness: 0.1,
  sharpen: true,
  denoise: true,
  threshold: 128
}

await processImage(imageFile, options)
</script>

<template>
  <div v-if="state.isProcessing">
    Processing... {{ Math.round(state.progress) }}%
  </div>
  
  <div v-if="state.hasResult">
    <div class="confidence-badge">
      Confidence: {{ Math.round(state.result!.confidence * 100) }}%
    </div>
    
    <div v-for="med in state.result!.medications" :key="med.name">
      {{ med.name }} - {{ med.dosage }} {{ med.frequency }}
    </div>
  </div>
</template>
```

### Component Integration

```vue
<template>
  <OCRPrescriptionProcessor 
    @medications-extracted="handleMedications"
    @processing-complete="handleComplete"
  />
</template>

<script setup>
import OCRPrescriptionProcessor from '@/components/medication/OCRPrescriptionProcessor.vue'

const handleMedications = (medications) => {
  // Handle extracted medications
  console.log('Extracted medications:', medications)
}

const handleComplete = (result) => {
  // Handle processing completion
  console.log('Processing complete:', result)
}
</script>
```

## Configuration

### Preprocessing Options

```typescript
interface PreprocessingOptions {
  contrast?: number      // 0-2, default 1
  brightness?: number    // -1 to 1, default 0
  sharpen?: boolean      // default true
  denoise?: boolean      // default true
  deskew?: boolean       // default true
  threshold?: number     // 0-255, default 128
}
```

### Medication Database

The service includes a built-in database of common South African medications:

```typescript
const commonMedications = [
  { brandName: 'Panado', genericName: 'Paracetamol', strength: '500mg' },
  { brandName: 'Disprin', genericName: 'Aspirin', strength: '300mg' },
  { brandName: 'Stilpane', genericName: 'Paracetamol + Codeine', strength: '500mg/8mg' },
  // ... more medications
]
```

## Dosage Pattern Recognition

The service recognizes various dosage patterns:

### Daily Patterns
- "Take one tablet daily"
- "Take two tablets twice daily"
- "Take three tablets three times daily"

### Specific Timing
- "Take one tablet morning"
- "Take two tablets at 12h00"
- "Take one tablet before breakfast"

### Interval Patterns
- "Take one tablet every 6 hours"
- "Take two tablets every 12 hours"

### Meal-Related
- "Take one tablet with food"
- "Take two tablets before meals"

## Result Structure

### OCRResult Interface

```typescript
interface OCRResult {
  success: boolean
  confidence: number
  text: string
  medications: ExtractedMedication[]
  prescriptionNumber?: string
  doctorName?: string
  icd10Codes: string[]
  rawText: string
  processingTime: number
  errors?: string[]
}
```

### ExtractedMedication Interface

```typescript
interface ExtractedMedication {
  name: string
  genericName?: string
  strength?: string
  dosage: string
  frequency: string
  instructions: string
  confidence: number
  manufacturer?: string
  prescriptionNumber?: string
  prescribingDoctor?: string
  icd10Code?: string
}
```

## Error Handling

The service provides comprehensive error handling:

```typescript
// Check for processing errors
if (!result.success) {
  console.error('OCR failed:', result.errors)
  return
}

// Validate results
const validation = ocrService.validateResult(result)
if (validation.requiresManualEntry) {
  console.warn('Manual entry recommended:', validation.suggestions)
}
```

## Performance Optimization

### Caching
- Results are cached by image hash
- Subsequent processing of the same image returns cached results
- Cache can be cleared manually or automatically

### Image Optimization
- Automatic image preprocessing for better OCR accuracy
- Configurable preprocessing parameters
- Support for various image formats and sizes

### Memory Management
- Proper cleanup of Tesseract workers
- Canvas element disposal
- Memory-efficient image processing

## Testing

Run the test suite:

```bash
npm run test ocrService
```

The test suite covers:
- Service initialization
- Text parsing accuracy
- Dosage pattern recognition
- Error handling
- Caching functionality
- Image preprocessing

## Internationalization

The service supports both English and Afrikaans:

```typescript
// English patterns
"Take one tablet daily"
"Take two tablets morning"

// Afrikaans patterns  
"Neem een tablet daagliks"
"Neem twee tablette oggend"
```

## Security Considerations

- **Client-side Processing**: All OCR processing happens in the browser
- **No Data Transmission**: Images are not sent to external servers
- **Local Storage**: Results are cached locally only
- **Privacy Compliance**: Meets HIPAA and POPIA requirements

## Browser Compatibility

- **Modern Browsers**: Chrome, Firefox, Safari, Edge
- **Canvas Support**: Required for image preprocessing
- **Web Workers**: Used for Tesseract processing
- **File API**: Required for image upload

## Dependencies

```json
{
  "tesseract.js": "^5.0.0"
}
```

## Future Enhancements

### Planned Features
- **Multi-language Support**: Additional language recognition
- **Advanced Preprocessing**: AI-powered image enhancement
- **Medication Database API**: Dynamic medication lookup
- **Batch Processing**: Queue-based multiple image processing
- **Result Export**: PDF and CSV export options

### Performance Improvements
- **WebAssembly**: Faster Tesseract processing
- **GPU Acceleration**: Hardware-accelerated image processing
- **Progressive Loading**: Stream-based image processing
- **Smart Caching**: Intelligent cache invalidation

## Troubleshooting

### Common Issues

1. **Low OCR Accuracy**
   - Adjust preprocessing options
   - Ensure good image quality
   - Check image orientation

2. **Slow Processing**
   - Reduce image size
   - Disable unnecessary preprocessing
   - Check browser performance

3. **Memory Issues**
   - Clear cache regularly
   - Process smaller batches
   - Restart browser if needed

### Debug Mode

Enable debug logging:

```typescript
// In development
localStorage.setItem('ocr-debug', 'true')

// Check console for detailed logs
```

## Contributing

When contributing to the OCR service:

1. **Follow TypeScript conventions**
2. **Add comprehensive tests**
3. **Update documentation**
4. **Test with various image types**
5. **Validate internationalization**

## License

This OCR service is part of the MedGuard SA project and follows the same licensing terms. 