# Enhanced Medication Views Documentation

## Overview

The enhanced medication views provide advanced functionality for batch creation from prescriptions, OCR prescription processing, medication enrichment, and comprehensive audit trails. These features streamline the medication management workflow and improve data accuracy.

## New Endpoints

### 1. Bulk Create from Prescription

**Endpoint:** `POST /api/medications/bulk_create_from_prescription/`

Creates multiple medications from prescription data with schedules, stock transactions, and prescription renewal records.

#### Request Payload

```json
{
  "medications": [
    {
      "name": "Medication Name",
      "generic_name": "Generic Name",
      "strength": "500mg",
      "medication_type": "tablet",
      "prescription_type": "prescription",
      "initial_stock": 30,
      "schedule_data": {
        "timing": "morning",
        "dosage_amount": 1,
        "frequency": "daily",
        "start_date": "2024-01-01",
        "instructions": "Take with food"
      }
    }
  ],
  "patient_id": 1,
  "prescription_number": "RX123456",
  "prescribed_by": "Dr. Smith",
  "prescribed_date": "2024-01-01"
}
```

#### Response

```json
{
  "message": "Successfully created 2 medications",
  "created_medications": [
    {
      "id": 1,
      "name": "Paracetamol",
      "initial_stock": 30
    }
  ],
  "created_schedules": 2,
  "created_transactions": 2,
  "prescription_number": "RX123456",
  "patient": {
    "id": 1,
    "name": "John Doe"
  }
}
```

#### Features

- **Atomic Transactions**: All operations are wrapped in database transactions with automatic rollback on failure
- **Stock Management**: Automatically creates stock transactions for initial stock
- **Schedule Creation**: Creates medication schedules based on provided data
- **Prescription Renewal**: Creates prescription renewal records for tracking
- **Comprehensive Logging**: Logs all creation activities for audit purposes

### 2. Prescription Upload (OCR Processing)

**Endpoint:** `POST /api/medications/prescription_upload/`

Processes OCR-extracted prescription data with medication enrichment and automatic schedule parsing.

#### Request Payload

```json
{
  "ocr_data": {
    "medications": [
      {
        "name": "Extracted medication name",
        "strength": "500mg",
        "instructions": "Take one tablet daily",
        "quantity": 30
      }
    ],
    "prescription_info": {
      "prescription_number": "RX123456",
      "prescribed_by": "Dr. Smith",
      "prescribed_date": "2024-01-01"
    }
  },
  "patient_id": 1,
  "confidence_score": 0.85
}
```

#### Response

```json
{
  "message": "Prescription processed successfully",
  "confidence_score": 0.85,
  "processed_medications": 2,
  "enrichment_results": [...],
  "bulk_creation_result": {
    "created_medications": 2,
    "created_schedules": 2,
    "created_transactions": 2
  }
}
```

#### Features

- **OCR Data Processing**: Handles raw OCR-extracted medication data
- **Medication Enrichment**: Automatically detects medication types and extracts generic names
- **Schedule Parsing**: Parses prescription instructions to create medication schedules
- **Confidence Scoring**: Tracks OCR confidence levels for quality assessment
- **Error Handling**: Gracefully handles OCR processing errors

### 3. Add Stock

**Endpoint:** `POST /api/medications/{id}/add_stock/`

Adds stock to an existing medication and creates detailed stock transactions.

#### Request Payload

```json
{
  "quantity": 30,
  "unit_price": 15.50,
  "batch_number": "BATCH123",
  "expiry_date": "2025-12-31",
  "notes": "Restocked from pharmacy"
}
```

#### Response

```json
{
  "message": "Successfully added 30 units to Test Medication",
  "medication_id": 1,
  "medication_name": "Test Medication",
  "new_stock": 40,
  "transaction_id": 5,
  "batch_number": "BATCH123",
  "expiry_date": "2025-12-31"
}
```

#### Features

