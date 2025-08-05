# Enhanced OCR Service Documentation

## Overview

The Enhanced OCR Service for MedGuard SA provides comprehensive prescription processing capabilities with multiple OCR providers, image quality assessment, automatic optimization, and intelligent validation. This service is designed to handle South African prescription formats while supporting international standards.

## Features

### 1. Multi-Provider OCR Processing
- **Google Cloud Vision API** - Primary production OCR service
- **Azure Computer Vision** - Fallback OCR service
- **Tesseract.js** - Local fallback for offline processing
- Automatic provider selection based on availability and performance

### 2. Image Quality Assessment
- **Resolution Analysis** - Evaluates image resolution for OCR suitability
- **Contrast Measurement** - Detects low contrast images
- **Brightness Analysis** - Identifies over/under-exposed images
- **Blur Detection** - Uses Laplacian variance to detect blur
- **Noise Assessment** - Measures image noise levels
- **Skew Detection** - Identifies rotated or skewed images
- **Overall Quality Score** - Weighted combination of all metrics

### 3. Automatic Image Optimization
- **Contrast Enhancement** - Improves text readability
- **Brightness Adjustment** - Normalizes lighting conditions
- **Auto-deskewing** - Corrects image rotation
- **Noise Reduction** - Applies median filtering
- **Sharpening** - Enhances text edges
- **Threshold Optimization** - Optimizes for text extraction

### 4. Prescription Format Detection
- **SA Standard** - South African public healthcare format
- **SA Private** - South African private healthcare format
- **International** - Generic international format
- **Language Detection** - English, Afrikaans, or mixed
- **Feature Recognition** - Identifies prescription-specific elements

### 5. Medical Abbreviation Expansion
- **Dosage Abbreviations** - mg, ml, mcg, g, kg
- **Frequency Abbreviations** - qd, bid, tid, qid, q4h, q6h, q8h, q12h
- **Route Abbreviations** - po, im, iv, sc, top, inh
- **Timing Abbreviations** - ac, pc, hs, am, pm
- **Instruction Abbreviations** - prn, stat, sos, ut, w/, w/o

### 6. Drug Database Cross-Referencing
- **Local Database** - Built-in common medications
- **External API Integration** - For comprehensive drug information
- **Alternative Suggestions** - Generic name mapping
- **Drug Interactions** - Safety warnings
- **Contraindications** - Medical warnings

### 7. Confidence-Based Validation
- **Multi-factor Scoring** - OCR confidence, image quality, medication validation
- **Manual Review Triggers** - Automatic detection of low-confidence results
- **Quality Thresholds** - Configurable confidence levels
- **Validation Reports** - Detailed analysis of results

### 8. Caching System
- **Image Hash Caching** - Prevents reprocessing identical images
- **Drug Validation Cache** - Speeds up medication lookups
- **Batch Processing Queue** - Manages concurrent processing
- **Memory Management** - Automatic cache cleanup

### 9. Batch Processing
- **Concurrent Processing** - Configurable concurrency limits
- **Progress Tracking** - Real-time batch status
- **Error Handling** - Graceful failure management
- **Resource Optimization** - Memory and CPU management

### 10. Comprehensive Validation
- **Image Quality Validation** - Ensures processable images
- **Format Validation** - Verifies prescription structure
- **Medication Validation** - Cross-references drug database
- **Data Completeness** - Checks for required fields

## Installation and Setup

### 1. Environment Variables

Add the following environment variables to your `.env` file:

```bash
# Google Cloud Vision API
VITE_GOOGLE_CLOUD_VISION_API_KEY=your_google_api_key
VITE_GOOGLE_CLOUD_PROJECT_ID=your_project_id
VITE_GOOGLE_CLOUD_REGION=us-central1

# Azure Computer Vision API
VITE_AZURE_COMPUTER_VISION_ENDPOINT=your_azure_endpoint
VITE_AZURE_COMPUTER_VISION_API_KEY=your_azure_api_key
VITE_AZURE_REGION=eastus
```

### 2. Dependencies

The service uses the following dependencies (already included in package.json):

```json
{
  "tesseract.js": "^6.0.1",
  "canvas": "^3.1.2"
}
```

### 3. Configuration

