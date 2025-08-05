# Enhanced API Configuration Guide

## Overview

The `api.ts` configuration file has been significantly enhanced to support comprehensive prescription workflow management, security, and reliability features for MedGuard SA.

## Key Features Added

### 1. Prescription Workflow Endpoints (Versioned)

All prescription-related endpoints are now properly versioned and organized:

```typescript
import { API_ENDPOINTS } from '@/config/api'

// Core prescription operations
const prescriptionId = '123'
const prescription = await api.get(API_ENDPOINTS.v1.PRESCRIPTIONS.DETAIL(prescriptionId))

// Prescription processing workflow
await api.post(API_ENDPOINTS.v1.PRESCRIPTIONS.PROCESS(prescriptionId))
await api.post(API_ENDPOINTS.v1.PRESCRIPTIONS.VALIDATE(prescriptionId))
await api.post(API_ENDPOINTS.v1.PRESCRIPTIONS.APPROVE(prescriptionId))

// Prescription lifecycle management
await api.post(API_ENDPOINTS.v1.PRESCRIPTIONS.RENEWAL_REQUEST(prescriptionId))
```

### 2. Comprehensive Error Handling

Error handling is now configurable and type-safe:

```typescript
import { ERROR_CONFIG, shouldRetry, getRetryConfig } from '@/config/api'

// Check if an error should be retried
if (shouldRetry(response.status)) {
  const retryConfig = getRetryConfig('SERVER_ERRORS')
  // Implement retry logic
}

// Get user-friendly error messages
const errorMessage = ERROR_CONFIG.MESSAGES.PRESCRIPTION_PROCESSING_ERROR
```

### 3. Request/Response Interceptors for Encryption

Sensitive prescription data is automatically encrypted:

```typescript
import { isSensitiveField, ENCRYPTION_CONFIG } from '@/config/api'

// Check if a field contains sensitive data
if (isSensitiveField('patient_name')) {
  // Apply encryption
}

// Encryption is automatically handled for:
// - patient_name, patient_id
// - prescriber_name, prescriber_id
// - medication_name, dosage, frequency, duration
// - notes, diagnosis
```

### 4. Retry Logic for Critical Operations

Critical prescription operations have intelligent retry logic:

```typescript
import { getRetryConfig } from '@/config/api'

const retryConfig = getRetryConfig('NETWORK_ERRORS')
// {
//   retry: true,
//   maxAttempts: 3,
//   backoffMultiplier: 2,
//   initialDelay: 1000
// }
```

### 5. Timeout Configurations

Different operations have appropriate timeouts:

```typescript
import { getTimeout } from '@/config/api'

const prescriptionTimeout = getTimeout('prescription') // 2 minutes
const ocrTimeout = getTimeout('ocr') // 1 minute
const uploadTimeout = getTimeout('upload') // 3 minutes
const analyticsTimeout = getTimeout('analytics') // 45 seconds
```

### 6. Rate Limiting for OCR Services

OCR services have specific rate limiting:

```typescript
import { apiConfig } from '@/config/api'

const ocrRateLimit = apiConfig.rateLimiting.ocr
// {
//   requestsPerMinute: 10,
//   burstLimit: 3
// }
```

### 7. Authentication Headers for Medical Data Compliance

Medical data compliance headers are automatically added:

```typescript
import { apiConfig } from '@/config/api'

// Headers automatically include:
// - Authorization: Bearer <token>
// - X-API-Version: v1
// - X-Request-ID: <unique-id>
// - X-Encryption-Algorithm: AES-256-GCM
```

### 8. Request Caching for Repeated Lookups

Frequently accessed data is cached:

```typescript
import { getCacheKey, getCacheTTL, CACHE_CONFIG } from '@/config/api'

const cacheKey = getCacheKey('prescriptions', { userId: '123', status: 'active' })
const ttl = getCacheTTL('prescriptions') // 5 minutes

// Cache strategies available:
// - MEMORY: In-memory cache
// - SESSION_STORAGE: Session storage
// - LOCAL_STORAGE: Local storage
// - INDEXED_DB: IndexedDB for larger data
```

### 9. Monitoring Endpoints for Analytics

Comprehensive monitoring and analytics:

