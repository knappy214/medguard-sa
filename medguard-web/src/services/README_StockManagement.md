# Stock Management Service

## Overview

The Stock Management Service is a comprehensive solution for managing medication inventory in the MedGuard SA application. It provides precise stock calculations, predictive analytics, and automated alerts to ensure patients never run out of critical medications.

## Features

### 1. Precise Stock Level Calculations
- **Function**: `calculateStockLevels(medicationId: string)`
- **Purpose**: Calculates exact stock levels based on prescription quantities and frequencies
- **Returns**: `StockCalculation` with current stock, usage rates, and predictions

```typescript
const stockCalculation = await stockManagementService.calculateStockLevels('med-123')
console.log(`Days until stockout: ${stockCalculation.daysUntilStockout}`)
console.log(`Recommended order date: ${stockCalculation.recommendedOrderDate}`)
```

### 2. Predictive Analytics for Refill Dates
- **Function**: `getPredictiveRefillDates(medicationId: string)`
- **Purpose**: Uses machine learning to predict optimal refill dates
- **Returns**: Predicted dates with confidence scores and alternative scenarios

```typescript
const prediction = await stockManagementService.getPredictiveRefillDates('med-123')
console.log(`Predicted refill: ${prediction.predictedRefillDate}`)
console.log(`Confidence: ${prediction.confidence * 100}%`)
```

### 3. Complex Medication Calculations

#### Insulin Pen Management
- **Function**: `calculateInsulinPenStock(medicationId: string)`
- **Purpose**: Handles insulin pen units, partial pens, and refill planning
- **Returns**: `InsulinPenCalculation` with detailed pen and unit analysis

```typescript
const insulinCalc = await stockManagementService.calculateInsulinPenStock('insulin-456')
console.log(`Total units: ${insulinCalc.totalUnits}`)
console.log(`Days remaining: ${insulinCalc.daysRemaining}`)
```

#### Liquid Medication Management
- **Function**: `calculateLiquidMedicationStock(medicationId: string)`
- **Purpose**: Manages volume-based medications with concentration tracking
- **Returns**: `LiquidMedicationCalculation` with volume and concentration data

```typescript
const liquidCalc = await stockManagementService.calculateLiquidMedicationStock('liquid-789')
console.log(`Remaining volume: ${liquidCalc.remainingVolume} ${liquidCalc.volumeUnit}`)
```

### 4. Automatic Reorder Alerts
- **Functions**: `createReorderAlerts()`, `getReorderAlerts()`
- **Purpose**: Creates alerts 5 working days before stock depletion
- **Features**: 
  - Automatic urgency calculation
  - Recommended order quantities
  - Integration with pharmacy systems

```typescript
const alerts = await stockManagementService.getReorderAlerts()
alerts.forEach(alert => {
  console.log(`${alert.medication.name}: ${alert.daysUntilStockout} days remaining`)
})
```

### 5. Waste Tracking and Adherence Patterns
- **Functions**: `trackWaste()`, `getWasteHistory()`, `getAdherencePatterns()`
- **Purpose**: Monitors medication waste and analyzes adherence patterns
- **Features**:
  - Waste categorization (expired, damaged, allergic reaction, etc.)
  - Cost tracking
  - Adherence rate analysis
  - Pattern recognition (time of day, day of week, monthly trends)

```typescript
// Track waste
const wasteData = {
  medicationId: 'med-123',
  wastedAmount: 5,
  wasteReason: 'expired',
  cost: 12.50,
  notes: 'Expired before use'
}
await stockManagementService.trackWaste(wasteData)

// Get adherence patterns
const patterns = await stockManagementService.getAdherencePatterns('med-123')
console.log(`Adherence rate: ${patterns[0]?.adherenceRate * 100}%`)
```

### 6. South African Pharmacy Integration
- **Functions**: `getPharmacyPriceComparison()`, `searchPharmacies()`
- **Purpose**: Compares prices across major SA pharmacy chains
- **Supported Chains**: Clicks, Dis-Chem, Medirite, Alpha Pharm, Medplus, Pharmacy Direct, Netcare Pharmacy, Life Pharmacy, Medicross, Mediclinic Pharmacy

```typescript
const comparison = await stockManagementService.getPharmacyPriceComparison('med-123')
console.log(`Best price: R${comparison.bestPrice} at ${comparison.bestPharmacy}`)
console.log(`Average price: R${comparison.averagePrice}`)
```

### 7. Prescription Renewal Management
- **Functions**: `getPrescriptionRepeats()`, `createPrescriptionRenewal()`, `setAutoRenewal()`
- **Purpose**: Handles prescription repeats and renewal tracking
- **Features**:
  - Automatic renewal reminders
  - Refill tracking
  - Expiry date monitoring
  - Auto-renewal settings

```typescript
const repeats = await stockManagementService.getPrescriptionRepeats()
const renewal = await stockManagementService.createPrescriptionRenewal('prescription-123', {
  refillsRemaining: 3,
  autoRenewal: true
})
```