```typescript
import { OCRService } from './services/ocrService'
import { ocrConfig, getBatchConfig } from './config/ocrConfig'

// Initialize the service
const ocrService = OCRService.getInstance()
await ocrService.initialize(ocrConfig)

// Configure batch processing
const batchConfig = getBatchConfig()
ocrService.configureBatchProcessing(batchConfig)
```

## Usage Examples

### Basic OCR Processing

```typescript
import { OCRService } from './services/ocrService'

const ocrService = OCRService.getInstance()
await ocrService.initialize()

const result = await ocrService.processPrescription(imageFile)
console.log('Extracted medications:', result.medications)
```

### Advanced Processing with Validation

```typescript
const result = await ocrService.processPrescription(imageFile)

// Validate results
const validation = ocrService.validateResult(result)

if (validation.requiresManualEntry) {
  console.log('Manual review required:', validation.suggestions)
}

// Get detailed medication report
const medicationReport = await ocrService.getMedicationValidationReport(result.medications)
console.log('Validated medications:', medicationReport.validated.length)
```

### Batch Processing

```typescript
const imageFiles = [file1, file2, file3, file4]
const results = await ocrService.processBatchPrescriptions(imageFiles)

const successful = results.filter(r => r.success)
const requiresReview = results.filter(r => r.requiresManualReview)

console.log(`Processed ${successful.length} successfully, ${requiresReview.length} need review`)
```

### Custom Preprocessing

```typescript
const preprocessingOptions = {
  contrast: 1.2,        // Enhance contrast
  brightness: 0.1,      // Slightly increase brightness
  sharpen: true,        // Apply sharpening
  denoise: true,        // Apply noise reduction
  deskew: true,         // Auto-deskew
  threshold: 140        // Custom threshold
}

const result = await ocrService.processPrescription(imageFile, preprocessingOptions)
```

## API Reference

### OCRService Class

#### Methods

##### `getInstance(): OCRService`
Returns the singleton instance of the OCR service.

##### `initialize(config?: OCRProviderConfig): Promise<void>`
Initializes the OCR service with optional configuration.

##### `processPrescription(imageFile: File | string, options?: PreprocessingOptions, batchId?: string, pageNumber?: number): Promise<OCRResult>`
Processes a single prescription image.

##### `processBatchPrescriptions(imageFiles: (File | string)[], options?: PreprocessingOptions): Promise<OCRResult[]>`
Processes multiple prescription images in batch.

##### `validateResult(result: OCRResult): ValidationResult`
Validates OCR results and provides recommendations.

##### `getMedicationValidationReport(medications: ExtractedMedication[]): Promise<MedicationValidationReport>`
Gets detailed validation report for medications.

##### `configureBatchProcessing(config: Partial<BatchProcessingConfig>): void`
Configures batch processing settings.

##### `getServiceStats(): ServiceStats`
Gets comprehensive service statistics.

##### `clearAllCaches(): void`
Clears all caches for memory management.

### Interfaces

