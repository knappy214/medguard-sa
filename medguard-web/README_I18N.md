# Vue I18n Setup for MedGuard Web

This document describes the internationalization (i18n) setup for the MedGuard Web application, specifically focused on medication management functionality.

## Overview

The application supports two South African locales:
- **English (en-ZA)**: Primary language
- **Afrikaans (af-ZA)**: Secondary language

## Architecture

### 1. Translation Files
- **Location**: `src/locales/`
- **Files**: 
  - `en.json` - English translations
  - `af.json` - Afrikaans translations

### 2. Key Translation Categories

#### Dashboard
- Dashboard title, subtitle, and main navigation
- Today's schedule, medication list, stock alerts
- Status indicators (taken, missed, upcoming)

#### Medication
- Medication properties (name, strength, form, quantity)
- Prescription types (prescription, over-the-counter, supplement)
- Medical information (side effects, interactions, storage)
- Dates and tracking (expiry, refill, last taken, next dose)

#### Schedule
- Frequency options (daily, twice daily, weekly, etc.)
- Timing relative to meals
- Custom schedule options
- Duration and date ranges

#### Forms & Strengths
- Medication forms (tablet, capsule, liquid, etc.)
- Strength units (mg, mcg, ml, units, etc.)

#### Alerts
- Stock alerts (low stock, out of stock)
- Medical alerts (expiring, missed dose, interactions)
- Safety alerts (allergy, overdose risk)

#### Actions & Validation
- Common actions (add, edit, delete, save)
- Form validation messages
- Success/error messages

### 3. South African Locale Formatting

#### Number Formatting
- **Currency**: ZAR (South African Rand) with symbol
- **Decimal**: Standard decimal formatting
- **Percent**: Percentage formatting

#### Date/Time Formatting
- **Short**: `15 Mar 2024`
- **Long**: `Friday, 15 March 2024`
- **Time**: `14:30`

## Usage

### Basic Translation
```vue
<template>
  <h1>{{ $t('dashboard.title') }}</h1>
  <p>{{ $t('dashboard.subtitle') }}</p>
</template>
```

### Number Formatting
```vue
<script setup>
import { useI18n } from 'vue-i18n'
const { n } = useI18n()

const price = 125.50
</script>

<template>
  <span>{{ n(price, 'currency') }}</span> <!-- R125.50 -->
</template>
```

### Date Formatting
```vue
<script setup>
import { useI18n } from 'vue-i18n'
const { d } = useI18n()

const date = new Date('2024-03-15')
</script>

<template>
  <span>{{ d(date, 'short') }}</span> <!-- 15 Mar 2024 -->
  <span>{{ d(date, 'long') }}</span> <!-- Friday, 15 March 2024 -->
</template>
```

### Language Switching
```vue
<script setup>
import { useLanguagePreference } from '@/composables/useLanguagePreference'

const { switchLanguage, currentLocale } = useLanguagePreference()
</script>

<template>
  <button @click="switchLanguage('af-ZA')">
    Switch to Afrikaans
  </button>
</template>
```

## Components

### LanguageSwitcher
- **Location**: `src/components/common/LanguageSwitcher.vue`
- **Features**: Dropdown with language options, persistent selection
- **Usage**: Automatically included in the main header

### useLanguagePreference Composable
- **Location**: `src/composables/useLanguagePreference.ts`
- **Features**: 
  - Persistent language storage in localStorage
  - Browser language detection
  - Automatic locale synchronization
  - Available languages list

## Configuration

### Vite Configuration
The `vite.config.ts` includes the `@intlify/unplugin-vue-i18n` plugin for:
- Pre-compilation of locale messages
- SFC i18n block support
- Performance optimization

### Main I18n Setup
The `src/main.ts` configures:
- Legacy mode disabled (Vue 3 Composition API)
- Fallback locale to English
- South African date/time and number formats
- Warning suppression for missing keys

## Best Practices

### 1. Translation Keys
- Use nested keys for organization: `dashboard.title`, `medication.name`
- Keep keys descriptive and consistent
- Use lowercase with dots for separation

### 2. Dynamic Content
- Use interpolation for dynamic values: `{{ $t('medication.pillsRemaining', { count: 5 }) }}`
- Format numbers and dates using the built-in formatters

### 3. Fallbacks
- Always provide fallback translations
- Use meaningful fallback messages
- Test with missing keys

### 4. Accessibility
- Ensure translations maintain semantic meaning
- Consider text length differences between languages
- Test with screen readers

## Testing

### Manual Testing
1. Switch between English and Afrikaans
2. Verify all UI elements translate correctly
3. Check number and date formatting
4. Test persistent language selection

### Automated Testing
```bash
# Type checking
npm run type-check

# Development server
npm run dev
```

## Adding New Translations

1. **Add to both language files** (`en.json` and `af.json`)
2. **Use consistent key structure**
3. **Test the translation in context**
4. **Update this documentation if needed**

### Example
```json
// en.json
{
  "medication": {
    "newFeature": "New Medication Feature"
  }
}

// af.json
{
  "medication": {
    "newFeature": "Nuwe Medikasie Kenmerk"
  }
}
```

## Troubleshooting

### Common Issues
1. **Missing translations**: Check both language files
2. **Formatting issues**: Verify number/date format configurations
3. **Persistent storage**: Clear localStorage if needed
4. **Type errors**: Ensure proper TypeScript types

### Debug Mode
Enable Vue I18n debug mode in development:
```typescript
const i18n = createI18n({
  // ... other options
  missingWarn: true,
  fallbackWarn: true
})
```

## Future Enhancements

- [ ] Add more South African languages (Zulu, Xhosa, etc.)
- [ ] Implement RTL support for future languages
- [ ] Add translation memory/caching
- [ ] Integrate with translation management system
- [ ] Add automated translation quality checks 