- **Stock Tracking**: Maintains detailed stock before/after levels
- **Batch Management**: Tracks batch numbers and expiry dates
- **Financial Tracking**: Records unit prices and total amounts
- **Analytics Update**: Automatically updates stock analytics
- **Audit Trail**: Creates comprehensive transaction records

### 4. Audit Trail

**Endpoint:** `GET /api/medications/{id}/audit_trail/`

Retrieves comprehensive audit trail for medication creation and modifications.

#### Response

```json
{
  "medication": {
    "id": 1,
    "name": "Test Medication",
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-01T10:00:00Z"
  },
  "transactions": [
    {
      "id": 1,
      "type": "purchase",
      "quantity": 30,
      "user": "Admin User",
      "timestamp": "2024-01-01T10:00:00Z",
      "notes": "Initial stock",
      "reference": "STOCK_20240101_100000"
    }
  ],
  "logs": [
    {
      "id": 1,
      "status": "taken",
      "patient": "John Doe",
      "scheduled_time": "2024-01-01T08:00:00Z",
      "actual_time": "2024-01-01T08:15:00Z",
      "dosage_taken": 1,
      "notes": ""
    }
  ],
  "alerts": [
    {
      "id": 1,
      "type": "low_stock",
      "priority": "medium",
      "status": "active",
      "created_by": "Admin User",
      "created_at": "2024-01-01T10:00:00Z",
      "title": "Low Stock Alert",
      "message": "Medication running low"
    }
  ]
}
```

#### Features

- **Comprehensive History**: Tracks all medication-related activities
- **User Attribution**: Links all actions to specific users
- **Timeline View**: Provides chronological activity timeline
- **Multi-Entity Tracking**: Covers transactions, logs, and alerts
- **Detailed Metadata**: Includes timestamps, notes, and references

## Medication Enrichment Features

### Automatic Type Detection

The system automatically detects medication types based on name and strength patterns:

- **Tablets**: Contains "tablet", "tab" in name
- **Capsules**: Contains "capsule", "cap" in name
- **Liquids**: Contains "liquid", "syrup", "suspension" in name
- **Inhalers**: Contains "inhaler", "puff" in name
- **Creams**: Contains "cream", "ointment" in name
- **Drops**: Contains "drops" or "ml" in strength

### Generic Name Extraction

Extracts standard generic names from common medications:

- Paracetamol → Acetaminophen
- Aspirin → Acetylsalicylic acid
- Ibuprofen → Ibuprofen
- Amoxicillin → Amoxicillin
- Omeprazole → Omeprazole
- Metformin → Metformin
- Atorvastatin → Atorvastatin
- Lisinopril → Lisinopril
- Amlodipine → Amlodipine

### Prescription Instruction Parsing

Automatically parses prescription instructions to extract:

- **Dosage Amount**: Number of units to take
- **Frequency**: How often to take (daily, twice_daily, etc.)
- **Timing**: When to take (morning, noon, night, custom)
- **Instructions**: Special instructions or notes

## Error Handling and Validation

### Bulk Creation Validation

- **Required Fields**: Validates all required medication fields
- **Patient Validation**: Ensures patient exists and is of correct type
- **Stock Validation**: Validates initial stock quantities
- **Schedule Validation**: Validates schedule data format
- **Rollback on Failure**: Automatically rolls back all changes if any medication fails

### OCR Processing Validation

- **Data Format**: Validates OCR data structure
- **Confidence Scoring**: Tracks and reports OCR confidence levels
- **Enrichment Errors**: Gracefully handles enrichment failures
- **Partial Processing**: Continues processing even if some medications fail

### Stock Management Validation

- **Quantity Validation**: Ensures positive quantities
- **Date Validation**: Validates expiry date formats
- **Price Validation**: Validates unit price formats
- **Batch Tracking**: Validates batch number formats

## Security and Permissions

### Authentication Requirements

All endpoints require authentication with appropriate user permissions:

- **Staff/Admin**: Full access to all endpoints
- **Caregiver**: Limited access based on patient relationships
- **Patient**: Read-only access to own medications