```typescript
import { API_ENDPOINTS, MONITORING_CONFIG } from '@/config/api'

// Send metrics
await api.post(API_ENDPOINTS.v1.MONITORING.ANALYTICS, {
  metric: 'prescription_processing_time',
  value: 1500,
  tags: { operation: 'ocr', status: 'success' }
})

// Check system health
const health = await api.get(API_ENDPOINTS.v1.MONITORING.HEALTH)
```

### 10. Backup API Endpoints for Failover

Automatic failover to backup endpoints:

```typescript
import { getBackupApiUrl } from '@/config/api'

// Primary endpoint fails, automatically try backup
const backupUrl = getBackupApiUrl('/api/v1/prescriptions/', 0)
// Falls back to: https://backup1.medguard-sa.com/api/v1/prescriptions/
```

## Usage Examples

### Prescription Processing Workflow

```typescript
import { API_ENDPOINTS, getTimeout, shouldRetry } from '@/config/api'

async function processPrescription(prescriptionId: string, imageFile: File) {
  try {
    // 1. Upload prescription image
    const uploadResponse = await api.post(API_ENDPOINTS.v1.OCR.PROCESS_IMAGE, {
      file: imageFile
    }, {
      timeout: getTimeout('ocr')
    })

    // 2. Process prescription
    const processResponse = await api.post(
      API_ENDPOINTS.v1.PRESCRIPTIONS.PROCESS(prescriptionId),
      { ocrResult: uploadResponse.data }
    )

    // 3. Validate prescription
    const validationResponse = await api.post(
      API_ENDPOINTS.v1.PRESCRIPTIONS.VALIDATE(prescriptionId)
    )

    // 4. Approve if valid
    if (validationResponse.data.isValid) {
      await api.post(API_ENDPOINTS.v1.PRESCRIPTIONS.APPROVE(prescriptionId))
    }

    return { success: true, prescriptionId }

  } catch (error) {
    if (shouldRetry(error.response?.status)) {
      // Implement retry logic
      return await retryOperation(() => processPrescription(prescriptionId, imageFile))
    }
    throw error
  }
}
```

### OCR Processing with Rate Limiting

```typescript
import { API_ENDPOINTS, apiConfig, devUtils } from '@/config/api'

async function processMultipleImages(images: File[]) {
  const batchSize = apiConfig.rateLimiting.ocr.burstLimit
  
  for (let i = 0; i < images.length; i += batchSize) {
    const batch = images.slice(i, i + batchSize)
    
    const promises = batch.map(image => 
      api.post(API_ENDPOINTS.v1.OCR.PROCESS_IMAGE, { file: image })
    )
    
    const results = await Promise.all(promises)
    
    // Log rate limiting info
    devUtils.logRateLimit('ocr', 
      parseInt(response.headers['X-RateLimit-Remaining'] || '0'),
      parseInt(response.headers['X-RateLimit-Reset'] || '0')
    )
    
    // Wait if we're approaching rate limit
    if (i + batchSize < images.length) {
      await new Promise(resolve => setTimeout(resolve, 6000)) // 6 seconds
    }
  }
}
```

### Caching Prescription Data

```typescript
import { getCacheKey, getCacheTTL, CACHE_CONFIG, devUtils } from '@/config/api'

class PrescriptionCache {
  private cache = new Map<string, { data: any, timestamp: number }>()

  async getPrescription(prescriptionId: string) {
    const cacheKey = getCacheKey('prescriptions', { id: prescriptionId })
    const cached = this.cache.get(cacheKey)
    
    if (cached && Date.now() - cached.timestamp < getCacheTTL('prescriptions')) {
      devUtils.logCacheOperation('get', cacheKey, true)
      return cached.data
    }
    
    devUtils.logCacheOperation('get', cacheKey, false)
    
    const response = await api.get(API_ENDPOINTS.v1.PRESCRIPTIONS.DETAIL(prescriptionId))
    
    this.cache.set(cacheKey, {
      data: response.data,
      timestamp: Date.now()
    })
    
    devUtils.logCacheOperation('set', cacheKey)
    return response.data
  }
}
```

### Monitoring and Analytics

