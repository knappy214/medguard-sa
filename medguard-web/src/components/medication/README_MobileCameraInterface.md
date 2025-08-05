# Mobile Camera Interface

A comprehensive mobile camera interface component optimized for prescription scanning with advanced features for image capture, quality assessment, and multi-page processing.

## Features

### 🎥 Native Camera Controls
- **Auto Focus**: Automatic focus adjustment for optimal image clarity
- **Auto Exposure**: Dynamic exposure control for proper lighting
- **Camera Switching**: Toggle between front and back cameras
- **Flash Control**: Manual flash control for low-light conditions
- **Low-light Optimization**: Enhanced performance in challenging lighting

### 📊 Real-time Quality Assessment
- **Brightness Analysis**: Monitor image brightness levels
- **Contrast Detection**: Analyze image contrast for readability
- **Sharpness Measurement**: Assess image sharpness and clarity
- **Quality Scoring**: Overall quality score with actionable feedback
- **Warning System**: Real-time warnings for poor image quality

### 🎯 Boundary Detection
- **Document Detection**: Automatic prescription boundary detection
- **Visual Guides**: Corner guides and boundary rectangles
- **Real-time Feedback**: Live boundary detection with overlay guides
- **Focus Indicators**: Visual focus points for precise positioning

### 📄 Multi-page Capture
- **Page Management**: Capture and manage multiple prescription pages
- **Page Review**: Grid view of captured pages with quality indicators
- **Page Selection**: Select specific pages for processing
- **Page Removal**: Remove unwanted pages from collection
- **Page Reordering**: Reorganize page sequence as needed

### 🖼️ Image Preview & Editing
- **Zoom Controls**: Pinch-to-zoom and wheel zoom functionality
- **Rotation**: 90-degree rotation increments
- **Pan Support**: Drag to pan around zoomed images
- **Crop Interface**: Image cropping with boundary guides
- **Quality Preview**: Real-time quality assessment display

### 📱 Mobile Optimizations
- **Haptic Feedback**: Tactile feedback for successful captures
- **Touch Gestures**: Intuitive touch controls for mobile devices
- **Responsive Design**: Optimized for various screen sizes
- **Performance**: Efficient image processing and memory management

### 🔒 Secure Local Storage
- **Automatic Storage**: Secure local storage of captured images
- **Retention Management**: Configurable retention periods
- **Cleanup System**: Automatic cleanup of old images
- **Privacy Focused**: Local-only storage with no cloud uploads

## Usage

### Basic Implementation

```vue
<template>
  <div>
    <button @click="showCamera = true">Open Camera</button>
    
    <MobileCameraInterface
      v-if="showCamera"
      @close="showCamera = false"
      @capture="handleImageCapture"
      @multi-page-capture="handleMultiPageCapture"
      @error="handleError"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import MobileCameraInterface from './MobileCameraInterface.vue'

const showCamera = ref(false)

const handleImageCapture = (imageData) => {
  console.log('Captured image:', imageData)
  // Process the captured image
}

const handleMultiPageCapture = (pages) => {
  console.log('Captured pages:', pages)
  // Process multiple pages
}

const handleError = (error) => {
  console.error('Camera error:', error)
}
</script>
```

### Advanced Configuration

