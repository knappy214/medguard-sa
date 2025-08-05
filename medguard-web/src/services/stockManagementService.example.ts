/**
 * Stock Management Service Usage Examples
 * 
 * This file demonstrates how to use the comprehensive stock management service
 * for various medication management scenarios in the MedGuard SA application.
 */

import stockManagementService from './stockManagementService'
import type { 
  StockCalculation, 
  InsulinPenCalculation, 
  LiquidMedicationCalculation,
  WasteTracking,
  PharmacyComparison,
  EmergencyStockAlert,
  StockReport
} from './stockManagementService'

/**
 * Example 1: Basic Stock Level Calculation
 * Calculates precise stock levels for any medication
 */
export async function exampleStockCalculation() {
  try {
    const medicationId = 'med-123'
    const stockCalculation: StockCalculation = await stockManagementService.calculateStockLevels(medicationId)
    
    console.log('Stock Calculation Results:')
    console.log(`Current Stock: ${stockCalculation.currentStock}`)
    console.log(`Daily Usage: ${stockCalculation.dailyUsage}`)
    console.log(`Days Until Stockout: ${stockCalculation.daysUntilStockout}`)
    console.log(`Recommended Order Date: ${stockCalculation.recommendedOrderDate}`)
    console.log(`Confidence: ${(stockCalculation.confidence * 100).toFixed(1)}%`)
    
    return stockCalculation
  } catch (error) {
    console.error('Error calculating stock levels:', error)
    throw error
  }
}

/**
 * Example 2: Insulin Pen Stock Management
 * Handles complex calculations for insulin pens with units and partial pens
 */
export async function exampleInsulinPenManagement() {
  try {
    const medicationId = 'insulin-456'
    const insulinCalculation: InsulinPenCalculation = await stockManagementService.calculateInsulinPenStock(medicationId)
    
    console.log('Insulin Pen Stock Analysis:')
    console.log(`Total Pens: ${insulinCalculation.totalPens}`)
    console.log(`Units Per Pen: ${insulinCalculation.unitsPerPen}`)
    console.log(`Total Units Available: ${insulinCalculation.totalUnits}`)
    console.log(`Daily Units Required: ${insulinCalculation.dailyUnits}`)
    console.log(`Days Remaining: ${insulinCalculation.daysRemaining}`)
    console.log(`Partial Pen Units: ${insulinCalculation.partialPenUnits}`)
    
    // Alert if running low
    if (insulinCalculation.daysRemaining <= 7) {
      console.warn('⚠️ INSULIN RUNNING LOW - Contact pharmacy immediately!')
    }
    
    return insulinCalculation
  } catch (error) {
    console.error('Error calculating insulin pen stock:', error)
    throw error
  }
}

/**
 * Example 3: Liquid Medication Management
 * Handles volume-based calculations for liquid medications
 */
export async function exampleLiquidMedicationManagement() {
  try {
    const medicationId = 'liquid-789'
    const liquidCalculation: LiquidMedicationCalculation = await stockManagementService.calculateLiquidMedicationStock(medicationId)
    
    console.log('Liquid Medication Stock Analysis:')
    console.log(`Total Volume: ${liquidCalculation.totalVolume} ${liquidCalculation.volumeUnit}`)
    console.log(`Daily Volume: ${liquidCalculation.dailyVolume} ${liquidCalculation.volumeUnit}`)
    console.log(`Concentration: ${liquidCalculation.concentration} ${liquidCalculation.concentrationUnit}`)
    console.log(`Days Remaining: ${liquidCalculation.daysRemaining}`)
    console.log(`Remaining Volume: ${liquidCalculation.remainingVolume} ${liquidCalculation.volumeUnit}`)
    
    return liquidCalculation
  } catch (error) {
    console.error('Error calculating liquid medication stock:', error)
    throw error
  }
}

/**
 * Example 4: Waste Tracking and Adherence
 * Tracks medication waste and analyzes adherence patterns
 */
export async function exampleWasteAndAdherenceTracking() {
  try {
    // Track medication waste
    const wasteData = {
      medicationId: 'med-123',
      medication: { id: 'med-123', name: 'Aspirin', dosage: '100mg', frequency: 'Once daily', time: '08:00', stock: 5, pill_count: 5, minStock: 10, instructions: 'Take with food', category: 'Pain Relief', isActive: true, createdAt: '', updatedAt: '' },
      wastedAmount: 5,
      wasteReason: 'expired' as const,
      cost: 12.50,
      notes: 'Medication expired before use'
    }
    
    const wasteTracking = await stockManagementService.trackWaste(wasteData)
    console.log('Waste tracked:', wasteTracking)
    
    // Get adherence patterns
    const adherencePatterns = await stockManagementService.getAdherencePatterns('med-123')
    console.log('Adherence patterns:', adherencePatterns)
    
    // Get waste history
    const wasteHistory = await stockManagementService.getWasteHistory('med-123')
    console.log('Waste history:', wasteHistory)
    
    return { wasteTracking, adherencePatterns, wasteHistory }
  } catch (error) {
    console.error('Error tracking waste and adherence:', error)
    throw error
  }
}

