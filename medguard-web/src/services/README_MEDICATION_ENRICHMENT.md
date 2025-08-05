# Medication Enrichment Service

## Overview

The Medication Enrichment Service integrates with the Perplexity API to provide comprehensive medication information for the MedGuard SA application. It enriches basic medication data with detailed information including side effects, contraindications, interactions, South African pricing, and availability.

## Features

### 1. Comprehensive Drug Information
- **Generic and brand names** available in South Africa
- **Active ingredients** and chemical composition
- **Manufacturer information** and contact details
- **Mechanism of action** and therapeutic effects
- **Regulatory status** (SAHPRA approval)

### 2. Safety Information
- **Side effects** with frequency and severity
- **Contraindications** and precautions
- **Drug interactions** with severity levels
- **Pregnancy and breastfeeding** safety information
- **Pediatric and geriatric** use considerations

### 3. Dosage Guidelines
- **Adult dosage** recommendations
- **Pediatric dosing** by age/weight
- **Renal and hepatic** dose adjustments
- **Administration instructions**
- **Duration of therapy** guidelines

### 4. South African Market Data
- **Cost analysis** in ZAR
- **Generic alternatives** and pricing
- **Insurance coverage** information
- **Pharmacy availability** and stock status
- **Online availability** options

### 5. Storage and Safety
- **Storage requirements** and conditions
- **Expiration guidelines**
- **Disposal instructions**
- **Temperature sensitivity**

### 6. Performance Features
- **Intelligent caching** with 24-hour TTL
- **Rate limiting** (50 requests/minute)
- **Parallel processing** for faster enrichment
- **Error handling** and graceful degradation
- **Resource management** and cleanup

## Usage

### Basic Enrichment

```typescript
import medicationEnrichmentService from '@/services/medicationEnrichmentService'
import type { PerplexityEnrichmentRequest } from '@/types/medication'

const request: PerplexityEnrichmentRequest = {
  medicationName: 'Paracetamol',
  genericName: 'Acetaminophen',
  strength: '500mg',
  includeInteractions: true,
  includeSideEffects: true,
  includeCost: true,
  includeAvailability: true
}

const result = await medicationEnrichmentService.enrichMedication(request)

if (result.success) {
  const enrichment = result.data
  console.log('Drug Info:', enrichment.drugInfo)
  console.log('Interactions:', enrichment.interactions)
  console.log('Side Effects:', enrichment.sideEffects)
  console.log('Cost Analysis:', enrichment.costAnalysis)
  console.log('Availability:', enrichment.availability)
}
```

### Integration with Medication API

```typescript
import medicationApi from '@/services/medicationApi'
import medicationEnrichmentService from '@/services/medicationEnrichmentService'

// Create medication with enrichment
const createMedicationWithEnrichment = async (medicationData: any) => {
  // First create the medication
  const medication = await medicationApi.createMedication(medicationData)
  
  // Then enrich it with additional information
  const enrichmentRequest: PerplexityEnrichmentRequest = {
    medicationName: medication.name,
    genericName: medication.genericName,
    strength: medication.strength,
    includeInteractions: true,
    includeSideEffects: true,
    includeCost: true,
    includeAvailability: true
  }
  
  const enrichment = await medicationEnrichmentService.enrichMedication(enrichmentRequest)
  
  if (enrichment.success && enrichment.data) {
    // Update medication with enriched data
    const updatedMedication = await medicationApi.updateMedication(medication.id, {
      ...medication,
      enrichedData: enrichment.data
    })
    
    return updatedMedication
  }
  
  return medication
}
```

### Batch Enrichment

```typescript
// Enrich multiple medications
const enrichMultipleMedications = async (medications: any[]) => {
  const enrichmentPromises = medications.map(medication => {
    const request: PerplexityEnrichmentRequest = {
      medicationName: medication.name,
      genericName: medication.genericName,
      strength: medication.strength
    }
    return medicationEnrichmentService.enrichMedication(request)
  })
  
  const results = await Promise.allSettled(enrichmentPromises)
  
  return results.map((result, index) => ({
    medication: medications[index],
    enrichment: result.status === 'fulfilled' ? result.value : null
  }))
}
```

## Configuration

### Service Configuration

The service uses the following configuration:

