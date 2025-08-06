# MedGuard SA Wagtail 7.0.2 Widgets

This directory contains modern interactive widgets for the MedGuard SA medication management system, all built using Wagtail 7.0.2's enhanced JavaScript integration and accessibility features.

## Overview

All widgets are designed to be:
- **Accessibility Compliant**: Full ARIA support, keyboard navigation, screen reader friendly
- **Modern & Interactive**: Real-time updates, drag & drop, visual feedback
- **Healthcare Focused**: Specifically designed for medication management workflows
- **Wagtail 7.0.2 Compatible**: Using the latest Wagtail features and improvements

## Widgets Implemented

### 1. MedicationDosageCalculatorWidget
**Purpose**: Enhanced medication dosage calculator with real-time calculations
- **Features**:
  - Real-time dosage calculations
  - Weight-based dosing
  - Age-based adjustments
  - Renal/hepatic impairment considerations
  - Interactive visual feedback
  - Accessibility compliant

### 2. PrescriptionOCRWidget
**Purpose**: Image upload and text extraction with real-time preview
- **Features**:
  - Image upload with drag & drop
  - Real-time OCR text extraction
  - Prescription data parsing
  - Interactive preview and editing
  - Multiple image format support
  - Accessibility compliant

### 3. MedicationInteractionCheckerWidget
**Purpose**: Dynamic drug interaction warnings and checking
- **Features**:
  - Real-time drug interaction checking
  - Severity-based warnings
  - Alternative medication suggestions
  - Patient-specific risk assessment
  - Interactive risk visualization
  - Accessibility compliant

### 4. StockLevelIndicatorWidget
**Purpose**: Real-time medication inventory levels monitoring
- **Features**:
  - Real-time stock level monitoring
  - Visual inventory indicators
  - Low stock alerts
  - Expiry date warnings
  - Reorder suggestions
  - Accessibility compliant

### 5. MedicationScheduleWidget
**Purpose**: Visual medication timing setup and management
- **Features**:
  - Visual schedule builder
  - Drag & drop time slots
  - Multiple medication support
  - Conflict detection
  - Reminder integration
  - Accessibility compliant

### 6. PharmacyLocatorWidget
**Purpose**: Map integration and location services for pharmacies
- **Features**:
  - Interactive map display
  - Location-based pharmacy search
  - Distance and availability filtering
  - Contact information integration
  - Route planning
  - Accessibility compliant

### 7. PrescriptionHistoryTimelineWidget
**Purpose**: Visual prescription tracking and history
- **Features**:
  - Visual timeline display
  - Prescription status tracking
  - Medication adherence visualization
  - Historical data analysis
  - Export capabilities
  - Accessibility compliant

### 8. MedicationAdherenceTrackerWidget
**Purpose**: Progress visualization for medication adherence
- **Features**:
  - Visual adherence tracking
  - Progress charts and graphs
  - Missed dose tracking
  - Adherence scoring
  - Goal setting and monitoring
  - Accessibility compliant

### 9. NotificationPreferenceWidget
**Purpose**: Setting up medication reminders and notifications
- **Features**:
  - Multi-channel notification setup
  - Customizable reminder schedules
  - Priority-based notifications
  - Integration with existing notification system
  - Accessibility compliant

## Technical Implementation

### Wagtail 7.0.2 Integration
All widgets use Wagtail 7.0.2's enhanced features:
- **Telepath Registration**: All widgets are registered with Wagtail's telepath system
- **AdminWidget Base**: Extends Wagtail's AdminWidget for consistent admin integration
- **Enhanced JavaScript**: Uses Wagtail 7.0.2's improved JavaScript integration
- **Accessibility**: Full ARIA support and keyboard navigation

### Accessibility Features
- **ARIA Labels**: Comprehensive ARIA labeling for screen readers
- **Keyboard Navigation**: Full keyboard accessibility
- **High Contrast**: Support for high contrast modes
- **Screen Reader Support**: Optimized for screen reader compatibility
- **Focus Management**: Proper focus handling and management

### Internationalization
- **Translation Ready**: All text uses Django's translation system
- **Bilingual Support**: Supports both English and Afrikaans
- **Locale Aware**: Respects user locale settings

## Usage

### Basic Usage
```python
from widgets.wagtail_widgets import MedicationDosageCalculatorWidget

# In a form or model
dosage_widget = MedicationDosageCalculatorWidget(
    options={
        'weight_based': True,
        'age_based': True,
        'renal_adjustment': True,
    }
)
```

### Advanced Usage with Custom Options
```python
# Custom OCR widget with specific options
ocr_widget = PrescriptionOCRWidget(
    options={
        'supported_formats': ['jpg', 'png', 'pdf'],
        'max_file_size': 5 * 1024 * 1024,  # 5MB
        'ocr_languages': ['en', 'af'],
        'confidence_threshold': 0.9,
    }
)
```

## File Structure

```
medguard_backend/widgets/
├── __init__.py                    # Package initialization
├── wagtail_widgets.py            # All widget implementations
└── README.md                     # This documentation
```

## CSS and JavaScript Dependencies

Each widget includes its own CSS and JavaScript files:
- CSS files: `css/widgets/{widget_name}.css`
- JavaScript files: `js/widgets/{widget_name}.js`

These files need to be created and included in your static files collection.

## Integration with Existing Systems

### Notification System Integration
The `NotificationPreferenceWidget` integrates with the existing MedGuard notification system:
- Uses `medguard_notifications` app
- Supports multiple notification channels
- Configurable reminder schedules

### Medication System Integration
All widgets integrate with the existing medication management system:
- Uses `medications` app models
- Supports prescription workflows
- Integrates with stock management

## Security Considerations

- **Input Validation**: All widgets include proper input validation
- **CSRF Protection**: Forms include CSRF protection
- **File Upload Security**: OCR widget includes file type and size validation
- **Data Privacy**: All widgets respect user privacy settings

## Performance Optimizations

- **Lazy Loading**: Widgets load data on demand
- **Caching**: Support for widget data caching
- **Minimal Dependencies**: Optimized for minimal resource usage
- **Progressive Enhancement**: Works without JavaScript (basic functionality)

## Future Enhancements

### Planned Features
- **Real-time Collaboration**: Multi-user widget interactions
- **Advanced Analytics**: Enhanced data visualization
- **Mobile Optimization**: Better mobile device support
- **API Integration**: External healthcare API integration

### Extensibility
All widgets are designed to be easily extensible:
- Modular architecture
- Plugin system support
- Customizable options
- Hook system integration

## Support and Maintenance

### Testing
- Unit tests for each widget
- Integration tests with Wagtail admin
- Accessibility testing with screen readers
- Cross-browser compatibility testing

### Documentation
- Comprehensive inline documentation
- Usage examples
- API documentation
- Accessibility guidelines

## Contributing

When adding new widgets:
1. Follow the existing widget pattern
2. Include full accessibility support
3. Add comprehensive documentation
4. Include unit tests
5. Register with Wagtail's telepath system

## License

This code is part of the MedGuard SA project and follows the same licensing terms. 