/**
 * Example 5: South African Pharmacy Price Comparison
 * Compares prices across major SA pharmacy chains
 */
export async function examplePharmacyPriceComparison() {
  try {
    const medicationId = 'med-123'
    const pharmacyComparison: PharmacyComparison = await stockManagementService.getPharmacyPriceComparison(medicationId)
    
    console.log('Pharmacy Price Comparison:')
    console.log(`Best Price: R${pharmacyComparison.bestPrice} at ${pharmacyComparison.bestPharmacy}`)
    console.log(`Average Price: R${pharmacyComparison.averagePrice}`)
    console.log(`Price Range: R${pharmacyComparison.priceRange.min} - R${pharmacyComparison.priceRange.max}`)
    console.log(`Availability: ${pharmacyComparison.availability}`)
    
    console.log('\nAvailable Pharmacies:')
    pharmacyComparison.pharmacies.forEach(pharmacy => {
      console.log(`- ${pharmacy.name}: R${pharmacy.price} (${pharmacy.distance}km away)`)
    })
    
    return pharmacyComparison
  } catch (error) {
    console.error('Error getting pharmacy comparison:', error)
    throw error
  }
}

/**
 * Example 6: Prescription Renewal Management
 * Handles prescription repeats and renewal tracking
 */
export async function examplePrescriptionRenewal() {
  try {
    // Get all prescription repeats
    const prescriptionRepeats = await stockManagementService.getPrescriptionRepeats()
    console.log('Prescription repeats:', prescriptionRepeats)
    
    // Create a new renewal
    const renewalData = {
      refillsRemaining: 3,
      autoRenewal: true
    }
    
    const newRenewal = await stockManagementService.createPrescriptionRenewal('prescription-123', renewalData)
    console.log('New renewal created:', newRenewal)
    
    // Set auto-renewal
    const autoRenewalSet = await stockManagementService.setAutoRenewal('prescription-123', true)
    console.log('Auto-renewal set:', autoRenewalSet)
    
    return { prescriptionRepeats, newRenewal, autoRenewalSet }
  } catch (error) {
    console.error('Error managing prescription renewals:', error)
    throw error
  }
}

/**
 * Example 7: Batch Expiration Monitoring
 * Monitors medication batch expiration dates
 */
export async function exampleBatchExpirationMonitoring() {
  try {
    // Get all batch expirations
    const batchExpirations = await stockManagementService.getBatchExpirations()
    console.log('Batch expirations:', batchExpirations)
    
    // Set expiration alert for specific medication
    const alertSet = await stockManagementService.setExpirationAlert('med-123', 30)
    console.log('Expiration alert set:', alertSet)
    
    // Filter critical expirations
    const criticalExpirations = batchExpirations.filter(batch => 
      batch.status === 'critical' || batch.status === 'expired'
    )
    
    if (criticalExpirations.length > 0) {
      console.warn('⚠️ CRITICAL: Medications expiring soon!')
      criticalExpirations.forEach(batch => {
        console.warn(`- ${batch.medication.name}: ${batch.daysUntilExpiration} days until expiration`)
      })
    }
    
    return { batchExpirations, alertSet, criticalExpirations }
  } catch (error) {
    console.error('Error monitoring batch expirations:', error)
    throw error
  }
}

/**
 * Example 8: Stock Report Generation
 * Generates comprehensive reports for healthcare providers
 */
export async function exampleStockReportGeneration() {
  try {
    // Generate monthly stock report
    const monthlyReport: StockReport = await stockManagementService.generateStockReport('monthly')
    console.log('Monthly Stock Report:')
    console.log(`Total Medications: ${monthlyReport.summary.totalMedications}`)
    console.log(`Low Stock Items: ${monthlyReport.summary.lowStockItems}`)
    console.log(`Out of Stock Items: ${monthlyReport.summary.outOfStockItems}`)
    console.log(`Total Value: R${monthlyReport.summary.totalValue}`)
    console.log(`Waste Value: R${monthlyReport.summary.wasteValue}`)
    
    console.log('\nRecommendations:')
    monthlyReport.recommendations.forEach(rec => console.log(`- ${rec}`))
    
    // Export report as PDF
    const pdfBlob = await stockManagementService.exportStockReport(monthlyReport.reportId, 'pdf')
    console.log('PDF report generated:', pdfBlob.size, 'bytes')
    
    return { monthlyReport, pdfBlob }
  } catch (error) {
    console.error('Error generating stock report:', error)
    throw error
  }
}

/**
 * Example 9: Emergency Stock Alerts
 * Handles critical medication alerts
 */