### Data Validation

- **Input Sanitization**: All input data is sanitized and validated
- **SQL Injection Protection**: Uses Django ORM for safe database operations
- **XSS Protection**: Output is properly escaped
- **CSRF Protection**: All POST requests require CSRF tokens

## Performance Considerations

### Database Optimization

- **Select Related**: Uses `select_related` and `prefetch_related` for efficient queries
- **Bulk Operations**: Uses bulk creation where possible
- **Indexing**: Leverages existing database indexes
- **Transaction Management**: Uses atomic transactions for data consistency

### Caching Strategy

- **Analytics Caching**: Caches stock analytics calculations
- **Audit Trail Caching**: Caches audit trail data for frequently accessed medications
- **Enrichment Caching**: Caches medication enrichment results

### Memory Management

- **Lazy Loading**: Implements lazy loading for large datasets
- **Pagination**: Uses pagination for large result sets
- **Streaming**: Streams large file uploads

## Integration Points

### External API Preparation

The system is prepared for integration with external APIs:

- **Perplexity API**: Ready for medication enrichment integration
- **Pharmacy APIs**: Prepared for pharmacy system integration
- **OCR Services**: Ready for OCR service integration
- **Drug Databases**: Prepared for comprehensive drug database integration

### Notification System

- **Stock Alerts**: Automatically creates stock alerts for low inventory
- **Prescription Renewals**: Tracks prescription renewal dates
- **Audit Notifications**: Notifies administrators of significant changes
- **Error Notifications**: Alerts administrators of processing errors

## Testing

### Test Coverage

Comprehensive test coverage includes:

- **Unit Tests**: Individual endpoint functionality
- **Integration Tests**: End-to-end workflow testing
- **Error Handling Tests**: Validation and error scenarios
- **Performance Tests**: Load and stress testing
- **Security Tests**: Authentication and authorization testing

### Test Data

Test data includes:

- **Sample Prescriptions**: Realistic prescription data
- **OCR Data**: Sample OCR-extracted data
- **User Scenarios**: Various user types and permissions
- **Error Scenarios**: Invalid data and edge cases

## Monitoring and Logging

### Audit Logging

All operations are logged with:

- **User Attribution**: Links actions to specific users
- **Timestamp**: Precise timing of all operations
- **Data Changes**: Records before/after states
- **Error Details**: Comprehensive error information

### Performance Monitoring

- **Response Times**: Tracks endpoint response times
- **Database Queries**: Monitors query performance
- **Memory Usage**: Tracks memory consumption
- **Error Rates**: Monitors error frequencies

## Future Enhancements

### Planned Features

- **Perplexity API Integration**: Full medication enrichment
- **Advanced OCR**: Multi-language OCR support
- **Machine Learning**: Predictive stock management
- **Mobile Integration**: Enhanced mobile app support
- **Real-time Notifications**: WebSocket-based notifications

### Scalability Improvements

- **Microservices**: Service decomposition for better scalability
- **Event Sourcing**: Event-driven architecture
- **CQRS**: Command Query Responsibility Segregation
- **Distributed Caching**: Redis-based distributed caching

## API Versioning

The enhanced views maintain backward compatibility while adding new functionality:

- **Version 1**: Original medication endpoints
- **Version 2**: Enhanced endpoints with new features
- **Deprecation Policy**: Clear deprecation timelines
- **Migration Guide**: Step-by-step migration instructions

## Support and Documentation

### API Documentation

- **OpenAPI/Swagger**: Auto-generated API documentation
- **Postman Collections**: Ready-to-use API collections
- **Code Examples**: Comprehensive code examples
- **Integration Guides**: Step-by-step integration instructions

### Troubleshooting

- **Common Issues**: Frequently encountered problems and solutions
- **Debug Mode**: Enhanced debugging capabilities
- **Log Analysis**: Tools for log analysis and debugging
- **Performance Tuning**: Guidelines for performance optimization 