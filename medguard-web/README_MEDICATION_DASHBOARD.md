# MedGuard SA Medication Dashboard

A comprehensive Vue.js medication management dashboard built with Tailwind CSS v4 and DaisyUI v5, designed specifically for healthcare applications in South Africa.

## 🚀 Features

### Core Functionality
- **Medication List**: Display all medications with pill count indicators and stock status
- **Daily Schedule**: View today's medication schedule with tick boxes for marking taken/missed
- **Stock Alerts**: Real-time warnings for low stock and out-of-stock medications
- **Language Support**: Full bilingual support (English/Afrikaans) with language switcher
- **Responsive Design**: Mobile-first design that works on all devices
- **Django REST API Integration**: Ready for backend integration

### Healthcare-Focused Design
- **Accessibility**: WCAG 2.2 AA compliant with high contrast ratios
- **Senior-Friendly**: Large touch targets (48px+) and clear visual hierarchy
- **Medical Color Palette**: Trustworthy blue (#2563EB) and healing green (#10B981)
- **Visual Indicators**: Color-coded status badges and progress bars

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Vue 3 + Composition API + TypeScript
- **Styling**: Tailwind CSS v4 + DaisyUI v5
- **Internationalization**: Vue I18n
- **HTTP Client**: Axios for API communication
- **Build Tool**: Vite

### Project Structure
```
src/
├── components/
│   ├── common/
│   │   └── LanguageSwitcher.vue      # Language toggle component
│   └── medication/
│       ├── MedicationDashboard.vue   # Main dashboard component
│       ├── MedicationCard.vue        # Individual medication display
│       ├── ScheduleCard.vue          # Daily schedule with tick boxes
│       ├── StockAlertsCard.vue       # Stock warnings and alerts
│       └── AddMedicationModal.vue    # Add new medication form
├── services/
│   └── medicationApi.ts              # API service layer
├── types/
│   └── medication.ts                 # TypeScript interfaces
├── App.vue                          # Main application component
├── main.ts                          # Application entry point
└── style.css                        # Global styles and theme
```

## 🎨 Design System

### Color Palette
- **Primary Blue**: #2563EB (Trust, professionalism)
- **Secondary Green**: #10B981 (Health, healing)
- **Success Green**: #22C55E (Medication taken)
- **Warning Orange**: #F59E0B (Low stock alerts)
- **Error Red**: #EF4444 (Missed doses, critical alerts)
- **Info Blue**: #3B82F6 (General information)

### Components
- **Cards**: Clean, bordered cards with hover effects
- **Buttons**: Consistent button styles with loading states
- **Alerts**: Color-coded alert system for different severity levels
- **Forms**: Accessible form controls with validation
- **Modals**: Responsive modal dialogs for data entry

## 📱 Responsive Design

### Breakpoints
- **Mobile**: < 768px (Single column layout)
- **Tablet**: 768px - 1024px (Two column layout)
- **Desktop**: > 1024px (Three column layout)

### Mobile Optimizations
- Touch-friendly buttons (48px minimum)
- Swipe gestures for navigation
- Optimized typography for readability
- Collapsible sections for better space usage

## 🌐 Internationalization

### Supported Languages
- **English (en-ZA)**: Primary language
- **Afrikaans (af-ZA)**: Secondary language

### Translation Features
- Automatic language detection
- Persistent language preference
- Contextual translations
- RTL support ready

### Translation Keys
```typescript
{
  dashboard: {
    title: 'Medication Dashboard',
    subtitle: 'Manage your medications safely',
    todaySchedule: 'Today\'s Schedule',
    medicationList: 'Medication List',
    stockAlerts: 'Stock Alerts',
    // ... more keys
  },
  common: {
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    // ... more keys
  }
}
```

## 🔌 API Integration

### Django REST API Endpoints
```typescript
// Base URL: http://localhost:8000/api
const endpoints = {
  medications: '/medications/',
  schedule: '/medications/schedule/today/',
  alerts: '/medications/alerts/',
  markTaken: '/medications/schedule/{id}/mark-taken/',
  markMissed: '/medications/schedule/{id}/mark-missed/',
  updateStock: '/medications/{id}/stock/'
}
```

### Data Models
```typescript
interface Medication {
  id: string
  name: string
  dosage: string
  frequency: string
  time: string
  stock: number
  minStock: number
  instructions: string
  category: string
  isActive: boolean
  createdAt: string
  updatedAt: string
}

interface MedicationSchedule {
  id: string
  medicationId: string
  medication: Medication
  scheduledTime: string
  status: 'pending' | 'taken' | 'missed'
  takenAt?: string
  notes?: string
}

interface StockAlert {
  id: string
  medicationId: string
  medication: Medication
  type: 'low_stock' | 'out_of_stock' | 'expiring_soon'
  message: string
  severity: 'warning' | 'error' | 'info'
  createdAt: string
  isRead: boolean
}
```

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Django backend (optional for development)

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Format code
npm run format
```

### Environment Variables
```bash
# .env.local
VITE_API_BASE_URL=http://localhost:8000/api
```

### Development Mode
The application includes mock data for development:
- Sample medications with various stock levels
- Today's schedule with different statuses
- Stock alerts for testing

## 🧪 Testing

### Component Testing
```bash
# Run tests
npm run test

# Run tests with coverage
npm run test:coverage
```

### Accessibility Testing
- Automated testing with axe-core
- Manual testing with screen readers
- Keyboard navigation testing
- Color contrast validation

## 🔧 Configuration

### Tailwind CSS Configuration
```css
@theme {
  --color-primary: 37 99 235;      /* #2563EB */
  --color-secondary: 16 185 129;   /* #10B981 */
  --color-success: 34 197 94;      /* #22C55E */
  --color-warning: 245 158 11;     /* #F59E0B */
  --color-error: 239 68 68;        /* #EF4444 */
  --color-info: 59 130 246;        /* #3B82F6 */
}
```

### DaisyUI Configuration
```javascript
// tailwind.config.js
module.exports = {
  plugins: [require('daisyui')],
  daisyui: {
    themes: ['light', 'dark'],
    darkTheme: 'dark',
    base: true,
    styled: true,
    utils: true,
    prefix: '',
    logs: true,
    themeRoot: ':root'
  }
}
```

## 📊 Performance

### Optimization Features
- **Code Splitting**: Automatic route-based code splitting
- **Lazy Loading**: Components loaded on demand
- **Image Optimization**: Responsive images with WebP support
- **Caching**: API response caching with localStorage
- **Bundle Analysis**: Built-in bundle analyzer

### Performance Metrics
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## 🔒 Security

### Security Features
- **Input Validation**: Client-side and server-side validation
- **XSS Protection**: Automatic content sanitization
- **CSRF Protection**: Token-based CSRF protection
- **HTTPS Only**: Secure communication in production
- **Content Security Policy**: Strict CSP headers

## 🚀 Deployment

### Production Build
```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Docker Deployment
```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Environment Configuration
```bash
# Production environment variables
VITE_API_BASE_URL=https://api.medguard-sa.co.za
VITE_APP_ENV=production
VITE_APP_VERSION=$npm_package_version
```

## 🤝 Contributing

### Development Guidelines
1. Follow Vue 3 Composition API patterns
2. Use TypeScript for type safety
3. Implement proper error handling
4. Add comprehensive documentation
5. Write unit tests for components
6. Ensure accessibility compliance

### Code Style
- Use Prettier for code formatting
- Follow ESLint rules
- Use conventional commit messages
- Add JSDoc comments for functions

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Documentation
- [Vue 3 Documentation](https://vuejs.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)
- [DaisyUI Documentation](https://daisyui.com/)
- [Vue I18n Documentation](https://vue-i18n.intlify.dev/)

### Community
- GitHub Issues: For bug reports and feature requests
- Discord: For community discussions
- Email: For enterprise support

---

**MedGuard SA** - Empowering healthcare through technology 