```vue
<template>
  <MobileCameraInterface
    :auto-focus="true"
    :auto-exposure="true"
    :quality-threshold="75"
    :multi-page="true"
    :auto-capture="false"
    :capture-delay="3"
    :enable-haptic-feedback="true"
    :enable-boundary-detection="true"
    :enable-quality-assessment="true"
    :enable-flash-control="true"
    :enable-low-light-optimization="true"
    :max-pages="10"
    :storage-retention-days="7"
    @capture="handleImageCapture"
    @multi-page-capture="handleMultiPageCapture"
    @quality-assessment="handleQualityAssessment"
    @boundary-detected="handleBoundaryDetection"
    @error="handleError"
  />
</template>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `autoFocus` | Boolean | `true` | Enable automatic focus adjustment |
| `autoExposure` | Boolean | `true` | Enable automatic exposure control |
| `qualityThreshold` | Number | `70` | Minimum quality score (0-100) |
| `multiPage` | Boolean | `true` | Enable multi-page capture mode |
| `autoCapture` | Boolean | `false` | Enable automatic capture when conditions are met |
| `captureDelay` | Number | `3` | Delay in seconds before auto-capture |
| `enableHapticFeedback` | Boolean | `true` | Enable haptic feedback on mobile devices |
| `enableBoundaryDetection` | Boolean | `true` | Enable prescription boundary detection |
| `enableQualityAssessment` | Boolean | `true` | Enable real-time quality assessment |
| `enableFlashControl` | Boolean | `true` | Enable flash control |
| `enableLowLightOptimization` | Boolean | `true` | Enable low-light optimization |
| `maxPages` | Number | `10` | Maximum number of pages to capture |
| `storageRetentionDays` | Number | `7` | Days to retain images in local storage |

## Events

| Event | Payload | Description |
|-------|---------|-------------|
| `close` | - | Emitted when camera is closed |
| `capture` | `imageData: string` | Emitted when single image is captured |
| `multi-page-capture` | `pages: PrescriptionPage[]` | Emitted when multiple pages are captured |
| `error` | `error: string` | Emitted when camera error occurs |
| `quality-assessment` | `quality: ImageQuality` | Emitted during quality assessment |
| `boundary-detected` | `boundaries: any` | Emitted when boundaries are detected |

## Types

### ImageQuality
```typescript
interface ImageQuality {
  brightness: number      // 0-100
  contrast: number        // 0-100
  sharpness: number       // 0-100
  noise: number          // 0-100
  blur: number           // 0-100
  overall: number        // 0-100
  isValid: boolean       // Whether quality meets threshold
  warnings: string[]     // Quality warnings
}
```

### PrescriptionPage
```typescript
interface PrescriptionPage {
  id: string
  imageData: string
  pageNumber: number
  quality: ImageQuality
  ocrText: string
  extractedMedications: PrescriptionMedication[]
  confidence: number
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed'
}
```

## Browser Support

### Required APIs
- **getUserMedia**: Camera access
- **Canvas API**: Image processing
- **LocalStorage**: Image storage
- **Vibration API**: Haptic feedback (optional)

### Mobile Support
- **iOS Safari**: 11.0+
- **Android Chrome**: 53+
- **Samsung Internet**: 6.0+
- **Firefox Mobile**: 36+

### Desktop Support
- **Chrome**: 53+
- **Firefox**: 36+
- **Safari**: 11.0+
- **Edge**: 79+

## Performance Considerations

### Image Processing
- **Canvas Operations**: Optimized for real-time processing
- **Memory Management**: Automatic cleanup of processed images
- **Quality Assessment**: Efficient algorithms for real-time analysis

### Mobile Optimization
- **Touch Events**: Optimized touch handling for mobile devices
- **Battery Usage**: Efficient camera usage to minimize battery drain
- **Memory Usage**: Controlled memory allocation for image storage

### Storage Management
- **Automatic Cleanup**: Scheduled cleanup of old images
- **Size Limits**: Configurable storage limits
- **Retention Policies**: Automatic deletion based on age

## Security & Privacy

### Data Handling
- **Local Storage Only**: All images stored locally on device
- **No Cloud Upload**: No automatic cloud synchronization
- **Secure Cleanup**: Secure deletion of stored images
- **Permission Based**: Camera access requires user permission

### Privacy Features
- **No Tracking**: No analytics or tracking of camera usage
- **User Control**: Full user control over captured images
- **Secure Storage**: Encrypted local storage (where supported)

## Accessibility

### Screen Reader Support
- **ARIA Labels**: Proper labeling for screen readers
- **Keyboard Navigation**: Full keyboard accessibility
- **Focus Management**: Proper focus handling

### Visual Accessibility
- **High Contrast**: Support for high contrast mode
- **Reduced Motion**: Respects user's motion preferences
- **Color Blindness**: Color-safe design considerations

## Error Handling

### Common Errors
- **Camera Permission Denied**: User denied camera access
- **Camera Not Available**: No camera hardware available
- **Storage Full**: Local storage capacity exceeded
- **Quality Too Low**: Image quality below threshold

### Error Recovery
- **Graceful Degradation**: Fallback options when features unavailable
- **User Feedback**: Clear error messages and recovery suggestions
- **Retry Mechanisms**: Automatic retry for transient errors

## Integration Examples

### With Prescription Scanner
```vue
<template>
  <div>
    <PrescriptionScanner
      :camera-component="MobileCameraInterface"
      :camera-props="cameraProps"
      @scan-complete="handleScanComplete"
    />
  </div>
</template>

<script setup>
import MobileCameraInterface from './MobileCameraInterface.vue'

const cameraProps = {
  qualityThreshold: 80,
  multiPage: true,
  enableBoundaryDetection: true
}
</script>
```

### With OCR Processing
```vue
<script setup>
import { useOCR } from '@/composables/useOCR'

const { processImage } = useOCR()

const handleImageCapture = async (imageData) => {
  const result = await processImage(imageData)
  if (result.success) {
    // Process OCR results
    console.log('OCR Text:', result.text)
    console.log('Medications:', result.medications)
  }
}
</script>
```

## Troubleshooting

### Camera Not Working
1. Check browser permissions
2. Ensure HTTPS connection (required for camera access)
3. Verify camera hardware availability
4. Check browser compatibility

### Poor Image Quality
1. Adjust quality threshold settings
2. Ensure proper lighting conditions
3. Check camera focus settings
4. Verify camera resolution settings

### Performance Issues
1. Reduce max pages limit
2. Disable unnecessary features
3. Check device memory availability
4. Optimize image processing settings

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `npm install`
3. Run development server: `npm run dev`
4. Test camera functionality on mobile device

### Testing
- Test on various mobile devices
- Verify camera permissions
- Test image quality assessment
- Validate multi-page functionality

### Code Style
- Follow Vue 3 Composition API patterns
- Use TypeScript for type safety
- Maintain accessibility standards
- Follow existing code conventions

## License

This component is part of the MedGuard SA project and follows the project's licensing terms.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review browser compatibility
3. Test on different devices
4. Contact the development team

---

**Note**: This component requires camera permissions and works best on mobile devices with modern browsers. Ensure proper HTTPS setup for production deployment. 