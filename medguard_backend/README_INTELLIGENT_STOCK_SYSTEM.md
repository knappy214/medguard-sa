# Intelligent Stock Tracking System

## Overview

The MedGuard SA Intelligent Stock Tracking System provides advanced medication inventory management with predictive analytics, automated ordering, and real-time monitoring capabilities. This system helps healthcare providers and patients maintain optimal medication stock levels while preventing stockouts and managing expiration dates.

## Features

### 🔍 **Predictive Analytics**
- **Stock Depletion Prediction**: Uses time series analysis to predict when medications will run out
- **Usage Pattern Analysis**: Analyzes historical data to identify usage trends and seasonal patterns
- **Confidence Scoring**: Provides confidence levels for predictions based on data quality
- **Recommendation Engine**: Suggests optimal order quantities and timing

### 📊 **Real-time Monitoring**
- **Stock Level Tracking**: Real-time monitoring of current stock levels
- **Low Stock Alerts**: Automated alerts when stock falls below thresholds
- **Expiration Monitoring**: Tracks medication expiration dates and sends warnings
- **Usage Rate Calculation**: Calculates daily, weekly, and monthly usage rates

### 🔗 **Pharmacy Integration**
- **Multiple Integration Types**: Support for API, EDI, Webhook, and Manual integrations
- **Automated Ordering**: Automatic order placement when stock reaches thresholds
- **Stock Synchronization**: Real-time sync with pharmacy systems
- **Connection Testing**: Built-in connection testing and health monitoring

### 📈 **Advanced Analytics**
- **Stock Visualization**: Interactive charts and graphs for stock trends
- **Usage Volatility Analysis**: Measures consistency of medication usage
- **Seasonal Factor Calculation**: Accounts for seasonal variations in usage
- **Comprehensive Reporting**: Detailed reports for inventory management

### 🚨 **Smart Alerts**
- **Multi-level Alerts**: Low, medium, high, and critical priority alerts
- **Prescription Renewal Reminders**: Tracks prescription expiration and renewal needs
- **Stockout Warnings**: Early warnings before medications run out
- **Expiry Notifications**: Alerts for medications expiring soon

## Architecture

### Backend Components

#### Models
- **Medication**: Core medication information and stock levels
- **StockTransaction**: Tracks all stock movements with detailed analytics
- **StockAnalytics**: Stores calculated metrics and predictions
- **PharmacyIntegration**: Manages connections to external pharmacy systems
- **StockAlert**: Handles alert generation and management
- **StockVisualization**: Stores chart data and analytics
- **PrescriptionRenewal**: Tracks prescription renewals and reminders

#### Services
- **IntelligentStockService**: Core service for stock management and predictions
- **StockAnalyticsService**: Handles analytics calculations and reporting
- **NotificationService**: Manages alert delivery and notifications

#### Tasks (Celery)
- **update_stock_analytics_task**: Updates analytics for medications
- **predict_stock_depletion_task**: Runs stock depletion predictions
- **check_prescription_renewals_task**: Monitors prescription renewals
- **integrate_with_pharmacy_task**: Handles pharmacy system integration
- **generate_stock_visualizations_task**: Creates stock charts and graphs
- **monitor_stock_levels_task**: Continuous stock level monitoring

### Frontend Components

#### Vue.js Components
- **StockAnalytics.vue**: Displays stock analytics and predictions
- **PharmacyIntegration.vue**: Manages pharmacy system integrations
- **MedicationDashboard.vue**: Main dashboard with stock overview
- **StockAlertsCard.vue**: Shows active stock alerts
- **MedicationCard.vue**: Individual medication display with stock info

#### API Integration
- **medicationApi.ts**: Frontend API service for medication operations
- **Stock Analytics Endpoints**: `/api/medications/{id}/analytics/`
- **Pharmacy Integration Endpoints**: `/api/pharmacy-integrations/`
- **Stock Analytics Dashboard**: `/api/stock-analytics/dashboard/`

## Installation & Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd medguard_backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Set up the intelligent stock system
python manage.py setup_intelligent_stock_system --create-sample-data

# Start Celery worker for background tasks
celery -A medguard_backend worker -l info

# Start Celery beat for scheduled tasks
celery -A medguard_backend beat -l info
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd medguard-web

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Configuration

#### Environment Variables
```bash
# Django settings
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/medguard

# Celery settings
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# API settings
VITE_API_BASE_URL=http://localhost:8000/api
```

#### Celery Beat Schedule
```python
# settings/base.py
CELERY_BEAT_SCHEDULE = {
    'update-stock-analytics': {
        'task': 'medications.update_stock_analytics',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
    },
    'monitor-stock-levels': {
        'task': 'medications.monitor_stock_levels',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'check-prescription-renewals': {
        'task': 'medications.check_prescription_renewals',
        'schedule': crontab(hour=9, minute=0),  # Daily at 9 AM
    },
}
```

