# Stock Deduction Implementation

## Overview

This document describes the implementation of automatic stock deduction when medications are marked as taken in the MedGuard SA system. This is a critical feature that ensures accurate medication inventory tracking.

## What Was Implemented

### 1. Backend Stock Deduction Logic

**File: `medguard_backend/medications/views.py`**

The `mark_taken` action in `MedicationScheduleViewSet` has been enhanced to:

- **Deduct stock automatically**: When a medication is marked as taken, the system automatically reduces the medication's `pill_count` by the dosage amount
- **Create stock transactions**: Each dose taken creates a `StockTransaction` record with type `DOSE_TAKEN`
- **Check stock availability**: Prevents marking as taken if insufficient stock is available
- **Generate low stock alerts**: Automatically creates `StockAlert` records when stock falls below the threshold
- **Use database transactions**: Ensures data consistency with atomic operations

### 2. Frontend Response Handling

**File: `medguard-web/src/services/medicationApi.ts`**

The `markAsTaken` method has been updated to:

- **Handle new response format**: Returns detailed information about stock changes
- **Provide user feedback**: Includes stock deducted, remaining stock, and low stock alerts
- **Handle errors gracefully**: Specifically handles insufficient stock errors
- **Maintain backward compatibility**: Still works with mock data for development

### 3. Enhanced User Interface

**File: `medguard-web/src/components/medication/MedicationDashboard.vue`**

The dashboard now:

- **Shows stock information**: Displays stock deducted and remaining stock in console logs
- **Handles low stock alerts**: Logs when low stock alerts are triggered
- **Provides error feedback**: Shows specific messages for insufficient stock scenarios

### 4. Internationalization Support

**Files: `medguard-web/src/locales/en.json` and `medguard-web/src/locales/af.json`**

Added new translation keys for:

- Stock deduction messages
- Insufficient stock warnings
- Low stock alerts
- Success confirmations

## How It Works

### 1. Mark as Taken Process

When a user clicks "Mark as Taken":

1. **Frontend** calls `medicationApi.markAsTaken(scheduleId)`
2. **Backend** receives the request at `/api/medications/schedules/{id}/mark_taken/`
3. **Stock Check**: System verifies sufficient stock is available
4. **Medication Log**: Creates or updates a `MedicationLog` entry with status `TAKEN`
5. **Stock Transaction**: Creates a `StockTransaction` with type `DOSE_TAKEN` and negative quantity
6. **Stock Update**: Automatically reduces the medication's `pill_count`
7. **Alert Check**: If stock falls below threshold, creates a `StockAlert`
8. **Response**: Returns success/failure with detailed stock information

### 2. Stock Transaction Details

Each stock transaction includes:

- **Transaction Type**: `DOSE_TAKEN`
- **Quantity**: Negative value (e.g., -1 for 1 pill)
- **Stock Before/After**: Tracks stock levels before and after the transaction
- **Reference**: Links to the specific schedule and date
- **Notes**: Descriptive information about the dose taken

### 3. Low Stock Alert System

When stock falls below the `low_stock_threshold`:

- **Alert Type**: `LOW_STOCK` or `OUT_OF_STOCK` based on current level
- **Priority**: `HIGH` for low stock, `CRITICAL` for out of stock
- **Status**: `ACTIVE` until resolved
- **Prevention**: Only creates one active alert per medication

## Error Handling

### 1. Insufficient Stock

If a user tries to mark a medication as taken but there's insufficient stock:

- **HTTP 400**: Returns a 400 Bad Request status
- **Error Message**: "Only X pills available, but Y required"
- **Current Stock**: Includes current stock level in response
- **Frontend Handling**: Shows appropriate error message to user

### 2. Database Consistency

- **Atomic Transactions**: All operations wrapped in database transactions
- **Rollback**: If any step fails, all changes are rolled back
- **Data Integrity**: Ensures stock levels remain accurate

## Testing

### Test Script

**File: `medguard_backend/test_stock_deduction.py`**

A comprehensive test script that verifies:

1. **Stock Deduction**: Confirms stock is correctly reduced when marking as taken
2. **Transaction Creation**: Verifies stock transactions are created
3. **Alert Generation**: Tests low stock alert creation
4. **Insufficient Stock**: Validates error handling for insufficient stock
5. **Data Consistency**: Ensures all related data is updated correctly

### Running Tests

```bash
cd medguard_backend
python test_stock_deduction.py
```

## API Response Format

### Success Response

```json
{
  "message": "Medication marked as taken successfully",
  "schedule": { /* schedule data */ },
  "stock_deducted": 1,
  "remaining_stock": 49,
  "low_stock_alert": false
}
```

### Error Response (Insufficient Stock)

```json
{
  "error": "Insufficient stock",
  "message": "Only 0 pills available, but 1 required",
  "current_stock": 0,
  "required": 1
}
```

## Benefits

### 1. Accurate Inventory Tracking

- **Real-time Updates**: Stock levels are updated immediately when medications are taken
- **Audit Trail**: Complete history of all stock movements through transactions
- **Prevents Overdosing**: Cannot mark as taken if insufficient stock exists

### 2. Proactive Alerts

- **Low Stock Warnings**: Users are notified before stock runs out
- **Critical Alerts**: Immediate notifications when stock is depleted
- **Preventive Action**: Allows time to refill prescriptions

### 3. Data Integrity

- **Consistent State**: Stock levels always match actual usage
- **Transaction History**: Complete audit trail for compliance
- **Error Prevention**: Prevents impossible scenarios (negative stock)

## Future Enhancements

### 1. User Interface Improvements

- **Toast Notifications**: Show stock updates in real-time
- **Stock Indicators**: Visual indicators for low stock medications
- **Refill Reminders**: Automatic reminders when stock is low

### 2. Advanced Features

- **Batch Processing**: Handle multiple medications at once
- **Partial Doses**: Support for fractional dosage amounts
- **Stock Predictions**: AI-powered stock forecasting
- **Auto-refill**: Integration with pharmacy systems for automatic refills

### 3. Analytics

- **Usage Patterns**: Track medication consumption trends
- **Adherence Metrics**: Correlate stock usage with adherence
- **Cost Analysis**: Track medication costs and usage

## Conclusion

The stock deduction implementation provides a robust foundation for accurate medication inventory management. It ensures that:

- Stock levels are always accurate and up-to-date
- Users are proactively warned about low stock situations
- The system prevents impossible scenarios (negative stock)
- Complete audit trails are maintained for compliance
- The user experience is enhanced with meaningful feedback

This implementation addresses one of the most critical aspects of medication management systems and provides a solid foundation for future enhancements. 