### 8. Batch Expiration Monitoring
- **Functions**: `getBatchExpirations()`, `setExpirationAlert()`
- **Purpose**: Monitors medication batch expiration dates
- **Features**:
  - Batch number tracking
  - Expiration date alerts
  - Status categorization (safe, warning, critical, expired)
  - Recommended actions

```typescript
const expirations = await stockManagementService.getBatchExpirations()
const criticalExpirations = expirations.filter(batch => batch.status === 'critical')
criticalExpirations.forEach(batch => {
  console.warn(`${batch.medication.name}: ${batch.daysUntilExpiration} days until expiration`)
})
```

### 9. Stock Reports for Healthcare Providers
- **Functions**: `generateStockReport()`, `exportStockReport()`
- **Purpose**: Creates comprehensive reports for healthcare providers
- **Report Types**: daily, weekly, monthly, quarterly, annual
- **Export Formats**: PDF, CSV, Excel
- **Content**: Stock levels, waste analysis, adherence patterns, recommendations

```typescript
const report = await stockManagementService.generateStockReport('monthly')
console.log(`Total medications: ${report.summary.totalMedications}`)
console.log(`Low stock items: ${report.summary.lowStockItems}`)

const pdfBlob = await stockManagementService.exportStockReport(report.reportId, 'pdf')
```

### 10. Emergency Stock Notifications
- **Functions**: `getEmergencyStockAlerts()`, `acknowledgeEmergencyAlert()`, `resolveEmergencyAlert()`
- **Purpose**: Handles critical medication alerts
- **Alert Types**: critical_medication, life_sustaining, controlled_substance, specialty_medication
- **Features**:
  - Severity levels (low, medium, high, critical)
  - Urgency indicators (immediate, within_24h, within_48h, within_week)
  - Contact information for pharmacy, doctor, and emergency services
  - Acknowledgment and resolution tracking

```typescript
const emergencies = await stockManagementService.getEmergencyStockAlerts()
emergencies.forEach(alert => {
  if (alert.urgency === 'immediate') {
    console.error(`🚨 EMERGENCY: ${alert.medication.name} - ${alert.actionRequired}`)
    console.log(`Contact: ${alert.contactInfo.pharmacy}`)
  }
})
```

## Integration with Existing Services

The Stock Management Service integrates seamlessly with existing MedGuard services:

### Authentication Integration
- Uses `authService` for user identification
- Tracks waste and actions by authenticated users
- Maintains audit trails for compliance

### API Integration
- Follows existing API patterns and error handling
- Uses `apiClientEnhanced` for HTTP requests
- Supports both real API and mock data modes

### Type Safety
- Fully typed with TypeScript interfaces
- Extends existing medication types
- Provides comprehensive type definitions for all features

## Error Handling

The service implements robust error handling:

```typescript
try {
  const calculation = await stockManagementService.calculateStockLevels('med-123')
  // Handle success
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.message)
  } else if (error instanceof NetworkError) {
    console.error('Network Error:', error.message)
  } else {
    console.error('Unexpected Error:', error)
  }
}
```

## Mock Data Support

For development and testing, the service provides comprehensive mock data:

- Realistic stock calculations
- Sample pharmacy comparisons
- Mock emergency alerts
- Test adherence patterns
- Example waste tracking

## Usage Examples

See `stockManagementService.example.ts` for comprehensive usage examples covering all features.

## Best Practices

### 1. Error Handling
Always wrap service calls in try-catch blocks and handle errors appropriately.

### 2. Async/Await
Use async/await for all service calls to handle promises properly.

### 3. Type Safety
Leverage TypeScript interfaces for type-safe data handling.

### 4. Batch Operations
Use Promise.all for concurrent operations when possible.

### 5. Regular Monitoring
Set up regular calls to check stock levels and alerts.

## Security Considerations

- All sensitive data is encrypted in transit
- User authentication required for all operations
- Audit trails maintained for compliance
- No PHI stored in client-side code
- Secure API endpoints with proper authorization

## Performance Optimization

- Efficient API calls with proper caching
- Batch operations for multiple medications
- Lazy loading of detailed data
- Optimized database queries
- Minimal network overhead

## Future Enhancements

- Real-time stock updates via WebSocket
- Advanced machine learning for predictions
- Integration with more pharmacy chains
- Mobile push notifications
- Voice assistant integration
- Blockchain for prescription tracking

## Support

For questions or issues with the Stock Management Service:

1. Check the example file for usage patterns
2. Review the TypeScript interfaces for data structures
3. Test with mock data first
4. Ensure proper authentication setup
5. Verify API endpoints are accessible

## Contributing

When contributing to the Stock Management Service:

1. Follow existing code patterns
2. Add comprehensive TypeScript types
3. Include mock data for new features
4. Update documentation
5. Add usage examples
6. Test with both real and mock APIs 