```typescript
const ENRICHMENT_CONFIG = {
  // Cache settings
  cache: {
    ttl: 24 * 60 * 60 * 1000, // 24 hours
    maxSize: 100, // Maximum cache entries
    cleanupInterval: 60 * 60 * 1000 // 1 hour
  },
  
  // Rate limiting
  rateLimit: {
    maxRequests: 50, // Max requests per window
    windowMs: 60 * 1000, // 1 minute window
    retryDelay: 2000 // 2 seconds
  },
  
  // Perplexity API settings
  perplexity: {
    baseURL: 'https://api.perplexity.ai',
    model: 'llama-3.1-sonar-large-128k-online',
    maxTokens: 4000,
    temperature: 0.1,
    timeout: 30000
  },
  
  // South African specific settings
  southAfrica: {
    currency: 'ZAR',
    language: 'en-ZA',
    timezone: 'Africa/Johannesburg',
    regulatoryBody: 'SAHPRA'
  }
}
```

### Environment Variables

Add these to your environment configuration:

```typescript
// config/environment.ts
export const environment = {
  // ... existing config
  
  // Perplexity API configuration
  PERPLEXITY_API_KEY: import.meta.env.VITE_PERPLEXITY_API_KEY,
  PERPLEXITY_BASE_URL: import.meta.env.VITE_PERPLEXITY_BASE_URL || 'https://api.perplexity.ai',
  
  // Enrichment service configuration
  ENRICHMENT_CACHE_TTL: 24 * 60 * 60 * 1000, // 24 hours
  ENRICHMENT_RATE_LIMIT: 50, // requests per minute
  ENRICHMENT_ENABLED: true
}
```

## API Integration

### Backend Proxy

The service uses a backend proxy for Perplexity API calls to ensure security and proper rate limiting:

```typescript
// Frontend service calls backend proxy
private async queryPerplexity(prompt: string): Promise<string | null> {
  try {
    const response = await apiClient.post('/api/medications/enrichment/perplexity/', {
      prompt,
      model: ENRICHMENT_CONFIG.perplexity.model,
      max_tokens: ENRICHMENT_CONFIG.perplexity.maxTokens,
      temperature: ENRICHMENT_CONFIG.perplexity.temperature
    })

    return response.data?.response || null
  } catch (error) {
    console.error('Perplexity API query failed:', error)
    return null
  }
}
```

### Backend Endpoint

The backend should implement the following endpoint:

```python
# Django view example
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def perplexity_enrichment(request):
    """
    Proxy endpoint for Perplexity API calls
    """
    try:
        prompt = request.data.get('prompt')
        model = request.data.get('model', 'llama-3.1-sonar-large-128k-online')
        max_tokens = request.data.get('max_tokens', 4000)
        temperature = request.data.get('temperature', 0.1)
        
        # Call Perplexity API
        response = call_perplexity_api(prompt, model, max_tokens, temperature)
        
        return Response({
            'response': response,
            'success': True
        })
    except Exception as e:
        return Response({
            'error': str(e),
            'success': False
        }, status=500)
```

## Data Types

### PerplexityEnrichmentRequest

```typescript
interface PerplexityEnrichmentRequest {
  medicationName: string
  genericName?: string
  strength?: string
  manufacturer?: string
  includeInteractions?: boolean
  includeSideEffects?: boolean
  includeCost?: boolean
  includeAvailability?: boolean
}
```

### PerplexityEnrichmentResponse

```typescript
interface PerplexityEnrichmentResponse {
  success: boolean
  data?: MedicationEnrichment
  error?: string
  source: 'perplexity'
  timestamp: string
}
```

### MedicationEnrichment

```typescript
interface MedicationEnrichment {
  drugInfo?: DrugDatabaseEntry
  interactions?: MedicationInteraction[]
  sideEffects?: string[]
  contraindications?: string[]
  dosageGuidelines?: DosageGuideline[]
  costAnalysis?: CostAnalysis
  availability?: AvailabilityInfo
  enrichedAt: string
  source: 'perplexity' | 'drug_database' | 'manual'
}
```

## Caching Strategy

### Cache Implementation

- **LRU Cache**: Least Recently Used eviction policy
- **TTL**: 24-hour time-to-live for cache entries
- **Automatic Cleanup**: Hourly cleanup of expired entries
- **Cache Key**: Based on medication name, generic name, and strength

### Cache Management

```typescript
// Clear cache
medicationEnrichmentService.clearCache()

// Get cache statistics
const stats = medicationEnrichmentService.getCacheStats()
console.log(`Cache size: ${stats.size}/${stats.maxSize}`)

// Get rate limit statistics
const rateLimitStats = medicationEnrichmentService.getRateLimitStats()
console.log(`Rate limit: ${rateLimitStats.currentRequests}/${rateLimitStats.maxRequests}`)
```

## Rate Limiting

### Implementation

- **Window-based**: 1-minute sliding window
- **Request Limit**: 50 requests per minute
- **Automatic Retry**: Waits for window reset when limit exceeded
- **Graceful Degradation**: Continues processing when rate limited

