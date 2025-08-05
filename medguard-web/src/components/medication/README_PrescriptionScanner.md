# PrescriptionScanner Component

A comprehensive Vue 3 component for scanning and processing prescription images to extract medication information using OCR (Optical Character Recognition).

## Features

### 1. Camera & File Upload Support
- **Camera Mode**: Direct camera capture using device camera
- **Upload Mode**: File upload for existing prescription images
- **Both Modes**: Support for both camera and file upload simultaneously

### 2. Image Preprocessing
- **Contrast Enhancement**: Improves text readability
- **Noise Removal**: Reduces image artifacts
- **Image Sharpening**: Enhances text clarity
- **Rotation**: Supports 0°, 90°, 180°, 270° rotation
- **Brightness/Contrast**: Adjustable image parameters

### 3. OCR Integration
- **Text Extraction**: Extracts text from prescription images
- **Service Agnostic**: Designed to work with various OCR services:
  - Google Cloud Vision API
  - Azure Computer Vision
  - AWS Textract
  - Tesseract.js (client-side)
- **Error Handling**: Graceful handling of OCR failures

### 4. Prescription Parsing
- **Medication Detection**: Identifies medication names, dosages, frequencies
- **Abbreviation Expansion**: Maps common prescription abbreviations:
  - `po` → "by mouth" / "per mond"
  - `qd` → "once daily" / "een keer daagliks"
  - `bid` → "twice daily" / "twee keer daagliks"
  - And many more...
- **Multi-language Support**: English and Afrikaans prescription formats

### 5. Review Interface
- **Medication Selection**: Checkbox selection for multiple medications
- **Inline Editing**: Edit extracted medication information
- **Batch Import**: Import all medications from a single prescription
- **OCR Text Preview**: View raw extracted text for verification

### 6. Error Handling
- **Camera Permissions**: Handles camera access failures
- **File Validation**: Validates image file types
- **OCR Failures**: Graceful handling of text extraction errors
- **Poor Image Quality**: User feedback for image quality issues

## Usage

### Basic Usage

```vue
<template>
  <PrescriptionScanner
    @add="handleAddMedication"
    @bulk-add="handleBulkAdd"
    @error="handleError"
    @close="handleClose"
  />
</template>

<script setup>
import PrescriptionScanner from '@/components/medication/PrescriptionScanner.vue'
import type { MedicationFormData, BulkMedicationEntry } from '@/types/medication'

const handleAddMedication = (medication: MedicationFormData) => {
  // Handle single medication addition
  console.log('Added medication:', medication)
}

const handleBulkAdd = (medications: BulkMedicationEntry[]) => {
  // Handle bulk medication addition
  console.log('Added medications:', medications)
}

const handleError = (error: string) => {
  // Handle scanner errors
  console.error('Scanner error:', error)
}

const handleClose = () => {
  // Handle scanner close
  console.log('Scanner closed')
}
</script>
```

### Advanced Usage

```vue
<template>
  <PrescriptionScanner
    mode="both"
    :allow-batch="true"
    :auto-process="false"
    @add="handleAddMedication"
    @bulk-add="handleBulkAdd"
    @error="handleError"
    @close="handleClose"
  />
</template>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `mode` | `'camera' \| 'upload' \| 'both'` | `'both'` | Scanner mode |
| `allowBatch` | `boolean` | `true` | Enable batch medication import |
| `autoProcess` | `boolean` | `false` | Automatically process images after capture |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `add` | `MedicationFormData` | Single medication added |
| `bulk-add` | `BulkMedicationEntry[]` | Multiple medications added |
| `error` | `string` | Error occurred during processing |
| `close` | - | Scanner modal closed |

## OCR Service Integration

The component includes a placeholder OCR function that can be replaced with real OCR services:

### Google Cloud Vision API Example

```typescript
const processOCR = async (imageData: string): Promise<string> => {
  try {
    const response = await fetch('/api/ocr/google-vision', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        image: imageData.split(',')[1], // Remove data:image/jpeg;base64, prefix
      }),
    })
    
    const result = await response.json()
    return result.text
  } catch (err) {
    throw new Error('OCR processing failed')
  }
}
```

### Tesseract.js Example

```typescript
import Tesseract from 'tesseract.js'