export async function exampleEmergencyStockAlerts() {
  try {
    // Get emergency stock alerts
    const emergencyAlerts: EmergencyStockAlert[] = await stockManagementService.getEmergencyStockAlerts()
    console.log('Emergency stock alerts:', emergencyAlerts)
    
    // Process each emergency alert
    for (const alert of emergencyAlerts) {
      console.log(`🚨 EMERGENCY ALERT: ${alert.medication.name}`)
      console.log(`Type: ${alert.alertType}`)
      console.log(`Severity: ${alert.severity}`)
      console.log(`Days Remaining: ${alert.daysRemaining}`)
      console.log(`Action Required: ${alert.actionRequired}`)
      console.log(`Contact Pharmacy: ${alert.contactInfo.pharmacy}`)
      
      // Acknowledge alert
      if (!alert.acknowledged) {
        const acknowledged = await stockManagementService.acknowledgeEmergencyAlert(alert.alertId)
        console.log('Alert acknowledged:', acknowledged)
      }
      
      // Resolve alert if stock has been replenished
      if (alert.daysRemaining > 7) {
        const resolved = await stockManagementService.resolveEmergencyAlert(
          alert.alertId, 
          'Stock replenished - emergency resolved'
        )
        console.log('Alert resolved:', resolved)
      }
    }
    
    return emergencyAlerts
  } catch (error) {
    console.error('Error handling emergency stock alerts:', error)
    throw error
  }
}

/**
 * Example 10: Predictive Analytics
 * Uses predictive analytics for medication refill planning
 */
export async function examplePredictiveAnalytics() {
  try {
    const medicationId = 'med-123'
    
    // Get predictive refill dates
    const predictiveRefill = await stockManagementService.getPredictiveRefillDates(medicationId)
    console.log('Predictive Refill Analysis:')
    console.log(`Predicted Refill Date: ${predictiveRefill.predictedRefillDate}`)
    console.log(`Confidence: ${(predictiveRefill.confidence * 100).toFixed(1)}%`)
    console.log('Factors considered:', predictiveRefill.factors)
    console.log('Alternative dates:', predictiveRefill.alternativeDates)
    
    // Get reorder alerts
    const reorderAlerts = await stockManagementService.getReorderAlerts()
    console.log('Reorder alerts:', reorderAlerts)
    
    // Create new reorder alerts
    const newAlerts = await stockManagementService.createReorderAlerts()
    console.log('New reorder alerts created:', newAlerts)
    
    return { predictiveRefill, reorderAlerts, newAlerts }
  } catch (error) {
    console.error('Error with predictive analytics:', error)
    throw error
  }
}

/**
 * Example 11: Comprehensive Stock Management Dashboard
 * Combines multiple features for a complete dashboard
 */
export async function exampleComprehensiveDashboard() {
  try {
    const medicationId = 'med-123'
    
    // Get all stock-related data
    const [
      stockCalculation,
      predictiveRefill,
      pharmacyComparison,
      batchExpirations,
      emergencyAlerts,
      adherencePatterns
    ] = await Promise.all([
      stockManagementService.calculateStockLevels(medicationId),
      stockManagementService.getPredictiveRefillDates(medicationId),
      stockManagementService.getPharmacyPriceComparison(medicationId),
      stockManagementService.getBatchExpirations(medicationId),
      stockManagementService.getEmergencyStockAlerts(),
      stockManagementService.getAdherencePatterns(medicationId)
    ])
    
    // Create dashboard summary
    const dashboard = {
      stock: {
        current: stockCalculation.currentStock,
        daysUntilStockout: stockCalculation.daysUntilStockout,
        recommendedOrderDate: stockCalculation.recommendedOrderDate,
        confidence: stockCalculation.confidence
      },
      predictive: {
        refillDate: predictiveRefill.predictedRefillDate,
        confidence: predictiveRefill.confidence
      },
      pharmacy: {
        bestPrice: pharmacyComparison.bestPrice,
        bestPharmacy: pharmacyComparison.bestPharmacy,
        availability: pharmacyComparison.availability
      },
      expirations: batchExpirations.filter(b => b.actionRequired),
      emergencies: emergencyAlerts.filter(a => !a.resolved),
      adherence: adherencePatterns[0]?.adherenceRate || 0
    }
    
    console.log('Comprehensive Stock Dashboard:', dashboard)
    
    // Generate alerts based on dashboard data
    const alerts = []
    
    if (dashboard.stock.daysUntilStockout <= 5) {
      alerts.push('🚨 CRITICAL: Stock running very low!')
    }
    
    if (dashboard.emergencies.length > 0) {
      alerts.push('🚨 EMERGENCY: Critical medications need attention!')
    }
    
    if (dashboard.expirations.length > 0) {
      alerts.push('⚠️ WARNING: Medications expiring soon!')
    }
    
    if (dashboard.adherence < 0.8) {
      alerts.push('📊 ADHERENCE: Medication adherence below 80%')
    }
    
    console.log('Active Alerts:', alerts)
    
    return { dashboard, alerts }
  } catch (error) {
    console.error('Error creating comprehensive dashboard:', error)
    throw error
  }
}

// Export all examples for easy access
export const stockManagementExamples = {
  exampleStockCalculation,
  exampleInsulinPenManagement,
  exampleLiquidMedicationManagement,
  exampleWasteAndAdherenceTracking,
  examplePharmacyPriceComparison,
  examplePrescriptionRenewal,
  exampleBatchExpirationMonitoring,
  exampleStockReportGeneration,
  exampleEmergencyStockAlerts,
  examplePredictiveAnalytics,
  exampleComprehensiveDashboard
} 