### Rate Limit Configuration

```typescript
interface RateLimitConfig {
  maxRequests: number      // 50 requests
  windowMs: number         // 60 seconds
  currentRequests: number  // Current count
  resetTime: number        // Window reset timestamp
}
```

## Error Handling

### Error Types

1. **Network Errors**: Connection failures, timeouts
2. **API Errors**: Perplexity API failures
3. **Parsing Errors**: Invalid JSON responses
4. **Rate Limit Errors**: Too many requests
5. **Cache Errors**: Cache corruption or overflow

### Error Recovery

```typescript
// Graceful error handling
const result = await medicationEnrichmentService.enrichMedication(request)

if (!result.success) {
  console.error('Enrichment failed:', result.error)
  
  // Fallback to basic medication data
  return {
    ...medication,
    enrichedData: null,
    enrichmentError: result.error
  }
}
```

## Testing

### Running Tests

```bash
# Run all enrichment service tests
npm run test medicationEnrichmentService

# Run specific test suite
npm run test -- --grep "Cache Management"

# Run with coverage
npm run test:coverage medicationEnrichmentService
```

### Test Coverage

The test suite covers:

- ✅ API integration and error handling
- ✅ Cache management and expiration
- ✅ Rate limiting and throttling
- ✅ Data parsing and validation
- ✅ Prompt building and formatting
- ✅ Resource management and cleanup
- ✅ Edge cases and error scenarios

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**: Multiple enrichment types processed concurrently
2. **Intelligent Caching**: Reduces API calls for repeated requests
3. **Rate Limiting**: Prevents API quota exhaustion
4. **Error Recovery**: Graceful degradation on failures
5. **Resource Management**: Automatic cleanup of expired data

### Monitoring

```typescript
// Monitor service performance
const cacheStats = medicationEnrichmentService.getCacheStats()
const rateLimitStats = medicationEnrichmentService.getRateLimitStats()

console.log('Performance Metrics:', {
  cacheHitRate: cacheStats.size / cacheStats.maxSize,
  rateLimitUsage: rateLimitStats.currentRequests / rateLimitStats.maxRequests,
  cacheEfficiency: cacheStats.size > 0 ? 'Good' : 'Poor'
})
```

## Security Considerations

### API Security

- **Backend Proxy**: All Perplexity API calls go through backend
- **Authentication**: Requires user authentication
- **Rate Limiting**: Prevents abuse and quota exhaustion
- **Input Validation**: Sanitizes medication names and parameters
- **Error Sanitization**: Prevents information leakage

### Data Privacy

- **HIPAA Compliance**: Follows healthcare data privacy standards
- **Audit Logging**: Logs all enrichment requests
- **Data Retention**: Cache expires after 24 hours
- **Secure Storage**: Enriched data stored securely

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - Check rate limit statistics
   - Implement exponential backoff
   - Consider increasing rate limit window

2. **Cache Performance**
   - Monitor cache hit rates
   - Adjust cache TTL if needed
   - Clear cache if corrupted

3. **Parsing Errors**
   - Check Perplexity API response format
   - Validate JSON structure
   - Implement fallback parsing

4. **Network Issues**
   - Check backend connectivity
   - Verify Perplexity API status
   - Implement retry logic

### Debug Mode

```typescript
// Enable debug logging
const DEBUG_MODE = true

if (DEBUG_MODE) {
  console.log('Enrichment Request:', request)
  console.log('Cache Stats:', medicationEnrichmentService.getCacheStats())
  console.log('Rate Limit Stats:', medicationEnrichmentService.getRateLimitStats())
}
```

## Future Enhancements

### Planned Features

1. **Offline Mode**: Cache-based enrichment when offline
2. **Batch Processing**: Optimized bulk enrichment
3. **Custom Prompts**: User-defined enrichment queries
4. **Multi-language**: Support for Afrikaans responses
5. **Advanced Caching**: Redis-based distributed caching
6. **Analytics**: Enrichment usage and performance metrics

### Integration Opportunities

1. **Drug Database**: Integration with local drug databases
2. **Pharmacy APIs**: Real-time availability and pricing
3. **Insurance APIs**: Coverage and cost information
4. **Clinical Decision Support**: Integration with CDS systems
5. **Patient Education**: Educational content enrichment

## Support

For issues or questions about the Medication Enrichment Service:

1. Check the troubleshooting section above
2. Review the test suite for usage examples
3. Monitor performance metrics and logs
4. Contact the development team for assistance

---

**Note**: This service requires a valid Perplexity API key and backend proxy implementation for production use. 