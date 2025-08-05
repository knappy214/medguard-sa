# Prescription Workflow Test Suite

Comprehensive test suite for the MedGuard SA prescription processing workflow, covering frontend, backend, and integration testing.

## 📋 Test Overview

This test suite provides comprehensive coverage for the prescription workflow including:

### Frontend Tests
- **PrescriptionWorkflow.test.ts** - End-to-end workflow testing
- **OCRService.test.ts** - Image processing and text extraction
- **MedicationParser.test.ts** - Prescription text parsing and validation

### Backend Tests
- **test_prescription_workflow.py** - Django API testing and database operations

### Integration Tests
- Complete workflow testing from OCR to medication creation
- Performance and load testing
- Error handling and edge cases
- Security and data integrity validation

## 🚀 Quick Start

### Run All Tests
```bash
# Run comprehensive test suite with detailed reporting
npm run test:runner

# Run frontend tests only
npm run test:prescription

# Run backend tests only
npm run test:backend

# Run all tests (frontend + backend)
npm run test:all
```

### Run Tests with Coverage
```bash
# Frontend coverage
npm run test:prescription:coverage

# Backend coverage
npm run test:backend:coverage

# All coverage
npm run test:all:coverage
```

### Watch Mode (Development)
```bash
# Watch frontend tests
npm run test:prescription:watch

# Watch all tests
npm run test:watch
```

## 📊 Test Structure

### 1. PrescriptionWorkflow.test.ts
End-to-end workflow testing covering:

- **OCR Image Processing**
  - Image quality assessment
  - Text extraction accuracy
  - Format detection
  - ICD-10 code extraction

- **Text Parsing and Medication Extraction**
  - 21-medication prescription parsing
  - Complex dosage instructions
  - "As needed" medications
  - Brand name to generic mapping

- **Medication Validation**
  - Database validation
  - Drug interaction checking
  - Dosage validation

- **Form Data Conversion**
  - Bulk medication entries
  - API submission format

- **API Submission and Error Handling**
  - Network error handling
  - Retry mechanisms
  - Timeout handling

- **Schedule Generation**
  - Complex timing requirements
  - Patient preferences

- **Performance Testing**
  - Large prescription processing
  - Concurrent processing
  - Memory management

- **Error Handling and Edge Cases**
  - Malformed prescriptions
  - Missing information
  - Network timeouts

- **Accessibility and Mobile Testing**
  - Mobile device constraints
  - Accessible error messages

- **Security and Data Handling**
  - Data encryption
  - Privacy protection
  - Audit logging

### 2. OCRService.test.ts
Comprehensive OCR service testing:

- **Image Quality Assessment**
  - Contrast, brightness, blur detection
  - Noise and skew analysis
  - Processability evaluation

- **Image Preprocessing**
  - Contrast enhancement
  - Brightness adjustment
  - Sharpening and denoising
  - Deskewing and thresholding

- **Text Extraction and Processing**
  - Multi-language support
  - Medical abbreviation expansion
  - Prescription metadata extraction

- **Prescription Format Detection**
  - South African standard format
  - Private practice format
  - International format detection

- **Medication Validation**
  - Brand name to generic mapping
  - Drug interaction identification
  - Dosage validation

- **Error Handling**
  - Unsupported file formats
  - Corrupted images
  - Network timeouts
  - OCR failures

- **Performance Testing**
  - Processing time limits
  - Concurrent processing
  - Caching mechanisms

- **Batch Processing**
  - Multiple prescription handling
  - Error handling in batches
  - Configuration management

### 3. MedicationParser.test.ts
Prescription text parsing and validation:

- **Basic Prescription Parsing**
  - 21-medication prescription handling
  - Patient and doctor information extraction
  - ICD-10 code extraction

- **Complex Dosage Instructions**
  - Tapering schedules
  - Weekly medications
  - Split dosages
  - Specific timing requirements

