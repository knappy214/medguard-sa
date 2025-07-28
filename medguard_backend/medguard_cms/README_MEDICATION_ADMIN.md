# MedGuard SA - Wagtail ModelAdmin Medication Management

This document describes the comprehensive Wagtail ModelAdmin setup for medication management in MedGuard SA, including custom admin panels, filtering, search, bulk actions, and internationalization support.

## Overview

The medication management system provides a complete admin interface for managing:
- **Medications**: Drug inventory, stock levels, expiration dates
- **Medication Schedules**: Patient medication schedules and timing
- **Medication Logs**: Adherence tracking and dose history
- **Stock Alerts**: Automated alerts for low stock and expiring medications

## Features

### 🎨 Custom Admin Panels
- **Organized Field Groups**: Fields are logically grouped into panels (Basic Information, Dosage, Stock Management, etc.)
- **Healthcare Color Scheme**: Professional medical color palette with accessibility compliance
- **Status Indicators**: Visual status indicators for stock levels, expiration dates, and adherence scores
- **Responsive Design**: Mobile-friendly interface with touch-optimized controls

### 🔍 Advanced Filtering & Search
- **Custom Filter Sets**: Model-specific filters for each medication entity
- **Multi-field Search**: Search across medication names, patient names, manufacturers
- **Date Range Filters**: Filter by expiration dates, schedule periods, log dates
- **Status Filters**: Filter by medication status, schedule status, alert priority

### ⚡ Bulk Actions
- **Stock Management**: Bulk update stock levels, mark medications as expired
- **Schedule Management**: Activate/deactivate/pause multiple schedules
- **Log Management**: Mark multiple logs as taken/missed
- **Alert Management**: Acknowledge, resolve, or dismiss multiple alerts
- **Export Functionality**: Export data to CSV with custom field selection

### 🌍 Internationalization
- **Bilingual Support**: English (en-ZA) and Afrikaans (af-ZA)
- **Complete Translation**: All UI elements, field labels, and help text translated
- **Locale-aware Formatting**: Date, time, and number formatting for South Africa

## File Structure

```
medguard_cms/
├── medguard_cms/
│   ├── wagtail_hooks.py          # ModelAdmin configuration
│   ├── settings/
│   │   └── base.py               # Wagtail settings with i18n
│   ├── static/
│   │   ├── css/
│   │   │   └── medication-admin.css  # Custom healthcare styling
│   │   └── js/
│   │       └── medication-admin.js   # Enhanced functionality
│   └── templates/
│       └── wagtailadmin/
│           ├── base.html             # Custom admin base template
│           └── modeladmin/
│               └── bulk_actions.html # Bulk actions interface
├── locale/
│   ├── en-ZA/
│   │   └── LC_MESSAGES/
│   │       └── django.po            # English translations
│   └── af-ZA/
│       └── LC_MESSAGES/
│           └── django.po            # Afrikaans translations
└── README_MEDICATION_ADMIN.md
```

## Configuration

### ModelAdmin Setup

The `wagtail_hooks.py` file configures four main ModelAdmin classes:

1. **MedicationModelAdmin**
   - Manages medication inventory
   - Stock status and expiration tracking
   - Manufacturer and prescription type filtering

2. **MedicationScheduleModelAdmin**
   - Patient medication schedules
   - Timing and frequency management
   - Active status and "take today" indicators

3. **MedicationLogModelAdmin**
   - Medication adherence tracking
   - Dose history and timing accuracy
   - Adherence score calculation

4. **StockAlertModelAdmin**
   - Automated stock alerts
   - Priority-based alert management
   - Resolution tracking

### Custom Filter Sets

Each model has a dedicated filter set:

```python
class MedicationFilterSet(WagtailFilterSet):
    class Meta:
        model = Medication
        fields = {
            'medication_type': ['exact'],
            'prescription_type': ['exact'],
            'manufacturer': ['icontains'],
            'name': ['icontains'],
            'generic_name': ['icontains'],
            'pill_count': ['gte', 'lte'],
            'expiration_date': ['gte', 'lte'],
        }
```

### Healthcare Color Scheme

The system uses a professional healthcare color palette:

```css
:root {
    --medguard-primary: #2563EB;      /* Trust & Professionalism */
    --medguard-secondary: #10B981;    /* Health & Safety */
    --medguard-accent: #F59E0B;       /* Warning & Attention */
    --medguard-danger: #EF4444;       /* Critical & Alerts */
    --medguard-success: #059669;      /* Success */
    --medguard-warning: #D97706;      /* Warning */
    --medguard-info: #3B82F6;         /* Information */
    --medguard-neutral: #6B7280;      /* Neutral */
}
```

## Usage

### Accessing the Admin Interface

1. Navigate to the Wagtail admin at `/admin/`
2. Look for the "Medication Management" section in the sidebar
3. Choose from the four main sections:
   - Medications
   - Medication Schedules
   - Medication Logs
   - Stock Alerts

### Bulk Operations

1. Select multiple items using checkboxes
2. Choose "Bulk Actions" from the action dropdown
3. Select the desired action (update stock, export, etc.)
4. Configure action-specific options
5. Apply the action to all selected items

### Search and Filtering

1. Use the search bar for quick text searches
2. Apply filters using the filter panel
3. Combine multiple filters for precise results
4. Save frequently used filter combinations

### Language Switching

1. The interface automatically detects the user's language preference
2. Manual language switching is available in the user settings
3. All content is displayed in the selected language

## Development

### Adding New Models

To add a new medication-related model:

1. Create the model in `medications/models.py`
2. Add a new ModelAdmin class in `wagtail_hooks.py`
3. Create a custom filter set if needed
4. Add translations to both language files
5. Update the MedicationManagementGroup items tuple

### Customizing Styles

The healthcare theme can be customized by modifying:
- `medication-admin.css` for visual styling
- `medication-admin.js` for enhanced functionality
- `base.html` for global admin styling

### Adding Translations

1. Add new translation strings to both `.po` files
2. Run `python manage.py compilemessages` to compile translations
3. Restart the development server

## Security Considerations

- All bulk actions require confirmation for destructive operations
- CSRF protection is enabled for all forms
- User permissions are enforced through Wagtail's permission system
- Sensitive medical data is handled according to healthcare privacy standards

## Performance Optimization

- Database queries are optimized with `select_related()` and `prefetch_related()`
- Pagination is implemented for large datasets
- Search results are cached where appropriate
- Static assets are optimized for production

## Accessibility

- WCAG 2.2 AA compliance
- High contrast mode support
- Keyboard navigation
- Screen reader compatibility
- Touch-friendly interface for mobile devices

## Browser Support

- Chrome/Chromium (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Troubleshooting

### Common Issues

1. **Translations not appearing**
   - Ensure `USE_I18N = True` in settings
   - Check that locale paths are correctly configured
   - Run `python manage.py compilemessages`

2. **Bulk actions not working**
   - Verify CSRF token is included in forms
   - Check user permissions for the model
   - Ensure JavaScript is enabled

3. **Styling issues**
   - Clear browser cache
   - Check that static files are being served correctly
   - Verify CSS file paths in templates

### Debug Mode

Enable debug mode in settings to see detailed error messages:

```python
DEBUG = True
```

## Contributing

When contributing to the medication management system:

1. Follow the existing code style and patterns
2. Add appropriate translations for new strings
3. Test with both English and Afrikaans interfaces
4. Ensure accessibility compliance
5. Update this documentation for new features

## License

This medication management system is part of MedGuard SA and follows the project's licensing terms. 