# Production Configuration Setup Guide

This guide explains how to configure and use the production settings for MedGuard SA.

## Overview

The production configuration (`production.ts`) provides comprehensive settings for:

1. **Google Cloud Vision API** - Primary OCR processing
2. **Azure Computer Vision** - Backup OCR service
3. **Perplexity API** - AI-powered medication analysis with rate limiting
4. **Secure Image Storage** - Encrypted prescription photo storage
5. **HIPAA-compliant Logging** - Audit trails and compliance
6. **Medication Database Connections** - Drug validation and interactions
7. **South African Pharmacy APIs** - Local pharmacy integrations
8. **Monitoring & Alerting** - Performance and error tracking
9. **Backup & Disaster Recovery** - Data protection and business continuity
10. **Performance Optimization** - Caching, compression, and optimization

## Quick Start

### 1. Environment Setup

Copy the example environment file and configure your production values:

```bash
cp env.production.example .env.production
```

### 2. Import Configuration

```typescript
import productionConfig from '@/config/production'

// Or import specific configurations
import { 
  googleCloudVisionConfig, 
  perplexityApiConfig,
  monitoringConfig 
} from '@/config/production'
```

### 3. Validate Configuration

```typescript
import { validateProductionConfig, getProductionConfigSummary } from '@/config/production'

// Validate all settings
const validation = validateProductionConfig()
if (!validation.isValid) {
  console.error('Configuration errors:', validation.errors)
}

// Get configuration summary
const summary = getProductionConfigSummary()
console.log('Services configured:', summary.services)
```

## Configuration Details

### 1. Google Cloud Vision API

**Purpose**: Primary OCR processing for prescription images

**Setup**:
1. Create a Google Cloud project
2. Enable the Vision API
3. Create service account credentials
4. Set environment variables:
   - `VITE_GOOGLE_CLOUD_VISION_API_KEY`
   - `VITE_GOOGLE_CLOUD_PROJECT_ID`
   - `VITE_GOOGLE_CLOUD_REGION`

**Features**:
- South African language support (English & Afrikaans)
- Rate limiting and quota management
- Automatic fallback to Azure
- Performance optimization with caching

### 2. Azure Computer Vision (Backup)

**Purpose**: Backup OCR service when Google Cloud Vision is unavailable

**Setup**:
1. Create Azure Cognitive Services resource
2. Get endpoint and API key
3. Set environment variables:
   - `VITE_AZURE_COMPUTER_VISION_ENDPOINT`
   - `VITE_AZURE_COMPUTER_VISION_API_KEY`
   - `VITE_AZURE_REGION`

**Features**:
- Automatic failover from Google Cloud Vision
- Lower rate limits but reliable backup
- Document orientation detection

### 3. Perplexity API

**Purpose**: AI-powered medication analysis and drug information

**Setup**:
1. Sign up for Perplexity API
2. Get API key
3. Set environment variable: `VITE_PERPLEXITY_API_KEY`

**Features**:
- Rate limiting (50 req/min, 1000 req/hour)
- Intelligent caching (1 hour TTL)
- Medication-specific prompts
- Drug interaction analysis

### 4. Secure Image Storage

**Purpose**: Encrypted storage for prescription photos

**Setup**:
1. Generate 32-character encryption key
2. Configure cloud storage bucket
3. Set environment variables:
   - `VITE_STORAGE_ENCRYPTION_KEY`
   - `VITE_STORAGE_BUCKET_NAME`

**Features**:
- AES-256-GCM encryption
- Automatic key rotation (30 days)
- GDPR-compliant European storage
- Virus scanning and metadata extraction

### 5. HIPAA-compliant Logging

**Purpose**: Audit trails and compliance logging

**Features**:
- 7-year log retention (HIPAA requirement)
- PHI data masking
- Structured JSON logging
- Security and access event tracking
- Automatic alerting for security events

### 6. Medication Database Connections

**Purpose**: Drug validation and interaction checking

**Setup**:
1. Configure PostgreSQL database
2. Set up DrugBank API access
3. Configure SAHPRA integration
4. Set environment variables:
   - `VITE_MEDICATION_DB_URL`
   - `VITE_DRUGBANK_API_KEY`
   - `VITE_SAHPRA_API_KEY`

**Features**:
- Real-time drug validation
- South African medication database
- Multiple fallback databases
- Fuzzy matching for drug names

### 7. South African Pharmacy APIs

**Purpose**: Local pharmacy integrations and verification

**Setup**:
1. Register with Pharmacy Council of South Africa
2. Configure regional pharmacy networks
3. Set environment variables:
   - `VITE_PHARMACY_API_KEY`
   - `VITE_GAUTENG_PHARMACY_API_KEY`
   - `VITE_WC_PHARMACY_API_KEY`
   - `VITE_KZN_PHARMACY_API_KEY`

**Features**:
- License verification
- Drug availability checking
- Pricing information
- Generic substitution support