const processOCR = async (imageData: string): Promise<string> => {
  try {
    const result = await Tesseract.recognize(imageData, 'eng', {
      logger: m => console.log(m)
    })
    return result.data.text
  } catch (err) {
    throw new Error('OCR processing failed')
  }
}
```

## Prescription Abbreviations

The component includes comprehensive abbreviation mappings for both English and Afrikaans:

### English Abbreviations
- `po` → "by mouth"
- `pr` → "by rectum"
- `im` → "intramuscular"
- `iv` → "intravenous"
- `qd` → "once daily"
- `bid` → "twice daily"
- `tid` → "three times daily"
- `qid` → "four times daily"
- `prn` → "as needed"
- `ac` → "before meals"
- `pc` → "after meals"
- `hs` → "at bedtime"

### Afrikaans Abbreviations
- `po` → "per mond"
- `pr` → "per rektum"
- `im` → "intramuskulêr"
- `iv` → "intraveneus"
- `qd` → "een keer daagliks"
- `bid` → "twee keer daagliks"
- `tid` → "drie keer daagliks"
- `qid` → "vier keer daagliks"
- `prn` → "soos benodig"
- `ac` → "voor maaltye"
- `pc` → "na maaltye"
- `hs` → "voor slaaptyd"

## Image Preprocessing

The component includes several image preprocessing techniques:

### Contrast Enhancement
```typescript
ctx.filter = `contrast(${contrast}) brightness(${brightness})`
```

### Image Sharpening
```typescript
const kernel = [
  0, -1, 0,
  -1, 5, -1,
  0, -1, 0
]
```

### Rotation
```typescript
ctx.save()
ctx.translate(canvas.width / 2, canvas.height / 2)
ctx.rotate((angle * Math.PI) / 180)
ctx.drawImage(img, -img.width / 2, -img.height / 2)
ctx.restore()
```

## Styling

The component uses DaisyUI classes and includes custom styling:

```css
.modal {
  z-index: 1000;
}

.steps .step {
  @apply text-sm;
}

.steps .step-primary {
  @apply text-primary;
}

/* Custom scrollbar for medication list */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}
```

## Internationalization

The component supports both English and Afrikaans through Vue I18n:

### English Keys
```json
{
  "prescriptionScanner": {
    "title": "Prescription Scanner",
    "scanPrescription": "Scan Prescription",
    "cameraMode": "Camera Mode",
    "uploadMode": "Upload Mode"
  }
}
```

### Afrikaans Keys
```json
{
  "prescriptionScanner": {
    "title": "Voorskrif Skandeerder",
    "scanPrescription": "Skandeer Voorskrif",
    "cameraMode": "Kamera Modus",
    "uploadMode": "Oplaai Modus"
  }
}
```

## Browser Compatibility

- **Camera API**: Requires HTTPS in production
- **File API**: Modern browsers with FileReader support
- **Canvas API**: All modern browsers
- **MediaDevices API**: Modern browsers with camera support

## Security Considerations

- **Camera Permissions**: Requires user consent for camera access
- **File Upload**: Validates file types to prevent malicious uploads
- **Image Processing**: Client-side processing for privacy
- **OCR Service**: Consider using secure API endpoints for OCR processing

## Performance Considerations

- **Image Size**: Large images are automatically compressed
- **Processing**: Image preprocessing is done client-side
- **Memory**: Proper cleanup of video streams and canvas elements
- **Caching**: Consider caching OCR results for repeated scans

## Future Enhancements

1. **Real-time OCR**: Live text extraction during camera preview
2. **Barcode Scanning**: Support for medication barcode scanning
3. **AI-powered Parsing**: Machine learning for better prescription parsing
4. **Cloud Storage**: Secure storage of prescription images
5. **Medication Database**: Integration with medication databases for validation
6. **Voice Input**: Voice-to-text for manual entry
7. **Offline Support**: Client-side OCR for offline functionality

## Troubleshooting

### Camera Not Working
- Check browser permissions
- Ensure HTTPS in production
- Verify camera availability

### OCR Not Working
- Check image quality
- Verify OCR service configuration
- Review network connectivity

### Parsing Issues
- Check prescription format
- Verify abbreviation mappings
- Review language settings

## Contributing

When contributing to this component:

1. Follow Vue 3 Composition API patterns
2. Maintain TypeScript type safety
3. Add comprehensive error handling
4. Update translation files for new features
5. Test with various image qualities and formats
6. Ensure accessibility compliance
7. Add unit tests for new functionality 