- **Afrikaans Prescription Support**
  - Multi-language parsing
  - Term translation
  - Quantity handling

- **Medication Type Detection**
  - Insulin pens
  - Inhalers
  - Tablets and capsules
  - Various medication forms

- **Dosage and Frequency Parsing**
  - Multiple dosage patterns
  - Frequency variations
  - Timing instructions

- **Quantity and Repeat Parsing**
  - Quantity validation
  - Repeat information
  - Missing data handling

- **Brand Name to Generic Mapping**
  - South African medication database
  - Generic name identification
  - Missing mappings handling

- **Error Handling and Validation**
  - Malformed prescriptions
  - Missing information
  - Validation errors

- **Form Data Conversion**
  - API format conversion
  - Data integrity maintenance

- **Performance Testing**
  - Large prescription efficiency
  - Memory leak prevention

### 4. test_prescription_workflow.py (Backend)
Django API and database testing:

- **API Endpoint Testing**
  - Prescription parsing endpoints
  - Bulk medication creation
  - Schedule generation
  - Image upload processing

- **Database Operations**
  - Transaction integrity
  - Bulk operations
  - Data validation

- **Error Handling**
  - Network errors
  - Validation errors
  - Database errors

- **Performance Testing**
  - Load testing
  - Concurrent processing
  - Response time validation

- **Security Testing**
  - Authentication requirements
  - Data encryption
  - Privacy protection

- **Integration Testing**
  - Complete workflow testing
  - End-to-end validation

## 🎯 Test Data

The test suite uses realistic prescription data including:

### 21-Medication Prescription
Complete prescription with diabetes, cardiovascular, respiratory, and supplement medications:

```text
1. NOVORAPID FlexPen 100units/ml
2. LANTUS SoloStar Pen 100units/ml
3. METFORMIN 500mg tablets
4. LIPITOR 20mg tablets
5. COZAAR 50mg tablets
6. VENTOLIN inhaler 100mcg
7. SERETIDE 250/25 inhaler
8. PANADO 500mg tablets
9. OMEPRAZOLE 20mg capsules
10. MOVICOL sachets
11. VITAMIN D3 1000IU tablets
12. FOLIC ACID 5mg tablets
13. CALCIUM CARBONATE 500mg tablets
14. MAGNESIUM 400mg tablets
15. OMEGA-3 1000mg capsules
16. PROBIOTIC capsules
17. MELATONIN 3mg tablets
18. ASPIRIN 100mg tablets
19. VITAMIN B12 1000mcg tablets
20. ZINC 15mg tablets
21. VITAMIN C 500mg tablets
```

### Complex Dosage Instructions
Tests for complex medication schedules:

- Tapering dosages (Prednisone)
- Weekly medications (Methotrexate)
- Split dosages (Insulin Mixtard)
- Specific timing (Warfarin at 18h00)

### Afrikaans Prescriptions
Multi-language support testing with Afrikaans medication terms.

## 📈 Performance Benchmarks

### Frontend Tests
- **OCR Processing**: < 10 seconds for standard prescriptions
- **Text Parsing**: < 1 second for 21-medication prescriptions
- **Concurrent Processing**: < 30 seconds for 5 concurrent prescriptions
- **Memory Usage**: < 100MB for large prescription processing

### Backend Tests
- **API Response Time**: < 1 second average
- **Bulk Creation**: < 5 seconds for 21 medications
- **Database Operations**: < 2 seconds for complex queries
- **Load Testing**: < 15 seconds for 10 concurrent requests

### Integration Tests
- **Complete Workflow**: < 15 seconds end-to-end
- **Error Recovery**: < 5 seconds for error scenarios
- **Data Integrity**: 100% validation success rate

## 🔧 Configuration

### Frontend Test Configuration
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/tests/']
    }
  }
})
```

### Backend Test Configuration
```python
# settings/test.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'medguard_test',
        'USER': 'test_user',
        'PASSWORD': 'test_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 📊 Coverage Requirements