```typescript
import { API_ENDPOINTS, MONITORING_CONFIG, devUtils } from '@/config/api'

class PerformanceMonitor {
  private metrics: Map<string, number[]> = new Map()

  trackMetric(metric: string, value: number, tags?: Record<string, string>) {
    if (!this.metrics.has(metric)) {
      this.metrics.set(metric, [])
    }
    
    this.metrics.get(metric)!.push(value)
    
    // Log metric in development
    devUtils.logMetric(metric, value, tags)
    
    // Send to monitoring endpoint (sampled)
    if (Math.random() < MONITORING_CONFIG.SAMPLING.DEFAULT) {
      this.sendMetric(metric, value, tags)
    }
  }

  private async sendMetric(metric: string, value: number, tags?: Record<string, string>) {
    try {
      await api.post(API_ENDPOINTS.v1.MONITORING.ANALYTICS, {
        metric,
        value,
        tags,
        timestamp: Date.now()
      })
    } catch (error) {
      console.warn('Failed to send metric:', error)
    }
  }
}
```

## Configuration Options

### Environment Variables

```typescript
// In environment.ts
export const environment = {
  FORCE_REAL_API: true,
  API_BASE_URL: 'http://localhost:8000',
  ENABLE_API_LOGGING: true,
  IS_DEVELOPMENT: import.meta.env.DEV,
  IS_PRODUCTION: import.meta.env.PROD
}
```

### Custom Timeouts

```typescript
// Override default timeouts
const customConfig = {
  ...apiConfig,
  timeout: {
    ...apiConfig.timeout,
    prescription: 180000, // 3 minutes for complex prescriptions
    ocr: 90000, // 1.5 minutes for OCR
  }
}
```

### Rate Limiting Configuration

```typescript
// Adjust rate limits based on user tier
const premiumRateLimits = {
  ocr: { requestsPerMinute: 30, burstLimit: 10 },
  prescription: { requestsPerMinute: 60, burstLimit: 10 },
  general: { requestsPerMinute: 200, burstLimit: 40 }
}
```

## Security Considerations

1. **Encryption**: All sensitive data is automatically encrypted using AES-256-GCM
2. **Authentication**: JWT tokens are automatically refreshed
3. **Rate Limiting**: Prevents abuse and ensures fair usage
4. **Audit Trail**: All prescription operations are logged for compliance
5. **Data Privacy**: Sensitive fields are identified and protected

## Performance Optimizations

1. **Caching**: Frequently accessed data is cached with appropriate TTL
2. **Retry Logic**: Intelligent retry with exponential backoff
3. **Timeout Management**: Operation-specific timeouts prevent hanging requests
4. **Batch Operations**: Support for bulk operations to reduce API calls
5. **Monitoring**: Real-time performance tracking and alerting

## Migration Guide

### From Old API Structure

```typescript
// Old way
const prescription = await api.get(`/api/medications/prescriptions/${id}/`)

// New way
const prescription = await api.get(API_ENDPOINTS.v1.PRESCRIPTIONS.DETAIL(id))
```

### Adding New Endpoints

```typescript
// Add to API_ENDPOINTS.v1
NEW_FEATURE: {
  CREATE: '/api/v1/new-feature/',
  LIST: '/api/v1/new-feature/',
  DETAIL: (id: string) => `/api/v1/new-feature/${id}/`,
}
```

## Troubleshooting

### Common Issues

1. **Rate Limit Exceeded**: Check rate limiting configuration and implement backoff
2. **Timeout Errors**: Adjust timeout values for specific operations
3. **Cache Misses**: Verify cache keys and TTL settings
4. **Encryption Errors**: Ensure encryption keys are properly configured

### Debug Mode

Enable detailed logging in development:

```typescript
// All API calls, responses, errors, cache operations, and metrics are logged
// Check browser console for detailed information
```

## Best Practices

1. **Always use versioned endpoints** for future compatibility
2. **Implement proper error handling** with retry logic
3. **Use appropriate timeouts** for different operations
4. **Monitor performance** and adjust configurations accordingly
5. **Cache frequently accessed data** to improve performance
6. **Respect rate limits** to ensure system stability
7. **Log operations** for debugging and compliance
8. **Use backup endpoints** for high availability 