#### OCRResult
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
  imageQuality: ImageQualityAssessment
  prescriptionFormat: PrescriptionFormat
  requiresManualReview: boolean
  batchId?: string
  pageNumber?: number
  totalPages?: number
}
```

#### ImageQualityAssessment
```typescript
interface ImageQualityAssessment {
  overallScore: number
  resolution: number
  contrast: number
  brightness: number
  blur: number
  noise: number
  skew: number
  isProcessable: boolean
  recommendations: string[]
}
```

#### PrescriptionFormat
```typescript
interface PrescriptionFormat {
  type: 'SA_STANDARD' | 'SA_PRIVATE' | 'INTERNATIONAL' | 'UNKNOWN'
  confidence: number
  features: string[]
  language: 'en' | 'af' | 'mixed'
}
```

## Configuration Options

### OCR Provider Configuration

```typescript
interface OCRProviderConfig {
  googleCloudVision?: {
    apiKey: string
    projectId: string
    region: string
  }
  azureComputerVision?: {
    endpoint: string
    apiKey: string
    region: string
  }
  tesseract?: {
    enabled: boolean
    languages: string[]
  }
}
```

### Batch Processing Configuration

```typescript
interface BatchProcessingConfig {
  maxConcurrent: number      // Maximum concurrent processing
  timeout: number           // Timeout in milliseconds
  retryAttempts: number     // Number of retry attempts
  qualityThreshold: number  // Minimum quality score (0-1)
}
```

### Preprocessing Options

```typescript
interface PreprocessingOptions {
  contrast?: number    // Contrast adjustment (0-2, default 1)
  brightness?: number  // Brightness adjustment (-1 to 1, default 0)
  sharpen?: boolean    // Apply sharpening (default true)
  denoise?: boolean    // Apply noise reduction (default true)
  deskew?: boolean     // Auto-deskew (default true)
  threshold?: number   // Binary threshold (0-255, default 128)
}
```

## Error Handling

The service provides comprehensive error handling:

```typescript
try {
  const result = await ocrService.processPrescription(imageFile)
  
  if (!result.success) {
    console.error('OCR Processing Failed:', result.errors)
    return
  }
  
  if (result.requiresManualReview) {
    console.warn('Manual review required')
  }
  
} catch (error) {
  console.error('OCR Service Error:', error)
  ocrService.clearAllCaches() // Recovery mechanism
}
```

## Performance Optimization

### Caching Strategy
- Image hash-based caching prevents reprocessing
- Drug validation cache speeds up lookups
- Automatic cache cleanup for memory management

### Batch Processing
- Configurable concurrency limits
- Progress tracking and error handling
- Resource optimization

### Quality Assessment
- Early detection of poor quality images
- Automatic optimization for better results
- Confidence-based processing decisions

## Security Considerations

### API Key Management
- Environment variable-based configuration
- No hardcoded credentials
- Secure key rotation support

### Data Privacy
- Local processing when possible
- Secure API communication
- No persistent storage of sensitive data

### Error Handling
- No sensitive data in error messages
- Graceful degradation on failures
- Secure logging practices

## Monitoring and Debugging

### Service Statistics
```typescript
const stats = ocrService.getServiceStats()
console.log('Cache size:', stats.cacheStats.size)
console.log('Average quality score:', stats.qualityStats.averageScore)
console.log('Validated medications:', stats.validationStats.validated)
```

### Configuration Validation
```typescript
import { validateOCRConfig } from './config/ocrConfig'

const validation = validateOCRConfig()
if (!validation.isValid) {
  console.error('Configuration errors:', validation.errors)
}
```

### Quality Monitoring
- Track average image quality scores
- Monitor processing success rates
- Analyze common quality issues

## Troubleshooting

### Common Issues

1. **Low OCR Confidence**
   - Check image quality
   - Verify preprocessing settings
   - Consider manual entry for critical data

2. **Provider Failures**
   - Verify API keys and configuration
   - Check network connectivity
   - Review provider quotas and limits

3. **Memory Issues**
   - Clear caches periodically
   - Reduce batch size
   - Monitor memory usage

4. **Performance Issues**
   - Adjust concurrency settings
   - Optimize image preprocessing
   - Use appropriate quality thresholds

### Debug Mode

Enable detailed logging for troubleshooting:

```typescript
// Enable Tesseract logging
await ocrService.initialize({
  ...ocrConfig,
  tesseract: {
    ...ocrConfig.tesseract,
    logger: m => console.log('Tesseract:', m)
  }
})
```

## Future Enhancements

### Planned Features
- **Machine Learning Models** - Custom prescription format recognition
- **Real-time Processing** - WebSocket-based streaming
- **Advanced Validation** - Drug interaction checking
- **Multi-language Support** - Additional language models
- **Cloud Integration** - Direct cloud storage processing

### Performance Improvements
- **WebAssembly** - Faster image processing
- **Web Workers** - Background processing
- **GPU Acceleration** - Hardware-accelerated operations
- **Caching Optimization** - Intelligent cache strategies

## Support and Maintenance

### Regular Maintenance
- Update medication database
- Monitor API quotas and limits
- Review and optimize configurations
- Clear caches periodically

### Monitoring
- Track processing success rates
- Monitor image quality trends
- Analyze user feedback
- Performance metrics collection

### Updates
- Regular dependency updates
- Security patches
- Feature enhancements
- Bug fixes

## Contributing

When contributing to the OCR service:

1. Follow TypeScript best practices
2. Add comprehensive tests
3. Update documentation
4. Consider performance implications
5. Maintain backward compatibility

## License

This enhanced OCR service is part of the MedGuard SA project and follows the same licensing terms. 