### 8. Monitoring & Alerting

**Purpose**: Performance monitoring and error tracking

**Setup**:
1. Configure monitoring endpoint
2. Set up alert webhooks
3. Set environment variables:
   - `VITE_MONITORING_ENDPOINT`
   - `VITE_ALERT_WEBHOOK_URL`

**Features**:
- Real-time performance monitoring
- Automatic health checks
- Multi-level alerting (email, SMS, Slack)
- Custom dashboards and reports

### 9. Backup & Disaster Recovery

**Purpose**: Data protection and business continuity

**Setup**:
1. Configure backup endpoints
2. Set up disaster recovery systems
3. Set environment variables:
   - `VITE_BACKUP_ENDPOINT`
   - `VITE_DISASTER_RECOVERY_ENDPOINT`

**Features**:
- Hourly data backups
- 1-hour RTO (Recovery Time Objective)
- 5-minute RPO (Recovery Point Objective)
- Geographic redundancy across regions

### 10. Performance Optimization

**Purpose**: Application performance and user experience

**Features**:
- Multi-level caching (browser, application, CDN)
- Image optimization and compression
- Database connection pooling
- Code splitting and tree shaking
- API batching and pagination

## Usage Examples

### OCR Processing

```typescript
import { googleCloudVisionConfig } from '@/config/production'

// Use Google Cloud Vision for OCR
const ocrResult = await processImageWithGoogleVision(imageFile, {
  languageHints: googleCloudVisionConfig.ocr.languageHints,
  confidenceThreshold: googleCloudVisionConfig.ocr.confidenceThreshold
})
```

### Medication Analysis

```typescript
import { perplexityApiConfig } from '@/config/production'

// Analyze drug interactions
const interactionPrompt = perplexityApiConfig.medicationPrompts.drugInteraction
  .replace('{drug1}', 'Aspirin')
  .replace('{drug2}', 'Warfarin')

const analysis = await queryPerplexityAPI(interactionPrompt, {
  model: perplexityApiConfig.models.default,
  maxTokens: perplexityApiConfig.models.maxTokens
})
```

### Secure Storage

```typescript
import { secureImageStorageConfig } from '@/config/production'

// Store prescription image securely
const encryptedImage = await encryptImage(imageFile, {
  algorithm: secureImageStorageConfig.encryption.algorithm,
  key: secureImageStorageConfig.encryption.key
})

await uploadToSecureStorage(encryptedImage, {
  bucket: secureImageStorageConfig.storage.bucketName,
  enableVersioning: secureImageStorageConfig.storage.enableVersioning
})
```

### Monitoring

```typescript
import { monitoringConfig } from '@/config/production'

// Track prescription processing
await trackPrescriptionProcessing({
  prescriptionId: 'prescription-123',
  processingTime: 2500,
  success: true,
  endpoint: monitoringConfig.endpoint
})

// Send alert for failures
if (failedPrescriptions > monitoringConfig.alerting.thresholds.failedPrescriptions) {
  await sendAlert({
    type: 'prescription_failure',
    message: 'High prescription failure rate detected',
    webhookUrl: monitoringConfig.alerting.webhookUrl
  })
}
```

## Security Considerations

1. **Environment Variables**: Never commit actual API keys to version control
2. **Encryption Keys**: Use strong, randomly generated encryption keys
3. **Access Control**: Implement proper IAM roles and permissions
4. **Network Security**: Use HTTPS for all API communications
5. **Data Retention**: Follow HIPAA requirements for data retention
6. **Audit Logging**: Enable comprehensive audit trails
7. **Regular Updates**: Keep dependencies and configurations updated

## Troubleshooting

### Common Issues

1. **Missing Environment Variables**
   ```bash
   # Check if all required variables are set
   npm run validate:config
   ```

2. **API Rate Limiting**
   ```typescript
   // Check rate limit status
   const rateLimitStatus = await checkRateLimit('perplexity')
   if (rateLimitStatus.exceeded) {
     // Implement exponential backoff
     await delay(rateLimitStatus.retryAfter)
   }
   ```

3. **OCR Failures**
   ```typescript
   // Check OCR provider status
   const providers = getAvailableOCRProviders()
   if (providers.length === 0) {
     throw new Error('No OCR providers available')
   }
   ```

### Validation Commands

```bash
# Validate production configuration
npm run validate:production

# Check environment variables
npm run check:env

# Test API connections
npm run test:apis
```

## Support

For issues with production configuration:

1. Check the validation output for errors and warnings
2. Verify all environment variables are correctly set
3. Test API connections individually
4. Review monitoring dashboards for performance issues
5. Check audit logs for security events

## Compliance Notes

- **HIPAA**: All logging and data handling follows HIPAA requirements
- **GDPR**: Data storage in European regions for GDPR compliance
- **POPIA**: South African data protection compliance
- **SAHPRA**: South African health product regulatory compliance 