## Usage

### Stock Analytics Dashboard

1. **View Stock Analytics**
   - Navigate to medication details
   - Click "Stock Analytics" tab
   - View current stock, usage rates, and predictions

2. **Monitor Predictions**
   - Check "Days Until Stockout" for each medication
   - Review confidence levels for predictions
   - View recommended order quantities

3. **Generate Reports**
   - Click "Generate Report" for detailed analytics
   - Export data for external analysis
   - Schedule automated reports

### Pharmacy Integration

1. **Add Integration**
   - Go to "Pharmacy Integration" section
   - Click "Add Integration"
   - Select integration type (API, EDI, Webhook, Manual)
   - Configure connection details

2. **Test Connection**
   - Click "Test Connection" to verify setup
   - Monitor connection status
   - Review sync history

3. **Enable Auto-Ordering**
   - Toggle "Auto Order" for automatic ordering
   - Set order thresholds and lead times
   - Configure order quantity multipliers

### Stock Alerts

1. **View Active Alerts**
   - Check dashboard for active alerts
   - Review alert priorities and details
   - Acknowledge or resolve alerts

2. **Configure Alert Thresholds**
   - Set low stock thresholds per medication
   - Configure expiration warning days
   - Customize alert delivery methods

## API Endpoints

### Stock Analytics
```
GET /api/medications/{id}/analytics/
POST /api/medications/{id}/predict_stockout/
GET /api/medications/{id}/usage_patterns/
GET /api/medications/{id}/stock_visualization/
POST /api/medications/{id}/record_dose/
```

### Pharmacy Integration
```
GET /api/pharmacy-integrations/
POST /api/pharmacy-integrations/{id}/test_connection/
POST /api/pharmacy-integrations/{id}/sync_stock/
```

### Stock Analytics Dashboard
```
GET /api/stock-analytics/dashboard/
GET /api/stock-analytics/low_stock_alerts/
GET /api/stock-analytics/expiring_soon/
```

## Data Models

### StockAnalytics
```python
{
    "daily_usage_rate": 2.5,
    "weekly_usage_rate": 17.5,
    "monthly_usage_rate": 75.0,
    "days_until_stockout": 12,
    "predicted_stockout_date": "2024-02-15",
    "recommended_order_quantity": 50,
    "recommended_order_date": "2024-02-10",
    "stockout_confidence": 0.85
}
```

### PharmacyIntegration
```python
{
    "name": "Clicks Pharmacy API",
    "pharmacy_name": "Clicks Pharmacy",
    "integration_type": "api",
    "status": "active",
    "api_endpoint": "https://api.clicks.co.za/v1",
    "auto_order_enabled": true,
    "order_threshold": 15,
    "order_lead_time_days": 2
}
```

## Monitoring & Maintenance

### Health Checks
- Monitor Celery worker status
- Check database connection health
- Verify pharmacy integration connectivity
- Review error logs and alerts

### Performance Optimization
- Cache frequently accessed analytics data
- Optimize database queries with proper indexing
- Monitor API response times
- Scale Celery workers based on load

### Data Maintenance
- Regular cleanup of old transaction data
- Archive completed prescription renewals
- Update analytics calculations
- Refresh stock visualizations

## Troubleshooting

### Common Issues

1. **Analytics Not Updating**
   - Check Celery worker status
   - Verify task execution in logs
   - Ensure sufficient transaction data exists

2. **Pharmacy Integration Failures**
   - Test connection manually
   - Verify API credentials and endpoints
   - Check network connectivity
   - Review error logs for specific issues

3. **Prediction Accuracy Issues**
   - Ensure sufficient historical data (minimum 30 days)
   - Check for data quality issues
   - Review usage pattern consistency
   - Adjust calculation parameters

### Debug Commands
```bash
# Check Celery worker status
celery -A medguard_backend inspect active

# View task results
celery -A medguard_backend inspect scheduled

# Test pharmacy integration
python manage.py shell
>>> from medications.services import IntelligentStockService
>>> service = IntelligentStockService()
>>> integration = PharmacyIntegration.objects.get(id=1)
>>> service.integrate_with_pharmacy(None, integration)
```

## Future Enhancements

### Planned Features
- **Machine Learning Integration**: Advanced ML models for better predictions
- **Multi-location Support**: Support for multiple pharmacy locations
- **Advanced Reporting**: Custom report builder and scheduling
- **Mobile Notifications**: Push notifications for critical alerts
- **Integration Marketplace**: Pre-built integrations for major pharmacy systems

### Performance Improvements
- **Real-time Analytics**: WebSocket-based real-time updates
- **Advanced Caching**: Redis-based caching for analytics data
- **Database Optimization**: Query optimization and indexing improvements
- **API Rate Limiting**: Implement rate limiting for external APIs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki
- Review the troubleshooting guide 