### Minimum Coverage Targets
- **Frontend**: 80% line coverage
- **Backend**: 85% line coverage
- **Integration**: 90% workflow coverage

### Coverage Areas
- **OCR Service**: Image processing, text extraction, validation
- **Parser Service**: Text parsing, medication extraction, validation
- **API Endpoints**: All prescription-related endpoints
- **Database Operations**: CRUD operations, transactions
- **Error Handling**: All error scenarios and edge cases

## 🐛 Troubleshooting

### Common Issues

#### Frontend Tests Failing
```bash
# Clear test cache
npm run test:unit -- --clearCache

# Check for missing dependencies
npm install

# Verify TypeScript compilation
npm run build
```

#### Backend Tests Failing
```bash
# Check database connection
python manage.py check --database default

# Run migrations
python manage.py migrate

# Clear test database
python manage.py flush --no-input
```

#### Integration Tests Failing
```bash
# Check both frontend and backend are running
npm run dev  # Frontend
python manage.py runserver  # Backend

# Verify API endpoints are accessible
curl http://localhost:8000/api/prescription/parse/
```

### Performance Issues
```bash
# Run performance profiling
npm run test:prescription -- --profile

# Check memory usage
npm run test:prescription -- --maxWorkers=1
```

## 📝 Test Reports

The test runner generates detailed reports:

### JSON Report
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "summary": {
    "totalTests": 150,
    "passedTests": 145,
    "failedTests": 5,
    "successRate": 96.7
  },
  "performance": {
    "averageTestTime": 250,
    "slowestTest": "Complete Workflow",
    "fastestTest": "Basic Parsing"
  },
  "coverage": {
    "frontend": 85.2,
    "backend": 88.7,
    "integration": 87.0
  }
}
```

### Markdown Report
Human-readable report with:
- Test summary and statistics
- Performance metrics
- Coverage information
- Detailed test results
- Recommendations for improvement

## 🔄 Continuous Integration

### GitHub Actions
```yaml
name: Prescription Workflow Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm install
      - name: Run frontend tests
        run: npm run test:prescription:coverage
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Run backend tests
        run: npm run test:backend:coverage
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: prescription-tests
        name: Prescription Workflow Tests
        entry: npm run test:prescription
        language: system
        types: [typescript, python]
        pass_filenames: false
```

## 📚 Additional Resources

### Documentation
- [OCR Service Documentation](../services/README_OCR.md)
- [Prescription Parser Documentation](../utils/README.md)
- [API Documentation](../../medguard_backend/medications/README_PRESCRIPTION_PARSER.md)

### Related Tests
- [Stock Management Tests](../services/__tests__/)
- [Schedule Generator Tests](../services/__tests__/)
- [Medication Enrichment Tests](../services/__tests__/)

### Performance Monitoring
- [Performance Monitor](../../medguard_backend/scripts/performance_monitor.py)
- [Deployment Optimizations](../../medguard_backend/scripts/deploy_optimizations.py)

## 🤝 Contributing

When adding new tests:

1. **Follow the existing structure** and naming conventions
2. **Include realistic test data** that represents actual use cases
3. **Add performance benchmarks** for new functionality
4. **Update coverage requirements** if needed
5. **Document new test scenarios** in this README

### Test Naming Convention
- `describe` blocks: Feature or component being tested
- `it` blocks: Specific behavior or scenario
- Use descriptive names that explain the test purpose

### Example
```typescript
describe('OCR Service - Image Quality Assessment', () => {
  it('should detect poor quality images and suggest manual review', async () => {
    // Test implementation
  })
})
```

## 📞 Support

For questions or issues with the test suite:

1. Check the troubleshooting section above
2. Review the test reports for specific failure details
3. Check the related documentation
4. Create an issue with detailed error information

---

**Last Updated**: January 2024
**Test Suite Version**: 1.0.0
**Coverage Target**: 85%+ 